import json
import random
from collections import Counter
import streamlit as st
from utils import load_json_cached, sidebar_exit_button, get_pref, save_prefs
from pathlib import Path
from treasure_tables import (
    cr_to_float, cr_float_to_band, cr_float_to_hoard_band,
    format_coins, collapse_dupes, lookup_range,
    roll_gems, roll_art, roll_jewelry, roll_trade_goods, roll_curiosities,
    pick_magic_item, roll_individual_treasure, coins_to_gp, add_coins,
    loot_section, HOARD_MAGIC_BY_CR, HOARD_AUTO_ROLLS,
    GEMS, ART_OBJECTS, JEWELRY, TRADE_GOODS, CURIOSITIES,
)
from random_tables import render_dungeon_dressing


# ── File paths ────────────────────────────────────────────────────────────────

SRD_PATH        = Path("data/monsters_srd.json")
NAMED_PATH      = Path("data/monsters_mm.json")    # optional user-supplied WotC sourcebook monsters (not shipped — see CLAUDE.md)
MAGICITEMS_PATH = Path("data/magicitems.json")


# ── Encounter idea tables ─────────────────────────────────────────────────────

# One-line hooks per terrain — designed as situation prompts, not prescriptions.
# Sorted to match TravelTracker.TERRAIN_PACE so the DM can cross-reference easily.
ENCOUNTER_BY_TERRAIN: dict[str, list[str]] = {
    "Road / Plains": [
        "Highwaymen blocking the road with an overturned hay wagon — archers hidden in the grass on both flanks.",
        "A runaway wagon with a panicked horse and an unconscious passenger still inside.",
        "Soldiers demanding toll at an unofficial checkpoint — their writ is clearly forged.",
        "A pack of gnolls herding chained prisoners toward the hills.",
        "An urgent rider approaching fast; the dust cloud preceded them by minutes.",
        "Cultists mid-ritual in a field beside the road, too absorbed to notice anyone approaching.",
        "An overturned caravan — no bodies, no blood, no tracks, everything valuable gone.",
        "A travelling merchant anxious to offload goods at any price — clearly stolen.",
        "A doppelganger posing as a stranded traveller, quietly cataloguing each party member.",
        "Refugees moving west, all from the same village, none willing to say what happened.",
        "A druid in argument with a road construction crew about a protected oak.",
        "City guards looking for a fugitive whose description matches a party member.",
        "An abandoned tollbooth, recently vacated; the gate is down, the lock broken from the inside.",
        "A wandering friar offering blessing and water whose route conveniently covers every road in the region.",
    ],
    "Forest": [
        "A wounded deer staggers across the path — whatever brought it down is still close.",
        "Bandits in a prepared ambush between two felled trees, one playing injured in the road.",
        "A will-o'-wisp drifting between the trunks, drawn toward something ahead.",
        "1d4 dire wolves that have been tracking the party for the last hour.",
        "A corrupted dryad, her tree visibly rotting, lashing out at anything that enters her grove.",
        "Goblins raiding a woodcutter's camp — the woodcutter may still be alive inside the cabin.",
        "A colossal spider web spanning the entire trail; something is wrapped at the centre.",
        "A treant, lately awoken, blocking the path and asking who gave the party permission to pass.",
        "Ettercaps herding giant spiders onto the road — the party is standing in the way.",
        "A green hag posing as a lost old woman, offering directions to somewhere worse.",
        "A pixie court mid-trial — they've caught a sprite accused of leading travellers astray.",
        "An owlbear with cubs; the cubs are curious, the mother is not.",
        "A charcoal burner's camp, abandoned mid-meal; the fire is still warm.",
        "Hunters who take the party for poachers — or something worse, if it suits them.",
    ],
    "Hills": [
        "Orc raiders descending from the ridge, having spotted the party from above.",
        "A shepherd whose flock vanished overnight — wool scattered but not a drop of blood.",
        "A half-collapsed burial mound with fresh drag marks leading in and something glowing inside.",
        "A wyvern circling the valley — not hunting, just watching, which is somehow worse.",
        "Hill giants hurling boulders at each other across the valley the party is walking through.",
        "A wounded griffon on a ledge above the road, blocking passage; it's protecting an egg.",
        "Bandit scouts watching from a ridge above; they've been there a while, waiting for backup.",
        "A merchant caravan mired in mud on a hill track, offering reward to anyone who helps.",
        "A stone giant seated cross-legged in a gap between hills, meditating; the path runs directly under it.",
        "Kobold trappers who've seeded the hillside with pit traps, watching to see what falls in.",
        "A spectral cavalry riding silently downhill — a battle fought here centuries ago, replaying.",
        "An earth elemental that has been part of the hill's structure and has finally decided to leave.",
        "A shepherd's dog sitting in the road, refusing to move, staring at a specific patch of hillside.",
    ],
    "Mountains": [
        "An avalanche triggered deliberately by stone giants who've decided the pass is closed for winter.",
        "A young griffon who has claimed this pass as her territory — no one told her she couldn't.",
        "Dwarven prospectors pinned behind rocks, taking fire from orc raiders on the slope above.",
        "A manticore circling overhead, low enough that it's clearly made a decision about the party.",
        "A rope bridge over a deep chasm — and something underneath that doesn't want it crossed.",
        "A monastery carved into the cliff face; monks who ask the same question on entry and exit: 'What did you take?'",
        "Wyverns nesting on an outcrop directly above the only safe path forward.",
        "A frost giant who fell from a higher path and is lying, dazed, across the trail.",
        "A mountain goat herd stampeding downslope — driven by something higher up.",
        "A dwarven citadel gate, sealed from the inside, with something hammering at it from within.",
        "Cloud giant servants gathering materials for a construction project; they haven't asked permission.",
        "A blinded ranger mapping this pass for three seasons — she knows every danger, but can't get down alone.",
        "A shrine to a long-forgotten god, still active; anything left here disappears by morning.",
    ],
    "Swamp": [
        "A hag's hovel, smoke from the chimney and fresh footprints leading to the door from two directions.",
        "1d8 lizardfolk who view the party as trespassers in a sacred marsh.",
        "A will-o'-wisp leading the most confident party member toward a patch of deep quicksand.",
        "A hydra asleep across the only raised crossing — the only dry path through this stretch.",
        "A black dragon wyrmling who has buried a small hoard here and is very paranoid about it.",
        "Bullywugs mid-ceremony, croaking in unison; interrupting would be cosmically unwise.",
        "A yuan-ti pureblood scout who has been following the party for two hours without being detected.",
        "A massive swarm of insects — not hostile, just hungry, and everywhere.",
        "A ghost standing knee-deep in the water, repeating the last words it spoke before dying.",
        "Merrow dragging a sunken merchant barge toward deeper water; the cargo might still be inside.",
        "A troll family camp — three adults and two young, which makes retreat complicated.",
        "Vine blights overgrown around an old stone road marker; clearing them would help, if they allow it.",
        "A ruin half-submerged in the muck — one window is lit, and the light inside moves.",
    ],
    "Desert": [
        "Bandits on fast camels who know every water source in this desert — and will destroy them if pursued.",
        "A dying caravan's last survivor, delirious, with a map pressed into their hands.",
        "A brass door standing upright in the sand, hinges upward — whatever it sealed is long buried.",
        "A djinn freed from imprisonment after four centuries, cheerfully giving misleading directions.",
        "A giant scorpion guarding the only water source for ten miles.",
        "Sand pirates with a hidden underground cache; the entrance is a puzzle lock.",
        "A brass dragon sunning on a rock who wants to ask the party exactly three questions.",
        "Nomad hunters who know where the next oasis is — price negotiable.",
        "A stone colossus half-buried in dunes, still animated, slowly turning to track the party.",
        "Blue slaadi hunting through the desert, following a scent trail that ends here.",
        "A sandstorm carrying something inside it — something alive.",
        "A mirage that turns out to be real: a genuine oasis, heavily trapped.",
        "A merchant caravan travelling by night to avoid the heat, nervous about what else travels by night.",
    ],
    "Coastal": [
        "Pirates flying merchant colours; the flag changes once they're close enough to cut off retreat.",
        "A sea hag's tide-pool lair, exposed at low tide, its occupant nowhere to be seen.",
        "Sahuagin raiding a fishing village at dawn — most villagers are still asleep.",
        "Merfolk at the waterline, willing to trade safe passage for the right information.",
        "Smugglers using a sea cave accessible only at low tide; they're currently inside.",
        "A lighthouse flashing distress code every night — no keeper has been seen in weeks.",
        "A shipwreck half on shore, still settling, with survivors possibly in the hold.",
        "A kraken's tentacle — just one, feeling along the beach — connected to something patient offshore.",
        "A ghost ship run aground, crew at their posts, repeating the final hour of their lives.",
        "Locathah fishers who've found something in their nets they can't identify and don't want.",
        "Coastal bandits with a catapult they have no idea how to aim, demanding toll.",
        "A sea witch auctioning salvage rights to a sunken ship — buyers from three factions, all armed.",
        "Merrow hunting in the shallows at dusk, and the tide is coming in.",
    ],
    "Underdark": [
        "A mind flayer with two thralls, methodically searching every chamber for something specific.",
        "Drow scouts on patrol — they spotted the party two intersections ago.",
        "A roper motionless on the ceiling, tentacles retracted, waiting.",
        "A deep gnome who survived a cave-in three days ago and is running out of water.",
        "A myconid colony willing to parley — anything shared in the spore-dream is permanent.",
        "A cloaker that has spent two years perfecting its ceiling pose in this exact corridor.",
        "A beholder drifting through a cavern it believes is its territory, marked with floating runes.",
        "An aboleth in an underground lake, projecting visions of the surface to lure swimmers in.",
        "A kuo-toa settlement holding a mock trial for a captured sahuagin — they want witnesses.",
        "Derro scouts leading something enormous on chains through the tunnel ahead.",
        "A petrified adventurer in a perfect running pose — whatever did it is still somewhere close.",
        "Gibbering mouthers flooding a low passage; the sound alone is enough to break concentration.",
        "A cave fisher dangling its line through a crack above the only navigable section of tunnel.",
    ],
    "Arctic / Tundra": [
        "Frost giants migrating south, driving reindeer before them, not watching where they step.",
        "A polar bear mother whose cub has wandered too close to the party.",
        "Remorhazes lurking beneath a section of ice that looks solid but creaks underfoot.",
        "Barbarian hunters who mistake the party for rivals from a competing clan.",
        "A frozen expedition camp — tents still standing, cold meals on the table, no one anywhere.",
        "A yeti tracking the party through a blizzard, close enough to be a silhouette in the white.",
        "An ice cave with footprints going in and none coming out; the tracks are two days old.",
        "A white dragon, juvenile, demanding toll in the form of something warm to eat.",
        "Ice trolls sheltering in a collapsed snow structure; they emerge when disturbed.",
        "A frost giant shaman performing a ritual at a ring of upright ice columns.",
        "Survivors of a wrecked supply sled; they're unhurt, but the cargo is scattered across half a mile of ice.",
        "A pack of winter wolves in a loose cordon around something they've cornered in the snow.",
        "A crevasse that wasn't there yesterday, cutting the trail clean across and going down very deep.",
    ],
    "Sea / River": [
        "River pirates using a chain strung low across the water to halt vessels, boarding immediately after.",
        "A ghost ship maintaining course and speed, skeleton crew following orders from before they died.",
        "Sahuagin boarding from the stern while a distraction plays out at the bow.",
        "A maelstrom directly above an aboleth's lair; the aboleth has learned to use it as a net.",
        "A kelpie posing as a drowning person, targeting whoever looks most likely to jump in.",
        "Merfolk blocking the river mouth, demanding a specific magic item they've already identified.",
        "A water elemental that has developed opinions and doesn't want vessels disturbing its river.",
        "A plague ship flying quarantine flags, crewed by people who need help but shouldn't be touched.",
        "A sea serpent using a river to travel upstream — considerably larger than the channel should support.",
        "River cultists in reed boats converging from both banks; their god is the crocodile in the water.",
        "A sunken dwarven barge visible through clear water, a locked chest through the porthole.",
        "Rival treasure hunters in a race downriver — they'll sabotage the party if given any opportunity.",
        "A nixie toll collector blocking a ford — genuinely official, genuinely required, deeply inconvenient.",
    ],
    "Urban": [
        "A pickpocket who has already taken something before the party realises they're a target.",
        "A street brawl spilling out of a tavern — one side is fighting dirty and is about to win.",
        "City guards with an accurate description of a party member, acting on a real warrant.",
        "A tiefling being chased by a mob who haven't verified they have the right person.",
        "A street preacher proclaiming that one party member is a prophesied figure — loudly and publicly.",
        "Two mages mid-duel, collateral damage expanding; the city fine for this is enormous.",
        "A noble's palanquin overturned by a crowd; the noble is looking for someone to blame.",
        "An assassination attempt on a council member — the assassin is disguised as a beggar nearby.",
        "A guild enforcer collecting a debt from a shopkeeper who can't pay; bystanders are uncomfortable.",
        "A child selling a genuine magic item for six copper, not knowing what it is.",
        "A poisoned city well, and the alchemist who discovered it trying to warn people and being ignored.",
        "A warehouse fire spreading fast — workers trapped inside, and something that started it still there.",
        "A foreign dignitary's escort stopped at a checkpoint they weren't briefed on — tension building.",
    ],
    "Dungeon": [
        "A patrol of 1d6 guards who haven't been relieved in days — bored, jumpy, looking for an excuse.",
        "A gelatinous cube drifting silently through the corridor, nearly invisible in the dim light.",
        "A trapped chest with a sleeping kobold curled against it, clearly on guard duty.",
        "Skeletons animated by a rune carved into the floor; destroying the rune is the real challenge.",
        "An ooze seeping under a door, having dissolved the lock from the inside.",
        "Two rival goblin factions in a standoff over stolen food — both turn on the party when interrupted.",
        "A lone survivor hiding in a barrel alcove, terrified, with information she'll share only if escorted out.",
        "A mimic that has been convincingly posing as a door for several years.",
        "A vampire spawn chained to the wall who insists the people who chained it are the real monsters.",
        "Animated armour on patrol — it will raise an alarm if it spots the party but won't fight alone.",
        "A cursed corridor where floor flames rise in sequence — someone designed this carefully.",
        "An intellect devourer waiting inside a humanoid skull, hoping someone will look inside.",
        "The sound of something singing in a lower chamber — the melody is wrong in a way that's hard to place.",
    ],
}


