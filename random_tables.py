"""Shared random roll tables + renderers.

Data layer for roll-on-demand flavor tables that appear on multiple pages
(Streamlit page files cannot import from each other, so shared tables live
here in the project root — same pattern as treasure_tables.py).

Current consumers:
- WILD_MAGIC       → pages/Spells.py (Wild Magic tab) and pages/Combat.py (expander)
- DUNGEON_DRESSING → pages/EncounterBuilder.py (Dungeon Dressing tab)

Each table ships with a `render_*` helper so the roll button + full-table
expander behave identically everywhere. Callers pass a unique `key_prefix`
so widget keys never collide across pages.
"""

import random
import streamlit as st


# ── Wild Magic Surge (d100, 50 paired entries: 01–02 … 99–100) ────────────────

WILD_MAGIC = [
    "Roll on this table at the start of each of your turns for the next minute, ignoring this result on subsequent rolls.",
    "For the next minute, you can see any invisible creature if you have line of sight to it.",
    "A modron chosen and controlled by the DM appears in an unoccupied space within 5 feet of you, then disappears 1 minute later.",
    "You cast Fireball as a 3rd-level spell centered on yourself.",
    "You cast Magic Missile as a 5th-level spell.",
    "Roll a d10. Your height changes by a number of inches equal to the roll. If even, you grow; if odd, you shrink.",
    "You cast Confusion centered on yourself.",
    "For the next minute, you regain 5 hit points at the start of each of your turns.",
    "You grow a long beard made of feathers that remains until you sneeze, at which point the feathers explode from your face.",
    "You teleport up to 60 feet to an unoccupied space of your choice that you can see.",
    "A unicorn controlled by the DM appears in a space within 5 feet of you, then disappears 1 minute later.",
    "You can't speak for the next minute. Whenever you try, pink bubbles float out of your mouth.",
    "A spectral shield hovers near you for the next minute, granting you a +2 bonus to AC and immunity to Magic Missile.",
    "You are immune to being intoxicated by alcohol for the next 5d6 days.",
    "Your hair falls out but grows back within 24 hours.",
    "Until you cast a spell, you have disadvantage on attack rolls and ability checks.",
    "You cast Polymorph on yourself. If you fail the saving throw, you turn into a sheep for the spell's duration.",
    "Illusory butterflies and flower petals flutter in the air within 10 feet of you for the next minute.",
    "You can take one additional action immediately.",
    "Each creature within 30 feet of you becomes invisible for the next minute. Attacking or casting a spell breaks the effect.",
    "You gain resistance to all damage for the next minute.",
    "A random creature within 60 feet of you becomes poisoned for 1d4 hours.",
    "You glow with bright light in a 30-foot radius for the next minute. Any creature that ends its turn within 5 feet of you is blinded until the end of its next turn.",
    "You cast Polymorph on a random creature within 60 feet of you. If it fails, it turns into a goat.",
    "Leaves grow from you. They remain until one of the long rest conditions is met.",
    "A number of Magic Mouths (as the spell) equal to your proficiency bonus appear on surfaces near you and spend 1 minute loudly announcing your arrival.",
    "For the next minute, any flammable object you touch that isn't being worn or carried by another creature bursts into flame.",
    "You regain your lowest-level expended spell slot.",
    "For the next minute, you must shout when you speak.",
    "You cast Fog Cloud centered on yourself.",
    "Up to three creatures you choose within 30 feet of you take 4d10 lightning damage.",
    "You are frightened by the nearest creature until the end of your next turn.",
    "Each creature within 30 feet of you becomes invisible for the next minute.",
    "You gain 4d10 temporary hit points.",
    "You manifest an aura of shimmering, multicolored light radiating 5 feet from you. Each creature that ends its turn within the aura must succeed on a CON save or be blinded until the end of its next turn.",
    "You teleport up to 60 feet to an unoccupied space of your choice that you can see.",
    "An ethereal copy of you appears and mimics your actions for 1 minute, then disappears.",
    "You are surrounded by faint, ethereal music for the next minute.",
    "You regain all expended sorcery points.",
    "Maximize the damage of the next damaging spell you cast within the next minute.",
    "Roll a d10. Your age changes by a number of years equal to the roll; if odd, you age; if even, you grow younger (min 1).",
    "1d6 flumphs controlled by the DM appear in unoccupied spaces within 60 feet of you and are frightened of you. They vanish after 1 minute.",
    "You regain 2d10 hit points.",
    "You turn into a potted plant until the start of your next turn. While a plant, you are incapacitated and have vulnerability to all damage. If you drop to 0 HP, your pot breaks and your form reverts.",
    "For the next minute, you can teleport up to 20 feet as a bonus action on each of your turns.",
    "You cast Levitate on yourself.",
    "A unicorn controlled by the DM appears within 5 feet of you. It departs after 1 minute.",
    "You can't speak for the next minute. Whenever you try, yellow butterflies fly from your mouth.",
    "A teleportation circle appears that lasts for 1 minute. Any creature can step through it and appears anywhere you specify.",
    "You and all creatures within 30 feet of you gain vulnerability to piercing damage for the next minute.",
]


