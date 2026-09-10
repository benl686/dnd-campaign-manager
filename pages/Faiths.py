import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, confirm_delete, load_campaigns, no_campaigns_notice
from pathlib import Path


def _mark_dirty(key: str):
    """Mark an edit form as having unsaved changes (used as on_change callback)."""
    st.session_state[key] = True


FAITHS_PATH    = Path("json/faiths.json")

OTHERS_KEY    = "_Others_"
CLIPBOARD_KEY = "clipboard_faith"

campaigns = load_campaigns()
if "faiths" not in st.session_state:
    st.session_state.faiths = load_json(FAITHS_PATH, {})

st.title("Faiths")
st.caption("Each campaign has its own list of faiths, with individual conflicts and details.")

if not campaigns:
    no_campaigns_notice()
else:
    faiths_by_camp = st.session_state.faiths
    if isinstance(faiths_by_camp, list):
        faiths_by_camp = {}
    st.session_state.faiths = faiths_by_camp

    # Stale key cleanup — keys are now faith_delete_pending_{camp_idx}_{faith_idx}
    # Using numeric indices avoids fragile underscore-splitting on campaign names.
    for key in list(st.session_state.keys()):
        if key.startswith("faith_delete_pending_"):
            parts = key.split("_")
            try:
                camp_idx  = int(parts[-2])
                faith_idx = int(parts[-1])
            except (ValueError, IndexError):
                del st.session_state[key]
                continue
            if camp_idx >= len(campaigns):
                del st.session_state[key]
                continue
            camp_key = campaigns[camp_idx]["name"]
            if faith_idx >= len(faiths_by_camp.get(camp_key, [])):
                del st.session_state[key]

    for camp_idx, camp in enumerate(campaigns):
        camp_name = camp["name"]
        header = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name
        with st.expander(header):
            camp_key = camp_name
            camp_faiths = faiths_by_camp.get(camp_key, [])

            # ── Clipboard paste bar ───────────────────────────────────────────
            clip = st.session_state.get(CLIPBOARD_KEY)
            if clip:
                pb1, pb2 = st.columns([4, 1])
                pb1.info(f"📋 Clipboard: **{clip['label']}**")
                if pb2.button("Paste Here", key=f"faith_paste_{camp_key}"):
                    camp_faiths.append(dict(clip["record"]))
                    faiths_by_camp[camp_key] = camp_faiths
                    st.session_state.faiths = faiths_by_camp
                    save_json(FAITHS_PATH, faiths_by_camp)
                    st.success(f"Pasted: {clip['label']}")
                    st.rerun()

            for idx, faith in enumerate(camp_faiths):
                faith_header = faith.get("name", f"Faith {idx+1}")
                with st.expander(f"Faith: {faith_header}"):
                    dirty_key = f"{camp_key}_faith_dirty_{idx}"

                    name = st.text_input(
                        "Faith name",
                        value=faith.get("name", ""),
                        key=f"{camp_key}_faith_name_{idx}",
                        on_change=_mark_dirty, args=(dirty_key,),
                    )

                    doctrine = st.text_area(
                        "Doctrine",
                        value=faith.get("doctrine", ""),
                        height=400,
                        key=f"{camp_key}_faith_doctrine_{idx}",
                        on_change=_mark_dirty, args=(dirty_key,),
                    )
                    # Conflicts removed — use Relationship Map to track faith conflicts.

                    if st.session_state.get(dirty_key):
                        st.caption("⚠ Unsaved changes")

                    if st.button("Copy", key=f"{camp_key}_faith_copy_{idx}",
                                 help="Copy to clipboard to paste into another campaign"):
                        st.session_state[CLIPBOARD_KEY] = {
                            "record": faith,
                            "label": faith.get("name", f"Faith {idx+1}"),
                        }
                        st.rerun()

                    c_save, c_delete = st.columns([7.5, 1])

                    flag_key = f"faith_delete_pending_{camp_idx}_{idx}"

                    if c_save.button("Save Faith", key=f"{camp_key}_faith_save_{idx}"):
                        camp_faiths[idx] = {
                            "name":     name.strip() or faith.get("name", f"Faith {idx+1}"),
                            "doctrine": doctrine,
                        }
                        faiths_by_camp[camp_key] = camp_faiths
                        st.session_state.faiths = faiths_by_camp
                        st.session_state[flag_key] = False  # saving disarms a pending delete
                        st.session_state[dirty_key] = False
                        save_json(FAITHS_PATH, faiths_by_camp)
                        st.success("Faith saved")

                    if confirm_delete(c_delete, flag_key, f"{camp_key}_faith_{idx}"):
                        camp_faiths.pop(idx)
                        faiths_by_camp[camp_key] = camp_faiths
                        st.session_state.faiths = faiths_by_camp
                        save_json(FAITHS_PATH, faiths_by_camp)
                        st.warning("Faith deleted")
                        st.rerun()

            st.markdown("---")
            st.subheader("Add New Faith")
            new_name = st.text_input(
                f"New faith name for {camp_name}",
                key=f"{camp_key}_new_faith_name",
            )
            new_doctrine = st.text_area(
                "Doctrine",
                height=360,
                key=f"{camp_key}_new_faith_doctrine",
            )

            if st.button(f"Add faith to {camp_name}", key=f"{camp_key}_add_faith"):
                if new_name.strip():
                    camp_faiths.append({
                        "name":     new_name.strip(),
                        "doctrine": new_doctrine,
                    })
                    faiths_by_camp[camp_key] = camp_faiths
                    st.session_state.faiths = faiths_by_camp
                    save_json(FAITHS_PATH, faiths_by_camp)
                    st.success("Faith added")
                    st.rerun()
                else:
                    st.error("Faith name is required")


# ── Others Archive ────────────────────────────────────────────────────────────
# Access session state directly so this renders even when no campaigns exist.
_faiths_ss   = st.session_state.faiths if isinstance(st.session_state.faiths, dict) else {}
others_faiths = _faiths_ss.get(OTHERS_KEY, [])
if others_faiths:
    with st.expander(f"📦 Others Archive — {len(others_faiths)} orphaned faith(s)"):
        st.caption("Faiths kept when their campaign was deleted. Copy them to move to a campaign.")
        for oi, faith in enumerate(others_faiths):
            with st.expander(faith.get("name", f"Faith {oi+1}")):
                if faith.get("doctrine"):
                    st.markdown(faith["doctrine"][:300] + ("…" if len(faith.get("doctrine","")) > 300 else ""))

                oc1, oc2 = st.columns(2)
                if oc1.button("Copy", key=f"others_faith_copy_{oi}"):
                    st.session_state[CLIPBOARD_KEY] = {
                        "record": faith, "label": faith.get("name", f"Faith {oi+1}"),
                    }
                    st.rerun()
                if confirm_delete(oc2, f"others_faith_del_{oi}", f"others_faith_{oi}"):
                    others_faiths.pop(oi)
                    _faiths_ss[OTHERS_KEY] = others_faiths
                    st.session_state.faiths = _faiths_ss
                    save_json(FAITHS_PATH, _faiths_ss)
                    st.rerun()

