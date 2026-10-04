# Recon Notes — The Last Census

Notes taken while studying the local install before writing any content. Everything here was
verified against files on disk (vanilla `starsector-core`, the API source zip, installed mods).

## Environment
- Game: **Starsector 0.98a-RC7** (from `starsector.log`: "Starting Starsector 0.98a-RC7 launcher").
- Runtime: bundled `jre/` is **Azul Zulu 17.0.10** (`jre/release`). `vmparams` launches with Java 17 flags.
- `starfarer.api.jar` classes are **class-file major 61 (Java 17)** → compile with `javac --release 17`.
- JDK on PATH: Temurin `javac 17.0.20.1`. Also present: JDK 8, JDK 21 (not used).
- Python 3.14.7 with Pillow 12.3.0 and numpy 2.5.3 (sprite generation, validator).
- API sources: `starsector-core/starfarer.api.zip` (1947 .java files incl. all of `impl`). Extracted to scratch for grepping.

## Installed libraries (ids from each mod_info.json)
| Mod | id | version |
|---|---|---|
| LazyLib | `lw_lazylib` | 3.0.0 |
| LunaLib | `lunalib` | 2.0.4 (depends on LazyLib) |
| GraphicsLib | `shaderLib` | 1.10.2 |
| MagicLib | `MagicLib` | 1.5.6 |
| Console Commands | `lw_console` | 4.0.9 |
| Additional Console Commands | `console_additions` | 1.3.16 |

LunaLib settings API (javap): `lunalib.lunaSettings.LunaSettings.getBoolean/getInt/getFloat(String modId, String fieldId)`
return boxed (nullable) values. Settings are declared in `data/config/LunaSettings.csv` with header
`fieldID,fieldName,fieldType,defaultValue,secondaryValue,fieldDescription,minValue,maxValue,tab`.

## mod_info.json / jars / settings
- mod_info: `id, name, author, version, description, gameVersion, jars[], modPlugin, dependencies[{id,name}]`.
- Custom rules.csv commands are found by simple class name in packages listed in
  `data/config/settings.json` → `"ruleCommandPackages": [...]` (vanilla + LunaLib + Console do this).
- Merging: mod `data/config/*.json`, `default_ship_roles.json`, CSVs are merged with vanilla by id.

## Ships
- `ship_data.csv` header (58 cols): `name,id,designation,tech/manufacturer,system id,fleet pts,hitpoints,armor rating,max flux,8/6/5/4%,flux dissipation,ordnance points,fighter bays,max speed,acceleration,deceleration,max turn rate,turn acceleration,mass,shield type,defense id,shield arc,shield upkeep,shield efficiency,phase cost,phase upkeep,min crew,max crew,cargo,fuel,fuel/ly,range,max burn,base value,cr %/day,CR to deploy,peak CR sec,CR loss/sec,supplies/rec,supplies/mo,c/s,c/f,f/s,f/f,crew/s,crew/f,hints,tags,logistics n/a reason,codex variant id,rarity,breakProb,minPieces,maxPieces,travel drive,number`
- DP shown in game = `supplies/rec` column; `fleet pts` is the FP used by fleet gen.
- `.ship` JSON: `hullId, hullName, hullSize, spriteName, width, height, center[x_from_left, y_from_bottom], collisionRadius, shieldCenter, shieldRadius, bounds[] (flat x,y list), engineSlots[], weaponSlots[], style, viewOffset, builtInMods/builtInWeapons (optional)`.
- **Ship-local coords**: `+x = forward (toward sprite top)`, `+y = left (toward sprite's left edge)`.
  From image pixel (px from left, py from top): `x = (H - py) - cy`, `y = cx - px`. Angles CCW from forward (+ = left).
  Verified on hammerhead.ship (108x164, center 54,71; nose-side slots at x≈84, engines at x≈-70, left-side turret at +y with +45°).
