"""TintKit — interactive controls.

Every control is a :class:`CanvasControl`: it draws from theme tokens, repaints
on theme change, and actually *works* (clicks, drags, state). Composites reuse
these — a toolbar is a row of :class:`IconButton`, a dialog footer is a row of
:class:`Button`; nothing re-implements a button.

Geometry literals go through ``s()`` so the layout scales to the screen DPI;
fonts, ``measure()`` and icon pixel sizes are already real-px (Tk scaling +
the icon loader) and are left alone.

    from tintkit import Theme, Button, Toggle
    Button(parent, theme, "Save", role="primary", icon="save",
           command=do_save).pack()
"""

import tkinter as tk

from . import icons
from .scaling import s
from .theme import mix, on_color
from .primitives import (CanvasControl, rounded_rect, aa_oval, aa_round_rect,
                         put_icon, font, measure)


# ----------------------------------------------------------------------------
# Button  (also used for chips — a chip is just role="primary"/"neutral")
# ----------------------------------------------------------------------------
class Button(CanvasControl):
    """role: primary · neutral · danger · warn   ·   variant: filled · outline · ghost."""

    def __init__(self, parent, theme, label, role="primary", variant="filled",
                 icon=None, disabled=False, command=None, stretch=False,
                 min_w=92, h=36, bg="bg"):
        self.label = label
        self.role = role
        self.variant = variant
        self.icon_name = icon
        self.disabled = disabled
        self.command = command
        self.stretch = stretch
        bold = (variant == "filled")
        iw = s(22) if icon else 0
        w = max(s(min_w), int(s(28) + measure(9, label, bold) + iw))
        super().__init__(parent, theme, w, s(h), bg=bg,
                         cursor="" if disabled else "hand2")
        if not disabled and command:
            self.canvas.bind("<Button-1>", lambda e: self.command())
        if stretch:
            self.canvas.bind("<Configure>", self._on_stretch)

    def _interactive(self):
        return not self.disabled

    def _on_stretch(self, e):
        if e.width > 4 and e.width != self.w:
            self.w = e.width
            self.repaint()

    def _pal(self):
        t = self.theme
        return {"primary": (t["accent"], t["accent_hover"], t["on_accent"]),
                "neutral": (t["chip"], t["hover"], t["fg"]),
                "danger": (t["danger"], t["danger_hover"], t["on_danger"]),
                "warn": (t["warn"], t["warn_hover"], t["on_warn"])}[self.role]

    def _edge(self):
        t = self.theme
        return {"primary": t["accent"], "neutral": t["fg_dim"],
                "danger": t["danger"], "warn": t["warn"]}[self.role]

    def _fg(self):
        if self.disabled:
            return self.theme["fg_dim"]
        if self.variant == "filled":
            return self._pal()[2]
        return self.theme["fg"]               # outline / ghost: plain text

    def draw(self):
        c, t = self.canvas, self.theme
        r = t["r_control"]
        base, hov, _ = self._pal()
        x1, y1 = self.w - s(1), self.h - s(1)
        if self.disabled:
            rounded_rect(c, s(1), s(1), x1, y1, r, fill=t["chip"])
        elif self.variant == "filled":
            rounded_rect(c, s(1), s(1), x1, y1, r,
                         fill=hov if self._hover else base)
        elif self.variant == "outline":
            rounded_rect(c, s(1), s(1), x1, y1, r,
                         fill=t["hover"] if self._hover else self.bg,
                         outline=self._edge(), width=s(1))
        else:                                  # ghost
            rounded_rect(c, s(1), s(1), x1, y1, r,
                         fill=t["hover"] if self._hover else t["chip"],
                         outline=t["border"], width=s(1))
        fg = self._fg()
        cx, cy = self.w / 2, self.h / 2
        bold = (self.variant == "filled")
        if self.icon_name:
            ic = icons.load(self.icon_name, 16, fg)
            iw = ic.width() if ic else s(16)
            total = iw + s(6) + measure(9, self.label, bold)
            x = cx - total / 2
            put_icon(c, x, cy, ic, anchor="w")
            c.create_text(x + iw + s(6), cy, anchor="w", text=self.label,
                          fill=fg, font=font(9, bold))
        else:
            c.create_text(cx, cy, text=self.label, fill=fg, font=font(9, bold))


