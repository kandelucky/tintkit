"""TintKit — foldout prototypes (Unity-Inspector-style collapsible groups).

Four visual variants of a fold-away group, side by side, each filled with a
different mix of controls, plus a live Dark/Light + accent switcher. A test
bench for picking ONE look before the widget graduates into the kit proper.

    python demo_foldout.py

A — Flat        chevron + dim caption, no background (the lightest look).
B — Strip       full-width Unity-style header bar; indented body behind a
                guide line; holds a nested flat foldout.
C — Enable      strip header carrying an on/off checkbox (a Unity component):
                unticking hides the body even while the fold is open.
D — Card        a bordered card whose header folds the body inside the border.
"""

import tkinter as tk

from tintkit import (
    Theme, setup_dpi, s,
    Surface, Label, IconLabel,
    Button, TitledSlider, Toggle, Checkbox, SegmentedTabs, Dropdown, TextField,
    HoverTip,
)
from tintkit.containers import theme_frame

PANEL = "bar"          # every column mimics a tool panel: bar bg, bordered


# ----------------------------------------------------------------------------
# the foldout variants
# ----------------------------------------------------------------------------
class _FoldBase:
    """Shared open/close plumbing. Subclasses build a header into the wrap and
    (optionally) restyle the body container; content goes into ``.body``."""

    def __init__(self, parent, theme, title, open=False):
        self.theme = theme
        self.title = title
        self.open = open
        self.wrap = Surface(parent, theme, bg=PANEL)
        self._build_header(self.wrap.widget)
        self.holder = Surface(self.wrap.widget, theme, bg=PANEL)
        self.body = self._build_body(self.holder.widget)

    def pack(self, **kw):
        self.wrap.widget.pack(**kw)
        self._refresh()
        return self

    def _build_body(self, holder):
        "Default body container: plain, no indent. Variants may override."
        inner = Surface(holder, self.theme, bg=PANEL)
        inner.widget.pack(fill="x")
        return inner.widget

    def toggle(self, _e=None):
        self.open = not self.open
        self._refresh()

    def _visible(self):
        return self.open

    def _refresh(self):
        self._chev.set_icon("chevron-down" if self.open else "chevron-right")
        if self._visible():
            if not self.holder.widget.winfo_manager():
                self.holder.widget.pack(fill="x")
        else:
            self.holder.widget.pack_forget()

    def _bind_toggle(self, *widgets):
        for w in widgets:
            w.bind("<Button-1>", self.toggle)


def _hover(theme, frame, children, base):
    "Header hover: lift the strip (and everything riding on it) to `hover`."
    everything = [frame] + children

    def paint(tok):
        def apply(_e=None):
            if not frame.winfo_exists():
                return
            col = theme[tok]
            for w in everything:
                w.configure(bg=col)
        return apply
    on, off = paint("hover"), paint(base)
    frame.bind("<Enter>", on)
    frame.bind("<Leave>", off)
    theme.subscribe(off)                   # follow Dark/Light while idle
    frame.bind("<Destroy>", lambda e: theme.unsubscribe(off))


class FoldFlat(_FoldBase):
    "A — chevron + small dim caption on the panel background. No chrome at all."

    def _build_header(self, parent):
        head = tk.Frame(parent, bg=self.theme[PANEL], cursor="hand2")
        theme_frame(self.theme, head, bg=PANEL)
        head.pack(fill="x", pady=(0, s(4)))
        self._chev = IconLabel(head, self.theme, "chevron-right", 12,
                               fg="fg_dim", bg=PANEL)
        self._chev.widget.pack(side="left", padx=(0, s(6)))
        cap = Label(head, self.theme, self.title, fg="fg_dim", bg=PANEL,
                    size=8, bold=True)
        cap.widget.pack(side="left")
        self._bind_toggle(head, self._chev.widget, cap.widget)


