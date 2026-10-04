package tlc.campaign;

import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.campaign.FactionAPI;
import com.fs.starfarer.api.campaign.SectorEntityToken;
import com.fs.starfarer.api.campaign.econ.MarketAPI;
import com.fs.starfarer.api.campaign.rules.MemoryAPI;
import tlc.TLCIds;

/** Thin helpers around global (sector) memory, the single source of truth for quest state. */
public final class TLCMem {
    private TLCMem() {
    }

    public static MemoryAPI global() {
        return Global.getSector().getMemoryWithoutUpdate();
    }

    public static boolean flag(String key) {
        return global().getBoolean(key);
    }

    public static void setFlag(String key, boolean value) {
        global().set(key, value);
    }

    public static void setFlag(String key, boolean value, float days) {
        global().set(key, value, days);
    }

    public static int getInt(String key) {
        Object o = global().get(key);
        if (o instanceof Number) return ((Number) o).intValue();
        if (o instanceof String) {
            try {
                return Integer.parseInt((String) o);
            } catch (NumberFormatException ignored) {
                return 0;
            }
        }
        return 0;
    }

    public static void setInt(String key, int value) {
        global().set(key, value);
    }

    public static int increment(String key) {
        int v = getInt(key) + 1;
        setInt(key, v);
        return v;
    }

    public static String getString(String key, String def) {
        String s = global().getString(key);
        return s == null || s.isEmpty() ? def : s;
    }

    public static void setString(String key, String value) {
        global().set(key, value);
    }

    public static String stage() {
        return getString(TLCIds.MEM_STAGE, TLCIds.STAGE_BROADCAST);
    }

    public static String igState() {
        return getString(TLCIds.MEM_IG_STATE, TLCIds.IG_NONE);
    }

    public static FactionAPI bureau() {
        return Global.getSector().getFaction(TLCIds.FACTION_BUREAU);
    }

    public static MarketAPI tallyhouseMarket() {
        if (Global.getSector().getEconomy() == null) return null;
        return Global.getSector().getEconomy().getMarket(TLCIds.ID_TALLYHOUSE_MARKET);
    }

    public static SectorEntityToken tallyhouse() {
        MarketAPI m = tallyhouseMarket();
        if (m != null && m.getPrimaryEntity() != null) return m.getPrimaryEntity();
        return Global.getSector().getEntityById(TLCIds.ID_TALLYHOUSE_ENTITY);
    }

    public static SectorEntityToken relay() {
        return Global.getSector().getEntityById(TLCIds.ID_RELAY_ENTITY);
    }

    /** True if the Tallyhouse still exists and still belongs to the Bureau. */
    public static boolean tallyhouseIntact() {
        MarketAPI m = tallyhouseMarket();
        return m != null && TLCIds.FACTION_BUREAU.equals(m.getFactionId()) && m.getPrimaryEntity() != null;
    }
}