# ----------------------------------------------------------------------------
# IconButton  (toolbar square + tool-rail tile with a caption)
# ----------------------------------------------------------------------------
class IconButton(CanvasControl):
    "A square icon control; pass ``label`` to make a captioned rail tile."

    def __init__(self, parent, theme, icon, w=34, h=34, label=None,
                 active=False, command=None, icon_px=18, bg="bar"):
        self.icon_name = icon
        self.label = label
        self.active = active
        self.command = command
        self.icon_px = icon_px
        super().__init__(parent, theme, s(w), s(h), bg=bg)
        if command:
            self.canvas.bind("<Button-1>", lambda e: self.command())

    def set_active(self, on):
        self.active = on
        self.repaint()

    def draw(self):
        c, t = self.canvas, self.theme
        r = min(t["r_control"], (self.h - s(4)) / 2)
        fill = t["accent"] if self.active else (t["hover"] if self._hover
                                                else self.bg)
        if fill != self.bg:
            rounded_rect(c, s(2), s(2), self.w - s(2), self.h - s(2), r,
                         fill=fill)
        col = t["on_accent"] if self.active else t["fg"]
        if self.label:
            put_icon(c, self.w / 2, self.h / 2 - s(6),
                     icons.load(self.icon_name, self.icon_px, col))
            tc = t["on_accent"] if self.active else t["fg_dim"]
            c.create_text(self.w / 2, self.h - s(11), text=self.label, fill=tc,
                          font=font(8))
        else:
            put_icon(c, self.w / 2, self.h / 2,
                     icons.load(self.icon_name, self.icon_px, col))


# ----------------------------------------------------------------------------
# Slider
# ----------------------------------------------------------------------------
class Slider(CanvasControl):
    "Labelled value slider; drag the knob. ``chip`` tints a colour swatch."

    def __init__(self, parent, theme, label, value=132, lo=0, hi=200,
                 neutral=100, chip=None, width=240, command=None, bg="bg"):
        self.label, self.lo, self.hi, self.neutral = label, lo, hi, neutral
        self.value, self.chip, self.command = value, chip, command
        w = s(width)
        self.x0 = s(12) + (s(14) if chip else 0)
        self.x1 = w - s(12)
        super().__init__(parent, theme, w, s(38), bg=bg, cursor="hand2")
        self.canvas.bind("<Configure>", self._cfg)
        self.canvas.bind("<Button-1>", self._drag)
        self.canvas.bind("<B1-Motion>", self._drag)

    def _interactive(self):
        return False                           # hover doesn't alter the look

    def _cfg(self, e):
        nx = e.width - s(12)
        if nx > self.x0 and nx != self.x1:
            self.x1, self.w = nx, e.width
            self.repaint()

    def _v2x(self, v):
        return self.x0 + (v - self.lo) / (self.hi - self.lo) * (self.x1 - self.x0)

    def _drag(self, e):
        f = min(1.0, max(0.0, (e.x - self.x0) / (self.x1 - self.x0)))
        self.value = round(self.lo + f * (self.hi - self.lo))
        self.repaint()
        if self.command:
            self.command(self.value)

    def draw(self):
        c, t = self.canvas, self.theme
        if self.chip:
            rounded_rect(c, 0, s(13), s(10), s(23), s(2), fill=self.chip)
        c.create_text(self.x0, s(11), text=self.label, anchor="w", fill=t["fg"],
                      font=font(9))
        d = self.value - self.neutral
        c.create_text(self.x1, s(11), text=(f"+{d}" if d > 0 else str(d)),
                      anchor="e", fill=t["fg_dim"], font=font(9))
        y, th = s(27), t["track_h"]
        c.create_line(self.x0, y, self.x1, y, fill=t["divider"], width=th,
                      capstyle="round")
        nx, kx = self._v2x(self.neutral), self._v2x(self.value)
        if abs(kx - nx) > 1:
            c.create_line(nx, y, kx, y, fill=t["accent"], width=th,
                          capstyle="round")
        aa_round_rect(c, kx - s(6), y - s(9), kx + s(6), y + s(9), s(5),
                      fill=t["accent"], behind=self.bg)


