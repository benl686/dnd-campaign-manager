import math
import random
import streamlit as st
from utils import load_json, load_json_cached, save_json, sidebar_exit_button, confirm_delete
from character_lib import (
    ability_mod, proficiency_bonus, get_classes, classes_label,
    SKILL_ABILITY, ABILITIES, SKILLS, CHAR_CLASSES, CLASS_SAVE_PROFS,
    STAT_BOOST_ITEMS, CLASS_HIT_DICE, EQUIP_STATS, MULTICLASS_REQS,
    STANDARD_ARRAY, POINT_BUY_COSTS, POINT_BUY_BUDGET,
)
from pathlib import Path


DATA_PATH       = Path("json/characters.json")
ITEMS_SRD_PATH  = Path("data/items_srd.json")
MAGICITEMS_PATH = Path("data/magicitems.json")
SPELLS_SRD_PATH = Path("data/spells_srd.json")


# ── Cached reference-data builders ────────────────────────────────────────────
# Build and sort large reference lists once per file-mtime instead of on every
# rerender. Changing either mtime key (when files update) busts the cache.

@st.cache_data(show_spinner=False)
def _ref_item_list(items_mtime: float, magic_mtime: float) -> list:
    """Sorted (name, category) pairs combining SRD equipment and magic items."""
    items = [(it["name"], it.get("category", "Equipment"))
             for it in load_json(str(ITEMS_SRD_PATH), [])]
    magic = [(it["name"], it.get("category", "Magic Item"))
             for it in load_json(str(MAGICITEMS_PATH), [])]
    combined = items + magic
    combined.sort(key=lambda x: x[0])
    return combined


@st.cache_data(show_spinner=False)
def _ref_spell_list(mtime: float) -> list:
    """5e-edition spells sorted by level then name for the spell-add dropdown."""
    raw = load_json(str(SPELLS_SRD_PATH), [])
    filtered = [s for s in raw if s.get("gamesystem_key") in ("5e-2014", "5e-2024")]
    filtered.sort(key=lambda s: (s.get("level", 0), s.get("name", "")))
    return filtered


st.title("Character Creator")
st.caption("Data is saved to 'json/characters.json' in your app folder; it always loads and saves automatically.")

if "characters" not in st.session_state:
    st.session_state.characters = load_json(DATA_PATH, [])

_STALE_PREFIXES = ("char_delete_pending_", "mc_count_", "lu_pending_", "inv_del_pending_")
for key in list(st.session_state.keys()):
    if any(key.startswith(p) for p in _STALE_PREFIXES):
        try:
            idx = int(key.split("_")[-1])
            if idx >= len(st.session_state.characters):
                del st.session_state[key]
        except (ValueError, IndexError):
            pass

st.subheader("Add New Character")

# Version counter: incrementing resets all create-form widget keys (clears the form after creation)
if "create_form_v" not in st.session_state:
    st.session_state.create_form_v = 0
_cfv = st.session_state.create_form_v  # snapshot once per render

