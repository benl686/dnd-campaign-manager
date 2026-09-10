import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, load_campaigns, no_campaigns_notice
from pathlib import Path

WORLDBUILDING_PATH = Path("json/worldbuilding.json")

# ── Select-box option lists ────────────────────────────────────────────────────

REGION_TYPES = ["Forest", "Mountain", "Desert", "Plains", "Coast", "Swamp",
                "Tundra", "Jungle", "Underground", "Volcanic", "Urban", "Other"]
CITY_TYPES   = ["City", "Town", "Village", "Hamlet", "Outpost", "Fortress",
                "Port", "Capital", "Ruin", "Other"]
NATION_TYPES = ["Kingdom", "Empire", "Republic", "City-State", "Tribe",
                "Confederation", "Theocracy", "Magocracy", "Other"]
LORE_CATS    = ["History", "Legend / Myth", "Prophecy", "Religion", "Faction Lore",
                "Magic / Arcana", "Nature / Ecology", "Other"]
PLANE_TYPES  = ["Material Plane", "Outer Plane", "Inner Plane", "Transitive Plane",
                "Demiplane", "Shadow Realm", "Other"]


# ── Migration ─────────────────────────────────────────────────────────────────

def _migrate(camp_wb: dict) -> dict:
    """Convert the old {locations: str, lore: str} schema to the new list-based schema.

    Called on first load; if the campaign data already has a 'regions' key it is
    already migrated and returned unchanged.
    """
    if "regions" in camp_wb:
        return camp_wb   # already new format

    migrated: dict = {
        "regions": [], "cities": [], "nations": [], "lore": [], "planes": []
    }
    old_locs = (camp_wb.get("locations") or "").strip()
    old_lore = (camp_wb.get("lore") or "").strip()

    if old_locs:
        migrated["regions"].append({
            "name": "Legacy Location Notes", "region_type": "Other",
            "climate": "", "ruler": "", "description": old_locs, "notes": "",
        })
    if old_lore:
        migrated["lore"].append({
            "name": "Legacy Lore Notes", "lore_category": "Other",
            "description": old_lore,
        })
    return migrated


def _blank_camp() -> dict:
    """Return an empty worldbuilding dict for a campaign with no existing data."""
    return {"regions": [], "cities": [], "nations": [], "lore": [], "planes": []}


# ── Delete-confirmation helper ─────────────────────────────────────────────────

def _delete_ui(del_key: str, confirm_fn, cancel_label: str = "✕ Delete") -> bool:
    """Render a two-step delete button.  Returns True on confirmed delete."""
    if st.session_state.get(del_key):
        col_y, _, col_n = st.columns([1, 7, 1])
        if col_y.button("⚠️ Confirm delete", key=f"{del_key}_yes", type="primary"):
            st.session_state.pop(del_key, None)
            confirm_fn()
            return True
        if col_n.button("Cancel", key=f"{del_key}_no"):
            st.session_state.pop(del_key, None)
            st.rerun()
    else:
        if st.button(cancel_label, key=f"{del_key}_btn"):
            st.session_state[del_key] = True
            st.rerun()
    return False


# ── Per-category tab renderers ─────────────────────────────────────────────────

