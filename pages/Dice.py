from utils import sidebar_exit_button
import random
import re
import math
import streamlit as st

# ── Constants ──────────────────────────────────────────────────────────────────

DICE = [4, 6, 8, 10, 12, 20, 100]

# Per-group fill/stroke colours for multi-group rolls; cycles for >5 groups
_GROUP_COLORS = [
    ("#b8860b", "#7a5c00"),   # gold    — default / group 0
    ("#9b1c1c", "#6b0000"),   # crimson — group 1
    ("#1e40af", "#0d2a80"),   # cobalt  — group 2
    ("#166534", "#0a3d20"),   # emerald — group 3
    ("#6b21a8", "#420066"),   # purple  — group 4
]

# ── Session state ──────────────────────────────────────────────────────────────

if "roll_history" not in st.session_state:
    st.session_state.roll_history = []
if "last_roll" not in st.session_state:
    st.session_state.last_roll = None


# ── Expression parser ──────────────────────────────────────────────────────────

def _validate_dice(num: int, sides: int):
    """Raise ValueError for out-of-range dice parameters."""
    if num < 1 or num > 100:
        raise ValueError(f"Dice count must be 1–100, got {num}")
    if sides < 2:
        raise ValueError(f"Die sides must be ≥ 2, got {sides}")


def parse_multi_expression(expr: str) -> list[dict]:
    """Parse single or multi-group dice expressions into a list of term dicts.

    Supports:
      '2d6'                        → single group, no modifier
      '2d6+3'  or  '2d6 - 1'      → single group with modifier (no space required)
      '2d6 + 1d8'                  → two groups, totalled
      '2d6 fire + 1d8 cold + 5'   → two labeled groups plus flat modifier
      '4d6 + 2d4 - 3'             → two groups, negative modifier

    For multi-group, operators MUST be padded with spaces: ' + ' or ' - '.
    Labels are any text following the die sides on the same term.

    Returns a list of dicts, each one of:
      {"type": "dice", "sign": ±1, "num": int, "sides": int, "label": str}
      {"type": "mod",  "sign": ±1, "value": int}

    Raises ValueError on any parse failure.
    """
    s = expr.strip()
    if not s:
        raise ValueError("Empty expression")

    # ── Single-group path: no space-padded operator present ───────────────────
    if not re.search(r'\s[+\-]\s', s):
        m = re.match(r'^(\d*)d(\d+)\s*([+-]\s*\d+)?\s*$', s, re.I)
        if not m:
            raise ValueError(
                f"Invalid expression: {s!r}\n"
                "Use 'NdX', 'NdX+M', or 'NdX label + NdY label + M' format."
            )
        num, sides = int(m.group(1) or 1), int(m.group(2))
        _validate_dice(num, sides)
        mod = int(m.group(3).replace(' ', '')) if m.group(3) else 0
        terms: list[dict] = [{"type": "dice", "sign": 1, "num": num,
                               "sides": sides, "label": ""}]
        if mod:
            terms.append({"type": "mod", "sign": 1 if mod >= 0 else -1,
                           "value": abs(mod)})
        return terms

    # ── Multi-group path: split on ' + ' / ' - ' ──────────────────────────────
    # re.split with a capturing group interleaves [term, sign, term, sign, ...]
    parts = re.split(r'\s+([+\-])\s+', s)
    signs     = ['+']       + parts[1::2]   # sign for each term ('+'  = implicit for first)
    term_strs = [parts[0]]  + parts[2::2]   # raw text of each term

    result: list[dict] = []
    for sign_ch, ts in zip(signs, term_strs):
        sign = -1 if sign_ch == '-' else 1
        ts   = ts.strip()

        # Try dice match: optional_count 'd' sides optional_label
        dm = re.match(r'^(\d*)d(\d+)\s*(.*)?$', ts, re.I)
        if dm:
            num, sides = int(dm.group(1) or 1), int(dm.group(2))
            _validate_dice(num, sides)
            result.append({"type": "dice", "sign": sign, "num": num,
                           "sides": sides, "label": (dm.group(3) or "").strip()})
            continue

        # Try plain integer modifier
        nm = re.match(r'^(\d+)$', ts)
        if nm:
            result.append({"type": "mod", "sign": sign, "value": int(nm.group(1))})
            continue

        raise ValueError(f"Cannot parse term: {ts!r}")

    if not result:
        raise ValueError(f"No valid terms found in: {s!r}")
    return result


