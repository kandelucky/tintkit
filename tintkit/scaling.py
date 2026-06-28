"""TintKit — one global pixel scale.

Tkinter's ``tk scaling`` already scales fonts (point sizes) and text
measurement to the screen DPI. What it does NOT scale is the hard pixel
geometry we draw on canvases — a 36 px button stays 36 device px on a 150 %
screen and looks tiny. So every geometry literal in the kit goes through
``s()``; fonts, ``measure()`` and icon sizes are left alone (already real px).

``setup_dpi`` sets the factor once: ``S = screen_dpi / 96`` (1.0 at 100 %,
1.5 at 150 %). Geometry is authored against a 96-DPI baseline and scaled up.
"""

S = 1.0


def set_scale(value):
    "Set the global factor (screen DPI / 96). Called once by ``setup_dpi``."
    global S
    S = max(0.1, float(value))


def s(v):
    "Scale a baseline-96 pixel value to the active screen, rounded to an int."
    return int(round(v * S))
