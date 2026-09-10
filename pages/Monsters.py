import json
import math
import re
import unicodedata
import streamlit as st
from utils import load_json, save_json, edition_selector, filter_by_edition, strip_links, edition_label, deduplicate_editions, sidebar_exit_button, page_nav, confirm_delete
from pathlib import Path


def _normalize(text: str) -> str:
    """Strip diacritics, spaces, and punctuation for closer search matching.

    'ogre' matches 'Ogrémoch', 'cryovain' matches 'Cryovain', 'mindflayer'
    matches 'Mind Flayer', and 'willowisp' matches "Will-o'-Wisp" — the same
    normalization is applied to both stored names and the typed query, so
    spacing/punctuation differences never block an otherwise-exact match.
    """
    ascii_text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]", "", ascii_text)


# ── File paths ────────────────────────────────────────────────────────────────
SRD_PATH = Path("data/monsters_srd.json")        # downloaded by download_data.py
HOMEBREW_PATH = Path("json/homebrew_monsters.json")    # user-created monsters, stored locally

ABILITIES = ["str", "dex", "con", "int", "wis", "cha"]
ABILITY_LABELS = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

# ── Homebrew monster dropdown options ─────────────────────────────────────────

MONSTER_TYPES = [
    "Aberration", "Beast", "Celestial", "Construct", "Dragon", "Elemental",
    "Fey", "Fiend", "Giant", "Humanoid", "Monstrosity", "Ooze", "Plant", "Undead",
]
MONSTER_SIZES = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]
ALIGNMENTS = [
    "Lawful Good", "Neutral Good", "Chaotic Good",
    "Lawful Neutral", "True Neutral", "Chaotic Neutral",
    "Lawful Evil", "Neutral Evil", "Chaotic Evil",
    "Unaligned", "Any Alignment",
]
# All valid D&D 5e CR values
CR_VALUES = ["0", "1/8", "1/4", "1/2"] + [str(n) for n in range(1, 31)]

# ── Cross-edition deduplication ───────────────────────────────────────────────

# All stat fields that must match exactly for two monsters to be considered the same.
_MONSTER_STAT_FIELDS = ["cr", "type", "size", "str", "dex", "con", "int", "wis", "cha", "hp", "ac", "speed"]

def _monsters_same(a, b):
    """Return True only if every stat and action name is identical between editions.

    Per user rule: any single stat change OR any added/removed action is significant
    and keeps the two entries separate.
    """
    # All numerical/categorical stats must match
    for f in _MONSTER_STAT_FIELDS:
        if str(a.get(f, "")).lower().strip() != str(b.get(f, "")).lower().strip():
            return False

    # Action names must match (sorted so order doesn't matter)
    def _names(record, key):
        return sorted(e.get("name", "").lower().strip() for e in record.get(key, []))

    for key in ("actions", "special_abilities", "legendary_actions"):
        if _names(a, key) != _names(b, key):
            return False

    return True


# ── Role tagging ──────────────────────────────────────────────────────────────
# Derive a set of gameplay-role tags from a monster's action text and stats.
# Used by the Role filter multiselect — pre-computed into _role_tags at load time.

ALL_ROLES = ["Melee", "Ranged", "Spellcaster", "Controller", "Support", "Tank", "Legendary", "Swarm"]


def _tank_hp_floor(cr):
    """HP threshold above which a monster qualifies as Tank for this CR.

    Scales with CR so low-CR durable monsters (e.g. Gelatinous Cube at CR 2)
    are correctly tagged rather than being excluded by an absolute HP cutoff.
    Thresholds sit at roughly 70% of the minimum HP for each DMG defensive-CR tier.
    """
    if cr <= 0:    return 10
    if cr <= 0.25: return 20
    if cr <= 0.5:  return 35
    if cr <= 1:    return 50
    if cr <= 2:    return 65
    if cr <= 4:    return 85
    if cr <= 6:    return 110
    if cr <= 9:    return 140
    if cr <= 12:   return 170
    if cr <= 16:   return 220
    if cr <= 20:   return 280
    return int(cr * 18)


def _tank_ac_tier(ac):
    """Lowest CR at which this AC is the DMG-expected norm (defensive CR table).

    Used for 'high AC for CR' detection: if a monster's AC implies a higher
    defensive-CR tier than its actual CR, it qualifies as Tank by armour.
    """
    if ac <= 13: return 0
    if ac == 14: return 4
    if ac <= 15: return 5
    if ac == 16: return 8
    if ac == 17: return 10
    if ac == 18: return 13
    return 17


