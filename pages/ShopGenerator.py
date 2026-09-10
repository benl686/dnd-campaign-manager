"""
ShopGenerator.py — Generate a merchant's shop inventory.

Pulls SRD item and magic item data to produce a randomised stock list
for any shop type. Prices are based on SRD cost fields with a configurable
markup/discount modifier. Magic shops filter by rarity appropriate to the
party level.
"""

import json
import random
import re
from pathlib import Path
import streamlit as st
from utils import load_json_cached, sidebar_exit_button, get_pref, save_prefs
from treasure_tables import GEMS, JEWELRY

ITEMS_PATH      = Path("data/items_srd.json")
MAGICITEMS_PATH = Path("data/magicitems.json")

# Bare single-word metal names in SRD trade goods have no unit qualifier.
# We append "(per lb.)" so the DM knows what they're looking at.
_METAL_TRADE_GOODS = {"platinum", "gold", "silver", "copper", "iron", "tin", "lead"}


# ── Shop type → SRD item categories ──────────────────────────────────────────
# Each shop type draws from a subset of SRD categories. "Magic Shop" and
# "Alchemist" also pull from magicitems.json (filtered by rarity).

SHOP_TYPES = {
    "General Store":      ["Adventuring Gear", "Equipment Pack", "Tools", "Trade Good"],
    "Blacksmith":         ["Weapon", "Weapons", "Armor", "Shield", "Tools", "Ammunition"],
    "Armsdealer":         ["Weapon", "Weapons", "Ammunition"],
    "Armorer":            ["Armor", "Shield"],
    "Alchemist":          ["Potion", "Potions", "Poison"],
    "Fletcher / Bowyer":  ["Ammunition"],   # ranged weapons added by special filter
    "Magic Shop":         ["Potion", "Potions", "Ring", "Rod", "Scroll",
                           "Wand", "Wondrous Item", "Spellcasting Focus"],
    "Jeweler":            [],               # uses treasure_tables gem / jewelry pools
    "Tavern / Inn":       [],               # uses curated food/drink list
    "Book & Scroll Shop": ["Scroll", "Spellcasting Focus", "Adventuring Gear"],
}

# Tavern stock is entirely custom (not in SRD item file)
_TAVERN_STOCK = [
    ("Ale (mug)",               0.04),  ("Ale (gallon)",             0.20),
    ("Wine (common, pitcher)",  0.20),  ("Wine (fine, bottle)",     10.00),
    ("Bread (loaf)",            0.02),  ("Cheese (wedge)",           0.10),
    ("Meal (poor quality)",     0.03),  ("Meal (modest quality)",    0.30),
    ("Meal (comfortable quality)", 0.50), ("Room (night, poor)",     0.10),
    ("Room (night, modest)",    0.50),  ("Room (night, comfortable)", 2.00),
    ("Candle (10)",             0.10),  ("Torch",                    0.01),
    ("Lantern oil (flask)",     0.10),
]

# Keywords that identify ranged weapons for the Fletcher shop
_RANGED_KEYWORDS = {"bow", "crossbow", "dart", "sling", "blowgun", "javelin", "throwing"}

# Party level → available magic item rarities for magic shops
_LEVEL_RARITIES = [
    (4,  ["Common"]),
    (10, ["Common", "Uncommon"]),
    (16, ["Common", "Uncommon", "Rare"]),
    (20, ["Common", "Uncommon", "Rare", "Very Rare"]),
    (30, ["Common", "Uncommon", "Rare", "Very Rare", "Legendary"]),
]

def _rarities_for_level(level: int) -> list[str]:
    for threshold, rarities in _LEVEL_RARITIES:
        if level <= threshold:
            return rarities
    return ["Common", "Uncommon", "Rare", "Very Rare", "Legendary"]


# ── Stock density ─────────────────────────────────────────────────────────────
# Keys include the item-count range so the DM knows what each tier means.
STOCK_SIZES = {
    "Bare Bones (2–4)":     (2,  4),
    "Sparse (5–9)":         (5,  9),
    "Modest (10–15)":       (10, 15),
    "Normal (16–25)":       (16, 25),
    "Well-Stocked (26–40)": (26, 40),
    "Abundant (41–60)":     (41, 60),
}

