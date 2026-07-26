#!/usr/bin/env python3
"""Genera le icone a tema eclissi totale per la PWA.

Disegna un'eclissi solare totale: disco lunare scuro con corona dorata
luminosa e raggi, coerente con la palette del sito (ink #060917,
corona #FFC24A -> #FF7A3D). Renderizza in super-sampling e riduce ai
formati richiesti dal manifest e da iPhone.
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter

# Palette dal sito
INK = (6, 9, 23)
INK_2 = (11, 17, 40)
CORONA = (255, 194, 74)
CORONA_HOT = (255, 122, 61)
VIOLET = (156, 140, 255)

SS = 4  # super-sampling


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def radial_background(size):
    """Sfondo radiale scuro con leggero bagliore verso l'alto."""
    img = Image.new("RGB", (size, size), INK)
    px = img.load()
    cx, cy = size * 0.5, size * 0.42
    maxd = size * 0.85
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - cx, y - cy) / maxd
            d = min(1.0, d)
            px[x, y] = lerp(INK_2, INK, d)
    return img


def add_glow(draw_size, center, radius, color, blur):
    """Crea un layer con un disco sfocato (bagliore)."""
    layer = Image.new("L", (draw_size, draw_size), 0)
    d = ImageDraw.Draw(layer)
    cx, cy = center
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=255)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    color_layer = Image.new("RGB", (draw_size, draw_size), color)
    return color_layer, layer


def make_eclipse(size, subject=1.0):
    S = size * SS
    base = radial_background(S).convert("RGB")

    cx, cy = S * 0.5, S * 0.5
    moon_r = S * 0.26 * subject      # raggio del disco lunare (nero)
    corona_r = moon_r * 1.28         # raggio interno della corona

    # Stelle di sfondo
    star_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(star_layer)
    rnd = random.Random(2026)
    for _ in range(90):
        x = rnd.uniform(0, S)
        y = rnd.uniform(0, S)
        if math.hypot(x - cx, y - cy) < corona_r * 1.9:
            continue
        r = rnd.uniform(S * 0.002, S * 0.006)
        a = rnd.randint(40, 150)
        sd.ellipse([x - r, y - r, x + r, y + r], fill=(233, 233, 245, a))
    base = Image.alpha_composite(base.convert("RGBA"), star_layer).convert("RGB")

    # Bagliore esterno della corona (contenuto, per non annegare il cielo scuro)
    glow_c, glow_a = add_glow(S, (cx, cy), corona_r * 1.55, CORONA_HOT, S * 0.05)
    base = Image.composite(glow_c, base, glow_a.point(lambda p: int(p * 0.40)))
    glow_c, glow_a = add_glow(S, (cx, cy), corona_r * 1.28, CORONA, S * 0.035)
    base = Image.composite(glow_c, base, glow_a.point(lambda p: int(p * 0.60)))

    # Raggi della corona
    ray_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ray_layer)
    rnd2 = random.Random(7)
    n_rays = 48
    for i in range(n_rays):
        ang = (i / n_rays) * 2 * math.pi + rnd2.uniform(-0.03, 0.03)
        length = corona_r * rnd2.uniform(1.28, 1.62)
        w = max(1, int(S * rnd2.uniform(0.0035, 0.009)))
        x0 = cx + math.cos(ang) * corona_r * 1.02
        y0 = cy + math.sin(ang) * corona_r * 1.02
        x1 = cx + math.cos(ang) * length
        y1 = cy + math.sin(ang) * length
        col = lerp(CORONA, CORONA_HOT, rnd2.random())
        rd.line([x0, y0, x1, y1], fill=col + (170,), width=w)
    ray_layer = ray_layer.filter(ImageFilter.GaussianBlur(S * 0.006))
    base = Image.alpha_composite(base.convert("RGBA"), ray_layer).convert("RGB")

    # Anello di corona luminoso attorno al disco lunare
    ring = Image.new("L", (S, S), 0)
    rdd = ImageDraw.Draw(ring)
    rdd.ellipse([cx - corona_r, cy - corona_r, cx + corona_r, cy + corona_r], fill=255)
    rdd.ellipse([cx - moon_r, cy - moon_r, cx + moon_r, cy + moon_r], fill=0)
    ring = ring.filter(ImageFilter.GaussianBlur(S * 0.02))
    ring_col = Image.new("RGB", (S, S), CORONA)
    base = Image.composite(ring_col, base, ring)

    # Disco lunare nero con bordo netto
    fg = ImageDraw.Draw(base)
    fg.ellipse([cx - moon_r, cy - moon_r, cx + moon_r, cy + moon_r], fill=(4, 6, 16))

    # "Diamond ring": punto luminoso sul bordo
    dr_ang = math.radians(-42)
    dx = cx + math.cos(dr_ang) * moon_r
    dy = cy + math.sin(dr_ang) * moon_r
    glow_c, glow_a = add_glow(S, (dx, dy), S * 0.045 * subject, (255, 255, 240), S * 0.02 * subject)
    base = Image.composite(glow_c, base, glow_a)
    fg = ImageDraw.Draw(base)
    core_r = S * 0.012 * subject
    fg.ellipse([dx - core_r, dy - core_r, dx + core_r, dy + core_r], fill=(255, 255, 250))

    return base.resize((size, size), Image.LANCZOS)


def make_maskable(size):
    """Versione maskable: soggetto rimpicciolito entro la safe area (~72%)."""
    return make_eclipse(size, subject=0.72)


def main():
    out = "."
    icon = make_eclipse(1024)

    sizes = {
        "icon-192.png": 192,
        "icon-512.png": 512,
        "apple-touch-icon.png": 180,
        "favicon-32.png": 32,
    }
    for name, sz in sizes.items():
        icon.resize((sz, sz), Image.LANCZOS).save(f"{out}/{name}")
        print("scritto", name, sz)

    # maskable 512 dedicata con safe area
    make_maskable(512).save(f"{out}/icon-maskable-512.png")
    print("scritto icon-maskable-512.png 512")

    # favicon.ico multi-size
    ico = make_eclipse(256)
    ico.save(f"{out}/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("scritto favicon.ico")


if __name__ == "__main__":
    main()