def monster_roles(m):
    """Return a list of gameplay-role tags for a monster dict.

    Roles derived purely from action/ability text and a few stat fields:
      Melee       — has melee weapon or spell attacks
      Ranged      — has ranged weapon/spell attacks or thrown weapons
      Spellcaster — has spellcasting trait or uses spell save DC
      Controller  — inflicts conditions (charmed, stunned, etc.) via saving throws
      Support     — heals or meaningfully buffs allies (leadership, auras, healing touch)
      Tank        — very durable: high HP, high AC, regeneration, or legendary resistance
      Legendary   — has legendary actions (boss-tier threat)
      Swarm       — is or leads a swarm of smaller creatures
    """
    text = " ".join(
        a.get("desc", "") + " " + a.get("name", "")
        for sec in ("actions", "special_abilities", "legendary_actions", "bonus_actions")
        for a in m.get(sec, [])
    ).lower()
    name = m.get("name", "").lower()
    roles = []

    # ── Melee ─────────────────────────────────────────────────────────────────
    if any(k in text for k in ("melee weapon attack", "melee spell attack")):
        roles.append("Melee")

    # ── Ranged ────────────────────────────────────────────────────────────────
    if any(k in text for k in ("ranged weapon attack", "ranged spell attack",
                                "shortbow", "longbow", "crossbow", "thrown")):
        roles.append("Ranged")

    # ── Spellcaster ───────────────────────────────────────────────────────────
    if any(k in text for k in ("spellcasting", "innate spellcasting", "spell save dc",
                                "as a spell", "cantrip", "spell attack modifier")):
        roles.append("Spellcaster")

    # ── Controller — inflicts conditions via saving throws ────────────────────
    if (any(k in text for k in ("charmed", "frightened", "stunned", "paralyzed",
                                 "incapacitated", "restrained", "blinded", "petrified"))
            and "saving throw" in text):
        roles.append("Controller")

    # ── Support — heals or buffs allies ───────────────────────────────────────
    # Check action/ability names for classic support keywords
    action_names = " ".join(
        a.get("name", "").lower()
        for sec in ("actions", "special_abilities", "legendary_actions", "bonus_actions")
        for a in m.get(sec, [])
    )
    heals_others = (
        any(k in text for k in ("regain", "heal", "cure"))
        and any(k in text for k in ("friendly", "ally", "allies",
                                     "each creature", "one creature", "you touch"))
    )
    has_support_ability = any(k in action_names for k in (
        "healing", "cure", "leadership", "rallying", "bolster", "divine grace",
        "channel divinity", "aura of protection", "aura of courage",
        "inspiring", "aid",
    ))
    if heals_others or has_support_ability:
        roles.append("Support")

    # ── Tank — very durable frontliner ────────────────────────────────────────
    # Parse base HP from "123 (Xd8 + Y)" format
    hp_m = re.match(r'(\d+)', str(m.get("hp", "0")))
    base_hp = int(hp_m.group(1)) if hp_m else 0
    # Parse AC (may be an int or "17 (natural armor)")
    try:
        ac_int = int(str(m.get("ac", "0")).split()[0])
    except (ValueError, IndexError):
        ac_int = 0
    cr_float = cr_to_float(m.get("cr", 0))
    if (base_hp >= _tank_hp_floor(cr_float)          # above-average HP for this CR
            or _tank_ac_tier(ac_int) > cr_float      # AC implies a higher defensive-CR tier
            or "legendary resistance" in text         # can negate failed saves
            or "regenerat" in text                    # regeneration (trolls, etc.)
            or "parry" in text                        # defensive reaction
            or "indomitable" in text):                # fighter-like endurance
        roles.append("Tank")

    # ── Legendary ─────────────────────────────────────────────────────────────
    if m.get("legendary_actions"):
        roles.append("Legendary")

    # ── Swarm ─────────────────────────────────────────────────────────────────
    if "swarm" in name or "swarm" in text[:50]:
        roles.append("Swarm")

    return roles


# ── Stat helpers ──────────────────────────────────────────────────────────────

def ability_mod(score):
    """Convert an ability score to its modifier (floor((score-10)/2))."""
    return math.floor((score - 10) / 2)

def fmt_mod(score):
    """Return 'score (±mod)' string, e.g. '16 (+3)'."""
    m = ability_mod(score)
    return f"{score} ({'+' if m >= 0 else ''}{m})"

# Fractional CRs are stored as floats in JSON; map them to the display strings
_CR_DISPLAY = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}

def fmt_cr(cr):
    """Format a CR value for display, handling fractional CRs like 0.25 → '1/4'."""
    try:
        f = float(cr)
        return _CR_DISPLAY.get(f, str(int(f)) if f == int(f) else str(f))
    except Exception:
        return str(cr)


def cr_to_float(cr):
    """Convert a CR value (string fraction like '1/4' or number) to float."""
    try:
        if "/" in str(cr):
            n, d = str(cr).split("/")
            return float(n) / float(d)
        return float(cr)
    except Exception:
        return 0.0


