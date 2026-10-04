# DEV NOTES — The Last Census (full spoilers)

## 1. Everything the mod adds, and where it lives

| Content | Where in game | Files |
|---|---|---|
| Faction **Assessment Bureau** (`tlc_bureau`) | Owns the Tallyhouse; Assessor circuits fly through the core | `data/world/factions/tlc_bureau.faction`, `tools/gen_data.py` |
| **Assize** system (orange star) | Hyperspace ≈(-1800, 9800), about 3.5 LY north of Zagan (shifted if another system is in the way) | `src/tlc/world/TLCWorldGen.java` |
| **The Tallyhouse** (size-4 Bureau station, orbits the gas giant Abeyance) | Assize | market `tlc_tallyhouse_market`, entity `tlc_tallyhouse_station` |
| Planets Docket, Abeyance, Escrow; the Margins asteroid belt; Bureau comm relay and nav buoy | Assize | |
| **Dead Letter Office** (hidden derelict) | Assize, orbit radius 14,500, *discoverable*: only detected within roughly 1,500 su | entity `tlc_dead_letter_annex` |
| **Envoi** system (red dwarf) with the **Bureau Courier Relay** | ≈5200, 3600 from Assize (north-east) | entity `tlc_envoi_relay` |
| Hulls: Tally, Assessor, Magistrate, Exchequer (+ secret Plenipotentiary) | Bureau military market (rep-gated), Bureau fleets, quest rewards | `data/hulls/*`, `graphics/ships/*` |
| Weapons: Writ Projector, Subpoena SRM, Accrual Autocannon, Injunction Emitter, Foreclosure Battery | Bureau markets (weapons sell frequency boosted), Bureau ships, Dead Letter Office cache | `data/weapons/*` |
| Hullmod **Assessor Protocols** (built into Bureau hulls, hidden) | | `TLCProtocols`, `TLCLedgerPlugin` |
| Systems **Surcharge**, **Summary Judgment** | Assessor/Magistrate; Plenipotentiary | `src/tlc/systems/*` |
| Market condition **Automated Administration** (+2 stability) | The Tallyhouse | `TLCAutomatedAdminCondition` |
| Blueprint package **Bureau Charter Archive** | Reward from ending A | `data/campaign/special_items.csv` |
| Intel: *Unregistered Transmission / The Last Census*, *Office of the Inspector-General* | Intel tab, Story tag | `TLCCensusIntel`, `TLCHearingIntel` |

## 2. How each system works

### 2.1 Assessor circuits (`TLCAssessorManager`, sector script)
* Up to **3** circuits (LunaLib, 0–6), one dispatched every ~7 days (±25%) from the Tallyhouse. The first leaves on day 1.
* Each circuit is a Bureau fleet of 30–60 FP (+10 per in-game year after 206, max +40), quality 0.8, with no officers.
  The commander is an "Assessor Unit ###" persona.
* Route: 2–3 random non-Bureau colonies of size ≥3 that are not hostile to the Bureau (player colonies weighted ×1.5),
  visited nearest-first. At each it stops for 4–8 days ("conducting an assessment of X"), then returns home and despawns.
* Audits use the **vanilla hassle framework**. The manager sets `$willHasslePlayer` and `$hassleType = tlc_audit` on
  circuit fleets, and vanilla `HasslePlayerScript` decides when one approaches you (only in star systems, within
  2000 su, 25% roll per check, 20–30 day cooldown per hassle type). The manager switches hassling off while you hold a
  **certificate** (`$tlc_certified`), are **Commissioner**, after ending A, or if audits are disabled in LunaLib.
* **Statute of limitations:** every 30 days, if your standing with the Bureau is Hostile or worse, it rises by 0.15
  (to at most −0.45, Inhospitable), with a campaign message. Hostility can never permanently lock the quest.

### 2.2 The audit (`TLCAuditCMD` + rules `tlc_audit*`)
Levy = 250 × ships (min 500, max 6000), plus 500/1000/2000 per gamma/beta/alpha core in cargo.

| Choice | Effect |
|---|---|
| Transmit manifest and pay | Pay the levy; drugs and organs confiscated; 90-day certificate; +2 rep (limit Welcoming). **The first compliant audit invites you to the Tallyhouse** (stage *broadcast* → *report*). |
| Explain you can't pay | Shown when credits < levy. Contraband still confiscated; 30-day certificate; no rep. |
| Present your warrant | Only if Provisional Enumerator. Free; 90-day certificate; +1 rep. |
| "Statute 14(c)" (lie) | Costs a story point; free; 60-day certificate. |
| "There is no Domain." | Once per audit. Increments `$tlc_noDomainCount`; the 3rd separate time opens the secret (§4.1). You stay in the audit afterwards. |
| Refuse | −3 rep. If the Assessors are as strong as you or stronger: they turn hostile to "impound" you (low rep impact for the fight). If weaker: −2 rep and they let you go. |

### 2.3 Questline "The Last Census"
State is in sector memory (`$tlc_stage`, `$tlc_returnsFiled`, `$tlc_enumerator`, `$tlc_relayActive`, ...) and the
intel just displays it.