# ── Dungeon Dressing (d60, one entry per roll) ────────────────────────────────

# Flavor details for rooms and corridors to make exploration feel textured
# without requiring the DM to improvise every small detail.

DUNGEON_DRESSING = [
    "Dusty tapestries depicting a war between gods no one remembers.",
    "A broken table with a half-eaten meal, long since rotted.",
    "Scorch marks on the floor in the outline of a humanoid shape.",
    "Iron shackles bolted to the wall — one set is torn free.",
    "A child's shoe in the corner, muddy and old.",
    "Words scratched into the stone: 'DO NOT OPEN THE THIRD DOOR'.",
    "A cracked mirror reflecting a room that doesn't look quite like this one.",
    "Dozens of candles burned down to stubs, wax pooled across the floor.",
    "A pile of bones sorted by size — someone was meticulous.",
    "A trapdoor, nailed shut from this side with fresh nails.",
    "Water dripping from the ceiling into a perfectly placed bowl.",
    "A crude map drawn in charcoal on the wall — it's of this dungeon, but slightly wrong.",
    "An open book, pages slowly turning in a breeze with no source.",
    "A row of hooks on the wall, one of which holds a single glove.",
    "Bloodstains trailing to a wall and stopping — no door, no crack.",
    "A mounted animal head whose glass eyes follow movement in the room.",
    "A smashed arcane apparatus, still faintly humming.",
    "A child's drawing pinned to the wall by a dagger.",
    "Coins scattered across the floor — all face down.",
    "A locked chest sitting in the open, key in the lock, unlocked.",
    "A broom propped in the corner, as if someone set it down a moment ago.",
    "A lantern on a long chain, swinging slowly despite the still air.",
    "Names and tally marks scratched into the lower half of the wall, as if made from a seated position.",
    "A half-finished mural on one wall — the artist stopped mid-stroke.",
    "A prayer rug, perfectly clean, kneeling-worn, facing the wrong direction.",
    "Dozens of arrows embedded in the west wall at different heights and angles.",
    "A brass incense holder, the ash cone still intact, undisturbed.",
    "A wall cabinet of small labelled drawers, all empty, each label in a different handwriting.",
    "A painting covered by a cloth — whatever is beneath has worn through the fabric in one spot.",
    "A child's height markings penciled on a door frame, stopping at roughly four feet.",
    "A ring of salt on the floor, large enough for a person to stand in, unbroken.",
    "A rope hanging from the ceiling with the end cut clean — someone took it down deliberately.",
    "A smashed hourglass, sand mixed with what might be powdered bone.",
    "A small metal cage on a hook, door open, nothing inside.",
    "A throne carved directly from the stone, too large for any humanoid.",
    "A long crack in the floor running perfectly straight from wall to wall — too clean to be natural.",
    "A doorway bricked up from this side, with 'DON'T' scratched above the lintel.",
    "Two chairs facing each other with a simple board game laid out between them, mid-play.",
    "A calendar on the wall, dates crossed off with increasing frequency, then stopped.",
    "A dozen dried herbs hanging from the ceiling in neat bundles — all of them poisonous, all correctly labeled.",
    "An ornate bathtub full of water that has never once been still.",
    "Finger-painted murals of stick figures fighting something with no recognisable limbs.",
    "A shrine to an unnamed god: a bowl of old blood, wire flowers, two carved wooden eyes.",
    "A long hallway of identical doors, all open, all leading to identical empty rooms.",
    "A bed with the blankets turned down as if waiting for someone, pillow indented.",
    "Hundreds of candle stubs arranged on the floor into a shape — a word? a map? hard to tell.",
    "A lectern with an open book, all pages blank, a quill still wet with ink.",
    "A sigil burned into every door frame — the same one, exactly the same size and position each time.",
    "The remnants of a meal set for three. Two chairs knocked back. One still neatly tucked in.",
    "A grate in the floor leaking warm air and a sound like very distant chanting.",
    "A wine rack full of bottles, each labeled with a name — none of them wine.",
    "A skeleton seated at a writing desk, one hand still raised as if asking a question.",
    "Claw marks on the inside of a locked door.",
    "An enormous mirror, face-down on the floor, too heavy for one person to move.",
    "A stone channel along the wall, long dry, that once carried something other than water.",
    "The only clean floor in the entire dungeon — and no footprints anywhere near it.",
    "Manacles at ten-foot intervals along one wall: one pair open, one closed, one closed with the occupant still inside.",
    "A fresco of a great battle where every figure on the losing side has been chipped away.",
    "A wooden box on a high shelf, just out of reach, with 'EVIDENCE' burned into the lid.",
    "A drain in the centre of the floor, too large for drainage — something could climb through it.",
]