# ----------------------------------------------------------------------------
# Toggle
# ----------------------------------------------------------------------------
class Toggle(CanvasControl):
    def __init__(self, parent, theme, value=False, command=None, bg="bg"):
        self.value = value
        self.command = command
        super().__init__(parent, theme, s(42), s(22), bg=bg)
        self.canvas.bind("<Button-1>", self._click)

    def _interactive(self):
        return False

    def _click(self, _e):
        self.value = not self.value
        self.repaint()
        if self.command:
            self.command(self.value)

    def draw(self):
        c, t = self.canvas, self.theme
        on = self.value
        track = t["accent"] if on else t["chip"]
        aa_round_rect(c, s(1), s(2), s(41), s(20), t["r_pill"], fill=track,
                      behind=self.bg)
        kx = s(31) if on else s(11)
        aa_oval(c, kx - s(7), s(4), kx + s(7), s(18),
                fill=t["on_accent"] if on else t["fg_dim"], behind=track)


# ----------------------------------------------------------------------------
# Radio  (+ a small group controller for exclusivity)
# ----------------------------------------------------------------------------
class Radio(CanvasControl):
    def __init__(self, parent, theme, label, selected=False, disabled=False,
                 command=None, bg="bg"):
        self.label = label
        self.selected = selected
        self.disabled = disabled
        self.command = command
        w = s(25) + measure(9, label) + s(4)
        super().__init__(parent, theme, w, s(18), bg=bg,
                         cursor="" if disabled else "hand2")
        if not disabled:
            self.canvas.bind("<Button-1>", self._click)

    def _interactive(self):
        return False

    def _click(self, _e):
        if not self.selected and self.command:
            self.command()

    def set_selected(self, on):
        self.selected = on
        self.repaint()

    def draw(self):
        c, t = self.canvas, self.theme
        on = self.selected
        ring = (t["accent"] if on else t["ring"])
        if self.disabled:
            ring = t["accent_soft"] if on else t["border"]
        aa_oval(c, s(2), s(2), s(16), s(16), outline=ring, width=s(2),
                behind=self.bg)
        if on:
            aa_oval(c, s(6), s(6), s(12), s(12), behind=self.bg,
                    fill=t["accent_soft"] if self.disabled else t["accent"])
        c.create_text(s(25), s(9), text=self.label, anchor="w",
                      fill=t["fg_dim"] if self.disabled else t["fg"],
                      font=font(9))


class RadioGroup:
    "Wires several :class:`Radio` items so only one is on at a time."

    def __init__(self, theme, command=None):
        self.theme = theme
        self.command = command
        self.value = None
        self._items = []

    def add(self, parent, label, value, selected=False, disabled=False, bg="bg"):
        r = Radio(parent, self.theme, label, selected=selected,
                  disabled=disabled, command=lambda: self.select(value), bg=bg)
        self._items.append((value, r))
        if selected:
            self.value = value
        return r

    def select(self, value):
        self.value = value
        for v, r in self._items:
            r.set_selected(v == value)
        if self.command:
            self.command(value)


# ----------------------------------------------------------------------------
# Checkbox  (off · on · mixed)
# ----------------------------------------------------------------------------
class Checkbox(CanvasControl):
    # off -> on -> mixed -> off, but only when the box can be indeterminate;
    # a plain checkbox just flips on/off.
    _CYCLE = {"off": "on", "on": "mixed", "mixed": "off"}

    def __init__(self, parent, theme, label, state="off", disabled=False,
                 tristate=None, command=None, bg="bg"):
        self.label = label
        self.state = state
        self.disabled = disabled
        self.tristate = (state == "mixed") if tristate is None else tristate
        self.command = command
        w = s(25) + measure(9, label) + s(4)
        super().__init__(parent, theme, w, s(18), bg=bg,
                         cursor="" if disabled else "hand2")
        if not disabled:
            self.canvas.bind("<Button-1>", self._click)

    def _interactive(self):
        return False

    def _click(self, _e):
        if self.tristate:
            self.state = self._CYCLE[self.state]
        else:
            self.state = "off" if self.state == "on" else "on"
        self.repaint()
        if self.command:
            self.command(self.state)

    def draw(self):
        c, t = self.canvas, self.theme
        if self.state == "off":
            edge = t["border"] if self.disabled else t["ring"]
            aa_round_rect(c, s(2), s(2), s(16), s(16), s(5), outline=edge,
                          width=s(2), behind=self.bg)
        else:
            fill = t["accent_soft"] if self.disabled else t["accent"]
            aa_round_rect(c, s(2), s(2), s(16), s(16), s(5), fill=fill,
                          behind=self.bg)
            if self.state == "on":
                put_icon(c, s(9), s(9), icons.load("check", 12, t["on_accent"]))
            else:                              # mixed — a centred dash, not a blob
                aa_round_rect(c, s(5), s(8), s(13), s(11), s(1.5),
                              fill=t["on_accent"], behind=fill)
        c.create_text(s(25), s(9), text=self.label, anchor="w",
                      fill=t["fg_dim"] if self.disabled else t["fg"],
                      font=font(9))


