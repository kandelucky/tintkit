"""TintKit — composites.

Bigger pieces assembled *only* from the kit: a toolbar is a row of
:class:`IconButton`, the folder nav reuses :class:`Badge` and :class:`IconLabel`,
the settings window reuses :class:`Toggle`, :class:`Dropdown`, :class:`Button`.
No composite re-implements a primitive, and every part restyles on theme change.

Geometry literals go through ``s()`` to scale to the screen DPI.
"""

import tkinter as tk

from .scaling import s
from .primitives import Surface, Label, IconLabel, rounded_rect, put_icon, font
from . import icons
from .controls import (IconButton, Toggle, Dropdown, SegmentedTabs, Slider,
                       Button, Badge)
from .containers import Card, SectionHeader


# ----------------------------------------------------------------------------
# Toolbar — a row of square icon buttons (exclusive active item)
# ----------------------------------------------------------------------------
def toolbar(parent, theme, items, active=0, bg="bar", command=None):
    "items: list of icon names. Returns a Surface; one item stays active."
    bar = Surface(parent, theme, bg=bg)
    btns = []

    def choose(i):
        for j, b in enumerate(btns):
            b.set_active(j == i)
        if command:
            command(i, items[i])
    for i, name in enumerate(items):
        b = IconButton(bar.widget, theme, name, active=(i == active), bg=bg,
                       command=lambda i=i: choose(i))
        b.pack(side="left", padx=s(3), pady=s(5))
        btns.append(b)
    return bar


# ----------------------------------------------------------------------------
# Tool rail — captioned tiles (icon above a label)
# ----------------------------------------------------------------------------
def tool_rail(parent, theme, items, active=0, bg="bar", command=None):
    "items: list of (icon, label). Returns a Surface; one tile stays active."
    box = Surface(parent, theme, bg=bg)
    btns = []

    def choose(i):
        for j, b in enumerate(btns):
            b.set_active(j == i)
        if command:
            command(i, items[i][1])
    for i, (name, label) in enumerate(items):
        b = IconButton(box.widget, theme, name, w=70, h=56, label=label,
                       active=(i == active), icon_px=20, bg=bg,
                       command=lambda i=i: choose(i))
        b.pack(side="left", padx=s(2))
        btns.append(b)
    return box


# ----------------------------------------------------------------------------
# Folder navigation — path bar + collapsible folder tree
# ----------------------------------------------------------------------------
class FolderNav:
    def __init__(self, parent, theme, crumbs, tree_rows, count_text,
                 filter_text="Filter folders…"):
        self.theme = theme
        self.tree_rows = tree_rows
        self.filter_text = filter_text
        self.open = True
        self.box = Surface(parent, theme, bg="bg")

        outer = Surface(self.box.widget, theme, bg="border")
        outer.widget.pack(fill="x")
        bar = Surface(outer.widget, theme, bg="chip")
        bar.widget.pack(fill="x", padx=s(1), pady=s(1))
        self.bar = bar.widget

        IconButton(self.bar, theme, "chevron-up", w=32, h=38, bg="chip").pack(
            side="left", padx=(s(4), s(2)))
        Surface(self.bar, theme, bg="border", width=s(1), height=s(22)).pack(
            side="left", padx=s(4))
        for i, (nm, cur) in enumerate(crumbs):
            if i:
                IconLabel(self.bar, theme, "chevron-right", 12, fg="fg_dim",
                          bg="chip").pack(side="left", padx=s(2))
            self._crumb(nm, cur)

        self.toggle_btn = IconButton(self.bar, theme, "chevron-up", w=26, h=38,
                                     active=True, bg="chip",
                                     command=self._toggle)
        self.toggle_btn.pack(side="left", padx=(s(2), 0))
        Badge(self.bar, theme, count_text, bg="chip").pack(side="right",
                                                           padx=s(8))

        self.drop = Surface(self.box.widget, theme, bg="bg")
        self._render()

    def _crumb(self, name, current):
        lb = Label(self.bar, self.theme, name, fg=("fg" if current else "fg_dim"),
                   bg="chip", size=11, bold=current, cursor="hand2",
                   padx=s(5), pady=s(9))
        lb.widget.pack(side="left")
        if not current:
            w = lb.widget
            w.bind("<Enter>", lambda e: w.configure(fg=self.theme["accent"]))
            w.bind("<Leave>", lambda e: w.configure(fg=self.theme["fg_dim"]))

    def _toggle(self):
        self.open = not self.open
        self.toggle_btn.icon_name = "chevron-up" if self.open else "chevron-down"
        self.toggle_btn.set_active(self.open)
        self._render()

    def _render(self):
        for w in self.drop.widget.winfo_children():
            w.destroy()
        if self.open:
            folder_tree(self.drop.widget, self.theme, self.tree_rows,
                        self.filter_text)
            self.drop.widget.pack(fill="x", pady=(s(6), 0))
        else:
            self.drop.widget.pack_forget()

    def pack(self, **k):
        self.box.pack(**k)
        return self

    def grid(self, **k):
        self.box.grid(**k)
        return self

    def place(self, **k):
        self.box.place(**k)
        return self


