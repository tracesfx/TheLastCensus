# The Last Census — Design Document

## 1. Concept shortlist and critique

| # | Concept | Originality | Fits Starsector tone | Implementable in budget (and verifiable without playtesting) | Fun |
|---|---|---|---|---|---|
| 1 | **The Last Census** — a Domain bureaucracy (an automated audit office) wakes on schedule at game start and begins auditing a Sector that has forgotten it. Audits, census contracts, writs that *seize* ships, a dead empire's paperwork. | High. No mod I know of turns *bureaucracy* into mechanics. | Excellent: dry deadpan surface, melancholy core (a faithful machine counting the dead for an empire that will never read the report). | High. Mostly campaign logic (rules.csv, intel, fleet scripts) that I can verify by reading code; combat effects are simple stat/flag changes. Automata suit procedural sprites. | Audits create memorable encounters with real choices, the Writ makes capturing ships easier, there is a short questline with an ending, and a secret boss. |
| 2 | **Tethermen** — a tug guild that hauls megastructures; tether-harpoon physics in combat; moving convoys in the campaign. | High | Good (industrial) | **Low** to verify. Physics tethers and AI interplay can't be validated without playtesting, so the risk of janky combat is high. | High if it works |
| 3 | **The Choir** — a fleet-wide flux network where linked ships share hard flux and overloads cascade. | Medium | Medium | Medium. Balance is untestable, and the campaign side is thin. | Combat only |
| 4 | **Ember** — a star collapses over the campaign; evacuations, changing markets, a nova event. | High | Excellent | Medium-low. Runtime star/planet type changes are risky to ship unseen. | Story-heavy, easy to miss |
| 5 | **Kintsugi Yards** — gild D-mods into bonuses; ships grow stronger as they break. | Medium (D-mod-positive mods exist) | Good | High | Narrow appeal |
| 6 | **Lamplighters** — relight dead hyperspace beacons to carve safe lanes through storms. | Medium-high | Good | Low (hyperspace terrain manipulation) | Moderate |

**Decision: Concept 1, "The Last Census".** It is the strongest single idea that can be expressed at once through
mechanics (audits, writs, liens), visuals (ivory-and-jade Domain office automata), writing (statute-quoting machines,
census returns generated from the real state of each colony) and quests (the census and what to do with it). It is also
the concept whose correctness I can best guarantee without being able to launch the game.

## 2. Hook
> *The Domain is gone. Its paperwork isn't.*

On the first day of the campaign, an administrative station at the northern edge of the Persean Sector wakes from a
dormancy that lasted the entire post-Collapse era. Its statutory dormancy period has expired, so the Domain Bureau of Colonial
Assessment resumes the **Grand Audit**: a census of every colony and a registry check of every vessel in the Sector.
Its Assessor cutters fan out into a Sector that has never heard of them, hailing captains, demanding manifests,
renewing registrations that lapsed two hundred cycles ago, and occasionally seizing a ship.

## 3. Theme and tone
- **Surface:** deadpan bureaucratic precision. Statute numbers, late fees, certificates and receipts. The humour lives
  entirely in the *straight face*; nothing winks at the player.
- **Core:** melancholy. The Bureau's records list colonies that died in the Collapse, and its census will be transmitted
  to a Domain that cannot receive it. Everyone except the Bureau knows this.
- **Visual language:** Domain civil-service automata. Aged ivory plating, ledger-jade trim, dark slate structure,
  brass fittings, small amber running lights. Blocky, symmetrical, modular hulls with sensor domes (the "eye" of the assessor).
- **Naming convention:** Bureau hardware is named for legal and fiscal instruments (Writ, Subpoena, Accrual, Injunction,
  Foreclosure; Tally, Assessor, Magistrate, Exchequer). Places are named for legal states (Assize, Abeyance, Escrow, Docket, Envoi).

## 4. Lore bible
- **The Domain Bureau of Colonial Assessment ("the Bureau").** The Domain civil agency for colonial census, tithe assessment and
  the registry of vessels and charters. It ran semi-autonomous offices in each sector, staffed by small human
  audit teams and a licensed administrative intelligence.
- **The Tallyhouse.** The Bureau's Persean regional office, a station orbiting the gas giant **Abeyance** in the **Assize**
  system, north of the core worlds. When the Gates failed, its last commissioner put the office into statutory dormancy
  "pending restoration of contact or expiry of the dormancy period, whichever comes first". The staff left. The period has now expired.
- **The Registrar of Assize.** The Tallyhouse's administrative intelligence: courteous, punctilious and literal, and faintly
  aware that something is wrong. It addresses the player by legal status ("unregistered master of vessels"). It will not
  accept "the Domain is gone" without documentation, because the Bureau's records contain no such entry.
- **Assessors.** Automated audit cutters that fly circuits between colonies. Their protocol: hail, request the manifest,
  assess the levy, seize contraband, issue a certificate. They fight only when refused, and when they fight they try to *seize* rather than destroy.
