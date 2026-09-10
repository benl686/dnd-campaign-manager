"""
treasure_tables.py — D&D 5e treasure constants and rolling helpers.

Individual treasure uses 10 granular CR bands with a formula-based extras
system that grows exponentially: at CR 5 a creature has maybe a 20% shot at
one gem; at CR 30 it carries ~10 gems, ~8 art objects, ~8 jewelry pieces, etc.
Each extra item picks its own value tier based on the creature's CR.

Tier system: all categories use clean round-number tiers from the set
{10, 25, 50, 100, 250, 500, 1000, 2500, 5000}, each step roughly 2–2.5×.
No odd values like 750 or 2000; no skipped steps like going 500→2500.

Item names use Title Case and are sorted alphabetically within each tier.
"""

import random
from collections import Counter


# ── CR helpers ────────────────────────────────────────────────────────────────

def cr_to_float(cr) -> float:
    try:
        if "/" in str(cr):
            n, d = str(cr).split("/")
            return float(n) / float(d)
        return float(cr)
    except Exception:
        return 0.0


def cr_float_to_band(cr_float: float) -> str:
    """10-tier individual-treasure band."""
    if cr_float <= 0:      return "CR 0"
    elif cr_float <= 0.25: return "CR 1/8–1/4"
    elif cr_float <= 1.0:  return "CR 1/2–1"
    elif cr_float <= 4.0:  return "CR 2–4"
    elif cr_float <= 8.0:  return "CR 5–8"
    elif cr_float <= 12.0: return "CR 9–12"
    elif cr_float <= 16.0: return "CR 13–16"
    elif cr_float <= 20.0: return "CR 17–20"
    elif cr_float <= 24.0: return "CR 21–24"
    return "CR 25+"


def cr_float_to_hoard_band(cr_float: float) -> str:
    """6-tier DMG hoard band (for hoard coins/magic tables)."""
    if cr_float <= 4:    return "CR 0–4"
    elif cr_float <= 10: return "CR 5–10"
    elif cr_float <= 16: return "CR 11–16"
    elif cr_float <= 20: return "CR 17–20"
    elif cr_float <= 24: return "CR 21–24"
    return "CR 25+"


# ── Coin helpers ──────────────────────────────────────────────────────────────

def roll_coins(nd: int, ds: int, mult: int = 1) -> int:
    if nd == 0:
        return 0
    return sum(random.randint(1, ds) for _ in range(nd)) * mult


def lookup_range(table: list, roll: int):
    for lo, hi, val in table:
        if lo <= roll <= hi:
            return val
    return table[-1][2]


def format_coins(totals: dict) -> str:
    order = ["cp", "sp", "ep", "gp", "pp"]
    parts = [f"{totals[k]:,} {k}" for k in order if totals.get(k, 0) > 0]
    return ", ".join(parts) if parts else "No coins"


def collapse_dupes(items: list) -> str:
    counts = Counter(items)
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return ", ".join(f"{n} x{counts[n]}" if counts[n] > 1 else n for n in seen)


# ── Individual coin tables (10 bands) ────────────────────────────────────────

INDIVIDUAL_BY_CR = {
    "CR 0": [
        (1,  50, {"cp": (1,6,1), "sp": (0,0,0), "ep": (0,0,0), "gp": (0,0,0), "pp": (0,0,0)}),
        (51, 85, {"cp": (2,6,1), "sp": (0,0,0), "ep": (0,0,0), "gp": (0,0,0), "pp": (0,0,0)}),
        (86,100, {"cp": (0,0,0), "sp": (1,4,1), "ep": (0,0,0), "gp": (0,0,0), "pp": (0,0,0)}),
    ],
    "CR 1/8–1/4": [
        (1,  30, {"cp": (3,6,1), "sp": (0,0,0), "ep": (0,0,0), "gp": (0,0,0), "pp": (0,0,0)}),
        (31, 55, {"cp": (2,6,1), "sp": (1,4,1), "ep": (0,0,0), "gp": (0,0,0), "pp": (0,0,0)}),
        (56, 75, {"cp": (0,0,0), "sp": (1,6,1), "ep": (0,0,0), "gp": (0,0,0), "pp": (0,0,0)}),
        (76, 92, {"cp": (0,0,0), "sp": (2,6,1), "ep": (0,0,0), "gp": (0,0,0), "pp": (0,0,0)}),
        (93,100, {"cp": (0,0,0), "sp": (1,4,1), "ep": (1,3,1), "gp": (0,0,0), "pp": (0,0,0)}),
    ],
    "CR 1/2–1": [
        (1,  20, {"cp": (2,6,1), "sp": (2,6,1), "ep": (0,0,0), "gp": (0,0,0), "pp": (0,0,0)}),
        (21, 45, {"cp": (0,0,0), "sp": (3,6,1), "ep": (0,0,0), "gp": (0,0,0), "pp": (0,0,0)}),
        (46, 65, {"cp": (0,0,0), "sp": (1,6,1), "ep": (1,6,1), "gp": (0,0,0), "pp": (0,0,0)}),
        (66, 85, {"cp": (0,0,0), "sp": (2,6,1), "ep": (0,0,0), "gp": (1,4,1), "pp": (0,0,0)}),
        (86, 96, {"cp": (0,0,0), "sp": (0,0,0), "ep": (1,4,1), "gp": (1,4,1), "pp": (0,0,0)}),
        (97,100, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,1), "pp": (0,0,0)}),
    ],
    "CR 2–4": [
        (1,  20, {"cp": (0,0,0), "sp": (2,6,1), "ep": (0,0,0), "gp": (2,4,1), "pp": (0,0,0)}),
        (21, 45, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (3,4,1), "pp": (0,0,0)}),
        (46, 65, {"cp": (0,0,0), "sp": (0,0,0), "ep": (1,6,1), "gp": (1,6,1), "pp": (0,0,0)}),
        (66, 85, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,1), "pp": (0,0,0)}),
        (86, 96, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (3,6,1), "pp": (0,0,0)}),
        (97,100, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,4,1), "pp": (1,4,1)}),
    ],
    "CR 5–8": [
        (1,  25, {"cp": (4,6,100),"sp": (1,6,10), "ep": (0,0,0),   "gp": (2,6,1),  "pp": (0,0,0)}),
        (26, 50, {"cp": (0,0,0),  "sp": (1,6,100),"ep": (0,0,0),   "gp": (1,6,10), "pp": (0,0,0)}),
        (51, 70, {"cp": (0,0,0),  "sp": (0,0,0),  "ep": (1,6,100), "gp": (1,6,10), "pp": (0,0,0)}),
        (71, 90, {"cp": (0,0,0),  "sp": (0,0,0),  "ep": (0,0,0),   "gp": (2,6,10), "pp": (0,0,0)}),
        (91, 99, {"cp": (0,0,0),  "sp": (0,0,0),  "ep": (0,0,0),   "gp": (3,6,10), "pp": (0,0,0)}),
        (100,100,{"cp": (0,0,0),  "sp": (0,0,0),  "ep": (0,0,0),   "gp": (2,6,10), "pp": (1,4,1)}),
    ],
    "CR 9–12": [
        (1,  20, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (1,6,100),  "pp": (0,0,0)}),
        (21, 45, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,100),  "pp": (0,0,0)}),
        (46, 70, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (1,6,100),  "pp": (1,6,10)}),
        (71, 90, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,100),  "pp": (2,6,10)}),
        (91,100, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (1,4,1000), "pp": (1,4,100)}),
    ],
    "CR 13–16": [
        (1,  20, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,100),  "pp": (1,6,100)}),
        (21, 45, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (1,6,1000), "pp": (0,0,0)}),
        (46, 70, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,100),  "pp": (2,6,100)}),
        (71, 90, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (1,6,1000), "pp": (1,6,100)}),
        (91,100, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,1000), "pp": (2,6,100)}),
    ],
    # Bands 8-10: dramatically scaled upward so each tier is clearly richer than the last.
    # CR 17-20 avg ~19k gp · CR 21-24 avg ~102k gp · CR 25+ avg ~530k gp.
    "CR 17–20": [
        (1,  20, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (1,6,1000),  "pp": (1,4,100)}),
        (21, 45, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,2000),  "pp": (2,6,200)}),
        (46, 70, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (3,6,2000),  "pp": (3,6,200)}),
        (71, 90, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,4,5000),  "pp": (2,6,500)}),
        (91,100, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (1,4,10000), "pp": (2,4,1000)}),
    ],
    "CR 21–24": [
        (1,  15, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,5000),  "pp": (2,6,500)}),
        (16, 40, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,6,10000), "pp": (2,6,1000)}),
        (41, 65, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (3,6,10000), "pp": (3,6,1000)}),
        (66, 90, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,4,20000), "pp": (3,6,2000)}),
        (91,100, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (1,4,50000), "pp": (3,6,5000)}),
    ],
    "CR 25+": [
        (1,  10, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (3,6,10000),  "pp": (3,6,2000)}),
        (11, 30, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,4,50000),  "pp": (2,6,5000)}),
        (31, 65, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (3,6,50000),  "pp": (3,6,5000)}),
        (66, 90, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (2,4,100000), "pp": (3,6,5000)}),
        (91,100, {"cp": (0,0,0), "sp": (0,0,0), "ep": (0,0,0), "gp": (3,6,100000), "pp": (4,6,10000)}),
    ],
}

