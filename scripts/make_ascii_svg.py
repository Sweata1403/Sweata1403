"""
Convert a portrait photo into a CLEAN, monochrome ASCII-art SVG (Andrew6rant
style: one light-gray color, subject isolated on a dark background) that "types"
itself in like a terminal, then holds.

Monochrome is deliberate -- per-character rainbow color is what makes ASCII
portraits look noisy. One fill color + a good density ramp + high contrast (so a
busy background washes out to blank) reads as neat and legible.

GitHub renders SVGs embedded via <img> and runs their SMIL animations there (JS
does not run). The whole portrait is revealed by ONE continuous top-to-bottom
clip growth (eased, not 53 separate per-row snaps -- that reads as choppy), with
a glowing scan-beam riding the exact same eased timing so the two stay locked,
then freezes.
"""
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# defaults to the prepped grayscale image (see prep_photo.py), which already has
# the background removed + local contrast applied.
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "avi-ascii.svg")

COLS = 100
ROWS = 53
CELL_W = 8
CELL_H = 15
RAMP = " .`:-=+*cs#%@"  # bright(sparse) -> dark(dense); leading space clears bg
USER = "sweata1403"
NAME = "Sweata Chakraborty"

# the prepped image already has bg removed + CLAHE local contrast, so only
# light global tuning is needed here.
CONTRAST = 1.05
BRIGHTNESS = 1.0
GAMMA = 0.45          # <1 brightens mids -> face lands in sparser chars
SHARPEN = False
WHITE_FLOOR = 0.82    # luminance above this is forced to blank (space)

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"      # the single ascii color (matches Andrew6rant)
ACCENT = "#22d3ee"   # scan-line / HUD accent (matches info-card.py's ACCENT)

# ---- reveal timing (single continuous eased sweep, looping) ---------------
TOTAL_SCAN = 2.8      # how long the top->bottom reveal takes. make_info_card.py's
                       # SCAN_SYNC should match this so the info panel "pops up"
                       # right as the portrait finishes scanning
EASE = "0.22 0.61 0.36 1"  # ease-out spline shared by the clip reveal + scan beam
                            # so they never drift apart mid-animation
CYCLE = 15.0           # whole scan-and-hold sequence repeats every this many
                       # seconds. make_info_card.py's CYCLE should match.


def loop_anim(attr, keyframes, calc_mode="linear", key_splines=None, extra=""):
    """A <animate> that repeats forever on a CYCLE-second clock. `keyframes` is
    a list of (absolute_time_seconds, value) pairs; the last time must be
    CYCLE so the loop wraps cleanly back to the first value."""
    times = ";".join(f"{t / CYCLE:.4f}" for t, _ in keyframes)
    values = ";".join(str(v) for _, v in keyframes)
    splines = f' keySplines="{key_splines}"' if calc_mode == "spline" and key_splines else ""
    return (f'<animate attributeName="{attr}" values="{values}" keyTimes="{times}" '
            f'calcMode="{calc_mode}"{splines} dur="{CYCLE}s" begin="0s" '
            f'repeatCount="indefinite" {extra}/>')

# ---- 1. sample the image into a COLS x ROWS grayscale grid ----------------
im = Image.open(SRC).convert("L")               # grayscale
if SHARPEN:
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))
im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
im = ImageEnhance.Contrast(im).enhance(CONTRAST)
im = im.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

STATIC = bool(os.environ.get("STATIC"))  # emit frozen state for previews

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        lum = px[x, y] / 255.0
        lum = pow(lum, GAMMA)
        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue
        idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
        idx = max(0, min(len(RAMP) - 1, idx))
        chars.append(RAMP[idx])
    rows_txt.append("".join(chars))

art_top = TITLEBAR_H + PAD * 0.35

# ---- 2. assemble SVG ------------------------------------------------------
parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, '
    f'Menlo, Consolas, monospace">'
)
parts.append('<defs>'
             f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
             f'</linearGradient>'
             f'<linearGradient id="scanGlow" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>'
             f'<stop offset="0.5" stop-color="{ACCENT}" stop-opacity="0.5"/>'
             f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>'
             f'</linearGradient>'
             f'<filter id="glow" x="-50%" y="-200%" width="200%" height="500%">'
             f'<feGaussianBlur stdDeviation="2.2"/></filter>'
             f'<clipPath id="scanReveal"><rect x="{PAD}" y="{art_top:.1f}" width="{ART_W}" height="0">'
             + loop_anim("height", [(0, 0), (TOTAL_SCAN, ART_H), (CYCLE, ART_H)],
                         calc_mode="spline", key_splines=f"{EASE};0 0 1 1") +
             f'</rect></clipPath>'
             '</defs>')

parts.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>')
parts.append(f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
             f'fill="none" stroke="{FRAME}" stroke-width="1"/>')

parts.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
             f'text-anchor="middle">{USER}@github: ~$ ./portrait.sh</text>')

