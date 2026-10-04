package tlc.combat;

import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.combat.BaseEveryFrameCombatPlugin;
import com.fs.starfarer.api.combat.BeamAPI;
import com.fs.starfarer.api.combat.CombatEngineAPI;
import com.fs.starfarer.api.combat.CombatEntityAPI;
import com.fs.starfarer.api.combat.DamagingProjectileAPI;
import com.fs.starfarer.api.combat.FluxTrackerAPI;
import com.fs.starfarer.api.combat.MutableShipStatsAPI;
import com.fs.starfarer.api.combat.ShipAPI;
import com.fs.starfarer.api.combat.ShipCommand;
import com.fs.starfarer.api.combat.ShipVariantAPI;
import com.fs.starfarer.api.combat.WeaponAPI;
import com.fs.starfarer.api.combat.listeners.ApplyDamageResultAPI;
import com.fs.starfarer.api.combat.listeners.DamageListener;
import com.fs.starfarer.api.fleet.FleetMemberAPI;
import com.fs.starfarer.api.impl.campaign.ids.Tags;
import com.fs.starfarer.api.input.InputEventAPI;
import com.fs.starfarer.api.loading.VariantSource;
import com.fs.starfarer.api.util.IntervalUtil;
import org.apache.log4j.Logger;
import tlc.TLCIds;

import java.awt.Color;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * One per battle (registered in data/config/settings.json "plugins"). Central bookkeeping for every
 * Bureau combat mechanic, so no effect can outlive its source:
 * <ul>
 * <li>Liens and settlements (Assessor Protocols hullmod)</li>
 * <li>Writs of seizure (Writ Projector) - seized ships are tagged always-recoverable for post-battle salvage</li>
 * <li>Timed debuffs (Surcharge, Injunction, Summary Judgment) with guaranteed expiry</li>
 * <li>Per-weapon accrual state (Accrual Autocannon)</li>
 * </ul>
 * All maps are keyed by combat objects and live only as long as this plugin (i.e. one battle).
 */
public class TLCLedgerPlugin extends BaseEveryFrameCombatPlugin {
    private static final Logger log = Global.getLogger(TLCLedgerPlugin.class);

    public static final String KEY = "tlc_ledger_plugin";
    public static final float WRIT_WINDOW = 3f;
    public static final float SETTLE_FRACTION = 0.5f;
    public static final float SETTLE_CAP = 0.3f;
    public static final float SURCHARGE_FLUX_PCT = 35f;
    public static final float SURCHARGE_SHIELD_PCT = 15f;
    public static final float INJUNCTION_MULT = 0.8f;
    public static final float JUDGMENT_SHIELD_PCT = 25f;

    public static final Color JADE = new Color(130, 235, 175, 255);
    public static final Color AMBER = new Color(255, 190, 90, 255);

    public enum Debuff {SURCHARGE, INJUNCTION, JUDGMENT}

    private static final String MOD_SURCHARGE = "tlc_surcharge_debuff";
    private static final String MOD_INJUNCTION = "tlc_injunction_debuff";
    private static final String MOD_JUDGMENT = "tlc_judgment_debuff";

    private static final class TimedDebuff {
        ShipAPI ship;
        Debuff type;
        float until;
        float magnitude;
        boolean applied;
    }

    public static final class AccrualState {
        public CombatEntityAPI lastTarget;
        public float lastHit = -100f;
        public int stacks;
    }

    private CombatEngineAPI engine;
    private final Map<ShipAPI, Map<ShipAPI, Float>> liens = new HashMap<ShipAPI, Map<ShipAPI, Float>>();
    private final Map<ShipAPI, Float> lastWrit = new HashMap<ShipAPI, Float>();
    private final Map<ShipAPI, Float> writText = new HashMap<ShipAPI, Float>();
    private final Set<ShipAPI> lienholders = new HashSet<ShipAPI>();
    private final Set<ShipAPI> listened = new HashSet<ShipAPI>();
    private final Set<ShipAPI> resolved = new HashSet<ShipAPI>();
    private final Map<String, TimedDebuff> debuffs = new HashMap<String, TimedDebuff>();
    private final Map<WeaponAPI, AccrualState> accrual = new HashMap<WeaponAPI, AccrualState>();
    private final IntervalUtil scan = new IntervalUtil(0.1f, 0.1f);
    private boolean loggedError = false;

