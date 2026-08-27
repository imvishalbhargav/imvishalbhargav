#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Animated dithered terminal banner for GitHub profile.
Subject: Vishal Bhargav (@imvishalbhargav)  -- Cloud & DevOps focus.

Pipeline (per Master Prompt spirit):
  photo -> crop head+shoulders -> autocontrast+contrast+unsharp
        -> Floyd-Steinberg serpentine 1-bit dither (single hue, tone from density)
  dark  : background segmented out, dots draw the LIT subject
  light : background kept, dots draw the DARK parts

Outputs (into this folder):
  dark.svg, light.svg            <- the animated deliverables (SMIL)
  dark_preview.png, light_preview.png <- static final-state previews (for eyeballing)
"""

import os, math, random
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont
from scipy import ndimage

random.seed(7)
np.random.seed(7)

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = r"C:\Users\vishjal\Downloads\pfp4.jpeg"

# ----------------------------------------------------------------------------
# Layout (SVG user units == preview px at scale 1)
# ----------------------------------------------------------------------------
W, H = 1180, 610
TITLE_H = 42

# left portrait panel
PANEL_L = 24
PANEL_L_W = 430
# portrait dot box (inside left panel)
PX0, PY0 = 46, 96
PW, PH = 386, 436
COLS = 150
PITCH = PW / COLS
ROWS = int(round(PH / PITCH))
DOT = PITCH * 1.02  # slight overlap kills hairline gaps

# right info panel
INFO_L = 480
INFO_R = 1150
ROW_Y0 = 150
ROW_DY = 20.5
LABEL_X = INFO_L + 8
VALUE_R = INFO_R - 10

N_GROUPS = 60           # shimmer-in groups (random spatial -> appears everywhere)
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"
FONT_MONO_B = r"C:\Windows\Fonts\consolab.ttf"

# ----------------------------------------------------------------------------
# Content
# ----------------------------------------------------------------------------
NAME = "Vishal Bhargav"
HANDLE = "@imvishalbhargav"
ROWS_INFO = [
    ("sec", "SYSTEM"),
    ("Subject",   "Vishal Bhargav"),
    ("Role",      "Cloud & DevOps Engineer"),
    ("Origin",    "Jaipur, India"),
    ("Education", "B.Tech CSE - Arya College"),
    ("Status",    "Building - Learning - Shipping"),
    ("ToolChain", "VSCode - Git - Docker - TF"),
    ("sec", "CORE"),
    ("Lang",      "Python - C - C++"),
    ("Cloud",     "AWS - GCP"),
    ("Container", "Docker - K8s - Helm"),
    ("IaC",       "Terraform - Ansible"),
    ("CI/CD",     "GitHub Actions"),
    ("Monitor",   "Grafana - ELK"),
    ("sec", "GRID"),
    ("Mail",      "imvishalbhargav@gmail.com"),
    ("Portfolio", "imvishalbhargav.vercel.app"),
    ("LinkedIn",  "/in/imvishalbhargav"),
    ("GitHub",    "imvishalbhargav"),
]

THEMES = {
    "dark": dict(
        bg="#0A101F", panel="#0D1526", stroke="#1B2740",
        dot="#F43F5E", head="#22D3EE", label="#8FA3BF", value="#F1F5F9",
        dim="#5A6B85", leader="#26324A", accent="#10B981", pill_bg="#132033",
        titlebar="#0C1322", frame="#22304C",
    ),
    "light": dict(
        bg="#F4F7FB", panel="#FFFFFF", stroke="#D6E0EC",
        dot="#E11D48", head="#0891B2", label="#475569", value="#0F172A",
        dim="#94A3B8", leader="#CBD5E1", accent="#059669", pill_bg="#EDF3FA",
        titlebar="#EAF0F7", frame="#C6D3E2",
    ),
}


# ----------------------------------------------------------------------------
# Image -> ink field
# ----------------------------------------------------------------------------
def load_crop():
    im = Image.open(PHOTO).convert("RGB")
    w, h = im.size
    target = COLS / ROWS  # width/height
    # crop to target aspect, centered horizontally, biased slightly up (headroom)
    if w / h > target:
        nw = int(h * target); x0 = (w - nw) // 2
        im = im.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w / target); y0 = int((h - nh) * 0.42)
        im = im.crop((0, y0, w, y0 + nh))
    return im


def build_fields():
    im = load_crop()
    # grayscale + contrast pipeline
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.3)
    g = g.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    g = g.resize((COLS, ROWS), Image.LANCZOS)
    G = np.asarray(g, dtype=np.float32) / 255.0

    # foreground mask from color distance to white (studio bg is near-white)
    rgb = np.asarray(im.resize((COLS, ROWS), Image.LANCZOS), dtype=np.float32)
    dist = np.sqrt(((255.0 - rgb) ** 2).sum(axis=2))
    fg = dist > 60.0
    fg = ndimage.binary_closing(fg, np.ones((3, 3)), iterations=2)
    fg = ndimage.binary_fill_holes(fg)
    lbl, n = ndimage.label(fg)
    if n:
        sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
        fg = lbl == (int(np.argmax(sizes)) + 1)

    ink_dark = (G * fg)            # lit subject only
    ink_light = (1.0 - G)          # dark parts of full image
    return ink_dark, ink_light


def dither(ink):
    """Floyd-Steinberg, serpentine, 1-bit. ink in [0,1], 1 == full ink."""
    h, w = ink.shape
    img = ink.astype(np.float32).copy()
    out = np.zeros((h, w), np.uint8)
    for y in range(h):
        ltr = (y % 2 == 0)
        xr = range(w) if ltr else range(w - 1, -1, -1)
        for x in xr:
            old = img[y, x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = 1 if new else 0
            err = old - new
            if ltr:
                if x + 1 < w: img[y, x + 1] += err * 0.4375
                if y + 1 < h:
                    if x - 1 >= 0: img[y + 1, x - 1] += err * 0.1875
                    img[y + 1, x] += err * 0.3125
                    if x + 1 < w: img[y + 1, x + 1] += err * 0.0625
            else:
                if x - 1 >= 0: img[y, x - 1] += err * 0.4375
                if y + 1 < h:
                    if x + 1 < w: img[y + 1, x + 1] += err * 0.1875
                    img[y + 1, x] += err * 0.3125
                    if x - 1 >= 0: img[y + 1, x - 1] += err * 0.0625
    return out


def runs(bitmap):
    """Row run-length -> list of (x,y,w,h) rects in dot-box coordinates."""
    rects = []
    h, w = bitmap.shape
    for r in range(h):
        c = 0
        while c < w:
            if bitmap[r, c]:
                c0 = c
                while c < w and bitmap[r, c]:
                    c += 1
                x = PX0 + c0 * PITCH
                y = PY0 + r * PITCH
                width = (c - c0) * PITCH + (DOT - PITCH)
                rects.append((x, y, width, DOT))
            else:
                c += 1
    return rects


# ----------------------------------------------------------------------------
# SVG
# ----------------------------------------------------------------------------
def fmt(v): return f"{v:.2f}".rstrip("0").rstrip(".")


def xesc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rects_to_path(rects):
    d = []
    for (x, y, w, h) in rects:
        d.append(f"M{fmt(x)} {fmt(y)}h{fmt(w)}v{fmt(h)}h{fmt(-w)}z")
    return "".join(d)


def cwidth(fs):  # monospace char width estimate
    return fs * 0.55


def build_svg(rects, T, mode):
    fs = 13.0
    cw = cwidth(fs)
    groups = [[] for _ in range(N_GROUPS)]
    for rc in rects:
        groups[random.randrange(N_GROUPS)].append(rc)

    P = []
    P.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" font-family="\'JetBrains Mono\',\'Consolas\',monospace">')
    # bg + frame
    P.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="14" fill="{T["bg"]}"/>')
    P.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="13" fill="none" '
             f'stroke="{T["stroke"]}" stroke-width="1"/>')
    # title bar
    P.append(f'<rect x="1" y="1" width="{W-2}" height="{TITLE_H}" rx="13" fill="{T["titlebar"]}"/>')
    P.append(f'<rect x="1" y="{TITLE_H-8}" width="{W-2}" height="10" fill="{T["titlebar"]}"/>')
    P.append(f'<line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}" stroke="{T["stroke"]}"/>')
    for i, col in enumerate(["#FF5F56", "#FFBD2E", "#27C93F"]):
        P.append(f'<circle cx="{26+i*20}" cy="{TITLE_H/2}" r="6" fill="{col}"/>')
    P.append(f'<text x="96" y="{TITLE_H/2+4}" font-size="13" fill="{T["dim"]}">profile.sh --live</text>')
    P.append(f'<text x="{W-24}" y="{TITLE_H/2+4}" font-size="12" fill="{T["dim"]}" '
             f'text-anchor="end">~/ {xesc(HANDLE)}</text>')

    # left panel + portrait frame
    P.append(f'<rect x="{PANEL_L}" y="{TITLE_H+14}" width="{PANEL_L_W}" height="{H-TITLE_H-30}" '
             f'rx="10" fill="{T["panel"]}" stroke="{T["stroke"]}"/>')
    P.append(f'<text x="{PANEL_L+14}" y="{TITLE_H+34}" font-size="11" letter-spacing="2" '
             f'fill="{T["head"]}">VISUAL.MAP</text>')
    P.append(f'<circle cx="{PANEL_L+PANEL_L_W-20}" cy="{TITLE_H+30}" r="4" fill="{T["accent"]}">'
             f'<animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    fx, fy, fw, fh = PX0-8, PY0-8, PW+16, PH+16
    P.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="6" fill="none" '
             f'stroke="{T["frame"]}" stroke-dasharray="2 4"/>')
    P.append(f'<text x="{PANEL_L+14}" y="{H-42}" font-size="10" letter-spacing="1" '
             f'fill="{T["dim"]}">floyd-steinberg . serpentine . {COLS}x{ROWS}</text>')

    # portrait dots (shimmer-in groups) wrapped in a group that idles
    P.append(f'<g><animate attributeName="opacity" begin="3.1s" dur="9s" '
             f'values="1;0.94;1" repeatCount="indefinite"/>')
    for gi, grp in enumerate(groups):
        if not grp:
            continue
        begin = 0.2 + (gi / N_GROUPS) * 1.9 + random.uniform(-0.12, 0.12)
        begin = max(0.05, begin)
        P.append(f'<path d="{rects_to_path(grp)}" fill="{T["dot"]}" '
                 f'shape-rendering="crispEdges" opacity="0">'
                 f'<animate attributeName="opacity" begin="{begin:.2f}s" dur="0.6s" '
                 f'from="0" to="1" fill="freeze"/></path>')
    P.append('</g>')

    # right info panel heading + LIVE + handle pill
    P.append(f'<text x="{INFO_L}" y="{TITLE_H+34}" font-size="15" letter-spacing="1" '
             f'font-weight="bold" fill="{T["head"]}">SYSTEM.INFO</text>')
    # LIVE badge
    lx = INFO_R - 58
    P.append(f'<rect x="{lx}" y="{TITLE_H+18}" width="58" height="20" rx="5" '
             f'fill="none" stroke="{T["stroke"]}"/>')
    P.append(f'<circle cx="{lx+13}" cy="{TITLE_H+28}" r="4" fill="#FF4D4D">'
             f'<animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite"/></circle>')
    P.append(f'<text x="{lx+24}" y="{TITLE_H+32}" font-size="11" letter-spacing="1" '
             f'fill="#FF6B6B">LIVE</text>')
    # handle pill
    pill_w = (len(HANDLE) + 2) * cwidth(13) + 20
    P.append(f'<rect x="{INFO_L}" y="{TITLE_H+44}" width="{pill_w:.0f}" height="24" rx="12" '
             f'fill="{T["pill_bg"]}" stroke="{T["stroke"]}"/>')
    P.append(f'<circle cx="{INFO_L+14}" cy="{TITLE_H+56}" r="4" fill="{T["accent"]}"/>')
    P.append(f'<text x="{INFO_L+26}" y="{TITLE_H+60}" font-size="13" fill="{T["value"]}">{xesc(HANDLE)}</text>')

    # rows
    y = ROW_Y0
    for kind, *rest in ROWS_INFO:
        if kind == "sec":
            (title,) = rest
            P.append(f'<line x1="{LABEL_X}" y1="{y-4}" x2="{INFO_R}" y2="{y-4}" '
                     f'stroke="{T["leader"]}"/>')
            P.append(f'<text x="{LABEL_X}" y="{y+9}" font-size="10" letter-spacing="3" '
                     f'fill="{T["dim"]}">{xesc(title)}</text>')
            y += ROW_DY + 4
            continue
        label, value = kind, rest[0]
        vlen = len(value) * cw
        # label
        P.append(f'<text x="{LABEL_X}" y="{y}" font-size="{fs}" fill="{T["label"]}">{xesc(label)}</text>')
        # value (locked width, right aligned)
        P.append(f'<text x="{VALUE_R}" y="{y}" font-size="{fs}" fill="{T["value"]}" '
                 f'text-anchor="end" textLength="{vlen:.1f}" '
                 f'lengthAdjust="spacingAndGlyphs">{xesc(value)}</text>')
        # dotted leader between label and value
        lead_x0 = LABEL_X + len(label) * cw + 8
        lead_x1 = VALUE_R - vlen - 8
        if lead_x1 > lead_x0:
            P.append(f'<line x1="{lead_x0:.1f}" y1="{y-4}" x2="{lead_x1:.1f}" y2="{y-4}" '
                     f'stroke="{T["leader"]}" stroke-dasharray="1 4"/>')
        y += ROW_DY
    P.append('</svg>')
    return "\n".join(P)


# ----------------------------------------------------------------------------
# PIL preview (final-state, no animation) -- for eyeballing only
# ----------------------------------------------------------------------------
def esc(s): return s


def build_preview(rects, T, path, scale=2):
    def S(v): return int(round(v * scale))
    img = Image.new("RGB", (S(W), S(H)), T["bg"])
    d = ImageDraw.Draw(img)
    fs = 13
    mono = ImageFont.truetype(FONT_MONO, S(fs))
    mono_sm = ImageFont.truetype(FONT_MONO, S(11))
    mono_xs = ImageFont.truetype(FONT_MONO, S(10))
    monob = ImageFont.truetype(FONT_MONO_B, S(15))

    d.rounded_rectangle([S(1), S(1), S(W-2), S(H-2)], radius=S(13),
                        fill=T["bg"], outline=T["stroke"], width=max(1, S(1)))
    # title bar
    d.rectangle([S(2), S(2), S(W-2), S(TITLE_H)], fill=T["titlebar"])
    d.line([0, S(TITLE_H), S(W), S(TITLE_H)], fill=T["stroke"])
    for i, col in enumerate(["#FF5F56", "#FFBD2E", "#27C93F"]):
        cx, cy = S(26+i*20), S(TITLE_H/2)
        d.ellipse([cx-S(6), cy-S(6), cx+S(6), cy+S(6)], fill=col)
    d.text((S(96), S(TITLE_H/2)), "profile.sh --live", font=mono, fill=T["dim"], anchor="lm")
    d.text((S(W-24), S(TITLE_H/2)), f"~/ {HANDLE}", font=mono_sm, fill=T["dim"], anchor="rm")

    # left panel
    d.rounded_rectangle([S(PANEL_L), S(TITLE_H+14), S(PANEL_L+PANEL_L_W), S(H-16)],
                        radius=S(10), fill=T["panel"], outline=T["stroke"], width=max(1, S(1)))
    d.text((S(PANEL_L+14), S(TITLE_H+28)), "V I S U A L . M A P", font=mono_sm, fill=T["head"], anchor="lm")
    ax, ay = S(PANEL_L+PANEL_L_W-20), S(TITLE_H+30)
    d.ellipse([ax-S(4), ay-S(4), ax+S(4), ay+S(4)], fill=T["accent"])
    fx, fy, fw, fh = PX0-8, PY0-8, PW+16, PH+16
    d.rounded_rectangle([S(fx), S(fy), S(fx+fw), S(fy+fh)], radius=S(6), outline=T["frame"], width=max(1, S(1)))
    d.text((S(PANEL_L+14), S(H-44)), f"floyd-steinberg . serpentine . {COLS}x{ROWS}",
           font=mono_xs, fill=T["dim"], anchor="lm")

    # portrait dots
    for (x, y, w, h) in rects:
        d.rectangle([S(x), S(y), S(x+w), S(y+h)], fill=T["dot"])

    # right panel heading
    d.text((S(INFO_L), S(TITLE_H+30)), "SYSTEM.INFO", font=monob, fill=T["head"], anchor="lm")
    lx = INFO_R - 58
    d.rounded_rectangle([S(lx), S(TITLE_H+18), S(lx+58), S(TITLE_H+38)], radius=S(5), outline=T["stroke"], width=max(1, S(1)))
    ex, ey = S(lx+13), S(TITLE_H+28)
    d.ellipse([ex-S(4), ey-S(4), ex+S(4), ey+S(4)], fill="#FF4D4D")
    d.text((S(lx+24), S(TITLE_H+28)), "LIVE", font=mono_sm, fill="#FF6B6B", anchor="lm")
    pill_w = (len(HANDLE)+2) * (13*0.55) + 20
    d.rounded_rectangle([S(INFO_L), S(TITLE_H+44), S(INFO_L+pill_w), S(TITLE_H+68)], radius=S(12),
                        fill=T["pill_bg"], outline=T["stroke"], width=max(1, S(1)))
    px, py = S(INFO_L+14), S(TITLE_H+56)
    d.ellipse([px-S(4), py-S(4), px+S(4), py+S(4)], fill=T["accent"])
    d.text((S(INFO_L+26), S(TITLE_H+56)), HANDLE, font=mono, fill=T["value"], anchor="lm")

    y = ROW_Y0
    for kind, *rest in ROWS_INFO:
        if kind == "sec":
            (title,) = rest
            d.line([S(LABEL_X), S(y-4), S(INFO_R), S(y-4)], fill=T["leader"])
            d.text((S(LABEL_X), S(y+4)), " ".join(title), font=mono_xs, fill=T["dim"], anchor="lm")
            y += ROW_DY + 4
            continue
        label, value = kind, rest[0]
        d.text((S(LABEL_X), S(y-4)), label, font=mono, fill=T["label"], anchor="lm")
        d.text((S(VALUE_R), S(y-4)), value, font=mono, fill=T["value"], anchor="rm")
        lw = mono.getlength(label) / scale
        vw = mono.getlength(value) / scale
        lead_x0 = LABEL_X + lw + 8
        lead_x1 = VALUE_R - vw - 8
        yy = S(y-4)
        x = lead_x0
        while x < lead_x1:
            d.line([S(x), yy, S(x+1), yy], fill=T["leader"], width=max(1, S(1)))
            x += 5
        y += ROW_DY

    img.save(path)
    return path


# ----------------------------------------------------------------------------
def main():
    ink_dark, ink_light = build_fields()
    out = {}
    for mode, ink in (("dark", ink_dark), ("light", ink_light)):
        bm = dither(ink)
        rects = runs(bm)
        T = THEMES[mode]
        svg = build_svg(rects, T, mode)
        sp = os.path.join(HERE, f"{mode}.svg")
        with open(sp, "w", encoding="utf-8") as f:
            f.write(svg)
        pp = os.path.join(HERE, f"{mode}_preview.png")
        build_preview(rects, T, pp)
        out[mode] = (len(rects), os.path.getsize(sp))
        print(f"{mode}: dots(runs)={len(rects)}  svg={out[mode][1]//1024}KB  grid={COLS}x{ROWS}")
    print("done")


if __name__ == "__main__":
    main()
