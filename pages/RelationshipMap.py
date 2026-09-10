"""
RelationshipMap.py — Campaign-wide relationship web.

Data is stored in json/relationship_web.json (migrated from npcs.json on
first load).  Entity sources:
  - Alliances  (from factions.json) — rendered as compound parent nodes
  - Factions   (from factions.json, □ rectangle nodes)
  - NPCs       (from npcs.json, ○ ellipse nodes)
  - Faiths     (from faiths.json, ◇ diamond nodes)

Visualization uses Cytoscape.js via st.iframe.
Alliances render as large rounded-rectangle compound nodes whose children
(members) are drawn inside them.  Alliances can contain other alliances,
producing nested boxes.  Because Cytoscape.js supports true compound overlap,
allied alliance boxes can overlap visually — one box can have part of it
inside another alliance's boundary.
"""

import json as _json
import re
import streamlit as st
from utils import load_json, save_json, sidebar_exit_button, get_pref, save_prefs, load_campaigns, no_campaigns_notice
from pathlib import Path

# ── Cytoscape.js bundling ──────────────────────────────────────────────────────
# Download cytoscape.min.js once to static/ so we never hit the CDN again.
# _CY_INLINE is set to the <script> block on first call and reused for the
# lifetime of the process — avoids re-reading the file on every render.
_CY_LOCAL  = Path("static/cytoscape.min.js")
_CY_URL    = "https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"
_CY_INLINE: "str | None" = None   # module-level cache


def _cytoscape_tag() -> str:
    """Return a <script> block with Cytoscape.js inlined from local disk.

    On first call: downloads the library to static/cytoscape.min.js if absent,
    then reads it into memory. Subsequent calls return the cached string.
    Falls back to a CDN <script src> only if the download fails.
    """
    global _CY_INLINE
    if _CY_INLINE is not None:
        return _CY_INLINE
    if not _CY_LOCAL.exists():
        try:
            import urllib.request
            _CY_LOCAL.parent.mkdir(exist_ok=True)
            urllib.request.urlretrieve(_CY_URL, str(_CY_LOCAL))
        except Exception:
            pass   # network unavailable — fall back to CDN src tag
    if _CY_LOCAL.exists():
        _CY_INLINE = f"<script>{_CY_LOCAL.read_text(encoding='utf-8')}</script>"
    else:
        _CY_INLINE = f'<script src="{_CY_URL}"></script>'
    return _CY_INLINE

# ── Paths ─────────────────────────────────────────────────────────────────────

NPCS_PATH      = Path("json/npcs.json")
FACTIONS_PATH  = Path("json/factions.json")
FAITHS_PATH    = Path("json/faiths.json")
RELWEB_PATH    = Path("json/relationship_web.json")

# ── Constants ─────────────────────────────────────────────────────────────────

REL_TYPES = [
    "Ally", "Enemy", "Rival", "Romantic Interest", "Family",
    "Employer / Employee", "Former Ally", "Former Enemy", "Complicated", "Unknown",
]

# Edge colours by relationship type
_EDGE_COLOURS = {
    "Ally":                "#2ECC71",
    "Enemy":               "#E74C3C",
    "Rival":               "#E67E22",
    "Romantic Interest":   "#E91E8C",
    "Family":              "#9B59B6",
    "Employer / Employee": "#3498DB",
    "Former Ally":         "#95A5A6",
    "Former Enemy":        "#BDC3C7",
    "Complicated":         "#F39C12",
    "Unknown":             "#7F8C8D",
}
_DEFAULT_EDGE = "#7F8C8D"

# NPC node colours by importance
_NPC_COLOURS = {
    "Major NPC":         "#F1C40F",
    "Ally":              "#2ECC71",
    "Enemy":             "#E74C3C",
    "Minor NPC":         "#BDC3C7",
    "Neutral / Unknown": "#95A5A6",
}
_FACTION_COLOUR = "#AED6F1"   # light blue
_FAITH_COLOUR   = "#D7BDE2"   # light purple
_UNKNOWN_COLOUR = "#ECF0F1"   # fallback

# Alliance cluster colours (background fill, border)
_ALLIANCE_FILL   = "#FEFDE7"
_ALLIANCE_BORDER = "#F1C40F"


# ── Data migration ────────────────────────────────────────────────────────────

