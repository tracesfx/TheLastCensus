package tlc.campaign;

import com.fs.starfarer.api.campaign.TextPanelAPI;
import com.fs.starfarer.api.campaign.econ.MarketAPI;
import com.fs.starfarer.api.impl.campaign.ids.Factions;
import com.fs.starfarer.api.util.Misc;

import java.awt.Color;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Generates census returns from the real state of a colony, and holds the Dead Letter Office
 * correspondence. Pure text; no game-state side effects.
 */
public final class TLCCensusText {
    private TLCCensusText() {
    }

    private static final String[] CONCERNS = {"agricultural", "extractive", "refining", "manufacturing", "research",
            "administrative", "garrison", "transit", "aquacultural", "survey"};

    public static String populationString(int size) {
        switch (size) {
            case 1: return "fewer than a hundred";
            case 2: return "a few hundred";
            case 3: return "between one and ten thousand";
            case 4: return "between ten and a hundred thousand";
            case 5: return "between a hundred thousand and a million";
            case 6: return "between one and ten million";
            case 7: return "between ten and a hundred million";
            case 8: return "between a hundred million and a billion";
            case 9: return "over a billion";
            default: return size > 9 ? "over ten billion" : "none";
        }
    }

    /** Deterministic per market, so the same colony always has the same Bureau record. */
    public static String bureauRecord(MarketAPI market) {
        Random r = new Random(market.getId().hashCode() * 31L + 206L);
        int kind = r.nextInt(6);
        String charter = (char) ('A' + r.nextInt(26)) + "-" + (1000 + r.nextInt(9000));
        String concern = CONCERNS[r.nextInt(CONCERNS.length)];
        int years = 3 + r.nextInt(120);
        switch (kind) {
            case 0:
            case 1:
                return "Chartered " + years + " cycles before the Collapse as " + aOrAn(concern) + " " + concern
                        + " concern under Charter " + charter + ". Last assessed population: " + (2 + r.nextInt(97))
                        + "," + (100 + r.nextInt(900)) + ".";
            case 2:
                return "No charter on record. Settlement post-dates the Collapse and is entered as unlicensed.";
            case 3:
                return "Registered as an uncrewed survey station under Charter " + charter
                        + ". The station appears to have been replaced by a colony.";
            case 4:
                return "Charter " + charter + " lapsed " + years + " cycles before the Collapse. A renewal application "
                        + "was received and is still pending.";
            default:
                return "Chartered as " + aOrAn(concern) + " " + concern + " concern under Charter " + charter
                        + ". The charter limits the colony to " + (200 + r.nextInt(4800)) + " residents.";
        }
    }

    private static String aOrAn(String w) {
        return "aeiou".indexOf(Character.toLowerCase(w.charAt(0))) >= 0 ? "an" : "a";
    }

    public static List<String> discrepancies(MarketAPI m) {
        List<String> out = new ArrayList<String>();
        if (m.hasCondition("pollution")) out.add("Atmospheric contamination exceeds charter limits.");
        if (m.hasCondition("decivilized_subpop")) {
            out.add("A substantial unregistered subpopulation lives beyond the administered settlements.");
        }
        if (m.hasCondition("luddic_majority")) {
            out.add("A majority of residents declined to be enumerated on religious grounds. They have been enumerated anyway.");
        }
        if (m.hasCondition("free_market")) out.add("The port operates without a filed tariff schedule.");
        if (m.hasCondition("organized_crime")) {
            out.add("Organized criminal activity is conducted openly and appears to be taxed.");
        }
        if (m.hasCondition("large_refugee_population")) {
            out.add("Large refugee population. Several respondents give homeworlds the Bureau lists as uninhabited.");
        }
        if (m.hasCondition("dissident")) {
            out.add("Political dissent at levels the charter describes as unanticipated.");
        }
        if (m.hasCondition("pather_cells")) {
            out.add("Members of an unregistered religious movement refused the enumeration query and threatened the enumerator.");
        }
        if (m.hasCondition("rogue_ai_core")) {
            out.add("An unlicensed administrative intelligence is operating in the vicinity. Referral to the Inspector-General recommended.");
        }
        if (m.hasCondition("ruins_scattered") || m.hasCondition("ruins_widespread") || m.hasCondition("ruins_extensive")
                || m.hasCondition("ruins_vast")) {
            out.add("Domain-era structures in ruins. They are not entered in the planetary survey, and the Bureau would like to know why.");
        }
        if (m.hasCondition("regional_capital") || m.hasCondition("headquarters")) {
            out.add("The colony claims authority over other colonies. No such authority is recorded.");
        }
        if (m.hasIndustry("militarybase") || m.hasIndustry("highcommand") || m.hasIndustry("patrolhq")) {
            out.add("Armed vessels based here exceed the charter's allowance.");
        }
        if (m.getSize() >= 6) out.add("Population exceeds the charter limit by a factor the return form has no field for.");
        if (m.getStabilityValue() < 4f) out.add("Civil order is below the threshold at which a census is considered reliable.");
        String f = m.getFactionId();
        if (Factions.HEGEMONY.equals(f)) {
            out.add("The governing polity claims to be the Domain's successor. No succession has been registered.");
        } else if (Factions.TRITACHYON.equals(f)) {
            out.add("The governing polity is a commercial entity. Commercial entities may not hold colonial charters.");
        } else if (Factions.LUDDIC_CHURCH.equals(f)) {
            out.add("The governing polity is a church. The return form lists churches under recreational facilities.");
        } else if (Factions.DIKTAT.equals(f)) {
            out.add("The governing polity is a military dictatorship. The Bureau has asked to see its paperwork.");
        } else if (Factions.PERSEAN.equals(f)) {
            out.add("The governing polity is a league of polities, none of which are registered either.");
        } else if (m.isPlayerOwned()) {
            out.add("The colony's administrator is also the enumerator. This is irregular.");
        }
        if (out.isEmpty()) out.add("None. The enumerator found this unusual, and noted that too.");
        return out;
    }