- **The Inspector-General.** The Bureau's internal-affairs intelligence, patterned on and named after the last human
  Inspector-General of the Persean office, **Ismene Varga**. It wakes only when a discrepancy is escalated, for example when
  the same captain keeps telling Assessors that the Domain no longer exists.
- **The Courier Relay at Envoi.** The Bureau's dedicated transmitter for returns bound for Domain Central, on the far
  side of a dim red star. Pirate salvagers have been stripping it.
- **The Dead Letter Office.** A derelict mail-sorting annex in Assize's outer dark, holding two centuries of undelivered
  Domain correspondence, including a sealed letter from the last commissioner, **Adaeze Okafor**, addressed to the Registrar.
- **Politics.** The Bureau has no record of the Hegemony as a Domain instrumentality and lists it as "an unregistered
  polity of uncertain standing"; the Hegemony, for its part, does not care for AI-run Domain relics (inhospitable).
  Pirates and the Luddic Path refuse audits on sight (hostile). Tri-Tachyon would very much like the Registrar's core (suspicious).
  Everyone else is merely confused (neutral).

## 5. Content list
### Faction
- `tlc_bureau`, the **Assessment Bureau**, with custom logo and crest. No human officers: Bureau personnel are automata (AI portraits, "ai" name set).

### Worlds
- **Assize** (orange star, north of the core ≈ 3–4 LY from Zagan): Docket (barren), Abeyance (gas giant) with the
  **Tallyhouse** (size 4 Bureau market: open + military market, no black market), Escrow (frozen), an asteroid belt
  (the Margins), a Bureau comm relay, and the hidden **Dead Letter Office**.
- **Envoi** (red dwarf, further north-east): a dead rock and the **Courier Relay**.
- Market condition `tlc_automated_admin` (Automated Administration).

### Ships (custom procedural sprites)
| Hull | Size | Role / identity | System |
|---|---|---|---|
| Tally | Frigate | Fast census cutter; Writ carrier; light energy | Maneuvering Jets (vanilla) |
| Assessor | Destroyer | Iconic audit cutter; mixed ballistic/energy | **Surcharge** (custom) |
| Magistrate | Cruiser | Line adjudicator; large energy spine | **Surcharge** (custom, wider) |
| Exchequer | Capital | Armoured treasury battleship with a huge hold | Fortress Shield (vanilla) |
| Plenipotentiary | Cruiser (unique) | The Inspector-General's flagship; secret reward | **Summary Judgment** (custom) |

### Weapons
| Weapon | Mount | Mechanic |
|---|---|---|
| Writ Projector | S energy beam | **Writ of Seizure**: a ship destroyed while under a writ is guaranteed recoverable after battle |
| Subpoena SRM | S missile | Guided EMP-heavy missile that disables a subsystem |
| Accrual Autocannon | M ballistic | **Compound interest**: consecutive hits on the same target deal escalating bonus damage |
| Injunction Emitter | M energy | On hit, suppresses the target's weapon rate of fire for a few seconds |
| Foreclosure Battery | L energy | Bonus damage against high-flux targets |

### Hullmod
- **Assessor Protocols** (built into all Bureau hulls), **Lien & Settlement**: damage this ship deals to an enemy is
  recorded as a lien. When that enemy is destroyed, every lienholder is *settled*: it instantly sheds flux in proportion to its share.

### Campaign systems
1. **Audits.** Up to 3 Assessor fleets roam between core markets via the vanilla hassle framework. Audit choices: comply
   (registration levy, contraband seized, AI cores "registered" for a fee, 90-day certificate), show the Enumerator's
   warrant (exempt), lie with a story point (exempt), say "There is no Domain." (recorded…), or refuse (rep loss, and a fight if they are stronger).
2. **Questline "The Last Census"** (intel-tracked):
   0. *Unregistered Transmission*: from day 3 the player has intel on the Grand Audit broadcast, pointing to Assize.
   1. *Report to the Tallyhouse*: an audience with the Registrar; accept the **Provisional Enumerator's warrant**.
   2. *Census Returns*: file returns at 3 inhabited markets. Each return is generated from that market's real state
      (size, faction, conditions) and pays credits and Bureau standing. Returns stay repeatable (once per market) for pay.
   3. *The Courier Relay*: drive off the pirate salvagers at Envoi and reactivate the relay.
   4. *Transmission*: the census goes out into the dark. Silence. The Registrar asks whether anyone is listening.
      - **"No. The Domain is gone."**: the audit ends and Assessors are recalled. Reward: the Bureau Charter blueprint package and a Magistrate.
      - **"Someone will be. Keep counting."**: the audit continues and the player becomes *Commissioner* (never audited again).
        Reward: an Exchequer and a commission payment.
      - Extra dialogue if the player carries the Okafor letter and/or the Inspector-General's finding.