@st.cache_data(show_spinner=False)
def _monster_options(path, mtime):
    """Pre-compute per-monster derived fields and sidebar filter options.

    Computed once per file version (cache busts on mtime change):
      _cr_float  — avoids re-parsing fractional CR strings at filter time
      _role_tags — avoids re-running monster_roles() on every Role-filter render
                   (roles: Melee, Ranged, Spellcaster, Controller, Support, Tank[CR-relative], Legendary, Swarm)
      _name_norm — avoids re-running _normalize() (diacritics/space/punctuation
                   stripping) on every search keypress
    Returns the enriched list plus sorted unique types, sizes, and CR floats.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for m in data:
        m["_cr_float"]  = cr_to_float(m.get("cr", 0))
        m["_role_tags"] = monster_roles(m)                  # pre-compute role tags once
        m["_name_norm"] = _normalize(m.get("name", ""))     # pre-compute normalised name for search
    all_types = sorted({m.get("type", "").title() for m in data if m.get("type")})
    all_sizes = sorted({m.get("size", "").title() for m in data if m.get("size")})
    cr_values = sorted({m["_cr_float"] for m in data})
    return data, all_types, all_sizes, cr_values


@st.cache_data(show_spinner=False)
def _named_monster_options(path, mtime):
    """Same pre-computation as _monster_options (incl. space/punctuation-stripped
    _name_norm) but for the Sourcebook/MM monster file.

    Returns (data, all_sources, cr_values).
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for m in data:
        m["_cr_float"]  = cr_to_float(m.get("cr", 0))
        m["_role_tags"] = monster_roles(m)
        m["_name_norm"] = _normalize(m.get("name", ""))
    all_sources = sorted({m.get("source", "Unknown") for m in data if m.get("source")})
    cr_values   = sorted({m["_cr_float"] for m in data})
    return data, all_sources, cr_values


@st.cache_data(show_spinner=False)
def _filtered_srd_monsters(path, mtime, gamesystem):
    """Return the edition-filtered/deduplicated SRD monster list, cached per gamesystem.

    Prevents deduplicate_editions() — which compares every monster pair — from
    re-running on every Streamlit rerun when the user hasn't changed the edition.
    """
    all_monsters, _, _, _ = _monster_options(path, mtime)
    if gamesystem is None:
        return deduplicate_editions(all_monsters, same_fn=_monsters_same)
    return filter_by_edition(all_monsters, gamesystem)


def _mtime_or_none(p: Path):
    """File mtime for cache keying, or None when the file doesn't exist."""
    return p.stat().st_mtime if p.exists() else None


@st.cache_data(show_spinner=False)
def _spell_ref_options(srd_mtime, hb_mtime):
    """Sorted spell names + name→spell dict for the stat-block Spell Reference.

    Cached on both file mtimes so the ~2,000-name set build, sort, and lookup
    dict are computed once per file version instead of once per rendered
    spellcasting monster (up to 50 per page).
    """
    all_spells = (
        (load_json("data/spells_srd.json", []) if srd_mtime is not None else [])
        + (load_json("json/homebrew_spells.json", []) if hb_mtime is not None else [])
    )
    by_name = {}
    for s in all_spells:
        n = s.get("name")
        if n and n not in by_name:   # first occurrence wins — SRD before homebrew
            by_name[n] = s
    return sorted(by_name), by_name


# Regex for sub-option lists inside action descriptions — compiled once at module load.
# Matches "Title. Description" patterns (e.g. "Fire Form. The target ignites…").
_SUBITEM = re.compile(r'^([A-Z][A-Za-z ,\'\-()]{0,50})\.\s+(.+)', re.DOTALL)


# ── Spell card renderer (shared with spell reference inside stat blocks) ──────

def render_spell(s):
    """Render a compact spell card for spell dict `s`."""
    level_text = s.get("level_text", str(s.get("level", 0)))
    school     = s.get("school", "")
    header     = f"*{level_text} {school}*" if level_text and school else ""
    if header:
        st.markdown(header)
    cols = st.columns(4)
    cols[0].markdown(f"**Casting Time:** {s.get('casting_time', '—')}")
    cols[1].markdown(f"**Range:** {s.get('range', '—')}")
    cols[2].markdown(f"**Components:** {s.get('components', '—')}")
    cols[3].markdown(f"**Duration:** {s.get('duration', '—')}")
    if s.get("concentration"):
        st.warning("⚡ Concentration")
    if s.get("ritual"):
        st.info("🔁 Ritual")
    if s.get("material"):
        st.markdown(f"**Material:** {strip_links(s.get('material', ''))}")
    st.markdown(strip_links(s.get("desc", "")))
    hl = s.get("higher_level", "")
    if hl:
        st.markdown(f"**At Higher Levels:** {strip_links(hl)}")
    classes_str = s.get("classes", "")
    if classes_str:
        st.caption(f"Classes: {classes_str}")


# ── Stat block renderer ───────────────────────────────────────────────────────

