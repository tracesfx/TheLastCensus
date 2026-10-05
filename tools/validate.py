"""
validate.py - static QA for The Last Census.  Run from the mod root:  python tools/validate.py
Exit code 1 if any ERROR is found.  Warnings are printed but do not fail the build.

Checks (see VERIFICATION_REPORT.md for the full list):
  * every mod JSON-family file parses as STRICT JSON; vanilla files are parsed with a Starsector-lenient parser
  * every CSV has the vanilla header and consistent column counts; no duplicate ids; all ids prefixed tlc_
  * no id collides with vanilla ids (hulls, weapons, hullmods, systems, factions, conditions, items, entities, variants)
  * hulls: .ship <-> ship_data.csv, sprite exists, size matches, centre/slots/engines/shield inside sprite and on opaque pixels
  * weapons: .wpn <-> weapon_data.csv, sprites, projectile specs, sounds, offsets, effect classes
  * variants: hull/slot/weapon existence, mount type+size legality, OP budget, vent/cap limits, hullmod legality
  * faction: every referenced hull/weapon/hullmod/fighter/portrait/name source/music/commodity exists, doctrine sums
  * roles, systems, hullmods, conditions, special items, custom entities, styles, settings graphics
  * descriptions exist for every hull/weapon/system/entity/faction and every custom description id used in Java
  * rules.csv: header, command names (vanilla + compiled tlc.rulecmd), option handlers, custom triggers
  * Java: every class named in data exists in the compiled output; TLCIds constants resolve; tlc_ literals are known ids
"""
import csv
import glob
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.normpath(os.path.join(ROOT, "..", ".."))
CORE = os.path.join(GAME, "starsector-core")
VDATA = os.path.join(CORE, "data")
API_JAR = os.path.join(CORE, "starfarer.api.jar")
API_ZIP = os.path.join(CORE, "starfarer.api.zip")
CLASSES = os.path.join(ROOT, "build", "classes")
MOD_JAR = os.path.join(ROOT, "jars", "TheLastCensus.jar")

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


