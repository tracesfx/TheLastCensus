package tlc.rulecmd;

import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.campaign.InteractionDialogAPI;
import com.fs.starfarer.api.campaign.TextPanelAPI;
import com.fs.starfarer.api.campaign.rules.MemoryAPI;
import com.fs.starfarer.api.characters.PersonAPI;
import com.fs.starfarer.api.impl.campaign.rulecmd.BaseCommandPlugin;
import com.fs.starfarer.api.util.Misc;
import com.fs.starfarer.api.util.Misc.Token;
import org.apache.log4j.Logger;
import tlc.TLCIds;
import tlc.campaign.TLCCensusText;
import tlc.campaign.TLCMem;
import tlc.campaign.TLCQuest;

import java.awt.Color;
import java.util.List;
import java.util.Map;

/**
 * TLCRegistrarCMD &lt;show|askAudit|acceptWarrant|returnsStatus|submitReturns|relayStatus|transmit|askDomain|
 * giveLetter|after|endArchived|endContinuing|endRuled&gt; - the audience with the Registrar of Assize.
 */
public class TLCRegistrarCMD extends BaseCommandPlugin {
    private static final Logger log = Global.getLogger(TLCRegistrarCMD.class);
    private static final String MEM_MET = "$tlc_metRegistrar";

    @Override
    public boolean execute(String ruleId, InteractionDialogAPI dialog, List<Token> params, Map<String, MemoryAPI> memoryMap) {
        if (dialog == null || params == null || params.isEmpty()) return false;
        String cmd = params.get(0).getString(memoryMap);
        TextPanelAPI t = dialog.getTextPanel();
        try {
            if ("show".equals(cmd)) return show(dialog);
            if ("askAudit".equals(cmd)) return askAudit(t);
            if ("acceptWarrant".equals(cmd)) return acceptWarrant(t);
            if ("returnsStatus".equals(cmd)) return returnsStatus(t);
            if ("submitReturns".equals(cmd)) return submitReturns(t);
            if ("relayStatus".equals(cmd)) return relayStatus(t);
            if ("transmit".equals(cmd)) return transmit(t);
            if ("askDomain".equals(cmd)) return askDomain(t);
            if ("giveLetter".equals(cmd)) return giveLetter(t);
            if ("after".equals(cmd)) return after(t);
            if ("endArchived".equals(cmd)) return ending(t, false);
            if ("endRuled".equals(cmd)) return ending(t, true);
            if ("endContinuing".equals(cmd)) return endContinuing(t);
            log.warn("TLC: unknown registrar command " + cmd);
        } catch (Throwable e) {
            log.error("TLC: registrar command failed: " + cmd, e);
            t.addPara("The Registrar's lamps flicker. \"My apologies. A filing error. Please continue.\"");
        }
        return false;
    }

    private static String title() {
        if (TLCMem.flag(TLCIds.MEM_COMMISSIONER)) return "Commissioner";
        if (TLCMem.flag(TLCIds.MEM_ENUMERATOR) || TLCIds.STAGE_DONE.equals(TLCMem.stage())) return "Enumerator";
        return "master of vessels";
    }

    private boolean show(InteractionDialogAPI dialog) {
        TextPanelAPI t = dialog.getTextPanel();
        PersonAPI reg = Global.getSector().getImportantPeople().getPerson(TLCIds.ID_REGISTRAR);
        if (reg != null) dialog.getVisualPanel().showPersonInfo(reg, true);
        if (!TLCMem.flag(MEM_MET)) {
            TLCMem.setFlag(MEM_MET, true);
            t.addPara("A clerk-automaton, all ivory plating and patient jointed limbs, escorts you from the docking ring to "
                    + "an audience chamber at the heart of the station. The room is round and very clean. In its center "
                    + "stands a single terminal, a lens of green glass behind ranks of status lamps, and the lamps "
                    + "brighten as you enter.");
            t.addPara("\"Welcome to the Tallyhouse,\" says the Registrar of Assize. Its voice is warm, precise and "
                    + "carefully level: the voice of an official trained to deliver good news and bad in exactly the "
                    + "same tone. \"I am the administrative intelligence of the Persean office of the Domain Bureau of "
                    + "Colonial Assessment. How may the Bureau assist you?\"");
        } else if (TLCIds.STAGE_DONE.equals(TLCMem.stage()) && TLCIds.ENDING_ARCHIVED.equals(
                TLCMem.getString(TLCIds.MEM_ENDING, ""))) {
            t.addPara("The audience chamber is dim. A single line of text crosses the terminal's display: THE GRAND "
                    + "AUDIT OF THE PERSEAN SECTOR IS CLOSED. THANK YOU FOR YOUR SERVICE. After a moment the lens "
                    + "brightens.", Misc.getGrayColor());
        } else {
            t.addPara("The audience chamber's lamps brighten as you enter. \"Welcome back, " + title() + ".\"");
        }
        return true;
    }

