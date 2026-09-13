#!/usr/bin/env python3
"""Draw the cable + charger product images as PNGs (PIL, deterministic)."""
from PIL import Image, ImageDraw, ImageFont
import math

OUT_DIR = "/Users/shwetangmahudkar/Desktop/Mikoshi/site/mikoshi-img/gallery"
W, H = 736, 751
BG = (18, 21, 26)
INK = (233, 231, 226)
MUTED = (139, 144, 153)
DIM = (77, 84, 94)
ACCENT = (53, 224, 255)
SURF = (27, 32, 39)
SURF2 = (23, 27, 33)
EDGE = (42, 48, 58)

def F(size, bold=False):
    return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf", size)

# ---------------- cable ----------------
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

CX = W // 2
# loop geometry
LY0, LY1 = 300, 620          # loop top / bottom
LYC = (LY0 + LY1) // 2       # 460
RX, RY = 210, 160

# base cable ring (thick dark) + inner dark ring for depth
d.ellipse([CX - RX, LYC - RY, CX + RX, LYC + RY], outline=EDGE, width=26)
d.ellipse([CX - RX + 22, LYC - RY + 22, CX + RX - 22, LYC + RY - 22], outline=EDGE, width=8)

# dashed accent ring (braid glint): arcs
bbox = [CX - RX + 12, LYC - RY + 12, CX + RX - 12, LYC + RY - 12]
for a in range(0, 360, 24):
    d.arc(bbox, a, a + 13, fill=ACCENT, width=5)

# connector stubs: top connector bottom (250) -> loop top (300) ; loop bottom (620) -> bottom connector top
d.line([CX, 250, CX, 300], fill=EDGE, width=24)
d.line([CX, 620, CX, 650], fill=EDGE, width=24)

# top connector
d.rounded_rectangle([CX - 55, 130, CX + 55, 250], radius=18, fill=SURF, outline=EDGE, width=3)
d.rounded_rectangle([CX - 24, 106, CX + 24, 136], radius=6, fill=SURF2)
d.rounded_rectangle([CX - 24, 106, CX + 24, 120], radius=6, fill=ACCENT)

# bottom connector
d.rounded_rectangle([CX - 55, 650, CX + 55, 740], radius=18, fill=SURF, outline=EDGE, width=3)
d.rounded_rectangle([CX - 24, 740, CX + 24, 770], radius=6, fill=SURF2)
d.rounded_rectangle([CX - 24, 754, CX + 24, 768], radius=6, fill=ACCENT)

# labels INSIDE the loop (clear of strokes)
d.text((CX, 445), "E-MARKER", font=F(28, True), fill=ACCENT, anchor="mm")
d.text((CX, 495), "100W \u00b7 20V/5A", font=F(22), fill=INK, anchor="mm")
d.text((CX, 545), "1M / 2M / 3M", font=F(18), fill=MUTED, anchor="mm")

img.save(f"{OUT_DIR}/cable-100w.png")

# ---------------- charger ----------------
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

d.rounded_rectangle([228, 190, 508, 550], radius=34, fill=SURF, outline=EDGE, width=3)
d.rounded_rectangle([300, 255, 436, 445], radius=18, fill=SURF2)

# GaN glow rings (concentric)
d.ellipse([268, 290, 468, 490], outline=ACCENT, width=2)
d.ellipse([318, 340, 418, 440], outline=ACCENT, width=2)
d.text((368, 390), "GaN", font=F(26, True), fill=ACCENT, anchor="mm")

# USB-C port
d.rounded_rectangle([356, 452, 380, 478], radius=6, fill=(11, 13, 16))
d.rounded_rectangle([362, 458, 374, 470], radius=3, fill=ACCENT)

# prongs
d.rounded_rectangle([306, 140, 336, 208], radius=6, fill=EDGE)
d.rounded_rectangle([400, 140, 430, 208], radius=6, fill=EDGE)
d.rounded_rectangle([312, 552, 332, 574], radius=4, fill=(11, 13, 16))
d.rounded_rectangle([404, 552, 424, 574], radius=4, fill=(11, 13, 16))

# labels
d.text((368, 118), "20W PD CHARGER", font=F(26, True), fill=INK, anchor="mm")
d.text((368, 616), "ETL CERTIFIED", font=F(22, True), fill=ACCENT, anchor="mm")
d.text((368, 660), "PD 3.0 \u00b7 QC 3.0 \u00b7 5 COLOURS", font=F(16), fill=MUTED, anchor="mm")
img.save(f"{OUT_DIR}/charger-20w-gan.png")

print("PNGs saved")
