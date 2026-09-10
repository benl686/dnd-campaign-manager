import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, confirm_delete, load_campaigns, no_campaigns_notice
from pathlib import Path


# ── File paths ────────────────────────────────────────────────────────────────

CALENDAR_PATH  = Path("json/calendar.json")


# ── Forgotten Realms calendar constants ──────────────────────────────────────

FR_MONTHS = [
    "Hammer", "Alturiak", "Ches", "Tarsakh", "Mirtul", "Kythorn",
    "Flamerule", "Eleasis", "Elient", "Marpenoth", "Uktar", "Nightal",
]
FR_DAYS_PER_MONTH  = 30   # FR months are always 30 days
FR_MONTHS_PER_YEAR = 12


# ── Session state ─────────────────────────────────────────────────────────────

if "calendar_data" not in st.session_state:
    st.session_state.calendar_data = load_json(CALENDAR_PATH, {})


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Campaign Calendar & Timeline")

campaigns = load_campaigns()
if not campaigns:
    no_campaigns_notice()
    st.stop()

camp_names = [c["name"] for c in campaigns]
camp_name  = st.selectbox("Campaign", camp_names, key="cal_camp")

# Initialise calendar data for this campaign with sensible defaults
cal = st.session_state.calendar_data.setdefault(camp_name, {
    "current_day":          1,
    "current_month":        1,
    "current_year":         1,
    "use_fr_calendar":      False,
    "custom_days_per_month":  30,
    "custom_months_per_year": 12,
    "events":               [],
})

# Stale delete-confirm cleanup — drop any armed "Confirm?" flag whose event
# index no longer exists for this campaign, so a shifted-in event can't
# inherit a pre-armed delete confirmation from the event that used to sit at
# that index. Prefix-strip (not underscore-split) so campaign names
# containing underscores can't be mis-parsed.
_cal_ev_len = len(cal.get("events", []))
_cal_prefix = f"cal_del_{camp_name}_"
for _key in list(st.session_state.keys()):
    if _key.startswith(_cal_prefix):
        _suffix = _key[len(_cal_prefix):]
        if _suffix.isdigit() and int(_suffix) >= _cal_ev_len:
            del st.session_state[_key]

tab_current, tab_events = st.tabs(["Current Date", "Timeline"])


# ══════════════════════════════════════════════════════════════════════════════
# CURRENT DATE TAB
# ══════════════════════════════════════════════════════════════════════════════

