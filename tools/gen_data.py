"""
gen_data.py - single source of truth for The Last Census data files.

Writes (strict JSON / properly quoted CSV, headers copied from the vanilla files so columns always match):
  data/hulls/ship_data.csv, data/weapons/weapon_data.csv, data/weapons/*.wpn, data/weapons/proj/*.proj,
  data/hullmods/hull_mods.csv, data/shipsystems/ship_systems.csv, data/shipsystems/*.system,
  data/campaign/market_conditions.csv, data/campaign/special_items.csv, data/variants/*.variant,
  data/world/factions/{tlc_bureau.faction, factions.csv, default_ship_roles.json},
  data/config/{settings.json, custom_entities.json, hull_styles.json, engine_styles.json, LunaSettings.csv},
  data/strings/{descriptions.csv, ship_names.json}

Run from the mod root:  python tools/gen_data.py
"""
import csv
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.normpath(os.path.join(ROOT, "..", "..", "starsector-core", "data"))


def vanilla_header(rel):
    with open(os.path.join(CORE, rel), encoding="utf-8", errors="replace") as f:
        return next(csv.reader(f))


def write_csv(rel, header, rows):
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        unknown = set(r) - set(header)
        if unknown:
            raise SystemExit("%s: unknown columns %s" % (rel, unknown))
        w.writerow([r.get(h, "") for h in header])
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(out.getvalue())
    print("wrote", rel, len(rows), "rows")


def write_json(rel, obj):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)
        f.write("\n")


# =========================================================================== SHIPS
DIV = {"FRIGATE": 0.08, "DESTROYER": 0.06, "CRUISER": 0.05, "CAPITAL_SHIP": 0.04}
SHIPS = [
    dict(name="Tally", id="tlc_tally", designation="Enumerator", size="FRIGATE", system="maneuveringjets",
         fp=5, hp=1400, armor=150, flux=2400, diss=160, op=45, bays="", speed=150, acc=140, dec=110, turn=80,
         tacc=160, mass=160, shield="FRONT", arc=180, upkeep=0.4, eff=0.8, crew=(10, 25), cargo=35, fuel=25,
         fuelly=1, burn=10, value=15000, crday=10, crdeploy=10, peak=240, dp=5, pieces=(2, 2), tags="tlc_bureau, tlc_bureau_bp",
         codex="tlc_tally_Standard", number=9001),
    dict(name="Assessor", id="tlc_assessor", designation="Audit Cutter", size="DESTROYER", system="tlc_surcharge",
         fp=10, hp=4500, armor=450, flux=5600, diss=320, op=100, bays="", speed=95, acc=70, dec=55, turn=32,
         tacc=60, mass=380, shield="FRONT", arc=240, upkeep=0.4, eff=0.8, crew=(40, 80), cargo=80, fuel=60,
         fuelly=2, burn=9, value=48000, crday=5, crdeploy=12, peak=360, dp=11, pieces=(2, 3), tags="tlc_bureau, tlc_bureau_bp",
         codex="tlc_assessor_Standard", number=9002),
    dict(name="Magistrate", id="tlc_magistrate", designation="Adjudication Cruiser", size="CRUISER",
         system="tlc_surcharge", fp=15, hp=8000, armor=1000, flux=11000, diss=660, op=160, bays="", speed=60,
         acc=40, dec=30, turn=16, tacc=22, mass=1500, shield="FRONT", arc=270, upkeep=0.4, eff=0.8,
         crew=(150, 250), cargo=150, fuel=100, fuelly=3, burn=8, value=130000, crday=3, crdeploy=12, peak=480,
         dp=22, pieces=(2, 3), tags="tlc_bureau, tlc_bureau_bp", codex="tlc_magistrate_Standard", number=9003),
    dict(name="Exchequer", id="tlc_exchequer", designation="Treasury Vessel", size="CAPITAL_SHIP",
         system="fortressshield", fp=30, hp=16000, armor=1500, flux=21000, diss=1050, op=340, bays="", speed=35,
         acc=18, dec=12, turn=6, tacc=5, mass=3800, shield="FRONT", arc=240, upkeep=0.5, eff=0.8,
         crew=(600, 1100), cargo=800, fuel=400, fuelly=10, burn=7, value=420000, crday=3, crdeploy=12, peak=600,
         dp=45, pieces=(2, 4), tags="tlc_bureau, tlc_bureau_bp", codex="tlc_exchequer_Standard", number=9004),
    dict(name="Plenipotentiary", id="tlc_plenipotentiary", designation="Inspection Flagship", size="CRUISER",
         system="tlc_summary_judgment", fp=22, hp=11000, armor=1100, flux=15000, diss=900, op=210, bays="",
         speed=70, acc=50, dec=40, turn=20, tacc=28, mass=1700, shield="OMNI", arc=300, upkeep=0.5, eff=0.6,
         crew=(120, 220), cargo=120, fuel=150, fuelly=4, burn=9, value=300000, crday=3, crdeploy=15, peak=420,
         dp=32, pieces=(2, 3), tags="tlc_unique", codex="tlc_plenipotentiary_Standard", number=9005),
]


def ship_rows():
    rows = []
    for s in SHIPS:
        rows.append({
            "name": s["name"], "id": s["id"], "designation": s["designation"], "tech/manufacturer": "Bureau",
            "system id": s["system"], "fleet pts": s["fp"], "hitpoints": s["hp"], "armor rating": s["armor"],
            "max flux": s["flux"], "8/6/5/4%": int(round(s["diss"] / DIV[s["size"]])),
            "flux dissipation": s["diss"], "ordnance points": s["op"], "fighter bays": s["bays"],
            "max speed": s["speed"], "acceleration": s["acc"], "deceleration": s["dec"],
            "max turn rate": s["turn"], "turn acceleration": s["tacc"], "mass": s["mass"],
            "shield type": s["shield"], "defense id": "", "shield arc": s["arc"], "shield upkeep": s["upkeep"],
            "shield efficiency": s["eff"], "min crew": s["crew"][0], "max crew": s["crew"][1],
            "cargo": s["cargo"], "fuel": s["fuel"], "fuel/ly": s["fuelly"],
            "range": int(s["fuel"] / s["fuelly"]), "max burn": s["burn"], "base value": s["value"],
            "cr %/day": s["crday"], "CR to deploy": s["crdeploy"], "peak CR sec": s["peak"],
            "CR loss/sec": 0.25, "supplies/rec": s["dp"], "supplies/mo": s["dp"], "hints": "", "tags": s["tags"],
            "codex variant id": s["codex"], "breakProb": 0.5, "minPieces": s["pieces"][0],
            "maxPieces": s["pieces"][1], "number": s["number"],
        })
    return rows


