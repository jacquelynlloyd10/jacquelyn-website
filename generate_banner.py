#!/usr/bin/env python3
"""
Generates linkedin-banner.png at exactly 1584x396 pixels using Pillow.
Produces a clean, standard PNG that LinkedIn's uploader accepts.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1584, 396

NAVY       = (26,  35,  50)
GOLD       = (201, 169, 110)
GOLD_LIGHT = (223, 192, 144)
WHITE      = (250, 249, 247)
WHITE_DIM  = (250, 249, 247, 128)

FONTS = "C:/Windows/Fonts/"

def load(path, size):
    return ImageFont.truetype(path, size)

import random, struct
random.seed(42)

img  = Image.new("RGB", (W, H), NAVY)
draw = ImageDraw.Draw(img)

# ── Pixel-level noise so the file has real content ──
pixels = img.load()
for y in range(H):
    for x in range(W):
        n = random.randint(-6, 6)
        r = max(0, min(255, NAVY[0] + n))
        g = max(0, min(255, NAVY[1] + n))
        b = max(0, min(255, NAVY[2] + n))
        pixels[x, y] = (r, g, b)

# ── Subtle left-to-right gradient overlay ──
for x in range(W):
    t = x / W
    overlay = int(30 * (1 - t))
    for y in range(H):
        r, g, b = pixels[x, y]
        pixels[x, y] = (min(255, r + overlay), min(255, g + overlay), min(255, b + overlay))

# ── Gold vertical bar ──
BAR_X = 88
BAR_H = 190
BAR_Y = (H - BAR_H) // 2
draw.rectangle([BAR_X, BAR_Y, BAR_X + 4, BAR_Y + BAR_H], fill=GOLD)

# ── "Jacquelyn Lloyd" ──
TEXT_X = BAR_X + 48
font_name = load(FONTS + "georgia.ttf", 88)
draw.text((TEXT_X, 68), "Jacquelyn Lloyd", font=font_name, fill=WHITE)

# ── "Privately Held · PE-Backed · CPG" ──
font_tag = load(FONTS + "georgiai.ttf", 28)
draw.text((TEXT_X + 2, 174), "Privately Held  \u00B7  PE-Backed  \u00B7  CPG", font=font_tag, fill=GOLD_LIGHT)

# ── Right side ──
font_advisory = load(FONTS + "arialbd.ttf", 18)
font_url      = load(FONTS + "arial.ttf",   13)

advisory = "HR  EXECUTIVE  ADVISORY"
adv_w = draw.textlength(advisory, font=font_advisory)
RIGHT_EDGE = W - 88
adv_x = RIGHT_EDGE - int(adv_w)
adv_y = H // 2 - 28
draw.text((adv_x, adv_y), advisory, font=font_advisory, fill=WHITE)

# Gold rule
RULE_W = 240
rule_y = H // 2 + 2
draw.rectangle([RIGHT_EDGE - RULE_W, rule_y, RIGHT_EDGE, rule_y + 1], fill=GOLD)

# URL
url_text = "JACQUELYNLLOYD.COM"
url_w = draw.textlength(url_text, font=font_url)
url_x = RIGHT_EDGE - int(url_w)
url_y = H // 2 + 16
draw.text((url_x, url_y), url_text, font=font_url, fill=(200, 198, 195))

# Save as JPEG at high quality with DPI metadata
out_jpg = os.path.join(os.path.dirname(__file__), "linkedin-banner.jpg")
img.save(out_jpg, "JPEG", quality=97, dpi=(96, 96), subsampling=0)
kb_jpg = os.path.getsize(out_jpg) / 1024

# Also save as PNG (no compression)
out_png = os.path.join(os.path.dirname(__file__), "linkedin-banner.png")
img.save(out_png, "PNG", compress_level=0)
kb_png = os.path.getsize(out_png) / 1024

print(f"JPEG: {out_jpg}  ({kb_jpg:.0f} KB)")
print(f"PNG:  {out_png}  ({kb_png:.0f} KB)")
