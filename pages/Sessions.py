import datetime
import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, confirm_delete, load_campaigns, no_campaigns_notice
from pathlib import Path


def _mark_dirty(key: str):
    """Set a dirty flag when an edit widget changes (used as on_change callback)."""
    st.session_state[key] = True


SESSIONS_PATH  = Path("json/sessions.json")

OTHERS_KEY    = "_Others_"
CLIPBOARD_KEY = "clipboard_session"


# ── Schema helpers ─────────────────────────────────────────────────────────────

def _full_schema(entry: dict) -> dict:
    """Return entry with all fields present, defaulting missing ones to ''.
    Keeps the page backward-compatible with old records that only had
    {date, title, summary, key_events}.
    """
    return {
        "date":        entry.get("date", datetime.date.today().isoformat()),
        "title":       entry.get("title", ""),
        "summary":     entry.get("summary", ""),
        "key_events":  entry.get("key_events", ""),
        "attendance":  entry.get("attendance", ""),
        "xp_awarded":  entry.get("xp_awarded", ""),
        "loot":        entry.get("loot", ""),
        "cliffhanger": entry.get("cliffhanger", ""),
        "next_hooks":  entry.get("next_hooks", ""),
    }


def _session_label(sess: dict) -> str:
    """Expander header: date + title, with attendance count if present."""
    base = f"{sess.get('date', '—')}  —  {sess.get('title', 'Untitled')}"
    if sess.get("attendance"):
        names = [n.strip() for n in sess["attendance"].split(",") if n.strip()]
        if names:
            base += f"  ·  {len(names)} present"
    return base


# ── Session state ──────────────────────────────────────────────────────────────

campaigns = load_campaigns()
if "sessions" not in st.session_state:
    st.session_state.sessions = load_json(SESSIONS_PATH, {})


# ── Page ───────────────────────────────────────────────────────────────────────

st.title("Session Notes")
st.caption("Session logs are grouped under each campaign, newest first.")

if not campaigns:
    no_campaigns_notice()
