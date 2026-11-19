"""Neon logolar — Birzumda Yukla uslubida (porlovchi halqa, yaltiroq ikonka, 3D yozuv).
Ishga tushirish: python make_logos.py  →  assets/<bot>.jpg
"""
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

S = 640
OUT = Path(__file__).parent / "assets"
FONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"
SYM_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BOTS = {  # neon rang, och rang, to'q rang, nom
    "lotin": ((168, 85, 247), (233, 213, 255), (59, 7, 100), "LOTIN"),
    "hisob": ((16, 185, 129), (209, 250, 229), (2, 44, 34), "HISOB"),
    "stiker": ((249, 115, 22), (255, 237, 213), (67, 20, 7), "STIKER"),
    "musiqa": ((236, 72, 153), (252, 231, 243), (80, 7, 36), "MUSIQA"),
    "eslatma": ((234, 179, 8), (254, 249, 195), (66, 32, 6), "ESLATMA"),
}


def font(size, weight=900):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def vgrad(w, h, top, bottom):
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return g.resize((w, h))


def glow(layer: Image.Image, radius, strength=1.0):
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1:
        g = Image.eval(g, lambda v: min(255, int(v * strength)))
    return g


def screen(base, add):
    return ImageChops.screen(base, add)


def shape_fill(mask: Image.Image, top, bottom, outline=(255, 255, 255), ow=6):
    """Maskani yaltiroq gradient bilan to'ldiradi + oq chegara + yuqori yaltirash."""
    w, h = mask.size
    fill = vgrad(w, h, top, bottom).convert("RGBA")
    fill.putalpha(mask)
    # yuqori yarmida yaltirash
    hl = Image.new("L", (w, h), 0)
    bbox = mask.getbbox() or (0, 0, w, h)
    hd = ImageDraw.Draw(hl)
    hd.ellipse((bbox[0] - 40, bbox[1] - (bbox[3] - bbox[1]) * 0.9, bbox[2] + 40, bbox[1] + (bbox[3] - bbox[1]) * 0.45), fill=90)
    hl = ImageChops.multiply(hl, mask).filter(ImageFilter.GaussianBlur(6))
    white = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    white.putalpha(hl)
    fill = Image.alpha_composite(fill, white)
    edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(ow * 2 + 1)), mask)
    ol = Image.new("RGBA", (w, h), outline + (0,))
    ol.putalpha(edge)
    return Image.alpha_composite(ol, fill)


def icon_mask(key, neon):
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    cx, cy = 320, 225
    inner = None  # (mask, colour) — ikonka ichidagi qism
    if key == "lotin":
        d.rounded_rectangle((cx - 120, cy - 85, cx + 120, cy + 70), 40, fill=255)
        d.polygon([(cx - 60, cy + 60), (cx - 95, cy + 115), (cx - 10, cy + 65)], fill=255)  # nutq pufakchasi dumi
        inner = Image.new("L", (S, S), 0)
        ImageDraw.Draw(inner).text((cx, cy - 8), "A⇄Я", font=ImageFont.truetype(SYM_FONT, 92), fill=255, anchor="mm")
    elif key == "hisob":
        d.rounded_rectangle((cx - 85, cy - 105, cx + 85, cy + 105), 30, fill=255)
        inner = Image.new("L", (S, S), 0)
        di = ImageDraw.Draw(inner)
        di.rounded_rectangle((cx - 60, cy - 80, cx + 60, cy - 35), 10, fill=255)
        for r in range(3):
            for c in range(3):
                x, y = cx - 45 + c * 45, cy + 5 + r * 40
                di.rounded_rectangle((x - 16, y - 13, x + 16, y + 13), 7, fill=255)
    elif key == "stiker":
        x0, y0, x1, y1, f = cx - 105, cy - 105, cx + 105, cy + 105, 70
        d.polygon([(x0 + 30, y0), (x1 - f, y0), (x1, y0 + f), (x1, y1 - 30), (x1 - 30, y1), (x0 + 30, y1), (x0, y1 - 30), (x0, y0 + 30)], fill=255)
        inner = Image.new("L", (S, S), 0)
        di = ImageDraw.Draw(inner)
        di.polygon([(x1 - f, y0), (x1 - f, y0 + f), (x1, y0 + f)], fill=255)
        di.ellipse((cx - 45, cy - 30, cx - 15, cy), fill=255)
        di.ellipse((cx + 15, cy - 30, cx + 45, cy), fill=255)
        di.arc((cx - 60, cy - 30, cx + 60, cy + 60), 20, 160, fill=255, width=16)
    elif key == "musiqa":
        d.text((cx, cy + 10), "♫", font=ImageFont.truetype(SYM_FONT, 270), fill=255, anchor="mm")
    elif key == "eslatma":
        r = 100
        d.ellipse((cx - r, cy - r + 10, cx + r, cy + r + 10), fill=255)
        d.ellipse((cx - r - 25, cy - r - 25, cx - r + 45, cy - r + 45), fill=255)
        d.ellipse((cx + r - 45, cy - r - 25, cx + r + 25, cy - r + 45), fill=255)
        inner = Image.new("L", (S, S), 0)
        di = ImageDraw.Draw(inner)
        di.line((cx, cy + 10, cx, cy - 55), fill=255, width=16)
        di.line((cx, cy + 10, cx + 50, cy + 35), fill=255, width=16)
        for i in range(12):
            a = math.radians(i * 30)
            di.ellipse((cx + 78 * math.sin(a) - 5, cy + 10 - 78 * math.cos(a) - 5, cx + 78 * math.sin(a) + 5, cy + 10 - 78 * math.cos(a) + 5), fill=255)
    return m, inner


