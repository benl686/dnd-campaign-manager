import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, confirm_delete, load_campaigns, no_campaigns_notice
from pathlib import Path


QUESTS_PATH    = Path("json/quests.json")
NPCS_PATH      = Path("json/npcs.json")

OTHERS_KEY    = "_Others_"
CLIPBOARD_KEY = "clipboard_quest"

CUSTOM_OPTION = "Other (custom)…"

campaigns = load_campaigns()
if "quests" not in st.session_state:
    st.session_state.quests = load_json(QUESTS_PATH, {})
if "npcs" not in st.session_state:
    st.session_state.npcs = load_json(NPCS_PATH, {})


def _npc_names(camp_name: str) -> list[str]:
    """Return sorted NPC names for a campaign, or [] if none."""
    raw = st.session_state.npcs.get(camp_name, {})
    npc_list = raw.get("npc_list", [])
    return sorted({n["name"] for n in npc_list if n.get("name")})


def _giver_selectbox(camp_name: str, key: str, current_value: str):
    """Render a selectbox + optional custom text input for quest giver.

    When NPCs exist for the campaign the field is a selectbox. The last option
    is 'Other (custom)…' which reveals a plain text input so free-form names
    (and existing non-NPC values) are still supported. Falls back to a plain
    text_input when no NPCs are defined yet.

    Returns the final giver string.
    """
    npc_names = _npc_names(camp_name)

    if npc_names:
        options = npc_names + [CUSTOM_OPTION]
        default_idx = options.index(current_value) if current_value in npc_names else options.index(CUSTOM_OPTION)

        chosen = st.selectbox("Quest Giver", options=options, index=default_idx, key=key)

        if chosen == CUSTOM_OPTION:
            pre = current_value if current_value not in npc_names else ""
            return st.text_input("Custom giver name", value=pre, key=key + "_custom")
        return chosen
    else:
        return st.text_input("Quest Giver", value=current_value, key=key)


def _reward_fields(quest: dict, key_prefix: str) -> dict:
    """Render the Reward tab fields and return a dict of current values.

    Schema stored under quest['reward']:
      gp (int), xp (int | None — None = milestone), items (str), notes (str)
    """
    reward = quest.get("reward", {})

    col_gp, col_xp = st.columns(2)
    with col_gp:
        gp = st.number_input(
            "Gold rewarded (gp)",
            min_value=0,
            value=int(reward.get("gp", 0)),
            step=1,
            key=f"{key_prefix}_gp",
        )
    with col_xp:
        # XP is optional — milestone campaigns skip it entirely
        track_xp = st.checkbox(
            "Track XP reward",
            value=reward.get("xp") is not None,
            key=f"{key_prefix}_track_xp",
            help="Uncheck if your campaign uses milestone leveling",
        )
        if track_xp:
            xp = st.number_input(
                "XP rewarded",
                min_value=0,
                value=int(reward.get("xp") or 0),
                step=50,
                key=f"{key_prefix}_xp",
            )
        else:
            xp = None

    items = st.text_area(
        "Item rewards",
        value=reward.get("items", ""),
        height=120,
        placeholder="Magic items, equipment, property…",
        key=f"{key_prefix}_items",
    )
    notes = st.text_area(
        "Other rewards / notes",
        value=reward.get("notes", ""),
        height=100,
        placeholder="Titles, land grants, favors, reputation…",
        key=f"{key_prefix}_notes",
    )

    return {"gp": int(gp), "xp": xp, "items": items, "notes": notes}


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Quests")
st.caption("Quests are grouped under each campaign.")

if not campaigns:
    no_campaigns_notice()
