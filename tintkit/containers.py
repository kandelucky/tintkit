"""TintKit — containers and surfaces.

Rounded cards, dialogs, callouts, the section header, the hero line, the drag
sashes and a themed scrollbar. These reuse the controls (a dialog footer is
real :class:`Button` widgets) and the themed plain widgets (:class:`Surface`,
:class:`Label`, :class:`IconLabel`) so the whole tree restyles live.

The rounded **Card** is the trick tk can't do with a plain Frame: a canvas
draws the rounded fill + hairline, and the content frame sits inset by ``pad``
(>= the corner radius) so its square corners never poke through the curve.

Geometry literals go through ``s()`` to scale to the screen DPI.
"""

import tkinter as tk
import tkinter.ttk as ttk

from .scaling import s
from .theme import mix
from .primitives import (CanvasControl, Surface, Label, IconLabel,
                         rounded_rect, font)
from .controls import Button, TextField


# ----------------------------------------------------------------------------
# Card — a rounded, hairline surface; add content into ``.body``
# ----------------------------------------------------------------------------
class Card:
    def __init__(self, parent, theme, pad=16, bg="panel", outer="bg",
                 radius=None, width=None):
        self.theme = theme
        self.pad = s(pad)
        self._bg, self._outer, self._radius = bg, outer, radius
        self.canvas = tk.Canvas(parent, highlightthickness=0, bg=theme[outer])
        self._w = width or 1
        if width:
            self.canvas.configure(width=width)
        self.body = tk.Frame(self.canvas, bg=theme[bg])
        self._win = self.canvas.create_window(self.pad, self.pad,
                                              window=self.body, anchor="nw")
        if width:                       # fixed-width card: size the body now, as
            self.canvas.itemconfigure(  # <Configure> may never change the width
                self._win, width=width - 2 * self.pad)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.body.bind("<Configure>", self._on_body)
        theme.subscribe(self._repaint)
        self.canvas.bind("<Destroy>", self._destroyed)
        self._repaint()

    def _radius_px(self):
        r = self._radius
        if r is None:
            return self.theme["r_card"]
        return self.theme[r] if isinstance(r, str) else s(r)

    def _on_canvas(self, e):
        if e.width > 1 and e.width != self._w:
            self._w = e.width
            self.canvas.itemconfigure(self._win, width=self._w - 2 * self.pad)
            self._repaint()

    def _on_body(self, e):
        h = e.height + 2 * self.pad
        if int(self.canvas.cget("height")) != h:
            self.canvas.configure(height=h)
        self._repaint()

    def _repaint(self):
        try:
            c, t = self.canvas, self.theme
            c.configure(bg=t[self._outer])
            self.body.configure(bg=t[self._bg])
            c.delete("cardbg")
            w, h = self._w, int(c.cget("height"))
            rounded_rect(c, 0, 0, w - s(1), h - s(1), self._radius_px(),
                         fill=t[self._bg], outline=t["border"], width=s(1),
                         tags="cardbg")
            c.tag_lower("cardbg")
        except tk.TclError:
            pass

    def _destroyed(self, e):
        if e.widget is self.canvas:
            self.theme.unsubscribe(self._repaint)

    def pack(self, **k):
        self.canvas.pack(**k)
        return self

    def grid(self, **k):
        self.canvas.grid(**k)
        return self

    def place(self, **k):
        self.canvas.place(**k)
        return self


# ----------------------------------------------------------------------------
# Section header — accent tick + title + divider rule
# ----------------------------------------------------------------------------
class SectionHeader(CanvasControl):
    def __init__(self, parent, theme, title, bg="bg"):
        self.title = title
        super().__init__(parent, theme, s(200), s(34), bg=bg, cursor="")
        self.canvas.bind("<Configure>", self._cfg)

    def _interactive(self):
        return False

    def _cfg(self, e):
        if e.width > 1 and e.width != self.w:
            self.w = e.width
            self.repaint()

    def draw(self):
        c, t = self.canvas, self.theme
        c.create_rectangle(0, s(6), s(3), s(30), fill=t["accent"], outline="")
        c.create_text(s(14), s(18), text=self.title.upper(), anchor="w",
                      fill=t["fg"], font=font(12, True))
        c.create_line(s(14), s(31), self.w - s(2), s(31), fill=t["divider"])


