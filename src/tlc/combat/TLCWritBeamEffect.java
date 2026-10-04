package tlc.combat;

import com.fs.starfarer.api.combat.BeamAPI;
import com.fs.starfarer.api.combat.BeamEffectPlugin;
import com.fs.starfarer.api.combat.CombatEngineAPI;
import com.fs.starfarer.api.combat.CombatEntityAPI;
import com.fs.starfarer.api.combat.ShipAPI;
import com.fs.starfarer.api.util.IntervalUtil;

/** Writ Projector: while the beam is fully on a hostile ship, that ship is "under writ". */
public class TLCWritBeamEffect implements BeamEffectPlugin {
    private final IntervalUtil fx = new IntervalUtil(0.3f, 0.5f);

    @Override
    public void advance(float amount, CombatEngineAPI engine, BeamAPI beam) {
        if (engine == null || beam == null || engine.isPaused()) return;
        CombatEntityAPI target = beam.getDamageTarget();
        if (!(target instanceof ShipAPI)) return;
        if (beam.getBrightness() < 0.9f) return;
        ShipAPI ship = (ShipAPI) target;
        if (ship.isFighter() || ship.isHulk()) return;
        if (beam.getSource() != null && beam.getSource().getOwner() == ship.getOwner()) return;
        TLCLedgerPlugin ledger = TLCLedgerPlugin.get();
        if (ledger == null) return;
        ledger.markWrit(ship, beam.getSource());
        fx.advance(amount);
        if (fx.intervalElapsed() && beam.getTo() != null) {
            engine.addHitParticle(beam.getTo(), ship.getVelocity(), 22f, 0.9f, 0.3f, TLCLedgerPlugin.AMBER);
        }
    }
}
