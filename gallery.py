"""TintKit — the gallery / living style guide.

Every component in the kit rendered together in one scrollable window, with a
live theme switcher at the top: flip Dark/Light and pick an accent — the whole
window repaints instantly. This is the proof that the kit is one coherent,
themeable system, and a worked example of how to use each widget.

    python gallery.py

Needs Pillow for the icons + mock thumbnails (``pip install pillow``); without
it the window still runs, just without those images.
"""

import os
import sys
import tkinter as tk
import tkinter.ttk as ttk

from tintkit import (
    Theme, setup_dpi, icons, mix, s,
    Surface, Label, IconLabel, Dot, font,
    Button, IconButton, Slider, TitledSlider, Toggle, RadioGroup, Checkbox,
    SegmentedTabs, Badge, Tag, ProgressBar, Tooltip, HoverTip, TextField,
    TextArea, Dropdown, MultiDropdown,
    Card, Foldout, SectionHeader, hero_line, callout, dialog, v_sash, h_sash,
    themed_scrollbar,
    toolbar, tool_rail, FolderNav, FolderTree, SelectTile, SelectRow,
    multiselect_list, SettingsWindow, CanvasControl, rounded_rect,
)

try:
    from PIL import Image, ImageDraw, ImageTk
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

# accent presets offered by the switcher
ACCENTS = [
    ("Sage", "#8fae9b"), ("Terracotta", "#c08457"), ("Ocean", "#5b8ec9"),
    ("Violet", "#9b7fc0"), ("Gold", "#c9a24a"), ("Rose", "#c87f96"),
]

PALETTES = [
    ((46, 74, 120), (180, 205, 230), "sun", (245, 230, 180)),
    ((120, 72, 58), (235, 205, 165), "hill", (90, 60, 45)),
    ((40, 86, 64), (205, 228, 185), "hill", (60, 95, 70)),
    ((92, 64, 104), (224, 205, 232), "sun", (250, 240, 200)),
    ((110, 96, 44), (232, 222, 170), "sun", (250, 245, 210)),
    ((52, 92, 112), (200, 226, 236), "hill", (45, 70, 85)),
]
_REFS = []


def mock_photo(i, size):
    "A fake thumbnail so the selection views have something to frame."
    if not HAVE_PIL:
        return None
    size = round(size * icons.DPI)
    top, bot, shape, scol = PALETTES[i % len(PALETTES)]
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        f = y / (size - 1)
        d.line([(0, y), (size, y)],
               fill=tuple(int(top[k] + (bot[k] - top[k]) * f) for k in range(3)))
    if shape == "sun":
        d.ellipse([size * .58, size * .12, size * .84, size * .38], fill=scol)
    else:
        d.polygon([(0, size), (size * .42, size * .5), (size * .8, size),
                   (0, size)], fill=scol)
    ph = ImageTk.PhotoImage(img)
    _REFS.append(ph)
    return ph


# ----------------------------------------------------------------------------
# small page helpers
# ----------------------------------------------------------------------------
def caption(parent, theme, text, bg="bg"):
    return Label(parent, theme, text, fg="fg_dim", bg=bg, size=8, anchor="w",
                 justify="left")


def labelled(parent, theme, text, control, bg="bg"):
    "A control with a trailing label (toggle / radio rows)."
    row = Surface(parent, theme, bg=bg)
    control(row.widget).pack(side="left")
    Label(row.widget, theme, text, fg="fg", bg=bg, size=9).pack(side="left",
                                                                padx=8)
    return row


# ----------------------------------------------------------------------------
# the live theme switcher
# ----------------------------------------------------------------------------
class Swatch(CanvasControl):
    "A clickable accent colour chip; rings itself when it's the active accent."

    def __init__(self, parent, theme, color, command):
        self.color = color
        self.command = command
        super().__init__(parent, theme, 24, 24, bg="bg")
        self.canvas.bind("<Button-1>", lambda e: self.command(self.color))

    def draw(self):
        c, t = self.canvas, self.theme
        active = (t.accent.lower() == self.color.lower())
        rounded_rect(c, 3, 3, 21, 21, t["r_control"], fill=self.color,
                     outline=t["fg"] if active else t["border"],
                     width=2 if active else 1)
        if self._hover and not active:
            rounded_rect(c, 1, 1, 23, 23, t["r_control"] + 2, outline=t["ring"],
                         width=1)


def theme_bar(parent, theme):
    bar = Surface(parent, theme, bg="bg")
    Label(bar.widget, theme, "Theme", fg="fg_dim", bg="bg", size=9).pack(
        side="left", padx=(0, 10))
    SegmentedTabs(bar.widget, theme, ["Dark", "Light"],
                  selected=0 if theme.scheme == "dark" else 1,
                  command=lambda i, _l: theme.set(
                      scheme="dark" if i == 0 else "light"),
                  bg="bg").pack(side="left", padx=(0, 24))
    Label(bar.widget, theme, "Accent", fg="fg_dim", bg="bg", size=9).pack(
        side="left", padx=(0, 8))
    for _name, col in ACCENTS:
        Swatch(bar.widget, theme, col,
               command=lambda c: theme.set(accent=c)).pack(side="left", padx=2)
    return bar


