"""
Factions.py — Campaign factions and multi-entity alliances.

Schema v2 (factions.json):
  {camp_name: {"faction_list": [...], "alliances": [...]}}
  faction: {name, description}
  alliance: {name, priority, members: [{name, type}], notes}

Alliances moved here from NPCs.py. Members can be any mix of
factions, NPCs, or faiths — they appear as groups in the Relationship Map.
The old per-faction alliances/conflicts text fields are removed; use the
Relationship Map page to track those connections instead.
"""

import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, confirm_delete, load_campaigns, no_campaigns_notice
from pathlib import Path


def _mark_dirty(key: str):
    """Mark an edit form as having unsaved changes (on_change callback)."""
    st.session_state[key] = True


FACTIONS_PATH  = Path("json/factions.json")
NPCS_PATH      = Path("json/npcs.json")
FAITHS_PATH    = Path("json/faiths.json")

OTHERS_KEY    = "_Others_"
CLIPBOARD_KEY = "clipboard_faction"

MEMBER_TYPES = ["faction", "npc", "faith"]


# ── Schema migration ──────────────────────────────────────────────────────────

def _migrate_camp(data) -> dict:
    """Upgrade old flat-list schema to {faction_list, alliances} dict.

    v1: [faction, ...]
    v2: {faction_list: [...], alliances: [...]}
    """
    if isinstance(data, list):
        return {"faction_list": data, "alliances": []}
    data.setdefault("faction_list", [])
    data.setdefault("alliances", [])
    return data


# ── Data loading ──────────────────────────────────────────────────────────────

campaigns = load_campaigns()
if "factions" not in st.session_state:
    st.session_state.factions = load_json(FACTIONS_PATH, {})


def _save_factions():
    save_json(FACTIONS_PATH, st.session_state.factions)


@st.cache_data(show_spinner=False)
def _npc_names(camp_name: str, _mtime: float) -> list[str]:
    """NPC names for the campaign. Keyed on npcs.json mtime — busts when NPCs are saved."""
    raw = load_json(NPCS_PATH, {}).get(camp_name, {})
    if isinstance(raw, dict):
        return [n["name"] for n in raw.get("npc_list", [])]
    return []


@st.cache_data(show_spinner=False)
def _faith_names(camp_name: str, _mtime: float) -> list[str]:
    """Faith names for the campaign. Keyed on faiths.json mtime — busts when faiths are saved."""
    faiths = load_json(FAITHS_PATH, {}).get(camp_name, [])
    return [f["name"] for f in faiths if isinstance(f, dict)]


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Factions")
st.caption(
    "Track factions and multi-entity alliances. "
    "Alliances group any mix of factions, NPCs, and faiths — "
    "they appear as cluster nodes in the Relationship Map."
)

if not campaigns:
    no_campaigns_notice()
