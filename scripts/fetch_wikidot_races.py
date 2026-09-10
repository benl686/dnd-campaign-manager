"""
fetch_wikidot_races.py — Scrape missing race/lineage entries from dnd5e.wikidot.com.

Fetches races listed in MISSING_RACES, normalises them to the same schema used
by download_data.py / normalize_race(), and appends them to data/races_srd.json.
Re-run any time a new race needs to be added; already-present names are skipped.

URL format: https://dnd5e.wikidot.com/lineage:{slug}
"""

import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL  = "https://dnd5e.wikidot.com/lineage:"
RACES_PATH = Path("data/races_srd.json")
DELAY     = 0.6   # seconds between requests


# ── Races to fetch — (display name, wikidot slug) ────────────────────────────
MISSING_RACES = [
    ("Locathah",   "locathah"),
    ("Verdan",     "verdan"),
    ("Grung",      "grung"),
    ("Yuan-ti",    "yuan-ti"),
    ("Astral Elf", "elf-astral"),
    ("Autognome",  "autognome"),
    ("Giff",       "giff"),
    ("Hadozee",    "hadozee"),
    ("Plasmoid",   "plasmoid"),
    ("Thri-kreen", "thri-kreen"),
    ("Kender",     "kender"),
    # Plane Shift (Magic: The Gathering crossover PDFs)
    ("Aetherborn", "aetherborn"),
    ("Aven",       "aven"),
    ("Khenra",     "khenra"),
    ("Kor",        "kor"),
    ("Merfolk",    "merfolk"),
    ("Naga",       "naga"),
    ("Siren",      "siren"),
    ("Vampire",    "vampire"),
]


# ── HTML helpers ─────────────────────────────────────────────────────────────

def strip_tags(s):
    """Remove HTML tags and decode common entities."""
    s = re.sub(r"<[^>]+>", "", s)
    for esc, ch in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                    ("&nbsp;", " "), ("&#160;", " "), ("&apos;", "'"),
                    ("&quot;", '"'), ("&#39;", "'"), ("&rsquo;", "'"),
                    ("&lsquo;", "'"), ("&mdash;", "—"), ("&ndash;", "–")]:
        s = s.replace(esc, ch)
    return " ".join(s.split()).strip()


def parse_race_page(html, display_name, slug):
    """
    Parse a dnd5e.wikidot.com lineage page into our race schema.

    Pages may contain multiple rule-edition sections (2014 original + MotM update).
    We extract the FIRST complete block as the primary entry.

    Returns a dict matching the schema from normalize_race() in download_data.py,
    or None if the page is an error / empty.
    """
    if "page not found" in html.lower() or "does not exist" in html.lower():
        return None

    # Extract the page-content div
    m = re.search(r'id="page-content"[^>]*>(.*?)(?:id="page-options|class="page-info-break)',
                  html, re.DOTALL)
    if not m:
        return None
    block = m.group(1)

    # ── Source ────────────────────────────────────────────────────────────────
    src_m = re.search(r"<p>\s*Source:\s*(.*?)</p>", block, re.DOTALL)
    source = strip_tags(src_m.group(1)) if src_m else ""

    # ── Flavour description (italicised lead paragraph) ──────────────────────
    desc_m = re.search(r"<p>\s*<em><strong>(.*?)</strong></em>\s*</p>", block, re.DOTALL)
    desc = strip_tags(desc_m.group(1)) if desc_m else ""

    # ── Traits — each is a <ul><li><strong>Name.</strong> Desc</li></ul> ─────
    traits = []
    for li in re.finditer(r"<li>(.*?)</li>", block, re.DOTALL):
        raw = li.group(1)
        # Trait name is bolded, optionally also italicised:
        #   old format: <strong>Name.</strong> Desc
        #   new format: <em><strong>Name.</strong></em> Desc
        nm_m = re.match(r"\s*(?:<em>)?<strong>(.*?)</strong>(?:</em>)?\.?\s*(.*)", raw, re.DOTALL)
        if nm_m:
            t_name = strip_tags(nm_m.group(1)).rstrip(".")
            t_desc = strip_tags(nm_m.group(2))
            traits.append({"name": t_name, "desc": t_desc})
        else:
            # Fallback: plain list item (e.g. language bullet)
            plain = strip_tags(raw)
            if plain:
                traits.append({"name": "", "desc": plain})

    # ── Extract key trait values for quick-display fields ────────────────────
    def _trait_desc(name):
        """Return the desc of the first trait matching name (case-insensitive)."""
        nl = name.lower()
        for t in traits:
            if t["name"].lower() == nl:
                return t["desc"]
        return ""

    size_text    = _trait_desc("Size")
    speed_text   = _trait_desc("Speed")
    ability_text = _trait_desc("Ability Score Increase") or _trait_desc("Ability Scores")
    lang_text    = _trait_desc("Languages")

    return {
        "name":           display_name,
        "slug":           f"wikidot_{slug}",
        "gamesystem_key": "5e-2014",
        "desc":           desc,
        "traits":         traits,
        "is_subrace":     False,
        "subrace_of":     "",
        "source":         source,
        "size_text":      size_text,
        "speed_text":     speed_text,
        "ability_text":   ability_text,
        "languages_text": lang_text,
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    races = json.loads(RACES_PATH.read_text(encoding="utf-8"))
    existing = {r["name"].lower() for r in races}

    to_fetch = [(n, s) for n, s in MISSING_RACES if n.lower() not in existing]
    print(f"Already present : {len(existing)} races")
    print(f"To fetch        : {len(to_fetch)}")
    print()

    added = 0
    for display_name, slug in to_fetch:
        url = BASE_URL + slug
        print(f"  Fetching {display_name} ({slug})", end="  ", flush=True)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DND-Manager/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                html = r.read().decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            print(f"ERROR: {e}")
            time.sleep(DELAY)
            continue

        race = parse_race_page(html, display_name, slug)
        if race is None:
            print("NOT FOUND")
        else:
            races.append(race)
            added += 1
            traits_count = len(race["traits"])
            print(f"OK  (source: {race['source'] or 'n/a'}, {traits_count} traits)")

        time.sleep(DELAY)

    if added:
        RACES_PATH.write_text(json.dumps(races, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nDone. Added {added} races. Total: {len(races)}")


if __name__ == "__main__":
    main()
