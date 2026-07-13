"""
Build a neofetch-style info card SVG (Andrew6rant style) to sit to the RIGHT of
the ASCII portrait: colored key/value rows for work experience, tech stack, and
highlights -- NOT GitHub stats (the contribution graph covers those).

Static content, hand-authored below. Lines fade/slide in on a short stagger so
it feels like the panel is printing alongside the portrait. STATIC=1 emits the
frozen state for Quick Look previews.
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

W, H = 480, 376
PAD = 20
TITLEBAR_H = 30
KEY_X = PAD
VAL_X = PAD + 92
LINE_H = 20.5

# keep in sync with make_ascii_svg.py's TOTAL_SCAN/CYCLE -- this panel stays
# blank ("awaiting scan...") until the portrait finishes its scan sweep, then
# pops in row by row, like a HUD pulling up a match, then the whole thing
# resets and loops every CYCLE seconds.
SCAN_SYNC = 2.8
CYCLE = 15.0


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

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
KEY = "#ffa657"      # orange keys (matches Andrew)
SECTION = "#58a6ff"  # blue section headers
GREEN = "#3fb950"
ACCENT = "#22d3ee"

# ===========================================================================
#  EDIT THIS  -- your info panel. It re-lays-out automatically; if it gets too
#  tall for the card, bump H above (and the width= in your profile README).
#  The username in the header is HOST below.
#
#  row types:
#    ("host",)              -> "you@github" header + rule
#    ("kv", key, value)     -> orange key + light value
#    ("sec", title)         -> blue "— title —" section rule
#    ("bul", text)          -> green dot + light bullet
#    ("gap",)               -> a little vertical space
# ===========================================================================
HOST = "sweata1403"   # shown as  sweata1403@github  in the header

ROWS = [
    ("host",),
    ("kv", "Role", "Senior SWE @ Capgemini"),
    ("kv", "Cert", "AWS SAA-C03 Certified"),
    ("kv", "Focus", "DevOps, Data Eng & Cloud Migration"),
    ("kv", "Learning", "PySpark, Terraform, Ansible"),
    ("gap",),
    ("sec", "Stack"),
    ("kv", "Languages", "Python, SQL, PySpark"),
    ("kv", "CI/CD", "GitHub Actions, CI/CD pipelines"),
    ("kv", "Cloud", "AWS, Azure"),
    ("kv", "GitHub", "Enterprise Automation (10K+ repos)"),
    ("gap",),
    ("sec", "Highlights"),
    ("bul", "AWS Solutions Architect Associate (SAA-C03) certified"),
    ("bul", "GitHub Enterprise Automation Expert (10K+ repos)"),
    ("bul", "Leading cloud migration & DevOps at Capgemini"),
]


def esc(s):
    return html.escape(s)


def rise(inner, i):
    """fade + slight upward slide, staggered by row index; loops every CYCLE."""
    if STATIC:
        return f"<g>{inner}</g>"
    delay = SCAN_SYNC + 0.15 + i * 0.075
    fade = loop_anim("opacity", [(0, 0), (delay, 0), (delay + 0.45, 1), (CYCLE, 1)])
    times = ";".join(f"{t / CYCLE:.4f}" for t in [0, delay, delay + 0.45, CYCLE])
    slide = (f'<animateTransform attributeName="transform" type="translate" '
             f'values="0 5;0 5;0 0;0 0" keyTimes="{times}" calcMode="spline" '
             f'keySplines="0 0 1 1;0.2 0.8 0.2 1;0 0 1 1" dur="{CYCLE}s" begin="0s" '
             f'repeatCount="indefinite"/>')
    return f'<g opacity="0" transform="translate(0,5)">{inner}{fade}{slide}</g>'


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<defs>'
    f'<linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#ibg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">{esc(HOST)}@github: ~$ neofetch</text>')

if not STATIC:
    # placeholder shown only while the portrait is mid-scan; swapped for the
    # real rows (via rise()) once SCAN_SYNC elapses, then hidden again until
    # the next loop. The pulse just runs forever underneath an on/off gate so
    # the two animations never fight over the same attribute.
    gate = loop_anim("opacity", [(0, 1), (SCAN_SYNC, 1), (SCAN_SYNC + 0.01, 0), (CYCLE, 0)], calc_mode="discrete")
    parts.append(
        f'<g opacity="1">{gate}'
        f'<text x="{KEY_X}" y="{TITLEBAR_H + 34}" fill="{ACCENT}" font-size="12.5">awaiting scan...'
        f'<animate attributeName="opacity" values="0.35;1;0.35" keyTimes="0;0.5;1" '
        f'dur="0.9s" repeatCount="indefinite"/></text></g>'
    )

y = TITLEBAR_H + 30
for i, row in enumerate(ROWS):
    kind = row[0]
    if kind == "gap":
        y += LINE_H * 0.5
        continue
    if kind == "host":
        host = esc(HOST)
        rule_x = KEY_X + (len(HOST) + 7) * 8 + 8
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" font-size="14" font-weight="700">'
                 f'<tspan fill="{GREEN}">{host}</tspan><tspan fill="{MUTED}">@</tspan>'
                 f'<tspan fill="{ACCENT}">github</tspan></text>'
                 f'<line x1="{rule_x}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "sec":
        title = esc(row[1])
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{SECTION}" font-size="12.5" font-weight="700">'
                 f'&#8212; {title}</text>'
                 f'<line x1="{KEY_X + 12 + len(row[1])*8}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "kv":
        key, val = esc(row[1]), esc(row[2])
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{KEY}" font-size="12.5" font-weight="700">{key}</text>'
                 f'<text x="{VAL_X}" y="{y:.1f}" fill="{INK}" font-size="12.5">{val}</text>')
    elif kind == "bul":
        txt = esc(row[1])
        inner = (f'<circle cx="{KEY_X+3}" cy="{y-4:.1f}" r="2.5" fill="{GREEN}"/>'
                 f'<text x="{KEY_X+14}" y="{y:.1f}" fill="{INK}" font-size="12.5">{txt}</text>')
    else:
        continue
    parts.append(rise(inner, i))
    y += LINE_H

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", W, "x", H, "content_bottom", round(y))
