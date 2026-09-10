import streamlit as st
from utils import load_json, load_json_cached, edition_selector, filter_by_edition, deduplicate_editions, sidebar_exit_button, page_nav
from pathlib import Path


DATA_PATH = Path("data/backgrounds.json")

st.title("Backgrounds")

if not DATA_PATH.exists():
    st.warning("Background data not found. Run `python scripts/download_data.py` to download it.")
    st.stop()


def _backgrounds_same(a, b):
    """Return True only if a background's text is identical across editions.

    Same pattern as Monsters/Races/Spells/Feats: 2024 backgrounds were
    substantially rewritten (feat-granting instead of skill-only, etc.), so
    any difference in desc/sections keeps both entries visible.
    """
    return (
        str(a.get("desc", "")).strip().lower() == str(b.get("desc", "")).strip().lower()
        and {k: str(v).strip().lower() for k, v in a.get("sections", {}).items()}
            == {k: str(v).strip().lower() for k, v in b.get("sections", {}).items()}
    )


backgrounds = load_json_cached(DATA_PATH, [])

# Inline filters — edition radio, then search + source filter
gamesystem = edition_selector(sidebar=False)
bf1, bf2 = st.columns([3, 2])
search = bf1.text_input("Search backgrounds", key="bg_search", placeholder="e.g. Acolyte")
sources = sorted({b.get("source", "") for b in backgrounds if b.get("source")})
source_filter = bf2.multiselect("Source", sources, key="bg_source")

# "All" edition: merge backgrounds that are word-for-word identical across
# 2014/2024 instead of showing every reprint twice.
if gamesystem is None:
    filtered = deduplicate_editions(backgrounds, same_fn=_backgrounds_same)
else:
    filtered = filter_by_edition(backgrounds, gamesystem)

if search:
    sl = search.lower()
    filtered = [b for b in filtered if sl in b.get("name", "").lower() or sl in b.get("desc", "").lower()]
if source_filter:
    filtered = [b for b in filtered if b.get("source", "") in source_filter]

filtered = sorted(filtered, key=lambda b: b.get("name", ""))

# Only render results once the user has searched or applied a source filter
if not (search or source_filter):
    st.info("Search by name or select a source above to see backgrounds.")
    st.stop()

# Paginate at 50/page — page_nav shows the found-count caption and resets to
# page 1 whenever the filter signature changes
filter_sig = (search, tuple(source_filter), gamesystem)
page_slice = page_nav(filtered, "bg_page", "_bg_sig", filter_sig)

for bg in page_slice:
    source = bg.get("source", "")
    with st.expander(f"**{bg['name']}**" + (f"  —  {source}" if source else "")):
        desc = bg.get("desc", "")
        if desc:
            st.markdown(desc)
        sections = bg.get("sections", {})
        for section_name, section_text in sections.items():
            if section_text:
                st.markdown(f"#### {section_name}")
                st.markdown(section_text)