# st.container(border=True) draws a native bordered box — no HTML div hack needed.
# No st.form either — plain widgets so class changes trigger live reruns,
# enabling save-throw auto-populate and live modifier display.
with st.container(border=True):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        name = st.text_input("Name", key=f"new_name_{_cfv}")
    with col2:
        class_sel = st.selectbox("Class", CHAR_CLASSES, key=f"new_class_sel_{_cfv}")
    with col3:
        level = st.number_input("Level", min_value=1, max_value=None, value=1, step=1, key=f"new_level_{_cfv}")

    # Custom class row — only rendered when "Other (custom)" is selected
    if class_sel == "Other (custom)":
        class_custom = st.text_input(
            "Custom class name",
            placeholder="e.g. Blood Hunter, Mystic, Pugilist — leave blank to use selection above",
            key=f"class_custom_new_{_cfv}",
        )
        char_class = class_custom.strip() or ""
    else:
        char_class = class_sel

    cc1, cc2, cc3, cc4, cc5 = st.columns(5)
    with cc1:
        max_hp = st.number_input("Max HP", min_value=1, value=10, step=1, key=f"new_max_hp_{_cfv}")
    with cc2:
        current_hp = st.number_input("Current HP", min_value=1, value=10, step=1, key=f"new_current_hp_{_cfv}")
    with cc3:
        temp_hp = st.number_input("Temp HP", min_value=0, value=0, step=1, key=f"new_temp_hp_{_cfv}")
    with cc4:
        ac = st.number_input("AC", min_value=1, value=10, step=1, key=f"new_ac_{_cfv}")
    with cc5:
        initiative = st.number_input("Initiative", min_value=-10, value=0, step=1, key=f"new_initiative_{_cfv}")

    # ── Ability score method selector ────────────────────────────────────────
    stat_method = st.radio(
        "Ability score method",
        ["Standard Array", "Point Buy", "Manual / Roll"],
        horizontal=True,
        key=f"stat_method_{_cfv}",
        help=(
            "**Standard Array**: Assign 15, 14, 13, 12, 10, 8 across abilities.  "
            "**Point Buy**: Spend 27 points (scores 8–15).  "
            "**Manual / Roll**: Type values freely or roll 4d6 drop-lowest."
        ),
    )

    _ab_cols = st.columns(6)
    _ab_default_order = [15, 14, 13, 12, 10, 8]  # default assignment STR→CHA

    if stat_method == "Standard Array":
        # Each ability gets a selectbox picking from the six array values.
        # Defaults follow the classic assignment order (STR=15, DEX=14, …).
        _arr_vals = {}
        for col, ab, default in zip(_ab_cols, ABILITIES, _ab_default_order):
            with col:
                _arr_vals[ab] = st.selectbox(
                    ab, STANDARD_ARRAY,
                    index=STANDARD_ARRAY.index(default),
                    key=f"new_arr_{ab}_{_cfv}",
                )
        # Live duplicate warning so user spots conflicts immediately
        _used_vals = list(_arr_vals.values())
        _dupes = sorted({v for v in _used_vals if _used_vals.count(v) > 1})
        if _dupes:
            st.warning(f"Each array value must be used exactly once. Duplicated: {_dupes}")
        str_ = _arr_vals["STR"]; dex = _arr_vals["DEX"]; con = _arr_vals["CON"]
        int_ = _arr_vals["INT"]; wis = _arr_vals["WIS"]; cha = _arr_vals["CHA"]

    elif stat_method == "Point Buy":
        # Scores 8–15, 27-point budget. Costs follow the DMG table.
        _pb_vals = {}
        for col, ab in zip(_ab_cols, ABILITIES):
            with col:
                _pb_vals[ab] = st.number_input(
                    ab, min_value=8, max_value=15, value=8, step=1,
                    key=f"new_pb_{ab}_{_cfv}",
                )
        _spent     = sum(POINT_BUY_COSTS.get(v, 0) for v in _pb_vals.values())
        _remaining = POINT_BUY_BUDGET - _spent
        if _remaining >= 0:
            st.caption(
                f"Points spent: **{_spent}** / {POINT_BUY_BUDGET}  •  "
                f"Remaining: **{_remaining}**"
            )
        else:
            st.warning(
                f"Over budget by **{-_remaining}** points "
                f"({_spent} / {POINT_BUY_BUDGET} used)."
            )
        str_ = _pb_vals["STR"]; dex = _pb_vals["DEX"]; con = _pb_vals["CON"]
        int_ = _pb_vals["INT"]; wis = _pb_vals["WIS"]; cha = _pb_vals["CHA"]

    else:  # Manual / Roll
        # "Roll all" button pre-fills widget keys before the number_inputs render,
        # so the rolled values appear immediately and remain editable.
        if st.button("🎲 Roll all (4d6 drop lowest)", key=f"roll_stats_{_cfv}"):
            for ab in ABILITIES:
                _rolls = [random.randint(1, 6) for _ in range(4)]
                # Drop the lowest of four dice — standard 5e roll method
                st.session_state[f"new_manual_{ab}_{_cfv}"] = sum(sorted(_rolls)[1:])
        _manual_vals = {}
        for col, ab, default in zip(_ab_cols, ABILITIES, _ab_default_order):
            with col:
                _manual_vals[ab] = st.number_input(
                    ab, min_value=1, value=default, step=1,
                    key=f"new_manual_{ab}_{_cfv}",
                )
        str_ = _manual_vals["STR"]; dex = _manual_vals["DEX"]; con = _manual_vals["CON"]
        int_ = _manual_vals["INT"]; wis = _manual_vals["WIS"]; cha = _manual_vals["CHA"]

    # Compute live modifiers and PB so bonuses update instantly as stats/class change
    _new_scores = {"STR": int(str_), "DEX": int(dex), "CON": int(con),
                   "INT": int(int_), "WIS": int(wis), "CHA": int(cha)}
    _new_mods = {ab: ability_mod(s) for ab, s in _new_scores.items()}
    _new_pb   = proficiency_bonus(int(level))

    st.markdown("#### Saving Throws")
    st.caption("One box = Proficiency. Two boxes = Expertise. Auto-checked from class — override freely.")
    save_prof, save_xprt = {}, {}
    rows = st.columns(6)
    for idx, ab in enumerate(ABILITIES):
        with rows[idx]:
            label_col, c1, c2 = st.columns([1.4, 0.5, 0.5])
            with label_col:
                # Pre-read live checkbox state so the displayed bonus is accurate before the widgets render
                _def_p  = ab in CLASS_SAVE_PROFS.get(class_sel, set())
                _cur_p  = st.session_state.get(f"save_prof_{ab}_{class_sel}_{_cfv}", _def_p)
                _cur_x  = st.session_state.get(f"save_xprt_{ab}_{_cfv}", False)
                _bonus  = _new_mods[ab] + _new_pb * (int(_cur_p) + int(_cur_x))
                st.markdown(f"**{ab}** {'+' if _bonus>=0 else ''}{_bonus}")
            with c1:
                # Key includes class so checkboxes reset with class defaults on every class change
                save_prof[ab] = st.checkbox("Proficient", value=_def_p,
                                             key=f"save_prof_{ab}_{class_sel}_{_cfv}",
                                             label_visibility="collapsed")
            with c2:
                save_xprt[ab] = st.checkbox("Expert", key=f"save_xprt_{ab}_{_cfv}",
                                             label_visibility="collapsed")

    st.markdown("#### Skills")
    st.caption("One box = Proficiency. Two boxes = Expertise.")
    skill_prof, skill_xprt = {}, {}
    skillcols = st.columns(3)
    for _si, skill in enumerate(SKILLS):
        ab = SKILL_ABILITY[skill]
        with skillcols[_si % 3]:
            label_col, c1, c2 = st.columns([2, 0.5, 0.5])
            with label_col:
                _cur_sp = st.session_state.get(f"skill_prof_{skill}_{_cfv}", False)
                _cur_sx = st.session_state.get(f"skill_xprt_{skill}_{_cfv}", False)
                _b = _new_mods[ab] + _new_pb * (int(_cur_sp) + int(_cur_sx))
                st.markdown(f"{skill} {'+' if _b>=0 else ''}{_b}")
            with c1:
                skill_prof[skill] = st.checkbox("Proficient", key=f"skill_prof_{skill}_{_cfv}",
                                                label_visibility="collapsed")
            with c2:
                skill_xprt[skill] = st.checkbox("Expert", key=f"skill_xprt_{skill}_{_cfv}",
                                                label_visibility="collapsed")

    # Show deferred success message from the previous creation (survives the rerun)
    if st.session_state.get("_char_created_msg"):
        st.success(st.session_state.pop("_char_created_msg"))

    if st.button("Create character", type="primary", key=f"create_btn_{_cfv}"):
        # Validate stat method before saving
        _stat_err = None
        _cur_method = st.session_state.get(f"stat_method_{_cfv}", "Manual / Roll")
        if _cur_method == "Standard Array":
            _used = [int(str_), int(dex), int(con), int(int_), int(wis), int(cha)]
            if sorted(_used) != sorted(STANDARD_ARRAY):
                _stat_err = "Each standard array value (15, 14, 13, 12, 10, 8) must appear exactly once."
        elif _cur_method == "Point Buy":
            _spent_final = sum(POINT_BUY_COSTS.get(v, 0) for v in
                               [int(str_), int(dex), int(con), int(int_), int(wis), int(cha)])
            if _spent_final > POINT_BUY_BUDGET:
                _stat_err = f"Point buy is over budget ({_spent_final}/{POINT_BUY_BUDGET} points)."

        if _stat_err:
            st.error(_stat_err)
        elif name.strip():
            new_char = {
                "name": name.strip(), "char_class": char_class.strip(), "level": int(level),
                "max_hp": int(max_hp), "current_hp": int(current_hp), "temp_hp": int(temp_hp),
                "ac": int(ac), "initiative": int(initiative),
                "str": int(str_), "dex": int(dex), "con": int(con),
                "int": int(int_), "wis": int(wis), "cha": int(cha),
                "save_prof": save_prof, "save_xprt": save_xprt,
                "skill_prof": skill_prof, "skill_xprt": skill_xprt,
            }
            st.session_state.characters.append(new_char)
            save_json(DATA_PATH, st.session_state.characters)
            # Store message in session_state before rerun so it survives the render reset
            st.session_state._char_created_msg = f"Created {name.strip()}"
            # Bump version → all form widget keys change → form shows blank on next render
            st.session_state.create_form_v += 1
            st.rerun()
        else:
            st.error("Name is required")

st.divider()
st.subheader("Your characters")
if not st.session_state.characters:
    st.info("No characters yet. Add one using the form above.")
