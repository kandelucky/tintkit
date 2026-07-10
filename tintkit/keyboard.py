"""Keyboard fixes for Tk on Windows: non-Latin (Georgian, Armenian, ...) typing
and Ctrl-shortcut / right-click clipboard on non-Latin layouts.

Two fixes, both needed for a non-Latin keyboard to work fully in Tk 8.6:

1. Unicode keyboard recovery — Tk 8.6 decodes ``WM_CHAR`` through the Windows
   ANSI code page, so any character outside it reaches Tk as ``'?'`` even though
   Windows delivered the correct Unicode codepoint. ``recover_char()`` asks
   Win32 ``ToUnicodeEx`` for the real character; the recovery binding inserts it.
   ``root.tk.call("encoding", "system", "utf-8")`` does NOT fix this — that only
   fixes strings Python hands to Tk (labels, ``.insert``). This fixes typing.

2. Clipboard shortcut router + right-click menu — Tk's default ``<Control-c>``…
   bindings match by the Latin keysym, so on a non-Latin layout (keysym ``'??'``)
   Copy / Paste / Cut / Select-All silently break. The router falls back to the
   hardware keycode; right-click opens a Cut/Copy/Paste/Select-All menu.

``install()`` wires both into every ``tkinter.Entry`` / ``tkinter.Text`` via a
one-time monkey-patch on their ``__init__``. tintkit calls it at import, so any
app that imports tintkit before building widgets is covered. No-op off Windows
for the recovery half (the clipboard router is cross-platform).

Widgets that bind their OWN ``<KeyPress>`` replace the recovery binding Tk-side
(a same-sequence instance bind overwrites the previous one). Such widgets should
call ``recover_char(event)`` from that handler, insert the result, and return
``"break"``. ``recover_char`` returns ``None`` when there is nothing to recover,
so ordinary keys fall through untouched.
"""

import sys
import tkinter


# --- Cross-platform clipboard router + right-click menu ---------------------

if sys.platform == "darwin":
    _MODIFIER_KEYPRESS = "<Command-KeyPress>"
    _RIGHT_CLICK_EVENTS = ("<Button-2>", "<Control-Button-1>")
    _CLIPBOARD_KEYCODES = {8: "<<Copy>>", 9: "<<Paste>>", 7: "<<Cut>>", 0: "<<SelectAll>>"}
else:
    _MODIFIER_KEYPRESS = "<Control-KeyPress>"
    _RIGHT_CLICK_EVENTS = ("<Button-3>",)
    # Windows VK codes.
    _CLIPBOARD_KEYCODES = {67: "<<Copy>>", 86: "<<Paste>>", 88: "<<Cut>>", 65: "<<SelectAll>>"}


def _on_clipboard_modifier(event):
    # Latin keysym → Tk's default <Control-c>/<Command-c> already fired.
    if event.keysym.lower() in ("v", "c", "x", "a"):
        return None
    action = _CLIPBOARD_KEYCODES.get(event.keycode)
    if action is None:
        return None
    try:
        event.widget.event_generate(action)
    except tkinter.TclError:
        return None
    return "break"


def _on_right_click_popup(event):
    widget = event.widget
    has_sel = False
    try:
        has_sel = bool(widget.selection_present())
    except Exception:
        try:
            has_sel = bool(widget.tag_ranges("sel"))
        except Exception:
            has_sel = False
    menu = tkinter.Menu(widget, tearoff=0)
    menu.add_command(
        label="Cut",
        state="normal" if has_sel else "disabled",
        command=lambda: widget.event_generate("<<Cut>>"),
    )
    menu.add_command(
        label="Copy",
        state="normal" if has_sel else "disabled",
        command=lambda: widget.event_generate("<<Copy>>"),
    )
    menu.add_command(
        label="Paste",
        command=lambda: widget.event_generate("<<Paste>>"),
    )
    menu.add_separator()
    menu.add_command(
        label="Select All",
        command=lambda: widget.event_generate("<<SelectAll>>"),
    )
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