else:
    factions_by_camp = st.session_state.factions
    if isinstance(factions_by_camp, list):
        factions_by_camp = {}
    st.session_state.factions = factions_by_camp

    # Stale delete-confirm cleanup — drop any armed "Confirm?"/"Delete" flag
    # whose faction or alliance index no longer exists for that campaign, so a
    # shifted-in record can't inherit a pre-armed delete confirmation from
    # whatever record used to sit at that index. Prefix-strip (not
    # underscore-split) so campaign names containing underscores can't be
    # mis-parsed.
    for camp in campaigns:
        cn    = camp["name"]
        raw   = factions_by_camp.get(cn, {})
        cdata = _migrate_camp(raw) if raw else {"faction_list": [], "alliances": []}
        f_len = len(cdata.get("faction_list", []))
        a_len = len(cdata.get("alliances", []))
        f_prefix = f"{cn}_f_delete_pending_"
        a_prefix = f"alliance_del_{cn}_"
        for key in list(st.session_state.keys()):
            if key.startswith(f_prefix):
                suffix = key[len(f_prefix):]
                if suffix.isdigit() and int(suffix) >= f_len:
                    del st.session_state[key]
            elif key.startswith(a_prefix):
                suffix = key[len(a_prefix):]
                if suffix.isdigit() and int(suffix) >= a_len:
                    del st.session_state[key]

    for camp in campaigns:
        camp_name = camp["name"]
        header    = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name

        with st.expander(header):
            # Ensure new schema
            if camp_name not in factions_by_camp:
                factions_by_camp[camp_name] = {"faction_list": [], "alliances": []}
            else:
                factions_by_camp[camp_name] = _migrate_camp(factions_by_camp[camp_name])
            st.session_state.factions = factions_by_camp

            camp_data    = factions_by_camp[camp_name]
            camp_factions = camp_data["faction_list"]
            camp_alliances = camp_data["alliances"]

            # ── Clipboard paste bar ───────────────────────────────────────────
            clip = st.session_state.get(CLIPBOARD_KEY)
            if clip:
                pb1, pb2 = st.columns([4, 1])
                pb1.info(f"📋 Clipboard: **{clip['label']}**")
                if pb2.button("Paste Here", key=f"faction_paste_{camp_name}"):
                    camp_factions.append(dict(clip["record"]))
                    _save_factions()
                    st.success(f"Pasted: {clip['label']}")
                    st.rerun()


            # ═══════════════════════════════════════════════════════════════
            # SECTION 1 — Factions
            # ═══════════════════════════════════════════════════════════════

            st.markdown("### Factions")

            for idx, faction in enumerate(camp_factions):
                with st.expander(f"**{faction.get('name', f'Faction {idx+1}')}**"):
                    dirty_key = f"{camp_name}_f_dirty_{idx}"

                    fc1, fc2 = st.columns([2, 3])
                    name = fc1.text_input(
                        "Faction Name", value=faction.get("name", ""),
                        key=f"{camp_name}_f_name_{idx}",
                        on_change=_mark_dirty, args=(dirty_key,),
                    )
                    desc = fc2.text_area(
                        "Description and Goals", value=faction.get("description", ""),
                        height=100,
                        key=f"{camp_name}_f_desc_{idx}",
                        on_change=_mark_dirty, args=(dirty_key,),
                    )
                    # Alliances/Conflicts text fields removed — use Relationship Map instead.

                    if st.session_state.get(dirty_key):
                        st.caption("⚠ Unsaved changes")

                    if st.button("Copy", key=f"{camp_name}_f_copy_{idx}",
                                 help="Copy this faction to clipboard to paste into another campaign"):
                        st.session_state[CLIPBOARD_KEY] = {
                            "record": faction,
                            "label":  faction.get("name", f"Faction {idx+1}"),
                        }
                        st.rerun()

                    c_save, c_delete = st.columns([7.5, 1])

                    if c_save.button("Save Faction", key=f"{camp_name}_f_save_{idx}"):
                        camp_factions[idx] = {
                            "name":        name.strip() or faction.get("name", f"Faction {idx+1}"),
                            "description": desc,
                        }
                        st.session_state[dirty_key] = False
                        _save_factions()
                        st.success("Faction saved.")

                    if confirm_delete(c_delete, f"{camp_name}_f_delete_pending_{idx}", f"{camp_name}_f_{idx}"):
                        camp_factions.pop(idx)
                        _save_factions()
                        st.warning("Faction deleted.")
                        st.rerun()

            st.markdown("---")

            # ── Add New Faction ───────────────────────────────────────────────
            st.subheader("Add New Faction")
            with st.form(f"add_faction_{camp_name}", clear_on_submit=True):
                af1, af2 = st.columns([2, 3])
                new_name = af1.text_input("Faction Name", placeholder="e.g. The Merchant's Guild")
                new_desc = af2.text_area("Description and Goals", height=80)
                if st.form_submit_button("Add Faction"):
                    if new_name.strip():
                        camp_factions.append({
                            "name":        new_name.strip(),
                            "description": new_desc.strip(),
                        })
                        _save_factions()
                        st.success(f"Added: {new_name.strip()}")
                        st.rerun()
                    else:
                        st.error("Faction name is required.")

            st.markdown("---")


            # ═══════════════════════════════════════════════════════════════
            # SECTION 2 — Alliances
            # ═══════════════════════════════════════════════════════════════

            st.markdown("### Alliances & Groups")
            st.caption(
                "Collect factions, NPCs, faiths, or other alliances into named alliances. "
                "An alliance containing another alliance shows as a nested box inside it on the "
                "Relationship Map. One connection represents the whole group."
            )

            # Build member option lists for this campaign.
            # mtime keys bust the cache when the source files change.
            _npcs_mt   = NPCS_PATH.stat().st_mtime   if NPCS_PATH.exists()   else 0
            _faiths_mt = FAITHS_PATH.stat().st_mtime if FAITHS_PATH.exists() else 0
            faction_names  = [f["name"] for f in camp_factions]
            npc_names      = _npc_names(camp_name, _npcs_mt)
            faith_names    = _faith_names(camp_name, _faiths_mt)
            alliance_names = [a["name"] for a in camp_alliances]

            # Display existing alliances
            if not camp_alliances:
                st.caption("No alliances yet.")
            else:
                for ai, alliance in enumerate(camp_alliances):
                    members     = alliance.get("members", [])
                    member_strs = [f"{m['name']} ({m['type']})" for m in members]
                    al_label    = f"★ **{alliance['name']}** · P{alliance.get('priority', 5)} · {len(members)} member(s)"

                    with st.expander(al_label):
                        if member_strs:
                            st.caption("Members: " + ", ".join(member_strs))
                        if alliance.get("notes"):
                            st.caption(f"↳ {alliance['notes']}")

                        with st.form(f"edit_alliance_{camp_name}_{ai}"):
                            ea1, ea2 = st.columns([3, 1])
                            new_aname = ea1.text_input("Alliance Name", value=alliance["name"])
                            new_apri  = ea2.number_input(
                                "Priority", min_value=1, max_value=10,
                                value=int(alliance.get("priority", 5)), step=1,
                            )
                            new_anotes = st.text_input("Notes", value=alliance.get("notes", ""))

                            # Exclude self from the sub-alliance list to prevent self-nesting
                            other_alliances = [a for a in alliance_names if a != alliance["name"]]
                            st.caption("**Sub-alliance members:**")
                            new_sub_alliances = st.multiselect(
                                "Sub-Alliances", other_alliances,
                                default=[m["name"] for m in members if m.get("type") == "alliance" and m["name"] in other_alliances],
                                key=f"ae_alliances_{camp_name}_{ai}",
                                help="Nested alliances appear as a box-inside-box on the Relationship Map.",
                            )
                            st.caption("**Faction members:**")
                            new_factions = st.multiselect(
                                "Factions", faction_names,
                                default=[m["name"] for m in members if m.get("type") == "faction" and m["name"] in faction_names],
                                key=f"ae_factions_{camp_name}_{ai}",
                            )
                            st.caption("**NPC members:**")
                            new_npcs = st.multiselect(
                                "NPCs", npc_names,
                                default=[m["name"] for m in members if m.get("type") == "npc" and m["name"] in npc_names],
                                key=f"ae_npcs_{camp_name}_{ai}",
                            )
                            st.caption("**Faith members:**")
                            new_faiths = st.multiselect(
                                "Faiths", faith_names,
                                default=[m["name"] for m in members if m.get("type") == "faith" and m["name"] in faith_names],
                                key=f"ae_faiths_{camp_name}_{ai}",
                            )

                            eb1, eb2 = st.columns([4, 1])
                            ad_key = f"alliance_del_{camp_name}_{ai}"
                            if ad_key not in st.session_state:
                                st.session_state[ad_key] = False

                            if eb1.form_submit_button("Save"):
                                new_members = (
                                    [{"name": n, "type": "alliance"} for n in new_sub_alliances]
                                    + [{"name": n, "type": "faction"} for n in new_factions]
                                    + [{"name": n, "type": "npc"}     for n in new_npcs]
                                    + [{"name": n, "type": "faith"}   for n in new_faiths]
                                )
                                camp_alliances[ai] = {
                                    "name":     new_aname.strip() or alliance["name"],
                                    "priority": int(new_apri),
                                    "members":  new_members,
                                    "notes":    new_anotes.strip(),
                                }
                                _save_factions()
                                st.rerun()

                            if not st.session_state[ad_key]:
                                if eb2.form_submit_button("Delete"):
                                    st.session_state[ad_key] = True
                                    st.rerun()
                            else:
                                if eb2.form_submit_button("Confirm?"):
                                    camp_alliances.pop(ai)
                                    _save_factions()
                                    st.session_state[ad_key] = False
                                    st.rerun()

            # ── Create New Alliance ───────────────────────────────────────────
            st.markdown("**Create New Alliance**")
            with st.form(f"add_alliance_{camp_name}", clear_on_submit=True):
                na1, na2 = st.columns([3, 1])
                new_aname  = na1.text_input("Alliance Name", placeholder="e.g. The Grand Coalition")
                new_apri   = na2.number_input("Priority", min_value=1, max_value=10, value=5, step=1)
                new_anotes = st.text_input("Notes (optional)", placeholder="Shared goal, origin, etc.")

                st.caption("**Add sub-alliance members:**")
                sel_alliances = st.multiselect(
                    "Sub-Alliances", alliance_names,
                    key=f"na_alliances_{camp_name}",
                    help="Nested alliances appear as a box-inside-box on the Relationship Map.",
                )
                st.caption("**Add faction members:**")
                sel_factions = st.multiselect("Factions", faction_names, key=f"na_factions_{camp_name}")
                st.caption("**Add NPC members:**")
                sel_npcs     = st.multiselect("NPCs", npc_names,         key=f"na_npcs_{camp_name}")
                st.caption("**Add faith members:**")
                sel_faiths   = st.multiselect("Faiths", faith_names,     key=f"na_faiths_{camp_name}")

                if st.form_submit_button("Create Alliance"):
                    if new_aname.strip():
                        new_members = (
                            [{"name": n, "type": "alliance"} for n in sel_alliances]
                            + [{"name": n, "type": "faction"} for n in sel_factions]
                            + [{"name": n, "type": "npc"}     for n in sel_npcs]
                            + [{"name": n, "type": "faith"}   for n in sel_faiths]
                        )
                        camp_alliances.append({
                            "name":     new_aname.strip(),
                            "priority": int(new_apri),
                            "members":  new_members,
                            "notes":    new_anotes.strip(),
                        })
                        _save_factions()
                        st.rerun()
                    else:
                        st.error("Alliance name is required.")


