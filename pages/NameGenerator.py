from utils import sidebar_exit_button, get_pref, save_prefs
from name_tables import NAMES
import random
import streamlit as st


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Name Generator")
st.caption(
    "Expanded name lists drawing from D&D PHB, FR lore, BG3, DOS2, Dragon Age, "
    "The Witcher, Critical Role, Tolkien, and Arthurian legend."
)

RACES = sorted(NAMES.keys())
GENDERS = ["Male", "Female"]

# Pre-seed session_state from saved prefs so controls remember their last values.
get_pref("ng_race",    RACES[0])
get_pref("ng_gender",  "Male")
get_pref("ng_surname", True)
get_pref("ng_count",   5)

col_race, col_gender, col_surname = st.columns([2, 1, 1])
with col_race:
    race = st.selectbox("Race", RACES, key="ng_race")
with col_gender:
    gender = st.selectbox("Gender", GENDERS, key="ng_gender")
with col_surname:
    include_surname = st.checkbox("Include Surname / Clan Name", key="ng_surname")

# Resolve lists for the selection
race_data  = NAMES[race]
given_pool = race_data.get("male" if gender == "Male" else "female", [])
surn_pool  = race_data.get("surname", [])

count = st.number_input("Names to Generate", min_value=1, max_value=20, step=1, key="ng_count")
# Persist any changes the user made.
save_prefs({"ng_race":   st.session_state.ng_race,
            "ng_gender": st.session_state.ng_gender,
            "ng_surname": st.session_state.ng_surname,
            "ng_count":  int(st.session_state.ng_count)})

if st.button("Generate Names"):
    if not given_pool:
        st.warning("No name data for this combination.")
    else:
        picks = [random.choice(given_pool) for _ in range(int(count))]
        if include_surname and surn_pool:
            for p in picks:
                st.success(f"{p} {random.choice(surn_pool)}")
        else:
            for p in picks:
                st.success(p)

# Full list browser
with st.expander(f"Browse all {race} {gender} names ({len(given_pool)})"):
    st.write(", ".join(sorted(given_pool)))

if include_surname and surn_pool:
    with st.expander(f"Browse all {race} surnames / clan names ({len(surn_pool)})"):
        st.write(", ".join(sorted(surn_pool)))