    @Override
    public void init(CombatEngineAPI engine) {
        this.engine = engine;
        if (engine != null) engine.getCustomData().put(KEY, this);
    }

    /** Returns this battle's ledger, creating one if the settings-registered instance is missing or stale. */
    public static TLCLedgerPlugin get() {
        CombatEngineAPI e = Global.getCombatEngine();
        if (e == null) return null;
        Object o = e.getCustomData().get(KEY);
        if (o instanceof TLCLedgerPlugin && ((TLCLedgerPlugin) o).engine == e) return (TLCLedgerPlugin) o;
        TLCLedgerPlugin p = new TLCLedgerPlugin();
        p.engine = e;
        e.getCustomData().put(KEY, p);
        e.addPlugin(p);
        return p;
    }

    @Override
    public void advance(float amount, List<InputEventAPI> events) {
        if (engine == null) engine = Global.getCombatEngine();
        if (engine == null || engine.isPaused()) return;
        try {
            tickDebuffs();
            scan.advance(amount);
            if (scan.intervalElapsed()) {
                attachListeners();
                resolveDeaths();
            }
        } catch (Throwable t) {
            if (!loggedError) {
                loggedError = true;
                log.error("TLC: ledger plugin error (further errors suppressed)", t);
            }
        }
    }

    private float now() {
        return engine.getTotalElapsedTime(false);
    }

    // ------------------------------------------------------------------------------------ debuffs
    public boolean hasDebuff(ShipAPI ship, Debuff type) {
        return ship != null && debuffs.containsKey(ship.getId() + "|" + type);
    }

    public void refreshDebuff(ShipAPI ship, Debuff type, float duration, float magnitude) {
        if (ship == null || engine == null) return;
        String key = ship.getId() + "|" + type;
        TimedDebuff d = debuffs.get(key);
        if (d == null) {
            d = new TimedDebuff();
            d.ship = ship;
            d.type = type;
            debuffs.put(key, d);
        }
        d.until = Math.max(d.until, now() + duration);
        if (!d.applied || Math.abs(d.magnitude - magnitude) > 0.05f) {
            d.magnitude = magnitude;
            apply(d);
            d.applied = true;
        }
    }

    private void tickDebuffs() {
        if (debuffs.isEmpty()) return;
        float t = now();
        Iterator<TimedDebuff> it = debuffs.values().iterator();
        while (it.hasNext()) {
            TimedDebuff d = it.next();
            boolean gone = d.ship == null || d.ship.isHulk() || !d.ship.isAlive() || !engine.isEntityInPlay(d.ship);
            if (gone || t > d.until) {
                remove(d);
                it.remove();
                continue;
            }
            switch (d.type) {
                case JUDGMENT:
                    d.ship.blockCommandForOneFrame(ShipCommand.VENT_FLUX);
                    d.ship.setJitterUnder(d, AMBER, 0.7f, 6, 0f, 8f);
                    break;
                case INJUNCTION:
                    d.ship.setJitterUnder(d, JADE, 0.35f, 3, 0f, 4f);
                    break;
                default:
                    d.ship.setJitterUnder(d, JADE, 0.25f * d.magnitude, 3, 0f, 5f);
                    break;
            }
        }
    }