def render_stat_block(m):
    """Render a full D&D 5e stat block for monster dict `m` using Streamlit columns."""

    # Row 1: type/size/alignment | CR/HP/AC | speed
    c1, c2, c3 = st.columns(3)

    # Alignment: title-case for display ("chaotic evil" → "Chaotic Evil")
    alignment_display = m.get("alignment", "—").title() if m.get("alignment") else "—"

    c1.markdown(
        f"**Type:** {m.get('type', '—').title()}  \n"
        f"**Size:** {m.get('size', '—').title()}  \n"
        f"**Alignment:** {alignment_display}"
    )
    # AC: show armour source in brackets, e.g. "17 [Natural Armor]"
    ac_val  = m.get("ac", "—")
    ac_text = m.get("ac_text", "").strip()
    ac_display = f"{ac_val} [{ac_text.title()}]" if ac_text else str(ac_val)
    c2.markdown(
        f"**CR:** {fmt_cr(m.get('cr', '—'))}  \n"
        f"**HP:** {m.get('hp', '—')} {('(' + m['hp_dice'] + ')') if m.get('hp_dice') else ''}  \n"
        f"**AC:** {ac_display}"
    )
    # Speed: dict or string; title-case each movement keyword ("walk"→"Walk")
    speed = m.get("speed", {})
    if isinstance(speed, dict):
        speed_str = ", ".join(f"{k.title()} {v}" for k, v in speed.items())
    else:
        # Capitalise the first letter of each movement keyword (walk, fly, swim, climb, burrow)
        speed_str = re.sub(
            r'\b(walk|fly|swim|climb|burrow|hover)\b',
            lambda mo: mo.group(0).capitalize(),
            str(speed)
        )
    c3.markdown(f"**Speed:** {speed_str or '—'}")

    st.markdown("---")

    # Row 2: six ability score metrics
    cols = st.columns(6)
    for col, ab, label in zip(cols, ABILITIES, ABILITY_LABELS):
        score = m.get(ab, 10)
        col.metric(label, fmt_mod(score))

    # Saving throws — stored per ability with full name keys like "strength_save"
    saves = {
        k: m.get(f"{k}_save")
        for k in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    }
    save_parts = [
        f"{k[:3].upper()} {'+' if v >= 0 else ''}{v}"
        for k, v in saves.items() if v is not None
    ]
    if save_parts:
        st.markdown(f"**Saving Throws:** {', '.join(save_parts)}")

    # Skills: SRD monsters store a dict {name: int}; named/homebrew monsters store a plain string
    skills = m.get("skills", {})
    if skills:
        if isinstance(skills, dict):
            skill_str = ", ".join(
                f"{k.title()} {'+' if v >= 0 else ''}{v}" for k, v in skills.items()
            )
        else:
            skill_str = skills  # already formatted
        st.markdown(f"**Skills:** {skill_str}")

    # Damage traits and condition immunities
    for field, label in [
        ("damage_vulnerabilities", "Damage Vulnerabilities"),
        ("damage_resistances",     "Damage Resistances"),
        ("damage_immunities",      "Damage Immunities"),
        ("condition_immunities",   "Condition Immunities"),
    ]:
        val = m.get(field, "")
        if val:
            st.markdown(f"**{label}:** {val}")

    # Senses: fix comma spacing and capitalise the first letter of each entry
    # e.g. "darkvision 60 ft., passive Perception 14" → "Darkvision 60 ft., Passive Perception 14"
    senses_val = m.get("senses", "")
    if senses_val:
        senses_val = re.sub(r",([^ ])", r", \1", senses_val)
        senses_val = ", ".join(
            (s[0].upper() + s[1:]) if s else s
            for s in (seg.strip() for seg in senses_val.split(","))
        )
        st.markdown(f"**Senses:** {senses_val}")

    # Languages: fix comma spacing only (proper nouns are already capitalised in the data)
    lang_val = m.get("languages", "")
    if lang_val:
        lang_val = re.sub(r",([^ ])", r", \1", lang_val)
        st.markdown(f"**Languages:** {lang_val}")

    st.markdown("---")

    # Pattern: "Intro text:\nName. Description.\nName. Description."
    # Detected when every line after the first matches "Word(s). text" — formatted as bullets.
    # _SUBITEM regex is compiled once at module level (above render_stat_block).

    def _render_desc(name: str, desc: str):
        """Render an action/trait name + desc, converting sub-option lists to bullets."""
        label = f"**{name}:** " if name else ""
        if '\n' not in desc:
            st.markdown(label + strip_links(desc))
            return
        # Already has markdown list markers — just render as-is
        if re.search(r'^[-*] ', desc, re.MULTILINE):
            st.markdown(label + strip_links(desc))
            return
        parts = [p.strip() for p in desc.split('\n') if p.strip()]
        intro, items = parts[0], parts[1:]
        matches = [_SUBITEM.match(item) for item in items]
        if items and all(matches):
            # Intro line first, then each sub-option as a bullet
            st.markdown(label + strip_links(intro))
            for mo in matches:
                st.markdown(f"- **{mo.group(1).strip()}.** {strip_links(mo.group(2).strip())}")
        else:
            st.markdown(label + strip_links(desc))

    # Traits (passive special abilities listed before the action sections)
    for ability in m.get("special_abilities", []):
        _render_desc(ability.get("name", ""), ability.get("desc", ""))

    # Standard actions — sort order:
    #   0 = Standalone specials (saves, conditions, recharge) NOT called by Multiattack
    #   1 = Multiattack that references special abilities by name
    #   2 = Specials the Multiattack explicitly calls out (e.g. Tail/Breaths in Tiamat)
    #   3 = Generic Multiattack (references only basic attacks)
    #   4 = Basic weapon / spell attacks (plain damage only)
    #
    # Reading flow: standalone options → Multiattack → pieces of Multiattack → basic hits
    actions = m.get("actions", [])
    if actions:
        st.markdown("#### Actions")

        _SKIP_WORDS = {"the", "and", "with", "its", "one", "two", "can", "use", "makes",
                       "three", "four", "five", "or", "of", "a", "an", "each", "per"}

        def _has_effect(action):
            """True if the action does more than plain weapon damage."""
            desc = action.get("desc", "").lower()
            name = action.get("name", "").lower()
            return (
                "saving throw" in desc
                or any(k in desc for k in ("stunned", "frightened", "restrained",
                                            "paralyzed", "charmed", "poisoned",
                                            "prone", "grappled", "petrified",
                                            "blinded", "incapacitated",
                                            "regain", "heal", "drain", "absorb",
                                            "reduce", "ability score"))
                or desc.count("hit:") > 1
                or "recharge" in name
            )

        # Combined text of all Multiattack descriptions — used to detect which
        # special abilities the Multiattack calls out by name
        multi_desc = " ".join(
            a.get("desc", "").lower() for a in actions
            if a.get("name", "").lower().startswith("multiattack")
        )

        def _sig_words(action):
            """Significant words from an action name (length > 3, not filler)."""
            return {w for w in action.get("name", "").lower().split()
                    if len(w) > 3 and w not in _SKIP_WORDS}

        def _is_special_in_multi(action):
            """True if the Multiattack desc mentions this special action by name."""
            words = _sig_words(action)
            return bool(words) and any(w in multi_desc for w in words)

        # Does any Multiattack reference a special action by name?
        any_multi_refs_specials = any(
            _is_special_in_multi(a) for a in actions
            if not a.get("name", "").lower().startswith("multiattack") and _has_effect(a)
        )

        def _action_tier(action, idx):
            name = action.get("name", "").lower()
            desc = action.get("desc", "").lower()
            # 2024 PHB format uses "Melee/Ranged/Spell Attack Roll:" instead of "Weapon Attack:"
            is_weapon = ("weapon attack" in desc or "spell attack" in desc
                         or "attack roll:" in desc)

            if name.startswith("multiattack"):
                # Tier 1 = multi that calls out specials; tier 3 = generic multi
                return (1, idx) if any_multi_refs_specials else (3, idx)

            if _has_effect(action):
                # Tier 2 = special the multi calls out; tier 0 = standalone special
                return (2, idx) if _is_special_in_multi(action) else (0, idx)

            if is_weapon:
                return (4, idx)   # plain weapon attack
            return (0, idx)       # non-weapon non-multi treated as standalone special

        # enumerate() carries the original index into the sort key — avoids the
        # O(n²) actions.index() lookup per element and keeps ties in data order
        for _, action in sorted(enumerate(actions), key=lambda ia: _action_tier(ia[1], ia[0])):
            _render_desc(action.get("name", ""), action.get("desc", ""))

    # Bonus actions (5e 2024 monsters often have these separate from actions)
    bonus = m.get("bonus_actions", [])
    if bonus:
        st.markdown("#### Bonus Actions")
        for action in bonus:
            _render_desc(action.get("name", ""), action.get("desc", ""))

    # Reactions
    reactions = m.get("reactions", [])
    if reactions:
        st.markdown("#### Reactions")
        for action in reactions:
            _render_desc(action.get("name", ""), action.get("desc", ""))

    # Legendary actions — desc text explains the legendary action economy
    leg_desc = m.get("legendary_desc", "")
    leg_actions = m.get("legendary_actions", [])
    if leg_desc or leg_actions:
        st.markdown("#### Legendary Actions")
        if leg_desc:
            st.markdown(strip_links(leg_desc))
        for action in leg_actions:
            _render_desc(action.get("name", ""), action.get("desc", ""))

    # Spell reference — only shown for monsters that have a Spellcasting ability
    # so non-spellcasters don't get an irrelevant lookup widget
    def _has_spellcasting(monster):
        for ability in monster.get("special_abilities", []):
            if "spellcasting" in ability.get("name", "").lower():
                return True
        for action in monster.get("actions", []):
            if "spellcasting" in action.get("name", "").lower():
                return True
        return False

    if _has_spellcasting(m):
        spell_names, spells_by_name = _spell_ref_options(
            _mtime_or_none(Path("data/spells_srd.json")),
            _mtime_or_none(Path("json/homebrew_spells.json")),
        )
        if spell_names:
            with st.expander("🔍 Spell Reference"):
                # Key must be stable across reruns to hold the user's selection.
                # _monster_options/_named_monster_options are @st.cache_data, and
                # Streamlit deep-copies cached return values on every call, so
                # id(m) changes every rerun even though m's content is identical
                # — using id(m) here made the selectbox always snap back to the
                # first spell. Derive the key from content instead.
                sel_spell = st.selectbox(
                    "Look up spell", spell_names,
                    key=f"spell_ref_{m.get('name', '')}_{m.get('source', '')}_{m.get('cr', '')}"
                )
                spell_obj = spells_by_name.get(sel_spell)
                if spell_obj:
                    render_spell(spell_obj)


