package tlc.campaign;

import com.fs.starfarer.api.EveryFrameScript;
import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.campaign.CampaignFleetAPI;
import com.fs.starfarer.api.campaign.FactionAPI;
import com.fs.starfarer.api.campaign.FleetAssignment;
import com.fs.starfarer.api.campaign.SectorEntityToken;
import com.fs.starfarer.api.campaign.econ.MarketAPI;
import com.fs.starfarer.api.campaign.rules.MemoryAPI;
import com.fs.starfarer.api.characters.FullName;
import com.fs.starfarer.api.characters.PersonAPI;
import com.fs.starfarer.api.impl.campaign.HasslePlayerScript;
import com.fs.starfarer.api.combat.ShipVariantAPI;
import com.fs.starfarer.api.fleet.FleetMemberAPI;
import com.fs.starfarer.api.impl.campaign.fleets.FleetFactoryV3;
import com.fs.starfarer.api.impl.campaign.fleets.FleetParamsV3;
import com.fs.starfarer.api.impl.campaign.ids.Factions;
import com.fs.starfarer.api.impl.campaign.ids.MemFlags;
import com.fs.starfarer.api.impl.campaign.ids.Personalities;
import com.fs.starfarer.api.impl.campaign.ids.Ranks;
import com.fs.starfarer.api.impl.campaign.ids.Tags;
import com.fs.starfarer.api.util.IntervalUtil;
import com.fs.starfarer.api.util.Misc;
import com.fs.starfarer.api.util.WeightedRandomPicker;
import org.apache.log4j.Logger;
import tlc.TLCIds;
import tlc.TLCSettings;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Random;

/**
 * Sector script. Keeps the Bureau's Assessor circuits flying, toggles whether they audit the player,
 * applies the hostility "statute of limitations", and drives the quest/Inspector-General ticks.
 */
public class TLCAssessorManager implements EveryFrameScript {
    private static final Logger log = Global.getLogger(TLCAssessorManager.class);

    private static final float SPAWN_INTERVAL_DAYS = 7f;
    private static final float BROADCAST_DELAY_DAYS = 3f;
    private static final float AMNESTY_INTERVAL_DAYS = 30f;
    private static final String MEM_RECALLED = "$tlc_recalled";

    private final IntervalUtil tracker = new IntervalUtil(0.4f, 0.6f);
    private final List<CampaignFleetAPI> assessors = new ArrayList<CampaignFleetAPI>();
    private float spawnCooldown = 1f;
    private float amnestyTimer = 0f;
    private float daysElapsed = 0f;

    @Override
    public void advance(float amount) {
        if (Global.getSector() == null || Global.getSector().isPaused()) return;
        float days = Global.getSector().getClock().convertToDays(amount);
        spawnCooldown -= days;
        amnestyTimer += days;
        daysElapsed += days;
        tracker.advance(days);
        if (!tracker.intervalElapsed()) return;
        try {
            TLCCensusIntel.ensureExists(daysElapsed >= BROADCAST_DELAY_DAYS);
            pruneDead();
            if (amnestyTimer >= AMNESTY_INTERVAL_DAYS) {
                amnestyTimer = 0f;
                applyAmnesty();
            }
            if (TLCMem.flag(TLCIds.MEM_AUDITS_ENDED)) {
                recallAll();
            } else {
                maintain();
            }
            updateHassleFlags();
            cleanupSeizedTags();
            TLCInspectorGeneral.advance();
            TLCQuest.advance();
        } catch (Throwable t) {
            log.error("TLC: Assessor manager tick failed", t);
        }
    }

    private void pruneDead() {
        Iterator<CampaignFleetAPI> it = assessors.iterator();
        while (it.hasNext()) {
            CampaignFleetAPI f = it.next();
            if (f == null || !f.isAlive()) it.remove();
        }
    }

    private void maintain() {
        if (!TLCMem.tallyhouseIntact()) return;
        if (assessors.size() >= TLCSettings.maxAssessorFleets()) return;
        if (spawnCooldown > 0f) return;
        spawnCooldown = SPAWN_INTERVAL_DAYS * (0.75f + (float) Math.random() * 0.5f);
        spawnAssessor();
    }