# Price modifiers — label includes multiplier so the DM sees the effect at a glance
PRICE_MODS = {
    "Fire Sale (×0.5)":    0.50,
    "Discount (×0.75)":    0.75,
    "Standard (×1.0)":     1.00,
    "Marked Up (×1.25)":   1.25,
    "Premium (×1.5)":      1.50,
    "Luxury (×1.75)":      1.75,
    "Extortionate (×2.0)": 2.00,
    "Black Market (×3.0)": 3.00,
}

# Rarity base prices (gp) used when magic item cost field is zero/missing
_RARITY_BASE_GP = {
    "Common": 100, "Uncommon": 500, "Rare": 5000,
    "Very Rare": 50000, "Legendary": 500000,
}

# Fallback prices by SRD category when the cost field is zero/missing
_CATEGORY_FALLBACK_GP = {
    "Weapon": 15,    "Weapons": 15,   "Armor": 50,
    "Shield": 10,    "Ammunition": 0.05,
    "Potion": 50,    "Potions": 50,   "Poison": 100,
    "Adventuring Gear": 2, "Tools": 15, "Trade Good": 5,
    "Ring": 200,     "Rod": 300,      "Scroll": 100,
    "Wand": 250,     "Wondrous Item": 200, "Spellcasting Focus": 25,
}


# ── Data loaders ──────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _load_srd(path: str, mtime: float, _ver: int = 3) -> list:
    """Load and cache SRD items; normalize and deduplicate by canonical name.

    Canonical key = lowercase name with any trailing parenthetical stripped, so
    "Glassblower's Tools" and "Glassblower's Tools (30 GP)" collapse to one entry.
    Also title-cases words inside parentheses ("Holy Water (flask)" → "(Flask)")
    and appends a unit to bare metal trade-good names ("Platinum" → "Platinum (per lb.)").
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    seen: set[str] = set()
    deduped: list[dict] = []
    for item in raw:
        name = item.get("name", "").strip()
        # Strip trailing parenthetical to get a canonical comparison key.
        canon = re.sub(r'\s*\([^)]+\)\s*$', '', name).strip().lower()
        if not canon or canon in seen:
            continue
        seen.add(canon)
        item = dict(item)   # don't mutate the parsed original
        # Title-case each word inside parentheses: "(flask)" → "(Flask)"
        item["name"] = re.sub(
            r'\(([^)]+)\)',
            lambda m: '(' + ' '.join(
                (w[0].upper() + w[1:]) if w else '' for w in m.group(1).split()
            ) + ')',
            name,
        )
        # Strip trailing price tags from the display name: "(30 Gp)" / "(5 Sp)" → removed.
        # Dedup already used canon (no parenthetical), so this only affects display.
        item["name"] = re.sub(r'\s*\(\d[\d,]*\s*[GgSsCc][Pp]\)\s*$', '', item["name"]).strip()
        # Bare metal commodity names carry no unit in the SRD data; clarify for the DM.
        if item.get("category") == "Trade Good" and canon in _METAL_TRADE_GOODS:
            item["name"] += " (per lb.)"
        deduped.append(item)
    return deduped


@st.cache_data(show_spinner=False)
def _load_magic(path: str, mtime: float) -> list:
    """Load and cache magic items; cache busts on file modification."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ── Price helpers ─────────────────────────────────────────────────────────────

def _gp_str(gp: float) -> str:
    """Format a gp value to a readable coin string.

    Uses integer display for whole-number values so 500 gp shows as "500 gp"
    rather than the scientific "5e+02 gp" that :.2g produces.
    """
    if gp >= 1.0:
        rounded = round(gp, 2)
        if rounded == int(rounded):
            return f"{int(rounded):,} gp"
        return f"{rounded:,.2f} gp"
    if gp >= 0.1:
        return f"{round(gp * 10)} sp"
    return f"{max(1, round(gp * 100))} cp"


