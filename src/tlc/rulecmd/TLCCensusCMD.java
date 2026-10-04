package tlc.rulecmd;

import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.campaign.InteractionDialogAPI;
import com.fs.starfarer.api.campaign.RepLevel;
import com.fs.starfarer.api.campaign.SectorEntityToken;
import com.fs.starfarer.api.campaign.TextPanelAPI;
import com.fs.starfarer.api.campaign.econ.MarketAPI;
import com.fs.starfarer.api.campaign.rules.MemoryAPI;
import com.fs.starfarer.api.impl.campaign.rulecmd.BaseCommandPlugin;
import com.fs.starfarer.api.util.Misc;
import com.fs.starfarer.api.util.Misc.Token;
import org.apache.log4j.Logger;
import tlc.TLCIds;
import tlc.campaign.TLCCensusText;
import tlc.campaign.TLCMem;
import tlc.campaign.TLCQuest;

import java.awt.Color;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * TLCCensusCMD &lt;canFile|fileReturn|stageIn stage...|returnsDone|returnsPending|relayEnter|relayClear|activateRelay|
 * dloEnter|dloRead|dloSearch&gt;
 */
public class TLCCensusCMD extends BaseCommandPlugin {
    private static final Logger log = Global.getLogger(TLCCensusCMD.class);

    public static final int PAY_PER_SIZE = 1000;
    public static final int QUEST_BONUS = 1500;

    @Override
    public boolean execute(String ruleId, InteractionDialogAPI dialog, List<Token> params, Map<String, MemoryAPI> memoryMap) {
        if (params == null || params.isEmpty()) return false;
        String cmd = params.get(0).getString(memoryMap);
        try {
            if ("stageIn".equals(cmd)) {
                String stage = TLCMem.stage();
                for (int i = 1; i < params.size(); i++) {
                    if (stage.equals(params.get(i).getString(memoryMap))) return true;
                }
                return false;
            }
            if ("relayClear".equals(cmd)) return TLCQuest.relayClear();
            if ("returnsDone".equals(cmd)) return TLCMem.getInt(TLCIds.MEM_RETURNS) >= TLCIds.RETURNS_REQUIRED;
            if ("returnsPending".equals(cmd)) return TLCMem.getInt(TLCIds.MEM_RETURNS) < TLCIds.RETURNS_REQUIRED;
            if (dialog == null) return false;
            if ("canFile".equals(cmd)) return canFile(market(dialog));
            if ("fileReturn".equals(cmd)) return fileReturn(dialog);
            if ("relayEnter".equals(cmd)) return relayEnter(dialog);
            if ("activateRelay".equals(cmd)) return activateRelay(dialog);
            if ("dloEnter".equals(cmd)) return dloEnter(dialog);
            if ("dloRead".equals(cmd)) return dloRead(dialog);
            if ("dloSearch".equals(cmd)) return dloSearch(dialog);
            log.warn("TLC: unknown census command " + cmd);
        } catch (Throwable t) {
            log.error("TLC: census command failed: " + cmd, t);
        }
        return false;
    }

    private static MarketAPI market(InteractionDialogAPI dialog) {
        SectorEntityToken e = dialog.getInteractionTarget();
        return e == null ? null : e.getMarket();
    }

    public static boolean canFile(MarketAPI m) {
        if (m == null || m.getPrimaryEntity() == null) return false;
        if (m.isPlanetConditionMarketOnly() || m.isHidden() || m.isPlayerOwned()) return false;
        if (m.getSize() < 3) return false;
        if (TLCIds.FACTION_BUREAU.equals(m.getFactionId())) return false;
        return !m.getMemoryWithoutUpdate().getBoolean(TLCIds.MEM_CENSUS_FILED);
    }

    // ------------------------------------------------------------------------------------ census returns
    private boolean fileReturn(InteractionDialogAPI dialog) {
        MarketAPI m = market(dialog);
        if (!canFile(m)) return false;
        TextPanelAPI t = dialog.getTextPanel();
        TLCCensusText.printReturn(t, m);
        m.getMemoryWithoutUpdate().set(TLCIds.MEM_CENSUS_FILED, true);
        int filed = TLCMem.increment(TLCIds.MEM_RETURNS);
        boolean questReturn = TLCIds.STAGE_RETURNS.equals(TLCMem.stage()) && filed <= TLCIds.RETURNS_REQUIRED;
        int pay = PAY_PER_SIZE * m.getSize() + (questReturn ? QUEST_BONUS : 0);
        t.addPara("You transmit the return to the Tallyhouse. The acknowledgment arrives a few seconds later: RECEIVED. "
                + "FILED. THANK YOU.");
        TLCQuest.giveCredits(pay, t);
        TLCQuest.adjustRep(0.01f, RepLevel.FRIENDLY, t);
        if (questReturn) {
            if (filed >= TLCIds.RETURNS_REQUIRED) {
                t.addPara("That makes %s returns. The Registrar will want to see you.", Misc.getHighlightColor(),
                        "" + filed);
            } else {
                t.addPara("Returns filed for the Registrar: %s of %s.", Misc.getHighlightColor(), "" + filed,
                        "" + TLCIds.RETURNS_REQUIRED);
            }
            TLCQuest.setStage(TLCIds.STAGE_RETURNS, t);
        }
        return true;
    }