# ----------------------------------------------------------------------------
# sections
# ----------------------------------------------------------------------------
def build_elements(parent, theme):
    grid = Surface(parent, theme, bg="bg")
    grid.widget.grid_columnconfigure(0, weight=1, uniform="e")
    grid.widget.grid_columnconfigure(1, weight=1, uniform="e")
    g = grid.widget

    items = [
        ("Section header",
         lambda p: SectionHeader(p, theme, "Basic Edits")),
        ("Primary button",
         lambda p: Button(p, theme, "Save", role="primary", icon="save")),
        ("Chips (active + normal)",
         lambda p: _chips(p, theme)),
        ("Full-width button",
         lambda p: Button(p, theme, "Clear all", role="neutral",
                          icon="rotate-ccw", stretch=True, h=40)),
        ("Icon buttons", lambda p: _icon_buttons(p, theme)),
        ("Slider", lambda p: Slider(p, theme, "Exposure", value=134)),
        ("Slider with colour",
         lambda p: Slider(p, theme, "Red", value=72, chip="#c98b80")),
        ("Toolbar",
         lambda p: toolbar(p, theme, ["folder-open", "save", "info", "undo",
                                      "redo", "menu"], bg="bg")),
        ("Tool rail",
         lambda p: tool_rail(p, theme, [("sliders-horizontal", "Basic"),
                                        ("crop", "Crop"),
                                        ("droplets", "Colors")], bg="bg")),
        ("Tabs (segmented)",
         lambda p: SegmentedTabs(p, theme, ["Large", "Medium", "List"])),
        ("Toggle", lambda p: _toggles(p, theme)),
        ("Radio", lambda p: _radios(p, theme)),
        ("Checkbox", lambda p: _checks(p, theme)),
        ("Dropdown",
         lambda p: Dropdown(p, theme, [("Large icons", "layout-grid"),
                                       ("Medium icons", "layout-grid"),
                                       ("List", "menu")])),
        ("Badge / counter", lambda p: _badges(p, theme)),
        ("Tags (status)", lambda p: _tags(p, theme)),
        ("Progress bar", lambda p: ProgressBar(p, theme, 0.62)),
        ("Text field", lambda p: TextField(p, theme, "File name")),
        ("Text area (multi-line)",
         lambda p: TextArea(p, theme, "Shot on a grey morning by the lake.\n"
                            "Lifted the shadows, cooled the highlights.\n"
                            "Warmed the midtones a touch, then pulled the\n"
                            "clarity back so the water stayed soft.\n"
                            "Grab the handle on the right to scroll.",
                            height=3)),
        ("Tooltip", lambda p: Tooltip(p, theme, "Hand tool — drag to pan")),
        ("Hover tip — hover the buttons", lambda p: _hovertips(p, theme)),
        ("Icon label", lambda p: _icon_labels(p, theme)),
        ("Status dots — a fixed grade, not a token",
         lambda p: _dots(p, theme)),
    ]
    for i, (cap, builder) in enumerate(items):
        cell = Surface(g, theme, bg="bg")
        cell.widget.grid(row=i // 2, column=i % 2, sticky="new", padx=(0, s(26)),
                         pady=(0, s(16)))
        caption(cell.widget, theme, cap).pack(anchor="w", pady=(0, s(5)))
        holder = Surface(cell.widget, theme, bg="bg")
        holder.widget.pack(anchor="w", fill="x")
        builder(holder.widget).pack(anchor="w", fill="x")
    return grid


def _chips(p, theme):
    row = Surface(p, theme, bg="bg")
    Button(row.widget, theme, "Auto level", role="primary").pack(
        side="left", padx=(0, 6))
    Button(row.widget, theme, "Auto contrast", role="neutral").pack(side="left")
    return row


def _toggles(p, theme):
    box = Surface(p, theme, bg="bg")
    labelled(box.widget, theme, "Aligned",
             lambda q: Toggle(q, theme, value=True)).pack(anchor="w", pady=2)
    labelled(box.widget, theme, "Mirror",
             lambda q: Toggle(q, theme, value=False)).pack(anchor="w", pady=2)
    return box


def _radios(p, theme):
    g = RadioGroup(theme)
    row = Surface(p, theme, bg="bg")
    g.add(row.widget, "On", "on", selected=True).pack(side="left", padx=(0, 16))
    g.add(row.widget, "Off", "off").pack(side="left", padx=(0, 16))
    return row


def _checks(p, theme):
    row = Surface(p, theme, bg="bg")
    Checkbox(row.widget, theme, "On", "on").pack(side="left", padx=(0, 16))
    Checkbox(row.widget, theme, "Off", "off").pack(side="left", padx=(0, 16))
    Checkbox(row.widget, theme, "Mixed", "mixed").pack(side="left", padx=(0, 16))
    return row