- Weapon slot: `id, type (BALLISTIC/ENERGY/MISSILE/HYBRID/SYNERGY/COMPOSITE/UNIVERSAL/...), size, mount (TURRET/HARDPOINT), angle, arc, locations[x,y]`.
- Engine slot: `location, angle (180 = aft), length, width, contrailSize, style` (style id from engine_styles.json or `CUSTOM` + `styleSpec`).
- Skins (`data/hulls/skins/*.skin`): `baseHullId, skinHullId, hullName, spriteName, builtInMods, removeWeaponSlots…`.
- Variants: `variantId, hullId, displayName, fluxVents, fluxCapacitors, hullMods[], permaMods[], sMods[], goalVariant, weaponGroups[{mode, autofire, weapons{slotId: weaponId}}]`.
- Vanilla roles live in `data/world/factions/default_ship_roles.json` (`combatSmall/Medium/Large/Capital`, `freighterSmall`, …);
  mods add their variant ids to these roles (merged). Only factions that *know* the hull use them.

## Weapons
- `weapon_data.csv` header: `name,id,tier,rarity,base value,range,damage/second,damage/shot,emp,impact,turn rate,OPs,ammo,ammo/sec,reload size,type,energy/shot,energy/second,chargeup,chargedown,burst size,burst delay,min spread,max spread,spread/shot,spread decay/sec,beam speed,proj speed,launch speed,flight time,proj hitpoints,autofireAccBonus,extraArcForAI,hints,tags,groupTag,tech/manufacturer,for weapon tooltip>>,primaryRoleStr,speedStr,trackingStr,turnRateStr,accuracyStr,customPrimary,customPrimaryHL,customAncillary,customAncillaryHL,noDPSInTooltip,number`
- `.wpn`: `id, specClass (projectile|beam), type, size, turretSprite, hardpointSprite, (+Glow/Gun sprites), turretOffsets, hardpointOffsets, *AngleOffsets, barrelMode, animationType, muzzleFlashSpec, projectileSpecId, fireSoundOne/Two`; beams add `fringeColor, coreColor, width, textureType, collisionClass, beamEffect`.
- Effect hooks: `beamEffect` (BeamEffectPlugin, in .wpn), `onFireEffect` (in .wpn), `everyFrameEffect` (in .wpn), `onHitEffect` (OnHitEffectPlugin, in .proj).
- `.proj` for ballistic/energy shots: `id, specClass:projectile, spawnType (BALLISTIC|BALLISTIC_AS_BEAM|PLASMA|...), collisionClass, length, width, fadeTime, fringeColor, coreColor, bulletSprite…`; missiles: `specClass:missile, missileType:MISSILE, sprite, size, center, engineSpec, engineSlots`.
- **Sprite anchoring**: turret and hardpoint sprites are both centered on the slot; muzzle offsets are measured from
  sprite center. Evidence: heavy mortar hardpoint 26x44 with `hardpointOffsets` 22 (= H/2), ion cannon hardpoint 28x36 with 18 (= H/2).
  So hardpoint art = breech in the lower half, barrel to the top edge.
- Vanilla sprite sizes: wolf 52x96, hammerhead 108x164, eagle 168x218, onslaught 288x384; small turret 24–36px, medium 44px, large 72px.

## Hullmods / systems
- `hull_mods.csv`: `name,id,tier,rarity,tech/manufacturer,tags,uiTags,base value,unlocked,hidden,hiddenEverywhere,cost_frigate,cost_dest,cost_cruiser,cost_capital,script,desc,short,sModDesc,sprite`.
- Hullmod class extends `BaseHullMod` (`applyEffectsBeforeShipCreation`, `applyEffectsAfterShipCreation`, `advanceInCombat`, `getDescriptionParam`, `addPostDescriptionSection`).
- `ship_systems.csv` + `.system` JSON: `id, type (STAT_MOD…), aiType, statsScript`; custom AI = `"aiType":"CUSTOM", "aiScript":"fqcn"` (vanilla dweller/threat systems do this).
  Stats script extends `BaseShipSystemScript` (`apply/unapply/getStatusData`). AI implements `ShipSystemAIScript`.