# ----------------------------------------------------------------------------
# Hero line — the accent-bar dialog heading
# ----------------------------------------------------------------------------
def hero_line(parent, theme, title, bg="panel"):
    row = Surface(parent, theme, bg=bg)
    Surface(row.widget, theme, bg="accent", width=s(3)).pack(side="left",
                                                             fill="y")
    Label(row.widget, theme, "  " + title, fg="fg", bg=bg, size=14,
          bold=True).pack(side="left")
    return row


# ----------------------------------------------------------------------------
# Callout — note / tip / warning
# ----------------------------------------------------------------------------
_CALLOUTS = {
    "info": ("fg_dim", "info", "Note", "fg"),
    "tip": ("accent", "star", "Tip", "accent"),
    "warn": ("warn", "info", "Warning", "warn"),
}


def callout(parent, theme, kind, text, title=None):
    edge, icon, deflabel, lcol = _CALLOUTS[kind]
    title = title or deflabel
    card = Card(parent, theme, pad=10, bg="panel")
    Surface(card.body, theme, bg=edge, width=s(3)).pack(side="left", fill="y")
    pad = Surface(card.body, theme, bg="panel")
    pad.widget.pack(side="left", fill="both", expand=True, padx=s(10), pady=s(2))
    head = Surface(pad.widget, theme, bg="panel")
    head.widget.pack(fill="x", anchor="w")
    IconLabel(head.widget, theme, icon, 15, fg=edge, bg="panel").pack(
        side="left", padx=(0, s(7)))
    Label(head.widget, theme, title, fg=lcol, bg="panel", size=9,
          bold=True).pack(side="left")
    Label(pad.widget, theme, text, fg="fg_dim", bg="panel", size=9,
          justify="left", wraplength=s(260)).pack(anchor="w", pady=(s(3), 0))
    return card


# ----------------------------------------------------------------------------
# Dialog — rounded popup: hero + close + body + optional input + buttons
# ----------------------------------------------------------------------------
def dialog(parent, theme, title, body_text, buttons, with_input=None,
           width=340, on_close=None):
    cw = s(width)
    card = Card(parent, theme, pad=20, bg="panel", width=cw)
    b = card.body
    top = Surface(b, theme, bg="panel")
    top.widget.pack(fill="x")
    hero_line(top.widget, theme, title).pack(side="left")
    x = IconLabel(top.widget, theme, "x", 16, fg="fg_dim", bg="panel",
                  cursor="hand2")
    x.widget.pack(side="right")
    if on_close:
        x.widget.bind("<Button-1>", lambda e: on_close())
    Label(b, theme, body_text, fg="fg_dim", bg="panel", size=9, justify="left",
          wraplength=cw - s(60)).pack(anchor="w", pady=(s(12), 0))
    if with_input is not None:
        TextField(b, theme, with_input, bg="panel").pack(fill="x",
                                                         pady=(s(12), 0))
    foot = Surface(b, theme, bg="panel")
    foot.widget.pack(fill="x", pady=(s(18), 0))
    for spec in buttons:
        Button(foot.widget, theme, bg="panel", **spec).pack(side="right",
                                                            padx=(s(8), 0))
    return card


# ----------------------------------------------------------------------------
# Movable panels — drag sashes (look only; reused from the real app)
# ----------------------------------------------------------------------------
def theme_frame(theme, frame, **tokens):
    """Keep a plain ``tk.Frame``'s colours following the theme.

    ``tokens`` maps tk options to theme tokens, e.g.
    ``theme_frame(theme, f, bg="bg", highlightbackground="border")``. Without
    this a frame built straight from ``theme[...]`` freezes on the palette it
    was born in and turns dark on a light page after a live theme switch.
    """
    def restyle():
        if not frame.winfo_exists():
            return
        frame.configure(**{opt: theme[tok] for opt, tok in tokens.items()})
    restyle()
    theme.subscribe(restyle)
    frame.bind("<Destroy>", lambda e: theme.unsubscribe(restyle))
    return frame