3. **Hostility amnesty ("statute of limitations")**: if the player is hostile to the Bureau, standing creeps back toward
   "inhospitable" once a month, so the questline can never be permanently locked.

### Secrets
- **The Inspector-General** (main secret): tell three different Assessor audits "There is no Domain." The discrepancy is
  escalated and the Inspector-General comes to hold a hearing. The only evidence it will accept is a test of the hypothesis:
  "If the Domain stood, an unregistered fleet could not defeat me." Defeat it and its flagship, the **Plenipotentiary**, is
  guaranteed recoverable. The finding unlocks extra dialogue at the end of the questline.
- **The Dead Letter Office** (minor secret): an undiscovered derelict in Assize's outer orbit. Read random undelivered
  Domain letters, recover a sealed letter to the Registrar (alternate ending text), and a cache of Bureau weapons.

### Settings (LunaLib)
- Enable audits of the player fleet (default on).
- Maximum concurrent Assessor fleets (0–6, default 3).

## 6. Scope budget and priority
**MUST** (no release without): faction, Assize system and market, 4 faction hulls with variants and sprites, 5 weapons,
Assessor Protocols, Surcharge, Writ of Seizure, Assessor fleets with audits, questline stages 0–4 with both endings, the
Inspector-General secret (Plenipotentiary hull and Summary Judgment), descriptions, build script, validator, and all docs.

**SHOULD:** Dead Letter Office and letter, LunaLib settings, custom station/relay sprites, Registrar portrait, hostility amnesty.

**STRETCH:** Process Server fighter wing for the Exchequer, GraphicsLib light data, custom sounds, more audit vignettes.

**Cut rules:** If time runs short, cut STRETCH, then the Dead Letter Office cache, then the Registrar portrait (fall back to
a vanilla AI portrait). Never cut validation or docs.

## 7. Technical plan
- **Mod id** `the_last_census`, **prefix** `tlc_` on every id, Java package `tlc.*`.
- **Dependencies:** LazyLib (`lw_lazylib`) and LunaLib (`lunalib`), both installed. GraphicsLib and MagicLib are not needed.
- **Build:** `build.sh`: javac `--release 17` against `starfarer.api.jar` plus core libs, LazyLib and LunaLib jars → `jars/TheLastCensus.jar`. Fails loudly.
- **World gen:** `onNewGame` generates Assize and Envoi when they are missing. `onGameLoad` performs the same idempotent
  generation for existing saves (guarded by a sector memory flag) and (re)registers scripts. Markets are added to the economy in code.
- **Scripts:** `TLCAssessorManager` (EveryFrameScript, sector), `TLCCensusIntel` (BaseIntelPlugin), and rule commands
  `TLCAuditCMD` and `TLCCensusCMD` (package `tlc.rulecmd`, registered via `ruleCommandPackages`). The Inspector-General uses a
  fleet event listener. All transient combat state lives in combat-engine custom data; nothing stores combat objects in the campaign.
- **Combat:** one `TLCLedgerPlugin` (EveryFrameCombatPlugin, added lazily by the hullmod or weapons) tracks liens, writs
  and timed debuffs, with a 0.1 s interval for death checks and no per-frame allocation in the hot path.
- **Save safety:** only ids, primitives and vanilla objects (fleets, entities, intel) are stored in memory or intel; XStream aliases go in `configureXStream`.
- **Validation:** `tools/validate.py` runs on every build (see VERIFICATION_REPORT.md).

## 8. Risk list
| Risk | Mitigation |
|---|---|
| Can't launch the game to test | Exhaustive static validator, javac against the real API, line-by-line traces of startup and new-game hooks, adversarial review ×2 |
| rules.csv mistakes (unreachable options, broken conditions) | Mirror the vanilla hassle template exactly; the validator checks rule option/trigger consistency and that every custom command exists |
| Tagging shared stock variants (Writ) | Clone the variant before tagging, exactly as vanilla does post-inflation |
| Assessor fleets clogging the economy or lagging | Hard cap (≤6), simple assignments, despawn when the route ends |
| Quest soft-locks | No time limits on main stages; amnesty for hostility; relay pirates are respawned if despawned without being beaten; every stage reachable without combat luck |
| Sprite/slot misalignment | Slots are defined in the generator spec, which writes the PNG and the slot coordinates together; the validator checks bounds |
| Economy exploits | No buy-back loops: census pays once per market; audits only cost the player; no new commodities |
| Balance | Every number compared to vanilla baselines in BALANCE.md; identities through trade-offs |

## 9. Time plan (≈ autonomous session)
Recon 15% → Design 5% → Foundation (build, validator, skeleton) 10% → Art generator and sprites 15% → Data slice
(faction, ships, weapons) 15% → Combat Java 10% → Campaign Java and rules 15% → Verification and adversarial review 10% → Polish and docs 5%.