def _migrate_from_npcs():
    """One-time migration: copy relationship_web entries from npcs.json to
    relationship_web.json.  Only runs when relationship_web.json is absent/empty.
    """
    if RELWEB_PATH.exists():
        existing = load_json(RELWEB_PATH, {})
        if existing:
            return  # already migrated

    npcs_data = load_json(NPCS_PATH, {})
    web: dict[str, list] = {}
    for camp_name, camp_data in npcs_data.items():
        if not isinstance(camp_data, dict):
            continue
        old_web = camp_data.get("relationship_web", [])
        if old_web:
            web[camp_name] = old_web

    save_json(RELWEB_PATH, web)


# ── Data helpers ──────────────────────────────────────────────────────────────

def _load_rel_web() -> dict:
    return load_json(RELWEB_PATH, {})


def _save_rel_web(data: dict):
    save_json(RELWEB_PATH, data)


@st.cache_data(show_spinner=False)
def _factions_camp(camp_name: str, _mtime: float) -> tuple[list, list]:
    """Return (faction_list, alliances) for the campaign. Keyed on factions.json mtime."""
    raw = load_json(FACTIONS_PATH, {}).get(camp_name, {})
    if isinstance(raw, list):               # old schema
        return raw, []
    return raw.get("faction_list", []), raw.get("alliances", [])


@st.cache_data(show_spinner=False)
def _npc_list_camp(camp_name: str, _mtime: float) -> list:
    """Return npc_list for the campaign. Keyed on npcs.json mtime."""
    raw = load_json(NPCS_PATH, {}).get(camp_name, {})
    if isinstance(raw, dict):
        return raw.get("npc_list", [])
    return []


@st.cache_data(show_spinner=False)
def _faith_list_camp(camp_name: str, _mtime: float) -> list:
    """Return faiths list for the campaign. Keyed on faiths.json mtime."""
    return load_json(FAITHS_PATH, {}).get(camp_name, [])


def _entity_priority(name: str, npc_list, factions, faiths, alliances) -> int:
    """Return the priority (1–10) of any named entity; default 5."""
    for n in npc_list:
        if n.get("name") == name:
            return int(n.get("priority", 5))
    for a in alliances:
        if a.get("name") == name:
            return int(a.get("priority", 5))
    return 5


def _auto_assign(a: str, b: str, npc_list, factions, faiths, alliances) -> tuple[str, str]:
    """Return (entity_a, entity_b) so the higher-priority entity is A.
    Tiebreaker: alphabetical.
    """
    pa = _entity_priority(a, npc_list, factions, faiths, alliances)
    pb = _entity_priority(b, npc_list, factions, faiths, alliances)
    if pb > pa or (pb == pa and b.lower() < a.lower()):
        return b, a
    return a, b


def _entity_labels(npc_list, factions, faiths, alliances) -> list[tuple[str, str]]:
    """Return [(display_label, clean_name)] sorted priority-desc, alpha-asc.

    Order: alliances (★) → factions (□) → faiths (◇) → NPCs (○)
    within each group sorted by priority desc then name asc.
    """
    entries = []
    for a in sorted(alliances, key=lambda x: (-int(x.get("priority", 5)), x["name"].lower())):
        entries.append((f"★ {a['name']}  (P{a.get('priority',5)} alliance)", a["name"]))
    for f in sorted(factions, key=lambda x: x.get("name", "").lower()):
        entries.append((f"□ {f['name']}  (faction)", f["name"]))
    for faith in sorted(faiths, key=lambda x: x.get("name", "").lower()):
        entries.append((f"◇ {faith['name']}  (faith)", faith["name"]))
    for n in sorted(npc_list, key=lambda x: (-int(x.get("priority", 5)), x.get("name","").lower())):
        entries.append((f"○ {n['name']}  (P{n.get('priority',5)} NPC)", n["name"]))
    return entries


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cid(prefix: str, name: str) -> str:
    """Stable Cytoscape node ID: prefix + sanitised name."""
    return f"{prefix}_{re.sub(r'[^a-zA-Z0-9]', '_', name)}"


