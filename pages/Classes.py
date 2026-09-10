import json
import streamlit as st
from utils import load_json_cached, edition_selector, filter_by_edition, deduplicate_editions, sidebar_exit_button, page_nav
from pathlib import Path


DATA_PATH = Path("data/classes.json")

st.title("Classes & Subclasses")

if not DATA_PATH.exists():
    st.warning("Class data not found. Run `python scripts/download_data.py` to download it.")
    st.stop()


@st.cache_data(show_spinner=False)
def _class_filter_options(path, mtime):
    """Pre-compute sidebar filter options from the classes file.

    Keyed on mtime so the cache busts when the file changes.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    caster_types = sorted({c.get("caster_type", "") for c in data if c.get("caster_type")})
    sources      = sorted({c.get("source", "")      for c in data if c.get("source")})
    return caster_types, sources


def _classes_same(a, b):
    """Return True if a class/subclass has the same feature progression across editions.

    Same pattern as Races: compares the structural (level, name) signature of
    features rather than prose, since feature text is often reworded between
    2014 and 2024 without the underlying feature actually changing. Hit dice
    and saving throws are compared directly since those are simple values.
    """
    a_feats = sorted((f.get("level"), str(f.get("name", "")).lower().strip()) for f in a.get("features", []))
    b_feats = sorted((f.get("level"), str(f.get("name", "")).lower().strip()) for f in b.get("features", []))
    return (
        a_feats == b_feats
        and str(a.get("hit_dice", "")).strip().lower() == str(b.get("hit_dice", "")).strip().lower()
        and str(a.get("saving_throws", "")).strip().lower() == str(b.get("saving_throws", "")).strip().lower()
    )


classes = load_json_cached(DATA_PATH, [])

# Inline filters — edition radio, then search, then view/caster/source
gamesystem = edition_selector(sidebar=False)
search = st.text_input("Search classes", key="cls_search", placeholder="e.g. Fighter")
cf1, cf2, cf3 = st.columns(3)
view = cf1.radio("View", ["Base Classes", "Subclasses", "All"], key="cls_view")
caster_types, sources = _class_filter_options(str(DATA_PATH), DATA_PATH.stat().st_mtime)
caster_filter = cf2.multiselect("Caster Type", caster_types, key="cls_caster")
source_filter = cf3.multiselect("Source", sources, key="cls_source")

# "All" edition: merge classes/subclasses whose feature progression is
# identical across 2014/2024 instead of showing every reprint twice.
if gamesystem is None:
    filtered = deduplicate_editions(classes, same_fn=_classes_same)
else:
    filtered = filter_by_edition(classes, gamesystem)

if view == "Base Classes":
    filtered = [c for c in filtered if not c.get("subclass_of")]
elif view == "Subclasses":
    filtered = [c for c in filtered if c.get("subclass_of")]

if search:
    sl = search.lower()
    filtered = [c for c in filtered if sl in c.get("name", "").lower() or sl in c.get("subclass_of", "").lower()]
if caster_filter:
    filtered = [c for c in filtered if c.get("caster_type", "") in caster_filter]
if source_filter:
    filtered = [c for c in filtered if c.get("source", "") in source_filter]

filtered = sorted(filtered, key=lambda c: (c.get("subclass_of", "") or c.get("name", ""), c.get("name", "")))

# Only render results once the user has searched or applied a non-default filter
_active_filter = search or caster_filter or source_filter or view != "All"
if not _active_filter:
    st.info("Search by name or select a filter above to see classes.")
    st.stop()

# Paginate at 50/page — page_nav shows the found-count caption and resets to
# page 1 whenever the filter signature changes
filter_sig = (search, view, tuple(caster_filter), tuple(source_filter), gamesystem)
page_slice = page_nav(filtered, "cls_page", "_cls_sig", filter_sig)

for cls in page_slice:
    subclass_of = cls.get("subclass_of", "")
    hit_dice = cls.get("hit_dice", "")
    caster = cls.get("caster_type", "")
    source = cls.get("source", "")
    primary = cls.get("primary_abilities", "")
    saves = cls.get("saving_throws", "")

    if subclass_of:
        title = f"**{cls['name']}** *(subclass of {subclass_of})*"
    else:
        title = f"**{cls['name']}**"

    subtitle_parts = []
    if hit_dice:
        subtitle_parts.append(f"Hit Die: {hit_dice}")
    if caster:
        subtitle_parts.append(f"Caster: {caster}")
    if source:
        subtitle_parts.append(source)

    label = title + ("  —  " + "  |  ".join(subtitle_parts) if subtitle_parts else "")

    with st.expander(label):
        if primary:
            st.markdown(f"**Primary Abilities:** {primary}")
        if saves:
            st.markdown(f"**Saving Throw Proficiencies:** {saves}")

        desc = cls.get("desc", "")
        if desc:
            st.markdown(desc)

        features = cls.get("features", [])
        if features:
            st.markdown("#### Class Features")
            features_sorted = sorted(features, key=lambda f: f.get("level", 1))
            for feat in features_sorted:
                level = feat.get("level", "")
                fname = feat.get("name", "")
                fdesc = feat.get("desc", "")
                if fname:
                    level_str = f"Lv{level}: " if level else ""
                    st.markdown(f"**{level_str}{fname}**")
                if fdesc:
                    st.markdown(fdesc)