# ── XP tables (DMG 2014) ──────────────────────────────────────────────────────

# Per-character XP thresholds by level: [Easy, Medium, Hard, Deadly]
# Levels 1–20 are the raw DMG values; levels 21–30 are extrapolated for
# epic-tier play at roughly 15% growth per level.
# LEVEL_POWER_FACTOR is applied on top to correct for D&D's non-linear
# power curve (see party_thresholds).
XP_THRESHOLDS = {
    1:  [25,   50,   75,    100],
    2:  [50,   100,  150,   200],
    3:  [75,   150,  225,   400],
    4:  [125,  250,  375,   500],
    5:  [250,  500,  750,   1100],
    6:  [300,  600,  900,   1400],
    7:  [350,  750,  1100,  1700],
    8:  [450,  900,  1400,  2100],
    9:  [550,  1100, 1600,  2400],
    10: [600,  1200, 1900,  2800],
    11: [800,  1600, 2400,  3600],
    12: [1000, 2000, 3000,  4500],
    13: [1100, 2200, 3400,  5100],
    14: [1250, 2500, 3800,  5700],
    15: [1400, 2800, 4300,  6400],
    16: [1600, 3200, 4800,  7200],
    17: [2000, 3900, 5900,  8800],
    18: [2100, 4200, 6300,  9500],
    19: [2400, 4900, 7300,  10900],
    20: [2800, 5700, 8500,  12700],
    # ── Epic tier (extrapolated, ~15% growth per level) ──────────────────────
    21: [3200,  6400,  9600,  14400],
    22: [3700,  7400,  11000, 16500],
    23: [4200,  8400,  12500, 18800],
    24: [4900,  9800,  14700, 22000],
    25: [5600,  11200, 16800, 25200],
    26: [6400,  12800, 19200, 28800],
    27: [7400,  14800, 22200, 33300],
    28: [8500,  17000, 25500, 38300],
    29: [9800,  19600, 29400, 44100],
    30: [11200, 22400, 33600, 50400],
}

