package tlc.combat;

import com.fs.starfarer.api.combat.CombatEngineAPI;
import com.fs.starfarer.api.combat.CombatEntityAPI;
import com.fs.starfarer.api.combat.DamagingProjectileAPI;
import com.fs.starfarer.api.combat.OnFireEffectPlugin;
import com.fs.starfarer.api.combat.OnHitEffectPlugin;
import com.fs.starfarer.api.combat.ShipAPI;
import com.fs.starfarer.api.combat.WeaponAPI;
import com.fs.starfarer.api.combat.listeners.ApplyDamageResultAPI;
import org.lwjgl.util.vector.Vector2f;

/**
 * Accrual Autocannon - "compound interest". Consecutive hits on the same ship add a stack; each stack adds
 * 5% damage to subsequent shots (max 10 stacks = +50%). Switching targets or 2 s without a hit resets.
 * State lives in the per-battle ledger because the game instantiates the on-fire and on-hit plugins separately.
 */
public class TLCAccrualEffect implements OnFireEffectPlugin, OnHitEffectPlugin {
    public static final float PER_STACK = 0.05f;
    public static final int MAX_STACKS = 10;
    public static final float WINDOW = 2f;

    @Override
    public void onFire(DamagingProjectileAPI projectile, WeaponAPI weapon, CombatEngineAPI engine) {
        if (projectile == null || weapon == null || engine == null) return;
        TLCLedgerPlugin ledger = TLCLedgerPlugin.get();
        if (ledger == null) return;
        TLCLedgerPlugin.AccrualState s = ledger.accrual(weapon);
        if (engine.getTotalElapsedTime(false) - s.lastHit > WINDOW) {
            s.stacks = 0;
            s.lastTarget = null;
        }
        if (s.stacks > 0) projectile.setDamageAmount(projectile.getDamageAmount() * (1f + PER_STACK * s.stacks));
    }

    @Override
    public void onHit(DamagingProjectileAPI projectile, CombatEntityAPI target, Vector2f point, boolean shieldHit,
                      ApplyDamageResultAPI damageResult, CombatEngineAPI engine) {
        if (projectile == null || engine == null || !(target instanceof ShipAPI)) return;
        WeaponAPI w = projectile.getWeapon();
        if (w == null) return;
        TLCLedgerPlugin ledger = TLCLedgerPlugin.get();
        if (ledger == null) return;
        TLCLedgerPlugin.AccrualState s = ledger.accrual(w);
        float t = engine.getTotalElapsedTime(false);
        if (s.lastTarget == target && t - s.lastHit <= WINDOW) {
            s.stacks = Math.min(MAX_STACKS, s.stacks + 1);
        } else {
            s.stacks = 1;
        }
        s.lastTarget = target;
        s.lastHit = t;
    }
}