# Representative CR float for each band (used when caller doesn't supply exact CR)
BAND_MIDPOINTS = {
    "CR 0": 0, "CR 1/8–1/4": 0.2, "CR 1/2–1": 0.75,
    "CR 2–4": 3, "CR 5–8": 6.5, "CR 9–12": 10.5,
    "CR 13–16": 14.5, "CR 17–20": 18.5, "CR 21–24": 22.5, "CR 25+": 27,
}


# ── Formula-based extras ──────────────────────────────────────────────────────
# Expected count grows as a power law above threshold_cr, doubling roughly
# every 6-8 CR levels.  The fractional part becomes a probability of one more.
# CR 0–4 always yields 0 extras of any kind.

def _extra_count(cr_float: float, threshold_cr: float, scale: float) -> float:
    """Expected number of extras of this type at this CR.

    Uses exponent 1.5 so counts grow steeply at high CR: a CR 10 creature
    gets a handful of gems while CR 30 (Tiamat) gets 30+.
    """
    if cr_float <= threshold_cr:
        return 0.0
    return ((cr_float - threshold_cr) ** 1.5) / scale


def _roll_count(expected: float) -> int:
    """floor(expected) guaranteed + bernoulli(frac) chance of one more."""
    base = int(expected)
    return base + (1 if random.random() < (expected - base) else 0)


def _pick(tiers: list, weights: list) -> int:
    return random.choices(tiers, weights=weights, k=1)[0]


def _gem_tier_at_cr(cr: float) -> int:
    # Tiers: 10 / 50 / 100 / 250 / 500 / 1000 / 5000
    t = [10, 50, 100, 250, 500, 1000, 5000]
    if cr <= 5:    w = [10,  4,  2,  1,  0,  0,  0]
    elif cr <= 8:  w = [ 4, 10,  6,  4,  2,  0,  0]
    elif cr <= 12: w = [ 0,  4, 10,  8,  4,  2,  0]
    elif cr <= 16: w = [ 0,  0,  4,  8, 10,  4,  2]
    elif cr <= 20: w = [ 0,  0,  0,  4,  8, 10,  4]
    elif cr <= 24: w = [ 0,  0,  0,  0,  4,  8, 10]
    else:          w = [ 0,  0,  0,  0,  2,  6, 10]
    return _pick(t, w)


def _art_tier_at_cr(cr: float) -> int:
    # Tiers: 25 / 100 / 250 / 500 / 1000 / 2500 / 5000
    t = [25, 100, 250, 500, 1000, 2500, 5000]
    if cr <= 5:    w = [10,  4,  1,  0,  0,  0,  0]
    elif cr <= 8:  w = [ 4, 10,  6,  2,  0,  0,  0]
    elif cr <= 12: w = [ 0,  4,  8,  6,  4,  0,  0]
    elif cr <= 16: w = [ 0,  0,  2,  6,  8,  4,  0]
    elif cr <= 20: w = [ 0,  0,  0,  2,  6,  8,  4]
    elif cr <= 24: w = [ 0,  0,  0,  0,  2,  8,  6]
    else:          w = [ 0,  0,  0,  0,  0,  6,  8]
    return _pick(t, w)


def _jewelry_tier_at_cr(cr: float) -> int:
    # Tiers: 25 / 100 / 250 / 500 / 1000 / 2500 / 5000
    t = [25, 100, 250, 500, 1000, 2500, 5000]
    if cr <= 6:    w = [10,  6,  2,  0,  0,  0,  0]
    elif cr <= 10: w = [ 4, 10,  6,  2,  0,  0,  0]
    elif cr <= 14: w = [ 0,  4,  8,  6,  4,  0,  0]
    elif cr <= 18: w = [ 0,  0,  2,  6,  8,  4,  0]
    elif cr <= 22: w = [ 0,  0,  0,  2,  6,  8,  4]
    elif cr <= 26: w = [ 0,  0,  0,  0,  2,  8,  6]
    else:          w = [ 0,  0,  0,  0,  0,  4,  8]
    return _pick(t, w)


def _trade_tier_at_cr(cr: float) -> int:
    # Tiers: 10 / 50 / 100 / 500 / 1000 / 2500
    t = [10, 50, 100, 500, 1000, 2500]
    if cr <= 10:   w = [10,  6,  2,  0,  0,  0]
    elif cr <= 14: w = [ 2, 10,  6,  2,  0,  0]
    elif cr <= 18: w = [ 0,  4,  8,  4,  2,  0]
    elif cr <= 22: w = [ 0,  0,  4,  8,  4,  2]
    else:          w = [ 0,  0,  2,  6,  6,  4]
    return _pick(t, w)


def _curiosity_tier_at_cr(cr: float) -> int:
    # Tiers: 0 / 10 / 25 / 50 / 100 / 250 / 500 / 1000 / 2500
    # Low tiers are trinkets — mundane-odd finds for low-CR creatures.
    t = [0, 10, 25, 50, 100, 250, 500, 1000, 2500]
    if cr <= 8:    w = [4,  8,  6,  4,  2,  0,  0,  0,  0]
    elif cr <= 12: w = [1,  3,  6, 10,  4,  2,  0,  0,  0]
    elif cr <= 16: w = [0,  1,  3,  8, 10,  6,  2,  0,  0]
    elif cr <= 20: w = [0,  0,  1,  4,  8,  8,  4,  2,  0]
    elif cr <= 24: w = [0,  0,  0,  2,  4,  8,  8,  4,  2]
    else:          w = [0,  0,  0,  0,  2,  6,  6,  6,  4]
    return _pick(t, w)


# ── Hoard coins (6 bands) ─────────────────────────────────────────────────────

HOARD_COINS_BY_CR = {
    "CR 0–4":   {"cp": (6,6,100), "sp": (3,6,100), "ep": (0,0,0),   "gp": (2,6,10),   "pp": (0,0,0)},
    "CR 5–10":  {"cp": (2,6,100), "sp": (2,6,1000),"ep": (0,0,0),   "gp": (6,6,100),  "pp": (3,6,10)},
    "CR 11–16": {"cp": (0,0,0),   "sp": (0,0,0),   "ep": (0,0,0),   "gp": (4,6,1000), "pp": (5,6,100)},
    "CR 17–20": {"cp": (0,0,0),   "sp": (0,0,0),   "ep": (0,0,0),   "gp": (8,6,1000), "pp": (4,6,100)},
    "CR 21–24": {"cp": (0,0,0),   "sp": (0,0,0),   "ep": (0,0,0),   "gp": (10,6,1000),"pp": (6,6,100)},
    "CR 25+":   {"cp": (0,0,0),   "sp": (0,0,0),   "ep": (0,0,0),   "gp": (12,6,1000),"pp": (8,6,1000)},
}

HOARD_MAGIC_BY_CR = {
    "CR 0–4": [
        (1,6,None),(7,16,"Common"),(17,36,"Uncommon"),(37,60,"Uncommon"),
        (61,76,"Rare"),(77,91,"Rare"),(92,97,"Very Rare"),(98,99,"Very Rare"),(100,100,"Legendary"),
    ],
    "CR 5–10": [
        (1,4,None),(5,10,"Common"),(11,22,"Uncommon"),(23,49,"Uncommon"),
        (50,66,"Rare"),(67,77,"Rare"),(78,89,"Very Rare"),(90,95,"Very Rare"),
        (96,98,"Legendary"),(99,99,"Legendary"),(100,100,"Legendary"),
    ],
    "CR 11–16": [
        (1,3,None),(4,6,"Uncommon"),(7,12,"Rare"),(13,20,"Rare"),
        (21,30,"Very Rare"),(31,42,"Very Rare"),(43,62,"Very Rare"),
        (63,74,"Legendary"),(75,84,"Legendary"),(85,93,"Legendary"),
        (94,97,"Legendary"),(98,99,"Legendary"),(100,100,"Legendary"),
    ],
    "CR 17–20": [
        (1,2,None),(3,6,"Very Rare"),(7,100,"Legendary"),
    ],
    "CR 21–24": [
        (1,2,None),(3,5,"Very Rare"),(6,100,"Legendary"),
    ],
    "CR 25+": [
        (1,2,None),(3,100,"Legendary"),
    ],
}

