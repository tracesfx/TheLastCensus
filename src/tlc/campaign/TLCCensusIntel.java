package tlc.campaign;

import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.campaign.FactionAPI;
import com.fs.starfarer.api.campaign.SectorEntityToken;
import com.fs.starfarer.api.campaign.TextPanelAPI;
import com.fs.starfarer.api.campaign.comm.IntelInfoPlugin;
import com.fs.starfarer.api.impl.campaign.ids.Tags;
import com.fs.starfarer.api.impl.campaign.intel.BaseIntelPlugin;
import com.fs.starfarer.api.ui.SectorMapAPI;
import com.fs.starfarer.api.ui.TooltipMakerAPI;
import com.fs.starfarer.api.util.Misc;
import tlc.TLCIds;

import java.awt.Color;
import java.util.Set;

/**
 * Intel entry for the questline "The Last Census". All state lives in global memory (see TLCIds.MEM_*);
 * this class only presents it, so rules.csv and Java can never disagree about the current stage.
 */
public class TLCCensusIntel extends BaseIntelPlugin {

    public static TLCCensusIntel get() {
        if (Global.getSector() == null) return null;
        IntelInfoPlugin p = Global.getSector().getIntelManager().getFirstIntel(TLCCensusIntel.class);
        return p instanceof TLCCensusIntel ? (TLCCensusIntel) p : null;
    }

    /** Creates the intel (the "unregistered transmission") once the broadcast delay has elapsed. */
    public static void ensureExists(boolean timeOk) {
        if (get() != null) return;
        if (!timeOk && TLCIds.STAGE_BROADCAST.equals(TLCMem.stage())) return;
        if (!TLCMem.tallyhouseIntact() && TLCIds.STAGE_BROADCAST.equals(TLCMem.stage())) return;
        TLCCensusIntel intel = new TLCCensusIntel();
        intel.setImportant(true);
        Global.getSector().getIntelManager().addIntel(intel);
    }

    /** Push an update notification (with optional dialog text panel). */
    public static void update(String reason, TextPanelAPI panel) {
        TLCCensusIntel intel = get();
        if (intel == null) {
            intel = new TLCCensusIntel();
            intel.setImportant(true);
            Global.getSector().getIntelManager().addIntel(intel, panel == null, panel);
            return;
        }
        if (panel != null) {
            intel.sendUpdate(reason, panel);
        } else {
            intel.sendUpdateIfPlayerHasIntel(reason, false);
        }
    }

    @Override
    protected String getName() {
        if (TLCIds.STAGE_DONE.equals(TLCMem.stage())) return "The Last Census - Filed";
        if (TLCIds.STAGE_BROADCAST.equals(TLCMem.stage())) return "Unregistered Transmission";
        return "The Last Census";
    }

    @Override
    public String getIcon() {
        return Global.getSettings().getSpriteName("intel", "tlc_census");
    }

    @Override
    public Set<String> getIntelTags(SectorMapAPI map) {
        Set<String> tags = super.getIntelTags(map);
        tags.add(Tags.INTEL_STORY);
        tags.add(TLCIds.FACTION_BUREAU);
        return tags;
    }

    @Override
    public FactionAPI getFactionForUIColors() {
        FactionAPI f = TLCMem.bureau();
        return f != null ? f : super.getFactionForUIColors();
    }

    @Override
    public SectorEntityToken getMapLocation(SectorMapAPI map) {
        String stage = TLCMem.stage();
        if (TLCIds.STAGE_RELAY.equals(stage) && !TLCMem.flag(TLCIds.MEM_RELAY_ACTIVE)) {
            SectorEntityToken relay = TLCMem.relay();
            if (relay != null) return relay;
        }
        return TLCMem.tallyhouse();
    }

    @Override
    protected void addBulletPoints(TooltipMakerAPI info, ListInfoMode mode, boolean isUpdate, Color tc, float initPad) {
        Color h = Misc.getHighlightColor();
        String stage = TLCMem.stage();
        float pad = initPad;
        if (TLCIds.STAGE_BROADCAST.equals(stage)) {
            info.addPara("Investigate the source of the broadcast in the Assize system", pad, tc, h, "Assize");
        } else if (TLCIds.STAGE_REPORT.equals(stage)) {
            info.addPara("Report to the Registrar of Assize at the Tallyhouse", pad, tc, h, "Registrar of Assize");
        } else if (TLCIds.STAGE_RETURNS.equals(stage)) {
            int n = Math.min(TLCMem.getInt(TLCIds.MEM_RETURNS), TLCIds.RETURNS_REQUIRED);
            if (n < TLCIds.RETURNS_REQUIRED) {
                info.addPara("Census returns filed: %s of %s", pad, tc, h, "" + n, "" + TLCIds.RETURNS_REQUIRED);
            } else {
                info.addPara("Return to the Registrar with your census returns", pad, tc, h, "Registrar");
            }
        } else if (TLCIds.STAGE_RELAY.equals(stage)) {
            if (!TLCMem.flag(TLCIds.MEM_RELAY_ACTIVE)) {
                info.addPara("Reactivate the Bureau courier relay in the Envoi system", pad, tc, h, "Envoi");
            } else {
                info.addPara("Tell the Registrar that the courier relay is online", pad, tc, h, "Registrar");
            }
        } else {
            String ending = TLCMem.getString(TLCIds.MEM_ENDING, "");
            if (TLCIds.ENDING_CONTINUING.equals(ending)) {
                info.addPara("The Grand Audit continues. You hold the rank of Commissioner.", pad, tc, h, "Commissioner");
            } else {
                info.addPara("The Grand Audit is closed. The census has been filed.", pad, tc);
            }
        }
    }