else:
    sessions_by_camp = st.session_state.sessions
    if isinstance(sessions_by_camp, list):
        sessions_by_camp = {}
    st.session_state.sessions = sessions_by_camp

    # Stale delete-confirm cleanup — drop any armed "Confirm?" flag whose session
    # index no longer exists for that campaign, so a shifted-in session can't
    # inherit a pre-armed delete confirmation from the session that used to sit
    # at that index. Prefix-strip (not underscore-split) so campaign names
    # containing underscores can't be mis-parsed.
    for camp in campaigns:
        cn      = camp["name"]
        cur_len = len(sessions_by_camp.get(cn, []))
        prefix  = f"sess_delete_{cn}_"
        for key in list(st.session_state.keys()):
            if key.startswith(prefix):
                suffix = key[len(prefix):]
                if suffix.isdigit() and int(suffix) >= cur_len:
                    del st.session_state[key]

    for camp in campaigns:
        camp_name = camp["name"]
        header    = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name
        camp_sessions = sessions_by_camp.get(camp_name, [])

        # Build expander title with session count
        exp_header = f"{header}  —  {len(camp_sessions)} session{'s' if len(camp_sessions) != 1 else ''}"
        with st.expander(exp_header):
            camp_sessions = sessions_by_camp.get(camp_name, [])

            # ── Clipboard paste bar ───────────────────────────────────────────
            clip = st.session_state.get(CLIPBOARD_KEY)
            if clip:
                pb1, pb2 = st.columns([4, 1])
                pb1.info(f"📋 Clipboard: **{clip['label']}**")
                if pb2.button("Paste Here", key=f"session_paste_{camp_name}"):
                    camp_sessions.append(dict(clip["record"]))
                    sessions_by_camp[camp_name] = camp_sessions
                    st.session_state.sessions = sessions_by_camp
                    save_json(SESSIONS_PATH, sessions_by_camp)
                    st.success(f"Pasted: {clip['label']}")
                    st.rerun()

            # ── Add New Session ───────────────────────────────────────────────
            st.subheader("Add New Session")
            with st.form(f"add_session_{camp_name}"):
                ac1, ac2 = st.columns([1, 3])
                new_date  = ac1.date_input("Date", value=datetime.date.today())
                new_title = ac2.text_input("Session title")

                new_summary    = st.text_area("Summary", height=120,
                                              placeholder="What happened this session?")
                new_key_events = st.text_area("Key Events & NPCs", height=90,
                                              placeholder="Notable moments, NPCs encountered, decisions made…")

                fa1, fa2, fa3 = st.columns(3)
                new_attendance = fa1.text_input("Attendance",
                                                placeholder="Aria, Thrak, Zephyr…",
                                                help="Comma-separated character or player names.")
                new_xp         = fa2.text_input("XP / Milestone",
                                                placeholder="e.g. 350 XP or Lvl 5",
                                                help="XP awarded or milestone reached this session.")
                new_loot       = fa3.text_input("Loot & Rewards",
                                                placeholder="e.g. Sword of Truth, 200 gp",
                                                help="Notable items or gold found.")

                new_cliffhanger = st.text_area("Session Cliffhanger",
                                               height=70,
                                               placeholder="Where did things end? What's the last image the players saw?")
                new_next_hooks  = st.text_area("Next Session Hooks",
                                               height=70,
                                               placeholder="Unresolved threads, questions raised, what's coming next…")

                if st.form_submit_button("Add Session"):
                    if new_title.strip():
                        camp_sessions.append({
                            "date":        new_date.isoformat(),
                            "title":       new_title.strip(),
                            "summary":     new_summary.strip(),
                            "key_events":  new_key_events.strip(),
                            "attendance":  new_attendance.strip(),
                            "xp_awarded":  new_xp.strip(),
                            "loot":        new_loot.strip(),
                            "cliffhanger": new_cliffhanger.strip(),
                            "next_hooks":  new_next_hooks.strip(),
                        })
                        sessions_by_camp[camp_name] = camp_sessions
                        st.session_state.sessions = sessions_by_camp
                        save_json(SESSIONS_PATH, sessions_by_camp)
                        st.success("Session added")
                        st.rerun()
                    else:
                        st.error("Title is required")

            # ── Session list ──────────────────────────────────────────────────
            if not camp_sessions:
                st.info("No sessions logged yet.")
            else:
                st.markdown("---")
                st.subheader(f"Sessions ({len(camp_sessions)})")
                st.caption("Newest first by date.")

                # Search filter
                sess_q = st.text_input(
                    "Search sessions",
                    placeholder="Filter by title, summary, events, attendance…",
                    key=f"sess_search_{camp_name}",
                )

                # Indexed sort preserves correct stored indices (never use list.index())
                indexed_sessions = sorted(
                    enumerate(camp_sessions),
                    key=lambda i_s: i_s[1].get("date", ""),
                    reverse=True,
                )

                if sess_q.strip():
                    sq = sess_q.strip().lower()
                    indexed_sessions = [
                        (orig, s) for orig, s in indexed_sessions
                        if sq in s.get("title", "").lower()
                        or sq in s.get("summary", "").lower()
                        or sq in s.get("key_events", "").lower()
                        or sq in s.get("attendance", "").lower()
                        or sq in s.get("cliffhanger", "").lower()
                        or sq in s.get("next_hooks", "").lower()
                    ]

                if not indexed_sessions:
                    st.caption("No sessions match that search.")

                for orig_idx, sess in indexed_sessions:
                    s = _full_schema(sess)
                    edit_flag = f"sess_edit_{camp_name}_{orig_idx}"
                    dirty_key = f"sess_dirty_{camp_name}_{orig_idx}"

                    with st.expander(_session_label(s)):

                        # ── View / Edit toggle ────────────────────────────────
                        if st.session_state.get(edit_flag):
                            if st.button("✕ Close Edit", key=f"sess_editclose_{camp_name}_{orig_idx}"):
                                st.session_state[edit_flag] = False
                                st.session_state[dirty_key] = False
                                st.rerun()
                        else:
                            # ── Read-only view ────────────────────────────────
                            # Quick stats row
                            vc = [x for x in [s["attendance"], s["xp_awarded"], s["loot"]] if x]
                            if vc:
                                vm1, vm2, vm3 = st.columns(3)
                                if s["attendance"]:
                                    vm1.metric("Attendance", s["attendance"])
                                if s["xp_awarded"]:
                                    vm2.metric("XP / Milestone", s["xp_awarded"])
                                if s["loot"]:
                                    vm3.metric("Loot", s["loot"])

                            if s["summary"]:
                                st.markdown(f"**Summary**  \n{s['summary']}")
                            if s["key_events"]:
                                st.markdown(f"**Key Events**  \n{s['key_events']}")
                            if s["cliffhanger"]:
                                st.info(f"**Cliffhanger:** {s['cliffhanger']}")
                            if s["next_hooks"]:
                                st.success(f"**Next Session Hooks:** {s['next_hooks']}")

                            row = st.columns([1, 1, 5])
                            if row[0].button("✏ Edit", key=f"sess_editbtn_{camp_name}_{orig_idx}"):
                                st.session_state[edit_flag] = True
                                st.rerun()
                            if row[1].button("Copy", key=f"sess_copy_{camp_name}_{orig_idx}",
                                             help="Copy to clipboard"):
                                st.session_state[CLIPBOARD_KEY] = {
                                    "record": sess,
                                    "label":  sess.get("title", "Session"),
                                }
                                st.rerun()
                            continue

                        # ── Edit form (only shown when edit_flag is True) ──────
                        ec1, ec2 = st.columns([1, 3])
                        edit_date = ec1.date_input(
                            "Date",
                            value=datetime.date.fromisoformat(s["date"]) if s["date"] else datetime.date.today(),
                            key=f"sess_edit_date_{camp_name}_{orig_idx}",
                            on_change=_mark_dirty, args=(dirty_key,),
                        )
                        edit_title = ec2.text_input(
                            "Title", value=s["title"],
                            key=f"sess_edit_title_{camp_name}_{orig_idx}",
                            on_change=_mark_dirty, args=(dirty_key,),
                        )

                        # Tabs within the edit form for organisation
                        et1, et2, et3 = st.tabs(["📝 Notes", "📊 Details", "🔮 Next Session"])

                        with et1:
                            edit_summary = st.text_area(
                                "Summary", value=s["summary"], height=150,
                                key=f"sess_edit_summary_{camp_name}_{orig_idx}",
                                on_change=_mark_dirty, args=(dirty_key,),
                            )
                            edit_events = st.text_area(
                                "Key Events & NPCs", value=s["key_events"], height=120,
                                key=f"sess_edit_events_{camp_name}_{orig_idx}",
                                on_change=_mark_dirty, args=(dirty_key,),
                            )

                        with et2:
                            ea1, ea2, ea3 = st.columns(3)
                            edit_attendance = ea1.text_input(
                                "Attendance", value=s["attendance"],
                                key=f"sess_edit_att_{camp_name}_{orig_idx}",
                                on_change=_mark_dirty, args=(dirty_key,),
                            )
                            edit_xp = ea2.text_input(
                                "XP / Milestone", value=s["xp_awarded"],
                                key=f"sess_edit_xp_{camp_name}_{orig_idx}",
                                on_change=_mark_dirty, args=(dirty_key,),
                            )
                            edit_loot = ea3.text_input(
                                "Loot & Rewards", value=s["loot"],
                                key=f"sess_edit_loot_{camp_name}_{orig_idx}",
                                on_change=_mark_dirty, args=(dirty_key,),
                            )

                        with et3:
                            edit_cliffhanger = st.text_area(
                                "Session Cliffhanger", value=s["cliffhanger"], height=80,
                                key=f"sess_edit_cliff_{camp_name}_{orig_idx}",
                                on_change=_mark_dirty, args=(dirty_key,),
                                placeholder="Where did things end?",
                            )
                            edit_next = st.text_area(
                                "Next Session Hooks", value=s["next_hooks"], height=80,
                                key=f"sess_edit_next_{camp_name}_{orig_idx}",
                                on_change=_mark_dirty, args=(dirty_key,),
                                placeholder="Unresolved threads, upcoming events…",
                            )

                        if st.session_state.get(dirty_key):
                            st.caption("⚠ Unsaved changes")

                        btn_cols = st.columns([7.5, 1])
                        if btn_cols[0].button("Save Session", key=f"sess_save_{camp_name}_{orig_idx}"):
                            camp_sessions[orig_idx] = {
                                "date":        edit_date.isoformat(),
                                "title":       edit_title.strip() or s["title"] or "Untitled",
                                "summary":     edit_summary.strip(),
                                "key_events":  edit_events.strip(),
                                "attendance":  edit_attendance.strip(),
                                "xp_awarded":  edit_xp.strip(),
                                "loot":        edit_loot.strip(),
                                "cliffhanger": edit_cliffhanger.strip(),
                                "next_hooks":  edit_next.strip(),
                            }
                            sessions_by_camp[camp_name] = camp_sessions
                            st.session_state.sessions = sessions_by_camp
                            save_json(SESSIONS_PATH, sessions_by_camp)
                            st.session_state[dirty_key] = False
                            st.session_state[edit_flag] = False
                            st.success("Saved")
                            st.rerun()

                        if confirm_delete(btn_cols[1], f"sess_delete_{camp_name}_{orig_idx}",
                                          f"sess_{camp_name}_{orig_idx}"):
                            camp_sessions.pop(orig_idx)
                            sessions_by_camp[camp_name] = camp_sessions
                            st.session_state.sessions = sessions_by_camp
                            save_json(SESSIONS_PATH, sessions_by_camp)
                            st.rerun()


