import random
import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, load_campaigns, no_campaigns_notice
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

WEATHER_PATH      = Path("json/weather_tracker.json")

CLIMATES = [
    "Temperate",
    "Arctic / Tundra",
    "Desert",
    "Tropical / Jungle",
    "Coastal / Maritime",
    "Mountain",
    "Underground / Underdark",
]

WEATHER_BY_CLIMATE = {
    "Temperate": [
        "Clear skies, mild breeze", "Overcast with scattered clouds", "Light rain, cool temperatures",
        "Heavy downpour, limited visibility", "Foggy morning, clearing by midday",
        "Blustery wind, leaves rattling", "Sunny and warm, shirtsleeve weather",
        "Thunderstorm, lightning in the distance", "Light snowfall (winter only), dusting the ground",
        "Crisp and cold, frost on the ground", "A rainbow arcing over the nearest hills, light rain easing",
        "Bitter cold snap, breath visible even at midday",
        "Damp, grey sky with persistent drizzle that never quite becomes rain",
        "Perfect autumn afternoon, leaves drifting, light golden",
        "Gusty pre-storm winds, clouds building in the west",
        "Morning haze burning off by noon, warm and still",
        "Heavy dew overnight, everything glistening at dawn",
        "Rolling fog bank moving through, visibility down to 30 feet",
        "Sudden cold rain that stops as quickly as it started",
        "Unseasonably warm for the season — almost eerie in its stillness",
        "Still morning air before a gathering storm; birdsong has gone quiet",
        "Sudden hail for thirty seconds, then nothing, then sunshine as if nothing happened",
        "A clammy, oppressive afternoon that never quite resolves into rain",
        "Pale winter sun with no warmth whatsoever behind it",
        "A fast-moving squall that leaves everything smelling of wet stone",
    ],
    "Arctic / Tundra": [
        "Blinding blizzard, near-zero visibility", "Clear but bitterly cold, exposed skin hurts within minutes",
        "Light snowfall, calm winds, deceptively pleasant", "Frozen fog clinging to the ground",
        "Brief arctic sun, deceptive warmth that vanishes with the clouds",
        "Howling wind, windchill below -20°F", "Ice storm — every surface becomes treacherous",
        "Overcast and flat, the horizon indistinguishable from the sky",
        "Aurora borealis at night, green and violet curtains", "Sudden whiteout conditions with no warning",
        "Ground blizzard — air seems clear above the knees, surface is chaos",
        "Overcast, temperature rising slightly — dangerous thaw on ice bridges",
        "Crackling, eerie silence; the ice groans in the far distance",
        "Thin sunlight through high cloud, just enough to blind on fresh snow",
        "A rare break in the cloud, bitterly cold but clear as glass",
        "Frost fog rolling in from the glaciers, reducing visibility",
        "Sudden temperature drop of 20°F in under an hour",
        "Melt water running under the ice — surface unreliable underfoot",
        "Parhelion — two false suns flanking the real one, all equally blinding",
        "Permafrost heaving — ground buckles and shifts without warning",
        "A brief window of dead calm between two fronts — use it while it lasts",
        "Spindrift: loose surface snow blowing horizontally at shin height in a technically clear sky",
        "Ice fog — tiny suspended ice crystals glittering in the air, visibility under 20 feet",
        "A pressure ridge has formed overnight, raising a wall of buckled ice across the route",
        "Hoarfrost forming on every exposed surface as temperatures plummet through the afternoon",
    ],
    "Desert": [
        "Scorching sun, zero clouds, heat shimmer in every direction",
        "Sandstorm approaching from the east, moving fast",
        "Cool night air, stars brilliant overhead, temperature dropping fast",
        "Haze from reflected heat, mirages appearing beyond 200 feet",
        "Unexpected rain — flash flood risk in any dry channel",
        "Dust devil spinning lazily across the flats",
        "Oppressive heat, no wind, nowhere to go",
        "Dry lightning on the horizon, no rain below it",
        "Unseasonably cool with a light wind, pleasant while it lasts",
        "Heavy dew at dawn — moisture on rocks and gear",
        "Pre-dawn cold, cloak-weather despite yesterday's heat",
        "High wind with no sand in the air — just noise and unsteadiness",
        "An unexpected pocket of cool air trapped in a low valley",
        "The horizon shimmers violently; distances impossible to judge",
        "Clouds building but burning away before they can release any rain",
        "Red dawn, sand particles carried high in the atmosphere",
        "Rock too hot to touch by midday; metal equipment burns bare skin",
        "Night storm: brief, violent, over in 30 minutes, trails mud in its wake",
        "Relentless sun; shadows sharp as blades, no softening haze",
        "A haboob (wall of dust) visible on the horizon — hours away, or minutes",
        "A false dawn — light before sunrise fades back to dark before the real sunrise",
        "Absolute windless silence; sound carries for miles in all directions",
        "The sharp smell of rain in the air; not a drop falls anywhere",
        "The ground still radiating heat long after sunset, burning through boot leather",
        "Twilight lasting barely fifteen minutes, then absolute darkness with no transition",
    ],
    "Tropical / Jungle": [
        "Oppressive humidity, still air, everything damp before you move",
        "Daily afternoon thunderstorm, building since late morning",
        "Morning mist threading through the canopy, cool and grey",
        "Torrential monsoon rain, inches per hour",
        "Brilliant sun piercing the canopy, insects deafening",
        "Warm breeze carrying floral scents and something rotting",
        "Low clouds threatening downpour at any moment",
        "Calm and clear — eerie quiet in the undergrowth",
        "Unseasonable chill with high winds shaking the canopy",
        "Overcast all day, dripping with humidity",
        "The forest has gone completely silent — always a bad sign",
        "Distant thunder circling the canopy without ever breaking into rain",
        "Sudden squall shaking the canopy but barely reaching the forest floor",
        "Thick cloud cover, no rain but muggy beyond endurance",
        "A rare clear sky through a gap in the canopy — feels like another world",
        "Bioluminescent fungi glowing faintly at ground level after dark",
        "Ash-fall from a distant volcano, everything dusted pale grey",
        "Shallow river flooding its banks, trail half-submerged",
        "Pre-dawn chorus of birds and insects; overwhelming, beautiful, unrelenting",
        "Midday dead calm — everything stops, waiting for a storm that may not come",
        "The jungle floor ankle-deep in standing water after last night's rain; dry camp impossible",
        "A heat shimmer rising from the canopy itself, the entire forest visibly steaming",
        "A clearing in the rain after a week of daily storms — the animals seem confused by it",
        "Steam rising from the ground as the first sun in days hits wet soil",
        "Heavy mist at ground level, canopy overhead is clear and bright",
    ],
    "Coastal / Maritime": [
        "Strong sea wind, waves choppy and rough", "Dense coastal fog, navigation by landmarks impossible",
        "Clear skies, salty breeze, good weather to be at sea",
        "Incoming squall from the ocean, arriving within the hour",
        "Calm sea, flat water, glassy surface — unsettlingly still",
        "Mild rain with warm temperatures, pleasant if you don't mind wet",
        "Thunderstorm over the open water, approaching the coast",
        "Offshore gale — dangerous for small vessels, waves breaking over the pier",
        "Misty drizzle all day, visibility poor but workable",
        "Perfect sailing weather, fair wind and following sea",
        "A waterspout visible in the distance, moving parallel to the coast",
        "Spring tide — the beach is underwater, exposing rocky cliffs not usually seen",
        "High humidity, salt crystallising on metal and leather equipment",
        "Sharp afternoon sea breeze, welcome relief from the day's heat",
        "A bank of fog so thick it muffles sound as well as sight",
        "Red sky at night — sailor's warning, weather changing tomorrow",
        "Unseasonably cold current offshore, chilling the entire coast",
        "Lightning striking the open water in the distance, no rain here yet",
        "Surf unusually high and rough for the conditions — something offshore",
        "Rainbow over the water in the early morning, gone within minutes",
        "Dead calm — no wind, no swell, sails useless; oars required",
        "A sudden wind shift catches every sail wrong simultaneously",
        "Bioluminescent water after dark, beautiful and deeply disorienting to navigate",
        "A ship-swallowing fog bank — vessels twenty feet away are completely invisible",
        "An unseasonably warm current making the water noticeably warmer than the air above it",
    ],
    "Mountain": [
        "Clear at dawn but clouds building by midmorning, thunderstorm by noon",
        "High altitude wind, bitterly cold despite being midsummer",
        "Thin air — exertion costs twice as much, headaches likely",
        "Cloud inversion — the valley below hidden in white, the peak above clear",
        "Heavy hail, briefly intense, over in minutes, leaving marble-sized ice",
        "Rockfall triggered by the overnight freeze-thaw cycle",
        "Crisp and perfectly clear — visibility extends for fifty miles",
        "A chinook (warm wind) dropping the temperature by 20°F in thirty minutes",
        "Freezing rain coating every exposed surface in a sheet of ice",
        "Heavy snow at altitude; lower paths remain clear and warm",
        "Pre-dawn silence, stars extraordinary in the thin air",
        "Mist clinging to cliff faces and waterfalls, dripping constantly",
        "An ice shelf calving somewhere below, the sound like a cannon shot",
        "Anvil clouds building around the peaks above, lightning striking the summits",
        "Storm pinning the party in place — movement impossible for 1d4 hours",
        "Thin sunlight giving plenty of light but no warmth whatsoever",
        "A large raptor (condor, griffon, or eagle) circling the summit overhead",
        "Biting insects emerging after a brief warm spell — worse at altitude, somehow",
        "Fog bank rolling over the pass, eliminating every landmark",
        "Full moon making the snowfields as bright as midday",
        "Verglas — a sheet of invisible ice over every surface that looks like wet rock",
        "Wind coming from directly below, pushing upward against the descent",
        "Afternoon sun melting the surface snow, which freezes hard as glass overnight",
        "A brown dust cloud visible in the plains far below — nothing but clean air up here",
        "Clear morning with every summit visible and seemingly reachable, then cloud by 10am",
    ],
    "Underground / Underdark": [
        "Dead air — torches burn lower, breathing costs more effort",
        "Dripping water from the ceiling, steady as a clock",
        "A faint tremor, brief, settling dust from above",
        "Distant flowing water — direction impossible to determine",
        "Sudden cold draft from an unseen passage, extinguishing unshielded flames",
        "A bloom of phosphorescent spores drifting through the dark",
        "The sound of something moving steadily in a parallel corridor",
        "Unusual warmth — volcanic vents nearby, rock hot to the touch",
        "A thick mineral smell, almost sweet — possibly toxic",
        "Condensation on every surface, everything slick with moisture",
        "Echoes playing tricks — sounds appear to come from everywhere at once",
        "A sudden change in air pressure — something large has moved nearby",
        "Perfect, oppressive silence, the kind that presses against the ears",
        "Bioluminescent moss providing dim blue-green ambient light",
        "A cloud of harmless cave bats disturbed and swirling overhead",
        "The groan of shifting rock from above — settling, probably",
        "Rising water — a passage behind the party is now ankle-deep",
        "Sulfurous vents releasing hot gas — move quickly or take damage",
        "The clicking of unknown insects in the surrounding dark",
        "Crystal formations refracting torchlight into fractured prismatic rainbows",
        "A sudden temperature drop of 10°F with no discernible cause",
        "A distant regular booming sound — water hammer in flooded tunnels, or something else",
        "An odd electric feeling in the air, like before a lightning storm; hair standing on end",
        "Fine mineral dust in the air, coating everything and irritating eyes and throats",
        "The sound of flowing water stops abruptly, mid-rush, as if a valve somewhere closed",
    ],
}


