"""
gen_misc.py - faction flag/crest, UI icons, campaign station sprites and portraits for The Last Census.
Run from the mod root:  python tools/gen_misc.py
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import Canvas  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IVORY = (226, 216, 190)
JADE = (96, 156, 124)
JADE_D = (38, 74, 62)
BRASS = (190, 152, 86)
INK = (24, 30, 32)
S = 4


def path(*p):
    full = os.path.join(ROOT, *p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


def down(im, size):
    return im.resize(size, Image.LANCZOS)


def seal(d, cx, cy, r, ring=BRASS, field=JADE, glyph=IVORY, ticks=24, eye=True, lw=None):
    """The Bureau seal: toothed outer ring, ruled field, central eye between two ledger lines."""
    lw = lw or max(2, int(r * 0.06))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ring)
    for k in range(ticks):
        a = 2 * math.pi * k / ticks
        x0, y0 = cx + math.cos(a) * r * 0.80, cy + math.sin(a) * r * 0.80
        x1, y1 = cx + math.cos(a) * r * 0.96, cy + math.sin(a) * r * 0.96
        d.line([(x0, y0), (x1, y1)], fill=INK, width=max(1, lw // 2))
    d.ellipse([cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78], fill=INK)
    d.ellipse([cx - r * 0.72, cy - r * 0.72, cx + r * 0.72, cy + r * 0.72], fill=field)
    if eye:
        # ledger lines
        for dy in (-0.42, 0.42):
            d.line([(cx - r * 0.62, cy + r * dy), (cx + r * 0.62, cy + r * dy)], fill=glyph, width=lw)
        # almond eye
        pts = []
        for i in range(41):
            t = -1 + 2 * i / 40
            pts.append((cx + t * r * 0.58, cy - (1 - t * t) * r * 0.26))
        for i in range(41):
            t = 1 - 2 * i / 40
            pts.append((cx + t * r * 0.58, cy + (1 - t * t) * r * 0.26))
        d.polygon(pts, fill=glyph)
        d.ellipse([cx - r * 0.19, cy - r * 0.19, cx + r * 0.19, cy + r * 0.19], fill=field)
        d.ellipse([cx - r * 0.09, cy - r * 0.09, cx + r * 0.09, cy + r * 0.09], fill=INK)


def flag():
    W, H = 410 * S, 256 * S
    im = Image.new("RGBA", (W, H), JADE_D + (255,))
    d = ImageDraw.Draw(im)
    # ruled ledger field
    for y in range(0, H, 22 * S):
        d.line([(0, y), (W, y)], fill=(48, 88, 74, 255), width=S)
    d.line([(64 * S, 0), (64 * S, H)], fill=(120, 60, 50, 255), width=2 * S)   # the margin line
    d.rectangle([0, H * 0.40, W, H * 0.60], fill=IVORY + (255,))
    d.rectangle([0, H * 0.40, W, H * 0.415], fill=BRASS + (255,))
    d.rectangle([0, H * 0.585, W, H * 0.60], fill=BRASS + (255,))
    seal(d, W * 0.5, H * 0.5, H * 0.36, lw=6 * S)
    down(im, (410, 256)).save(path("graphics", "factions", "tlc_bureau_flag.png"))


def crest():
    W = H = 256 * S
    im = Image.new("RGBA", (W, H), (30, 52, 48, 255))
    d = ImageDraw.Draw(im)
    rng = random.Random(4)
    for y in range(0, H, 18 * S):
        d.line([(0, y), (W, y)], fill=(40, 68, 62, 255), width=S)
    for _ in range(60):
        x = rng.randint(0, W)
        y = rng.randint(0, H)
        d.rectangle([x, y, x + rng.randint(8, 40) * S, y + 3 * S], fill=(36, 62, 57, 255))
    im = im.filter(ImageFilter.GaussianBlur(2 * S))
    d = ImageDraw.Draw(im)
    seal(d, W / 2, H / 2, W * 0.36, ring=(232, 226, 210), field=(30, 52, 48), glyph=(232, 226, 210), lw=7 * S)
    down(im, (256, 256)).save(path("graphics", "factions", "tlc_bureau_crest.png"))


def glyph_icon(name, size, draw_fn, rel):
    W = H = size * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    draw_fn(d, W, H)
    down(im, (size, size)).save(path(*rel.split("/")))


def framed_icon(name, size, draw_fn, rel, bg=(22, 36, 34), border=JADE):
    W = H = size * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([S, S, W - S, H - S], radius=5 * S, fill=bg + (255,), outline=border + (255,), width=2 * S)
    draw_fn(d, W, H)
    down(im, (size, size)).save(path(*rel.split("/")))


def icons():
    white = (235, 235, 235, 255)

    def surcharge(d, W, H):
        cx, cy, r = W / 2, H / 2, W * 0.40
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=white, width=int(W * 0.07))
        for k in range(12):
            a = 2 * math.pi * k / 12
            d.line([(cx + math.cos(a) * r * 1.02, cy + math.sin(a) * r * 1.02),
                    (cx + math.cos(a) * r * 1.20, cy + math.sin(a) * r * 1.20)], fill=white, width=int(W * 0.04))
        # percent sign
        d.ellipse([cx - r * 0.55, cy - r * 0.55, cx - r * 0.15, cy - r * 0.15], outline=white, width=int(W * 0.05))
        d.ellipse([cx + r * 0.15, cy + r * 0.15, cx + r * 0.55, cy + r * 0.55], outline=white, width=int(W * 0.05))
        d.line([(cx + r * 0.5, cy - r * 0.55), (cx - r * 0.5, cy + r * 0.55)], fill=white, width=int(W * 0.06))
    glyph_icon("surcharge", 64, surcharge, "graphics/icons/hullsys/tlc_surcharge.png")

    def gavel(d, W, H):
        def rot_rect(cx, cy, length, thick, ang):
            ca, sa = math.cos(ang), math.sin(ang)
            pts = []
            for (u, v) in ((-length / 2, -thick / 2), (length / 2, -thick / 2), (length / 2, thick / 2),
                           (-length / 2, thick / 2)):
                pts.append((cx + u * ca - v * sa, cy + u * sa + v * ca))
            return pts
        # handle runs from the head (upper left) down to the lower right, 45 degrees
        hx, hy = W * 0.40, H * 0.36
        d.polygon(rot_rect(W * 0.60, H * 0.56, W * 0.56, W * 0.085, math.pi / 4), fill=white)
        # head: a thick block perpendicular to the handle, with two collar bands
        d.polygon(rot_rect(hx, hy, W * 0.46, W * 0.24, -math.pi / 4), fill=white)
        for off in (-0.13, 0.13):
            bx = hx + off * W * math.cos(-math.pi / 4)
            by = hy + off * W * math.sin(-math.pi / 4)
            d.polygon(rot_rect(bx, by, W * 0.035, W * 0.30, -math.pi / 4), fill=white)
        # sound block
        d.rounded_rectangle([W * 0.10, H * 0.80, W * 0.46, H * 0.90], radius=W * 0.02, fill=white)
    glyph_icon("judgment", 64, gavel, "graphics/icons/hullsys/tlc_summary_judgment.png")

    def protocols(d, W, H):
        d.rounded_rectangle([W * 0.08, H * 0.08, W * 0.92, H * 0.92], radius=W * 0.12, fill=(40, 62, 58, 255),
                            outline=(200, 200, 190, 255), width=int(W * 0.05))
        for y in (0.32, 0.5, 0.68):
            d.line([(W * 0.2, H * y), (W * 0.8, H * y)], fill=(150, 200, 170, 255), width=int(W * 0.05))
        d.ellipse([W * 0.56, H * 0.56, W * 0.86, H * 0.86], fill=BRASS + (255,), outline=INK + (255,),
                  width=int(W * 0.03))
    glyph_icon("protocols", 32, protocols, "graphics/hullmods/tlc_protocols.png")

    def admin(d, W, H):
        seal(d, W / 2, H / 2, W * 0.36, lw=3 * S)
    framed_icon("admin", 40, admin, "graphics/icons/markets/tlc_automated_admin.png")

    def census(d, W, H):
        d.rectangle([W * 0.22, H * 0.18, W * 0.78, H * 0.84], fill=IVORY + (255,))
        for y in (0.32, 0.44, 0.56, 0.68):
            d.line([(W * 0.28, H * y), (W * 0.72, H * y)], fill=JADE + (255,), width=2 * S)
        d.line([(W * 0.34, H * 0.20), (W * 0.34, H * 0.82)], fill=(150, 70, 60, 255), width=S)
        d.ellipse([W * 0.52, H * 0.58, W * 0.80, H * 0.86], fill=BRASS + (255,))
    framed_icon("census", 40, census, "graphics/icons/intel/tlc_census.png")

    def inspector(d, W, H):
        gavel(d, W, H)
    framed_icon("inspector", 40, inspector, "graphics/icons/intel/tlc_inspector.png", bg=(30, 26, 22), border=BRASS)

    def station_glyph(d, W, H):
        cx, cy = W / 2, H / 2
        d.rectangle([cx - W * 0.30, cy - H * 0.30, cx + W * 0.30, cy + H * 0.30], outline=white, width=int(W * 0.08))
        d.ellipse([cx - W * 0.12, cy - H * 0.12, cx + W * 0.12, cy + H * 0.12], fill=white)
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d.line([(cx + dx * W * 0.30, cy + dy * H * 0.30), (cx + dx * W * 0.46, cy + dy * H * 0.46)], fill=white,
                   width=int(W * 0.07))
    glyph_icon("station", 64, station_glyph, "graphics/icons/tlc_tallyhouse_icon.png")

    def relay_glyph(d, W, H):
        cx, cy = W / 2, H / 2
        d.line([(cx, cy - H * 0.40), (cx, cy + H * 0.40)], fill=white, width=int(W * 0.08))
        for y in (-0.25, 0.0, 0.25):
            d.line([(cx - W * 0.30, cy + y * H), (cx + W * 0.30, cy + y * H)], fill=white, width=int(W * 0.06))
        d.ellipse([cx - W * 0.10, cy - H * 0.48, cx + W * 0.10, cy - H * 0.30], fill=white)
    glyph_icon("relay", 64, relay_glyph, "graphics/icons/tlc_relay_icon.png")


# ------------------------------------------------------------------ campaign sprites

def tallyhouse():
    c = Canvas(160, 160, seed=201)
    for k in range(4):
        a = k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)

        def rot(x, y):
            return (x * ca - (y - 80) * sa, 80 + x * sa + (y - 80) * ca)
        arm = [rot(-9, 8), rot(9, 8), rot(9, 60), rot(-9, 60)]
        c.part(("poly", arm), z=0.22, bevel=1.4, mat="slate2")
        pod = [rot(-20, 6), rot(20, 6), rot(20, 30), rot(-20, 30)]
        c.part(("poly", pod), z=0.34, bevel=2.0, mat="ivory", panels={"dx": 5, "dy": 5})
        stripe = [rot(-20, 24), rot(20, 24), rot(20, 27), rot(-20, 27)]
        c.stripe(("poly", stripe), mat="jade")
        drawer = [rot(-14, 34), rot(14, 34), rot(14, 44), rot(-14, 44)]
        c.part(("poly", drawer), z=0.30, bevel=1.2, mat="ivory2")
        hx, hy = rot(0, 39)
        c.part(("rect", hx - 3, hy - 1, hx + 3, hy + 1), z=0.33, bevel=0.4, mat="brass")
        lx, ly = rot(17, 9)
        c.light(lx, ly)
    c.part(("ellipse", 0, 80, 40, 40), z=0.26, bevel=2.0, mat="slate")
    c.part(("ellipse", 0, 80, 36, 36), z=0.30, bevel=2.0, mat="ivory", panels={"dx": 6, "dy": 6})
    c.part(("ellipse", 0, 80, 24, 24), z=0.38, bevel=1.5, mat="brass")
    c.part(("ellipse", 0, 80, 20, 20), z=0.40, bevel=1.5, mat="jade2")
    c.part(("ellipse", 0, 80, 11, 11), z=0.46, bevel=2.5, mat="lens", dome=True, gloss=0.9)
    for k in range(12):
        a = 2 * math.pi * k / 12
        c.groove([(math.cos(a) * 26, 80 + math.sin(a) * 26), (math.cos(a) * 34, 80 + math.sin(a) * 34)], width=0.6)
    c.greebles(-30, 50, 30, 110, n=16, seed=9)
    img = c.render(grime=0.25)
    img.save(path("graphics", "stations", "tlc_tallyhouse.png"))


def courier_relay():
    c = Canvas(96, 96, seed=211)
    c.part(("rect", -3.5, 6, 3.5, 90), z=0.25, bevel=1.0, mat="slate")
    for y, w in ((18, 30), (34, 38), (50, 42), (66, 34)):
        c.part(("rrect", -w, y - 4, -6, y + 4, 1.5), z=0.32, bevel=1.0, mat="ivory2", panels={"dx": 4, "dy": 4})
        c.part(("rrect", 6, y - 4, w, y + 4, 1.5), z=0.32, bevel=1.0, mat="ivory2", panels={"dx": 4, "dy": 4})
        c.stripe(("rect", -w, y + 2, w, y + 3), mat="jade")
    # broken panel (scavenged): carve a missing chunk by painting dark low plate
    c.part(("rect", 18, 46, 42, 54), z=0.05, bevel=0.5, mat="dark", override=True)
    c.part(("ellipse", 0, 82, 11, 11), z=0.36, bevel=1.2, mat="brass")
    c.part(("ellipse", 0, 82, 8, 8), z=0.40, bevel=2.0, mat="lens", dome=True, gloss=0.8)
    c.part(("ellipse", 0, 8, 6, 6), z=0.34, bevel=1.0, mat="slate2")
    c.greebles(-5, 10, 5, 76, n=8, seed=3, smin=1.0, smax=2.5)
    img = c.render(grime=0.35)
    img.save(path("graphics", "stations", "tlc_courier_relay.png"))


def dead_letter_office():
    c = Canvas(84, 84, seed=221)
    c.part(("rrect", -30, 20, 30, 64, 4), z=0.30, bevel=1.6, mat="ivory2", panels={"dx": 4, "dy": 5})
    c.part(("rect", -6, 6, 6, 78), z=0.22, bevel=1.0, mat="slate2")
    for (y0, y1) in ((24, 34), (36, 46), (48, 58)):
        c.part(("rrect", -36, y0, -30, y1, 1.0), z=0.26, bevel=0.8, mat="ivory", sym=True)
    c.part(("rect", 10, 22, 28, 40), z=0.04, bevel=0.5, mat="dark", override=True)   # hull breach
    c.part(("rect", -26, 50, -12, 62), z=0.04, bevel=0.5, mat="dark", override=True)
    c.stripe(("rect", -30, 42, 30, 44), mat="jade")
    c.part(("ellipse", 0, 70, 6, 6), z=0.34, bevel=1.0, mat="brass")
    c.greebles(-28, 22, 28, 62, n=12, seed=5)
    img = c.render(grime=0.45)
    img.save(path("graphics", "stations", "tlc_dead_letter_office.png"))


# ------------------------------------------------------------------ portraits

def portrait(name, bezel, lens_col, accent, bg_col, seed, severe=False):
    W = H = 128 * S
    rng = random.Random(seed)
    im = Image.new("RGBA", (W, H), bg_col + (255,))
    d = ImageDraw.Draw(im)
    # background: racks of filing drawers fading into darkness
    for row in range(8):
        for col in range(6):
            x0 = col * 22 * S - 4 * S
            y0 = row * 17 * S - 6 * S
            shade = 18 + rng.randint(0, 10)
            d.rectangle([x0, y0, x0 + 20 * S, y0 + 15 * S],
                        fill=(bg_col[0] + shade, bg_col[1] + shade, bg_col[2] + shade, 255))
            d.rectangle([x0 + 7 * S, y0 + 6 * S, x0 + 13 * S, y0 + 8 * S], fill=(110, 92, 60, 255))
    im = im.filter(ImageFilter.GaussianBlur(3 * S))
    d = ImageDraw.Draw(im)
    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    v = np.clip(1.15 - np.hypot(xx - W / 2, yy - H * 0.55) / (W * 0.62), 0.25, 1.0)
    arr = np.asarray(im).astype(np.float32)
    arr[..., :3] *= v[..., None]
    im = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im)
    cx, cy = W / 2, H * 0.52
    # terminal housing
    d.rounded_rectangle([cx - 44 * S, cy - 50 * S, cx + 44 * S, cy + 58 * S], radius=10 * S, fill=bezel + (255,))
    d.rounded_rectangle([cx - 40 * S, cy - 46 * S, cx + 40 * S, cy + 54 * S], radius=8 * S,
                        fill=tuple(max(0, c - 34) for c in bezel) + (255,))
    # ledger scanlines in the screen
    d.rounded_rectangle([cx - 34 * S, cy - 40 * S, cx + 34 * S, cy + 34 * S], radius=6 * S, fill=(14, 22, 22, 255))
    for y in range(int(cy - 38 * S), int(cy + 33 * S), 4 * S):
        d.line([(cx - 32 * S, y), (cx + 32 * S, y)], fill=(lens_col[0] // 5, lens_col[1] // 5, lens_col[2] // 5, 255),
               width=S)
    # the eye: concentric rings
    for r, col in ((27, accent), (24, (20, 26, 28)), (20, tuple(c // 2 for c in lens_col)), (15, lens_col),
                   (8, tuple(min(255, c + 60) for c in lens_col)), (3, (250, 250, 240))):
        d.ellipse([cx - r * S, cy - 4 * S - r * S, cx + r * S, cy - 4 * S + r * S], fill=col + (255,))
    if severe:
        # a hard horizontal shutter across the eye
        d.rectangle([cx - 30 * S, cy - 6 * S, cx + 30 * S, cy - 2 * S], fill=(16, 16, 18, 255))
    # status text blocks under the eye
    for i in range(5):
        w = rng.randint(8, 22) * S
        d.rectangle([cx - 28 * S + i * 12 * S, cy + 26 * S, cx - 28 * S + i * 12 * S + w * 0.5, cy + 28 * S],
                    fill=lens_col + (255,))
    # brass grille + plate
    for i in range(7):
        d.line([(cx - 18 * S + i * 6 * S, cy + 40 * S), (cx - 18 * S + i * 6 * S, cy + 50 * S)], fill=accent + (255,),
               width=2 * S)
    im = im.filter(ImageFilter.GaussianBlur(0.6 * S))
    # glow on the lens
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - 34 * S, cy - 38 * S, cx + 34 * S, cy + 30 * S], fill=lens_col + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(10 * S))
    im = Image.alpha_composite(im, glow)
    down(im, (128, 128)).save(path("graphics", "portraits", name + ".png"))


if __name__ == "__main__":
    flag()
    crest()
    icons()
    tallyhouse()
    courier_relay()
    dead_letter_office()
    portrait("tlc_registrar", (206, 196, 170), (110, 210, 160), BRASS, (28, 34, 34), seed=1)
    portrait("tlc_assessor", (186, 178, 156), (120, 200, 170), (150, 130, 90), (30, 30, 34), seed=2)
    portrait("tlc_inspector_general", (40, 38, 40), (235, 170, 80), (196, 160, 84), (22, 20, 22), seed=3, severe=True)
    print("misc art done")