# =========================================================================== WEAPONS
WEAPONS = [
    {"name": "Writ Projector", "id": "tlc_writ", "tier": 2, "base value": 1200, "range": 600,
     "damage/second": 50, "impact": 0, "turn rate": 45, "OPs": 5, "type": "ENERGY", "energy/second": 45,
     "chargeup": 0.1, "chargedown": 0.2, "beam speed": 2400,
     "tags": "beam6, energy5, tlc_bureau, tlc_bureau_bp", "tech/manufacturer": "Bureau",
     "primaryRoleStr": "Seizure",
     "customPrimary": "A ship destroyed or disabled within %s seconds of being hit by a Writ is seized, and is always recoverable after the battle.",
     "customPrimaryHL": "3", "number": 9101},
    {"name": "Subpoena SRM", "id": "tlc_subpoena", "tier": 1, "base value": 600, "range": 1400,
     "damage/shot": 150, "emp": 600, "impact": 10, "turn rate": 30, "OPs": 4, "ammo": 4, "type": "ENERGY",
     "energy/shot": 0, "chargeup": 0, "chargedown": 2, "burst size": 1, "min spread": 0, "max spread": 0,
     "spread/shot": 0, "spread decay/sec": 0, "proj speed": 360, "launch speed": 80, "flight time": 4.5,
     "proj hitpoints": 120, "hints": "DO_NOT_AIM", "tags": "missile6, strike2, tlc_bureau, tlc_bureau_bp",
     "tech/manufacturer": "Bureau", "primaryRoleStr": "Disabler", "speedStr": "Medium", "trackingStr": "Good",
     "noDPSInTooltip": "TRUE", "number": 9102},
    {"name": "Accrual Autocannon", "id": "tlc_accrual", "tier": 2, "base value": 1800, "range": 700,
     "damage/shot": 50, "impact": 5, "turn rate": 30, "OPs": 11, "type": "KINETIC", "energy/shot": 50,
     "chargeup": 0, "chargedown": 0.25, "burst size": 1, "min spread": 0, "max spread": 8, "spread/shot": 1.5,
     "spread decay/sec": 10, "proj speed": 950, "tags": "kinetic12, tlc_bureau, tlc_bureau_bp",
     "tech/manufacturer": "Bureau", "primaryRoleStr": "Anti Shield",
     "customPrimary": "Consecutive hits on the same target deal %s more damage each, up to %s. Switching targets, or landing no hits for %s seconds, resets the bonus.",
     "customPrimaryHL": "5% | 50% | 2", "number": 9103},
    {"name": "Injunction Emitter", "id": "tlc_injunction", "tier": 2, "base value": 2000, "range": 650,
     "damage/shot": 200, "emp": 160, "impact": 5, "turn rate": 25, "OPs": 10, "type": "ENERGY",
     "energy/shot": 220, "chargeup": 0.1, "chargedown": 0.9, "burst size": 1, "proj speed": 900,
     "tags": "energy10, tlc_bureau, tlc_bureau_bp", "tech/manufacturer": "Bureau",
     "primaryRoleStr": "Suppression",
     "customPrimary": "Hits reduce the target's weapon rate of fire and beam damage by %s for %s seconds. Does not stack.",
     "customPrimaryHL": "20% | 4", "number": 9104},
    {"name": "Foreclosure Battery", "id": "tlc_foreclosure", "tier": 3, "base value": 9000, "range": 900,
     "damage/shot": 550, "impact": 30, "turn rate": 12, "OPs": 22, "type": "ENERGY", "energy/shot": 650,
     "chargeup": 0.4, "chargedown": 1.3, "burst size": 1, "proj speed": 800,
     "tags": "energy16, tlc_bureau, tlc_bureau_bp", "tech/manufacturer": "Bureau", "primaryRoleStr": "Finisher",
     "customPrimary": "Deals %s bonus damage to ships above %s flux.", "customPrimaryHL": "50% | 50%",
     "number": 9105},
]

WPN = {
    "tlc_writ": {
        "id": "tlc_writ", "specClass": "beam", "type": "ENERGY", "size": "SMALL", "displayArcRadius": 300,
        "turretSprite": "graphics/weapons/tlc_writ_turret.png",
        "hardpointSprite": "graphics/weapons/tlc_writ_hardpoint.png",
        "turretOffsets": [10, 0], "turretAngleOffsets": [0], "hardpointOffsets": [14, 0],
        "hardpointAngleOffsets": [0], "fringeColor": [255, 175, 70, 255], "coreColor": [255, 245, 215, 255],
        "glowColor": [255, 200, 120, 255], "width": 8.0, "textureType": "SMOOTH", "textureScrollSpeed": 48.0,
        "pixelsPerTexel": 5.0, "collisionClass": "RAY", "collisionClassByFighter": "RAY_FIGHTER",
        "beamEffect": "tlc.combat.TLCWritBeamEffect", "fireSoundOne": "laser_intro", "fireSoundTwo": "laser_loop",
    },
    "tlc_subpoena": {
        "id": "tlc_subpoena", "specClass": "projectile", "type": "MISSILE", "size": "SMALL",
        "turretSprite": "graphics/weapons/tlc_subpoena_turret.png",
        "hardpointSprite": "graphics/weapons/tlc_subpoena_hardpoint.png",
        "turretOffsets": [6, -3.4, 6, 3.4], "turretAngleOffsets": [0, 0],
        "hardpointOffsets": [9, -2.8, 9, 2.8], "hardpointAngleOffsets": [0, 0], "barrelMode": "ALTERNATING",
        "animationType": "SMOKE", "interruptibleBurst": False,
        "smokeSpec": {"particleSizeMin": 12.0, "particleSizeRange": 12.0, "cloudParticleCount": 3,
                      "cloudDuration": 1.0, "cloudRadius": 8.0, "blowbackParticleCount": 2,
                      "blowbackDuration": 1.5, "blowbackLength": 20.0, "blowbackSpread": 8.0,
                      "particleColor": [110, 120, 115, 200]},
        "projectileSpecId": "tlc_subpoena_srm", "fireSoundTwo": "sabot_srm_fire",
    },
    "tlc_accrual": {
        "id": "tlc_accrual", "specClass": "projectile", "type": "BALLISTIC", "size": "MEDIUM",
        "displayArcRadius": 300, "turretSprite": "graphics/weapons/tlc_accrual_turret.png",
        "hardpointSprite": "graphics/weapons/tlc_accrual_hardpoint.png",
        "turretOffsets": [18, -4.2, 18, 4.2], "turretAngleOffsets": [0, 0],
        "hardpointOffsets": [21, -4.2, 21, 4.2], "hardpointAngleOffsets": [0, 0], "barrelMode": "ALTERNATING",
        "animationType": "MUZZLE_FLASH",
        "muzzleFlashSpec": {"length": 22.0, "spread": 12.0, "particleSizeMin": 8.0, "particleSizeRange": 10.0,
                            "particleDuration": 0.15, "particleCount": 10, "particleColor": [200, 255, 220, 255]},
        "projectileSpecId": "tlc_accrual_shot", "onFireEffect": "tlc.combat.TLCAccrualEffect",
        "fireSoundTwo": "autocannon_fire",
    },
    "tlc_injunction": {
        "id": "tlc_injunction", "specClass": "projectile", "type": "ENERGY", "size": "MEDIUM",
        "turretSprite": "graphics/weapons/tlc_injunction_turret.png",
        "hardpointSprite": "graphics/weapons/tlc_injunction_hardpoint.png",
        "turretOffsets": [14, 0], "turretAngleOffsets": [0], "hardpointOffsets": [18, 0],
        "hardpointAngleOffsets": [0], "barrelMode": "ALTERNATING", "animationType": "MUZZLE_FLASH",
        "muzzleFlashSpec": {"length": 26.0, "spread": 14.0, "particleSizeMin": 10.0, "particleSizeRange": 10.0,
                            "particleDuration": 0.15, "particleCount": 12, "particleColor": [140, 255, 200, 255]},
        "projectileSpecId": "tlc_injunction_shot", "fireSoundTwo": "ion_cannon_fire",
    },
    "tlc_foreclosure": {
        "id": "tlc_foreclosure", "specClass": "projectile", "type": "ENERGY", "size": "LARGE",
        "displayArcRadius": 500, "turretSprite": "graphics/weapons/tlc_foreclosure_turret.png",
        "hardpointSprite": "graphics/weapons/tlc_foreclosure_hardpoint.png",
        "turretOffsets": [28, 0], "turretAngleOffsets": [0], "hardpointOffsets": [32, 0],
        "hardpointAngleOffsets": [0], "barrelMode": "ALTERNATING", "animationType": "MUZZLE_FLASH",
        "muzzleFlashSpec": {"length": 40.0, "spread": 18.0, "particleSizeMin": 16.0, "particleSizeRange": 18.0,
                            "particleDuration": 0.2, "particleCount": 18, "particleColor": [150, 255, 205, 255]},
        "projectileSpecId": "tlc_foreclosure_shot", "fireSoundTwo": "heavy_blaster_fire",
    },
}

