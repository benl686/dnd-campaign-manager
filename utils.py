import json
from pathlib import Path


# ── Condition reference data ──────────────────────────────────────────────────
# Shared by Conditions.py (display page) and Combat.py (inline reference panel).
# Keeping it here avoids importing Conditions.py, which has top-level st.* calls.

CONDITION_DATA = {
    "Blinded": {
        "desc": "A blinded creature can't see and automatically fails any ability check that requires sight. Attack rolls against the creature have advantage, and the creature's attack rolls have disadvantage.",
        "ends": "Until the effect that caused it ends (spell, disease, etc.).",
    },
    "Charmed": {
        "desc": "A charmed creature can't attack the charmer or target the charmer with harmful abilities or magical effects. The charmer has advantage on any ability check to interact socially with the creature.",
        "ends": "When the charmer harms the creature, or the effect ends.",
    },
    "Deafened": {
        "desc": "A deafened creature can't hear and automatically fails any ability check that requires hearing.",
        "ends": "Until the effect that caused it ends.",
    },
    "Exhausted": {
        "desc": "Levels 1–6. Level 1: Disadvantage on ability checks. Level 2: Speed halved. Level 3: Disadvantage on attacks and saving throws. Level 4: Max HP halved. Level 5: Speed reduced to 0. Level 6: Death.",
        "ends": "Finishing a long rest (with food/drink) removes one exhaustion level.",
    },
    "Frightened": {
        "desc": "A frightened creature has disadvantage on ability checks and attack rolls while the source of its fear is within line of sight. The creature can't willingly move closer to the source of its fear.",
        "ends": "When the creature can no longer see or hear the source.",
    },
    "Grappled": {
        "desc": "A grappled creature's speed becomes 0, and it can't benefit from any bonus to its speed. The condition ends if the grappler is incapacitated or if an effect removes the grappled creature from the reach of the grappler.",
        "ends": "Grappler is incapacitated, or the target escapes (Athletics or Acrobatics vs. grappler's Athletics).",
    },
    "Incapacitated": {
        "desc": "An incapacitated creature can't take actions or reactions.",
        "ends": "Until the effect that caused it ends.",
    },
    "Invisible": {
        "desc": "An invisible creature is impossible to see without magic or a special sense. Attack rolls against the creature have disadvantage, and the creature's attack rolls have advantage.",
        "ends": "Until the effect that caused it ends.",
    },
    "Paralyzed": {
        "desc": "A paralyzed creature is incapacitated and can't move or speak. It automatically fails STR and DEX saving throws. Attack rolls against it have advantage. Any hit within 5 feet is a critical hit.",
        "ends": "Until the effect that caused it ends.",
    },
    "Petrified": {
        "desc": "Transformed into solid inanimate substance. Incapacitated, can't move or speak, unaware of surroundings. Automatically fails STR and DEX saves. Resistance to all damage. Immune to poison and disease.",
        "ends": "Until greater restoration or similar magic is used.",
    },
    "Poisoned": {
        "desc": "A poisoned creature has disadvantage on attack rolls and ability checks.",
        "ends": "Until the poison is neutralized (antitoxin, lesser restoration, etc.).",
    },
    "Prone": {
        "desc": "Only movement option is to crawl unless the creature stands up (costing half movement). Disadvantage on attack rolls. Attacks against it have advantage within 5 ft., or disadvantage from farther away.",
        "ends": "Spend half movement speed to stand up.",
    },
    "Restrained": {
        "desc": "Speed becomes 0. Attack rolls against the creature have advantage; its attack rolls have disadvantage. The creature has disadvantage on DEX saving throws.",
        "ends": "Until the restraint is removed or escaped.",
    },
    "Stunned": {
        "desc": "Incapacitated, can't move, and can speak only falteringly. Automatically fails STR and DEX saving throws. Attack rolls against the creature have advantage.",
        "ends": "Until the effect that caused it ends.",
    },
    "Unconscious": {
        "desc": "Incapacitated, can't move or speak, unaware of surroundings. Drops held items, falls prone. Automatically fails STR and DEX saves. Attacks have advantage; any hit within 5 ft. is a critical hit.",
        "ends": "Until the creature regains consciousness (HP restored, lesser restoration, etc.).",
    },
}


# ── JSON helpers ──────────────────────────────────────────────────────────────

