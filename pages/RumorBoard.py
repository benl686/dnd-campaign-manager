import random
import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, load_campaigns, no_campaigns_notice
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

RUMOR_PATH     = Path("json/rumor_board.json")
SESSIONS_PATH  = Path("json/sessions.json")

STATUSES = ["Unverified", "Investigating", "Confirmed", "False"]

STATUS_COLOR = {
    "Unverified":   "🟡",
    "Investigating":"🔵",
    "Confirmed":    "🟢",
    "False":        "🔴",
}


# ── Tavern rumor generator table ──────────────────────────────────────────────

TAVERN_RUMORS = [
    "A merchant caravan went missing on the old south road — third one this month.",
    "Someone's been buying up all the wolfsbane in town. No one knows why.",
    "The blacksmith's apprentice hasn't been seen in two days. The blacksmith won't talk about it.",
    "A fisherman swears he pulled up a human hand in his net. Wearing a noble's ring.",
    "The old keep outside of town has had lights in the windows every night this week.",
    "A traveller claims the road through the forest is cursed — his horse went mad before they reached the other side.",
    "The lord's tax collector hasn't returned from his rounds. The lord seems unbothered.",
    "Strange music can be heard from the cemetery after midnight. No one can agree what song.",
    "A beggar woman outside of town claims to see the future — and she's been right twice already.",
    "There's a new player at the card tables who hasn't lost a single hand in six nights.",
    "A farmer found his entire flock dead, arranged in a circle, none of them wounded.",
    "The temple of the sun god has closed its doors and won't say why.",
    "Someone is hiring adventurers for a job they won't describe until you sign a contract.",
    "A child claims to have found a door in the hill behind the mill that wasn't there last week.",
    "The local thieves' guild has gone quiet — usually means something big is being planned.",
    "A map was found on a dead body — it shows a vault beneath this very town.",
    "Three different people dreamed about a tower that doesn't exist — on the same night.",
    "A halfling traveller is paying premium prices for information about the old empire's ruins.",
    "There's a bounty on a warlock operating out of the docks — put up by a rival warlock.",
    "The river upstream ran red for a day last week. The wizards at the college are 'not concerned'.",
    "The travelling circus that passed through last month left something behind — something that breathes.",
    "A local shepherd's daughter claims she can speak to ravens, and they've been saying terrible things.",
    "Someone found an old contract at the bottom of the river, signed in blood, and now they won't say who they made it with.",
    "The new magistrate keeps asking about the old mine — the one sealed after the accident thirty years ago.",
    "Three gravediggers have quit this month. They say the graves are filling themselves.",
    "The miller's wife has been wearing long sleeves even in this heat. She always rolled them up in summer before.",
    "A royal inspector is supposedly coming next week. The innkeeper has been bribing someone to delay the paperwork.",
    "The eastern road is safe enough — if you travel in daylight and don't stop at the ruins. People who stop at the ruins don't finish the journey.",
    "A sage in the capital will pay 500 gold for a living specimen of something that used to be extinct. The reward poster shows only a rough sketch.",
    "The garrison hasn't received their pay in two months. The officers are pretending everything's fine, but the soldiers aren't.",
    "Old Petra says the town well connects to the sea somehow. She's been saying it for years, but now it's started smelling of salt.",
    "A bard played a song no one had heard before — and six people in the common room started weeping before he could finish the first verse. He left before anyone could ask him about it.",
    "Someone is leaving offerings outside the old chapel — but it's been deconsecrated for a decade and no priest has served it since.",
    "The lord's hound can find anyone in the county. He's lent it to someone, but no one knows who.",
    "A merchant arrived with crates addressed to the alchemist, sealed with an unrecognised stamp. The alchemist hasn't opened his shutters since.",
    "The keep's dungeons have been quietly expanded. At night.",
    "A water-seller on the corner gives accurate information for the right price. She knows things she shouldn't.",
    "A wizard's tower on the coast has been dark for a month. It normally sends a signal light. The fishermen are getting nervous.",
    "Someone is buying children's drawings — blank, unused ones — for a copper each, in bulk, no questions.",
    "The barber doubles as a surgeon and an informant. Half the town's secrets pass through that chair.",
    "A knight errant has been asking about the old battleground east of here. She looks like she's searching for something specific.",
    "The dwarven engineers surveying the quarry packed up and left overnight, leaving all their equipment behind.",
    "A horse arrived at the stable three nights ago, rider missing, saddle intact, with a sealed letter addressed to the mayor — who claims it was empty.",
    "The herbalist who retired to the hills has been turning everyone away for a month. She used to welcome visitors.",
    "No birds have nested on the east side of town this year. Animals tend to know.",
    "A bounty hunter arrived this morning looking for someone matching a traveller who came through last week.",
    "The local baron's second son has been spending a lot of time at the docks — strange, given that the baron hates the sea.",
    "A cartographer is offering good money for anyone who can verify whether the old lighthouse still stands. She's already sent three scouts. None came back.",
    "A silver mine opened two valleys over — but the workers are being paid in unworked silver chips, not coin. Someone doesn't want this tracked.",
    "The stars have been slightly wrong, according to the college's astronomer. Not dramatically wrong. Just slightly. She's the only one paying attention.",
    "The halfling family that ran the bakery left in a hurry two weeks ago, leaving loaves in the oven. Nobody's seen them since.",
    "Word is the local crime lord has gone legitimate — bought a shipping business. Everyone who worked for him before is terrified.",
    "A pilgrim road unused for two generations has fresh footprints on it. Going one direction only.",
    "The city watch has been patrolling in pairs for the first time in years. The captain won't say why.",
    "There's a man at the end of the bar who has been here every night for a month — orders the same thing, says nothing, tips generously. Nobody knows his name.",
    "An old soldier swears the bridge on the south road is haunted by the men who built it. Worked to death by the old count. Still there.",
    "A merchant sold a painting at auction — unrecognised subject, astronomical price, buyer in a mask. Three days later the merchant left town.",
    "Something killed the trapper's dogs, but didn't touch the cabin, the traps, or the food stores. Just the dogs.",
    "A beekeeper claims his bees are spelling words in their comb. He's been trying to read it, but they keep changing the message.",
    "The latest patrol sent to check the watchtower came back with one fewer member than left — and they can't agree on how many went out.",
    "Two city watchmen were seen carrying something large and wrapped in sailcloth out of the guildhall at three in the morning. Neither of them are on night duty.",
    "A tinker left a music box with the innkeeper as payment last week. It plays a different tune every day. Last night it played a funeral march.",
    "The judge overseeing the land dispute went missing. The case was settled the next morning, very quickly, in favour of the larger landowner.",
    "Someone has been replacing the candles in the temple with black ones overnight. The priests keep removing them. They're always back by dawn.",
    "A well-known fence was found dead in his shop with no wounds and a look of absolute terror on his face. His inventory was untouched.",
    "Three families in the merchant quarter say their children have been sleepwalking to the same spot — a blank section of wall at the end of the lane.",
    "The new toll road reduced travel time between the two cities by half. Nobody's asking who actually built it, or how, or in how little time.",
    "A census taker going door to door turned up at three houses that don't have anyone living in them. The civic rolls say they do.",
    "Someone offered the ratcatcher triple his usual rate to clear the old granary. He turned down two other jobs to take it. He won't say why it needs to be done so urgently.",
    "A messenger arrived carrying only a single sealed coin — no letter, no name. The innkeeper pocketed it and hasn't been right since.",
    "The night soil collectors haven't come in four nights. The guild foreman says the crew simply didn't show up, and no one knows where they went.",
    "A travelling artist spent three days sketching the ruins outside town and left in a tremendous hurry, abandoning everything including a canvas still wet with paint.",
    "The old chandler's shop changed hands quietly last month. New owner keeps the shutters closed. The stock in the window hasn't moved once.",
    "A man came in last night, bought one drink, left a sealed letter on the table, and walked out. The letter is addressed to someone in this town. No one knows who to give it to.",
    "Three different merchants claim they were robbed on the same road on the same night. None of them were travelling together. None of them saw anyone.",
    "A woman arrived at the temple and spent six hours in confession. Left looking like a different person. The priest hasn't spoken to anyone since.",
    "The harbour master has been closing the portcullis one hour earlier than usual for two weeks. He hasn't given any reason and hasn't answered questions about it.",
]