| Stage | How to advance | Notes |
|---|---|---|
| **broadcast** | Intel appears on day ~3 ("Unregistered Transmission"), pointing at Assize. Either comply with any audit, or dock at the Tallyhouse and *Request an audience with the Registrar*. | The Registrar can be met at any stage. |
| **report** | Ask the Registrar: *"I will serve as an enumerator."* | You receive the Provisional Enumerator's warrant. |
| **returns** | Dock at 3 colonies (size ≥3, not Bureau, not player-owned) and choose *File a Bureau census return for this colony*. | Each return is generated from that colony's real conditions and pays 1000 × size (+1500 for the three quest returns), +1 rep (limit Friendly). Each colony can be filed once, forever. Filing stays available (and paid) afterwards while you hold the warrant. |
| **relay** | Back at the Registrar: *"I have filed the returns..."*. A pirate *Relay Salvage Gang* (80% of your FP, 50–180) spawns at the Envoi relay. Destroy or drive it off, then interact with the relay: *Install the Registrar's transmission key*. | The relay refuses activation while any salvage-gang fleet is in Envoi. If the gang can't spawn, the relay is simply free. |
| **transmit** | Registrar: *"The relay at Envoi is online."* The census is sent; silence; the Registrar asks whether anyone is listening. | |
| **done** | Choose an ending (below). | Intel moves to completed. |

**Endings**
* **A, "No. The Domain is gone."** The Grand Audit closes and all Assessor circuits are recalled and despawn. You get the
  **Bureau Charter Archive** blueprint package (all four Bureau hulls and five weapons) and a Magistrate
  (*DBV Countersigned*). Rep +30 (limit Cooperative). The warrant is retired. The Tallyhouse stays open.
* **B, "Someone will be. Keep counting."** The audit continues. You become **Commissioner** and are never audited
  again. You get an Exchequer (*DBV Close of Accounts*) and 100,000 credits. Rep +30 (limit Cooperative). Census
  filing stays available.
* **A′, "Your Inspector-General already ruled on that."** Only appears if the IG secret was completed. Same rewards as
  A, with different dialogue.
* If you delivered the **Okafor letter** (§4.2), both endings and the transmission scene gain extra lines.

### 2.4 Combat mechanics (all bookkeeping in `TLCLedgerPlugin`, one per battle, registered in `settings.json`)
* **Writ of Seizure (Writ Projector):** while a Writ beam is fully on an enemy ship (not fighters), the ship is "under
  writ" ("WRIT SERVED" text). If it becomes a hulk within **3 s** of the last writ tick, it is **SEIZED**: in campaign
  battles its fleet member's variant is cloned (if stock) and tagged `always_recoverable`, so it is always offered for
  recovery if you win. Station modules are excluded. Once a seized ship has joined your fleet, the sector script strips the
  tags again, so the guarantee covers only the battle in which the writ was served.
* **Lien & Settlement (Assessor Protocols):** every Bureau ship's damage to each enemy is tallied (hull + armour +
  shield damage). When that enemy becomes a hulk, each surviving lienholder dissipates flux equal to **50%** of what it
  dealt, capped at **30%** of its own capacity, hard flux first ("Lien settled").
* **Accrual Autocannon:** per weapon, consecutive hits on the same ship within 2 s add a stack (max 10). Each stack
  adds +5% damage to subsequent shots.
* **Injunction Emitter:** on hit, the target gets −20% ballistic/energy/missile rate of fire and −20% beam damage for
  4 s. Refreshes; does not stack.
* **Foreclosure Battery:** on hit against a ship at ≥50% flux, a follow-up energy hit for +50% of the shot's damage
  ("FORECLOSED").
* **Surcharge:** 6 s; enemies within 800 su (1000 su for cruisers and capitals) get +35% weapon flux cost and +15%
  shield damage taken. The debuff is refreshed every frame with a 0.25 s timer, so it ends even if the caster dies.
  The AI fires it when enough enemy tonnage is in range.
* **Summary Judgment:** 8 s on the locked target within 1200 su: blocks the vent command every frame, +25% shield
  damage taken. The AI fires it on targets above 45% flux.

## 3. Bureau market
The Tallyhouse sells Bureau hulls and weapons through its military market (vanilla rep gating) and a normal open
market. It has no black market. Docking is possible at any standing better than Hostile (trade is disabled at
Inhospitable, as in vanilla), and the Registrar audience needs the same.

## 4. Secrets

### 4.1 The Inspector-General (main secret)
* **Trigger:** answer **"There is no Domain."** at three *different* audits. The third Assessor refers the
  discrepancy to the Office of the Inspector-General (`$tlc_igState = referred`).
* The next time you are in a star system and not in a dialog (and not hostile to the Bureau), the IG's fleet arrives
  about 1700 su away and pursues you to talk. The fleet is the **Plenipotentiary** *DBV Final Reading* (Inspector-General
  Ismene Varga, level-7 officer) with 2 Magistrates, 2 Assessors and 2 Tallies. A *Office of the Inspector-General*
  intel entry is added.
