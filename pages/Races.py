import re
import streamlit as st
from utils import load_json, load_json_cached, save_json, edition_selector, filter_by_edition, strip_links, edition_label, deduplicate_editions, sidebar_exit_button, confirm_delete, page_nav
from pathlib import Path


SRD_PATH      = Path("data/races_srd.json")
HOMEBREW_PATH = Path("json/homebrew_races.json")

# Used only in the homebrew form — SRD races embed size in trait text, not a structured field
SIZES = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]


def _races_same(a, b):
    """Return True if two race entries are functionally the same across editions.

    Compares the sorted set of trait names.  Speed and size are intentionally
    not compared here because they also live inside trait text and parsing them
    is fragile.  Ability bonuses are excluded because the 2014→2024 shift from
    fixed bonuses to player-chosen bonuses would cause every race to differ on
    that field, making deduplication useless.
    """
    a_traits = sorted(t["name"].lower().strip() for t in a.get("traits", []))
    b_traits = sorted(t["name"].lower().strip() for t in b.get("traits", []))
    return a_traits == b_traits


@st.cache_data(show_spinner=False)
def _filtered_races(path, mtime, gamesystem):
    """Return the edition-filtered/deduplicated race list, cached per gamesystem.

    Same pattern as Monsters/Spells/Items: prevents deduplicate_editions() —
    which sorts every record's trait names to compare edition pairs — from
    re-running on every Streamlit rerun when the edition hasn't changed.
    """
    races = load_json_cached(path, [])
    if gamesystem is None:
        return deduplicate_editions(races, same_fn=_races_same)
    return filter_by_edition(races, gamesystem)


def _compact_size(text):
    """Extract just the size word from a verbose trait string like 'You are Medium.'"""
    for s in ("Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"):
        if s.lower() in text.lower():
            return s
    return text.strip().rstrip(".")


def _compact_speed(text):
    """Extract a concise speed value from verbose trait text."""
    parts = []
    for m in re.finditer(r"(\d+)[\s-]foot|(\d+)\s*feet", text, re.I):
        val = m.group(1) or m.group(2)
        # Determine movement type from surrounding context
        context = text[max(0, m.start() - 30):m.start()].lower()
        if "swim" in context:
            parts.append(f"swim {val} ft.")
        elif "fly" in context or "flight" in context:
            parts.append(f"fly {val} ft.")
        elif "climb" in context:
            parts.append(f"climb {val} ft.")
        elif "burrow" in context:
            parts.append(f"burrow {val} ft.")
        else:
            parts.insert(0, f"{val} ft.")   # walking goes first
    return ", ".join(dict.fromkeys(parts)) or text.strip().rstrip(".")



# Trait names that are pulled out and displayed separately above the traits list,
# so they don't repeat in the bullet points.
_HOISTED_TRAITS = {
    "size", "speed", "age", "alignment", "creature type",
    "ability score increase", "ability score increases", "ability scores",
    "languages",
}


def render_race(r):
    """Render all details of a single race record inside an expander."""
    traits = r.get("traits", [])

    # Build a lookup of trait name → desc for hoisted fields
    trait_by_name = {t["name"].lower(): strip_links(t.get("desc", ""))
                     for t in traits if t.get("name")}

    # ── Summary line: Size · Speed ────────────────────────────────────────────
    summary = []
    size_src  = r.get("size_text") or trait_by_name.get("size", "")
    speed_src = r.get("speed_text") or trait_by_name.get("speed", "")
    if size_src:
        summary.append(f"**Size:** {_compact_size(size_src)}")
    if speed_src:
        summary.append(f"**Speed:** {_compact_speed(speed_src)}")
    if summary:
        st.markdown("  ·  ".join(summary))

    # ── Creature Type ─────────────────────────────────────────────────────────
    ctype = trait_by_name.get("creature type", "")
    if ctype:
        st.markdown(f"**Creature Type:** {ctype}")

    # ── Age ───────────────────────────────────────────────────────────────────
    age = trait_by_name.get("age", "")
    if age:
        st.markdown(f"**Age:** {age}")

    # ── Alignment ─────────────────────────────────────────────────────────────
    align = trait_by_name.get("alignment", "")
    if align:
        st.markdown(f"**Alignment:** {align}")

    # ── Ability Score Increases ───────────────────────────────────────────────
    ability = (r.get("ability_text")
               or trait_by_name.get("ability score increase")
               or trait_by_name.get("ability score increases")
               or trait_by_name.get("ability scores", ""))
    if ability:
        st.markdown(f"**Ability Score Increases:** {ability}")

    # ── General description ───────────────────────────────────────────────────
    if r.get("desc"):
        st.markdown(strip_links(r["desc"]))

    # ── Racial traits — skip any already shown above ──────────────────────────
    body_traits = [t for t in traits if t.get("name", "").lower() not in _HOISTED_TRAITS]
    if body_traits:
        st.markdown("**Racial Traits**")
        for t in body_traits:
            name = t.get("name", "")
            desc = strip_links(t.get("desc", ""))
            if name and desc:
                st.markdown(f"- **{name}.** {desc}")
            elif name:
                st.markdown(f"- **{name}.**")
            elif desc:
                st.markdown(f"- {desc}")

    # ── Languages ─────────────────────────────────────────────────────────────
    lang = r.get("languages_text") or trait_by_name.get("languages", "")
    if lang:
        st.caption(f"Languages: {lang}")


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Race Reference")

tab_srd, tab_homebrew = st.tabs(["SRD Races", "Homebrew Races"])