    private void apply(TimedDebuff d) {
        MutableShipStatsAPI s = d.ship.getMutableStats();
        switch (d.type) {
            case SURCHARGE:
                s.getBallisticWeaponFluxCostMod().modifyPercent(MOD_SURCHARGE, SURCHARGE_FLUX_PCT * d.magnitude);
                s.getEnergyWeaponFluxCostMod().modifyPercent(MOD_SURCHARGE, SURCHARGE_FLUX_PCT * d.magnitude);
                s.getMissileWeaponFluxCostMod().modifyPercent(MOD_SURCHARGE, SURCHARGE_FLUX_PCT * d.magnitude);
                s.getShieldDamageTakenMult().modifyPercent(MOD_SURCHARGE, SURCHARGE_SHIELD_PCT * d.magnitude);
                break;
            case INJUNCTION:
                s.getBallisticRoFMult().modifyMult(MOD_INJUNCTION, INJUNCTION_MULT);
                s.getEnergyRoFMult().modifyMult(MOD_INJUNCTION, INJUNCTION_MULT);
                s.getMissileRoFMult().modifyMult(MOD_INJUNCTION, INJUNCTION_MULT);
                s.getBeamWeaponDamageMult().modifyMult(MOD_INJUNCTION, INJUNCTION_MULT);
                break;
            case JUDGMENT:
                s.getShieldDamageTakenMult().modifyPercent(MOD_JUDGMENT, JUDGMENT_SHIELD_PCT);
                break;
        }
    }

    private void remove(TimedDebuff d) {
        if (d.ship == null) return;
        MutableShipStatsAPI s = d.ship.getMutableStats();
        switch (d.type) {
            case SURCHARGE:
                s.getBallisticWeaponFluxCostMod().unmodify(MOD_SURCHARGE);
                s.getEnergyWeaponFluxCostMod().unmodify(MOD_SURCHARGE);
                s.getMissileWeaponFluxCostMod().unmodify(MOD_SURCHARGE);
                s.getShieldDamageTakenMult().unmodify(MOD_SURCHARGE);
                break;
            case INJUNCTION:
                s.getBallisticRoFMult().unmodify(MOD_INJUNCTION);
                s.getEnergyRoFMult().unmodify(MOD_INJUNCTION);
                s.getMissileRoFMult().unmodify(MOD_INJUNCTION);
                s.getBeamWeaponDamageMult().unmodify(MOD_INJUNCTION);
                break;
            case JUDGMENT:
                s.getShieldDamageTakenMult().unmodify(MOD_JUDGMENT);
                break;
        }
    }

    // ------------------------------------------------------------------------------------ accrual
    public AccrualState accrual(WeaponAPI weapon) {
        AccrualState s = accrual.get(weapon);
        if (s == null) {
            s = new AccrualState();
            accrual.put(weapon, s);
        }
        return s;
    }

    // ------------------------------------------------------------------------------------ writs
    public void markWrit(ShipAPI target, ShipAPI source) {
        if (target == null || engine == null) return;
        float t = now();
        lastWrit.put(target, t);
        Float last = writText.get(target);
        if (last == null || t - last > 4f) {
            writText.put(target, t);
            engine.addFloatingText(target.getLocation(), "WRIT SERVED", 18f, AMBER, target, 0.2f, 0.6f);
        }
    }

    private void seize(ShipAPI ship) {
        if (ship.isFighter() || ship.isStationModule() || ship.getParentStation() != null) return;
        engine.addFloatingText(ship.getLocation(), "SEIZED", 32f, AMBER, ship, 0.5f, 2f);
        if (!engine.isInCampaign() || engine.isSimulation()) return;
        FleetMemberAPI m = ship.getFleetMember();
        if (m == null) return;
        ShipVariantAPI v = m.getVariant();
        if (v == null || v.hasTag(Tags.VARIANT_ALWAYS_RECOVERABLE)) return;
        // Stock variants are shared: clone before tagging, exactly as vanilla does after fleet inflation.
        if (v.isStockVariant() || v.getSource() != VariantSource.REFIT) {
            v = v.clone();
            v.setSource(VariantSource.REFIT);
            m.setVariant(v, false, false);
        }
        v.addTag(Tags.VARIANT_ALWAYS_RECOVERABLE);
        v.addTag(TLCIds.SEIZED_TAG);
    }

    // ------------------------------------------------------------------------------------ liens
    public void registerLienholder(ShipAPI ship) {
        if (ship != null) lienholders.add(ship);
    }

    void addLien(ShipAPI target, ShipAPI source, float dmg) {
        Map<ShipAPI, Float> m = liens.get(target);
        if (m == null) {
            m = new HashMap<ShipAPI, Float>(4);
            liens.put(target, m);
        }
        Float v = m.get(source);
        m.put(source, v == null ? dmg : v + dmg);
    }