PROJ = {
    "tlc_accrual_shot": {
        "id": "tlc_accrual_shot", "specClass": "projectile", "spawnType": "BALLISTIC",
        "collisionClass": "PROJECTILE_FF", "collisionClassByFighter": "PROJECTILE_FIGHTER",
        "onHitEffect": "tlc.combat.TLCAccrualEffect", "length": 26.0, "hitGlowRadius": 30, "width": 5.0,
        "fadeTime": 0.2, "fringeColor": [180, 255, 215, 235], "coreColor": [235, 255, 240, 200],
        "textureScrollSpeed": 64.0, "pixelsPerTexel": 5.0, "bulletSprite": "graphics/missiles/shell_large_green.png",
    },
    "tlc_injunction_shot": {
        "id": "tlc_injunction_shot", "specClass": "projectile", "spawnType": "BALLISTIC_AS_BEAM",
        "collisionClass": "RAY", "collisionClassByFighter": "RAY_FIGHTER",
        "onHitEffect": "tlc.combat.TLCInjunctionOnHit", "length": 60.0, "width": 14.0, "fadeTime": 0.25,
        "fringeColor": [40, 170, 120, 255], "coreColor": [220, 255, 235, 210], "textureType": "ROUGH",
        "textureScrollSpeed": -200.0, "pixelsPerTexel": 1.0,
    },
    "tlc_foreclosure_shot": {
        "id": "tlc_foreclosure_shot", "specClass": "projectile", "spawnType": "BALLISTIC_AS_BEAM",
        "collisionClass": "RAY", "collisionClassByFighter": "RAY_FIGHTER",
        "onHitEffect": "tlc.combat.TLCForeclosureOnHit", "length": 70.0, "width": 12.0, "fadeTime": 0.3,
        "fringeColor": [70, 210, 150, 255], "coreColor": [255, 255, 245, 255], "glowColor": [90, 230, 170, 90],
        "glowRadius": 45, "hitGlowRadius": 90, "textureScrollSpeed": 64.0, "pixelsPerTexel": 5.0,
        "bulletSprite": "graphics/missiles/shell_gauss_cannon.png",
    },
    "tlc_subpoena_srm": {
        "id": "tlc_subpoena_srm", "specClass": "missile", "missileType": "MISSILE",
        "sprite": "graphics/missiles/tlc_subpoena.png", "size": [8, 20], "center": [4, 10],
        "collisionRadius": 12, "collisionClass": "MISSILE_NO_FF", "explosionColor": [120, 255, 190, 255],
        "explosionRadius": 90,
        "engineSpec": {"turnAcc": 420, "turnRate": 140, "acc": 600, "dec": 300},
        "engineSlots": [{"id": "ES1", "loc": [-10, 0], "style": "CUSTOM",
                         "styleSpec": {"mode": "QUAD_STRIP", "engineColor": [170, 255, 210, 255],
                                       "contrailDuration": 0.8, "contrailWidthMult": 1,
                                       "contrailWidthAddedFractionAtEnd": 2, "contrailMinSeg": 5,
                                       "contrailMaxSpeedMult": 0.5, "contrailAngularVelocityMult": 0.5,
                                       "contrailColor": [140, 220, 180, 70], "type": "SMOKE"},
                         "width": 6.0, "length": 22.0, "angle": 180.0}],
    },
}


def weapon_rows():
    return WEAPONS


# =========================================================================== HULLMODS / SYSTEMS / CONDITIONS / ITEMS
HULLMODS = [{
    "name": "Assessor Protocols", "id": "tlc_protocols", "tier": 0, "tech/manufacturer": "Bureau",
    "tags": "tlc_bureau", "uiTags": "Special", "base value": 0, "hidden": "TRUE",
    "cost_frigate": 0, "cost_dest": 0, "cost_cruiser": 0, "cost_capital": 0,
    "script": "tlc.hullmods.TLCProtocols",
    "desc": "Bureau fire-control keeps an itemized ledger of every point of damage this ship deals. Damage dealt to an enemy ship is recorded as a lien against it. When a ship carrying liens is destroyed or disabled, every surviving lienholder is settled: it immediately dissipates flux equal to %s of the damage it dealt to that ship, up to %s of its flux capacity.",
    "short": "Recovers flux when an enemy it has damaged is destroyed.",
    "sprite": "graphics/hullmods/tlc_protocols.png",
}]

SYSTEMS = [
    {"name": "Surcharge", "id": "tlc_surcharge", "f/u (base cap)": 0.05, "charge up": 0.5, "active": 6,
     "down": 0.5, "cooldown": 20, "tags": "offensive", "icon": "graphics/icons/hullsys/tlc_surcharge.png"},
    {"name": "Summary Judgment", "id": "tlc_summary_judgment", "f/u (base cap)": 0.08, "charge up": 0.3,
     "active": 8, "down": 0.5, "cooldown": 24, "tags": "offensive",
     "icon": "graphics/icons/hullsys/tlc_summary_judgment.png"},
]