def folder_tree(parent, theme, rows, filter_text=None):
    outer = Surface(parent, theme, bg="border")
    outer.widget.pack(fill="x")
    panel = Surface(outer.widget, theme, bg="sidebar")
    panel.widget.pack(fill="x", padx=s(1), pady=s(1))
    p = panel.widget
    if filter_text is not None:
        _tree_filter(p, theme, filter_text)
    else:
        Label(p, theme, "Folders", fg="fg_dim", bg="sidebar", size=8,
              bold=True, anchor="w").pack(fill="x", padx=s(12), pady=(s(8), s(4)))
    for depth, name, kind, current in rows:
        _tree_row(p, theme, depth, name, kind, current)
    Surface(p, theme, bg="sidebar", height=s(8)).pack()
    return panel


def _tree_filter(parent, theme, text):
    box = Surface(parent, theme, bg="sidebar")
    box.widget.pack(fill="x", padx=s(10), pady=(s(8), s(6)))
    outer = Surface(box.widget, theme, bg="border")
    outer.widget.pack(fill="x")
    inner = Surface(outer.widget, theme, bg="bg")
    inner.widget.pack(fill="x", padx=s(1), pady=s(1))
    row = Surface(inner.widget, theme, bg="bg")
    row.widget.pack(fill="x", padx=s(8), pady=s(5))
    IconLabel(row.widget, theme, "search", 14, fg="fg_dim", bg="bg").pack(
        side="left", padx=(0, s(6)))
    Label(row.widget, theme, text, fg="fg_dim", bg="bg", size=9).pack(side="left")


def _tree_row(parent, theme, depth, name, kind, current):
    base = "lift" if current else "sidebar"
    row = Surface(parent, theme, bg=base)
    row.widget.pack(fill="x")
    Surface(row.widget, theme, bg=("accent" if current else base),
            width=s(3)).pack(side="left", fill="y")
    Surface(row.widget, theme, bg=base, width=s(4 + depth * 16)).pack(
        side="left")
    if kind in ("open", "closed"):
        IconLabel(row.widget, theme,
                  "chevron-down" if kind == "open" else "chevron-right",
                  12, fg="fg_dim", bg=base).pack(side="left")
    else:
        Surface(row.widget, theme, bg=base, width=s(12)).pack(side="left")
    IconLabel(row.widget, theme, "folder-open", 16,
              fg=("accent" if current else "fg"), bg=base).pack(side="left",
                                                                padx=(s(2), 0))
    Label(row.widget, theme, name, fg=("accent" if current else "fg"), bg=base,
          size=10, bold=current, cursor="hand2", padx=s(6)).pack(side="left",
                                                                 pady=s(4))


# ----------------------------------------------------------------------------
# Selection — the same frame in every view (list · thumbnails)
# ----------------------------------------------------------------------------
class _Selectable:
    "Common theme handling for the selection demo views."

    def _bind(self, theme, root):
        self.theme = theme
        self.root = root
        theme.subscribe(self._restyle)
        root.bind("<Destroy>", self._destroyed)
        self._restyle()

    def _destroyed(self, e):
        if e.widget is self.root:
            self.theme.unsubscribe(self._restyle)

    def pack(self, **k):
        self.root.pack(**k)
        return self

    def grid(self, **k):
        self.root.grid(**k)
        return self

    def place(self, **k):
        self.root.place(**k)
        return self


class SelectTile(_Selectable):
    "A thumbnail with a selection frame; the caption never recolours."

    def __init__(self, parent, theme, image, name, selected=False, size=120):
        self.selected = selected
        cell = tk.Frame(parent)
        self.cell = cell
        self.holder = tk.Frame(cell, highlightthickness=s(2))
        self.holder.pack(padx=s(4), pady=(s(4), 0))
        self.pic = tk.Label(self.holder, image=image, cursor="hand2")
        self.pic.image = image
        self.pic.pack()
        self.cap = tk.Label(cell, text=name, font=font(7),
                            wraplength=s(size + 8))
        self.cap.pack(pady=(s(2), s(4)))
        self._bind(theme, cell)

    def _restyle(self):
        try:
            t = self.theme
            # selection is the frame alone — an accent border, nothing tinted;
            # the caption never recolours either.
            edge = t["accent"] if self.selected else t["sidebar"]
            self.cell.configure(bg=t["sidebar"])
            self.holder.configure(bg=t["sidebar"], highlightbackground=edge,
                                  highlightcolor=edge)
            self.pic.configure(bg=t["sidebar"])
            self.cap.configure(bg=t["sidebar"], fg=t["fg"])
        except tk.TclError:
            pass


