import datetime
import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, load_campaigns, no_campaigns_notice
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

PLANNER_PATH   = Path("json/session_planner.json")
SESSIONS_PATH  = Path("json/sessions.json")


# ── Session state ─────────────────────────────────────────────────────────────

if "planner_data" not in st.session_state:
    st.session_state.planner_data = load_json(PLANNER_PATH, {})


def save_planner():
    """Persist the planner to disk."""
    save_json(PLANNER_PATH, st.session_state.planner_data)


def _empty_plan() -> dict:
    """Return a blank plan with the simplified flat schema."""
    return {
        "title":             "",
        "planned_date":      datetime.date.today().isoformat(),
        "premise":           "",   # session plan / what you want to accomplish
        "key_events":        "",   # free-form prep notes: hooks, NPCs, locations, encounters
        "attendance":        "",   # expected players / characters
        "xp_awarded":        "",   # planned milestone or XP
        "rewards":           "",   # planned loot / rewards
        "cliffhanger_setup": "",   # how you want the session to end
        "next_hooks":        "",   # threads you want to set up for next time
    }


def _migrate_plan(plan: dict) -> dict:
    """Migrate an old multi-field plan (hooks/npcs/locations/encounters/…)
    to the new flat schema that mirrors the Sessions page layout.
    Returns the plan unchanged if it's already in the new format.
    """
    if "key_events" in plan:
        # Already new schema — just fill any missing keys with defaults
        for k, v in _empty_plan().items():
            plan.setdefault(k, v)
        return plan

    # Compile the old separate sections into one key_events block
    parts = []
    for label, field in [
        ("🎯 HOOKS & STORY THREADS", "hooks"),
        ("👥 NPCs",                  "npcs"),
        ("🗺 LOCATIONS",             "locations"),
        ("⚔️ ENCOUNTERS",            "encounters"),
    ]:
        if plan.get(field):
            parts.append(f"{label}\n{plan[field]}")

    return {
        "title":             plan.get("title", ""),
        "planned_date":      plan.get("planned_date", datetime.date.today().isoformat()),
        "premise":           plan.get("premise", "") or plan.get("session_goal", ""),
        "key_events":        "\n\n".join(parts),
        "attendance":        "",
        "xp_awarded":        "",
        "rewards":           plan.get("rewards", ""),
        "cliffhanger_setup": plan.get("cliffhanger_setup", ""),
        "next_hooks":        "",
    }


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Session Planner")
st.caption(
    "Plan your next session here. When it's over, switch to **Session Done** "
    "to log what happened — it pre-fills from your plan and saves straight to Session Notes."
)

campaigns = load_campaigns()
if not campaigns:
    no_campaigns_notice()
    st.stop()

camp_names = [c["name"] for c in campaigns]
camp_name  = st.selectbox("Campaign", camp_names, key="planner_camp")

# Load, migrate if needed, and store back
raw_plan = st.session_state.planner_data.get(camp_name, _empty_plan())
plan     = _migrate_plan(raw_plan)
st.session_state.planner_data[camp_name] = plan

st.divider()

tab_plan, tab_done = st.tabs(["📋 Planning", "✅ Session Done"])


# ══════════════════════════════════════════════════════════════════════════════
# PLANNING TAB — same field layout as "Add New Session" in Sessions.py
# ══════════════════════════════════════════════════════════════════════════════