with tab_current:
    st.subheader("In-World Date")

    # ── Apply pending advance result ──────────────────────────────────────────
    # Streamlit raises StreamlitAPIException if you set a widget's session state
    # key after that widget has been instantiated in the same render pass.
    # The advance buttons run AFTER the date widgets, so we can't update the
    # widget keys there directly.  Instead, the advance handler stores its result
    # in a non-widget key (_cal_adv_<camp>), and we consume it HERE — at the top
    # of the tab, before any widget is instantiated — where setting widget keys
    # is still allowed.
    _adv_key = f"_cal_adv_{camp_name}"
    _pending = st.session_state.pop(_adv_key, None)
    if _pending:
        st.session_state["cal_day"]  = _pending["day"]
        st.session_state["cal_year"] = _pending["year"]
        if _pending["use_fr"]:
            st.session_state["cal_month_fr"] = _pending["month_name"]
        else:
            st.session_state["cal_month_num"] = _pending["month"]

    # ── Calendar type selector ────────────────────────────────────────────────

    use_fr = st.checkbox(
        "Use Forgotten Realms calendar (named months, 30-day months, 12 months)",
        value=cal.get("use_fr_calendar", False),
        key="cal_use_fr",
    )
    cal["use_fr_calendar"] = use_fr

    # ── Custom calendar configuration (non-FR only) ───────────────────────────
    # Lets the DM define any homebrew calendar structure (e.g. 28-day months,
    # 13 months per year, etc.).

    if use_fr:
        days_in_month  = FR_DAYS_PER_MONTH
        months_in_year = FR_MONTHS_PER_YEAR
    else:
        cs1, cs2 = st.columns(2)
        custom_dpm = cs1.number_input(
            "Days per month",
            min_value=1, max_value=999,
            value=int(cal.get("custom_days_per_month", 30)),
            step=1, key="cal_dpm",
            help="How many days are in each month of your world's calendar.",
        )
        custom_mpy = cs2.number_input(
            "Months per year",
            min_value=1, max_value=999,
            value=int(cal.get("custom_months_per_year", 12)),
            step=1, key="cal_mpy",
            help="How many months are in each year of your world's calendar.",
        )
        days_in_month  = int(custom_dpm)
        months_in_year = int(custom_mpy)
        # Write back immediately so advance logic uses live values
        cal["custom_days_per_month"]  = days_in_month
        cal["custom_months_per_year"] = months_in_year

    st.divider()

    # ── Date inputs ───────────────────────────────────────────────────────────

    if use_fr and int(cal.get("current_month", 1)) > FR_MONTHS_PER_YEAR:
        st.warning("FR calendar only has 12 months. Displaying Nightal (month 12).")

    dc1, dc2, dc3 = st.columns(3)
    day  = dc1.number_input(
        "Day",
        min_value=1, max_value=days_in_month,
        value=min(int(cal.get("current_day", 1)), days_in_month),
        key="cal_day",
    )
    year = dc3.number_input(
        "Year",
        min_value=1, max_value=9999,
        value=int(cal.get("current_year", 1)),
        key="cal_year",
    )

    if use_fr:
        stored_m   = min(int(cal.get("current_month", 1)) - 1, 11)
        month_name = dc2.selectbox("Month", FR_MONTHS, index=stored_m, key="cal_month_fr")
        month      = FR_MONTHS.index(month_name) + 1
    else:
        stored_m = min(int(cal.get("current_month", 1)), months_in_year)
        month = dc2.number_input(
            "Month",
            min_value=1, max_value=months_in_year,
            value=stored_m,
            key="cal_month_num",
        )

    # Display formatted date
    if use_fr:
        display_month = FR_MONTHS[min(int(month) - 1, 11)]
        date_str = f"Day {int(day)} of {display_month}, Year {int(year)} DR"
    else:
        date_str = f"Day {int(day)}, Month {int(month)}, Year {int(year)}"

    st.markdown(f"### {date_str}")

    # ── Advance time buttons ──────────────────────────────────────────────────
    # IMPORTANT: After advancing, we must update the widget session state keys
    # directly (st.session_state["cal_day"] etc.) before calling st.rerun().
    # Without this, Streamlit reuses the cached widget values from the previous
    # render and the else-branch below immediately overwrites the advance.

    st.markdown("**Advance time:**")
    adv_cols = st.columns(6)
    advance = 0
    if adv_cols[0].button("+ 1 Day"):
        advance = 1
    if adv_cols[1].button("+ 7 Days"):
        advance = 7
    if adv_cols[2].button(f"+ 1 Month ({days_in_month}d)"):
        advance = days_in_month
    if adv_cols[3].button("+ 1 Year"):
        advance = days_in_month * months_in_year

    custom_adv = adv_cols[4].number_input(
        "Custom days", min_value=0, value=0, step=1,
        key="cal_adv", label_visibility="collapsed",
    )
    if adv_cols[5].button("+ Custom Days"):
        advance = int(custom_adv)

    if advance:
        # Roll over days → months → years using this campaign's calendar structure
        total_days = int(day) + advance
        m = int(month)
        y = int(year)
        while total_days > days_in_month:
            total_days -= days_in_month
            m += 1
            if m > months_in_year:
                m = 1
                y += 1

        cal["current_day"]            = total_days
        cal["current_month"]          = m
        cal["current_year"]           = y
        cal["custom_days_per_month"]  = days_in_month
        cal["custom_months_per_year"] = months_in_year

        # Store new values for consumption at the TOP of the next render (before
        # any widgets are instantiated), where setting widget keys is legal.
        st.session_state[_adv_key] = {
            "day":        total_days,
            "month":      m,
            "year":       y,
            "use_fr":     use_fr,
            "month_name": FR_MONTHS[min(m - 1, 11)],
        }

        st.session_state.calendar_data[camp_name] = cal
        save_json(CALENDAR_PATH, st.session_state.calendar_data)
        st.rerun()
    else:
        # No advance — write the current widget values back to cal (manual edits)
        cal["current_day"]   = int(day)
        cal["current_month"] = int(month)
        cal["current_year"]  = int(year)

    # Manual Save button — only needed when editing day/month/year fields directly
    if st.button("Save Date"):
        cal["custom_days_per_month"]  = days_in_month
        cal["custom_months_per_year"] = months_in_year
        st.session_state.calendar_data[camp_name] = cal
        save_json(CALENDAR_PATH, st.session_state.calendar_data)
        st.success("Saved.")
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TIMELINE TAB
# ══════════════════════════════════════════════════════════════════════════════

