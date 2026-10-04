package tlc.rulecmd;

import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.campaign.CampaignFleetAPI;
import com.fs.starfarer.api.campaign.InteractionDialogAPI;
import com.fs.starfarer.api.campaign.TextPanelAPI;
import com.fs.starfarer.api.campaign.rules.MemoryAPI;
import com.fs.starfarer.api.characters.PersonAPI;
import com.fs.starfarer.api.impl.campaign.rulecmd.BaseCommandPlugin;
import com.fs.starfarer.api.util.Misc;
import com.fs.starfarer.api.util.Misc.Token;
import org.apache.log4j.Logger;
import tlc.TLCIds;
import tlc.campaign.TLCInspectorGeneral;
import tlc.campaign.TLCMem;

import java.util.List;
import java.util.Map;

/** TLCHearingCMD &lt;active|greet|submit|defer&gt; - the Inspector-General's hearing. */
public class TLCHearingCMD extends BaseCommandPlugin {
    private static final Logger log = Global.getLogger(TLCHearingCMD.class);

    @Override
    public boolean execute(String ruleId, InteractionDialogAPI dialog, List<Token> params, Map<String, MemoryAPI> memoryMap) {
        if (dialog == null || params == null || params.isEmpty()) return false;
        String cmd = params.get(0).getString(memoryMap);
        if ("active".equals(cmd)) {
            String s = TLCMem.igState();
            return TLCIds.IG_DISPATCHED.equals(s) || TLCIds.IG_WAITING.equals(s);
        }
        TextPanelAPI t = dialog.getTextPanel();
        try {
            if ("greet".equals(cmd)) return greet(dialog, t);
            if ("submit".equals(cmd)) return submit(t);
            if ("defer".equals(cmd)) return defer(dialog, t);
            log.warn("TLC: unknown hearing command " + cmd);
        } catch (Throwable e) {
            log.error("TLC: hearing command failed: " + cmd, e);
        }
        return false;
    }

    private boolean greet(InteractionDialogAPI dialog, TextPanelAPI t) {
        PersonAPI ig = TLCInspectorGeneral.getOrCreateInspector();
        dialog.getVisualPanel().showPersonInfo(ig, true);
        if (TLCIds.IG_WAITING.equals(TLCMem.igState())) {
            t.addPara("The black-and-gold terminal answers at once, as if it had been waiting with its hand on the "
                    + "switch. \"Master of vessels. You have come to give evidence?\"");
            return true;
        }
        t.addPara("The comm display is black lacquer and gold leaf around an amber lens, half shuttered like a "
                + "heavy-lidded eye. The voice is a woman's, dry and exact, with an accent no living person in the "
                + "Sector has ever heard.");
        t.addPara("\"I am Ismene Varga, Inspector-General of the Persean office. Or I am the record the Bureau kept of "
                + "her, which for the purposes of this hearing amounts to the same thing.\"");
        t.addPara("\"Three of my Assessors have recorded the same testimony from you: that the Domain no longer exists. "
                + "Testimony is not evidence. I have come to examine the evidence.\"");
        if (TLCMem.flag(TLCIds.MEM_AUDITS_ENDED)) {
            t.addPara("\"I am aware that the Registrar has closed the Grand Audit. The Office of the Inspector-General "
                    + "does not close when an audit does. A referral, once filed, is heard.\"");
        }
        t.addPara("\"The hypothesis is simple. If the Domain still stands, no unregistered fleet could defeat an officer "
                + "of the Bureau. If you can defeat me, then the Domain is not standing behind me.\" The lens opens a "
                + "fraction wider. \"Shall we proceed?\"", Misc.getHighlightColor(), "If you can defeat me");
        return true;
    }

    private boolean submit(TextPanelAPI t) {
        t.addPara("\"Very well.\" Somewhere behind the voice, a gavel strikes wood: a recording, two hundred cycles old. "
                + "\"This hearing is in session.\"");
        return true;
    }

    private boolean defer(InteractionDialogAPI dialog, TextPanelAPI t) {
        t.addPara("\"A continuance, then. The hearing is adjourned.\" The lens narrows. \"I will hold session in orbit of "
                + "Assize. Present yourself when you are ready to give evidence. I have been patient for two hundred "
                + "cycles; I can be patient a little longer.\"");
        if (dialog.getInteractionTarget() instanceof CampaignFleetAPI) {
            TLCInspectorGeneral.sendHomeToWait((CampaignFleetAPI) dialog.getInteractionTarget());
        }
        return true;
    }
}