# CR → XP value (DMG appendix)
CR_XP = {
    0: 10, 0.125: 25, 0.25: 50, 0.5: 100,
    1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800,
    6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900,
    11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000,
    16: 15000, 17: 18000, 18: 20000, 19: 22000, 20: 25000,
    21: 33000, 22: 41000, 23: 50000, 24: 62000, 30: 155000,
}

# Encounter XP multiplier thresholds: (max_count, multiplier).
# Ordered so the first matching max_count applies.
# encounter_multiplier() shifts the index up for small parties (≤2) or down
# for large parties (≥6) per the DMG party-size adjustment.
MULTIPLIERS = [(1, 1.0), (2, 1.5), (6, 2.0), (10, 2.5), (14, 3.0), (9999, 4.0)]

# ── Non-linear party power correction ────────────────────────────────────────
# DMG XP thresholds assume a roughly linear power curve, but D&D 5e has hard
# breakpoints where parties become dramatically more capable:
#   • Level 5 — Extra Attack, Fireball, 3rd-level spells
#   • Level 11 — 6th-level spells (Disintegrate, Heal)
#   • Level 17 — 9th-level spells (Wish, True Resurrection)
# These factors scale each character's effective XP budget upward so that the
# same adjusted-XP encounter is rated correctly less dangerous for higher-level
# parties (e.g., a group of level 5s can handle far more than 5× what level 1s
# can — closer to 10–15× — because one Fireball replaces 3 cantrips).
LEVEL_POWER_FACTOR = {
    1: 1.00, 2: 1.00, 3: 1.05, 4: 1.10,   # Tier 1: foundational, limited resources
    5: 1.35, 6: 1.45, 7: 1.55, 8: 1.65,   # Tier 2: Extra Attack + 3rd-level spells
    9: 1.75, 10: 1.85,
    11: 2.10, 12: 2.20, 13: 2.30, 14: 2.40,  # Tier 3: 6th-level spells
    15: 2.50, 16: 2.60,
    17: 3.00, 18: 3.10, 19: 3.20, 20: 3.50,  # Tier 4: 9th-level spells (peak standard)
    # ── Epic tier — 9th-level slots are full; growth from epic boons/features ──
    21: 3.70, 22: 3.90, 23: 4.10, 24: 4.30,  # Epic Tier 1: first epic boons
    25: 4.60, 26: 4.80, 27: 5.00, 28: 5.20,  # Epic Tier 2: legendary abilities
    29: 5.40, 30: 5.80,                        # Epic Tier 3: demigod threshold
}



# ── Helpers ───────────────────────────────────────────────────────────────────

def cr_xp(cr_float):
    """XP value for a CR, linearly interpolating between the nearest known entries.

    CR_XP has explicit DMG-published values for CR 0-24 and CR 30, but WotC
    never published CR 25-29 — those used to snap to whichever of CR 24/30
    was numerically closer (e.g. CR 25-26 silently got CR 24's XP value, and
    CR 27 tied and also resolved to CR 24). Interpolating instead gives each
    in-between CR a proportionate value on the line between its two nearest
    defined neighbors.
    """
    if cr_float in CR_XP:
        return CR_XP[cr_float]
    keys = sorted(CR_XP.keys())
    if cr_float <= keys[0]:
        return CR_XP[keys[0]]
    if cr_float >= keys[-1]:
        return CR_XP[keys[-1]]
    lower = max(k for k in keys if k < cr_float)
    upper = min(k for k in keys if k > cr_float)
    frac = (cr_float - lower) / (upper - lower)
    return round(CR_XP[lower] + frac * (CR_XP[upper] - CR_XP[lower]))


def encounter_multiplier(num_monsters, party_size):
    """Return the XP multiplier for the given total monster count and party size.

    Standard thresholds (3–5 players):
      1: ×1.0 · 2: ×1.5 · 3–6: ×2.0 · 7–10: ×2.5 · 11–14: ×3.0 · 15+: ×4.0

    DMG party-size adjustment (p. 82):
      ≤ 2 players — shift one step higher (small party is more vulnerable)
      3–5 players — standard thresholds
      ≥ 6 players — shift one step lower (large party shares the load)
    """
    # Find the base index from the monster count
    base_idx = len(MULTIPLIERS) - 1
    for i, (max_count, _) in enumerate(MULTIPLIERS):
        if num_monsters <= max_count:
            base_idx = i
            break

    # Apply party-size step shift, clamped to valid range
    if party_size <= 2:
        adj_idx = min(base_idx + 1, len(MULTIPLIERS) - 1)
    elif party_size >= 6:
        adj_idx = max(base_idx - 1, 0)
    else:
        adj_idx = base_idx

    return MULTIPLIERS[adj_idx][1]