# ── Others Archive ────────────────────────────────────────────────────────────

_factions_ss = st.session_state.factions if isinstance(st.session_state.factions, dict) else {}
others_raw   = _factions_ss.get(OTHERS_KEY, [])
# Others archive may still be old flat-list format
others_factions = others_raw if isinstance(others_raw, list) else others_raw.get("faction_list", [])

if others_factions:
    with st.expander(f"📦 Others Archive — {len(others_factions)} orphaned faction(s)"):
        st.caption("Factions kept when their campaign was deleted. Copy them to move to a campaign.")
        for oi, faction in enumerate(others_factions):
            with st.expander(faction.get("name", f"Faction {oi+1}")):
                if faction.get("description"):
                    st.markdown(f"**Description:** {faction['description']}")

                oc1, oc2 = st.columns(2)
                if oc1.button("Copy", key=f"others_f_copy_{oi}",
                               help="Copy to clipboard, then paste into a campaign"):
                    st.session_state[CLIPBOARD_KEY] = {
                        "record": faction,
                        "label":  faction.get("name", f"Faction {oi+1}"),
                    }
                    st.rerun()

                if confirm_delete(oc2, f"others_f_del_{oi}", f"others_f_{oi}"):
                    others_factions.pop(oi)
                    if isinstance(others_raw, list):
                        _factions_ss[OTHERS_KEY] = others_factions
                    else:
                        _factions_ss[OTHERS_KEY]["faction_list"] = others_factions
                    st.session_state.factions = _factions_ss
                    save_json(FACTIONS_PATH, _factions_ss)
                    st.rerun()