def v_sash(parent, theme):
    "Vertical sidebar↔preview sash: bar + centred grip, accent on hover."
    comp = Surface(parent, theme, bg="bg")
    Surface(comp.widget, theme, bg="sidebar", width=s(120), height=s(90)).pack(
        side="left")
    sash = tk.Frame(comp.widget, bg=theme["bar"], width=s(8), height=s(90),
                    cursor="sb_h_double_arrow")
    sash.pack(side="left")
    sash.pack_propagate(False)
    grip = tk.Frame(sash, bg=theme["fg_dim"])
    grip.place(relx=0.5, rely=0.5, anchor="center", width=s(4), height=s(40))
    preview = tk.Frame(comp.widget, bg=theme["bg"], width=s(120), height=s(90),
                       highlightthickness=s(1), highlightbackground=theme["border"])
    preview.pack(side="left")
    theme_frame(theme, preview, bg="bg", highlightbackground="border")
    _hover_grip(theme, sash, grip, "bar")
    return comp


def h_sash(parent, theme):
    "Horizontal folder-list divider: hairline + centred grip, accent on hover."
    comp = Surface(parent, theme, bg="bg")
    Surface(comp.widget, theme, bg="sidebar", width=s(200), height=s(44)).pack(
        fill="x")
    sash = tk.Frame(comp.widget, bg=theme["sidebar"], height=s(11), width=s(200),
                    cursor="sb_v_double_arrow")
    sash.pack(fill="x")
    sash.pack_propagate(False)
    line = tk.Frame(sash, bg=theme["border"])
    line.place(relx=0, rely=0.5, relwidth=1, height=s(1), anchor="w")
    theme_frame(theme, line, bg="border")
    grip = tk.Frame(sash, bg=theme["fg_dim"])
    grip.place(relx=0.5, rely=0.5, anchor="center", width=s(40), height=s(4))
    Surface(comp.widget, theme, bg="sidebar", width=s(200), height=s(44)).pack(
        fill="x")
    _hover_grip(theme, sash, grip, "sidebar")
    return comp


def _hover_grip(theme, sash, grip, base_token):
    def on(_e=None):
        sash.configure(bg=theme["hover"])
        grip.configure(bg=theme["accent"])

    def off(_e=None):
        if not sash.winfo_exists():
            return
        sash.configure(bg=theme[base_token])
        grip.configure(bg=theme["fg_dim"])
    for w in (sash, grip):
        w.bind("<Enter>", on)
        w.bind("<Leave>", off)
    # follow live theme switches while the grip is idle (not hovered)
    theme.subscribe(off)
    sash.bind("<Destroy>", lambda e: theme.unsubscribe(off))


# ----------------------------------------------------------------------------
# Themed scrollbar — slim, arrow-less; restyles on theme change
# ----------------------------------------------------------------------------
def themed_scrollbar(parent, theme, command, name="TintKit.Vertical.TScrollbar"):
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.layout(name, [
        ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])

    def restyle():
        style.configure(name, troughcolor=theme["sidebar"],
                        background=theme["border"], bordercolor=theme["sidebar"],
                        borderwidth=0, relief="flat", arrowcolor=theme["sidebar"],
                        width=s(10))
        style.map(name, background=[
            ("active", mix(theme["border"], theme["fg"], 0.35)),
            ("pressed", mix(theme["border"], theme["fg"], 0.5))])
    restyle()
    theme.subscribe(restyle)
    sb = ttk.Scrollbar(parent, orient="vertical", command=command, style=name)
    sb.bind("<Destroy>", lambda e: theme.unsubscribe(restyle))
    return sb