def _tab_regions(camp_name: str, wb: dict):
    """Render the Regions tab for one campaign."""
    entries = wb[camp_name].setdefault("regions", [])

    for idx, e in enumerate(entries):
        pfx = f"wb_{camp_name}_reg_{idx}"
        with st.expander(f"📍 {e.get('name', 'Unnamed')}  —  *{e.get('region_type', '')}*"):
            name = st.text_input("Name", value=e.get("name", ""), key=f"{pfx}_name")
            c1, c2 = st.columns(2)
            rtype = c1.selectbox("Type", REGION_TYPES,
                                 index=_sel_idx(REGION_TYPES, e.get("region_type", "Other")),
                                 key=f"{pfx}_type")
            climate = c2.text_input("Climate", value=e.get("climate", ""),
                                    placeholder="Temperate, arid…", key=f"{pfx}_climate")
            ruler = st.text_input("Ruling faction / power", value=e.get("ruler", ""),
                                  key=f"{pfx}_ruler")
            desc  = st.text_area("Description", value=e.get("description", ""),
                                 height=220, key=f"{pfx}_desc")
            notes = st.text_area("Notes / hooks", value=e.get("notes", ""),
                                 height=100, key=f"{pfx}_notes")

            sa, sb = st.columns(2)
            if sa.button("Save", key=f"{pfx}_save"):
                entries[idx] = {"name": name, "region_type": rtype, "climate": climate,
                                "ruler": ruler, "description": desc, "notes": notes}
                save_json(WORLDBUILDING_PATH, wb)
                st.success("Saved")

            def _del(i=idx):
                entries.pop(i)
                save_json(WORLDBUILDING_PATH, wb)
                st.rerun()

            with sb:
                _delete_ui(f"{pfx}_del", _del)

    st.markdown("##### Add region / land")
    pfx_n = f"wb_{camp_name}_reg_new"
    nn = st.text_input("Name *", placeholder="The Ashwood, etc.", key=f"{pfx_n}_name")
    nc1, nc2 = st.columns(2)
    ntype    = nc1.selectbox("Type", REGION_TYPES, key=f"{pfx_n}_type")
    nclimate = nc2.text_input("Climate", placeholder="e.g. Cold, Tropical", key=f"{pfx_n}_climate")
    nruler   = st.text_input("Ruling faction / power", key=f"{pfx_n}_ruler")
    ndesc    = st.text_area("Description", height=150, key=f"{pfx_n}_desc")
    nnotes   = st.text_area("Notes / hooks", height=80, key=f"{pfx_n}_notes")
    if st.button("+ Add Region", key=f"{pfx_n}_btn"):
        if nn.strip():
            entries.append({"name": nn.strip(), "region_type": ntype, "climate": nclimate,
                            "ruler": nruler, "description": ndesc, "notes": nnotes})
            save_json(WORLDBUILDING_PATH, wb)
            st.rerun()
        else:
            st.error("Name is required")


def _tab_cities(camp_name: str, wb: dict):
    """Render the Cities & Towns tab for one campaign."""
    entries = wb[camp_name].setdefault("cities", [])

    for idx, e in enumerate(entries):
        pfx = f"wb_{camp_name}_city_{idx}"
        with st.expander(f"🏙️ {e.get('name', 'Unnamed')}  —  *{e.get('city_type', '')}*"):
            name = st.text_input("Name", value=e.get("name", ""), key=f"{pfx}_name")
            c1, c2, c3 = st.columns(3)
            ctype = c1.selectbox("Type", CITY_TYPES,
                                 index=_sel_idx(CITY_TYPES, e.get("city_type", "City")),
                                 key=f"{pfx}_type")
            pop   = c2.text_input("Population", value=e.get("population", ""),
                                  placeholder="~12,000", key=f"{pfx}_pop")
            ruler = c3.text_input("Ruler / Mayor", value=e.get("ruler", ""),
                                  key=f"{pfx}_ruler")
            region = st.text_input("Region / Nation (optional)", value=e.get("region", ""),
                                   key=f"{pfx}_region")
            desc   = st.text_area("Description", value=e.get("description", ""),
                                  height=220, key=f"{pfx}_desc")
            notes  = st.text_area("Notes / hooks", value=e.get("notes", ""),
                                  height=100, key=f"{pfx}_notes")

            sa, sb = st.columns(2)
            if sa.button("Save", key=f"{pfx}_save"):
                entries[idx] = {"name": name, "city_type": ctype, "population": pop,
                                "ruler": ruler, "region": region,
                                "description": desc, "notes": notes}
                save_json(WORLDBUILDING_PATH, wb)
                st.success("Saved")

            def _del(i=idx):
                entries.pop(i)
                save_json(WORLDBUILDING_PATH, wb)
                st.rerun()

            with sb:
                _delete_ui(f"{pfx}_del", _del)

    st.markdown("##### Add city / town / settlement")
    pfx_n  = f"wb_{camp_name}_city_new"
    nn     = st.text_input("Name *", placeholder="Ironhaven, etc.", key=f"{pfx_n}_name")
    nc1, nc2, nc3 = st.columns(3)
    ntype  = nc1.selectbox("Type", CITY_TYPES, key=f"{pfx_n}_type")
    npop   = nc2.text_input("Population", placeholder="~5,000", key=f"{pfx_n}_pop")
    nruler = nc3.text_input("Ruler / Mayor", key=f"{pfx_n}_ruler")
    nreg   = st.text_input("Region / Nation", key=f"{pfx_n}_region")
    ndesc  = st.text_area("Description", height=150, key=f"{pfx_n}_desc")
    nnotes = st.text_area("Notes / hooks", height=80, key=f"{pfx_n}_notes")
    if st.button("+ Add City", key=f"{pfx_n}_btn"):
        if nn.strip():
            entries.append({"name": nn.strip(), "city_type": ntype, "population": npop,
                            "ruler": nruler, "region": nreg,
                            "description": ndesc, "notes": nnotes})
            save_json(WORLDBUILDING_PATH, wb)
            st.rerun()
        else:
            st.error("Name is required")