# ══════════════════════════════════════════════════════════════════════════════
# SRD RACES TAB
# ══════════════════════════════════════════════════════════════════════════════

with tab_srd:
    if not SRD_PATH.exists():
        st.warning("Race data not found. Run `python scripts/download_data.py` to download it.")
    else:
        # Inline filters: edition, name search, source, subrace toggle
        gamesystem    = edition_selector(sidebar=False)
        search        = st.text_input("Search by name", key="race_search",
                                      placeholder="e.g. Elf, Dwarf, Tiefling")

        # Collect unique sources for filter dropdown (from the raw list, pre-dedup)
        all_sources = sorted(set(
            r.get("source", "") for r in load_json_cached(SRD_PATH, []) if r.get("source")
        ))
        rf1, rf2 = st.columns([3, 1])
        selected_sources = rf1.multiselect("Source book", all_sources, key="race_sources")
        show_subraces = rf2.checkbox("Show subraces", value=True, key="race_subraces")

        # Edition dedup/filter is cached — deduplicate_editions() doesn't re-run
        # on every rerun when the edition selector hasn't changed.
        races = _filtered_races(str(SRD_PATH), SRD_PATH.stat().st_mtime, gamesystem)

        # Hide subraces when the checkbox is off
        if not show_subraces:
            races = [r for r in races if not r.get("is_subrace")]

        filtered = races
        if search:
            filtered = [r for r in filtered if search.lower() in r.get("name", "").lower()]
        if selected_sources:
            filtered = [r for r in filtered if r.get("source", "") in selected_sources]
        filtered = sorted(filtered, key=lambda r: r.get("name", ""))

        if search or selected_sources or not show_subraces:
            # Paginate at 50/page — page_nav shows the found-count caption and
            # resets to page 1 whenever the filter signature changes
            filter_sig = (search, tuple(selected_sources), show_subraces, gamesystem)
            page_slice = page_nav(filtered, "race_page", "_race_sig", filter_sig)
            for r in page_slice:
                # Source book takes priority; fall back to edition label for pure SRD entries
                src = r.get("source") or edition_label(r.get("gamesystem_key", ""))
                label = r["name"]
                with st.expander(label + (f"  —  {src}" if src else "")):
                    render_race(r)
        else:
            st.info("Search by name, filter by source book, or uncheck 'Show subraces' to browse races.")


# ══════════════════════════════════════════════════════════════════════════════
# HOMEBREW RACES TAB
# ══════════════════════════════════════════════════════════════════════════════

with tab_homebrew:
    if "homebrew_races" not in st.session_state:
        st.session_state.homebrew_races = load_json(HOMEBREW_PATH, [])

    st.subheader("Add Homebrew Race")
    with st.form("add_homebrew_race"):
        hr1, hr2, hr3 = st.columns([3, 2, 1])
        hr_name  = hr1.text_input("Race Name")
        hr_size  = hr2.selectbox("Size", SIZES, index=SIZES.index("Medium"))
        hr_speed = hr3.number_input("Speed (ft.)", min_value=0, value=30, step=5)

        hr_ab    = st.text_input("Ability Score Increases",
                                 placeholder="e.g. +2 STR, +1 CON")
        hr_langs = st.text_input("Languages",
                                 placeholder="e.g. Common, Elvish")
        hr_traits = st.text_area("Racial Traits", height=120,
                                  placeholder="Describe traits here — e.g.\n\nDarkvision. You can see in dim light within 60 feet as if it were bright light...")
        hr_desc   = st.text_area("Description", height=80)

        if st.form_submit_button("Add Homebrew Race"):
            if hr_name.strip():
                new_race = {
                    "name":            hr_name.strip(),
                    "size":            hr_size,
                    "speed":           f"{hr_speed} ft.",
                    "ability_bonuses": hr_ab.strip(),
                    "languages":       hr_langs.strip(),
                    "traits":          hr_traits.strip(),  # plain text for homebrew
                    "desc":            hr_desc.strip(),
                    "homebrew":        True,
                }
                st.session_state.homebrew_races.append(new_race)
                save_json(HOMEBREW_PATH, st.session_state.homebrew_races)
                st.success(f"Added {hr_name.strip()}")
            else:
                st.error("Name is required.")

    hb_races = st.session_state.homebrew_races
    st.subheader("Your Homebrew Races")
    if not hb_races:
        st.info("No homebrew races yet. Add one above.")
    else:
        for idx, r in enumerate(hb_races):
            with st.expander(f"{r['name']}  —  {r.get('size', '')}"):
                meta = []
                if r.get("size"):
                    meta.append(f"**Size:** {r['size']}")
                if r.get("speed"):
                    meta.append(f"**Speed:** {r['speed']}")
                if meta:
                    st.markdown("  ·  ".join(meta))
                if r.get("ability_bonuses"):
                    st.markdown(f"**Ability Score Increases:** {r['ability_bonuses']}")
                if r.get("languages"):
                    st.markdown(f"**Languages:** {r['languages']}")
                if r.get("traits"):
                    st.markdown("**Racial Traits**")
                    st.markdown(r["traits"])
                if r.get("desc"):
                    st.markdown(r["desc"])

                # Two-step delete confirmation
                dc1, dc2 = st.columns([8, 1])
                if confirm_delete(dc2, f"hbr_delete_{idx}", f"hbr_{idx}"):
                    st.session_state.homebrew_races.pop(idx)
                    save_json(HOMEBREW_PATH, st.session_state.homebrew_races)
                    st.rerun()

