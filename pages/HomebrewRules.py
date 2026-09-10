import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, confirm_delete, load_campaigns, no_campaigns_notice
from pathlib import Path


RULES_PATH = Path("json/homebrew_rules.json")

CATEGORIES = ["Combat", "Exploration", "Social", "Crafting", "Other"]

campaigns = load_campaigns()
if "homebrew_rules" not in st.session_state:
    st.session_state.homebrew_rules = load_json(RULES_PATH, {})

st.title("Homebrew Rules")
st.caption("House rules are grouped under each campaign.")

if not campaigns:
    no_campaigns_notice()
else:
    rules_by_camp = st.session_state.homebrew_rules
    if isinstance(rules_by_camp, list):
        rules_by_camp = {}
    st.session_state.homebrew_rules = rules_by_camp

    # Stale delete-confirm cleanup — drop any armed "Confirm?" flag whose rule
    # index no longer exists for that campaign, so a shifted-in rule can't
    # inherit a pre-armed delete confirmation from the rule that used to sit
    # at that index. Prefix-strip (not underscore-split) so campaign names
    # containing underscores can't be mis-parsed.
    for camp in campaigns:
        cn      = camp["name"]
        cur_len = len(rules_by_camp.get(cn, []))
        prefix  = f"rule_delete_{cn}_"
        for key in list(st.session_state.keys()):
            if key.startswith(prefix):
                suffix = key[len(prefix):]
                if suffix.isdigit() and int(suffix) >= cur_len:
                    del st.session_state[key]

    for camp in campaigns:
        camp_name = camp["name"]
        header = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name
        with st.expander(header):
            camp_rules = rules_by_camp.get(camp_name, [])

            # Search filter
            rule_q = st.text_input(
                "Search rules",
                placeholder="Filter by name, category, or description…",
                key=f"rule_search_{camp_name}",
            )

            for idx, rule in enumerate(camp_rules):
                # Apply search filter — still use orig idx for save/delete
                if rule_q.strip():
                    rq = rule_q.strip().lower()
                    if not (rq in rule.get("name", "").lower()
                            or rq in rule.get("category", "").lower()
                            or rq in rule.get("description", "").lower()):
                        continue
                with st.expander(f"[{rule.get('category', 'Other')}] {rule.get('name', f'Rule {idx+1}')}"):
                    rc1, rc2 = st.columns([3, 1])
                    edit_name = rc1.text_input("Rule name", value=rule.get("name", ""), key=f"rule_name_{camp_name}_{idx}")
                    # Fall back to "Other" if the stored category isn't a current option
                    # (e.g. CATEGORIES changed after this rule was saved) — avoids a crash.
                    stored_cat = rule.get("category", "Other")
                    cat_idx = CATEGORIES.index(stored_cat) if stored_cat in CATEGORIES else CATEGORIES.index("Other")
                    edit_cat = rc2.selectbox("Category", CATEGORIES, index=cat_idx, key=f"rule_cat_{camp_name}_{idx}")
                    edit_desc = st.text_area("Description", value=rule.get("description", ""), height=150, key=f"rule_desc_{camp_name}_{idx}")

                    btn_cols = st.columns([7.5, 1])
                    if btn_cols[0].button("Save rule", key=f"rule_save_{camp_name}_{idx}"):
                        camp_rules[idx] = {
                            "name": edit_name.strip() or rule.get("name", f"Rule {idx+1}"),
                            "category": edit_cat,
                            "description": edit_desc,
                        }
                        rules_by_camp[camp_name] = camp_rules
                        st.session_state.homebrew_rules = rules_by_camp
                        save_json(RULES_PATH, rules_by_camp)
                        st.success("Saved")

                    if confirm_delete(btn_cols[1], f"rule_delete_{camp_name}_{idx}", f"rule_{camp_name}_{idx}"):
                        camp_rules.pop(idx)
                        rules_by_camp[camp_name] = camp_rules
                        st.session_state.homebrew_rules = rules_by_camp
                        save_json(RULES_PATH, rules_by_camp)
                        st.rerun()

            st.markdown("---")
            st.subheader("Add New Rule")
            with st.form(f"add_rule_{camp_name}"):
                nc1, nc2 = st.columns([3, 1])
                new_name = nc1.text_input("Rule name", key=f"new_rule_name_{camp_name}")
                new_cat = nc2.selectbox("Category", CATEGORIES, key=f"new_rule_cat_{camp_name}")
                new_desc = st.text_area("Description", height=150, key=f"new_rule_desc_{camp_name}")

                if st.form_submit_button(f"Add rule to {camp_name}"):
                    if new_name.strip():
                        camp_rules.append({
                            "name": new_name.strip(),
                            "category": new_cat,
                            "description": new_desc,
                        })
                        rules_by_camp[camp_name] = camp_rules
                        st.session_state.homebrew_rules = rules_by_camp
                        save_json(RULES_PATH, rules_by_camp)
                        st.success("Rule added")
                        st.rerun()
                    else:
                        st.error("Rule name is required")