def _icon_buttons(p, theme):
    row = Surface(p, theme, bg="bg")
    for icon, active in [("undo", False), ("redo", False), ("crop", True),
                         ("info", False)]:
        IconButton(row.widget, theme, icon, active=active, bg="bg").pack(
            side="left", padx=(0, 6))
    # captioned rail tile — the same control with label=
    IconButton(row.widget, theme, "droplets", w=46, h=44, label="Colors",
               bg="bg").pack(side="left", padx=(12, 0))
    return row


def _hovertips(p, theme):
    row = Surface(p, theme, bg="bg")
    save = Button(row.widget, theme, "Save", role="primary", icon="save")
    save.pack(side="left", padx=(0, 8))
    HoverTip(save.canvas, theme, "Save (Ctrl+S)")
    note = Button(row.widget, theme, "Export", role="neutral", icon="folder-open")
    note.pack(side="left")
    HoverTip(note.canvas, theme, "Writes a copy beside the original; the "
             "negative is never touched.", wrap=180)
    return row


def _icon_labels(p, theme):
    row = Surface(p, theme, bg="bg")
    for name in ("crop", "droplets", "sliders-horizontal", "star", "info"):
        IconLabel(row.widget, theme, name, 16, fg="fg_dim", bg="bg").pack(
            side="left", padx=(0, 12))
    IconLabel(row.widget, theme, "star", 16, fg="accent", bg="bg").pack(
        side="left")
    return row


# A grade means the same in dark and light, so these are fixed hex, not tokens.
GRADES = [("#5f9e6a", "Cheap — recomputed instantly"),
          ("#c9a24a", "Moderate — taxes later edits"),
          ("#c0574e", "Costly — forces a full re-render")]


def _dots(p, theme):
    row = Surface(p, theme, bg="bg")
    for color, tip in GRADES:
        d = Dot(row.widget, theme, color, bg="bg")
        d.pack(side="left", padx=(0, 6))
        HoverTip(d.widget, theme, tip, wrap=160)
        Label(row.widget, theme, tip.split(" — ")[0], fg="fg_dim", bg="bg",
              size=9).pack(side="left", padx=(0, 16))
    return row


def _badges(p, theme):
    row = Surface(p, theme, bg="bg")
    Badge(row.widget, theme, "12 / 248").pack(side="left", padx=(0, 8))
    Badge(row.widget, theme, "Keeper", "accent").pack(side="left")
    return row


def _tags(p, theme):
    row = Surface(p, theme, bg="bg")
    Tag(row.widget, theme, "Keeper", "accent").pack(side="left", padx=(0, 6))
    Tag(row.widget, theme, "Reject", "danger").pack(side="left", padx=(0, 6))
    Tag(row.widget, theme, "Maybe", "warn").pack(side="left", padx=(0, 6))
    Tag(row.widget, theme, "RAW", "neutral").pack(side="left")
    return row


def build_titled_sliders(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "The title sits on its own strip, so a dense "
            "stack never overlaps its tracks. Drag one — the value tracks it; "
            "the reset icon appears once it leaves neutral.").pack(
                anchor="w", pady=(0, 12))
    grid = Surface(box.widget, theme, bg="bg")
    grid.widget.pack(fill="x")
    for i in (0, 1):
        grid.widget.grid_columnconfigure(i, weight=1, uniform="ts")

    # left: the roomy default, graded with a dot column
    left = Surface(grid.widget, theme, bg="bg")
    left.widget.grid(row=0, column=0, sticky="new", padx=(0, s(26)))
    caption(left.widget, theme, "Default — dot column shared by every row").pack(
        anchor="w", pady=(0, s(6)))
    rows = [("Exposure", 132, None, GRADES[0][0]),
            ("Contrast", 100, None, None),
            ("Clarity", 118, None, GRADES[1][0]),
            ("Dehaze", 100, None, GRADES[2][0])]
    for label, val, chip, dot in rows:
        ts = TitledSlider(left.widget, theme, label, value=val, chip=chip,
                          dot=dot, dot_slot=True,
                          dot_tip=next((t for c, t in GRADES if c == dot), ""),
                          on_reset=lambda: None)
        ts.pack(fill="x", pady=(0, s(8)))
        _REFS.append(ts)

    # right: compact rows + a colour chip
    right = Surface(grid.widget, theme, bg="bg")
    right.widget.grid(row=0, column=1, sticky="new")
    caption(right.widget, theme, "compact=True — a denser strip for long "
            "stacks of minor sliders").pack(anchor="w", pady=(0, s(6)))
    for label, chip in [("Red", "#c98b80"), ("Green", "#8fae9b"),
                        ("Blue", "#7f9dc0"), ("Gold", "#c9a24a")]:
        ts = TitledSlider(right.widget, theme, label, value=100, chip=chip,
                          compact=True, on_reset=lambda: None)
        ts.pack(fill="x", pady=(0, s(4)))
        _REFS.append(ts)
    return box