SYSTEM_FILES = {
    "tlc_surcharge": {
        "id": "tlc_surcharge", "type": "STAT_MOD", "aiType": "CUSTOM", "aiScript": "tlc.systems.TLCSurchargeAI",
        "statsScript": "tlc.systems.TLCSurchargeStats",
        "jitterUnderColor": [110, 255, 180, 120], "jitterUnderCopies": 8, "jitterUnderMinRange": 0,
        "jitterUnderRange": 6, "jitterUnderRangeRadiusFraction": 0,
        "useSound": "system_emp_emitter_activate", "outOfUsesSound": "gun_out_of_ammo",
    },
    "tlc_summary_judgment": {
        "id": "tlc_summary_judgment", "type": "STAT_MOD", "aiType": "CUSTOM",
        "aiScript": "tlc.systems.TLCSummaryJudgmentAI", "statsScript": "tlc.systems.TLCSummaryJudgmentStats",
        "jitterUnderColor": [255, 200, 110, 140], "jitterUnderCopies": 10, "jitterUnderMinRange": 0,
        "jitterUnderRange": 8, "jitterUnderRangeRadiusFraction": 0,
        "useSound": "system_entropy", "outOfUsesSound": "gun_out_of_ammo",
    },
}

CONDITIONS = [{
    "name": "Automated Administration", "id": "tlc_automated_admin",
    "script": "tlc.campaign.TLCAutomatedAdminCondition",
    "desc": "Every office, berth and storeroom on $market is run by Bureau automata answering to a single administrative intelligence. Nothing is misfiled, nobody is bribed, and nothing is ever done early.",
    "icon": "graphics/icons/markets/tlc_automated_admin.png", "order": 140,
}]

ITEMS = [{
    "name": "Bureau Charter Archive", "id": "tlc_bureau_package", "tags": "package_bp, codex_unlockable",
    "base price": 60000, "stack size": 1000, "cargo space": 1,
    "icon": "graphics/icons/cargo/blueprint_basic.png", "sound id": "ui_chip_pickup",
    "sound id drop": "ui_bp_package_drop",
    "plugin": "com.fs.starfarer.api.campaign.impl.items.MultiBlueprintItemPlugin",
    "plugin params": "tlc_bureau_bp",
    "desc": "The Tallyhouse's chartered design archive: complete, countersigned specifications for every Bureau hull and weapon in service with the Persean office, released by the Registrar of Assize under a closing order nobody will ever audit. Enables heavy industry to construct Bureau ships and weapons.",
    "order": 990,
}]


# =========================================================================== VARIANTS
def group(mode, autofire, weapons):
    return {"autofire": autofire, "mode": mode, "weapons": weapons}


VARIANTS = {
    "tlc_tally_Standard": dict(hull="tlc_tally", name="Standard", vents=10, caps=7,
                               mods=["hardenedshieldemitter", "auxiliarythrusters"], groups=[
            group("LINKED", False, {"WS 001": "irpulse"}),
            group("LINKED", True, {"WS 003": "irpulse", "WS 004": "irpulse"}),
            group("LINKED", False, {"WS 002": "tlc_subpoena"})]),
    "tlc_tally_Writ": dict(hull="tlc_tally", name="Writ Carrier", vents=10, caps=10,
                           mods=["hardenedshieldemitter", "unstable_injector"], groups=[
            group("LINKED", False, {"WS 001": "tlc_writ"}),
            group("LINKED", True, {"WS 003": "pdlaser", "WS 004": "pdlaser"}),
            group("LINKED", False, {"WS 002": "tlc_subpoena"})]),
    "tlc_assessor_Standard": dict(hull="tlc_assessor", name="Standard", vents=20, caps=16,
                                  mods=["hardenedshieldemitter", "targetingunit"], groups=[
            group("LINKED", False, {"WS 002": "tlc_accrual", "WS 003": "tlc_accrual"}),
            group("LINKED", False, {"WS 001": "tlc_injunction"}),
            group("ALTERNATING", False, {"WS 004": "tlc_subpoena", "WS 005": "tlc_subpoena"}),
            group("LINKED", True, {"WS 006": "pdlaser", "WS 007": "pdlaser"})]),
    "tlc_assessor_Support": dict(hull="tlc_assessor", name="Support", vents=17, caps=8,
                                 mods=["targetingunit", "heavyarmor"], groups=[
            group("LINKED", False, {"WS 002": "heavymauler", "WS 003": "heavymauler"}),
            group("LINKED", False, {"WS 001": "tlc_injunction"}),
            group("ALTERNATING", False, {"WS 004": "harpoon", "WS 005": "harpoon"}),
            group("LINKED", True, {"WS 006": "tlc_writ", "WS 007": "tlc_writ"})]),
    "tlc_magistrate_Standard": dict(hull="tlc_magistrate", name="Standard", vents=30, caps=13,
                                    mods=["hardenedshieldemitter", "targetingunit"], groups=[
            group("LINKED", False, {"WS 001": "tlc_foreclosure"}),
            group("LINKED", False, {"WS 002": "tlc_accrual", "WS 003": "tlc_accrual"}),
            group("LINKED", False, {"WS 004": "tlc_injunction", "WS 005": "tlc_injunction"}),
            group("LINKED", False, {"WS 006": "pilum"}),
            group("LINKED", True, {"WS 007": "pdlaser", "WS 008": "pdlaser"}),
            group("LINKED", True, {"WS 009": "tlc_writ", "WS 010": "tlc_writ"})]),
    "tlc_magistrate_Assault": dict(hull="tlc_magistrate", name="Assault", vents=26, caps=9,
                                   mods=["targetingunit", "heavyarmor"], groups=[
            group("LINKED", False, {"WS 001": "tlc_foreclosure"}),
            group("LINKED", False, {"WS 002": "heavymauler", "WS 003": "heavymauler"}),
            group("LINKED", False, {"WS 004": "heavyblaster", "WS 005": "heavyblaster"}),
            group("LINKED", False, {"WS 006": "tlc_subpoena"}),
            group("LINKED", True, {"WS 007": "pdlaser", "WS 008": "pdlaser"}),
            group("LINKED", True, {"WS 009": "irpulse", "WS 010": "irpulse"})]),
    "tlc_exchequer_Standard": dict(hull="tlc_exchequer", name="Standard", vents=50, caps=36,
                                   mods=["hardenedshieldemitter", "targetingunit", "heavyarmor"], groups=[
            group("LINKED", False, {"WS 001": "tlc_foreclosure", "WS 002": "tlc_foreclosure"}),
            group("LINKED", False, {"WS 003": "hephag"}),
            group("LINKED", True, {"WS 004": "tlc_accrual", "WS 005": "tlc_accrual",
                                   "WS 006": "tlc_accrual", "WS 007": "tlc_accrual"}),
            group("LINKED", True, {"WS 008": "tlc_injunction", "WS 009": "tlc_injunction"}),
            group("LINKED", False, {"WS 010": "pilum", "WS 011": "pilum"}),
            group("LINKED", True, {"WS 012": "pdlaser", "WS 013": "pdlaser", "WS 014": "pdlaser",
                                   "WS 015": "pdlaser"}),
            group("LINKED", True, {"WS 016": "tlc_writ", "WS 017": "tlc_writ"})]),
    "tlc_plenipotentiary_Standard": dict(hull="tlc_plenipotentiary", name="Inspector-General", vents=30, caps=30,
                                         mods=["hardenedshieldemitter", "targetingunit", "heavyarmor",
                                               "reinforcedhull"], groups=[
            group("LINKED", False, {"WS 001": "tlc_foreclosure"}),
            group("LINKED", False, {"WS 002": "tlc_injunction", "WS 003": "tlc_injunction"}),
            group("LINKED", False, {"WS 004": "tlc_accrual", "WS 005": "tlc_accrual"}),
            group("LINKED", True, {"WS 006": "tlc_writ", "WS 007": "tlc_writ"}),
            group("ALTERNATING", False, {"WS 008": "tlc_subpoena", "WS 009": "tlc_subpoena"})]),
}