# Auto-suggested hoard contents for TreasureGenerator Encounter Loot baseline.
# Multi-tier format: list of {"count": int, "tier": int} rows per category.
HOARD_AUTO_ROLLS = {
    "CR 0–4": {
        "gems":    [{"count": 2, "tier": 10}],
        "art":     [{"count": 1, "tier": 25}],
        "jewelry": [{"count": 1, "tier": 25}],
        "trade":   [],
        "curs":    [],
        "magic":   1,
    },
    "CR 5–10": {
        "gems":    [{"count": 2, "tier": 50}, {"count": 1, "tier": 100}],
        "art":     [{"count": 2, "tier": 250}],
        "jewelry": [{"count": 1, "tier": 250}],
        "trade":   [{"count": 1, "tier": 50}],
        "curs":    [],
        "magic":   2,
    },
    "CR 11–16": {
        "gems":    [{"count": 2, "tier": 500}, {"count": 1, "tier": 1000}],
        "art":     [{"count": 2, "tier": 1000}, {"count": 1, "tier": 2500}],
        "jewelry": [{"count": 2, "tier": 1000}],
        "trade":   [{"count": 1, "tier": 100}],
        "curs":    [{"count": 1, "tier": 1000}],
        "magic":   3,
    },
    "CR 17–20": {
        "gems":    [{"count": 3, "tier": 1000}, {"count": 1, "tier": 5000}],
        "art":     [{"count": 2, "tier": 2500}, {"count": 1, "tier": 5000}],
        "jewelry": [{"count": 2, "tier": 2500}],
        "trade":   [{"count": 1, "tier": 500}],
        "curs":    [{"count": 1, "tier": 1000}],
        "magic":   4,
    },
    "CR 21–24": {
        "gems":    [{"count": 3, "tier": 1000}, {"count": 2, "tier": 5000}],
        "art":     [{"count": 2, "tier": 2500}, {"count": 2, "tier": 5000}],
        "jewelry": [{"count": 3, "tier": 2500}],
        "trade":   [{"count": 2, "tier": 500}],
        "curs":    [{"count": 1, "tier": 2500}],
        "magic":   5,
    },
    "CR 25+": {
        "gems":    [{"count": 3, "tier": 1000}, {"count": 3, "tier": 5000}],
        "art":     [{"count": 2, "tier": 2500}, {"count": 2, "tier": 5000}],
        "jewelry": [{"count": 2, "tier": 2500}, {"count": 2, "tier": 5000}],
        "trade":   [{"count": 2, "tier": 500}],
        "curs":    [{"count": 2, "tier": 2500}],
        "magic":   6,
    },
}


# ── Gems ──────────────────────────────────────────────────────────────────────
# Tiers: 10 / 50 / 100 / 250 / 500 / 1000 / 5000 gp
# Naming convention: Mineral (Variety, Quality) — variety/subspecies first,
# quality/condition second.  Sorted alphabetically within each tier.

GEMS = {
    10:   ["Agate (Banded)",
           "Agate (Eye)",
           "Agate (Moss)",
           "Aragonite",
           "Azurite",
           "Calcite (Honey)",
           "Celestite",
           "Chrysocolla",
           "Dalmatian Stone",
           "Epidote",
           "Feldspar (Green) [aka Amazonite]",
           "Flint (Knapped)",
           "Fluorite",
           "Fuchsite",
           "Gypsum (Crystalline) [aka Selenite]",
           "Hematite",
           "Jasper (Brown)",
           "Jasper (Mookaite)",
           "Jasper (Ocean)",
           "Jasper (Picture)",
           "Jasper (Red)",
           "Lapis Lazuli",
           "Magnesite",
           "Malachite",
           "Marble (Zebra)",
           "Obsidian (Rainbow) [aka Volcanic Glass]",
           "Obsidian (Snowflake) [aka Volcanic Glass]",
           "Obsidian [aka Volcanic Glass]",
           "Petrified Wood",
           "Pyrite (Nodule) [aka Fool's Gold]",
           "Quartz (Blue)",
           "Quartz (Glittering) [aka Aventurine]",
           "Quartz (Golden Sheen) [aka Tiger Eye]",
           "Rhodonite",
           "Serpentine",
           "Soapstone",
           "Sodalite",
           "Turquoise",
           "Unakite",
           "Zoisite (Thulite)"],
    50:   ["Agate (Blue Lace)",
           "Agate (Crazy Lace)",
           "Agate (Fire)",
           "Agate (Plume)",
           "Agate (Rose-Banded)",
           "Apatite (Green)",
           "Chalcedony",
           "Chalcedony (Black) [aka Onyx]",
           "Chalcedony (Blue)",
           "Chalcedony (Grape)",
           "Chalcedony (Green) [aka Chrysoprase]",
           "Chalcedony (Heliotrope) [aka Bloodstone]",
           "Chalcedony (Red) [aka Carnelian]",
           "Chalcedony (Red-Banded) [aka Sardonyx]",
           "Dumortierite",
           "Garnet (Almandine)",
           "Hemimorphite",
           "Howlite",
           "Jasper",
           "Jasper (Bumblebee)",
           "Kyanite (Pale)",
           "Labradorite (Pale)",
           "Lepidolite",
           "Moonstone",
           "Obsidian (Gold Sheen) [aka Volcanic Glass]",
           "Obsidian (Mahogany) [aka Volcanic Glass]",
           "Opal (Common)",
           "Prehnite",
           "Quartz",
           "Quartz (Phantom)",
           "Quartz (Purple, Pale) [aka Amethyst]",
           "Quartz (Rutilated)",
           "Quartz (Smoky)",
           "Quartz (Star Rose)",
           "Quartz (Yellow) [aka Citrine]",
           "Rhodochrosite",
           "Sunstone",
           "Sunstone (Spangled)",
           "Variscite",
           "Zircon"],
    100:  ["Amber [aka Fossilized Resin]",
           "Andalusite",
           "Apatite (Blue)",
           "Beryl (Blue, Pale) [aka Aquamarine]",
           "Chrysoberyl",
           "Coral",
           "Cordierite (Violet) [aka Iolite]",
           "Danburite",
           "Garnet (Pyrope)",
           "Garnet (Red)",
           "Jade",
           "Jet [aka Fossilized Wood]",
           "Kyanite (Blue)",
           "Labradorite (Bright)",
           "Pearl (Freshwater)",
           "Pearl (White)",
           "Pectolite (Blue) [aka Larimar]",
           "Quartz (Hawk's Eye)",
           "Quartz (Prasiolite)",
           "Quartz (Purple) [aka Amethyst]",
           "Quartz (Rose, Fine)",
           "Spinel (Red/Brown)",
           "Topaz (Blue)",
           "Topaz (White)",
           "Tourmaline",
           "Tourmaline (Black)",
           "Zircon (Blue)",
           "Zircon (Golden)"],
    250:  ["Apatite (Neon Blue)",
           "Beryl (Golden) [aka Heliodor]",
           "Beryl (Pink) [aka Morganite]",
           "Diaspore (Color-Changing)",
           "Garnet (Color-Changing)",
           "Garnet (Rhodolite)",
           "Garnet (Spessartine)",
           "Kornerupine",
           "Moonstone (Rainbow)",
           "Pearl (Black)",
           "Pearl (Golden)",
           "Quartz (Ametrine)",
           "Quartz (Cat's Eye)",
           "Quartz (Purple, Deep Royal) [aka Amethyst]",
           "Scapolite (Yellow)",
           "Spinel (Pink)",
           "Spodumene (Pink) [aka Kunzite]",
           "Sugilite",
           "Sunstone (Fine)",
           "Titanite (Sphene)",
           "Topaz (Pink)",
           "Topaz (Yellow)",
           "Tourmaline (Chrome)",
           "Tourmaline (Rubellite)",
           "Tourmaline (Verdelite)"],
    500:  ["Beryl (Blue) [aka Aquamarine]",
           "Beryl (Green, Pale) [aka Emerald]",
           "Chrysoberyl (Cat's Eye) [aka Cymophane]",
           "Chrysoberyl (Color-Changing, Pale) [aka Alexandrite]",
           "Corundum (Green) [aka Sapphire]",
           "Garnet (Demantoid)",
           "Garnet (Hessonite)",
           "Garnet (Malaia)",
           "Garnet (Mandarin)",
           "Garnet (Tsavorite)",
           "Moonstone (Blue)",
           "Olivine (Green) [aka Peridot]",
           "Opal (Boulder)",
           "Opal (Crystal)",
           "Opal (White)",
           "Pearl (Black, Fine)",
           "Pearl (South Sea)",
           "Spinel (Blue)",
           "Spinel (Lavender)",
           "Spinel (Red)",
           "Sunstone (Copper Schiller)",
           "Topaz",
           "Topaz (Imperial)",
           "Tourmaline (Bi-Color)",
           "Tourmaline (Indicolite)",
           "Tourmaline (Mint)",
           "Tourmaline (Watermelon)"],
    1000: ["Ammolite [aka Opalized Fossil Shell]",
           "Benitoite",
           "Beryl (Green) [aka Emerald]",
           "Beryl (Red, Pale) [aka Bixbite]",
           "Beryl (Trapiche, Green) [aka Emerald]",
           "Chrysoberyl (Cat's Eye, Fine) [aka Cymophane]",
           "Chrysoberyl (Color-Changing, Fine) [aka Alexandrite]",
           "Corundum (Blue) [aka Sapphire]",
           "Corundum (Color-Changing) [aka Sapphire]",
           "Corundum (Padparadscha) [aka Sapphire]",
           "Corundum (Pink) [aka Sapphire]",
           "Corundum (Red, Pale) [aka Ruby]",
           "Corundum (Red, Star) [aka Star Ruby]",
           "Corundum (Star) [aka Star Sapphire]",
           "Corundum (Yellow) [aka Sapphire]",
           "Corundum (Yellow, Fancy) [aka Sapphire]",
           "Diamond (Small)",
           "Garnet (Demantoid, Fine)",
           "Garnet (Tsavorite, Fine)",
           "Grandidierite (Fine)",
           "Hauyne",
           "Jade (Jadeite, Imperial)",
           "Jeremejevite",
           "Musgravite",
           "Opal",
           "Opal (Black)",
           "Opal (Fire)",
           "Opal (Harlequin)",
           "Serendibite",
           "Spinel (Blue, Fine)",
           "Spinel (Cobalt)",
           "Spinel (Red, Fine)",
           "Taaffeite (Pale)",
           "Tourmaline (Neon Copper, Pale)",
           "Zoisite (Blue) [aka Tanzanite]"],
    5000: ["Benitoite (Fine)",
           "Beryl (Red, Fine) [aka Bixbite]",
           "Beryl (Vivid Green, Fine) [aka Emerald]",
           "Chrysoberyl (Color-Changing, Flawless) [aka Alexandrite]",
           "Corundum (Black) [aka Sapphire]",
           "Corundum (Cornflower Blue) [aka Sapphire]",
           "Corundum (Padparadscha, Fine) [aka Sapphire]",
           "Corundum (Red) [aka Ruby]",
           "Corundum (Red, Pigeon's Blood) [aka Ruby]",
           "Corundum (Red, Star, Fine) [aka Star Ruby]",
           "Diamond",
           "Diamond (Blue, Fancy)",
           "Diamond (Flawless)",
           "Diamond (Green, Fancy)",
           "Diamond (Orange, Fancy)",
           "Diamond (Pink, Fancy)",
           "Diamond (Red, Fancy)",
           "Diamond (Yellow, Fancy)",
           "Jade (Jadeite, Finest Imperial)",
           "Musgravite (Large)",
           "Opal (Black, Fine)",
           "Painite",
           "Poudretteite",
           "Spinel (Cobalt, Fine)",
           "Taaffeite (Fine)",
           "Tourmaline (Neon Copper, Fine)",
           "Zircon (Jacinth)",
           "Zoisite (Blue, Large) [aka Tanzanite]"],
}