with tab_plan:

    st.caption(
        "Plan your next session. Uses the same fields as Session Notes so "
        "the Session Done tab can pre-fill them for you when the session ends."
    )

    # ── Title + Date ──────────────────────────────────────────────────────────

    try:
        _plan_date_default = datetime.date.fromisoformat(plan.get("planned_date", datetime.date.today().isoformat()))
    except ValueError:
        _plan_date_default = datetime.date.today()

    # Pre-set the widget key from saved data on first load for this campaign.
    # Never pass value= on subsequent renders — that would override the user's selection.
    _date_key = f"plan_date_{camp_name}"
    if _date_key not in st.session_state:
        st.session_state[_date_key] = _plan_date_default

    pc1, pc2 = st.columns([1, 3])
    plan_date  = pc1.date_input("Planned Date", key=_date_key)
    plan_title = pc2.text_input(
        "Session title",
        value=plan.get("title", ""),
        placeholder="e.g. The Siege of Ironhold",
        key=f"plan_title_{camp_name}",
    )

    # ── Main planning fields ──────────────────────────────────────────────────

    plan_premise = st.text_area(
        "Session Premise",
        value=plan.get("premise", ""),
        height=100,
        placeholder="What's the broad plan for this session? What do you want to accomplish?",
        key=f"plan_premise_{camp_name}",
    )

    plan_key_events = st.text_area(
        "Prep Notes — Hooks, NPCs, Locations & Encounters",
        value=plan.get("key_events", ""),
        height=220,
        placeholder=(
            "Jot down everything you're prepping. For example:\n\n"
            "🎯 HOOKS\n- Resolve the missing prince plot\n- Introduce the Thieves Guild contact\n\n"
            "👥 NPCs\n- Lord Malkavian — wants the orb, will betray at the last moment\n\n"
            "🗺 LOCATIONS\n- The Dark Tower: tense, cramped, flickering torches\n\n"
            "⚔️ ENCOUNTERS\n- Guard Captain (CR 5, can be bribed)\n- Tower Boss (CR 10, deadly)"
        ),
        key=f"plan_key_events_{camp_name}",
        help="Free-form. Structure it however works for you — this field pre-fills Key Events in Session Done.",
    )

    # ── Detail row (mirrors Sessions.py add form) ─────────────────────────────

    fa1, fa2, fa3 = st.columns(3)
    plan_attendance = fa1.text_input(
        "Expected Attendance",
        value=plan.get("attendance", ""),
        placeholder="Aria, Thrak, Zephyr…",
        key=f"plan_att_{camp_name}",
        help="Who is confirmed for this session?",
    )
    plan_xp = fa2.text_input(
        "Planned Milestone / XP",
        value=plan.get("xp_awarded", ""),
        placeholder="e.g. Lvl 7 or 400 XP",
        key=f"plan_xp_{camp_name}",
    )
    plan_rewards = fa3.text_input(
        "Planned Rewards",
        value=plan.get("rewards", ""),
        placeholder="e.g. Sword of Truth, 500 gp",
        key=f"plan_rewards_{camp_name}",
    )

    plan_cliffhanger = st.text_area(
        "Planned Cliffhanger",
        value=plan.get("cliffhanger_setup", ""),
        height=70,
        placeholder="How do you want the session to end? What image will leave players wanting more?",
        key=f"plan_cliff_{camp_name}",
    )
    plan_next = st.text_area(
        "Story Threads to Set Up",
        value=plan.get("next_hooks", ""),
        height=70,
        placeholder="Foreshadowing, new questions to introduce, threads to leave dangling…",
        key=f"plan_next_{camp_name}",
    )

    st.divider()

    # ── Save / Clear ──────────────────────────────────────────────────────────

    sc1, sc2 = st.columns([3, 1])
    if sc1.button("Save Plan", type="primary", width='stretch'):
        st.session_state.planner_data[camp_name] = {
            "title":             plan_title.strip(),
            "planned_date":      plan_date.isoformat(),
            "premise":           plan_premise.strip(),
            "key_events":        plan_key_events.strip(),
            "attendance":        plan_attendance.strip(),
            "xp_awarded":        plan_xp.strip(),
            "rewards":           plan_rewards.strip(),
            "cliffhanger_setup": plan_cliffhanger.strip(),
            "next_hooks":        plan_next.strip(),
        }
        save_planner()
        st.success("Plan saved.")

    clear_key = f"plan_clear_pending_{camp_name}"
    if clear_key not in st.session_state:
        st.session_state[clear_key] = False
    if not st.session_state[clear_key]:
        if sc2.button("Clear Plan", width='stretch'):
            st.session_state[clear_key] = True
            st.rerun()
    else:
        if sc2.button("Confirm Clear?", type="primary", width='stretch'):
            st.session_state.planner_data[camp_name] = _empty_plan()
            save_planner()
            st.session_state[clear_key] = False
            # Drop the date widget key so it reinitialises to today on next render
            st.session_state.pop(f"plan_date_{camp_name}", None)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SESSION DONE TAB — same field layout as "Add New Session" in Sessions.py,
# pre-filled from the saved plan's matching fields.
# ══════════════════════════════════════════════════════════════════════════════