    // ------------------------------------------------------------------------------------ courier relay
    private boolean relayEnter(InteractionDialogAPI dialog) {
        TextPanelAPI t = dialog.getTextPanel();
        if (TLCMem.flag(TLCIds.MEM_RELAY_ACTIVE)) {
            t.addPara("The courier relay hums on its mast, every panel lit. It is waiting for traffic that nobody has "
                    + "sent in two hundred cycles, and it seems perfectly content to keep waiting.");
            return true;
        }
        t.addPara("Your " + (Global.getSector().getPlayerFleet().getNumShips() > 1 ? "fleet holds" : "ship holds")
                + " station beside the relay mast. Up close the damage is worse than it looked: whole tiers of panels "
                + "have been cut away, and someone has spray-painted a price on the reactor housing. But the housing is "
                + "sealed, and the reactor inside it is warm.");
        if (!TLCIds.STAGE_RELAY.equals(TLCMem.stage())) {
            t.addPara("Without Bureau codes there is nothing more to do here.", Misc.getGrayColor());
        } else if (!TLCQuest.relayClear()) {
            t.addPara("The salvage gang's fleet is still in the system. You will not have time to work on the relay "
                    + "while they are around.", Misc.getNegativeHighlightColor(), "still in the system");
        } else {
            t.addPara("The Registrar's transmission key is in your hold, in a case the size of a ration tin, labeled in "
                    + "four languages.");
        }
        return true;
    }

    private boolean activateRelay(InteractionDialogAPI dialog) {
        if (!TLCIds.STAGE_RELAY.equals(TLCMem.stage()) || !TLCQuest.relayClear()) return false;
        TextPanelAPI t = dialog.getTextPanel();
        t.addPara("Your engineers seat the key in a socket at the base of the mast. For a long moment nothing happens.");
        t.addPara("Then the reactor spools up with a sound you feel through the hull, and the surviving panels light one "
                + "tier at a time, bottom to top. A carrier signal goes out on a band no one in the Sector monitors, "
                + "pointed at a Gate that has not answered since the Collapse. The relay reports itself READY.");
        TLCMem.setFlag(TLCIds.MEM_RELAY_ACTIVE, true);
        TLCQuest.setStage(TLCIds.STAGE_RELAY, t);
        return true;
    }

    // ------------------------------------------------------------------------------------ Dead Letter Office
    private boolean dloEnter(InteractionDialogAPI dialog) {
        TextPanelAPI t = dialog.getTextPanel();
        t.addPara("A boarding party cuts its way into the annex through a jammed cargo hatch. Inside, in the light of "
                + "their suit lamps, are the sorting floors: rack upon rack of message capsules, data slates, and real "
                + "paper in bundles tied with string, all of it frozen exactly where it was set down two hundred cycles "
                + "ago.");
        t.addPara("A placard above the main sorting table reads, in Domain standard: CORRESPONDENCE HELD PENDING ADDRESS "
                + "VERIFICATION. DO NOT DISCARD. EVERYTHING HERE IS SOMEBODY'S.", Misc.getGrayColor());
        return true;
    }

    private boolean dloRead(InteractionDialogAPI dialog) {
        TextPanelAPI t = dialog.getTextPanel();
        int mask = TLCMem.getInt(TLCIds.MEM_LETTERS_READ);
        List<Integer> unread = new ArrayList<Integer>();
        for (int i = 0; i < TLCCensusText.LETTERS.length; i++) {
            if ((mask & (1 << i)) == 0) unread.add(i);
        }
        if (unread.isEmpty()) {
            t.addPara("You have read every letter your party can reach without breaking open the sealed racks. The rest "
                    + "will have to stay where they are, waiting for their addresses.");
            return true;
        }
        int pick = unread.get(new Random().nextInt(unread.size()));
        TLCMem.setInt(TLCIds.MEM_LETTERS_READ, mask | (1 << pick));
        t.addPara(TLCCensusText.LETTERS[pick]);
        return true;
    }

    private boolean dloSearch(InteractionDialogAPI dialog) {
        TextPanelAPI t = dialog.getTextPanel();
        Color h = Misc.getHighlightColor();
        t.addPara("Behind the sorting floor is the annex's secure room, where registered and diplomatic mail was held. "
                + "Its door has failed open. Inside are crated weapon components consigned to the Tallyhouse armory and "
                + "never delivered, and a single envelope lying on its own on the duty clerk's desk.");
        t.addPara("The envelope is heavy cream paper, sealed with Bureau wax. It is addressed: %s. Below that, in a "
                + "smaller hand: %s", h, "To the Registrar of Assize", "Personal. To be opened by the addressee only.");
        TLCMem.setFlag(TLCIds.MEM_HAS_LETTER, true);
        TLCQuest.giveWeapons(TLCIds.WEAPON_FORECLOSURE, 2, t);
        TLCQuest.giveWeapons(TLCIds.WEAPON_WRIT, 4, t);
        TLCQuest.giveWeapons(TLCIds.WEAPON_ACCRUAL, 2, t);
        t.addPara("You take the letter with you. It seems wrong to leave it here.");
        return true;
    }
}