# ── Art Objects ───────────────────────────────────────────────────────────────
# Tiers: 25 / 100 / 250 / 500 / 1000 / 2500 / 5000 gp
# All names Title Cased and sorted alphabetically within each tier.

ART_OBJECTS = {
    25:   ["A Pair of Engraved Bone Dice",
           "A Set of Painted Wooden Nesting Dolls",
           "Beaded Curtain of Dyed Glass and Bone",
           "Black Velvet Mask Stitched with Silver Thread",
           "Brass Belt Buckle Cast as a Roaring Lion",
           "Bundle of Rare Feathers Tied with Silk Ribbon",
           "Carved Antler Drinking Cup with a Copper Rim",
           "Carved Bone Statuette",
           "Carved Wooden Toy Soldier Painted in Livery",
           "Cloth-of-Gold Vestments",
           "Copper Brooch Shaped Like a Leaping Fish",
           "Copper Chalice with Silver Filigree",
           "Embroidered Silk Handkerchief",
           "Embroidered Table Runner with Festival Scenes",
           "Gold Locket with a Painted Portrait Inside",
           "Leather-Bound Journal with Gilt Clasps",
           "Painted Clay Figurine of a Harvest Deity",
           "Pressed-Tin Icon of a Local Saint",
           "Silver Ewer",
           "Small Gold Bracelet",
           "Small Mirror in a Painted Wooden Frame",
           "Tarnished Silver Ring with an Engraved Family Crest",
           "Whalebone Scrimshaw Depicting a Sea Serpent Hunt"],
    100:  ["A Hand-Colored Woodcut Print of a Famous Battle",
           "A Miniature Mechanical Singing Bird in a Copper Cage",
           "A Set of Carved Bone Narrative Relief Panels",
           "Blown Glass Vase in Deep Cobalt Blue",
           "Bronze Figurine of a Seated Scholar",
           "Cast Bronze Oil Lamp with Intricate Scrollwork",
           "Embossed Leather-Bound Poetry Collection with Gilt Spine",
           "Enameled Copper Plate Depicting a Hunt Scene",
           "Gilt-Edged Prayer Book with Illuminated Capitals",
           "Lacquered Wooden Box with Inlaid Mother-of-Pearl",
           "Pewter Beer Stein with a Hinged Silver Lid",
           "Set of Five Carved Ivory Gaming Pieces",
           "Small Carved Jade Turtle",
           "Small Carved Soapstone Bowl with a Fitted Lid",
           "Stained Glass Panel of a Kingfisher in Flight",
           "Terracotta Figurine of a Dancing Bear",
           "Woven Wool Tapestry Fragment with Geometric Patterns"],
    250:  ["Alabaster Perfume Bottle with a Gold Stopper",
           "Box of Turquoise Animal Figurines",
           "Brass Mug with Jade Inlay",
           "Bronze Crown",
           "Carved Ivory Statuette",
           "Enameled Snuff Box Depicting a Masquerade",
           "Engraved Silver Hip Flask with a Hunting Motif",
           "Gilded Birdcage Holding a Mechanical Songbird",
           "Gilded Music Sheet in a Lacquered Case",
           "Gold Bird Cage with Electrum Filigree",
           "Gold Ring Set with Bloodstone",
           "Large Gold Bracelet",
           "Large Well-Made Tapestry",
           "Marble Sundial Etched with Zodiac Signs",
           "Painted Silk Fan with Ivory Spines",
           "Polished Obsidian Hand Mirror in a Silver Frame",
           "Rosewood Flute Inlaid with Silver Vines",
           "Set of Carved Ivory Gaming Tiles in a Rosewood Box",
           "Set of Fine Hand-Painted Porcelain Tea Bowls",
           "Silk Robe with Gold Embroidery",
           "Silver Necklace with a Gemstone Pendant",
           "Silver Writing Set: Pen, Inkpot, and Wax Seal",
           "Silvered Hunting Horn on an Embroidered Baldric",
           "Small Bronze Bust of a Forgotten Emperor",
           "Wooden Puzzle Box with Hidden Compartment"],
    500:  ["A Bronze Bull Figurine with Eyes of Polished Jet",
           "A Finely-Wrought Bronze Mirror in a Decorated Stand",
           "A Reliquary Box of Gilded Cedar with Crystal Windows",
           "A Silk-Embroidered Ceremonial Banner",
           "An Amber Sculpture of a Coiled Dragon with an Insect Inclusion",
           "An Illuminated Single Folio from a Lost Codex",
           "An Ivory Diptych (Two Carved Panels) in a Rosewood Frame",
           "An Old Nautical Map on Vellum with Gilded Compass Rose",
           "Carved Hardwood Panel Depicting a Mythological Battle",
           "Carved Obsidian Bust of a Nobleman",
           "Ivory Hair Combs Carved as Breaking Waves (Matched Pair)",
           "Painted Enamel Box Set with Small Gemstone Chips",
           "Pair of Matching Silver Candlesticks with Garnet Insets",
           "Set of Twelve Silver Spoons with Engraved Noble Crests",
           "Silver-Inlaid Mahogany Writing Desk Ornament",
           "Tapestry Panel Woven with a Unicorn Hunt in Fine Wool"],
    1000: ["A Bronze Astrolabe in Perfect Working Condition",
           "A Gilded Saddle Tooled with Gryphon Motifs",
           "A Jeweled Hourglass with Powdered Pearl Sand",
           "A Masterwork Oil Painting of a Moonlit Harbour",
           "A Stained Glass Triptych of the Seasons in a Bronze Frame",
           "Alabaster Bust of a Veiled Woman So Fine the Veil Seems Sheer",
           "An Ebony Cane with a Sculpted Gold Raven Head",
           "Antique Silver Candelabra with Seven Serpentine Arms",
           "Carved Harp of Exotic Wood with Ivory Inlay and Zircon Gems",
           "Carved Malachite Chess Set with Gold-Veined Board",
           "Ceremonial Electrum Dagger with a Black Pearl in the Pommel",
           "Crystal Decanter with a Matching Set of Six Goblets",
           "Gold Dragon Comb Set with Red Garnets as Eyes",
           "Obsidian Statuette with Gold Fittings and Inlay",
           "Painted Gold War Mask",
           "Platinum Pocket Watch That Runs Slightly Fast",
           "Silver Chalice Set with Moonstones",
           "Silver Music Box That Plays a Haunting Lullaby",
           "Small Gold Idol"],
    2500: ["A Ceremonial Shield of Silvered Steel Chased with Gold Knotwork",
           "A Clockwork Nightingale in a Gilded Cage That Sings at Dusk",
           "A Crystal Punch Bowl with Twelve Matching Cups on a Silver Tray",
           "A Golden Orrery Showing the Movement of the Five Moons",
           "A Kraken Carved from a Single Ammonite Fossil and Mounted in Gold",
           "Carved Jade Dragon with Ruby Eyes",
           "Embroidered Silk and Velvet Mantle Set with Numerous Moonstones",
           "Eye Patch with a Mock Eye Set in Blue Sapphire and Moonstone",
           "Fine Gold Chain Set with a Fire Opal",
           "Gold Circlet Set with Four Aquamarines",
           "Gold Music Box",
           "Illuminated Manuscript Bound in Dragonhide with a Clasp of Hammered Gold",
           "Old Masterwork Painting",
           "Pearl-Inlaid Ebony Lute with a Warm Tone",
           "Platinum Bracelet Set with a Sapphire",
           "Platinum Tiara Set with Alexandrites",
           "Set of Twelve Golden Spice Jars Each with a Different Gemstone Lid",
           "Tapestry Woven with Silver Thread Depicting a Celestial Map"],
    5000: ["A Chandelier of Rock Crystal and Gold Said to Have Lit a Royal Coronation",
           "A Full-Length Portrait of a Monarch Painted on Gold Leaf and Framed in Platinum",
           "A Life-Size Marble Falcon with Sapphire Eyes on an Onyx Plinth",
           "A Throne of Solid Silver Engraved with a Dynasty's Battle History",
           "An Altar Cloth Woven from Cloth-of-Gold and Seeded with Pearls",
           "An Ancient Mithral Harp Strung with Platinum Wire Still in Perfect Tune",
           "An Emperor's Funeral Mask in Beaten Gold with Jade Inlays",
           "Bejeweled Ivory Drinking Horn with Gold Filigree",
           "Gold Cup Set with Emeralds",
           "Gold Jewelry Box with Platinum Filigree",
           "Jade Game Board with Solid Gold Playing Pieces",
           "Jeweled Gold Crown",
           "Jeweled Platinum Ring",
           "Jeweled Scepter with a Large Central Sapphire and Flanking Diamonds",
           "Platinum Reliquary Studded with Sapphires",
           "Small Gold Statuette Set with Rubies"],
}