def roll_terms(terms: list[dict]) -> tuple[list[dict], int]:
    """Roll all dice in a parsed term list and return (rolled_groups, total).

    rolled_groups contains only 'dice' terms, each extended with:
      "rolls":    [int, ...]   individual die results
      "subtotal": int          sum of rolls (unsigned; apply .sign for direction)

    The returned total is the signed grand sum (all dice + all modifiers).
    """
    rolled_groups: list[dict] = []
    total = 0

    for term in terms:
        if term["type"] == "dice":
            rolls    = [random.randint(1, term["sides"]) for _ in range(term["num"])]
            subtotal = sum(rolls)
            group    = {**term, "rolls": rolls, "subtotal": subtotal}
            rolled_groups.append(group)
            total   += term["sign"] * subtotal
        else:  # modifier
            total   += term["sign"] * term["value"]

    return rolled_groups, total


# ── SVG die shape generation ──────────────────────────────────────────────────

def die_shape(sides: int, size: int = 80) -> str:
    """Return an SVG shape element (no outer <svg> tag) for the given die type."""
    h = w = size
    cx, cy = w / 2, h / 2

    if sides == 4:
        pts = f"{cx},{h*0.05} {w*0.95},{h*0.92} {w*0.05},{h*0.92}"
        return f'<polygon points="{pts}" />'
    elif sides == 6:
        r = size * 0.42
        return f'<rect x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" rx="{size*0.12}" />'
    elif sides == 8:
        pts = f"{cx},{h*0.05} {w*0.95},{cy} {cx},{h*0.95} {w*0.05},{cy}"
        return f'<polygon points="{pts}" />'
    elif sides == 10:
        n, r = 5, size * 0.46
        pts = " ".join(
            f"{cx + r*math.cos(2*math.pi/n*i - math.pi/2):.1f},"
            f"{cy + r*math.sin(2*math.pi/n*i - math.pi/2):.1f}"
            for i in range(n)
        )
        return f'<polygon points="{pts}" />'
    elif sides == 12:
        n, r = 6, size * 0.46
        pts = " ".join(
            f"{cx + r*math.cos(2*math.pi/n*i - math.pi/2):.1f},"
            f"{cy + r*math.sin(2*math.pi/n*i - math.pi/2):.1f}"
            for i in range(n)
        )
        return f'<polygon points="{pts}" />'
    elif sides == 20:
        n, r = 6, size * 0.46
        pts = " ".join(
            f"{cx + r*math.cos(math.pi/n*(2*i) - math.pi/2):.1f},"
            f"{cy + r*math.sin(math.pi/n*(2*i) - math.pi/2):.1f}"
            for i in range(n)
        )
        return f'<polygon points="{pts}" />'
    else:  # d100 / other
        return f'<circle cx="{cx}" cy="{cy}" r="{size*0.44}" />'


# ── Animation HTML builder ────────────────────────────────────────────────────