class FoldStrip(_FoldBase):
    """B — the Unity look: a full-width header strip a step lighter than the
    panel, bold title, hover feedback; the body indents behind a guide line."""

    def _build_header(self, parent):
        head = tk.Frame(parent, bg=self.theme["chip"], cursor="hand2")
        theme_frame(self.theme, head, bg="chip")
        head.pack(fill="x", pady=(0, s(2)))
        self._head = head
        self._chev = IconLabel(head, self.theme, "chevron-right", 12,
                               fg="fg", bg="chip")
        self._chev.widget.pack(side="left", padx=(s(8), s(6)), pady=s(6))
        title = Label(head, self.theme, self.title, fg="fg", bg="chip",
                      size=9, bold=True)
        title.widget.pack(side="left", pady=s(6))
        self._bind_toggle(head, self._chev.widget, title.widget)
        _hover(self.theme, head, [self._chev.widget, title.widget], "chip")

    def _build_body(self, holder):
        guide = tk.Frame(holder, bg=self.theme["divider"], width=s(1))
        theme_frame(self.theme, guide, bg="divider")
        guide.pack(side="left", fill="y", padx=(s(13), 0))
        inner = Surface(holder, self.theme, bg=PANEL)
        inner.widget.pack(side="left", fill="x", expand=True,
                          padx=(s(10), 0), pady=(s(2), s(6)))
        return inner.widget


class FoldEnable(FoldStrip):
    """C — the strip header carries an enable checkbox, like a Unity component:
    the chevron folds, the tick switches the whole group on/off, and while OFF
    the body stays hidden even if the fold is open."""

    def __init__(self, parent, theme, title, open=False, enabled=True):
        self.enabled = enabled
        super().__init__(parent, theme, title, open)

    def _build_header(self, parent):
        head = tk.Frame(parent, bg=self.theme["chip"], cursor="hand2")
        theme_frame(self.theme, head, bg="chip")
        head.pack(fill="x", pady=(0, s(2)))
        self._chev = IconLabel(head, self.theme, "chevron-right", 12,
                               fg="fg", bg="chip")
        self._chev.widget.pack(side="left", padx=(s(8), s(4)), pady=s(6))
        self._chk = Checkbox(head, self.theme, "",
                             state="on" if self.enabled else "off", bg="chip",
                             command=lambda _st: self._set_enabled())
        self._chk.pack(side="left")
        HoverTip(self._chk.canvas, self.theme, "Turn the whole group on / off")
        self._title = Label(head, self.theme, self.title,
                            fg="fg" if self.enabled else "fg_dim",
                            bg="chip", size=9, bold=True)
        self._title.widget.pack(side="left", padx=(s(2), 0), pady=s(6))
        gear = IconLabel(head, self.theme, "settings", 13, fg="fg_dim",
                         bg="chip")
        gear.widget.pack(side="right", padx=(0, s(8)))
        HoverTip(gear.widget, self.theme, "Group options (just a mock)")
        self._bind_toggle(head, self._chev.widget, self._title.widget)
        _hover(self.theme, head,
               [self._chev.widget, self._title.widget, gear.widget], "chip")

    def _set_enabled(self):
        self.enabled = self._chk.state == "on"
        self._title._fg = "fg" if self.enabled else "fg_dim"
        self._title._restyle()
        if self.enabled and not self.open:
            self.open = True               # ticking it on reveals the knobs
        self._refresh()

    def _visible(self):
        return self.open and self.enabled


class FoldCard(_FoldBase):
    "D — a bordered box; the header sits inside and the body grows the box."

    def _build_header(self, parent):
        box = tk.Frame(parent, bg=self.theme[PANEL], highlightthickness=1,
                       highlightbackground=self.theme["border"])
        theme_frame(self.theme, box, bg=PANEL, highlightbackground="border")
        box.pack(fill="x")
        self._box = box
        head = tk.Frame(box, bg=self.theme[PANEL], cursor="hand2")
        theme_frame(self.theme, head, bg=PANEL)
        head.pack(fill="x", padx=s(9), pady=s(7))
        self._chev = IconLabel(head, self.theme, "chevron-right", 12,
                               fg="fg_dim", bg=PANEL)
        self._chev.widget.pack(side="left", padx=(0, s(6)))
        cap = Label(head, self.theme, self.title, fg="fg_dim", bg=PANEL,
                    size=8, bold=True)
        cap.widget.pack(side="left")
        self._bind_toggle(head, self._chev.widget, cap.widget)

    def _build_body(self, holder):
        # the body must live INSIDE the border box, under the header
        self.holder.widget.destroy()
        self.holder = Surface(self._box, self.theme, bg=PANEL)
        inner = Surface(self.holder.widget, self.theme, bg=PANEL)
        inner.widget.pack(fill="x", padx=s(10), pady=(0, s(9)))
        return inner.widget


