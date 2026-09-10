"""
ResourceTracker.py — Per-character class resource tracking.

Persists each character's pools (spell slots, ki, rage, etc.) to
json/resources.json so they survive page refreshes. Resources store a
name, max value, current value, and reset type (long/short/dawn/manual).

Short Rest restores resources with reset="short".
Long Rest restores everything.
"""

import streamlit as st
from utils import load_json, load_json_cached, save_json, sidebar_exit_button, confirm_delete
from pathlib import Path

CHARS_PATH     = Path("json/characters.json")
RESOURCES_PATH = Path("json/resources.json")

# ── Spell slot table (same as Combat.py, reproduced here to avoid importing) ──
_SLOT_TABLE = {
    1:  [2,0,0,0,0,0,0,0,0], 2:  [3,0,0,0,0,0,0,0,0],
    3:  [4,2,0,0,0,0,0,0,0], 4:  [4,3,0,0,0,0,0,0,0],
    5:  [4,3,2,0,0,0,0,0,0], 6:  [4,3,3,0,0,0,0,0,0],
    7:  [4,3,3,1,0,0,0,0,0], 8:  [4,3,3,2,0,0,0,0,0],
    9:  [4,3,3,3,1,0,0,0,0], 10: [4,3,3,3,2,0,0,0,0],
    11: [4,3,3,3,2,1,0,0,0], 12: [4,3,3,3,2,1,0,0,0],
    13: [4,3,3,3,2,1,1,0,0], 14: [4,3,3,3,2,1,1,0,0],
    15: [4,3,3,3,2,1,1,1,0], 16: [4,3,3,3,2,1,1,1,0],
    17: [4,3,3,3,2,1,1,1,1], 18: [4,3,3,3,3,1,1,1,1],
    19: [4,3,3,3,3,2,1,1,1], 20: [4,3,3,3,3,2,2,1,1],
}
_ORDINALS = ["1st","2nd","3rd","4th","5th","6th","7th","8th","9th"]

# ── Common resource templates by class ───────────────────────────────────────
# Tuples of (display_name, default_max, reset_type).
# Only include things with a fixed numeric max; open-ended passives are omitted.
CLASS_TEMPLATES: dict[str, list[tuple]] = {
    "Artificer":  [("Flash of Genius", 3, "long"), ("Infusions Active", 2, "long")],
    "Barbarian":  [("Rage", 2, "long"), ("Relentless Endurance", 1, "long")],
    "Bard":       [("Bardic Inspiration", 3, "long"), ("Song of Rest", 1, "short")],
    "Cleric":     [("Channel Divinity", 1, "short")],
    "Druid":      [("Wild Shape", 2, "short")],
    "Fighter":    [("Action Surge", 1, "short"), ("Second Wind", 1, "short"),
                   ("Indomitable", 1, "long")],
    "Monk":       [("Ki Points", 4, "short"), ("Stunning Strike", 2, "short")],
    "Paladin":    [("Channel Divinity", 1, "short"), ("Lay on Hands", 25, "long")],
    "Ranger":     [("Favored Foe", 1, "long")],
    "Rogue":      [("Uncanny Dodge", 1, "short"), ("Evasion", 1, "short")],
    "Sorcerer":   [("Sorcery Points", 4, "long"), ("Metamagic (uses)", 2, "long")],
    "Warlock":    [("Pact Magic Slots", 2, "short"), ("Mystic Arcanum 6th", 1, "long"),
                   ("Mystic Arcanum 7th", 1, "long")],
    "Wizard":     [("Arcane Recovery", 1, "long"), ("Spell Mastery", 1, "long")],
}

