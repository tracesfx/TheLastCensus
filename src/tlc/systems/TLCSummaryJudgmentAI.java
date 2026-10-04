package tlc.systems;

import com.fs.starfarer.api.combat.CombatEngineAPI;
import com.fs.starfarer.api.combat.ShipAPI;
import com.fs.starfarer.api.combat.ShipSystemAIScript;
import com.fs.starfarer.api.combat.ShipSystemAPI;
import com.fs.starfarer.api.combat.ShipwideAIFlags;
import com.fs.starfarer.api.util.IntervalUtil;
import com.fs.starfarer.api.util.Misc;
import org.lwjgl.util.vector.Vector2f;

/** Uses Summary Judgment on the current target once it is under real flux pressure (so it cannot vent its way out). */
public class TLCSummaryJudgmentAI implements ShipSystemAIScript {
    private ShipAPI ship;
    private ShipSystemAPI system;
    private final IntervalUtil tracker = new IntervalUtil(0.3f, 0.5f);

    @Override
    public void init(ShipAPI ship, ShipSystemAPI system, ShipwideAIFlags flags, CombatEngineAPI engine) {
        this.ship = ship;
        this.system = system;
    }

    @Override
    public void advance(float amount, Vector2f missileDangerDir, Vector2f collisionDangerDir, ShipAPI target) {
        if (ship == null || system == null) return;
        tracker.advance(amount);
        if (!tracker.intervalElapsed()) return;
        if (system.isActive() || system.isCoolingDown() || system.isOutOfAmmo()) return;
        if (ship.getFluxTracker().isOverloadedOrVenting()) return;
        ShipAPI t = target != null ? target : ship.getShipTarget();
        if (t == null || t.isFighter() || t.isHulk() || !t.isAlive() || t.getOwner() == ship.getOwner()) return;
        if (Misc.getDistance(ship.getLocation(), t.getLocation()) - t.getCollisionRadius() > TLCSummaryJudgmentStats.RANGE) {
            return;
        }
        if (t.getFluxLevel() > 0.45f || t.getFluxTracker().isOverloaded()) {
            ship.setShipTarget(t);
            ship.useSystem();
        }
    }
}