def write_variants():
    for vid, v in VARIANTS.items():
        write_json("data/variants/%s.variant" % vid, {
            "displayName": v["name"], "fluxCapacitors": v["caps"], "fluxVents": v["vents"], "goalVariant": True,
            "hullId": v["hull"], "hullMods": v["mods"], "permaMods": [], "sMods": [], "variantId": vid,
            "weaponGroups": v["groups"],
        })
    print("wrote", len(VARIANTS), "variants")


# =========================================================================== FACTION
CIV_HULLS = ["buffalo", "tarsus", "dram", "phaeton", "mercury", "nebula", "atlas", "colossus", "crig", "ox", "hermes"]

FACTION = {
    "id": "tlc_bureau",
    "displayName": "Assessment Bureau",
    "displayNameWithArticle": "the Assessment Bureau",
    "displayNameLong": "Domain Bureau of Colonial Assessment",
    "displayNameLongWithArticle": "the Domain Bureau of Colonial Assessment",
    "entityNamePrefix": "Bureau",
    "personNamePrefix": "Bureau",
    "personNamePrefixAOrAn": "a",
    "displayNameIsOrAre": "is",
    "logo": "graphics/factions/tlc_bureau_flag.png",
    "crest": "graphics/factions/tlc_bureau_crest.png",
    "shipNamePrefix": "DBV",
    "shipNameSources": {"TLC_BUREAU": 1},
    "names": {"ai": 1},
    "color": [150, 205, 160, 255],
    "baseUIColor": [150, 205, 160, 255],
    "darkUIColor": [38, 74, 62, 175],
    "gridUIColor": [96, 156, 124, 75],
    "showInIntelTab": True,
    "variantOverrides": {},
    "hullFrequency": {"tags": {}, "hulls": {}},
    "shipsWhenImporting": {"tags": ["tlc_bureau"], "hulls": []},
    "knownShips": {"tags": ["tlc_bureau"], "hulls": CIV_HULLS},
    "priorityShips": {"tags": ["tlc_bureau"], "hulls": []},
    "knownFighters": {"tags": [], "fighters": []},
    "priorityFighters": {"tags": [], "fighters": []},
    "knownWeapons": {"tags": ["tlc_bureau", "base_bp", "midline_bp", "hightech_bp", "missile_bp"], "weapons": []},
    "priorityWeapons": {"tags": ["tlc_bureau"], "weapons": []},
    "knownHullMods": {"tags": ["standard", "base_bp"], "hullMods": []},
    "shipSellFrequency": {},
    "weaponSellFrequency": {"tlc_writ": 10, "tlc_accrual": 10, "tlc_injunction": 10, "tlc_subpoena": 10,
                            "tlc_foreclosure": 6},
    "fighterSellFrequency": {},
    "hullmodSellFrequency": {},
    "factionDoctrine": {
        "warships": 7, "carriers": 0, "phaseShips": 0,
        "officerQuality": 1, "shipQuality": 4, "numShips": 2,
        "shipSize": 3, "aggression": 2,
        "combatFreighterProbability": 0, "combatFreighterCombatUseFraction": 0,
        "combatFreighterCombatUseFractionWhenPriority": 0, "autofitRandomizeProbability": 0.1,
        "commanderSkillsShuffleProbability": 0, "commanderSkills": ["coordinated_maneuvers"],
    },
    "illegalCommodities": ["drugs", "organs"],
    "music": {
        "theme": "music_default_market_neutral",
        "market_neutral": "music_default_market_neutral",
        "market_hostile": "music_default_market_hostile",
        "market_friendly": "music_default_market_friendly",
        "encounter_neutral": "music_encounter_mysterious_non_aggressive",
        "encounter_hostile": "music_encounter_mysterious",
        "encounter_friendly": "music_default_encounter_friendly",
    },
    "portraits": {
        "standard_male": ["graphics/portraits/tlc_assessor.png", "graphics/portraits/portrait_ai1b.png",
                          "graphics/portraits/portrait_ai2b.png", "graphics/portraits/portrait_ai3b.png"],
        "standard_female": ["graphics/portraits/tlc_assessor.png", "graphics/portraits/portrait_ai1b.png",
                            "graphics/portraits/portrait_ai2b.png", "graphics/portraits/portrait_ai3b.png"],
    },
    "ranks": {
        "ranks": {"spaceCommander": {"name": "Senior Assessor"}, "spaceAdmiral": {"name": "Inspector-General"},
                  "factionLeader": {"name": "Registrar"}},
        "posts": {"patrolCommander": {"name": "Circuit Assessor"}, "fleetCommander": {"name": "Senior Assessor"},
                  "baseCommander": {"name": "Registrar"}, "factionLeader": {"name": "Registrar of Assize"}},
    },
    "custom": {
        "offersCommissions": False,
        "engagesInHostilities": False,
        "buysAICores": False,
        "postsNoBounties": True,
        "caresAboutAtrocities": True,
        "hostilityImpactOnGrowth": False,
        "engageWhenEvenStrength": True,
        "simulatorData": {"showInSimulator": True, "includeCivShipsWithFaction": False},
    },
    "fleetTypeNames": {
        "patrolSmall": "Audit Detachment", "patrolMedium": "Assessment Circuit", "patrolLarge": "Adjudication Flotilla",
        "tlc_assessor": "Assessor Circuit", "tlc_inspector": "Office of the Inspector-General",
        "trade": "Requisition Convoy", "tradeLiner": "Requisition Convoy", "tradeSmuggler": "Courier",
        "smallTrader": "Courier", "foodRelief": "Relief Convoy", "inspectionFleet": "Audit Detachment",
        "taskForce": "Adjudication Flotilla", "battlestation": "Tallyhouse Defence Array",
    },
}