def _tab_nations(camp_name: str, wb: dict):
    """Render the Nations & Kingdoms tab for one campaign."""
    entries = wb[camp_name].setdefault("nations", [])

    for idx, e in enumerate(entries):
        pfx = f"wb_{camp_name}_nat_{idx}"
        with st.expander(f"👑 {e.get('name', 'Unnamed')}  —  *{e.get('nation_type', '')}*"):
            name = st.text_input("Name", value=e.get("name", ""), key=f"{pfx}_name")
            c1, c2 = st.columns(2)
            ntype   = c1.selectbox("Type", NATION_TYPES,
                                   index=_sel_idx(NATION_TYPES, e.get("nation_type", "Kingdom")),
                                   key=f"{pfx}_type")
            capital = c2.text_input("Capital city", value=e.get("capital", ""),
                                    key=f"{pfx}_capital")
            c3, c4 = st.columns(2)
            ruler  = c3.text_input("Ruler / Head of state", value=e.get("ruler", ""),
                                   key=f"{pfx}_ruler")
            govt   = c4.text_input("Government structure", value=e.get("government", ""),
                                   placeholder="Feudal monarchy, council…",
                                   key=f"{pfx}_govt")
            allies = st.text_input("Allies", value=e.get("allies", ""), key=f"{pfx}_allies")
            rivals = st.text_input("Rivals / Enemies", value=e.get("rivals", ""),
                                   key=f"{pfx}_rivals")
            desc   = st.text_area("Description", value=e.get("description", ""),
                                  height=220, key=f"{pfx}_desc")
            notes  = st.text_area("Notes / hooks", value=e.get("notes", ""),
                                  height=100, key=f"{pfx}_notes")

            sa, sb = st.columns(2)
            if sa.button("Save", key=f"{pfx}_save"):
                entries[idx] = {"name": name, "nation_type": ntype, "capital": capital,
                                "ruler": ruler, "government": govt, "allies": allies,
                                "rivals": rivals, "description": desc, "notes": notes}
                save_json(WORLDBUILDING_PATH, wb)
                st.success("Saved")

            def _del(i=idx):
                entries.pop(i)
                save_json(WORLDBUILDING_PATH, wb)
                st.rerun()

            with sb:
                _delete_ui(f"{pfx}_del", _del)

    st.markdown("##### Add nation / kingdom")
    pfx_n   = f"wb_{camp_name}_nat_new"
    nn      = st.text_input("Name *", placeholder="The Iron Dominion, etc.", key=f"{pfx_n}_name")
    nc1, nc2 = st.columns(2)
    ntype   = nc1.selectbox("Type", NATION_TYPES, key=f"{pfx_n}_type")
    ncap    = nc2.text_input("Capital city", key=f"{pfx_n}_capital")
    nc3, nc4 = st.columns(2)
    nruler  = nc3.text_input("Ruler", key=f"{pfx_n}_ruler")
    ngovt   = nc4.text_input("Government structure", key=f"{pfx_n}_govt")
    nallies = st.text_input("Allies", key=f"{pfx_n}_allies")
    nrivals = st.text_input("Rivals / Enemies", key=f"{pfx_n}_rivals")
    ndesc   = st.text_area("Description", height=150, key=f"{pfx_n}_desc")
    nnotes  = st.text_area("Notes / hooks", height=80, key=f"{pfx_n}_notes")
    if st.button("+ Add Nation", key=f"{pfx_n}_btn"):
        if nn.strip():
            entries.append({"name": nn.strip(), "nation_type": ntype, "capital": ncap,
                            "ruler": nruler, "government": ngovt, "allies": nallies,
                            "rivals": nrivals, "description": ndesc, "notes": nnotes})
            save_json(WORLDBUILDING_PATH, wb)
            st.rerun()
        else:
            st.error("Name is required")