- Combat listeners: `ship.addListener(DamageListener)` reports damage **taken** by that ship with the source object
  (see ChiralFigmentStats). `DamageDealtModifier`/`DamageTakenModifier` modify pre-application damage.

## Ship recovery (for the "Writ of Seizure" mechanic)
- `FleetEncounterContext` (post-battle) checks `member.getVariant().hasTag(Tags.VARIANT_ALWAYS_RECOVERABLE)` ("always_recoverable"):
  such ships skip the random "not recoverable" roll and `Misc.isShipRecoverable` returns true.
- Stock variants are shared objects → **clone before tagging** (`variant.clone(); setSource(VariantSource.REFIT); member.setVariant(v,false,false)`), as vanilla does after inflation.

## Campaign
- ModPlugin lifecycle: `onApplicationLoad, onNewGame, onNewGameAfterProcGen, onNewGameAfterEconomyLoad, onNewGameAfterTimePass, onGameLoad(newGame), beforeGameSave, afterGameSave, configureXStream`.
- Vanilla systems: `data/scripts/world/systems/*.java` (e.g. Arcadia): `sector.createStarSystem`, `initStar`, `addPlanet`, `addCustomEntity`, `createJumpPoint`, `autogenerateHyperspaceJumpPoints`.
- Vanilla system coordinates (`data/campaign/starmap.json`): core spans x≈-19000..11000, y≈-14500..3200. North of Zagan (-3900,3200) is open.
- Custom entity types: `data/config/custom_entities.json` (merged). Tag `has_interaction_dialog` → rules-driven dialog (`OpenInteractionDialog`, `$customType`).
- Markets are created in code (`Global.getFactory().createMarket`, `addCondition`, `addIndustry`, `addSubmarket`, `Global.getSector().getEconomy().addMarket(m, true)`).
  Submarkets: `open_market, black_market, generic_military, storage`. Industries: `population, spaceport, militarybase, orbitalstation_high, …`.
- **NPC hails ("hassle")**: vanilla `HasslePlayerScript` (always running) picks nearby non-hostile fleets whose memory has
  `$willHasslePlayer=true` and `$hassleType=<type>`, makes them pursue the player, and the encounter fires a
  `BeginFleetEncounter` rule with `$pursuePlayer_hassle score:50`, `$hassleType == <type>` → `HailPlayer` → `OpenCommLink` rule.
  Template: Knights of Ludd "sacredProtectors" tithe in rules.csv (lines ~35935-36035). Exactly what the audits need.
- Rules: market main menu options = `PopulateOptions` + `$hasMarket` + `$menuState == main`; return with `FireAll PopulateOptions`.
  Option syntax `order:optionId:Text`. Useful vanilla commands: `AddText, SetStoryOption, MakeOtherFleetPreventDisengage, MakeOtherFleetHostile, HailPlayer, AdjustRep, ShowPersonVisual, DismissDialog, EndConversation, FireAll/FireBest`.
- Intel: `BaseIntelPlugin` (`createIntelInfo`, `createSmallDescription`, `getIntelTags`, `getMapLocation`, `getIcon`, `advanceImpl`, `sendUpdateIfPlayerHasIntel`).
- Fleets: `FleetFactoryV3.createFleet(FleetParamsV3)`; `withOfficers=false` avoids human officers. Remnant AI-core officers only go on `automated` hulls.
- Faction file keys: `id, displayName…, color, shipNamePrefix, names, knownShips{tags,hulls}, knownWeapons, knownFighters, knownHullMods, priorityShips/Weapons, factionDoctrine, illegalCommodities, portraits, ranks, custom{…}, fleetTypeNames, music`.
- `descriptions.csv`: `id,type,text1..text5,notes`; types SHIP, WEAPON, SHIP_SYSTEM (text2 = type label, text3 = short, text5 = detail with {{hl}}), CUSTOM, FACTION, RESOURCE.
