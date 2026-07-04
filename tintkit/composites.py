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
from .containers import Card, SectionHeader, themed_scrollbar


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
    IconLabel(row.widget, theme, "folder-open", 14,
              fg=("accent" if current else "fg"), bg=base).pack(side="left",
                                                                padx=(s(2), 0))
    Label(row.widget, theme, name, fg=("accent" if current else "fg"), bg=base,
          size=10, bold=current, cursor="hand2", padx=s(6)).pack(side="left",
                                                                 pady=0)


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
        self.pic.pack(side="left", padx=(s(4), s(8)), pady=0)
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
# Settings window — a left tab rail + a swappable, scrollable content pane
# ----------------------------------------------------------------------------
class SettingsWindow:
    """A left tab-rail beside a swappable, scrollable content pane.

    App-agnostic chrome. You supply the ``tabs`` and one *builder* per tab; the
    kit draws the rail (accent active row, optional icon), scrolls the pane, and
    hands each builder this object so it can lay content out with :meth:`group`
    / :meth:`row` / :meth:`note` and re-run itself with :meth:`rebuild`. It owns
    no window of its own — pack/grid/place ``.root`` into a :class:`Card` (a
    gallery) or a ``Toplevel`` body (an app); the header/footer, if any, belong
    to the host.

        def general(win):
            win.group("Language")
            Dropdown(win.row("Interface language"), theme, langs).pack()

        SettingsWindow(parent, theme, tabs=[
            ("general", "General", "settings", general), ...],
        ).pack(fill="both", expand=True)

    Parameters
    ----------
    tabs        list of ``(key, label, icon_or_None, builder)``. ``builder`` is
                called with this SettingsWindow whenever its tab is shown; it
                fills ``win.body`` (usually via :meth:`group` / :meth:`row`).
    icon_loader ``(name, px, colour) -> image | None`` for the rail glyphs,
                given a *logical* px size (it DPI-scales itself). Defaults to the
                kit's own :func:`icons.load`; pass the app's loader to draw from
                its icon set. Ignored for text-only tabs (``icon`` is ``None``).
    rail_bg /   theme tokens for the rail and content backgrounds (a gallery
    pane_bg     shows it on a ``"panel"`` card, an app on the window ``"bg"``).
    header      a small caption above the tabs, or ``None`` for none.
    width /     fixed size in logical px; omit either to fill the parent on that
    height      axis (an app in a resizable window passes neither).
    """

    def __init__(self, parent, theme, tabs, width=None, height=None,
                 rail_w=150, header="SETTINGS", icon_loader=None,
                 rail_bg="sidebar", pane_bg="bg"):
        self.theme = theme
        self.tabs = tabs
        self.active = tabs[0][0]
        self._icon = icon_loader or icons.load
        self._rail_bg, self._pane_bg = rail_bg, pane_bg
        self._rows = {}                      # key -> (row, stripe, ic, lbl, name)
        self.body = None

        root = tk.Frame(parent, bg=theme[pane_bg])
        self.root = root
        if width:
            root.configure(width=s(width))
        if height:
            root.configure(height=s(height))
        if width or height:
            root.pack_propagate(False)

        # LEFT — the tab rail.
        rail = tk.Frame(root, bg=theme[rail_bg], width=s(rail_w))
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        self._rail = rail
        self._header = None
        if header:
            self._header = tk.Label(rail, text="  " + header, anchor="w",
                                    bg=theme[rail_bg], fg=theme["fg_dim"],
                                    font=font(8, True))
            self._header.pack(fill="x", pady=(s(16), s(8)))
        else:
            tk.Frame(rail, bg=theme[rail_bg], height=s(8)).pack(fill="x")
        for key, label, icon, _b in tabs:
            self._make_row(rail, key, label, icon)

        self._divider = tk.Frame(root, width=s(1), bg=theme["border"])
        self._divider.pack(side="left", fill="y")

        # RIGHT — a scrollable content pane.
        right = tk.Frame(root, bg=theme[pane_bg])
        right.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(right, highlightthickness=0, bg=theme[pane_bg])
        sb = themed_scrollbar(right, theme, self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.pane = tk.Frame(self.canvas, bg=theme[pane_bg])
        self._win = self.canvas.create_window((0, 0), window=self.pane,
                                              anchor="nw")
        self.pane.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._win, width=e.width))
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(
            int(-e.delta / 120), "units"))

        theme.subscribe(self._paint)
        root.bind("<Destroy>", self._destroyed)
        self.show(self.active)

    # -- rail ---------------------------------------------------------------
    def _make_row(self, parent, key, label, name):
        side = self.theme[self._rail_bg]
        row = tk.Frame(parent, bg=side, cursor="hand2")
        row.pack(fill="x")
        stripe = tk.Frame(row, bg=side, width=s(3))
        stripe.pack(side="left", fill="y")
        ic = None
        if name:
            ic = tk.Label(row, bg=side)
            ic.pack(side="left", padx=(s(12), s(9)), pady=s(9))
            lbl = tk.Label(row, text=label, bg=side, fg=self.theme["fg_dim"],
                           anchor="w", font=font(10))
            lbl.pack(side="left", fill="x", expand=True)
        else:
            lbl = tk.Label(row, text=label, bg=side, fg=self.theme["fg_dim"],
                           anchor="w", font=font(10), padx=s(14), pady=s(9))
            lbl.pack(side="left", fill="x", expand=True)
        self._rows[key] = (row, stripe, ic, lbl, name)
        for w in [row, stripe, lbl] + ([ic] if ic else []):
            w.bind("<Button-1>", lambda e, k=key: self.show(k))
            w.bind("<Enter>", lambda e, k=key: self._hover(k, True))
            w.bind("<Leave>", lambda e, k=key: self._hover(k, False))

    def _hover(self, key, on):
        if key == self.active:
            return
        row, stripe, ic, lbl, _n = self._rows[key]
        bg = self.theme["hover"] if on else self.theme[self._rail_bg]
        for w in [row, stripe, lbl] + ([ic] if ic else []):
            w.configure(bg=bg)

    def _paint(self):
        "Repaint the rail + chrome for the active tab / theme (a live subscriber)."
        try:
            side, pane = self.theme[self._rail_bg], self.theme[self._pane_bg]
            self.root.configure(bg=pane)
            self._rail.configure(bg=side)
            self._divider.configure(bg=self.theme["border"])
            self.canvas.configure(bg=pane)
            self.pane.configure(bg=pane)
            if self._header is not None:
                self._header.configure(bg=side, fg=self.theme["fg_dim"])
            for key, (row, stripe, ic, lbl, name) in self._rows.items():
                on = (key == self.active)
                col = self.theme["accent"] if on else self.theme["fg_dim"]
                for w in [row, lbl] + ([ic] if ic else []):
                    w.configure(bg=side)
                stripe.configure(bg=self.theme["accent"] if on else side)
                lbl.configure(fg=col, font=font(10, on))
                if ic is not None:
                    img = self._icon(name, 17, col)
                    if img is not None:
                        ic.configure(image=img)
                        ic.image = img               # keep a hard ref alive
        except tk.TclError:
            pass

    def _destroyed(self, e):
        if e.widget is self.root:
            self.theme.unsubscribe(self._paint)

    # -- content ------------------------------------------------------------
    def show(self, key):
        "Switch to tab ``key``: repaint the rail, rebuild the pane, scroll to top."
        self.active = key
        self._paint()
        for w in self.pane.winfo_children():
            w.destroy()
        self.body = Surface(self.pane, self.theme, bg=self._pane_bg)
        self.body.widget.pack(fill="both", expand=True,
                              padx=s(22), pady=(s(4), s(20)))
        builder = next(b for k, _l, _i, b in self.tabs if k == key)
        builder(self)
        self.canvas.yview_moveto(0.0)

    def rebuild(self):
        "Re-run the active tab's builder (e.g. after a control changes layout)."
        self.show(self.active)

    # -- content helpers (used by the tab builders) -------------------------
    def group(self, title):
        "A section header (accent tick + title + rule) titling a block."
        return SectionHeader(self.body.widget, self.theme, title,
                             bg=self._pane_bg).pack(fill="x", pady=(s(18), s(2)))

    def row(self, title, desc=None):
        "One setting line — title (+ optional description) left, controls right."
        " Returns the right-hand frame; pack the control(s) into it."
        r = Surface(self.body.widget, self.theme, bg=self._pane_bg)
        r.widget.pack(fill="x", pady=s(6))
        left = Surface(r.widget, self.theme, bg=self._pane_bg)
        left.widget.pack(side="left", fill="x", expand=True)
        Label(left.widget, self.theme, title, fg="fg", bg=self._pane_bg,
              size=10, anchor="w").pack(anchor="w")
        if desc:
            Label(left.widget, self.theme, desc, fg="fg_dim", bg=self._pane_bg,
                  size=8, anchor="w", justify="left",
                  wraplength=s(330)).pack(anchor="w", pady=(s(2), 0))
        right = Surface(r.widget, self.theme, bg=self._pane_bg)
        right.widget.pack(side="right", padx=(s(16), 0))
        return right.widget

    def note(self, text):
        "A small dim explanatory line under a block."
        return Label(self.body.widget, self.theme, text, fg="fg_dim",
                     bg=self._pane_bg, size=8, anchor="w", justify="left",
                     wraplength=s(440)).pack(fill="x", pady=(s(10), 0))

    def pack(self, **k):
        self.root.pack(**k)
        return self

    def grid(self, **k):
        self.root.grid(**k)
        return self

    def place(self, **k):
        self.root.place(**k)
        return self
