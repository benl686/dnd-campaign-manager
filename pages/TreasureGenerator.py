import json
import random
import copy
import streamlit as st
from pathlib import Path
from utils import load_json_cached, sidebar_exit_button
from treasure_tables import (
    cr_to_float, cr_float_to_band, cr_float_to_hoard_band,
    format_coins, collapse_dupes, lookup_range,
    roll_hoard_coins, roll_gems, roll_art, roll_jewelry,
    roll_trade_goods, roll_curiosities, pick_magic_item,
    roll_individual_treasure, coins_to_gp, add_coins, loot_section,
    INDIVIDUAL_BY_CR, BAND_MIDPOINTS, HOARD_COINS_BY_CR,
    HOARD_MAGIC_BY_CR, HOARD_AUTO_ROLLS,
    GEMS, ART_OBJECTS, JEWELRY, TRADE_GOODS, CURIOSITIES,
)

SRD_MONSTERS_PATH = Path("data/monsters_srd.json")
MAGICITEMS_PATH   = Path("data/magicitems.json")


@st.cache_data(show_spinner=False)
def _load_monsters(path: str, mtime: float):
    # _name_lower is pre-computed so search filters don't re-lowercase
    # 3,500+ names on every rerun while a query is active.
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for m in data:
        m["_cr_float"] = cr_to_float(m.get("cr", 0))
        m["_name_lower"] = m.get("name", "").lower()
    return data


@st.cache_data(show_spinner=False)
def _load_magic_items(path: str, mtime: float):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ── Session state ─────────────────────────────────────────────────────────────

if "tg_enc_monsters" not in st.session_state:
    st.session_state.tg_enc_monsters = []
if "tg_loot_results" not in st.session_state:
    st.session_state.tg_loot_results = []
if "tg_ind_monsters" not in st.session_state:
    # Default: one starter row for the Individual Monster tab
    st.session_state.tg_ind_monsters = [{"cr_band": list(INDIVIDUAL_BY_CR.keys())[0], "count": 1, "label": ""}]
if "tg_ind_results" not in st.session_state:
    st.session_state.tg_ind_results = []


def _on_tg_count_change(idx: int):
    v = st.session_state.get(f"tg_enc_cnt_{idx}", 1)
    if idx < len(st.session_state.tg_enc_monsters):
        st.session_state.tg_enc_monsters[idx]["count"] = max(1, int(v))


# ── Multi-tier row helper ─────────────────────────────────────────────────────

