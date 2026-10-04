package tlc.campaign;

import com.fs.starfarer.api.impl.campaign.econ.BaseMarketConditionPlugin;
import com.fs.starfarer.api.ui.TooltipMakerAPI;
import com.fs.starfarer.api.util.Misc;

/** The Tallyhouse is run entirely by Bureau automata: steady, incorruptible, slow. */
public class TLCAutomatedAdminCondition extends BaseMarketConditionPlugin {
    public static final float STABILITY_BONUS = 2f;

    @Override
    public void apply(String id) {
        if (market == null) return;
        market.getStability().modifyFlat(id, STABILITY_BONUS, "Automated administration");
    }

    @Override
    public void unapply(String id) {
        if (market == null) return;
        market.getStability().unmodifyFlat(id);
    }

    @Override
    protected void createTooltipAfterDescription(TooltipMakerAPI tooltip, boolean expanded) {
        super.createTooltipAfterDescription(tooltip, expanded);
        tooltip.addPara("%s stability", 10f, Misc.getHighlightColor(), "+" + (int) STABILITY_BONUS);
    }
}