def build_foldouts(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "A bordered group that folds — the chevron and "
            "caption live inside the border, and the box grows around whatever "
            "you stack in .body. Click a header.").pack(anchor="w",
                                                        pady=(0, 12))
    grid = Surface(box.widget, theme, bg="bg")
    grid.widget.pack(fill="x")
    for i in (0, 1, 2):
        grid.widget.grid_columnconfigure(i, weight=1, uniform="fo")

    # open, holding real controls
    fo = Foldout(grid.widget, theme, "LIGHT", open=True, bg="bg")
    fo.box.grid(row=0, column=0, sticky="new", padx=(0, s(14)))
    for label in ("Exposure", "Contrast", "Shadows"):
        TitledSlider(fo.body, theme, label, value=100, bg="bg", compact=True,
                     on_reset=lambda: None).pack(fill="x", pady=(0, s(4)))

    # graded, closed
    fo2 = Foldout(grid.widget, theme, "DETAIL", open=False, bg="bg",
                  dot=GRADES[2][0], dot_tip=GRADES[2][1])
    fo2.box.grid(row=0, column=1, sticky="new", padx=(0, s(14)))
    for label in ("Sharpen", "Noise"):
        TitledSlider(fo2.body, theme, label, value=100, bg="bg", compact=True,
                     on_reset=lambda: None).pack(fill="x", pady=(0, s(4)))

    # ungraded but holding the dot column, so the captions line up with fo2
    fo3 = Foldout(grid.widget, theme, "EFFECTS", open=False, bg="bg",
                  dot_slot=True)
    fo3.box.grid(row=0, column=2, sticky="new")
    Checkbox(fo3.body, theme, "Film grain", "on").pack(anchor="w", pady=s(3))
    Checkbox(fo3.body, theme, "Vignette", "off").pack(anchor="w", pady=s(3))
    _REFS.extend([fo, fo2, fo3])
    return box


def build_folder_tree(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "The tree body on its own — no crumbs, no count. "
            "The filter box is persistent: typing rebuilds only the rows, so it "
            "never loses focus.").pack(anchor="w", pady=(0, 12))
    grid = Surface(box.widget, theme, bg="bg")
    grid.widget.pack(fill="x")
    grid.widget.grid_columnconfigure(0, weight=1, uniform="ft")
    grid.widget.grid_columnconfigure(1, weight=1, uniform="ft")

    KIDS = {"Pictures": ["2024", "2025", "Scans"], "2024": ["Wedding", "Trip"],
            "2025": ["Studio"]}
    PARENT = {c: p for p, cs in KIDS.items() for c in cs}
    state = {"expanded": {"Pictures", "2024"}, "current": "Wedding",
             "filter": ""}

    def rows():
        out = []

        def walk(name, depth):
            kids = KIDS.get(name, [])
            kind = ("open" if name in state["expanded"] else "closed") if kids \
                else "leaf"
            flt = state["filter"]
            if not flt or flt in name.lower():
                out.append((depth, name, kind, name == state["current"], name))
            if kids and (name in state["expanded"] or flt):
                for k in kids:
                    walk(k, depth + 1)

        walk("Pictures", 0)
        return out

    def on_row(name):
        state["current"] = name
        state["expanded"].add(name)
        tree.set_rows(rows())

    def on_toggle(name):
        state["expanded"].symmetric_difference_update({name})
        tree.set_rows(rows())

    def on_filter(text):
        state["filter"] = text.lower().strip()
        tree.set_rows(rows())

    # with a live filter box
    left = Surface(grid.widget, theme, bg="bg")
    left.widget.grid(row=0, column=0, sticky="new", padx=(0, s(26)))
    caption(left.widget, theme, "filter_text= — a live search row").pack(
        anchor="w", pady=(0, s(6)))
    tree = FolderTree(left.widget, theme, filter_text="Filter folders",
                      on_row=on_row, on_toggle=on_toggle, on_filter=on_filter)
    tree.set_rows(rows())
    tree.pack(fill="x")

    # without one — a plain 'Folders' caption instead
    right = Surface(grid.widget, theme, bg="bg")
    right.widget.grid(row=0, column=1, sticky="new")
    caption(right.widget, theme, "filter_text=None — a plain caption").pack(
        anchor="w", pady=(0, s(6)))
    plain = FolderTree(right.widget, theme)
    plain.set_rows([(0, "Pictures", "open", False, "Pictures"),
                    (1, "2024", "closed", False, "2024"),
                    (1, "2025", "closed", True, "2025"),
                    (1, "Scans", "leaf", False, "Scans")])
    plain.pack(fill="x")
    _REFS.extend([tree, plain])
    return box


