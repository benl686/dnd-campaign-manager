import json
import random
import streamlit as st
from utils import load_json, load_json_cached, save_json, edition_selector, filter_by_edition, edition_label, deduplicate_editions, sidebar_exit_button, page_nav, confirm_delete
from pathlib import Path


# ── File paths ────────────────────────────────────────────────────────────────
# magicitems.json is downloaded separately from items_srd.json because it comes
# from a different Open5e endpoint (/v2/magicitems/) and is much larger.
MAGICITEMS_PATH = Path("data/magicitems.json")
EQUIP_PATH      = Path("data/items_srd.json")     # weapons, armor, adventuring gear
HOMEBREW_PATH   = Path("json/homebrew_items.json")      # user-created items

# ── Constants ─────────────────────────────────────────────────────────────────
RARITIES = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Artifact", "Varies"]

# Category values used in magicitems.json for the subcategory filter
MAGIC_SUBCATS = ["All", "Wondrous Items", "Weapons", "Armor", "Potions",
                 "Rings", "Rods", "Scrolls", "Staves", "Wands"]

# Category strings used in items_srd.json to identify weapon/armor rows.
# These are excluded from the Equipment tab so they don't appear twice.
WEAPON_CATS          = {"Weapons", "Weapon"}
ARMOR_CATS           = {"Armor", "Shield"}
EXCLUDED_FROM_EQUIP  = WEAPON_CATS | ARMOR_CATS   # union: anything weapon or armor

HOMEBREW_CATEGORIES = [
    "Wondrous Items", "Weapons", "Armor", "Potions", "Rings",
    "Rods", "Scrolls", "Staves", "Wands", "Adventuring Gear", "Other"
]


@st.cache_data(show_spinner=False)
def _load_items(magic_path, magic_mtime, equip_path, equip_mtime, gamesystem):
    """Load, edition-filter/dedup, and split items into per-tab buckets.

    All five operations run only once per (file version × edition) combination —
    avoids re-reading 2,300+ magic items and re-filtering into tab sublists on
    every Streamlit rerender.

    Returns (magicitems, equip_all, mundane_w, magic_w, mundane_a, magic_a, gear, gear_cats).
    """
    raw_magic = json.loads(Path(magic_path).read_text(encoding="utf-8"))
    raw_equip = json.loads(Path(equip_path).read_text(encoding="utf-8"))

    # Edition dedup/filter — done once here instead of at page-level every render
    if gamesystem is None:
        raw_magic = deduplicate_editions(raw_magic, ["category", "rarity"])
        raw_equip = deduplicate_editions(raw_equip,  ["category"])
    else:
        raw_magic = filter_by_edition(raw_magic, gamesystem)
        raw_equip = filter_by_edition(raw_equip, gamesystem)

    # Split into tab-level sublists once — avoids per-render list comprehensions
    mundane_w  = [i for i in raw_equip if i.get("category", "") in WEAPON_CATS]
    magic_w    = [i for i in raw_magic if i.get("category", "") == "Weapons"]
    mundane_a  = [i for i in raw_equip if i.get("category", "") in ARMOR_CATS]
    magic_a    = [i for i in raw_magic if i.get("category", "") == "Armor"]
    gear       = [i for i in raw_equip if i.get("category", "") not in EXCLUDED_FROM_EQUIP]
    gear_cats  = sorted({i.get("category", "") for i in gear if i.get("category")})

    return raw_magic, raw_equip, mundane_w, magic_w, mundane_a, magic_a, gear, gear_cats