def party_thresholds(levels):
    """Sum the XP thresholds across all party members for each difficulty tier.

    Applies LEVEL_POWER_FACTOR to each character's row so that higher-level
    parties have proportionally larger budgets — correcting for the non-linear
    power jumps the DMG table doesn't account for.
    """
    totals = [0, 0, 0, 0]
    for lvl in levels:
        clamped = max(1, min(30, lvl))  # table runs 1–30; clamp edge cases only
        row = XP_THRESHOLDS.get(clamped, XP_THRESHOLDS[30])
        pf = LEVEL_POWER_FACTOR.get(clamped, 1.0)
        for j in range(4):
            totals[j] += int(row[j] * pf)
    return totals


# ── Combined difficulty scale ─────────────────────────────────────────────────
# Tiers 1-5 mirror the DMG XP scale; tier 6 captures fights that are
# simultaneously high-XP *and* badly outnumbered.
# Combined index = XP_tier (1-5) + AE_adjustment (0-4), clamped to [1, 6].
_COMBINED_TIERS = {
    1: ("Trivial",      "🟢"),
    2: ("Easy",         "🟡"),
    3: ("Medium",       "🟠"),
    4: ("Hard",         "🔴"),
    5: ("Deadly",       "💀"),
    6: ("Catastrophic", "☠️"),
}
# AE label → (max_ratio, label, emoji, tier_adjustment).
# Favorable = 0: fight is exactly as hard as XP says (no extra pressure).
# Each step up adds one full tier of difficulty to the combined rating.
_AE_TIERS = [
    (0.51, "Favorable",    "🟢", 0),   # monsters fewer than half the party
    (1.01, "Even",         "🟡", 1),   # roughly 1:1
    (2.01, "Outnumbered",  "🟠", 2),   # up to 2:1
    (3.01, "Swarmed",      "🔴", 3),   # up to 3:1
    (None, "Overwhelming", "☠️", 4),   # >3:1
]

# ── Boss Threat factor ────────────────────────────────────────────────────────
# Compares the boss-weighted effective XP to the party's power-corrected Easy
# threshold per character, isolating *individual monster quality* from the
# count pressure already captured by Action Economy.
#
# effective_xp = boss_fraction × max_xp + (1 − boss_fraction) × avg_xp,
#   where boss_fraction = highest single-monster XP / total raw XP.
#
# For equal monsters: boss_fraction ≈ 1/n, so effective_xp ≈ avg_xp (no change).
# For boss + many minions: boss_fraction grows, and effective_xp slides toward
# the boss's XP, so cheap minions can't dilute the boss's threat.
#
# Adjustment is always ≤ 0 — Boss Threat can only REDUCE the Result, never
# inflate it. Example: 100 CR-0 goblins vs level-5 party → Fodder (−4),
# pulling a Catastrophic AE result back to a realistic rating.
_BOSS_THREAT_TIERS = [
    (1.00, "Threatening", "🔴",  0),   # dominant monster is a real threat at party level
    (0.40, "Weak",        "🟠", -1),   # dominant monster somewhat below par
    (0.15, "Feeble",      "🟡", -2),   # noticeably outclassed
    (0.04, "Negligible",  "🟢", -3),   # very minor individual threat
    (0.00, "Fodder",      "🟢", -4),   # trivially easy kills (CR 0 vs high-level party)
]


def difficulty_label(adjusted_xp, thresholds):
    """Return (label, emoji, xp_tier) for adjusted XP vs power-corrected party thresholds.

    xp_tier is 1 (Trivial) through 5 (Deadly) and feeds into combined_result_tier().
    """
    easy, medium, hard, deadly = thresholds
    if adjusted_xp < easy:
        return "Trivial",  "🟢", 1
    if adjusted_xp < medium:
        return "Easy",     "🟡", 2
    if adjusted_xp < hard:
        return "Medium",   "🟠", 3
    if adjusted_xp < deadly:
        return "Hard",     "🔴", 4
    return "Deadly", "💀", 5


def action_economy_label(total_monsters, party_size):
    """Return (ratio_str, label, emoji, ae_adj) for the monster:player action ratio.

    ae_adj (0-4) is added to the XP tier index to produce the combined Result tier.
    Each step represents one full difficulty tier of extra pressure from outnumbering:
      0 Favorable   — no extra pressure (monsters ≤ half the party)
      1 Even        — slight pressure at ~1:1
      2 Outnumbered — up to 2:1; notable concentration/save pressure
      3 Swarmed     — up to 3:1; party likely can't keep up with incoming damage
      4 Overwhelming — >3:1; action economy collapse
    """
    if party_size == 0:
        return "—", "N/A", "⚪", 0
    ratio = total_monsters / party_size
    ratio_str = f"{ratio:.1f}:1"
    for max_ratio, label, emoji, adj in _AE_TIERS:
        if max_ratio is None or ratio <= max_ratio:
            return ratio_str, label, emoji, adj
    return ratio_str, "Overwhelming", "☠️", 4  # fallback


def boss_threat_label(effective_xp, easy_threshold_total, party_size):
    """Return (label, emoji, bt_adj) for boss-weighted effective XP vs party's Easy-per-character.

    effective_xp uses the boss-weighting formula:
        effective_xp  = boss_fraction × max_monster_xp + (1 − boss_fraction) × avg_xp,
        where boss_fraction = max_monster_xp / total_raw_xp.

    For equal monsters, boss_fraction ≈ 1/n, so effective_xp ≈ avg_xp (no change).
    For a boss + many minions, boss_fraction grows and effective_xp slides toward
    the boss's XP, so cheap extras can't wash out a powerful leader.

    bt_adj is 0 (Threatening) to −4 (Fodder). Always ≤ 0 — can only REDUCE the
    combined Result. Prevents swarms of trivially weak enemies from looking
    catastrophic purely from action-economy pressure.
    """
    easy_per_char = easy_threshold_total / max(1, party_size)
    if easy_per_char <= 0:
        return "Threatening", "🔴", 0
    ratio = effective_xp / easy_per_char
    for min_ratio, label, emoji, adj in _BOSS_THREAT_TIERS:
        if ratio >= min_ratio:
            return label, emoji, adj
    return "Fodder", "🟢", -4   # fallback for ratio exactly 0


def combined_result_tier(xp_tier, ae_adj, bt_adj):
    """Return (label, emoji) for the three-factor combined difficulty.

    Formula: XP tier (1-5) + AE adjustment (0 to +4) + Boss Threat adjustment (−4 to 0),
    clamped to [1, 6].
    Examples:
      Easy(2) + Favorable(0) + Threatening(0) = 2 = Easy
      Easy(2) + Overwhelming(4) + Threatening(0) = 6 = Catastrophic
      Easy(2) + Overwhelming(4) + Fodder(−4)    = 2 = Easy
    """
    idx = max(1, min(6, xp_tier + ae_adj + bt_adj))
    label, emoji = _COMBINED_TIERS[idx]
    return label, emoji


