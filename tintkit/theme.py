"""TintKit — theme engine.

One source of truth for every colour and geometry token. A widget never
hard-codes a colour; it reads ``theme[name]`` and re-renders when the theme
changes::

    theme = Theme(scheme="dark", accent="#8fae9b")
    theme.set(scheme="light")          # live switch — repaints everything
    theme.set(accent="#c08457")        # new accent — derived shades recomputed

Every drawn control subscribes once (the ``CanvasControl`` base does this for
you) so a single ``theme.set(...)`` repaints the whole window — no restart::

    theme.subscribe(self.repaint)

Colours fall into four groups:

* **scheme neutrals** — bg / panel / fg / border … (from ``dark`` or ``light``)
* **accent** — derived from one seed colour (hover · soft · on_accent)
* **semantic** — ``danger`` / ``warn``, each derived the same way as the accent
* **geometry** — radius scale, track height, etc. (no magic numbers in widgets)
"""


# ----------------------------------------------------------------------------
# colour maths
# ----------------------------------------------------------------------------
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in rgb)


def mix(c1, c2, t):
    "Blend hex ``c1`` toward hex ``c2`` by ``t`` (0..1)."
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex(tuple(a[i] * (1 - t) + b[i] * t for i in range(3)))


def lighten(c, t):
    "Move ``c`` toward white by ``t``."
    return mix(c, "#ffffff", t)


def darken(c, t):
    "Move ``c`` toward black by ``t``."
    return mix(c, "#000000", t)


def _luminance(c):
    "Perceived luminance 0..1 (sRGB weighted)."
    r, g, b = (v / 255 for v in hex_to_rgb(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def on_color(c):
    "Readable text/icon colour to sit on top of ``c`` — tinted black or white."
    if _luminance(c) > 0.55:
        return mix("#000000", c, 0.10)        # dark text, faintly tinted
    return mix("#ffffff", c, 0.06)            # light text, faintly tinted


# ----------------------------------------------------------------------------
# schemes (neutral palettes) + geometry
# ----------------------------------------------------------------------------
SCHEMES = {
    "dark": {
        "bg": "#141414", "panel": "#1d1d1d", "bar": "#1d1d1d",
        "sidebar": "#1a1a1a", "hover": "#2a2a2a", "lift": "#242424",
        "chip": "#242424", "border": "#2c2c2c", "divider": "#2c2c2c",
        "fg": "#ededed", "fg_dim": "#8a8a8a", "ring": "#9a9a9a",
        "scrim": "#0a0a0a", "tooltip": "#0b0b0b",
    },
    "light": {
        "bg": "#f4f4f3", "panel": "#ffffff", "bar": "#ffffff",
        "sidebar": "#ececea", "hover": "#e4e4e1", "lift": "#eeeeec",
        "chip": "#e9e9e6", "border": "#d3d3cf", "divider": "#dcdcd8",
        "fg": "#1c1c1c", "fg_dim": "#6a6a66", "ring": "#5a5a56",
        "scrim": "#9a9a96", "tooltip": "#2a2a28",
    },
}

GEOMETRY = {
    "r_control": 4,        # button / chip / field
    "r_pill": 999,         # toggle / tag / badge  (clamped to a full pill)
    "r_card": 8,           # card / dialog / callout surfaces
    "track_h": 6,          # slider track thickness
    "border_w": 1,         # hairline width
}

# Default semantic seeds; each scheme can tweak them if needed.
SEMANTIC_SEEDS = {
    "danger": "#c75d54",
    "warn": "#d6a85c",
}

DEFAULT_ACCENT = "#8fae9b"


# ----------------------------------------------------------------------------
# theme
# ----------------------------------------------------------------------------
class Theme:
    """Live palette + geometry tokens with a repaint-subscriber list.

    Read a colour with ``theme["accent"]`` or ``theme.get("accent")``.
    Geometry tokens (``r_control`` …) live in the same namespace.
    """

    def __init__(self, scheme="dark", accent=DEFAULT_ACCENT,
                 danger=None, warn=None):
        self._subs = []
        self.scheme = scheme
        self.accent = accent
        self.danger = danger or SEMANTIC_SEEDS["danger"]
        self.warn = warn or SEMANTIC_SEEDS["warn"]
        self._rebuild()

    # -- derivation --------------------------------------------------------
    def _shades(self, seed):
        "From one seed: (base, hover, soft, on) tuned to the active scheme."
        base = seed
        if self.scheme == "dark":
            hover = lighten(seed, 0.14)
            soft = mix(seed, self._neutral["panel"], 0.42)
        else:
            hover = darken(seed, 0.10)
            soft = mix(seed, self._neutral["panel"], 0.55)
        return base, hover, soft, on_color(seed)

    def _rebuild(self):
        from . import scaling
        self._neutral = dict(SCHEMES[self.scheme])
        c = dict(self._neutral)
        # geometry tokens are in baseline-96 px → scale to the active screen
        c.update({k: scaling.s(v) for k, v in GEOMETRY.items()})

        a, a_h, a_s, a_on = self._shades(self.accent)
        c.update(accent=a, accent_hover=a_h, accent_soft=a_s, on_accent=a_on)

        d, d_h, _d_s, d_on = self._shades(self.danger)
        c.update(danger=d, danger_hover=d_h, on_danger=d_on)

        w, w_h, _w_s, w_on = self._shades(self.warn)
        c.update(warn=w, warn_hover=w_h, on_warn=w_on)

        self.colors = c

    # -- public ------------------------------------------------------------
    def set(self, scheme=None, accent=None, danger=None, warn=None):
        "Change any part of the theme and repaint every subscriber."
        if scheme is not None:
            self.scheme = scheme
        if accent is not None:
            self.accent = accent
        if danger is not None:
            self.danger = danger
        if warn is not None:
            self.warn = warn
        self._rebuild()
        self._notify()

    def toggle_scheme(self):
        self.set(scheme="light" if self.scheme == "dark" else "dark")

    def __getitem__(self, key):
        return self.colors[key]

    def get(self, key, default=None):
        return self.colors.get(key, default)

    # -- subscribers -------------------------------------------------------
    def subscribe(self, fn):
        "Register a repaint callback; returns ``fn`` for convenience."
        self._subs.append(fn)
        return fn

    def unsubscribe(self, fn):
        try:
            self._subs.remove(fn)
        except ValueError:
            pass

    def _notify(self):
        # Iterate a copy; dead widgets unsubscribe themselves mid-loop.
        for fn in list(self._subs):
            try:
                fn()
            except Exception:
                self.unsubscribe(fn)