# ── Tattoo data ───────────────────────────────────────────────────────────────
# Tasha's Cauldron of Everything magical tattoos — hardcoded because they are not
# available through Open5e or 5etools in a clean structured format.
TATTOOS = [
    {
        "name": "Absorbing Tattoo",
        "rarity": "Very Rare",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo contains a single color, and it changes you in subtle ways. "
            "While this tattoo is on your skin, you have resistance to a type of damage based on the color: "
            "acid (green), cold (blue), fire (red), force (white), lightning (yellow), necrotic (black), "
            "poison (purple), psychic (silver), radiant (gold), or thunder (orange).\n\n"
            "**Absorb Elements.** When you take damage of the chosen type, you can use your reaction to gain immunity "
            "to that damage type until the start of your next turn, including against the triggering damage. "
            "You can use this reaction a number of times equal to your proficiency bonus, and you regain all "
            "expended uses when you finish a long rest."
        ),
        "tags": ["Damage Resistance", "Reaction"],
    },
    {
        "name": "Barrier Tattoo",
        "rarity": "Uncommon / Rare / Very Rare",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo depicts protective imagery and uses ink that resembles armor.\n\n"
            "**Protection.** While you aren't wearing armor, the tattoo grants you an Armor Class depending on the tattoo's rarity:\n\n"
            "- **Uncommon:** AC 12 + Dex modifier\n"
            "- **Rare:** AC 15 + Dex modifier (max 2)\n"
            "- **Very Rare:** AC 18 (no modifier)\n\n"
            "You can use a shield and still gain this benefit."
        ),
        "tags": ["Armor Class", "Defense"],
    },
    {
        "name": "Blood Fury Tattoo",
        "rarity": "Legendary",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo evokes fury in its form. It has 10 charges.\n\n"
            "**Bloodthirsty Strikes.** While this tattoo is on your skin, you can expend the tattoo's charges in the following ways:\n\n"
            "- When you hit a creature with a weapon attack, you can expend 1 charge to deal an extra 4d6 necrotic damage, "
            "and you regain a number of hit points equal to the necrotic damage dealt.\n"
            "- When a creature you can see damages you, you can expend 3 charges and use your reaction to make a melee attack "
            "against that creature, with advantage on your attack roll.\n\n"
            "The tattoo regains all expended charges daily at dawn."
        ),
        "tags": ["Necrotic", "Healing", "Attack"],
    },
    {
        "name": "Coiling Grasp Tattoo",
        "rarity": "Uncommon",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo has long intertwining designs. While the tattoo is on your skin, "
            "you can, as an action, cause the tattoo to extrude into an inky tentacle, which reaches out at one creature you "
            "can see within 15 feet of you. The creature must succeed on a DC 14 Strength saving throw or be grappled by you "
            "until the start of your next turn. As an action, you can release the creature early. Until the grapple ends, "
            "the creature is restrained, and you can't use the tentacle on another target. The tentacle vanishes when the grapple ends."
        ),
        "tags": ["Grapple", "Control"],
    },
    {
        "name": "Eldritch Claw Tattoo",
        "rarity": "Uncommon",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo depicts clawlike forms and other jagged shapes. "
            "While this tattoo is on your skin, your unarmed strikes are considered magical for the purpose of overcoming "
            "immunity and resistance to nonmagical attacks, and you gain a +1 bonus to attack rolls and damage rolls with unarmed strikes.\n\n"
            "**Eldritch Maul.** As a bonus action, you can empower the tattoo for 1 minute. For the duration, each of your "
            "unarmed strikes can reach a target up to 15 feet away from you, as inky tendrils launch from your arm toward "
            "the target. In addition, your unarmed strikes deal 1d6 force damage on a hit. Once used, this bonus action "
            "can't be used again until the next dawn."
        ),
        "tags": ["Unarmed Strikes", "Force", "Melee"],
    },
    {
        "name": "Ghost Step Tattoo",
        "rarity": "Very Rare",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo shifts and wavers on the skin, as if being viewed through "
            "running water. The tattoo has 3 charges, and it regains all expended charges daily at dawn.\n\n"
            "**Ghostly Form.** As a bonus action while this tattoo is on your skin, you can expend 1 of the tattoo's "
            "charges to become incorporeal until the end of your turn. For the duration, you gain the following benefits:\n\n"
            "- You have resistance to bludgeoning, piercing, and slashing damage from nonmagical attacks.\n"
            "- You can't be grappled or restrained.\n"
            "- You can move through other creatures and objects as if they were difficult terrain. If you end your turn "
            "inside an object, you take 1d10 force damage. If this damage reduces you to 0 hit points, you are ejected "
            "from the object in the nearest unoccupied space."
        ),
        "tags": ["Incorporeal", "Movement", "Defense"],
    },
    {
        "name": "Illuminator's Tattoo",
        "rarity": "Common",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo features beautiful calligraphy, images of writing implements, "
            "and other such imagery. While this tattoo is on your skin, you can write with your fingertip as if it were "
            "an ink pen that never runs out of ink.\n\n"
            "As a bonus action, you can cause writing of your choice to appear on a surface you touch, "
            "or cause writing on a surface you touch to disappear. Either way, the writing can cover an area no larger "
            "than 1 square foot. The writing remains until you use this feature again. The writing is invisible to "
            "everyone except you and creatures you choose when you use this bonus action. Once you use this bonus action, "
            "it can't be used again until the next dawn."
        ),
        "tags": ["Utility", "Writing"],
    },
    {
        "name": "Lifewell Tattoo",
        "rarity": "Very Rare",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo comprises symbols of life and rebirth.\n\n"
            "**Life Ward.** While this tattoo is on your skin, you have immunity to necrotic damage.\n\n"
            "When you would be reduced to 0 hit points, you can use your reaction to instead be reduced to 1 hit point. "
            "Once this reaction is used, it can't be used again until the next dawn."
        ),
        "tags": ["Immunity", "Necrotic", "Survival"],
    },
    {
        "name": "Masquerade Tattoo",
        "rarity": "Common",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo appears on your skin as whatever you desire. As a bonus action, "
            "you can shape the tattoo into any color or pattern and move it to any area of your skin. Whatever form it takes, "
            "it is always obviously a tattoo. It can range in size from no smaller than a copper piece to an intricate work "
            "of art that covers all your skin.\n\n"
            "While the tattoo is on your skin, you can cast the *disguise self* spell from it as an action. "
            "Once the spell is cast from the tattoo, it can't be cast again until the next dawn."
        ),
        "tags": ["Disguise", "Utility"],
    },
    {
        "name": "Shadowfell Brand Tattoo",
        "rarity": "Very Rare",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this magic tattoo is shadowy and ever-shifting.\n\n"
            "**Shadow Essence.** You gain darkvision with a range of 60 feet. If you already have darkvision, its range "
            "increases by 30 feet.\n\n"
            "**Shadowy Defense.** When you are hit by an attack roll, you can use your reaction to become insubstantial "
            "for a moment, causing that attack to deal only half its damage to you. You then teleport, along with any "
            "equipment you are wearing or carrying, up to 30 feet to an unoccupied space you can see. Once this reaction "
            "is used, it can't be used again until the next dawn."
        ),
        "tags": ["Darkvision", "Teleportation", "Defense"],
    },
    {
        "name": "Spellwrought Tattoo",
        "rarity": "Common to Legendary (by spell level)",
        "attunement": "No",
        "desc": (
            "Produced by a special needle, this tattoo contains a single spell of up to 5th level, wrought on your skin "
            "by a magic needle. To use the tattoo, you must hold the needle against your skin and speak the needle's "
            "command word. The needle turns into the ink that becomes the tattoo, which appears on your skin.\n\n"
            "Once the tattoo is there, you can cast its spell, requiring no material components. The tattoo glows faintly "
            "while you cast the spell and for the spell's duration. Once the spell ends, the tattoo vanishes from your skin.\n\n"
            "**Rarity by spell level:**\n"
            "- Cantrip: Common\n"
            "- 1st level: Common\n"
            "- 2nd level: Uncommon\n"
            "- 3rd level: Uncommon\n"
            "- 4th level: Rare\n"
            "- 5th level: Rare"
        ),
        "tags": ["Spellcasting", "Versatile"],
    },
    {
        "name": "Venomous Tattoo",
        "rarity": "Uncommon",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this tattoo is decorated with serpentine imagery. While this tattoo is on "
            "your skin, you gain the following benefits:\n\n"
            "- Your unarmed strikes deal an additional 1d6 poison damage on a hit.\n"
            "- You have advantage on saving throws you make to avoid or end the poisoned condition on yourself.\n"
            "- You have resistance to poison damage."
        ),
        "tags": ["Poison", "Unarmed", "Resistance"],
    },
    {
        "name": "Vigilant Blade Tattoo",
        "rarity": "Uncommon",
        "attunement": "Yes",
        "desc": (
            "Produced by a special needle, this tattoo depicts bladed weapons. While the tattoo is on your skin, "
            "you have proficiency with all simple and martial weapons, and your speed is not reduced by wearing heavy armor.\n\n"
            "In addition, when you roll initiative, you can add your proficiency bonus to the roll."
        ),
        "tags": ["Combat", "Weapons", "Initiative"],
    },
]
# Collect every unique tag across all tattoos for the multiselect filter
TATTOO_TAGS = sorted({tag for t in TATTOOS for tag in t.get("tags", [])})


