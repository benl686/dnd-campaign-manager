"""
One-time script to download SRD/open data from the Open5e v2 API into local JSON files.
Run with: python scripts/download_data.py

Produces:
  data/monsters_srd.json   — 3,500+ monsters
  data/spells_srd.json     — 1,900+ spells
  data/items_srd.json      — equipment items
  data/magicitems.json     — 2,300+ magic items (used by Items page)
  data/feats.json          — feats
  data/backgrounds.json    — backgrounds
  data/classes.json        — classes and subclasses
"""

import json
import re
import urllib.request
from pathlib import Path

BASE = "https://api.open5e.com/v2"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def fetch_all(endpoint, extra_params=""):
    results = []
    url = f"{BASE}{endpoint}?limit=100{extra_params}"
    while url:
        print(f"  Fetching {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "DND-Manager/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            page = json.loads(r.read())
        results.extend(page.get("results", []))
        url = page.get("next")
    return results


def _str(val, fallback=""):
    if val is None:
        return fallback
    if isinstance(val, dict):
        return val.get("name", fallback) or val.get("as_string", fallback)
    return str(val)


def _gamesystem_key(record):
    try:
        return record["document"]["gamesystem"]["key"]
    except (KeyError, TypeError):
        return ""


def _speed_str(speed):
    if not speed:
        return ""
    if isinstance(speed, str):
        return speed
    parts = []
    for key in ("walk", "fly", "swim", "burrow", "climb"):
        v = speed.get(key, 0)
        if v:
            parts.append(f"{key} {v} ft.")
    if speed.get("hover"):
        parts.append("(hover)")
    return ", ".join(parts)


def _senses_str(m):
    parts = []
    for field, label in [
        ("darkvision_range", "Darkvision"), ("blindsight_range", "Blindsight"),
        ("tremorsense_range", "Tremorsense"), ("truesight_range", "Truesight"),
    ]:
        v = m.get(field)
        if v:
            parts.append(f"{label} {v} ft.")
    passive = m.get("passive_perception")
    if passive:
        parts.append(f"Passive Perception {passive}")
    return ", ".join(parts)


def normalize_monster(m):
    ab = m.get("ability_scores", {})
    ri = m.get("resistances_and_immunities", {})
    saves = m.get("saving_throws", {})
    skills = m.get("skill_bonuses", {})
    actions_raw = m.get("actions", [])

    def split_actions(action_type):
        return [
            {"name": a["name"], "desc": a["desc"]}
            for a in actions_raw
            if a.get("action_type") == action_type
        ]

    return {
        "name": m.get("name", ""),
        "slug": m.get("key", ""),
        "gamesystem_key": _gamesystem_key(m),
        "cr": m.get("challenge_rating", ""),
        "type": _str(m.get("type", "")),
        "size": _str(m.get("size", "")),
        "alignment": m.get("alignment", ""),
        "hp": m.get("hit_points", ""),
        "hp_dice": m.get("hit_dice", ""),
        "ac": m.get("armor_class", ""),
        "ac_text": m.get("armor_detail", ""),
        "speed": _speed_str(m.get("speed", {})),
        "str": ab.get("strength", 10),
        "dex": ab.get("dexterity", 10),
        "con": ab.get("constitution", 10),
        "int": ab.get("intelligence", 10),
        "wis": ab.get("wisdom", 10),
        "cha": ab.get("charisma", 10),
        "strength_save": saves.get("strength"),
        "dexterity_save": saves.get("dexterity"),
        "constitution_save": saves.get("constitution"),
        "intelligence_save": saves.get("intelligence"),
        "wisdom_save": saves.get("wisdom"),
        "charisma_save": saves.get("charisma"),
        "skills": skills,
        "senses": _senses_str(m),
        "languages": _str(m.get("languages", "")),
        "damage_vulnerabilities": ri.get("damage_vulnerabilities_display", ""),
        "damage_resistances": ri.get("damage_resistances_display", ""),
        "damage_immunities": ri.get("damage_immunities_display", ""),
        "condition_immunities": ri.get("condition_immunities_display", ""),
        "special_abilities": [{"name": t["name"], "desc": t["desc"]} for t in m.get("traits", [])],
        "actions": split_actions("ACTION"),
        "bonus_actions": split_actions("BONUS_ACTION"),
        "reactions": split_actions("REACTION"),
        "legendary_desc": "",
        "legendary_actions": split_actions("LEGENDARY_ACTION"),
    }


def _components_str(s):
    parts = []
    if s.get("verbal"):
        parts.append("V")
    if s.get("somatic"):
        parts.append("S")
    if s.get("material"):
        mat = s.get("material_specified", "")
        parts.append(f"M ({mat})" if mat else "M")
    return ", ".join(parts)


def normalize_spell(s):
    classes_raw = s.get("classes", [])
    classes_str = ", ".join(c.get("name", "") for c in classes_raw) if isinstance(classes_raw, list) else str(classes_raw)
    level = s.get("level", 0)
    ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
    level_text = "Cantrip" if level == 0 else f"{ordinals.get(level, str(level)+'th')}-level"
    casting_raw = s.get("casting_time", "")
    casting_map = {"action": "1 action", "bonus_action": "1 bonus action", "reaction": "1 reaction", "minute": "1 minute", "hour": "1 hour"}
    casting_time = casting_map.get(casting_raw, casting_raw)
    range_val = s.get("range_text") or (f"{s.get('range', '')} feet" if s.get("range") else "")
    return {
        "name": s.get("name", ""),
        "slug": s.get("key", ""),
        "gamesystem_key": _gamesystem_key(s),
        "level": level,
        "level_text": level_text,
        "school": _str(s.get("school", "")),
        "casting_time": casting_time,
        "range": range_val,
        "components": _components_str(s),
        "material": s.get("material_specified", ""),
        "duration": s.get("duration", ""),
        "concentration": "yes" if s.get("concentration") else "",
        "ritual": "yes" if s.get("ritual") else "",
        "desc": s.get("desc", ""),
        "higher_level": s.get("higher_level", ""),
        "classes": classes_str,
    }


def normalize_item(item):
    cat = item.get("category", {})
    cat_name = _str(cat) if cat else "Adventuring Gear"
    weapon_data = item.get("weapon") or {}
    armor_data = item.get("armor") or {}

    if weapon_data:
        category = "Weapons"
    elif armor_data:
        category = "Armor"
    elif "potion" in item.get("name", "").lower():
        category = "Potions"
    else:
        category = cat_name or "Adventuring Gear"

    props = weapon_data.get("properties", [])
    props_str = ", ".join(_str(p) for p in props) if props else ""

    cost_obj = item.get("cost", {})
    if isinstance(cost_obj, dict):
        cost_str = f"{cost_obj.get('quantity', '')} {cost_obj.get('unit', '')}".strip()
    else:
        cost_str = str(cost_obj) if cost_obj else ""

    weight_obj = item.get("weight", {})
    if isinstance(weight_obj, dict):
        weight_str = f"{weight_obj.get('quantity', '')} {weight_obj.get('unit', '')}".strip()
    else:
        weight_str = str(weight_obj) if weight_obj else ""

    return {
        "name": item.get("name", ""),
        "slug": item.get("key", ""),
        "gamesystem_key": _gamesystem_key(item),
        "category": category,
        "rarity": "",
        "requires_attunement": "",
        "description": item.get("desc", ""),
        "cost": cost_str,
        "weight": weight_str,
        "damage_dice": weapon_data.get("damage_dice", ""),
        "damage_type": _str(weapon_data.get("damage_type", "")),
        "weapon_range": str(weapon_data.get("range", "") or ""),
        "properties": props_str,
        "base_ac": armor_data.get("base_ac", ""),
        "armor_class": "",
        "stealth_disadvantage": armor_data.get("stealth_disadvantage", False),
        "strength_requirement": armor_data.get("strength_requirement", ""),
        "plus_dex_mod": armor_data.get("plus_dex_mod", ""),
    }


def normalize_magicitem(item):
    rarity_obj = item.get("rarity", {})
    rarity = _str(rarity_obj) if rarity_obj else ""
    cat_obj = item.get("category", {})
    cat = _str(cat_obj) if cat_obj else "Wondrous Item"

    weapon_data = item.get("weapon") or {}
    armor_data = item.get("armor") or {}
    attune = item.get("requires_attunement", False)
    attune_detail = item.get("attunement_detail", "") or ""

    if "tattoo" in item.get("name", "").lower():
        display_cat = "Tattoos"
    elif weapon_data:
        display_cat = "Weapons"
    elif armor_data:
        display_cat = "Armor"
    elif "potion" in item.get("name", "").lower() or "elixir" in item.get("name", "").lower():
        display_cat = "Potions"
    elif "ring" in cat.lower():
        display_cat = "Rings"
    elif "rod" in cat.lower():
        display_cat = "Rods"
    elif "scroll" in cat.lower() or "scroll" in item.get("name", "").lower():
        display_cat = "Scrolls"
    elif "staff" in cat.lower():
        display_cat = "Staves"
    elif "wand" in cat.lower():
        display_cat = "Wands"
    else:
        display_cat = "Wondrous Items"

    ac_display = ""
    if armor_data:
        ac_display = armor_data.get("ac_display", "")

    cost_obj = item.get("cost", "")
    if isinstance(cost_obj, (int, float)):
        cost_str = f"{cost_obj} gp"
    else:
        cost_str = str(cost_obj) if cost_obj else ""

    return {
        "name": item.get("name", ""),
        "slug": item.get("key", ""),
        "gamesystem_key": _gamesystem_key(item),
        "category": display_cat,
        "rarity": rarity,
        "requires_attunement": attune_detail if attune_detail else ("Yes" if attune else ""),
        "description": item.get("desc", ""),
        "cost": cost_str,
        "damage_dice": weapon_data.get("damage_dice", ""),
        "damage_type": _str(weapon_data.get("damage_type", "")),
        "properties": ", ".join(_str(p) for p in weapon_data.get("properties", [])),
        "armor_class": ac_display,
        "stealth_disadvantage": armor_data.get("grants_stealth_disadvantage", False) if armor_data else False,
        "strength_requirement": armor_data.get("strength_score_required", "") if armor_data else "",
    }


def normalize_feat(f):
    benefits = f.get("benefits", [])
    benefits_text = "\n".join(f"- {b.get('desc', '')}" for b in benefits) if benefits else ""
    return {
        "name": f.get("name", ""),
        "slug": f.get("key", ""),
        "gamesystem_key": _gamesystem_key(f),
        "prerequisite": f.get("prerequisite", ""),
        "has_prerequisite": f.get("has_prerequisite", False),
        "type": f.get("type", "GENERAL"),
        "desc": f.get("desc", ""),
        "benefits": benefits_text,
        "source": f.get("document", {}).get("display_name", ""),
    }


def normalize_background(b):
    benefits = b.get("benefits", [])
    sections = {}
    for ben in benefits:
        sections[ben.get("name", "Other")] = ben.get("desc", "")
    return {
        "name": b.get("name", ""),
        "slug": b.get("key", ""),
        "gamesystem_key": _gamesystem_key(b),
        "desc": b.get("desc", ""),
        "sections": sections,
        "source": b.get("document", {}).get("display_name", ""),
    }


def normalize_class(c):
    features = c.get("features", [])
    features_text = []
    for f in features:
        features_text.append({"name": f.get("name", ""), "desc": f.get("desc", ""), "level": f.get("level", 1)})
    return {
        "name": c.get("name", ""),
        "slug": c.get("key", ""),
        "gamesystem_key": _gamesystem_key(c),
        "subclass_of": c.get("subclass_of", {}).get("name", "") if c.get("subclass_of") else "",
        "hit_dice": str(c.get("hit_dice", "")).lower(),  # API returns "D8"; normalise to "d8"
        "caster_type": c.get("caster_type", ""),
        "primary_abilities": ", ".join(_str(a) for a in (c.get("primary_abilities") or [])),
        "saving_throws": ", ".join(_str(s) for s in (c.get("saving_throws") or [])),
        "desc": c.get("desc", ""),
        "features": features_text,
        "source": c.get("document", {}).get("display_name", ""),
    }


def normalize_race(r):
    """Normalize a raw Open5e v2 /species/ record into a flat display-ready dict.

    The v2 API stores ALL race data (size, speed, ability bonuses, languages)
    as plain-text trait entries rather than structured fields.  We normalize the
    traits list and also extract the most useful values into top-level fields so
    the UI can show a quick summary without parsing trait descriptions at render time.
    """
    # Traits list — preserve all entries including meta-traits like Size/Speed
    traits = [
        {"name": t.get("name", ""), "desc": t.get("desc", "")}
        for t in (r.get("traits") or [])
        if t.get("name")
    ]

    def _trait_desc(name):
        """Return the desc of the first trait whose name matches (case-insensitive)."""
        nl = name.lower()
        for t in traits:
            if t["name"].lower() == nl:
                return t["desc"].strip()
        return ""

    # subspecies_of is a slug string (e.g. "srd_halfling"), not a nested object
    subrace_of = r.get("subspecies_of", "") or ""

    return {
        "name":           r.get("name", ""),
        "slug":           r.get("key", ""),
        "gamesystem_key": _gamesystem_key(r),
        "desc":           r.get("desc", ""),
        "traits":         traits,
        "is_subrace":     bool(r.get("is_subspecies", False)),
        "subrace_of":     subrace_of,
        "source":         r.get("document", {}).get("display_name", ""),
        # Key info extracted from named traits for quick header display
        "size_text":      _trait_desc("Size"),
        "speed_text":     _trait_desc("Speed"),
        "ability_text":   _trait_desc("Ability Score Increase"),
        "languages_text": _trait_desc("Languages"),
    }


def main():
    print("Downloading monsters...")
    monsters_raw = fetch_all("/creatures/")
    monsters = [normalize_monster(m) for m in monsters_raw]
    (DATA_DIR / "monsters_srd.json").write_text(json.dumps(monsters, indent=2), encoding="utf-8")
    print(f"  Saved {len(monsters)} monsters.")

    print("Downloading spells...")
    spells_raw = fetch_all("/spells/")
    spells = [normalize_spell(s) for s in spells_raw]
    (DATA_DIR / "spells_srd.json").write_text(json.dumps(spells, indent=2), encoding="utf-8")
    print(f"  Saved {len(spells)} spells.")

    print("Downloading equipment items...")
    items_raw = fetch_all("/items/")
    items = [normalize_item(i) for i in items_raw]
    (DATA_DIR / "items_srd.json").write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"  Saved {len(items)} equipment items.")

    print("Downloading magic items...")
    magicitems_raw = fetch_all("/magicitems/")
    magicitems = [normalize_magicitem(i) for i in magicitems_raw]
    (DATA_DIR / "magicitems.json").write_text(json.dumps(magicitems, indent=2), encoding="utf-8")
    print(f"  Saved {len(magicitems)} magic items.")

    print("Downloading feats...")
    feats_raw = fetch_all("/feats/")
    feats = [normalize_feat(f) for f in feats_raw]
    (DATA_DIR / "feats.json").write_text(json.dumps(feats, indent=2), encoding="utf-8")
    print(f"  Saved {len(feats)} feats.")

    print("Downloading backgrounds...")
    backgrounds_raw = fetch_all("/backgrounds/")
    backgrounds = [normalize_background(b) for b in backgrounds_raw]
    (DATA_DIR / "backgrounds.json").write_text(json.dumps(backgrounds, indent=2), encoding="utf-8")
    print(f"  Saved {len(backgrounds)} backgrounds.")

    print("Downloading classes...")
    classes_raw = fetch_all("/classes/")
    classes = [normalize_class(c) for c in classes_raw]
    (DATA_DIR / "classes.json").write_text(json.dumps(classes, indent=2), encoding="utf-8")
    print(f"  Saved {len(classes)} classes/subclasses.")

    print("Downloading races/species...")
    # Open5e v2 uses /species/ (the 2024 PHB terminology); no /races/ endpoint exists
    races_raw = fetch_all("/species/")
    races = [normalize_race(r) for r in races_raw]

    # Resolve subrace_of slugs to human-readable parent race names.
    # The API stores a raw slug like "toh_darakhul"; we map it to the actual name
    # or strip the source prefix and title-case the remainder as a fallback.
    slug_to_name = {r["slug"]: r["name"] for r in races if r.get("slug")}
    for r in races:
        raw = r.get("subrace_of", "")
        if raw:
            if raw in slug_to_name:
                r["subrace_of"] = slug_to_name[raw]
            else:
                cleaned = re.sub(r"^[a-z0-9]+_", "", raw).replace("_", " ").title()
                r["subrace_of"] = cleaned

    (DATA_DIR / "races_srd.json").write_text(
        json.dumps(races, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  Saved {len(races)} races/subraces.")

    print("Done.")


if __name__ == "__main__":
    main()