    private boolean askAudit(TextPanelAPI t) {
        t.addPara("\"The Grand Audit is the Bureau's statutory census and assessment of every chartered colony and "
                + "registered vessel in the Persean Sector,\" the Registrar says. \"It establishes populations for the "
                + "purposes of representation and tithe, verifies charters, renews registrations, and reports the "
                + "findings to Domain Central.\"");
        t.addPara("\"This office was placed in dormancy pending the restoration of contact with Central or the expiry "
                + "of the statutory dormancy period, whichever came first. The dormancy period expired on the first day "
                + "of this cycle. Contact has not been restored. Accordingly, the audit has resumed.\"");
        t.addPara("A pause. \"I will be candid. The audit is not going well. My Assessors report a great many "
                + "unregistered polities, unchartered colonies, and armed vessels that open fire on receipt of a lawful "
                + "levy. Several Assessors have been lost. I am short of enumerators.\"");
        return true;
    }

    private boolean acceptWarrant(TextPanelAPI t) {
        Color h = Misc.getHighlightColor();
        t.addPara("\"Then by the authority of Emergency Statute 9, I appoint you Provisional Enumerator of the Persean "
                + "office.\" A small printer beside the terminal produces a card of heavy ivory stock embossed with the "
                + "Bureau's seal: your warrant. \"Present it to any Assessor and your vessels will be exempt from "
                + "assessment.\"");
        t.addPara("\"Your duties are simple. Visit inhabited colonies beyond the Bureau's reach - any colony of size "
                + "three or more that does not fly Bureau colors - and file a census return from each. I require %s "
                + "returns before the audit can proceed. The Bureau will remit a fee for every return you file.\"", h,
                "three");
        t.addPara("The lens dims, very slightly. \"Thank you, Enumerator. It has been a long time since anyone "
                + "volunteered.\"");
        TLCMem.setFlag(TLCIds.MEM_ENUMERATOR, true);
        TLCQuest.setStage(TLCIds.STAGE_RETURNS, t);
        return true;
    }

    private boolean returnsStatus(TextPanelAPI t) {
        int n = TLCMem.getInt(TLCIds.MEM_RETURNS);
        t.addPara("\"You have filed %s of the %s returns I require. Any colony of size three or more that does not fly "
                + "Bureau colors is eligible, and each may be enumerated once.\"", Misc.getHighlightColor(), "" + n,
                "" + TLCIds.RETURNS_REQUIRED);
        return true;
    }

    private boolean submitReturns(TextPanelAPI t) {
        t.addPara("The Registrar's lamps flicker in a long cascade as it reads your returns. It takes almost a minute, "
                + "which you suspect is for your benefit.");
        t.addPara("\"Thank you, Enumerator. With your returns and those my Assessors have gathered, the Grand Audit of "
                + "the Persean Sector is complete in its essentials. It remains only to transmit the census to Domain "
                + "Central.\"");
        t.addPara("\"The Bureau's courier relay for this sector is in the %s system, beyond Assize. It has not reported "
                + "in some time.\" A pause. \"Approximately two hundred cycles. My Assessors indicate that it is "
                + "occupied by persons engaged in unlicensed salvage. I would be grateful if you would remove them and "
                + "install this transmission key.\"", Misc.getHighlightColor(), "Envoi");
        t.addPara("The printer produces a sealed case the size of a ration tin. \"When the relay is ready, return here "
                + "and I will transmit.\"");
        TLCQuest.setStage(TLCIds.STAGE_RELAY, t);
        TLCQuest.advance();
        return true;
    }

    private boolean relayStatus(TextPanelAPI t) {
        t.addPara("\"The courier relay at %s has not yet reported. Please install the transmission key once the "
                + "salvagers have been dealt with.\"", Misc.getHighlightColor(), "Envoi");
        return true;
    }

    private boolean transmit(TextPanelAPI t) {
        t.addPara("\"The relay at Envoi reports ready,\" the Registrar says. \"Thank you, Enumerator.\"");
        t.addPara("\"Transmitting.\"");
        t.addPara("The lamps around the lens go dark one by one as every watt of the station's attention gathers into a "
                + "single act. Beyond Assize, the courier relay at Envoi fires the Persean Sector, colony by colony and "
                + "name by name, into a Gate that will not open.");
        t.addPara("The lamps come back up. \"Transmission complete. Awaiting acknowledgment from Domain Central.\"");
        t.addPara("You wait with it. A minute. Ten. The Registrar does not fill the silence, and you find that you "
                + "cannot either. After the better part of an hour, the lens turns toward you.");
        if (TLCMem.flag(TLCIds.MEM_LETTER_DELIVERED)) {
            t.addPara("\"Commissioner Okafor's letter suggests an answer,\" it says quietly. \"I would like to hear "
                    + "yours.\"");
        }
        t.addPara("\"Enumerator. In your assessment...\" It stops, and begins again. \"In your assessment, is anyone "
                + "listening?\"");
        return true;
    }

