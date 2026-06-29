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
    Surface, Label, font,
    Button, IconButton, Slider, Toggle, RadioGroup, Checkbox, SegmentedTabs,
    Badge, Tag, ProgressBar, Tooltip, TextField, Dropdown, MultiDropdown,
    Card, SectionHeader, hero_line, callout, dialog, v_sash, h_sash,
    themed_scrollbar,
    toolbar, tool_rail, FolderNav, SelectTile, SelectRow,
    SettingsWindow, CanvasControl, rounded_rect,
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
        ("Tooltip", lambda p: Tooltip(p, theme, "Hand tool — drag to pan")),
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


def build_nav(parent, theme):
    box = Surface(parent, theme, bg="bg")
    caption(box.widget, theme, "Folder navigation — a path bar + a collapsible "
            "folder tree (▾ opens it · ↑ goes up).").pack(anchor="w",
                                                          pady=(0, 10))
    FolderNav(box.widget, theme,
              crumbs=[("Home", False), ("Photos", False), ("2024", True)],
              tree_rows=[(0, "Home", "open", False), (1, "Photos", "open", False),
                         (2, "2023", "closed", False), (2, "2024", "open", True),
                         (3, "Wedding", "leaf", False), (3, "Trip", "leaf", False),
                         (1, "Documents", "closed", False)],
              count_text="248 photos").pack(fill="x")
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
    MultiDropdown(box.widget, theme,
                  ["Sky.jpg", "Ridge.jpg", "Valley.jpg", "Dawn.jpg",
                   "Harbor.jpg", "Forest.jpg", "Dunes.jpg", "Cliff.jpg"],
                  selected=(2, 4)).pack(anchor="w")
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
    caption(box.widget, theme, "Standard — accent bar + title").pack(
        anchor="w", pady=(0, 8))
    grid = Surface(box.widget, theme, bg="bg")
    grid.widget.pack(fill="x")
    for i, title in enumerate(["Save file", "Delete file", "Rename"]):
        grid.widget.grid_columnconfigure(i, weight=1, uniform="h")
        card = Card(grid.widget, theme, pad=14)
        card.canvas.grid(row=0, column=i, sticky="nsew", padx=(0, 10))
        hero_line(card.body, theme, title).pack(anchor="w", fill="x")
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
            "(General · Export · Culling · About) + a live pane.").pack(
                anchor="w", pady=(0, 10))
    stage = tk.Frame(box.widget, bg=theme["scrim"], height=s(460))
    stage.pack(fill="x")
    stage.pack_propagate(False)
    theme.subscribe(lambda: stage.winfo_exists() and stage.configure(
        bg=theme["scrim"]))
    SettingsWindow(stage, theme, width=600, height=420).pack(pady=s(20))
    return box


# ----------------------------------------------------------------------------
# window
# ----------------------------------------------------------------------------
SECTIONS = [
    ("Elements", build_elements),
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
