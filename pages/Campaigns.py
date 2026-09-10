import streamlit as st
from utils import load_json, save_json, sidebar_exit_button
from pathlib import Path


DATA_PATH  = Path("json/campaigns.json")
OTHERS_KEY = "_Others_"

# ── Data store registry ───────────────────────────────────────────────────────
# Maps human-readable label → (json_path, schema_type).
# schema_type controls how records are merged into the _Others_ bucket.
DATA_STORES = {
    "Factions":           (Path("json/factions.json"),           "list"),
    "Faiths":             (Path("json/faiths.json"),             "list"),
    "Quests":             (Path("json/quests.json"),             "list"),
    "Sessions":           (Path("json/sessions.json"),           "list"),
    "Homebrew Rules":     (Path("json/homebrew_rules.json"),     "list"),
    "Travel Log":         (Path("json/travel_tracker.json"),     "list"),
    "Rumor Board":        (Path("json/rumor_board.json"),        "list"),
    "Magic Item Journal": (Path("json/magic_item_journal.json"), "list"),
    "Party Inventory":    (Path("json/party_inventory.json"),    "list"),
    "NPCs":               (Path("json/npcs.json"),               "npc"),
    "Worldbuilding":      (Path("json/worldbuilding.json"),      "worldbuilding"),
    "Downtime":           (Path("json/downtime.json"),           "downtime"),
    "Calendar":           (Path("json/calendar.json"),           "singular"),
    "Weather":            (Path("json/weather_tracker.json"),    "singular"),
}


def _has_camp_data(data: dict, camp_name: str, schema: str) -> bool:
    """Return True if this data store has non-empty content for camp_name."""
    camp = data.get(camp_name)
    if not camp:
        return False
    if schema == "list":
        return bool(camp)
    if schema == "npc":
        return bool(camp.get("npc_list") or camp.get("relationship_web"))
    if schema == "worldbuilding":
        return any(camp.get(k) for k in ("regions", "cities", "nations", "lore", "planes"))
    if schema == "downtime":
        return any(isinstance(v, list) and v for v in camp.values())
    if schema == "singular":
        return True
    return False


def _move_to_others(data: dict, camp_name: str, schema: str) -> None:
    """Merge camp_name's records into the _Others_ key, preserving existing Others data."""
    camp_data = data.get(camp_name)
    if not camp_data:
        return

    if schema == "list":
        others = data.get(OTHERS_KEY, [])
        data[OTHERS_KEY] = others + (camp_data if isinstance(camp_data, list) else [])

    elif schema == "npc":
        others = data.get(OTHERS_KEY, {"npc_list": [], "relationship_web": [], "legacy_notes": ""})
        for key in ("npc_list", "relationship_web"):
            others[key] = others.get(key, []) + camp_data.get(key, [])
        parts = [p for p in (others.get("legacy_notes",""), camp_data.get("legacy_notes","")) if p]
        others["legacy_notes"] = "\n".join(parts)
        data[OTHERS_KEY] = others

    elif schema == "worldbuilding":
        others = data.get(OTHERS_KEY, {})
        for key in ("regions", "cities", "nations", "lore", "planes"):
            others[key] = others.get(key, []) + camp_data.get(key, [])
        data[OTHERS_KEY] = others

    elif schema == "downtime":
        others = data.get(OTHERS_KEY, {})
        for char_name, activities in camp_data.items():
            if isinstance(activities, list):
                others[char_name] = others.get(char_name, []) + activities
        data[OTHERS_KEY] = others

    elif schema == "singular":
        # Weather / calendar: no meaningful merge — only keep if Others slot is empty
        if OTHERS_KEY not in data:
            data[OTHERS_KEY] = camp_data

    data.pop(camp_name, None)


def _execute_cascade(camp_name: str, delete_set: set) -> None:
    """Perform cascade delete for one campaign.

    delete_set: DATA_STORES display-name labels to permanently erase.
    Everything else with data moves to _Others_.
    """
    for label, (path, schema) in DATA_STORES.items():
        raw = load_json(path, {})
        # Nothing stored for this campaign in this data store at all — skip the
        # write entirely. Previously every one of the 14 stores was rewritten
        # (full atomic write + .bak rotation) on every campaign delete, even
        # for stores the DM never touched for that campaign.
        if camp_name not in raw:
            continue
        if label in delete_set:
            raw.pop(camp_name, None)
        elif _has_camp_data(raw, camp_name, schema):
            _move_to_others(raw, camp_name, schema)
        else:
            raw.pop(camp_name, None)   # present but empty/falsy — clean up the stale entry
        save_json(path, raw)

    # Invalidate loaded session state so pages reload fresh data on next visit
    for ss_key in ("npcs", "factions", "faiths", "quests", "sessions",
                   "homebrew_rules", "downtime_data", "travel_data",
                   "weather_data", "rumor_board", "item_journal", "party_inv",
                   "calendar_data"):
        st.session_state.pop(ss_key, None)