def build_nav(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "Folder navigation — click a folder to open · "
            "▸ expands · ↑ goes up · type to filter.").pack(anchor="w",
                                                            pady=(0, 10))

    # A tiny in-memory tree so the demo genuinely navigates, expands and filters.
    KIDS = {"Home": ["Photos", "Documents"], "Photos": ["2023", "2024"],
            "2024": ["Wedding", "Trip"]}
    PARENT = {c: p for p, cs in KIDS.items() for c in cs}
    state = {"expanded": {"Home", "Photos", "2024"}, "current": "2024",
             "filter": ""}

    def rows():
        out = []

        def walk(name, depth):
            kids = KIDS.get(name, [])
            kind = ("open" if name in state["expanded"] else "closed") if kids \
                else "leaf"
            flt = state["filter"]
            if not flt or flt in name.lower():
                out.append((depth, name, kind, name == state["current"], name))
            if kids and (name in state["expanded"] or flt):
                for k in kids:
                    walk(k, depth + 1)

        walk("Home", 0)
        return out

    def crumbs():
        chain, n = [], state["current"]
        while n is not None:
            chain.append(n)
            n = PARENT.get(n)
        chain.reverse()
        return [(nm, nm, nm == state["current"]) for nm in chain]

    def count():
        return f"{len(KIDS.get(state['current'], []))} folders"

    def open_folder(name):
        state["current"] = name
        state["expanded"].add(name)
        nav.update(crumbs=crumbs(), tree_rows=rows(), count_text=count())

    def toggle(name):
        state["expanded"].symmetric_difference_update({name})
        nav.update(tree_rows=rows())

    def go_up():
        p = PARENT.get(state["current"])
        if p is not None:
            open_folder(p)

    def do_filter(text):
        state["filter"] = text.lower().strip()
        nav.update(tree_rows=rows())     # crumbs untouched → filter box keeps focus

    nav = FolderNav(box.widget, theme, crumbs(), rows(), count(),
                    on_up=go_up, on_crumb=open_folder, on_row=open_folder,
                    on_toggle=toggle, on_filter=do_filter)
    nav.pack(fill="x")
    return box


