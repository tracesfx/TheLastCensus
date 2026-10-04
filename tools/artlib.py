"""
artlib.py - procedural sprite toolkit for The Last Census.

Renders layered, beveled, panel-lined "Domain civil service" hardware with a single light
direction (upper-left), consistent palette and supersampled anti-aliasing.

Coordinate convention for authoring: design units = final pixels.
  x = lateral offset from the sprite centre line (+ = image right)
  y = distance from the TOP edge of the image (ships face up)
Everything is rendered at SS x resolution and downsampled.
"""
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 4  # supersampling factor

# ---------------------------------------------------------------- palette
PAL = {
    # name: (base rgb, roughness 0..1, metal 0..1)
    "ivory":   ((204, 194, 168), 0.55, 0.05),
    "ivory2":  ((182, 173, 150), 0.60, 0.05),
    "slate":   ((78, 84, 88),    0.70, 0.30),
    "slate2":  ((58, 63, 67),    0.75, 0.30),
    "dark":    ((36, 39, 42),    0.80, 0.20),
    "jade":    ((96, 156, 124),  0.45, 0.10),
    "jade2":   ((70, 122, 98),   0.50, 0.10),
    "brass":   ((176, 140, 78),  0.30, 0.85),
    "black":   ((30, 30, 34),    0.25, 0.40),   # lacquer (Inspector-General)
    "gold":    ((196, 160, 84),  0.25, 0.90),
    "lens":    ((40, 92, 84),    0.10, 0.20),
    "copper":  ((150, 96, 64),   0.40, 0.80),
}
LIGHT = np.array([-0.55, -0.65, 0.52])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
HALF = (LIGHT + np.array([0, 0, 1.0]))
HALF = HALF / np.linalg.norm(HALF)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def value_noise(w, h, cell, rng, octaves=3):
    """Cheap fractal value noise in [0,1], shape (h, w)."""
    out = np.zeros((h, w), dtype=np.float32)
    amp, tot = 1.0, 0.0
    c = cell
    for _ in range(octaves):
        gw, gh = max(2, int(w / c) + 2), max(2, int(h / c) + 2)
        grid = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((grid * 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
        out += amp * (np.asarray(im, dtype=np.float32) / 255.0)
        tot += amp
        amp *= 0.5
        c = max(2, c / 2)
    return out / tot


class Canvas:
    """A supersampled height/material canvas.

    W, H are FINAL pixel dimensions. All draw calls take design units (final px, centre-line x, top y).
    """

    def __init__(self, W, H, seed=1):
        self.W, self.H = W, H
        self.w, self.h = W * SS, H * SS
        self.height = np.zeros((self.h, self.w), np.float32)
        self.mask = np.zeros((self.h, self.w), np.float32)
        self.mat = np.full((self.h, self.w), -1, np.int16)
        self.albedo_mul = np.ones((self.h, self.w), np.float32)
        self.emissive = np.zeros((self.h, self.w, 3), np.float32)
        self.gloss = np.zeros((self.h, self.w), np.float32)
        self.matnames = list(PAL.keys())
        self.rng = np.random.default_rng(seed)
        self.prng = random.Random(seed)
        self.lines = Image.new("L", (self.w, self.h), 0)     # engraved panel lines (darken + dent)
        self.ldraw = ImageDraw.Draw(self.lines)
        self.highlights = Image.new("L", (self.w, self.h), 0)  # raised trim lines
        self.hdraw = ImageDraw.Draw(self.highlights)

    # ---- coordinate helpers
    def P(self, x, y):
        return ((self.W / 2.0 + x) * SS, y * SS)

    def poly_pts(self, pts, mirror=False):
        if mirror:
            pts = [(-x, y) for (x, y) in pts]
        return [self.P(x, y) for (x, y) in pts]

    def _mask_from(self, fn):
        im = Image.new("L", (self.w, self.h), 0)
        d = ImageDraw.Draw(im)
        fn(d)
        return im

    # ---- primitive part: add a raised plate
    def part(self, shape, z=0.3, bevel=2.0, mat="ivory", mirror=False, sym=False, panels=None,
             gloss=0.0, dome=False, override=False):
        """shape: ('poly', [(x,y)...]) | ('rect', x0,y0,x1,y1) | ('rrect', x0,y0,x1,y1,r) | ('ellipse', cx,cy,rx,ry)
        sym=True draws the shape and its mirror image."""
        variants = [False, True] if sym else [mirror]
        for mir in variants:
            im = self._mask_from(lambda d: self._draw_shape(d, shape, mir, 255))
            m = np.asarray(im, np.float32) / 255.0
            if m.max() <= 0:
                continue
            b = max(1.0, bevel * SS)
            blur = np.asarray(im.filter(ImageFilter.GaussianBlur(b * 0.75)), np.float32) / 255.0
            prof = smoothstep(0.5, 1.0, blur)  # 0 at edge -> 1 inside
            if dome:
                # spherical-ish dome profile from blurred mask with a wide radius
                big = np.asarray(im.filter(ImageFilter.GaussianBlur(b * 2.5)), np.float32) / 255.0
                prof = np.sqrt(np.clip(smoothstep(0.45, 1.0, big), 0, 1))
            hz = z + 0.18 * prof
            sel = m > 0.5
            if dome or override:
                self.height[sel] = hz[sel]
            else:
                self.height[sel] = np.maximum(self.height[sel], hz[sel])
            self.mask = np.maximum(self.mask, m)
            mi = self.matnames.index(mat)
            self.mat[sel] = mi
            self.gloss[sel] = gloss
            if panels:
                self._panels(shape, mir, panels, im)

    def _draw_shape(self, d, shape, mir, fill):
        kind = shape[0]
        if kind == "poly":
            d.polygon(self.poly_pts(shape[1], mir), fill=fill)
        elif kind in ("rect", "rrect"):
            x0, y0, x1, y1 = shape[1:5]
            if mir:
                x0, x1 = -x1, -x0
            a, b = self.P(x0, y0), self.P(x1, y1)
            box = [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
            if kind == "rect":
                d.rectangle(box, fill=fill)
            else:
                d.rounded_rectangle(box, radius=shape[5] * SS, fill=fill)
        elif kind == "ellipse":
            cx, cy, rx, ry = shape[1:5]
            if mir:
                cx = -cx
            c = self.P(cx, cy)
            d.ellipse([c[0] - rx * SS, c[1] - ry * SS, c[0] + rx * SS, c[1] + ry * SS], fill=fill)

    def _panels(self, shape, mir, spec, partmask):
        """Engrave panel lines inside a part. spec = dict(dx=, dy=, breaks=prob, inset=)"""
        dx = spec.get("dx", 10) * SS
        dy = spec.get("dy", 12) * SS
        inset = spec.get("inset", 2) * SS
        br = spec.get("breaks", 0.25)
        bbox = partmask.getbbox()
        if not bbox:
            return
        er = partmask.filter(ImageFilter.MinFilter(int(inset) * 2 + 1)) if inset >= 1 else partmask
        layer = Image.new("L", (self.w, self.h), 0)
        d = ImageDraw.Draw(layer)
        x0, y0, x1, y1 = bbox
        lw = max(1, SS // 2)
        # horizontal seams
        yy = y0 + dy * (0.5 + 0.5 * self.prng.random())
        while yy < y1:
            xs = x0
            while xs < x1:
                seg = dx * (1 + 2 * self.prng.random())
                if self.prng.random() > br:
                    d.line([(xs, yy), (min(x1, xs + seg), yy)], fill=255, width=lw)
                xs += seg
            yy += dy * (0.7 + 0.6 * self.prng.random())
        # vertical seams (sparser), keep symmetric feel by using centre-relative positions
        cxp = self.w / 2
        k = 1
        while True:
            off = k * dx * 1.3
            if cxp - off < x0 and cxp + off > x1:
                break
            for xv in (cxp - off, cxp + off):
                if x0 < xv < x1:
                    ys = y0
                    while ys < y1:
                        seg = dy * (1 + 2 * self.prng.random())
                        if self.prng.random() > br:
                            d.line([(xv, ys), (xv, min(y1, ys + seg))], fill=255, width=lw)
                        ys += seg
            k += 1
            if k > 40:
                break
        layer = Image.fromarray(np.minimum(np.asarray(layer), np.asarray(er)))
        self.lines = Image.fromarray(np.maximum(np.asarray(self.lines), np.asarray(layer)))
        self.ldraw = ImageDraw.Draw(self.lines)
        # per-plate tonal + height variation on a centre-symmetric grid
        pm = np.asarray(partmask) > 127
        ys, xs = np.nonzero(pm)
        if len(xs):
            cellx = max(2, int(dx * 1.3))
            celly = max(2, int(dy))
            kx = np.abs(xs - cxp) // cellx
            ky = (ys - y0) // celly
            key = (kx * 7919 + ky * 104729 + self.prng.randint(0, 10 ** 6)) % 1000003
            rnd = (np.sin(key * 12.9898) * 43758.5453) % 1.0
            self.albedo_mul[ys, xs] *= (0.93 + 0.12 * rnd).astype(np.float32)
            self.height[ys, xs] += (0.012 * (rnd - 0.5)).astype(np.float32)

    # ---- details
    def groove(self, pts, width=0.6, mirror=False, sym=False):
        variants = [False, True] if sym else [mirror]
        for mir in variants:
            self.ldraw.line(self.poly_pts(pts, mir), fill=255, width=max(1, int(width * SS)))

    def trim(self, pts, width=0.6, mirror=False, sym=False):
        variants = [False, True] if sym else [mirror]
        for mir in variants:
            self.hdraw.line(self.poly_pts(pts, mir), fill=255, width=max(1, int(width * SS)))

    def stripe(self, shape, mat="jade", sym=False, mirror=False):
        """Paint a material over an existing area without changing height."""
        variants = [False, True] if sym else [mirror]
        for mir in variants:
            im = self._mask_from(lambda d: self._draw_shape(d, shape, mir, 255))
            m = (np.asarray(im) > 127) & (self.mask > 0.5)
            self.mat[m] = self.matnames.index(mat)

    def vent(self, x, y, w, h, n=4, sym=False, mirror=False, horizontal=True):
        """Dark recessed grille with slats."""
        variants = [False, True] if sym else [mirror]
        for mir in variants:
            xx = -x if mir else x
            self.part(("rect", xx - w / 2, y - h / 2, xx + w / 2, y + h / 2), z=self._h_max(xx, y, max(w, h) / 2) - 0.07,
                      bevel=0.5, mat="dark", override=True)
            for i in range(n):
                if horizontal:
                    yy = y - h / 2 + (i + 0.5) * h / n
                    self.groove([(xx - w / 2 + 0.6, yy), (xx + w / 2 - 0.6, yy)], width=0.45)
                else:
                    xv = xx - w / 2 + (i + 0.5) * w / n
                    self.groove([(xv, y - h / 2 + 0.6), (xv, y + h / 2 - 0.6)], width=0.45)

    def hatch(self, x, y, w, h, sym=False, mirror=False):
        variants = [False, True] if sym else [mirror]
        for mir in variants:
            xx = -x if mir else x
            self.groove([(xx - w / 2, y - h / 2), (xx + w / 2, y - h / 2), (xx + w / 2, y + h / 2),
                         (xx - w / 2, y + h / 2), (xx - w / 2, y - h / 2)], width=0.45)

    def light(self, x, y, color=(255, 190, 90), r=0.9, sym=False, mirror=False, strength=1.0):
        variants = [False, True] if sym else [mirror]
        for mir in variants:
            xx = -x if mir else x
            cx, cy = self.P(xx, y)
            rr = r * SS
            yy, xx2 = np.ogrid[:self.h, :self.w]
            dist = np.sqrt((xx2 - cx) ** 2 + (yy - cy) ** 2)
            core = np.clip(1.0 - dist / rr, 0, 1)
            halo = np.clip(1.0 - dist / (rr * 3.0), 0, 1) ** 2 * 0.45
            a = np.maximum(core, halo) * strength
            col = np.array(color, np.float32) / 255.0
            self.emissive = np.maximum(self.emissive, a[..., None] * col[None, None, :])

    def glyphs(self, x, y, n=4, size=1.2, sym=False, mirror=False, seed=0):
        """Registry markings: tiny blocky characters engraved as dark marks."""
        r = random.Random(seed)
        variants = [False, True] if sym else [mirror]
        pattern = [[r.random() < 0.55 for _ in range(6)] for _ in range(n)]
        for mir in variants:
            for i in range(n):
                cx = x + i * size * 2.6
                xx = -cx if mir else cx
                for j, on in enumerate(pattern[i]):
                    if on:
                        px = xx + (j % 2) * size * 0.9
                        py = y + (j // 2) * size * 0.9
                        a = self.P(px, py)
                        self.ldraw.rectangle([a[0], a[1], a[0] + size * 0.8 * SS, a[1] + size * 0.8 * SS], fill=200)

    def socket(self, x, y, r, mount="TURRET", angle=0.0):
        """Weapon mount socket: raised collar with a recessed (not black) well, like vanilla mounts."""
        z = self._h_max(x, y, r + 1.4)
        if mount == "TURRET":
            self.part(("ellipse", x, y, r + 1.4, r + 1.4), z=z + 0.02, bevel=0.9, mat="slate", override=True)
            self.part(("ellipse", x, y, r, r), z=z - 0.03, bevel=0.7, mat="slate2", override=True)
            self.part(("ellipse", x, y, r * 0.45, r * 0.45), z=z - 0.01, bevel=0.5, mat="slate", override=True)
            for k in range(6):
                a = k * math.pi / 3
                self.groove([(x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55),
                             (x + math.cos(a) * r * 0.92, y + math.sin(a) * r * 0.92)], width=0.3)
        else:
            self.part(("rrect", x - r - 0.8, y - r * 1.4, x + r + 0.8, y + r, 1.0), z=z + 0.02, bevel=0.7, mat="slate",
                      override=True)
            self.part(("rect", x - r * 0.65, y - r * 1.0, x + r * 0.65, y + r * 0.55), z=z - 0.03, bevel=0.5,
                      mat="slate2", override=True)

    def greebles(self, x0, y0, x1, y1, n=6, sym=False, seed=0, mats=("slate", "ivory2", "slate2"), zoff=0.04,
                 smin=1.2, smax=3.5):
        """Scatter small raised boxes (pipes, junction boxes, sensor blisters) inside a region."""
        r = random.Random(seed)
        for _ in range(n):
            w = r.uniform(smin, smax)
            h = r.uniform(smin, smax)
            cx = r.uniform(x0, x1)
            cy = r.uniform(y0, y1)
            z = self._h_at(cx, cy)
            if z <= 0.01:
                continue
            m = r.choice(mats)
            shape = ("rrect", cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, min(w, h) * 0.25)
            self.part(shape, z=z + zoff, bevel=0.5, mat=m, sym=sym)

    def rivets(self, pts, spacing=2.2, sym=False):
        """Dotted line of tiny raised studs."""
        variants = [False, True] if sym else [False]
        for mir in variants:
            for i in range(len(pts) - 1):
                (ax, ay), (bx, by) = pts[i], pts[i + 1]
                L = math.hypot(bx - ax, by - ay)
                n = max(1, int(L / spacing))
                for k in range(n + 1):
                    t = k / n
                    x = ax + (bx - ax) * t
                    y = ay + (by - ay) * t
                    xx = -x if mir else x
                    c = self.P(xx, y)
                    rr = 0.32 * SS
                    self.hdraw.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=255)

    def nozzle(self, x, y, w, h):
        z = self._h_at(x, y - h / 2)
        self.part(("rrect", x - w / 2 - 1.0, y - h, x + w / 2 + 1.0, y, 1.2), z=max(0.08, z + 0.01), bevel=0.8,
                  mat="slate2", override=True)
        self.part(("rrect", x - w / 2, y - h * 0.8, x + w / 2, y - 0.4, 0.8), z=max(0.02, z - 0.08), bevel=0.6,
                  mat="dark", override=True)
        cx, cy = self.P(x, y - 1.0)
        self.light(x, y - 1.2, color=(150, 230, 190), r=w * 0.32, strength=0.55)

    def _h_max(self, x, y, r):
        px, py = self.P(x, y)
        rr = r * SS
        x0, x1 = int(max(0, px - rr)), int(min(self.w, px + rr + 1))
        y0, y1 = int(max(0, py - rr)), int(min(self.h, py + rr + 1))
        if x1 <= x0 or y1 <= y0:
            return 0.0
        return float(self.height[y0:y1, x0:x1].max())

    def _h_at(self, x, y):
        px, py = self.P(x, y)
        px = int(min(self.w - 1, max(0, px)))
        py = int(min(self.h - 1, max(0, py)))
        return float(self.height[py, px])

    # ---- final render
    def render(self, grime=0.18, outline=0.55, ao=0.55, spec=0.35, wear_seed=7):
        h = self.height.copy()
        lines = np.asarray(self.lines, np.float32) / 255.0
        hil = np.asarray(self.highlights, np.float32) / 255.0
        h = h - lines * 0.05 + hil * 0.025
        m_im0 = Image.fromarray((self.mask * 255).astype(np.uint8))
        pillow = np.asarray(m_im0.filter(ImageFilter.GaussianBlur(SS * 6.0)), np.float32) / 255.0
        h = h + 0.22 * pillow * (self.mask > 0.5)
        # smooth tiny aliasing in height
        hs = np.asarray(Image.fromarray(np.clip(h * 255 / 1.2, 0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(SS * 0.35)), np.float32) / 255.0 * 1.2
        gy, gx = np.gradient(hs)
        k = 15.0 * SS / 4.0
        nx, ny, nz = -gx * k, -gy * k, np.ones_like(hs)
        nl = np.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = nx / nl, ny / nl, nz / nl
        diff = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
        sp = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)

        # albedo per material
        alb = np.zeros((self.h, self.w, 3), np.float32)
        rough = np.ones((self.h, self.w), np.float32)
        metal = np.zeros((self.h, self.w), np.float32)
        for i, name in enumerate(self.matnames):
            sel = self.mat == i
            if not sel.any():
                continue
            col, r, mt = PAL[name]
            alb[sel] = np.array(col, np.float32) / 255.0
            rough[sel] = r
            metal[sel] = mt
        # weathering: large blotches + fine speckle + per-panel tint
        rng = np.random.default_rng(wear_seed)
        n1 = value_noise(self.w, self.h, 28 * SS, rng, 3)
        n2 = value_noise(self.w, self.h, 3 * SS, rng, 2)
        wear = 1.0 - grime * (0.65 * smoothstep(0.45, 0.9, n1) + 0.35 * (n2 - 0.5))
        alb *= wear[..., None]
        alb *= (1.0 - 0.8 * lines)[..., None]
        alb *= self.albedo_mul[..., None]
        alb = alb * (1.0 + 0.25 * hil)[..., None]

        # ambient occlusion from height
        hb = np.asarray(Image.fromarray(np.clip(hs * 200, 0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(SS * 3.0)), np.float32) / 200.0
        occ = np.clip((hb - hs) * 3.6, 0, 1)
        # directional cast shadow (light from upper-left -> shadows fall lower-right)
        sdist = int(1.6 * SS)
        shifted = np.zeros_like(hs)
        shifted[sdist:, sdist:] = hs[:-sdist, :-sdist]
        sh_raw = np.clip((shifted - hs - 0.015) * 14.0, 0, 1)
        sh = np.asarray(Image.fromarray((sh_raw * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(SS * 0.8)), np.float32) / 255.0
        ambient = 0.40
        shade = ambient + 0.82 * diff
        shade *= (1.0 - ao * occ)
        shade *= (1.0 - 0.45 * sh)
        shininess = 8 + 60 * (1 - rough) + 120 * self.gloss
        specv = spec * (sp ** shininess) * (0.35 + 0.65 * (1 - rough) + self.gloss)
        spec_col = alb * metal[..., None] + (1 - metal[..., None]) * 1.0
        gm = np.sqrt(gx * gx + gy * gy) * SS
        ink = np.clip((gm - 0.06) * 2.2, 0, 1)
        shade *= (1.0 - 0.30 * ink)
        col = alb * shade[..., None] + specv[..., None] * spec_col
        col = col + self.emissive
        # crisp dark outline at silhouette
        m_im = Image.fromarray((self.mask * 255).astype(np.uint8))
        er = np.asarray(m_im.filter(ImageFilter.MinFilter(SS + 1 if (SS + 1) % 2 else SS + 2)), np.float32) / 255
        edge = np.clip(self.mask - er, 0, 1)
        col *= (1.0 - outline * edge)[..., None]
        col = np.clip(col, 0, 1)
        rgba = np.zeros((self.h, self.w, 4), np.uint8)
        rgba[..., :3] = (col * 255).astype(np.uint8)
        rgba[..., 3] = (np.clip(self.mask, 0, 1) * 255).astype(np.uint8)
        big = Image.fromarray(rgba, "RGBA")
        # premultiply-aware downsample: resize RGB*alpha and alpha separately
        arr = np.asarray(big, np.float32) / 255.0
        pm = arr.copy()
        pm[..., :3] *= pm[..., 3:4]
        pm_im = Image.fromarray((pm * 255).astype(np.uint8), "RGBA").resize((self.W, self.H), Image.LANCZOS)
        out = np.asarray(pm_im, np.float32) / 255.0
        a = out[..., 3:4]
        rgb = np.where(a > 1e-4, out[..., :3] / np.maximum(a, 1e-4), 0)
        res = np.concatenate([np.clip(rgb, 0, 1), a], axis=2)
        res_im = Image.fromarray((res * 255).astype(np.uint8), "RGBA")
        # clean near-transparent fringe
        ra = np.asarray(res_im).copy()
        ra[ra[..., 3] < 10] = 0
        return Image.fromarray(ra, "RGBA")

    def alpha_mask_final(self):
        m = Image.fromarray((self.mask * 255).astype(np.uint8)).resize((self.W, self.H), Image.LANCZOS)
        return np.asarray(m) > 127


# ---------------------------------------------------------------- ship-file helpers

def img_to_ship(px, py, W, H, cx, cy_bottom):
    """image pixel (from left, from top) -> ship coords (x fwd, y left)"""
    return [round((H - py) - cy_bottom, 1), round(cx - px, 1)]


def design_to_ship(x, y, W, H, cx, cy_bottom):
    """design (lateral from centre line, +right; y from top) -> ship coords"""
    px = W / 2.0 + x
    return img_to_ship(px, y, W, H, cx, cy_bottom)


def radial_bounds(mask, cx_img, cy_img, n=40):
    """Star-shaped outline: for n angles find farthest opaque pixel. Returns list of (px,py) image coords."""
    H, W = mask.shape
    pts = []
    maxr = math.hypot(W, H)
    for i in range(n):
        a = 2 * math.pi * i / n
        dx, dy = math.sin(a), -math.cos(a)
        best = 0.0
        r = 0.0
        while r < maxr:
            x = int(round(cx_img + dx * r))
            y = int(round(cy_img + dy * r))
            if x < 0 or y < 0 or x >= W or y >= H:
                break
            if mask[y, x]:
                best = r
            r += 0.5
        pts.append((cx_img + dx * (best + 0.5), cy_img + dy * (best + 0.5)))
    # simplify: drop nearly collinear points
    out = []
    for i, p in enumerate(pts):
        a = pts[i - 1]
        b = pts[(i + 1) % len(pts)]
        cross = (p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])
        if abs(cross) > 6.0 or i % 4 == 0:
            out.append(p)
    return out


def max_extent(mask, cx_img, cy_img):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return 10.0
    return float(np.max(np.hypot(xs - cx_img, ys - cy_img)))