# ── Page UI ───────────────────────────────────────────────────────────────────

st.title("Monster Reference")

NAMED_PATH = Path("data/monsters_mm.json")       # WotC sourcebook monsters (Beholder, Mind Flayer, named NPCs, etc.)

tab_srd, tab_named, tab_homebrew = st.tabs(["SRD Monsters", "Sourcebook Monsters", "Homebrew Monsters"])

# ── SRD tab ───────────────────────────────────────────────────────────────────
with tab_srd:
    if not SRD_PATH.exists():
        st.warning("SRD data not found. Run `python scripts/download_data.py` to download it.")
    else:
        # _monster_options is cached on mtime so the three expensive per-render
        # computations (type set, size set, CR floats) only run once per file version.
        _all_monsters, all_types, all_sizes, cr_values = _monster_options(
            str(SRD_PATH), SRD_PATH.stat().st_mtime
        )

        # Inline filters — edition radio, then name search, then type/size/CR/sort
        gamesystem = edition_selector(sidebar=False)
        search = st.text_input("Search by name", key="monster_search", placeholder="e.g. Dragon")
        mf1, mf2, mf3, mf4 = st.columns([2, 2, 2, 1])
        selected_types = mf1.multiselect("Type", all_types, key="monster_types")
        selected_sizes = mf2.multiselect("Size", all_sizes, key="monster_sizes")
        selected_roles = mf3.multiselect("Role", ALL_ROLES, key="monster_roles")
        role_and = st.checkbox("Match ALL roles (AND)", value=True, key="monster_role_and",
                               help="AND: monster must have every selected role. OR: any one is enough.")
        srd_sort = mf4.selectbox(
            "Sort by",
            ["CR ↑", "CR ↓", "Name A→Z", "Name Z→A", "Type"],
            key="monster_sort",
        )
        min_cr, max_cr = (cr_values[0], cr_values[-1]) if cr_values else (0.0, 30.0)
        cr_range = st.slider(
            "CR range", min_value=0.0, max_value=30.0,
            value=(min_cr, max_cr), step=0.25, key="monster_cr"
        )

        # Edition filter/dedup is cached — avoids re-running deduplicate_editions()
        # (which walks all 3,200+ monsters) on every rerun when edition hasn't changed.
        monsters = _filtered_srd_monsters(str(SRD_PATH), SRD_PATH.stat().st_mtime, gamesystem)

        # Apply filters — use pre-computed fields (_name_norm, _role_tags) from cache
        filtered = monsters
        if search:
            _q = _normalize(search)
            filtered = [m for m in filtered if _q in m["_name_norm"]]
        if selected_types:
            filtered = [m for m in filtered if m.get("type", "").title() in selected_types]
        if selected_sizes:
            filtered = [m for m in filtered if m.get("size", "").title() in selected_sizes]
        # CR slider filter — use pre-computed '_cr_float' from _monster_options
        filtered = [m for m in filtered if cr_range[0] <= m["_cr_float"] <= cr_range[1]]
        # Role filter — use pre-computed '_role_tags'; AND requires all, OR requires any
        if selected_roles:
            check = all if role_and else any
            filtered = [m for m in filtered
                        if check(r in m["_role_tags"] for r in selected_roles)]
        # Apply chosen sort
        if srd_sort == "CR ↑":
            filtered = sorted(filtered, key=lambda m: (m["_cr_float"], m.get("name", "")))
        elif srd_sort == "CR ↓":
            filtered = sorted(filtered, key=lambda m: (-m["_cr_float"], m.get("name", "")))
        elif srd_sort == "Name A→Z":
            filtered = sorted(filtered, key=lambda m: m.get("name", "").lower())
        elif srd_sort == "Name Z→A":
            filtered = sorted(filtered, key=lambda m: m.get("name", "").lower(), reverse=True)
        elif srd_sort == "Type":
            filtered = sorted(filtered, key=lambda m: (m.get("type", "").lower(), m["_cr_float"], m.get("name", "")))

        # Require at least 3 characters for a name search — the SRD has 3,500+ monsters
        # and 1-2 character queries match thousands of entries causing excessive render time.
        # Type/size filters are checkboxes so they're always intentional; no restriction there.
        search_active = len(search) >= 3 if search else False
        if search and not search_active:
            st.caption("Type at least 3 characters to search by name.")

        if search_active or selected_types or selected_sizes or selected_roles:
            filter_sig = (search, tuple(selected_types), tuple(selected_sizes), tuple(selected_roles), role_and, cr_range, gamesystem, srd_sort)
            page_slice = page_nav(filtered, "srd_page", "_srd_sig", filter_sig)
            for m in page_slice:
                # Prefer explicit source book; fall back to edition label for pure SRD entries
                src = m.get("source") or edition_label(m.get("gamesystem_key", ""))
                with st.expander(
                    f"{m['name']}  —  CR {fmt_cr(m.get('cr', '?'))}"
                    f"  |  {m.get('type', '').title()}  |  {m.get('size', '').title()}"
                    + (f"  —  {src}" if src else "")
                ):
                    render_stat_block(m)
        else:
            st.info("Search by name or select a Type / Size filter above to see monsters.")