def _tab_lore(camp_name: str, wb: dict):
    """Render the Lore & History tab for one campaign."""
    entries = wb[camp_name].setdefault("lore", [])

    for idx, e in enumerate(entries):
        pfx = f"wb_{camp_name}_lore_{idx}"
        with st.expander(f"📜 {e.get('name', 'Unnamed')}  —  *{e.get('lore_category', '')}*"):
            name = st.text_input("Name / Title", value=e.get("name", ""), key=f"{pfx}_name")
            cat  = st.selectbox("Category", LORE_CATS,
                                index=_sel_idx(LORE_CATS, e.get("lore_category", "History")),
                                key=f"{pfx}_cat")
            desc = st.text_area("Description", value=e.get("description", ""),
                                height=300, key=f"{pfx}_desc")

            sa, sb = st.columns(2)
            if sa.button("Save", key=f"{pfx}_save"):
                entries[idx] = {"name": name, "lore_category": cat, "description": desc}
                save_json(WORLDBUILDING_PATH, wb)
                st.success("Saved")

            def _del(i=idx):
                entries.pop(i)
                save_json(WORLDBUILDING_PATH, wb)
                st.rerun()

            with sb:
                _delete_ui(f"{pfx}_del", _del)

    st.markdown("##### Add lore entry")
    pfx_n = f"wb_{camp_name}_lore_new"
    nn    = st.text_input("Name / Title *", placeholder="The Founding War, etc.", key=f"{pfx_n}_name")
    ncat  = st.selectbox("Category", LORE_CATS, key=f"{pfx_n}_cat")
    ndesc = st.text_area("Description", height=200, key=f"{pfx_n}_desc")
    if st.button("+ Add Lore", key=f"{pfx_n}_btn"):
        if nn.strip():
            entries.append({"name": nn.strip(), "lore_category": ncat, "description": ndesc})
            save_json(WORLDBUILDING_PATH, wb)
            st.rerun()
        else:
            st.error("Name is required")


def _tab_planes(camp_name: str, wb: dict):
    """Render the Planes & Cosmology tab for one campaign."""
    entries = wb[camp_name].setdefault("planes", [])

    for idx, e in enumerate(entries):
        pfx = f"wb_{camp_name}_plane_{idx}"
        with st.expander(f"✨ {e.get('name', 'Unnamed')}  —  *{e.get('plane_type', '')}*"):
            name  = st.text_input("Name", value=e.get("name", ""), key=f"{pfx}_name")
            ptype = st.selectbox("Plane type", PLANE_TYPES,
                                 index=_sel_idx(PLANE_TYPES, e.get("plane_type", "Outer Plane")),
                                 key=f"{pfx}_type")
            desc  = st.text_area("Description", value=e.get("description", ""),
                                 height=250, key=f"{pfx}_desc")
            notes = st.text_area("Notes / hooks", value=e.get("notes", ""),
                                 height=100, key=f"{pfx}_notes")

            sa, sb = st.columns(2)
            if sa.button("Save", key=f"{pfx}_save"):
                entries[idx] = {"name": name, "plane_type": ptype,
                                "description": desc, "notes": notes}
                save_json(WORLDBUILDING_PATH, wb)
                st.success("Saved")

            def _del(i=idx):
                entries.pop(i)
                save_json(WORLDBUILDING_PATH, wb)
                st.rerun()

            with sb:
                _delete_ui(f"{pfx}_del", _del)

    st.markdown("##### Add plane / realm")
    pfx_n  = f"wb_{camp_name}_plane_new"
    nn     = st.text_input("Name *", placeholder="The Shadowfell, etc.", key=f"{pfx_n}_name")
    ntype  = st.selectbox("Plane type", PLANE_TYPES, key=f"{pfx_n}_type")
    ndesc  = st.text_area("Description", height=180, key=f"{pfx_n}_desc")
    nnotes = st.text_area("Notes / hooks", height=80, key=f"{pfx_n}_notes")
    if st.button("+ Add Plane", key=f"{pfx_n}_btn"):
        if nn.strip():
            entries.append({"name": nn.strip(), "plane_type": ntype,
                            "description": ndesc, "notes": nnotes})
            save_json(WORLDBUILDING_PATH, wb)
            st.rerun()
        else:
            st.error("Name is required")


