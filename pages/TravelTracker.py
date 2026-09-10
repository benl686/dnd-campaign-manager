import random
import streamlit as st
from utils import load_json, load_json_cached, save_json, sidebar_exit_button, load_campaigns, no_campaigns_notice
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

TRAVEL_PATH        = Path("json/travel_tracker.json")
WORLDBUILDING_PATH = Path("json/worldbuilding.json")

# Terrain types and associated travel pace (miles per day at normal pace)
TERRAIN_PACE = {
    "Road / Plains":   24,
    "Forest":          18,
    "Hills":           18,
    "Mountains":       12,
    "Swamp":           12,
    "Desert":          18,
    "Coastal":         24,
    "Underdark":        9,
    "Arctic / Tundra": 12,
    "Sea / River":     24,
    "Urban":           24,
}

# Simplified random encounter seeds by terrain — single-line hooks for quick use
ENCOUNTER_HOOKS = {
    "Road / Plains":   ["Highwaymen blocking the road","A runaway wagon with a spooked horse","Soldiers at an unofficial checkpoint","Gnolls driving captured townsfolk","A dust cloud — an urgent rider","Cultists in a roadside field","Overturned caravan — no bodies, no attackers","A travelling merchant with stolen goods"],
    "Forest":          ["Bandits in an ambush between fallen trees","1d4 dire wolves stalking prey","A corrupted dryad lashing out","Goblins raiding a camp","A giant spider web across the trail","A treant, slowly awoken and angry","A will-o'-wisp drifting between trees","Hunters who mistake the party for quarry"],
    "Hills":           ["Orc raiders on patrol","A shepherd whose flock scattered overnight","A half-collapsed barrow with something inside","Wyvern circling overhead, deciding","Hill giants hurling boulders at each other","A wounded griffon on a ledge","Bandit scouts watching from the ridge","A caravan mired in mud on a hill track"],
    "Mountains":       ["Avalanche triggered by stone giants playing","A young griffon defending a pass","Dwarven prospectors under attack","A manticore circling overhead","A narrow bridge with a troll beneath","A monastery with monks who ask strange questions","Wyverns nesting directly above the only path","A shrine to a long-dead god, still active"],
    "Swamp":           ["A hag's hovel, smoke from the chimney","1d8 lizardfolk who view the party as trespassers","A will-o'-wisp leading toward quicksand","A hydra sleeping on the only crossing","Bullywugs conducting a ceremony","A yuan-ti scout tailing the party","A disease-carrying insect swarm","The ruin of a trading post, still stocked"],
    "Desert":          ["Bandits on camels, fast and aggressive","A dying caravan with one survivor","A brass-bound door in the sand — nothing around it","A djinn who wants a favour","A giant scorpion guarding a watering hole","Sand pirates with a buried cache","A mirage that turns out to be real","Nomads who know where the next oasis is"],
    "Coastal":         ["Pirates disguised as merchants","A beached whale drawing predators","Sahuagin raiding a fishing village","A sea hag's tide-pool lair","Merfolk willing to trade — for the right price","Smugglers with a hidden sea cave","A lighthouse whose light is not a warning","A shipwreck with something in the hold"],
    "Underdark":       ["A mind flayer and its thralls","Drow scouts who've already spotted the party","A roper mimicking stalactites","A deep gnome desperate to reach the surface","Myconid colony willing to talk, or spore","A cloaker flat against the wall","A beholder, paranoid and territorial","An aboleth's lair — the water is never safe"],
    "Arctic / Tundra": ["Frost giants migrating south","A polar bear defending cubs","Remorhazes beneath the ice shelf","Barbarian hunters who see the party as rivals","A trapped arctic expedition — only the gear remains","Yeti tracking the party through a blizzard","An ice cave with something frozen inside","Remorhaz nest on the only warm ground around"],
    "Sea / River":     ["River pirates blocking a narrow gorge","A ghost ship drifting with no crew","Sahuagin attacking from underwater","A maelstrom with something at its centre","A kelpie luring the crew overboard","Merfolk seeking passage through their territory","A water elemental disturbed by the passage","A riverboat merchant with plague aboard"],
    "Urban":           ["A pickpocket working the crowd","A street brawl spilling into the party","City guards looking for someone matching a party member's description","A runaway slave begging for help","A street preacher whose cult is not what it seems","A mage duel shutting down a major street","A noble's palanquin overturned by a mob","An assassination attempt on someone nearby"],
}


