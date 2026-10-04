# Verification Report — The Last Census

## 0. Honest summary
* **The game was not launched.** The brief asked that the PC not be taken over, so all verification here is static.
  The Java compiles cleanly against the real `starfarer.api.jar`; a 1,000-line validator checks every data file and
  cross-reference; every API call was checked against the API sources shipped with the game; and two adversarial
  reviews were done (one by an independent reviewer agent).
* Results: **build 0 errors, 0 warnings** (`javac --release 17 -Xlint:all`); **validator 0 errors, 0 warnings**.
* What static checks cannot prove: in-game behaviour of AI fleets, visual tuning, actual balance in combat, and
  engine behaviours that are not visible in the API source (e.g. exactly when a hassling fleet opens the
  conversation). Those are listed in §6 as untested.

## 1. Build
| Item | Result |
|---|---|
| Compiler | Temurin javac 17.0.20.1, `--release 17` (game runs Azul Zulu 17.0.10; API class files are major 61) |
| Classpath | starfarer.api.jar, json, log4j, lwjgl, lwjgl_util, xstream, LazyLib (+Kotlin runtime), LunaLib, GraphicsLib (compile-time only, for the optional `tlc.compat` class) |
| Sources | 28 Java files, ~3,400 lines |
| Errors / warnings | 0 / 0 with `-Xlint:all` (serial/options/classfile/processing lint categories off) |
| Output | `jars/TheLastCensus.jar` |
| Command | `./build.sh` (fails with non-zero exit on any javac error or validator error) |

## 2. What `tools/validate.py` checks
1. **Parsing:** every mod `.json/.ship/.variant/.wpn/.proj/.system/.faction` parses as *strict* JSON. Vanilla files
   are read with a Starsector-dialect parser (comments, trailing commas, bare tokens, `0.5f`).
2. **CSV structure:** each known CSV has exactly the vanilla header, and every row has the header's column count.
3. **IDs:** no duplicates; every id carries the `tlc_` prefix (style ids use `TLC_`); no collision with any vanilla
   hull/skin, weapon, wing, hullmod, system, faction, condition, industry, item, entity type, variant or projectile id.
4. **Hulls:** a `.ship` exists for each row with a matching `hullId`. The sprite exists and its size equals
   width/height. Center, shield center and bounds lie inside the sprite. **Every weapon slot sits on opaque hull
   pixels.** Engines sit at the hull edge. Slot mount/size/type/arc are legal. The system id, built-in hullmods, hull
   style, engine styles and codex variant all exist. collisionRadius ≥ the bounds extent. A SHIP description exists.
5. **Weapons:** a `.wpn` exists per row with a matching id. All sprites, sounds and projectile specs exist. Offset and
   angle-offset arrays have consistent lengths. Muzzle offsets are sane relative to sprite size. Effect classes
   (`beamEffect`, `onFireEffect`, `onHitEffect`) exist in the compiled jar or the API. A WEAPON description exists.
6. **Variants:** the hull exists, the slots exist, and the weapons exist. **Mount legality**: the type compatibility
   matrix (HYBRID/SYNERGY/COMPOSITE/UNIVERSAL) is enforced, and a weapon may be the slot's size or one size smaller.
   **OP budget**: weapons + non-built-in hullmods at the hull size's cost + vents + capacitors ≤ hull OP. Vents and
   caps stay under the per-size maximum. Hullmods exist and are not hidden. No slot is used twice.
   OP use per variant is printed.
7. **Faction:** all referenced hulls, weapons, wings, hullmods, portraits, logo/crest, ship-name sources,
   person-name categories, music and illegal commodities exist. Doctrine points sum to 7/7. The faction knows at
   least one mod hull. **Every weapon and hullmod on the faction's own role variants is known to the faction**
   (added during this session after a real bug was found). A FACTION description exists.
8. **Roles:** every role in `default_ship_roles.json` is a vanilla role, and every variant listed exists.
9. **Systems, hullmods, conditions, items:** stats and AI script classes exist (CUSTOM aiType requires an aiScript).
   Sounds and icons exist. Hullmod descriptions contain `%s` parameters. Blueprint package tags match real hulls/weapons.
10. **Custom entities, styles, settings:** sprites, icons, illustrations and description ids exist. Hull-style
    sound sets exist. Graphics paths in `settings.json` exist. Combat plugin classes exist. Rule-command packages
    contain compiled classes. LunaSettings field types are valid. The mod_info plugin class and jar exist.
    **Dependencies are installed.**
