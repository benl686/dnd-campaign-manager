import copy
import math
import random
import uuid
import streamlit as st
from utils import load_json, load_json_cached, save_json, CONDITION_DATA, sidebar_exit_button, confirm_delete
from random_tables import render_wild_magic
from pathlib import Path


CHARS_PATH = Path("json/characters.json")

# ── Constants ─────────────────────────────────────────────────────────────────

CONDITIONS = [
    "Blinded", "Charmed", "Deafened", "Exhausted", "Frightened",
    "Grappled", "Incapacitated", "Invisible", "Paralyzed", "Petrified",
    "Poisoned", "Prone", "Restrained", "Stunned", "Unconscious",
]

DURATION_UNITS = ["Rounds", "Seconds", "Minutes", "Hours", "Indefinite"]

# Classes that use the standard spell slot progression
FULL_CASTERS = {"Bard", "Cleric", "Druid", "Sorcerer", "Wizard"}
# Half-casters contribute floor(level/2) to the combined caster level
HALF_CASTERS = {"Artificer", "Paladin", "Ranger"}

# Full-caster spell slot table — rows are caster levels 1-30,
# columns are spell levels 1-9 (index 0 = 1st level slots, etc.)
# Levels 21-30 (epic tier) retain L20 slots; the 9th-level progression peaks
# at standard L20 and epic boons grant features rather than more spell slots.
SPELL_SLOT_TABLE = {
    1:  [2, 0, 0, 0, 0, 0, 0, 0, 0],
    2:  [3, 0, 0, 0, 0, 0, 0, 0, 0],
    3:  [4, 2, 0, 0, 0, 0, 0, 0, 0],
    4:  [4, 3, 0, 0, 0, 0, 0, 0, 0],
    5:  [4, 3, 2, 0, 0, 0, 0, 0, 0],
    6:  [4, 3, 3, 0, 0, 0, 0, 0, 0],
    7:  [4, 3, 3, 1, 0, 0, 0, 0, 0],
    8:  [4, 3, 3, 2, 0, 0, 0, 0, 0],
    9:  [4, 3, 3, 3, 1, 0, 0, 0, 0],
    10: [4, 3, 3, 3, 2, 0, 0, 0, 0],
    11: [4, 3, 3, 3, 2, 1, 0, 0, 0],
    12: [4, 3, 3, 3, 2, 1, 0, 0, 0],
    13: [4, 3, 3, 3, 2, 1, 1, 0, 0],
    14: [4, 3, 3, 3, 2, 1, 1, 0, 0],
    15: [4, 3, 3, 3, 2, 1, 1, 1, 0],
    16: [4, 3, 3, 3, 2, 1, 1, 1, 0],
    17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
    19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
    20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    # ── Epic tier: slots unchanged from L20 per standard 5e epic rules ────────
    21: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    22: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    23: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    24: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    25: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    26: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    27: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    28: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    29: [4, 3, 3, 3, 3, 2, 2, 1, 1],
    30: [4, 3, 3, 3, 3, 2, 2, 1, 1],
}

# Warlock pact magic: {warlock_level: (slot_count, slot_level)}
# Levels 21-30 retain L20 pact magic (4 slots at 5th level).
WARLOCK_PACT_MAGIC = {
    1:  (1, 1),  2:  (2, 1),  3:  (2, 2),  4:  (2, 2),
    5:  (2, 3),  6:  (2, 3),  7:  (2, 4),  8:  (2, 4),
    9:  (2, 5),  10: (2, 5),  11: (3, 5),  12: (3, 5),
    13: (3, 5),  14: (3, 5),  15: (3, 5),  16: (3, 5),
    17: (4, 5),  18: (4, 5),  19: (4, 5),  20: (4, 5),
    # ── Epic tier ─────────────────────────────────────────────────────────────
    21: (4, 5),  22: (4, 5),  23: (4, 5),  24: (4, 5),  25: (4, 5),
    26: (4, 5),  27: (4, 5),  28: (4, 5),  29: (4, 5),  30: (4, 5),
}

