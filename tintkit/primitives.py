"""TintKit — drawing primitives and the shared control base.

Two things every drawn widget needs:

* **draw helpers** — ``rounded_rect`` (the one corner routine), ``put_icon``.
* **CanvasControl** — a tiny base that owns the canvas, tracks hover, subscribes
  to the theme and repaints on every theme change. Subclasses only implement
  ``draw()`` and read ``self.theme[...]`` / ``self._hover``.

A subclass computes its size first, then hands it to the base::

    class Dot(CanvasControl):
        def __init__(self, parent, theme):
            super().__init__(parent, theme, 16, 16, bg="panel")
        def draw(self):
            rounded_rect(self.canvas, 0, 0, 16, 16, 8, fill=self.theme["accent"])
"""

import sys
import tkinter as tk
import tkinter.font as tkfont

from . import icons

# UI font. Segoe UI is Windows-only, so we pick a native face per OS and, at
# ``setup_dpi`` time, verify it is actually installed — falling back to Tk's own
# default UI font and finally the Tk-guaranteed ``Helvetica`` alias. The result
# is a real, native-looking sans on Windows, macOS and Linux alike.
_PREFERRED_FONTS = {
    "win32":  ["Segoe UI", "Tahoma"],
    "darwin": ["SF Pro Text", "Helvetica Neue", "Lucida Grande"],
}
# Common desktop-Linux (and other unix) sans families, best first.
_FALLBACK_FONTS = ["Noto Sans", "DejaVu Sans", "Cantarell", "Ubuntu",
                   "Liberation Sans"]


def _default_family():
    "A safe per-platform family for use before ``resolve_font`` runs."
    return {"win32": "Segoe UI", "darwin": "Helvetica Neue"}.get(
        sys.platform, "DejaVu Sans")


FONT_FAMILY = _default_family()


# ----------------------------------------------------------------------------
# typography
# ----------------------------------------------------------------------------
def resolve_font(root=None):
    """Pick the best UI font actually installed on this OS; set ``FONT_FAMILY``.

    ``setup_dpi`` calls this once a root exists. It tries the platform's
    preferred families, then Tk's native default UI font, then the guaranteed
    ``Helvetica`` alias — so text always renders with a real face anywhere.
    Returns the chosen family.
    """
    global FONT_FAMILY
    try:
        available = set(tkfont.families(root))
    except tk.TclError:
        available = set()
    for fam in _PREFERRED_FONTS.get(sys.platform, []) + _FALLBACK_FONTS:
        if fam in available:
            FONT_FAMILY = fam
            return fam
    try:                                        # native default UI font's family
        FONT_FAMILY = tkfont.nametofont("TkDefaultFont").actual("family")
    except tk.TclError:
        FONT_FAMILY = "Helvetica"               # Tk-guaranteed sans alias
    return FONT_FAMILY


def font(size, bold=False):
    "A plain (family, size[, 'bold']) tuple for label/text use."
    return (FONT_FAMILY, size, "bold") if bold else (FONT_FAMILY, size)


def measure(size, text, bold=False):
    "Pixel width of ``text`` at the given size — for sizing canvas controls."
    return tkfont.Font(family=FONT_FAMILY, size=size,
                       weight="bold" if bold else "normal").measure(text)


# ----------------------------------------------------------------------------
# draw helpers
# ----------------------------------------------------------------------------
def _round_pts(x0, y0, x1, y1, r):
    return [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
            x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]