# ----------------------------------------------------------------------------
# Segmented tabs
# ----------------------------------------------------------------------------
class SegmentedTabs(CanvasControl):
    def __init__(self, parent, theme, options, selected=0, command=None, bg="bg"):
        self.options = list(options)
        self.selected = selected
        self.command = command
        self._widths = [measure(9, o) + s(28) for o in self.options]
        super().__init__(parent, theme, sum(self._widths) + s(6), s(36), bg=bg)
        self.canvas.bind("<Button-1>", self._click)

    def _interactive(self):
        return False

    def _click(self, e):
        x = s(3)
        for i, wd in enumerate(self._widths):
            if x <= e.x <= x + wd:
                if i != self.selected:
                    self.selected = i
                    self.repaint()
                    if self.command:
                        self.command(i, self.options[i])
                return
            x += wd

    def draw(self):
        c, t = self.canvas, self.theme
        total = sum(self._widths)
        rounded_rect(c, s(1), s(3), total + s(5), s(33), t["r_control"],
                     fill=t["chip"])
        x = s(3)
        for i, o in enumerate(self.options):
            a = (i == self.selected)
            wd = self._widths[i]
            if a:
                rounded_rect(c, x + s(1), s(5), x + wd - s(1), s(31),
                             t["r_control"], fill=t["accent"])
            c.create_text(x + wd / 2, s(18), text=o,
                          fill=t["on_accent"] if a else t["fg"], font=font(9, a))
            x += wd


# ----------------------------------------------------------------------------
# Badge / Tag
# ----------------------------------------------------------------------------
class Badge(CanvasControl):
    "Solid pill — kind: neutral · accent · danger · warn."

    def __init__(self, parent, theme, text, kind="neutral", bg="bg"):
        self.text = text
        self.kind = kind
        super().__init__(parent, theme, measure(9, text, True) + s(22), s(26),
                         bg=bg, cursor="")

    def _interactive(self):
        return False

    def draw(self):
        c, t = self.canvas, self.theme
        fill, fg = {"neutral": (t["chip"], t["fg"]),
                    "accent": (t["accent"], t["on_accent"]),
                    "danger": (t["danger"], t["on_danger"]),
                    "warn": (t["warn"], t["on_warn"])}[self.kind]
        rounded_rect(c, s(1), s(1), self.w - s(1), s(25), t["r_pill"], fill=fill)
        c.create_text(self.w / 2, s(13), text=self.text, fill=fg,
                      font=font(9, True))


class Tag(CanvasControl):
    "Outline pill — kind: accent · danger · warn · neutral."

    def __init__(self, parent, theme, text, kind="accent", bg="bg"):
        self.text = text
        self.kind = kind
        super().__init__(parent, theme, measure(7, text, True) + s(18), s(20),
                         bg=bg)

    def _interactive(self):
        return False

    def draw(self):
        c, t = self.canvas, self.theme
        # neutral text on a grey chip; the status colour reads from the ring only
        edge = {"accent": t["accent"], "danger": t["danger"], "warn": t["warn"],
                "neutral": t["border"]}[self.kind]
        aa_round_rect(c, s(1), s(1), self.w - s(1), s(19), t["r_pill"],
                      fill=t["chip"], outline=edge, width=s(1), behind=self.bg)
        c.create_text(self.w / 2, s(10), text=self.text, fill=t["fg"],
                      font=font(7, True))