def build_animation(
    die_list: list[dict],
    total: int,
    modifier: int,
    adv_mode: str,
    winning_idx: int | None,
) -> str:
    """Build the falling-dice animation HTML.

    die_list entries:
      {"value": int, "sides": int, "fill": str, "stroke": str}

    Advantage/disadvantage: the die at winning_idx is highlighted; others are
    greyed out. For multi-group rolls winning_idx is None.

    Returns a full HTML document for st.iframe().
    """
    size        = 90
    die_gap     = 10
    n           = len(die_list)
    total_w     = max(500, n * (size + die_gap) + 80)
    container_h = 260

    dice_svgs = []
    for i, d in enumerate(die_list):
        delay    = i * 0.13
        is_loser = (
            adv_mode in ("Advantage", "Disadvantage")
            and winning_idx is not None
            and i != winning_idx
        )
        shape      = die_shape(d["sides"], size)
        loser_style = "filter: grayscale(80%) opacity(0.4);" if is_loser else ""
        label      = str(d["value"])
        font_size  = size * 0.28 if len(label) > 1 else size * 0.32

        svg = f"""
        <div class="die" style="animation-delay:{delay:.2f}s; {loser_style}">
          <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}"
               xmlns="http://www.w3.org/2000/svg">
            <g fill="{d['fill']}" stroke="{d['stroke']}" stroke-width="2.5">
              {shape}
            </g>
            <text x="{size/2}" y="{size/2 + font_size*0.38:.1f}"
                  text-anchor="middle"
                  font-size="{font_size:.1f}"
                  font-family="Georgia, serif"
                  font-weight="bold"
                  fill="#fff2cc">
              {label}
            </text>
          </svg>
        </div>"""
        dice_svgs.append(svg)

    all_land_delay = (n - 1) * 0.13 + 0.55

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin: 0; background: transparent; overflow: hidden; }}
  .scene {{
    position: relative;
    width: {total_w}px;
    height: {container_h}px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: {die_gap}px;
    overflow: hidden;
  }}
  .die {{
    display: inline-block;
    animation: fall-bounce 0.55s cubic-bezier(.36,.07,.19,.97) both;
    transform-origin: center bottom;
    will-change: transform, opacity;
  }}
  @keyframes fall-bounce {{
    0%   {{ transform: translateY(-280px) rotate(-25deg); opacity: 0; }}
    60%  {{ transform: translateY(12px)   rotate(4deg);  opacity: 1; }}
    75%  {{ transform: translateY(-8px)   rotate(-2deg); opacity: 1; }}
    88%  {{ transform: translateY(4px)    rotate(1deg);  opacity: 1; }}
    100% {{ transform: translateY(0px)    rotate(0deg);  opacity: 1; }}
  }}
  .total-wrap {{
    position: absolute;
    bottom: 6px;
    left: 0; right: 0;
    text-align: center;
    animation: fade-in 0.35s ease both;
    animation-delay: {all_land_delay:.2f}s;
    opacity: 0;
  }}
  @keyframes fade-in {{
    from {{ opacity: 0; transform: scale(0.85); }}
    to   {{ opacity: 1; transform: scale(1); }}
  }}
  .total-label {{ font-size:22px; font-family:Georgia,serif; font-weight:bold;
                  color:#d4af37; text-shadow:0 1px 4px rgba(0,0,0,0.6); }}
  .total-num   {{ font-size:38px; font-family:Georgia,serif; font-weight:bold;
                  color:#fff8dc; text-shadow:0 2px 8px rgba(0,0,0,0.8);
                  margin-left:6px; }}
  .adv-label   {{ font-size:13px; color:#aaa; font-family:sans-serif;
                  margin-top:2px; }}
</style>
</head>
<body>
<div class="scene">
  {"".join(dice_svgs)}
  <div class="total-wrap">
    <span class="total-label">= </span><span class="total-num">{total}</span>
    {"" if not modifier else
      f'<span class="total-label"> {("+" if modifier > 0 else "")}{modifier}</span>'}
    {"" if adv_mode == "Normal" else
      f'<div class="adv-label">({adv_mode})</div>'}
  </div>
</div>
</body>
</html>"""
    return html


# ── Roll helpers ──────────────────────────────────────────────────────────────

def _make_die_list(rolls: list[int], sides: int,
                   fill: str = "#b8860b", stroke: str = "#7a5c00") -> list[dict]:
    """Build a die_list from a flat rolls array, all the same colour and shape."""
    return [{"value": r, "sides": sides, "fill": fill, "stroke": stroke}
            for r in rolls]


def do_roll(sides: int, adv_mode: str, label: str | None = None):
    """Quick-roll a single die (used by the quick-roll buttons).

    Handles advantage/disadvantage by rolling twice and keeping higher/lower.
    Stores result in st.session_state.last_roll.
    """
    fill, stroke = _GROUP_COLORS[0]

    if adv_mode in ("Advantage", "Disadvantage"):
        r1, r2      = random.randint(1, sides), random.randint(1, sides)
        winning_idx = 0 if (adv_mode == "Advantage") == (r1 >= r2) else 1
        rolls       = [r1, r2]
        result      = rolls[winning_idx]
        tag         = label or f"d{sides}"
        detail      = f"[{r1}, {r2}] → {result} ({adv_mode})"
        modifier    = 0
    else:
        rolls       = [random.randint(1, sides)]
        result      = rolls[0]
        modifier    = 0
        winning_idx = None
        tag         = label or f"d{sides}"
        detail      = f"[{result}]"

    st.session_state.last_roll = {
        "die_list":    _make_die_list(rolls, sides, fill, stroke),
        "total":       result,
        "modifier":    modifier,
        "adv_mode":    adv_mode,
        "winning_idx": winning_idx,
        "groups":      None,   # single roll — no group breakdown
    }
    entry = f"**{tag}**: {detail} = **{result}**"
    _push_history(entry)


def do_multi_roll(expr: str, adv_mode: str):
    """Parse and roll a potentially multi-group expression.

    Builds a colour-coded die_list and stores per-group breakdown for display.
    Advantage/disadvantage only applies when the expression resolves to a single
    die (e.g., 'd20'); for multi-group expressions it is ignored.
    """
    terms        = parse_multi_expression(expr)
    dice_terms   = [t for t in terms if t["type"] == "dice"]
    mod_terms    = [t for t in terms if t["type"] == "mod"]
    flat_mod     = sum(t["sign"] * t["value"] for t in mod_terms)
    # "Multi" means more than one physical die is being rolled — either more
    # than one dice group (e.g. "1d6 + 1d4") OR a single group specifying more
    # than one die (e.g. "2d6"). Checking only len(dice_terms) missed the
    # second case, so an expression like "2d6 adv" silently rolled a single
    # d6 twice (taking the higher) instead of ignoring adv/dis for a
    # multi-die expression as the function is meant to.
    is_multi     = len(dice_terms) > 1 or (len(dice_terms) == 1 and dice_terms[0]["num"] != 1)

    # Advantage/disadvantage: only for single-die expressions
    if adv_mode in ("Advantage", "Disadvantage") and not is_multi:
        t           = dice_terms[0]
        sides       = t["sides"]
        r1, r2      = random.randint(1, sides), random.randint(1, sides)
        winning_idx = 0 if (adv_mode == "Advantage") == (r1 >= r2) else 1
        result      = [r1, r2][winning_idx] + flat_mod
        fill, stroke = _GROUP_COLORS[0]
        st.session_state.last_roll = {
            "die_list":    _make_die_list([r1, r2], sides, fill, stroke),
            "total":       result,
            "modifier":    flat_mod,
            "adv_mode":    adv_mode,
            "winning_idx": winning_idx,
            "groups":      None,
        }
        detail = f"[{r1}, {r2}] → {[r1,r2][winning_idx]} ({adv_mode})"
        _push_history(f"**{expr}**: {detail}{f' {flat_mod:+d}' if flat_mod else ''} = **{result}**")
        return

    # Normal or multi-group roll
    rolled_groups, total = roll_terms(terms)
    total += 0  # already includes modifier contributions from roll_terms

    # Build flat die_list with per-group colours
    die_list: list[dict] = []
    for g_idx, g in enumerate(rolled_groups):
        fill, stroke = _GROUP_COLORS[g_idx % len(_GROUP_COLORS)]
        for rv in g["rolls"]:
            die_list.append({"value": rv, "sides": g["sides"],
                             "fill": fill, "stroke": stroke})

    st.session_state.last_roll = {
        "die_list":    die_list,
        "total":       total,
        "modifier":    flat_mod,
        "adv_mode":    "Normal",
        "winning_idx": None,
        "groups":      rolled_groups if is_multi else None,
        "flat_mod":    flat_mod,
    }

    # Build history entry
    if is_multi:
        parts = []
        for g in rolled_groups:
            rolls_str = f"[{', '.join(str(r) for r in g['rolls'])}]"
            name      = g["label"] or f"d{g['sides']}"
            signed    = g["sign"] * g["subtotal"]
            parts.append(f"{name} {rolls_str}={'−' if signed < 0 else ''}{abs(signed)}")
        if flat_mod:
            parts.append(f"{flat_mod:+d}")
        _push_history(f"**{expr}**: {' + '.join(parts)} = **{total}**")
    else:
        g         = rolled_groups[0] if rolled_groups else None
        rolls_str = f"[{', '.join(str(r) for r in g['rolls'])}]" if g else "[]"
        mod_str   = f" {flat_mod:+d}" if flat_mod else ""
        _push_history(f"**{expr}**: {rolls_str}{mod_str} = **{total}**")


def _push_history(entry: str):
    """Prepend entry to roll history, capped at 20."""
    st.session_state.roll_history.insert(0, entry)
    st.session_state.roll_history = st.session_state.roll_history[:20]


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("Dice Roller")

# Advantage / disadvantage mode (applies to quick rolls and single-die expressions)
with st.container():
    adv_col, *_ = st.columns([2, 5])
    adv_mode = adv_col.radio("Mode", ["Normal", "Advantage", "Disadvantage"],
                              horizontal=True, key="adv_mode")

# ── Quick roll buttons ────────────────────────────────────────────────────────
st.markdown("#### Quick Roll")
cols = st.columns(len(DICE))
for col, sides in zip(cols, DICE):
    if col.button(f"d{sides}", width='stretch'):
        do_roll(sides, adv_mode)
        st.rerun()

# ── Custom expression input ───────────────────────────────────────────────────
st.markdown("#### Custom Roll")
st.caption(
    "Single group: `2d6+3` · `d20` · `4d8-2`  \n"
    "Multi-group (pad operators with spaces): `2d6 + 1d8` · `2d6 fire + 1d8 cold + 5`"
)
expr_col, roll_col = st.columns([3, 1])
expr = expr_col.text_input(
    "Expression",
    label_visibility="collapsed",
    placeholder="2d6 fire + 1d8 cold + 5",
)
if roll_col.button("Roll", width='stretch'):
    if expr.strip():
        try:
            do_multi_roll(expr.strip(), adv_mode)
            st.rerun()
        except (ValueError, AttributeError) as e:
            st.error(str(e) if str(e) else "Invalid expression")
    else:
        st.error("Enter a dice expression")

# ── Animation display ─────────────────────────────────────────────────────────
if st.session_state.last_roll:
    lr   = st.session_state.last_roll
    html = build_animation(
        lr["die_list"], lr["total"], lr["modifier"],
        lr["adv_mode"], lr["winning_idx"],
    )
    st.iframe(html, height=260)

    # Per-group breakdown shown below animation for multi-group rolls
    groups = lr.get("groups")
    if groups and len(groups) > 1:
        flat_mod = lr.get("flat_mod", 0)
        parts    = []
        for g_idx, g in enumerate(groups):
            fill, _ = _GROUP_COLORS[g_idx % len(_GROUP_COLORS)]
            name    = g["label"] or f"d{g['sides']}"
            signed  = g["sign"] * g["subtotal"]
            rolls_s = ", ".join(str(r) for r in g["rolls"])
            parts.append(f"**{name}** [{rolls_s}] = {signed}")
        if flat_mod:
            parts.append(f"modifier {flat_mod:+d}")
        st.caption("  +  ".join(parts) + f"  =  **{lr['total']}**")

# ── Roll history ──────────────────────────────────────────────────────────────
if st.session_state.roll_history:
    st.markdown("---")
    st.markdown("#### Roll History")
    st.caption(f"Showing last {len(st.session_state.roll_history)} rolls (capped at 20). History is lost on page refresh.")
    if st.button("Clear History"):
        st.session_state.roll_history = []
        st.session_state.last_roll    = None
        st.rerun()
    for entry in st.session_state.roll_history:
        st.markdown(entry)