def rounded_rect(c, x0, y0, x1, y1, r, **kw):
    "A rounded rectangle on canvas ``c``; ``r`` is clamped to a full pill."
    r = max(0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    if r <= 0:
        return c.create_rectangle(x0, y0, x1, y1, **kw)
    return c.create_polygon(_round_pts(x0, y0, x1, y1, r), smooth=True, **kw)


def put_icon(c, cx, cy, img, anchor="center"):
    "Place ``img`` (or skip if it failed to load) centred at (cx, cy)."
    if img:
        return c.create_image(cx, cy, image=img, anchor=anchor)


# ----------------------------------------------------------------------------
# anti-aliased shapes  (pure Tk — no Pillow)
#
# Tkinter's canvas has no anti-aliasing: an ``create_oval`` / smooth polygon
# draws every curved edge as hard on/off pixels, so small circles and rounded
# corners come out jagged — worse on a high-DPI screen where the geometry is
# scaled up. We rasterise the shape ourselves into a ``tk.PhotoImage``: every
# pixel is super-sampled (SS x SS sub-points) and the sub-point colours — fill,
# outline, or the background behind the shape — are averaged, so each edge
# blends smoothly. A Tk PhotoImage can't alpha-composite onto a canvas, so the
# caller passes the solid colour sitting *behind* the shape (``behind``) and we
# pre-blend against it. Cached by exact pixel parameters; the shapes are tiny,
# so the pure-Python loop runs once per (shape, size, colours) and is cheap.
# ----------------------------------------------------------------------------
_AA_SS = 4                                          # sub-samples per axis
_aa_cache = {}
_aa_refs = []                                       # keep PhotoImages alive


def _hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _in_ellipse(px, py, cx, cy, rx, ry):
    if rx <= 0 or ry <= 0:
        return False
    dx, dy = (px - cx) / rx, (py - cy) / ry
    return dx * dx + dy * dy <= 1.0


def _in_rrect(px, py, x0, y0, x1, y1, r):
    "Inside a rounded rect: within ``r`` of the rect inset by ``r`` each side."
    if px < x0 or px > x1 or py < y0 or py > y1:
        return False
    if r <= 0:
        return True
    ccx = min(max(px, x0 + r), x1 - r)              # nearest corner centre
    ccy = min(max(py, y0 + r), y1 - r)
    dx, dy = px - ccx, py - ccy
    return dx * dx + dy * dy <= r * r


def _aa_render(w, h, behind, color_at):
    "A w x h PhotoImage; each pixel = SSxSS average of ``color_at`` / behind."
    ss = _AA_SS
    inv = 1.0 / (ss * ss)
    offs = [(k + 0.5) / ss for k in range(ss)]
    br, bg, bb = behind
    rows = []
    for y in range(h):
        cells = []
        for x in range(w):
            r = g = b = 0.0
            for oy in offs:
                sy = y + oy
                for ox in offs:
                    col = color_at(x + ox, sy)
                    if col is None:
                        r += br; g += bg; b += bb
                    else:
                        r += col[0]; g += col[1]; b += col[2]
            cells.append("#%02x%02x%02x" % (int(r * inv), int(g * inv),
                                            int(b * inv)))
        rows.append("{" + " ".join(cells) + "}")
    img = tk.PhotoImage(width=w, height=h)
    img.put(" ".join(rows))
    return img


def aa_oval(c, x0, y0, x1, y1, fill=None, outline=None, width=1, behind=None):
    """A smooth oval, pre-blended over ``behind`` (the solid colour behind it).
    Falls back to a plain ``create_oval`` when ``behind`` is not given."""
    if behind is None:
        return c.create_oval(x0, y0, x1, y1, fill=fill or "",
                             outline=outline or "", width=width)
    w, h = int(round(x1 - x0)), int(round(y1 - y0))
    if w <= 0 or h <= 0:
        return None
    pad = max(1, int(round(width))) if (outline and not fill) else 1
    key = ("oval", fill, outline, width, behind, w, h, pad)
    img = _aa_cache.get(key)
    if img is None:
        grow = width / 2.0 if (outline and not fill) else 0   # centre the stroke
        cx, cy = (w + 2 * pad) / 2.0, (h + 2 * pad) / 2.0
        rx, ry = w / 2.0 + grow, h / 2.0 + grow
        rxin, ryin = rx - width, ry - width
        fr = _hex_rgb(fill) if fill else None
        orr = _hex_rgb(outline) if outline else None

        def color_at(px, py):
            if not _in_ellipse(px, py, cx, cy, rx, ry):
                return None
            if orr is not None:
                return fr if _in_ellipse(px, py, cx, cy, rxin, ryin) else orr
            return fr

        img = _aa_render(w + 2 * pad, h + 2 * pad, _hex_rgb(behind), color_at)
        _aa_cache[key] = img
        _aa_refs.append(img)
    return c.create_image(int(round(x0)) - pad, int(round(y0)) - pad,
                          image=img, anchor="nw")


def aa_round_rect(c, x0, y0, x1, y1, r, fill=None, outline=None, width=1,
                  behind=None):
    """A smooth rounded rectangle, pre-blended over ``behind``. Falls back to a
    plain ``rounded_rect`` when ``behind`` is not given."""
    if behind is None:
        return rounded_rect(c, x0, y0, x1, y1, r, fill=fill or "",
                            outline=outline or "", width=width)
    w, h = int(round(x1 - x0)), int(round(y1 - y0))
    if w <= 0 or h <= 0:
        return None
    r = max(0, min(r, w / 2.0, h / 2.0))               # clamp to a full pill
    pad = max(1, int(round(width))) if (outline and not fill) else 1
    key = ("rrect", fill, outline, width, r, behind, w, h, pad)
    img = _aa_cache.get(key)
    if img is None:
        grow = width / 2.0 if (outline and not fill) else 0   # centre the stroke
        ox0, oy0 = pad - grow, pad - grow
        ox1, oy1 = pad + w + grow, pad + h + grow
        rout = r + grow
        ix0, iy0 = ox0 + width, oy0 + width
        ix1, iy1 = ox1 - width, oy1 - width
        rin = max(0, rout - width)
        fr = _hex_rgb(fill) if fill else None
        orr = _hex_rgb(outline) if outline else None

        def color_at(px, py):
            if not _in_rrect(px, py, ox0, oy0, ox1, oy1, rout):
                return None
            if orr is not None:
                return fr if _in_rrect(px, py, ix0, iy0, ix1, iy1, rin) else orr
            return fr

        img = _aa_render(w + 2 * pad, h + 2 * pad, _hex_rgb(behind), color_at)
        _aa_cache[key] = img
        _aa_refs.append(img)
    return c.create_image(int(round(x0)) - pad, int(round(y0)) - pad,
                          image=img, anchor="nw")


# ----------------------------------------------------------------------------
# theme-aware plain widgets
# ----------------------------------------------------------------------------
class _Themed:
    "Mixin: subscribe to the theme, restyle on change, unsubscribe on destroy."

    def _bind_theme(self, theme, widget):
        self.theme = theme
        self.widget = widget
        theme.subscribe(self._restyle)
        widget.bind("<Destroy>", self._on_destroy)
        self._restyle()

    def _on_destroy(self, e):
        if e.widget is self.widget:
            self.theme.unsubscribe(self._restyle)

    def _restyle(self):
        raise NotImplementedError

    def configure(self, **k):
        self.widget.configure(**k)

    def pack(self, **k):
        self.widget.pack(**k)
        return self

    def grid(self, **k):
        self.widget.grid(**k)
        return self

    def place(self, **k):
        self.widget.place(**k)
        return self


class Surface(_Themed):
    "A tk.Frame whose background follows a theme token (``panel`` / ``bg`` …)."

    def __init__(self, parent, theme, bg="panel", **kw):
        self._bg = bg
        self._bind_theme(theme, tk.Frame(parent, bg=theme[bg], **kw))

    def _restyle(self):
        try:
            self.widget.configure(bg=self.theme[self._bg])
        except tk.TclError:
            pass


class Label(_Themed):
    "A tk.Label bound to a foreground + background token."

    def __init__(self, parent, theme, text, fg="fg", bg="panel", size=9,
                 bold=False, **kw):
        self._fg, self._bg = fg, bg
        self._bind_theme(theme, tk.Label(parent, text=text, font=font(size, bold),
                                         **kw))

    def _restyle(self):
        try:
            self.widget.configure(fg=self.theme[self._fg], bg=self.theme[self._bg])
        except tk.TclError:
            pass


class IconLabel(_Themed):
    "A tk.Label holding a Lucide icon, recoloured + reloaded on theme change."

    def __init__(self, parent, theme, name, size=16, fg="fg", bg="panel",
                 rotate=0, **kw):
        self._name, self._size = name, size
        self._fg, self._bg, self._rot = fg, bg, rotate
        self._bind_theme(theme, tk.Label(parent, bg=theme[bg], **kw))

    def set_icon(self, name):
        self._name = name
        self._restyle()

    def _restyle(self):
        try:
            im = icons.load(self._name, self._size, self.theme[self._fg],
                            self._rot)
            self.widget.configure(bg=self.theme[self._bg], image=im or "")
            self.widget.image = im
        except tk.TclError:
            pass


# ----------------------------------------------------------------------------
# base control
# ----------------------------------------------------------------------------
class CanvasControl:
    """Canvas-backed widget with hover tracking + live theming.

    Parameters
    ----------
    parent, theme : the host frame and the shared :class:`Theme`.
    width, height : canvas size in px.
    bg            : theme token for the canvas background (so the control
                    blends into whatever surface hosts it — ``"bg"``,
                    ``"panel"``, ``"sidebar"`` …).
    cursor        : tk cursor; pass ``""`` for non-interactive demos.
    """

    def __init__(self, parent, theme, width, height, *, bg="bg",
                 cursor="hand2"):
        self.theme = theme
        self.w = width
        self.h = height
        self._bg = bg
        self._hover = False
        self.canvas = tk.Canvas(parent, width=width, height=height,
                                bg=theme[bg], highlightthickness=0,
                                cursor=cursor)
        self.canvas.tk_control = self       # back-ref: control from its canvas
        self.canvas.bind("<Enter>", self._enter)
        self.canvas.bind("<Leave>", self._leave)
        self.canvas.bind("<Destroy>", self._destroyed)
        theme.subscribe(self.repaint)
        self.repaint()

    # -- background --------------------------------------------------------
    @property
    def bg(self):
        return self.theme[self._bg]

    def set_bg(self, token):
        "Re-host the control on a different surface token and repaint."
        self._bg = token
        self.repaint()

    # -- hover -------------------------------------------------------------
    def _interactive(self):
        "Override to disable hover (e.g. a disabled button)."
        return True

    def _enter(self, _e):
        if self._interactive():
            self._hover = True
            self.repaint()

    def _leave(self, _e):
        if self._hover:
            self._hover = False
            self.repaint()

    def _destroyed(self, e):
        if e.widget is self.canvas:
            self.theme.unsubscribe(self.repaint)

    # -- paint -------------------------------------------------------------
    def repaint(self):
        try:
            self.canvas.configure(bg=self.bg)
            self.canvas.delete("all")
            self.draw()
        except tk.TclError:                         # widget already gone
            pass

    def draw(self):
        raise NotImplementedError

    def resize(self, w=None, h=None):
        if w is not None:
            self.w = w
        if h is not None:
            self.h = h
        self.canvas.configure(width=self.w, height=self.h)
        self.repaint()

    # -- geometry passthrough ---------------------------------------------
    def pack(self, **k):
        self.canvas.pack(**k)
        return self

    def grid(self, **k):
        self.canvas.grid(**k)
        return self

    def place(self, **k):
        self.canvas.place(**k)
        return self