# ── Jewelry ───────────────────────────────────────────────────────────────────
# Tiers: 25 / 100 / 250 / 500 / 1000 / 2500 / 5000 gp
# All names Title Cased and sorted alphabetically within each tier.

JEWELRY = {
    25:   ["A Braided Horsehair Bracelet with a Copper Charm",
           "A Braided Leather Band Set with a Single Polished Agate",
           "A Carved Wooden Pendant on a Waxed Cord",
           "A Copper Cuff Bracelet with Punch-Dot Decoration",
           "A Copper Nose Ring with a Tiny Turquoise Bead",
           "A Pewter Brooch in the Shape of a Running Fox",
           "A Plain Silver Ring",
           "A Polished Bone Ring Carved with Simple Spirals",
           "A Sailor's Knotwork Ring Woven from Silver Wire",
           "A Set of Carved Horn Hairpins",
           "A Simple Iron Armband Worked to Resemble a Serpent",
           "A Small Pewter Pendant Shaped Like an Anchor",
           "A String of Matched Glass Beads",
           "A Tin Locket Containing a Pressed Flower"],
    100:  ["A Bone Cameo Brooch in a Silver Bezel",
           "A Carved Jet Ring on a Simple Gold Band",
           "A Copper and Amber Pendant on a Leather Cord",
           "A Gold Toe Ring with a Chased Wave Pattern",
           "A Gold-Plated Copper Locket with a Painted Portrait Inside",
           "A Pair of Gold Stud Earrings Set with Tiny Garnets",
           "A Pair of Small Silver Hoop Earrings",
           "A Silver Ankle Chain Hung with Tiny Bells",
           "A Silver Thumb Ring with a Rope-Twist Pattern",
           "A Simple Gold Ring with No Gemstone",
           "A Thin Gold Chain Necklace",
           "A Twisted Silver Wire Bracelet",
           "An Enameled Gold Brooch in the Shape of a Four-Leaf Clover",
           "An Onyx Signet Ring in Polished Silver"],
    250:  ["A Braided Gold-and-Silver Torque",
           "A Coral Bead Necklace with a Gold Clasp",
           "A Filigree Silver Bracelet with Moonstone Cabochons",
           "A Gilded Bronze Torque with Zoomorphic Terminals",
           "A Gold Nose Stud Set with a Tiny Ruby Chip",
           "A Gold Signet Ring with an Intaglio Crest",
           "A Jade Bangle Polished to a Deep Green Luster",
           "A Matched Pair of Copper and Turquoise Earrings",
           "A Pair of Silver Drop Earrings Set with Amber",
           "A Pearl Drop Pendant on a Fine Silver Chain",
           "A Silver Hair Comb Set with a Row of Seed Pearls",
           "A Silver Locket Etched with a Sailing Ship",
           "A Silver Ring Set with a Faceted Garnet",
           "An Amethyst Pendant in a Twisted Gold Setting",
           "An Electrum Ring Set with a Carved Bloodstone"],
    500:  ["A Gilded Copper Headband Set with Polished Garnets",
           "A Gold Belt Chain Hung with Seven Carnelian Drops",
           "A Gold Charm Bracelet with Seven Small Gold Charms",
           "A Pair of Coral Drop Earrings in Silver Settings",
           "A Pair of Jade Ear Studs Capped in Gold",
           "A Pair of Silver Cufflinks Set with Polished Onyx",
           "A Pearl Choker on a Silver Thread with a Gold Clasp",
           "A Rose-Gold Ring Set with a Trio of Spinels",
           "A Silver Cloak Pin Set with a Faceted Blue Topaz",
           "A Silver Collar Set with Tumbled Amethysts",
           "A Silver Ring Set with a Polished Moonstone",
           "An Electrum Pendant Necklace Set with Carnelian",
           "An Electrum Signet Ring with a Carved Family Initial",
           "An Opal Cabochon Brooch Rimmed with Silver Leaves"],
    1000: ["A Braided Gold Bracelet with a Sapphire Clasp",
           "A Delicate Platinum Anklet Set with Seed Pearls",
           "A Filigree Gold Tiara Set with Amethysts",
           "A Gold Armband Worked as a Dragon Biting Its Tail with Emerald Eyes",
           "A Gold Choker Set with Alternating Rubies and Emeralds",
           "A Gold Ring Set with a Star Sapphire",
           "A Jet and Gold Mourning Locket Containing a Lock of Hair",
           "A Malachite Cameo in a Detailed Gold Setting",
           "A Matched Pair of Emerald Drop Earrings in Gold",
           "A Pair of Gold Chandelier Earrings Hung with Amethyst Briolettes",
           "A Pearl-Studded Gold Hairnet",
           "A Ruby Cabochon Set in a Gold Ring",
           "An Alexandrite Ring in a Scrollwork Gold Band",
           "An Amber and Gold Pendant Necklace",
           "An Opal Ring Flanked by Twin Diamonds in Gold"],
    2500: ["A Black Pearl Pendant on a Platinum Chain",
           "A Collar of Gold Set with Nine Graduated Emeralds",
           "A Gold Tiara Set with a Spray of Sapphires and Pearls",
           "A Heavily-Worked Emerald and Gold Bangle",
           "A Necklace of Graduated Rubies in Gold",
           "A Pair of Matched Star Sapphire Cufflinks",
           "A Pair of Platinum Combs Set with Star Sapphires",
           "A Pair of Ruby Drop Earrings in Gold with Diamond Accents",
           "A Platinum Choker Set with Alternating Sapphires and Diamonds",
           "A Platinum Ring Set with a Large Alexandrite",
           "A Sapphire and Diamond Necklace",
           "A Star Ruby Ring in Platinum with a Tiny Diamond Surround",
           "A Wide Hammered-Gold Arm-Torc Set with a Sunburst of Citrines",
           "An Armlet of White Gold Set with a Black Opal"],
    5000: ["A Bracelet of Entwined Mithral and Gold Set with Rubies",
           "A Diamond Tiara in the Old Imperial Style",
           "A Fire Opal Ring in Platinum with a Diamond Halo",
           "A Girdle of Gold Plaques Each Set with a Different Precious Gem",
           "A Grand Duchess's Brooch Featuring an Immense Blue Sapphire",
           "A Pair of Diamond Cluster Earrings with Detachable Emerald Drops",
           "A Platinum Collar Set with a Row of Flawless Rubies",
           "A Platinum Diadem Set with a Rare Alexandrite of Extraordinary Size",
           "A Ruby and Diamond Parure (Necklace, Bracelet, and Earrings)",
           "A Strand of Matched Black Pearls with a Ruby Clasp",
           "An Antique Collar of Emeralds and Diamonds in Gold",
           "An Opera-Length Strand of Perfectly Matched Pearls"],
}


# ── Trade Goods ───────────────────────────────────────────────────────────────
# Tiers: 10 / 50 / 100 / 500 / 1000 / 2500 gp
# All names Title Cased and sorted alphabetically within each tier.