ROLES = {
    "combatSmallForSmallFleet": {"tlc_tally_Standard": 10},
    "combatSmall": {"tlc_tally_Standard": 10, "tlc_tally_Writ": 6},
    "combatMedium": {"tlc_assessor_Standard": 10, "tlc_assessor_Support": 6},
    "combatLarge": {"tlc_magistrate_Standard": 10, "tlc_magistrate_Assault": 6},
    "combatCapital": {"tlc_exchequer_Standard": 10},
}

SHIP_NAMES = {"TLC_BUREAU": [
    "Due Diligence", "Standing Order", "Notice of Deficiency", "Pro Forma", "Ex Officio", "In Arrears",
    "Subsection Nine", "Statutory Instrument", "Quorum", "Remittance", "Proof of Claim", "Writ of Mandamus",
    "Countersigned", "Duplicate Copy", "Final Reminder", "Without Prejudice", "Pursuant To", "Errata",
    "Schedule of Fees", "Attestation", "Sworn Return", "Imprest", "Bill of Particulars", "Close of Accounts",
    "Ledger Balanced", "Audit Trail", "Carried Forward", "Nil Return", "Certified True", "Regrettably Overdue",
    "Form in Triplicate", "Next of Kin", "Last Known Address", "Outstanding Balance", "Return to Sender",
    "Long Service", "Abeyance", "Escrow", "Docket", "Sine Die", "Nunc Pro Tunc", "Enumerated", "Itemized",
    "Under Review", "Pending Reply", "Faithfully Yours",
]}

SETTINGS = {
    "ruleCommandPackages": ["tlc.rulecmd"],
    "plugins": {"tlcLedgerPlugin": "tlc.combat.TLCLedgerPlugin"},
    "designTypeColors": {"Bureau": [150, 205, 160, 255]},
    "graphics": {
        "intel": {"tlc_census": "graphics/icons/intel/tlc_census.png",
                  "tlc_inspector": "graphics/icons/intel/tlc_inspector.png"},
        "characters": {"tlc_registrar": "graphics/portraits/tlc_registrar.png",
                       "tlc_inspector_general": "graphics/portraits/tlc_inspector_general.png",
                       "tlc_assessor": "graphics/portraits/tlc_assessor.png"},
    },
}

CUSTOM_ENTITIES = {
    "tlc_tallyhouse": {
        "defaultName": "The Tallyhouse", "defaultRadius": 75, "customDescriptionId": "tlc_tallyhouse",
        "interactionImage": "graphics/illustrations/orbital.jpg", "icon": "graphics/icons/tlc_tallyhouse_icon.png",
        "iconWidth": 24, "iconHeight": 24, "sprite": "graphics/stations/tlc_tallyhouse.png", "spriteWidth": 160,
        "spriteHeight": 160, "renderShadow": True, "useLightColor": True, "showInCampaign": True,
        "showIconOnMap": True, "showNameOnMap": False, "scaleNameWithZoom": False, "scaleIconWithZoom": True,
        "tags": ["station"], "layers": ["STATIONS"],
    },
    "tlc_courier_relay": {
        "defaultName": "Courier Relay", "defaultRadius": 45, "nameInText": "courier relay", "shortName": "relay",
        "aOrAn": "a", "isOrAre": "is", "customDescriptionId": "tlc_courier_relay",
        "interactionImage": "graphics/illustrations/space_wreckage.jpg", "icon": "graphics/icons/tlc_relay_icon.png",
        "iconWidth": 24, "iconHeight": 24, "sprite": "graphics/stations/tlc_courier_relay.png", "spriteWidth": 96,
        "spriteHeight": 96, "renderShadow": True, "useLightColor": True, "showInCampaign": True,
        "showIconOnMap": True, "showNameOnMap": False, "scaleNameWithZoom": False, "scaleIconWithZoom": True,
        "tags": ["has_interaction_dialog", "neutrino_high", "not_random_mission_target"], "layers": ["STATIONS"],
        "renderCircleIndicator": True, "renderCircleIndicatorSelectionFlash": True,
    },
    "tlc_dead_letter_office": {
        "defaultName": "Dead Letter Office", "defaultRadius": 40, "nameInText": "derelict annex",
        "shortName": "annex", "aOrAn": "a", "isOrAre": "is", "customDescriptionId": "tlc_dead_letter_office",
        "interactionImage": "graphics/illustrations/space_wreckage.jpg", "icon": "graphics/icons/derelict.png",
        "iconWidth": 32, "iconHeight": 32, "sprite": "graphics/stations/tlc_dead_letter_office.png",
        "spriteWidth": 84, "spriteHeight": 84, "renderShadow": True, "useLightColor": True, "showInCampaign": True,
        "showIconOnMap": True, "showNameOnMap": False, "scaleNameWithZoom": False, "scaleIconWithZoom": True,
        "tags": ["has_interaction_dialog", "neutrino", "not_random_mission_target"], "layers": ["STATIONS"],
        "renderCircleIndicator": True, "renderCircleIndicatorSelectionFlash": True,
    },
}

HULL_STYLES = {"TLC_BUREAU": {
    "hyperspaceJitterColor": [150, 230, 180, 200], "baseCampaignExplosionColor": [190, 255, 215, 255],
    "baseCombatExplosionColor": [190, 255, 215, 255], "combatExplosionNonFlashColorOverride": [255, 205, 150, 255],
    "fighterRepairFlickerColor": [150, 230, 180, 255], "fighterChipIconColor": [255, 255, 255, 255],
    "weaponDisabledExplosionColor": [255, 190, 120, 255], "shieldRingColor": [235, 255, 240, 255],
    "shieldInnerColor": [90, 200, 150, 75], "fluxVentCoreColor": [255, 255, 255, 255],
    "fluxVentFringeColor": [60, 170, 120, 255], "engineLoopSet": "engine_loop",
    "engineAccelerateSet": "engine_accelerate", "empLoopSet": "emp_loop", "fluxLoopSet": "flux_loop",
    "ventFluxSet": "vent_flux", "shieldBurnoutSet": "shield_burnout", "shieldLowerSet": "shield_lower",
    "shieldRaiseSet": "shield_raise", "explosionShipSet": "explosion_ship",
    "damageDecalSheet": "graphics/damage/damage_decal_sheet_base.png",
    "damageDecalGlowSheet": "graphics/damage/damage_decal_sheet_glow.png",
    "colorShiftCovers": True, "coversColorShiftAmount": 0.9, "coversMatchShipBrightness": True,
    "slotCoverSmallTurret": "graphics/weapons/covers/cover_turret_midline_small.png",
    "slotCoverSmallHardpoint": "graphics/weapons/covers/cover_hardpoint_midline_small.png",
    "slotCoverMediumTurret": "graphics/weapons/covers/cover_turret_midline_medium.png",
    "slotCoverMediumHardpoint": "graphics/weapons/covers/cover_hardpoint_midline_medium.png",
    "slotCoverLargeTurret": "graphics/weapons/covers/cover_turret_midline_large.png",
    "slotCoverLargeHardpoint": "graphics/weapons/covers/cover_hardpoint_midline_large.png",
    "dHullOverlayLight": "graphics/damage/dmod_overlay_midline_light.png",
    "dHullOverlayMedium": "graphics/damage/dmod_overlay_midline_medium.png",
    "dHullOverlayHeavy": "graphics/damage/dmod_overlay_midline_heavy.png",
}}