# ── Session state ─────────────────────────────────────────────────────────────

campaigns = load_campaigns()
if "weather_data" not in st.session_state:
    st.session_state.weather_data = load_json(WEATHER_PATH, {})


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Weather Tracker")
st.caption("Track current weather per campaign. Roll new weather or set it manually.")

tab_tracker, tab_gen = st.tabs(["Weather Tracker", "Weather Generator"])

with tab_tracker:
    if not campaigns:
        no_campaigns_notice()
    else:
        for camp in campaigns:
            camp_name = camp["name"]
            header    = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name

            with st.expander(header):
                data = st.session_state.weather_data.get(camp_name, {
                    "climate":         CLIMATES[0],
                    "current_weather": "Not set",
                    "day_count":       1,
                    "history":         [],
                })

                # ── Climate and day counter ───────────────────────────────────────
                # Pending-day pattern: button handlers can't set a widget's session-state
                # key after the widget has already been instantiated in the same run, so
                # they write to a _pending_ key instead. We apply it here on the NEXT
                # render, before the number_input is created, so value= is honoured.
                pending_day_key = f"wx_pending_day_{camp_name}"
                if pending_day_key in st.session_state:
                    st.session_state[f"wx_day_{camp_name}"] = st.session_state.pop(pending_day_key)

                c1, c2 = st.columns([3, 1])
                with c1:
                    climate = st.selectbox(
                        "Climate / Terrain",
                        CLIMATES,
                        index=CLIMATES.index(data.get("climate", CLIMATES[0])),
                        key=f"wx_climate_{camp_name}",
                    )
                with c2:
                    day_count = st.number_input(
                        "Campaign Day",
                        min_value=1,
                        value=int(data.get("day_count", 1)),
                        step=1,
                        key=f"wx_day_{camp_name}",
                    )

                # ── Current weather display ───────────────────────────────────────
                current = data.get("current_weather", "Not set")
                st.markdown("**Current Weather**")
                if current == "Not set":
                    st.caption("No weather set yet. Roll or enter below.")
                else:
                    st.info(current)

                # ── Roll new weather ──────────────────────────────────────────────
                # Both buttons on the same row: main roll takes most of the width,
                # re-roll is pushed to the far right (5:1 split ≈ 83% / 17%).
                btn_label = (
                    "Roll Day 1 Weather"
                    if current == "Not set"
                    else f"▶ Next Day (Day {int(day_count) + 1}) — Roll Weather"
                )
                roll_col, reroll_col = st.columns([5, 1])

                if roll_col.button(btn_label, key=f"wx_roll_{camp_name}"):
                    new_weather = random.choice(WEATHER_BY_CLIMATE[climate])
                    history = data.get("history", [])
                    if current != "Not set":
                        # Archive the day that is ending, then advance
                        history.append({"day": int(day_count), "weather": current})
                        history = history[-10:]
                        new_day = int(day_count) + 1
                    else:
                        new_day = int(day_count)   # first roll: stay on current day
                    entry = {
                        "climate":         climate,
                        "current_weather": new_weather,
                        "day_count":       new_day,
                        "history":         history,
                    }
                    st.session_state.weather_data[camp_name] = entry
                    st.session_state[pending_day_key] = new_day   # applied before number_input next render
                    save_json(WEATHER_PATH, st.session_state.weather_data)
                    st.rerun()

                if reroll_col.button("↺ Re-roll", key=f"wx_reroll_{camp_name}",
                                     help="Re-roll weather for the current day without advancing the day counter"):
                    new_weather = random.choice(WEATHER_BY_CLIMATE[climate])
                    entry = {
                        "climate":         climate,
                        "current_weather": new_weather,
                        "day_count":       int(day_count),
                        "history":         data.get("history", []),
                    }
                    st.session_state.weather_data[camp_name] = entry
                    save_json(WEATHER_PATH, st.session_state.weather_data)
                    st.rerun()

                # ── Manual weather entry ──────────────────────────────────────────
                with st.expander("Set weather manually"):
                    manual = st.text_input(
                        "Weather description",
                        placeholder="e.g. Thunderstorm rolling in from the north…",
                        key=f"wx_manual_{camp_name}",
                    )
                    if st.button("Set Manual Weather", key=f"wx_manual_set_{camp_name}"):
                        if manual.strip():
                            history = data.get("history", [])
                            if current != "Not set":
                                history.append({"day": int(day_count), "weather": current})
                                history = history[-10:]
                            entry = {
                                "climate":         climate,
                                "current_weather": manual.strip(),
                                "day_count":       int(day_count),
                                "history":         history,
                            }
                            st.session_state.weather_data[camp_name] = entry
                            save_json(WEATHER_PATH, st.session_state.weather_data)
                            st.rerun()
                        else:
                            st.error("Enter a weather description.")

                # ── Weather history ───────────────────────────────────────────────
                history = data.get("history", [])
                if history:
                    with st.expander("Weather history (last 10 days)"):
                        for entry in reversed(history):
                            st.caption(f"Day {entry['day']}: {entry['weather']}")

                        st.markdown("---")
                        clear_key = f"wx_clear_hist_{camp_name}"
                        if clear_key not in st.session_state:
                            st.session_state[clear_key] = False
                        if not st.session_state[clear_key]:
                            if st.button("Clear History", key=f"wx_clear_hist_btn_{camp_name}"):
                                st.session_state[clear_key] = True
                                st.rerun()
                        else:
                            st.warning("Clear all weather history for this campaign?")
                            cc1, _, cc2 = st.columns([1, 7, 1])
                            if cc1.button("Confirm", key=f"wx_clear_hist_yes_{camp_name}"):
                                st.session_state.weather_data[camp_name]["history"] = []
                                save_json(WEATHER_PATH, st.session_state.weather_data)
                                st.session_state[clear_key] = False
                                st.rerun()
                            if cc2.button("Cancel", key=f"wx_clear_hist_no_{camp_name}"):
                                st.session_state[clear_key] = False
                                st.rerun()


with tab_gen:
    st.subheader("Weather Generator")
    st.caption("Quick one-off weather roll — not tied to a campaign.")
    gen_climate = st.selectbox("Climate / Terrain", list(WEATHER_BY_CLIMATE.keys()), key="wx_gen_climate")
    if st.button("Roll Weather", key="wx_gen_roll"):
        result = random.choice(WEATHER_BY_CLIMATE[gen_climate])
        st.info(f"**{gen_climate}:** {result}")