TRADE_GOODS = {
    10:   ["A Bag of Coarse Salt (10 lbs.)",
           "A Bolt of Undyed Linen (10 Yards)",
           "A Bundle of Cured Tobacco Leaf (5 lbs.)",
           "A Bundle of Dried Herbs and Simples",
           "A Coil of Good Hemp Rope (50 ft.)",
           "A Crate of Common Pottery (12 Pieces)",
           "A Jar of Pickled Fish (Sealed)",
           "A Pouch of Dried Mushrooms",
           "A Sack of Milled Oats (20 lbs.)",
           "A Sack of Mixed Peppercorns (1 lb.)",
           "A Skein of Homespun Wool Yarn (Dyed Madder Red)",
           "A Small Cask of Cooking Lard",
           "A Small Jug of Cheap Table Wine",
           "A Wrapped Block of Beeswax"],
    50:   ["A Bolt of Dyed Wool in Deep Indigo",
           "A Box of Cedar and Clove Incense Sticks (30 Count)",
           "A Cake of Pressed Tea (1 lb.)",
           "A Jar of Preserved Lemons in Brine",
           "A Pouch of Dried Cinnamon Sticks",
           "A Pouch of Dried Star Anise",
           "A Pouch of Dried Vanilla Pods",
           "A Roll of Oilskin Cloth",
           "A Sealed Jar of Fine Olive Oil",
           "A Small Cask of Honey Mead",
           "A Small Crate of Quality Wax Candles",
           "A Small Keg of Quality Ale",
           "A Small Vial of Saffron Threads",
           "A Stoppered Flask of Turpentine (Alchemical Grade)"],
    100:  ["A Bag of Cacao Beans (5 lbs.)",
           "A Bolt of Raw Silk",
           "A Box of Pressed Incense Cakes (Temple Grade)",
           "A Bundle of Rare Hardwood (Ebony Heartwood)",
           "A Cask of Northern Whisky (Aged Ten Years)",
           "A Lacquered Chest of Quality Tea Leaves",
           "A Packet of Alchemical Reagents with Cryptic Notes",
           "A Phial of Frankincense Oil",
           "A Pound of Quality Indigo Dye",
           "A Sealed Crock of Rare Honey",
           "A Sealed Tin of Quality Pipe-Weed Blend",
           "A Small Keg of Fine Red Wine",
           "A Small Pouch of Powdered Cinnamon and Cardamom",
           "A Wheel of Cave-Aged Cheese in Wax"],
    500:  ["A Bale of Snow-White Ermine Pelts (12 Count)",
           "A Bolt of Fine Silk Brocade",
           "A Carved Ivory Box Filled with Rare Spices",
           "A Case of Blown-Glass Alchemical Vessels (Master-Made)",
           "A Cask of Aged Brandy",
           "A Cask of High-Proof Spirits",
           "A Chest of Genuine Saffron (2 lbs.)",
           "A Crate of Dragonpepper Pods (Sealed Against Moisture)",
           "A Packet of Quality Alchemical Reagents with Notes",
           "A Phial of Ambergris Tincture",
           "A Sealed Box of Precious Imported Dyes",
           "A Small Chest of Polished Amber Chunks"],
    1000: ["A Bolt of Pure Spidersilk (10 Yards)",
           "A Cask of Legendary Aged Spirit from a Renowned Distillery",
           "A Coffer of Purple Murex Dye (Enough for a Royal Robe)",
           "A Crate of Star-Metal Filings (3 lbs.)",
           "A Half-Dozen Amphorae of Ancient Vintage Wine",
           "A Phial of Concentrated Alchemical Catalyst",
           "A Roll of Gilded Leather (Tooled and Ready for Binding)",
           "A Sealed Chest of Rare Imported Spice Blends",
           "A Set of Masterwork Surgical Instruments in a Fitted Case",
           "A Small Ingot of Raw Silver (5 lbs.)",
           "A Strongbox of Refined Alchemical Quicksilver",
           "A Velvet-Lined Case of Masterwork Clockwork Components"],
    2500: ["A Banded Chest of Adamantine Filings (1 lb.)",
           "A Bolt of Cloth-of-Gold (10 Yards)",
           "A Bolt of Shimmerweave Cloth (8 Yards)",
           "A Cask of Elven Dessert Wine (Century Vintage)",
           "A Cask of Legendary Vintage Wine",
           "A Chest of Imported Spices Worth a Fortune in the Right Market",
           "A Phial of Pure Ambergris",
           "A Pouch of Mithral Dust (1 oz.)",
           "A Roll of Sea-Silk Harvested from Deep-Sea Creatures",
           "A Sealed Lead Box of Volatile Alchemical Ingredients",
           "A Small Ingot of Electrum",
           "A Small Ingot of Refined Mithral"],
}


# ── Curiosities ───────────────────────────────────────────────────────────────
# Tiers: 0 / 10 / 25 / 50 / 100 / 250 / 500 / 1000 / 2500 gp
# 0/10/25 tiers contain trinkets — mundane-odd items with no confirmed magic,
# good for character flavor, starting gear, and low-CR loot.
# All names Title Cased and sorted alphabetically within each tier.