def text_layer(text, size, top, bottom, stroke, sw, y, extrude=None):
    f = font(size)
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # 3D chiqish (pastga soyalar)
    if extrude:
        for k in range(8, 0, -1):
            m = Image.new("L", (S, S), 0)
            ImageDraw.Draw(m).text((320, y + k), text, font=f, fill=255, anchor="mm", stroke_width=sw)
            ex = Image.new("RGBA", (S, S), extrude + (255,))
            ex.putalpha(m)
            layer = Image.alpha_composite(layer, ex)
    m_st = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m_st).text((320, y), text, font=f, fill=255, anchor="mm", stroke_width=sw)
    st = Image.new("RGBA", (S, S), stroke + (255,))
    st.putalpha(m_st)
    layer = Image.alpha_composite(layer, st)
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).text((320, y), text, font=f, fill=255, anchor="mm")
    box = m.getbbox()
    g = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    if box:
        g.paste(vgrad(box[2] - box[0], box[3] - box[1], top, bottom).convert("RGBA"), box[:2])
    g.putalpha(m)
    return Image.alpha_composite(layer, g), m_st


def make(key, neon, light, dark, name):
    # 1) fon: to'q, markazda rangli nur
    bg = Image.new("RGB", (S, S), (3, 4, 12))
    tint = Image.new("L", (S, S), 0)
    ImageDraw.Draw(tint).ellipse((60, 40, 580, 560), fill=255)
    tint = tint.filter(ImageFilter.GaussianBlur(120))
    bg = Image.composite(Image.new("RGB", (S, S), tuple(int(c * .35) for c in neon)), bg, tint)
    # pastki «pol» aksi
    floor = Image.new("L", (S, S), 0)
    ImageDraw.Draw(floor).ellipse((40, 560, 600, 700), fill=200)
    bg = screen(bg, Image.composite(Image.new("RGB", (S, S), neon), Image.new("RGB", (S, S)), floor.filter(ImageFilter.GaussianBlur(40))))

    # 2) ichki disk
    disk = Image.new("L", (S, S), 0)
    ImageDraw.Draw(disk).ellipse((70, 70, 570, 570), fill=255)
    bg = Image.composite(Image.new("RGB", (S, S), tuple(int(c * .18) for c in neon)), bg, disk.point(lambda v: v * 0.85))

    # 3) neon halqalar + porlash
    ring = Image.new("L", (S, S), 0)
    rd = ImageDraw.Draw(ring)
    rd.ellipse((48, 48, 592, 592), outline=255, width=14)
    rd.ellipse((78, 78, 562, 562), outline=200, width=4)
    ring_rgb = Image.composite(Image.new("RGB", (S, S), neon), Image.new("RGB", (S, S)), ring)
    bg = screen(bg, glow(ring_rgb, 22, 1.6))
    bg = screen(bg, glow(ring_rgb, 6, 1.2))
    core = Image.new("L", (S, S), 0)
    ImageDraw.Draw(core).ellipse((52, 52, 588, 588), outline=255, width=4)
    bg = screen(bg, Image.composite(Image.new("RGB", (S, S), light), Image.new("RGB", (S, S)), core))

    # yon tomonlarda ekvalayzer chiziqlari
    eq = Image.new("L", (S, S), 0)
    ed = ImageDraw.Draw(eq)
    for side in (-1, 1):
        for i, hgt in enumerate([40, 90, 130, 80, 50]):
            x = 320 + side * (175 + i * 18)
            ed.rounded_rectangle((x - 4, 225 - hgt / 2, x + 4, 225 + hgt / 2), 4, fill=255)
    bg = screen(bg, glow(Image.composite(Image.new("RGB", (S, S), neon), Image.new("RGB", (S, S)), eq), 8, 1.4))
    bg = screen(bg, Image.composite(Image.new("RGB", (S, S), light), Image.new("RGB", (S, S)), eq))

    img = bg.convert("RGBA")
    # 4) ikonka
    m, inner = icon_mask(key, neon)
    halo = Image.composite(Image.new("RGB", (S, S), neon), Image.new("RGB", (S, S)), m.filter(ImageFilter.MaxFilter(21)))
    img = Image.alpha_composite(img, Image.merge("RGBA", (*glow(halo, 25, 1.3).split(), glow(m, 25).point(lambda v: min(255, v * 2)))))
    img = Image.alpha_composite(img, shape_fill(m, light, neon))
    if inner:
        inn = Image.new("RGBA", (S, S), dark + (255,))
        inn.putalpha(ImageChops.multiply(inner, m.filter(ImageFilter.MinFilter(5))) if key != "stiker" else inner)
        img = Image.alpha_composite(img, inn)

    # 5) yozuvlar: BIRZUMDA (oq-xrom) va bot nomi (neon)
    t1, m1 = text_layer("BIRZUMDA", 84, (255, 255, 255), light, neon, 7, 405, extrude=dark)
    g1 = Image.composite(Image.new("RGB", (S, S), neon), Image.new("RGB", (S, S)), m1)
    img = Image.alpha_composite(img, Image.merge("RGBA", (*glow(g1, 14, 1.5).split(), glow(m1, 14).point(lambda v: min(255, v * 2)))))
    img = Image.alpha_composite(img, t1)
    size2 = 92 if len(name) <= 6 else 80
    t2, m2 = text_layer(name, size2, light, neon, (255, 255, 255), 4, 492, extrude=dark)
    img = Image.alpha_composite(img, t2)

    # 6) halqadagi yaltiroq nuqtalar
    sp = Image.new("L", (S, S), 0)
    sd = ImageDraw.Draw(sp)
    for ang in (-60, -125, 200, -15):
        a = math.radians(ang)
        x, y = 320 + 272 * math.cos(a), 320 + 272 * math.sin(a)
        sd.ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
        sd.line((x - 26, y, x + 26, y), fill=180, width=2)
        sd.line((x, y - 26, x, y + 26), fill=180, width=2)
    spk = Image.composite(Image.new("RGB", (S, S), (255, 255, 255)), Image.new("RGB", (S, S)), sp)
    img = Image.fromarray if False else img
    out = screen(img.convert("RGB"), glow(spk, 3, 1.5))
    out = screen(out, spk)
    OUT.mkdir(exist_ok=True)
    out.save(OUT / f"{key}.jpg", quality=93)
    return out


if __name__ == "__main__":
    for k, v in BOTS.items():
        make(k, *v)
    print("tayyor:", ", ".join(BOTS))
