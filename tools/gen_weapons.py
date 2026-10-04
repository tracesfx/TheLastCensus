"""
gen_weapons.py - Bureau weapon sprites (turret + hardpoint) and the Subpoena missile.
Conventions (verified against vanilla): weapons face up; turret AND hardpoint sprites are centred on
the slot; muzzle offsets are measured from the sprite centre, so hardpoint art puts the breech in the
lower half and the barrel up to the top edge.
Run from the mod root:  python tools/gen_weapons.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import Canvas  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "graphics", "weapons")


def save(c, name, outline=0.5):
    img = c.render(grime=0.10, outline=outline, ao=0.45, spec=0.45)
    img.save(os.path.join(OUT, name))
    print("wrote", name, img.size)


# --------------------------------------------------------------- Writ Projector (S energy beam)
def writ_turret():
    c = Canvas(24, 24, seed=101)
    c.part(("ellipse", 0, 13, 8.5, 8.5), z=0.30, bevel=1.2, mat="slate")
    c.part(("ellipse", 0, 13, 7.0, 7.0), z=0.36, bevel=1.4, mat="ivory")
    c.part(("rect", -2.6, 2.0, 2.6, 12), z=0.44, bevel=0.8, mat="slate2")
    c.part(("rect", -1.6, 1.0, 1.6, 4.0), z=0.50, bevel=0.5, mat="brass")
    c.part(("ellipse", 0, 14.5, 3.0, 3.0), z=0.46, bevel=1.0, mat="jade", dome=True)
    c.stripe(("rect", -7, 16.5, 7, 18), mat="jade")
    c.light(0, 2.0, color=(255, 210, 120), r=0.7, strength=0.7)
    save(c, "tlc_writ_turret.png")


def writ_hardpoint():
    c = Canvas(14, 28, seed=102)
    c.part(("rrect", -5.5, 13, 5.5, 26, 1.5), z=0.30, bevel=1.0, mat="slate")
    c.part(("rrect", -4.5, 14, 4.5, 24, 1.2), z=0.36, bevel=1.0, mat="ivory")
    c.part(("rect", -2.4, 2.0, 2.4, 15), z=0.44, bevel=0.7, mat="slate2")
    c.part(("rect", -1.5, 0.8, 1.5, 3.6), z=0.50, bevel=0.5, mat="brass")
    c.stripe(("rect", -4.5, 20, 4.5, 21.5), mat="jade")
    c.light(0, 1.6, color=(255, 210, 120), r=0.7, strength=0.7)
    save(c, "tlc_writ_hardpoint.png")


# --------------------------------------------------------------- Subpoena SRM (S missile)
def subpoena_turret():
    c = Canvas(22, 22, seed=111)
    c.part(("rrect", -8.5, 4.5, 8.5, 18.5, 2), z=0.30, bevel=1.0, mat="slate")
    c.part(("rrect", -7.5, 5.5, 7.5, 17.5, 1.8), z=0.36, bevel=1.0, mat="ivory")
    for x in (-3.4, 3.4):
        c.part(("ellipse", x, 8.5, 2.6, 2.6), z=0.30, bevel=0.5, mat="dark", override=True)
        c.part(("ellipse", x, 8.2, 1.3, 1.3), z=0.36, bevel=0.5, mat="jade", dome=True)
    c.stripe(("rect", -7.5, 13.5, 7.5, 15), mat="jade")
    c.glyphs(-6, 15.6, n=2, size=0.6, seed=4)
    save(c, "tlc_subpoena_turret.png")


def subpoena_hardpoint():
    c = Canvas(14, 24, seed=112)
    c.part(("rrect", -6.5, 3, 6.5, 22, 1.5), z=0.30, bevel=1.0, mat="slate")
    c.part(("rrect", -5.5, 4, 5.5, 21, 1.2), z=0.36, bevel=1.0, mat="ivory")
    for x in (-2.8, 2.8):
        c.part(("ellipse", x, 6.5, 2.2, 2.2), z=0.30, bevel=0.5, mat="dark", override=True)
        c.part(("ellipse", x, 6.3, 1.1, 1.1), z=0.36, bevel=0.5, mat="jade", dome=True)
    c.stripe(("rect", -5.5, 15, 5.5, 16.5), mat="jade")
    save(c, "tlc_subpoena_hardpoint.png")


def subpoena_missile():
    c = Canvas(8, 20, seed=113)
    c.part(("poly", [(-2.6, 15), (-3.8, 19.5), (-1.2, 18)]), z=0.25, bevel=0.4, mat="brass", sym=True)
    c.part(("rrect", -2.2, 2.5, 2.2, 18.5, 1.6), z=0.35, bevel=0.9, mat="ivory")
    c.part(("poly", [(0, 0.5), (2.0, 3.5), (-2.0, 3.5)]), z=0.38, bevel=0.6, mat="jade")
    c.stripe(("rect", -2.2, 7.5, 2.2, 9.0), mat="jade")
    out = os.path.join(ROOT, "graphics", "missiles", "tlc_subpoena.png")
    c.render(grime=0.05, outline=0.4).save(out)
    print("wrote tlc_subpoena.png")


# --------------------------------------------------------------- Accrual Autocannon (M ballistic)
def accrual_turret():
    c = Canvas(40, 40, seed=121)
    oct_pts = [(math.cos(math.pi / 8 + k * math.pi / 4) * 15, 22 + math.sin(math.pi / 8 + k * math.pi / 4) * 15)
               for k in range(8)]
    c.part(("poly", oct_pts), z=0.28, bevel=1.4, mat="slate")
    c.part(("rrect", -11, 13, 11, 31, 3), z=0.36, bevel=1.6, mat="ivory", panels={"dx": 4, "dy": 5})
    for x in (-4.2, 4.2):
        c.part(("rect", x - 1.8, 1.5, x + 1.8, 16), z=0.42, bevel=0.7, mat="slate2")
        c.part(("rect", x - 2.3, 1.0, x + 2.3, 3.6), z=0.46, bevel=0.5, mat="brass")
        c.part(("rect", x - 2.2, 9.0, x + 2.2, 10.5), z=0.45, bevel=0.4, mat="slate")
    c.part(("rect", -6.5, 13.5, 6.5, 17.5), z=0.44, bevel=0.6, mat="slate")
    c.stripe(("rect", -11, 25, 11, 27), mat="jade")
    c.part(("rect", -3, 29, 3, 32), z=0.40, bevel=0.4, mat="brass")
    c.greebles(-9, 18, 9, 30, n=4, seed=5, smin=1.0, smax=2.2)
    save(c, "tlc_accrual_turret.png")


def accrual_hardpoint():
    c = Canvas(24, 44, seed=122)
    c.part(("rrect", -11, 21, 11, 42, 2.5), z=0.28, bevel=1.3, mat="slate")
    c.part(("rrect", -9.5, 22, 9.5, 40, 2.2), z=0.36, bevel=1.4, mat="ivory", panels={"dx": 4, "dy": 5})
    for x in (-4.2, 4.2):
        c.part(("rect", x - 1.8, 1.5, x + 1.8, 24), z=0.42, bevel=0.7, mat="slate2")
        c.part(("rect", x - 2.3, 1.0, x + 2.3, 3.6), z=0.46, bevel=0.5, mat="brass")
        c.part(("rect", x - 2.2, 11, x + 2.2, 12.5), z=0.45, bevel=0.4, mat="slate")
    c.stripe(("rect", -9.5, 33, 9.5, 35), mat="jade")
    c.greebles(-8, 26, 8, 38, n=4, seed=6, smin=1.0, smax=2.2)
    save(c, "tlc_accrual_hardpoint.png")


# --------------------------------------------------------------- Injunction Emitter (M energy)
def injunction_turret():
    c = Canvas(36, 36, seed=131)
    c.part(("ellipse", 0, 20, 13.5, 13.5), z=0.28, bevel=1.4, mat="slate")
    c.part(("ellipse", 0, 20, 11.5, 11.5), z=0.36, bevel=2.0, mat="ivory", panels={"dx": 4, "dy": 5})
    c.part(("poly", [(-5.5, 13), (-4.0, 3), (-2.2, 3), (-2.2, 13)]), z=0.44, bevel=0.6, mat="slate2", sym=True)
    c.part(("rect", -1.0, 4.5, 1.0, 13), z=0.42, bevel=0.4, mat="jade")
    c.part(("ellipse", 0, 4.5, 1.8, 1.8), z=0.50, bevel=0.6, mat="lens", dome=True, gloss=0.8)
    c.part(("ellipse", 0, 21, 5.0, 5.0), z=0.44, bevel=1.2, mat="jade2", dome=True, gloss=0.5)
    c.stripe(("rect", -11.5, 27, 11.5, 28.5), mat="jade")
    c.light(0, 4.5, color=(160, 255, 200), r=0.8, strength=0.6)
    save(c, "tlc_injunction_turret.png")


def injunction_hardpoint():
    c = Canvas(24, 40, seed=132)
    c.part(("rrect", -11, 18, 11, 38, 3), z=0.28, bevel=1.3, mat="slate")
    c.part(("rrect", -9.5, 19, 9.5, 36, 2.5), z=0.36, bevel=1.6, mat="ivory", panels={"dx": 4, "dy": 5})
    c.part(("poly", [(-5.5, 20), (-4.0, 2), (-2.2, 2), (-2.2, 20)]), z=0.44, bevel=0.6, mat="slate2", sym=True)
    c.part(("rect", -1.0, 3.5, 1.0, 20), z=0.42, bevel=0.4, mat="jade")
    c.part(("ellipse", 0, 3.5, 1.8, 1.8), z=0.50, bevel=0.6, mat="lens", dome=True, gloss=0.8)
    c.part(("ellipse", 0, 28, 4.5, 4.5), z=0.44, bevel=1.2, mat="jade2", dome=True, gloss=0.5)
    c.light(0, 3.5, color=(160, 255, 200), r=0.8, strength=0.6)
    save(c, "tlc_injunction_hardpoint.png")


# --------------------------------------------------------------- Foreclosure Battery (L energy)
def foreclosure_turret():
    c = Canvas(60, 60, seed=141)
    c.part(("rrect", -20, 22, 20, 52, 6), z=0.26, bevel=1.8, mat="slate")
    c.part(("rrect", -17, 24, 17, 50, 5), z=0.34, bevel=2.0, mat="ivory", panels={"dx": 5, "dy": 6})
    c.part(("rrect", -21, 30, -15, 44, 1.5), z=0.30, bevel=0.8, mat="jade2")
    c.part(("rrect", 15, 30, 21, 44, 1.5), z=0.30, bevel=0.8, mat="jade2")
    c.part(("rect", -4.2, 2.0, 4.2, 30), z=0.42, bevel=1.0, mat="slate2")
    for y in (8, 13, 18, 23):
        c.part(("rect", -5.6, y - 1.2, 5.6, y + 1.2), z=0.47, bevel=0.6, mat="copper")
    c.part(("rect", -5.0, 1.0, 5.0, 4.0), z=0.48, bevel=0.6, mat="brass")
    c.part(("ellipse", 0, 38, 7.5, 7.5), z=0.40, bevel=1.2, mat="brass")
    c.part(("ellipse", 0, 38, 5.5, 5.5), z=0.44, bevel=2.0, mat="lens", dome=True, gloss=0.8)
    c.stripe(("rect", -17, 46, 17, 48), mat="jade")
    c.greebles(-15, 26, 15, 34, n=5, sym=False, seed=8, smin=1.2, smax=3.0)
    c.light(0, 1.8, color=(160, 255, 200), r=1.0, strength=0.7)
    save(c, "tlc_foreclosure_turret.png")


def foreclosure_hardpoint():
    c = Canvas(34, 66, seed=142)
    c.part(("rrect", -16, 32, 16, 64, 4), z=0.26, bevel=1.6, mat="slate")
    c.part(("rrect", -14, 34, 14, 62, 3.5), z=0.34, bevel=1.8, mat="ivory", panels={"dx": 5, "dy": 6})
    c.part(("rect", -4.2, 2.0, 4.2, 36), z=0.42, bevel=1.0, mat="slate2")
    for y in (9, 15, 21, 27):
        c.part(("rect", -5.6, y - 1.2, 5.6, y + 1.2), z=0.47, bevel=0.6, mat="copper")
    c.part(("rect", -5.0, 1.0, 5.0, 4.0), z=0.48, bevel=0.6, mat="brass")
    c.part(("ellipse", 0, 47, 6.5, 6.5), z=0.40, bevel=1.2, mat="brass")
    c.part(("ellipse", 0, 47, 4.8, 4.8), z=0.44, bevel=2.0, mat="lens", dome=True, gloss=0.8)
    c.stripe(("rect", -14, 57, 14, 59), mat="jade")
    c.light(0, 1.8, color=(160, 255, 200), r=1.0, strength=0.7)
    save(c, "tlc_foreclosure_hardpoint.png")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "graphics", "missiles"), exist_ok=True)
    for fn in (writ_turret, writ_hardpoint, subpoena_turret, subpoena_hardpoint, subpoena_missile,
               accrual_turret, accrual_hardpoint, injunction_turret, injunction_hardpoint,
               foreclosure_turret, foreclosure_hardpoint):
        fn()