# ── Session state ─────────────────────────────────────────────────────────────

campaigns = load_campaigns()
if "rumor_board" not in st.session_state:
    # Schema: {campaign_name: [{text, source, status, session}]}
    st.session_state.rumor_board = load_json(RUMOR_PATH, {})
if "sessions" not in st.session_state:
    st.session_state.sessions = load_json(SESSIONS_PATH, {})


def save_rumors():
    """Persist rumor board to disk."""
    save_json(RUMOR_PATH, st.session_state.rumor_board)


def _session_labels(camp_name):
    """Return session labels for a campaign, newest first.

    Each label is '{date} — {title}' — matches the Sessions page display format
    and is used as the stored session identifier in rumors.
    Returns an empty list if no sessions exist yet for this campaign.
    """
    camp_sessions = st.session_state.get("sessions", {}).get(camp_name, [])
    return [
        f"{s.get('date', '')} — {s.get('title', 'Untitled')}"
        for s in sorted(camp_sessions, key=lambda s: s.get("date", ""), reverse=True)
        if s.get("title")
    ]


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Rumor Board")
st.caption(
    "Track rumors and leads your party has heard. "
    "Update their status as the campaign progresses: Unverified → Investigating → Confirmed or False."
)

tab_board, tab_gen = st.tabs(["Rumor Board", "Tavern Rumors"])