# ── Session state ─────────────────────────────────────────────────────────────

campaigns = load_campaigns()
if "travel_data" not in st.session_state:
    # Schema: {campaign_name: [{origin, destination, terrain, miles, days, pace, notes, encounter}]}
    st.session_state.travel_data = load_json(TRAVEL_PATH, {})


def save_travel():
    """Persist travel log to disk."""
    save_json(TRAVEL_PATH, st.session_state.travel_data)


# ── Worldbuilding location helpers ────────────────────────────────────────────

_CUSTOM_SENTINEL = "— Enter custom location —"


def _wb_locations(camp_name: str) -> list[str]:
    """Return sorted location names for the campaign from worldbuilding.json.

    Pulls cities, regions, nations, and planes — all the named places a party
    might travel to or from.  Returns an empty list when the campaign has no
    worldbuilding data yet.

    Uses load_json_cached (mtime-keyed) instead of load_json — this is called
    once per campaign in the page's campaign loop, and worldbuilding.json only
    changes when the Worldbuilding page saves, so re-reading it from disk on
    every campaign iteration of every rerun was pure waste.
    """
    wb = load_json_cached(WORLDBUILDING_PATH, {})
    camp_wb = wb.get(camp_name, {})
    names: list[str] = []
    for category in ("cities", "regions", "nations", "planes"):
        for entry in camp_wb.get(category, []):
            n = entry.get("name", "").strip()
            if n:
                names.append(n)
    return sorted(set(names))


def _location_widgets(col, label: str, base_key: str,
                      wb_locs: list[str], default: str = "") -> tuple:
    """Render a location selectbox + custom text_input pair inside a st.form column.

    Returns (selectbox_widget_value, custom_text_widget_value) so the caller can
    resolve the final value with _resolve_location().

    Args:
        col:      The column container to render into.
        label:    Human-readable label (e.g. "From").
        base_key: Unique key prefix (must be stable across reruns).
        wb_locs:  Sorted location names from Worldbuilding for the current campaign.
        default:  Pre-fill value for the custom text input (used in edit forms).
    """
    sel = col.selectbox(label, options=[_CUSTOM_SENTINEL] + wb_locs,
                        key=f"{base_key}_sel",
                        # Pre-select the saved value when editing an existing leg
                        index=wb_locs.index(default) + 1 if default in wb_locs else 0)
    custom = col.text_input(
        "Custom" if sel == _CUSTOM_SENTINEL else "Override (optional)",
        value=default if sel == _CUSTOM_SENTINEL else "",
        placeholder="Type a location not listed above",
        key=f"{base_key}_custom",
    )
    return sel, custom


def _resolve_location(sel: str, custom: str) -> str:
    """Return the effective location name from the selectbox / custom pair."""
    if sel != _CUSTOM_SENTINEL:
        return sel
    return custom.strip()


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Travel Tracker")
st.caption("Log journey legs per campaign. Track distance, terrain, days travelled, and random encounter rolls.")

if not campaigns:
    no_campaigns_notice()
