#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cinematic tech-stack CHIPS for the "Full toolbelt" section — same premium
recipe as generate_buttons.py (3D gradient + bevel + top gloss + soft glow +
gliding shine via SMIL) but sized as compact pills and coloured per brand.

Shines are STAGGERED (per-chip begin offset) so 24 chips don't sweep in unison.
Text/icon colour auto-picks dark vs white from the base's luminance.

Outputs -> assets/tech/<name>.svg   (brand icons baked in from assets/tech/_icons.json)
"""
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))
TDIR = os.path.join(HERE, "assets", "tech")
os.makedirs(TDIR, exist_ok=True)
ICONS = json.load(open(os.path.join(TDIR, "_icons.json")))

# ---- colour helpers ----
def hx(c):
    c = c.lstrip("#"); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
def rgbs(t): return "#%02X%02X%02X" % t
def mix(c, tgt, f):
    a = hx(c); return rgbs(tuple(round(a[i] + (tgt[i] - a[i]) * f) for i in range(3)))
def light(c, f): return mix(c, (255, 255, 255), f)
def dark(c, f):  return mix(c, (0, 0, 0), f)
def lum(c):
    r, g, b = hx(c); return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0

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

# ---- chip geometry ----
BH = 34          # chip height
PADX = 13        # inner side padding
ICON = 16        # icon box
GAP = 8          # icon -> text gap
FS = 12.5        # label font size
OP = 7           # outer padding (glow room)
RX = 9           # corner radius


def chip(name, label, base, slug, idx=0):
    tw = text_w(label, FS)
    has_icon = bool(ICONS.get(slug))
    W = round(PADX + (ICON + GAP if has_icon else 0) + tw + PADX + 2)
    SW, SH = W + OP * 2, BH + OP * 2
    bx, by = OP, OP

    # auto contrast: light base -> ink text/icon, else white
    ink = lum(base) > 0.62
    fg = "#0A101F" if ink else "#FFFFFF"

    top, bot = light(base, 0.18), dark(base, 0.22)
    edge = light(base, 0.5)
    lip = dark(base, 0.45)
    glow = light(base, 0.28)

    icon_svg = ""
    if has_icon:
        s = ICON / 24.0
        icx, icy = bx + PADX, by + (BH - ICON) / 2
        icon_svg = (f'<g transform="translate({icx:.1f},{icy:.1f}) scale({s:.4f})" '
                    f'fill="{fg}" opacity="0.96"><path d="{ICONS[slug]}"/></g>')
    tx = bx + PADX + (ICON + GAP if has_icon else 0)
    tcy = by + BH / 2

    d = (idx % 8) * 0.42                 # staggered shine start
    x0 = bx - BH * 1.1 - 20
    x1 = bx + W + BH * 1.1
    uid = name.replace("-", "").replace("+", "p")

    P = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" '
         f'viewBox="0 0 {SW} {SH}" fill="none" '
         f'font-family="\'Segoe UI\',\'Helvetica Neue\',Arial,sans-serif">']
    P.append("<defs>")
    P.append(f'<linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>')
    P.append(f'<linearGradient id="gl{uid}" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.4"/>'
             f'<stop offset="0.6" stop-color="#FFFFFF" stop-opacity="0.04"/>'
             f'<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>')
    P.append(f'<linearGradient id="sh{uid}" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>'
             f'<stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.6"/>'
             f'<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>')
    P.append(f'<clipPath id="c{uid}"><rect x="{bx}" y="{by}" width="{W}" height="{BH}" rx="{RX}"/></clipPath>')
    P.append(f'<filter id="f{uid}" x="-60%" y="-60%" width="220%" height="220%">'
             f'<feGaussianBlur stdDeviation="4"/></filter>')
    P.append("</defs>")
    # soft glow (gentle staggered pulse)
    P.append(f'<rect x="{bx}" y="{by}" width="{W}" height="{BH}" rx="{RX}" fill="{glow}" '
             f'filter="url(#f{uid})" opacity="0.4">'
             f'<animate attributeName="opacity" values="0.3;0.6;0.3" dur="3.2s" '
             f'begin="{d:.2f}s" repeatCount="indefinite" calcMode="spline" '
             f'keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/></rect>')
    # lip + body
    P.append(f'<rect x="{bx}" y="{by+2}" width="{W}" height="{BH}" rx="{RX}" fill="{lip}"/>')
    P.append(f'<rect x="{bx}" y="{by}" width="{W}" height="{BH}" rx="{RX}" '
             f'fill="url(#g{uid})" stroke="{edge}" stroke-opacity="0.55" stroke-width="1"/>')
    # top gloss
    P.append(f'<g clip-path="url(#c{uid})">'
             f'<rect x="{bx}" y="{by}" width="{W}" height="{BH*0.52:.1f}" fill="url(#gl{uid})"/></g>')
    # gliding shine
    P.append(f'<g clip-path="url(#c{uid})"><g transform="skewX(-20)">'
             f'<rect y="{by-BH}" width="20" height="{BH*3}" fill="url(#sh{uid})">'
             f'<animate attributeName="x" values="{x0:.0f};{x1:.0f};{x1:.0f}" '
             f'keyTimes="0;0.4;1" dur="3.6s" begin="{d:.2f}s" repeatCount="indefinite" '
             f'calcMode="spline" keySplines="0.45 0 0.15 1;0 0 1 1"/></rect></g></g>')
    if icon_svg:
        P.append(icon_svg)
    P.append(f'<text x="{tx:.1f}" y="{tcy:.1f}" font-size="{FS}" font-weight="700" '
             f'letter-spacing="0.2" fill="{fg}" dominant-baseline="central">{label}</text>')
    P.append("</svg>")
    open(os.path.join(TDIR, f"{name}.svg"), "w", encoding="utf-8").write("".join(P))
    return f"{name}.svg", SW


# name, label, brand base colour, icon slug
TECH = [
    # ☁️ Cloud & Containers
    ("aws", "AWS", "#FF9900", "amazonwebservices"),
    ("gcp", "Google Cloud", "#4285F4", "googlecloud"),
    ("docker", "Docker", "#2496ED", "docker"),
    ("kubernetes", "Kubernetes", "#326CE5", "kubernetes"),
    ("nginx", "Nginx", "#009639", "nginx"),
    # 🔧 IaC · CI/CD · Automation
    ("terraform", "Terraform", "#7B42BC", "terraform"),
    ("ansible", "Ansible", "#1A1918", "ansible"),
    ("ghactions", "GitHub Actions", "#2088FF", "githubactions"),
    ("jenkins", "Jenkins", "#D24939", "jenkins"),
    # 📊 Monitoring & Observability
    ("grafana", "Grafana", "#F46800", "grafana"),
    ("prometheus", "Prometheus", "#E6522C", "prometheus"),
    ("elastic", "Elastic", "#00BFB3", "elastic"),
    # 💾 Databases
    ("mongodb", "MongoDB", "#47A248", "mongodb"),
    ("mysql", "MySQL", "#00618A", "mysql"),
    # 👨‍💻 Languages
    ("python", "Python", "#3776AB", "python"),
    ("c", "C", "#5A93CF", "c"),
    ("cpp", "C++", "#00599C", "cplusplus"),
    ("bash", "Bash", "#4EAA25", "gnubash"),
    ("javascript", "JavaScript", "#F7DF1E", "javascript"),
    # 🛠️ OS & Tools
    ("linux", "Linux", "#FCC624", "linux"),
    ("git", "Git", "#F05032", "git"),
    ("github", "GitHub", "#4A535E", "github"),
    ("vscode", "VS Code", "#0A84D8", "visualstudiocode"),
    ("figma", "Figma", "#F24E1E", "figma"),
]

if __name__ == "__main__":
    for i, (name, label, base, slug) in enumerate(TECH):
        fn, w = chip(name, label, base, slug, idx=i)
        print(f"{fn:16s} {w}px  {'icon' if ICONS.get(slug) else 'TEXT-ONLY'}")
    print(f"\n{len(TECH)} chips -> assets/tech/")
