package tlc.campaign;

import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.campaign.BattleAPI;
import com.fs.starfarer.api.campaign.CampaignEventListener.FleetDespawnReason;
import com.fs.starfarer.api.campaign.CampaignFleetAPI;
import com.fs.starfarer.api.campaign.listeners.FleetEventListener;
import org.apache.log4j.Logger;

/** Attached directly to quest fleets (never to the global listener manager). Save-safe: holds only a string. */
public class TLCFleetListener implements FleetEventListener {
    private static final Logger log = Global.getLogger(TLCFleetListener.class);

    public static final String KIND_IG = "ig";

    private String kind;

    public TLCFleetListener(String kind) {
        this.kind = kind;
    }

    @Override
    public void reportFleetDespawnedToListener(CampaignFleetAPI fleet, FleetDespawnReason reason, Object param) {
        try {
            if (KIND_IG.equals(kind)) TLCInspectorGeneral.onFleetDespawned(fleet, reason);
        } catch (Throwable t) {
            log.error("TLC: fleet despawn handling failed", t);
        }
    }

    @Override
    public void reportBattleOccurred(CampaignFleetAPI fleet, CampaignFleetAPI primaryWinner, BattleAPI battle) {
        try {
            if (KIND_IG.equals(kind)) TLCInspectorGeneral.onBattle(fleet, primaryWinner, battle);
        } catch (Throwable t) {
            log.error("TLC: battle handling failed", t);
        }
    }
}
