import streamlit as st
from utils import load_json, load_json_cached, save_json, sidebar_exit_button, load_campaigns, no_campaigns_notice
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

CHARACTERS_PATH  = Path("json/characters.json")
INVENTORY_PATH   = Path("json/party_inventory.json")


# ── Session state ─────────────────────────────────────────────────────────────

campaigns  = load_campaigns()
characters = load_json_cached(CHARACTERS_PATH, [])

if "party_inv" not in st.session_state:
    # Schema: {campaign_name: [{name, qty, weight_lbs, category, carried_by, notes}]}
    st.session_state.party_inv = load_json(INVENTORY_PATH, {})


def save_inv():
    """Persist party inventory to disk."""
    save_json(INVENTORY_PATH, st.session_state.party_inv)


CATEGORIES = [
    "Weapon", "Armor / Shield", "Adventuring Gear", "Tool",
    "Magic Item", "Consumable / Potion", "Treasure / Valuables",
    "Ammunition", "Container", "Other",
]


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Party Inventory")
st.caption("Shared loot and gear for the whole party. Track quantities, weight, and who's carrying what.")

# Character names for the "carried by" field
char_names = ["Party / Unassigned"] + [ch["name"] for ch in characters]

if not campaigns:
    no_campaigns_notice()
else:
    for camp in campaigns:
        camp_name = camp["name"]
        header    = f"{camp_name} ({camp.get('system', '')})" if camp.get("system") else camp_name

        with st.expander(header):
            items = st.session_state.party_inv.get(camp_name, [])

            # ── Category filter (rendered first so stats can reflect it) ──────
            cat_options = ["All"] + CATEGORIES
            cat_filter  = st.selectbox("Filter by category", cat_options, key=f"inv_cat_{camp_name}")

            # ── Summary stats — scoped to the active filter ───────────────────
            if items:
                # Count and weight only the items currently visible in the list
                stat_items = (
                    [it for it in items if it.get("category") == cat_filter]
                    if cat_filter != "All" else items
                )
                total_weight = sum(it.get("weight_lbs", 0) * it.get("qty", 1) for it in stat_items)
                sc1, sc2 = st.columns(2)
                sc1.metric(
                    "Items" if cat_filter == "All" else f"{cat_filter} Items",
                    len(stat_items),
                )
                sc2.metric(
                    "Total Weight" if cat_filter == "All" else f"{cat_filter} Weight",
                    f"{total_weight:.1f} lbs",
                )

            # ── Add item form ─────────────────────────────────────────────────
            st.markdown("#### Add Item")
            with st.form(f"add_inv_{camp_name}", clear_on_submit=True):
                af1, af2 = st.columns([3, 1])
                item_name = af1.text_input("Item name", placeholder="e.g. Rope (50 ft.)")
                qty        = af2.number_input("Qty", min_value=1, value=1, step=1)

                af3, af4, af5 = st.columns([2, 1, 2])
                category   = af3.selectbox("Category", CATEGORIES)
                weight_lbs = af4.number_input("Weight (lbs each)", min_value=0.0, value=0.0, step=0.5, format="%.1f")
                carried_by = af5.selectbox("Carried by", char_names)

                notes = st.text_area("Notes", placeholder="e.g. Borrowed from the blacksmith; worth 50 gp", height=60)
                submitted = st.form_submit_button("Add to Inventory")

                if submitted:
                    if item_name.strip():
                        new_item = {
                            "name":       item_name.strip(),
                            "qty":        int(qty),
                            "weight_lbs": float(weight_lbs),
                            "category":   category,
                            "carried_by": carried_by,
                            "notes":      notes.strip(),
                        }
                        if camp_name not in st.session_state.party_inv:
                            st.session_state.party_inv[camp_name] = []
                        st.session_state.party_inv[camp_name].append(new_item)
                        save_inv()
                        st.success(f"Added: {item_name.strip()} ×{int(qty)}")
                    else:
                        st.error("Item name is required.")

            # ── Item list ─────────────────────────────────────────────────────
            st.markdown("---")
            items = st.session_state.party_inv.get(camp_name, [])

            # Apply category filter
            if cat_filter != "All":
                visible = [(i, it) for i, it in enumerate(items) if it.get("category") == cat_filter]
            else:
                visible = list(enumerate(items))

            if not visible:
                st.caption("No items to show.")
            else:
                # Column headers
                hc1, hc2, hc3, hc4, hc5, hc6 = st.columns([3, 0.7, 1.5, 1.5, 1.5, 0.8])
                hc1.markdown("**Name**")
                hc2.markdown("**Qty**")
                hc3.markdown("**Category**")
                hc4.markdown("**Weight**")
                hc5.markdown("**Carrier**")
                hc6.markdown("")

                for i, item in visible:
                    ic1, ic2, ic3, ic4, ic5, ic6 = st.columns([3, 0.7, 1.5, 1.5, 1.5, 0.8])
                    ic1.write(item["name"])
                    ic2.write(str(item.get("qty", 1)))
                    ic3.write(item.get("category", ""))
                    weight_total = item.get("weight_lbs", 0) * item.get("qty", 1)
                    ic4.write(f"{weight_total:.1f} lbs" if weight_total else "—")
                    ic5.write(item.get("carried_by", "Party / Unassigned"))

                    with ic6.popover("✏"):
                        # Inline edit form
                        with st.form(f"edit_inv_{camp_name}_{i}"):
                            new_name   = st.text_input("Name",     value=item["name"])
                            new_qty    = st.number_input("Qty",    min_value=1, value=item.get("qty", 1), step=1)
                            new_weight = st.number_input("Weight (lbs each)", min_value=0.0, value=float(item.get("weight_lbs", 0)), step=0.5, format="%.1f")
                            new_cat    = st.selectbox("Category",  CATEGORIES, index=CATEGORIES.index(item.get("category", CATEGORIES[0])) if item.get("category") in CATEGORIES else 0)
                            new_carrier= st.selectbox("Carried by", char_names, index=char_names.index(item.get("carried_by","Party / Unassigned")) if item.get("carried_by") in char_names else 0)
                            new_notes  = st.text_area("Notes",     value=item.get("notes", ""), height=60)

                            ec1, ec2 = st.columns([4, 1])
                            if ec1.form_submit_button("Save"):
                                st.session_state.party_inv[camp_name][i] = {
                                    "name":       new_name.strip() or item["name"],
                                    "qty":        int(new_qty),
                                    "weight_lbs": float(new_weight),
                                    "category":   new_cat,
                                    "carried_by": new_carrier,
                                    "notes":      new_notes.strip(),
                                }
                                save_inv()
                                st.rerun()

                            # Two-step delete inside the popover
                            del_inner_key = f"inv_del_pending_{camp_name}_{i}"
                            if del_inner_key not in st.session_state:
                                st.session_state[del_inner_key] = False
                            if not st.session_state[del_inner_key]:
                                if ec2.form_submit_button("Delete"):
                                    st.session_state[del_inner_key] = True
                                    st.rerun()
                            else:
                                if ec2.form_submit_button("Confirm Delete?"):
                                    st.session_state.party_inv[camp_name].pop(i)
                                    save_inv()
                                    st.session_state[del_inner_key] = False
                                    st.rerun()

                    # Show notes as a caption below if present
                    if item.get("notes"):
                        st.caption(f"  ↳ {item['notes']}")

