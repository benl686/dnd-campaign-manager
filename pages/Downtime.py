import streamlit as st
from utils import load_json, load_json_cached, save_json, sidebar_exit_button, confirm_delete, load_campaigns, no_campaigns_notice
from pathlib import Path


# ── File paths ────────────────────────────────────────────────────────────────

CHARACTERS_PATH = Path("json/characters.json")
DOWNTIME_PATH   = Path("json/downtime.json")


# ── Standard downtime activities (PHB / XGE) ──────────────────────────────────

ACTIVITIES = [
    "Crafting",
    "Practicing a Profession",
    "Recuperating",
    "Researching",
    "Training (Language or Tool)",
    "Training (Ability / Skill)",
    "Carousing",
    "Crime",
    "Gambling",
    "Pit Fighting",
    "Religious Service",
    "Scribing a Spell Scroll",
    "Running a Business",
    "Selling Magic Items",
    "Buying Magic Items",
    "Other",
]

STATUSES = ["In Progress", "Completed", "Abandoned"]

# Short rule summaries shown when the player selects an activity (PHB/XGE)
ACTIVITY_DESCRIPTIONS = {
    "Crafting":                  "Craft nonmagical items using proficiency in the relevant tools. Spend 25 gp/week in materials; finish items worth up to 5 gp/day of work. Multiple characters can collaborate. Example: Crafting a sword (20 gp) takes 4 days and costs 10 gp in materials.",
    "Practicing a Profession":   "Work an honest job to maintain a modest lifestyle for free, or earn 1d6 × 5 gp per week with the right background. No roll required.",
    "Recuperating":              "Spend 3 downtime days to end one disease or poison affecting you, or reroll a failed death saving throw result once using Medicine DC 15.",
    "Researching":               "Spend at least 1 week and 50 gp digging up lore about a topic (spell, item, place). DM sets an Arcana/History/Religion check DC; failure may mean misleading info.",
    "Training (Language or Tool)": "Spend 250 days and 1 gp/day to gain proficiency in a language or tool. A tutor cuts the time to 250 days minus your INT modifier (min 10).",
    "Training (Ability / Skill)": "Train 10 workweeks (250 days) and spend 1 gp/day. Requires a trainer. Gain proficiency in one skill or tool at the end (XGE variant).",
    "Carousing":                 "Roll on the Carousing table after spending 50 gp × (1 for lower class, 10 for middle, 100 for upper). Results range from making a contact to starting a brawl or acquiring debt.",
    "Crime":                     "Plan and execute a heist or other illegal act. DM sets Dexterity (Stealth) or Charisma (Deception) checks; success yields gold, failure may mean jail time or infamy.",
    "Gambling":                  "Spend at least 10 gp per week. Make three checks (Wisdom + Insight, Charisma + Deception/Persuasion, chosen by DM). Count successes (0 = lose stake, 1 = lose half, 2 = break even, 3 = gain 1d6 × stake).",
    "Pit Fighting":              "Spend a week fighting for coin. Make three checks (STR Athletics, DEX Acrobatics, CON forced-march). Count successes: 0 = lose 2d6 gp, 1 = earn 2d6 gp, 2 = earn 6d6 gp, 3 = earn 10d6 gp.",
    "Religious Service":         "Work at a temple for 10 days. Gain a favor from the clergy — minor divine boons, information, or a free casting of a spell (up to 5th level) at DM's discretion.",
    "Scribing a Spell Scroll":   "Transcribe a known spell onto a scroll. Cost and time vary by level (e.g., 1st level: 1 week / 25 gp; 5th level: 12 weeks / 1,000 gp). Requires spell slots and spell list access.",
    "Running a Business":        "Roll d100 + downtime days. Low results mean paying costs or being robbed; moderate results break even; high rolls turn a profit (up to 9 × profit factor). Complications possible.",
    "Selling Magic Items":       "Find a buyer over 1d4 weeks (25 gp cost). Asking price ≈ half the listed gp value. Roll Charisma (Persuasion) to negotiate up to the full listed value; failure means no sale.",
    "Buying Magic Items":        "Spend 1d4 workweeks and 100 gp seeking the item. Roll on the Magic Item Purchase table. Higher rarity items are harder to find (DC increases, longer search time).",
    "Other":                     "Custom downtime activity agreed upon with the DM. Define the goal, actions required, and resolution mechanics.",
}


# ── Session state ─────────────────────────────────────────────────────────────

if "downtime_data" not in st.session_state:
    st.session_state.downtime_data = load_json(DOWNTIME_PATH, {})


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Downtime Tracker")

campaigns = load_campaigns()
if not campaigns:
    no_campaigns_notice()
    st.stop()

camp_names = [c["name"] for c in campaigns]
camp_name  = st.selectbox("Campaign", camp_names, key="dt_camp")

characters = load_json_cached(CHARACTERS_PATH, [])
char_names = [c["name"] for c in characters]

camp_dt = st.session_state.downtime_data.setdefault(camp_name, {})

# Stale delete-confirm cleanup — drop any armed "Confirm?" flag whose activity
# index no longer exists for that character, so a shifted-in activity can't
# inherit a pre-armed delete confirmation from the activity that used to sit
# at that index. Prefix-strip (not underscore-split) so campaign/character
# names containing underscores can't be mis-parsed.
for _dt_char, _dt_acts in camp_dt.items():
    _dt_prefix = f"dt_del_{camp_name}_{_dt_char}_"
    for _dt_key in list(st.session_state.keys()):
        if _dt_key.startswith(_dt_prefix):
            _dt_suffix = _dt_key[len(_dt_prefix):]
            if _dt_suffix.isdigit() and int(_dt_suffix) >= len(_dt_acts):
                del st.session_state[_dt_key]

