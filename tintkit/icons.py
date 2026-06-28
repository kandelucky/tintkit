"""TintKit — icon loader.

Loads a Lucide PNG, resizes it for the current DPI, recolours it to any theme
colour and caches the result. One loader for the whole kit — no widget draws
its own glyphs by hand, so every icon shares the same 2px Lucide stroke.

    from tintkit import icons
    img = icons.load("search", 16, theme["fg_dim"])
    canvas.create_image(x, y, image=img)

Without Pillow the loader returns ``None`` and callers simply skip the glyph.
Chevrons are stored once (``chevron-down``) and rotated to point any direction.
"""

import os

try:
    from PIL import Image, ImageTk
    HAVE_PIL = True
except Exception:                                   # pragma: no cover
    HAVE_PIL = False

# Bundled default icons ship inside the package, so the kit works as soon as
# it's installed. Point it at your own set with ``set_icon_dir(...)``.
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

DPI = 1.0                                            # set once at startup
_CACHE = {}
_REFS = []                                          # keep PhotoImages alive


def set_icon_dir(path):
    "Load icons from your own folder instead of the bundled set."
    global ICON_DIR
    ICON_DIR = os.path.abspath(path)
    _CACHE.clear()                                  # re-load names from the new dir

_ROT = {"down": 0, "up": 180, "right": 90, "left": 270}


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load(name, px=18, color="#ededed", rotate=0):
    "Return a recoloured ``ImageTk.PhotoImage`` for ``name``, or ``None``."
    key = (name, px, color, rotate, DPI)
    if key in _CACHE:
        return _CACHE[key]
    img = None
    path = os.path.join(ICON_DIR, name + ".png")
    if HAVE_PIL and os.path.exists(path):
        try:
            p = max(1, round(px * DPI))
            src = Image.open(path).convert("RGBA").resize((p, p), Image.LANCZOS)
            if rotate:
                src = src.rotate(rotate, expand=False, resample=Image.BICUBIC)
            r, g, b = _hex_to_rgb(color)
            solid = Image.new("RGBA", src.size, (r, g, b, 0))
            solid.putalpha(src.split()[3])
            img = ImageTk.PhotoImage(solid)
            _REFS.append(img)
        except Exception:
            img = None
    _CACHE[key] = img
    return img


def chevron(direction, px=14, color="#8a8a8a"):
    "The chevron PNG rotated to point ``up`` / ``down`` / ``left`` / ``right``."
    return load("chevron-down", px, color, rotate=_ROT[direction])
