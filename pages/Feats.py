import json
import streamlit as st
from utils import load_json_cached, edition_selector, filter_by_edition, deduplicate_editions, sidebar_exit_button, page_nav
from pathlib import Path


DATA_PATH = Path("data/feats.json")

st.title("Feats")

if not DATA_PATH.exists():
    st.warning("Feat data not found. Run `python scripts/download_data.py` to download it.")
    st.stop()


@st.cache_data(show_spinner=False)
def _feat_filter_options(path, mtime):
    """Pre-compute sidebar filter options from the feats file.

    Keyed on mtime so the cache busts when the file changes.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return sorted({f.get("type", "GENERAL") for f in data if f.get("type")})


def _feats_same(a, b):
    """Return True only if a feat's rules text is identical across editions.

    Same pattern as Monsters/Races/Spells: many feats (e.g. Grappler) were
    substantially rewritten between 2014 and 2024, so any wording difference
    in the actual rules text keeps both entries visible for comparison.
    """
    return (
        str(a.get("desc", "")).strip().lower() == str(b.get("desc", "")).strip().lower()
        and str(a.get("benefits", "")).strip().lower() == str(b.get("benefits", "")).strip().lower()
        and str(a.get("prerequisite", "")).strip().lower() == str(b.get("prerequisite", "")).strip().lower()
    )


feats = load_json_cached(DATA_PATH, [])

# Inline filters — edition radio, then search + type + prereq
gamesystem = edition_selector(sidebar=False)
search = st.text_input("Search by name or description", key="feat_search", placeholder="e.g. Alert")
ff1, ff2, ff3 = st.columns(3)
feat_types  = _feat_filter_options(str(DATA_PATH), DATA_PATH.stat().st_mtime)
type_filter = ff1.multiselect("Type", feat_types, key="feat_type")
prereq_filter = ff2.radio("Prerequisite", ["All", "Has prerequisite", "No prerequisite"], key="feat_prereq")

# "All" edition: merge feats that are word-for-word identical across 2014/2024
# instead of showing every reprint twice (per-edition views skip this — they
# only ever contain one edition's copy in the first place).
if gamesystem is None:
    filtered = deduplicate_editions(feats, same_fn=_feats_same)
else:
    filtered = filter_by_edition(feats, gamesystem)

if search:
    sl = search.lower()
    filtered = [f for f in filtered if sl in f.get("name", "").lower() or sl in f.get("desc", "").lower() or sl in f.get("benefits", "").lower()]
if type_filter:
    filtered = [f for f in filtered if f.get("type", "GENERAL") in type_filter]
if prereq_filter == "Has prerequisite":
    filtered = [f for f in filtered if f.get("has_prerequisite")]
elif prereq_filter == "No prerequisite":
    filtered = [f for f in filtered if not f.get("has_prerequisite")]

filtered = sorted(filtered, key=lambda f: f.get("name", ""))

# Only render results once the user has searched or applied a non-default filter
if not (search or type_filter or prereq_filter != "All"):
    st.info("Search by name or select a filter above to see feats.")
    st.stop()

# Paginate at 50/page — page_nav shows the found-count caption and resets to
# page 1 whenever the filter signature changes
filter_sig = (search, tuple(type_filter), prereq_filter, gamesystem)
page_slice = page_nav(filtered, "feat_page", "_feat_sig", filter_sig)

for feat in page_slice:
    prereq = feat.get("prerequisite", "")
    source = feat.get("source", "")
    subtitle_parts = []
    if prereq:
        subtitle_parts.append(f"Requires: {prereq}")
    if source:
        subtitle_parts.append(source)
    subtitle = "  |  ".join(subtitle_parts)

    with st.expander(f"**{feat['name']}**" + (f"  —  {subtitle}" if subtitle else "")):
        desc = feat.get("desc", "")
        if desc:
            st.markdown(desc)
        benefits = feat.get("benefits", "")
        if benefits:
            st.markdown(benefits)