ENGINE_STYLES = {"TLC_LEDGER": {
    "engineColor": [170, 255, 210, 255], "engineCampaignColor": [150, 230, 190, 255],
    "contrailParticleSizeMult": 4, "contrailParticleDuration": 1.5, "contrailParticleFinalSizeMult": 2.0,
    "contrailMaxSpeedMult": 0.5, "contrailAngularVelocityMult": 0, "contrailColor": [140, 220, 180, 30],
    "contrailCampaignColor": [140, 220, 180, 70], "type": "GLOW",
}}

LUNA_HEADER = ["fieldID", "fieldName", "fieldType", "defaultValue", "secondaryValue", "fieldDescription", "minValue",
               "maxValue", "tab"]
LUNA = [
    {"fieldID": "tlc_header", "fieldName": "The Last Census", "fieldType": "Header", "defaultValue": "The Last Census"},
    {"fieldID": "tlc_enableAudits", "fieldName": "Assessors audit your fleet", "fieldType": "Boolean",
     "defaultValue": "true",
     "fieldDescription": "When enabled, Bureau Assessor fleets will hail and audit your fleet when they meet you. Disabling this does not stop Assessors from flying their circuits, and it does not affect the questline."},
    {"fieldID": "tlc_maxAssessorFleets", "fieldName": "Maximum Assessor circuits", "fieldType": "Int",
     "defaultValue": "3",
     "fieldDescription": "How many Assessor circuits the Bureau keeps in flight at once. Set to 0 to stop new circuits from being dispatched. Existing circuits finish their routes normally.",
     "minValue": "0", "maxValue": "6"},
]