# ── Renderers ─────────────────────────────────────────────────────────────────

def render_wild_magic(key_prefix, nested=False):
    """Render the Wild Magic Surge roll button + full-table viewer.

    `key_prefix` namespaces the widget keys so this can appear on multiple
    pages (Spells, Combat) without key collisions.

    `nested=True` swaps the "Show full table" expander for a toggle —
    Streamlit forbids expanders inside expanders, so callers that place this
    inside their own expander (Combat) must pass nested=True.
    """
    # 50 entries → paired ranges 01–02, 03–04 … 99–100; roll a d100
    _wm_max = len(WILD_MAGIC) * 2  # 100

    if st.button("Roll Wild Magic Surge", key=f"{key_prefix}_wm_roll"):
        roll   = random.randint(1, _wm_max)
        idx    = (roll - 1) // 2          # map d100 roll → paired table entry
        result = WILD_MAGIC[idx]
        lo     = idx * 2 + 1
        hi     = idx * 2 + 2
        st.success(f"**Roll: {roll:03d} ({lo:02d}–{hi:02d})** — {result}")

    def _table_rows():
        """Emit the 50 paired-range table rows."""
        for i, entry in enumerate(WILD_MAGIC):
            lo = i * 2 + 1
            hi = i * 2 + 2
            st.markdown(f"**{lo:02d}–{hi:02d}** — {entry}")

    # Full table: toggle when nested inside a caller's expander, expander otherwise
    if nested:
        if st.toggle("Show full table", key=f"{key_prefix}_wm_table"):
            _table_rows()
    else:
        with st.expander("Show full table"):
            _table_rows()


def render_dungeon_dressing(key_prefix):
    """Render the Dungeon Dressing roll button + full-table expander.

    `key_prefix` namespaces the button key for reuse across pages.
    """
    st.caption("Flavor details for rooms and corridors — roll to add texture without prep.")
    if st.button("Roll Dungeon Detail", key=f"{key_prefix}_dd_roll"):
        roll   = random.randint(1, len(DUNGEON_DRESSING))
        result = DUNGEON_DRESSING[roll - 1]
        st.info(f"**Roll {roll:02d}:** {result}")

    with st.expander("Show full table"):
        for idx, entry in enumerate(DUNGEON_DRESSING, 1):
            st.markdown(f"**{idx:02d}.** {entry}")
