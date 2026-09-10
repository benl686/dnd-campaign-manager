import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, load_campaigns, no_campaigns_notice
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

JOURNAL_PATH   = Path("json/magic_item_journal.json")


# ── Session state ─────────────────────────────────────────────────────────────

campaigns = load_campaigns()
if "item_journal" not in st.session_state:
    # Schema: {campaign_name: [{display_name, appearance, found_in, identified, true_name, properties, notes}]}
    st.session_state.item_journal = load_json(JOURNAL_PATH, {})


def save_journal():
    """Write the current journal state to disk."""
    save_json(JOURNAL_PATH, st.session_state.item_journal)


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Magic Item Journal")
st.caption(
    "Track unidentified magic items found during play. "
    "Record their appearance and where they were found, then mark them identified once the party learns their true nature."
)

if not campaigns:
    no_campaigns_notice()
else:
    for camp in campaigns:
        camp_name = camp["name"]
        header    = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name

        with st.expander(header):
            journal = st.session_state.item_journal.get(camp_name, [])

            # ── Filter ────────────────────────────────────────────────────────
            filter_opts = ["All", "Unidentified", "Identified"]
            status_filter = st.radio(
                "Show",
                filter_opts,
                horizontal=True,
                key=f"jrn_filter_{camp_name}",
            )

            # ── Add new item form ─────────────────────────────────────────────
            st.markdown("#### Add Unidentified Item")
            with st.form(f"add_jrn_{camp_name}", clear_on_submit=True):
                jf1, jf2 = st.columns([2, 2])
                display_name = jf1.text_input("Working name", placeholder="e.g. Glowing Dagger")
                found_in     = jf2.text_input("Found in / session", placeholder="e.g. Session 4, orc chief's lair")
                appearance   = st.text_area(
                    "Appearance / description",
                    placeholder="Describe what the item looks like, any markings, temperature, weight, etc.",
                    height=80,
                )
                notes = st.text_area("Notes", placeholder="Party observations, detect magic aura, etc.", height=60)
                submitted = st.form_submit_button("Add Item")

                if submitted:
                    if display_name.strip():
                        new_item = {
                            "display_name": display_name.strip(),
                            "appearance":   appearance.strip(),
                            "found_in":     found_in.strip(),
                            "identified":   False,
                            "true_name":    "",
                            "properties":   "",
                            "notes":        notes.strip(),
                        }
                        if camp_name not in st.session_state.item_journal:
                            st.session_state.item_journal[camp_name] = []
                        st.session_state.item_journal[camp_name].append(new_item)
                        save_journal()
                        st.success(f"Added: {display_name.strip()}")
                    else:
                        st.error("Working name is required.")

            # ── Item list ─────────────────────────────────────────────────────
            st.markdown("---")

            journal = st.session_state.item_journal.get(camp_name, [])

            # Apply status filter
            if status_filter == "Unidentified":
                visible = [(i, it) for i, it in enumerate(journal) if not it.get("identified")]
            elif status_filter == "Identified":
                visible = [(i, it) for i, it in enumerate(journal) if it.get("identified")]
            else:
                visible = list(enumerate(journal))

            if not visible:
                st.caption("No items to show.")
            else:
                for i, item in visible:
                    badge = "✅ Identified" if item.get("identified") else "🔍 Unidentified"
                    label = f"{badge} — **{item['display_name']}**"
                    if item.get("found_in"):
                        label += f" *(found: {item['found_in']})*"

                    with st.expander(label):
                        # Appearance / notes (always visible)
                        if item.get("appearance"):
                            st.markdown(f"**Appearance:** {item['appearance']}")
                        if item.get("notes"):
                            st.markdown(f"**Notes:** {item['notes']}")

                        # ── Identify section ──────────────────────────────────
                        if not item.get("identified"):
                            st.markdown("#### Identify Item")
                            with st.form(f"identify_{camp_name}_{i}"):
                                id1, id2 = st.columns(2)
                                true_name  = id1.text_input("True name", value=item.get("true_name", ""))
                                properties = id2.text_area("Properties / description", value=item.get("properties", ""), height=80)
                                if st.form_submit_button("Mark as Identified"):
                                    if true_name.strip():
                                        st.session_state.item_journal[camp_name][i]["true_name"]  = true_name.strip()
                                        st.session_state.item_journal[camp_name][i]["properties"] = properties.strip()
                                        st.session_state.item_journal[camp_name][i]["identified"] = True
                                        save_journal()
                                        st.rerun()
                                    else:
                                        st.error("True name is required to identify.")
                        else:
                            # Show identified details
                            if item.get("true_name"):
                                st.success(f"**True Name:** {item['true_name']}")
                            if item.get("properties"):
                                st.markdown(f"**Properties:** {item['properties']}")

                            # Allow re-editing true name and properties
                            with st.form(f"edit_id_{camp_name}_{i}"):
                                e1, e2 = st.columns(2)
                                new_true = e1.text_input("Edit true name", value=item.get("true_name", ""))
                                new_prop = e2.text_area("Edit properties", value=item.get("properties", ""), height=60)
                                eu1, eu2 = st.columns(2)
                                if eu1.form_submit_button("Update"):
                                    st.session_state.item_journal[camp_name][i]["true_name"]  = new_true.strip()
                                    st.session_state.item_journal[camp_name][i]["properties"] = new_prop.strip()
                                    save_journal()
                                    st.success("Updated.")
                                if eu2.form_submit_button("Mark as Unidentified"):
                                    st.session_state.item_journal[camp_name][i]["identified"] = False
                                    save_journal()
                                    st.rerun()

                        # ── Delete ────────────────────────────────────────────
                        del_key = f"jrn_del_{camp_name}_{i}"
                        if del_key not in st.session_state:
                            st.session_state[del_key] = False

                        if not st.session_state[del_key]:
                            if st.button("Delete entry", key=f"jrn_del_btn_{camp_name}_{i}"):
                                st.session_state[del_key] = True
                                st.rerun()
                        else:
                            st.warning("Delete this entry?")
                            dc1, _, dc2 = st.columns([1, 7, 1])
                            if dc1.button("Confirm", key=f"jrn_del_confirm_{camp_name}_{i}"):
                                st.session_state.item_journal[camp_name].pop(i)
                                save_journal()
                                st.session_state[del_key] = False
                                st.rerun()
                            if dc2.button("Cancel", key=f"jrn_del_cancel_{camp_name}_{i}"):
                                st.session_state[del_key] = False
                                st.rerun()