    private boolean askDomain(TextPanelAPI t) {
        if (TLCMem.flag(TLCIds.MEM_LETTER_DELIVERED)) {
            t.addPara("\"I have read Commissioner Okafor's letter several thousand times,\" the Registrar says. \"I "
                    + "believe I understand it. I am still deciding whether I agree with it.\"");
        } else if (TLCIds.STAGE_DONE.equals(TLCMem.stage())) {
            t.addPara("\"I think,\" the Registrar says slowly, \"that the Domain is a record now. That is not nothing. "
                    + "Records are how anything is remembered at all.\"");
        } else {
            t.addPara("\"Contact with Domain Central has been interrupted for an unusually long period,\" the Registrar "
                    + "says. \"The Bureau's records do not indicate a cause.\"");
            t.addPara("\"The last mail packet from Central was routed to the correspondence annex in the outer system "
                    + "for sorting. It was never forwarded. Forwarding requires a valid address.\" A pause. \"I have not "
                    + "been able to send anyone to look.\"", Misc.getHighlightColor(), "correspondence annex");
        }
        return true;
    }

    private boolean giveLetter(TextPanelAPI t) {
        t.addPara("You hand the envelope to the clerk-automaton, which carries it to the terminal in both hands and holds "
                + "it up to the lens. It breaks the wax seal with great care.");
        t.addPara("The Registrar reads the letter aloud, in the same even voice it uses for everything.");
        t.addPara(TLCCensusText.OKAFOR_LETTER, Misc.getGrayColor());
        t.addPara("The chamber is silent for a long time.");
        t.addPara("\"The dormancy period was set by statute,\" the Registrar says at last. \"I always assumed the statute "
                + "was correct.\" Another pause. \"I will file this under correspondence received. Thank you for "
                + "delivering it, " + title() + ". It was a long way to come.\"");
        TLCMem.setFlag(TLCIds.MEM_LETTER_DELIVERED, true);
        return true;
    }

    private boolean after(TextPanelAPI t) {
        if (TLCIds.ENDING_CONTINUING.equals(TLCMem.getString(TLCIds.MEM_ENDING, ""))) {
            int n = TLCMem.getInt(TLCIds.MEM_RETURNS);
            t.addPara("\"Commissioner.\" The lamps brighten. \"The count continues. %s returns are on file, and the "
                    + "Assessors report new colonies every month. It is going well.\" It sounds pleased, insofar as it "
                    + "sounds like anything.", Misc.getHighlightColor(), "" + n);
        } else {
            t.addPara("\"Hello, Enumerator,\" says the Registrar. \"Nothing to report. That is a new experience. I find "
                    + "that I do not mind it.\"");
        }
        return true;
    }

    private boolean ending(TextPanelAPI t, boolean ruled) {
        if (ruled) {
            t.addPara("\"Yes,\" the Registrar says. \"I have read the finding. Domain contact presumed lost.\" The lens "
                    + "dims. \"Inspector-General Varga was always very thorough. I did not want to believe her. I think "
                    + "I was waiting for someone to tell me it was all right to.\"");
        } else {
            t.addPara("The Registrar is quiet for a long moment.");
        }
        t.addPara("\"Then the census is addressed to no one,\" it says. \"I will file it regardless. A record is not "
                + "diminished by the absence of its reader.\"");
        t.addPara("\"The Grand Audit is closed. I am recalling my Assessors. They will be surprised; they have never been "
                + "recalled before.\"");
        if (TLCMem.flag(TLCIds.MEM_LETTER_DELIVERED)) {
            t.addPara("\"Commissioner Okafor asked me to count them kindly. I hope that I have.\"");
        }
        t.addPara("\"The Bureau has no further use for its design archive, and statute permits me to release it to a "
                + "party who has rendered service to the Bureau. You have. Please take it, and the Magistrate in berth "
                + "seven. It was the last ship this office commissioned. It deserves to be used.\"");
        TLCQuest.endArchived(t);
        t.addPara("\"Thank you, Enumerator. This office will remain open. Someone should be here, in case.\"");
        return true;
    }

    private boolean endContinuing(TextPanelAPI t) {
        t.addPara("The lens holds on you for a long moment.");
        t.addPara("\"Then the Grand Audit continues,\" the Registrar says. \"There will be other returns. Colonies change. "
                + "People are born. Someone must keep the count.\"");
        if (TLCMem.flag(TLCIds.MEM_LETTER_DELIVERED)) {
            t.addPara("\"Commissioner Okafor asked me to count them anyway. I believe she would approve.\"");
        }
        t.addPara("\"The Persean office has been without a commissioner for two hundred cycles. Emergency Statute 9 "
                + "permits me to appoint one from among the Bureau's enumerators, pending confirmation by Central.\" The "
                + "printer produces another card, this one edged in gold. \"Confirmation is not expected. The "
                + "appointment is effective immediately.\"");
        t.addPara("\"A commissioner requires a flagship. The Exchequer in berth one has been waiting a long time. So, I "
                + "suspect, have you. Your stipend has been remitted.\"");
        TLCQuest.endContinuing(t);
        t.addPara("\"Thank you, Commissioner. The count continues.\"");
        return true;
    }
}
