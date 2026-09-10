"""Shape tests for the root data-table modules (random_tables, name_tables, npc_tables)."""

from name_tables import NAMES
from npc_tables import NPC_APPEARANCE, NPC_PERSONALITY, NPC_IDEAL, NPC_BOND, NPC_FLAW
from random_tables import WILD_MAGIC, DUNGEON_DRESSING


def test_wild_magic_is_paired_d100():
    # Renderers map a d100 roll onto paired entries (01–02 … 99–100),
    # which only works with exactly 50 entries.
    assert len(WILD_MAGIC) == 50
    assert all(isinstance(e, str) and e for e in WILD_MAGIC)


def test_dungeon_dressing_nonempty_strings():
    assert len(DUNGEON_DRESSING) >= 50
    assert all(isinstance(e, str) and e for e in DUNGEON_DRESSING)


def test_name_pools_complete():
    # Every race must offer male, female, and surname pools (the UI assumes all three)
    for race, pools in NAMES.items():
        for kind in ("male", "female", "surname"):
            assert pools.get(kind), f"{race} is missing a {kind} pool"


def test_npc_generator_pools_nonempty():
    for pool in (NPC_APPEARANCE, NPC_PERSONALITY, NPC_IDEAL, NPC_BOND, NPC_FLAW):
        assert len(pool) >= 10
        assert all(isinstance(e, str) and e for e in pool)
