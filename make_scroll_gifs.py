#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-scroll preview GIFs for the project cards (krishnash648-style).

Takes a tall full-page screenshot of a live site and pans a viewport-sized
window down it, so the card shows the whole site scrolling on a loop.

Trick for small files: holds are done with per-frame DURATION (not duplicate
frames), and every frame is quantised to ONE shared adaptive palette so colours
stay stable and the GIF compresses well.

  assets/_drinkit_full.png   -> assets/drinkit.gif
  assets/_portfolio_full.png -> assets/portfolio.gif
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")

CROP_H = 468         # viewport window height  (~1.62 card ratio)
STEP_MS = 80         # ms per pan frame
HOLD_TOP = 1000      # ms hold at top
HOLD_BOT = 1300      # ms hold at bottom


def ease(t):         # ease-in-out cubic
    return 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2)**3 / 2


def make(src, dst, width=760, n_pan=42, colors=132):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    nh = round(h * width / w)
    im = im.resize((width, nh), Image.LANCZOS)

    crop_h = min(CROP_H, nh)
    dist = max(0, nh - crop_h)

    # shared palette from the full (downscaled) image -> stable colours, small file
    pal_img = im.convert("P", palette=Image.ADAPTIVE, colors=colors)

    frames, durs = [], []
    n = 1 if dist == 0 else n_pan
    for i in range(n):
        t = 0 if n == 1 else i / (n - 1)
        y = round(ease(t) * dist)
        fr = im.crop((0, y, width, y + crop_h)).quantize(palette=pal_img, dither=Image.NONE)
        frames.append(fr)
        durs.append(STEP_MS)
    durs[0] = HOLD_TOP
    durs[-1] = HOLD_BOT

    frames[0].save(dst, save_all=True, append_images=frames[1:], loop=0,
                   duration=durs, disposal=2, optimize=True)
    kb = os.path.getsize(dst) // 1024
    print(f"{os.path.basename(dst):16s} {width}x{crop_h}  frames={len(frames)}  {kb}KB")


if __name__ == "__main__":
    # DrinKit page is very tall -> more frames; Portfolio is short & image-rich -> fewer
    make(os.path.join(A, "_drinkit_full.png"),   os.path.join(A, "drinkit.gif"),
         width=760, n_pan=44, colors=128)
    make(os.path.join(A, "_portfolio_full.png"), os.path.join(A, "portfolio.gif"),
         width=720, n_pan=24, colors=112)