# ── Others Archive ─────────────────────────────────────────────────────────────
# Access session state directly so this renders even when no campaigns exist.
_sessions_ss    = st.session_state.sessions if isinstance(st.session_state.sessions, dict) else {}
others_sessions = _sessions_ss.get(OTHERS_KEY, [])
if others_sessions:
    with st.expander(f"📦 Others Archive — {len(others_sessions)} orphaned session(s)"):
        st.caption("Sessions kept when their campaign was deleted. Copy them to move to a campaign.")
        for oi, sess in enumerate(others_sessions):
            label = f"{sess.get('date','—')}  —  {sess.get('title','Untitled')}"
            with st.expander(label):
                if sess.get("summary"):
                    st.markdown(sess["summary"][:200] + ("…" if len(sess.get("summary","")) > 200 else ""))

                oc1, oc2 = st.columns(2)
                if oc1.button("Copy", key=f"others_sess_copy_{oi}"):
                    st.session_state[CLIPBOARD_KEY] = {
                        "record": sess, "label": sess.get("title", "Session"),
                    }
                    st.rerun()
                if confirm_delete(oc2, f"others_sess_del_{oi}", f"others_sess_{oi}"):
                    others_sessions.pop(oi)
                    _sessions_ss[OTHERS_KEY] = others_sessions
                    st.session_state.sessions = _sessions_ss
                    save_json(SESSIONS_PATH, _sessions_ss)
                    st.rerun()