with tab_events:
    st.subheader("Timeline Events")

    # Add event form
    with st.form("add_event"):
        ef1, ef2 = st.columns([2, 3])
        ev_day  = ef1.number_input("Day",  min_value=1, max_value=days_in_month,
                                   value=min(int(cal.get("current_day",  1)), days_in_month))
        ev_year = ef1.number_input("Year", min_value=1,
                                   value=int(cal.get("current_year", 1)))

        if use_fr:
            stored_em  = min(int(cal.get("current_month", 1)) - 1, 11)
            ev_month_s = ef1.selectbox("Month", FR_MONTHS, index=stored_em)
            ev_month   = FR_MONTHS.index(ev_month_s) + 1
        else:
            ev_month = ef1.number_input(
                "Month", min_value=1, max_value=months_in_year,
                value=min(int(cal.get("current_month", 1)), months_in_year),
            )

        ev_title = ef2.text_input("Event title")
        ev_desc  = ef2.text_area("Description (optional)", height=60)

        if st.form_submit_button("Add Event"):
            if ev_title.strip():
                cal.setdefault("events", []).append({
                    "day":   int(ev_day),
                    "month": int(ev_month),
                    "year":  int(ev_year),
                    "title": ev_title.strip(),
                    "desc":  ev_desc.strip(),
                })
                # Keep events in chronological order
                cal["events"].sort(key=lambda e: (e["year"], e["month"], e["day"]))
                st.session_state.calendar_data[camp_name] = cal
                save_json(CALENDAR_PATH, st.session_state.calendar_data)
                st.rerun()
            else:
                st.error("Title is required.")

    st.markdown("---")

    events = cal.get("events", [])
    if not events:
        st.info("No events yet. Add one above.")
    else:
        # Search / filter events
        ev_q = st.text_input(
            "Search events",
            placeholder="Filter by title or description…",
            key=f"cal_ev_search_{camp_name}",
        )

        # Preserve original indices for safe deletion (see CLAUDE.md sort-index rule)
        indexed_events = list(enumerate(events))
        if ev_q.strip():
            eq = ev_q.strip().lower()
            indexed_events = [
                (ei, ev) for ei, ev in indexed_events
                if eq in ev.get("title", "").lower() or eq in ev.get("desc", "").lower()
            ]
        if not indexed_events:
            st.caption("No events match that search.")

        for ei, ev in indexed_events:
            if use_fr:
                month_label = FR_MONTHS[min(int(ev["month"]) - 1, 11)]
                date_label  = f"Day {ev['day']} of {month_label}, {ev['year']} DR"
            else:
                date_label = f"Day {ev['day']}, Month {ev['month']}, Year {ev['year']}"

            with st.expander(f"**{ev['title']}** — {date_label}"):
                if ev.get("desc"):
                    st.markdown(ev["desc"])

                _, cal_btn_col = st.columns([8, 1])
                if confirm_delete(cal_btn_col, f"cal_del_{camp_name}_{ei}", f"cal_{camp_name}_{ei}"):
                    cal["events"].pop(ei)
                    st.session_state.calendar_data[camp_name] = cal
                    save_json(CALENDAR_PATH, st.session_state.calendar_data)
                    st.rerun()