# ----------------------------------------------------------------------------
# Progress bar
# ----------------------------------------------------------------------------
class ProgressBar(CanvasControl):
    def __init__(self, parent, theme, value=0.62, width=240, bg="bg"):
        self.value = value
        super().__init__(parent, theme, s(width), s(10), bg=bg, cursor="")
        self.canvas.bind("<Configure>", self._cfg)

    def _interactive(self):
        return False

    def _cfg(self, e):
        if e.width > 4 and e.width != self.w:
            self.w = e.width
            self.repaint()

    def set_value(self, v):
        self.value = max(0.0, min(1.0, v))
        self.repaint()

    def draw(self):
        c, t = self.canvas, self.theme
        rounded_rect(c, 0, s(1), self.w, s(9), s(4), fill=t["chip"])
        if self.value > 0:
            rounded_rect(c, 0, s(1), max(s(8), int(self.w * self.value)), s(9),
                         s(4), fill=t["accent"])


# ----------------------------------------------------------------------------
# Tooltip (static styled bubble)
# ----------------------------------------------------------------------------
class Tooltip(CanvasControl):
    def __init__(self, parent, theme, text, bg="bg"):
        self.text = text
        super().__init__(parent, theme, measure(9, text) + s(22), s(30), bg=bg,
                         cursor="")

    def _interactive(self):
        return False

    def draw(self):
        c, t = self.canvas, self.theme
        rounded_rect(c, s(1), s(1), self.w - s(1), s(28), s(6), fill=t["tooltip"],
                     outline=t["border"])
        c.create_text(self.w / 2, s(14), text=self.text,
                      fill=on_color(t["tooltip"]), font=font(9))


# ----------------------------------------------------------------------------
# Text field  (themed tk.Entry)
# ----------------------------------------------------------------------------
class TextField:
    "A hairline-framed entry that restyles itself on theme change."

    def __init__(self, parent, theme, value="", bg="bg"):
        self.theme = theme
        self.outer = tk.Frame(parent, bg=theme["border"])
        self.entry = tk.Entry(self.outer, relief="flat", font=font(10),
                              highlightthickness=0)
        if value:
            self.entry.insert(0, value)
        self.entry.pack(fill="x", padx=s(1), pady=s(1), ipady=s(6), ipadx=s(6))
        theme.subscribe(self._restyle)
        self.outer.bind("<Destroy>", self._destroyed)
        self._restyle()

    def _destroyed(self, e):
        if e.widget is self.outer:
            self.theme.unsubscribe(self._restyle)

    def _restyle(self):
        try:
            t = self.theme
            self.outer.configure(bg=t["border"])
            self.entry.configure(bg=t["chip"], fg=t["fg"],
                                 insertbackground=t["fg"])
        except tk.TclError:
            pass

    def get(self):
        return self.entry.get()

    def pack(self, **k):
        self.outer.pack(**k)
        return self

    def grid(self, **k):
        self.outer.grid(**k)
        return self

    def place(self, **k):
        self.outer.place(**k)
        return self

    def grid(self, **k):
        self.outer.grid(**k)
        return self