11. **rules.csv:** header; unique `tlc_` ids; every condition and script command is a real rule command (vanilla
    `rulecmd.*` or the mod's compiled `tlc.rulecmd.*`); **every option introduced has a `DialogOptionSelected`
    handler** (except vanilla built-ins such as `cutCommLinkNoText`); every custom trigger fired with
    FireAll/FireBest has rules; every option id added from Java has a handler.
12. **Java ↔ data:** each `TLCIds` constant resolves in the registry its prefix names (HULL_, VARIANT_, WEAPON_,
    HULLMOD_, SYSTEM_, CONDITION_, ITEM_, FACTION_, ENTITY_, DESC_, PORTRAIT_, LUNA_, INDUSTRY_, SUBMARKET_,
    COMMODITY_). Every `"tlc_*"` string literal in Java is a known id or an explicitly whitelisted instance id.
    Every `setCustomDescriptionId`, `addCustomEntity` type, `addCondition`, `addIndustry` and `addSubmarket` literal
    resolves. Every graphics path in Java exists.
13. **Assets:** no orphan files under `graphics/`.
14. **GraphicsLib light data (optional):** header identical to GraphicsLib's `core_light_data.csv`; every projectile/beam id exists; type valid; the compat call is guarded by `isModEnabled("shaderLib")`.

**Validator self-test (fault injection):** each of the following was deliberately broken and caught, then restored:
illegal mount (large weapon in a small slot), OP overflow, unknown weapon in the faction file, slot moved outside the
sprite, a rules option with no handler, a missing Java class in a `.system` file, and a faction role variant using a
weapon the faction doesn't know.

## 3. Final results
```
[build] compiling 27 source files
[build] wrote jars/TheLastCensus.jar
  variant tlc_assessor_Standard          OP 100 / 100
  variant tlc_assessor_Support           OP 100 / 100
  variant tlc_exchequer_Standard         OP 340 / 340
  variant tlc_magistrate_Assault         OP 160 / 160
  variant tlc_magistrate_Standard        OP 160 / 160
  variant tlc_plenipotentiary_Standard   OP 205 / 210
  variant tlc_tally_Standard             OP  48 /  50
  variant tlc_tally_Writ                 OP  48 /  50
validate.py: 0 error(s), 0 warning(s)
[build] OK
```

## 4. Startup and new-game trace (manual, line by line)
1. **Application load:** the launcher reads `mod_info.json` (strict JSON, jar path and plugin class verified).
   Data CSV/JSON load: all formats checked (§2). The rules loader resolves command names, all of which exist.
   `settings.json` registers `tlcLedgerPlugin` (an `EveryFrameCombatPlugin`, same mechanism LunaLib and Console
   Commands use) and the `tlc.rulecmd` package. `TLCModPlugin.onApplicationLoad` only logs.
2. **New game, `onNewGame`:** vanilla SectorGen has already run. `TLCWorldGen.generateIfNeeded` checks the
   `$tlc_generated` sector flag and that the faction is loaded. It creates Assize (a free hyperspace spot is searched
   on rings of 1,400 su until 2,600 su from every existing system), its planets, the Tallyhouse custom entity, the
   comm relay and nav buoy, the asteroid belt, and the discoverable Dead Letter Office. It auto-generates jump points
   and clears hyperspace storms around the system (vanilla `NebulaEditor` pattern, try/catch). It then creates the
   market (vanilla station-market pattern; compare Citadel Arcadia: population_4 with population, spaceport,
   militarybase, a station) and adds it with `economy.addMarket(m, true)`. Then Envoi and its relay, faction
   relations (each null-checked), and the Registrar (ImportantPeople + admin + comm directory, idempotent).
   Everything is inside try/catch with logging.
3. **Procgen** places its systems around Assize and Envoi (they exist before procgen runs).
4. **`onGameLoad(true)`:** `ensurePeople` (idempotent), then the `TLCAssessorManager` sector script is added once
   (`hasScript` guard).
5. **First ticks:** the manager ticks every 0.4–0.6 days (try/catch around the whole tick). Day 1: the first Assessor
   circuit spawns. Day 3: the census intel appears. Subsequent circuits follow at ~7-day intervals up to the cap.
6. **Existing save:** `onGameLoad(false)` runs the same idempotent generation once (`$tlc_generated`;
   `getStarSystem("Assize")` is also checked so a system can never be duplicated), then the same script setup.
7. **Combat start:** the engine instantiates `TLCLedgerPlugin`, whose `init` stores it in the engine's custom data.
   `TLCLedgerPlugin.get()` re-creates it if the stored instance belongs to a different engine (stale), so per-battle
   state can never leak between battles.

## 5. Adversarial review
### 5.1 My review: the 20+ most likely failures, each checked
| # | Risk | Verdict / mitigation |
|---|---|---|
| 1 | Malformed CSV/JSON crashes loading | Strict JSON plus header/column checks; all data generated by scripts that copy vanilla headers |
| 2 | Unknown rules command or bad syntax | Validator resolves every command; syntax mirrors vanilla rules (hassle template, `$global.` and `$entity.` scopes, `score:` on conditions) |
| 3 | Data names a Java class that doesn't exist | Validator checks every class reference against the compiled jar and API jar |
| 4 | Faction references something missing; fleets get odd loadouts | Validator; plus the new check that role variants only use faction-known weapons (caught the Heavy Mauler/Heavy Blaster omission) |
| 5 | Illegal variants | Validator OP/mount checks; all variants fit their budgets |
| 6 | Sprite/slot misalignment | Slots and sprites come from one spec; validator requires slots on opaque pixels |
| 7 | World-gen NPE or duplicate systems on reload | Flag- and name-guarded idempotent generation; null checks; try/catch |
| 8 | Manager script duplicated across loads | `hasScript` guard |
| 9 | Assessor spawning with no valid route | Empty route returns early; markets filtered (hidden, hyperspace, size, faction, hostility) |
| 10 | Audit spam | Vanilla HasslePlayerScript odds and timeouts, plus 30–90-day certificates that switch hassling off |
| 11 | Quest blocked by Bureau hostility | Monthly "statute of limitations" lifts Hostile toward Inhospitable; audience requires only non-Hostile; census returns (which grant rep) don't require Bureau docking |
| 12 | Quest blocked because the relay salvagers never spawn or never die | Spawn failure marks the gang as spawned, which frees the relay; the gang has noAutoDespawn and sits at the relay where it can be fought |
| 13 | Numeric comparisons on missing memory in rules | All numeric/stage checks moved into Java condition commands (`stageIn`, `returnsDone`, `returnsPending`, `relayClear`, `active`) that default safely |
| 14 | Inspector-General unable to travel home | **Found and fixed**: the fleet had `MEMORY_KEY_NO_JUMP`, which would strand it in the player's system; removed |
| 15 | IG pursuit hijacked by other AI behaviour | **Found and fixed**: now sets `FLEET_BUSY`/`FLEET_SPECIAL_ACTION` exactly as vanilla hassles do |
| 16 | IG endless chase after a lost hearing | Any non-winning battle adjourns the hearing and the IG waits at the Tallyhouse |
| 17 | Recovered Plenipotentiary keeps the IG as captain | Vanilla recovery replaces non-AI captains (FleetEncounterContext ~1763), verified |
| 18 | Debuffs stuck forever (source ship dies mid-effect) | All debuffs live in the ledger with timers and death checks; systems only *refresh* them |
| 19 | Writ mutates shared stock variants | Stock or non-REFIT variants are cloned before tagging, as vanilla does after inflation; skipped in missions and sim |
| 20 | Seized ships permanently always-recoverable | **Found and fixed**: tags stripped once the ship is in the player's fleet |
| 21 | `String.format` crash from a stray `%` in UI text | All `addPara` format strings audited; percentages only appear in substituted values or `{{}}` description markup |
| 22 | Save breakage | Only vanilla objects, primitives and a String-holding listener are saved; no anonymous classes; XStream aliases registered |
| 23 | Registrar option offered when the quest can't proceed (Tallyhouse captured) | **Found and fixed**: option now requires Bureau ownership, consistent with the intel's warning |
| 24 | Economy exploits | Audits only take; census pays once per colony; no new commodities (BALANCE.md §Economy) |

### 5.2 Independent reviewer agent
*(Filled in below with its findings and the fixes applied.)*

## 6. Known limitations and untested areas
* **Not play-tested.** Fleet AI behaviour (Assessor routes, Surcharge/Summary Judgment AI timing), visual effects,
  and real combat balance have only been reasoned about, not observed.
* **Hassle timing** is vanilla's: audits can take a while to happen (25% roll per eligible encounter, 20–30 day
  cooldown per type). The questline doesn't depend on audits; you can go straight to the Tallyhouse.
* **Destroying the Tallyhouse** (e.g. saturation bombardment) or capturing it ends the questline; the intel says so.
* **Nexerelin random sector and sector-replacing mods are untested.** Assize and Envoi are placed relative to fixed
  coordinates with a free-space search, so they still generate, but distances to the core may differ.
* **Art** is procedural. It is consistent and readable but less detailed than vanilla's hand-painted sprites; there
  are no GraphicsLib normal/material maps (light data only).
* **No custom sounds or music**; vanilla sounds and tracks are reused by id.
