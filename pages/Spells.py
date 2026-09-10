import re
import json
import streamlit as st
from utils import load_json, load_json_cached, save_json, edition_selector, filter_by_edition, strip_links, edition_label, deduplicate_editions, sidebar_exit_button, confirm_delete, page_nav
from random_tables import render_wild_magic
from pathlib import Path


SRD_PATH = Path("data/spells_srd.json")
HOMEBREW_PATH = Path("json/homebrew_spells.json")


def _normalize_spell(s):
    """Fix minor formatting bugs in SRD data before display.

    Applies to every spell record regardless of edition so the UI is consistent:
      • '1minute' → '1 minute'  (missing space in casting_time)
      • '8 hour'  → '8 hours'   (missing plural in duration, only when count > 1)
    Returns a shallow copy so the cached source data is not mutated.
    """
    s = dict(s)
    ct = s.get("casting_time", "")
    if ct:
        # Insert a space between any digit and letter that are directly adjacent
        s["casting_time"] = re.sub(r'(\d)([A-Za-z])', r'\1 \2', ct)
    dur = s.get("duration", "")
    if dur:
        def _pluralize(m):
            # '1 hour' is singular and correct; '8 hour' should be '8 hours'
            return m.group(0) if m.group(1) == "1" else f'{m.group(1)} {m.group(2)}s'
        s["duration"] = re.sub(r'\b(\d+) (minute|hour|day|round|year)(?!s)\b', _pluralize, dur)
    return s


def _spells_same(a, b):
    """Return True if two spell entries are mechanically equivalent across editions.

    Cosmetic differences that are intentionally ignored:
      • School name (e.g. Acid Splash: Conjuration → Evocation)
      • Parenthetical material component descriptions (wording changed between editions)
      • Capitalisation and trailing punctuation in component text
      • Spacing in casting_time/duration (e.g. '1minute' vs '1 minute')
      • Singular vs plural duration units ('8 hour' vs '8 hours')

    Functional differences that keep the entries separate:
      • Level, range (targeting distance), concentration, ritual flag
      • Duration value (e.g. '1 hour' vs '8 hours' after normalisation)
      • Casting time value (e.g. '1 action' vs '1 bonus action')
    """
    def _norm(field, val):
        v = str(val).lower().strip()
        if field == "components":
            # Only compare V/S/M flags — strip the material description in parentheses
            v = re.sub(r'\s*\(.*?\)', '', v).strip()
        elif field in ("casting_time", "duration"):
            # Collapse internal whitespace and strip trailing plural 's'
            # so '1minute'/'1 minute' and '8 hour'/'8 hours' compare equal
            v = re.sub(r'\s+', '', v).rstrip('s')
        return v

    for f in ("level", "casting_time", "range", "components", "duration", "concentration", "ritual"):
        if _norm(f, a.get(f, "")) != _norm(f, b.get(f, "")):
            return False
    return True

SCHOOLS  = ["Abjuration", "Conjuration", "Divination", "Enchantment", "Evocation", "Illusion", "Necromancy", "Transmutation"]
CLASSES  = ["Artificer", "Bard", "Cleric", "Druid", "Paladin", "Ranger", "Sorcerer", "Warlock", "Wizard"]