    public static boolean hassleAllowed() {
        return TLCSettings.auditsEnabled()
                && !TLCMem.flag(TLCIds.MEM_CERTIFIED)
                && !TLCMem.flag(TLCIds.MEM_COMMISSIONER)
                && !TLCMem.flag(TLCIds.MEM_AUDITS_ENDED);
    }

    private void updateHassleFlags() {
        boolean allow = hassleAllowed();
        for (CampaignFleetAPI f : assessors) {
            if (f == null || !f.isAlive()) continue;
            MemoryAPI mem = f.getMemoryWithoutUpdate();
            mem.set(MemFlags.WILL_HASSLE_PLAYER, allow);
            mem.set(MemFlags.HASSLE_TYPE, TLCIds.HASSLE_AUDIT);
            // An audit already in pursuit when audits became disallowed (certificate, commission, closure, setting):
            // mark it complete so vanilla HasslePlayerScript calls off the chase.
            if (!allow && mem.contains(MemFlags.MEMORY_KEY_PURSUE_PLAYER + "_hassle")) {
                mem.set(HasslePlayerScript.HASSLE_COMPLETE_KEY, true);
            }
        }
    }

    private void spawnAssessor() {
        MarketAPI home = TLCMem.tallyhouseMarket();
        if (home == null || home.getPrimaryEntity() == null) return;
        SectorEntityToken homeEntity = home.getPrimaryEntity();
        Random rand = new Random();
        List<MarketAPI> route = pickRoute(home, 2 + rand.nextInt(2), rand);
        if (route.isEmpty()) return;

        float years = Global.getSector().getClock().getCycle() - 206;
        float combat = 30f + rand.nextFloat() * 30f + Math.max(0f, Math.min(40f, years * 10f));
        FleetParamsV3 params = new FleetParamsV3(home, home.getLocationInHyperspace(), TLCIds.FACTION_BUREAU, 0.8f,
                TLCIds.TYPE_ASSESSOR_FLEET, combat, 0f, 0f, 0f, 0f, 0f, 0f);
        params.withOfficers = false;
        params.ignoreMarketFleetSizeMult = true;
        params.random = rand;
        CampaignFleetAPI fleet = FleetFactoryV3.createFleet(params);
        if (fleet == null || fleet.getFleetData().getNumMembers() <= 0) return;

        PersonAPI commander = createAssessorPerson(rand);
        fleet.setCommander(commander);
        if (fleet.getFlagship() != null) fleet.getFlagship().setCaptain(commander);

        MemoryAPI mem = fleet.getMemoryWithoutUpdate();
        mem.set(TLCIds.MEM_ASSESSOR_FLEET, true);
        mem.set(MemFlags.HASSLE_TYPE, TLCIds.HASSLE_AUDIT);
        mem.set(MemFlags.WILL_HASSLE_PLAYER, hassleAllowed());

        homeEntity.getContainingLocation().addEntity(fleet);
        fleet.setLocation(homeEntity.getLocation().x, homeEntity.getLocation().y);
        for (MarketAPI m : route) {
            fleet.addAssignment(FleetAssignment.GO_TO_LOCATION, m.getPrimaryEntity(), 120f,
                    "travelling to assess " + m.getName());
            fleet.addAssignment(FleetAssignment.ORBIT_PASSIVE, m.getPrimaryEntity(), 4f + rand.nextFloat() * 4f,
                    "conducting an assessment of " + m.getName());
        }
        fleet.addAssignment(FleetAssignment.GO_TO_LOCATION_AND_DESPAWN, homeEntity, 200f, "returning to the Tallyhouse");
        assessors.add(fleet);
    }

    private static PersonAPI createAssessorPerson(Random rand) {
        PersonAPI p = Global.getFactory().createPerson();
        p.setFaction(TLCIds.FACTION_BUREAU);
        p.setName(new FullName("Assessor", "Unit " + (100 + rand.nextInt(900)), FullName.Gender.ANY));
        p.setPortraitSprite(TLCIds.PORTRAIT_ASSESSOR);
        p.setRankId(Ranks.SPACE_COMMANDER);
        p.setPostId(Ranks.POST_PATROL_COMMANDER);
        p.setPersonality(Personalities.STEADY);
        return p;
    }