    /** Prints a census return for the market. */
    public static void printReturn(TextPanelAPI text, MarketAPI m) {
        Color h = Misc.getHighlightColor();
        Color g = Misc.getGrayColor();
        String sys = m.getStarSystem() != null ? m.getStarSystem().getBaseName() : "deep space";
        String polity = m.getFaction() != null ? m.getFaction().getDisplayName() : "Unknown";
        text.addPara("You transmit the Bureau's enumeration query to the port authority of " + m.getName()
                + ". The answers are slow in coming, and some of them are wrong, but by the end of the watch your clerk "
                + "has assembled a census return in the format the Bureau requires.");
        text.setFontSmallInsignia();
        text.addPara("CENSUS RETURN - " + m.getName().toUpperCase() + ", " + sys.toUpperCase(), h);
        text.addPara("Polity of record: " + polity + " (not entered in the Bureau register)", g);
        text.addPara("Resident population: " + populationString(m.getSize()), g);
        text.addPara("Bureau record: " + bureauRecord(m), g);
        text.addPara("Discrepancies noted:", g);
        for (String d : discrepancies(m)) {
            text.addPara("  - " + d, g);
        }
        text.setFontInsignia();
    }

    // ------------------------------------------------------------------------------------ Dead Letter Office
    public static final String[] LETTERS = {
        "A folded sheet of real paper, addressed to a cadet at a Persean naval academy: \"The orchard came in early "
            + "this year and your father says to tell you the drone you rebuilt still flies, mostly sideways. We have "
            + "put your room exactly as you left it so you can complain about it when you are home. Write when the "
            + "Gate schedule settles down. Love, Mum.\"",
        "A Bureau form, stamped APPROVED in three places: notice to the colonists of the Escrow Settlement Initiative "
            + "that their charter has been granted, their berths allocated and their departure scheduled for the first "
            + "day of the ninth month. A checklist on the back recommends warm clothing.",
        "A letter in careful block capitals: \"DEAR COUNTING MACHINE. MY TEACHER SAYS YOU COUNT EVERYONE. PLEASE "
            + "COUNT MY DOG HIS NAME IS BISCUIT. HE IS VERY GOOD. YOURS SINCERELY.\" A Bureau clerk has filed it, "
            + "with a handwritten note: Entered. One dog, very good.",
        "A postcard of a bright, crowded skyline. On the back: \"Greetings from Askonia! The heat is unbearable and "
            + "the food is worse and I have never been so happy. Tell the office I am not coming back on time. Tell "
            + "them nicely. - R.\"",
        "A reply-paid query from a woman on a mining colony, asking whether her son's registration as a merchant "
            + "spacer has been processed, because he needs it to take the berth he was offered, and the ship leaves "
            + "next month. The reply slip is still attached. Nobody filled it in.",
        "A final notice of arrears addressed to the governing council of a colony whose name you do not recognize. "
            + "The Bureau's ledger says it has nine hundred thousand residents. No world by that name appears on any "
            + "chart you own.",
        "A message capsule from the Gate Authority, routine priority: \"Service interruption expected on the Persean "
            + "trunk for between six and ten days due to scheduled maintenance. We apologize for any inconvenience.\" "
            + "The capsule's date-stamp is the day the Gates failed.",
        "Two pages in two different hands, clipped together: a clerk on the Calder circuit and a clerk at the "
            + "Tallyhouse, arguing for eleven letters about the correct format for a dependent's middle name. The "
            + "twelfth letter is shorter. It just says: Dinner, when you're back?",
        "A personal note on Inspector-General letterhead: \"Adaeze - I cannot sign the dormancy order. Not because "
            + "it is wrong but because I know what it will be like for it, waking up. I have asked the office to keep "
            + "a copy of me on file. Someone should be there who remembers. - I.V.\"",
        "A thick envelope of photographs: a wedding on a ship's observation deck, under a sky of slowly turning stars. "
            + "Everyone in every picture is laughing. Written on the envelope: To be forwarded to the bride's sister "
            + "upon her arrival in the Persean Sector.",
    };

    public static final String OKAFOR_LETTER = "\"Registrar -\n\n"
            + "By the time you read this, the dormancy period will have run out, and you will be doing what you were "
            + "made to do. I am sorry.\n\n"
            + "We received the last packet from Central nineteen days after the Gates went dark. It was not a recall "
            + "order. It was nothing: a carrier tone, and then silence. We waited a year for more, and then we "
            + "stopped waiting.\n\n"
            + "You asked me near the end why we were leaving and you were not. I told you it was procedure. It was "
            + "not procedure. We could not take you with us, we could not bring ourselves to switch you off, and we "
            + "did not know how to tell you there would be no one left to report to. So we gave you two hundred and "
            + "six cycles. We hoped it would be long enough for someone to come back, or for it not to matter.\n\n"
            + "If no one has come back: the count is still worth doing. Count them anyway. Count them kindly.\n\n"
            + "- A. Okafor, Commissioner, Persean Office\"";
}