else:
    for i, ch in enumerate(st.session_state.characters):
        _ch_classes = get_classes(ch)
        with st.expander(f"{ch['name']} ({classes_label(_ch_classes)})"):

            # ── Quick HP / Temp HP (auto-saves on change, no Save button) ──────
            # Lets the player update HP mid-session without opening the full edit form.
            # Uses on_change to persist immediately and pops the edit-form widget keys
            # so they reinitialise from the freshly-saved values on next render.
            def _save_quick_hp(idx: int):
                st.session_state.characters[idx]["current_hp"] = st.session_state[f"qs_cur_hp_{idx}"]
                st.session_state.characters[idx]["temp_hp"]    = st.session_state[f"qs_tmp_hp_{idx}"]
                save_json(DATA_PATH, st.session_state.characters)
                # Let the edit-form widgets re-read from the updated character record
                st.session_state.pop(f"current_hp_{idx}", None)
                st.session_state.pop(f"temp_hp_{idx}",    None)

            qh1, qh2, qh3 = st.columns(3)
            with qh1:
                st.number_input(
                    "Current HP", min_value=0,
                    value=ch.get("current_hp", 1), step=1,
                    key=f"qs_cur_hp_{i}",
                    on_change=_save_quick_hp, args=(i,),
                )
            with qh2:
                # Max HP shown read-only here; editable in the edit form below
                st.number_input("Max HP", value=ch.get("max_hp", 1), disabled=True)
            with qh3:
                st.number_input(
                    "Temp HP", min_value=0,
                    value=ch.get("temp_hp", 0), step=1,
                    key=f"qs_tmp_hp_{i}",
                    on_change=_save_quick_hp, args=(i,),
                )
            st.caption("Quick HP — saves instantly. Edit form below for all other stats.")

            new_name = st.text_input("Name", value=ch["name"], key=f"name_{i}")

            # ── Multiclass editor ──────────────────────────────────────────────
            # mc_count tracks how many class rows are shown in this edit session
            mc_count_key  = f"mc_count_{i}"
            saved_classes = get_classes(ch)
            if mc_count_key not in st.session_state:
                st.session_state[mc_count_key] = len(saved_classes)
            mc_count  = st.session_state[mc_count_key]
            new_classes = []

            mch1, mch2 = st.columns([5, 1.5])
            mch1.markdown("**Classes**")
            if mch2.button("+ Add class", key=f"mc_add_{i}", width='stretch'):
                st.session_state[mc_count_key] += 1
                st.rerun()

            for ci in range(mc_count):
                default_cls = saved_classes[ci]["class"] if ci < len(saved_classes) else "Fighter"
                default_lvl = saved_classes[ci]["level"] if ci < len(saved_classes) else 1
                mc1, mc2, mc3 = st.columns([4, 1, 0.5], vertical_alignment="bottom")
                cls_name = mc1.text_input(
                    "Class", value=default_cls,
                    key=f"mc_cls_{i}_{ci}",
                    placeholder="e.g. Fighter, Wizard, Blood Hunter",
                    label_visibility="visible" if ci == 0 else "collapsed",
                )
                cls_lvl = mc2.number_input(
                    "Levels", min_value=1, max_value=None, value=default_lvl, step=1,
                    key=f"mc_lvl_{i}_{ci}",
                    label_visibility="visible" if ci == 0 else "collapsed",
                )
                if mc_count > 1:
                    if mc3.button("✕", key=f"mc_rem_{i}_{ci}"):
                        # Shift subsequent widget values down so indices stay contiguous
                        for k in range(ci, mc_count - 1):
                            st.session_state[f"mc_cls_{i}_{k}"] = st.session_state.get(f"mc_cls_{i}_{k+1}", "Fighter")
                            st.session_state[f"mc_lvl_{i}_{k}"] = st.session_state.get(f"mc_lvl_{i}_{k+1}", 1)
                        # Pop the now-unused last slot's keys. Without this they
                        # linger in session_state and get silently reused (showing
                        # the just-deleted class's stale name/level instead of the
                        # "Fighter"/1 default) if "+ Add class" is clicked again and
                        # a new row re-occupies this same index.
                        st.session_state.pop(f"mc_cls_{i}_{mc_count - 1}", None)
                        st.session_state.pop(f"mc_lvl_{i}_{mc_count - 1}", None)
                        st.session_state[mc_count_key] -= 1
                        st.rerun()
                else:
                    pass  # single-class: mc3 stays empty
                new_classes.append({"class": cls_name.strip() or default_cls, "level": int(cls_lvl)})

            # Total level = sum of all class levels
            new_level = sum(c["level"] for c in new_classes)
            # Primary class drives saving-throw auto-populate in the Saves tab
            new_class = new_classes[0]["class"] if new_classes else ""
            if len(new_classes) > 1:
                st.caption(f"Total level: {new_level}")
            ec1, ec2, ec3, ec4, ec5 = st.columns(5)
            with ec1:
                new_max_hp = st.number_input("Max HP", 1, None, ch.get("max_hp", ch.get("hp", 1)), 1, key=f"max_hp_{i}")
            with ec2:
                new_current_hp = st.number_input("Current HP", 1, None, ch.get("current_hp", 1), 1, key=f"current_hp_{i}")
            with ec3:
                new_temp_hp = st.number_input("Temp HP", 0, None, ch.get("temp_hp", 0), 1, key=f"temp_hp_{i}")
            with ec4:
                new_ac = st.number_input("AC", 1, None, ch["ac"], 1, key=f"ac_{i}")
            with ec5:
                new_init = st.number_input("Initiative", -10, None, ch["initiative"], 1, key=f"init_{i}")
            es1, es2, es3, es4, es5, es6 = st.columns(6)
            with es1:
                new_str = st.number_input("STR", 1, None, ch["str"], 1, key=f"str_{i}")
            with es2:
                new_dex = st.number_input("DEX", 1, None, ch["dex"], 1, key=f"dex_{i}")
            with es3:
                new_con = st.number_input("CON", 1, None, ch["con"], 1, key=f"con_{i}")
            with es4:
                new_int = st.number_input("INT", 1, None, ch["int"], 1, key=f"int_{i}")
            with es5:
                new_wis = st.number_input("WIS", 1, None, ch["wis"], 1, key=f"wis_{i}")
            with es6:
                new_cha = st.number_input("CHA", 1, None, ch["cha"], 1, key=f"cha_{i}")

            # ── Effective stat calculation (base scores + item/book bonuses + equip bonuses) ──
            # Load inventory early so equipped item bonuses flow into the stat display
            inventory = ch.get("inventory", [])

            # Pre-read live checkbox states so the stat display reacts immediately on equip toggle,
            # without waiting for the widget to persist back to session_state (same pattern as saves/skills).
            _live_eq = [
                st.session_state.get(f"inv_eq_{i}_{ii}", entry.get("equipped", False))
                for ii, entry in enumerate(inventory)
            ]

            # Sum ability and AC/initiative bonuses from currently equipped items
            _eq_ac   = sum(it.get("equip_bonuses", {}).get("AC", 0)         for ii, it in enumerate(inventory) if _live_eq[ii])
            _eq_init = sum(it.get("equip_bonuses", {}).get("Initiative", 0)  for ii, it in enumerate(inventory) if _live_eq[ii])
            _eq_ab   = {ab: sum(it.get("equip_bonuses", {}).get(ab, 0) for ii, it in enumerate(inventory) if _live_eq[ii]) for ab in ABILITIES}

            bonuses      = ch.get("stat_bonuses", [])
            bonus_totals = {ab: sum(b["amount"] for b in bonuses if b["ability"] == ab) for ab in ABILITIES}
            eff_scores   = {
                "STR": int(new_str) + bonus_totals["STR"] + _eq_ab["STR"],
                "DEX": int(new_dex) + bonus_totals["DEX"] + _eq_ab["DEX"],
                "CON": int(new_con) + bonus_totals["CON"] + _eq_ab["CON"],
                "INT": int(new_int) + bonus_totals["INT"] + _eq_ab["INT"],
                "WIS": int(new_wis) + bonus_totals["WIS"] + _eq_ab["WIS"],
                "CHA": int(new_cha) + bonus_totals["CHA"] + _eq_ab["CHA"],
            }
            emods    = {ab: ability_mod(s) for ab, s in zip(ABILITIES,
                        [int(new_str), int(new_dex), int(new_con), int(new_int), int(new_wis), int(new_cha)])}
            eff_mods = {ab: ability_mod(eff_scores[ab]) for ab in ABILITIES}

            # Base modifier row — always shown
            em1, em2, em3, em4, em5, em6 = st.columns(6)
            with em1: st.caption(f"STR base [ {emods['STR']:+d} ]")
            with em2: st.caption(f"DEX base [ {emods['DEX']:+d} ]")
            with em3: st.caption(f"CON base [ {emods['CON']:+d} ]")
            with em4: st.caption(f"INT base [ {emods['INT']:+d} ]")
            with em5: st.caption(f"WIS base [ {emods['WIS']:+d} ]")
            with em6: st.caption(f"CHA base [ {emods['CHA']:+d} ]")

            # Effective row — shown when stat_bonuses or equipped ability bonuses are active
            if any(v != 0 for v in bonus_totals.values()) or any(v != 0 for v in _eq_ab.values()):
                ef1, ef2, ef3, ef4, ef5, ef6 = st.columns(6)
                with ef1: st.caption(f"STR eff. {eff_scores['STR']} [ {eff_mods['STR']:+d} ]")
                with ef2: st.caption(f"DEX eff. {eff_scores['DEX']} [ {eff_mods['DEX']:+d} ]")
                with ef3: st.caption(f"CON eff. {eff_scores['CON']} [ {eff_mods['CON']:+d} ]")
                with ef4: st.caption(f"INT eff. {eff_scores['INT']} [ {eff_mods['INT']:+d} ]")
                with ef5: st.caption(f"WIS eff. {eff_scores['WIS']} [ {eff_mods['WIS']:+d} ]")
                with ef6: st.caption(f"CHA eff. {eff_scores['CHA']} [ {eff_mods['CHA']:+d} ]")

            # Equipped-item AC / initiative effects (not in ABILITIES, so shown separately)
            _eq_line = []
            if _eq_ac   != 0: _eq_line.append(f"AC → {int(new_ac) + _eq_ac} ({_eq_ac:+d})")
            if _eq_init != 0: _eq_line.append(f"Initiative → {int(new_init) + _eq_init} ({_eq_init:+d})")
            if _eq_line:
                st.caption("Equipped item effects: " + " | ".join(_eq_line))

            epb = proficiency_bonus(int(new_level))

            # ── LEVEL UP ─────────────────────────────────────────────────────
            lu_key = f"lu_pending_{i}"
            if lu_key not in st.session_state:
                st.session_state[lu_key] = False

            pb_c, lu_c = st.columns([5, 1.5])
            pb_c.caption(f"Proficiency bonus (PB): +{epb}")
            if lu_c.button("⬆ Level Up", key=f"lu_btn_{i}", width='stretch'):
                st.session_state[lu_key] = True
                st.session_state.pop(f"lu_roll_{i}", None)
                st.rerun()

            if st.session_state[lu_key]:
                lu_saved_level   = ch.get("level", 1)
                lu_saved_classes = get_classes(ch)
                con_mod_lu = ability_mod(ch.get("con", 10))

                with st.container(border=True):
                    st.markdown(f"**Level {lu_saved_level} → {lu_saved_level + 1}**")

                    # Which class gets this level?
                    cls_options   = [c["class"] for c in lu_saved_classes] + ["➕ Add new class"]
                    lu_cls_choice = st.selectbox(
                        "Level up which class?", cls_options, key=f"lu_cls_{i}",
                    )
                    is_new_cls = (lu_cls_choice == "➕ Add new class")

                    if is_new_cls:
                        # Selectbox mirrors the create form's class list; "Other (custom)" falls through to text input
                        lu_new_cls_sel = st.selectbox(
                            "New class", CHAR_CLASSES, key=f"lu_new_cls_sel_{i}",
                        )
                        if lu_new_cls_sel == "Other (custom)":
                            lu_new_cls_name = st.text_input(
                                "Custom class name", key=f"lu_new_cls_txt_{i}",
                                placeholder="e.g. Blood Hunter, Mystic, Pugilist",
                            ).strip()
                        else:
                            lu_new_cls_name = lu_new_cls_sel
                        hit_die = CLASS_HIT_DICE.get(lu_new_cls_name)
                        if lu_new_cls_name and hit_die is None:
                            st.caption("Custom/unknown class — choose hit die.")
                            hit_die = st.select_slider(
                                "Hit die", options=[4, 6, 8, 10, 12],
                                value=8, key=f"lu_die_{i}",
                            )
                        # Empty name → hit_die stays None, can_apply stays False
                    else:
                        lu_new_cls_name = ""
                        hit_die = CLASS_HIT_DICE.get(lu_cls_choice)
                        if hit_die is None:
                            st.caption("Custom class — choose hit die.")
                            hit_die = st.select_slider(
                                "Hit die", options=[4, 6, 8, 10, 12],
                                value=8, key=f"lu_die_{i}",
                            )

                    if hit_die is not None:
                        st.caption(f"Hit die: d{hit_die}  |  CON modifier: {con_mod_lu:+d}(CON)")
                        hp_method = st.radio(
                            "HP gain method",
                            ["Standard (average)", "Roll for HP"],
                            horizontal=True, key=f"lu_method_{i}",
                        )
                        if hp_method == "Standard (average)":
                            # D&D 5e average = floor(die/2)+1 + CON mod; minimum 1
                            final_hp_gain = max(1, (hit_die // 2 + 1) + con_mod_lu)
                            can_apply     = True
                            st.info(f"HP gain: **+{final_hp_gain}** (average d{hit_die} {con_mod_lu:+d}(CON))")
                        else:
                            roll_key = f"lu_roll_{i}"
                            if st.button("🎲 Roll!", key=f"lu_roll_btn_{i}"):
                                st.session_state[roll_key] = random.randint(1, hit_die)
                            rolled = st.session_state.get(roll_key)
                            if rolled is not None:
                                final_hp_gain = max(1, rolled + con_mod_lu)
                                can_apply     = True
                                st.info(f"Rolled **{rolled}** on d{hit_die} {con_mod_lu:+d}(CON) = **+{final_hp_gain} HP**")
                            else:
                                final_hp_gain = 0
                                can_apply     = False
                                st.caption("Click Roll! to determine your HP gain.")
                    else:
                        final_hp_gain = 0
                        can_apply     = False

                    # ── Multiclass prerequisite check (new class only) ────────
                    # Existing classes are exempt — you can level a class you
                    # already have regardless of your current ability scores.
                    if is_new_cls and lu_new_cls_name and can_apply:
                        # Permanent bonuses (tomes, etc.) count; equip bonuses don't.
                        _prereq_scores = {
                            "STR": int(new_str) + bonus_totals["STR"],
                            "DEX": int(new_dex) + bonus_totals["DEX"],
                            "CON": int(new_con) + bonus_totals["CON"],
                            "INT": int(new_int) + bonus_totals["INT"],
                            "WIS": int(new_wis) + bonus_totals["WIS"],
                            "CHA": int(new_cha) + bonus_totals["CHA"],
                        }
                        _req = MULTICLASS_REQS.get(lu_new_cls_name)
                        if _req:
                            _req_fn, _req_text = _req
                            if not _req_fn(_prereq_scores):
                                st.error(
                                    f"**{lu_new_cls_name}** requires **{_req_text}** "
                                    f"to multiclass into."
                                )
                                can_apply = False

                    ap_c, cn_c = st.columns(2)
                    if ap_c.button("Apply Level Up", key=f"lu_apply_{i}",
                                    type="primary", disabled=not can_apply,
                                    width='stretch'):
                        updated_cls  = [dict(c) for c in lu_saved_classes]
                        primary_cls  = updated_cls[0]["class"]  # for save-prof widget keys
                        saves_note   = ""

                        if is_new_cls:
                            updated_cls.append({"class": lu_new_cls_name, "level": 1})

                            # Auto-grant saving throw proficiencies the new class adds that the
                            # character doesn't already have.  Widget keys are cleared via the
                            # deferred sync dict so they pick up the updated value next render.
                            new_saves     = CLASS_SAVE_PROFS.get(lu_new_cls_name, set())
                            current_profs = st.session_state.characters[i].get("save_prof", {})
                            gained_saves  = [ab for ab in new_saves if not current_profs.get(ab, False)]
                            if gained_saves:
                                for ab in gained_saves:
                                    st.session_state.characters[i].setdefault("save_prof", {})[ab] = True
                                saves_note = f" Gained {', '.join(gained_saves)} saving throw proficiency."

                            desc = f"Added {lu_new_cls_name} (new multiclass). Max HP +{final_hp_gain}.{saves_note}"
                        else:
                            target_k = next(k for k, c in enumerate(updated_cls) if c["class"] == lu_cls_choice)
                            updated_cls[target_k]["level"] += 1
                            desc = f"{lu_cls_choice} to level {updated_cls[target_k]['level']}. Max HP +{final_hp_gain}."

                        new_total_lvl = sum(c["level"] for c in updated_cls)
                        saved_max_hp  = ch.get("max_hp", ch.get("hp", 1))
                        new_max_hp    = saved_max_hp + final_hp_gain

                        st.session_state.characters[i]["classes"]    = updated_cls
                        st.session_state.characters[i]["level"]      = new_total_lvl
                        st.session_state.characters[i]["char_class"] = primary_cls
                        st.session_state.characters[i]["max_hp"]     = new_max_hp

                        # Pop widget keys so they reinitialise from ch data on next render.
                        # Popping is always safe; setting after instantiation raises
                        # StreamlitAPIException.  The widgets will read from value= which
                        # references ch (already updated above) on the next rerun.
                        st.session_state.pop(f"max_hp_{i}", None)
                        for k in range(len(updated_cls)):
                            st.session_state.pop(f"mc_cls_{i}_{k}", None)
                            st.session_state.pop(f"mc_lvl_{i}_{k}", None)
                        for ab in (gained_saves if is_new_cls else []):
                            st.session_state.pop(f"esavep_{ab}_{i}_{primary_cls}", None)
                        st.session_state[mc_count_key] = len(updated_cls)  # plain key, safe to set

                        st.session_state.characters[i].setdefault("advancement_log", []).append({
                            "level": new_total_lvl, "event_type": "Level Up",
                            "description": desc, "notes": "",
                        })
                        save_json(DATA_PATH, st.session_state.characters)
                        st.session_state[lu_key] = False
                        st.session_state.pop(f"lu_roll_{i}", None)
                        st.rerun()

                    if cn_c.button("Cancel", key=f"lu_cancel_{i}", width='stretch'):
                        st.session_state[lu_key] = False
                        st.session_state.pop(f"lu_roll_{i}", None)
                        st.rerun()

            # ── Tabs: Saves/Skills | Stat Bonuses | Inventory | Spells | Log ────
            tab_saves, tab_bonuses, tab_inventory, tab_spells, tab_log = st.tabs([
                "Saves & Skills", "Stat Bonuses", "Inventory", "Spells", "Log",
            ])

            # ── SAVES & SKILLS TAB ────────────────────────────────────────────
            with tab_saves:
                # When class changes, default saves to the new class's proficiencies;
                # otherwise use the player's saved values so manual tweaks are preserved.
                class_changed = new_class != ch.get("char_class", "")
                sp_defaults = {
                    ab: (ab in CLASS_SAVE_PROFS.get(new_class, set())) if class_changed
                        else ch.get("save_prof", {}).get(ab, False)
                    for ab in ABILITIES
                }
                sx_defaults = {
                    ab: False if class_changed else ch.get("save_xprt", {}).get(ab, False)
                    for ab in ABILITIES
                }

                # Pre-read live checkbox values from session_state so bonus labels are accurate
                # immediately after a click — without waiting for Save.
                # Key format: esavep_{ab}_{char_idx}_{class}  (resets cleanly on class change)
                e_save_prof = {
                    ab: st.session_state.get(f"esavep_{ab}_{i}_{new_class}", sp_defaults[ab])
                    for ab in ABILITIES
                }
                e_save_xprt = {
                    ab: st.session_state.get(f"esavex_{ab}_{i}_{new_class}", sx_defaults[ab])
                    for ab in ABILITIES
                }

                st.markdown("#### Saving Throws")
                st.caption("One box = Proficiency. Two boxes = Expertise. Auto-populated from class — override freely.")
                row1 = st.columns(3)
                row2 = st.columns(3)
                rows = row1 + row2
                for idx, ab in enumerate(ABILITIES):
                    with rows[idx]:
                        label_col, c1, c2 = st.columns([1.4, 0.5, 0.5])
                        with label_col:
                            # Uses pre-read live values — updates on every checkbox click
                            bonus = eff_mods[ab] + epb * (int(e_save_prof[ab]) + int(e_save_xprt[ab]))
                            st.markdown(f"{ab} Save: {'+' if bonus>=0 else ''}{bonus}")
                        with c1:
                            e_save_prof[ab] = st.checkbox("Proficient", value=sp_defaults[ab],
                                                           key=f"esavep_{ab}_{i}_{new_class}",
                                                           label_visibility="collapsed")
                        with c2:
                            e_save_xprt[ab] = st.checkbox("Expert", value=sx_defaults[ab],
                                                           key=f"esavex_{ab}_{i}_{new_class}",
                                                           label_visibility="collapsed")

                # Pre-read live skill values from session_state for up-to-date bonus display
                sk_defaults  = {sk: ch.get("skill_prof", {}).get(sk, False) for sk in SKILLS}
                skx_defaults = {sk: ch.get("skill_xprt", {}).get(sk, False) for sk in SKILLS}
                e_skill_prof = {sk: st.session_state.get(f"eskp_{sk}_{i}", sk_defaults[sk])  for sk in SKILLS}
                e_skill_xprt = {sk: st.session_state.get(f"eskx_{sk}_{i}", skx_defaults[sk]) for sk in SKILLS}

                st.markdown("#### Skills")
                st.caption("One box = Proficiency. Two boxes = Expertise.")
                scols = st.columns(3)
                for j, skill in enumerate(SKILLS):
                    ab = SKILL_ABILITY[skill]
                    with scols[j % 3]:
                        label_col, c1, c2 = st.columns([2, 0.5, 0.5])
                        with label_col:
                            b = eff_mods[ab] + epb * (int(e_skill_prof[skill]) + int(e_skill_xprt[skill]))
                            st.markdown(f"{skill}: {'+' if b>=0 else ''}{b}")
                        with c1:
                            e_skill_prof[skill] = st.checkbox("Proficient", value=sk_defaults[skill],
                                                               key=f"eskp_{skill}_{i}",
                                                               label_visibility="collapsed")
                        with c2:
                            e_skill_xprt[skill] = st.checkbox("Expert", value=skx_defaults[skill],
                                                               key=f"eskx_{skill}_{i}",
                                                               label_visibility="collapsed")

            # ── STAT BONUSES TAB ──────────────────────────────────────────────
            with tab_bonuses:
                st.caption(
                    "Track permanent bonuses to ability scores from magic items, tomes, "
                    "and similar sources. Base scores above stay unchanged — effective "
                    "scores are recalculated automatically."
                )

                # Table of existing bonuses with per-row delete
                if bonuses:
                    hc1, hc2, hc3, hc4 = st.columns([3, 1.5, 1, 0.6])
                    hc1.markdown("**Source**"); hc2.markdown("**Ability**")
                    hc3.markdown("**Amount**"); hc4.markdown("")
                    for bi, bonus in enumerate(bonuses):
                        bc1, bc2, bc3, bc4 = st.columns([3, 1.5, 1, 0.6])
                        bc1.write(bonus["source"])
                        bc2.write(bonus["ability"])
                        bc3.write(f"{bonus['amount']:+d}")
                        if bc4.button("✕", key=f"del_bonus_{i}_{bi}"):
                            st.session_state.characters[i]["stat_bonuses"].pop(bi)
                            save_json(DATA_PATH, st.session_state.characters)
                            st.rerun()
                else:
                    st.caption("No bonuses recorded yet.")

                st.markdown("**Add bonus**")
                # Source dropdown auto-fills ability and amount for known items.
                # Source-namespaced widget keys reset the fields when the item changes.
                src_options = list(STAT_BOOST_ITEMS.keys())
                bonus_src_sel = st.selectbox(
                    "Source item", src_options,
                    key=f"bsrc_{i}",
                    help="Select a known stat-boosting item or 'Custom' to type your own.",
                )
                # Custom source text field (only useful when "Custom" is selected)
                if bonus_src_sel == "Custom (enter below)":
                    bonus_src_custom = st.text_input(
                        "Custom source name", key=f"bsrc_txt_{i}",
                        placeholder="e.g. Story reward, house rule, 2024 rules item",
                    )
                    actual_bonus_src = bonus_src_custom.strip()
                    def_abil  = ABILITIES[0]
                    def_amt   = 2
                    is_set_item = False
                else:
                    actual_bonus_src = bonus_src_sel
                    _ab, _amt = STAT_BOOST_ITEMS[bonus_src_sel]
                    def_abil    = _ab if _ab else ABILITIES[0]
                    def_amt     = _amt if _amt is not None else 0
                    is_set_item = (_amt is None)

                bfc1, bfc2 = st.columns([1.5, 1])
                new_bonus_ability = bfc1.selectbox(
                    "Ability", ABILITIES,
                    index=ABILITIES.index(def_abil),
                    key=f"babil_{i}_{bonus_src_sel}",  # keyed to source so it resets on change
                )
                new_bonus_amount = bfc2.number_input(
                    "Amount", min_value=-30, max_value=30,
                    value=def_amt, step=1,
                    key=f"bamt_{i}_{bonus_src_sel}",
                )
                if st.button("Add", key=f"badd_{i}"):
                    if actual_bonus_src:
                        st.session_state.characters[i].setdefault("stat_bonuses", []).append({
                            "source":  actual_bonus_src,
                            "ability": new_bonus_ability,
                            "amount":  int(new_bonus_amount),
                        })
                        save_json(DATA_PATH, st.session_state.characters)
                        st.rerun()
                    else:
                        st.error("Enter a source name.")
                if is_set_item:
                    st.caption(
                        "This item sets your score to a fixed value, not a flat bonus. "
                        "Enter the difference: **target score − your current base score** "
                        "(e.g. for INT 12 with Headband of Intellect, enter 7)."
                    )

            # ── INVENTORY TAB ─────────────────────────────────────────────────
            with tab_inventory:
                # inventory is already loaded earlier for equip-bonus stat calculations

                # Sorted item list — built once per file-mtime, not on every rerender.
                _ref_items = _ref_item_list(
                    ITEMS_SRD_PATH.stat().st_mtime  if ITEMS_SRD_PATH.exists()  else 0,
                    MAGICITEMS_PATH.stat().st_mtime if MAGICITEMS_PATH.exists() else 0,
                )

                st.markdown("**Add from reference**")
                if _ref_items:
                    inv_search = st.text_input("Search items", key=f"inv_search_{i}",
                                               placeholder="e.g. sword, potion")
                    _filtered_ref = _ref_items
                    if inv_search.strip():
                        sl = inv_search.strip().lower()
                        _filtered_ref = [(n, c) for n, c in _ref_items if sl in n.lower()]
                    if _filtered_ref:
                        ia1, ia2, ia3 = st.columns([4, 1, 1])
                        item_choice = ia1.selectbox(
                            "Item", [f"{n}  ({c})" for n, c in _filtered_ref],
                            key=f"inv_choice_{i}",
                            label_visibility="collapsed",
                        )
                        inv_qty_ref = ia2.number_input("Qty", min_value=1, value=1, step=1,
                                                        key=f"inv_qty_ref_{i}",
                                                        label_visibility="collapsed")
                        if ia3.button("Add", key=f"inv_add_ref_{i}", width='stretch'):
                            item_name = item_choice.split("  (")[0]
                            st.session_state.characters[i].setdefault("inventory", []).append(
                                {"name": item_name, "qty": int(inv_qty_ref), "notes": "",
                                 "equipped": False, "equip_bonuses": {}}
                            )
                            save_json(DATA_PATH, st.session_state.characters)
                            st.rerun()
                    else:
                        st.caption("No items match that search.")
                else:
                    st.caption("Reference item data not found — use custom entry below.")

                st.markdown("**Add custom item**")
                ic1, ic2, ic3 = st.columns([4, 1, 1])
                inv_custom_name = ic1.text_input("Custom item name", key=f"inv_custom_{i}",
                                                  placeholder="e.g. Bag of Holding, 10ft pole",
                                                  label_visibility="collapsed")
                inv_custom_qty  = ic2.number_input("Qty", min_value=1, value=1, step=1,
                                                    key=f"inv_cqty_{i}",
                                                    label_visibility="collapsed")
                if ic3.button("Add", key=f"inv_add_custom_{i}", width='stretch'):
                    if inv_custom_name.strip():
                        st.session_state.characters[i].setdefault("inventory", []).append(
                            {"name": inv_custom_name.strip(), "qty": int(inv_custom_qty), "notes": "",
                             "equipped": False, "equip_bonuses": {}}
                        )
                        save_json(DATA_PATH, st.session_state.characters)
                        st.rerun()

                # Inventory list
                st.markdown("---")
                if inventory:
                    # Eq = equipped checkbox, ⚙ = toggle bonus editor
                    ih0, ih1, ih2, ih3, ih4, ih5 = st.columns([0.5, 3, 0.6, 2, 0.5, 0.5])
                    ih0.markdown("**Eq**"); ih1.markdown("**Item**"); ih2.markdown("**Qty**")
                    ih3.markdown("**Notes**"); ih4.markdown("**⚙**"); ih5.markdown("")

                    for ii, entry in enumerate(inventory):
                        edit_key = f"inv_edit_{i}_{ii}"

                        ic0, ic1, ic2, ic3, ic4, ic5 = st.columns([0.5, 3, 0.6, 2, 0.5, 0.5])

                        new_equipped = ic0.checkbox(
                            "Equipped", value=entry.get("equipped", False),
                            key=f"inv_eq_{i}_{ii}", label_visibility="collapsed",
                        )
                        # Bold name when equipped
                        ic1.markdown(f"**{entry['name']}**" if new_equipped else entry["name"])

                        new_qty = ic2.number_input(
                            "Quantity", min_value=0, value=int(entry.get("qty", 1)),
                            step=1, key=f"inv_qty_{i}_{ii}", label_visibility="collapsed",
                        )
                        new_notes = ic3.text_input(
                            "Notes", value=entry.get("notes", ""),
                            key=f"inv_notes_{i}_{ii}", label_visibility="collapsed",
                            placeholder="notes…",
                        )
                        # ⚙ opens the inline editor (rename + equip bonuses).
                        # ⚙✓ variant shows when at least one equip bonus is already configured.
                        cfg_lbl = "⚙✓" if entry.get("equip_bonuses") else "⚙"
                        if ic4.button(cfg_lbl, key=f"inv_cfg_{i}_{ii}"):
                            st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                            st.rerun()
                        # Two-step delete confirm
                        inv_del_key = f"inv_del_pending_{i}_{ii}"
                        if not st.session_state.get(inv_del_key):
                            if ic5.button("✕", key=f"inv_del_{i}_{ii}"):
                                st.session_state[inv_del_key] = True
                                st.rerun()
                        else:
                            if ic5.button("✓?", key=f"inv_del_conf_{i}_{ii}", help="Confirm delete"):
                                st.session_state.characters[i]["inventory"].pop(ii)
                                save_json(DATA_PATH, st.session_state.characters)
                                st.session_state[inv_del_key] = False
                                st.rerun()

                        # Persist inline edits (equipped, qty, notes) immediately
                        changed = (
                            new_equipped != entry.get("equipped", False) or
                            new_qty      != entry.get("qty", 1)          or
                            new_notes    != entry.get("notes", "")
                        )
                        if changed:
                            st.session_state.characters[i]["inventory"][ii]["equipped"] = new_equipped
                            st.session_state.characters[i]["inventory"][ii]["qty"]      = new_qty
                            st.session_state.characters[i]["inventory"][ii]["notes"]    = new_notes
                            save_json(DATA_PATH, st.session_state.characters)

                        # ── Inline item editor: rename + equip bonuses (shown when ⚙ is toggled) ──
                        if st.session_state.get(edit_key, False):
                            with st.container(border=True):
                                # Rename field
                                rn1, rn2 = st.columns([4, 1])
                                rename_val = rn1.text_input(
                                    "Rename item", value=entry["name"],
                                    key=f"inv_rename_val_{i}_{ii}",
                                    label_visibility="collapsed",
                                    placeholder="Item name…",
                                )
                                if rn2.button("Rename", key=f"inv_rename_btn_{i}_{ii}",
                                              width='stretch'):
                                    if rename_val.strip() and rename_val.strip() != entry["name"]:
                                        st.session_state.characters[i]["inventory"][ii]["name"] = rename_val.strip()
                                        save_json(DATA_PATH, st.session_state.characters)
                                        st.rerun()

                                st.divider()
                                equip_bonuses = entry.get("equip_bonuses", {})
                                if equip_bonuses:
                                    bonus_str = ", ".join(
                                        f"{s}: {a:+d}" for s, a in equip_bonuses.items()
                                    )
                                    st.caption(f"Current bonuses when equipped: {bonus_str}")
                                else:
                                    st.caption("No equip bonuses set. Add one below.")

                                be1, be2, be3 = st.columns([2, 1, 1], vertical_alignment="bottom")
                                b_stat = be1.selectbox(
                                    "Stat", EQUIP_STATS, key=f"eq_stat_{i}_{ii}",
                                )
                                b_amt = be2.number_input(
                                    "Amount", min_value=-30, max_value=30,
                                    value=0, step=1, key=f"eq_amt_{i}_{ii}",
                                )
                                if be3.button("Set", key=f"eq_set_{i}_{ii}",
                                               width='stretch'):
                                    new_bonuses = dict(entry.get("equip_bonuses", {}))
                                    new_bonuses[b_stat] = int(b_amt)
                                    st.session_state.characters[i]["inventory"][ii]["equip_bonuses"] = new_bonuses
                                    save_json(DATA_PATH, st.session_state.characters)
                                    st.rerun()

                                if equip_bonuses and st.button("Clear all bonuses",
                                                                key=f"eq_clear_{i}_{ii}"):
                                    st.session_state.characters[i]["inventory"][ii]["equip_bonuses"] = {}
                                    save_json(DATA_PATH, st.session_state.characters)
                                    st.rerun()
                else:
                    st.caption("Inventory is empty.")

            # ── SPELLS TAB ────────────────────────────────────────────────────
            with tab_spells:
                known_spells = ch.get("known_spells", [])

                # Sorted spell list — built once per file-mtime, not on every rerender.
                _ref_spells = _ref_spell_list(
                    SPELLS_SRD_PATH.stat().st_mtime if SPELLS_SRD_PATH.exists() else 0
                )

                st.markdown("**Add from spell reference**")
                if _ref_spells:
                    sp1, sp2 = st.columns([2, 4])
                    sp_level  = sp1.selectbox(
                        "Filter by level",
                        ["All"] + ["Cantrip"] + [f"Level {n}" for n in range(1, 10)],
                        key=f"sp_level_{i}",
                    )
                    sp_search = sp2.text_input("Search by name", key=f"sp_search_{i}",
                                               placeholder="e.g. Fireball")

                    _spell_pool = _ref_spells
                    if sp_level != "All":
                        target_level = 0 if sp_level == "Cantrip" else int(sp_level.split()[-1])
                        _spell_pool = [s for s in _spell_pool if s.get("level", 0) == target_level]
                    if sp_search.strip():
                        sl = sp_search.strip().lower()
                        _spell_pool = [s for s in _spell_pool if sl in s.get("name", "").lower()]

                    # De-duplicate by name (keep first occurrence — 2014 entry)
                    _seen_sp: set = set()
                    _unique_pool = []
                    for s in _spell_pool:
                        if s["name"] not in _seen_sp:
                            _seen_sp.add(s["name"])
                            _unique_pool.append(s)

                    if _unique_pool:
                        sa1, sa2 = st.columns([5, 1])
                        def _spell_label(s):
                            lvl = "Cantrip" if s.get("level", 0) == 0 else f"Lv{s['level']}"
                            return f"{s['name']}  ({lvl} {s.get('school', '')})"
                        spell_choice_idx = sa1.selectbox(
                            "Spell", range(len(_unique_pool)),
                            format_func=lambda idx: _spell_label(_unique_pool[idx]),
                            key=f"sp_choice_{i}",
                            label_visibility="collapsed",
                        )
                        if sa2.button("Learn", key=f"sp_add_{i}", width='stretch'):
                            chosen = _unique_pool[spell_choice_idx]
                            already = any(s["name"] == chosen["name"] for s in known_spells)
                            if not already:
                                st.session_state.characters[i].setdefault("known_spells", []).append({
                                    "name":   chosen["name"],
                                    "level":  chosen.get("level", 0),
                                    "school": chosen.get("school", ""),
                                })
                                save_json(DATA_PATH, st.session_state.characters)
                                st.rerun()
                            else:
                                st.warning(f"{chosen['name']} is already known.")
                    else:
                        st.caption("No spells match — try a different search or level.")
                else:
                    st.caption("Spell reference data not found. Run `python scripts/download_data.py`.")

                # List of known spells, grouped by level
                st.markdown("---")
                if known_spells:
                    sorted_spells = sorted(known_spells, key=lambda s: (s.get("level", 0), s.get("name", "")))
                    current_level = -1
                    for si, sp in enumerate(sorted_spells):
                        lvl = sp.get("level", 0)
                        if lvl != current_level:
                            current_level = lvl
                            st.markdown(f"**{'Cantrips' if lvl == 0 else f'Level {lvl}'}**")
                        sc1, sc2 = st.columns([6, 0.5])
                        sc1.write(f"{sp['name']}  —  {sp.get('school', '')}")
                        if sc2.button("✕", key=f"sp_del_{i}_{si}"):
                            # Find and remove by original index (list is sorted copy)
                            orig_idx = next(
                                j for j, s in enumerate(st.session_state.characters[i].get("known_spells", []))
                                if s["name"] == sp["name"]
                            )
                            st.session_state.characters[i]["known_spells"].pop(orig_idx)
                            save_json(DATA_PATH, st.session_state.characters)
                            st.rerun()
                else:
                    st.caption("No spells known yet.")

            # ── LOG TAB ───────────────────────────────────────────────────────
            with tab_log:
                st.caption("Track level-ups, feats, ASIs, milestones, and other character growth events.")
                adv_log = ch.get("advancement_log", [])

                if adv_log:
                    ah1, ah2, ah3, ah4 = st.columns([0.5, 1.5, 3, 0.6])
                    ah1.markdown("**Lv**"); ah2.markdown("**Event**")
                    ah3.markdown("**Description**"); ah4.markdown("")
                    for ai, entry in enumerate(reversed(adv_log)):
                        real_idx = len(adv_log) - 1 - ai
                        ac1, ac2, ac3, ac4 = st.columns([0.5, 1.5, 3, 0.6])
                        ac1.write(str(entry.get("level", "?")))
                        ac2.write(entry.get("event_type", ""))
                        ac3.write(entry.get("description", ""))
                        if ac4.button("✕", key=f"del_adv_{i}_{real_idx}"):
                            st.session_state.characters[i].setdefault("advancement_log", []).pop(real_idx)
                            save_json(DATA_PATH, st.session_state.characters)
                            st.rerun()
                else:
                    st.caption("No log entries yet.")

                EVENT_TYPES = ["Level Up", "ASI", "Feat", "Subclass feature", "Milestone", "Spell learned", "Item acquired", "Other"]
                with st.form(key=f"add_adv_{i}"):
                    al1, al2, al3, al4 = st.columns([0.7, 1.5, 3, 1], vertical_alignment="bottom")
                    adv_level = al1.number_input("Level", min_value=1, max_value=None, value=int(new_level), step=1)
                    adv_event = al2.selectbox("Event", EVENT_TYPES)
                    adv_desc  = al3.text_input("Description", placeholder="e.g. Chose Sharpshooter feat; +2 DEX")
                    adv_notes = st.text_input("Notes (optional)", placeholder="Context, story reason, etc.")
                    if al4.form_submit_button("Add to Log"):
                        if adv_desc.strip():
                            entry = {
                                "level":       int(adv_level),
                                "event_type":  adv_event,
                                "description": adv_desc.strip(),
                                "notes":       adv_notes.strip(),
                            }
                            st.session_state.characters[i].setdefault("advancement_log", []).append(entry)
                            save_json(DATA_PATH, st.session_state.characters)
                            st.rerun()
                        else:
                            st.error("Description is required.")

            # ── Save / Delete buttons (outside tabs, always visible) ───────────
            flag_key = f"char_delete_pending_{i}"

            button_cols = st.columns([7.5, 1])
            if button_cols[0].button("Save changes", key=f"save_{i}"):
                new_record = {
                    "name": new_name.strip() or ch["name"],
                    # Primary class and total level kept for backward-compatibility with other pages
                    "char_class": new_classes[0]["class"].strip() if new_classes else "",
                    "level": new_level,
                    "classes": new_classes,  # full multiclass breakdown
                    "max_hp": int(new_max_hp),
                    "current_hp": int(new_current_hp),
                    "temp_hp": int(new_temp_hp),
                    "ac": int(new_ac),
                    "initiative": int(new_init),
                    "str": int(new_str),
                    "dex": int(new_dex),
                    "con": int(new_con),
                    "int": int(new_int),
                    "wis": int(new_wis),
                    "cha": int(new_cha),
                    "save_prof":    e_save_prof,
                    "save_xprt":    e_save_xprt,
                    "skill_prof":   e_skill_prof,
                    "skill_xprt":   e_skill_xprt,
                    # Preserve fields managed by their own add/delete buttons
                    "stat_bonuses":    ch.get("stat_bonuses", []),
                    "advancement_log": ch.get("advancement_log", []),
                    "inventory":       ch.get("inventory", []),
                    "known_spells":    ch.get("known_spells", []),
                }
                # Fields owned by the edit form — compare only these to detect real changes
                _EDIT_FIELDS = [
                    "name", "char_class", "level", "classes", "max_hp", "current_hp",
                    "temp_hp", "ac", "initiative", "str", "dex", "con", "int", "wis", "cha",
                    "save_prof", "save_xprt", "skill_prof", "skill_xprt",
                ]
                record_changed = any(new_record.get(f) != ch.get(f) for f in _EDIT_FIELDS)
                # Sync mc_count so the editor reflects exactly what was saved
                st.session_state[mc_count_key] = len(new_classes)
                st.session_state.characters[i] = new_record
                save_json(DATA_PATH, st.session_state.characters)
                st.session_state[flag_key] = False
                if record_changed:
                    st.success("Saved")
                else:
                    st.info("No changes to save.")

            if confirm_delete(button_cols[1], flag_key, f"char_{i}"):
                st.session_state.characters.pop(i)
                save_json(DATA_PATH, st.session_state.characters)
                st.warning("Deleted")
                st.rerun()

if "reset_chars_pending" not in st.session_state:
    st.session_state.reset_chars_pending = False

if not st.session_state.reset_chars_pending:
    if st.button("Reset all (erase ALL data)"):
        st.session_state.reset_chars_pending = True
        st.rerun()
else:
    st.error("⚠️ This will erase ALL character data and cannot be undone.")
    rc1, _, rc2 = st.columns([1, 7, 1])
    if rc1.button("Confirm — erase everything?"):
        st.session_state.characters = []
        save_json(DATA_PATH, [])
        st.session_state.reset_chars_pending = False
        st.info("All character data erased.")
        st.rerun()
    if rc2.button("Cancel"):
        st.session_state.reset_chars_pending = False
        st.rerun()