# ── Item renderers ────────────────────────────────────────────────────────────

def render_magic_item(item):
    """Render a magic item's details: rarity, attunement, damage (if weapon), AC (if armor), description."""
    rarity = item.get("rarity", "")
    attune = item.get("requires_attunement", "")
    cost   = item.get("cost", "")

    # Build the metadata line from whatever fields are present
    meta = []
    if rarity:  meta.append(f"**Rarity:** {rarity}")
    if attune:  meta.append(f"**Attunement:** {attune}")
    if cost:    meta.append(f"**Cost:** {cost}")
    if meta:
        st.markdown("  |  ".join(meta))

    # Weapon stats (only present on weapon-type magic items)
    dmg      = item.get("damage_dice", "")
    dmg_type = item.get("damage_type", "")
    props    = item.get("properties", "")
    if dmg:
        st.markdown(f"**Damage:** {dmg} {dmg_type}  |  **Properties:** {props or '—'}")

    # Armor stats (only present on armor-type magic items)
    ac = item.get("armor_class", "")
    if ac:
        stealth = " (Stealth disadvantage)" if item.get("stealth_disadvantage") else ""
        str_req = item.get("strength_requirement", "")
        st.markdown(
            f"**AC:** {ac}{stealth}"
            f"{f'  |  Strength {str_req} required' if str_req else ''}"
        )

    desc = item.get("description", "")
    if desc:
        st.markdown(desc)


def render_equip_item(item):
    """Render a mundane equipment item's details: cost, weight, damage (weapons), AC (armor), description."""
    cost   = item.get("cost", "")
    weight = item.get("weight", "")

    meta = []
    if cost:   meta.append(f"**Cost:** {cost}")
    if weight: meta.append(f"**Weight:** {weight}")
    if meta:
        st.markdown("  |  ".join(meta))

    dmg      = item.get("damage_dice", "")
    dmg_type = item.get("damage_type", "")
    if dmg:
        props = item.get("properties", "")
        st.markdown(f"**Damage:** {dmg} {dmg_type}  |  **Properties:** {props or '—'}")

    # base_ac comes from items_srd.json (equipment endpoint); armor_class is the fallback
    base_ac = item.get("base_ac", "") or item.get("armor_class", "")
    if base_ac:
        stealth = " (Stealth disadvantage)" if item.get("stealth_disadvantage") else ""
        st.markdown(f"**AC:** {base_ac}{stealth}")

    desc = item.get("description", "")
    if desc:
        st.markdown(desc)


