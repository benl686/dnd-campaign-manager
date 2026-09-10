import streamlit as st
from utils import CONDITION_DATA as CONDITIONS, sidebar_exit_button

EXHAUSTION_LEVELS = [
    (1, "Disadvantage on ability checks"),
    (2, "Speed halved"),
    (3, "Disadvantage on attack rolls and saving throws"),
    (4, "Hit point maximum halved"),
    (5, "Speed reduced to 0"),
    (6, "Death"),
]

OTHER_EFFECTS = {
    "Concentration": {
        "desc": "Some spells require you to maintain concentration in order to keep their magic active. If you lose concentration, such a spell ends. You lose concentration if: you cast another concentration spell, you take damage (Constitution saving throw DC = 10 or half the damage taken, whichever is higher), you are incapacitated or killed, or the DM decides a distraction is severe enough.",
        "ends": "Cast another concentration spell, or voluntarily end it (no action required).",
    },
    "Surprise": {
        "desc": "If you are surprised, you can't move or take an action on your first turn of combat, and you can't take a reaction until that turn ends. A member of a group can be surprised even if the other members aren't.",
        "ends": "After your first turn in combat.",
    },
    "Cover (Half)": {
        "desc": "A target with half cover has a +2 bonus to AC and DEX saving throws. A target has half cover if an obstacle blocks at least half of its body.",
        "ends": "When no longer behind cover.",
    },
    "Cover (Three-Quarters)": {
        "desc": "A target with three-quarters cover has a +5 bonus to AC and DEX saving throws. A target has three-quarters cover if about three-quarters of it is covered by an obstacle.",
        "ends": "When no longer behind cover.",
    },
    "Cover (Full)": {
        "desc": "A target with total cover can't be targeted directly by an attack or a spell, although some spells can reach such a target by including it in an area of effect.",
        "ends": "When no longer behind cover.",
    },
}

st.title("Conditions & Effects Reference")
st.caption("Standard D&D 5e conditions, exhaustion, and situational effects.")

search = st.text_input("Search conditions", placeholder="e.g. Prone, Charmed...")

st.header("Conditions")
for name, data in CONDITIONS.items():
    if search and search.lower() not in name.lower() and search.lower() not in data["desc"].lower():
        continue
    with st.expander(name):
        st.markdown(data["desc"])
        st.caption(f"**Ends when:** {data['ends']}")

st.header("Exhaustion")
st.markdown("Exhaustion is measured in levels. Each time a creature suffers exhaustion, it gains one level. A creature suffers the effect of its current level of exhaustion as well as all lower levels.")
st.markdown("Finishing a long rest reduces a creature's exhaustion level by 1, provided the creature has also had some food and drink.")

for level, effect in EXHAUSTION_LEVELS:
    if not search or search.lower() in f"exhaustion level {level}".lower() or search.lower() in effect.lower():
        col1, col2 = st.columns([1, 6])
        col1.markdown(f"**Level {level}**")
        col2.markdown(effect)

st.header("Other Effects")
for name, data in OTHER_EFFECTS.items():
    if search and search.lower() not in name.lower() and search.lower() not in data["desc"].lower():
        continue
    with st.expander(name):
        st.markdown(data["desc"])
        st.caption(f"**Ends when:** {data['ends']}")

