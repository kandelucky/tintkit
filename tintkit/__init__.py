"""TintKit — a small, themeable Tkinter widget kit.

A dark/light photo-tool look as reusable controls. One theme drives every
colour; controls reuse each other; everything is interactive.

    import tkinter as tk
    from tintkit import Theme, Button, setup_dpi

    root = tk.Tk()
    setup_dpi(root)                       # crisp icons on high-DPI screens
    theme = Theme(scheme="dark", accent="#8fae9b")
    Button(root, theme, "Save", icon="save", command=lambda: None).pack()
    root.mainloop()

Switch the look at any time — the whole window repaints::

    theme.set(scheme="light")
    theme.set(accent="#c08457")

See ``gallery.py`` for every component rendered together with a live switcher.
"""

from . import icons
from .icons import set_icon_dir
from .scaling import s, set_scale
from .theme import (Theme, mix, lighten, darken, on_color,
                    SCHEMES, DEFAULT_ACCENT)
from .primitives import (CanvasControl, Dot, Surface, Label, IconLabel,
                         rounded_rect, put_icon, font, measure, FONT_FAMILY,
                         resolve_font)
from .controls import (Button, IconButton, Slider, TitledSlider, Toggle, Radio,
                       RadioGroup, Checkbox, SegmentedTabs, Badge, Tag,
                       ProgressBar, Tooltip, HoverTip, TextField, TextArea,
                       Dropdown, MultiDropdown)
from .containers import (Card, Foldout, SectionHeader, HeroLine, hero_line,
                         callout, dialog, v_sash, h_sash, themed_scrollbar)
from .composites import (toolbar, tool_rail, FolderNav, FolderTree, folder_tree,
                         SelectTile, SelectRow, MultiSelectRow,
                         multiselect_list, SettingsWindow)

__all__ = [
    "Theme", "mix", "lighten", "darken", "on_color", "SCHEMES",
    "DEFAULT_ACCENT", "icons", "set_icon_dir", "setup_dpi",
    "enable_dpi_awareness", "s", "set_scale",
    "CanvasControl", "Dot", "Surface", "Label", "IconLabel",
    "rounded_rect", "put_icon", "font", "measure", "FONT_FAMILY", "resolve_font",
    "Button", "IconButton", "Slider", "TitledSlider", "Toggle", "Radio",
    "RadioGroup",
    "Checkbox", "SegmentedTabs", "Badge", "Tag", "ProgressBar", "Tooltip",
    "HoverTip", "TextField", "TextArea", "Dropdown", "MultiDropdown",
    "Card", "Foldout", "SectionHeader", "HeroLine", "hero_line", "callout",
    "dialog",
    "v_sash", "h_sash", "themed_scrollbar",
    "toolbar", "tool_rail", "FolderNav", "FolderTree", "folder_tree", "SelectTile",
    "SelectRow", "MultiSelectRow", "multiselect_list", "SettingsWindow",
]


def enable_dpi_awareness():
    """Tell Windows this process draws at the real screen resolution.

    MUST run before the first ``tk.Tk()`` — otherwise Tk caches the virtualised
    96 DPI and everything renders tiny. The kit calls this automatically on
    import, so importing ``tintkit`` before creating the root is enough.
    """
    import sys
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)   # per-monitor aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()     # older fallback
        except Exception:
            pass


def setup_dpi(root, zoom=1.0):
    """Scale fonts + icons + geometry to the screen. Returns the scale factor.

    Call once, right after creating the root window and BEFORE building the
    Theme. ``zoom`` is an extra comfort multiplier on top of the screen DPI
    (1.0 = true size; raise it to make the whole UI bigger).

    * Tk text scaling → ``(screen_dpi / 72) * zoom`` (fonts + text measurement).
    * The kit's geometry scale ``S`` → ``(screen_dpi / 96) * zoom`` (canvas px).
    """
    from . import scaling, primitives
    enable_dpi_awareness()                 # idempotent; real fix is at import
    primitives.resolve_font(root)          # native UI font for this OS
    try:
        fpix = root.winfo_fpixels("1i")
        root.tk.call("tk", "scaling", (fpix / 72.0) * zoom)
        factor = max(1.0, fpix / 96.0) * zoom
    except Exception:
        factor = zoom
    scaling.set_scale(factor)
    icons.DPI = factor
    return factor


# Set DPI awareness at import — before any tk.Tk() the caller creates.
enable_dpi_awareness()
