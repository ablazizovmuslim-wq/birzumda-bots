"""Botlar uchun avatarkalar (assets/*.jpg) — Birzumda uslubida. Ishga tushirish: python make_avatars.py"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 640
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = Path(__file__).parent / "assets"

BOTS = {  # rang1, rang2, belgi
    "lotin": ("#7c3aed", "#ec4899", "A↔Я"),
    "hisob": ("#059669", "#06b6d4", "$%"),
    "stiker": ("#f97316", "#ec4899", "sticker"),
    "musiqa": ("#2563eb", "#9333ea", "♫"),
    "eslatma": ("#f59e0b", "#ef4444", "clock"),
}


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def gradient(c1, c2):
    a, b = hex2rgb(c1), hex2rgb(c2)
    img = Image.new("RGB", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * S)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return img


def bolt(draw, cx, cy, k, fill):
    pts = [(36, 4), (14, 36), (30, 36), (24, 60), (50, 26), (34, 26), (40, 4)]
    draw.polygon([(cx + (x - 32) * k, cy + (y - 32) * k) for x, y in pts], fill=fill)


def make(key, c1, c2, sym):
    img = gradient(c1, c2)
    glow = Image.new("L", (S, S), 0)
    ImageDraw.Draw(glow).ellipse((90, 60, 550, 520), fill=110)
    img = Image.composite(Image.new("RGB", (S, S), "white"), img, glow.filter(ImageFilter.GaussianBlur(90)).point(lambda v: v // 3))
    d = ImageDraw.Draw(img)
    white = (255, 255, 255)
    if sym == "clock":
        cx, cy, r = 320, 300, 150
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=white, width=26)
        for i in range(12):
            a = math.radians(i * 30)
            d.line((cx + (r - 34) * math.sin(a), cy - (r - 34) * math.cos(a), cx + (r - 20) * math.sin(a), cy - (r - 20) * math.cos(a)), fill=white, width=8)
        d.line((cx, cy, cx, cy - 95), fill=white, width=20)
        d.line((cx, cy, cx + 70, cy + 30), fill=white, width=20)
        d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=white)
        d.ellipse((cx - r - 40, cy - r - 30, cx - r + 40, cy - r + 40), fill=white)   # qo'ng'iroq quloqlari
        d.ellipse((cx + r - 40, cy - r - 30, cx + r + 40, cy - r + 40), fill=white)
    elif sym == "sticker":
        x0, y0, x1, y1, fold = 170, 140, 470, 440, 90
        d.polygon([(x0 + 40, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1 - 40), (x1 - 40, y1), (x0 + 40, y1), (x0, y1 - 40), (x0, y0 + 40)], fill=white)
        d.polygon([(x1 - fold, y0), (x1 - fold, y0 + fold), (x1, y0 + fold)], fill=hex2rgb(c2))
        f = ImageFont.truetype(FONT, 170)
        d.text((x0 + 130, y0 + 175), "☺", font=f, fill=hex2rgb(c1), anchor="mm")
    else:
        size = {"A↔Я": 150, "$%": 210, "♫": 280}[sym]
        f = ImageFont.truetype(FONT, size)
        sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((328, 298), sym, font=f, fill=(0, 0, 0, 90), anchor="mm")
        img.paste(sh.filter(ImageFilter.GaussianBlur(8)), (0, 0), sh.filter(ImageFilter.GaussianBlur(8)))
        d = ImageDraw.Draw(img)
        d.text((320, 290), sym, font=f, fill=white, anchor="mm")
    # Birzumda belgisi — pastda chaqmoqli doira
    d.ellipse((270, 470, 370, 570), fill=white)
    bolt(d, 320, 520, 1.25, hex2rgb(c1))
    OUT.mkdir(exist_ok=True)
    img.save(OUT / f"{key}.jpg", quality=92)


if __name__ == "__main__":
    for k, (a, b, s) in BOTS.items():
        make(k, a, b, s)
    print("tayyor:", ", ".join(BOTS))
