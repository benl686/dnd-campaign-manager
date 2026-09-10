from utils import sidebar_exit_button
import streamlit as st

st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem;">
  <h1 style="font-size:3rem; margin-bottom:0.25rem;">⚔️ D&D Campaign Manager</h1>
  <p style="font-size:1.2rem; color:#aaa; margin-top:0;">
    Your all-in-one toolkit for running and playing 5th Edition D&D
  </p>
</div>
""", unsafe_allow_html=True)

st.divider()

col_dm, col_ref, col_tools = st.columns(3, gap="large")

with col_dm:
    st.markdown("### 🗺️ DM Tools")
    st.markdown("Everything you need to run your campaign, session by session.")
    st.markdown("""
| Page | What it does |
|------|-------------|
| **Campaigns** | Create and manage your campaigns — the root of everything else |
| **Characters** | Track PCs: HP, AC, ability scores, saves, skills |
| **Combat Tracker** | Initiative order, HP, conditions, round counter |
| **Encounter Builder** | Build encounters and calculate difficulty/XP |
| **Sessions** | Log session notes, summaries, and key events |
| **Session Planner** | Plan the next session; one click saves it to Session Notes when done |
| **NPCs** | Important and minor NPCs, relationships |
| **Factions** | Factions, alliances, and conflicts |
| **Faiths** | Deities, doctrines, and religious tensions |
| **Quests** | Active and completed quest tracking |
| **Worldbuilding** | Locations, lore, and setting notes |
| **Homebrew Rules** | House rules organised by category |
| **Dice Roller** | Quick rolls, custom expressions, advantage/disadvantage |
""")

with col_ref:
    st.markdown("### 📚 Reference")
    st.markdown("Searchable SRD and sourcebook content, filterable by edition.")
    st.markdown("""
| Page | What it does |
|------|-------------|
| **Monsters** | 3,500+ creatures with full stat blocks; add homebrew |
| **Spells** | Filter by level, school, and class |
| **Items** | Weapons, armor, magic items, equipment, and tattoos |
| **Backgrounds** | SRD + Xanathar's, Tasha's, and more |
| **Classes** | Class descriptions and features |
| **Races** | SRD races + popular PHB/sourcebook races; add homebrew |
| **Feats** | SRD + expanded sourcebook feats |
| **Conditions** | All 15 conditions, exhaustion table, cover rules |
""")

with col_tools:
    st.markdown("### 🛠️ Tools")
    st.markdown("Standalone generators and trackers for the table.")
    st.markdown("""
| Page | What it does |
|------|-------------|
| **Name Generator** | Random NPC and place names |
| **Treasure Generator** | Individual and hoard loot rolls |
| **Travel Tracker** | Overland travel, pace, and navigation |
| **Weather Tracker** | Random weather by climate and season |
| **Party Inventory** | Shared party loot and item tracking |
| **Magic Item Journal** | Log attunement and identified items |
| **Rumor Board** | Track rumours and player leads |
""")

st.divider()

tip_col, stat_col = st.columns([3, 1])
with tip_col:
    st.info(
        "**Getting started:** Head to **Campaigns** first and create a campaign — "
        "NPCs, Factions, Faiths, Quests, Worldbuilding, Sessions, and Homebrew Rules "
        "all live under a campaign. Characters, Combat, and the Reference pages are standalone."
    )
with stat_col:
    st.markdown("**Edition filter**")
    st.markdown(
        "All Reference pages have an edition toggle in the sidebar — "
        "switch between **2014** and **2024** rules, or show both."
    )

st.divider()
st.markdown("### How Things Work")

tut1, tut2, tut3 = st.columns(3, gap="large")

with tut1:
    st.markdown("**🗑️ Deleting campaigns**")
    st.markdown(
        "Deleting a campaign shows a checklist of all its data (NPCs, Quests, Factions, etc.). "
        "Checked items are permanently erased. **Unchecked items are kept** in a hidden "
        "**Others** archive, accessible at the bottom of each page. Nothing is lost unless you check it."
    )

with tut2:
    st.markdown("**📋 Copy & Paste**")
    st.markdown(
        "On NPCs, Factions, Faiths, Quests, and Sessions, every record has a **Copy** button. "
        "This puts it on the clipboard. A **Paste Here** bar then appears at the top of every "
        "campaign section — click it to drop the record in. Clipboard is page-specific: "
        "an NPC can't be pasted into Factions."
    )

with tut3:
    st.markdown("**✏️ Editing records**")
    st.markdown(
        "All records support **in-place editing** — you never need to delete and re-create. "
        "Look for **✏ Edit** or click **Save** buttons to commit changes. "
        "An **⚠ Unsaved changes** indicator appears on Sessions, Factions, and Faiths "
        "when you've edited a field without saving. "
        "Combat's **↻ Sync Sheet** button refreshes a character's AC and Max HP from their sheet."
    )

tut4, tut5, tut6 = st.columns(3, gap="large")

with tut4:
    st.markdown("**⚔️ Combat Tracker**")
    st.markdown(
        "Add combatants from your Characters page (imports HP, AC, spell slots, and inventory) "
        "or enter manually for monsters. HP bars flash red when damage is applied. "
        "Use **↩ Undo** to reverse the last turn. "
        "Reset Combat requires a confirm click to prevent accidents."
    )

with tut5:
    st.markdown("**🎲 Two-step deletes**")
    st.markdown(
        "Every delete in the app requires two clicks — **Delete** then **Confirm?** — "
        "so accidental taps don't destroy data. "
        "Major resets (campaign delete, encounter clear) add a third step with a "
        "checklist or warning banner."
    )

with tut6:
    st.markdown("**🔍 Search everywhere**")
    st.markdown(
        "Sessions, NPCs, Homebrew Rules, Calendar events, and Rumor Board all have "
        "search fields to filter by name or content. "
        "The Rumor Board also filters by session tag (e.g. `S3`). "
        "Encounter Builder and Treasure Generator search activates at 3 characters, "
        "or narrow the CR slider to browse without typing."
    )