# ── Sourcebook Monsters tab ───────────────────────────────────────────────────
with tab_named:
    st.info(
        "Monsters from official WotC sourcebooks that are not part of the open SRD — "
        "generic Monster Manual creatures (Beholder, Mind Flayer, Slaad…), Demon Lords, "
        "Archdevils, named villains, and more. Stat blocks are adapted for reference; "
        "always consult the source book for the authoritative version."
    )
    if not NAMED_PATH.exists():
        st.warning(
            "Sourcebook monster data not found. This tab reads from `data/monsters_mm.json`, "
            "which isn't included in this repo (non-SRD WotC content isn't redistributable) — "
            "see CLAUDE.md for details. Provide your own file with the same schema as "
            "`data/monsters_srd.json` (plus `source` and `named_creature` fields) to use this tab."
        )
    else:
        # _named_monster_options caches the file read + all derived fields (_cr_float,
        # _role_tags, _name_norm) so they are computed only once per file version.
        named_monsters, all_mm_sources, mm_cr_vals = _named_monster_options(
            str(NAMED_PATH), NAMED_PATH.stat().st_mtime
        )
        if not named_monsters:
            st.info("No sourcebook monsters loaded.")
        else:
            # Filters: name search, source multiselect, CR range, sort
            nc_search = st.text_input("Search by name", key="named_search", placeholder="e.g. Beholder")
            nf1, nf2, nf3, nf4 = st.columns([2, 2, 2, 1])
            selected_sources = nf1.multiselect("Source book", all_mm_sources, key="named_sources")
            mm_cr_min, mm_cr_max = (mm_cr_vals[0], mm_cr_vals[-1]) if mm_cr_vals else (0.0, 30.0)
            nc_cr = nf2.slider("CR range", min_value=0.0, max_value=30.0,
                               value=(mm_cr_min, mm_cr_max), step=0.25, key="named_cr")
            selected_roles_mm = nf3.multiselect("Role", ALL_ROLES, key="named_roles")
            role_and_mm = st.checkbox("Match ALL roles (AND)", value=True, key="named_role_and",
                                      help="AND: monster must have every selected role. OR: any one is enough.")
            mm_sort = nf4.selectbox(
                "Sort by",
                ["CR ↑", "CR ↓", "Name A→Z", "Name Z→A", "Type", "Source"],
                key="named_sort",
            )

            filtered_named = named_monsters
            if nc_search:
                _q = _normalize(nc_search)
                filtered_named = [m for m in filtered_named if _q in m["_name_norm"]]
            if selected_sources:
                filtered_named = [m for m in filtered_named if m.get("source", "") in selected_sources]
            filtered_named = [m for m in filtered_named if nc_cr[0] <= m["_cr_float"] <= nc_cr[1]]
            if selected_roles_mm:
                check_mm = all if role_and_mm else any
                filtered_named = [m for m in filtered_named
                                  if check_mm(r in m["_role_tags"] for r in selected_roles_mm)]
            # Apply chosen sort
            if mm_sort == "CR ↑":
                filtered_named = sorted(filtered_named, key=lambda m: (m["_cr_float"], m.get("name", "")))
            elif mm_sort == "CR ↓":
                filtered_named = sorted(filtered_named, key=lambda m: (-m["_cr_float"], m.get("name", "")))
            elif mm_sort == "Name A→Z":
                filtered_named = sorted(filtered_named, key=lambda m: m.get("name", "").lower())
            elif mm_sort == "Name Z→A":
                filtered_named = sorted(filtered_named, key=lambda m: m.get("name", "").lower(), reverse=True)
            elif mm_sort == "Type":
                filtered_named = sorted(filtered_named, key=lambda m: (m.get("type", "").lower(), m["_cr_float"], m.get("name", "")))
            elif mm_sort == "Source":
                filtered_named = sorted(filtered_named, key=lambda m: (m.get("source", ""), m["_cr_float"], m.get("name", "")))

            filter_sig_nc = (nc_search, tuple(selected_sources), tuple(selected_roles_mm), role_and_mm, nc_cr, mm_sort)
            page_slice_nc = page_nav(filtered_named, "named_page", "_named_sig", filter_sig_nc)
            for m in page_slice_nc:
                src = m.get("source", "Unknown source")
                with st.expander(
                    f"{m['name']}  —  CR {fmt_cr(m.get('cr', '?'))}"
                    f"  |  {m.get('type', '').title()}  |  {m.get('size', '').title()}"
                    f"  —  {src}"
                ):
                    render_stat_block(m)


