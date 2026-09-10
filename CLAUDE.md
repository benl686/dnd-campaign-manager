# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```powershell
pip install -r requirements.txt   # first time only — Streamlit is the only dependency
streamlit run Home.py
```

The app runs at `http://localhost:8501`. `Run.py` is an alternative launcher for packaged/standalone distribution — it auto-opens the browser and sets the working directory from the executable location. Use `streamlit run Home.py` for development.

## Populating SRD reference data

Data-pipeline scripts live in `scripts/` (they are run manually from the project root, never imported by the app). Run once before first launch (requires internet):

```powershell
python scripts/download_data.py
```

This fetches from the Open5e v2 API and writes:
- `data/monsters_srd.json` — ~3,180 monsters
- `data/spells_srd.json` — 1,955+ spells
- `data/items_srd.json` — 440+ items (weapons, armor, gear)
- `data/magicitems.json` — 2,300+ magic items
- `data/races_srd.json` — ~63 races and subraces (both 2014 and 2024 editions, plus Kobold Press's Tome of Heroes and Open5e Originals — legitimately-licensed OGL/ORC third-party content, not WotC-exclusive material)
- `data/feats.json`, `data/backgrounds.json`, `data/classes.json` — not yet used by UI pages but downloaded

The `data/` files are committed to git so end users who clone the repo don't need to run this script.

This public repo intentionally ships SRD data only. The Monsters page's "Sourcebook Monsters" and "Named Creatures" pools read from `data/monsters_mm.json`, which isn't included here (non-SRD WotC sourcebook content isn't redistributable) — those tabs simply don't appear when the file is absent, per the Monsters page's own file-existence check. If you want that data for personal use, you'd need to source and build `data/monsters_mm.json` yourself (same schema as `data/monsters_srd.json`, plus `source` and `named_creature` fields).

A manual content audit (every `source` field plus a raw-text sweep for WotC sourcebook names) also found 124 records — 47 monsters from Volo's Guide to Monsters / Mordenkainen's Tome of Foes, and 77 races from a dozen other non-SRD sourcebooks (Eberron: Rising from the Last War, Mordenkainen Presents: Monsters of the Multiverse, Van Richten's Guide to Ravenloft, the Plane Shift MTG-crossover PDFs, etc.) — that had leaked into `monsters_srd.json` and `races_srd.json` via an undocumented scraper that was never checked into this repo. Those records were removed before the first public commit.

## Sidebar navigation — Home.py MUST stay in sync

The sidebar is driven by `st.navigation()` in `Home.py`, **not** by auto-discovery. Any page file in `pages/` that is not registered in `Home.py` will be invisible to the user.

**Rule: whenever a new page is added or removed, update `Home.py` immediately.**

Current groups and where new pages belong:
- `""` (unlabelled) — the Home/landing page only (`pages/Welcome.py`)
- `"DM Tools"` — campaign-dependent tools (Campaigns, Characters, Combat, EncounterBuilder, Calendar, Downtime, Sessions, SessionPlanner, NPCs, Factions, Faiths, RelationshipMap, ResourceTracker, Quests, Worldbuilding, HomebrewRules, Dice)
- `"Reference"` — standalone SRD look-ups (Monsters, Spells, Items, Backgrounds, Classes, Races, Feats, Conditions)
- `"Tools"` — standalone utility pages (NameGenerator, TreasureGenerator, TravelTracker, WeatherTracker, PartyInventory, MagicItemJournal, RumorBoard, ShopGenerator)

Add new reference pages to `"Reference"` and new utility/generator pages to `"Tools"`. If a new campaign-dependent page is created, add it to `"DM Tools"`.

**Current DM Tools sidebar order:** NPCs → Factions → Faiths → RelationshipMap → ResourceTracker (continuity: create entities, group them, map relationships).

## Committing changes

**Claude should commit the project to git after every significant code change.** User data (JSON files) is stored locally and needs no commits — only source code changes get committed.

The `json/` folder (user campaign data), `me.txt`/`Cinfo.txt` (personal notes), and `*.json.tmp`/`*.json.bak` (save_json artifacts) are gitignored, so `git add -A` is safe — it can never sweep personal data into the repo. The `data/` reference files ARE tracked deliberately (see above).

Commit after: new pages, new features, bug fixes, refactors, or any session with multiple edits.

```powershell
git add -A
git commit -m "Short description of what changed"
git push
```

## Implementation plans

When working on a multi-step implementation plan, Claude creates `current_plan.md` in the project root. The plan file tracks progress with checkboxes so work can resume after a context switch or token limit.

**Conventions:**
- Erase (or overwrite) `current_plan.md` before starting a new unrelated plan.
- Update checkboxes (`- [ ]` → `- [x]`) as each step completes.
- When resuming a session, Claude reads `current_plan.md` to know what's already done.

## Shared utilities (`utils.py`)

All pages import from `utils.py` in the project root. **All new pages must do the same:**

```python
from utils import load_json, save_json
```

- `load_json(path, default)` — loads a JSON file or returns `default` if missing
- `save_json(path, data)` — writes data to JSON; this is all that's needed to persist user data. Writes are **atomic** (temp file + `os.replace`) and keep the previous version as `<file>.json.bak`, so a crash mid-write can never corrupt user data. It also creates missing parent folders, so fresh clones need no `json/` directory.
- `load_campaigns()` / `no_campaigns_notice()` — campaign-scoped pages load the campaign list and show the standard empty-state message with these; don't hand-roll either.
- `confirm_delete(container, flag_key, key, label="Delete")` — the standard two-step delete button (see Destructive action rules).
- `page_nav(items, page_key, sig_key, filter_sig)` — shared pagination for reference tables (see Reference pages — pagination).

## Running tests

```powershell
python -m pytest tests/
```

`tests/` covers the pure-logic root modules: treasure-table invariants (tier sets, d100 coverage, coin scaling, alphabetical sorting, naming rules), `character_lib` rules math, and data-table shapes (`random_tables`, `name_tables`, `npc_tables`). **Run after editing any of those modules.** Page files aren't covered (they execute streamlit at import).

## Data-table root modules

Large literal tables live in root modules, not page files, so page logic stays readable (pattern: `treasure_tables.py`): `name_tables.py` (NAMES dict for NameGenerator), `npc_tables.py` (NPC generator trait pools), `random_tables.py` (Wild Magic, Dungeon Dressing), `character_lib.py` (5e rules constants + pure math). New big tables go in a root module.

**Note on Save buttons:** Save buttons in the app are for *editing existing records* — updating a character's stats, changing a faith's doctrine, etc. — without having to delete and recreate the entry. They write the updated record back to the JSON file. They have nothing to do with git.

## Destructive action rules

**All destructive actions must use a two-step confirmation pattern.** This applies to every delete, reset, or clear operation anywhere in the app — no exceptions.

Standard way — the `utils.confirm_delete` helper:
```python
from utils import confirm_delete

if confirm_delete(container, f"thing_delete_pending_{unique_id}", f"thing_{unique_id}"):
    # perform deletion
    st.rerun()
```
- `container` is `st` or a column; `flag_key` is the pending boolean in session_state (keep the `*_delete_pending_*` naming so stale-key cleanup sweeps work); the third arg is the widget-key base (`_del` / `_confirm` suffixes are added).
- Optional `label=` overrides the button text (e.g. `label="Remove"` in Combat).
- **Not usable inside `st.form`** — forms only rerun on submit, so form-based deletes keep the hand-rolled `form_submit_button("Delete")` → `form_submit_button("Confirm?")` pattern (NPCs edit form, Factions alliances, PartyInventory).

"Reset all" / "Clear" buttons at the page level use custom labels ("Confirm Reset?", "Confirm Clear?") and stay hand-rolled with a page-level flag key (e.g. `reset_confirm`).

## Edit mode rules

**Every record the user can create must also be editable in-place.** Never force the user to delete and re-create an entry just to change a field. This applies to all data types: travel legs, downtime activities, inventory items, session notes, factions, faiths, NPCs, etc.

Edit forms should be toggled by an "✏ Edit" button on each record. Clicking it shows the form; clicking again (or clicking Save) dismisses it. Use a session state flag `{prefix}_edit_{idx}` to track open/closed state.

## Display order and stored index consistency

**The order items are displayed must always match the order they are stored.** Never sort a list for display and then delete or save by a different (stored) index — this risks modifying the wrong record.

Correct approach: if you need a specific display order, **keep the stored list in that order** (sort after add, sort after edit). Then the display index equals the stored index and there is no mismatch.

If you must display in a different order than stored (e.g. newest-first), use `sorted(enumerate(items), key=...)` to preserve the original index alongside each item:
```python
indexed = sorted(enumerate(items), key=lambda i_x: i_x[1]["date"], reverse=True)
for orig_idx, item in indexed:
    # use orig_idx for save/delete, not the loop counter
```

## UI text capitalization

Use **Title Case** for all user-visible headings, subheadings, button labels, and category names. Sentence case is only for caption/help text that forms a full grammatical sentence.

- `st.subheader`, `st.header`, `st.title` → always Title Case (e.g. "Add New Faith", not "Add new faith")
- Button labels → Title Case (e.g. "Roll Encounter Loot", "＋ Gem Tier", not "＋ gem tier")
- Treasure category labels → Title Case everywhere: **Gems**, **Art Objects**, **Jewelry**, **Trade Goods**, **Curiosities** — whether used in expander titles, result lines, or tab names
- `st.caption`, `help=`, `placeholder=` → sentence case with a period if it's a full sentence
- Inline result labels (e.g. `**Art Object (250 gp):**`) → Title Case

## Treasure item naming convention

All gem (and similar collectible) names use **Title Case** and follow the format **Mineral (Variety, Quality)** — mineral/family name first, qualifier(s) in parentheses:

- Variety/subspecies comes before quality: `Garnet (Tsavorite, Fine)` not `Garnet (Fine, Tsavorite)`
- Color comes before quality: `Spinel (Blue, Fine)`, `Diamond (Pink, Fancy)`
- Multiple qualifiers in parentheses follow the order: **Variety → Color → Quality/Condition**
- Do NOT put qualifiers as prefixes: `Corundum (Color-Changing) [aka Sapphire]` not `Color-Change Sapphire`; `Garnet (Tsavorite)` not `Tsavorite Garnet`
- Jadeite and Nephrite are varieties of Jade: `Jade (Jadeite, Imperial)` not `Jadeite (Imperial)`
- Standalone mineralogical names (Painite, Alexandrite, Kunzite, Morganite, Aquamarine, etc.) do not need a parent mineral — they are standard gem trade names
- **Common-name cross-references**: the primary display name is always the **proper mineral family**, with the common/trade name in a square-bracket `[aka X]` suffix — `Corundum (Red) [aka Ruby]`, `Beryl (Green) [aka Emerald]`, `Quartz (Purple) [aka Amethyst]`, `Beryl (Red, Fine) [aka Bixbite]`. Never the reverse (`Ruby [aka Red Corundum]` is wrong). Parens stay reserved for Variety/Color/Quality; no commas inside the brackets. Organic/descriptive identities keep their proper name primary too (`Amber [aka Fossilized Resin]`, `Pyrite (Nodule) [aka Fool's Gold]`). Direction and format enforced by `tests/test_treasure_tables.py`.
- All item lists must be sorted alphabetically within each value tier

## Code comments

Add comments throughout all code changes so the intent is clear at a glance:
- **Section headers** (`# ── SECTION ──`) to divide logical blocks within a file
- **Function docstrings** on every non-trivial function explaining inputs, outputs, and why it exists
- **Inline comments** on any expression that isn't immediately obvious — regex patterns, bit-twiddling, session state keys, filter chains, etc.
- **Why comments** when a decision could surprise a reader: why a particular API field is used, why order matters, why a workaround exists

Do NOT omit comments to save space. A future reader should be able to understand each file without cross-referencing other files.

## Architecture

This is a Streamlit multi-page app for D&D campaign management.

**Entry point:** `Home.py` — bare title page. Streamlit auto-discovers pages from the `pages/` directory.

**Data model:** All data is persisted as JSON files in the root directory. There is no database or ORM. Each page loads its JSON on startup into `st.session_state`, and explicit "Save" buttons write changes back to disk via `save_json`.

**Central dependency:** `json/campaigns.json` is the root entity. NPCs, Factions, Faiths, RelationshipMap, Quests, Worldbuilding, Sessions, and HomebrewRules all gate on campaigns existing first, and store their data as dicts keyed by campaign name. Characters, Combat, ResourceTracker, Dice, Monsters, Spells, Items, Conditions, and Races are standalone.

**JSON schemas by file:**

| File | Schema |
|------|--------|
| `json/characters.json` | `[{name, char_class, level, max_hp, current_hp, temp_hp, ac, initiative, str–cha, save_prof, save_xprt, skill_prof, skill_xprt, stat_bonuses, inventory, known_spells, stat_bonuses, advancement_log}]` |
| `json/campaigns.json` | `[{name, system, basic_info}]` |
| `json/npcs.json` | `{campaign_name: {npc_list: [{name, role, importance, priority, description, personality, secrets, notes}], legacy_notes: str}}` |
| `json/factions.json` | `{campaign_name: {faction_list: [{name, description}], alliances: [{name, priority, members: [{name, type}], notes}]}}` |
| `json/faiths.json` | `{campaign_name: [{name, doctrine}]}` |
| `json/relationship_web.json` | `{campaign_name: [{entity_a, rel_type, entity_b, notes}]}` |
| `json/resources.json` | `{character_name: [{name, max, current, reset}]}` — reset values: `"long"`, `"short"`, `"dawn"`, `"manual"` |
| `json/quests.json` | `{campaign_name: [{name, giver, details, completed}]}` |
| `json/worldbuilding.json` | `{campaign_name: {regions: [...], cities: [...], nations: [...], lore: [...], planes: [...]}}` |
| `json/sessions.json` | `{campaign_name: [{date, title, summary, key_events}]}` |
| `json/homebrew_rules.json` | `{campaign_name: [{name, category, description}]}` |
| `json/homebrew_monsters.json` | `[{name, cr, type, size, hp, ac, str–cha, special_abilities, actions, ...}]` |
| `json/homebrew_spells.json` | `[{name, level, school, casting_time, range, components, duration, desc, classes, ...}]` |
| `json/homebrew_items.json` | `[{name, category, rarity, requires_attunement, cost, description}]` |
| `json/homebrew_races.json` | `[{name, size, speed, ability_bonuses, languages, traits (plain text), desc, homebrew: true}]` |

**UI patterns used throughout:**
- Two-step delete confirmation: a `*_delete_pending_*` boolean in `st.session_state` gates a "Confirm?" button before any destructive action.
- Stale session state keys are cleaned up at page load by checking indices against the current list length.
- `st.rerun()` is called after mutations that affect the list structure (add/delete) so the UI re-renders with fresh indices.
- Streamlit widget keys are namespaced with campaign name + index (e.g., `f"{camp_name}_f_name_{idx}"`) to avoid key collisions across campaigns.
- Combat tracker is session-state only (no JSON persistence — combat is ephemeral).

**Live-reactive create forms (no `st.form`):**
- `st.form` batches all widget interactions until submit, preventing mid-form reruns. This breaks class-change → auto-populate saving throws, and prevents live modifier display.
- The character creation form uses plain widgets + a version counter (`create_form_v`) instead. Incrementing the counter changes all widget keys → effectively resets the form on next render.
- Use `st.session_state.get(key, default)` to pre-read current widget values *before* rendering them when the displayed value (like a bonus label) must reflect the live checkbox state.
- Class-keyed checkbox keys (`f"save_prof_{ab}_{class_sel}_{version}"`) cause checkboxes to reinitialise with class defaults whenever the class selectbox changes.

**Open5e v2 API notes:**
- Endpoint root: `https://api.open5e.com/v2/` (lists all available endpoints).
- Races are at `/species/` (not `/races/`); the API uses 2024 PHB terminology.
- Race/species records have no structured size/speed/ability fields — all data is embedded as plain-text trait entries (named "Size", "Speed", "Ability Score Increase", etc.).
- `is_subspecies: true` + `subspecies_of: "slug_key"` indicate subraces; these are flat in the list, not nested under parent races.

**Characters page — pure logic module (`character_lib.py`):**
- All streamlit-free rules data and math live in `character_lib.py` (project root): `ability_mod`, `proficiency_bonus`, `get_classes`, `classes_label`, `SKILL_ABILITY`, `ABILITIES`, `SKILLS`, `CHAR_CLASSES`, `CLASS_SAVE_PROFS`, `STAT_BOOST_ITEMS`, `CLASS_HIT_DICE`, `EQUIP_STATS`, `MULTICLASS_REQS`, `STANDARD_ARRAY`, `POINT_BUY_COSTS/BUDGET`.
- `pages/Characters.py` imports from it; unit tests in `tests/test_character_lib.py` cover the invariants. Add new rules constants there, not in the page file.

**Characters page — saving throw architecture:**
- `CLASS_SAVE_PROFS` (in `character_lib.py`) maps each standard class to its two saving throw proficiencies.
- In create form: checkbox keys include class name so they reset with class defaults on class change.
- In edit section: `class_changed = new_class != ch.get("char_class")` gates whether to use saved values or class defaults; checkbox keys also class-keyed for the same reset behaviour.
- Bonus labels pre-read from `st.session_state` (not from the JSON-loaded `ch`) so they reflect the current checkbox state immediately, before Save is clicked.

**Characters page — multiclassing:**
- `get_classes(ch)` returns `ch["classes"]` if present, otherwise builds `[{"class": ch["char_class"], "level": ch["level"]}]` for backward compatibility with old single-class records.
- `classes_label(classes)` returns `"Fighter 5 / Wizard 3"` style string for the expander title.
- `CLASS_HIT_DICE` maps standard class names → hit die size (used by Level Up).
- `EQUIP_STATS = ["AC", "STR", "DEX", "CON", "INT", "WIS", "CHA", "Initiative"]` — stats that inventory items can modify when equipped.
- The edit form uses session key `mc_count_{i}` to track how many class rows are currently shown. "✕" on a row shifts all subsequent widget keys down so indices stay contiguous.
- `char_class` (primary class, index 0) and `level` (sum of all class levels) are always kept as top-level fields for backward compatibility with Combat and other pages.
- Level is **uncapped** — `min_value=1, max_value=None` everywhere. No negative or decimal levels (enforced by `step=1`).

**Characters page — Level Up dialog:**
- Triggered by "⬆ Level Up" button; `lu_pending_{i}` boolean gates the dialog container.
- Lets the player pick which class gets the level (or add a new class for multiclassing). Unknown/custom classes show a `select_slider` to pick the hit die.
- HP method: "Standard (average)" uses `floor(die/2) + 1 + CON_mod` (minimum 1). "Roll for HP" stores the roll in `lu_roll_{i}` session state so it survives reruns.
- On Apply: updates `classes`, `level`, `char_class`, `max_hp` in session state and JSON; **pops** (does not set) all `mc_cls_{i}_{k}`, `mc_lvl_{i}_{k}`, `max_hp_{i}`, and any new `esavep_*` widget keys so the edit form reinitialises them from `value=ch.get(...)` on the next render; appends an entry to `advancement_log`.
- Widget sync uses pop-then-rerender: popping a widget key after instantiation is always safe; setting it after instantiation raises `StreamlitAPIException`. The handler writes updated data to `st.session_state.characters[i]` before calling `st.rerun()`, so `value=ch.get(...)` in the edit form picks up the new values automatically.

**Characters page — equip bonuses:**
- Inventory items can carry an `equip_bonuses` dict, e.g. `{"AC": 2, "STR": 1}`.
- "⚙" button on each inventory row toggles an inline bonus editor (`inv_cfg_{i}_{ii}` session key). Shows "⚙✓" when bonuses are already set.
- Equipped-item bonuses are pre-read from live checkbox states (`inv_eq_{i}_{ii}`) before stat display renders, so changes take effect immediately without waiting for Save (same pattern as saves/skills checkboxes).
- `_eq_ac`, `_eq_init`, `_eq_ab` are summed from all currently-equipped items and fed into `eff_scores` and the AC/Initiative caption.
- Item JSON schema now always includes `"equipped": false, "equip_bonuses": {}` on creation.

**Characters page — stale session state cleanup:**
- `_STALE_PREFIXES = ("char_delete_pending_", "mc_count_", "lu_pending_")` — cleaned at page load by checking index against current list length.
- `_lu_sync_` is NOT in stale prefixes — that deferred-sync mechanism was removed. The pop-then-rerender pattern is used instead.

**Encounter Builder — count widget:**
- `on_count_change(idx)` callback reads `enc_cnt_{idx}` from session state and updates `enc_monsters[idx]["count"]`. The roster `number_input` uses `on_change=on_count_change, args=(idx,)` instead of comparing return value and calling `st.rerun()`.
- When adding a duplicate monster, the existing count is incremented and `st.session_state[f"enc_cnt_{existing_idx}"] = new_count` is used (direct assignment, not pop). The roster renders *after* the search section, so the widget hasn't been instantiated yet when the button handler fires — direct assignment is safe and ensures the widget shows the updated count.

**Encounter Builder — breakdown caption formatting:**
- Reason/label annotations use square brackets `[label]`, not parentheses. Example: `XP **3** [Medium] + AE **+2** [Outnumbered] + BT **0** [Threatening]`.
- The same convention applies to metric help strings: tier adjustments are written as `[+2 to Result]`, threshold ranges as `Favorable ≤0.5:1 [+0]`, etc.
- Parentheses are still used for factual data that isn't a label/reason (e.g., `CR {cr} (HP {hp})`).

**Encounter Builder — Boss Threat metric (formerly "CR / Monster"):**
- Uses boss-weighted effective XP instead of plain average XP:
  `boss_fraction = max_single_monster_xp / total_raw_xp`
  `effective_xp  = boss_fraction × max_monster_xp + (1 − boss_fraction) × avg_xp`
- For equal monsters this equals avg_xp (no change). For a boss + many minions the effective XP slides toward the boss's value, so cheap extras can't dilute a powerful leader's threat.
- Abbreviated as "BT" in the breakdown caption: `XP **3** [Medium] + AE **+2** [Outnumbered] + BT **0** [Threatening]`.
- `boss_threat_label(effective_xp, easy_threshold_total, party_size)` replaces the old `cr_threat_label`. Tiers live in `_BOSS_THREAT_TIERS`.

**Explanation sweep rule:**
After any substantive change to a metric, formula, or behaviour that has an explanation attached (metric help text, docstrings, inline comments, `st.info`/`st.caption` copy), do a sweep of *all* explanations in that file and fix any that are now stale or misleading. Don't update unrelated files unless the concept is documented there too (e.g., CLAUDE.md architecture notes).

**Encounter Builder — monster pools:**
- Three pools selectable via radio: "SRD Monsters", "Named Creatures", "Both".
- The named/sourcebook pool is `data/monsters_mm.json` (same schema as SRD monsters, plus `source` and `named_creature` fields). "Named Creatures" and "Both" options are hidden when that file doesn't exist.
- `_load_monsters(path, mtime, source_tag)` tags every entry with `_source: "srd"` or `_source: "named"` at load time — used to badge named creatures in search results and prevent cross-source duplicate merges.
- Search uses an index-based selectbox (`range(len(matches))` + `format_func`) so duplicate names across pools are always uniquely selectable.
- Roster entries include a `"source"` field. Duplicate-merge check requires both `name` AND `source` to match.

**Encounter Builder — CR range slider:**
- `st.select_slider` with options `["0","1/8","1/4","1/2","1","2",...,"30"]` and default `("0","30")`.
- Any narrowing from the default activates search without requiring a text query (lets DMs browse by CR band alone).
- When both text and CR filter are active, both apply simultaneously.

**Encounter Builder — hoard loot magic items:**
- Count formula: `base_magic + excess^0.55`, where `base_magic` = highest-CR band's allocation from `HOARD_AUTO_ROLLS` and `excess` = sum of all monsters' allocations minus `base_magic`. Gives a single boss its full haul; adding more monsters scales sub-linearly.
- Rarity always uses the max-CR creature's hoard band so Tiamat-level encounters yield Legendary items.
- `HOARD_AUTO_ROLLS` must be imported from `treasure_tables` in any file that uses this formula.

**Encounter Builder / TreasureGenerator — `loot_section` helper:**
- Lives in `treasure_tables.py` (shared — page files can't import from each other); both pages import it.
- Signature: `loot_section(label, items, approx=False)` — renders one loot category as alphabetical point-form bullets, deduplicating identical `(name, value)` tuples as ×N. `approx=True` prepends `~` to values (Curiosities). 0 gp values display as "worthless".

**Treasure system architecture:**
- `treasure_tables.py` (project root) is the sole data layer for all treasure: coin tables, gem/art/jewelry/trade/curiosity item pools, hoard tables, tier-at-CR functions, and rolling helpers.
- `pages/TreasureGenerator.py` and `pages/EncounterBuilder.py` both import from it. Never duplicate treasure data in page files.

**Random tables module (`random_tables.py`):**
- The old RandomTables page was removed; its tables live in `random_tables.py` (project root) with shared `render_*` helpers so multiple pages get identical roll-button + full-table UI.
- `render_wild_magic(key_prefix, nested=False)` — used by `pages/Spells.py` ("Wild Magic" tab) and `pages/Combat.py` (🎲 expander below the top controls). Pass `nested=True` when calling from inside an expander — it swaps the full-table expander for a `st.toggle` (Streamlit forbids nested expanders).
- `render_dungeon_dressing(key_prefix)` — used by `pages/EncounterBuilder.py` ("Dungeon Dressing" tab).
- `key_prefix` namespaces widget keys per calling page; each caller must pass a unique prefix.

**Treasure tier system:**
- All categories use clean round-number tiers from `{10, 25, 50, 100, 250, 500, 1000, 2500, 5000}` — each step roughly 2–2.5×. No values like 750, 2000, or 7500.
- Per-category tiers: Gems `10/50/100/250/500/1000/5000` · Art & Jewelry `25/100/250/500/1000/2500/5000` · Trade Goods `10/50/100/500/1000/2500` · Curiosities `0/10/25/50/100/250/500/1000/2500` (tier 0 = worthless knick-knacks, displayed as "worthless").
- `HOARD_AUTO_ROLLS` keys must only reference tiers that exist in the corresponding dict.

**Treasure coin scaling (individual treasure):**
- CR 0–16: modest amounts; see `INDIVIDUAL_BY_CR` in `treasure_tables.py`.
- CR 17–20: avg ~19k gp — legendary monsters and adult-to-ancient dragons.
- CR 21–24: avg ~102k gp — demon lords, archdevils, ancient dragons.
- CR 25+: avg ~530k gp — deity-tier threats (Tiamat CR 30, Vecna, etc.).
- Each band's minimum should exceed the previous band's typical average so higher CR unambiguously yields more.

**Treasure extras (items) formula:**
- `_extra_count(cr, threshold, scale) = ((cr - threshold) ^ 1.5) / scale`
- Thresholds/scales in `roll_individual_treasure`: gems `(5, 4)`, art `(5, 5)`, jewelry `(6, 6)`, trade `(9, 8)`, curiosities `(12, 10)`.
- At CR 10: ~3 gems. At CR 20: ~15 gems. At CR 30: ~31 gems — designed so a Tiamat encounter yields a treasury, not a pocket.

**Treasure item name rules:**
- Convention-named categories (Gems, Trade Goods) must not have commas outside parentheses — `Garnet (Tsavorite, Fine)` is correct, prose commas are not. Art Objects, Jewelry, and Curiosities are descriptive prose names and may contain commas. (Enforced by `tests/test_treasure_tables.py`.)
- **No real-world place or culture names** — campaign worlds have no Colombia or Kashmir. Replace place qualifiers with the visual property they denote: Kashmir → `Corundum (Cornflower Blue) [aka Sapphire]`, Paraiba → `Tourmaline (Neon Copper)`. Mineral *trade names* that read as gem words (Tsavorite, Tanzanite, Padparadscha, Malaia) are fine per the standalone-name rule. (Enforced by `tests/test_treasure_tables.py`.)
- No item name may appear at two different tiers within a category. Enforced by tests.
- Items sorted alphabetically within each tier. Lists deduplicated as ×N in display.

**Reference pages — pagination:**
- `utils.page_nav(items, page_key, sig_key, filter_sig, page_size=50)` — shared helper used by all SRD reference pages (`PAGE_SIZE` also lives in utils).
- `page_nav` resets to page 1 automatically when `filter_sig` changes (new search term or filter value). Shows Previous/Next buttons only when results exceed the page size. Shows `"{n} found — showing {start+1}–{end} [page {page} of {total_pages}]"` caption format.
- Pagination applies to: SRD Monsters, Named Creatures, Magic Items, Equipment, Weapons, Armor, SRD Spells, SRD Races, Feats, Backgrounds, and Classes result lists. New reference result lists must use `page_nav` too (homebrew lists and the ~20-entry Tattoos tab are exempt — they can't exceed a page).

**Monsters page — caching architecture:**
- `_monster_options(path, mtime)` — cached loader for SRD monsters. Pre-computes `_cr_float`, `_role_tags`, and `_name_norm` on every monster so filters never rerun expensive operations. Keyed on mtime so cache busts when file changes.
- `_named_monster_options(path, mtime)` — same for `data/monsters_mm.json` (WotC sourcebook monsters). Returns `(data, all_sources, cr_values)`.
- `_filtered_srd_monsters(path, mtime, gamesystem)` — caches the `deduplicate_editions()` or `filter_by_edition()` result per gamesystem so the full 3,200-monster walk only runs when the edition selector changes.
- **Cache-busting rule:** when `monster_roles()` logic changes, update the docstring of `_monster_options` (changing its bytecode hash) so Streamlit invalidates the cached `_role_tags`. The docstring line lists the current role set.

**Monsters page — role tagging:**
- `ALL_ROLES` and `monster_roles()` are defined at the top of `Monsters.py`. Adding/changing a role requires: (1) update `ALL_ROLES` list, (2) update `monster_roles()` detection logic, (3) update `_monster_options` docstring to bust the role-tag cache.
- Current roles and their primary detection signals:
  - **Melee** — `"melee weapon attack"` or `"melee spell attack"` in action text
  - **Ranged** — `"ranged weapon attack"`, `"ranged spell attack"`, `"shortbow"`, `"longbow"`, `"crossbow"`, or `"thrown"` in text
  - **Spellcaster** — `"spellcasting"`, `"innate spellcasting"`, `"spell save dc"`, `"cantrip"`, or `"spell attack modifier"` in text
  - **Controller** — any condition keyword (charmed/frightened/stunned/paralyzed/incapacitated/restrained/blinded/petrified) AND `"saving throw"` both present
  - **Support** — healing-others text (`"regain"/"heal"/"cure"` + `"friendly"/"ally"/"allies"/"each creature"/"one creature"/"you touch"`) OR action name contains `"healing"/"cure"/"leadership"/"rallying"/"bolster"/"channel divinity"/"aura of protection"/"aura of courage"/"inspiring"/"aid"`
  - **Tank** — CR-relative HP via `_tank_hp_floor(cr)` (floors: CR≤0→10, ≤¼→20, ≤½→35, ≤1→50, ≤2→65, ≤4→85, ≤6→110, ≤9→140, ≤12→170, ≤16→220, ≤20→280, higher→cr×18) OR CR-relative AC via `_tank_ac_tier(ac) > cr_float` (maps AC≤13→tier 0, 14→4, 15→5, 16→8, 17→10, 18→13, 19+→17; qualifies when that tier > actual CR) OR `"legendary resistance"` OR `"regenerat"` OR `"parry"` OR `"indomitable"` in text
  - **Legendary** — non-empty `legendary_actions` field
  - **Swarm** — `"swarm"` in monster name or first 50 chars of action text

**Monsters page — stat block display rules:**
- **AC:** displayed as `"17 [Natural Armor]"` — `ac_text` field title-cased and wrapped in square brackets. If `ac_text` is empty, just the number.
- **Senses:** first letter of each comma-separated entry is capitalized at render time (e.g. `"darkvision 60 ft., passive Perception 14"` → `"Darkvision 60 ft., Passive Perception 14"`). The JSON data is also pre-fixed; the render step is a defensive fallback.
- **Action sort order (5-tier):** 0 = standalone specials not called by Multiattack · 1 = Multiattack referencing specials · 2 = specials the Multiattack calls out · 3 = generic Multiattack · 4 = basic weapon/spell attacks. Data in all three JSON files is pre-sorted to match. `is_weapon` detection covers both 2014 format (`"weapon attack"/"spell attack"`) and 2024 format (`"attack roll:"`).
- **Innate Spellcasting format:** descriptions must be bullet-point lists sorted by frequency — At Will first, then descending day-count (3/Day before 1/Day). Labels: `At Will`, `X/Day`, `X/Day Each`. The JSON data is pre-formatted; if you add a monster with prose-format spellcasting, run the reformat script or fix manually.

**Epic tier (levels 21–30):**
- `XP_THRESHOLDS` in `EncounterBuilder.py` extends to L30 with extrapolated values (~15% growth/level; L30 deadly = 50,400 XP).
- `LEVEL_POWER_FACTOR` extends to L30: L21–24 = 3.70–4.30 (first epic boons), L25–28 = 4.60–5.20 (legendary abilities), L29–30 = 5.40–5.80 (demigod threshold).
- `SPELL_SLOT_TABLE` and `WARLOCK_PACT_MAGIC` in `Combat.py` extend to L30; levels 21–30 retain L20 slot counts (standard 5e epic — boons grant features, not more slots).
- Party level slider and per-player inputs in EncounterBuilder max at 30 (not 20).
- `party_thresholds()` clamp is `min(30, lvl)`.

**NPCs page — simplified schema:**
- `npcs.json` now stores only `{npc_list, legacy_notes}` per campaign. The old `relationship_web` and `groups` keys are no longer written here.
- Each NPC has a `priority` field (1–10, default 5). Higher priority = that NPC becomes Entity A in the Relationship Map when auto-assigned. Shown as `· P{n}` in the NPC list expander title.
- `_migrate_camp()` handles v1 (plain text fields) → v2 (structured) on first load.

**Factions page — v2 schema and alliances:**
- `factions.json` schema changed from `{campaign_name: [faction, ...]}` to `{campaign_name: {faction_list: [...], alliances: [...]}}`. `_migrate_camp()` wraps old flat lists on first load.
- Faction records: `{name, description}` only — the old `alliances` and `conflicts` free-text fields are removed. Use the Relationship Map for those connections.
- Alliance records: `{name, priority, members: [{name, type}], notes}`. `type` is one of `"faction"`, `"npc"`, `"faith"`, or `"alliance"` (for sub-alliances / nested groups).
- Sub-alliances (type="alliance" members) create nested compound nodes on the Relationship Map (box inside box).
- Alliance `priority` (1–10) affects auto-assignment of Entity A/B in the Relationship Map, same as NPC priority.

**Faiths page — simplified:**
- `faiths.json` records now store only `{name, doctrine}`. The `conflicts` field is removed from create/edit forms (old data remains in JSON but is never shown or written). Use the Relationship Map for faith conflicts.

**Relationship Map — architecture:**
- **Data:** `json/relationship_web.json` — `{campaign_name: [{entity_a, rel_type, entity_b, notes}]}`. Owned exclusively by `RelationshipMap.py`. On first load, `_migrate_from_npcs()` copies any legacy `relationship_web` data from `npcs.json` (one-time, non-destructive).
- **Entity sources:** alliances (from `factions.json`, ★ compound nodes) → factions (□ rectangles) → faiths (◇ diamonds) → NPCs (○ ellipses). Dropdown in the relationship creator lists them in this order, sorted priority-desc then alpha within each group.
- **Visualization:** rendered as a self-contained Cytoscape.js HTML page via `st.components.v1.html`. Cytoscape.js is loaded from CDN (`cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js`) — no Python graphviz dependency.
- **Compound nodes:** alliances are Cytoscape compound parent nodes; their members render as children inside the alliance box. Sub-alliances (alliance-type members) nest as compound-inside-compound, producing visible box-inside-box nesting.
- **Overlapping boxes:** Ally edges between two alliance compound nodes use `idealEdgeLength: 10` and `edgeElasticity: 300` with `nodeOverlap: 4` in the CoSE layout. The spring force pulls allied alliance boxes together until they geometrically overlap.
- **Cross-boundary edges:** edges between individual members (inside or outside any alliance) are regular Cytoscape edges; they route across compound boundaries automatically.
- **Node ID scheme:** `_cid(prefix, name)` — prefix is `"a"` (alliance), `"f"` (faction), `"r"` (faith), `"n"` (NPC), `"e{i}"` (edge). Names are sanitised with `re.sub(r"[^a-zA-Z0-9]", "_", name)`.
- **`_entity_labels()`** builds the selectbox list; `_auto_assign()` swaps A/B so higher-priority entity is always A (alpha tiebreaker).
- Relationship creator is at the **top** of the page (above the graph). Entity A and B are index-based `st.selectbox` widgets (searchable by typing, scrollable).

**Resource Tracker — architecture:**
- `json/resources.json` — `{character_name: [{name, max, current, reset}]}`. Reset values: `"long"`, `"short"`, `"dawn"`, `"manual"`.
- Characters are loaded from `json/characters.json`; resource pools are stored separately (character records are not modified).
- `_on_cur_change(char_name, ri, widget_key)` is the `on_change` callback for each resource's `number_input` — writes directly to `st.session_state.res_data` and saves to disk immediately without a Save button.
- Short Rest restores resources with `reset="short"`; Long Rest restores all.
- `CLASS_TEMPLATES` dict maps class name → list of `(name, default_max, reset_type)` tuples for one-click pre-population. Spell slot quick-add buttons are auto-generated from `_SLOT_TABLE` at the character's current level.

**Shop Generator — architecture:**
- Standalone `pages/ShopGenerator.py` in the Tools group; no JSON persistence (generate on demand).
- `SHOP_TYPES` dict maps shop type → list of SRD item categories to draw from. `data/items_srd.json` and `data/magicitems.json` are the sources.
- Magic shops filter `magicitems.json` by rarity tier appropriate to party level (`_rarities_for_level(level)`).
- `STOCK_SIZES` controls item count range (Sparse 4–7, Normal 8–14, Well-Stocked 15–22).
- `PRICE_MODS` applies a multiplier to base item cost (Discount ×0.7 → Extortionate ×2.0).
- Jeweler shop uses `GEMS` and `JEWELRY` pools from `treasure_tables.py`. Tavern uses a curated `_TAVERN_STOCK` list. Fletcher adds ranged weapons via `_RANGED_KEYWORDS` filter on top of the Ammunition category.
- Results are sorted alphabetically and displayed as a table with Item / Qty / Price / Notes columns. Re-clicking Generate produces a new randomised stock; results live in `st.session_state.shop_stock`.
