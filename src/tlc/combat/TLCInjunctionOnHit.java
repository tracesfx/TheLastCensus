package tlc.combat;

import com.fs.starfarer.api.combat.CombatEngineAPI;
import com.fs.starfarer.api.combat.CombatEntityAPI;
import com.fs.starfarer.api.combat.DamagingProjectileAPI;
import com.fs.starfarer.api.combat.OnHitEffectPlugin;
import com.fs.starfarer.api.combat.ShipAPI;
import com.fs.starfarer.api.combat.listeners.ApplyDamageResultAPI;
import org.lwjgl.util.vector.Vector2f;

/** Injunction Emitter: hits suppress the target's weapons (-20% rate of fire and beam damage, 4 s, refreshes). */
public class TLCInjunctionOnHit implements OnHitEffectPlugin {
    public static final float DURATION = 4f;

    @Override
    public void onHit(DamagingProjectileAPI projectile, CombatEntityAPI target, Vector2f point, boolean shieldHit,
                      ApplyDamageResultAPI damageResult, CombatEngineAPI engine) {
        if (engine == null || !(target instanceof ShipAPI)) return;
        ShipAPI ship = (ShipAPI) target;
        if (ship.isHulk() || !ship.isAlive()) return;
        TLCLedgerPlugin ledger = TLCLedgerPlugin.get();
        if (ledger == null) return;
        boolean fresh = !ledger.hasDebuff(ship, TLCLedgerPlugin.Debuff.INJUNCTION);
        ledger.refreshDebuff(ship, TLCLedgerPlugin.Debuff.INJUNCTION, DURATION, 1f);
        if (fresh && point != null) {
            engine.addFloatingText(point, "INJUNCTION", 18f, TLCLedgerPlugin.JADE, ship, 0.2f, 0.6f);
        }
    }
}