# Healing item name substrings → (num_dice, die_size, flat_bonus)
# Checked in order so "greater" matches before "healing" alone.
HEALING_ITEM_DICE: list[tuple[str, int, int, int]] = [
    ("supreme healing",  10, 4, 20),
    ("superior healing",  8, 4,  8),
    ("greater healing",   4, 4,  4),
    ("healing",           2, 4,  2),
]


# ── Duration helpers ───────────────────────────────────────────────────────────

def to_rounds(value, unit):
    """Convert a duration value + unit to an internal round count.

    Returns -1 for Indefinite (never auto-expires). 1 round = 6 seconds.
    """
    if unit == "Indefinite":
        return -1
    value = max(1, int(value))
    if unit == "Rounds":   return value
    if unit == "Seconds":  return max(1, math.ceil(value / 6))
    if unit == "Minutes":  return value * 10
    if unit == "Hours":    return value * 600
    return -1


def fmt_remaining(remaining):
    """Short label: '∞' for indefinite, '3r' for finite round counts."""
    return "∞" if remaining < 0 else f"{remaining}r"


def tick_conditions(combatants):
    """Decrement round-based condition durations at end of a full round.

    Conditions at 1 round expire; indefinite (-1) are untouched.
    """
    for c in combatants:
        kept = []
        for cond in c.get("conditions", []):
            r = cond.get("remaining", -1)
            if r < 0:
                kept.append(cond)
            elif r > 1:
                kept.append({**cond, "remaining": r - 1})
            # r == 1 → expired, drop it
        c["conditions"] = kept
    return combatants


# ── Spell slot helpers ─────────────────────────────────────────────────────────

def get_spell_slots(classes: list[dict]) -> tuple[list[int], tuple | None]:
    """Return (regular_slots[9], warlock_pact) for the given classes list.

    regular_slots: list of 9 ints (max available per spell level 1-9).
    warlock_pact:  (slot_count, slot_level) or None.
    Uses PHB multiclassing rules: full casters add full level, half casters add
    floor(level/2). Warlock pact magic is kept separate.
    """
    caster_lvl  = 0
    warlock_lvl = 0
    for entry in classes:
        cls = entry.get("class", "")
        lvl = entry.get("level", 0)
        if cls in FULL_CASTERS:
            caster_lvl += lvl
        elif cls in HALF_CASTERS:
            caster_lvl += lvl // 2
        elif cls == "Warlock":
            warlock_lvl += lvl

    # Tables run 1–30; clamp only to handle theoretical edge cases above 30
    regular = list(SPELL_SLOT_TABLE.get(min(caster_lvl, 30), [0] * 9)) if caster_lvl > 0 else [0] * 9
    warlock = WARLOCK_PACT_MAGIC.get(min(warlock_lvl, 30)) if warlock_lvl > 0 else None
    return regular, warlock


# ── Item helpers ───────────────────────────────────────────────────────────────

def healing_roll(item_name: str) -> int | None:
    """Return HP healed for a recognised healing potion, or None."""
    name_lower = item_name.lower()
    for substring, nd, ds, fb in HEALING_ITEM_DICE:
        if substring in name_lower:
            return sum(random.randint(1, ds) for _ in range(nd)) + fb
    return None


# ── Session state ─────────────────────────────────────────────────────────────

if "combatants" not in st.session_state:
    st.session_state.combatants = []
if "current_turn" not in st.session_state:
    st.session_state.current_turn = 0
if "round_num" not in st.session_state:
    st.session_state.round_num = 1

# Load character data — mtime-cached so disk read is skipped when file unchanged.
chars = load_json_cached(CHARS_PATH, [])


# ── Page header ───────────────────────────────────────────────────────────────

st.title("Combat / Initiative Tracker")

top_cols = st.columns([3, 2, 2, 2])
top_cols[0].metric("Round", st.session_state.round_num)