else:
    for camp in campaigns:
        camp_name = camp["name"]
        header    = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name

        # Build worldbuilding location list for this campaign (used inside the form)
        _wb_locs = _wb_locations(camp_name)

        with st.expander(header):
            legs = st.session_state.travel_data.get(camp_name, [])

            # ── Cumulative totals ─────────────────────────────────────────────
            total_miles = sum(leg.get("miles", 0) for leg in legs)
            total_days  = sum(leg.get("days", 0) for leg in legs)
            if legs:
                tc1, tc2 = st.columns(2)
                tc1.metric("Total Distance", f"{total_miles:,} miles")
                tc2.metric("Total Travel Days", f"{total_days}")

            # ── Add leg form ──────────────────────────────────────────────────
            st.markdown("#### Log a New Journey Leg")
            with st.form(f"add_leg_{camp_name}", clear_on_submit=True):
                lf1, lf2 = st.columns(2)
                if _wb_locs:
                    # Selectbox populated from Worldbuilding; custom text input as fallback
                    orig_sel, orig_custom = _location_widgets(lf1, "From", f"add_orig_{camp_name}", _wb_locs)
                    dest_sel, dest_custom = _location_widgets(lf2, "To",   f"add_dest_{camp_name}", _wb_locs)
                else:
                    # No worldbuilding data yet — plain text inputs
                    orig_sel  = _CUSTOM_SENTINEL
                    dest_sel  = _CUSTOM_SENTINEL
                    orig_custom = lf1.text_input("From", placeholder="e.g. Waterdeep")
                    dest_custom = lf2.text_input("To",   placeholder="e.g. Neverwinter")

                lf3, lf4, lf5 = st.columns([2, 1, 1])
                terrain = lf3.selectbox("Terrain", list(TERRAIN_PACE.keys()))
                miles   = lf4.number_input("Distance (miles)", min_value=0, value=0, step=1)
                days    = lf5.number_input("Days travelled", min_value=0, value=0, step=1)

                pace_hint = TERRAIN_PACE[terrain]
                st.caption(
                    f"Normal pace on {terrain}: ~{pace_hint} miles/day. "
                    f"Slow pace (–⅓): {int(pace_hint * 0.67)} mi/day. "
                    f"Fast pace (+⅓): {int(pace_hint * 1.33)} mi/day."
                )

                notes = st.text_area("Notes (events, weather, encounters)", height=70)
                roll_enc = st.checkbox("Roll a random encounter for this leg")

                submitted = st.form_submit_button("Add Leg")
                if submitted:
                    origin      = _resolve_location(orig_sel, orig_custom)
                    destination = _resolve_location(dest_sel, dest_custom)
                    if origin or destination:
                        encounter = ""
                        if roll_enc:
                            pool = ENCOUNTER_HOOKS.get(terrain, [])
                            encounter = random.choice(pool) if pool else "No encounter table for this terrain."
                        new_leg = {
                            "origin":      origin,
                            "destination": destination,
                            "terrain":     terrain,
                            "miles":       int(miles),
                            "days":        int(days),
                            "notes":       notes.strip(),
                            "encounter":   encounter,
                        }
                        if camp_name not in st.session_state.travel_data:
                            st.session_state.travel_data[camp_name] = []
                        st.session_state.travel_data[camp_name].append(new_leg)
                        save_travel()
                        st.success(f"Logged: {origin or '?'} → {destination or '?'}")
                    else:
                        st.error("At least one of From / To is required.")

            # ── Leg list ──────────────────────────────────────────────────────
            st.markdown("---")
            legs = st.session_state.travel_data.get(camp_name, [])
            if not legs:
                st.caption("No journey legs logged yet.")
            else:
                for i, leg in enumerate(legs):
                    route = f"{leg.get('origin','?')} → {leg.get('destination','?')}"
                    summary = f"{route} | {leg.get('terrain','')} | {leg.get('miles',0)} mi / {leg.get('days',0)} days"
                    with st.expander(summary):
                        edit_flag = f"trav_edit_{camp_name}_{i}"
                        if edit_flag not in st.session_state:
                            st.session_state[edit_flag] = False

                        if not st.session_state.get(edit_flag):
                            # View mode
                            st.markdown(f"**Route:** {route}")
                            st.markdown(f"**Terrain:** {leg.get('terrain','')} | **Distance:** {leg.get('miles',0)} miles | **Days:** {leg.get('days',0)}")
                            if leg.get("notes"):
                                st.markdown(f"**Notes:** {leg['notes']}")
                            if leg.get("encounter"):
                                st.warning(f"**Encounter:** {leg['encounter']}")

                            btn_row = st.columns([1, 1, 5])
                            if btn_row[0].button("✏ Edit", key=f"trav_edit_btn_{camp_name}_{i}"):
                                st.session_state[edit_flag] = True
                                st.rerun()

                            # ── Delete ────────────────────────────────────────
                            del_key = f"trav_del_{camp_name}_{i}"
                            if del_key not in st.session_state:
                                st.session_state[del_key] = False
                            if not st.session_state[del_key]:
                                if btn_row[1].button("Delete", key=f"trav_del_btn_{camp_name}_{i}"):
                                    st.session_state[del_key] = True
                                    st.rerun()
                            else:
                                st.warning("Delete this leg?")
                                dc1, _, dc2 = st.columns([1, 7, 1])
                                if dc1.button("Confirm", key=f"trav_del_yes_{camp_name}_{i}"):
                                    st.session_state.travel_data[camp_name].pop(i)
                                    save_travel()
                                    st.session_state[del_key] = False
                                    st.rerun()
                                if dc2.button("Cancel", key=f"trav_del_no_{camp_name}_{i}"):
                                    st.session_state[del_key] = False
                                    st.rerun()
                        else:
                            # Edit mode
                            with st.form(f"trav_edit_form_{camp_name}_{i}"):
                                ef1, ef2 = st.columns(2)
                                saved_orig = leg.get("origin", "")
                                saved_dest = leg.get("destination", "")
                                if _wb_locs:
                                    e_orig_sel, e_orig_custom = _location_widgets(
                                        ef1, "From", f"edit_orig_{camp_name}_{i}", _wb_locs, default=saved_orig)
                                    e_dest_sel, e_dest_custom = _location_widgets(
                                        ef2, "To",   f"edit_dest_{camp_name}_{i}", _wb_locs, default=saved_dest)
                                else:
                                    e_orig_sel  = _CUSTOM_SENTINEL
                                    e_dest_sel  = _CUSTOM_SENTINEL
                                    e_orig_custom = ef1.text_input("From", value=saved_orig)
                                    e_dest_custom = ef2.text_input("To",   value=saved_dest)
                                ef3, ef4, ef5   = st.columns([2, 1, 1])
                                new_terrain = ef3.selectbox("Terrain", list(TERRAIN_PACE.keys()),
                                                            index=list(TERRAIN_PACE.keys()).index(leg.get("terrain", list(TERRAIN_PACE.keys())[0]))
                                                            if leg.get("terrain") in TERRAIN_PACE else 0)
                                new_miles   = ef4.number_input("Distance (miles)", min_value=0, value=int(leg.get("miles", 0)), step=1)
                                new_days    = ef5.number_input("Days travelled", min_value=0, value=int(leg.get("days", 0)), step=1)
                                new_notes   = st.text_area("Notes", value=leg.get("notes", ""), height=70)
                                new_enc     = st.text_input("Encounter", value=leg.get("encounter", ""))
                                sb1, sb2 = st.columns(2)
                                if sb1.form_submit_button("Save Changes"):
                                    new_origin      = _resolve_location(e_orig_sel, e_orig_custom)
                                    new_destination = _resolve_location(e_dest_sel, e_dest_custom)
                                    st.session_state.travel_data[camp_name][i].update({
                                        "origin":      new_origin,
                                        "destination": new_destination,
                                        "terrain":     new_terrain,
                                        "miles":       int(new_miles),
                                        "days":        int(new_days),
                                        "notes":       new_notes.strip(),
                                        "encounter":   new_enc.strip(),
                                    })
                                    save_travel()
                                    st.session_state[edit_flag] = False
                                    st.rerun()
                                if sb2.form_submit_button("Cancel"):
                                    st.session_state[edit_flag] = False
                                    st.rerun()

