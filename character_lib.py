"""
character_lib.py — pure character-sheet logic and 5e rules constants.

No streamlit imports: everything here is unit-testable data and math used by
pages/Characters.py (and importable by any future page needing class rules).
Contents: ability/proficiency math, skill→ability map, class lists, class
saving-throw proficiencies, stat-boost items, hit dice, equip-bonus stats,
multiclassing prerequisites, ability-score generation constants, and the
multiclass record helpers get_classes()/classes_label().
"""

import math


def ability_mod(score: int) -> int:
    return math.floor((score - 10) / 2)

def proficiency_bonus(level: int) -> int:
    if level <= 4: return 2
    if level <= 8: return 3
    if level <= 12: return 4
    if level <= 16: return 5
    return 6

SKILL_ABILITY = {
    "Acrobatics": "DEX", "Animal Handling": "WIS", "Arcana": "INT", "Athletics": "STR", "Deception": "CHA",
    "History": "INT", "Insight": "WIS", "Intimidation": "CHA", "Investigation": "INT", "Medicine": "WIS",
    "Nature": "INT", "Perception": "WIS", "Performance": "CHA", "Persuasion": "CHA", "Religion": "INT",
    "Sleight of Hand": "DEX", "Stealth": "DEX", "Survival": "WIS",
}
ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
SKILLS = list(SKILL_ABILITY.keys())

# Standard D&D 5e classes; "Other (custom)" lets players type a homebrew/3rd-party class
CHAR_CLASSES = [
    "Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter",
    "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard",
    "Other (custom)",
]

# Saving throw proficiencies automatically granted to each class at character creation
CLASS_SAVE_PROFS = {
    "Artificer":  {"CON", "INT"},
    "Barbarian":  {"STR", "CON"},
    "Bard":       {"DEX", "CHA"},
    "Cleric":     {"WIS", "CHA"},
    "Druid":      {"INT", "WIS"},
    "Fighter":    {"STR", "CON"},
    "Monk":       {"STR", "DEX"},
    "Paladin":    {"WIS", "CHA"},
    "Ranger":     {"STR", "DEX"},
    "Rogue":      {"DEX", "INT"},
    "Sorcerer":   {"CON", "CHA"},
    "Warlock":    {"WIS", "CHA"},
    "Wizard":     {"INT", "WIS"},
}

# Magic items / tomes that grant permanent stat bonuses.
# Each entry maps item name → (ability, amount).
# amount=None means the item sets a fixed value; user must enter the delta manually.
STAT_BOOST_ITEMS = {
    # Tomes & Manuals — permanently raise the stat by 2
    "Manual of Bodily Health":            ("CON", 2),
    "Manual of Gainful Exercise":         ("STR", 2),
    "Manual of Quickness of Action":      ("DEX", 2),
    "Tome of Clear Thought":              ("INT", 2),
    "Tome of Leadership and Influence":   ("CHA", 2),
    "Tome of Understanding":              ("WIS", 2),
    # Ioun Stones — permanently raise by 2
    "Ioun Stone of Fortitude":            ("CON", 2),
    "Ioun Stone of Insight":              ("INT", 2),
    "Ioun Stone of Agility":              ("DEX", 2),
    "Ioun Stone of Leadership":           ("CHA", 2),
    "Ioun Stone of Strength":             ("STR", 2),
    "Ioun Stone of Understanding":        ("WIS", 2),
    # "Set to X" items — amount must be entered as (target − base score)
    "Headband of Intellect (INT → 19)":   ("INT", None),
    "Gauntlets of Ogre Power (STR → 19)": ("STR", None),
    "Belt of Giant Strength — Hill (STR → 21)":  ("STR", None),
    "Belt of Giant Strength — Stone (STR → 23)": ("STR", None),
    "Belt of Giant Strength — Fire (STR → 25)":  ("STR", None),
    "Belt of Giant Strength — Cloud (STR → 27)": ("STR", None),
    "Belt of Giant Strength — Storm (STR → 29)": ("STR", None),
    "Amulet of Health (CON → 19)":        ("CON", None),
    "Custom (enter below)":               (None, None),
}

# Hit die per class — used by the Level Up feature to compute HP gain
CLASS_HIT_DICE = {
    "Artificer": 8,  "Barbarian": 12, "Bard": 8,    "Cleric": 8,   "Druid": 8,
    "Fighter": 10,   "Monk": 8,       "Paladin": 10, "Ranger": 10,  "Rogue": 8,
    "Sorcerer": 6,   "Warlock": 8,    "Wizard": 6,
}

# Stats that equipped items can modify; ability names must match ABILITIES list
EQUIP_STATS = ["AC", "STR", "DEX", "CON", "INT", "WIS", "CHA", "Initiative"]

# ── Multiclassing prerequisites (PHB p.163) ──────────────────────────────────
# Maps class name → (check_fn, human-readable requirement string).
# check_fn receives a dict of {ability: effective_score} and returns True if met.
# Fighter has an OR requirement; Monk/Paladin/Ranger have AND requirements.
MULTICLASS_REQS: dict[str, tuple] = {
    "Artificer": (lambda s: s["INT"] >= 13,                            "INT 13"),
    "Barbarian": (lambda s: s["STR"] >= 13,                            "STR 13"),
    "Bard":      (lambda s: s["CHA"] >= 13,                            "CHA 13"),
    "Cleric":    (lambda s: s["WIS"] >= 13,                            "WIS 13"),
    "Druid":     (lambda s: s["WIS"] >= 13,                            "WIS 13"),
    "Fighter":   (lambda s: s["STR"] >= 13 or s["DEX"] >= 13,          "STR 13 or DEX 13"),
    "Monk":      (lambda s: s["DEX"] >= 13 and s["WIS"] >= 13,         "DEX 13 and WIS 13"),
    "Paladin":   (lambda s: s["STR"] >= 13 and s["CHA"] >= 13,         "STR 13 and CHA 13"),
    "Ranger":    (lambda s: s["DEX"] >= 13 and s["WIS"] >= 13,         "DEX 13 and WIS 13"),
    "Rogue":     (lambda s: s["DEX"] >= 13,                            "DEX 13"),
    "Sorcerer":  (lambda s: s["CHA"] >= 13,                            "CHA 13"),
    "Warlock":   (lambda s: s["CHA"] >= 13,                            "CHA 13"),
    "Wizard":    (lambda s: s["INT"] >= 13,                            "INT 13"),
}

# ── Ability score generation constants ───────────────────────────────────────
# Standard array values assigned freely across the six abilities
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

# DMG point-buy costs per score (8–15 range, 27-point budget)
POINT_BUY_COSTS   = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_BUDGET  = 27


def get_classes(ch: dict) -> list:
    """Return the multiclass list, migrating single-class characters on the fly."""
    if "classes" in ch:
        return ch["classes"]
    return [{"class": ch.get("char_class", ""), "level": ch.get("level", 1)}]


def classes_label(classes: list) -> str:
    """Return 'Fighter 5 / Wizard 3' style display string."""
    parts = [f"{c['class']} {c['level']}" for c in classes if c.get("class") and c.get("level", 0) > 0]
    return " / ".join(parts) if parts else "?"