def on_count_change(idx):
    """on_change callback for the inline count number_input.

    Fires before the next script run, so XP calculations immediately see
    the updated count without needing a manual st.rerun() call.
    """
    new_val = st.session_state.get(f"enc_cnt_{idx}", 1)
    if idx < len(st.session_state.enc_monsters):
        st.session_state.enc_monsters[idx]["count"] = max(1, int(new_val))



@st.cache_data(show_spinner=False)
def _load_monsters(path, mtime, source_tag="srd"):
    """Cached monster list with pre-computed cr_float, _source, and _name_lower fields.

    source_tag — "srd" for SRD monsters, "named" for named/boss creatures.
    Used in the search results display to badge named creatures.
    _name_lower is pre-computed so the search filter doesn't re-lowercase
    3,500+ names on every rerun while a query is active.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for m in data:
        m["_cr_float"] = cr_to_float(m.get("cr", 0))
        m["_source"] = source_tag
        m["_name_lower"] = m.get("name", "").lower()
    return data


@st.cache_data(show_spinner=False)
def _load_magic_items(path, mtime):
    """Cached magic items list (flat list of item dicts)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ── Session state ─────────────────────────────────────────────────────────────

if "enc_monsters" not in st.session_state:
    # List of {"name": str, "cr": str, "cr_float": float, "count": int}
    st.session_state.enc_monsters = []
if "loot_results" not in st.session_state:
    st.session_state.loot_results = []
# Clear results that use the old format (pre-refactor had 'source' key instead of 'name')
if st.session_state.loot_results and "source" in st.session_state.loot_results[0]:
    st.session_state.loot_results = []


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Encounter Builder")

tab_enc, tab_loot, tab_ideas, tab_dress = st.tabs(["Encounter", "Loot", "Encounter Ideas", "Dungeon Dressing"])


# ══════════════════════════════════════════════════════════════════════════════
# ENCOUNTER TAB
# ══════════════════════════════════════════════════════════════════════════════

