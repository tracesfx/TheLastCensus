"""
gen_ships.py - generates Bureau hull sprites AND their .ship files from one spec, so weapon/engine
slots always line up with the art.  Run from the mod root:  python tools/gen_ships.py [hull ...]

Visual language: ivory armour plates laid over a dark slate frame with visible seams, jade service
stripes, brass fittings, a lens "eye" on every hull, amber running lights.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import Canvas, design_to_ship, radial_bounds, max_extent  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOCKET_R = {("SMALL", "TURRET"): 5.5, ("MEDIUM", "TURRET"): 8.0, ("LARGE", "TURRET"): 12.0,
            ("SMALL", "HARDPOINT"): 4.0, ("MEDIUM", "HARDPOINT"): 6.0, ("LARGE", "HARDPOINT"): 9.0}


class Hull:
    def __init__(self, hid, name, size, W, H, cy_from_top, seed):
        self.id, self.name, self.size = hid, name, size
        self.W, self.H = W, H
        self.cy_top = cy_from_top
        self.c = Canvas(W, H, seed)
        self.slots = []     # (id, type, size, mount, x, y, angle, arc)
        self.engines = []   # (x, y, width, length, contrail)
        self.builtin_mods = ["tlc_protocols"]
        self.shield_fwd = 0.0

    def slot(self, sid, wtype, wsize, mount, x, y, angle, arc, mirror_id=None):
        """Design coords. Angle as authored: + = toward the ship's LEFT (image left), - = right.
        If mirror_id is given a mirrored slot is added at -x with the negated angle."""
        self.slots.append((sid, wtype, wsize, mount, x, y, angle, arc))
        if mirror_id:
            self.slots.append((mirror_id, wtype, wsize, mount, -x, y, -angle, arc))

    def engine(self, x, y, width, length, contrail):
        self.engines.append((x, y, width, length, contrail))

    def sockets(self):
        for (sid, wtype, wsize, mount, x, y, angle, arc) in self.slots:
            self.c.socket(x, y, SOCKET_R[(wsize, mount)], mount, angle)
        for (x, y, w, l, ct) in self.engines:
            self.c.nozzle(x, y, w, min(7.0, w * 0.9))

    def write(self):
        img = self.c.render()
        sprite_rel = "graphics/ships/%s.png" % self.id
        img.save(os.path.join(ROOT, sprite_rel))
        W, H = self.W, self.H
        cx = W / 2.0
        cy_bottom = H - self.cy_top
        mask = self.c.alpha_mask_final()
        pts = radial_bounds(mask, cx, self.cy_top, n=44)
        bounds = []
        for (px, py) in pts:
            bounds += [round((H - py) - cy_bottom, 1), round(cx - px, 1)]
        ext = max_extent(mask, cx, self.cy_top)
        slots = []
        for (sid, wtype, wsize, mount, x, y, angle, arc) in self.slots:
            # Design x is +right; an authored angle of -30 on a right-side slot points right, which is
            # negative (clockwise) in Starsector's CCW-from-forward convention, so it is stored unchanged.
            slots.append({
                "angle": float(angle),
                "arc": float(arc),
                "id": sid,
                "locations": design_to_ship(x, y, W, H, cx, cy_bottom),
                "mount": mount,
                "size": wsize,
                "type": wtype,
            })
        engines = []
        for (x, y, w, l, ct) in self.engines:
            engines.append({
                "angle": 180.0,
                "contrailSize": float(ct),
                "length": float(l),
                "location": design_to_ship(x, y, W, H, cx, cy_bottom),
                "style": "TLC_LEDGER",
                "width": float(w),
            })
        ship = {
            "bounds": bounds,
            "builtInMods": self.builtin_mods,
            "center": [cx, cy_bottom],
            "collisionRadius": round(ext * 1.08 + 4, 1),
            "engineSlots": engines,
            "height": H,
            "hullId": self.id,
            "hullName": self.name,
            "hullSize": self.size,
            "shieldCenter": [self.shield_fwd, 0.0],
            "shieldRadius": round(ext * 1.02 + 2, 1),
            "spriteName": sprite_rel,
            "style": "TLC_BUREAU",
            "viewOffset": 0,
            "weaponSlots": slots,
            "width": W,
        }
        with open(os.path.join(ROOT, "data", "hulls", self.id + ".ship"), "w", encoding="utf-8") as f:
            json.dump(ship, f, indent=4)
        print("wrote %s (%dx%d) ext=%.1f slots=%d engines=%d" % (self.id, W, H, ext, len(slots), len(engines)))


# ======================================================================= hulls

def tally():
    h = Hull("tlc_tally", "Tally", "FRIGATE", 56, 92, 50, seed=11)
    c = h.c
    c.part(("poly", [(-6, 5), (6, 5), (12, 30), (13, 74), (10, 89), (-10, 89), (-13, 74), (-12, 30)]), z=0.14, bevel=1.2,
           mat="slate2")
    c.part(("poly", [(0, 3), (6, 10), (12, 30), (-12, 30), (-6, 10)]), z=0.36, bevel=1.8, mat="ivory",
           panels={"dx": 4, "dy": 6})
    c.part(("poly", [(3, 31), (12.5, 31), (14, 46), (3, 46)]), z=0.34, bevel=1.5, mat="ivory", sym=True,
           panels={"dx": 4, "dy": 5})
    c.part(("poly", [(2.2, 47.5), (15, 47.5), (17, 52), (17, 70), (13, 77), (2.2, 77)]), z=0.32, bevel=1.6,
           mat="ivory", sym=True, panels={"dx": 4, "dy": 5})
    c.part(("rect", 14, 55, 19, 65), z=0.20, bevel=1.0, mat="slate", sym=True)
    c.part(("rrect", 18, 40, 26, 82, 2.5), z=0.26, bevel=1.5, mat="ivory2", sym=True, panels={"dx": 4, "dy": 6})
    c.part(("rect", 19.5, 56, 24.5, 66), z=0.24, bevel=0.6, mat="slate", sym=True)
    c.part(("rrect", -11, 77, 11, 90, 2), z=0.22, bevel=1.5, mat="slate", panels={"dx": 5, "dy": 5})
    c.stripe(("rect", 18, 45, 26, 48), mat="jade", sym=True)
    c.stripe(("rect", 18, 74, 26, 76), mat="jade", sym=True)
    c.stripe(("poly", [(3, 41), (13.6, 41), (13.9, 44), (3, 44)]), mat="jade", sym=True)
    c.part(("ellipse", 0, 57, 6.2, 6.2), z=0.40, bevel=1.0, mat="brass")
    c.part(("ellipse", 0, 57, 4.4, 4.4), z=0.46, bevel=2.5, mat="lens", dome=True, gloss=0.85)
    c.vent(0, 70, 3.6, 8, n=3, horizontal=False)
    c.hatch(7, 22, 3.0, 4.5, sym=True)
    c.greebles(5, 49, 15, 74, n=6, sym=True, seed=31)
    c.greebles(19, 50, 25, 80, n=4, sym=True, seed=32, smin=1.0, smax=2.4)
    c.greebles(3, 79, 10, 88, n=3, sym=True, seed=33)
    c.rivets([(13, 50), (16, 53), (16, 69)], sym=True)
    c.rivets([(5, 12), (10.5, 29)], sym=True)
    c.trim([(0, 8), (0, 15)], width=0.5)
    c.glyphs(-14, 64, n=2, size=0.9, seed=3)
    c.light(22, 41.5, sym=True)
    c.light(0, 4.5, color=(255, 120, 90), r=0.8)
    h.slot("WS 001", "ENERGY", "SMALL", "TURRET", 0, 19, 0, 240)
    h.slot("WS 002", "MISSILE", "SMALL", "HARDPOINT", 0, 37, 0, 10)
    h.slot("WS 003", "ENERGY", "SMALL", "TURRET", 22, 61, -30, 210, mirror_id="WS 004")
    h.engine(-5.5, 90, 7, 18, 22)
    h.engine(5.5, 90, 7, 18, 22)
    h.sockets()
    h.write()


def assessor():
    h = Hull("tlc_assessor", "Assessor", "DESTROYER", 104, 150, 78, seed=23)
    c = h.c
    c.part(("poly", [(-10, 7), (10, 7), (18, 38), (30, 54), (30, 118), (24, 147), (-24, 147), (-30, 118), (-30, 54),
                     (-18, 38)]), z=0.14, bevel=1.5, mat="slate2")
    c.part(("poly", [(30, 14), (39, 20), (39, 30), (30, 34)]), z=0.22, bevel=1.5, mat="slate", sym=True)
    c.part(("poly", [(1.5, 8), (27, 8), (32, 13), (32, 29), (27, 34), (1.5, 34)]), z=0.36, bevel=2.2, mat="ivory",
           sym=True, panels={"dx": 6, "dy": 7})
    c.part(("rect", 2.5, 35.5, 13, 57), z=0.30, bevel=1.6, mat="ivory2", sym=True, panels={"dx": 5, "dy": 6})
    c.part(("poly", [(2.5, 58.5), (23, 58.5), (28, 63), (28, 86), (2.5, 86)]), z=0.34, bevel=2.0, mat="ivory", sym=True,
           panels={"dx": 6, "dy": 7})
    c.part(("poly", [(2.5, 88), (28, 88), (28, 115), (22, 122), (2.5, 122)]), z=0.33, bevel=2.0, mat="ivory", sym=True,
           panels={"dx": 6, "dy": 7})
    for (y0, y1) in [(60, 76), (78, 94), (96, 112)]:
        c.part(("rrect", 30, y0, 45, y1, 2), z=0.27, bevel=1.4, mat="ivory2", sym=True)
        ym = (y0 + y1) / 2.0
        c.part(("rect", 33, ym - 1.0, 41, ym + 1.0), z=0.31, bevel=0.4, mat="brass", sym=True)
        c.groove([(31, y0 + 2), (44, y0 + 2)], width=0.35, sym=True)
    c.part(("rrect", -22, 120, 22, 148, 3), z=0.24, bevel=2.0, mat="slate", panels={"dx": 6, "dy": 6})
    c.stripe(("rect", 1.5, 27, 32, 30), mat="jade", sym=True)
    c.stripe(("rect", 2.5, 98, 28, 101), mat="jade", sym=True)
    c.stripe(("rect", 30, 60, 45, 62), mat="jade", sym=True)
    c.part(("ellipse", 0, 20, 9.0, 9.0), z=0.42, bevel=1.0, mat="brass")
    c.part(("ellipse", 0, 20, 6.8, 6.8), z=0.47, bevel=2.5, mat="lens", dome=True, gloss=0.9)
    c.vent(0, 108, 3.5, 22, n=4, horizontal=False)
    c.vent(0, 132, 20, 6, n=5)
    c.vent(21, 46, 3, 12, n=3, horizontal=False, sym=True)
    c.hatch(-21, 20, 5, 6, sym=True)
    c.greebles(5, 60, 26, 84, n=8, sym=True, seed=41)
    c.greebles(5, 90, 26, 120, n=8, sym=True, seed=42)
    c.greebles(4, 122, 20, 146, n=5, sym=True, seed=43)
    c.rivets([(4, 10), (26, 10), (31, 15)], sym=True)
    c.rivets([(26, 60), (27.5, 64), (27.5, 85)], sym=True)
    c.glyphs(-26, 90, n=3, size=1.1, seed=5)
    c.light(30, 11, sym=True)
    c.light(26, 121, color=(255, 120, 90), sym=True)
    h.slot("WS 001", "ENERGY", "MEDIUM", "TURRET", 0, 46, 0, 260)
    h.slot("WS 002", "BALLISTIC", "MEDIUM", "TURRET", 16, 72, -10, 230, mirror_id="WS 003")
    h.slot("WS 004", "MISSILE", "SMALL", "HARDPOINT", 21, 13, 0, 10, mirror_id="WS 005")
    h.slot("WS 006", "ENERGY", "SMALL", "TURRET", 37.5, 104, -100, 210, mirror_id="WS 007")
    for x in (-12, 0, 12):
        h.engine(x, 148, 9, 26, 40)
    h.sockets()
    h.write()


def magistrate():
    h = Hull("tlc_magistrate", "Magistrate", "CRUISER", 150, 210, 108, seed=37)
    c = h.c
    c.part(("poly", [(-11, 5), (11, 5), (26, 60), (44, 66), (44, 182), (26, 205), (-26, 205), (-44, 182), (-44, 66),
                     (-26, 60)]), z=0.14, bevel=1.5, mat="slate2")
    c.part(("poly", [(1.5, 6), (10, 11), (24, 58), (24, 69), (1.5, 69)]), z=0.34, bevel=2.2, mat="ivory", sym=True,
           panels={"dx": 6, "dy": 8})
    c.part(("poly", [(1.5, 71), (26, 71), (50, 75), (54, 82), (54, 104), (46, 111), (1.5, 111)]), z=0.36, bevel=2.6,
           mat="ivory", sym=True, panels={"dx": 7, "dy": 8})
    c.part(("rect", 40, 112, 52, 140), z=0.24, bevel=1.5, mat="slate", sym=True)
    c.part(("poly", [(1.5, 113), (40, 113), (42, 170), (34, 181), (1.5, 181)]), z=0.33, bevel=2.6, mat="ivory2", sym=True,
           panels={"dx": 7, "dy": 8})
    c.part(("rrect", 50, 90, 70, 152, 4), z=0.28, bevel=2.0, mat="ivory", sym=True, panels={"dx": 5, "dy": 7})
    c.part(("rrect", -16, 116, 16, 150, 4), z=0.50, bevel=2.4, mat="ivory", panels={"dx": 6, "dy": 7})
    c.part(("rrect", -11, 122, 11, 131, 2), z=0.56, bevel=1.4, mat="slate2", override=True)
    c.part(("rrect", -32, 178, 32, 206, 4), z=0.25, bevel=2.0, mat="slate", panels={"dx": 7, "dy": 6})
    c.stripe(("poly", [(1.5, 84), (54, 84), (54, 89), (1.5, 89)]), mat="jade", sym=True)
    c.stripe(("rect", 50, 97, 70, 101), mat="jade", sym=True)
    c.stripe(("rect", 1.5, 52, 24, 55), mat="jade", sym=True)
    c.part(("ellipse", 0, 161, 8.0, 8.0), z=0.50, bevel=1.0, mat="brass")
    c.part(("ellipse", 0, 161, 6.0, 6.0), z=0.56, bevel=2.5, mat="lens", dome=True, gloss=0.9)
    for x in (-7, -2.3, 2.3, 7):
        c.light(x, 126.5, color=(255, 200, 120), r=0.7, strength=0.8)
    c.vent(0, 192, 26, 6, n=6)
    c.vent(30, 128, 6, 14, n=4, sym=True, horizontal=False)
    c.vent(60, 140, 8, 6, n=3, sym=True)
    c.hatch(-30, 96, 6, 6, sym=True)
    c.greebles(4, 72, 48, 108, n=12, sym=True, seed=51)
    c.greebles(4, 114, 38, 178, n=14, sym=True, seed=52)
    c.greebles(52, 104, 68, 150, n=6, sym=True, seed=53, smin=1.0, smax=2.6)
    c.greebles(4, 10, 20, 66, n=6, sym=True, seed=54)
    c.rivets([(3, 8), (10, 13), (23, 58)], sym=True)
    c.rivets([(26, 72), (50, 76), (53.5, 82), (53.5, 103)], sym=True)
    c.glyphs(-22, 168, n=4, size=1.1, seed=9)
    c.light(54, 76, sym=True)
    c.light(66, 150, color=(255, 120, 90), sym=True)
    c.light(0, 5, color=(255, 120, 90), r=0.8)
    h.slot("WS 001", "ENERGY", "LARGE", "TURRET", 0, 38, 0, 270)
    h.slot("WS 002", "BALLISTIC", "MEDIUM", "TURRET", 36, 80, -15, 220, mirror_id="WS 003")
    h.slot("WS 004", "ENERGY", "MEDIUM", "TURRET", 60, 120, -70, 220, mirror_id="WS 005")
    h.slot("WS 006", "MISSILE", "MEDIUM", "HARDPOINT", 0, 98, 0, 20)
    h.slot("WS 007", "ENERGY", "SMALL", "TURRET", 21, 64, -45, 230, mirror_id="WS 008")
    h.slot("WS 009", "ENERGY", "SMALL", "TURRET", 37, 171, -135, 230, mirror_id="WS 010")
    for x in (-21, -7, 7, 21):
        h.engine(x, 206, 10, 34, 55)
    h.sockets()
    h.write()


def exchequer():
    h = Hull("tlc_exchequer", "Exchequer", "CAPITAL_SHIP", 220, 300, 156, seed=41)
    c = h.c
    c.part(("poly", [(-16, 7), (16, 7), (36, 60), (54, 66), (102, 96), (102, 222), (54, 250), (40, 294), (-40, 294),
                     (-54, 250), (-102, 222), (-102, 96), (-54, 66), (-36, 60)]), z=0.12, bevel=2.0, mat="slate2")
    c.part(("poly", [(1.5, 6), (16, 12), (40, 56), (44, 74), (1.5, 74)]), z=0.34, bevel=2.6, mat="ivory", sym=True,
           panels={"dx": 7, "dy": 9})
    c.part(("poly", [(54, 77), (92, 87), (100, 100), (100, 156), (54, 156)]), z=0.34, bevel=3.0, mat="ivory2", sym=True,
           panels={"dx": 9, "dy": 12, "breaks": 0.1})
    c.part(("poly", [(54, 159), (100, 159), (100, 214), (92, 232), (54, 242)]), z=0.34, bevel=3.0, mat="ivory2",
           sym=True, panels={"dx": 9, "dy": 12, "breaks": 0.1})
    c.part(("rrect", 1.5, 64, 52, 160, 7), z=0.42, bevel=3.5, mat="ivory", sym=True, panels={"dx": 8, "dy": 10})
    c.part(("rrect", 1.5, 162, 52, 254, 7), z=0.42, bevel=3.5, mat="ivory", sym=True, panels={"dx": 8, "dy": 10})
    for y in (112, 140, 176, 204):
        c.part(("rect", 57, y - 2, 97, y + 2), z=0.38, bevel=0.8, mat="brass", sym=True)
    c.part(("rrect", -30, 80, 30, 124, 5), z=0.53, bevel=2.8, mat="ivory", panels={"dx": 7, "dy": 8})
    c.part(("rrect", -20, 90, 20, 99, 2), z=0.58, bevel=1.4, mat="slate2", override=True)
    c.part(("ellipse", 0, 192, 22, 22), z=0.48, bevel=2.0, mat="brass")
    c.part(("ellipse", 0, 192, 17, 17), z=0.51, bevel=2.0, mat="jade2")
    c.part(("ellipse", 0, 192, 8, 8), z=0.55, bevel=2.0, mat="lens", dome=True, gloss=0.7)
    for a in range(8):
        ang = a * math.pi / 4
        c.groove([(math.cos(ang) * 9, 192 + math.sin(ang) * 9), (math.cos(ang) * 16, 192 + math.sin(ang) * 16)],
                 width=0.6)
    c.part(("rrect", -62, 248, 62, 296, 6), z=0.26, bevel=2.4, mat="slate", panels={"dx": 8, "dy": 7})
    c.stripe(("rect", 1.5, 130, 52, 136), mat="jade", sym=True)
    c.stripe(("poly", [(54, 80), (92, 90), (92, 96), (54, 86)]), mat="jade", sym=True)
    c.stripe(("rect", -30, 116, 30, 119), mat="jade")
    for x in (-15, -9, -3, 3, 9, 15):
        c.light(x, 94.5, color=(255, 200, 120), r=0.75, strength=0.8)
    c.vent(0, 232, 3.5, 26, n=5, horizontal=False)
    c.vent(0, 272, 30, 6, n=6)
    c.vent(80, 186, 8, 26, n=6, sym=True, horizontal=False)
    c.vent(26, 228, 14, 6, n=4, sym=True)
    c.hatch(-38, 210, 8, 10, sym=True)
    c.greebles(4, 66, 50, 158, n=18, sym=True, seed=61)
    c.greebles(4, 164, 50, 250, n=16, sym=True, seed=62)
    c.greebles(58, 92, 98, 230, n=16, sym=True, seed=63, smin=1.5, smax=4.0)
    c.greebles(6, 250, 58, 292, n=10, sym=True, seed=64)
    c.greebles(4, 14, 36, 72, n=8, sym=True, seed=65)
    c.rivets([(3, 8), (16, 13), (40, 57), (43, 73)], sym=True)
    c.rivets([(56, 79), (91, 88), (99, 100), (99, 155)], sym=True)
    c.rivets([(99, 160), (99, 213), (91, 231), (56, 241)], sym=True)
    c.glyphs(-48, 142, n=5, size=1.3, seed=13)
    c.light(98, 102, sym=True)
    c.light(96, 226, color=(255, 120, 90), sym=True)
    c.light(0, 6, color=(255, 120, 90), r=0.9)
    h.slot("WS 001", "ENERGY", "LARGE", "TURRET", 22, 48, -5, 260, mirror_id="WS 002")
    h.slot("WS 003", "BALLISTIC", "LARGE", "TURRET", 0, 152, 0, 300)
    h.slot("WS 004", "BALLISTIC", "MEDIUM", "TURRET", 76, 128, -30, 220, mirror_id="WS 005")
    h.slot("WS 006", "BALLISTIC", "MEDIUM", "TURRET", 76, 200, -100, 220, mirror_id="WS 007")
    h.slot("WS 008", "ENERGY", "MEDIUM", "TURRET", 36, 228, -150, 220, mirror_id="WS 009")
    h.slot("WS 010", "MISSILE", "MEDIUM", "HARDPOINT", 10, 24, 0, 20, mirror_id="WS 011")
    h.slot("WS 012", "ENERGY", "SMALL", "TURRET", 92, 104, -60, 240, mirror_id="WS 013")
    h.slot("WS 014", "ENERGY", "SMALL", "TURRET", 92, 220, -120, 240, mirror_id="WS 015")
    h.slot("WS 016", "ENERGY", "SMALL", "TURRET", 48, 262, -160, 240, mirror_id="WS 017")
    for x in (-44, -22, 0, 22, 44):
        h.engine(x, 296, 13, 46, 80)
    h.sockets()
    h.write()


def plenipotentiary():
    h = Hull("tlc_plenipotentiary", "Plenipotentiary", "CRUISER", 164, 228, 118, seed=53)
    c = h.c
    c.part(("poly", [(-9, 9), (9, 9), (20, 58), (46, 118), (46, 154), (24, 196), (24, 220), (-24, 220), (-24, 196),
                     (-46, 154), (-46, 118), (-20, 58)]), z=0.12, bevel=1.5, mat="slate2")
    c.part(("poly", [(22, 150), (74, 176), (78, 206), (24, 196)]), z=0.28, bevel=2.4, mat="black", sym=True,
           panels={"dx": 6, "dy": 7})
    c.part(("rect", 1.5, 52, 14, 200), z=0.32, bevel=2.2, mat="black", sym=True, panels={"dx": 5, "dy": 9})
    c.part(("poly", [(1.5, 88), (44, 120), (44, 152), (1.5, 181)]), z=0.36, bevel=2.6, mat="ivory", sym=True,
           panels={"dx": 6, "dy": 7})
    c.part(("poly", [(1.5, 10), (56, 10), (64, 18), (64, 46), (56, 54), (1.5, 54)]), z=0.38, bevel=2.6, mat="black",
           sym=True, panels={"dx": 7, "dy": 8})
    c.part(("rrect", 56, 16, 72, 48, 4), z=0.35, bevel=2.0, mat="gold", sym=True)
    c.stripe(("rect", 1.5, 14, 64, 16.5), mat="gold", sym=True)
    c.stripe(("rect", 1.5, 48, 64, 50.5), mat="gold", sym=True)
    c.stripe(("poly", [(23, 160), (70, 182), (71, 188), (23, 166)]), mat="gold", sym=True)
    c.stripe(("poly", [(1.5, 97), (34, 121), (34, 125), (1.5, 101)]), mat="gold", sym=True)
    c.part(("ellipse", 0, 136, 14, 14), z=0.46, bevel=1.5, mat="gold")
    c.part(("ellipse", 0, 136, 10.5, 10.5), z=0.51, bevel=2.5, mat="lens", dome=True, gloss=0.9)
    c.part(("rrect", -26, 198, 26, 224, 4), z=0.25, bevel=2.0, mat="slate", panels={"dx": 6, "dy": 6})
    c.vent(0, 210, 24, 5, n=5)
    c.vent(0, 168, 3.2, 12, n=3, horizontal=False)
    c.vent(48, 30, 6, 12, n=3, horizontal=False, sym=True)
    c.greebles(4, 92, 40, 178, n=14, sym=True, seed=71, mats=("slate", "ivory2", "black"))
    c.greebles(26, 158, 72, 200, n=8, sym=True, seed=72, mats=("slate2", "gold", "black"))
    c.greebles(3, 56, 13, 196, n=10, sym=True, seed=73, mats=("slate", "gold", "slate2"))
    c.rivets([(3, 12), (55, 12), (63, 19), (63, 45)], sym=True)
    c.rivets([(24, 152), (72, 176)], sym=True)
    c.glyphs(-58, 30, n=4, size=1.1, seed=17)
    for x in (-44, -30, 30, 44):
        c.light(x, 12.5, color=(255, 200, 120), r=0.8, strength=0.9)
    c.light(76, 204, color=(255, 120, 90), sym=True)
    h.slot("WS 001", "ENERGY", "LARGE", "HARDPOINT", 0, 28, 0, 5)
    h.slot("WS 002", "ENERGY", "MEDIUM", "TURRET", 40, 32, -10, 250, mirror_id="WS 003")
    h.slot("WS 004", "UNIVERSAL", "MEDIUM", "TURRET", 28, 136, -60, 240, mirror_id="WS 005")
    h.slot("WS 006", "ENERGY", "SMALL", "TURRET", 58, 184, -120, 240, mirror_id="WS 007")
    h.slot("WS 008", "MISSILE", "SMALL", "HARDPOINT", 7, 68, 0, 10, mirror_id="WS 009")
    h.engine(-12, 224, 14, 50, 70)
    h.engine(12, 224, 14, 50, 70)
    h.shield_fwd = 6.0
    h.sockets()
    h.write()


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "graphics", "ships"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "data", "hulls"), exist_ok=True)
    only = sys.argv[1:] or ["tally", "assessor", "magistrate", "exchequer", "plenipotentiary"]
    for name in only:
        globals()[name]()