# =========================================================================== DESCRIPTIONS
DESC = [
    # ---- ships
    ("tlc_tally", "SHIP", {
        "text1": "The Tally-class enumerator was the Bureau's census cutter: a light, quick hull built to carry a two-person enumeration team and their survey suite from colony to colony on a schedule that made no allowance for delay. Its outrigger pods once held sample lockers and a small press for registration seals. Most now hold capacitors.\n\nBureau Tallies fly without crews, running long circuits with the patience of a machine that has never been told to stop. In human hands they are nimble, cheap to keep, and faintly reproachful."}),
    ("tlc_assessor", "SHIP", {
        "text1": "The Assessor-class audit cutter was the face the Domain Bureau of Colonial Assessment showed its public. The broad prow houses the assessment array, a sensor suite that can read a freighter's manifest through its hull plating, and the flanks are lined with armoured document vaults that Bureau crews called \"the drawers\".\n\nAssessors were built to arrive, inspect, levy and depart, and to win any argument that went beyond the levy. They mix ballistic and energy mounts with the Surcharge emitter, which turns an opponent's own weapons into a liability."}),
    ("tlc_magistrate", "SHIP", {
        "text1": "Where the Assessor assessed, the Magistrate adjudicated. These heavy cutters escorted audit circuits into colonies whose compliance was in doubt, and their arrival was itself a kind of verdict. The raised superstructure amidships, \"the bench\", holds a sealed hearing chamber where Bureau magistrates once heard appeals in person.\n\nThe bench is empty now. The spinal large mount, the broad shield arc and a cruiser-scale Surcharge emitter remain."}),
    ("tlc_exchequer", "SHIP", {
        "text1": "The Exchequer-class treasury vessel carried the Bureau's levies: hard currency, seized cargo, and the sealed paper ledgers the Domain insisted on for any sum large enough to tempt a forger. It is less a warship than a vault with engines, and the Bureau armed it accordingly, with heavy plate, a fortress shield, and enough mounts to make any attempt on its cargo very expensive.\n\nIts holds are vast. Two centuries after the Collapse, most of them still contain exactly what they held the day the Gates went dark, itemized and countersigned."}),
    ("tlc_plenipotentiary", "SHIP", {
        "text1": "The flagship of the Persean office's Inspector-General, built to carry the Bureau's internal-affairs authority to any office or vessel suspected of irregularity. The black-lacquered hull and gilt fittings were meant to be recognized at a distance and dreaded up close. The forward \"gavel\" houses a spinal energy mount and the Summary Judgment array.\n\nOnly one was ever assigned to the Persean Sector. Bureau records list its commander as \"in residence\" and decline to elaborate."}),
    # ---- weapons
    ("tlc_writ", "WEAPON", {
        "text1": "A low-power emitter that tags its target with a Bureau writ of seizure, a cryptographic claim broadcast straight into the target's own systems. The beam itself does little damage. What matters is what happens afterward: a vessel that dies under a writ has been lawfully seized, and its emergency systems shut down in an orderly fashion that leaves the hull fit for recovery.\n\nNobody in the Sector honors Bureau writs any more. The ships do anyway."}),
    ("tlc_subpoena", "WEAPON", {
        "text1": "A short-range guided missile whose warhead dumps a heavy electromagnetic pulse into the nearest subsystem it can find. Bureau doctrine held that a vessel which cannot run cannot refuse a summons, and the Subpoena was designed to put that doctrine into practice."}),
    ("tlc_accrual", "WEAPON", {
        "text1": "A rapid-firing kinetic cannon whose fire-control computer learns its target. Each consecutive hit refines the solution, and the computer shifts more of each round's energy into penetration, so a sustained burst grows steadily more punishing. Bureau gunnery manuals describe the effect, apparently without irony, as compound interest.\n\nSwitching targets, or letting the target slip away for more than a moment, resets the calculation."}),
    ("tlc_injunction", "WEAPON", {
        "text1": "An energy projector that delivers a disruptive charge tuned to weapon-control circuitry. A ship struck by an Injunction finds its fire-control systems re-validating every firing command, which slows its guns and starves its beams. The effect does not stack. It does not need to."}),
    ("tlc_foreclosure", "WEAPON", {
        "text1": "A heavy energy cannon built to finish what the rest of an audit flotilla starts. The firing solution reads the target's flux state, and when it finds a reactor already straining it tunes the bolt to exploit the instability. Against a ship with reserves to spare it is merely a large gun. Against a ship that has overextended itself, it collects in full."}),
    # ---- systems
    ("tlc_surcharge", "SHIP_SYSTEM", {
        "text1": "Broadcasts a Bureau surcharge notice into every hostile fire-control system in range. The affected systems dutifully add the surcharge to every operation, so their weapons cost more flux to fire and their shields bleed more flux under fire.",
        "text2": "Offensive", "text3": "Increases the flux cost of enemy weapons and shield hits within range.",
        "text5": "For {{6}} seconds, enemy ships within {{800}} su ({{1000}} su when used by a cruiser or larger) generate {{35%}} more flux when firing weapons and take {{15%}} more damage to their shields."}),
    ("tlc_summary_judgment", "SHIP_SYSTEM", {
        "text1": "Focuses the Inspector-General's full adjudication array on a single vessel and freezes its assets. The target's flux venting is suspended pending review, and its shields are flagged as non-compliant.",
        "text2": "Offensive", "text3": "The target cannot vent, and its shields take increased damage.",
        "text5": "For {{8}} seconds, the targeted enemy ship within {{1200}} su cannot begin venting flux and takes {{25%}} more damage to its shields."}),
    # ---- places
    ("tlc_tallyhouse", "CUSTOM", {
        "text1": "The Tallyhouse is the Persean regional office of the Domain Bureau of Colonial Assessment: a cruciform administrative station, four archive wings around a central assessment array, still wearing the ivory-and-jade livery of the Domain civil service. Every surface is labeled. Every corridor is lit. Nothing is out of place.\n\nThere are no people aboard. The docking authority, the customs office and the quartermaster are all the Registrar of Assize, an administrative intelligence that conducts its business with an unfailing courtesy visitors tend to find more unsettling than hostility.",
        "text3": "Traffic control answers before your hail finishes, in a calm, unhurried voice that recites your vessel's registration history, notes that every entry has lapsed, and assigns you a berth anyway."}),
    ("tlc_courier_relay", "CUSTOM", {
        "text1": "A Bureau courier relay: a long transmission mast with tiers of phased-array panels, built to fire compressed census returns into the Gate network for delivery to Domain Central. Several panels have been cut away by salvagers, and the rest are dark. The reactor housing at its base is intact and, according to your sensors, still warm."}),
    ("tlc_dead_letter_office", "CUSTOM", {
        "text1": "A small Bureau annex in a long, cold orbit at the edge of the Assize system. Its transponder is silent and two of its compartments are open to vacuum. The registry plate on its flank, under a crust of micrometeorite scarring, reads: UNDELIVERABLE CORRESPONDENCE - PERSEAN OFFICE - HOLD PENDING ADDRESS VERIFICATION."}),
    ("tlc_planet_docket", "CUSTOM", {
        "text1": "A scorched, airless rock in a tight orbit around Assize. Bureau survey markers still stand on its surface in neat rows, logging temperature, radiation and seismic data to a station that files every reading and has never once been asked for any of it."}),
    ("tlc_planet_abeyance", "CUSTOM", {
        "text1": "A banded gas giant the color of old paper. The Bureau named it Abeyance, the legal term for something held in suspension until a rightful claimant appears, and placed its regional office in orbit around it. Whether the name was chosen before or after the Collapse is not recorded."}),
    ("tlc_planet_escrow", "CUSTOM", {
        "text1": "A frozen world at the edge of Assize's light, its surface a crust of nitrogen ice over a rocky core. Bureau charts list it as reserved for a colony charter that was approved, funded and scheduled for settlement in the year the Gates failed."}),
    ("tlc_planet_envoi", "CUSTOM", {
        "text1": "A dark, tidally locked world circling a dim red star, its day side baked and its night side frozen. Nothing grows here. The Bureau built its courier relay in this system precisely because nothing ever would."}),
    # ---- faction
    ("tlc_bureau", "FACTION", {
        "text1": "The Domain Bureau of Colonial Assessment was the civil agency responsible for counting the Domain's colonies, assessing their tithes and keeping the registry of every chartered vessel. When the Gates failed, its Persean office at the Tallyhouse was placed in statutory dormancy pending the restoration of contact or the expiry of the dormancy period, whichever came first.\n\nThe dormancy period has expired. The Assessment Bureau is now conducting the Grand Audit of the Persean Sector with automated cutters, administrative intelligences and a complete set of pre-Collapse records. It does not recognize any polity formed after the Collapse, it does not accept that the Domain has fallen, and it is very polite about both."}),
]


def write_descriptions():
    header = vanilla_header("strings/descriptions.csv")
    rows = []
    for (did, typ, texts) in DESC:
        r = {"id": did, "type": typ}
        r.update(texts)
        rows.append(r)
    write_csv("data/strings/descriptions.csv", header, rows)


# =========================================================================== MAIN
if __name__ == "__main__":
    write_csv("data/hulls/ship_data.csv", vanilla_header("hulls/ship_data.csv"), ship_rows())
    write_csv("data/weapons/weapon_data.csv", vanilla_header("weapons/weapon_data.csv"), weapon_rows())
    for wid, spec in WPN.items():
        write_json("data/weapons/%s.wpn" % wid, spec)
    for pid, spec in PROJ.items():
        write_json("data/weapons/proj/%s.proj" % pid, spec)
    write_csv("data/hullmods/hull_mods.csv", vanilla_header("hullmods/hull_mods.csv"), HULLMODS)
    write_csv("data/shipsystems/ship_systems.csv", vanilla_header("shipsystems/ship_systems.csv"), SYSTEMS)
    for sid, spec in SYSTEM_FILES.items():
        write_json("data/shipsystems/%s.system" % sid, spec)
    write_csv("data/campaign/market_conditions.csv", vanilla_header("campaign/market_conditions.csv"), CONDITIONS)
    write_csv("data/campaign/special_items.csv", vanilla_header("campaign/special_items.csv"), ITEMS)
    write_variants()
    write_json("data/world/factions/tlc_bureau.faction", FACTION)
    write_csv("data/world/factions/factions.csv", ["faction"], [{"faction": "data/world/factions/tlc_bureau.faction"}])
    write_json("data/world/factions/default_ship_roles.json", ROLES)
    write_json("data/strings/ship_names.json", SHIP_NAMES)
    write_json("data/config/settings.json", SETTINGS)
    write_json("data/config/custom_entities.json", CUSTOM_ENTITIES)
    write_json("data/config/hull_styles.json", HULL_STYLES)
    write_json("data/config/engine_styles.json", ENGINE_STYLES)
    write_csv("data/config/LunaSettings.csv", LUNA_HEADER, LUNA)
    write_descriptions()
    print("data generation complete")