with tab_enc:
    if not SRD_PATH.exists():
        st.warning("Monster data not found. Run `python scripts/download_data.py` first.")
        st.stop()

    monsters_all = _load_monsters(str(SRD_PATH), SRD_PATH.stat().st_mtime, "srd")

    # ── Party setup ───────────────────────────────────────────────────────────
    # Pre-seed session_state from saved prefs so party config remembers last values.
    get_pref("enc_party_size",  4)
    get_pref("enc_same_level",  True)
    get_pref("enc_party_level", 5)
    st.subheader("Party")
    p1, p2 = st.columns([1, 3])
    party_size = p1.number_input("Number of Players", min_value=1, max_value=10, key="enc_party_size")
    same_level = p2.checkbox("All Same Level", key="enc_same_level")

    if same_level:
        lvl = st.slider("Party Level", 1, 30, key="enc_party_level")
        party_levels = [lvl] * party_size
    else:
        cols = st.columns(party_size)
        party_levels = [
            cols[k].number_input(f"P{k+1} level", 1, 30, 5, key=f"plvl_{k}")
            for k in range(party_size)
        ]

    # Persist party config (only enc_party_level is relevant when same_level=True,
    # but always saving all three is harmless and simpler).
    save_prefs({"enc_party_size":  int(st.session_state.enc_party_size),
                "enc_same_level":  bool(st.session_state.enc_same_level),
                "enc_party_level": int(st.session_state.enc_party_level)})

    thresholds = party_thresholds(party_levels)
    easy, medium, hard, deadly = thresholds

    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Easy",   f"{easy:,} XP")
    t2.metric("Medium", f"{medium:,} XP")
    t3.metric("Hard",   f"{hard:,} XP")
    t4.metric("Deadly", f"{deadly:,} XP")

    st.markdown("---")

    # ── Monster search & add ──────────────────────────────────────────────────
    st.subheader("Monsters")

    # Pool selector — named creatures tab may not have data yet
    _pool_options = ["SRD Monsters"]
    if NAMED_PATH.exists():
        _pool_options += ["Named Creatures", "Both"]
    pool_choice = st.radio("Monster pool", _pool_options, horizontal=True, key="enc_pool")

    # Load named pool only when needed to avoid unnecessary file I/O
    named_all = (
        _load_monsters(str(NAMED_PATH), NAMED_PATH.stat().st_mtime, "named")
        if NAMED_PATH.exists() and pool_choice in ("Named Creatures", "Both")
        else []
    )
    if pool_choice == "Named Creatures":
        search_pool = named_all
    elif pool_choice == "Both":
        search_pool = monsters_all + named_all
    else:
        search_pool = monsters_all

    # CR range slider — standard CR values including fractional tiers
    _CR_VALUES = ["0","1/8","1/4","1/2","1","2","3","4","5","6","7","8","9","10",
                  "11","12","13","14","15","16","17","18","19","20","21","22","23",
                  "24","25","26","27","28","29","30"]
    cr_range = st.select_slider(
        "CR Range", options=_CR_VALUES, value=("0", "30"), key="enc_cr_range"
    )
    cr_min_f    = cr_to_float(cr_range[0])
    cr_max_f    = cr_to_float(cr_range[1])
    # Any narrowing of the default 0–30 range counts as an active filter,
    # allowing browsing by CR alone without needing a text search.
    cr_filtered = cr_range != ("0", "30")

    search_q = st.text_input(
        "Search by name (3+ characters)", key="enc_search",
        placeholder="e.g. goblin, Tiamat, ancient dragon…"
    )
    # Activate when text ≥ 3 chars OR the CR slider has been narrowed.
    enc_search_active = len(search_q) >= 3 or cr_filtered
    if not enc_search_active:
        st.caption(f"Type 3+ characters or narrow the CR range to search ({len(search_pool):,}+ entries).")
    else:
        _name_q = search_q.lower()
        all_matches = [
            m for m in search_pool
            if (not _name_q or _name_q in m["_name_lower"])
            and cr_min_f <= m["_cr_float"] <= cr_max_f
        ]
        matches = all_matches[:50]
        if len(all_matches) > 50:
            st.caption(f"Showing 50 of {len(all_matches)} results — type more to narrow down.")
        if matches:
            # Index-based selectbox handles duplicate names when SRD and Named pools are merged.
            # Named creatures get a [Named] badge so the DM can tell them apart.
            chosen_idx = st.selectbox(
                "Select monster to add",
                range(len(matches)),
                format_func=lambda i: (
                    f"{matches[i]['name']} (CR {matches[i].get('cr', '?')}) [Named]"
                    if matches[i].get("_source") == "named"
                    else f"{matches[i]['name']} (CR {matches[i].get('cr', '?')})"
                ),
                key="enc_pick"
            )
            chosen = matches[chosen_idx]
            mc1, mc2 = st.columns([1, 4], vertical_alignment="bottom")
            qty = mc1.number_input("Count", min_value=1, value=1, key="enc_qty")
            if mc2.button(f"Add {chosen['name']} × {qty}"):
                # Merge into existing entry if same monster AND same source already added.
                # Source check prevents accidentally merging a named Goblin with an SRD Goblin.
                existing_idx = next(
                    (j for j, e in enumerate(st.session_state.enc_monsters)
                     if e["name"] == chosen["name"]
                     and e.get("source") == chosen.get("_source", "srd")),
                    None
                )
                if existing_idx is not None:
                    new_count = st.session_state.enc_monsters[existing_idx]["count"] + int(qty)
                    st.session_state.enc_monsters[existing_idx]["count"] = new_count
                    # Roster number_input hasn't rendered yet — set directly so the
                    # widget shows the updated count on next render.
                    st.session_state[f"enc_cnt_{existing_idx}"] = new_count
                else:
                    st.session_state.enc_monsters.append({
                        "name":     chosen["name"],
                        "cr":       str(chosen.get("cr", "0")),
                        "cr_float": chosen["_cr_float"],
                        "count":    int(qty),
                        "source":   chosen.get("_source", "srd"),
                    })
                st.rerun()
        else:
            st.caption("No monsters found.")

    # ── Encounter roster ──────────────────────────────────────────────────────
    if not st.session_state.enc_monsters:
        st.info("Search and add monsters above to build your encounter.")
    else:
        total_raw_xp   = 0
        total_monsters = sum(e["count"] for e in st.session_state.enc_monsters)

        header = st.columns([3, 1, 1, 1, 1])
        header[0].markdown("**Monster**")
        header[1].markdown("**CR**")
        header[2].markdown("**Count**")
        header[3].markdown("**XP each**")
        header[4].markdown("")

        for idx, entry in enumerate(st.session_state.enc_monsters):
            xp_each = cr_xp(entry["cr_float"])
            total_raw_xp += xp_each * entry["count"]

            row = st.columns([3, 1, 1, 1, 1])
            _name_display = (f"{entry['name']} [Named]"
                             if entry.get("source") == "named" else entry["name"])
            row[0].write(_name_display)
            row[1].write(entry["cr"])
            # Inline count editor
            row[2].number_input(
                "Count", min_value=1, value=entry["count"],
                label_visibility="collapsed", key=f"enc_cnt_{idx}",
                on_change=on_count_change, args=(idx,)
            )
            row[3].write(f"{xp_each:,}")
            if row[4].button("✕", key=f"enc_rm_{idx}"):
                _old_len = len(st.session_state.enc_monsters)
                st.session_state.enc_monsters.pop(idx)
                # Every row from idx onward shifts down by one index. Their
                # enc_cnt_* widget keys are cached in session_state from the
                # previous render, so without clearing them the monster that
                # shifts into a given index would silently display the count
                # that belonged to whoever used to sit there. Popping lets each
                # remaining row's number_input re-initialise from entry["count"].
                for _k in range(idx, _old_len):
                    st.session_state.pop(f"enc_cnt_{_k}", None)
                st.rerun()

        st.markdown("---")

        # ── Difficulty calculation ────────────────────────────────────────────
        mult                         = encounter_multiplier(total_monsters, len(party_levels))
        adjusted_xp                  = int(total_raw_xp * mult)
        xp_label, xp_emoji, xp_tier  = difficulty_label(adjusted_xp, thresholds)
        ae_ratio, ae_label, ae_emoji, ae_adj = action_economy_label(
            total_monsters, len(party_levels)
        )

        # Boss-weighted effective XP: measures individual monster quality while
        # preventing a swarm of cheap minions from burying a dangerous boss.
        #   boss_fraction = max single-monster XP / total raw XP
        #   effective_xp  = boss_fraction × max_xp + (1 − boss_fraction) × avg_xp
        # Equal monsters → effective_xp = avg_xp (no change from straight average).
        avg_xp          = total_raw_xp / max(1, total_monsters)
        max_monster_xp  = max((cr_xp(e["cr_float"]) for e in st.session_state.enc_monsters), default=0)
        boss_fraction   = max_monster_xp / max(1, total_raw_xp)
        effective_xp    = boss_fraction * max_monster_xp + (1 - boss_fraction) * avg_xp
        bt_label, bt_emoji, bt_adj = boss_threat_label(effective_xp, thresholds[0], len(party_levels))
        res_label, res_emoji = combined_result_tier(xp_tier, ae_adj, bt_adj)

        # Fully-rested caveat — show before the numbers so DMs read it first
        st.info(
            "**Fully rested party assumed.** These ratings expect full HP, all spell slots, "
            "and every ability available. Bump the Result up by one tier for each significant "
            "resource already spent before this encounter.",
            icon="ℹ️",
        )

        # Row 1: raw numbers
        dc1, dc2, dc3, dc4 = st.columns(4)
        dc1.metric("Raw XP",           f"{total_raw_xp:,}")
        # Build a dynamic size note so the tooltip reflects the active party
        _ps = len(party_levels)
        if _ps <= 2:
            _size_note = (f"Party of {_ps} (small) — multipliers shift one step higher than standard.\n")
        elif _ps >= 6:
            _size_note = (f"Party of {_ps} (large) — multipliers shift one step lower than standard.\n")
        else:
            _size_note = ""
        dc2.metric("Count ×",          f"×{mult}",
                   help=("DMG encounter multiplier applied to total raw XP. More monsters "
                         "overwhelm the action economy: they act more often, stack conditions, "
                         "and prevent the party from safely focusing fire.\n"
                         f"{_size_note}"
                         "Standard thresholds (3–5 players): "
                         "1: ×1.0 · 2: ×1.5 · 3–6: ×2.0 · 7–10: ×2.5 · 11–14: ×3.0 · 15+: ×4.0"))
        dc3.metric("Adjusted XP",      f"{adjusted_xp:,}",
                   help="Raw XP × the count multiplier. Compare against the party thresholds "
                        "above to read XP Difficulty.")
        dc4.metric("Monster : Player", ae_ratio,
                   help="How many monster actions the party faces each round relative to their own. "
                        "A 2:1 ratio means the party takes twice as many hits as they dish out — "
                        "concentration breaks, resource drain, and forced saves pile up fast. "
                        "Feeds directly into the Action Economy rating below.")

        # Row 2: four ratings that combine into the final Result.
        # XP Difficulty = adjusted XP vs power-corrected party budget (tier 1-5, feeds into Result as-is).
        # Action Economy = monster:player ratio pressure (+0 to +4 tiers).
        # Boss Threat   = boss-weighted effective XP vs party level (−4 to 0 tiers).
        # Result        = XP + AE + BT, clamped to [1, 6] on the combined scale.
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("XP Difficulty",  f"{xp_emoji} {xp_label}",
                  help="Adjusted XP compared to power-corrected party thresholds. "
                       "Higher-level parties get a larger budget because breakpoints like "
                       "level 5 (Extra Attack, Fireball) and level 11 (6th-level spells) "
                       "make each character disproportionately stronger. "
                       f"Trivial [+1] · Easy [+2] · Medium [+3] · Hard [+4] · Deadly [+5]\n"
                       f"Current: {xp_label} [+{xp_tier} to Result]")
        r2.metric("Action Economy", f"{ae_emoji} {ae_label}",
                  help="Monster:player action ratio. Each tier shifts Result up by one step — "
                       "more monsters means more attacks, more forced saves, and concentration "
                       "checks before the party can finish their turns.\n"
                       "Favorable ≤0.5:1 [+0] · Even ≤1:1 [+1] · Outnumbered ≤2:1 [+2] · "
                       f"Swarmed ≤3:1 [+3] · Overwhelming >3:1 [+4]\n"
                       f"Current: {ae_label} [+{ae_adj} to Result]")
        r3.metric("Boss Threat",    f"{bt_emoji} {bt_label}",
                  help="How dangerous is the dominant monster relative to the party's level? "
                       "Uses boss-weighted effective XP so a powerful boss isn't buried by cheap minions:\n"
                       "  effective XP = boss_fraction × max_XP + (1 − boss_fraction) × avg_XP,\n"
                       "  where boss_fraction = highest single-monster XP ÷ total raw XP.\n"
                       "Equal monsters → effective XP ≈ avg XP (no change). "
                       "Boss + minions → effective XP slides toward the boss's value.\n"
                       f"Effective XP: {effective_xp:,.0f}  |  Easy per character: {thresholds[0] / max(1, len(party_levels)):,.0f}\n"
                       "Threatening ≥100% [0] · Weak ≥40% [−1] · Feeble ≥15% [−2] · "
                       f"Negligible ≥4% [−3] · Fodder <4% [−4]\n"
                       f"Current: {bt_label} [{bt_adj} to Result]")
        r4.metric("Result",         f"{res_emoji} {res_label}",
                  help="Three-factor combined difficulty.\n"
                       f"  XP {xp_tier} [+{xp_tier}]  +  AE {'+' if ae_adj >= 0 else ''}{ae_adj}  +  BT {bt_adj}\n"
                       f"  = {xp_tier + ae_adj + bt_adj} → clamped to [{max(1, min(6, xp_tier + ae_adj + bt_adj))}] "
                       f"→ {res_label}\n"
                       "BT can only reduce the Result (never inflate it), so a swarm of trivial "
                       "enemies can't push a fight beyond what the XP and action economy already indicate.")

        # Inline breakdown so the maths are always visible without opening a tooltip
        st.caption(
            f"**Breakdown:** XP **{xp_tier}** [{xp_label}]  "
            f"+ AE **{'+' if ae_adj >= 0 else ''}{ae_adj}** [{ae_label}]  "
            f"+ BT **{bt_adj}** [{bt_label}]  "
            f"= **{max(1, min(6, xp_tier + ae_adj + bt_adj))}** → **{res_label}**"
        )

        # Two-step confirm before clearing the whole encounter
        if "enc_clear_pending" not in st.session_state:
            st.session_state.enc_clear_pending = False
        if not st.session_state.enc_clear_pending:
            if st.button("Clear Encounter"):
                st.session_state.enc_clear_pending = True
                st.rerun()
        else:
            if st.button("Confirm Clear?", type="primary"):
                # Drop every enc_cnt_* key too — otherwise a monster added after
                # clearing could land on a low index (e.g. 0) that still holds a
                # stale count from before the clear, and its number_input would
                # silently display that leftover value instead of the fresh
                # entry's actual count.
                for _key in list(st.session_state.keys()):
                    if _key.startswith("enc_cnt_"):
                        del st.session_state[_key]
                st.session_state.enc_monsters    = []
                st.session_state.loot_results    = []
                st.session_state.enc_clear_pending = False
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# LOOT TAB
# CR bands are derived automatically from each monster's CR float.
# Hoard mode = aggregate individual loot so amounts scale naturally with the
# encounter (avoids the inflation of applying full DMG hoard tables to a small
# group of monsters).
# ══════════════════════════════════════════════════════════════════════════════

