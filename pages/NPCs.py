"""
NPCs.py — Individual NPC tracking.

Stores npc_list per campaign in npcs.json.
Priority (1–10) on each NPC determines Entity A ordering in the Relationship Map.
Groups/Alliances and the Relationship Web now live in Factions and RelationshipMap.
"""

import random
import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, confirm_delete, load_campaigns, no_campaigns_notice
from npc_tables import NPC_APPEARANCE, NPC_PERSONALITY, NPC_IDEAL, NPC_BOND, NPC_FLAW
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

NPCS_PATH      = Path("json/npcs.json")

OTHERS_KEY    = "_Others_"
CLIPBOARD_KEY = "clipboard_npc"

IMPORTANCE_OPTIONS = ["Major NPC", "Minor NPC", "Ally", "Enemy", "Neutral / Unknown"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def save_npcs():
    """Write NPC data to disk."""
    save_json(NPCS_PATH, st.session_state.npcs)


def _migrate_camp(data: dict) -> dict:
    """Migrate older NPC schemas to the current {npc_list, legacy_notes} shape.

    v1: {important_npcs: str, minor_npcs: str, relationships: str}
    v2+: {npc_list: [...], legacy_notes: str}   (relationship_web / groups ignored now)
    """
    if "npc_list" not in data:
        legacy = []
        if data.get("important_npcs"):
            legacy.append("=== Important NPCs ===\n" + data["important_npcs"])
        if data.get("minor_npcs"):
            legacy.append("=== Minor NPCs ===\n" + data["minor_npcs"])
        if data.get("relationships"):
            legacy.append("=== Relationships ===\n" + data["relationships"])
        return {
            "npc_list":    [],
            "legacy_notes": "\n\n".join(legacy),
        }
    return data


# ── Data loading ──────────────────────────────────────────────────────────────

campaigns = load_campaigns()
if "npcs" not in st.session_state:
    st.session_state.npcs = load_json(NPCS_PATH, {})


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("NPCs")
st.caption(
    "Track named NPCs, their roles, and notes. "
    "Use the **Relationship Map** page to map connections between NPCs, factions, and faiths."
)

tab_list, tab_gen = st.tabs(["NPC List", "NPC Generator"])

with tab_list:
    if not campaigns:
        no_campaigns_notice()
    else:
        npcs = st.session_state.npcs
        if isinstance(npcs, list):
            npcs = {}

        # Stale delete-confirm cleanup — drop any armed "Confirm?" flag whose NPC
        # index no longer exists for that campaign. Without this, arming delete on
        # NPC index 5 and then deleting an earlier NPC (which shifts everything
        # after it down by one) leaves the flag armed at index 5 — the NPC that
        # shifts into that slot would then show a pre-armed "Confirm?" button and
        # could be deleted with a single click the user never intended.
        # Prefix-strip (not underscore-split) so campaign names containing
        # underscores can't be mis-parsed.
        for camp in campaigns:
            cn      = camp["name"]
            cur_len = len(npcs.get(cn, {}).get("npc_list", [])) if isinstance(npcs.get(cn), dict) else 0
            prefix  = f"npc_del_{cn}_"
            for key in list(st.session_state.keys()):
                if key.startswith(prefix):
                    suffix = key[len(prefix):]
                    if suffix.isdigit() and int(suffix) >= cur_len:
                        del st.session_state[key]

        for camp in campaigns:
            camp_name = camp["name"]
            header    = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name

            with st.expander(header):
                if camp_name not in npcs:
                    npcs[camp_name] = {"npc_list": [], "legacy_notes": ""}
                else:
                    npcs[camp_name] = _migrate_camp(npcs[camp_name])
                st.session_state.npcs = npcs

                camp_data = npcs[camp_name]
                npc_list  = camp_data.get("npc_list", [])

                # ── Clipboard paste bar ───────────────────────────────────────────
                clip = st.session_state.get(CLIPBOARD_KEY)
                if clip:
                    pb1, pb2 = st.columns([4, 1])
                    pb1.info(f"📋 Clipboard: **{clip['label']}**")
                    if pb2.button("Paste Here", key=f"npc_paste_{camp_name}"):
                        st.session_state.npcs[camp_name]["npc_list"].append(dict(clip["record"]))
                        save_npcs()
                        st.success(f"Pasted: {clip['label']}")
                        st.rerun()

                # ── Legacy notes ──────────────────────────────────────────────────
                if camp_data.get("legacy_notes"):
                    with st.expander("Imported Notes (from old format)"):
                        st.caption("Original freeform NPC notes, preserved for reference.")
                        st.text(camp_data["legacy_notes"])


                # ═══════════════════════════════════════════════════════════════
                # SECTION 1 — Add New NPC
                # ═══════════════════════════════════════════════════════════════

                st.markdown("### Add New NPC")
                with st.form(f"add_npc_{camp_name}", clear_on_submit=True):
                    nf1, nf2, nf3, nf4 = st.columns([2, 2, 1.2, 0.8])
                    npc_name   = nf1.text_input("Name", placeholder="e.g. Mira Voss")
                    role       = nf2.text_input("Role / Occupation", placeholder="e.g. merchant, guild master")
                    importance = nf3.selectbox("Type", IMPORTANCE_OPTIONS)
                    priority   = nf4.number_input(
                        "Priority", min_value=1, max_value=10, value=5, step=1,
                        help="Higher priority = Entity A in the Relationship Map when paired with lower-priority entities.",
                    )

                    description = st.text_area(
                        "Appearance / Description",
                        placeholder="Physical appearance, distinguishing features, mannerisms.",
                        height=80,
                    )
                    personality = st.text_area("Personality", placeholder="Ideal, bond, flaw, traits.", height=60)
                    secrets     = st.text_area("Secrets / DM Notes", placeholder="Hidden motivations, secrets.", height=60)
                    extra_notes = st.text_area("Notes", placeholder="Current status, location, plot involvement.", height=60)

                    if st.form_submit_button("Add NPC"):
                        if npc_name.strip():
                            st.session_state.npcs[camp_name]["npc_list"].append({
                                "name":        npc_name.strip(),
                                "role":        role.strip(),
                                "importance":  importance,
                                "priority":    int(priority),
                                "description": description.strip(),
                                "personality": personality.strip(),
                                "secrets":     secrets.strip(),
                                "notes":       extra_notes.strip(),
                            })
                            save_npcs()
                            st.success(f"Added: {npc_name.strip()}")
                        else:
                            st.error("Name is required.")

                st.markdown("---")


                # ═══════════════════════════════════════════════════════════════
                # SECTION 2 — NPC List
                # ═══════════════════════════════════════════════════════════════

                st.markdown("### NPC List")
                npc_list = st.session_state.npcs[camp_name].get("npc_list", [])

                nfl1, nfl2 = st.columns([2, 3])
                npc_search = nfl1.text_input(
                    "Search NPCs", placeholder="Filter by name, role, or notes…",
                    key=f"npc_search_{camp_name}",
                )
                imp_filter = nfl2.radio(
                    "Show", ["All"] + IMPORTANCE_OPTIONS,
                    horizontal=True, key=f"npc_filter_{camp_name}",
                )

                npc_q = npc_search.strip().lower()
                if imp_filter != "All":
                    visible_npcs = [
                        (i, n) for i, n in enumerate(npc_list)
                        if n.get("importance") == imp_filter
                        and (not npc_q or npc_q in n.get("name","").lower()
                             or npc_q in n.get("role","").lower()
                             or npc_q in n.get("notes","").lower())
                    ]
                elif npc_q:
                    visible_npcs = [
                        (i, n) for i, n in enumerate(npc_list)
                        if npc_q in n.get("name","").lower()
                        or npc_q in n.get("role","").lower()
                        or npc_q in n.get("notes","").lower()
                    ]
                else:
                    visible_npcs = list(enumerate(npc_list))

                if not visible_npcs:
                    st.caption("No NPCs to show.")
                else:
                    for ni, npc in visible_npcs:
                        imp   = npc.get("importance", "NPC")
                        pri   = npc.get("priority", 5)
                        label = (
                            f"**{npc['name']}** — {npc.get('role','')} *({imp})* · P{pri}"
                            if npc.get("role")
                            else f"**{npc['name']}** *({imp})* · P{pri}"
                        )

                        with st.expander(label):
                            if npc.get("description"):
                                st.markdown(f"**Appearance:** {npc['description']}")
                            if npc.get("personality"):
                                st.markdown(f"**Personality:** {npc['personality']}")
                            if npc.get("secrets"):
                                st.markdown(f"**Secrets / DM Notes:** {npc['secrets']}")
                            if npc.get("notes"):
                                st.markdown(f"**Notes:** {npc['notes']}")

                            if st.button("Copy", key=f"copy_npc_{camp_name}_{ni}",
                                         help="Copy to clipboard to paste into another campaign"):
                                st.session_state[CLIPBOARD_KEY] = {
                                    "record": npc, "label": npc.get("name", f"NPC {ni+1}"),
                                }
                                st.rerun()

                            with st.form(f"edit_npc_{camp_name}_{ni}"):
                                ef1, ef2, ef3, ef4 = st.columns([2, 2, 1.2, 0.8])
                                new_name = ef1.text_input("Name",              value=npc["name"])
                                new_role = ef2.text_input("Role / Occupation", value=npc.get("role", ""))
                                new_imp  = ef3.selectbox(
                                    "Type", IMPORTANCE_OPTIONS,
                                    index=IMPORTANCE_OPTIONS.index(npc.get("importance", IMPORTANCE_OPTIONS[0]))
                                          if npc.get("importance") in IMPORTANCE_OPTIONS else 0,
                                )
                                new_pri  = ef4.number_input(
                                    "Priority", min_value=1, max_value=10,
                                    value=int(npc.get("priority", 5)), step=1,
                                )
                                new_desc  = st.text_area("Appearance / Description", value=npc.get("description",""), height=70)
                                new_pers  = st.text_area("Personality",              value=npc.get("personality",""), height=60)
                                new_sec   = st.text_area("Secrets / DM Notes",       value=npc.get("secrets",""),     height=60)
                                new_notes = st.text_area("Notes",                     value=npc.get("notes",""),       height=60)

                                es1, es2 = st.columns([4, 1])
                                if es1.form_submit_button("Save Changes"):
                                    st.session_state.npcs[camp_name]["npc_list"][ni] = {
                                        "name":        new_name.strip() or npc["name"],
                                        "role":        new_role.strip(),
                                        "importance":  new_imp,
                                        "priority":    int(new_pri),
                                        "description": new_desc.strip(),
                                        "personality": new_pers.strip(),
                                        "secrets":     new_sec.strip(),
                                        "notes":       new_notes.strip(),
                                    }
                                    save_npcs()
                                    st.success("Saved.")

                                del_key = f"npc_del_{camp_name}_{ni}"
                                if del_key not in st.session_state:
                                    st.session_state[del_key] = False
                                if not st.session_state[del_key]:
                                    if es2.form_submit_button("Delete"):
                                        st.session_state[del_key] = True
                                        st.rerun()
                                else:
                                    if es2.form_submit_button("Confirm?"):
                                        st.session_state.npcs[camp_name]["npc_list"].pop(ni)
                                        save_npcs()
                                        st.session_state[del_key] = False
                                        st.rerun()


    # ── Others Archive ────────────────────────────────────────────────────────────

    others_data     = st.session_state.npcs.get(OTHERS_KEY, {})
    others_npc_list = others_data.get("npc_list", []) if isinstance(others_data, dict) else []
    if others_npc_list:
        with st.expander(f"📦 Others Archive — {len(others_npc_list)} orphaned NPC(s)"):
            st.caption("NPCs kept when their campaign was deleted. Copy them to move to a campaign.")
            for oi, npc in enumerate(others_npc_list):
                imp   = npc.get("importance", "NPC")
                label = f"**{npc['name']}** — {npc.get('role','')} *({imp})*" if npc.get("role") else f"**{npc['name']}** *({imp})*"
                with st.expander(label):
                    if npc.get("description"):
                        st.markdown(f"**Appearance:** {npc['description']}")
                    if npc.get("notes"):
                        st.markdown(f"**Notes:** {npc['notes']}")

                    oc1, oc2 = st.columns(2)
                    if oc1.button("Copy", key=f"others_npc_copy_{oi}"):
                        st.session_state[CLIPBOARD_KEY] = {
                            "record": npc, "label": npc.get("name", f"NPC {oi+1}"),
                        }
                        st.rerun()
                    if confirm_delete(oc2, f"others_npc_del_{oi}", f"others_npc_{oi}"):
                        others_npc_list.pop(oi)
                        st.session_state.npcs[OTHERS_KEY]["npc_list"] = others_npc_list
                        save_npcs()
                        st.rerun()


with tab_gen:
    st.subheader("NPC Generator")
    st.caption("Quick random NPC traits for a new face at the table.")
    if st.button("Generate NPC", key="npc_gen_roll"):
        st.markdown(f"**Appearance:** {random.choice(NPC_APPEARANCE)}")
        st.markdown(f"**Personality:** {random.choice(NPC_PERSONALITY)}")
        st.markdown(f"**Ideal:** {random.choice(NPC_IDEAL)}")
        st.markdown(f"**Bond:** {random.choice(NPC_BOND)}")
        st.markdown(f"**Flaw:** {random.choice(NPC_FLAW)}")
