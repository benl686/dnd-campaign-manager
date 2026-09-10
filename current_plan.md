# Plan: Dedupe + efficiency refactor (2026-07-04)

Items from code-review suggestions, approved by Ben.

- [x] 1. Move `_loot_section` into `treasure_tables.py`; update TreasureGenerator + EncounterBuilder; drop CLAUDE.md dual-copy warning
- [x] 2. Move `_page_nav` + `PAGE_SIZE` into `utils.py`; update Monsters + Items
- [x] 3. Add `utils.confirm_delete()` helper; refactor all two-step delete sites (~22 across 15 files)
- [x] 4. Add campaign-gating helper in `utils.py`; refactor campaign-dependent pages
- [x] 5. Split data tables out of NameGenerator.py / NPCs.py into root modules; extract Characters.py pure helpers to `character_lib.py`
- [x] 6. Fix `load_json_cached` — define cached inner loader once at module level
- [x] 7. Fix Exit button dead `window.close()` script
- [x] 8. Add pytest invariant tests for treasure_tables (+ extracted helpers)
- [x] 9. CLAUDE.md sweep for stale docs; final commit