with tab_loot:
    if not st.session_state.enc_monsters:
        st.info("Build an encounter in the Encounter tab first, then roll loot here.")
    else:
        magic_items_all = (
            _load_magic_items(str(MAGICITEMS_PATH), MAGICITEMS_PATH.stat().st_mtime)
            if MAGICITEMS_PATH.exists() else []
        )

        loot_tabs = st.tabs(["Roll", "References"])

        # ── Roll sub-tab ──────────────────────────────────────────────────────
        with loot_tabs[0]:
            st.subheader("Loot")
            st.caption(
                "CR bands are set automatically. "
                "Individual rolls per-creature; Hoard pools all individual loot "
                "into one combined total so the amount stays proportional to the encounter."
            )

            loot_mode = st.radio(
                "Loot mode",
                ["Individual (per monster)", "Hoard (combined pool)"],
                horizontal=True
            )

            if st.button("Roll Loot", type="primary"):
                results = []

                # Roll per-monster type, then aggregate
                for entry in st.session_state.enc_monsters:
                    band = cr_float_to_band(entry["cr_float"])
                    agg  = {"cp":0,"sp":0,"ep":0,"gp":0,"pp":0}
                    gems, arts, jewels, trades, curs = [], [], [], [], []
                    for _ in range(entry["count"]):
                        t = roll_individual_treasure(band, entry["cr_float"])
                        agg = add_coins(agg, t["coins"])
                        gems.extend(t["gems"]); arts.extend(t["arts"])
                        jewels.extend(t["jewels"]); trades.extend(t["trades"])
                        curs.extend(t["curiosities"])
                    results.append({
                        "name": entry["name"], "cr": entry["cr"],
                        "count": entry["count"], "band": band,
                        "coins": agg,
                        "gems": gems, "arts": arts, "jewels": jewels,
                        "trades": trades, "curs": curs,
                    })

                if loot_mode == "Hoard (combined pool)":
                    # Combine everything into one result entry
                    grand = {"cp":0,"sp":0,"ep":0,"gp":0,"pp":0}
                    all_gems, all_arts, all_jewels, all_trades, all_curs = [], [], [], [], []
                    for r in results:
                        grand = add_coins(grand, r["coins"])
                        all_gems   += r["gems"]
                        all_arts   += r["arts"]
                        all_jewels += r["jewels"]
                        all_trades += r["trades"]
                        all_curs   += r["curs"]
                    # Magic item count: base = highest-CR creature's hoard-band allocation,
                    # then add sqrt of the excess raw allocation from all other monsters.
                    # This gives a single powerful boss its full expected haul while
                    # preventing linear inflation when dozens of monsters are present.
                    # Rarity uses the highest CR band so a Tiamat encounter yields Legendary.
                    max_cr     = max(e["cr_float"] for e in st.session_state.enc_monsters)
                    hoard_band = cr_float_to_hoard_band(max_cr)
                    magic      = []
                    if max_cr >= 5:
                        base_magic = HOARD_AUTO_ROLLS.get(hoard_band, {}).get("magic", 1)
                        raw_total  = sum(
                            HOARD_AUTO_ROLLS.get(cr_float_to_hoard_band(e["cr_float"]), {}).get("magic", 1)
                            * e["count"]
                            for e in st.session_state.enc_monsters
                        )
                        # Base covers the single-boss expectation; sqrt covers extra monsters
                        excess      = max(0, raw_total - base_magic)
                        magic_rolls = max(1, round(base_magic + excess ** 0.55))
                        for _ in range(magic_rolls):
                            roll = random.randint(1, 100)
                            rar  = lookup_range(HOARD_MAGIC_BY_CR[hoard_band], roll)
                            item = pick_magic_item(rar, magic_items_all)
                            if item:
                                magic.append((item, rar))
                    results = [{
                        "name": "Combined Hoard", "cr": "—", "count": 1,
                        "band": f"pooled (max CR {max_cr:.3g})",
                        "coins": grand,
                        "gems": all_gems, "arts": all_arts, "jewels": all_jewels,
                        "trades": all_trades, "curs": all_curs, "magic": magic,
                    }]

                st.session_state.loot_results = results
                st.rerun()

            # ── Display results ───────────────────────────────────────────────
            if st.session_state.loot_results:
                grand_coins  = {"cp":0,"sp":0,"ep":0,"gp":0,"pp":0}
                extra_gp     = 0.0
                # Accumulated lists for the Total expander
                total_gems, total_arts, total_jewels = [], [], []
                total_trades, total_curs, total_magic = [], [], []

                for res in st.session_state.loot_results:
                    has_magic = "magic" in res
                    with st.expander(
                        f"**{res['name']} ×{res['count']}** — CR {res['cr']} [{res['band']}]",
                        expanded=True
                    ):
                        st.markdown(f"**Coins:** {format_coins(res['coins'])}")
                        loot_section("Gems",        res["gems"])
                        loot_section("Art Objects", res["arts"])
                        loot_section("Jewelry",     res["jewels"])
                        loot_section("Trade Goods", res["trades"])
                        loot_section("Curiosities", res["curs"], approx=True)
                        if has_magic and res["magic"]:
                            magic_counts = Counter(n for n, _ in res["magic"])
                            # Group magic items by name, show rarity
                            magic_rar = {n: r for n, r in res["magic"]}
                            st.markdown("**Magic Items:**")
                            for name, n in sorted(magic_counts.items()):
                                rar = magic_rar[name]
                                if n > 1:
                                    st.markdown(f"- {name} ×{n} *({rar})*")
                                else:
                                    st.markdown(f"- {name} *({rar})*")
                    grand_coins   = add_coins(grand_coins, res["coins"])
                    extra_gp     += sum(v for _,v in res["gems"]+res["arts"]+res["jewels"]+res["trades"]+res["curs"])
                    total_gems   += res["gems"]
                    total_arts   += res["arts"]
                    total_jewels += res["jewels"]
                    total_trades += res["trades"]
                    total_curs   += res["curs"]
                    if "magic" in res:
                        total_magic += res["magic"]

                # Total expander: only useful when there are multiple monster entries
                if len(st.session_state.loot_results) > 1:
                    with st.expander("**Total (All Monsters)**", expanded=False):
                        st.markdown(f"**Coins:** {format_coins(grand_coins)}")
                        loot_section("Gems",        total_gems)
                        loot_section("Art Objects", total_arts)
                        loot_section("Jewelry",     total_jewels)
                        loot_section("Trade Goods", total_trades)
                        loot_section("Curiosities", total_curs, approx=True)
                        if total_magic:
                            magic_counts = Counter(n for n, _ in total_magic)
                            magic_rar    = {n: r for n, r in total_magic}
                            st.markdown("**Magic Items:**")
                            for name, n in sorted(magic_counts.items()):
                                rar = magic_rar[name]
                                if n > 1:
                                    st.markdown(f"- {name} ×{n} *({rar})*")
                                else:
                                    st.markdown(f"- {name} *({rar})*")

                st.markdown("---")
                lc1, lc2 = st.columns(2)
                lc1.metric("Total Coins",  format_coins(grand_coins))
                lc2.metric("≈ Total Value", f"{coins_to_gp(grand_coins)+extra_gp:,.0f} gp")

        # ── References sub-tab ────────────────────────────────────────────────
        with loot_tabs[1]:
            st.caption("Quick-reference tables for all treasure categories.")
            ref_sub = st.tabs(["Gems", "Art Objects", "Jewelry", "Trade Goods", "Curiosities"])
            with ref_sub[0]:
                for v, items in sorted(GEMS.items()):
                    with st.expander(f"{v:,} gp gems"):
                        st.write(", ".join(items))
            with ref_sub[1]:
                for v, items in sorted(ART_OBJECTS.items()):
                    with st.expander(f"{v:,} gp art objects"):
                        for obj in items: st.markdown(f"- {obj}")
            with ref_sub[2]:
                for v, items in sorted(JEWELRY.items()):
                    with st.expander(f"{v:,} gp jewelry"):
                        for obj in items: st.markdown(f"- {obj}")
            with ref_sub[3]:
                for v, items in sorted(TRADE_GOODS.items()):
                    with st.expander(f"{v:,} gp trade goods"):
                        for obj in items: st.markdown(f"- {obj}")
            with ref_sub[4]:
                for v, items in sorted(CURIOSITIES.items()):
                    label = "Worthless (0 gp)" if v == 0 else f"~{v:,} gp"
                    with st.expander(f"{label} curiosities"):
                        for obj in items: st.markdown(f"- {obj}")