if st.session_state.combatants:
    if top_cols[1].button("Next Turn ▶"):
        st.session_state["_combat_snapshot"] = {
            "combatants":   copy.deepcopy(st.session_state.combatants),
            "current_turn": st.session_state.current_turn,
            "round_num":    st.session_state.round_num,
        }
        st.session_state.current_turn += 1
        if st.session_state.current_turn >= len(st.session_state.combatants):
            st.session_state.current_turn = 0
            st.session_state.round_num += 1
            st.session_state.combatants = tick_conditions(st.session_state.combatants)
        st.rerun()

if "_combat_snapshot" in st.session_state:
    if top_cols[2].button("↩ Undo"):
        snap = st.session_state.pop("_combat_snapshot")
        st.session_state.combatants   = snap["combatants"]
        st.session_state.current_turn = snap["current_turn"]
        st.session_state.round_num    = snap["round_num"]
        st.rerun()

if "reset_combat_pending" not in st.session_state:
    st.session_state.reset_combat_pending = False

if not st.session_state.reset_combat_pending:
    if top_cols[3].button("Reset Combat"):
        st.session_state.reset_combat_pending = True
        st.rerun()
else:
    if top_cols[3].button("Confirm Reset?", type="primary"):
        st.session_state.combatants   = []
        st.session_state.current_turn = 0
        st.session_state.round_num    = 1
        st.session_state.pop("_combat_snapshot", None)
        st.session_state.reset_combat_pending = False
        st.rerun()

st.markdown("---")


# ── Wild Magic Surge ──────────────────────────────────────────────────────────
# Quick-access d100 roll for sorcerer surges mid-combat. Table data + renderer
# live in random_tables.py (shared with the Spells page's Wild Magic tab).

with st.expander("🎲 Wild Magic Surge"):
    render_wild_magic("combat", nested=True)


# ── Add combatant ─────────────────────────────────────────────────────────────

with st.expander("Add Combatant", expanded=not bool(st.session_state.combatants)):
    char_names    = ["— Manual entry —"] + [c["name"] for c in chars]
    selected_char = st.selectbox("Import from characters", char_names, key="combat_char_select")

    with st.form("add_combatant"):
        if selected_char != "— Manual entry —":
            char_data    = next((c for c in chars if c["name"] == selected_char), {})
            default_name = char_data.get("name", "")
            default_hp   = char_data.get("max_hp", char_data.get("hp", 10))
            default_tmp  = char_data.get("temp_hp", 0)
            default_ac   = char_data.get("ac", 10)
            dex_mod      = (char_data.get("dex", 10) - 10) // 2
        else:
            char_data    = {}
            default_name, default_hp, default_tmp, default_ac, dex_mod = "", 10, 0, 10, 0

        fc1, fc2, fc3, fc4 = st.columns(4)
        new_name  = fc1.text_input("Name", value=default_name)
        new_hp    = fc2.number_input("Max HP", min_value=1, value=default_hp)
        new_ac    = fc3.number_input("AC", min_value=1, value=default_ac)
        init_mode = fc4.radio("Initiative", ["Roll d20", "Set manually"], horizontal=True)
        new_init  = fc4.number_input("Initiative modifier / value", value=dex_mod, key="init_val")

        if st.form_submit_button("Add to Combat"):
            if new_name.strip():
                roll = random.randint(1, 20) + int(new_init) if init_mode == "Roll d20" else int(new_init)
                # Pull class list from imported character for spell slot calculations
                imp_classes = char_data.get("classes", [])
                if not imp_classes and char_data.get("char_class"):
                    imp_classes = [{"class": char_data["char_class"], "level": char_data.get("level", 1)}]
                combatant = {
                    "name":               new_name.strip(),
                    "max_hp":             int(new_hp),
                    "current_hp":         int(new_hp),
                    "temp_hp":            int(default_tmp),
                    "ac":                 int(new_ac),
                    "initiative":         roll,
                    "conditions":         [],
                    # Character link — None for monsters / manual entries
                    "char_name":          selected_char if selected_char != "— Manual entry —" else None,
                    "char_classes":       imp_classes,
                    # Spell slots: track how many of each level have been used this combat
                    "spell_slots_used":   [0] * 9,
                    "warlock_slots_used": 0,
                    # Stable per-combatant id — the roster is re-sorted by initiative
                    # after every add/edit below, which changes each combatant's list
                    # index. All per-combatant widget keys are keyed on "_cid" (not
                    # the loop index) so a reorder can never attach one combatant's
                    # pending input / open panel to a different combatant that shifts
                    # into its old index.
                    "_cid":               uuid.uuid4().hex[:8],
                }
                st.session_state.combatants.append(combatant)
                st.session_state.combatants.sort(key=lambda x: x["initiative"], reverse=True)
                st.session_state.current_turn = min(
                    st.session_state.current_turn, len(st.session_state.combatants) - 1
                )
                st.rerun()
            else:
                st.error("Name is required")