# ----------------------------------------------------------------------------
# Dropdown (trigger chip + a real pop-up list)
# ----------------------------------------------------------------------------
class Dropdown(CanvasControl):
    """A select: a trigger chip + a pop-up list. ``mark`` is how the current
    row is shown — ``check`` · ``colour`` · ``both``. Options are plain strings
    or ``(label, icon_name)`` pairs."""

    def __init__(self, parent, theme, options, selected=0, command=None,
                 mark="both", min_w=170, bg="bg"):
        self.options = [(o, None) if isinstance(o, str) else tuple(o)
                        for o in options]
        self.selected = selected
        self.command = command
        self.mark = mark
        self._open = False
        self._popup = None
        self._has_icons = any(ic for _, ic in self.options)
        longest = max(measure(9, lbl) for lbl, _ in self.options)
        w = max(s(min_w), s(14) + (s(26) if self._has_icons else 0) + longest
                + s(34))
        super().__init__(parent, theme, w, s(32), bg=bg)
        self.canvas.bind("<Button-1>", lambda e: self.toggle())

    # -- trigger -----------------------------------------------------------
    def draw(self):
        c, t = self.canvas, self.theme
        lbl, ic = self.options[self.selected]
        rounded_rect(c, s(1), s(1), self.w - s(1), s(31), t["r_control"],
                     fill=t["hover"] if self._hover else t["chip"])
        tx = s(14)
        if self._has_icons and ic:
            put_icon(c, s(22), s(16), icons.load(ic, 16, t["fg"]))
            tx = s(40)
        c.create_text(tx, s(16), text=lbl, anchor="w", fill=t["fg"], font=font(9))
        put_icon(c, self.w - s(16), s(16),
                 icons.chevron("up" if self._open else "down", 14, t["fg_dim"]))

    # -- popup -------------------------------------------------------------
    def toggle(self):
        self.close() if self._open else self.open()

    def open(self):
        if self._popup:
            return
        t = self.theme
        self._open = True
        self.repaint()
        pop = tk.Toplevel(self.canvas)
        pop.overrideredirect(True)
        try:
            pop.attributes("-topmost", True)
        except tk.TclError:
            pass
        pop.configure(bg=t["border"])
        inner = tk.Frame(pop, bg=t["panel"])
        inner.pack(fill="both", expand=True, padx=s(1), pady=s(1))
        for i, (lbl, ic) in enumerate(self.options):
            self._row(inner, i, lbl, ic)
        self.canvas.update_idletasks()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty() + self.h + s(4)
        pop.geometry(f"+{x}+{y}")
        pop.bind("<Escape>", lambda e: self.close())
        try:
            pop.focus_force()
            pop.bind("<FocusOut>", lambda e: self.close())
        except tk.TclError:
            pass
        self._popup = pop

    def _row(self, parent, i, lbl, ic):
        t = self.theme
        is_sel = (i == self.selected)
        tint = is_sel and self.mark in ("colour", "both")
        base = mix(t["panel"], t["accent"], 0.26) if tint else t["panel"]
        cv = tk.Canvas(parent, height=s(22), width=self.w - s(2), bg=base,
                       highlightthickness=0, cursor="hand2")
        cv.pack(fill="x")
        tx = s(14)
        if self._has_icons and ic:
            put_icon(cv, s(22), s(11), icons.load(ic, 16,
                                                  t["accent"] if tint else t["fg"]))
            tx = s(40)
        cv.create_text(tx, s(11), text=lbl, anchor="w", fill=t["fg"],
                       font=font(9))
        if is_sel and self.mark in ("check", "both"):
            put_icon(cv, self.w - s(20), s(11), icons.load("check", 14,
                                                           t["accent"]))
        cv.bind("<Button-1>", lambda e, idx=i: self._choose(idx))
        cv.bind("<Enter>", lambda e: cv.configure(bg=mix(base, t["hover"], 0.6)))
        cv.bind("<Leave>", lambda e: cv.configure(bg=base))

    def _choose(self, i):
        self.selected = i
        self.close()
        if self.command:
            self.command(i, self.options[i][0])

    def close(self):
        self._open = False
        if self._popup:
            try:
                self._popup.destroy()
            except tk.TclError:
                pass
            self._popup = None
        self.repaint()