def load_json(path, default=None):
    """Read a JSON file from disk and return its contents.

    Returns `default` (empty list if not specified) when the file doesn't exist.
    Used for small, frequently-written files like json/homebrew_monsters.json where
    we always want a fresh read (no caching).
    """
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return [] if default is None else default


# Module-level holder for the @st.cache_data-wrapped loader. Built lazily on
# first use (streamlit may be unavailable in tests/scripts) and memoised so the
# decorated function is created exactly once — building it inside
# load_json_cached would recreate the wrapper on every call.
_CACHED_LOADER = None


def _get_cached_loader():
    """Return the cached file loader, creating and memoising it on first call."""
    global _CACHED_LOADER
    if _CACHED_LOADER is None:
        import streamlit as st

        @st.cache_data(show_spinner=False)
        def _load(p, mtime):
            # mtime is included in the cache key so edits bust the cache automatically
            return json.loads(Path(p).read_text(encoding="utf-8"))

        _CACHED_LOADER = _load
    return _CACHED_LOADER


def load_json_cached(path, default=None):
    """Cache-backed version of load_json for large read-only reference files.

    Uses Streamlit's @st.cache_data keyed on the file's mtime so the cache is
    automatically busted whenever the file changes on disk (e.g. after re-running
    scripts/download_data.py). Falls back to load_json if Streamlit isn't available.

    Use this instead of load_json for the big data/ files (monsters, spells, items,
    magicitems) — they can be several MB and re-reading them on every Streamlit
    interaction would make the app noticeably slow.
    """
    try:
        p = Path(path)
        if not p.exists():
            return [] if default is None else default
        return _get_cached_loader()(str(p), p.stat().st_mtime)
    except Exception:
        return load_json(path, default)