with tab_done:

    # Read the saved plan (not the live Planning tab widgets)
    saved_plan = st.session_state.planner_data.get(camp_name, _empty_plan())

    if not saved_plan.get("title"):
        st.warning("No plan saved yet. Go to the **Planning** tab, fill in a title, and click **Save Plan**.")
        st.stop()

    st.caption(
        "Fill in what actually happened. Fields are pre-filled from your plan — "
        "edit them to reflect reality, then save."
    )

    # ── Reference: view the saved plan ───────────────────────────────────────
    with st.expander("📋 View Your Plan", expanded=False):
        st.markdown(f"**{saved_plan.get('title', '')}** — _{saved_plan.get('planned_date', '')}_")
        if saved_plan.get("premise"):
            st.markdown(f"*{saved_plan['premise']}*")
        for lbl, k in [("Prep Notes", "key_events"), ("Attendance", "attendance"),
                       ("Planned Milestone", "xp_awarded"), ("Planned Rewards", "rewards"),
                       ("Planned Cliffhanger", "cliffhanger_setup"),
                       ("Story Threads to Set Up", "next_hooks")]:
            if saved_plan.get(k):
                st.markdown(f"**{lbl}:** {saved_plan[k]}")

    st.divider()

    # Pre-populate Key Events from the plan on first open.
    # The widget key persists the DM's edits; cleared when session is saved.
    _ke_sskey = f"done_key_events_{camp_name}"
    if _ke_sskey not in st.session_state:
        st.session_state[_ke_sskey] = saved_plan.get("key_events", "")

    try:
        _date_default = datetime.date.fromisoformat(
            saved_plan.get("planned_date", datetime.date.today().isoformat())
        )
    except ValueError:
        _date_default = datetime.date.today()

    # ── Identical field order to Sessions "Add New Session" ───────────────────

    ac1, ac2 = st.columns([1, 3])
    actual_date  = ac1.date_input("Date", value=_date_default, key=f"done_date_{camp_name}")
    actual_title = ac2.text_input(
        "Session title", value=saved_plan.get("title", ""), key=f"done_title_{camp_name}"
    )

    st.text_area(
        "Summary",
        height=120,
        placeholder="What happened this session? How did it differ from the plan?",
        key=f"done_summary_{camp_name}",
    )

    # Key Events pre-filled from the plan's prep notes (fully editable)
    st.text_area(
        "Key Events & NPCs",
        height=200,
        placeholder="Notable moments, NPCs encountered, decisions made…",
        key=_ke_sskey,
        help="Pre-filled from your planning prep notes. Edit to reflect what actually happened.",
    )

    fa1, fa2, fa3 = st.columns(3)
    fa1.text_input(
        "Attendance",
        placeholder="Aria, Thrak, Zephyr…",
        key=f"done_att_{camp_name}",
        help="Comma-separated character or player names.",
    )
    fa2.text_input(
        "XP / Milestone",
        placeholder="e.g. 350 XP or Lvl 7",
        key=f"done_xp_{camp_name}",
    )
    fa3.text_input(
        "Loot & Rewards",
        placeholder="e.g. Sword of Truth, 200 gp",
        key=f"done_loot_{camp_name}",
    )

    st.text_area(
        "Session Cliffhanger",
        height=70,
        placeholder="Where did things end? What's the last image the players saw?",
        key=f"done_cliff_{camp_name}",
    )
    st.text_area(
        "Next Session Hooks",
        height=70,
        placeholder="Unresolved threads, questions raised, what's coming next…",
        key=f"done_next_{camp_name}",
    )

    st.divider()

    # ── Save to Session Notes ─────────────────────────────────────────────────

    done_key = f"plan_done_pending_{camp_name}"
    if done_key not in st.session_state:
        st.session_state[done_key] = False

    if not st.session_state[done_key]:
        if st.button("✅ Session Done — Save to Session Notes", type="primary", width='stretch'):
            st.session_state[done_key] = True
            st.rerun()
    else:
        title_preview = (
            st.session_state.get(f"done_title_{camp_name}", "").strip()
            or saved_plan.get("title", "this session")
        )
        st.warning(f"Add **{title_preview}** to Session Notes and clear the plan?")
        col_yes, _, col_no = st.columns([1, 7, 1])

        if col_yes.button("Confirm", type="primary", key=f"done_confirm_{camp_name}"):
            live_date  = st.session_state.get(f"done_date_{camp_name}", _date_default)
            live_title = st.session_state.get(f"done_title_{camp_name}", "").strip()

            new_entry = {
                "date":        live_date.isoformat() if hasattr(live_date, "isoformat") else str(live_date),
                "title":       live_title or saved_plan.get("title", "Session"),
                # Summary falls back to the session premise if left blank
                "summary":     st.session_state.get(f"done_summary_{camp_name}", "").strip()
                               or saved_plan.get("premise", ""),
                "key_events":  st.session_state.get(_ke_sskey,                   "").strip(),
                "attendance":  st.session_state.get(f"done_att_{camp_name}",     "").strip(),
                "xp_awarded":  st.session_state.get(f"done_xp_{camp_name}",      "").strip(),
                "loot":        st.session_state.get(f"done_loot_{camp_name}",    "").strip(),
                "cliffhanger": st.session_state.get(f"done_cliff_{camp_name}",   "").strip(),
                "next_hooks":  st.session_state.get(f"done_next_{camp_name}",    "").strip(),
            }

            sessions_raw = load_json(SESSIONS_PATH, {})
            if isinstance(sessions_raw, list):
                sessions_raw = {}
            sessions_raw.setdefault(camp_name, []).append(new_entry)
            save_json(SESSIONS_PATH, sessions_raw)

            # Invalidate sessions cache so Sessions page picks up the new entry
            st.session_state.pop("sessions", None)

            # Clear all done-tab keys so next session starts fresh
            for _k in (f"done_date_{camp_name}", f"done_title_{camp_name}",
                       f"done_summary_{camp_name}", _ke_sskey,
                       f"done_att_{camp_name}", f"done_xp_{camp_name}",
                       f"done_loot_{camp_name}", f"done_cliff_{camp_name}",
                       f"done_next_{camp_name}"):
                st.session_state.pop(_k, None)

            # Clear the plan ready for the next session
            st.session_state.planner_data[camp_name] = _empty_plan()
            save_planner()
            st.session_state[done_key] = False

            st.success(
                f"✅ **{new_entry['title']}** saved to Session Notes. "
                "Plan cleared — ready for next session."
            )
            st.rerun()

        if col_no.button("Cancel", key=f"done_cancel_{camp_name}"):
            st.session_state[done_key] = False
            st.rerun()