# ══════════════════════════════════════════════════════════════════════════════
# ENCOUNTER IDEAS TAB
# Quick-roll terrain encounter hooks — one-line situation prompts for when the
# DM needs an encounter seed without opening a sourcebook.
# ══════════════════════════════════════════════════════════════════════════════

with tab_ideas:
    st.subheader("Encounter Ideas")
    st.caption(
        "One-line encounter hooks by terrain. Roll a random prompt or browse the full table. "
        "These are situation seeds — not stat blocks. Adjust to taste."
    )

    terrain_sel = st.selectbox(
        "Terrain",
        list(ENCOUNTER_BY_TERRAIN.keys()),
        key="ideas_terrain",
    )

    if st.button("Roll Encounter Hook", key="ideas_roll"):
        result = random.choice(ENCOUNTER_BY_TERRAIN[terrain_sel])
        st.warning(f"**{terrain_sel}:** {result}")

    with st.expander(f"All {terrain_sel} hooks ({len(ENCOUNTER_BY_TERRAIN[terrain_sel])})"):
        for idx, entry in enumerate(ENCOUNTER_BY_TERRAIN[terrain_sel], 1):
            st.markdown(f"**{idx:02d}.** {entry}")

    st.markdown("---")
    with st.expander("Browse all terrains"):
        for terrain, hooks in ENCOUNTER_BY_TERRAIN.items():
            st.markdown(f"**{terrain}** ({len(hooks)} hooks)")
            for idx, hook in enumerate(hooks, 1):
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**{idx:02d}.** {hook}")
            st.markdown("")


# ══════════════════════════════════════════════════════════════════════════════
# DUNGEON DRESSING TAB
# ══════════════════════════════════════════════════════════════════════════════
# Table data + renderer live in random_tables.py.

with tab_dress:
    st.subheader("Dungeon Dressing")
    render_dungeon_dressing("encbuilder")