    private static List<MarketAPI> pickRoute(MarketAPI home, int count, Random rand) {
        List<MarketAPI> out = new ArrayList<MarketAPI>();
        FactionAPI bureau = TLCMem.bureau();
        if (bureau == null) return out;
        WeightedRandomPicker<MarketAPI> picker = new WeightedRandomPicker<MarketAPI>(rand);
        for (MarketAPI m : Global.getSector().getEconomy().getMarketsCopy()) {
            if (m == null || m == home || m.isHidden()) continue;
            if (m.getPrimaryEntity() == null || m.getContainingLocation() == null) continue;
            if (m.getContainingLocation().isHyperspace()) continue;
            if (m.getSize() < 3) continue;
            if (TLCIds.FACTION_BUREAU.equals(m.getFactionId())) continue;
            if (m.getFaction() == null || bureau.isHostileTo(m.getFaction())) continue;
            float w = m.getSize();
            if (m.isPlayerOwned()) w *= 1.5f;
            picker.add(m, w);
        }
        while (out.size() < count && !picker.isEmpty()) {
            out.add(picker.pickAndRemove());
        }
        // nearest-neighbour ordering from the Tallyhouse for a sensible circuit
        List<MarketAPI> ordered = new ArrayList<MarketAPI>();
        SectorEntityToken from = home.getPrimaryEntity();
        while (!out.isEmpty()) {
            MarketAPI best = null;
            float bestD = Float.MAX_VALUE;
            for (MarketAPI m : out) {
                float d = Misc.getDistanceLY(from.getLocationInHyperspace(), m.getLocationInHyperspace());
                if (d < bestD) {
                    bestD = d;
                    best = m;
                }
            }
            out.remove(best);
            ordered.add(best);
            from = best.getPrimaryEntity();
        }
        return ordered;
    }

    private void recallAll() {
        SectorEntityToken home = TLCMem.tallyhouse();
        for (CampaignFleetAPI f : assessors) {
            if (f == null || !f.isAlive()) continue;
            MemoryAPI mem = f.getMemoryWithoutUpdate();
            mem.set(MemFlags.WILL_HASSLE_PLAYER, false);
            if (mem.getBoolean(MEM_RECALLED)) continue;
            mem.set(MEM_RECALLED, true);
            f.clearAssignments();
            if (home != null) {
                f.addAssignment(FleetAssignment.GO_TO_LOCATION_AND_DESPAWN, home, 200f, "recalled to the Tallyhouse");
            } else {
                Misc.giveStandardReturnToSourceAssignments(f);
            }
        }
    }

    /**
     * A Writ of Seizure only guarantees recovery from the battle it was served in. Once a seized ship has joined the
     * player's fleet, strip the tags again so it does not stay always-recoverable forever.
     */
    private void cleanupSeizedTags() {
        CampaignFleetAPI pf = Global.getSector().getPlayerFleet();
        if (pf == null) return;
        for (FleetMemberAPI m : pf.getFleetData().getMembersListCopy()) {
            ShipVariantAPI v = m.getVariant();
            if (v == null || !v.hasTag(TLCIds.SEIZED_TAG)) continue;
            v.removeTag(TLCIds.SEIZED_TAG);
            v.removeTag(Tags.VARIANT_ALWAYS_RECOVERABLE);
        }
    }

    /** "Statute of limitations": hostility with the Bureau decays toward Inhospitable once a month. */
    private void applyAmnesty() {
        FactionAPI b = TLCMem.bureau();
        if (b == null) return;
        float rel = b.getRelationship(Factions.PLAYER);
        if (rel > -0.5f) return;
        float newRel = Math.min(-0.45f, rel + 0.15f);
        b.setRelationship(Factions.PLAYER, newRel);
        if (Global.getSector().getCampaignUI() != null) {
            Global.getSector().getCampaignUI().addMessage(
                    "The Assessment Bureau has applied the statute of limitations to some of your outstanding penalties.",
                    Misc.getTextColor(), "statute of limitations", "", Misc.getHighlightColor(), Misc.getHighlightColor());
        }
    }

    @Override
    public boolean isDone() {
        return false;
    }

    @Override
    public boolean runWhilePaused() {
        return false;
    }
}