else:
    quests_by_camp = st.session_state.quests
    if isinstance(quests_by_camp, list):
        quests_by_camp = {}
    st.session_state.quests = quests_by_camp

    # Stale delete-confirm cleanup — drop any armed "Confirm?" flag whose quest
    # index no longer exists for that campaign. Without this, arming delete on
    # quest index 5 and then deleting an earlier quest (shifting later indices
    # down by one) leaves the flag armed at index 5, so the quest that shifts
    # into that slot shows a pre-armed "Confirm?" button and can be deleted
    # with a single click the user never intended.
    # Prefix-strip (not underscore-split) so campaign names containing
    # underscores can't be mis-parsed.
    for camp in campaigns:
        cn      = camp["name"]
        cur_len = len(quests_by_camp.get(cn, []))
        prefix  = f"quest_delete_pending_{cn}_"
        for key in list(st.session_state.keys()):
            if key.startswith(prefix):
                suffix = key[len(prefix):]
                if suffix.isdigit() and int(suffix) >= cur_len:
                    del st.session_state[key]

    for camp in campaigns:
        camp_name = camp["name"]
        header = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name
        with st.expander(header):
            camp_quests = quests_by_camp.get(camp_name, [])

            # ── Clipboard paste bar ───────────────────────────────────────────
            clip = st.session_state.get(CLIPBOARD_KEY)
            if clip:
                pb1, pb2 = st.columns([4, 1])
                pb1.info(f"📋 Clipboard: **{clip['label']}**")
                if pb2.button("Paste Here", key=f"quest_paste_{camp_name}"):
                    camp_quests.append(dict(clip["record"]))
                    quests_by_camp[camp_name] = camp_quests
                    st.session_state.quests = quests_by_camp
                    save_json(QUESTS_PATH, quests_by_camp)
                    st.success(f"Pasted: {clip['label']}")
                    st.rerun()

            # Sort: incomplete quests first, completed last
            sorted_indices = sorted(
                range(len(camp_quests)),
                key=lambda k: camp_quests[k].get("completed", False),
            )

            # ── Existing quests ───────────────────────────────────────────────
            for orig_idx in sorted_indices:
                quest = camp_quests[orig_idx]
                idx = orig_idx
                completed = quest.get("completed", False)
                title = quest.get("name", f"Quest {idx+1}")
                giver = quest.get("giver", "")
                display_title = f"{title} – {giver}" if giver else title

                with st.expander(display_title):
                    # ── Header row ────────────────────────────────────────────
                    top_cols = st.columns([2, 2, 1])
                    with top_cols[0]:
                        name = st.text_input(
                            "Quest",
                            value=quest.get("name", ""),
                            key=f"{camp_name}_q_name_{idx}",
                        )
                    with top_cols[1]:
                        giver_val = _giver_selectbox(
                            camp_name,
                            key=f"{camp_name}_q_giver_{idx}",
                            current_value=giver,
                        )
                    with top_cols[2]:
                        completed_val = st.checkbox(
                            "Completed",
                            value=completed,
                            key=f"{camp_name}_q_completed_{idx}",
                        )

                    # ── Tabs ──────────────────────────────────────────────────
                    tab_details, tab_reward = st.tabs(["Details", "Reward"])

                    with tab_details:
                        details = st.text_area(
                            "Details",
                            value=quest.get("details", ""),
                            height=300,
                            key=f"{camp_name}_q_details_{idx}",
                        )

                    with tab_reward:
                        reward_vals = _reward_fields(quest, key_prefix=f"{camp_name}_q_{idx}")

                    # ── Preview + actions ─────────────────────────────────────
                    st.markdown(
                        f"<span style='color:{'green' if completed_val else 'inherit'};'>Preview: "
                        f"{(name or 'Unnamed quest')} – {giver_val}</span>",
                        unsafe_allow_html=True,
                    )

                    # Copy to clipboard
                    if st.button("Copy", key=f"{camp_name}_q_copy_{idx}",
                                 help="Copy to clipboard to paste into another campaign"):
                        st.session_state[CLIPBOARD_KEY] = {
                            "record": quest,
                            "label": quest.get("name", f"Quest {idx+1}"),
                        }
                        st.rerun()

                    c_save, c_delete = st.columns([7.5, 1])

                    flag_key = f"quest_delete_pending_{camp_name}_{idx}"

                    if c_save.button("Save quest", key=f"{camp_name}_q_save_{idx}"):
                        camp_quests[idx] = {
                            "name":      name.strip() or quest.get("name", f"Quest {idx+1}"),
                            "giver":     (giver_val or "").strip(),
                            "details":   details,
                            "completed": completed_val,
                            "reward":    reward_vals,
                        }
                        quests_by_camp[camp_name] = camp_quests
                        st.session_state.quests = quests_by_camp
                        st.session_state[flag_key] = False
                        save_json(QUESTS_PATH, quests_by_camp)
                        st.success("Quest saved")

                    if confirm_delete(c_delete, flag_key, f"{camp_name}_q_{idx}"):
                        camp_quests.pop(idx)
                        quests_by_camp[camp_name] = camp_quests
                        st.session_state.quests = quests_by_camp
                        save_json(QUESTS_PATH, quests_by_camp)
                        st.warning("Quest deleted")
                        st.rerun()

            # ── Add new quest ─────────────────────────────────────────────────
            st.markdown("---")
            st.subheader("Add New Quest")
            top_cols_new = st.columns([2, 2])
            with top_cols_new[0]:
                new_name = st.text_input(
                    f"New Quest for {camp_name}",
                    key=f"{camp_name}_new_q_name",
                )
            with top_cols_new[1]:
                new_giver = _giver_selectbox(
                    camp_name,
                    key=f"{camp_name}_new_q_giver",
                    current_value="",
                )

            new_tab_details, new_tab_reward = st.tabs(["Details", "Reward"])

            with new_tab_details:
                new_details = st.text_area(
                    "Details",
                    height=300,
                    key=f"{camp_name}_new_q_details",
                )

            with new_tab_reward:
                new_reward_vals = _reward_fields({}, key_prefix=f"{camp_name}_new_q")

            if st.button(f"Add quest to {camp_name}", key=f"{camp_name}_add_quest"):
                if new_name.strip():
                    camp_quests.append({
                        "name":      new_name.strip(),
                        "giver":     (new_giver or "").strip(),
                        "details":   new_details,
                        "completed": False,
                        "reward":    new_reward_vals,
                    })
                    quests_by_camp[camp_name] = camp_quests
                    st.session_state.quests = quests_by_camp
                    save_json(QUESTS_PATH, quests_by_camp)
                    st.success("Quest added")
                    st.rerun()
                else:
                    st.error("Quest Name is required")


