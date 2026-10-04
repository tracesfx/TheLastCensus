package tlc.systems;

import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.combat.CombatEngineAPI;
import com.fs.starfarer.api.combat.MutableShipStatsAPI;
import com.fs.starfarer.api.combat.ShipAPI;
import com.fs.starfarer.api.combat.ShipSystemAPI;
import com.fs.starfarer.api.impl.combat.BaseShipSystemScript;
import com.fs.starfarer.api.util.IntervalUtil;
import com.fs.starfarer.api.util.Misc;
import tlc.combat.TLCLedgerPlugin;

import java.awt.Color;

/**
 * Summary Judgment (Plenipotentiary): freezes the targeted ship's assets for the active duration. It cannot begin
 * venting and its shields take +25% damage. Implemented as a refreshing ledger debuff.
 */
public class TLCSummaryJudgmentStats extends BaseShipSystemScript {
    public static final float RANGE = 1200f;
    private static final float REFRESH = 0.25f;

    private ShipAPI target;
    private final IntervalUtil arc = new IntervalUtil(0.6f, 0.9f);

    public static ShipAPI validTarget(ShipAPI ship) {
        if (ship == null) return null;
        ShipAPI t = ship.getShipTarget();
        if (t == null || t.isFighter() || t.isHulk() || !t.isAlive() || t.getOwner() == ship.getOwner()) return null;
        if (Misc.getDistance(ship.getLocation(), t.getLocation()) - t.getCollisionRadius() > RANGE) return null;
        return t;
    }

    @Override
    public void apply(MutableShipStatsAPI stats, String id, State state, float effectLevel) {
        if (!(stats.getEntity() instanceof ShipAPI)) return;
        ShipAPI ship = (ShipAPI) stats.getEntity();
        CombatEngineAPI engine = Global.getCombatEngine();
        if (engine == null) return;
        if (target == null) {
            target = validTarget(ship);
            if (target == null) return;
            engine.addFloatingText(target.getLocation(), "ASSETS FROZEN", 26f, TLCLedgerPlugin.AMBER, target, 0.5f, 1.2f);
        }
        if (target.isHulk() || !target.isAlive() || !engine.isEntityInPlay(target)) return;
        TLCLedgerPlugin ledger = TLCLedgerPlugin.get();
        if (ledger != null) ledger.refreshDebuff(target, TLCLedgerPlugin.Debuff.JUDGMENT, REFRESH, 1f);
        arc.advance(engine.getElapsedInLastFrame());
        if (arc.intervalElapsed()) {
            engine.spawnEmpArcVisual(ship.getLocation(), ship, target.getLocation(), target, 8f, TLCLedgerPlugin.AMBER,
                    new Color(255, 245, 220, 255));
        }
    }

    @Override
    public void unapply(MutableShipStatsAPI stats, String id) {
        target = null;
    }

    @Override
    public boolean isUsable(ShipSystemAPI system, ShipAPI ship) {
        return validTarget(ship) != null;
    }

    @Override
    public String getInfoText(ShipSystemAPI system, ShipAPI ship) {
        if (system.isOutOfAmmo() || system.getState() != ShipSystemAPI.SystemState.IDLE) return null;
        if (ship.getShipTarget() == null) return "NO TARGET";
        if (validTarget(ship) == null) return "OUT OF RANGE";
        return "READY";
    }

    @Override
    public StatusData getStatusData(int index, State state, float effectLevel) {
        if (index == 0) return new StatusData("target's assets frozen", false);
        return null;
    }
}