# ----------------------------------------------------------------------------
# demo content — a different toolbox inside every variant
# ----------------------------------------------------------------------------
def fill_sliders(parent, theme):
    "Compact TitledSliders — the photo-tool staple."
    for name, val, lo, hi, neu, fmt in (
            ("Distance", 10, 0, 50, 10, lambda v, n: str(v)),
            ("Angle", 45, -180, 180, 45, lambda v, n: f"{v}°"),
            ("Blur", 20, 0, 100, 20, lambda v, n: str(v)),
            ("Opacity", 60, 0, 100, 60, lambda v, n: str(v))):
        TitledSlider(parent, theme, name, value=val, lo=lo, hi=hi, neutral=neu,
                     bg=PANEL, compact=True, reset_tip="Reset",
                     value_fmt=fmt).pack(fill="x", pady=(s(3), 0))


def fill_colour_row(parent, theme, label="Colour", swatch="#000000"):
    row = Surface(parent, theme, bg=PANEL)
    row.widget.pack(fill="x", pady=(s(6), 0))
    Label(row.widget, theme, label, fg="fg_dim", bg=PANEL, size=8,
          bold=True).pack(side="left")
    sw = tk.Frame(row.widget, bg=swatch, cursor="hand2", width=s(40),
                  height=s(20), highlightthickness=1)
    theme_frame(theme, sw, highlightbackground="border")
    sw.pack(side="right")
    sw.pack_propagate(False)


def fill_toggles(parent, theme):
    "Toggle rows + segmented tabs."
    for name, on in (("Show grid", True), ("Snap to edges", False),
                     ("Live preview", True)):
        row = Surface(parent, theme, bg=PANEL)
        row.widget.pack(fill="x", pady=(s(4), 0))
        Label(row.widget, theme, name, fg="fg", bg=PANEL, size=9).pack(
            side="left")
        Toggle(row.widget, theme, value=on, bg=PANEL).pack(side="right")
    Label(parent, theme, "Quality", fg="fg_dim", bg=PANEL, size=8,
          bold=True).pack(anchor="w", pady=(s(9), s(3)))
    SegmentedTabs(parent, theme, ["Soft", "Normal", "Sharp"], selected=1,
                  bg=PANEL).pack(anchor="w")


def fill_checkboxes(parent, theme):
    for name, st in (("Keep EXIF", "on"), ("Keep ICC profile", "on"),
                     ("Strip GPS", "off")):
        Checkbox(parent, theme, name, state=st, bg=PANEL).pack(
            anchor="w", pady=(s(3), 0))


def fill_buttons(parent, theme):
    "Dropdown + text field + a two-button footer."
    Dropdown(parent, theme, ["Sans", "Sans Bold", "Serif", "Script"],
             selected=0, bg=PANEL, min_w=100).pack(fill="x", pady=(s(2), 0))
    TextField(parent, theme, "Watermark © Lasha", bg=PANEL).pack(
        fill="x", pady=(s(7), 0))
    foot = Surface(parent, theme, bg=PANEL)
    foot.widget.pack(fill="x", pady=(s(9), 0))
    foot.widget.grid_columnconfigure(0, weight=1, uniform="d")
    foot.widget.grid_columnconfigure(1, weight=1, uniform="d")
    Button(foot.widget, theme, "Apply", role="primary", variant="filled",
           stretch=True, bg=PANEL).grid(row=0, column=0, sticky="ew",
                                        padx=(0, s(3)))
    Button(foot.widget, theme, "Reset", role="neutral", variant="outline",
           stretch=True, bg=PANEL).grid(row=0, column=1, sticky="ew",
                                        padx=(s(3), 0))


# ----------------------------------------------------------------------------
# the page
# ----------------------------------------------------------------------------
ACCENTS = [("Sage", "#8fae9b"), ("Terracotta", "#c08457"),
           ("Ocean", "#5b8ec9"), ("Gold", "#c9a24a")]


def column(parent, theme, tag, name, note):
    "One bordered panel column: variant tag + name + hint, content below."
    col = tk.Frame(parent, bg=theme[PANEL], highlightthickness=1,
                   highlightbackground=theme["border"])
    theme_frame(theme, col, bg=PANEL, highlightbackground="border")
    col.pack(side="left", fill="both", expand=True, padx=s(6), pady=s(6))
    inner = Surface(col, theme, bg=PANEL)
    inner.widget.pack(fill="both", expand=True, padx=s(12), pady=s(10))
    Label(inner.widget, theme, tag + " — " + name, fg="fg", bg=PANEL,
          size=11, bold=True).pack(anchor="w")
    Label(inner.widget, theme, note, fg="fg_dim", bg=PANEL, size=8,
          justify="left", wraplength=s(240)).pack(anchor="w",
                                                  pady=(s(2), s(12)))
    return inner.widget