class SelectRow(_Selectable):
    "A list row with the selection frame; the name never recolours."

    def __init__(self, parent, theme, image, name, selected=False):
        self.selected = selected
        cell = tk.Frame(parent)
        self.cell = cell
        self.holder = tk.Frame(cell, highlightthickness=s(2))
        self.holder.pack(fill="x")
        self.pic = tk.Label(self.holder, image=image, cursor="hand2")
        self.pic.image = image
        self.pic.pack(side="left", padx=(s(4), s(8)), pady=s(2))
        self.name = tk.Label(self.holder, text=name, anchor="w", cursor="hand2",
                             font=font(9))
        self.name.pack(side="left", fill="x", expand=True)
        self._bind(theme, cell)

    def _restyle(self):
        try:
            t = self.theme
            # selection is the frame alone — an accent border, name never recolours.
            edge = t["accent"] if self.selected else t["sidebar"]
            for w in (self.cell, self.holder, self.pic, self.name):
                w.configure(bg=t["sidebar"])
            self.holder.configure(highlightbackground=edge, highlightcolor=edge)
            self.name.configure(fg=t["fg"])
        except tk.TclError:
            pass


# ----------------------------------------------------------------------------
# Multi-select list — checkable rows; selected rows tint + name turns accent
# ----------------------------------------------------------------------------
class MultiSelectRow(_Selectable):
    def __init__(self, parent, theme, name, selected=False, command=None):
        self.selected = selected
        self.name_text = name
        self.command = command
        row = tk.Frame(parent)
        self.row = row
        self.stripe = tk.Frame(row, width=s(3))
        self.stripe.pack(side="left", fill="y")
        self.box = tk.Canvas(row, width=s(20), height=s(30),
                             highlightthickness=0, cursor="hand2")
        self.box.pack(side="left", padx=(s(7), 0))
        self.lbl = tk.Label(row, text=name, anchor="w", font=font(9))
        self.lbl.pack(side="left", padx=(s(8), 0), fill="x", expand=True)
        for w in (row, self.box, self.lbl):
            w.bind("<Button-1>", self._click)
        self._bind(theme, row)

    def _click(self, _e):
        self.selected = not self.selected
        self._restyle()
        if self.command:
            self.command(self.selected)

    def _restyle(self):
        try:
            t = self.theme
            base = t["lift"] if self.selected else t["sidebar"]
            self.row.configure(bg=base)
            self.lbl.configure(bg=base,
                               fg=t["accent"] if self.selected else t["fg"],
                               font=font(9, self.selected))
            self.stripe.configure(bg=t["accent"] if self.selected else base)
            self.box.configure(bg=base)
            self.box.delete("all")
            if self.selected:
                rounded_rect(self.box, s(3), s(8), s(17), s(22), s(3),
                             fill=t["accent"])
                put_icon(self.box, s(10), s(15),
                         icons.load("check", 12, t["on_accent"]))
            else:
                rounded_rect(self.box, s(3), s(8), s(17), s(22), s(3), fill=base,
                             outline=t["ring"], width=s(2))
        except tk.TclError:
            pass


def multiselect_list(parent, theme, rows, width=240):
    "rows: list of (name, selected). Returns the bordered panel Surface."
    holder = Surface(parent, theme, bg="border")
    panel = Surface(holder.widget, theme, bg="sidebar")
    panel.widget.pack(padx=s(1), pady=s(1))
    Surface(panel.widget, theme, bg="sidebar", width=s(width), height=s(1)).pack()
    for name, sel in rows:
        MultiSelectRow(panel.widget, theme, name, selected=sel).pack(fill="x")
    Surface(panel.widget, theme, bg="sidebar", height=s(6)).pack()
    return holder


