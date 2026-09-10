"""Tests for character_lib.py — pure 5e rules constants and math."""

import character_lib as c

STANDARD_CLASSES = [cls for cls in c.CHAR_CLASSES if cls != "Other (custom)"]


def test_ability_mod():
    assert c.ability_mod(10) == 0
    assert c.ability_mod(8) == -1
    assert c.ability_mod(9) == -1
    assert c.ability_mod(11) == 0
    assert c.ability_mod(20) == 5
    assert c.ability_mod(30) == 10


def test_proficiency_bonus_breakpoints():
    # PHB progression: +2 at 1–4, +3 at 5–8, +4 at 9–12, +5 at 13–16, +6 at 17+
    for lvl, expected in [(1, 2), (4, 2), (5, 3), (8, 3), (9, 4), (12, 4),
                          (13, 5), (16, 5), (17, 6), (20, 6), (30, 6)]:
        assert c.proficiency_bonus(lvl) == expected, f"level {lvl}"


def test_class_save_profs_complete_and_valid():
    assert set(c.CLASS_SAVE_PROFS) == set(STANDARD_CLASSES)
    for cls, profs in c.CLASS_SAVE_PROFS.items():
        assert len(profs) == 2, f"{cls} must have exactly two save proficiencies"
        assert profs <= set(c.ABILITIES), f"{cls} has unknown ability names"


def test_class_hit_dice_valid():
    assert set(c.CLASS_HIT_DICE) == set(STANDARD_CLASSES)
    assert set(c.CLASS_HIT_DICE.values()) <= {6, 8, 10, 12}


def test_multiclass_reqs_cover_all_classes():
    assert set(c.MULTICLASS_REQS) == set(STANDARD_CLASSES)
    all_13 = {a: 13 for a in c.ABILITIES}
    all_10 = {a: 10 for a in c.ABILITIES}
    for cls, (check, _label) in c.MULTICLASS_REQS.items():
        assert check(all_13), f"{cls} should qualify with all 13s"
        assert not check(all_10), f"{cls} should not qualify with all 10s"


def test_skill_ability_map_valid():
    assert set(c.SKILL_ABILITY.values()) <= set(c.ABILITIES)
    assert len(c.SKILLS) == 18  # the 5e skill list


def test_point_buy_constants():
    assert sorted(c.POINT_BUY_COSTS) == list(range(8, 16))
    costs = [c.POINT_BUY_COSTS[s] for s in range(8, 16)]
    assert costs == sorted(costs), "point-buy costs must be non-decreasing"
    assert c.POINT_BUY_BUDGET == 27


def test_standard_array():
    assert sorted(c.STANDARD_ARRAY, reverse=True) == [15, 14, 13, 12, 10, 8]


def test_stat_boost_items_reference_valid_abilities():
    for item, (ability, amount) in c.STAT_BOOST_ITEMS.items():
        assert ability is None or ability in c.ABILITIES, item
        assert amount is None or isinstance(amount, int), item


def test_equip_stats():
    assert "AC" in c.EQUIP_STATS and "Initiative" in c.EQUIP_STATS
    assert set(c.ABILITIES) <= set(c.EQUIP_STATS)


def test_get_classes_migration():
    # Legacy single-class records are wrapped on the fly
    assert c.get_classes({"char_class": "Rogue", "level": 4}) == [{"class": "Rogue", "level": 4}]
    # Records with a classes list pass through untouched
    multi = [{"class": "Fighter", "level": 5}, {"class": "Wizard", "level": 3}]
    assert c.get_classes({"classes": multi}) is multi


def test_classes_label():
    assert c.classes_label([{"class": "Fighter", "level": 5},
                            {"class": "Wizard", "level": 3}]) == "Fighter 5 / Wizard 3"
    # Zero-level and unnamed rows are skipped; empty list falls back to "?"
    assert c.classes_label([{"class": "Bard", "level": 0}]) == "?"
    assert c.classes_label([]) == "?"