def build(root, theme):
    page = Surface(root, theme, bg="bg")
    page.widget.pack(fill="both", expand=True)

    # theme switcher
    bar = Surface(page.widget, theme, bg="bg")
    bar.widget.pack(fill="x", padx=s(14), pady=(s(10), s(4)))
    Label(bar.widget, theme, "Foldout prototypes", fg="fg", bg="bg", size=13,
          bold=True).pack(side="left")
    Dropdown(bar.widget, theme, [n for n, _c in ACCENTS], selected=0, bg="bg",
             min_w=120,
             command=lambda i, _l: theme.set(accent=ACCENTS[i][1])).pack(
                 side="right", padx=(s(8), 0))
    SegmentedTabs(bar.widget, theme, ["Dark", "Light"],
                  selected=0 if theme.scheme == "dark" else 1, bg="bg",
                  command=lambda i, _l: theme.set(
                      scheme="dark" if i == 0 else "light")).pack(side="right")

    row = Surface(page.widget, theme, bg="bg")
    row.widget.pack(fill="both", expand=True, padx=s(8), pady=(0, s(8)))

    # A — flat: sliders in one group, checkboxes in a second (closed) one
    a = column(row.widget, theme, "A", "Flat",
               "Chevron + dim caption, no background — the lightest chrome "
               "(what crop's Straighten group does today).")
    fa1 = FoldFlat(a, theme, "SHADOW", open=True).pack(fill="x")
    fill_sliders(fa1.body, theme)
    fill_colour_row(fa1.body, theme)
    fa2 = FoldFlat(a, theme, "METADATA", open=False).pack(fill="x",
                                                          pady=(s(10), 0))
    fill_checkboxes(fa2.body, theme)

    # B — strip, with a nested flat foldout inside
    b = column(row.widget, theme, "B", "Strip",
               "Unity's look: a full-width header bar one step lighter, bold "
               "title, hover feedback, the body indented behind a guide "
               "line. Groups stack flush; one holds a nested foldout.")
    fb1 = FoldStrip(b, theme, "View options", open=True).pack(fill="x")
    fill_toggles(fb1.body, theme)
    nested = FoldFlat(fb1.body, theme, "ADVANCED", open=False).pack(
        fill="x", pady=(s(10), 0))
    fill_checkboxes(nested.body, theme)
    fb2 = FoldStrip(b, theme, "Transform", open=False).pack(fill="x")
    fill_sliders(fb2.body, theme)

    # C — enable: the Manoni shadow case
    c = column(row.widget, theme, "C", "Enable",
               "The strip header carries an on/off tick (a Unity component). "
               "Ticking it off hides the knobs even while the fold is open; "
               "ticking it back on pops them out again.")
    fc1 = FoldEnable(c, theme, "Shadow", open=True, enabled=True).pack(
        fill="x")
    fill_sliders(fc1.body, theme)
    fill_colour_row(fc1.body, theme)
    fc2 = FoldEnable(c, theme, "Outline", open=False, enabled=False).pack(
        fill="x")
    fill_colour_row(fc2.body, theme, label="Outline colour", swatch="#ffffff")

    # D — card
    d = column(row.widget, theme, "D", "Card",
               "A bordered card that folds: the header lives inside the box "
               "and the border grows around the content — the crop-card "
               "look, made collapsible.")
    fd1 = FoldCard(d, theme, "TEXT STYLE", open=True).pack(fill="x")
    fill_buttons(fd1.body, theme)
    fd2 = FoldCard(d, theme, "PLACEMENT", open=False).pack(fill="x",
                                                           pady=(s(8), 0))
    fill_toggles(fd2.body, theme)
    return page


def main():
    root = tk.Tk()
    root.title("TintKit — foldout prototypes")
    setup_dpi(root)
    theme = Theme(scheme="dark", accent="#8fae9b")
    root.configure(bg=theme["bg"])
    build(root, theme)
    root.geometry("+40+40")
    root.mainloop()


if __name__ == "__main__":
    main()