# ── Page setup ────────────────────────────────────────────────────────────────

# ── Artifact property tables (DMG) ───────────────────────────────────────────
# Each entry is a tuple: (lo, hi, text). Ranges are uneven so roll is resolved
# by iterating until lo <= roll <= hi. hi=100 is displayed as "00".

MINOR_BENEFICIAL = [
    (1,  20, "While attuned to the artifact, you gain proficiency in one skill of the DM's choice."),
    (21, 30, "While attuned to the artifact, you are immune to disease."),
    (31, 40, "While attuned to the artifact, you can't be charmed or frightened."),
    (41, 50, "While attuned to the artifact, you have resistance against one damage type of the DM's choice."),
    (51, 60, "While attuned to the artifact, you can use an action to cast one cantrip (chosen by the DM) from it."),
    (61, 70, "While attuned to the artifact, you can use an action to cast one 1st-level spell (chosen by the DM) from it. After you cast the spell, roll a d6. On a roll of 1–5, you can't cast it again until the next dawn."),
    (71, 80, "As 61–70 above, except the spell is 2nd level."),
    (81, 90, "As 61–70 above, except the spell is 3rd level."),
    (91, 100, "While attuned to the artifact, you gain a +1 bonus to Armor Class."),
]

MAJOR_BENEFICIAL = [
    (1,  20, "While attuned to the artifact, one of your ability scores (DM's choice) increases by 2, to a maximum of 24."),
    (21, 30, "While attuned to the artifact, you regain 1d6 hit points at the start of your turn if you have at least 1 hit point."),
    (31, 40, "When you hit with a weapon attack while attuned to the artifact, the target takes an extra 1d6 damage of the weapon's type."),
    (41, 50, "While attuned to the artifact, your walking speed increases by 10 feet."),
    (51, 60, "While attuned to the artifact, you can use an action to cast one 4th-level spell (chosen by the DM) from it. After you cast the spell, roll a d6. On a roll of 1–5, you can't cast it again until the next dawn."),
    (61, 70, "As 51–60 above, except the spell is 5th level."),
    (71, 80, "As 51–60 above, except the spell is 6th level."),
    (81, 90, "As 51–60 above, except the spell is 7th level."),
    (91, 100, "While attuned to the artifact, you can't be blinded, deafened, petrified, or stunned."),
]

MINOR_DETRIMENTAL = [
    (1,  5,  "While attuned to the artifact, you have disadvantage on saving throws against spells."),
    (6,  10, "The first time you touch a gem or piece of jewelry while attuned to this artifact, the value of the gem or jewelry is reduced by half."),
    (11, 15, "While attuned to the artifact, you are blinded when you are more than 10 feet away from it."),
    (16, 20, "While attuned to the artifact, you have disadvantage on saving throws against poison."),
    (21, 30, "While attuned to the artifact, you emit a sour stench noticeable from up to 10 feet away."),
    (31, 35, "While attuned to the artifact, all holy water within 10 feet of you is destroyed."),
    (36, 40, "While attuned to the artifact, you are physically ill and have disadvantage on any ability check or saving throw that uses Strength or Constitution."),
    (41, 45, "While attuned to the artifact, your weight increases by 1d4 × 10 pounds."),
    (46, 50, "While attuned to the artifact, your appearance changes as the DM decides."),
    (51, 55, "While attuned to the artifact, you are deafened when you are more than 10 feet away from it."),
    (56, 60, "While attuned to the artifact, your weight drops by 1d4 × 5 pounds."),
    (61, 65, "While attuned to the artifact, you can't smell."),
    (66, 70, "While attuned to the artifact, nonmagical flames are extinguished within 30 feet of you."),
    (71, 80, "While you are attuned to the artifact, other creatures can't take short or long rests while within 300 feet of you."),
    (81, 85, "While attuned to the artifact, you deal 1d6 necrotic damage to any plant you touch that isn't a creature."),
    (86, 90, "While you are attuned to the artifact, animals within 30 feet of you are hostile toward you."),
    (91, 95, "While attuned to the artifact, you must eat and drink six times the normal amount each day."),
    (96, 100, "While you are attuned to the artifact, your flaw is amplified in a way determined by the DM."),
]

