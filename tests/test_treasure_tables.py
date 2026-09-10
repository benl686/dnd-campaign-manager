"""Invariant tests for treasure_tables.py.

These encode the documented rules from CLAUDE.md (tier system, item naming,
coin scaling) so that table edits that silently break them fail CI instead of
producing wrong loot at the table.
"""

import pytest

import treasure_tables as t

# The clean round-number tier set every category must draw from.
# 0 is allowed only for Curiosities (worthless knick-knacks).
ALLOWED_TIERS = {0, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000}

CATEGORY_POOLS = {
    "GEMS":        t.GEMS,
    "ART_OBJECTS": t.ART_OBJECTS,
    "JEWELRY":     t.JEWELRY,
    "TRADE_GOODS": t.TRADE_GOODS,
    "CURIOSITIES": t.CURIOSITIES,
}

# HOARD_AUTO_ROLLS category key → item-pool dict its tiers must exist in
_AUTO_ROLL_POOLS = {
    "gems":    t.GEMS,
    "art":     t.ART_OBJECTS,
    "jewelry": t.JEWELRY,
    "trade":   t.TRADE_GOODS,
    "curs":    t.CURIOSITIES,
}


# ── Tier system ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,pool", CATEGORY_POOLS.items())
def test_tiers_are_clean_round_numbers(name, pool):
    assert set(pool) <= ALLOWED_TIERS, f"{name} has off-menu tiers"


def test_zero_tier_only_in_curiosities():
    for name, pool in CATEGORY_POOLS.items():
        if name != "CURIOSITIES":
            assert 0 not in pool, f"{name} must not have a 0 gp tier"


# ── Item naming rules ─────────────────────────────────────────────────────────

def _strip_parens(name: str) -> str:
    """Drop parenthesised qualifiers — 'Garnet (Tsavorite, Fine)' → 'Garnet '."""
    import re
    return re.sub(r"\([^)]*\)", "", name)


@pytest.mark.parametrize("name", ["GEMS", "TRADE_GOODS"])
def test_convention_named_items_have_no_prose_commas(name):
    # Gem/trade names follow 'Mineral (Variety, Quality)' — commas belong ONLY
    # inside the parentheses. Art/Jewelry/Curiosities are descriptive prose and
    # are exempt (see CLAUDE.md treasure item naming convention).
    pool = CATEGORY_POOLS[name]
    bad = [i for tier in pool.values() for i in tier if "," in _strip_parens(i)]
    assert not bad, f"{name} items have commas outside parentheses: {bad[:5]}"


@pytest.mark.parametrize("name,pool", CATEGORY_POOLS.items())
def test_items_sorted_alphabetically_within_tiers(name, pool):
    for tier, items in pool.items():
        assert items == sorted(items), f"{name}[{tier}] is not alphabetically sorted"


@pytest.mark.parametrize("name,pool", CATEGORY_POOLS.items())
def test_tiers_are_nonempty(name, pool):
    for tier, items in pool.items():
        assert items, f"{name}[{tier}] is empty"


# Real-world place/culture words that break immersion in a fantasy setting.
# Mineral trade names (Tsavorite, Tanzanite, Padparadscha…) are allowed per the
# CLAUDE.md naming convention — this list targets transparent Earth adjectives
# used as qualifiers or in prose names.
_REAL_WORLD_TERMS = [
    "Oregon", "Botswana", "Kashmir", "Siberi", "Paraiba", "Colombi", "Burm",
    "Ceylon", "Madagascar", "Brazil", "Africa", "Chinese", "Japan", "Egypt",
    "Persia", "Ottoman", "Venet", "Damascus", "Mahjong", "Empire-Style",
    "Aztec", "Viking", "Celtic", "Europe", "American", "Zultanite",
]


@pytest.mark.parametrize("name,pool", CATEGORY_POOLS.items())
def test_no_real_world_place_names(name, pool):
    bad = [i for tier in pool.values() for i in tier
           if any(w.lower() in i.lower() for w in _REAL_WORLD_TERMS)]
    assert not bad, f"{name} items reference real-world places: {bad[:5]}"


@pytest.mark.parametrize("name,pool", CATEGORY_POOLS.items())
def test_no_duplicate_names_across_tiers(name, pool):
    seen = {}
    for tier, items in pool.items():
        for i in items:
            assert i not in seen, f"{name}: '{i}' appears at tiers {seen[i]} and {tier}"
            seen[i] = tier


@pytest.mark.parametrize("name,pool", CATEGORY_POOLS.items())
def test_aka_bracket_format(name, pool):
    # Square brackets are reserved for common-name cross-references and must
    # follow the exact ' [aka X]' suffix format (no commas, end of name) so
    # they can't be confused with the (Variety, Quality) qualifiers.
    import re
    for tier, items in pool.items():
        for i in items:
            if "[" in i or "]" in i:
                assert re.search(r" \[aka [^,\[\]]+\]$", i), (
                    f"{name}[{tier}]: bad bracket format: {i}"
                )


# Common variety names that must appear only inside [aka …] brackets — the
# primary display name is always the proper mineral family (Corundum, Beryl,
# Quartz, …). Keeps the naming direction consistent: Corundum (Red) [aka Ruby].
_COMMON_VARIETY_NAMES = [
    "Ruby", "Sapphire", "Emerald", "Aquamarine", "Amethyst", "Citrine",
    "Carnelian", "Chrysoprase", "Bloodstone", "Onyx", "Sardonyx",
    "Alexandrite", "Tanzanite", "Kunzite", "Iolite", "Peridot", "Larimar",
    "Amazonite", "Aventurine", "Tiger Eye", "Morganite", "Heliodor",
    "Bixbite", "Selenite",
]