RESET_LABELS = {"long": "Long Rest", "short": "Short Rest", "dawn": "Dawn", "manual": "Manual"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _save(data: dict):
    save_json(RESOURCES_PATH, data)


def _restore(resources: list, rest_type: str) -> list:
    """Return a copy of resources with appropriate ones refilled."""
    result = []
    for r in resources:
        new_r = dict(r)
        # Long rest restores everything; short rest restores short-rest resources
        if rest_type == "long" or (rest_type == "short" and r.get("reset") == "short"):
            new_r["current"] = r["max"]
        result.append(new_r)
    return result


def _on_cur_change(char_name: str, ri: int, widget_key: str):
    """on_change callback: write updated current value to session state and disk."""
    st.session_state.res_data[char_name][ri]["current"] = st.session_state[widget_key]
    _save(st.session_state.res_data)


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Resource Tracker")
st.caption("Track spell slots, ki, rage, and other per-character resources mid-session.")

characters = load_json_cached(CHARS_PATH, [])
if not characters:
    st.info("No characters yet. Add them on the Characters page first.")
    st.stop()

if "res_data" not in st.session_state:
    st.session_state.res_data = load_json(RESOURCES_PATH, {})

res_data: dict = st.session_state.res_data

# ── Global rest buttons ───────────────────────────────────────────────────────
rb1, rb2, _ = st.columns([1, 1, 4])
if rb1.button("💤 Short Rest — All"):
    for ch in characters:
        name = ch["name"]
        if name in res_data:
            res_data[name] = _restore(res_data[name], "short")
    _save(res_data)
    st.rerun()
if rb2.button("🌙 Long Rest — All"):
    for ch in characters:
        name = ch["name"]
        if name in res_data:
            res_data[name] = _restore(res_data[name], "long")
    _save(res_data)
    st.rerun()

st.markdown("---")

# ── Per-character panels ───────────────────────────────────────────────────────
for i, ch in enumerate(characters):
    name     = ch["name"]
    ch_class = ch.get("char_class", "Unknown")
    level    = int(ch.get("level", 1))

    # Ensure this character has an entry
    if name not in res_data:
        res_data[name] = []
    resources = res_data[name]

    # Status badge: how many pools are depleted
    depleted = sum(1 for r in resources if r.get("current", r.get("max", 0)) < r.get("max", 1))
    badge    = f"  ·  ⚠️ {depleted} depleted" if depleted else "  ·  ✓ Full"
    label    = f"{name} — {ch_class} {level}{badge}"

    with st.expander(label):

        # Individual rest buttons
        ir1, ir2, _ = st.columns([1, 1, 4])
        if ir1.button("💤 Short Rest", key=f"sr_{i}"):
            res_data[name] = _restore(resources, "short")
            _save(res_data)
            st.rerun()
        if ir2.button("🌙 Long Rest", key=f"lr_{i}"):
            res_data[name] = _restore(resources, "long")
            _save(res_data)
            st.rerun()

        # ── Resource table ─────────────────────────────────────────────────
        if resources:
            rh1, rh2, rh3, rh4, rh5 = st.columns([3, 1.2, 1, 1.5, 0.5])
            rh1.markdown("**Resource**")
            rh2.markdown("**Remaining**")
            rh3.markdown("**Max**")
            rh4.markdown("**Resets On**")

            for ri, r in enumerate(resources):
                rc1, rc2, rc3, rc4, rc5 = st.columns([3, 1.2, 1, 1.5, 0.5])
                rc1.write(r["name"])

                # Editable current value — on_change saves immediately
                wkey = f"res_{name}_{ri}"
                rc2.number_input(
                    "Remaining", label_visibility="collapsed",
                    min_value=0, max_value=r["max"],
                    value=int(r.get("current", r["max"])),
                    step=1, key=wkey,
                    on_change=_on_cur_change, args=(name, ri, wkey),
                )

                rc3.write(str(r["max"]))
                rc4.caption(RESET_LABELS.get(r.get("reset", "long"), "Long Rest"))

                # Two-step delete
                if confirm_delete(rc5, f"res_del_{i}_{ri}", f"res_{i}_{ri}", label="✕", confirm_label="✓?"):
                    res_data[name].pop(ri)
                    _save(res_data)
                    st.rerun()
        else:
            st.caption("No resources tracked yet. Add some below.")

        st.markdown("---")

        # ── Add resource ───────────────────────────────────────────────────
        with st.expander("➕ Add Resource"):

            # ── Spell slot quick-add ───────────────────────────────────────
            st.caption("Spell slots (click to add):")
            slots = _SLOT_TABLE.get(min(level, 20), _SLOT_TABLE[20])
            sl_cols = st.columns(9)
            for si, slot_count in enumerate(slots):
                if slot_count > 0:
                    res_key = f"Spell Slot {_ORDINALS[si]}"
                    btn_label = f"{_ORDINALS[si]}\n({slot_count})"
                    if sl_cols[si].button(btn_label, key=f"slot_{i}_{si}"):
                        if not any(r["name"] == res_key for r in resources):
                            res_data[name].append({
                                "name": res_key, "max": slot_count,
                                "current": slot_count, "reset": "long",
                            })
                            _save(res_data)
                            st.rerun()
                        else:
                            st.toast(f"{res_key} already tracked.")

            # ── Class template quick-add ───────────────────────────────────
            templates = CLASS_TEMPLATES.get(ch_class, [])
            if templates:
                st.caption(f"Common {ch_class} resources (click to add):")
                t_cols = st.columns(min(len(templates), 4))
                for ti, (tmpl_name, tmpl_max, tmpl_reset) in enumerate(templates):
                    if t_cols[ti % 4].button(tmpl_name, key=f"tmpl_{i}_{ti}"):
                        if not any(r["name"] == tmpl_name for r in resources):
                            res_data[name].append({
                                "name": tmpl_name, "max": tmpl_max,
                                "current": tmpl_max, "reset": tmpl_reset,
                            })
                            _save(res_data)
                            st.rerun()
                        else:
                            st.toast(f"{tmpl_name} already tracked.")

            # ── Manual custom resource ─────────────────────────────────────
            st.caption("Custom resource:")
            with st.form(key=f"add_res_{i}"):
                af1, af2, af3, af4 = st.columns([3, 1, 1.5, 1], vertical_alignment="bottom")
                new_name  = af1.text_input("Name", placeholder="e.g. Rage, Ki Points, Sorcery Points")
                new_max   = af2.number_input("Max",  min_value=1, value=1, step=1)
                new_reset = af3.selectbox("Resets On", list(RESET_LABELS.values()))
                if af4.form_submit_button("Add"):
                    if new_name.strip():
                        # Map display label back to short key
                        reset_key = {v: k for k, v in RESET_LABELS.items()}[new_reset]
                        res_data[name].append({
                            "name":    new_name.strip(),
                            "max":     int(new_max),
                            "current": int(new_max),
                            "reset":   reset_key,
                        })
                        _save(res_data)
                        st.rerun()
                    else:
                        st.error("Name is required.")