# ── Homebrew tab ──────────────────────────────────────────────────────────────
with tab_homebrew:
    # Load homebrew monsters into session state on first visit; avoid re-reading on reruns
    if "homebrew_monsters" not in st.session_state:
        st.session_state.homebrew_monsters = load_json(HOMEBREW_PATH, [])

    st.subheader("Add Homebrew Monster")
    with st.form("add_homebrew_monster"):
        hb_name = st.text_input("Name")
        hc1, hc2, hc3, hc4 = st.columns(4)
        hb_cr        = hc1.selectbox("CR", CR_VALUES, index=CR_VALUES.index("1"))
        hb_type      = hc2.selectbox("Type", MONSTER_TYPES, index=MONSTER_TYPES.index("Humanoid"))
        hb_size      = hc3.selectbox("Size", MONSTER_SIZES, index=MONSTER_SIZES.index("Medium"))
        hb_alignment = hc4.selectbox("Alignment", ALIGNMENTS, index=ALIGNMENTS.index("True Neutral"))

        hd1, hd2, hd3 = st.columns(3)
        hb_hp    = hd1.number_input("HP", min_value=1, value=10)
        hb_ac    = hd2.number_input("AC", min_value=1, value=12)
        hb_speed = hd3.text_input("Speed", value="30 ft.")

        ha1, ha2, ha3, ha4, ha5, ha6 = st.columns(6)
        hb_str = ha1.number_input("STR", 1, 30, 10)
        hb_dex = ha2.number_input("DEX", 1, 30, 10)
        hb_con = ha3.number_input("CON", 1, 30, 10)
        hb_int = ha4.number_input("INT", 1, 30, 10)
        hb_wis = ha5.number_input("WIS", 1, 30, 10)
        hb_cha = ha6.number_input("CHA", 1, 30, 10)

        hb_traits = st.text_area(
            "Special Abilities (one per line: Name: Description)", height=100,
            placeholder="Pack Tactics: This creature has advantage on attack rolls while an ally is adjacent.\nRegeneration: The creature regains 10 HP at the start of its turn.",
        )
        hb_actions_text = st.text_area(
            "Actions (one per line: Name: Description)", height=100,
            placeholder="Multiattack: The creature makes two attacks.\nClaw: +5 to hit, reach 5 ft., one target. Hit: 1d6+3 slashing damage.",
        )
        hb_legendary = st.text_area(
            "Legendary Actions (one per line: Name: Description)", height=80,
            placeholder="Attack (1 Action): Makes one attack.",
        )
        st.caption("Each non-empty line must be in **Name: Description** format.")

        if st.form_submit_button("Add Homebrew Monster"):
            if hb_name.strip():
                # Validate that every non-empty line contains a colon separator
                bad_lines = []
                for field_text, field_label in [
                    (hb_traits, "Special Abilities"),
                    (hb_actions_text, "Actions"),
                    (hb_legendary, "Legendary Actions"),
                ]:
                    for line in field_text.strip().splitlines():
                        if line.strip() and ":" not in line:
                            bad_lines.append(f'{field_label}: "{line.strip()}"')
                if bad_lines:
                    st.warning(
                        "Some lines are missing a colon (Name: Description format):\n"
                        + "\n".join(bad_lines[:3])
                        + ("\n…" if len(bad_lines) > 3 else "")
                    )

                def parse_entries(text):
                    """Parse 'Name: Description' lines into the standard action list format."""
                    entries = []
                    for line in text.strip().splitlines():
                        if ":" in line:
                            n, _, d = line.partition(":")
                            entries.append({"name": n.strip(), "desc": d.strip()})
                    return entries

                new_hb = {
                    "name": hb_name.strip(), "cr": hb_cr.strip(), "type": hb_type.strip(),
                    "size": hb_size.strip(), "alignment": hb_alignment.strip(),
                    "hp": hb_hp, "ac": hb_ac, "speed": hb_speed.strip(),
                    "str": hb_str, "dex": hb_dex, "con": hb_con,
                    "int": hb_int, "wis": hb_wis, "cha": hb_cha,
                    "special_abilities": parse_entries(hb_traits),
                    "actions":           parse_entries(hb_actions_text),
                    "legendary_actions": parse_entries(hb_legendary),
                    "homebrew": True,
                }
                st.session_state.homebrew_monsters.append(new_hb)
                save_json(HOMEBREW_PATH, st.session_state.homebrew_monsters)
                st.success(f"Added {hb_name.strip()}")
            else:
                st.error("Name is required")

    st.subheader("Your Homebrew Monsters")
    hb_monsters = st.session_state.homebrew_monsters
    if not hb_monsters:
        st.info("No homebrew monsters yet. Add one above.")
    else:
        for i, m in enumerate(hb_monsters):
            with st.expander(
                f"{m['name']}  —  CR {fmt_cr(m.get('cr', '?'))}  |  {m.get('type', '').title()}"
            ):
                render_stat_block(m)

                # Two-step delete: first press shows "Confirm?", second press deletes
                dc1, dc2 = st.columns([8, 1])
                if confirm_delete(dc2, f"hbm_delete_{i}", f"hbm_{i}"):
                    st.session_state.homebrew_monsters.pop(i)
                    save_json(HOMEBREW_PATH, st.session_state.homebrew_monsters)
                    st.rerun()