CURIOSITIES = {
    0:    ["A Boot with No Match, Sized for a Foot with Six Toes",
           "A Bottle Stopper in the Shape of a Weeping Woman",
           "A Brass Doorknob That Is Always Locked Even Though It Has No Door",
           "A Brass Ring Engraved with the Word 'Remember' and Nothing Else",
           "A Bundle of Crow Feathers Tied with Red String",
           "A Charcoal Portrait of a Group of People You Have Never Met",
           "A Chess Piece (a Knight) Fashioned Entirely from Teeth",
           "A Child's Drawing of a Figure with Wings, Labeled 'Mother'",
           "A Child's Knitted Sock, Far Too Small for Any Known Child",
           "A Child's Wooden Toy Carved into a Dragon",
           "A Coin with the Same Face on Both Sides",
           "A Deck of Cards Missing Every Queen",
           "A Dried Apple Core with a Tiny Face Carved into One Side",
           "A Dried Seahorse Tied with Sailor's Rope",
           "A Dried Starfish with Six Arms Arranged Unnaturally Evenly",
           "A Flint Arrowhead Tied to a Sprig of Dried Holly",
           "A Fragment of Stained Glass from a Destroyed Temple",
           "A Handkerchief Embroidered with a Coat of Arms No One Recognizes",
           "A Letter Opener Engraved with the Words 'For Emergencies Only'",
           "A Lock of Silvery Hair Tied with a Black Ribbon",
           "A Set of Teeth on a String, Each from a Different Creature",
           "A Set of Three Brass Buttons, Each Engraved with a Different Animal",
           "A Shard of Bone Carved into the Shape of a Sleeping Cat",
           "A Single Playing Card — the Jack of Blades, from a Deck No One Recognizes",
           "A Small Cloth Doll with a Pin Through Its Heart",
           "A Small Leather Pouch Containing Seven Perfectly Round River Stones",
           "A Small Stone Idol of an Unknown Deity",
           "A Spool of Thread That Appears to Be Spun Gold, Only One Yard Remaining",
           "A Stone Carving of a Hand Making an Obscene Gesture, Exquisitely Crafted",
           "A Strip of Cloth from a Wedding Dress, Badly Bloodstained at the Hem",
           "A Thumb-Sized Brass Statue of a Cat in a Regal Sitting Pose",
           "A Tiny Bronze Shield Too Small for Any Purpose, Engraved with a Heraldic Boar",
           "A Tooth on a Chain — Too Large to Be Human, Too Small to Be Anything Familiar",
           "A Wig of Human Hair That Never Tangles",
           "An Origami Crane Made from a Page Torn Out of a Holy Book"],
    10:   ["A Ball of Twine That Has Never Been Successfully Unwound to Its End",
           "A Brass Padlock That Locks Itself at Sunset",
           "A Broken Pocket Sundial That Still Casts a Shadow at Midnight",
           "A Carved Bone Whistle That Makes No Sound Anyone Else Can Hear",
           "A Child's Music Box That Plays a Lullaby with Too Many Notes",
           "A Coil of Fishing Line with a Hook and a Note Reading 'Don't Use This in Rivers'",
           "A Compass Rose Torn from a Larger Map, with One Direction Blacked Out",
           "A Copper Coin from a Kingdom That Never Existed",
           "A Dried Ear, Very Old, with a Gold Earring Still Attached",
           "A Folded Note Reading 'I'm Sorry' — the Handwriting Is Your Own",
           "A Glass Bead That Swirls with Color When Submerged in Water",
           "A Glass Vial Containing a Single Perfectly Preserved Tear",
           "A Letter in a Language No One Recognizes",
           "A Loop of Braided Copper Wire That Hums Faintly in the Dark",
           "A Mummified Goblin Hand That Slowly Curls Its Fingers When Held",
           "A Perfect Black Feather That Smells Faintly of Sulfur",
           "A Perfect Sphere of Black Glass That Reflects No Light",
           "A Piece of Crystal That Faintly Glows in the Moonlight",
           "A Piece of Obsidian Shaped Like a Teardrop, Always Cold to the Touch",
           "A Pocket Watch That Runs Backwards",
           "A Pocket-Sized Portrait Frame That Is Always Slightly Warm on the Back",
           "A Pressed Flower from a Plant That Doesn't Grow in Any Known Region",
           "A Recipe Written in Blood on a Scrap of Parchment — for Soup",
           "A Rusted Key to a Lock That Doesn't Exist Yet",
           "A Scroll Containing a Single Musical Note, Transcribed Obsessively 400 Times",
           "A Small Book Filled with Sketches of Faces — None of Them Have Eyes",
           "A Small Copper Pot That Is Always Faintly Warm and Smells of Cinnamon",
           "A Small Jar of Grave Dirt Labeled with the Name of a City That Burned Down",
           "A Small Silver Bell That Makes No Sound When Rung",
           "A Smooth River Stone with a Spiral Pattern That Wasn't There When You First Found It",
           "A Snakeskin Wallet, Always Slightly Heavier Than It Should Be",
           "A Spectacularly Ugly Brooch in the Shape of a Frog, Inexplicably Expensive-Looking",
           "A Stoppered Vial Labeled 'Happy,' Containing a Golden Liquid That Evaporates When Opened",
           "A Swatch of Fur from an Animal That Walked on Two Legs",
           "A Tiny Iron Box That Is Always Warm to the Touch, Though Nothing Is Inside",
           "A Vial of Black Sand That Never Settles",
           "A Wax Seal Impression from a Noble House Wiped Out a Century Ago",
           "A Whistle Carved from a Gallows Beam That Dogs Refuse to Approach",
           "A Wooden Handle with No Blade, Paired with a Scabbard That Fits Perfectly",
           "A Worn Coin with a Hole Drilled Through It and a Faded Rune on Each Face",
           "An Empty Bottle That Smells of a Different Perfume Each Time It Is Opened",
           "An Old Military Medal from a War Two Centuries Ago, Still Polished Bright"],
    25:   ["A Bar of Soap That Never Gets Smaller No Matter How Often It Is Used",
           "A Candle That Will Not Light but Casts a Faint Shadow Anyway",
           "A Ceramic Whistle Shaped Like a Bird That Actually Summons Birds",
           "A Child's Marble That Shows a Different Tiny Landscape Each Time You Look Closely",
           "A Copper Coin That Always Returns to Your Pocket Within a Day of Being Spent",
           "A Cracked Compass That Always Points Toward the Nearest City",
           "A Dried Flower That Blooms When Held by Someone Who Is Lying",
           "A Fragment of a Map Showing an Island That Appears on No Known Chart",
           "A Glass Eye That Seems to Track Movement on Its Own",
           "A Key That Fits Every Lock but Opens None of Them",
           "A Leather-Bound Book Where Every Page Is Blank Except the Last, Which Has Your Name",
           "A Length of Black Thread That Ties Itself in Knots Overnight",
           "A Length of Rope, Only Six Inches Long, Which Cannot Be Cut by Any Blade",
           "A Locket Containing a Portrait of a Stranger — and a Lock of Your Own Hair",
           "A Map to a Location That Shifts One Inch South Every Day",
           "A Pair of Spectacles That Make Everything Look Slightly More Sinister",
           "A Perfectly Preserved Butterfly Pinned to Velvet, Still Alive by All Appearances",
           "A Playing Card Whose Face Slowly Changes to Resemble Whoever Holds It",
           "A Quill Whose Ink Dries in a Color Matching the Writer's Mood",
           "A Sealed Scroll Whose Wax Seal Reforms Every Time It Is Broken",
           "A Single Die That Always Rolls a Six",
           "A Small Golden Bee with Ruby Eyes, Twice as Heavy as It Should Be",
           "A Small Mirror That Shows the Viewer Ten Seconds in the Past",
           "A Snow Globe Containing a Village No One Can Identify — Sometimes Its Windows Are Lit",
           "A Thin Glass Rod That Vibrates When Pointed North-North-East",
           "A Tiny Compass That Points Toward Whatever You're Most Afraid Of",
           "A Tiny Painting of a Door That Appears in a Different Room of Your Dreams Each Night",
           "A Tiny Portrait of an Elderly Man Who Looks Impossibly Familiar",
           "A Tiny Stoppered Bottle with a Miniature Ship Inside That Sails on Its Own",
           "A Wooden Mask with a Painted Smile That Has Moved Since You Last Looked",
           "An Hourglass Filled with What Appears to Be Solidified Moonlight",
           "An Unlit Lantern That Fills with Soft Light When You Whisper a Secret to It"],
    50:   ["A Brass Compass Whose Needle Points Toward the Nearest Lie",
           "A Bronze Bell That Rings Only in the Presence of Active Magic",
           "A Candle Snuffer That Extinguishes Flames a Heartbeat Before It Touches Them",
           "A Candle That Burns with a Cold Blue Flame and Casts No Shadows",
           "A Child's Wooden Top That Spins Forever Without Slowing",
           "A Clay Tablet Impressed with a Star Map That Matches No Known Sky",
           "A Dried Flower That Smells of a Different Season Each Hour",
           "A Glass Eye That Weeps Real Tears When Held by Someone Grieving",
           "A Journal Written Entirely in a Cipher No Sage Has Cracked",
           "A Large Iron Key That Opens No Known Lock",
           "A Map Drawn on Preserved Skin; All Landmarks Are Unknown",
           "A Music Box That Plays a Different Tune Each Time It Is Opened",
           "A Playing Card That Changes Suit Silently Each Dawn",
           "A Set of Wind Chimes That Ring Only When Someone Speaks a Name Aloud",
           "A Stoppered Vial Containing a Tiny, Perpetual Thunderstorm",
           "A Tin Soldier That Changes Its Stance When No One Watches",
           "A Worn Coin Stamped with the Face of a God No One Recognizes",
           "An Abacus Whose Beads Slide to Answer Sums No One Asked",
           "An Hourglass Filled with Black Sand That Flows Slowly Upward"],
    100:  ["A Bell Jar Containing a Wisp of Fog That Rearranges Itself into Shapes",
           "A Blank Book That Smells Strongly of a Library Fire",
           "A Bootlace That Unties Itself Only at the Worst Possible Moment",
           "A Brass Box That Hums Faintly When Opened and Falls Silent When Touched",
           "A Button Carved from an Unidentifiable Dark Material",
           "A Compass That Always Points Toward the Nearest Body of Water",
           "A Leather Purse That Always Feels Lighter Than It Should",
           "A Monocle That Makes Everything Look Slightly Younger",
           "A Pincushion Shaped Like a Hedgehog That Squeaks When Storms Approach",
           "A Sealed Letter Addressed to Someone Named 'T. Voss'",
           "A Small Fork That Is Always Slightly Warm",
           "A Small Glass Sphere That Fogs from Within When Touched",
           "A Vial of Red Liquid That Evaporates When Exposed to Air",
           "An Iron Nail Pulled from a Ghost Ship — Always Cold and Slightly Wet"],
    250:  ["A Brass Cylinder Containing a Message in a Language Not Yet Invented",
           "A Candlestick That Burns Any Candle Twice as Long",
           "A Deck of Cards Where Every Card Is the Same — the Three of Clubs",
           "A Door Knocker Shaped Like a Sleeping Face That Wakes to Announce Visitors",
           "A Hand Mirror That Shows the Viewer as They Will Look in Ten Years",
           "A Pair of Iron Shackles with No Keyhole That Open When Commanded",
           "A Pocket Watch Frozen at the Exact Same Time for over a Century",
           "A Portrait Whose Painted Subject's Eyes Follow the Viewer",
           "A Prism That Casts Darkness Instead of Rainbows",
           "A Riding Crop That Makes Any Horse Slightly Braver",
           "A Silver Spoon That Tarnishes Black in the Presence of Poison",
           "A Small Golden Cage Containing a Feather That Floats Against Gravity",
           "A Smooth Stone That Whispers Softly When Clutched in a Fist",
           "A Thimble That Fills with Fresh Water Each Morning",
           "A Vial of Ink Visible Only by Moonlight",
           "A Wax Seal Stamp Bearing the Sigil of a Civilization Thought Extinct",
           "An Astrolabe That Tracks a Star No Astronomer Can Find"],
    500:  ["A Bottle of Perfume That Smells Like a Different Cherished Memory to Each Person",
           "A Coin That Always Lands on Its Edge When Dropped",
           "A Compass Needle That Points Toward the Nearest Person Who Means You Harm",
           "A Folded Map Whose Roads Rearrange Themselves Each Time It Is Unfolded",
           "A Hand Bell Whose Ring Is Heard Only by the Person It Is Rung For",
           "A Locket That Shows a Vision of the Person Who Last Held It Before You",
           "A Pair of Dice That Always Sum to 7 No Matter How They Are Thrown",
           "A Quill That Writes Whatever the Holder Is Thinking, Unbidden",
           "A Shard of Mirror That Reflects a Room Different from the One You Are In",
           "A Silver Whistle That Produces No Sound Audible to Humans",
           "A Skeleton Key Made of Ice That Never Melts but Opens Nothing Yet Found",
           "A Small Clay Effigy That Melts in Water and Re-Forms Each Morning",
           "An Embroidery Hoop Where Half-Finished Scenes Complete Themselves Overnight",
           "An Ink Bottle That Writes Out a Warning Before Sealing Itself When Opened"],
    1000: ["A Cartographer's Pen That Corrects Small Errors in Any Map It Touches",
           "A Celestial Globe That Rotates on Its Own at Precisely One Revolution per Day",
           "A Chess Set Whose Pieces Rearrange Themselves to a New Game Each Night",
           "A Clockwork Beetle of Extraordinary Craft That Moves When No One Is Looking",
           "A Crystal Skull Filled with Luminescent Slowly-Swirling Silver Fog",
           "A Lantern Showing the Room as It Appeared One Hundred Years Ago When Lit",
           "A Length of Rope That Ties Itself in the Same Complex Knot Every Morning",
           "A Music Box That Plays the Song Your Mother Hummed — Even If You Never Knew Her",
           "A Pair of Silver Scissors That Cut Only Shadows",
           "A Preserved Eye from a Creature No Naturalist Has Catalogued",
           "A Sealed Jar Containing a Perfectly Preserved Homunculus",
           "A Ship in a Bottle Whose Tiny Crew Appear Frozen Mid-Panic",
           "A Sundial That Casts Its Shadow by Moonlight",
           "An Inkwell That Refills Itself Each Dawn with Ink of a Random Color"],
    2500: ["A Birdcage That Keeps Whatever Sleeps Inside It Ageless",
           "A Black Candle That Reveals Invisible Writing on Nearby Surfaces",
           "A Book Whose Pages Fill with the Reader's Own Memories as They Read",
           "A Chessboard on Which Games Play Out Foretelling Distant Battles",
           "A Clockwork Heart That Beats Once per Minute and Quickens Under Stress",
           "A Compass That Always Points Toward the Bearer's Greatest Desire",
           "A Lantern That Illuminates Only What the Bearer Most Fears to See",
           "A Looking Glass That Reflects the Viewer's Truest Self — Most Refuse a Second Look",
           "A Mirror That Reflects Only the Room, Never Any People Standing Before It",
           "A Rolled Tapestry Depicting Tomorrow's Sunrise in Exact Detail",
           "A Silver Locket Containing a Miniature Landscape of a Place No One Can Find",
           "A Sphere of Clear Glass Containing a Tiny Storm That Reacts to Emotions",
           "An Ancient Crown of Blackened Silver That Fits the Head of Every Wearer Perfectly",
           "An Orrery of an Unknown Planetary System That Adjusts Itself as Though Observed"],
}