    @Override
    public void createSmallDescription(TooltipMakerAPI info, float width, float height) {
        Color h = Misc.getHighlightColor();
        Color g = Misc.getGrayColor();
        float opad = 10f;
        FactionAPI bureau = TLCMem.bureau();
        if (bureau != null) info.addImage(bureau.getLogo(), width, 128, 3f);
        String stage = TLCMem.stage();

        info.addPara("A Domain-era broadcast is repeating on every comm relay in the Persean Sector, on a channel nobody "
                + "has used in two hundred cycles:", opad);
        info.addPara("ATTENTION. ALL CHARTERED COLONIES AND REGISTERED VESSELS OF THE PERSEAN SECTOR. THE GRAND AUDIT HAS "
                + "COMMENCED. ASSESSORS OF THE DOMAIN BUREAU OF COLONIAL ASSESSMENT WILL CALL UPON YOU IN DUE COURSE. "
                + "PLEASE HAVE YOUR MANIFESTS AND CHARTERS AVAILABLE FOR INSPECTION. THE BUREAU THANKS YOU FOR YOUR "
                + "COOPERATION.", g, opad);
        info.addPara("Relay triangulation places the source in the %s system, north of the core worlds.", opad, h,
                "Assize");

        if (!TLCIds.STAGE_BROADCAST.equals(stage) && !TLCIds.STAGE_REPORT.equals(stage)) {
            info.addPara("The source is the Tallyhouse, the Persean office of the Domain Bureau of Colonial Assessment, "
                    + "run by an administrative intelligence styling itself the Registrar of Assize. It has engaged you "
                    + "as a Provisional Enumerator: your fleet is exempt from audit, and the Bureau pays for census returns "
                    + "filed at inhabited colonies outside its reach.", opad);
        } else if (TLCIds.STAGE_REPORT.equals(stage)) {
            info.addPara("A Bureau Assessor invited you to report to the Registrar of Assize at the Tallyhouse, citing an "
                    + "emergency statute that allows the Bureau to engage compliant masters of vessels as enumerators.", opad);
        }

        if (TLCIds.STAGE_RETURNS.equals(stage)) {
            int n = TLCMem.getInt(TLCIds.MEM_RETURNS);
            info.addPara("Returns filed so far: %s. The Registrar asked for at least %s.", opad, h, "" + n,
                    "" + TLCIds.RETURNS_REQUIRED);
            info.addPara("Dock at any inhabited colony of size 3 or more that is not a Bureau market and choose to file a "
                    + "census return. Each colony can be enumerated once.", g, opad);
        } else if (TLCIds.STAGE_RELAY.equals(stage)) {
            if (!TLCMem.flag(TLCIds.MEM_RELAY_ACTIVE)) {
                info.addPara("The census cannot be filed until it is transmitted to Domain Central through the Bureau's "
                        + "courier relay in the %s system. The relay has been silent for two centuries, and the "
                        + "Registrar reports that salvagers have been stripping it.", opad, h, "Envoi");
            } else {
                info.addPara("The courier relay at Envoi is awake again and waiting for traffic. The Registrar will want "
                        + "to know.", opad);
            }
        } else if (TLCIds.STAGE_DONE.equals(stage)) {
            String ending = TLCMem.getString(TLCIds.MEM_ENDING, "");
            if (TLCIds.ENDING_CONTINUING.equals(ending)) {
                info.addPara("The census was transmitted through the relay at Envoi. No acknowledgment came. You told "
                        + "the Registrar that someone would be listening one day, and the Grand Audit goes on. The Bureau "
                        + "has named you Commissioner of the Persean office. Its Assessors will not audit you again.", opad);
            } else {
                info.addPara("The census was transmitted through the relay at Envoi. No acknowledgment came. You told "
                        + "the Registrar the truth, and it closed the Grand Audit and recalled its Assessors. The "
                        + "Tallyhouse remains open, and very quiet.", opad);
            }
        }

        if (!TLCMem.tallyhouseIntact() && !TLCIds.STAGE_DONE.equals(stage)) {
            info.addPara("The Tallyhouse no longer answers in the Bureau's name. Without the Registrar, the Grand Audit "
                    + "cannot be completed.", Misc.getNegativeHighlightColor(), opad);
        }
        if (TLCMem.flag(TLCIds.MEM_COMMISSIONER)) {
            info.addPara("As Commissioner, your fleet is never audited by Bureau Assessors.", g, opad);
        } else if (TLCMem.flag(TLCIds.MEM_ENUMERATOR)) {
            info.addPara("While you hold the Provisional Enumerator's warrant, you can present it to any Assessor to pass "
                    + "an audit without charge.", g, opad);
        }
    }

    @Override
    public String getSortString() {
        return "The Last Census";
    }

    @Override
    public boolean shouldRemoveIntel() {
        return false;
    }

    @Override
    public IntelSortTier getSortTier() {
        return TLCIds.STAGE_DONE.equals(TLCMem.stage()) ? IntelSortTier.TIER_COMPLETED : super.getSortTier();
    }
}