# ----------------------------------------------------------------------------
# Settings window — a left tab rail + a swappable pane (kit-built)
# ----------------------------------------------------------------------------
class SettingsWindow:
    TABS = ["General", "Export", "Culling", "About"]

    def __init__(self, parent, theme, width=560, height=400):
        self.theme = theme
        self.active = 0
        self._tabs = []
        card = Card(theme=theme, parent=parent, pad=0, bg="panel", width=s(width))
        self.card = card
        body = card.body
        body.configure(height=s(height))
        body.pack_propagate(False)
        rail = Surface(body, theme, bg="sidebar")
        rail.widget.pack(side="left", fill="y")
        rail.widget.configure(width=s(140))
        rail.widget.pack_propagate(False)
        Label(rail.widget, theme, "  SETTINGS", fg="fg_dim", bg="sidebar",
              size=8, bold=True, anchor="w").pack(fill="x", pady=(s(16), s(8)))
        for i, name in enumerate(self.TABS):
            self._tab(rail.widget, i, name)
        self.pane = Surface(body, theme, bg="panel")
        self.pane.widget.pack(side="left", fill="both", expand=True,
                              padx=s(20), pady=s(16))
        self._show(0)

    def _tab(self, parent, i, name):
        row = Surface(parent, self.theme, bg="sidebar")
        row.widget.pack(fill="x")
        stripe = Surface(row.widget, self.theme, bg="sidebar", width=s(3))
        stripe.widget.pack(side="left", fill="y")
        lbl = Label(row.widget, self.theme, name, fg="fg_dim", bg="sidebar",
                    size=10, cursor="hand2", anchor="w", padx=s(12), pady=s(8))
        lbl.widget.pack(side="left", fill="x", expand=True)
        self._tabs.append((stripe, lbl))
        for w in (row.widget, lbl.widget):
            w.bind("<Button-1>", lambda e, idx=i: self._show(idx))

    def _show(self, i):
        self.active = i
        for j, (stripe, lbl) in enumerate(self._tabs):
            on = (j == i)
            stripe._bg = "accent" if on else "sidebar"
            stripe._restyle()
            lbl._fg = "accent" if on else "fg_dim"
            lbl.widget.configure(font=font(10, on))
            lbl._restyle()
        for w in self.pane.widget.winfo_children():
            w.destroy()
        [self._general, self._export, self._culling, self._about][i]()

    # -- panes -------------------------------------------------------------
    def _row(self, label, control_factory):
        r = Surface(self.pane.widget, self.theme, bg="panel")
        r.widget.pack(fill="x", pady=s(6))
        Label(r.widget, self.theme, label, fg="fg", bg="panel", size=10).pack(
            side="left")
        control_factory(r.widget).pack(side="right")

    def _general(self):
        SectionHeader(self.pane.widget, self.theme, "General", bg="panel").pack(
            fill="x")
        self._row("Dark theme", lambda p: Toggle(p, self.theme, value=True,
                                                 bg="panel"))
        self._row("Confirm before delete",
                  lambda p: Toggle(p, self.theme, value=True, bg="panel"))
        self._row("Thumbnail size",
                  lambda p: Dropdown(p, self.theme, ["Small", "Medium", "Large"],
                                     selected=2, bg="panel"))

    def _export(self):
        SectionHeader(self.pane.widget, self.theme, "Export", bg="panel").pack(
            fill="x")
        self._row("Format", lambda p: SegmentedTabs(p, self.theme,
                                                    ["JPG", "PNG", "TIFF"],
                                                    bg="panel"))
        Slider(self.pane.widget, self.theme, "Quality", value=85, lo=0, hi=100,
               neutral=0, bg="panel").pack(fill="x", pady=(s(8), 0))
        self._row("Convert to sRGB",
                  lambda p: Toggle(p, self.theme, value=True, bg="panel"))

    def _culling(self):
        SectionHeader(self.pane.widget, self.theme, "Culling", bg="panel").pack(
            fill="x")
        self._row("Keep on right arrow",
                  lambda p: Toggle(p, self.theme, value=False, bg="panel"))
        self._row("Reject folder name",
                  lambda p: Dropdown(p, self.theme, ["Rejected", "Trash",
                                                    "_cull"], bg="panel"))

    def _about(self):
        SectionHeader(self.pane.widget, self.theme, "About", bg="panel").pack(
            fill="x")
        Label(self.pane.widget, self.theme, "TintKit — a themeable Tkinter "
              "UI kit.", fg="fg_dim", bg="panel", size=10,
              justify="left").pack(anchor="w", pady=(s(4), s(12)))
        Button(self.pane.widget, self.theme, "Check for updates",
               role="neutral", variant="outline", bg="panel").pack(anchor="w")

    def pack(self, **k):
        self.card.pack(**k)
        return self

    def grid(self, **k):
        self.card.grid(**k)
        return self

    def place(self, **k):
        self.card.place(**k)
        return self