def save_json(path, data):
    """Write `data` to a JSON file atomically, creating parent folders if needed.

    Write order matters here — it guarantees no crash can corrupt user data:
      1. Serialize to a sibling .tmp file (never touches the real file).
      2. Atomically move the current file to .bak (os.replace is atomic on NTFS).
      3. Atomically move .tmp over the real path.
    If the process dies at any point (e.g. the Exit button's os._exit), the
    previous good copy survives as either the original file or its .bak.
    """
    import os
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)   # fresh clones have no json/ folder
    tmp = Path(str(p) + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if p.exists():
        os.replace(p, str(p) + ".bak")            # keep last good version as backup
    os.replace(tmp, p)


# ── UI preference persistence ─────────────────────────────────────────────────
# Lightweight key-value store in json/ui_prefs.json.
# Use get_pref() BEFORE rendering a widget (to pre-seed session_state so the
# widget picks up the saved value), then save_prefs() AFTER the widget block.

_PREFS_PATH = "json/ui_prefs.json"


def get_pref(key, default):
    """Ensure st.session_state[key] is initialised from ui_prefs.json.

    On the first render of a new browser session the value is read from disk.
    On subsequent renders within the same session the already-present
    session_state value is returned immediately (no disk read).
    Always call this before the widget that uses key=key so Streamlit sees the
    saved value in session_state when it builds the widget.
    """
    import streamlit as st
    if key not in st.session_state:
        prefs = load_json(_PREFS_PATH, {})
        st.session_state[key] = prefs.get(key, default)
    return st.session_state[key]


def save_prefs(updates: dict):
    """Merge updates into ui_prefs.json. Only writes when at least one value changed."""
    prefs = load_json(_PREFS_PATH, {})
    if any(prefs.get(k) != v for k, v in updates.items()):
        prefs.update(updates)
        save_json(_PREFS_PATH, prefs)


# ── Campaign gating ───────────────────────────────────────────────────────────
# json/campaigns.json is the root entity — campaign-scoped pages load it and
# show a standard notice when empty. Campaigns.py (the creator page) manages
# the file itself and doesn't use these helpers.

CAMPAIGNS_PATH = "json/campaigns.json"


def load_campaigns():
    """Fresh-read the campaign list that campaign-scoped pages gate on."""
    return load_json(CAMPAIGNS_PATH, [])


def no_campaigns_notice():
    """Standard empty-state message — render it where the campaign UI would go."""
    import streamlit as st
    st.info("No campaigns yet. Create one on the Campaigns page first.")


# ── Two-step delete confirmation ──────────────────────────────────────────────

def confirm_delete(container, flag_key, key, label="Delete", confirm_label="Confirm?"):
    """Two-step destructive-action button (see CLAUDE.md destructive action rules).

    First click arms `flag_key` in session_state and reruns; the button then
    renders as `confirm_label`. The second click disarms the flag and returns
    True — the caller performs the actual deletion and calls st.rerun().

    container — st, a column, or any element container to render the button in
    flag_key  — session_state key holding the armed/pending boolean; callers
                keep their existing `*_delete_pending_*`-style names so
                page-level stale-key cleanup sweeps keep working
    key       — widget key base; buttons use f"{key}_del" / f"{key}_confirm"

    Not usable inside st.form (forms only rerun on submit) — form-based
    deletes must keep hand-rolled form_submit_button logic.
    """
    import streamlit as st
    if not st.session_state.get(flag_key):
        if container.button(label, key=f"{key}_del"):
            st.session_state[flag_key] = True
            st.rerun()
        return False
    if container.button(confirm_label, key=f"{key}_confirm"):
        st.session_state[flag_key] = False
        return True
    return False


# ── Pagination ────────────────────────────────────────────────────────────────

PAGE_SIZE = 50  # max entries shown per page in reference tables


def page_nav(items, page_key, sig_key, filter_sig, page_size=PAGE_SIZE):
    """Paginate `items`, show nav controls if needed, return the current-page slice.

    Resets to page 1 automatically when filter_sig changes so stale page numbers
    don't leave the user on a now-empty page after narrowing the search.
    page_key   — session_state key that holds the current page number (int)
    sig_key    — session_state key that holds the last-seen filter fingerprint
    filter_sig — hashable value representing the current active filters
    """
    import math
    import streamlit as st

    # Reset to page 1 whenever the filters change
    if st.session_state.get(sig_key) != filter_sig:
        st.session_state[sig_key] = filter_sig
        st.session_state[page_key] = 1

    n = len(items)
    total_pages = max(1, math.ceil(n / page_size))
    page = max(1, min(st.session_state.get(page_key, 1), total_pages))
    start = (page - 1) * page_size
    end   = min(start + page_size, n)

    if n > page_size:
        st.caption(
            f"{n} found — showing {start + 1}–{end} "
            f"[page {page} of {total_pages}]"
        )
        nc1, nc2, nc3 = st.columns([1, 3, 1])
        if nc1.button("← Prev", key=f"{page_key}_prev", disabled=(page <= 1)):
            st.session_state[page_key] = page - 1
            st.rerun()
        nc2.markdown(f"<div style='text-align:center'>Page {page} of {total_pages}</div>",
                     unsafe_allow_html=True)
        if nc3.button("Next →", key=f"{page_key}_next", disabled=(page >= total_pages)):
            st.session_state[page_key] = page + 1
            st.rerun()
    else:
        st.caption(f"{n} found")

    return items[start:end]


# ── Text helpers ──────────────────────────────────────────────────────────────

import re as _re

# Compiled once at import — strip_links runs on every action/trait/spell line of
# every rendered stat block, so skipping the per-call regex-cache lookup matters.
_MD_LINK = _re.compile(r'\[([^\]]+)\]\([^)]+\)')

def strip_links(text: str) -> str:
    """Remove markdown hyperlinks from SRD text, keeping only the display label.

    Open5e embeds links like [true seeing](https://api.open5e.com/...) in
    descriptions. Streamlit renders these as clickable URLs, which is distracting
    in a local reference tool. This strips them to plain text.
    """
    return _MD_LINK.sub(r'\1', text or "")


# ── Edition filtering ─────────────────────────────────────────────────────────

# Maps the human-readable label shown in the UI to the gamesystem_key stored in
# the downloaded JSON. None means "show everything regardless of edition".
EDITION_KEYS = {
    "All":       None,
    "2014 Rules": "5e-2014",
    "2024 Rules": "5e-2024",
    "A5E":        "a5e",       # Level Up: Advanced 5th Edition (EN Publishing)
}

# Reverse map: gamesystem_key → display label used in expander headers.
# "5e-both" is a synthetic key assigned by deduplicate_editions() when a record
# is identical across both editions. Keys not listed here return "" so they're
# silently omitted from the header.
_EDITION_LABEL_MAP = {
    "5e-2014": "2014 Rules",
    "5e-2024": "2024 Rules",
    "5e-both": "2014/2024 Rules",
    "a5e":     "A5E",           # Level Up: Advanced 5th Edition
}


def edition_label(gamesystem_key: str) -> str:
    """Return a short display label for a gamesystem_key, e.g. '2014 Rules'.

    Returns '' for unknown/missing keys so callers can gate on truthiness.
    """
    return _EDITION_LABEL_MAP.get(gamesystem_key or "", "")


def deduplicate_editions(records, key_fields=None, same_fn=None):
    """Merge records that appear in both 5e-2014 and 5e-2024 into a single entry.

    Two records are considered "the same" when either:
      • same_fn(record_2014, record_2024) returns True  — use for custom logic, OR
      • all key_fields have identical (lowercased, stripped) values  — simple fallback

    Matching pairs are collapsed into one record with gamesystem_key='5e-both'.
    Differing pairs are kept as two separate entries so the user can compare.
    Records from only one edition, or from non-5e keys, are returned unchanged.
    Only call this when the 'All' edition is active — per-edition views use
    filter_by_edition instead.
    """
    from collections import defaultdict

    by_name = defaultdict(list)
    for r in records:
        by_name[r.get("name", "")].append(r)

    result = []
    for _name, group in by_name.items():
        entry_2014 = next((r for r in group if r.get("gamesystem_key") == "5e-2014"), None)
        entry_2024 = next((r for r in group if r.get("gamesystem_key") == "5e-2024"), None)
        # Anything that isn't one of the two main 5e editions (e.g. homebrew) passes through
        others     = [r for r in group if r.get("gamesystem_key") not in ("5e-2014", "5e-2024")]

        if entry_2014 and entry_2024:
            if same_fn is not None:
                same = same_fn(entry_2014, entry_2024)
            elif key_fields is not None:
                same = all(
                    str(entry_2014.get(f, "")).lower().strip() ==
                    str(entry_2024.get(f, "")).lower().strip()
                    for f in key_fields
                )
            else:
                same = False

            if same:
                # Use 2014 as the display copy; mark as shared across both editions
                result.append({**entry_2014, "gamesystem_key": "5e-both"})
            else:
                # Genuinely differs — show both so the user can compare
                result.extend([entry_2014, entry_2024])
        elif entry_2014:
            result.append(entry_2014)
        elif entry_2024:
            result.append(entry_2024)

        result.extend(others)

    return result


def edition_selector(sidebar=True):
    """Render a radio button for edition filtering and return the active gamesystem key.

    Stores the selection in st.session_state["edition"] so it persists across
    page navigations within the same session. Returns None when "All" is selected.
    """
    import streamlit as st
    container = st.sidebar if sidebar else st
    edition = container.radio(
        "Edition",
        list(EDITION_KEYS.keys()),
        index=list(EDITION_KEYS.keys()).index(st.session_state.get("edition", "All")),
        horizontal=True,
        key="edition_radio",
    )
    st.session_state["edition"] = edition
    return EDITION_KEYS[edition]


def filter_by_edition(records, gamesystem_key):
    """Filter a list of records to only those matching `gamesystem_key`.

    Pass None (returned by edition_selector when "All" is chosen) to skip
    filtering and return every record unchanged.
    """
    if gamesystem_key is None:
        return records
    return [r for r in records if r.get("gamesystem_key") == gamesystem_key]


def sidebar_exit_button():
    """Render an Exit button in the sidebar — idempotent, safe to call multiple times.

    Home.py calls this before pg.run() so the button always appears.
    Individual page calls are no-ops: the script-run context flag ensures
    the button is only added to the sidebar once per render cycle.
    """
    import os
    import time
    import threading
    import streamlit as st
    # Use the Streamlit script-run context as a per-render flag so duplicate
    # calls within the same render cycle are silently ignored.
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        if ctx is not None:
            if getattr(ctx, "_exit_btn_rendered", False):
                return
            ctx._exit_btn_rendered = True
    except Exception:
        pass  # internal API unavailable — fall through and render normally
    if st.sidebar.button("⏻ Exit", width='stretch', help="Shut down the Streamlit server"):
        # Browsers refuse window.close() on tabs a script didn't open, and
        # st.markdown strips <script> tags anyway — so just tell the user.
        st.sidebar.success("Server stopped — you can close this tab.")

        def _kill():
            time.sleep(0.5)
            os._exit(0)

        threading.Thread(target=_kill, daemon=True).start()
