# TintKit — UI kit

A small, themeable **Tkinter widget kit** for a fast, dark photo tool look —
and a living style guide that renders every widget together. One theme drives
every colour; widgets reuse each other; everything is interactive; and the look
(light / dark + accent) can be switched live, with no restart.

![Theme](https://img.shields.io/badge/theme-sage-8fae9b) ![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![UI](https://img.shields.io/badge/ui-tkinter-informational)

## Run the gallery

```bash
python gallery.py
```

Every component in one scrollable window, with a **live theme switcher** at the
top: flip Dark / Light and pick an accent — the whole window repaints instantly.

## Install

```bash
pip install tintkit            # the kit — zero required dependencies
pip install "tintkit[icons]"   # + Pillow, to recolour the Lucide icons
```

The kit is **pure-stdlib tkinter** — no required dependencies. The bundled
[Lucide](https://lucide.dev/) icons need [Pillow](https://python-pillow.org/)
to recolour; without it every widget still works and the shapes stay
**anti-aliased** (drawn in pure Tk) — only the glyphs are skipped. Point the
loader at your own icons with `set_icon_dir("…/my_icons")`.

## Use the kit

```python
import tkinter as tk
from tintkit import Theme, setup_dpi, Button, Toggle

root = tk.Tk()
setup_dpi(root)                       # crisp icons on high-DPI screens
theme = Theme(scheme="dark", accent="#8fae9b")

Button(root, theme, "Save", icon="save", command=lambda: print("saved")).pack()
Toggle(root, theme, value=True, command=lambda on: print(on)).pack()
root.mainloop()
```

Every widget takes the same first two arguments — the parent and the shared
`theme` — and returns an object you `.pack()` / `.grid()` like a normal widget.

### Theme it

One theme object is the single source of truth. Change any part and the whole
tree repaints:

```python
theme.set(scheme="light")             # dark <-> light
theme.set(accent="#c08457")           # any accent; shades are derived for you
theme.set(danger="#d05f5f", warn="#e0b85a")
theme.toggle_scheme()
```

Read a colour or geometry token anywhere with `theme["accent"]`,
`theme["panel"]`, `theme["r_control"]` …

## What's inside

A package, not one file — each piece small and reusable:

| module | what it holds |
|---|---|
| `tintkit/theme.py` | schemes (dark/light), accent + danger/warn derivation, the repaint observer |
| `tintkit/icons.py` | the Lucide icon loader (recoloured per theme) |
| `tintkit/primitives.py` | `rounded_rect`, the `CanvasControl` base, themed `Surface` / `Label` / `IconLabel` |
| `tintkit/controls.py` | Button, IconButton, Slider, Toggle, Radio, Checkbox, SegmentedTabs, Dropdown, Badge, Tag, ProgressBar, Tooltip, TextField |
| `tintkit/containers.py` | Card (rounded), dialog, callout, hero line, section header, drag sashes, scrollbar |
| `tintkit/composites.py` | toolbar, tool rail, folder nav + tree, selection views, multi-select list, settings window |
| `gallery.py` | the style guide window + live switcher |

### Design rules

- **One theme.** No widget hard-codes a colour; it reads `theme[...]` and
  subscribes to repaint on change. The `CanvasControl` base does this for you.
- **One radius scale.** `r_control` (button / chip / field), `r_pill`
  (toggle / tag / badge), `r_card` (card / dialog / callout). No magic numbers.
- **Widgets reuse widgets.** A toolbar is a row of `IconButton`; a dialog footer
  is real `Button`s; the settings pane uses `Toggle` / `Dropdown` / `Slider`.
  Nothing re-implements a primitive.
- **One icon source.** All glyphs are [Lucide](https://lucide.dev/) PNGs
  (ISC License) recoloured at load time — no hand-drawn symbols.

## Notes

- The gallery is a **demo**: handlers mostly do nothing, but the controls are
  genuinely interactive (drag sliders, toggle switches, switch tabs, open the
  dropdown, tick rows, switch the theme).
- The older standalone previews are kept in `archive/` (`ui_preview.py`,
  `settings_preview.py`, `nav_preview.py`) — superseded by the kit + `gallery.py`.