MAJOR_DETRIMENTAL = [
    (1,  5,  "While you are attuned to the artifact, your body rots over the course of four days, after which the rotting stops. You lose your hair by the end of day 1, fingertips and toe tips by the end of day 2, lips and nose by the end of day 3, and ears by the end of day 4. A regenerate spell restores lost body parts."),
    (6,  10, "While you are attuned to the artifact, you determine your alignment daily at dawn by rolling a d6 twice. On the first roll, a 1–2 indicates lawful, 3–4 neutral, and 5–6 chaotic. On the second roll, a 1–2 indicates good, 3–4 neutral, and 5–6 evil."),
    (11, 15, "When you first attune to the artifact, it gives you a quest determined by the DM. You must complete this quest as if affected by the geas spell. Once you complete the quest, you are no longer affected by this property."),
    (16, 20, "The artifact houses a bodiless life force that is hostile toward you. Each time you use an action to use one of the artifact's properties, there is a 50 percent chance that the life force tries to leave the artifact and enter your body. If you fail a DC 20 Charisma saving throw, it succeeds, and you become an NPC under the DM's control until the intruding life force is banished using magic such as the dispel evil and good spell."),
    (21, 25, "Creatures with a challenge rating of 0, as well as plants that aren't creatures, drop to 0 hit points when within 10 feet of the artifact."),
    (26, 30, "The artifact imprisons a death slaad. Each time you use one of the artifact's properties as an action, the slaad has a 10 percent chance of escaping, whereupon it appears within 15 feet of you and attacks you."),
    (31, 35, "While you are attuned to the artifact, creatures of a particular type other than humanoid (as chosen by the DM) are always hostile toward you."),
    (36, 40, "The artifact dilutes magic potions within 10 feet of it, rendering them nonmagical."),
    (41, 45, "The artifact erases magic scrolls within 10 feet of it, rendering them nonmagical."),
    (46, 50, "Before using one of the artifact's properties as an action, you must use a bonus action to draw blood, either from yourself or from a willing or incapacitated creature within your reach, using a piercing or slashing melee weapon. The subject takes 1d4 damage of the appropriate type."),
    (51, 60, "When you become attuned to the artifact, you gain a form of long-term madness."),
    (61, 65, "You take 4d10 psychic damage when you become attuned to the artifact."),
    (66, 70, "You take 8d10 psychic damage when you become attuned to the artifact."),
    (71, 75, "Before you can become attuned to the artifact, you must kill a creature of your alignment."),
    (76, 80, "When you become attuned to the artifact, one of your ability scores is reduced by 2 at random. A greater restoration spell restores the ability to normal."),
    (81, 85, "Each time you become attuned to the artifact, you age 3d10 years. You must succeed on a DC 10 Constitution saving throw or die from the shock. If you die, you are instantly transformed into a wight under the DM's control that is sworn to protect the artifact."),
    (86, 90, "While attuned to the artifact, you lose the ability to speak."),
    (91, 95, "While attuned to the artifact, you have vulnerability to all damage."),
    (96, 100, "When you become attuned to the artifact, there is a 10 percent chance that you attract the attention of a god that sends an avatar to wrest the artifact from you. The avatar has the same alignment as its creator and the statistics of an empyrean. Once it obtains the artifact, the avatar vanishes."),
]


def _range_label(lo: int, hi: int) -> str:
    """Format a d100 roll range; 100 is displayed as '00'."""
    return f"{lo:02d}–{'00' if hi == 100 else f'{hi:02d}'}"


def _roll_prop(table: list) -> tuple[int, int, int, str]:
    """Roll d100 and return (roll, lo, hi, text) by scanning the range tuples."""
    roll = random.randint(1, 100)
    for lo, hi, text in table:
        if lo <= roll <= hi:
            return roll, lo, hi, text
    lo, hi, text = table[-1]
    return roll, lo, hi, text


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Items Reference")

# Edition filter — applies to magic weapons, armor, and magic items
st.caption("Edition filter applies to magic weapons, armor, and magic items.")
gamesystem = edition_selector(sidebar=False)

# _load_items caches: file reads + edition dedup/filter + per-tab sublist splits.
# Nothing re-runs on reruns unless a file changes on disk or the edition selector changes.
if not MAGICITEMS_PATH.exists() or not EQUIP_PATH.exists():
    magicitems = equip_all = mundane_w = magic_w = mundane_a = magic_a = gear = []
    gear_cats = []
else:
    (magicitems, equip_all,
     mundane_w, magic_w,
     mundane_a, magic_a,
     gear, gear_cats) = _load_items(
        str(MAGICITEMS_PATH), MAGICITEMS_PATH.stat().st_mtime,
        str(EQUIP_PATH),      EQUIP_PATH.stat().st_mtime,
        gamesystem,
    )

tab_weapons, tab_armor, tab_magic, tab_equip, tab_tattoos, tab_homebrew = st.tabs(
    ["Weapons", "Armor", "Magic Items", "Equipment", "Tattoos", "Homebrew"]
)