st.markdown("---")


# ── Condition reference ────────────────────────────────────────────────────────

with st.expander("📖 Condition Reference"):
    ref_cond = st.selectbox("Condition", list(CONDITION_DATA.keys()), key="cond_ref_select")
    if ref_cond in CONDITION_DATA:
        st.markdown(CONDITION_DATA[ref_cond]["desc"])
        st.caption(f"**Ends:** {CONDITION_DATA[ref_cond]['ends']}")

st.markdown("---")


# ── Combatant list ────────────────────────────────────────────────────────────

if not st.session_state.combatants:
    st.info("No combatants yet. Add some using the form above.")
else:
    for i, c in enumerate(st.session_state.combatants):
        # setdefault so combatants added before this fix (still in a live session's
        # state) get an id on first render instead of raising/behaving oddly.
        cid = c.setdefault("_cid", uuid.uuid4().hex[:8])
        is_active = i == st.session_state.current_turn
        temp_hp   = c.get("temp_hp", 0)
        hp_pct    = max(0, c["current_hp"] / c["max_hp"]) if c["max_hp"] > 0 else 0

        # Build condition summary for expander label
        cond_parts = []
        for cd in c.get("conditions", []):
            tag = f"{cd['name']} ({fmt_remaining(cd['remaining'])})"
            if cd.get("concentration"):
                tag += " 🎯"
            cond_parts.append(tag)
        cond_summary = ", ".join(cond_parts)

        hp_label = f"HP {c['current_hp']}/{c['max_hp']}"
        if temp_hp > 0:
            hp_label += f" +{temp_hp}tmp"

        label = (
            f"{'▶ ' if is_active else '   '}**{c['name']}**"
            f"  —  Init {c['initiative']}  |  AC {c['ac']}  |  {hp_label}"
            + (f"  |  {cond_summary}" if cond_summary else "")
        )

        with st.expander(label, expanded=is_active):

            # ── Edit-in-place ──────────────────────────────────────────────────
            edit_flag = f"combat_edit_{cid}"
            if edit_flag not in st.session_state:
                st.session_state[edit_flag] = False

            btn_row = st.columns([2, 2, 5])
            if btn_row[0].button("✕ Cancel Edit" if st.session_state[edit_flag] else "✏ Edit",
                                  key=f"edit_toggle_{cid}"):
                st.session_state[edit_flag] = not st.session_state[edit_flag]
                st.rerun()

            # Sync button — only shown for character-linked combatants
            if c.get("char_name"):
                linked = next((ch for ch in chars if ch["name"] == c["char_name"]), None)
                if linked and btn_row[1].button("↻ Sync Sheet", key=f"sync_sheet_{cid}",
                                                 help="Update AC and Max HP from the character sheet"):
                    st.session_state.combatants[i]["ac"]      = linked.get("ac", c["ac"])
                    st.session_state.combatants[i]["max_hp"]  = linked.get("max_hp", c["max_hp"])
                    # Cap current HP at new max if max decreased
                    st.session_state.combatants[i]["current_hp"] = min(
                        c["current_hp"], st.session_state.combatants[i]["max_hp"]
                    )
                    st.success(f"Synced {c['char_name']}: AC {linked.get('ac')} / Max HP {linked.get('max_hp')}")
                    st.rerun()

            if st.session_state[edit_flag]:
                ec1, ec2, ec3, ec4, ec5 = st.columns(5)
                edit_name   = ec1.text_input("Name",       value=c["name"],        key=f"edit_name_{cid}")
                edit_ac     = ec2.number_input("AC",        min_value=1, value=c["ac"],        key=f"edit_ac_{cid}")
                edit_max_hp = ec3.number_input("Max HP",    min_value=1, value=c["max_hp"],     key=f"edit_maxhp_{cid}")
                edit_tmp    = ec4.number_input("Temp HP",   min_value=0, value=temp_hp,         key=f"edit_tmp_{cid}")
                edit_init   = ec5.number_input("Initiative",              value=c["initiative"], key=f"edit_init_{cid}")
                if st.button("💾 Save edits", key=f"edit_save_{cid}"):
                    new_max = int(edit_max_hp)
                    st.session_state.combatants[i].update({
                        "name":       edit_name.strip() or c["name"],
                        "ac":         int(edit_ac),
                        "max_hp":     new_max,
                        "current_hp": min(c["current_hp"], new_max),
                        "temp_hp":    max(0, int(edit_tmp)),
                        "initiative": int(edit_init),
                    })
                    st.session_state.combatants.sort(key=lambda x: x["initiative"], reverse=True)
                    st.session_state[edit_flag] = False
                    st.rerun()
                st.markdown("---")

            # ── Main action panel ──────────────────────────────────────────────
            cc1, cc2, cc3, cc4 = st.columns([3, 1, 1, 1])

            # ── Conditions ────────────────────────────────────────────────────
            with cc1:
                st.markdown("**Conditions**")

                for ci, cond in enumerate(c.get("conditions", [])):
                    r_label  = fmt_remaining(cond["remaining"])
                    conc_tag = " 🎯 Conc." if cond.get("concentration") else ""
                    row = st.columns([4, 1])
                    row[0].markdown(f"**{cond['name']}**{conc_tag} — {r_label} remaining")
                    if row[1].button("✕", key=f"rm_cond_{cid}_{ci}"):
                        st.session_state.combatants[i]["conditions"].pop(ci)
                        st.rerun()

                # Add-condition form: plain widgets (no st.form) so that changing
                # the condition selectbox immediately updates the description below it.
                new_cond = st.selectbox("Condition", CONDITIONS, key=f"cond_name_{cid}")
                if new_cond in CONDITION_DATA:
                    # Show full description — no truncation
                    st.caption(CONDITION_DATA[new_cond]["desc"])
                    st.caption(f"**Ends:** {CONDITION_DATA[new_cond]['ends']}")
                ac2, ac3, ac4 = st.columns([1, 1.5, 1])
                dur_val  = ac2.number_input("Duration", min_value=1, value=1,
                                             key=f"dur_val_{cid}")
                dur_unit = ac3.selectbox("Unit", DURATION_UNITS, key=f"dur_unit_{cid}")
                ac3.caption("1 round = 6 sec | 1 min = 10 rounds")
                is_conc  = ac4.checkbox("Concentration", key=f"is_conc_{cid}")

                if st.button("+ Add Condition", key=f"add_cond_btn_{cid}"):
                    remaining = to_rounds(
                        st.session_state.get(f"dur_val_{cid}", 1),
                        st.session_state.get(f"dur_unit_{cid}", "Rounds"),
                    )
                    if st.session_state.get(f"is_conc_{cid}", False):
                        # Drop existing concentration condition before adding the new one
                        st.session_state.combatants[i]["conditions"] = [
                            cd for cd in st.session_state.combatants[i]["conditions"]
                            if not cd.get("concentration")
                        ]
                    st.session_state.combatants[i]["conditions"].append({
                        "name":          st.session_state.get(f"cond_name_{cid}", CONDITIONS[0]),
                        "remaining":     remaining,
                        "concentration": st.session_state.get(f"is_conc_{cid}", False),
                    })
                    st.rerun()

            # ── Damage (absorbs temp HP first) ────────────────────────────────
            with cc2:
                dmg = st.number_input("Damage", min_value=0, value=0, step=1, key=f"dmg_{cid}")
                if st.button("Apply Damage", key=f"apply_dmg_{cid}"):
                    dmg_val  = max(0, int(dmg))
                    cur_tmp  = st.session_state.combatants[i].get("temp_hp", 0)
                    absorbed = min(cur_tmp, dmg_val)       # temp HP soaks first
                    net_dmg  = dmg_val - absorbed           # remainder hits regular HP

                    # Record HP before update so the progress bar can animate from old → new
                    old_hp = c["current_hp"]

                    st.session_state.combatants[i]["temp_hp"]    = cur_tmp - absorbed
                    st.session_state.combatants[i]["current_hp"] = max(0, c["current_hp"] - net_dmg)

                    if absorbed:
                        st.session_state[f"_tmp_absorbed_{cid}"] = absorbed
                    else:
                        st.session_state.pop(f"_tmp_absorbed_{cid}", None)

                    # Flag HP bar to animate red flash on the next render (damage > 0 only)
                    if net_dmg > 0:
                        max_hp = max(1, c["max_hp"])
                        st.session_state[f"_hp_anim_{cid}"] = {
                            "from": old_hp / max_hp,
                            "to":   st.session_state.combatants[i]["current_hp"] / max_hp,
                        }

                    # Concentration check reminder
                    conc_conds = [cd for cd in c.get("conditions", []) if cd.get("concentration")]
                    if conc_conds and dmg_val > 0:
                        dc = max(10, dmg_val // 2)
                        st.session_state[f"_conc_warn_{cid}"] = (c["name"], conc_conds[0]["name"], dc)
                    else:
                        st.session_state.pop(f"_conc_warn_{cid}", None)
                    st.rerun()

                if f"_tmp_absorbed_{cid}" in st.session_state:
                    st.caption(f"🛡 {st.session_state[f'_tmp_absorbed_{cid}']} absorbed by Temp HP")
                if f"_conc_warn_{cid}" in st.session_state:
                    cw_name, cw_cond, cw_dc = st.session_state[f"_conc_warn_{cid}"]
                    st.warning(f"⚡ {cw_name} concentrating ({cw_cond}) — CON save DC {cw_dc}!")

            # ── Heal + Set Temp HP ────────────────────────────────────────────
            with cc3:
                heal = st.number_input("Heal", min_value=0, value=0, step=1, key=f"heal_{cid}")
                if st.button("Apply Heal", key=f"apply_heal_{cid}"):
                    st.session_state.combatants[i]["current_hp"] = min(
                        c["max_hp"], c["current_hp"] + int(heal)
                    )
                    st.rerun()

                st.markdown("")  # spacer
                tmp_set = st.number_input("Set Temp HP", min_value=0, value=temp_hp,
                                           step=1, key=f"tmp_set_{cid}")
                if st.button("Set", key=f"set_tmp_{cid}", help="Temp HP replaces — doesn't stack"):
                    # PHB rule: temp HP doesn't stack; keep the higher value
                    st.session_state.combatants[i]["temp_hp"] = max(temp_hp, int(tmp_set))
                    st.rerun()

            # ── Remove ────────────────────────────────────────────────────────
            with cc4:
                if confirm_delete(st, f"combat_delete_{cid}", f"combat_{cid}", label="Remove"):
                    st.session_state.combatants.pop(i)
                    st.session_state.current_turn = min(
                        st.session_state.current_turn,
                        max(0, len(st.session_state.combatants) - 1)
                    )
                    st.rerun()

            # ── HP progress bar ───────────────────────────────────────────────
            tmp_disp = f" (+{temp_hp} temp)" if temp_hp > 0 else ""

            # Pop the damage-animation flag — if set, the bar was just hit this render.
            # The CSS animation plays from old HP (red) → new HP (blue) in one shot.
            # On the next render the flag is gone, so the normal st.progress bar shows.
            hp_anim = st.session_state.pop(f"_hp_anim_{cid}", None)

            if hp_anim:
                fp   = min(100.0, max(0.0, hp_anim["from"] * 100))  # old HP %
                tp   = min(100.0, max(0.0, hp_anim["to"]   * 100))  # new HP %
                cur  = c["current_hp"]
                mx   = c["max_hp"]
                # Duration scales slightly with the size of the hit so a 1-HP scratch
                # feels snappier than a big chunk of HP disappearing.
                delta   = max(0.0, fp - tp)
                dur_ms  = int(300 + delta * 5)   # 300ms base + 5ms per %-point lost
                st.html(f"""
<style>
@keyframes hp-dmg-{cid} {{
  0%   {{ width:{fp:.1f}%; background:#c0392b; }}
  70%  {{ background:#c0392b; }}
  100% {{ width:{tp:.1f}%; background:#4e8cff; }}
}}
.hp-wrap-{cid}{{background:#ddd;border-radius:4px;height:8px;overflow:hidden;margin:4px 0 2px;}}
.hp-fill-{cid}{{
  height:100%;
  border-radius:4px;
  width:{tp:.1f}%;
  background:#4e8cff;
  animation:hp-dmg-{cid} {dur_ms}ms ease-out forwards;
}}
</style>
<div class="hp-wrap-{cid}"><div class="hp-fill-{cid}"></div></div>
<p style="font-size:12px;color:#888;margin:0">HP: {cur}/{mx}{tmp_disp}</p>
""")
            else:
                st.progress(hp_pct, text=f"HP: {c['current_hp']}/{c['max_hp']}{tmp_disp}")

            # ── Resources (spell slots + items) — character combatants only ───
            if c.get("char_name") and c.get("char_classes"):
                with st.expander("📦 Resources"):
                    res_tab_spells, res_tab_items = st.tabs(["🔮 Spell Slots", "🎒 Items"])

                    # ── Spell slots ───────────────────────────────────────────
                    with res_tab_spells:
                        regular_slots, warlock_pact = get_spell_slots(c["char_classes"])
                        used = c.get("spell_slots_used", [0] * 9)
                        # Pad to 9 in case of legacy data
                        while len(used) < 9: used.append(0)

                        has_any = any(s > 0 for s in regular_slots) or warlock_pact

                        if not has_any:
                            st.caption("No spell slots — this class doesn't cast spells.")
                        else:
                            if any(s > 0 for s in regular_slots):
                                st.markdown("**Regular slots**")
                                for lvl_idx, total in enumerate(regular_slots):
                                    if total == 0:
                                        continue
                                    remaining_slots = max(0, total - used[lvl_idx])
                                    sc1, sc2, sc3, sc4 = st.columns([1.5, 3, 1, 1])
                                    sc1.markdown(f"**Lv {lvl_idx + 1}**")
                                    # Visual pip display: ● = available, ○ = used
                                    pips = "●" * remaining_slots + "○" * (total - remaining_slots)
                                    sc2.markdown(f"{pips}  {remaining_slots}/{total}")
                                    if sc3.button("Use", key=f"use_slot_{cid}_{lvl_idx}",
                                                   disabled=remaining_slots == 0):
                                        st.session_state.combatants[i]["spell_slots_used"][lvl_idx] = (
                                            used[lvl_idx] + 1
                                        )
                                        st.rerun()
                                    if sc4.button("↩", key=f"rec_slot_{cid}_{lvl_idx}",
                                                   disabled=used[lvl_idx] == 0,
                                                   help="Recover one slot"):
                                        st.session_state.combatants[i]["spell_slots_used"][lvl_idx] = (
                                            used[lvl_idx] - 1
                                        )
                                        st.rerun()

                            if warlock_pact:
                                st.markdown("**Pact Magic (Warlock)**")
                                wk_total, wk_lvl = warlock_pact
                                wk_used      = c.get("warlock_slots_used", 0)
                                wk_remaining = max(0, wk_total - wk_used)
                                wc1, wc2, wc3, wc4, wc5 = st.columns([1.5, 2, 1, 1, 2])
                                wc1.markdown(f"**Lv {wk_lvl}**")
                                wc2.markdown(f"{'●'*wk_remaining}{'○'*(wk_total-wk_remaining)}  {wk_remaining}/{wk_total}")
                                if wc3.button("Use", key=f"use_wk_{cid}", disabled=wk_remaining == 0):
                                    st.session_state.combatants[i]["warlock_slots_used"] = wk_used + 1
                                    st.rerun()
                                if wc4.button("↩", key=f"rec_wk_{cid}", disabled=wk_used == 0,
                                               help="Recover one pact slot"):
                                    st.session_state.combatants[i]["warlock_slots_used"] = wk_used - 1
                                    st.rerun()
                                if wc5.button("Short Rest", key=f"sr_wk_{cid}",
                                               help="Recover all pact magic slots"):
                                    st.session_state.combatants[i]["warlock_slots_used"] = 0
                                    st.rerun()

                            if st.button("Long Rest — recover all slots", key=f"lr_{cid}"):
                                st.session_state.combatants[i]["spell_slots_used"]   = [0] * 9
                                st.session_state.combatants[i]["warlock_slots_used"] = 0
                                st.rerun()

                    # ── Items ─────────────────────────────────────────────────
                    with res_tab_items:
                        # Re-load character from saved data for current inventory
                        linked_char = next((ch for ch in chars if ch["name"] == c["char_name"]), None)
                        inventory   = linked_char.get("inventory", []) if linked_char else []
                        usable      = [(ii, it) for ii, it in enumerate(inventory)
                                       if it.get("qty", 0) > 0]

                        if not usable:
                            st.caption("No items with quantity > 0 in inventory.")
                        else:
                            ih1, ih2, ih3 = st.columns([4, 1, 2])
                            ih1.markdown("**Item**")
                            ih2.markdown("**Qty**")
                            ih3.markdown("")
                            for ii, item in usable:
                                ic1, ic2, ic3 = st.columns([4, 1, 2])
                                ic1.write(item["name"])
                                ic2.write(str(item.get("qty", 0)))
                                if ic3.button("Use", key=f"use_item_{cid}_{ii}"):
                                    hp_gained = healing_roll(item["name"])
                                    # Decrement inventory qty and persist to characters.json
                                    for ch_rec in chars:
                                        if ch_rec["name"] == c["char_name"]:
                                            ch_rec["inventory"][ii]["qty"] = max(0, item["qty"] - 1)
                                            break
                                    save_json(CHARS_PATH, chars)
                                    # Apply healing if it's a healing item
                                    if hp_gained is not None:
                                        new_hp = min(
                                            st.session_state.combatants[i]["max_hp"],
                                            st.session_state.combatants[i]["current_hp"] + hp_gained,
                                        )
                                        st.session_state.combatants[i]["current_hp"] = new_hp
                                        st.session_state[f"_item_msg_{cid}"] = (
                                            f"Used **{item['name']}** — healed **+{hp_gained} HP**."
                                        )
                                    else:
                                        st.session_state[f"_item_msg_{cid}"] = (
                                            f"Used **{item['name']}**."
                                        )
                                    st.rerun()

                        if f"_item_msg_{cid}" in st.session_state:
                            st.success(st.session_state.pop(f"_item_msg_{cid}"))

