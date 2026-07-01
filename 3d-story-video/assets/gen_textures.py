"""Generate procedural planet textures (Earth, Moon) as equirectangular PNGs
for textured_sphere(). Run once with the env python; outputs into ./assets/.

To make other planets, copy a function and change the base color + features.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

os.makedirs("assets", exist_ok=True)
W, H = 1024, 512


def _blob(d, cx, cy, scale, color):
    n = random.randint(8, 13)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = scale * (0.55 + random.random() * 0.7)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.8))
    d.polygon(pts, fill=color)


def earth():
    random.seed(3)
    img = Image.new("RGB", (W, H), (28, 92, 158))      # ocean
    d = ImageDraw.Draw(img)
    for _ in range(40):                                # ocean depth variation
        cx, cy, r = random.randint(0, W), random.randint(0, H), random.randint(40, 140)
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=random.choice([(24, 80, 140), (36, 104, 172)]))
    greens = [(58, 140, 74), (70, 156, 86), (96, 150, 70)]
    for _ in range(16):                                # continents
        _blob(d, random.randint(0, W), random.randint(int(H * 0.22), int(H * 0.78)),
              random.randint(45, 120), random.choice(greens))
    for _ in range(5):                                 # deserts
        _blob(d, random.randint(0, W), random.randint(int(H * 0.3), int(H * 0.7)),
              random.randint(25, 55), (193, 168, 110))
    img = img.filter(ImageFilter.GaussianBlur(3))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 46], fill=(232, 238, 244))   # ice caps
    d.rectangle([0, H - 46, W, H], fill=(232, 238, 244))
    img.filter(ImageFilter.GaussianBlur(2)).save("assets/earth_texture.png")


def moon():
    random.seed(11)
    img = Image.new("RGB", (W, H), (158, 155, 146))
    d = ImageDraw.Draw(img)
    for _ in range(8):                                 # maria
        cx, cy, r = random.randint(0, W), random.randint(0, H), random.randint(70, 150)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(128, 125, 117))
    for _ in range(60):                                # craters
        cx, cy, r = random.randint(0, W), random.randint(0, H), random.randint(6, 38)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(112, 109, 101),
                  outline=(184, 181, 171), width=2)
    img.filter(ImageFilter.GaussianBlur(2)).save("assets/moon_texture.png")


if __name__ == "__main__":
    earth()
    moon()
    print("wrote assets/earth_texture.png and assets/moon_texture.png")