# ------------------------------------------------------------------ lenient JSON (Starsector dialect)
class Lenient:
    def __init__(self, text):
        self.s = text
        self.i = 0
        self.n = len(text)

    def ws(self):
        while self.i < self.n:
            c = self.s[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif c == "#" or (c == "/" and self.s.startswith("//", self.i)):
                while self.i < self.n and self.s[self.i] not in "\r\n":
                    self.i += 1
            else:
                break

    def value(self):
        self.ws()
        c = self.s[self.i]
        if c == "{":
            return self.obj()
        if c == "[":
            return self.arr()
        if c in "\"'":
            return self.string()
        return self.bare()

    def obj(self):
        self.i += 1
        out = {}
        while True:
            self.ws()
            if self.s[self.i] == "}":
                self.i += 1
                return out
            if self.s[self.i] == ",":
                self.i += 1
                continue
            k = self.string() if self.s[self.i] in "\"'" else self.bare(key=True)
            self.ws()
            if self.s[self.i] == ":":
                self.i += 1
            v = self.value()
            out[str(k)] = v

    def arr(self):
        self.i += 1
        out = []
        while True:
            self.ws()
            if self.s[self.i] == "]":
                self.i += 1
                return out
            if self.s[self.i] == ",":
                self.i += 1
                continue
            out.append(self.value())

    def string(self):
        q = self.s[self.i]
        self.i += 1
        buf = []
        while self.s[self.i] != q:
            if self.s[self.i] == "\\":
                self.i += 1
                esc = self.s[self.i]
                buf.append({"n": "\n", "t": "\t", "r": "\r"}.get(esc, esc))
            else:
                buf.append(self.s[self.i])
            self.i += 1
        self.i += 1
        return "".join(buf)

    def bare(self, key=False):
        j = self.i
        stop = " \t\r\n,:]}" if key else " \t\r\n,]}"
        while self.i < self.n and self.s[self.i] not in stop:
            if self.s[self.i] == "#":
                break
            self.i += 1
        tok = self.s[j:self.i].strip()
        if key:
            return tok
        low = tok.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        if low == "null":
            return None
        t = tok[:-1] if tok[-1:] in "fF" and re.match(r"^-?[\d.]+[fF]$", tok) else tok
        try:
            return int(t)
        except ValueError:
            try:
                return float(t)
            except ValueError:
                return tok


def lenient_load(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return Lenient(f.read()).value()


def strict_load(path, rel):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        err("JSON parse failed (strict) %s: %s" % (rel, e))
        return None


def read_csv(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


def csv_dicts(path):
    hdr, rows = read_csv(path)
    out = []
    for r in rows:
        if not r or not any(x.strip() for x in r):
            continue
        out.append({hdr[i]: (r[i] if i < len(r) else "") for i in range(len(hdr))})
    return out


def mod(*p):
    return os.path.join(ROOT, *p)


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def gfx_exists(path):
    """Graphics path may be the mod's or vanilla's."""
    return os.path.exists(mod(path)) or os.path.exists(os.path.join(CORE, path))


# ------------------------------------------------------------------ vanilla registries
def vanilla_ids(csvrel, col="id"):
    return {d[col].strip() for d in csv_dicts(os.path.join(VDATA, csvrel)) if d.get(col, "").strip()}


V = {}
V["hull"] = vanilla_ids("hulls/ship_data.csv")
for sk in glob.glob(os.path.join(VDATA, "hulls", "skins", "*.skin")):
    try:
        V["hull"].add(lenient_load(sk)["skinHullId"])
    except Exception:
        pass
V["weapon"] = vanilla_ids("weapons/weapon_data.csv")
V["wing"] = vanilla_ids("hulls/wing_data.csv")
V["hullmod"] = vanilla_ids("hullmods/hull_mods.csv")
V["system"] = vanilla_ids("shipsystems/ship_systems.csv")
V["commodity"] = vanilla_ids("campaign/commodities.csv")
V["condition"] = vanilla_ids("campaign/market_conditions.csv")
V["industry"] = vanilla_ids("campaign/industries.csv")
V["submarket"] = vanilla_ids("campaign/submarkets.csv")
V["item"] = vanilla_ids("campaign/special_items.csv")
V["faction"] = set()
for d in csv_dicts(os.path.join(VDATA, "world", "factions", "factions.csv")):
    p = os.path.join(CORE, d["faction"].strip())
    if os.path.exists(p):
        try:
            V["faction"].add(lenient_load(p)["id"])
        except Exception:
            pass
V["entity"] = set(lenient_load(os.path.join(VDATA, "config", "custom_entities.json")).keys())
V["engine_style"] = set(lenient_load(os.path.join(VDATA, "config", "engine_styles.json")).keys())
V["hull_style"] = set(lenient_load(os.path.join(VDATA, "config", "hull_styles.json")).keys())
_snd = lenient_load(os.path.join(VDATA, "config", "sounds.json"))
V["sound"] = set()
V["music"] = set()
for k, v in _snd.items():
    if k == "music" and isinstance(v, dict):
        V["music"] |= set(v.keys())
    else:
        V["sound"].add(k)
        if isinstance(v, dict):
            V["sound"] |= set(v.keys())
V["variant"] = {os.path.splitext(os.path.basename(p))[0]
                for p in glob.glob(os.path.join(VDATA, "variants", "**", "*.variant"), recursive=True)}
V["proj"] = set()
for p in glob.glob(os.path.join(VDATA, "weapons", "proj", "*.proj")):
    try:
        V["proj"].add(lenient_load(p)["id"])
    except Exception:
        V["proj"].add(os.path.splitext(os.path.basename(p))[0])
V["role"] = set(lenient_load(os.path.join(VDATA, "world", "factions", "default_ship_roles.json")).keys())
V["shipname_src"] = set(lenient_load(os.path.join(VDATA, "strings", "ship_names.json")).keys())
V["person_name_cat"] = {d["category"].strip() for d in csv_dicts(os.path.join(VDATA, "characters", "person_names.csv"))}
V["desc"] = {(d["id"], d["type"]) for d in csv_dicts(os.path.join(VDATA, "strings", "descriptions.csv"))}
VWPN = {}
for p in glob.glob(os.path.join(VDATA, "weapons", "*.wpn")):
    try:
        w = lenient_load(p)
        VWPN[w["id"]] = w
    except Exception:
        pass
VHMOD = {d["id"]: d for d in csv_dicts(os.path.join(VDATA, "hullmods", "hull_mods.csv"))}
VWEP = {d["id"]: d for d in csv_dicts(os.path.join(VDATA, "weapons", "weapon_data.csv"))}

# vanilla rule commands + API classes
API_CLASSES = set()
with zipfile.ZipFile(API_JAR) as z:
    for n in z.namelist():
        if n.endswith(".class"):
            API_CLASSES.add(n[:-6].replace("/", "."))
RULE_CMDS = set()
for c in API_CLASSES:
    if c.startswith("com.fs.starfarer.api.impl.campaign.rulecmd.") and "$" not in c:
        RULE_CMDS.add(c.rsplit(".", 1)[1])

# compiled mod classes
MOD_CLASSES = set()
if os.path.isdir(CLASSES):
    for p in glob.glob(os.path.join(CLASSES, "**", "*.class"), recursive=True):
        MOD_CLASSES.add(os.path.relpath(p, CLASSES)[:-6].replace("\\", ".").replace("/", "."))
elif os.path.exists(MOD_JAR):
    with zipfile.ZipFile(MOD_JAR) as z:
        for n in z.namelist():
            if n.endswith(".class"):
                MOD_CLASSES.add(n[:-6].replace("/", "."))
if not MOD_CLASSES:
    err("no compiled classes found (run ./build.sh)")
for c in MOD_CLASSES:
    if c.startswith("tlc.rulecmd.") and "$" not in c:
        RULE_CMDS.add(c.rsplit(".", 1)[1])


def class_exists(fqcn, where):
    if not fqcn:
        return
    if fqcn in MOD_CLASSES or fqcn in API_CLASSES:
        return
    err("%s: class not found: %s" % (where, fqcn))


# ------------------------------------------------------------------ 1. parse everything
JSON_EXT = (".json", ".ship", ".variant", ".wpn", ".proj", ".system", ".faction", ".skin")
mod_json = {}
for p in glob.glob(mod("**", "*"), recursive=True):
    r = rel(p)
    if r.startswith(("build/", ".git/", "tools/", "src/")) or not os.path.isfile(p):
        continue
    if p.endswith(JSON_EXT):
        d = strict_load(p, r)
        if d is not None:
            mod_json[r] = d

KNOWN_HEADERS = {
    "data/hulls/ship_data.csv": "hulls/ship_data.csv",
    "data/weapons/weapon_data.csv": "weapons/weapon_data.csv",
    "data/hullmods/hull_mods.csv": "hullmods/hull_mods.csv",
    "data/shipsystems/ship_systems.csv": "shipsystems/ship_systems.csv",
    "data/strings/descriptions.csv": "strings/descriptions.csv",
    "data/campaign/rules.csv": "campaign/rules.csv",
    "data/campaign/market_conditions.csv": "campaign/market_conditions.csv",
    "data/campaign/special_items.csv": "campaign/special_items.csv",
    "data/world/factions/factions.csv": "world/factions/factions.csv",
}
for p in glob.glob(mod("data", "**", "*.csv"), recursive=True):
    r = rel(p)
    hdr, rows = read_csv(p)
    if r in KNOWN_HEADERS:
        vh, _ = read_csv(os.path.join(VDATA, KNOWN_HEADERS[r]))
        if hdr != vh:
            err("%s: header differs from vanilla %s" % (r, KNOWN_HEADERS[r]))
    for i, row in enumerate(rows, start=2):
        if row and len(row) != len(hdr):
            err("%s line %d: %d columns, header has %d" % (r, i, len(row), len(hdr)))

# ------------------------------------------------------------------ 2. mod registries
M = {k: set() for k in V}


def collect(csvrel, key, col="id"):
    p = mod(*csvrel.split("/"))
    if not os.path.exists(p):
        return []
    ds = csv_dicts(p)
    seen = set()
    for d in ds:
        i = d.get(col, "").strip()
        if not i:
            continue
        if i in seen:
            err("%s: duplicate id %s" % (csvrel, i))
        seen.add(i)
        M[key].add(i)
    return ds


SHIPS = collect("data/hulls/ship_data.csv", "hull")
WEPS = collect("data/weapons/weapon_data.csv", "weapon")
HMODS = collect("data/hullmods/hull_mods.csv", "hullmod")
SYSS = collect("data/shipsystems/ship_systems.csv", "system")
CONDS = collect("data/campaign/market_conditions.csv", "condition")
ITEMS = collect("data/campaign/special_items.csv", "item")
DESCS = csv_dicts(mod("data", "strings", "descriptions.csv")) if os.path.exists(mod("data", "strings", "descriptions.csv")) else []
M["desc"] = {(d["id"], d["type"]) for d in DESCS}
seen_desc = set()
for d in DESCS:
    k = (d["id"], d["type"])
    if k in seen_desc:
        err("descriptions.csv duplicate (%s,%s)" % k)
    seen_desc.add(k)
for r, d in mod_json.items():
    if r.endswith(".variant"):
        M["variant"].add(d.get("variantId"))
        if d.get("variantId") != os.path.splitext(os.path.basename(r))[0]:
            err("%s: variantId does not match file name" % r)
    if r.endswith(".proj"):
        M["proj"].add(d.get("id"))
    if r.endswith(".faction"):
        M["faction"].add(d.get("id"))
ENT = mod_json.get("data/config/custom_entities.json", {})
M["entity"] = set(ENT.keys())
M["engine_style"] = set(mod_json.get("data/config/engine_styles.json", {}).keys())
M["hull_style"] = set(mod_json.get("data/config/hull_styles.json", {}).keys())
M["shipname_src"] = set(mod_json.get("data/strings/ship_names.json", {}).keys())

for key, ids in M.items():
    if key in ("desc", "role", "sound", "music", "person_name_cat", "shipname_src", "engine_style", "hull_style"):
        continue
    for i in ids:
        if i is None:
            continue
        if not str(i).startswith("tlc_"):
            err("id without tlc_ prefix (%s): %s" % (key, i))
        if i in V.get(key, set()):
            err("id collides with vanilla %s: %s" % (key, i))
for key in ("engine_style", "hull_style", "shipname_src"):
    for i in M[key]:
        if not i.startswith("TLC_"):
            err("%s id without TLC_ prefix: %s" % (key, i))
        if i in V[key]:
            err("%s collides with vanilla: %s" % (key, i))

ALL = {k: (V.get(k, set()) | M.get(k, set())) for k in set(V) | set(M)}

# ------------------------------------------------------------------ 3. hulls
try:
    from PIL import Image
except ImportError:
    Image = None
    warn("Pillow not installed; sprite checks skipped")

HULLSPEC = {}
for s in SHIPS:
    hid = s["id"]
    p = mod("data", "hulls", hid + ".ship")
    if not os.path.exists(p):
        err("hull %s: missing data/hulls/%s.ship" % (hid, hid))
        continue
    sh = mod_json.get(rel(p))
    if not sh:
        continue
    HULLSPEC[hid] = (s, sh)
    if sh.get("hullId") != hid:
        err("%s.ship hullId mismatch" % hid)
    if s["system id"] and s["system id"] not in ALL["system"]:
        err("hull %s: unknown system %s" % (hid, s["system id"]))
    for m in sh.get("builtInMods", []):
        if m not in ALL["hullmod"]:
            err("hull %s: unknown built-in hullmod %s" % (hid, m))
    if sh.get("style") not in ALL["hull_style"]:
        err("hull %s: unknown hull style %s" % (hid, sh.get("style")))
    if (hid, "SHIP") not in ALL["desc"]:
        err("hull %s: no SHIP description" % hid)
    if s["codex variant id"] and s["codex variant id"] not in ALL["variant"]:
        err("hull %s: codex variant %s missing" % (hid, s["codex variant id"]))
    sp = sh.get("spriteName", "")
    if not gfx_exists(sp):
        err("hull %s: sprite missing %s" % (hid, sp))
        continue
    if Image is None:
        continue
    im = Image.open(mod(sp) if os.path.exists(mod(sp)) else os.path.join(CORE, sp)).convert("RGBA")
    W, H = im.size
    if (W, H) != (sh["width"], sh["height"]):
        err("hull %s: sprite %dx%d but .ship says %sx%s" % (hid, W, H, sh["width"], sh["height"]))
    alpha = im.split()[3].load()
    cx, cy = sh["center"]
    if not (0 <= cx <= W and 0 <= cy <= H):
        err("hull %s: center outside sprite" % hid)

    def to_img(x, y):
        return cx - y, H - (x + cy)

    def opaque(px, py, r=1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                qx, qy = int(round(px)) + dx, int(round(py)) + dy
                if 0 <= qx < W and 0 <= qy < H and alpha[qx, qy] > 40:
                    return True
        return False

    ids = set()
    for ws in sh.get("weaponSlots", []):
        if ws["id"] in ids:
            err("hull %s: duplicate slot id %s" % (hid, ws["id"]))
        ids.add(ws["id"])
        px, py = to_img(*ws["locations"])
        if not (0 <= px < W and 0 <= py < H):
            err("hull %s slot %s: location outside sprite (%.1f,%.1f)" % (hid, ws["id"], px, py))
        elif not opaque(px, py):
            err("hull %s slot %s: location over transparent pixels" % (hid, ws["id"]))
        if ws["mount"] not in ("TURRET", "HARDPOINT", "HIDDEN"):
            err("hull %s slot %s: bad mount %s" % (hid, ws["id"], ws["mount"]))
        if ws["size"] not in ("SMALL", "MEDIUM", "LARGE"):
            err("hull %s slot %s: bad size" % (hid, ws["id"]))
        if ws["type"] not in ("BALLISTIC", "ENERGY", "MISSILE", "HYBRID", "SYNERGY", "COMPOSITE", "UNIVERSAL",
                              "BUILT_IN", "DECORATIVE", "SYSTEM", "LAUNCH_BAY", "STATION_MODULE"):
            err("hull %s slot %s: bad type" % (hid, ws["id"]))
        if not (0 < ws.get("arc", 0) <= 360):
            err("hull %s slot %s: arc out of range" % (hid, ws["id"]))
    for i, es in enumerate(sh.get("engineSlots", [])):
        px, py = to_img(*es["location"])
        if not (0 <= px < W and -2 <= py < H + 2):
            err("hull %s engine %d outside sprite" % (hid, i))
        elif not opaque(px, py - 2, r=2):
            warn("hull %s engine %d not adjacent to hull pixels" % (hid, i))
        if es.get("style") not in ALL["engine_style"] and es.get("style") != "CUSTOM":
            err("hull %s engine %d: unknown style %s" % (hid, i, es.get("style")))
    sx, sy = sh.get("shieldCenter", [0, 0])
    px, py = to_img(sx, sy)
    if not (0 <= px < W and 0 <= py < H):
        err("hull %s: shield center outside sprite" % hid)
    b = sh.get("bounds", [])
    if len(b) < 6 or len(b) % 2:
        err("hull %s: bounds malformed" % hid)
    for k in range(0, len(b) - 1, 2):
        px, py = to_img(b[k], b[k + 1])
        if not (-3 <= px <= W + 3 and -3 <= py <= H + 3):
            err("hull %s: bounds point outside sprite" % hid)
    ext = max(((b[k] ** 2 + b[k + 1] ** 2) ** 0.5 for k in range(0, len(b) - 1, 2)), default=0)
    if sh.get("collisionRadius", 0) < ext:
        err("hull %s: collisionRadius %.1f smaller than bounds extent %.1f" % (hid, sh["collisionRadius"], ext))
    # sanity vs size
    size = sh.get("hullSize")
    lim = {"FRIGATE": 140, "DESTROYER": 220, "CRUISER": 320, "CAPITAL_SHIP": 460}.get(size)
    if lim and max(W, H) > lim:
        warn("hull %s: sprite unusually large for %s" % (hid, size))
    for c in ("supplies/rec", "fleet pts", "ordnance points", "hitpoints", "max flux", "flux dissipation"):
        try:
            if float(s[c]) <= 0:
                err("hull %s: %s must be positive" % (hid, c))
        except ValueError:
            err("hull %s: %s not numeric" % (hid, c))

# ------------------------------------------------------------------ 4. weapons
WSPEC = dict(VWPN)
WDATA = dict(VWEP)
for w in WEPS:
    wid = w["id"]
    WDATA[wid] = w
    p = mod("data", "weapons", wid + ".wpn")
    if not os.path.exists(p):
        err("weapon %s: missing .wpn" % wid)
        continue
    spec = mod_json.get(rel(p))
    if not spec:
        continue
    WSPEC[wid] = spec
    if spec.get("id") != wid:
        err("%s.wpn id mismatch" % wid)
    if (wid, "WEAPON") not in ALL["desc"]:
        err("weapon %s: no WEAPON description" % wid)
    for k in ("turretSprite", "hardpointSprite", "turretGlowSprite", "hardpointGlowSprite", "turretGunSprite",
              "hardpointGunSprite"):
        if k in spec and not gfx_exists(spec[k]):
            err("weapon %s: %s missing %s" % (wid, k, spec[k]))
    for k in ("fireSoundOne", "fireSoundTwo"):
        if k in spec and spec[k] not in ALL["sound"]:
            err("weapon %s: unknown sound %s" % (wid, spec[k]))
    for k in ("beamEffect", "onFireEffect", "everyFrameEffect"):
        if k in spec:
            class_exists(spec[k], "weapon %s %s" % (wid, k))
    if spec.get("specClass") == "projectile":
        if spec.get("projectileSpecId") not in ALL["proj"]:
            err("weapon %s: unknown projectile %s" % (wid, spec.get("projectileSpecId")))
    for mount in ("turret", "hardpoint"):
        offs = spec.get(mount + "Offsets", [])
        angs = spec.get(mount + "AngleOffsets", [])
        if len(offs) != 2 * len(angs):
            err("weapon %s: %sOffsets/AngleOffsets length mismatch" % (wid, mount))
        sk = spec.get(mount + "Sprite")
        if Image and sk and gfx_exists(sk):
            im = Image.open(mod(sk) if os.path.exists(mod(sk)) else os.path.join(CORE, sk))
            hh = im.size[1]
            for k in range(0, len(offs), 2):
                if offs[k] > hh / 2 + 12:
                    warn("weapon %s: %s muzzle offset %.1f far beyond sprite edge (h=%d)" % (wid, mount, offs[k], hh))
    if spec.get("type") != w.get("type") and spec.get("type") in ("BALLISTIC", "ENERGY", "MISSILE"):
        pass  # csv 'type' is damage type, not mount type
    try:
        float(w["OPs"])
    except ValueError:
        err("weapon %s: OPs not numeric" % wid)
for r, d in mod_json.items():
    if r.endswith(".proj"):
        if "onHitEffect" in d:
            class_exists(d["onHitEffect"], r)
        for k in ("sprite", "bulletSprite"):
            if k in d and not gfx_exists(d[k]):
                err("%s: %s missing %s" % (r, k, d[k]))

# ------------------------------------------------------------------ 5. variants
SIZE_N = {"SMALL": 0, "MEDIUM": 1, "LARGE": 2}
COMPAT = {"BALLISTIC": {"BALLISTIC"}, "ENERGY": {"ENERGY"}, "MISSILE": {"MISSILE"},
          "HYBRID": {"BALLISTIC", "ENERGY"}, "SYNERGY": {"ENERGY", "MISSILE"},
          "COMPOSITE": {"BALLISTIC", "MISSILE"}, "UNIVERSAL": {"BALLISTIC", "ENERGY", "MISSILE"}}
MAXVC = {"FRIGATE": 10, "DESTROYER": 20, "CRUISER": 30, "CAPITAL_SHIP": 50}
HCOST = {"FRIGATE": "cost_frigate", "DESTROYER": "cost_dest", "CRUISER": "cost_cruiser",
         "CAPITAL_SHIP": "cost_capital"}
ALLHMOD = dict(VHMOD)
for h in HMODS:
    ALLHMOD[h["id"]] = h
for r, v in mod_json.items():
    if not r.endswith(".variant"):
        continue
    vid = v.get("variantId")
    hid = v.get("hullId")
    if hid not in HULLSPEC:
        err("variant %s: hull %s not a mod hull (or missing)" % (vid, hid))
        continue
    s, sh = HULLSPEC[hid]
    size = sh["hullSize"]
    slots = {ws["id"]: ws for ws in sh["weaponSlots"]}
    builtins = set(sh.get("builtInMods", []))
    op = 0.0
    used = set()
    for g in v.get("weaponGroups", []):
        if g.get("mode") not in ("LINKED", "ALTERNATING"):
            err("variant %s: bad group mode %s" % (vid, g.get("mode")))
        for sid, wid in g.get("weapons", {}).items():
            if sid in used:
                err("variant %s: slot %s used twice" % (vid, sid))
            used.add(sid)
            if sid not in slots:
                err("variant %s: no slot %s on %s" % (vid, sid, hid))
                continue
            if wid not in WDATA or wid not in WSPEC:
                err("variant %s: unknown weapon %s" % (vid, wid))
                continue
            sl = slots[sid]
            ws = WSPEC[wid]
            wtype, wsize = ws.get("type"), ws.get("size")
            if wtype not in COMPAT.get(sl["type"], set()):
                err("variant %s: %s (%s) cannot mount in %s slot %s" % (vid, wid, wtype, sl["type"], sid))
            d = SIZE_N[sl["size"]] - SIZE_N.get(wsize, 9)
            if d not in (0, 1):
                err("variant %s: %s size %s illegal in %s slot %s" % (vid, wid, wsize, sl["size"], sid))
            try:
                op += float(WDATA[wid]["OPs"])
            except ValueError:
                pass
    for m in v.get("hullMods", []):
        if m not in ALLHMOD:
            err("variant %s: unknown hullmod %s" % (vid, m))
            continue
        if m in builtins:
            continue
        if ALLHMOD[m].get("hidden", "").upper() == "TRUE":
            err("variant %s: hidden hullmod %s" % (vid, m))
        try:
            op += float(ALLHMOD[m][HCOST[size]])
        except ValueError:
            pass
    vc = v.get("fluxVents", 0) + v.get("fluxCapacitors", 0)
    if v.get("fluxVents", 0) > MAXVC[size] or v.get("fluxCapacitors", 0) > MAXVC[size]:
        err("variant %s: vents/caps exceed %d" % (vid, MAXVC[size]))
    op += vc
    hop = float(s["ordnance points"])
    if op > hop + 1e-6:
        err("variant %s: OP %.0f exceeds hull OP %.0f" % (vid, op, hop))
    elif op < hop - 10:
        warn("variant %s: %.0f of %.0f OP unused" % (vid, hop - op, hop))
    print("  variant %-30s OP %3.0f / %3.0f" % (vid, op, hop))

# ------------------------------------------------------------------ 6. faction / roles / names
for r, f in mod_json.items():
    if not r.endswith(".faction"):
        continue
    for k in ("logo", "crest"):
        if not gfx_exists(f.get(k, "")):
            err("%s: %s missing" % (r, k))
    for h in f.get("knownShips", {}).get("hulls", []) + f.get("priorityShips", {}).get("hulls", []):
        if h not in ALL["hull"]:
            err("%s: unknown hull %s" % (r, h))
    for w in f.get("knownWeapons", {}).get("weapons", []) + f.get("priorityWeapons", {}).get("weapons", []):
        if w not in ALL["weapon"]:
            err("%s: unknown weapon %s" % (r, w))
    for w in list(f.get("weaponSellFrequency", {}).keys()):
        if w not in ALL["weapon"]:
            err("%s: weaponSellFrequency unknown weapon %s" % (r, w))
    for w in f.get("knownFighters", {}).get("fighters", []):
        if w not in ALL["wing"]:
            err("%s: unknown wing %s" % (r, w))
    for m in f.get("knownHullMods", {}).get("hullMods", []):
        if m not in ALL["hullmod"]:
            err("%s: unknown hullmod %s" % (r, m))
    for k in f.get("shipNameSources", {}):
        if k not in ALL["shipname_src"]:
            err("%s: unknown ship name source %s" % (r, k))
    for k in f.get("names", {}):
        if k not in V["person_name_cat"]:
            err("%s: unknown person name category %s" % (r, k))
    for lst in f.get("portraits", {}).values():
        for p in lst:
            if not gfx_exists(p):
                err("%s: portrait missing %s" % (r, p))
    for k, m in f.get("music", {}).items():
        if m not in V["music"]:
            err("%s: unknown music %s" % (r, m))
    for c in f.get("illegalCommodities", []):
        if c not in ALL["commodity"]:
            err("%s: unknown commodity %s" % (r, c))
    doc = f.get("factionDoctrine", {})
    if doc.get("warships", 0) + doc.get("carriers", 0) + doc.get("phaseShips", 0) != 7:
        err("%s: doctrine fleet composition must sum to 7" % r)
    if doc.get("officerQuality", 0) + doc.get("shipQuality", 0) + doc.get("numShips", 0) != 7:
        err("%s: doctrine quality points must sum to 7" % r)
    known_tags = set(f.get("knownShips", {}).get("tags", []))
    tagged = [s["id"] for s in SHIPS if known_tags & {t.strip() for t in s["tags"].split(",")}]
    if not tagged:
        err("%s: knows no mod hulls" % r)
    if (f["id"], "FACTION") not in ALL["desc"]:
        err("%s: no FACTION description" % r)
    # every weapon/hullmod on the faction's own role variants must be known to the faction
    kw_tags = set(f.get("knownWeapons", {}).get("tags", []))
    kw = set(f.get("knownWeapons", {}).get("weapons", []))
    for wid, wd in WDATA.items():
        if kw_tags & {t.strip() for t in wd.get("tags", "").split(",")}:
            kw.add(wid)
    km_tags = set(f.get("knownHullMods", {}).get("tags", []))
    km = set(f.get("knownHullMods", {}).get("hullMods", []))
    for mid, md in ALLHMOD.items():
        if km_tags & {t.strip() for t in md.get("tags", "").split(",")}:
            km.add(mid)
    role_variants = set()
    for vs in mod_json.get("data/world/factions/default_ship_roles.json", {}).values():
        role_variants |= set(vs.keys())
    for r2, v in mod_json.items():
        if not r2.endswith(".variant") or v.get("variantId") not in role_variants:
            continue
        builtins = set(HULLSPEC.get(v["hullId"], ({}, {}))[1].get("builtInMods", []))
        for g in v.get("weaponGroups", []):
            for wid in g.get("weapons", {}).values():
                if wid not in kw:
                    err("%s: role variant %s uses weapon %s the faction does not know" % (r, v["variantId"], wid))
        for m in v.get("hullMods", []):
            if m not in km and m not in builtins:
                err("%s: role variant %s uses hullmod %s the faction does not know" % (r, v["variantId"], m))
fl = mod("data", "world", "factions", "factions.csv")
if os.path.exists(fl):
    for d in csv_dicts(fl):
        if not os.path.exists(mod(d["faction"])):
            err("factions.csv: missing %s" % d["faction"])
roles = mod_json.get("data/world/factions/default_ship_roles.json", {})
for role, vs in roles.items():
    if role not in V["role"]:
        err("default_ship_roles: unknown role %s" % role)
    for vid in vs:
        if vid not in ALL["variant"]:
            err("default_ship_roles: unknown variant %s" % vid)

# ------------------------------------------------------------------ 7. systems, hullmods, conditions, items
for s in SYSS:
    sid = s["id"]
    p = mod("data", "shipsystems", sid + ".system")
    sp = mod_json.get(rel(p))
    if not sp:
        err("system %s: missing/invalid .system" % sid)
        continue
    if sp.get("id") != sid:
        err("%s.system id mismatch" % sid)
    class_exists(sp.get("statsScript"), "system %s statsScript" % sid)
    if sp.get("aiType") == "CUSTOM":
        class_exists(sp.get("aiScript"), "system %s aiScript" % sid)
        if not sp.get("aiScript"):
            err("system %s: CUSTOM aiType without aiScript" % sid)
    for k in ("useSound", "loopSound", "deactivateSound", "outOfUsesSound"):
        if k in sp and sp[k] not in ALL["sound"]:
            err("system %s: unknown sound %s" % (sid, sp[k]))
    if not gfx_exists(s["icon"]):
        err("system %s: icon missing" % sid)
    if (sid, "SHIP_SYSTEM") not in ALL["desc"]:
        err("system %s: no SHIP_SYSTEM description" % sid)
for h in HMODS:
    class_exists(h["script"], "hullmod %s" % h["id"])
    if not gfx_exists(h["sprite"]):
        err("hullmod %s: sprite missing" % h["id"])
    n_params = h["desc"].count("%s")
    if n_params == 0:
        warn("hullmod %s: description has no %%s parameters" % h["id"])
for c in CONDS:
    class_exists(c["script"], "condition %s" % c["id"])
    if not gfx_exists(c["icon"]):
        err("condition %s: icon missing" % c["id"])
for it in ITEMS:
    class_exists(it["plugin"], "item %s" % it["id"])
    if not gfx_exists(it["icon"]):
        err("item %s: icon missing" % it["id"])
    for k in ("sound id", "sound id drop"):
        if it[k] and it[k] not in ALL["sound"]:
            err("item %s: unknown sound %s" % (it["id"], it[k]))
    if "package_bp" in it["tags"]:
        tag = it["plugin params"].strip()
        n = [s["id"] for s in SHIPS if tag in [t.strip() for t in s["tags"].split(",")]]
        n += [w["id"] for w in WEPS if tag in [t.strip() for t in w["tags"].split(",")]]
        if not n:
            err("item %s: blueprint tag %s matches nothing" % (it["id"], tag))

# ------------------------------------------------------------------ 8. entities, styles, settings
for eid, e in ENT.items():
    for k in ("sprite", "icon", "interactionImage"):
        if k in e and not gfx_exists(e[k]):
            err("custom entity %s: %s missing %s" % (eid, k, e[k]))
    if e.get("customDescriptionId") and (e["customDescriptionId"], "CUSTOM") not in ALL["desc"]:
        err("custom entity %s: description %s missing" % (eid, e["customDescriptionId"]))
for sid, st in mod_json.get("data/config/hull_styles.json", {}).items():
    for k, v in st.items():
        if isinstance(v, str) and v.startswith("graphics/") and not gfx_exists(v):
            err("hull style %s: %s missing %s" % (sid, k, v))
        if k.endswith("Set") and isinstance(v, str) and v not in V["sound"]:
            err("hull style %s: unknown sound set %s" % (sid, v))
settings = mod_json.get("data/config/settings.json", {})
for cat, entries in settings.get("graphics", {}).items():
    for k, p in entries.items():
        if not gfx_exists(p):
            err("settings.json graphics %s.%s missing %s" % (cat, k, p))
for k, cls in settings.get("plugins", {}).items():
    class_exists(cls, "settings.json plugin %s" % k)
for pkg in settings.get("ruleCommandPackages", []):
    if not any(c.startswith(pkg + ".") for c in MOD_CLASSES):
        err("settings.json: ruleCommandPackage %s has no compiled classes" % pkg)
luna = mod("data", "config", "LunaSettings.csv")
LUNA_IDS = set()
if os.path.exists(luna):
    for d in csv_dicts(luna):
        LUNA_IDS.add(d["fieldID"])
        if d["fieldType"] not in ("Header", "Boolean", "Int", "Double", "String", "Text", "Color", "Keycode", "Radio"):
            err("LunaSettings: bad type %s" % d["fieldType"])
mi = mod_json.get("mod_info.json", {})
if mi.get("modPlugin"):
    class_exists(mi["modPlugin"], "mod_info modPlugin")
for j in mi.get("jars", []):
    if not os.path.exists(mod(j)):
        err("mod_info: jar missing %s" % j)
for dep in mi.get("dependencies", []):
    if not os.path.isdir(os.path.join(GAME, "mods")):
        break
    found = False
    for p in glob.glob(os.path.join(GAME, "mods", "*", "mod_info.json")):
        try:
            if lenient_load(p).get("id") == dep["id"]:
                found = True
        except Exception:
            pass
    if not found:
        err("mod_info: dependency %s not installed" % dep["id"])

# ------------------------------------------------------------------ 9. rules.csv
RULES = mod("data", "campaign", "rules.csv")
BUILTIN_OPTIONS = {"cutCommLink", "cutCommLinkNoText", "defaultLeave", "marketLeave", "cutCommLinkPolite",
                   "continueCutComm", "fleetEncounterLeave"}
if os.path.exists(RULES):
    rows = csv_dicts(RULES)
    opt_handlers = set()
    triggers = {}
    introduced = {}
    fired = []
    rule_ids = set()
    for d in rows:
        rid = d["id"].strip()
        if not rid or rid.startswith("#"):
            continue
        if rid in rule_ids:
            err("rules.csv duplicate id %s" % rid)
        rule_ids.add(rid)
        if not rid.startswith("tlc_"):
            err("rules.csv id without tlc_ prefix: %s" % rid)
        trig = d["trigger"].strip()
        if not trig:
            err("rules.csv %s: empty trigger" % rid)
        triggers.setdefault(trig, []).append(rid)
        for line in d["conditions"].splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^\$option\s*==\s*(\S+)", line)
            if m and trig == "DialogOptionSelected":
                opt_handlers.add(m.group(1))
            first = line.split()[0]
            if first.startswith("$") or first.startswith("!$") or first.startswith("!"):
                continue
            if first not in RULE_CMDS:
                err("rules.csv %s: unknown condition command %s" % (rid, first))
        for line in d["script"].splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            first = line.split()[0]
            if first.startswith("$"):
                continue
            if first not in RULE_CMDS:
                err("rules.csv %s: unknown script command %s" % (rid, first))
            if first in ("FireAll", "FireBest") and len(line.split()) > 1:
                fired.append((rid, line.split()[1]))
        for line in d["options"].splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) >= 3 and re.match(r"^-?\d+(\.\d+)?$", parts[0].strip()):
                oid = parts[1].strip()
            else:
                oid = parts[0].strip()
            introduced.setdefault(oid, rid)
    for oid, rid in introduced.items():
        if oid in BUILTIN_OPTIONS:
            continue
        if oid not in opt_handlers:
            err("rules.csv %s: option %s has no DialogOptionSelected handler" % (rid, oid))
    for rid, t in fired:
        if t.startswith("TLC") and t not in triggers:
            err("rules.csv %s: fires trigger %s but no rule handles it" % (rid, t))
    # Java may add options with ids handled in rules: collect ids from Java sources too
    JAVA_OPTION_IDS = set()
    for p in glob.glob(mod("src", "**", "*.java"), recursive=True):
        with open(p, encoding="utf-8") as f:
            for m in re.finditer(r'addOption\(\s*[^,]+,\s*"([A-Za-z0-9_]+)"', f.read()):
                JAVA_OPTION_IDS.add(m.group(1))
    for oid in JAVA_OPTION_IDS:
        if oid not in opt_handlers:
            err("Java adds dialog option %s but rules.csv has no handler" % oid)
else:
    warn("no rules.csv")

# ------------------------------------------------------------------ 10. Java id constants and literals
IDS_FILE = mod("src", "tlc", "TLCIds.java")
KNOWN_LITERALS = set()
for k in ("hull", "weapon", "hullmod", "system", "condition", "item", "faction", "entity", "variant", "proj"):
    KNOWN_LITERALS |= {i for i in M.get(k, set()) if i}
KNOWN_LITERALS |= {d[0] for d in M["desc"]}
KNOWN_LITERALS |= LUNA_IDS
if os.path.exists(IDS_FILE):
    with open(IDS_FILE, encoding="utf-8") as f:
        src = f.read()
    PREFIX_REG = [("HULL_", "hull"), ("VARIANT_", "variant"), ("WEAPON_", "weapon"), ("HULLMOD_", "hullmod"),
                  ("SYSTEM_", "system"), ("CONDITION_", "condition"), ("ITEM_", "item"), ("FACTION_", "faction"),
                  ("ENTITY_", "entity"), ("DESC_", "desc"), ("PORTRAIT_", "gfx"), ("LUNA_", "luna"),
                  ("INDUSTRY_", "industry"), ("SUBMARKET_", "submarket"), ("COMMODITY_", "commodity")]
    for name, val in re.findall(r'public static final String (\w+)\s*=\s*"([^"]*)"', src):
        for pre, reg in PREFIX_REG:
            if name.startswith(pre):
                if reg == "desc":
                    ok = any(val == d[0] for d in ALL["desc"])
                elif reg == "gfx":
                    ok = gfx_exists(val)
                elif reg == "luna":
                    ok = val in LUNA_IDS
                else:
                    ok = val in ALL.get(reg, set())
                if not ok:
                    err("TLCIds.%s = \"%s\" does not resolve to a known %s" % (name, val, reg))
                break
        KNOWN_LITERALS.add(val)
else:
    warn("src/tlc/TLCIds.java not found")
# Non-registry identifiers used in Java: entity/planet instance ids created by TLCWorldGen, stat-modifier ids,
# memory-flag reasons and custom-data keys. These are not looked up in any data registry, so they cannot be typos
# of one; everything that IS a registry id goes through TLCIds and is validated above.
LITERAL_WHITELIST = {"tlc_audit", "tlc_inspector", "tlc_assessor", "tlc_census", "tlc_hearing", "tlc_relay",
                     "tlc_ledger_plugin", "tlc_surcharge_debuff", "tlc_injunction_debuff", "tlc_judgment_debuff",
                     "tlc_assize_star", "tlc_abeyance", "tlc_assize_relay", "tlc_assize_buoy",
                     "tlc_escrow", "tlc_gen", "tlc_envoi_star", "tlc_envoi_rock"}
for p in glob.glob(mod("src", "**", "*.java"), recursive=True):
    with open(p, encoding="utf-8") as f:
        src = f.read()
    for lit in re.findall(r'"(tlc_[A-Za-z0-9_]+)"', src):
        if lit not in KNOWN_LITERALS and lit not in LITERAL_WHITELIST:
            warn("%s: string literal \"%s\" is not a known id (typo?)" % (rel(p), lit))
    for m in re.finditer(r'setCustomDescriptionId\(\s*"([^"]+)"\s*\)', src):
        if (m.group(1), "CUSTOM") not in ALL["desc"]:
            err("%s: custom description id %s missing" % (rel(p), m.group(1)))
    for m in re.finditer(r'addCustomEntity\([^,]+,[^,]+,\s*"([^"]+)"', src):
        if m.group(1) not in ALL["entity"]:
            err("%s: unknown custom entity type %s" % (rel(p), m.group(1)))
    for m in re.finditer(r'(?:addCondition|hasCondition)\(\s*"([^"]+)"', src):
        if m.group(1) not in ALL["condition"]:
            err("%s: unknown market condition %s" % (rel(p), m.group(1)))
    for m in re.finditer(r'addIndustry\(\s*"([^"]+)"', src):
        if m.group(1) not in ALL["industry"]:
            err("%s: unknown industry %s" % (rel(p), m.group(1)))
    for m in re.finditer(r'addSubmarket\(\s*"([^"]+)"', src):
        if m.group(1) not in ALL["submarket"]:
            err("%s: unknown submarket %s" % (rel(p), m.group(1)))

# ------------------------------------------------------------------ 10b. GraphicsLib light data (optional)
LIGHTS = mod("data", "lights", "tlc_light_data.csv")
GLIB_CORE = os.path.join(GAME, "mods", "GraphicsLib", "data", "lights", "core_light_data.csv")
if os.path.exists(LIGHTS):
    hdr, _ = read_csv(LIGHTS)
    if os.path.exists(GLIB_CORE):
        ghdr, _ = read_csv(GLIB_CORE)
        if hdr != ghdr:
            err("tlc_light_data.csv header differs from GraphicsLib core_light_data.csv")
    for d in csv_dicts(LIGHTS):
        if d["type"] == "projectile" and d["id"] not in ALL["proj"]:
            err("light data: unknown projectile %s" % d["id"])
        if d["type"] == "beam" and (d["id"] not in WSPEC or WSPEC[d["id"]].get("specClass") != "beam"):
            err("light data: %s is not a beam weapon" % d["id"])
        if d["type"] not in ("projectile", "beam"):
            err("light data: bad type %s" % d["type"])
    with open(mod("src", "tlc", "TLCModPlugin.java"), encoding="utf-8") as f:
        if "isModEnabled(\"shaderLib\")" not in f.read():
            err("GraphicsLib compat must be guarded by isModEnabled(\"shaderLib\")")

# ------------------------------------------------------------------ 11. orphan graphics
referenced = set()
for r, d in mod_json.items():
    for m in re.finditer(r'graphics/[A-Za-z0-9_/.-]+\.(?:png|jpg)', json.dumps(d)):
        referenced.add(m.group(0))
for p in glob.glob(mod("data", "**", "*.csv"), recursive=True):
    with open(p, encoding="utf-8") as f:
        for m in re.finditer(r'graphics/[A-Za-z0-9_/.-]+\.(?:png|jpg)', f.read()):
            referenced.add(m.group(0))
for p in glob.glob(mod("src", "**", "*.java"), recursive=True):
    with open(p, encoding="utf-8") as f:
        for m in re.finditer(r'graphics/[A-Za-z0-9_/.-]+\.(?:png|jpg)', f.read()):
            ref = m.group(0)
            referenced.add(ref)
            if not gfx_exists(ref):
                err("%s: graphics path missing %s" % (rel(p), ref))
for p in glob.glob(mod("graphics", "**", "*.*"), recursive=True):
    r = rel(p)
    if r not in referenced:
        warn("unreferenced asset %s" % r)

# ------------------------------------------------------------------ report
print()
for w in warnings:
    print("WARN  ", w)
for e in errors:
    print("ERROR ", e)
print("\nvalidate.py: %d error(s), %d warning(s)" % (len(errors), len(warnings)))
sys.exit(1 if errors else 0)