# ── WEAPONS tab ───────────────────────────────────────────────────────────────
with tab_weapons:
    # mundane_w / magic_w already split by _load_items above

    fc1, fc2, fc3 = st.columns([3, 2, 2])
    w_search = fc1.text_input("Search weapons", key="w_search", placeholder="e.g. sword")
    w_type   = fc2.radio("Show", ["All", "Mundane only", "Magic only"], horizontal=True, key="w_type")
    w_rarity = fc3.multiselect("Rarity (magic)", RARITIES, key="w_rarity")

    # Merge mundane and magic lists; tag each entry so the renderer knows which to use
    combined_w = []
    if w_type != "Magic only":
        combined_w += [{**i, "_magic": False} for i in mundane_w]
    if w_type != "Mundane only":
        combined_w += [{**i, "_magic": True} for i in magic_w]

    if w_search:
        sl = w_search.lower()
        combined_w = [i for i in combined_w if sl in i.get("name", "").lower()]
    if w_rarity:
        # Rarity filter only makes sense for magic items; mundane items pass through
        combined_w = [i for i in combined_w if not i["_magic"] or i.get("rarity", "").title() in w_rarity]
    combined_w = sorted(combined_w, key=lambda i: i.get("name", ""))

    # Only render results once the user has searched or filtered
    if w_search or w_rarity or w_type != "All":
        filter_sig_w = (w_search, tuple(w_rarity), w_type, gamesystem)
        page_slice_w = page_nav(combined_w, "weapons_page", "_weapons_sig", filter_sig_w)
        for it in page_slice_w:
            badge  = "✦ " if it["_magic"] else ""   # ✦ prefix marks magic items visually
            rarity = it.get("rarity", "")
            src    = edition_label(it.get("gamesystem_key", ""))
            label  = (f"{badge}{it['name']}"
                      + (f"  —  {rarity}" if rarity else "")
                      + (f"  —  {src}" if src else ""))
            with st.expander(label):
                if it["_magic"]:
                    render_magic_item(it)
                else:
                    render_equip_item(it)
    else:
        st.info("Search by name or select a filter above to see weapons.")


# ── ARMOR tab ─────────────────────────────────────────────────────────────────
with tab_armor:
    # mundane_a / magic_a already split by _load_items above

    ac1, ac2, ac3 = st.columns([3, 2, 2])
    a_search = ac1.text_input("Search armor", key="a_search", placeholder="e.g. plate")
    a_type   = ac2.radio("Show", ["All", "Mundane only", "Magic only"], horizontal=True, key="a_type")
    a_rarity = ac3.multiselect("Rarity (magic)", RARITIES, key="a_rarity")

    combined_a = []
    if a_type != "Magic only":
        combined_a += [{**i, "_magic": False} for i in mundane_a]
    if a_type != "Mundane only":
        combined_a += [{**i, "_magic": True} for i in magic_a]

    if a_search:
        sl = a_search.lower()
        combined_a = [i for i in combined_a if sl in i.get("name", "").lower()]
    if a_rarity:
        combined_a = [i for i in combined_a if not i["_magic"] or i.get("rarity", "").title() in a_rarity]
    combined_a = sorted(combined_a, key=lambda i: i.get("name", ""))

    # Only render results once the user has searched or filtered
    if a_search or a_rarity or a_type != "All":
        filter_sig_a = (a_search, tuple(a_rarity), a_type, gamesystem)
        page_slice_a = page_nav(combined_a, "armor_page", "_armor_sig", filter_sig_a)
        for it in page_slice_a:
            badge  = "✦ " if it["_magic"] else ""
            rarity = it.get("rarity", "")
            src    = edition_label(it.get("gamesystem_key", ""))
            label  = (f"{badge}{it['name']}"
                      + (f"  —  {rarity}" if rarity else "")
                      + (f"  —  {src}" if src else ""))
            with st.expander(label):
                if it["_magic"]:
                    render_magic_item(it)
                else:
                    render_equip_item(it)
    else:
        st.info("Search by name or select a filter above to see armor.")