# targeting-frame corner brackets around the art area (HUD "scanning" framing)
BRACKET = 14
bx0, by0 = PAD - 6, art_top - 6
bx1, by1 = PAD + ART_W + 6, art_top + ART_H + 6
for cx, cy, dx, dy in [(bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)]:
    parts.append(
        f'<path d="M{cx} {cy+dy*BRACKET} L{cx} {cy} L{cx+dx*BRACKET} {cy}" '
        f'stroke="{ACCENT}" stroke-width="1.5" fill="none" opacity="0.7"/>'
    )

# one <text> per row (single color -> no per-char markup, tiny file). All rows
# render immediately and are revealed together by the single clip-path growth
# above -- one continuous eased sweep instead of 53 separate row snaps.
font_size = CELL_H * 0.86
row_texts = []
for ry, line in enumerate(rows_txt):
    y = art_top + ry * CELL_H + CELL_H * 0.74
    safe = html.escape(line)
    row_texts.append(
        f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
        f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>'
    )

if STATIC:
    parts.extend(row_texts)
else:
    parts.append(f'<g clip-path="url(#scanReveal)">{"".join(row_texts)}</g>')

    # scanning beam: a glowing bar riding the exact same eased curve as the
    # clip reveal above, so the "light" and the reveal edge never drift apart.
    # Fades out right after it reaches the bottom, then the whole thing loops.
    y0, y1 = art_top - 9, art_top + ART_H - 9
    parts.append(
        f'<rect x="{PAD}" y="{art_top:.1f}" width="{ART_W}" height="18" fill="url(#scanGlow)">'
        + loop_anim("y", [(0, f"{y0:.1f}"), (TOTAL_SCAN, f"{y1:.1f}"), (CYCLE, f"{y1:.1f}")],
                    calc_mode="spline", key_splines=f"{EASE};0 0 1 1")
        + loop_anim("opacity", [(0, 1), (TOTAL_SCAN, 1), (TOTAL_SCAN + 0.01, 0), (CYCLE, 0)],
                    calc_mode="discrete")
        + '</rect>'
    )
    y0, y1 = art_top, art_top + ART_H
    parts.append(
        f'<rect x="{PAD}" y="{art_top:.1f}" width="{ART_W}" height="2" fill="{ACCENT}" filter="url(#glow)">'
        + loop_anim("y", [(0, f"{y0:.1f}"), (TOTAL_SCAN, f"{y1:.1f}"), (CYCLE, f"{y1:.1f}")],
                    calc_mode="spline", key_splines=f"{EASE};0 0 1 1")
        + loop_anim("opacity", [(0, 1), (TOTAL_SCAN, 1), (TOTAL_SCAN + 0.01, 0), (CYCLE, 0)],
                    calc_mode="discrete")
        + '</rect>'
    )

# status bar: a "scanning" line that fades out right as the sweep finishes,
# handing off to the normal whoami line with a steady blinking cursor
status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
status_y = status_line_y + 19
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')

WHOAMI_IN = TOTAL_SCAN + 0.35  # when the whoami line finishes fading in

if not STATIC:
    parts.append(
        f'<text x="{PAD}" y="{status_y:.1f}" fill="{ACCENT}" font-size="13">'
        f'{USER}@github:~$ scan --face <tspan opacity="0.85">[analyzing...]</tspan>'
        + loop_anim("opacity", [(0, 1), (TOTAL_SCAN - 0.3, 1), (TOTAL_SCAN, 0), (CYCLE, 0)])
        + '</text>'
    )

whoami_opacity = '1' if STATIC else '0'
whoami_reveal = '' if STATIC else loop_anim(
    "opacity", [(0, 0), (TOTAL_SCAN, 0), (WHOAMI_IN, 1), (CYCLE, 1)]
)
parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13" opacity="{whoami_opacity}">'
             f'{USER}@github:~$ whoami <tspan fill="{INK}">{html.escape(NAME)}</tspan>{whoami_reveal}</text>')
cursor_x = PAD + 172 + len(USER) * 8
if STATIC:
    parts.append(f'<rect x="{cursor_x}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}" opacity="0.85">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
                 f'begin="0s" dur="1s" repeatCount="indefinite"/></rect>')
else:
    # gate visibility on the 15s loop clock; the blink itself just runs forever
    # underneath, so it doesn't need to be re-synced every cycle
    parts.append(
        f'<g opacity="0">'
        + loop_anim("opacity", [(0, 0), (WHOAMI_IN, 0), (WHOAMI_IN + 0.01, 1), (CYCLE, 1)], calc_mode="discrete")
        + f'<rect x="{cursor_x}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}" opacity="0">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
        f'begin="{WHOAMI_IN:.2f}s" dur="1s" repeatCount="indefinite"/></rect>'
        f'</g>'
    )

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", CANVAS_W, "x", CANVAS_H)