def _srd_price(item: dict, modifier: float) -> str:
    try:
        base = float(item.get("cost") or 0)
    except (ValueError, TypeError):
        base = 0.0
    if base <= 0:
        base = _CATEGORY_FALLBACK_GP.get(item.get("category", ""), 5)
    return _gp_str(base * modifier)


def _magic_price(item: dict, modifier: float) -> str:
    base = _RARITY_BASE_GP.get(item.get("rarity", "Common"), 100)
    # Vary price ±20% within rarity tier to make shops feel distinct
    varied = base * modifier * random.uniform(0.8, 1.2)
    return f"{round(varied / 10) * 10:,} gp"   # round to nearest 10 gp


# ── Stock generation ──────────────────────────────────────────────────────────

def _generate_stock(
    shop_type: str, stock_size: str, party_level: int,
    price_mod: float, srd_items: list, magic_items: list,
) -> list[dict]:
    """Return a list of {name, qty, price, notes} dicts for the shop's inventory."""

    count = random.randint(*STOCK_SIZES[stock_size])
    result: list[dict] = []

    # ── Jeweler ───────────────────────────────────────────────────────────────
    if shop_type == "Jeweler":
        pool = []
        for tier_items in GEMS.values():
            pool += [(n, "Gem") for n in tier_items]
        for tier_items in JEWELRY.values():
            pool += [(n, "Jewelry") for n in tier_items]
        random.shuffle(pool)
        seen: set[str] = set()
        for name, cat in pool:
            if name not in seen:
                seen.add(name)
                # Random price within plausible gem tier ranges
                price_gp = random.choice([10, 25, 50, 100, 250, 500, 1000, 2500, 5000])
                result.append({
                    "name": name, "qty": random.randint(1, 3),
                    "price": _gp_str(price_gp * price_mod), "notes": cat,
                })
            if len(result) >= count:
                break
        return result

    # ── Tavern / Inn ──────────────────────────────────────────────────────────
    if shop_type == "Tavern / Inn":
        picks = random.sample(_TAVERN_STOCK, min(count, len(_TAVERN_STOCK)))
        for name, base_gp in picks:
            result.append({
                "name": name, "qty": random.randint(5, 20),
                "price": _gp_str(base_gp * price_mod), "notes": "Tavern fare",
            })
        return result

    # ── Standard SRD pool ────────────────────────────────────────────────────
    categories = SHOP_TYPES.get(shop_type, [])
    srd_pool = [item for item in srd_items if item.get("category", "") in categories]

    # Fletcher: add ranged weapons beyond the Ammunition category
    if shop_type == "Fletcher / Bowyer":
        extra_ranged = [
            item for item in srd_items
            if item.get("category") in ("Weapon", "Weapons")
            and any(kw in item.get("name", "").lower() for kw in _RANGED_KEYWORDS)
        ]
        # De-duplicate by name
        existing_names = {i["name"] for i in srd_pool}
        srd_pool += [i for i in extra_ranged if i["name"] not in existing_names]

    # ── Magic Shop: blend SRD magic items + magicitems.json ──────────────────
    if shop_type in ("Magic Shop", "Book & Scroll Shop"):
        allowed = _rarities_for_level(party_level)
        magic_pool = [i for i in magic_items if i.get("rarity") in allowed]
        random.shuffle(magic_pool)
        random.shuffle(srd_pool)

        # Give magic items roughly half the slots; rest goes to SRD potion/scroll entries
        magic_count   = min(count // 2, len(magic_pool))
        regular_count = min(count - magic_count, len(srd_pool))

        for item in srd_pool[:regular_count]:
            result.append({
                "name": item["name"], "qty": random.randint(1, 3),
                "price": _srd_price(item, price_mod),
                "notes": item.get("category", ""),
            })
        for item in magic_pool[:magic_count]:
            att_note = " — requires attunement" if item.get("requires_attunement") else ""
            result.append({
                "name": item["name"], "qty": 1,
                "price": _magic_price(item, price_mod),
                "notes": f"{item.get('rarity', '')} magic item{att_note}",
            })
        return result

    # ── All other shop types ──────────────────────────────────────────────────
    if not srd_pool:
        return []

    picks = random.sample(srd_pool, min(count, len(srd_pool)))
    for item in picks:
        # Ammunition is typically sold in bundles
        qty = random.randint(10, 40) if item.get("category") == "Ammunition" else random.randint(1, 3)
        result.append({
            "name": item["name"], "qty": qty,
            "price": _srd_price(item, price_mod),
            "notes": item.get("category", ""),
        })
    return result


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Shop Generator")
st.caption("Generate a merchant's inventory for any shop type. Re-roll as many times as you like.")

if not ITEMS_PATH.exists():
    st.error("Item data not found. Run `python scripts/download_data.py` first.")
    st.stop()

srd_items   = _load_srd(str(ITEMS_PATH),      ITEMS_PATH.stat().st_mtime, _ver=3)
magic_items = (
    _load_magic(str(MAGICITEMS_PATH), MAGICITEMS_PATH.stat().st_mtime)
    if MAGICITEMS_PATH.exists() else []
)

# ── Settings ──────────────────────────────────────────────────────────────────
# Pre-seed session_state from saved prefs so widgets remember their last values.
_shop_keys   = list(SHOP_TYPES.keys())
_stock_keys  = list(STOCK_SIZES.keys())
_price_keys  = list(PRICE_MODS.keys())
get_pref("shop_type",    _shop_keys[0])
get_pref("shop_stock_size", _stock_keys[2])   # default "Modest (10–15)"
get_pref("shop_level",   5)
get_pref("shop_price",   _price_keys[2])   # default "Standard (×1.0)"
sc1, sc2, sc3, sc4 = st.columns(4)
shop_type   = sc1.selectbox("Shop Type",   _shop_keys,  key="shop_type")
stock_size  = sc2.selectbox("Stock",       _stock_keys, key="shop_stock_size")
party_level = sc3.number_input("Party Level", min_value=1, max_value=30, step=1, key="shop_level")
price_label = sc4.selectbox("Prices",      _price_keys, key="shop_price")
price_mod   = PRICE_MODS[price_label]
# Persist any changes the user made to these settings.
save_prefs({"shop_type":  st.session_state.shop_type,
            "shop_stock_size": st.session_state.shop_stock_size,
            "shop_level": st.session_state.shop_level,
            "shop_price": st.session_state.shop_price})

# ── Generate button ───────────────────────────────────────────────────────────
if "shop_stock"  not in st.session_state:
    st.session_state.shop_stock = []
if "shop_header" not in st.session_state:
    st.session_state.shop_header = ""

gen_col, _ = st.columns([1, 5])
if gen_col.button("🎲 Generate", width='stretch'):
    st.session_state.shop_stock = _generate_stock(
        shop_type, stock_size, int(party_level), price_mod, srd_items, magic_items
    )
    mod_label  = price_label.split("(")[0].strip()   # "Fire Sale" from "Fire Sale (×0.5)"
    size_label = stock_size.split(" (")[0]            # "Modest" from "Modest (10–15)"
    st.session_state.shop_header = f"{size_label} {shop_type}  ·  {mod_label} pricing"

# ── Display results ───────────────────────────────────────────────────────────
stock = st.session_state.shop_stock
if stock:
    st.subheader(st.session_state.shop_header)
    st.caption(f"{len(stock)} items in stock")

    # Column headers
    h1, h2, h3, h4 = st.columns([3.5, 0.8, 1.5, 2.5])
    h1.markdown("**Item**")
    h2.markdown("**Qty**")
    h3.markdown("**Price**")
    h4.markdown("**Notes**")
    st.divider()

    # Sort alphabetically so the DM can scan quickly
    for row in sorted(stock, key=lambda r: r["name"].lower()):
        c1, c2, c3, c4 = st.columns([3.5, 0.8, 1.5, 2.5])
        c1.write(row["name"])
        c2.write(str(row["qty"]))
        c3.write(row["price"])
        c4.caption(row["notes"])
else:
    st.info("Configure the options above and click **🎲 Generate** to stock the shop.")