def _tier_rows(label: str, ss_key: str, tier_options: list, default_rows: list):
    """Render multiple (count, tier) rows for one loot category.

    ss_key         — session-state key holding the list of {'count':int,'tier':int}
    tier_options   — sorted list of valid gp tiers
    default_rows   — list of {'count':int,'tier':int} used when key not yet set
    Returns current list of (count, tier) pairs for use at roll time.
    """
    if ss_key not in st.session_state:
        st.session_state[ss_key] = copy.deepcopy(default_rows)

    rows = st.session_state[ss_key]
    pairs = []
    for i, row in enumerate(rows):
        c1, c2, c3 = st.columns([2, 4, 1])
        cnt = c1.number_input(
            "n", min_value=0, max_value=400, value=row.get("count", 1),
            step=1, label_visibility="collapsed", key=f"{ss_key}_cnt_{i}"
        )
        tier_idx = tier_options.index(row.get("tier", tier_options[0])) if row.get("tier") in tier_options else 0
        tier = c2.selectbox(
            "t", tier_options, index=tier_idx,
            label_visibility="collapsed", key=f"{ss_key}_tier_{i}",
            format_func=lambda v: f"{v:,} gp each"
        )
        if c3.button("✕", key=f"{ss_key}_rm_{i}"):
            _old_len = len(rows)
            rows.pop(i)
            # Every row from i onward shifts down by one index. Clearing only
            # row i's own keys (as before) left every later row still keyed to
            # its old index, so it kept displaying the count/tier that
            # belonged to whoever used to sit there. Clear the whole tail so
            # each shifted row re-initialises from the (now-shifted) row data.
            for k in range(i, _old_len):
                st.session_state.pop(f"{ss_key}_cnt_{k}", None)
                st.session_state.pop(f"{ss_key}_tier_{k}", None)
            st.rerun()
        pairs.append((int(cnt), tier))

    if st.button(f"＋ {label.title()} Tier", key=f"{ss_key}_add"):
        rows.append({"count": 1, "tier": tier_options[len(tier_options)//2]})
        st.rerun()
    return pairs


def _reset_tier_rows(ss_key: str, default_rows: list):
    """Reset tier rows to default and clear widget keys."""
    max_old = len(st.session_state.get(ss_key, []))
    for i in range(max_old):
        st.session_state.pop(f"{ss_key}_cnt_{i}", None)
        st.session_state.pop(f"{ss_key}_tier_{i}", None)
    st.session_state[ss_key] = copy.deepcopy(default_rows)


def _roll_tier_rows(pairs: list, roll_fn) -> list:
    """Execute rolls for all tier-rows and return list of (name, gp) tuples."""
    results = []
    for cnt, tier in pairs:
        if cnt > 0:
            names = roll_fn(tier, int(cnt))
            results.extend((n, tier) for n in names)
    return results


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Treasure Generator")
st.caption("Roll individual monster loot, encounter-based loot, or full hoards.")

magic_items_all = (
    _load_magic_items(str(MAGICITEMS_PATH), MAGICITEMS_PATH.stat().st_mtime)
    if MAGICITEMS_PATH.exists() else []
)

GEM_TIERS  = sorted(GEMS.keys())
ART_TIERS  = sorted(ART_OBJECTS.keys())
JEW_TIERS  = sorted(JEWELRY.keys())
TRD_TIERS  = sorted(TRADE_GOODS.keys())
CUR_TIERS  = sorted(CURIOSITIES.keys())

tab_encounter, tab_individual, tab_hoard, tab_ref = st.tabs([
    "Encounter Loot", "Individual Monster", "Treasure Hoard", "References",
])


# ══════════════════════════════════════════════════════════════════════════════
# ENCOUNTER LOOT — mini encounter builder
# ══════════════════════════════════════════════════════════════════════════════

with tab_encounter:
    st.subheader("Encounter Loot")
    st.caption(
        "Add monsters, then roll. Individual uses each monster's own CR band. "
        "Hoard auto-fills quantities as a baseline you can freely edit."
    )

    if not SRD_MONSTERS_PATH.exists():
        st.warning("Monster data not found. Run `python scripts/download_data.py` first.")
    else:
        monsters_all = _load_monsters(str(SRD_MONSTERS_PATH), SRD_MONSTERS_PATH.stat().st_mtime)

        # Monster search
        search_q = st.text_input(
            "Search monsters by name",
            key="tg_enc_search",
            placeholder="e.g. goblin, dragon… (type 3+ characters)"
        )
        search_active = len(search_q) >= 3
        if search_q and not search_active:
            st.caption("Type at least 3 characters to search (3,500+ monsters).")
        elif search_active:
            _lq = search_q.lower()   # lower once — not once per monster
            all_matches = [m for m in monsters_all if _lq in m["_name_lower"]]
            matches = all_matches[:50]
            if len(all_matches) > 50:
                st.caption(f"Showing 50 of {len(all_matches)} — type more to narrow.")
            if matches:
                chosen_name = st.selectbox("Select monster", [m["name"] for m in matches], key="tg_enc_pick")
                chosen = next(m for m in matches if m["name"] == chosen_name)
                ac1, ac2 = st.columns([1, 4])
                qty = ac1.number_input("Count", min_value=1, value=1, key="tg_enc_qty")
                if ac2.button(f"Add {chosen_name} × {qty}"):
                    existing = next((j for j,e in enumerate(st.session_state.tg_enc_monsters)
                                     if e["name"] == chosen_name), None)
                    if existing is not None:
                        nc = st.session_state.tg_enc_monsters[existing]["count"] + int(qty)
                        st.session_state.tg_enc_monsters[existing]["count"] = nc
                        st.session_state[f"tg_enc_cnt_{existing}"] = nc
                    else:
                        st.session_state.tg_enc_monsters.append({
                            "name": chosen_name, "cr": str(chosen.get("cr","0")),
                            "cr_float": chosen["_cr_float"], "count": int(qty),
                        })
                    st.rerun()
            else:
                st.caption("No monsters found.")

        enc_list = st.session_state.tg_enc_monsters
        if not enc_list:
            st.info("Add monsters above to build your encounter.")
        else:
            hdr = st.columns([3,1,1,1])
            hdr[0].markdown("**Monster**"); hdr[1].markdown("**CR**")
            hdr[2].markdown("**Count**");  hdr[3].markdown("")
            for idx, entry in enumerate(enc_list):
                row = st.columns([3,1,1,1])
                row[0].write(entry["name"]); row[1].write(entry["cr"])
                row[2].number_input("c", min_value=1, value=entry["count"],
                    label_visibility="collapsed", key=f"tg_enc_cnt_{idx}",
                    on_change=_on_tg_count_change, args=(idx,))
                if row[3].button("✕", key=f"tg_enc_rm_{idx}"):
                    _old_len = len(enc_list)
                    enc_list.pop(idx)
                    # Same stale-key issue as the tier-row/individual-monster
                    # removers above: every row from idx onward shifts down by
                    # one index, so their tg_enc_cnt_* keys must be cleared too
                    # or a shifted row would display the previous occupant's count.
                    for k in range(idx, _old_len):
                        st.session_state.pop(f"tg_enc_cnt_{k}", None)
                    st.session_state.tg_loot_results = []
                    st.rerun()

            st.markdown("---")
            loot_mode = st.radio("Loot mode", ["Individual (per monster)", "Hoard (combined pool)"],
                                 horizontal=True, key="tg_loot_mode")

            if loot_mode == "Hoard (combined pool)":
                max_cr     = max(e["cr_float"] for e in enc_list)
                hoard_band = cr_float_to_hoard_band(max_cr)
                auto       = HOARD_AUTO_ROLLS[hoard_band]

                # Roster change → reset tier rows to new auto-fill baseline
                roster_sig = str([(e["name"], e["count"]) for e in enc_list])
                if st.session_state.get("tg_roster_sig") != roster_sig:
                    st.session_state["tg_roster_sig"] = roster_sig
                    for k, rows in [("tg_h_gems", auto["gems"]), ("tg_h_art",  auto["art"]),
                                    ("tg_h_jew",  auto["jewelry"]),("tg_h_trd", auto["trade"]),
                                    ("tg_h_cur",  auto["curs"])]:
                        _reset_tier_rows(k, rows)
                    st.session_state.pop("tg_magic_n", None)

                st.info(f"Auto-filled for **{hoard_band}** (max CR {max_cr:.3g}). Adjust freely.")
                magic_n = st.number_input("Magic item rolls", min_value=0, max_value=10,
                                          value=auto["magic"], step=1, key="tg_magic_n")
                st.markdown("**Gems**");        gem_pairs = _tier_rows("gem",        "tg_h_gems", GEM_TIERS, auto["gems"])
                st.markdown("**Art Objects**"); art_pairs = _tier_rows("art",        "tg_h_art",  ART_TIERS, auto["art"])
                st.markdown("**Jewelry**");     jew_pairs = _tier_rows("jewelry",    "tg_h_jew",  JEW_TIERS, auto["jewelry"])
                st.markdown("**Trade Goods**"); trd_pairs = _tier_rows("trade good", "tg_h_trd",  TRD_TIERS, auto["trade"])
                st.markdown("**Curiosities**"); cur_pairs = _tier_rows("curiosity",  "tg_h_cur",  CUR_TIERS, auto["curs"])

            col1, col2 = st.columns([1, 4])
            if col1.button("Roll Encounter Loot", type="primary"):
                results = []
                if loot_mode == "Individual (per monster)":
                    for entry in enc_list:
                        band = cr_float_to_band(entry["cr_float"])
                        agg  = {"cp":0,"sp":0,"ep":0,"gp":0,"pp":0}
                        gems, arts, jewels, trades, curs = [], [], [], [], []
                        for _ in range(entry["count"]):
                            t = roll_individual_treasure(band, entry["cr_float"])
                            agg = add_coins(agg, t["coins"])
                            gems.extend(t["gems"]); arts.extend(t["arts"])
                            jewels.extend(t["jewels"]); trades.extend(t["trades"])
                            curs.extend(t["curiosities"])
                        results.append({"type":"individual","name":entry["name"],
                            "cr":entry["cr"],"count":entry["count"],"band":band,
                            "coins":agg,"gems":gems,"arts":arts,
                            "jewels":jewels,"trades":trades,"curs":curs})
                else:
                    max_cr     = max(e["cr_float"] for e in enc_list)
                    hoard_band = cr_float_to_hoard_band(max_cr)
                    coins  = roll_hoard_coins(hoard_band)
                    gems   = _roll_tier_rows(gem_pairs, roll_gems)
                    arts   = _roll_tier_rows(art_pairs, roll_art)
                    jewels = _roll_tier_rows(jew_pairs, roll_jewelry)
                    trades = _roll_tier_rows(trd_pairs, roll_trade_goods)
                    curs   = _roll_tier_rows(cur_pairs, roll_curiosities)
                    magic  = []
                    for _ in range(int(magic_n)):
                        r   = random.randint(1,100)
                        rar = lookup_range(HOARD_MAGIC_BY_CR[hoard_band], r)
                        it  = pick_magic_item(rar, magic_items_all)
                        if it: magic.append((it, rar))
                    results.append({"type":"hoard","band":hoard_band,
                        "coins":coins,"gems":gems,"arts":arts,
                        "jewels":jewels,"trades":trades,"curs":curs,"magic":magic})
                st.session_state.tg_loot_results = results
                st.rerun()

            if "tg_clear_pending" not in st.session_state:
                st.session_state.tg_clear_pending = False
            if not st.session_state.tg_clear_pending:
                if col2.button("Clear", key="tg_clear"):
                    st.session_state.tg_clear_pending = True
                    st.rerun()
            else:
                if col2.button("Confirm Clear?", key="tg_clear_confirm", type="primary"):
                    st.session_state.tg_enc_monsters = []
                    st.session_state.tg_loot_results = []
                    st.session_state.tg_clear_pending = False
                    st.rerun()

            # Results
            if st.session_state.tg_loot_results:
                st.markdown("---"); st.markdown("### Results")
                grand    = {"cp":0,"sp":0,"ep":0,"gp":0,"pp":0}
                extra_gp = 0.0
                # Accumulated lists for the Total expander
                total_gems, total_arts, total_jewels = [], [], []
                total_trades, total_curs, total_magic = [], [], []

                for res in st.session_state.tg_loot_results:
                    if res["type"] == "individual":
                        label = f"**{res['name']} ×{res['count']}** — CR {res['cr']} [{res['band']}]"
                    else:
                        label = f"**Hoard** [{res['band']}]"
                    with st.expander(label, expanded=True):
                        st.markdown(f"**Coins:** {format_coins(res['coins'])}")
                        loot_section("Gems",        res["gems"])
                        loot_section("Art Objects", res["arts"])
                        loot_section("Jewelry",     res["jewels"])
                        loot_section("Trade Goods", res["trades"])
                        loot_section("Curiosities", res["curs"], approx=True)
                        if res.get("magic"):
                            st.markdown("**Magic Items:**")
                            for name, rar in res["magic"]: st.success(f"{name} *({rar})*")
                    grand        = add_coins(grand, res["coins"])
                    extra_gp    += sum(v for _,v in res["gems"]+res["arts"]+res["jewels"]+res["trades"]+res["curs"])
                    total_gems   += res["gems"]
                    total_arts   += res["arts"]
                    total_jewels += res["jewels"]
                    total_trades += res["trades"]
                    total_curs   += res["curs"]
                    if res.get("magic"):
                        total_magic += res["magic"]

                # Total expander: only useful when there are multiple result entries
                if len(st.session_state.tg_loot_results) > 1:
                    with st.expander("**Total (All Monsters)**", expanded=False):
                        st.markdown(f"**Coins:** {format_coins(grand)}")
                        loot_section("Gems",        total_gems)
                        loot_section("Art Objects", total_arts)
                        loot_section("Jewelry",     total_jewels)
                        loot_section("Trade Goods", total_trades)
                        loot_section("Curiosities", total_curs, approx=True)
                        if total_magic:
                            st.markdown("**Magic Items:**")
                            for name, rar in total_magic:
                                st.success(f"{name} *({rar})*")

                st.markdown("---")
                lc1, lc2 = st.columns(2)
                lc1.metric("Total Coins", format_coins(grand))
                lc2.metric("≈ Total Value", f"{coins_to_gp(grand)+extra_gp:,.0f} gp")


# ══════════════════════════════════════════════════════════════════════════════
# INDIVIDUAL MONSTER
# One or more monsters at different CR bands; results persist until re-rolled.
# ══════════════════════════════════════════════════════════════════════════════

_IND_CR_OPTIONS = list(INDIVIDUAL_BY_CR.keys())

with tab_individual:
    st.subheader("Individual Monster Treasure")
    st.caption(
        "Add any number of monsters at different CR bands, then roll. "
        "Type 3+ characters in the name field to search SRD monsters and auto-fill the CR band. "
        "CR 0–4 yields coins only; extras scale exponentially above that."
    )

    # Load SRD monsters for name search (shared cache with Encounter Loot tab)
    ind_monsters_all = (
        _load_monsters(str(SRD_MONSTERS_PATH), SRD_MONSTERS_PATH.stat().st_mtime)
        if SRD_MONSTERS_PATH.exists() else []
    )

    ind_list = st.session_state.tg_ind_monsters

    # ── Process pending monster picks before rendering widgets ────────────────
    # Checks all rows for a non-placeholder selectbox value; if found, updates
    # the entry's label and CR band, then reruns so widgets re-render cleanly.
    for idx, entry in enumerate(ind_list):
        pick_key = f"ind_pick_{idx}"
        if st.session_state.get(pick_key, 0) != 0:
            stored = st.session_state.get(f"ind_matches_{idx}", [])
            pick_i = st.session_state[pick_key] - 1  # option 0 is placeholder; real picks start at 1
            if 0 <= pick_i < len(stored):
                m = stored[pick_i]
                entry["label"]   = m["name"]
                entry["cr_band"] = cr_float_to_band(m["_cr_float"])
                # Set widget keys so text_input and selectbox re-render with updated values
                st.session_state[f"ind_search_{idx}"] = m["name"]
                st.session_state[f"ind_cr_{idx}"]     = entry["cr_band"]
            st.session_state.pop(pick_key, None)
            st.session_state.tg_ind_results = []
            st.rerun()

    # Header row
    if ind_list:
        h1, h2, h3, h4 = st.columns([2, 2, 1, 0.4])
        h1.caption("Name / Search (optional)")
        h2.caption("CR Band")
        h3.caption("Count")

    # Editable monster rows
    for idx, entry in enumerate(ind_list):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 0.4])

        search_q = c1.text_input(
            "Name", value=entry.get("label", ""),
            key=f"ind_search_{idx}", label_visibility="collapsed",
            placeholder=f"Monster {idx + 1} or search…"
        )
        entry["label"] = search_q  # keep label in sync with live text input on every render

        cr_idx = _IND_CR_OPTIONS.index(entry["cr_band"]) if entry["cr_band"] in _IND_CR_OPTIONS else 0
        entry["cr_band"] = c2.selectbox(
            "CR Band", _IND_CR_OPTIONS, index=cr_idx,
            key=f"ind_cr_{idx}", label_visibility="collapsed"
        )
        entry["count"] = c3.number_input(
            "Count", min_value=1, max_value=200, value=entry.get("count", 1),
            step=1, key=f"ind_cnt_{idx}", label_visibility="collapsed"
        )
        # Delete button — keep at least one row
        if c4.button("✕", key=f"ind_del_{idx}", disabled=(len(ind_list) == 1)):
            _old_len = len(ind_list)
            ind_list.pop(idx)
            # Every row from idx onward shifts down by one index. Without
            # clearing their keys, each shifted row would keep displaying the
            # name/CR band/count (and stale search-match state) that belonged
            # to whoever used to sit at that index.
            for k in range(idx, _old_len):
                st.session_state.pop(f"ind_search_{k}", None)
                st.session_state.pop(f"ind_cr_{k}", None)
                st.session_state.pop(f"ind_cnt_{k}", None)
                st.session_state.pop(f"ind_matches_{k}", None)
                st.session_state.pop(f"ind_pick_{k}", None)
            st.session_state.tg_ind_results = []
            st.rerun()

        # Monster search results — only shown when 3+ characters are typed
        if ind_monsters_all and len(search_q) >= 3:
            _lq = search_q.lower()
            matches = [m for m in ind_monsters_all if _lq in m["_name_lower"]][:20]
            st.session_state[f"ind_matches_{idx}"] = matches  # stored for pick handler above
            if matches:
                # Index-based selectbox: option 0 = placeholder, 1..N = match results.
                # Using integer indices avoids issues if two monsters share the same name.
                st.selectbox(
                    f"ind_select_{idx}",
                    [0] + list(range(1, len(matches) + 1)),
                    format_func=lambda i, _m=matches: (
                        "— select to auto-fill CR —" if i == 0
                        else f"{_m[i-1]['name']} (CR {_m[i-1].get('cr', '?')})"
                    ),
                    key=f"ind_pick_{idx}",
                    label_visibility="collapsed",
                )
            else:
                st.caption("No monsters found — CR band can be set manually.")
        else:
            st.session_state.pop(f"ind_matches_{idx}", None)

    st.markdown("")
    ba, br, bc = st.columns([1, 1, 1])
    if ba.button("＋ Add Monster", key="ind_add"):
        ind_list.append({"cr_band": _IND_CR_OPTIONS[0], "count": 1, "label": ""})
        st.session_state.tg_ind_results = []
        st.rerun()

    if br.button("Roll Individual Treasure", type="primary", key="ind_roll"):
        results = []
        for i, entry in enumerate(ind_list):
            band   = entry["cr_band"]
            cr_mid = BAND_MIDPOINTS.get(band, 0.0)
            agg    = {"cp":0,"sp":0,"ep":0,"gp":0,"pp":0}
            gems, arts, jewels, trades, curs = [], [], [], [], []
            for _ in range(entry["count"]):
                t = roll_individual_treasure(band, cr_mid)
                agg = add_coins(agg, t["coins"])
                gems.extend(t["gems"]); arts.extend(t["arts"])
                jewels.extend(t["jewels"]); trades.extend(t["trades"])
                curs.extend(t["curiosities"])
            label = entry.get("label", "").strip() or f"Monster {i + 1}"
            results.append({
                "label": label, "cr_band": band, "count": entry["count"],
                "coins": agg, "gems": gems, "arts": arts,
                "jewels": jewels, "trades": trades, "curs": curs,
            })
        st.session_state.tg_ind_results = results
        st.rerun()

    if "ind_clear_pending" not in st.session_state:
        st.session_state.ind_clear_pending = False
    if not st.session_state.ind_clear_pending:
        if bc.button("Clear All", key="ind_clear"):
            st.session_state.ind_clear_pending = True
            st.rerun()
    else:
        if bc.button("Confirm Clear?", key="ind_clear_confirm", type="primary"):
            st.session_state.tg_ind_monsters = [{"cr_band": _IND_CR_OPTIONS[0], "count": 1, "label": ""}]
            st.session_state.tg_ind_results  = []
            st.session_state.ind_clear_pending = False
            st.rerun()

    # ── Display results ───────────────────────────────────────────────────────
    if st.session_state.tg_ind_results:
        st.markdown("---")
        grand    = {"cp":0,"sp":0,"ep":0,"gp":0,"pp":0}
        extra_gp = 0.0
        total_gems, total_arts, total_jewels = [], [], []
        total_trades, total_curs = [], []

        for res in st.session_state.tg_ind_results:
            with st.expander(
                f"**{res['label']} ×{res['count']}** [{res['cr_band']}]",
                expanded=True
            ):
                st.markdown(f"**Coins:** {format_coins(res['coins'])}")
                loot_section("Gems",        res["gems"])
                loot_section("Art Objects", res["arts"])
                loot_section("Jewelry",     res["jewels"])
                loot_section("Trade Goods", res["trades"])
                loot_section("Curiosities", res["curs"], approx=True)
            grand        = add_coins(grand, res["coins"])
            extra_gp    += sum(v for _,v in res["gems"]+res["arts"]+res["jewels"]+res["trades"]+res["curs"])
            total_gems   += res["gems"]
            total_arts   += res["arts"]
            total_jewels += res["jewels"]
            total_trades += res["trades"]
            total_curs   += res["curs"]

        # Total expander: only useful when there are multiple entries
        if len(st.session_state.tg_ind_results) > 1:
            with st.expander("**Total (All Monsters)**", expanded=False):
                st.markdown(f"**Coins:** {format_coins(grand)}")
                loot_section("Gems",        total_gems)
                loot_section("Art Objects", total_arts)
                loot_section("Jewelry",     total_jewels)
                loot_section("Trade Goods", total_trades)
                loot_section("Curiosities", total_curs, approx=True)

        st.markdown("---")
        lc1, lc2 = st.columns(2)
        lc1.metric("Total Coins", format_coins(grand))
        lc2.metric("≈ Total Value", f"{coins_to_gp(grand)+extra_gp:,.0f} gp")


# ══════════════════════════════════════════════════════════════════════════════
# TREASURE HOARD — full manual control with multi-tier rows
# ══════════════════════════════════════════════════════════════════════════════

with tab_hoard:
    st.subheader("Treasure Hoard")
    st.caption(
        "A lair, a vault, or a dungeon level. Add multiple tier rows per category "
        "to mix values — e.g. 5× 100 gp gems + 1× 500 gp gem."
    )

    cr_band_h = st.selectbox("Dungeon / Encounter Level",
                             list(HOARD_COINS_BY_CR.keys()), key="hoard_cr")
    hoard_magic_n = st.number_input("Magic item rolls", min_value=0, max_value=10,
                                    value=2, step=1, key="hoard_magic_n")

    st.markdown("**Gems**");        gem_pairs_h = _tier_rows("gem",        "h_gems", GEM_TIERS, [{"count":2,"tier":100}])
    st.markdown("**Art Objects**"); art_pairs_h = _tier_rows("art",        "h_art",  ART_TIERS, [{"count":1,"tier":250}])
    st.markdown("**Jewelry**");     jew_pairs_h = _tier_rows("jewelry",    "h_jew",  JEW_TIERS, [{"count":1,"tier":250}])
    st.markdown("**Trade Goods**"); trd_pairs_h = _tier_rows("trade good", "h_trd",  TRD_TIERS, [])
    st.markdown("**Curiosities**"); cur_pairs_h = _tier_rows("curiosity",  "h_cur",  CUR_TIERS, [])

    if st.button("Roll Treasure Hoard"):
        coins  = roll_hoard_coins(cr_band_h)
        gems   = _roll_tier_rows(gem_pairs_h, roll_gems)
        arts   = _roll_tier_rows(art_pairs_h, roll_art)
        jewels = _roll_tier_rows(jew_pairs_h, roll_jewelry)
        trades = _roll_tier_rows(trd_pairs_h, roll_trade_goods)
        curs   = _roll_tier_rows(cur_pairs_h, roll_curiosities)

        st.markdown(f"**Coins:** {format_coins(coins)}")
        loot_section("Gems",        gems)
        loot_section("Art Objects", arts)
        loot_section("Jewelry",     jewels)
        loot_section("Trade Goods", trades)
        loot_section("Curiosities", curs, approx=True)

        if hoard_magic_n > 0:
            st.markdown("**Magic Items:**")
            for _ in range(int(hoard_magic_n)):
                r   = random.randint(1,100)
                rar = lookup_range(HOARD_MAGIC_BY_CR[cr_band_h], r)
                it  = pick_magic_item(rar, magic_items_all)
                if it: st.markdown(f"- {it} *({rar})*")

        total_gp = (coins_to_gp(coins)
                    + sum(v for _,v in gems+arts+jewels+trades+curs))
        st.caption(f"Estimated total value: **{total_gp:,.0f} gp**")


# ══════════════════════════════════════════════════════════════════════════════
# REFERENCES
# ══════════════════════════════════════════════════════════════════════════════

with tab_ref:
    st.subheader("References")
    r1, r2, r3, r4, r5 = st.tabs(["Gems", "Art Objects", "Jewelry", "Trade Goods", "Curiosities"])
    with r1:
        for v, items in sorted(GEMS.items()):
            with st.expander(f"{v:,} gp Gems"): st.write(", ".join(items))
    with r2:
        for v, items in sorted(ART_OBJECTS.items()):
            with st.expander(f"{v:,} gp Art Objects"):
                for i in items: st.markdown(f"- {i}")
    with r3:
        for v, items in sorted(JEWELRY.items()):
            with st.expander(f"{v:,} gp Jewelry"):
                for i in items: st.markdown(f"- {i}")
    with r4:
        st.caption("Commodities found on merchants, in warehouses, and on caravan guards.")
        for v, items in sorted(TRADE_GOODS.items()):
            with st.expander(f"{v:,} gp Trade Goods"):
                for i in items: st.markdown(f"- {i}")
    with r5:
        st.caption("Unusual items with no confirmed magical effect — good for hooks and intrigue.")
        for v, items in sorted(CURIOSITIES.items()):
            label = "Worthless (0 gp)" if v == 0 else f"~{v:,} gp"
            with st.expander(f"{label} Curiosities"):
                for i in items: st.markdown(f"- {i}")