def build_selection(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "One selection frame in every view mode — switch "
            "the view; the 2nd photo stays picked. The name never recolours.").pack(
                anchor="w", pady=(0, 10))

    bar = Surface(box.widget, theme, bg="bg")
    bar.widget.pack(anchor="w", pady=(0, 10))

    stage = Surface(box.widget, theme, bg="sidebar")
    stage.widget.pack(anchor="w")
    pad = Surface(stage.widget, theme, bg="sidebar")
    pad.widget.pack(padx=s(8), pady=s(8))

    def show(mode):
        for w in pad.widget.winfo_children():
            w.destroy()
        if mode == 0:                                   # list rows
            col = Surface(pad.widget, theme, bg="sidebar")
            col.widget.pack()
            Surface(col.widget, theme, bg="sidebar", width=s(250),
                    height=s(1)).pack()
            for k, nm in enumerate(["IMG_0421.jpg", "IMG_0422.jpg",
                                    "IMG_0423.jpg", "IMG_0424.jpg"]):
                SelectRow(col.widget, theme, mock_photo(k, 16), nm,
                          selected=(k == 1)).pack(fill="x", pady=0)
        elif mode == 1:                                 # small thumbnails
            grid = Surface(pad.widget, theme, bg="sidebar")
            grid.widget.pack()
            for k in range(6):
                SelectTile(grid.widget, theme, mock_photo(k, 38),
                           f"IMG_{421+k}", selected=(k == 1), size=38).grid(
                    row=k // 3, column=k % 3, padx=s(3), pady=s(3))
        else:                                           # large thumbnails
            grid = Surface(pad.widget, theme, bg="sidebar")
            grid.widget.pack()
            for k in range(4):
                SelectTile(grid.widget, theme, mock_photo(k, 66),
                           f"IMG_{421+k}", selected=(k == 1), size=66).grid(
                    row=k // 2, column=k % 2, padx=s(4), pady=s(4))

    SegmentedTabs(bar.widget, theme, ["List", "Small", "Large"], selected=0,
                  command=lambda i, _l: show(i), bg="bg").pack(anchor="w")
    show(0)
    return box


def build_multiselect(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "A multi-select dropdown — click to open, then "
            "tick several rows; the closed chip summarises the choice.").pack(
                anchor="w", pady=(0, 10))
    row = Surface(box.widget, theme, bg="bg")
    row.widget.pack(fill="x")

    left = Surface(row.widget, theme, bg="bg")
    left.widget.pack(side="left", anchor="n", padx=(0, s(40)))
    caption(left.widget, theme, "MultiDropdown — collapses to a chip").pack(
        anchor="w", pady=(0, s(6)))
    MultiDropdown(left.widget, theme,
                  ["Sky.jpg", "Ridge.jpg", "Valley.jpg", "Dawn.jpg",
                   "Harbor.jpg", "Forest.jpg", "Dunes.jpg", "Cliff.jpg"],
                  selected=(2, 4)).pack(anchor="w")

    right = Surface(row.widget, theme, bg="bg")
    right.widget.pack(side="left", anchor="n")
    caption(right.widget, theme, "multiselect_list — always open, ticks in "
            "place").pack(anchor="w", pady=(0, s(6)))
    multiselect_list(right.widget, theme,
                     [("Keep EXIF", True), ("Keep ICC profile", True),
                      ("Strip GPS", False), ("Embed thumbnail", False)],
                     width=220).pack(anchor="w")
    return box


def build_dropdowns(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "An open dropdown — three ways to mark the "
            "picked row: colour tint, a checkmark, or both.").pack(
                anchor="w", pady=(0, 12))
    row = Surface(box.widget, theme, bg="bg")
    row.widget.pack(anchor="w")
    for lbl, mark in [("Colour", "colour"), ("Checkmark", "check"),
                      ("Colour + check", "both")]:
        col = Surface(row.widget, theme, bg="bg")
        col.widget.pack(side="left", padx=(0, 30), anchor="n")
        caption(col.widget, theme, lbl).pack(anchor="w", pady=(0, 6))
        Dropdown(col.widget, theme,
                 [("Crop", "crop"), ("Adjust", "sliders-horizontal"),
                  ("Colour", "droplets"), ("Rotate", "rotate-ccw")],
                 selected=1, mark=mark).pack(anchor="w")
    return box


def build_heroes(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "Standard — accent bar + title. A dialog heading.").pack(
        anchor="w", pady=(0, 8))
    grid = Surface(box.widget, theme, bg="bg")
    grid.widget.pack(fill="x")
    for i, title in enumerate(["Save file", "Delete file", "Rename"]):
        grid.widget.grid_columnconfigure(i, weight=1, uniform="h")
        card = Card(grid.widget, theme, pad=14)
        card.canvas.grid(row=0, column=i, sticky="nsew", padx=(0, 10))
        hero_line(card.body, theme, title).pack(anchor="w", fill="x")

    caption(box.widget, theme, "icon= — a tool panel's section heading. "
            "set_title / set_icon retitle it in place as the panel swaps "
            "tools.").pack(anchor="w", pady=(s(18), 8))
    strip = Surface(box.widget, theme, bg="bar")
    strip.widget.pack(fill="x")
    hero = hero_line(strip.widget, theme, "Basic Edits",
                     icon="sliders-horizontal", bg="bar", size=11,
                     pad=(0, 9)).pack(fill="x")

    # a live retitle, exactly as Manoni's rail drives its panel heading
    TOOLS = [("Basic Edits", "sliders-horizontal"), ("Colors", "palette"),
             ("Crop", "crop"), ("Actions", "circle-play")]
    picker = Surface(box.widget, theme, bg="bg")
    picker.widget.pack(anchor="w", pady=(s(10), 0))

    def retitle(i, _label):
        title, icon = TOOLS[i]
        hero.set_title(title)
        hero.set_icon(icon)

    SegmentedTabs(picker.widget, theme, [t for t, _ in TOOLS], selected=0,
                  command=retitle, bg="bg").pack(anchor="w")
    _REFS.append(hero)
    return box


def build_buttons(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "Standard — No (ghost) · Yes (accent) · "
            "Delete (danger)").pack(anchor="w")
    row = Surface(box.widget, theme, bg="bg")
    row.widget.pack(anchor="w", pady=(6, 16))
    Button(row.widget, theme, "No", role="neutral", variant="ghost").pack(
        side="left", padx=(0, 8))
    Button(row.widget, theme, "Yes", role="primary").pack(side="left",
                                                          padx=(0, 8))
    Button(row.widget, theme, "Delete", role="danger", icon="trash-2").pack(
        side="left")

    caption(box.widget, theme, "Variants (role × weight)").pack(anchor="w")
    table = Surface(box.widget, theme, bg="bg")
    table.widget.pack(anchor="w", pady=(6, 0))
    variants = ["filled", "outline", "ghost"]
    for j, v in enumerate(variants):
        Label(table.widget, theme, v, fg="fg_dim", bg="bg", size=8).grid(
            row=0, column=j + 1, padx=6, pady=(0, 4))
    roles = [("Yes", "primary"), ("Delete", "danger"), ("Careful", "warn"),
             ("No", "neutral")]
    for i, (lab, role) in enumerate(roles):
        Label(table.widget, theme, lab, fg="fg", bg="bg", size=9,
              anchor="w").grid(row=i + 1, column=0, sticky="w", padx=(0, 12),
                               pady=4)
        for j, v in enumerate(variants):
            Button(table.widget, theme, lab, role=role, variant=v).grid(
                row=i + 1, column=j + 1, padx=6, pady=4)
    return box


def build_dialogs(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "A · Confirm — with scrim (the app dims "
            "behind)").pack(anchor="w")
    scrim = tk.Frame(box.widget, bg=theme["scrim"], height=s(210))
    scrim.pack(fill="x", pady=(s(6), s(16)))
    scrim.pack_propagate(False)
    theme.subscribe(lambda: scrim.winfo_exists() and scrim.configure(
        bg=theme["scrim"]))
    dialog(scrim, theme, "Save changes?",
           "This photo has no saved copy. Save before moving on?",
           buttons=[{"label": "Yes, save", "role": "primary"},
                    {"label": "No", "role": "neutral", "variant": "ghost"}],
           on_close=lambda: None).canvas.place(relx=0.5, rely=0.5,
                                               anchor="center")

    grid = Surface(box.widget, theme, bg="bg")
    grid.widget.pack(fill="x")
    grid.widget.grid_columnconfigure(0, weight=1, uniform="d")
    grid.widget.grid_columnconfigure(1, weight=1, uniform="d")
    left = Surface(grid.widget, theme, bg="bg")
    left.widget.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    caption(left.widget, theme, "B · Destructive action").pack(anchor="w")
    dialog(left.widget, theme, "Delete file?",
           "The file moves to the Rejected folder. Ctrl+Z undoes it.",
           buttons=[{"label": "Delete", "role": "danger", "icon": "trash-2"},
                    {"label": "Cancel", "role": "neutral", "variant": "ghost"}],
           on_close=lambda: None).pack(anchor="w", pady=(6, 0))
    right = Surface(grid.widget, theme, bg="bg")
    right.widget.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
    caption(right.widget, theme, "C · Input field").pack(anchor="w")
    dialog(right.widget, theme, "Rename file", "New name:",
           with_input="IMG_0421-edit",
           buttons=[{"label": "Save", "role": "primary"},
                    {"label": "Cancel", "role": "neutral", "variant": "ghost"}],
           on_close=lambda: None).pack(anchor="w", pady=(6, 0))
    return box


def build_callouts(parent, theme):
    box = Surface(parent, theme, bg="bg")
    grid = Surface(box.widget, theme, bg="bg")
    grid.widget.pack(fill="x")
    data = [("Note", "info", "ESC reverts your changes before you move on."),
            ("Tip", "tip", "Alt + click sets the clone source."),
            ("Warning", "warn", "The file is read-only — saving makes a copy.")]
    for i, (name, kind, text) in enumerate(data):
        grid.widget.grid_columnconfigure(i, weight=1, uniform="c")
        col = Surface(grid.widget, theme, bg="bg")
        col.widget.grid(row=0, column=i, sticky="nsew", padx=(0, 10))
        caption(col.widget, theme, name).pack(anchor="w", pady=(0, 4))
        callout(col.widget, theme, kind, text).pack(fill="x")
    return box


def build_panels(parent, theme):
    box = Surface(parent, theme, bg="bg")
    row = Surface(box.widget, theme, bg="bg")
    row.widget.pack(fill="x")
    for cap, builder in [("Side-panel sash (drag horizontally)", v_sash),
                         ("Folder-list divider (drag vertically)", h_sash)]:
        col = Surface(row.widget, theme, bg="bg")
        col.widget.pack(side="left", padx=(0, 30), anchor="n")
        caption(col.widget, theme, cap).pack(anchor="w", pady=(0, 8))
        builder(col.widget, theme).pack(anchor="w")

    col = Surface(row.widget, theme, bg="bg")
    col.widget.pack(side="left", anchor="n")
    caption(col.widget, theme, "Scrollbar handle").pack(anchor="w", pady=(0, 8))
    sbox = tk.Frame(col.widget, bg=theme["sidebar"], width=s(220), height=s(150))
    sbox.pack(anchor="w")
    sbox.pack_propagate(False)
    theme.subscribe(lambda: sbox.winfo_exists() and sbox.configure(
        bg=theme["sidebar"]))
    cv = tk.Canvas(sbox, bg=theme["sidebar"], highlightthickness=0)
    sb = themed_scrollbar(sbox, theme, cv.yview)
    cv.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    cv.pack(side="left", fill="both", expand=True)
    holder = tk.Frame(cv, bg=theme["sidebar"])
    cv.create_window((0, 0), window=holder, anchor="nw")
    theme.subscribe(lambda: cv.winfo_exists() and cv.configure(
        bg=theme["sidebar"]))
    theme.subscribe(lambda: holder.winfo_exists() and holder.configure(
        bg=theme["sidebar"]))
    for i in range(16):
        Label(holder, theme, f"  IMG_{421+i}.jpg", fg="fg", bg="sidebar",
              size=9, anchor="w").pack(fill="x", pady=0, padx=6)
    holder.update_idletasks()
    cv.configure(scrollregion=cv.bbox("all"))
    Label(box.widget, theme, "(hover the sashes — the grip turns accent)",
          fg="fg_dim", bg="bg", size=8).pack(anchor="w", pady=(10, 0))
    return box


def build_settings(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "The Settings window — a left tab rail "
            "(General · Export · Culling · About) + a live, scrollable pane. "
            "The app supplies the tabs + content; the kit draws the chrome.").pack(
                anchor="w", pady=(0, 10))
    stage = tk.Frame(box.widget, bg=theme["scrim"], height=s(460))
    stage.pack(fill="x")
    stage.pack_propagate(False)
    theme.subscribe(lambda: stage.winfo_exists() and stage.configure(
        bg=theme["scrim"]))

    def general(win):
        win.group("General")
        Toggle(win.row("Dark theme"), theme, value=True, bg="panel").pack()
        Toggle(win.row("Confirm before delete"), theme, value=True,
               bg="panel").pack()
        Dropdown(win.row("Thumbnail size"), theme, ["Small", "Medium", "Large"],
                 selected=2, bg="panel").pack()

    def export(win):
        win.group("Export")
        SegmentedTabs(win.row("Format"), theme, ["JPG", "PNG", "TIFF"],
                      bg="panel").pack()
        Slider(win.body.widget, theme, "Quality", value=85, lo=0, hi=100,
               neutral=0, bg="panel").pack(fill="x", pady=(s(8), 0))
        Toggle(win.row("Convert to sRGB"), theme, value=True, bg="panel").pack()

    def culling(win):
        win.group("Culling")
        Toggle(win.row("Keep on right arrow"), theme, value=False,
               bg="panel").pack()
        Dropdown(win.row("Reject folder name"), theme,
                 ["Rejected", "Trash", "_cull"], bg="panel").pack()
        # note() plain, then the same call raised into each callout kind
        win.note("Culling never moves a file until you press Enter.")
        win.note("Hold Shift while culling to skip the confirmation.",
                 kind="tip")
        win.note("Rejected photos are moved, not copied — the originals leave "
                 "this folder.", kind="warn")

    def about(win):
        win.group("About")
        Label(win.body.widget, theme, "TintKit — a themeable Tkinter UI kit.",
              fg="fg_dim", bg="panel", size=10, justify="left").pack(
                  anchor="w", pady=(s(4), s(12)))
        Button(win.body.widget, theme, "Check for updates", role="neutral",
               variant="outline", bg="panel").pack(anchor="w")

    card = Card(stage, theme, pad=0, bg="panel", width=s(600))
    card.pack(pady=s(20))
    SettingsWindow(card.body, theme, width=600, height=420, pane_bg="panel",
                   tabs=[("general", "General", None, general),
                         ("export", "Export", None, export),
                         ("culling", "Culling", None, culling),
                         ("about", "About", None, about)]).pack()
    return box


# ----------------------------------------------------------------------------
# window
# ----------------------------------------------------------------------------
SECTIONS = [
    ("Elements", build_elements),
    ("Titled slider — strip, value, reset, dot column", build_titled_sliders),
    ("Foldout — collapsible groups", build_foldouts),
    ("Folder tree — filter box + rows", build_folder_tree),
    ("Navigation — folder header", build_nav),
    ("Photo selection — a frame everywhere", build_selection),
    ("Multi-select dropdown — tick many", build_multiselect),
    ("Dropdown — open menu, selected row", build_dropdowns),
    ("Hero line", build_heroes),
    ("Buttons — Yes / No / Careful", build_buttons),
    ("Dialog — popup window", build_dialogs),
    ("Tip / Warning", build_callouts),
    ("Movable panels + scrollbar", build_panels),
    ("Settings window", build_settings),
]


def build(root, theme):
    root.configure(bg=theme["bg"])
    root.title("TintKit — UI kit gallery")
    theme.subscribe(lambda: root.winfo_exists() and root.configure(
        bg=theme["bg"]))

    top = Surface(root, theme, bg="bg")
    top.widget.pack(fill="x", padx=s(20), pady=(s(14), s(4)))
    Label(top.widget, theme, "TintKit — UI kit", fg="fg", bg="bg", size=16,
          bold=True).pack(side="left")
    Label(top.widget, theme, "one theme · reusable widgets · live switch",
          fg="fg_dim", bg="bg", size=10).pack(side="left", padx=s(12))
    theme_bar(root, theme).widget.pack(fill="x", padx=s(20), pady=(0, s(6)))

    outer = Surface(root, theme, bg="bg")
    outer.widget.pack(fill="both", expand=True, padx=s(20), pady=s(8))
    canvas = tk.Canvas(outer.widget, bg=theme["bg"], highlightthickness=0)
    theme.subscribe(lambda: canvas.winfo_exists() and canvas.configure(
        bg=theme["bg"]))
    vsb = themed_scrollbar(outer.widget, theme, canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    page = Surface(canvas, theme, bg="bg")
    win = canvas.create_window((0, 0), window=page.widget, anchor="nw")
    page.widget.bind("<Configure>",
                     lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

    for title, builder in SECTIONS:
        SectionHeader(page.widget, theme, title).pack(fill="x", pady=(s(26), s(10)))
        builder(page.widget, theme).pack(fill="x")
    Surface(page.widget, theme, bg="bg", height=s(28)).pack()


def main():
    root = tk.Tk()
    setup_dpi(root)
    theme = Theme(scheme="dark", accent="#8fae9b")
    build(root, theme)
    if os.environ.get("TINTKIT_SELFTEST") or "--selftest" in sys.argv:
        root.update_idletasks()
        root.update()
        theme.set(scheme="light")
        root.update_idletasks()
        root.update()
        theme.set(scheme="dark", accent="#c08457")
        root.update_idletasks()
        root.update()
        root.destroy()
        return
    try:
        root.state("zoomed")
    except Exception:
        root.geometry("1320x880")
    root.mainloop()


if __name__ == "__main__":
    main()