def test_gems_use_mineral_primary_names():
    for tier, items in t.GEMS.items():
        for i in items:
            primary = i.split(" [aka")[0]  # strip the cross-reference suffix
            for common in _COMMON_VARIETY_NAMES:
                assert not primary.startswith(common), (
                    f"GEMS[{tier}]: '{i}' uses common name as primary — "
                    f"should be mineral-family-first with [aka {common}]"
                )


@pytest.mark.parametrize("name,pool", CATEGORY_POOLS.items())
def test_article_grammar(name, pool):
    # 'A' before a vowel (except U — 'A Unicorn' is correct) or 'An' before a
    # consonant (except H — 'An Hourglass' is correct) is a typo.
    import re
    bad = [i for tier in pool.values() for i in tier
           if re.match(r"^A [AEIO]", i) or re.match(r"^An [^AEIOUH]", i)]
    assert not bad, f"{name} has A/An grammar slips: {bad[:5]}"


# ── Hoard tables reference valid tiers ────────────────────────────────────────

def test_hoard_auto_rolls_reference_existing_tiers():
    for band, alloc in t.HOARD_AUTO_ROLLS.items():
        for cat, pool in _AUTO_ROLL_POOLS.items():
            for row in alloc.get(cat, []):
                assert row["tier"] in pool, (
                    f"HOARD_AUTO_ROLLS[{band}][{cat}] uses tier {row['tier']} "
                    f"which does not exist in the {cat} pool"
                )


def test_hoard_tables_share_band_keys():
    assert list(t.HOARD_AUTO_ROLLS) == list(t.HOARD_MAGIC_BY_CR) == list(t.HOARD_COINS_BY_CR)


def test_hoard_band_function_maps_into_tables():
    for cr in [0, 0.125, 1, 4, 5, 10, 11, 16, 17, 20, 21, 24, 25, 30]:
        assert t.cr_float_to_hoard_band(cr) in t.HOARD_AUTO_ROLLS


# ── Individual treasure — d100 coverage and coin scaling ──────────────────────

def test_individual_bands_cover_d100_without_gaps():
    for band, rows in t.INDIVIDUAL_BY_CR.items():
        spans = sorted((lo, hi) for lo, hi, _ in rows)
        assert spans[0][0] == 1 and spans[-1][1] == 100, f"{band} does not span 1–100"
        for (lo1, hi1), (lo2, hi2) in zip(spans, spans[1:]):
            assert hi1 + 1 == lo2, f"{band} has a gap/overlap at {hi1}→{lo2}"


def _band_avg_gp(rows):
    """Probability-weighted expected gp value of one band's d100 table."""
    rates = {"cp": 0.01, "sp": 0.1, "ep": 0.5, "gp": 1, "pp": 10}
    total = 0.0
    for lo, hi, coins in rows:
        p = (hi - lo + 1) / 100
        row_avg = sum(n * (die + 1) / 2 * mult * rates[c]
                      for c, (n, die, mult) in coins.items() if n)
        total += p * row_avg
    return total


def test_individual_coin_averages_increase_with_cr():
    # Higher CR must unambiguously yield more coin (CLAUDE.md coin-scaling rule)
    avgs = [_band_avg_gp(rows) for rows in t.INDIVIDUAL_BY_CR.values()]
    for i in range(1, len(avgs)):
        assert avgs[i] > avgs[i - 1], (
            f"band {list(t.INDIVIDUAL_BY_CR)[i]} avg {avgs[i]:.1f} gp does not "
            f"exceed previous band avg {avgs[i-1]:.1f} gp"
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def test_cr_to_float():
    assert t.cr_to_float("1/2") == 0.5
    assert t.cr_to_float("1/8") == 0.125
    assert t.cr_to_float(5) == 5.0
    assert t.cr_to_float("30") == 30.0
    assert t.cr_to_float("garbage") == 0.0


def test_roll_helpers_draw_from_correct_tier():
    for tier, roll_fn, pool in [
        (100, t.roll_gems, t.GEMS),
        (250, t.roll_art, t.ART_OBJECTS),
        (250, t.roll_jewelry, t.JEWELRY),
    ]:
        names = roll_fn(tier, 5)
        assert len(names) == 5
        assert all(n in pool[tier] for n in names)


def test_roll_individual_treasure_shape():
    # Signature is (cr_band, cr_float) — use a real band key from the table
    band = [b for b in t.INDIVIDUAL_BY_CR if "9" in b][0]
    res = t.roll_individual_treasure(band, 10.0)
    assert set(res) == {"coins", "gems", "arts", "jewels", "trades", "curiosities"}
    assert set(res["coins"]) == {"cp", "sp", "ep", "gp", "pp"}


def test_coin_math():
    assert t.coins_to_gp({"cp": 100, "sp": 10, "ep": 2, "gp": 3, "pp": 1}) == 16.0
    assert t.add_coins({"gp": 5}, {"gp": 7, "pp": 1}) == {"cp": 0, "sp": 0, "ep": 0, "gp": 12, "pp": 1}