st.markdown("---")


# ── Add downtime activity ─────────────────────────────────────────────────────

st.subheader("Log Downtime Activity")

# Show description for whichever activity is currently selected (updates on rerun)
_selected_act = st.session_state.get("dt_act", ACTIVITIES[0])
if _selected_act in ACTIVITY_DESCRIPTIONS:
    st.info(ACTIVITY_DESCRIPTIONS[_selected_act])

with st.form("add_downtime"):
    df1, df2 = st.columns(2)
    dt_char    = df1.selectbox("Character", char_names if char_names else ["(no characters)"], key="dt_char")
    dt_act     = df2.selectbox("Activity",  ACTIVITIES, key="dt_act")

    df3, df4, df5 = st.columns(3)
    dt_days   = df3.number_input("Days spent", min_value=1, value=1)
    dt_status = df4.selectbox("Status", STATUSES)
    dt_result = df5.text_input("Outcome / roll result (optional)")

    dt_notes = st.text_area("Notes", height=60)

    if st.form_submit_button("Add Activity"):
        if dt_char and dt_char != "(no characters)":
            char_dt = camp_dt.setdefault(dt_char, [])
            char_dt.append({
                "activity": dt_act,
                "days":     int(dt_days),
                "status":   dt_status,
                "result":   dt_result.strip(),
                "notes":    dt_notes.strip(),
            })
            st.session_state.downtime_data[camp_name] = camp_dt
            save_json(DOWNTIME_PATH, st.session_state.downtime_data)
            st.rerun()
        else:
            st.error("Add a character in the Characters page first.")

st.markdown("---")


# ── Per-character downtime view ───────────────────────────────────────────────

if not camp_dt:
    st.info("No downtime logged yet. Add an activity above.")
else:
    # Filter to a single character or show all
    view_char = st.selectbox(
        "View activities for",
        ["All characters"] + [ch for ch in char_names if ch in camp_dt],
        key="dt_view_char"
    )

    chars_to_show = (
        [ch for ch in char_names if ch in camp_dt]
        if view_char == "All characters"
        else [view_char]
    )

    for char in chars_to_show:
        activities = camp_dt.get(char, [])
        if not activities:
            continue

        total_days    = sum(a["days"] for a in activities)
        in_progress   = sum(1 for a in activities if a["status"] == "In Progress")
        completed     = sum(1 for a in activities if a["status"] == "Completed")

        st.subheader(char)
        sm1, sm2, sm3 = st.columns(3)
        sm1.metric("Total Days", total_days)
        sm2.metric("In Progress", in_progress)
        sm3.metric("Completed", completed)

        for ai, act in enumerate(activities):
            status_icon = {"In Progress": "🔄", "Completed": "✅", "Abandoned": "❌"}.get(act["status"], "")
            label = f"{status_icon} **{act['activity']}** — {act['days']} day{'s' if act['days'] != 1 else ''}"
            if act.get("result"):
                label += f"  |  {act['result']}"

            with st.expander(label):
                sc1, sc2, sc3 = st.columns([3, 1, 1])
                with sc1:
                    if act.get("notes"):
                        st.markdown(act["notes"])

                    # Inline status editor — saved immediately since it's a single-field action
                    new_status = st.selectbox(
                        "Status",
                        STATUSES,
                        index=STATUSES.index(act["status"]) if act["status"] in STATUSES else 0,
                        key=f"dt_status_{camp_name}_{char}_{ai}"
                    )
                    if new_status != act["status"]:
                        camp_dt[char][ai]["status"] = new_status
                        st.session_state.downtime_data[camp_name] = camp_dt
                        save_json(DOWNTIME_PATH, st.session_state.downtime_data)
                        st.rerun()

                # Edit toggle button
                edit_flag = f"dt_edit_{camp_name}_{char}_{ai}"
                if edit_flag not in st.session_state:
                    st.session_state[edit_flag] = False
                with sc2:
                    if st.button(
                        "✕ Cancel" if st.session_state[edit_flag] else "✏ Edit",
                        key=f"dt_edit_btn_{camp_name}_{char}_{ai}"
                    ):
                        st.session_state[edit_flag] = not st.session_state[edit_flag]
                        st.rerun()

                with sc3:
                    _, dt_btn_col = st.columns([8, 1])
                    if confirm_delete(dt_btn_col, f"dt_del_{camp_name}_{char}_{ai}", f"dt_{camp_name}_{char}_{ai}"):
                        camp_dt[char].pop(ai)
                        st.session_state.downtime_data[camp_name] = camp_dt
                        save_json(DOWNTIME_PATH, st.session_state.downtime_data)
                        st.rerun()

                # Inline edit form
                if st.session_state.get(edit_flag):
                    with st.form(f"dt_edit_form_{camp_name}_{char}_{ai}"):
                        ef1, ef2, ef3 = st.columns(3)
                        edit_days    = ef1.number_input("Days spent", min_value=1, value=act["days"])
                        edit_status  = ef2.selectbox("Status", STATUSES, index=STATUSES.index(act["status"]) if act["status"] in STATUSES else 0)
                        edit_result  = ef3.text_input("Outcome / roll result", value=act.get("result", ""))
                        edit_notes   = st.text_area("Notes", value=act.get("notes", ""), height=60)
                        if st.form_submit_button("Save Changes"):
                            camp_dt[char][ai].update({
                                "days":   int(edit_days),
                                "status": edit_status,
                                "result": edit_result.strip(),
                                "notes":  edit_notes.strip(),
                            })
                            st.session_state.downtime_data[camp_name] = camp_dt
                            save_json(DOWNTIME_PATH, st.session_state.downtime_data)
                            st.session_state[edit_flag] = False
                            st.rerun()