_class_bindings_installed = False


def _install_class_bindings_once(any_widget):
    global _class_bindings_installed
    if _class_bindings_installed:
        return
    _class_bindings_installed = True
    for cls in ("Entry", "Text"):
        any_widget.bind_class(cls, _MODIFIER_KEYPRESS, _on_clipboard_modifier, add=True)
        for evt in _RIGHT_CLICK_EVENTS:
            any_widget.bind_class(cls, evt, _on_right_click_popup, add=True)


# --- Windows-only Unicode keyboard recovery ---------------------------------

if sys.platform.startswith("win"):
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32", use_last_error=True)

    _user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    _user32.GetKeyboardLayout.restype = wintypes.HKL

    _user32.GetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
    _user32.GetKeyboardState.restype = wintypes.BOOL

    _user32.MapVirtualKeyExW.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.HKL]
    _user32.MapVirtualKeyExW.restype = wintypes.UINT

    _user32.ToUnicodeEx.argtypes = [
        wintypes.UINT, wintypes.UINT,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_wchar_p, ctypes.c_int,
        wintypes.UINT, wintypes.HKL,
    ]
    _user32.ToUnicodeEx.restype = ctypes.c_int

    _MAPVK_VK_TO_VSC = 0
    _RECOVERY_ATTR = "_tk_unicode_recovery_attached"

    def _vk_to_unicode(vk_code):
        state = (ctypes.c_ubyte * 256)()
        if not _user32.GetKeyboardState(state):
            return None
        layout = _user32.GetKeyboardLayout(0)
        scan = _user32.MapVirtualKeyExW(vk_code, _MAPVK_VK_TO_VSC, layout)
        buf = ctypes.create_unicode_buffer(8)
        n = _user32.ToUnicodeEx(vk_code, scan, state, buf, len(buf), 0, layout)
        if n > 0:
            return buf.value[:n]
        return None

    def recover_char(event):
        """Real Unicode char for a keystroke Tk mangled to ``'?'``, else ``None``.

        Call from a widget's own ``<KeyPress>`` handler when that handler
        replaces the recovery binding install() adds; insert the result yourself
        and return ``"break"``. ``None`` means nothing to recover.
        """
        if event.char == "?" and event.keysym == "??":
            try:
                return _vk_to_unicode(event.keycode)
            except Exception:
                return None
        return None

    def _on_keypress(event):
        recovered = recover_char(event)
        if recovered:
            try:
                event.widget.insert(event.widget.index("insert"), recovered)
            except Exception:
                return None
            return "break"
        return None

    def attach_unicode_keyboard_recovery(tk_widget):
        if getattr(tk_widget, _RECOVERY_ATTR, False):
            return
        setattr(tk_widget, _RECOVERY_ATTR, True)
        tk_widget.bind("<KeyPress>", _on_keypress, add=True)

else:
    def recover_char(event):
        return None

    def attach_unicode_keyboard_recovery(tk_widget):
        pass


# --- One-time monkey-patch of tk.Entry / tk.Text ----------------------------

_installed = False


def install():
    """Wire the recovery + clipboard fixes into every tk.Entry / tk.Text.

    Idempotent; tintkit calls it at import. Safe to call again."""
    global _installed
    if _installed:
        return
    _installed = True

    orig_entry_init = tkinter.Entry.__init__
    orig_text_init = tkinter.Text.__init__

    def _patched_entry_init(self, *args, **kwargs):
        orig_entry_init(self, *args, **kwargs)
        attach_unicode_keyboard_recovery(self)
        _install_class_bindings_once(self)

    def _patched_text_init(self, *args, **kwargs):
        orig_text_init(self, *args, **kwargs)
        attach_unicode_keyboard_recovery(self)
        _install_class_bindings_once(self)

    tkinter.Entry.__init__ = _patched_entry_init
    tkinter.Text.__init__ = _patched_text_init