@st.cache_data(show_spinner=False)
def _load_normalized_spells(path, mtime):
    """Load spells and apply formatting normalisations, cached per file version.

    Combines the file read and _normalize_spell pass into one cached step so the
    ~7,000-spell list comprehension only runs when the file changes on disk,
    not on every Streamlit rerender.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [_normalize_spell(s) for s in data]


@st.cache_data(show_spinner=False)
def _filtered_spells(path, mtime, gamesystem):
    """Return the edition-filtered/deduplicated spell list, cached per gamesystem.

    Prevents deduplicate_editions() from re-running on every rerender when the
    user hasn't changed the edition selector.
    """
    spells = _load_normalized_spells(path, mtime)
    if gamesystem is None:
        return deduplicate_editions(spells, same_fn=_spells_same)
    return filter_by_edition(spells, gamesystem)

# Common options for homebrew spell creation; "Other (custom)" triggers a free-text field
CASTING_TIMES = [
    "1 action", "1 bonus action", "1 reaction", "1 minute", "10 minutes",
    "1 hour", "8 hours", "24 hours", "Other (custom)",
]
SPELL_RANGES = [
    "Self", "Touch", "5 feet", "10 feet", "30 feet", "60 feet", "90 feet",
    "120 feet", "150 feet", "300 feet", "500 feet", "1 mile", "Sight",
    "Unlimited", "Other (custom)",
]
DURATIONS = [
    "Instantaneous", "1 round", "1 minute", "10 minutes", "1 hour",
    "8 hours", "24 hours", "Until dispelled", "Special", "Other (custom)",
]

def render_spell(s):
    level_text = s.get("level_text", str(s.get("level", 0)))
    school = s.get("school", "")
    header = f"*{level_text} {school}*" if level_text and school else ""
    if header:
        st.markdown(header)
    cols = st.columns(4)
    cols[0].markdown(f"**Casting Time:** {s.get('casting_time', '—')}")
    cols[1].markdown(f"**Range:** {s.get('range', '—')}")
    cols[2].markdown(f"**Components:** {s.get('components', '—')}")
    cols[3].markdown(f"**Duration:** {s.get('duration', '—')}")
    if s.get("concentration"):
        st.warning("⚡ Concentration")
    if s.get("ritual"):
        st.info("🔁 Ritual")
    if s.get("material"):
        st.markdown(f"**Material:** {strip_links(s.get('material', ''))}")
    st.markdown(strip_links(s.get("desc", "")))
    hl = s.get("higher_level", "")
    if hl:
        st.markdown(f"**At Higher Levels:** {strip_links(hl)}")
    classes_str = s.get("classes", "")
    if classes_str:
        st.caption(f"Classes: {classes_str}")


st.title("Spell Reference")

tab_srd, tab_homebrew, tab_wild = st.tabs(["SRD Spells", "Homebrew Spells", "Wild Magic"])

with tab_srd:
    if not SRD_PATH.exists():
        st.warning("SRD data not found. Run `python scripts/download_data.py` to download it.")
    else:
        # _filtered_spells caches: file read + _normalize_spell + edition dedup/filter.
        # None of these steps re-run on reruns unless the file or edition changes.
        gamesystem = edition_selector(sidebar=False)
        spells = _filtered_spells(str(SRD_PATH), SRD_PATH.stat().st_mtime, gamesystem)

        # Inline filters
        search = st.text_input("Search by name", key="spell_search", placeholder="e.g. Fireball")
        sf1, sf2, sf3 = st.columns(3)
        level_filter  = sf1.multiselect("Level", list(range(10)), format_func=lambda x: "Cantrip" if x == 0 else f"Level {x}", key="spell_level")
        school_filter = sf2.multiselect("School", SCHOOLS, key="spell_school")
        class_filter  = sf3.multiselect("Class", CLASSES, key="spell_class")

        filtered = spells
        if search:
            _sq = search.lower()   # pre-lower once — avoids repeated .lower() per spell
            filtered = [s for s in filtered if _sq in s.get("name", "").lower()]
        if level_filter:
            filtered = [s for s in filtered if s.get("level", 0) in level_filter]
        if school_filter:
            filtered = [s for s in filtered if s.get("school", "").title() in school_filter]
        if class_filter:
            cf_lower = [c.lower() for c in class_filter]
            filtered = [s for s in filtered if any(c in s.get("classes", "").lower() for c in cf_lower)]
        filtered = sorted(filtered, key=lambda s: (s.get("level", 0), s.get("name", "")))

        # Only render results once the user has entered a search term or applied a filter
        if search or level_filter or school_filter or class_filter:
            # Paginate at 50/page — page_nav shows the found-count caption and
            # resets to page 1 whenever the filter signature changes
            filter_sig = (search, tuple(level_filter), tuple(school_filter),
                          tuple(class_filter), gamesystem)
            page_slice = page_nav(filtered, "spell_page", "_spell_sig", filter_sig)
            for s in page_slice:
                level = s.get("level", 0)
                level_label = "Cantrip" if level == 0 else f"Lv{level}"
                src = edition_label(s.get("gamesystem_key", ""))
                with st.expander(
                    f"{s['name']}  —  {level_label}  |  {s.get('school', '').title()}"
                    + (f"  —  {src}" if src else "")
                ):
                    render_spell(s)
        else:
            st.info("Search by name or select a filter above to see spells.")


with tab_homebrew:
    if "homebrew_spells" not in st.session_state:
        st.session_state.homebrew_spells = load_json(HOMEBREW_PATH, [])

    st.subheader("Add Homebrew Spell")
    with st.form("add_homebrew_spell"):
        hs_name = st.text_input("Spell Name")
        hc1, hc2 = st.columns(2)
        hs_level = hc1.selectbox("Level", list(range(10)), format_func=lambda x: "Cantrip" if x == 0 else f"Level {x}")
        hs_school = hc2.selectbox("School", SCHOOLS)

        hd1, hd2, hd3, hd4 = st.columns(4)
        hs_casting_sel  = hd1.selectbox("Casting Time", CASTING_TIMES)
        hs_range_sel    = hd2.selectbox("Range", SPELL_RANGES, index=SPELL_RANGES.index("60 feet"))
        hs_components   = hd3.text_input("Components", value="V, S")
        hs_duration_sel = hd4.selectbox("Duration", DURATIONS)

        # Custom free-text fields — only used when "Other (custom)" is chosen in the selectbox above
        hdc1, hdc2, _, hdc4 = st.columns(4)
        hs_casting_custom  = hdc1.text_input("Custom casting time",
                                              placeholder="e.g. 1 reaction when…",
                                              label_visibility="collapsed", key="hs_cast_c")
        hs_range_custom    = hdc2.text_input("Custom range",
                                              placeholder="e.g. Special",
                                              label_visibility="collapsed", key="hs_range_c")
        hs_duration_custom = hdc4.text_input("Custom duration",
                                              placeholder="e.g. Until dawn",
                                              label_visibility="collapsed", key="hs_dur_c")

        hs_casting  = (hs_casting_custom.strip()  or hs_casting_sel)  if hs_casting_sel  == "Other (custom)" else hs_casting_sel
        hs_range    = (hs_range_custom.strip()    or hs_range_sel)    if hs_range_sel    == "Other (custom)" else hs_range_sel
        hs_duration = (hs_duration_custom.strip() or hs_duration_sel) if hs_duration_sel == "Other (custom)" else hs_duration_sel

        he1, he2 = st.columns(2)
        hs_conc = he1.checkbox("Concentration")
        hs_ritual = he2.checkbox("Ritual")
        hs_material = st.text_input("Material components (if any)")
        hs_classes_sel = st.multiselect("Classes", CLASSES)
        hs_classes = ", ".join(hs_classes_sel)
        hs_desc = st.text_area("Description", height=200)
        hs_higher = st.text_area("At Higher Levels", height=80)

        if st.form_submit_button("Add Homebrew Spell"):
            if hs_name.strip():
                new_spell = {
                    "name": hs_name.strip(), "level": hs_level,
                    "level_text": "Cantrip" if hs_level == 0 else f"{hs_level}{'st' if hs_level==1 else 'nd' if hs_level==2 else 'rd' if hs_level==3 else 'th'}-level",
                    "school": hs_school, "casting_time": hs_casting, "range": hs_range,
                    "components": hs_components, "duration": hs_duration,
                    "concentration": "yes" if hs_conc else "",
                    "ritual": "yes" if hs_ritual else "",
                    "material": hs_material.strip(),
                    "classes": hs_classes.strip(),
                    "desc": hs_desc, "higher_level": hs_higher, "homebrew": True,
                }
                st.session_state.homebrew_spells.append(new_spell)
                save_json(HOMEBREW_PATH, st.session_state.homebrew_spells)
                st.success(f"Added {hs_name.strip()}")
            else:
                st.error("Name is required")

    hb_spells = st.session_state.homebrew_spells
    st.subheader("Your Homebrew Spells")
    if not hb_spells:
        st.info("No homebrew spells yet. Add one above.")
    else:
        for i, s in enumerate(hb_spells):
            level = s.get("level", 0)
            level_label = "Cantrip" if level == 0 else f"Lv{level}"
            with st.expander(f"{s['name']}  —  {level_label}  |  {s.get('school', '')}"):
                render_spell(s)
                dc1, dc2 = st.columns([8, 1])
                if confirm_delete(dc2, f"hbs_delete_{i}", f"hbs_{i}"):
                    st.session_state.homebrew_spells.pop(i)
                    save_json(HOMEBREW_PATH, st.session_state.homebrew_spells)
                    st.rerun()


# ── Wild Magic Surge tab ──────────────────────────────────────────────────────
# Table data + renderer live in random_tables.py (shared with Combat page).

with tab_wild:
    st.subheader("Wild Magic Surge")
    render_wild_magic("spells")