with tab_board:
    if not campaigns:
        no_campaigns_notice()
    else:
        for camp in campaigns:
            camp_name = camp["name"]
            header    = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name

            with st.expander(header):
                rumors = st.session_state.rumor_board.get(camp_name, [])

                # ── Summary counts ────────────────────────────────────────────────
                if rumors:
                    counts = {s: sum(1 for r in rumors if r.get("status") == s) for s in STATUSES}
                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.metric(f"{STATUS_COLOR['Unverified']} Unverified",   counts["Unverified"])
                    sc2.metric(f"{STATUS_COLOR['Investigating']} Investigating", counts["Investigating"])
                    sc3.metric(f"{STATUS_COLOR['Confirmed']} Confirmed",     counts["Confirmed"])
                    sc4.metric(f"{STATUS_COLOR['False']} False",             counts["False"])

                # ── Filters ───────────────────────────────────────────────────────
                sess_labels = _session_labels(camp_name)

                ff1, ff2 = st.columns([2, 1])
                status_filter = ff1.radio(
                    "Show",
                    ["All"] + STATUSES,
                    horizontal=True,
                    key=f"rb_filter_{camp_name}",
                )
                # Populate session filter from session notes when available
                if sess_labels:
                    session_filter = ff2.selectbox(
                        "Filter by session",
                        ["All"] + sess_labels,
                        key=f"rb_sess_filter_{camp_name}",
                    )
                else:
                    session_filter = ff2.text_input(
                        "Filter by session",
                        placeholder="e.g. S3",
                        key=f"rb_sess_filter_{camp_name}",
                    )

                # ── Add rumor form ────────────────────────────────────────────────
                st.markdown("#### Add Rumor / Lead")
                with st.form(f"add_rumor_{camp_name}", clear_on_submit=True):
                    rf1, rf2 = st.columns([3, 1])
                    source  = rf1.text_input("Source", placeholder="e.g. Overheard at the Rusty Anchor")
                    # Session picker: dropdown from session notes, or free text if none exist
                    if sess_labels:
                        sess_sel_add = rf2.selectbox(
                            "Session",
                            ["(no session)"] + sess_labels,
                            key=f"rb_add_sess_{camp_name}",
                        )
                        session = "" if sess_sel_add == "(no session)" else sess_sel_add
                    else:
                        session = rf2.text_input("Session / date", placeholder="e.g. S3")
                    text    = st.text_area(
                        "Rumor text",
                        placeholder="What did the party hear? Be specific — vague rumors are easy to forget.",
                        height=90,
                    )
                    if st.form_submit_button("Add Rumor"):
                        if text.strip():
                            new_rumor = {
                                "text":    text.strip(),
                                "source":  source.strip(),
                                "session": session.strip(),
                                "status":  "Unverified",
                            }
                            if camp_name not in st.session_state.rumor_board:
                                st.session_state.rumor_board[camp_name] = []
                            st.session_state.rumor_board[camp_name].append(new_rumor)
                            save_rumors()
                            st.success("Rumor added.")
                        else:
                            st.error("Rumor text is required.")

                # ── Rumor list ────────────────────────────────────────────────────
                st.markdown("---")
                rumors = st.session_state.rumor_board.get(camp_name, [])

                # Apply status + session filters.
                # Exact match when using the session dropdown (labels are full date — title strings).
                # Substring match when falling back to free-text input (backward compat for old entries).
                def _sess_match(r):
                    stored = r.get("session", "")
                    if not session_filter or session_filter == "All":
                        return True
                    if sess_labels:
                        return stored == session_filter   # dropdown: exact match
                    return session_filter.strip().lower() in stored.lower()  # text: substring

                visible = [
                    (i, r) for i, r in enumerate(rumors)
                    if (status_filter == "All" or r.get("status") == status_filter)
                    and _sess_match(r)
                ]

                if not visible:
                    st.caption("No rumors to show.")
                else:
                    for i, rumor in visible:
                        status = rumor.get("status", "Unverified")
                        badge  = STATUS_COLOR.get(status, "⚪")
                        source_tag = f" — *{rumor['source']}*" if rumor.get("source") else ""
                        session_tag = f" *(Session: {rumor['session']})*" if rumor.get("session") else ""
                        label = f"{badge} {status}{source_tag}{session_tag}"

                        with st.expander(label):
                            st.write(rumor["text"])

                            # ── Edit form ─────────────────────────────────────────────
                            with st.form(f"edit_rumor_{camp_name}_{i}"):
                                ef1, ef2 = st.columns([3, 1])
                                new_source = ef1.text_input("Source", value=rumor.get("source", ""))
                                # Session picker: prefer dropdown; fall back to text for legacy values
                                if sess_labels:
                                    stored_sess = rumor.get("session", "")
                                    sess_opts   = ["(no session)"] + sess_labels
                                    # Pre-select the stored value if it matches a known label
                                    sess_idx    = sess_opts.index(stored_sess) if stored_sess in sess_opts else 0
                                    sess_sel_edit = ef2.selectbox(
                                        "Session", sess_opts, index=sess_idx,
                                        key=f"rb_edit_sess_{camp_name}_{i}",
                                    )
                                    new_session = "" if sess_sel_edit == "(no session)" else sess_sel_edit
                                else:
                                    new_session = ef2.text_input("Session", value=rumor.get("session", ""))
                                new_text    = st.text_area("Rumor text", value=rumor.get("text", ""), height=80)
                                new_status  = st.selectbox(
                                    "Status",
                                    STATUSES,
                                    index=STATUSES.index(status),
                                    key=f"rb_status_{camp_name}_{i}",
                                )
                                if st.form_submit_button("Save Changes"):
                                    st.session_state.rumor_board[camp_name][i]["source"]  = new_source.strip()
                                    st.session_state.rumor_board[camp_name][i]["session"] = new_session.strip()
                                    st.session_state.rumor_board[camp_name][i]["text"]    = new_text.strip()
                                    st.session_state.rumor_board[camp_name][i]["status"]  = new_status
                                    save_rumors()
                                    st.success("Saved.")

                            # ── Delete ────────────────────────────────────────────
                            del_key = f"rb_del_{camp_name}_{i}"
                            if del_key not in st.session_state:
                                st.session_state[del_key] = False
                            if not st.session_state[del_key]:
                                if st.button("Delete rumor", key=f"rb_del_btn_{camp_name}_{i}"):
                                    st.session_state[del_key] = True
                                    st.rerun()
                            else:
                                st.warning("Delete this rumor?")
                                dc1, _, dc2 = st.columns([1, 7, 1])
                                if dc1.button("Confirm", key=f"rb_del_yes_{camp_name}_{i}"):
                                    st.session_state.rumor_board[camp_name].pop(i)
                                    save_rumors()
                                    st.session_state[del_key] = False
                                    st.rerun()
                                if dc2.button("Cancel", key=f"rb_del_no_{camp_name}_{i}"):
                                    st.session_state[del_key] = False
                                    st.rerun()


with tab_gen:
    st.subheader("Tavern Rumors")
    st.caption("Overheard at the bar. May be true, false, or somewhere in between.")
    n_rumors = st.number_input("Number of rumors to roll", min_value=1, max_value=5, value=1, key="gen_rumor_count")
    if st.button("Roll Rumor(s)", key="gen_rumor_roll"):
        # Sample without replacement so you don't hear the same thing twice
        picks = random.sample(TAVERN_RUMORS, min(int(n_rumors), len(TAVERN_RUMORS)))
        for rumor in picks:
            st.warning(f"**Rumor:** {rumor}")

    with st.expander("Show full table"):
        for idx, entry in enumerate(TAVERN_RUMORS, 1):
            st.markdown(f"**{idx:02d}.** {entry}")