# ── Cytoscape.js HTML builder ─────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _build_cytoscape_html(npc_list, factions, faiths, alliances, rel_web: list, reset_layout: bool = False, campaign_slug: str = "") -> str:
    """Build a self-contained HTML page that renders the graph with Cytoscape.js.

    Height is intentionally omitted — the caller passes height= to st.iframe so
    the slider can change the viewport without busting this cache.

    Decorated with @st.cache_data so identical inputs return the cached string
    instantly, which prevents Streamlit from recreating the iframe on every rerun.
    Keeping the same iframe instance means the browser's Cytoscape layout and
    node positions survive page interactions (checkbox toggles, etc.).

    Alliances are compound parent nodes — members are drawn inside them.
    Sub-alliances (type="alliance" members) nest as compound-inside-compound.
    Relationship edges are drawn between specific named nodes.
    """

    # ── Build parent-lookup tables ─────────────────────────────────────────────

    # Sub-alliance nesting: alliance name → parent alliance name (first wins,
    # a compound node can only have one Cytoscape parent).
    alliance_parent: dict[str, str] = {}
    for a in alliances:
        for m in a.get("members", []):
            if m.get("type") == "alliance" and m["name"] not in alliance_parent:
                alliance_parent[m["name"]] = a["name"]

    alliance_names: set[str] = {a["name"] for a in alliances}

    # entity_alliances: entity_name → [(alliance_name, priority), ...] sorted
    # priority-desc so index 0 is the PRIMARY (highest-priority) alliance.
    # Entities can belong to multiple alliances; the primary gets a solid node,
    # secondary alliances get a semi-transparent "shadow" duplicate node so
    # every alliance shows its members even when they're shared.
    entity_alliances: dict[str, list[tuple[str, int]]] = {}
    for a in alliances:
        apri = int(a.get("priority", 5))
        for m in a.get("members", []):
            if m.get("type") != "alliance":
                mname = m["name"]
                entity_alliances.setdefault(mname, []).append((a["name"], apri))
    for mname in entity_alliances:
        entity_alliances[mname].sort(key=lambda x: (-x[1], x[0].lower()))

    # primary alliance per entity (highest priority, alpha tiebreaker)
    member_primary: dict[str, str] = {
        mname: alist[0][0] for mname, alist in entity_alliances.items()
    }
    # entity name → type string (needed when building name_to_id later)
    member_type: dict[str, str] = {}
    for a in alliances:
        for m in a.get("members", []):
            if m.get("type") != "alliance":
                member_type.setdefault(m["name"], m.get("type", "npc"))

    # ── Elements list ──────────────────────────────────────────────────────────
    elements: list[dict] = []

    # Alliance compound nodes
    for a in alliances:
        node: dict = {
            "data": {
                "id":    _cid("a", a["name"]),
                "label": f'★ {a["name"]}',
                "etype": "alliance",
                "name":  a["name"],
            }
        }
        if a["name"] in alliance_parent:
            node["data"]["parent"] = _cid("a", alliance_parent[a["name"]])
        elements.append(node)

    # Member nodes: one primary node (solid) + one shadow node per secondary alliance.
    # Shadow nodes appear inside the secondary alliance's compound box, giving a
    # visual "this entity also belongs here" indicator even for shared members.
    for a in alliances:
        for m in a.get("members", []):
            if m.get("type") == "alliance":
                continue
            mname = m["name"]
            mtype = m.get("type", "npc")
            is_primary = member_primary.get(mname) == a["name"]

            if is_primary:
                node_id = _cid(mtype[0], mname)
                node_data: dict = {
                    "id": node_id, "label": mname,
                    "etype": mtype, "name": mname,
                    "parent": _cid("a", a["name"]),
                }
            else:
                # Unique ID per (entity, secondary-alliance) pair
                node_id = f"{_cid(mtype[0], mname)}_sh_{_cid('a', a['name'])}"
                node_data = {
                    "id": node_id, "label": mname,
                    "etype": mtype, "name": mname,
                    "parent": _cid("a", a["name"]),
                    "shadow": True,
                }
            elements.append({"data": node_data})

            # Dashed "also a member" edge from primary → shadow so the
            # connection between instances is visible on the graph.
            if not is_primary:
                primary_id = _cid(mtype[0], mname)
                elements.append({
                    "data": {
                        "id":         f"same_{node_id}",
                        "source":     primary_id,
                        "target":     node_id,
                        "label":      "also member",
                        "color":      "#AAAAAA",
                        "sameEntity": True,
                    }
                })

    # Standalone nodes: entities not inside any alliance at all
    member_names: set[str] = set(entity_alliances.keys())

    for n in npc_list:
        nm = n.get("name", "")
        if nm and nm not in member_names and nm not in alliance_names:
            elements.append({
                "data": {
                    "id": _cid("n", nm), "label": nm, "etype": "npc",
                    "name": nm, "importance": n.get("importance", "Minor NPC"),
                }
            })
    for f in factions:
        nm = f.get("name", "")
        if nm and nm not in member_names and nm not in alliance_names:
            elements.append({"data": {"id": _cid("f", nm), "label": nm, "etype": "faction", "name": nm}})
    for faith in faiths:
        nm = faith.get("name", "")
        if nm and nm not in member_names and nm not in alliance_names:
            elements.append({"data": {"id": _cid("r", nm), "label": nm, "etype": "faith", "name": nm}})

    # ── Name → Cytoscape ID lookup ────────────────────────────────────────────
    # Relationship edges always target PRIMARY nodes so the connection is clear.
    name_to_id: dict[str, str] = {}
    for a in alliances:
        name_to_id[a["name"]] = _cid("a", a["name"])
    for mname, mtype in member_type.items():
        name_to_id[mname] = _cid(mtype[0], mname)   # primary node ID
    for n in npc_list:
        nm = n.get("name", "")
        if nm and nm not in name_to_id:
            name_to_id[nm] = _cid("n", nm)
    for f in factions:
        nm = f.get("name", "")
        if nm and nm not in name_to_id:
            name_to_id[nm] = _cid("f", nm)
    for faith in faiths:
        nm = faith.get("name", "")
        if nm and nm not in name_to_id:
            name_to_id[nm] = _cid("r", nm)

    # ── Relationship edges ────────────────────────────────────────────────────
    for i, rel in enumerate(rel_web):
        ea    = rel.get("entity_a", "")
        eb    = rel.get("entity_b", "")
        rtype = rel.get("rel_type", "")
        src   = name_to_id.get(ea)
        tgt   = name_to_id.get(eb)
        if not src or not tgt:
            continue
        # Alliance-to-alliance Ally edges get a shorter spring so the physics
        # pulls the two compound boxes together until they overlap.
        is_aa_ally = (ea in alliance_names and eb in alliance_names and rtype == "Ally")
        elements.append({
            "data": {
                "id":       f"e{i}",
                "source":   src,
                "target":   tgt,
                "label":    rtype,
                "color":    _EDGE_COLOURS.get(rtype, _DEFAULT_EDGE),
                "aaAlly":   is_aa_ally,
            }
        })

    elements_json = _json.dumps(elements, ensure_ascii=False)

    # Per-importance NPC colour overrides injected as style objects
    npc_imp_styles = ",\n".join(
        f'{{ selector: \'node[etype="npc"][importance="{imp}"]\', '
        f'style: {{ "background-color": "{col}" }} }}'
        for imp, col in _NPC_COLOURS.items()
    )

    # Load Cytoscape.js from local disk (downloaded once); CDN fallback if unavailable.
    cyto_script = _cytoscape_tag()

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{cyto_script}
<style>
  body, html {{ margin:0; padding:0; background:transparent; overflow:hidden; height:100%; }}
  #cy {{ width:100%; height:100%; background:#f8f8f8; border-radius:6px; }}
  #hint {{ position:absolute; bottom:6px; right:8px; font:11px Arial,sans-serif;
           color:#888; background:rgba(255,255,255,.7); padding:2px 6px; border-radius:4px; }}