# ── Rolling helpers ───────────────────────────────────────────────────────────

def roll_individual_coins(cr_band: str) -> dict:
    table = INDIVIDUAL_BY_CR[cr_band]
    roll = random.randint(1, 100)
    coins_def = lookup_range(table, roll)
    return {k: roll_coins(*v) for k, v in coins_def.items()}


def roll_hoard_coins(cr_band: str) -> dict:
    coins_def = HOARD_COINS_BY_CR[cr_band]
    return {k: roll_coins(*v) for k, v in coins_def.items()}


def roll_gems(value_tier: int, count: int) -> list:
    pool = GEMS.get(value_tier, [])
    return [random.choice(pool) for _ in range(count)] if pool else []


def roll_art(value_tier: int, count: int) -> list:
    pool = ART_OBJECTS.get(value_tier, [])
    return [random.choice(pool) for _ in range(count)] if pool else []


def roll_jewelry(value_tier: int, count: int) -> list:
    pool = JEWELRY.get(value_tier, [])
    return [random.choice(pool) for _ in range(count)] if pool else []


def roll_trade_goods(value_tier: int, count: int) -> list:
    pool = TRADE_GOODS.get(value_tier, [])
    return [random.choice(pool) for _ in range(count)] if pool else []


def roll_curiosities(value_tier: int, count: int) -> list:
    pool = CURIOSITIES.get(value_tier, [])
    return [random.choice(pool) for _ in range(count)] if pool else []


# Memo for pick_magic_item: (items_all reference, {rarity_lower: [names]}).
# Hoard rolls call pick_magic_item in a loop with the same list object, and
# rescanning all 2,300+ magic items per roll is wasted work — this groups them
# once per list object instead. Keyed on identity, so a different list (new
# rerun, changed data file) simply rebuilds the pools; correctness never
# depends on the memo being warm.
_MAGIC_POOLS: tuple | None = None


def _rarity_pools(items_all: list) -> dict:
    """Group item names by lowercased rarity, memoised per items_all object."""
    global _MAGIC_POOLS
    # Read the global once into a local — Streamlit serves multiple sessions from
    # threads in one process, so a concurrent call can reassign _MAGIC_POOLS for a
    # different items_all between our check and our return. Always return the
    # pools we just computed for OUR items_all, never re-read the (possibly
    # since-overwritten) global.
    cached = _MAGIC_POOLS
    if cached is not None and cached[0] is items_all:
        return cached[1]
    pools: dict[str, list] = {}
    for it in items_all:
        pools.setdefault(it.get("rarity", "").lower(), []).append(it["name"])
    _MAGIC_POOLS = (items_all, pools)
    return pools


def pick_magic_item(rarity: str | None, items_all: list) -> str | None:
    if rarity is None or not items_all:
        return None
    pool = _rarity_pools(items_all).get(rarity.lower())
    return random.choice(pool) if pool else f"[{rarity} magic item — none in data]"


def roll_individual_treasure(cr_band: str, cr_float: float = None) -> dict:
    """Roll complete individual monster treasure.

    cr_band  — used for the coin table lookup.
    cr_float — used for the extras formula (how many items, which tier).
               Defaults to the band's representative midpoint if omitted.

    Returns dict with "coins" (dict) and five lists:
    "gems", "arts", "jewels", "trades", "curiosities"  — each is a list of (name, gp_value).
    """
    if cr_float is None:
        cr_float = BAND_MIDPOINTS.get(cr_band, 0.0)

    coins = roll_individual_coins(cr_band)

    # Counts scale steeply: threshold sets the CR at which extras start appearing;
    # scale controls the rate. CR 10 → ~3 gems; CR 20 → ~15; CR 30 → ~31.
    gem_n  = _roll_count(_extra_count(cr_float, 5,  4.0))
    art_n  = _roll_count(_extra_count(cr_float, 5,  5.0))
    jew_n  = _roll_count(_extra_count(cr_float, 6,  6.0))
    trd_n  = _roll_count(_extra_count(cr_float, 9,  8.0))
    cur_n  = _roll_count(_extra_count(cr_float, 8, 10.0))  # starts at CR 8 for trinket-tier finds

    gems, arts, jewels, trades, curs = [], [], [], [], []
    for _ in range(gem_n):
        t = _gem_tier_at_cr(cr_float);  n = roll_gems(t, 1);  gems.append((n[0], t)) if n else None
    for _ in range(art_n):
        t = _art_tier_at_cr(cr_float);  n = roll_art(t, 1);   arts.append((n[0], t)) if n else None
    for _ in range(jew_n):
        t = _jewelry_tier_at_cr(cr_float); n = roll_jewelry(t, 1); jewels.append((n[0], t)) if n else None
    for _ in range(trd_n):
        t = _trade_tier_at_cr(cr_float); n = roll_trade_goods(t, 1); trades.append((n[0], t)) if n else None
    for _ in range(cur_n):
        t = _curiosity_tier_at_cr(cr_float); n = roll_curiosities(t, 1); curs.append((n[0], t)) if n else None

    return {"coins": coins, "gems": gems, "arts": arts,
            "jewels": jewels, "trades": trades, "curiosities": curs}


def coins_to_gp(coins: dict) -> float:
    return (coins.get("cp",0)*0.01 + coins.get("sp",0)*0.1 + coins.get("ep",0)*0.5
            + coins.get("gp",0) + coins.get("pp",0)*10)


def add_coins(a: dict, b: dict) -> dict:
    return {k: a.get(k,0) + b.get(k,0) for k in ["cp","sp","ep","gp","pp"]}


# ── Loot display helper ───────────────────────────────────────────────────────

def loot_section(label: str, items: list, approx: bool = False):
    """Render one treasure category as a bulleted point-form list.

    Shared by TreasureGenerator and EncounterBuilder so both pages format loot
    identically (page files can't import from each other, so it lives here).
    Duplicates are collapsed to ×N, entries sorted alphabetically by name.
    approx=True prepends '~' to values (used for Curiosities).
    0 gp items display as 'worthless' rather than '~0 gp'.
    """
    import streamlit as st  # lazy — keeps this module importable outside the app (tests, scripts)

    if not items:
        return
    counts = Counter(items)  # (name, value) → count
    st.markdown(f"**{label}:**")
    for (name, value), n in sorted(counts.items(), key=lambda kv: kv[0][0]):
        if value == 0:
            val_str = "worthless"
        else:
            prefix = "~" if approx else ""
            val_str = f"{prefix}{value:,} gp"
        if n > 1:
            st.markdown(f"- {name} ×{n} ({val_str} each)")
        else:
            st.markdown(f"- {name} ({val_str})")