# ── MAGIC ITEMS tab ───────────────────────────────────────────────────────────
with tab_magic:
    mi_tab_items, mi_tab_props = st.tabs(["Magic Items", "Artifact Properties"])

    # ── Magic Items sub-tab ───────────────────────────────────────────────────
    with mi_tab_items:
        # magicitems already loaded and edition-filtered by _load_items above
        if not magicitems:
            st.warning("Magic item data not found. Run `python scripts/download_data.py` to download it.")
        else:
            mc1, mc2, mc3, mc4 = st.columns([3, 2, 2, 2])
            mi_search = mc1.text_input("Search magic items", key="mi_search")
            mi_cat    = mc2.selectbox("Category", MAGIC_SUBCATS, key="mi_cat")
            mi_rarity = mc3.multiselect("Rarity", RARITIES, key="mi_rarity")
            mi_attune = mc4.radio("Attunement", ["All", "Required", "Not required"], key="mi_attune")

            # Require 3+ chars for name search — magic items list has 2,300+ entries and
            # 1-2 character queries return most of them, causing excessive render time.
            # Category/rarity/attunement filters are intentional selections; no restriction.
            mi_search_active = len(mi_search) >= 3 if mi_search else False
            if mi_search and not mi_search_active:
                st.caption("Type at least 3 characters to search by name.")

            # magicitems is already edition-filtered/deduped by _load_items above
            filtered_mi = magicitems
            if mi_search_active:
                filtered_mi = [i for i in filtered_mi if mi_search.lower() in i.get("name", "").lower()]
            if mi_cat != "All":
                filtered_mi = [i for i in filtered_mi if i.get("category", "") == mi_cat]
            if mi_rarity:
                filtered_mi = [i for i in filtered_mi if i.get("rarity", "").title() in mi_rarity]
            if mi_attune == "Required":
                filtered_mi = [i for i in filtered_mi if i.get("requires_attunement")]
            elif mi_attune == "Not required":
                filtered_mi = [i for i in filtered_mi if not i.get("requires_attunement")]
            filtered_mi = sorted(filtered_mi, key=lambda i: i.get("name", ""))

            # Only render results once the user has searched or applied a non-default filter
            if mi_search_active or mi_cat != "All" or mi_rarity or mi_attune != "All":
                filter_sig_mi = (mi_search, mi_cat, tuple(mi_rarity), mi_attune, gamesystem)
                page_slice_mi = page_nav(filtered_mi, "magic_page", "_magic_sig", filter_sig_mi)
                for it in page_slice_mi:
                    cat      = it.get("category", "")
                    rarity   = it.get("rarity", "")
                    # Build "Category  |  Rarity" subtitle, skipping empty parts
                    subtitle = "  |  ".join(filter(None, [cat, rarity]))
                    src      = edition_label(it.get("gamesystem_key", ""))
                    with st.expander(
                        f"{it['name']}"
                        + (f"  —  {subtitle}" if subtitle else "")
                        + (f"  —  {src}" if src else "")
                    ):
                        render_magic_item(it)
            else:
                st.info("Search by name or select a filter above to see magic items.")

    # ── Artifact Properties sub-tab ───────────────────────────────────────────
    with mi_tab_props:
        st.subheader("Artifact Properties")
        st.caption(
            "Each artifact can have up to four minor beneficial properties, two major "
            "beneficial properties, four minor detrimental properties, and two major "
            "detrimental properties. Roll d100 on the relevant table."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Roll Minor Beneficial", key="art_minor_ben"):
                roll, lo, hi, result = _roll_prop(MINOR_BENEFICIAL)
                st.success(f"**Roll {roll:02d} ({_range_label(lo, hi)}):** {result}")

            with st.expander("Minor Beneficial table"):
                for lo, hi, entry in MINOR_BENEFICIAL:
                    st.markdown(f"**{_range_label(lo, hi)}** — {entry}")

            st.divider()

            if st.button("Roll Major Beneficial", key="art_major_ben"):
                roll, lo, hi, result = _roll_prop(MAJOR_BENEFICIAL)
                st.success(f"**Roll {roll:02d} ({_range_label(lo, hi)}):** {result}")

            with st.expander("Major Beneficial table"):
                for lo, hi, entry in MAJOR_BENEFICIAL:
                    st.markdown(f"**{_range_label(lo, hi)}** — {entry}")

        with col2:
            if st.button("Roll Minor Detrimental", key="art_minor_det"):
                roll, lo, hi, result = _roll_prop(MINOR_DETRIMENTAL)
                st.error(f"**Roll {roll:02d} ({_range_label(lo, hi)}):** {result}")

            with st.expander("Minor Detrimental table"):
                for lo, hi, entry in MINOR_DETRIMENTAL:
                    st.markdown(f"**{_range_label(lo, hi)}** — {entry}")

            st.divider()

            if st.button("Roll Major Detrimental", key="art_major_det"):
                roll, lo, hi, result = _roll_prop(MAJOR_DETRIMENTAL)
                st.error(f"**Roll {roll:02d} ({_range_label(lo, hi)}):** {result}")

            with st.expander("Major Detrimental table"):
                for lo, hi, entry in MAJOR_DETRIMENTAL:
                    st.markdown(f"**{_range_label(lo, hi)}** — {entry}")

        st.divider()

        if st.button("Roll All Four (full artifact)", key="art_roll_all"):
            for label, table, fn in [
                ("Minor Beneficial",  MINOR_BENEFICIAL,  st.success),
                ("Major Beneficial",  MAJOR_BENEFICIAL,  st.success),
                ("Minor Detrimental", MINOR_DETRIMENTAL, st.error),
                ("Major Detrimental", MAJOR_DETRIMENTAL, st.error),
            ]:
                roll, lo, hi, result = _roll_prop(table)
                fn(f"**{label} — Roll {roll:02d} ({_range_label(lo, hi)}):** {result}")


# ── EQUIPMENT tab ─────────────────────────────────────────────────────────────
with tab_equip:
    # gear / gear_cats already split by _load_items above
    if not gear:
        st.warning("Equipment data not found. Run `python scripts/download_data.py` to download it.")
    else:
        ec1, ec2 = st.columns([3, 3])
        eq_search = ec1.text_input("Search equipment", key="eq_search")
        eq_cat    = ec2.selectbox("Category", ["All"] + gear_cats, key="eq_cat")

        filtered_eq = gear
        if eq_search:
            filtered_eq = [i for i in filtered_eq if eq_search.lower() in i.get("name", "").lower()]
        if eq_cat != "All":
            filtered_eq = [i for i in filtered_eq if i.get("category", "") == eq_cat]
        filtered_eq = sorted(filtered_eq, key=lambda i: i.get("name", ""))

        # Only render results once the user has searched or picked a category
        if eq_search or eq_cat != "All":
            filter_sig_eq = (eq_search, eq_cat, gamesystem)
            page_slice_eq = page_nav(filtered_eq, "equip_page", "_equip_sig", filter_sig_eq)
            for it in page_slice_eq:
                cat = it.get("category", "")
                src = edition_label(it.get("gamesystem_key", ""))
                with st.expander(
                    f"{it['name']}"
                    + (f"  —  {cat}" if cat else "")
                    + (f"  —  {src}" if src else "")
                ):
                    render_equip_item(it)
        else:
            st.info("Search by name or select a category above to see equipment.")


# ── TATTOOS tab ───────────────────────────────────────────────────────────────
with tab_tattoos:
    st.caption("Magical tattoos from Tasha's Cauldron of Everything. Each requires a magic needle to apply.")

    tc1, tc2, tc3 = st.columns([3, 2, 2])
    t_search = tc1.text_input("Search tattoos", key="t_search")
    t_rarity = tc2.multiselect("Rarity", RARITIES, key="t_rarity")
    t_tags   = tc3.multiselect("Tags", TATTOO_TAGS, key="t_tags")

    filtered_t = TATTOOS[:]   # copy so filters don't mutate the constant
    if t_search:
        sl = t_search.lower()
        filtered_t = [t for t in filtered_t if sl in t["name"].lower() or sl in t["desc"].lower()]
    if t_rarity:
        # Rarity field can be "Uncommon / Rare / Very Rare" so check with `in`
        filtered_t = [t for t in filtered_t if any(r in t["rarity"] for r in t_rarity)]
    if t_tags:
        # Keep tattoos that have at least one of the selected tags
        filtered_t = [t for t in filtered_t if any(tag in t.get("tags", []) for tag in t_tags)]

    st.caption(f"{len(filtered_t)} tattoos found")
    for tattoo in filtered_t:
        attune_note = "Requires attunement" if tattoo["attunement"] == "Yes" else "No attunement"
        with st.expander(f"**{tattoo['name']}**  —  {tattoo['rarity']}  |  {attune_note}"):
            tags_str = "  ".join(f"`{tag}`" for tag in tattoo.get("tags", []))
            if tags_str:
                st.markdown(tags_str)
            st.markdown(tattoo["desc"])


# ── HOMEBREW tab ──────────────────────────────────────────────────────────────
with tab_homebrew:
    # Load homebrew items into session state on first visit; avoid re-reading on reruns
    if "homebrew_items" not in st.session_state:
        st.session_state.homebrew_items = load_json(HOMEBREW_PATH, [])

    st.subheader("Add Homebrew Item")
    with st.form("add_homebrew_item"):
        hi_name = st.text_input("Item Name")
        hic1, hic2, hic3 = st.columns(3)
        hi_cat       = hic1.selectbox("Category", HOMEBREW_CATEGORIES)
        hi_rarity    = hic2.selectbox("Rarity", RARITIES)
        hi_attune_sel = hic3.selectbox(
            "Requires Attunement",
            ["No", "Yes", "Yes — by condition (specify below)"],
        )
        hi_cost  = st.text_input("Cost", placeholder="e.g. 500 gp")
        # Condition detail — only relevant when "Yes — by condition" is chosen above
        hi_attune_detail = st.text_input(
            "Attunement condition",
            placeholder="e.g. by a wizard, by a creature of evil alignment",
            key="hi_attune_detail",
        )
        if hi_attune_sel == "No":
            hi_attune = ""
        elif hi_attune_sel == "Yes":
            hi_attune = "Yes"
        else:
            hi_attune = hi_attune_detail.strip() or "Yes"
        hi_desc   = st.text_area("Description", height=200)

        if st.form_submit_button("Add Homebrew Item"):
            if hi_name.strip():
                new_item = {
                    "name": hi_name.strip(), "category": hi_cat, "rarity": hi_rarity,
                    "requires_attunement": hi_attune,
                    "cost": hi_cost.strip(), "description": hi_desc, "homebrew": True,
                }
                st.session_state.homebrew_items.append(new_item)
                save_json(HOMEBREW_PATH, st.session_state.homebrew_items)
                st.success(f"Added {hi_name.strip()}")
            else:
                st.error("Name is required")

    hb_items = st.session_state.homebrew_items
    st.subheader("Your Homebrew Items")
    if not hb_items:
        st.info("No homebrew items yet. Add one above.")
    else:
        for i, it in enumerate(hb_items):
            with st.expander(
                f"{it['name']}  —  {it.get('category', '')}  |  {it.get('rarity', '')}"
            ):
                render_magic_item(it)

                # Two-step delete: first click arms the confirmation, second click deletes
                dc1, dc2 = st.columns([8, 1])
                if confirm_delete(dc2, f"hbi_delete_{i}", f"hbi_{i}"):
                    st.session_state.homebrew_items.pop(i)
                    save_json(HOMEBREW_PATH, st.session_state.homebrew_items)
                    st.rerun()