# ----------------------------------------------------------------------------
# MultiDropdown — a closed trigger that opens a tick-many menu
# ----------------------------------------------------------------------------
class MultiDropdown(CanvasControl):
    """A multi-select: a trigger chip summarising how many of ``options`` are
    ticked, and a pop-up where each row toggles independently and the menu
    stays open. ``selected`` is an iterable of indices; options are plain
    strings or ``(label, icon_name)`` pairs."""

    def __init__(self, parent, theme, options, selected=(), command=None,
                 placeholder="Select…", min_w=180, bg="bg"):
        self.options = [(o, None) if isinstance(o, str) else tuple(o)
                        for o in options]
        self.selected = set(selected)
        self.command = command
        self.placeholder = placeholder
        self._open = False
        self._popup = None
        self._rows = []
        self._has_icons = any(ic for _, ic in self.options)
        longest = max(measure(9, lbl) for lbl, _ in self.options)
        w = max(s(min_w), s(14) + longest + s(46))
        super().__init__(parent, theme, w, s(32), bg=bg)
        self.canvas.bind("<Button-1>", lambda e: self.toggle())

    def values(self):
        "The ticked option labels, in option order."
        return [self.options[i][0] for i in sorted(self.selected)]

    # -- closed trigger ----------------------------------------------------
    def _summary(self):
        labels = self.values()
        if not labels:
            return self.placeholder, "fg_dim"
        if len(labels) <= 2:
            return ", ".join(labels), "fg"
        return "%d selected" % len(labels), "fg"

    def draw(self):
        c, t = self.canvas, self.theme
        rounded_rect(c, s(1), s(1), self.w - s(1), s(31), t["r_control"],
                     fill=t["hover"] if self._hover else t["chip"])
        text, fg = self._summary()
        c.create_text(s(14), s(16), text=text, anchor="w", fill=t[fg],
                      font=font(9))
        put_icon(c, self.w - s(16), s(16),
                 icons.chevron("up" if self._open else "down", 14, t["fg_dim"]))

    # -- popup -------------------------------------------------------------
    def toggle(self):
        self.close() if self._open else self.open()

    def open(self):
        if self._popup:
            return
        t = self.theme
        self._open = True
        self.repaint()
        pop = tk.Toplevel(self.canvas)
        pop.overrideredirect(True)
        try:
            pop.attributes("-topmost", True)
        except tk.TclError:
            pass
        pop.configure(bg=t["border"])
        inner = tk.Frame(pop, bg=t["panel"])
        inner.pack(fill="both", expand=True, padx=s(1), pady=s(1))
        self._rows = []
        for i, (lbl, ic) in enumerate(self.options):
            self._add_row(inner, i, lbl, ic)
        self.canvas.update_idletasks()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty() + self.h + s(4)
        pop.geometry("+%d+%d" % (x, y))
        pop.bind("<Escape>", lambda e: self.close())
        try:
            pop.focus_force()
            pop.bind("<FocusOut>", lambda e: self.close())
        except tk.TclError:
            pass
        self._popup = pop

    def _add_row(self, parent, i, lbl, ic):
        cv = tk.Canvas(parent, height=s(22), width=self.w - s(2),
                       highlightthickness=0, cursor="hand2")
        cv.pack(fill="x")
        cv.bind("<Button-1>", lambda e, idx=i: self._toggle_row(idx))
        cv.bind("<Enter>", lambda e, idx=i: self._paint_row(idx, True))
        cv.bind("<Leave>", lambda e, idx=i: self._paint_row(idx, False))
        self._rows.append((cv, lbl, ic))
        self._paint_row(i, False)

    def _paint_row(self, i, hover):
        t = self.theme
        cv, lbl, ic = self._rows[i]
        on = i in self.selected
        base = mix(t["panel"], t["accent"], 0.22) if on else t["panel"]
        if hover:
            base = mix(base, t["hover"], 0.6)
        cv.configure(bg=base)
        cv.delete("all")
        if on:                                 # ticked box + check
            aa_round_rect(cv, s(12), s(5), s(24), s(17), s(4), fill=t["accent"],
                          behind=base)
            put_icon(cv, s(18), s(11), icons.load("check", 11, t["on_accent"]))
        else:                                  # empty box
            aa_round_rect(cv, s(12), s(5), s(24), s(17), s(4), outline=t["ring"],
                          width=s(2), behind=base)
        tx = s(36)
        if self._has_icons and ic:
            put_icon(cv, s(44), s(11),
                     icons.load(ic, 16, t["accent"] if on else t["fg"]))
            tx = s(60)
        cv.create_text(tx, s(11), text=lbl, anchor="w", fill=t["fg"], font=font(9))

    def _toggle_row(self, i):
        self.selected.discard(i) if i in self.selected else self.selected.add(i)
        self._paint_row(i, True)
        self.repaint()                         # refresh the trigger summary
        if self.command:
            self.command(self.values())

    def close(self):
        self._open = False
        if self._popup:
            try:
                self._popup.destroy()
            except tk.TclError:
                pass
            self._popup = None
        self.repaint()