# ── Utility ───────────────────────────────────────────────────────────────────

def _sel_idx(options: list, value: str) -> int:
    """Return the index of value in options, or 0 if not found."""
    try:
        return options.index(value)
    except ValueError:
        return 0


# ── Page ──────────────────────────────────────────────────────────────────────

campaigns = load_campaigns()

if "worldbuilding" not in st.session_state:
    st.session_state.worldbuilding = load_json(WORLDBUILDING_PATH, {})

st.title("Worldbuilding")
st.caption("Notes are grouped by campaign. Each tab covers a different part of your world.")

if not campaigns:
    no_campaigns_notice()
else:
    wb = st.session_state.worldbuilding
    if isinstance(wb, list):
        wb = {}

    # Migrate any campaigns still on the old {locations, lore} string schema
    migrated = False
    for camp in campaigns:
        cn = camp["name"]
        raw = wb.get(cn, {})
        new_raw = _migrate(raw)
        if new_raw is not raw:
            wb[cn] = new_raw
            migrated = True
        # Ensure all five category keys exist (safe for partially-migrated data)
        for key in ("regions", "cities", "nations", "lore", "planes"):
            wb[cn].setdefault(key, [])

    if migrated:
        save_json(WORLDBUILDING_PATH, wb)

    # Stale delete-confirm cleanup — drop any armed "{pfx}_del" flag whose entry
    # index no longer exists for that campaign/category, so a shifted-in entry
    # can't inherit a pre-armed delete confirmation from the entry that used to
    # sit at that index. Category → widget-key abbreviation used by the tab
    # renderers above (regions="reg", cities="city", nations="nat", lore="lore",
    # planes="plane").
    _CATEGORY_ABBR = {
        "regions": "reg", "cities": "city", "nations": "nat",
        "lore": "lore", "planes": "plane",
    }
    for camp in campaigns:
        cn = camp["name"]
        for cat, abbr in _CATEGORY_ABBR.items():
            cur_len = len(wb[cn].get(cat, []))
            prefix  = f"wb_{cn}_{abbr}_"
            for key in list(st.session_state.keys()):
                if key.startswith(prefix) and key.endswith("_del"):
                    middle = key[len(prefix):-len("_del")]
                    if middle.isdigit() and int(middle) >= cur_len:
                        del st.session_state[key]

    st.session_state.worldbuilding = wb

    for camp in campaigns:
        camp_name = camp["name"]
        header = (f"{camp_name} ({camp['system']})" if camp.get("system") else camp_name)

        # Compute entry counts for the expander subtitle
        cw = wb[camp_name]
        counts = (f"{len(cw['regions'])}R · {len(cw['cities'])}C · "
                  f"{len(cw['nations'])}N · {len(cw['lore'])}L · {len(cw['planes'])}P")

        with st.expander(f"{header}   —   {counts}"):
            tab_r, tab_c, tab_n, tab_l, tab_p = st.tabs(
                ["🗺️ Regions", "🏙️ Cities", "👑 Nations", "📜 Lore", "✨ Planes"]
            )
            with tab_r:
                _tab_regions(camp_name, wb)
            with tab_c:
                _tab_cities(camp_name, wb)
            with tab_n:
                _tab_nations(camp_name, wb)
            with tab_l:
                _tab_lore(camp_name, wb)
            with tab_p:
                _tab_planes(camp_name, wb)