</style>
</head>
<body>
<div id="cy"></div>
<div id="hint">scroll to zoom · drag to pan · drag nodes to reposition</div>
<script>
(function() {{
var elements = {elements_json};

var cy = cytoscape({{
  container: document.getElementById('cy'),
  elements: elements,

  style: [
    // ── Default node ──────────────────────────────────────────────────────────
    {{ selector: 'node',
       style: {{ 'label': 'data(label)', 'text-valign': 'center', 'text-halign': 'center',
                 'font-family': 'Arial,sans-serif', 'font-size': '11px', 'color': '#222',
                 'text-wrap': 'wrap', 'text-max-width': '90px' }} }},

    // ── Alliance compound ─────────────────────────────────────────────────────
    // text-margin-y negative → label floats above the top border (not merged into it).
    // compound-sizing-wrt-labels:'include' tells the layout engine to reserve that
    // space so the label is never covered by a neighbour.
    {{ selector: 'node[etype="alliance"]',
       style: {{ 'background-color': '{_ALLIANCE_FILL}', 'background-opacity': 0.75,
                 'border-color': '{_ALLIANCE_BORDER}', 'border-width': 3,
                 'font-size': '12px', 'font-weight': 'bold',
                 'text-valign': 'top', 'text-halign': 'center',
                 'text-margin-y': -14,
                 'compound-sizing-wrt-labels': 'include',
                 'shape': 'roundrectangle', 'padding': '10px',
                 'min-width': '80px', 'min-height': '40px' }} }},

    // ── Faction (rectangle) ───────────────────────────────────────────────────
    {{ selector: 'node[etype="faction"]',
       style: {{ 'background-color': '{_FACTION_COLOUR}', 'shape': 'rectangle',
                 'border-color': '#5DADE2', 'border-width': 1.5,
                 'width': 90, 'height': 38 }} }},

    // ── NPC (ellipse) ─────────────────────────────────────────────────────────
    {{ selector: 'node[etype="npc"]',
       style: {{ 'background-color': '{_UNKNOWN_COLOUR}', 'shape': 'ellipse',
                 'border-color': '#7F8C8D', 'border-width': 1,
                 'width': 85, 'height': 38 }} }},

    // Per-importance NPC colours
    {npc_imp_styles},

    // ── Faith (diamond) ───────────────────────────────────────────────────────
    {{ selector: 'node[etype="faith"]',
       style: {{ 'background-color': '{_FAITH_COLOUR}', 'shape': 'diamond',
                 'border-color': '#A569BD', 'border-width': 1.5,
                 'width': 85, 'height': 52 }} }},

    // ── Shadow node (entity present in multiple alliances) ───────────────────
    {{ selector: 'node[?shadow]',
       style: {{ 'opacity': 0.5, 'border-style': 'dashed', 'border-width': 2 }} }},

    // ── Edges ─────────────────────────────────────────────────────────────────
    {{ selector: 'edge',
       style: {{ 'label': 'data(label)', 'curve-style': 'bezier',
                 'line-color': 'data(color)',
                 'target-arrow-color': 'data(color)', 'target-arrow-shape': 'triangle',
                 'source-arrow-color': 'data(color)', 'source-arrow-shape': 'triangle',
                 'arrow-scale': 0.7, 'width': 2,
                 'font-size': '9px', 'font-family': 'Arial,sans-serif', 'color': '#444',
                 'text-rotation': 'autorotate', 'text-margin-y': -8,
                 'text-background-color': '#fff', 'text-background-opacity': 0.75,
                 'text-background-padding': '2px' }} }},

    // ── Same-entity dashed link (primary → shadow duplicate) ──────────────────
    {{ selector: 'edge[?sameEntity]',
       style: {{ 'line-style': 'dashed', 'line-color': '#AAAAAA',
                 'width': 1.5, 'opacity': 0.65,
                 'target-arrow-shape': 'none', 'source-arrow-shape': 'none',
                 'font-size': '8px', 'color': '#AAAAAA',
                 'text-background-opacity': 0 }} }},
  ],

}});

cy.userZoomingEnabled(true);
cy.userPanningEnabled(true);
cy.minZoom(0.15);
cy.maxZoom(4);

// ── Persistent layout: save/restore positions via localStorage ───────────────
var LAYOUT_KEY = 'cy_pos_' + {_json.dumps(campaign_slug)};
var DO_RESET   = {_json.dumps(reset_layout)};

// After layout, push any standalone node that landed inside a compound box
// outward to the nearest edge of that box, preventing visual false-membership.
function pushOutOfCompounds() {{
    var compounds  = cy.nodes(':parent');
    var standalone = cy.nodes(':childless').filter(function(n) {{ return !n.data('parent'); }});
    standalone.forEach(function(node) {{
        var pos = {{ x: node.position('x'), y: node.position('y') }};
        var changed = true, iters = 8;
        while (changed && iters-- > 0) {{
            changed = false;
            compounds.forEach(function(cpd) {{
                var bb  = cpd.boundingBox({{ includeLabels: false, includeOverlays: false }});
                var pad = 40;
                if (pos.x > bb.x1 - pad && pos.x < bb.x2 + pad &&
                    pos.y > bb.y1 - pad && pos.y < bb.y2 + pad) {{
                    var dl = pos.x - (bb.x1 - pad);
                    var dr = (bb.x2 + pad) - pos.x;
                    var du = pos.y - (bb.y1 - pad);
                    var dd = (bb.y2 + pad) - pos.y;
                    var mn = Math.min(dl, dr, du, dd);
                    if      (mn === dl) pos.x = bb.x1 - pad - 15;
                    else if (mn === dr) pos.x = bb.x2 + pad + 15;
                    else if (mn === du) pos.y = bb.y1 - pad - 15;
                    else                pos.y = bb.y2 + pad + 15;
                    changed = true;
                }}
            }});
        }}
        node.position(pos);
    }});
}}

// Serialize all node positions to localStorage so reruns restore the same layout.
function savePositions() {{
    var pos = {{}};
    cy.nodes().forEach(function(n) {{
        pos[n.id()] = {{ x: n.position('x'), y: n.position('y') }};
    }});
    try {{ localStorage.setItem(LAYOUT_KEY, JSON.stringify(pos)); }} catch(e) {{}}
}}

// Run a fresh CoSE layout, then post-process and save.
function runLayout() {{
    var layout = cy.layout({{
        name: 'cose',
        animate: false,
        randomize: true,
        // Higher repulsion + zero nodeOverlap keeps compounds separate.
        // Higher gravity + smaller componentSpacing prevents scatter to corners.
        nodeRepulsion: function() {{ return 120000; }},
        nodeOverlap:   0,
        idealEdgeLength: function() {{ return 80; }},
        edgeElasticity:  function() {{ return 150; }},
        nestingFactor:   1,
        gravity:         80,
        numIter:         400,
        initialTemp:     200,
        coolingFactor:   0.95,
        minTemp:         1.0,
        componentSpacing: 50,
    }});
    cy.one('layoutstop', function() {{
        pushOutOfCompounds();
        savePositions();
        cy.fit(undefined, 30);
    }});
    layout.run();
}}

// Restore saved positions if they cover all current nodes; otherwise run fresh layout.
// This prevents the map from re-randomising on every rerun.
var savedRaw = null;
try {{ savedRaw = DO_RESET ? null : localStorage.getItem(LAYOUT_KEY); }} catch(e) {{}}
var usedSaved = false;
if (savedRaw) {{
    try {{
        var saved = JSON.parse(savedRaw);
        var allCovered = cy.nodes().every(function(n) {{ return saved[n.id()] !== undefined; }});
        if (allCovered && cy.nodes().length > 0) {{
            cy.nodes().forEach(function(n) {{
                var p = saved[n.id()];
                if (p) n.position(p);
            }});
            cy.fit(undefined, 30);
            usedSaved = true;
        }}
    }} catch(e) {{}}
}}
if (!usedSaved) {{
    if (DO_RESET) {{ try {{ localStorage.removeItem(LAYOUT_KEY); }} catch(e) {{}} }}
    runLayout();
}}

// Auto-save whenever the user manually repositions a node.
cy.on('dragfree', 'node', savePositions);
}})();
</script>
</body>
</html>"""


# ── Page ──────────────────────────────────────────────────────────────────────

_migrate_from_npcs()   # run once; no-op if relationship_web.json already exists

st.title("Relationship Map")
st.caption(
    "Create and visualise connections between NPCs, factions, faiths, and alliances. "
    "Alliances (from the Factions page) appear as cluster nodes that group their members."
)

campaigns = load_campaigns()
if not campaigns:
    no_campaigns_notice()
    st.stop()

if "rel_web_data" not in st.session_state:
    st.session_state.rel_web_data = _load_rel_web()

# ── Campaign selector ─────────────────────────────────────────────────────────
camp_names    = [c["name"] for c in campaigns]
selected_camp = st.selectbox("Campaign", camp_names)

# Load entity sources for this campaign — cached by file mtime so reads are
# skipped when the source files haven't changed since the last render.
_factions_mt = FACTIONS_PATH.stat().st_mtime if FACTIONS_PATH.exists() else 0
_npcs_mt     = NPCS_PATH.stat().st_mtime     if NPCS_PATH.exists()     else 0
_faiths_mt   = FAITHS_PATH.stat().st_mtime   if FAITHS_PATH.exists()   else 0
factions, alliances = _factions_camp(selected_camp, _factions_mt)
npc_list            = _npc_list_camp(selected_camp, _npcs_mt)
faiths              = _faith_list_camp(selected_camp, _faiths_mt)

# Ensure campaign key exists
if selected_camp not in st.session_state.rel_web_data:
    st.session_state.rel_web_data[selected_camp] = []

rel_web      = st.session_state.rel_web_data[selected_camp]
entity_labels = _entity_labels(npc_list, factions, faiths, alliances)
alliance_names = {a["name"] for a in alliances}


# ═══════════════════════════════════════════════════════════════════════
# SECTION 1 — Relationship Creator (at the top)
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Relationship Web")

# ── Add relationship form ─────────────────────────────────────────────────────
# Entity A and B are searchable/scrollable selectboxes — type to filter,
# scroll to browse. Entities are ordered: ★ alliances → □ factions →
# ◇ faiths → ○ NPCs, each group sorted priority-desc then alpha.
if not entity_labels:
    st.info(
        "No entities found for this campaign. "
        "Add NPCs on the NPCs page, factions on the Factions page, or faiths on the Faiths page first."
    )
else:
    with st.form(f"add_rel_{selected_camp}", clear_on_submit=True):
        rf1, rf2, rf3 = st.columns([2.5, 1.5, 2.5])

        # Index-based selectbox so identical names across types are always unique
        a_idx = rf1.selectbox(
            "Entity A",
            range(len(entity_labels)),
            format_func=lambda i: entity_labels[i][0],
        )
        rel_type = rf2.selectbox("Relationship", REL_TYPES)
        b_idx = rf3.selectbox(
            "Entity B",
            range(len(entity_labels)),
            format_func=lambda i: entity_labels[i][0],
            index=min(1, len(entity_labels) - 1),  # default to second entry so A ≠ B
        )

        rel_notes = st.text_area("Notes (optional)", placeholder="Context, history, tensions.", height=60)

        if st.form_submit_button("Add Relationship"):
            ea = entity_labels[a_idx][1]
            eb = entity_labels[b_idx][1]
            if ea != eb:
                # Auto-assign so the higher-priority entity always lands in slot A,
                # regardless of which dropdown the user picked it from — _auto_assign
                # was previously defined but never called, so this never actually ran.
                ea, eb = _auto_assign(ea, eb, npc_list, factions, faiths, alliances)
                st.session_state.rel_web_data[selected_camp].append({
                    "entity_a": ea, "rel_type": rel_type,
                    "entity_b": eb, "notes":    rel_notes.strip(),
                })
                _save_rel_web(st.session_state.rel_web_data)
                st.success(f"Added: {ea} ↔ {eb}")
            else:
                st.error("Entity A and B must be different.")

# ── Relationship list ─────────────────────────────────────────────────────────
rel_web = st.session_state.rel_web_data.get(selected_camp, [])

def _disp(name: str) -> str:
    """Add ★ prefix when displaying alliance names in the list."""
    return f"★ {name}" if name in alliance_names else name

if rel_web:
    rh1, rh2, rh3, rh4 = st.columns([2.5, 1.5, 2.5, 0.6])
    rh1.markdown("**Entity A**"); rh2.markdown("**Relationship**"); rh3.markdown("**Entity B**")

    indexed = sorted(
        enumerate(rel_web),
        key=lambda ir: (ir[1].get("entity_a","").lower(), ir[1].get("entity_b","").lower()),
    )
    for ri, rel in indexed:
        rc1, rc2, rc3, rc4 = st.columns([2.5, 1.5, 2.5, 0.6])
        rc1.write(_disp(rel.get("entity_a", "")))
        rc2.write(rel.get("rel_type", ""))
        rc3.write(_disp(rel.get("entity_b", "")))

        with rc4.popover("✏"):
            with st.form(f"edit_rel_{selected_camp}_{ri}"):
                er1, er2, er3 = st.columns([2, 1.5, 2])
                new_ea = er1.text_input("Entity A", value=rel.get("entity_a", ""))
                new_rt = er2.selectbox(
                    "Relationship", REL_TYPES,
                    index=REL_TYPES.index(rel.get("rel_type", REL_TYPES[0]))
                          if rel.get("rel_type") in REL_TYPES else 0,
                )
                new_eb     = er3.text_input("Entity B", value=rel.get("entity_b", ""))
                new_notes  = st.text_area("Notes", value=rel.get("notes", ""), height=60)
                eb1, eb2   = st.columns([4, 1])
                if eb1.form_submit_button("Save"):
                    st.session_state.rel_web_data[selected_camp][ri] = {
                        "entity_a": new_ea.strip() or rel["entity_a"],
                        "rel_type": new_rt,
                        "entity_b": new_eb.strip() or rel["entity_b"],
                        "notes":    new_notes.strip(),
                    }
                    _save_rel_web(st.session_state.rel_web_data)
                    st.rerun()
                if eb2.form_submit_button("Delete"):
                    st.session_state.rel_web_data[selected_camp].pop(ri)
                    _save_rel_web(st.session_state.rel_web_data)
                    st.rerun()

        if rel.get("notes"):
            _, nc, _, _ = st.columns([2.5, 4, 0.6, 0.6])
            nc.caption(f"↳ {rel['notes']}")
else:
    st.caption("No relationships yet. Add one above.")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 2 — Visual Graph
# ═══════════════════════════════════════════════════════════════════════

st.markdown("### Visual Map")

# ── Display controls ──────────────────────────────────────────────────────────
# Pre-seed session_state from saved prefs so widgets remember their last values.
get_pref("rm_show_legend",   True)
get_pref("rm_show_all",      False)
get_pref("rm_graph_height",  650)
dc1, dc2, dc3, dc4 = st.columns([1, 1.5, 1, 0.8])
show_legend       = dc1.checkbox("Show Legend", key="rm_show_legend")
show_all_entities = dc2.checkbox(
    "Show All Entities (Even Without Connections)", key="rm_show_all",
    help="When off, only entities that appear in at least one relationship are rendered.",
)
graph_height = dc3.slider("Graph Height", min_value=300, max_value=1200, step=50, key="rm_graph_height")
# Persist any changes the user made to these controls.
save_prefs({"rm_show_legend": st.session_state.rm_show_legend,
            "rm_show_all":    st.session_state.rm_show_all,
            "rm_graph_height": st.session_state.rm_graph_height})
# Reset clears localStorage positions so the auto-layout re-runs from scratch.
if dc4.button("Reset Layout", help="Clear saved node positions and re-run automatic layout."):
    st.session_state[f"map_reset_{selected_camp}"] = True
    st.rerun()

# Build display lists — optionally filter to only connected entities
rel_web = st.session_state.rel_web_data.get(selected_camp, [])
if show_all_entities:
    vis_npcs      = npc_list
    vis_factions  = factions
    vis_faiths    = faiths
    vis_alliances = alliances
else:
    connected: set[str] = set()
    for rel in rel_web:
        connected.add(rel["entity_a"])
        connected.add(rel["entity_b"])
    # Pull in entire alliances (and their members) when any member or the
    # alliance itself is referenced in the web
    for a in alliances:
        if a["name"] in connected or any(m["name"] in connected for m in a.get("members", [])):
            connected.add(a["name"])
            for m in a.get("members", []):
                connected.add(m["name"])
    vis_npcs      = [n for n in npc_list  if n.get("name") in connected]
    vis_factions  = [f for f in factions  if f.get("name") in connected]
    vis_faiths    = [f for f in faiths    if f.get("name") in connected]
    vis_alliances = [a for a in alliances if a["name"] in connected]

# ── Graph (Cytoscape.js) ──────────────────────────────────────────────────────
if vis_npcs or vis_factions or vis_faiths or vis_alliances or rel_web:
    do_reset  = st.session_state.get(f"map_reset_{selected_camp}", False)
    camp_slug = re.sub(r'[^a-zA-Z0-9]', '_', selected_camp)
    # Height is NOT passed to the HTML builder — it uses height:100% in CSS so
    # the slider can change the iframe viewport without busting the HTML cache.
    # When inputs are unchanged, @st.cache_data returns the same string →
    # Streamlit keeps the same iframe instance → browser positions are preserved.
    html = _build_cytoscape_html(
        vis_npcs, vis_factions, vis_faiths, vis_alliances, rel_web,
        reset_layout=do_reset,
        campaign_slug=camp_slug,
    )
    st.iframe(html, height=graph_height + 4)
    # Clear the reset flag so the next rerun uses saved positions again.
    if do_reset:
        st.session_state[f"map_reset_{selected_camp}"] = False
else:
    st.info(
        "No data to display. Add some relationships above, or enable "
        '"Show all entities" to display everything.'
    )

# ── Legend ────────────────────────────────────────────────────────────────────
if show_legend:
    leg1, leg2 = st.columns(2)
    with leg1:
        st.caption("**Node type**")
        for label, colour in [
            ("★ Alliance (compound box)", _ALLIANCE_BORDER),
            ("□ Faction",                 _FACTION_COLOUR),
            ("◇ Faith",                   _FAITH_COLOUR),
            ("○ NPC",                     "#BDC3C7"),
        ]:
            st.markdown(
                f"<span style='color:{colour};font-size:1.2em'>■</span>&nbsp;{label}",
                unsafe_allow_html=True,
            )
    with leg2:
        st.caption("**Relationship type**")
        for rtype, colour in _EDGE_COLOURS.items():
            st.markdown(
                f"<span style='color:{colour};font-size:1.2em'>—</span>&nbsp;{rtype}",
                unsafe_allow_html=True,
            )
