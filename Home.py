import streamlit as st
from utils import sidebar_exit_button

# set_page_config MUST be called once here and ONLY here.
# If any page file also calls it, Streamlit silently falls back to alphabetical
# file-based navigation and ignores the st.navigation() grouping entirely.
st.set_page_config(page_title="D&D Manager", layout="wide")

# st.navigation() defines the sidebar structure and controls which page script runs.
# Pages are grouped under display headers; the empty-string group has no header.
# The first page in the list is shown by default when the app first loads.
pg = st.navigation(
    {
        # Unlabelled group — the Home/landing page sits above the DM Tools section
        "": [
            st.Page("pages/Welcome.py", title="Home", icon="🏠"),
        ],
        # Campaign management tools — most require a campaign to exist first
        "DM Tools": [
            st.Page("pages/Campaigns.py",        title="Campaigns"),
            st.Page("pages/Characters.py",       title="Characters"),
            st.Page("pages/Combat.py",           title="Combat Tracker"),
            st.Page("pages/EncounterBuilder.py", title="Encounter Builder"),
            st.Page("pages/Calendar.py",         title="Calendar & Timeline"),
            st.Page("pages/Downtime.py",         title="Downtime Tracker"),
            st.Page("pages/Sessions.py",         title="Sessions"),
            st.Page("pages/SessionPlanner.py",   title="Session Planner"),
            st.Page("pages/NPCs.py",             title="NPCs"),
            st.Page("pages/Factions.py",         title="Factions"),
            st.Page("pages/Faiths.py",           title="Faiths"),
            st.Page("pages/RelationshipMap.py",  title="Relationship Map"),
            st.Page("pages/ResourceTracker.py",  title="Resource Tracker"),
            st.Page("pages/Quests.py",           title="Quests"),
            st.Page("pages/Worldbuilding.py",    title="Worldbuilding"),
            st.Page("pages/HomebrewRules.py",    title="Homebrew Rules"),
            st.Page("pages/Dice.py",             title="Dice Roller"),
        ],
        # Read-only SRD + sourcebook reference data — all standalone, no campaign required
        "Reference": [
            st.Page("pages/Monsters.py",      title="Monsters"),
            st.Page("pages/Spells.py",        title="Spells"),
            st.Page("pages/Items.py",         title="Items"),
            st.Page("pages/Backgrounds.py",   title="Backgrounds"),
            st.Page("pages/Classes.py",       title="Classes"),
            st.Page("pages/Races.py",         title="Races"),
            st.Page("pages/Feats.py",         title="Feats"),
            st.Page("pages/Conditions.py",    title="Conditions"),
        ],
        # Utility tools — generators, trackers, and party-wide tools
        "Tools": [
            st.Page("pages/NameGenerator.py",     title="Name Generator"),
            st.Page("pages/TreasureGenerator.py", title="Treasure Generator"),
            st.Page("pages/TravelTracker.py",     title="Travel Tracker"),
            st.Page("pages/WeatherTracker.py",    title="Weather Tracker"),
            st.Page("pages/PartyInventory.py",    title="Party Inventory"),
            st.Page("pages/MagicItemJournal.py",  title="Magic Item Journal"),
            st.Page("pages/RumorBoard.py",        title="Rumor Board"),
            st.Page("pages/ShopGenerator.py",     title="Shop Generator"),
        ],
    }
)

# Exit button lives here so it always renders regardless of st.stop() calls in pages.
# Individual pages also call sidebar_exit_button() but st.stop() can prevent that.
sidebar_exit_button()

# Run the currently selected page's script — this replaces the main content area
pg.run()