# ── Session state ─────────────────────────────────────────────────────────────

if "campaigns" not in st.session_state:
    st.session_state.campaigns = load_json(DATA_PATH, [])

# Stale-key cleanup for delete and cascade flags
for key in list(st.session_state.keys()):
    if key.startswith(("camp_delete_pending_", "camp_cascade_")):
        try:
            idx = int(key.split("_")[-1])
        except ValueError:
            continue
        if idx >= len(st.session_state.campaigns):
            del st.session_state[key]


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Campaign Manager")
st.caption("Campaigns are saved to 'json/campaigns.json' and shared across all tabs.")

# ── Create form ───────────────────────────────────────────────────────────────

st.markdown("""
    <div style="background-color: #f8f9fa; border: 2px solid #466799; border-radius: 12px;
                padding: 24px 18px; margin-bottom: 24px; box-shadow: 2px 4px 20px rgba(60,60,100,.12)">
    <h2 style="color:#466799; margin-top: 0; margin-bottom:8px;">Create New Campaign</h2>
""", unsafe_allow_html=True)

with st.form("create_campaign"):
    name       = st.text_input("Campaign name")
    st.caption("System: **D&D 5e**")
    basic_info = st.text_area("Basic info (premise, setting, key themes)", height=120)
    create     = st.form_submit_button("Create Campaign")

    if create:
        if name.strip():
            existing_names = [c["name"].lower() for c in st.session_state.campaigns]
            if name.strip().lower() in existing_names:
                st.error("A campaign with this name already exists.")
            else:
                st.session_state.campaigns.append({
                    "name": name.strip(), "system": "D&D 5e", "basic_info": basic_info,
                })
                save_json(DATA_PATH, st.session_state.campaigns)
                st.success(f"Created campaign '{name.strip()}'")
        else:
            st.error("Campaign name is required")

st.markdown("</div>", unsafe_allow_html=True)

# ── Campaign list ─────────────────────────────────────────────────────────────

st.subheader("Your Campaigns")
if not st.session_state.campaigns:
    st.info("No campaigns yet. Create one above.")