* The hearing: the IG states her hypothesis: *if you can defeat me, the Domain is not standing behind me.*
  * **"Proceed."** The fleet turns hostile (no rep impact) and the battle begins.
  * **"Not today."** The IG adjourns and waits in orbit at the Tallyhouse indefinitely. Interact with her fleet there
    to reopen the hearing. Leaving the system before she reaches you has the same effect.
* **Win** (the Plenipotentiary destroyed or disabled): finding filed, *Domain contact presumed lost*
  (`$tlc_igState = ruled`). The Plenipotentiary is **always recoverable**, and it is the only copy in the game. The
  rest of her fleet goes home. This unlocks ending A′.
* **Lose or retreat:** the hearing is adjourned and she waits at the Tallyhouse for a rematch.
* Needs audits enabled (LunaLib) to trigger.

### 4.2 The Dead Letter Office (minor secret)
* A derelict annex far out in Assize (orbit 14,500). It is not on the map until your sensors pass within about
  1,500 su. The Registrar's answer to *"Do you know what happened to the Domain?"* hints at it ("the correspondence
  annex in the outer system").
* **Read an undelivered letter:** ten hand-written vignettes, each shown once, in random order.
* **Search the rest of the annex** (once): an undelivered armoury consignment (2× Foreclosure, 4× Writ, 2× Accrual)
  and a sealed letter to the Registrar from the last Commissioner, Adaeze Okafor.
* Deliver it at the Registrar (*Give the Registrar the sealed letter*) to hear it read aloud. It explains why the
  dormancy period was 206 cycles, and it changes lines in the transmission scene and both endings.

## 5. Testing tips (Console Commands is installed)
```
jump Assize                       # teleport to the Bureau's system, then:
goto The Tallyhouse
jump Envoi                        # relay system
addship tlc_exchequer_Standard    # also tlc_tally_Standard, tlc_assessor_Standard, tlc_magistrate_Standard, tlc_plenipotentiary_Standard
addweapon tlc_writ 4              # tlc_subpoena, tlc_accrual, tlc_injunction, tlc_foreclosure
addspecial tlc_bureau_package
setrelation tlc_bureau player 50  # make the military market accessible
reveal                            # campaign: infinite sensor range (finds the Dead Letter Office instantly)
```
Quest state can be poked with RunCode (sector memory):
```
runcode Global.getSector().getMemoryWithoutUpdate().set("$tlc_enumerator", true)
runcode Global.getSector().getMemoryWithoutUpdate().set("$tlc_stage", "returns")
runcode Global.getSector().getMemoryWithoutUpdate().set("$tlc_returnsFiled", 3)
runcode Global.getSector().getMemoryWithoutUpdate().set("$tlc_igState", "referred")   # summon the Inspector-General
runcode Global.getSector().getMemoryWithoutUpdate().unset("$tlc_certified")          # allow audits again
```
* To meet an Assessor quickly: check the intel map for Bureau fleets near core worlds, or park at a large core
  colony for a few days. Hassles need you to be visible and outside hyperspace.
* To test the Writ: fit Writ Projectors, finish an enemy while the beam is on it, and watch for **SEIZED**. Then win
  and check that the ship is offered for recovery.
* `starsector.log` lines from this mod are prefixed `TLC:`.

## 6. Code map
| Package | Purpose |
|---|---|
| `tlc` | `TLCModPlugin` (lifecycle), `TLCIds` (every id, validated), `TLCSettings` (LunaLib) |
| `tlc.world` | `TLCWorldGen`: idempotent generation of Assize, Envoi, the market and the Registrar |
| `tlc.campaign` | `TLCAssessorManager` (sector script), `TLCCensusIntel`, `TLCHearingIntel`, `TLCInspectorGeneral`, `TLCQuest`, `TLCCensusText`, `TLCFleetListener`, `TLCMem`, `TLCAutomatedAdminCondition` |
| `tlc.rulecmd` | rules.csv commands: `TLCAuditCMD`, `TLCRegistrarCMD`, `TLCCensusCMD`, `TLCHearingCMD` |
| `tlc.combat` | `TLCLedgerPlugin` + weapon effects |
| `tlc.hullmods`, `tlc.systems` | Assessor Protocols; Surcharge and Summary Judgment (stats + AI) |
| `tlc.compat` | Optional GraphicsLib light registration (loaded only when `shaderLib` is enabled) |

Tooling: `./build.sh` (compile + jar + validate), `tools/gen_data.py` (all CSV/JSON data and prose),
`tools/gen_rules.py` (rules.csv), `tools/gen_ships.py`/`gen_weapons.py`/`gen_misc.py` (art plus `.ship` files),
`tools/validate.py` (static QA).

## 7. Save notes
* Saved objects: `TLCAssessorManager` (fleet list + timers), the two intel objects (one fleet reference), and
  `TLCFleetListener` (a single string). All are aliased in `configureXStream`. No combat objects and no anonymous
  classes are stored.
* Existing saves get the systems on first load (guarded by `$tlc_generated`). Removing the mod from a save is not supported.