    private void attachListeners() {
        if (lienholders.isEmpty()) return;
        for (ShipAPI s : engine.getShips()) {
            if (s == null || s.isFighter() || s.isHulk() || listened.contains(s)) continue;
            s.addListener(new LienListener(this, s));
            listened.add(s);
        }
    }

    private void settle(ShipAPI target, Map<ShipAPI, Float> holders) {
        for (Map.Entry<ShipAPI, Float> e : holders.entrySet()) {
            ShipAPI h = e.getKey();
            if (h == null || h.isHulk() || !h.isAlive() || !engine.isEntityInPlay(h)) continue;
            FluxTrackerAPI ft = h.getFluxTracker();
            if (ft == null) continue;
            float curr = ft.getCurrFlux();
            float amount = Math.min(e.getValue() * SETTLE_FRACTION, ft.getMaxFlux() * SETTLE_CAP);
            amount = Math.min(amount, curr);
            if (amount < 1f) continue;
            float hard = ft.getHardFlux();
            ft.setHardFlux(hard - Math.min(hard, amount));
            ft.setCurrFlux(curr - amount);
            engine.addFloatingText(h.getLocation(), "Lien settled: -" + (int) amount + " flux", 18f, JADE, h, 0.3f, 1f);
        }
    }

    private void resolveDeaths() {
        float t = now();
        Iterator<Map.Entry<ShipAPI, Map<ShipAPI, Float>>> it = liens.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<ShipAPI, Map<ShipAPI, Float>> e = it.next();
            ShipAPI tgt = e.getKey();
            if (tgt == null) {
                it.remove();
            } else if (tgt.isHulk()) {
                settle(tgt, e.getValue());
                it.remove();
            } else if (!engine.isEntityInPlay(tgt)) {
                it.remove(); // retreated: liens lapse
            }
        }
        Iterator<Map.Entry<ShipAPI, Float>> wit = lastWrit.entrySet().iterator();
        while (wit.hasNext()) {
            Map.Entry<ShipAPI, Float> e = wit.next();
            ShipAPI tgt = e.getKey();
            if (tgt == null) {
                wit.remove();
            } else if (tgt.isHulk()) {
                if (t - e.getValue() <= WRIT_WINDOW + 0.25f && resolved.add(tgt)) seize(tgt);
                wit.remove();
                writText.remove(tgt);
            } else if (!engine.isEntityInPlay(tgt) || t - e.getValue() > 30f) {
                wit.remove();
                writText.remove(tgt);
            }
        }
    }

    static ShipAPI resolveSource(Object o) {
        if (o instanceof ShipAPI) {
            ShipAPI s = (ShipAPI) o;
            if (s.isFighter() && s.getWing() != null && s.getWing().getSourceShip() != null) {
                return s.getWing().getSourceShip();
            }
            return s;
        }
        if (o instanceof DamagingProjectileAPI) return ((DamagingProjectileAPI) o).getSource();
        if (o instanceof BeamAPI) return ((BeamAPI) o).getSource();
        if (o instanceof WeaponAPI) return ((WeaponAPI) o).getShip();
        return null;
    }

    /** Attached to each ship; records damage that ship takes from lienholders. */
    private static final class LienListener implements DamageListener {
        private final TLCLedgerPlugin plugin;
        private final ShipAPI owner;

        LienListener(TLCLedgerPlugin plugin, ShipAPI owner) {
            this.plugin = plugin;
            this.owner = owner;
        }

        @Override
        public void reportDamageApplied(Object source, CombatEntityAPI target, ApplyDamageResultAPI result) {
            if (target != owner || result == null) return;
            ShipAPI src = resolveSource(source);
            if (src == null || !plugin.lienholders.contains(src)) return;
            if (src.getOwner() == owner.getOwner()) return;
            float dmg = result.getDamageToHull() + result.getTotalDamageToArmor() + result.getDamageToShields();
            if (dmg > 0f) plugin.addLien(owner, src, dmg);
        }
    }
}
