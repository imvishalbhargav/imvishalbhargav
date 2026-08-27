#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cinematic, self-animating SVG buttons for the profile README.

GitHub sanitizes JS/CSS in READMEs, so real on-click animation is impossible.
These are the next best thing: premium 3D-gradient buttons that ANIMATE on their
own via SMIL — a soft pulsing glow + a glossy light sweep that keeps gliding
across the surface. Rendered as <img> so they animate on the profile.

Outputs -> assets/buttons/<name>.svg   (brand icons baked in from simple-icons)
"""
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))
BDIR = os.path.join(HERE, "assets", "buttons")
os.makedirs(BDIR, exist_ok=True)
ICONS = json.load(open(os.path.join(BDIR, "_icons.json")))

# in-house action glyphs (24x24 viewBox, filled)
GLYPHS = {
    "play":  "M8 5.5v13a1 1 0 0 0 1.5.87l11-6.5a1 1 0 0 0 0-1.74l-11-6.5A1 1 0 0 0 8 5.5z",
    "arrow": "M13.2 4.6 20.6 12l-7.4 7.4-1.7-1.7 4.5-4.5H3.4v-2.4h12.6l-4.5-4.5z",
    "spark": "M12 2l1.9 5.6L19.5 9l-4.6 3.4L16.3 18 12 14.7 7.7 18l1.4-5.6L4.5 9l5.6-1.4z",
}

# ---------- colour helpers ----------
def hx(c):
    c = c.lstrip("#"); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
def rgbs(t): return "#%02X%02X%02X" % t
def mix(c, tgt, f):
    a, b = hx(c), tgt
    return rgbs(tuple(round(a[i] + (b[i] - a[i]) * f) for i in range(3)))
def light(c, f): return mix(c, (255, 255, 255), f)
def dark(c, f):  return mix(c, (0, 0, 0), f)

# accurate text width via a bold system font (falls back to estimate)
_FONT = None
def text_w(s, fs):
    global _FONT
    try:
        from PIL import ImageFont
        if _FONT is None:
            _FONT = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 100)
        return _FONT.getlength(s) / 100.0 * fs
    except Exception:
        return len(s) * fs * 0.60

# ---------- geometry ----------
BH = 44          # button height
PADX = 19        # inner side padding
ICON = 18        # icon box
GAP = 11         # icon -> text gap
FS = 14.5        # label font size
LS = 0.2         # letter spacing
OP = 10          # outer padding (room for glow)
RX = 12          # corner radius


def button(name, label, base, glow, icon=None, glyph=None, stops=None,
           diagonal=False, tint="#FFFFFF", text="#FFFFFF"):
    """Emit one animated SVG button; width auto-fit to its label."""
    tw = text_w(label, FS)
    inner = PADX + (ICON + GAP if (icon or glyph) else 0) + tw + PADX
    W = round(inner + 4)                      # button width
    SW, SH = W + OP * 2, BH + OP * 2           # svg canvas (glow room)
    bx, by = OP, OP                            # button top-left

    top, bot = light(base, 0.16), dark(base, 0.20)
    edge = light(base, 0.45)
    lip = dark(base, 0.42)

    # gradient stops
    if stops:
        gstops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    else:
        gstops = (f'<stop offset="0" stop-color="{top}"/>'
                  f'<stop offset="1" stop-color="{bot}"/>')
    if diagonal:
        gcoord = 'x1="0" y1="0" x2="1" y2="1"'
    else:
        gcoord = 'x1="0" y1="0" x2="0" y2="1"'

    # icon markup
    icon_svg = ""
    icx = bx + PADX
    icy = by + (BH - ICON) / 2
    if icon and ICONS.get(icon):
        s = ICON / 24.0
        icon_svg = (f'<g transform="translate({icx:.1f},{icy:.1f}) scale({s:.4f})" '
                    f'fill="{tint}" opacity="0.97"><path d="{ICONS[icon]}"/></g>')
    elif glyph:
        s = ICON / 24.0
        icon_svg = (f'<g transform="translate({icx:.1f},{icy:.1f}) scale({s:.4f})" '
                    f'fill="{tint}" opacity="0.97"><path d="{GLYPHS[glyph]}"/></g>')

    tx = bx + PADX + (ICON + GAP if (icon or glyph) else 0)
    tcy = by + BH / 2

    # skewed shine band travel range
    x0 = bx - BH * 1.1 - 26
    x1 = bx + W + BH * 1.1

    uid = name.replace("-", "")
    P = []
    P.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" '
             f'viewBox="0 0 {SW} {SH}" fill="none" '
             f'font-family="\'Segoe UI\',\'Helvetica Neue\',Arial,sans-serif">')
    P.append("<defs>")
    P.append(f'<linearGradient id="g{uid}" {gcoord}>{gstops}</linearGradient>')
    P.append(f'<linearGradient id="gl{uid}" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.42"/>'
             f'<stop offset="0.55" stop-color="#FFFFFF" stop-opacity="0.06"/>'
             f'<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>')
    P.append(f'<linearGradient id="sh{uid}" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>'
             f'<stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.75"/>'
             f'<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>')
    P.append(f'<clipPath id="c{uid}"><rect x="{bx}" y="{by}" width="{W}" height="{BH}" rx="{RX}"/></clipPath>')
    P.append(f'<filter id="f{uid}" x="-60%" y="-60%" width="220%" height="220%">'
             f'<feGaussianBlur stdDeviation="5.5"/></filter>')
    P.append("</defs>")

    # 1) outer glow (blurred colour copy, pulsing)
    P.append(f'<rect x="{bx}" y="{by}" width="{W}" height="{BH}" rx="{RX}" '
             f'fill="{glow}" filter="url(#f{uid})" opacity="0.55">'
             f'<animate attributeName="opacity" values="0.4;0.85;0.4" dur="2.6s" '
             f'repeatCount="indefinite" calcMode="spline" '
             f'keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/></rect>')
    # 2) 3D lip (depth under the button)
    P.append(f'<rect x="{bx}" y="{by+2.5}" width="{W}" height="{BH}" rx="{RX}" fill="{lip}"/>')
    # 3) body
    P.append(f'<rect x="{bx}" y="{by}" width="{W}" height="{BH}" rx="{RX}" '
             f'fill="url(#g{uid})" stroke="{edge}" stroke-opacity="0.55" stroke-width="1"/>')
    # 4) glossy top dome (clipped)
    P.append(f'<g clip-path="url(#c{uid})">'
             f'<rect x="{bx}" y="{by}" width="{W}" height="{BH*0.55:.1f}" fill="url(#gl{uid})"/></g>')
    # 5) travelling shine (clipped, skewed, eased with a pause)
    P.append(f'<g clip-path="url(#c{uid})"><g transform="skewX(-20)">'
             f'<rect y="{by-BH}" width="24" height="{BH*3}" fill="url(#sh{uid})" opacity="0.55">'
             f'<animate attributeName="x" values="{x0:.0f};{x1:.0f};{x1:.0f}" '
             f'keyTimes="0;0.42;1" dur="3.4s" repeatCount="indefinite" '
             f'calcMode="spline" keySplines="0.45 0 0.15 1;0 0 1 1"/></rect></g></g>')
    # 6) icon + label
    if icon_svg:
        P.append(icon_svg)
    P.append(f'<text x="{tx:.1f}" y="{tcy:.1f}" font-size="{FS}" font-weight="700" '
             f'letter-spacing="{LS}" fill="{text}" dominant-baseline="central">{label}</text>')
    P.append("</svg>")

    open(os.path.join(BDIR, f"{name}.svg"), "w", encoding="utf-8").write("".join(P))
    return f"{name}.svg", SW, SH


# ---------- the button set ----------
BUTTONS = [
    # social row
    dict(name="linkedin",  label="LinkedIn",   base="#0A66C2", glow="#0A66C2", icon="linkedin"),
    dict(name="portfolio", label="Portfolio",  base="#0891B2", glow="#22D3EE", icon="vercel"),
    dict(name="email",     label="Email",      base="#D93F2B", glow="#F87171", icon="gmail"),
    dict(name="instagram", label="Instagram",  base="#C7377F", glow="#DD2A7B", icon="instagram",
         stops=[(0, "#F58529"), (0.5, "#DD2A7B"), (1, "#8134AF")], diagonal=True),
    dict(name="reddit",    label="Reddit",     base="#FF4500", glow="#FF6A33", icon="reddit"),
    # project 1 (DrinKit)
    dict(name="live-demo", label="Live Demo",  base="#10B981", glow="#34E4B0", glyph="play"),
    dict(name="src-cyan",  label="Source",     base="#1C2942", glow="#22D3EE", icon="github"),
    # project 2 (Portfolio)
    dict(name="visit-site", label="Visit Site", base="#0EA5C0", glow="#22D3EE", glyph="play"),
    dict(name="src-purple", label="Source",     base="#1C2942", glow="#A78BFA", icon="github"),
    # CTAs
    dict(name="see-more",   label="See more on my portfolio", base="#10B981", glow="#22D3EE",
         glyph="arrow", stops=[(0, "#0FA36B"), (1, "#0E7490")], diagonal=True),
    dict(name="connect-linkedin", label="Connect on LinkedIn", base="#0A66C2", glow="#3B82F6", icon="linkedin"),
    dict(name="say-hi",           label="Say hi via Email",    base="#10B981", glow="#34E4B0", icon="gmail"),
]

if __name__ == "__main__":
    for cfg in BUTTONS:
        fn, w, h = button(**cfg)
        print(f"{fn:28s} {w}x{h}")
    print(f"\n{len(BUTTONS)} buttons -> assets/buttons/")