else:
    for i, camp in enumerate(st.session_state.campaigns):
        flag_key    = f"camp_delete_pending_{i}"
        cascade_key = f"camp_cascade_{i}"

        if flag_key not in st.session_state:
            st.session_state[flag_key] = False
        if cascade_key not in st.session_state:
            st.session_state[cascade_key] = False

        with st.expander(f"{camp['name']}  —  D&D 5e"):

            # ── Cascade checklist (state 3: after second confirm) ─────────────
            if st.session_state[cascade_key]:
                st.warning(f"⚠ Deleting **{camp['name']}**. Choose what happens to its data:")
                st.caption("Checked items are **permanently deleted**. Unchecked items are moved to the **Others** archive, accessible in each page.")

                # Load each data store and build the checklist (only show ones with content)
                existing_data: dict[str, dict] = {}
                has_data_for: dict[str, bool]  = {}
                # "singular" schema (Calendar/Weather) has only one Others slot and no
                # sensible way to merge two calendars — flag campaigns whose data would
                # silently be discarded (not "kept in Others" as the UI copy implies)
                # because that slot is already taken by a different campaign's data.
                singular_conflict: dict[str, bool] = {}
                for label, (path, schema) in DATA_STORES.items():
                    raw = load_json(path, {})
                    existing_data[label] = raw
                    has_data_for[label]  = _has_camp_data(raw, camp["name"], schema)
                    if schema == "singular":
                        singular_conflict[label] = OTHERS_KEY in raw

                data_types_with_content = [lbl for lbl, has in has_data_for.items() if has]

                if not data_types_with_content:
                    st.info("No data found for this campaign in any page. Deleting it now.")
                    delete_set = set()
                else:
                    st.caption("Select which data to **permanently delete** (leave unchecked to keep in Others):")
                    delete_set = set()
                    # Group into columns for readability
                    cols = st.columns(3)
                    for ci, lbl in enumerate(data_types_with_content):
                        if singular_conflict.get(lbl):
                            # Force-checked and disabled — being honest that this WILL be
                            # deleted, instead of letting the user leave it "unchecked"
                            # and believe it was kept.
                            cols[ci % 3].checkbox(
                                f"Delete {lbl}", value=True, disabled=True,
                                key=f"cascade_cb_{i}_{lbl}",
                                help="Others archive already holds a different campaign's "
                                     "data for this — there's only one slot, so this can't "
                                     "be merged and will be deleted.",
                            )
                            delete_set.add(lbl)
                        elif cols[ci % 3].checkbox(f"Delete {lbl}", value=False, key=f"cascade_cb_{i}_{lbl}"):
                            delete_set.add(lbl)

                cc1, cc2 = st.columns(2)
                if cc1.button("Delete Campaign", type="primary", key=f"cascade_confirm_{i}"):
                    _execute_cascade(camp["name"], delete_set)
                    st.session_state.campaigns.pop(i)
                    save_json(DATA_PATH, st.session_state.campaigns)
                    st.session_state[cascade_key] = False
                    kept = [l for l in data_types_with_content if l not in delete_set]
                    if kept:
                        st.success(f"Campaign deleted. Kept in Others: {', '.join(kept)}.")
                    else:
                        st.success("Campaign and all its data deleted.")
                    st.rerun()
                if cc2.button("Cancel", key=f"cascade_cancel_{i}"):
                    st.session_state[cascade_key] = False
                    st.rerun()

            else:
                # ── Normal edit form (states 1 & 2) ───────────────────────────
                new_name = st.text_input("Campaign name", value=camp["name"], key=f"camp_name_{i}")
                st.caption("System: **D&D 5e**")
                new_basic_info = st.text_area(
                    "Basic info (premise, setting, key themes)",
                    value=camp.get("basic_info", ""),
                    height=120,
                    key=f"camp_basic_{i}",
                )

                button_cols = st.columns([7.5, 1])
                if button_cols[0].button("Save Changes", key=f"camp_save_{i}"):
                    final_name = new_name.strip() or camp["name"]
                    # Exclude this campaign's own current name from the collision check,
                    # so re-saving without changing the name doesn't false-positive.
                    other_names = [
                        c["name"].lower() for j, c in enumerate(st.session_state.campaigns) if j != i
                    ]
                    if final_name.lower() in other_names:
                        st.error("A campaign with this name already exists.")
                    else:
                        st.session_state.campaigns[i] = {
                            "name": final_name,
                            "system": "D&D 5e",
                            "basic_info": new_basic_info,
                        }
                        save_json(DATA_PATH, st.session_state.campaigns)
                        st.session_state[flag_key] = False
                        st.success("Saved")

                if not st.session_state[flag_key]:
                    if button_cols[1].button("Delete", key=f"camp_delete_{i}"):
                        st.session_state[flag_key] = True
                        st.rerun()
                else:
                    # State 2: first confirm — show inline warning + Confirm/Cancel buttons
                    st.warning(f"Really delete **{camp['name']}**? You'll choose what to keep next.")
                    dc1, _, dc2 = st.columns([1, 7, 1])
                    if dc1.button("Confirm delete?", key=f"camp_confirm_{i}", type="primary"):
                        st.session_state[cascade_key] = True
                        st.session_state[flag_key]    = False
                        st.rerun()
                    if dc2.button("Cancel", key=f"camp_cancel_del_{i}"):
                        st.session_state[flag_key] = False
                        st.rerun()

# ── Reset all ─────────────────────────────────────────────────────────────────

if "reset_all_camps_pending" not in st.session_state:
    st.session_state.reset_all_camps_pending = False

if not st.session_state.reset_all_camps_pending:
    if st.button("Reset all campaigns (erase ALL campaign data)"):
        st.session_state.reset_all_camps_pending = True
        st.rerun()
else:
    st.warning("This will permanently delete all campaign data. This cannot be undone.")
    rc1, _, rc2 = st.columns([1, 7, 1])
    if rc1.button("Confirm — Erase Everything", type="primary"):
        st.session_state.campaigns = []
        save_json(DATA_PATH, [])
        st.session_state.reset_all_camps_pending = False
        st.info("All campaign data erased.")
        st.rerun()
    if rc2.button("Cancel"):
        st.session_state.reset_all_camps_pending = False
        st.rerun()