# ── Others Archive ────────────────────────────────────────────────────────────
# Access session state directly so this renders even when no campaigns exist.
_quests_ss   = st.session_state.quests if isinstance(st.session_state.quests, dict) else {}
others_quests = _quests_ss.get(OTHERS_KEY, [])
if others_quests:
    with st.expander(f"📦 Others Archive — {len(others_quests)} orphaned quest(s)"):
        st.caption("Quests kept when their campaign was deleted. Copy them to move to a campaign.")
        for oi, quest in enumerate(others_quests):
            status = "✅" if quest.get("completed") else "❌"
            label  = f"{status} {quest.get('name', f'Quest {oi+1}')}"
            if quest.get("giver"):
                label += f" — {quest['giver']}"
            with st.expander(label):
                if quest.get("details"):
                    st.markdown(quest["details"][:200] + ("…" if len(quest.get("details",""))>200 else ""))

                oc1, oc2 = st.columns(2)
                if oc1.button("Copy", key=f"others_quest_copy_{oi}"):
                    st.session_state[CLIPBOARD_KEY] = {
                        "record": quest, "label": quest.get("name", f"Quest {oi+1}"),
                    }
                    st.rerun()
                if confirm_delete(oc2, f"others_quest_del_{oi}", f"others_quest_{oi}"):
                    others_quests.pop(oi)
                    _quests_ss[OTHERS_KEY] = others_quests
                    st.session_state.quests = _quests_ss
                    save_json(QUESTS_PATH, _quests_ss)
                    st.rerun()

