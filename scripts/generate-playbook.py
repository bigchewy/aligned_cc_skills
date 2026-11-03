#!/usr/bin/env python3
"""Build the playbook pages from skills/playbook/layers.yaml and the framework registry.

Steps: load -> validate -> render -> write. A data error stops the build before
anything is written: the script prints one ERROR line per problem to stderr and
exits 1.

A run writes skills/playbook/pages/: index.html (the I / We / It map),
style.css, and frameworks/<id>.html for every placed framework. --check builds
in memory, compares with what is on disk, and writes nothing. --report prints
the frameworks in two or more areas and the required documents that come from
outside. The build writes no timestamps, so the same input gives the same bytes.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LAYERS_FILE = ROOT / "skills" / "playbook" / "layers.yaml"
FRAMEWORKS_FILE = ROOT / "frameworks" / "registry.yaml"
ADVISORS_FILE = ROOT / "advisors" / "registry.yaml"
PAGES_DIR = ROOT / "skills" / "playbook" / "pages"
TEMPLATES = ROOT / "scripts" / "playbook-templates"
ORG_CHART_STYLE = ROOT / "scripts" / "org-chart-templates" / "style.css"

# The org chart generator owns the text helpers (escaping, dashes, sentences,
# template filling). The playbook uses the same ones so both sites read alike.
_oc_spec = importlib.util.spec_from_file_location(
    "generate_org_chart", ROOT / "scripts" / "generate-org-chart.py"
)
_oc = importlib.util.module_from_spec(_oc_spec)
_oc_spec.loader.exec_module(_oc)
text, sentence, framework_name, fill = _oc.text, _oc.sentence, _oc.framework_name, _oc.fill


def _read_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _homes(layers):
    """Map each framework id to the (layer_id, area_id) pairs it sits in, in file order."""
    homes = {}
    for layer in layers.get("layers") or []:
        for area in layer.get("areas") or []:
            for fid in area.get("frameworks") or []:
                homes.setdefault(fid, []).append((layer.get("id"), area.get("id")))
    return homes


def check_layers(layers, registry):
    """Check the layers file against the registry. Return a list of ERROR strings.

    registry is the parsed registry file: {"frameworks": [{"id": ...}, ...]}.
    """
    known = {f["id"] for f in registry.get("frameworks") or []}
    held = [h["id"] for h in layers.get("holding") or []]
    errors = []

    seen_areas = set()
    placed = set()
    for layer in layers.get("layers") or []:
        for area in layer.get("areas") or []:
            aid = area.get("id")
            if aid in seen_areas:
                errors.append(f"ERROR: area id '{aid}' is used twice")
            seen_areas.add(aid)

            members = area.get("frameworks") or []
            seen_members = set()
            for fid in members:
                if fid not in known:
                    errors.append(f"ERROR: unknown framework '{fid}' in area '{aid}'")
                if fid in seen_members:
                    errors.append(f"ERROR: framework '{fid}' is in area '{aid}' twice")
                seen_members.add(fid)
            placed |= seen_members

            start = area.get("start")
            if not start:
                errors.append(f"ERROR: area '{aid}' has no start")
            elif start not in members:
                errors.append(f"ERROR: start '{start}' is not in the frameworks of area '{aid}'")

    for fid in held:
        if fid not in known:
            errors.append(f"ERROR: unknown framework '{fid}' in holding")
        if fid in placed:
            errors.append(f"ERROR: '{fid}' is both in an area and in holding")

    for fid in sorted(known):
        if fid not in placed and fid not in held:
            errors.append(f"ERROR: unplaced framework '{fid}'")

    return errors


DOC_KINDS = (("required_documents", "required"), ("helpful_documents", "helpful"))
OUTSIDE = "outside"


def _is_link(entry):
    """True when a document entry is a plain name or a {doc, from} mapping with the right types."""
    if isinstance(entry, str):
        return bool(entry)
    if not isinstance(entry, dict) or set(entry) != {"doc", "from"}:
        return False
    if not isinstance(entry["doc"], str) or not entry["doc"]:
        return False
    src = entry["from"]
    if isinstance(src, str):
        return bool(src)
    # A list names several writing frameworks; 'outside' stands alone, never inside a list.
    return (
        isinstance(src, list)
        and bool(src)
        and all(isinstance(s, str) and s and s != OUTSIDE for s in src)
    )


def doc_links(entry):
    """List one framework's document links, required first, in file order.

    Each link is {"doc": str, "from": list[str], "kind": "required" | "helpful"}.
    A plain-string entry (allowed in project-local registries) reads as from: ["outside"].
    Malformed entries are skipped here; check_links reports them.
    """
    links = []
    for key, kind in DOC_KINDS:
        for item in entry.get(key) or []:
            if not _is_link(item):
                continue
            if isinstance(item, str):
                links.append({"doc": item, "from": [OUTSIDE], "kind": kind})
                continue
            src = item["from"]
            links.append({"doc": item["doc"], "from": [src] if isinstance(src, str) else list(src), "kind": kind})
    return links


def _required_loops(frameworks):
    """Find each loop made only of required links. Return a list of [(fid, doc, writer), ...] paths."""
    edges = {}
    for f in frameworks:
        for link in doc_links(f):
            if link["kind"] != "required":
                continue
            for writer in link["from"]:
                if writer != OUTSIDE and writer != f["id"]:
                    edges.setdefault(f["id"], []).append((link["doc"], writer))

    loops, seen = [], set()

    def walk(start, node, path, on_path):
        for doc, writer in edges.get(node, []):
            step = path + [(node, doc, writer)]
            if writer == start:
                key = frozenset(step)
                if key not in seen:
                    seen.add(key)
                    loops.append(step)
            elif writer not in on_path and writer > start:
                walk(start, writer, step, on_path | {writer})

    for start in sorted(edges):
        walk(start, start, [], {start})
    return loops


def check_links(registry):
    """Check every document link in the registry. Return a list of ERROR strings.

    registry is the parsed registry file: {"frameworks": [{"id": ...}, ...]}.
    Checks: each entry is a name or {doc, from}; every from is a known id or
    'outside'; no framework names itself; no loop made only of required links;
    a framework with a market that writes for others feeds at least one
    framework of the same market or of no market.
    """
    frameworks = registry.get("frameworks") or []
    known = {f["id"] for f in frameworks}
    market = {f["id"]: f.get("market") for f in frameworks}
    errors = []
    readers = {}  # writer id -> [(reader id, doc)]

    for f in frameworks:
        fid = f["id"]
        for key, _ in DOC_KINDS:
            for item in f.get(key) or []:
                if not _is_link(item):
                    errors.append(
                        f"ERROR: '{fid}' has a {key} entry that is neither a name nor "
                        f"a mapping with doc and from (a from list holds framework ids only, "
                        f"never 'outside'): {item!r}"
                    )
        for link in doc_links(f):
            for writer in link["from"]:
                if writer == OUTSIDE:
                    continue
                if writer == fid:
                    errors.append(f"ERROR: '{fid}' document '{link['doc']}' has from '{writer}', which is itself")
                elif writer not in known:
                    errors.append(f"ERROR: '{fid}' document '{link['doc']}' has unknown from '{writer}'")
                else:
                    readers.setdefault(writer, []).append((fid, link["doc"]))

    for loop in _required_loops(frameworks):
        steps = " -> ".join(f"'{fid}' needs '{doc}' from '{writer}'" for fid, doc, writer in loop)
        errors.append(f"ERROR: required loop: {steps}")

    for writer, fed in readers.items():
        m = market.get(writer)
        if not m:
            continue
        if any(market.get(reader) in (None, m) for reader, _ in fed):
            continue
        pairs = ", ".join(f"'{doc}' for '{reader}' ({market.get(reader)})" for reader, doc in fed)
        errors.append(
            f"ERROR: '{writer}' has market {m} but writes only for frameworks of another market: {pairs}"
        )

    return errors


def outside_required(registry):
    """List (framework id, doc) for every required document whose from is only 'outside'."""
    out = []
    for f in registry.get("frameworks") or []:
        for link in doc_links(f):
            if link["kind"] == "required" and link["from"] == [OUTSIDE]:
                out.append((f["id"], link["doc"]))
    return out


def check_advisors(registry, advisors):
    """Every framework that names an advisor names one in the advisor registry."""
    return [
        f"ERROR: '{f['id']}' has unknown advisor '{f['advisor']}'"
        for f in registry.get("frameworks") or []
        if f.get("advisor") and f["advisor"] not in advisors
    ]


def load_and_validate(layers_path, frameworks_path, advisors_path=ADVISORS_FILE):
    """Load the layers file and the registries. Return (data, errors)."""
    layers = _read_yaml(layers_path)
    registry = _read_yaml(frameworks_path)
    advisors = {a["id"]: a for a in _read_yaml(advisors_path).get("advisors") or []}
    errors = check_layers(layers, registry) + check_links(registry) + check_advisors(registry, advisors)
    data = {
        "layers": layers,
        "frameworks": {f["id"]: f for f in registry.get("frameworks") or []},
        "homes": _homes(layers),
        "advisors": advisors,
    }
    return data, errors


# ---------------------------------------------------------------- upstream graph

IT = "it"


def in_it(fid, data):
    """A framework counts as It when any of its homes is in the It layer."""
    return any(layer == IT for layer, _ in data["homes"].get(fid, []))


def upstream_edges(fid, data):
    """Every (writer, reader, kind) edge upstream of fid, in the order found.

    Empty unless fid sits in It: no arrow points into a We or I framework. The
    walk continues from a writer only when that writer is in It, so a We or I
    writer shows as a leaf. Each writer and reader pair appears once; when a
    writer feeds a reader both a required and a helpful document, the edge is
    required. 'outside' is never a node. A loop ends when it reaches a
    framework already walked.
    """
    if not in_it(fid, data):
        return []
    frameworks = data["frameworks"]
    edges = {}  # (writer, reader) -> kind, in insertion order
    queue, walked = [fid], {fid}
    while queue:
        reader = queue.pop(0)
        for link in doc_links(frameworks[reader]):
            for writer in link["from"]:
                if writer == OUTSIDE or writer == reader or writer not in frameworks:
                    continue
                pair = (writer, reader)
                if pair not in edges or link["kind"] == "required":
                    edges[pair] = link["kind"] if pair not in edges else "required"
                if writer not in walked and in_it(writer, data):
                    walked.add(writer)
                    queue.append(writer)
    return [(w, r, kind) for (w, r), kind in edges.items()]


# ---------------------------------------------------------------- render

STAGES = ("idea", "pilot", "nail-it", "scale-it", "milk-it")
STAGE_LABEL = {"idea": "Idea", "pilot": "Pilot", "nail-it": "Nail it", "scale-it": "Scale it", "milk-it": "Milk it"}
MARKETS = ("b2b", "b2c")
MARKET_LABEL = {"b2b": "B2B", "b2c": "B2C"}
CLOSING = "Put the result into your Top Goal or your next check-in."
TOKENS_END = "/* B2B and B2C switch */"


def _template(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def stylesheet():
    """The org chart's tokens and base type, then the playbook's own rules."""
    org = ORG_CHART_STYLE.read_text(encoding="utf-8")
    if TOKENS_END not in org:
        raise ValueError(f"{ORG_CHART_STYLE} no longer has the line {TOKENS_END!r}")
    base = org.split(TOKENS_END)[0].split("\n", 1)[1]
    head = "/* Playbook pages. Built by scripts/generate-playbook.py from the org chart's tokens\n   and scripts/playbook-templates/style.css; edit those, not this copy. */\n"
    return head + base + _template("style.css")


def name_of(fid, data):
    return framework_name(data["frameworks"][fid]["name"])


def area_lookup(data):
    """(layer_id, area_id) -> (layer, area)."""
    out = {}
    for layer in data["layers"].get("layers") or []:
        for area in layer.get("areas") or []:
            out[(layer["id"], area["id"])] = (layer, area)
    return out


def home_labels(fid, data):
    lookup = area_lookup(data)
    return [f"{lookup[h][0]['name']} · {lookup[h][1]['name']}" for h in data["homes"].get(fid, [])]


def chips(fw):
    stages = [s for s in STAGES if s in (fw.get("stages") or [])]
    out = [f'<span class="chip stage">{STAGE_LABEL[s]}</span>' for s in stages]
    if fw.get("market") in MARKETS:
        out.append(f'<span class="chip market">{MARKET_LABEL[fw["market"]]}</span>')
    return "".join(out)


def filter_group(kind, legend, any_label, options):
    radios = [f'<label><input type="radio" name="{kind}" value="" checked><span>{any_label}</span></label>']
    radios += [
        f'<label><input type="radio" name="{kind}" value="{value}"><span>{label}</span></label>'
        for value, label in options
    ]
    return (
        f'    <fieldset class="filter" data-filter="{kind}"><legend class="label">{legend}</legend>'
        + "".join(radios)
        + "</fieldset>"
    )


def map_item(fid, data, start):
    fw = data["frameworks"][fid]
    stages = " ".join(s for s in STAGES if s in (fw.get("stages") or []))
    market = fw.get("market") or ""
    attrs = f'class="item" data-stages="{stages}" data-market="{market}"' + (" data-start" if start else "")
    label = '<span class="start-label">Start here</span>' if start else ""
    tags = chips(fw)
    return (
        f"<li {attrs}>{label}"
        f'<a class="name" href="frameworks/{text(fid)}.html">{text(name_of(fid, data))}</a>'
        f'<p class="use">{sentence(fw.get("use_when", ""))}</p>'
        + (f'<span class="chips">{tags}</span>' if tags else "")
        + "</li>"
    )


def render_index(data):
    indent = "      "
    columns = []
    for layer in data["layers"].get("layers") or []:
        areas = []
        for area in layer.get("areas") or []:
            order = [area["start"]] + [f for f in area["frameworks"] if f != area["start"]]
            lis = "\n".join(indent + "    " + map_item(f, data, f == area["start"]) for f in order)
            areas.append(
                f'{indent}<section class="area" id="area-{text(area["id"])}">\n'
                f'{indent}  <h3>{text(area["name"])}</h3>\n'
                f'{indent}  <p class="note">{text(area.get("note", ""))}</p>\n'
                f'{indent}  <ul class="items">\n{lis}\n{indent}  </ul>\n'
                f"{indent}</section>"
            )
        columns.append(
            f'    <div class="layer" id="layer-{text(layer["id"])}">\n'
            f'      <div class="layer-head"><h2>{text(layer["name"])}</h2>'
            f'<p class="muted">{text(layer.get("does", ""))}</p></div>\n'
            + "\n".join(areas)
            + "\n    </div>"
        )
    filters = "\n".join([
        filter_group("stage", "Stage", "Any", [(s, STAGE_LABEL[s]) for s in STAGES]),
        filter_group("market", "Market", "Both", [(m, MARKET_LABEL[m]) for m in MARKETS]),
    ])
    return fill(_template("index.html"), filters=filters, columns="\n".join(columns))


def writer_link(writer, data):
    if writer not in data["frameworks"]:
        return text(writer)
    name = text(name_of(writer, data))
    if writer in data["homes"]:
        return f'<a href="{text(writer)}.html">{name}</a>'
    return name


def doc_section(title, links, data):
    if not links:
        return ""
    rows = []
    for link in links:
        if link["from"] == [OUTSIDE]:
            src = "from outside"
        else:
            src = "from " + " or ".join(writer_link(w, data) for w in link["from"])
        rows.append(f'      <li><span class="doc">{text(link["doc"])}</span><span class="from">{src}</span></li>')
    return f"  <section>\n    <h2>{title}</h2>\n    <ul class=\"docs\">\n" + "\n".join(rows) + "\n    </ul>\n  </section>"


# Graph geometry, in SVG units (1 unit = 1 CSS pixel at natural size).
# PAD_LEFT leaves room for the brackets that join two boxes in one column.
# BRACKET stays well short of COL_GAP / 2, where the forward lines bend, so a
# bracket never lies on top of a bend.
BOX_W, BOX_H, COL_GAP, ROW_GAP, PAD, PAD_LEFT, BRACKET = 150, 46, 52, 14, 10, 24, 13
LINE_CHARS = 19


def _wrap(name):
    """Split a name into at most two lines of about LINE_CHARS characters."""
    words, lines, line = name.split(), [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > LINE_CHARS:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    lines.append(line)
    if len(lines) > 2:
        second = " ".join(lines[1:])
        lines = [lines[0], second[: LINE_CHARS - 1].rstrip() + "…"]
    return lines


def _depths(fid, edges):
    """Steps from fid to each node, walking from reader to writer."""
    depth = {fid: 0}
    queue = [fid]
    while queue:
        node = queue.pop(0)
        for w, r, _ in edges:
            if r == node and w not in depth:
                depth[w] = depth[node] + 1
                queue.append(w)
    return depth


def render_graph(fid, edges, data):
    """Inline SVG: writers to the left, fid on the right, one column per step.

    A column is the number of steps from fid, so a writer is never more than
    one column left of its reader. Three kinds of line follow from that: one
    column left to right (most lines), a bracket on the left between two boxes
    in the same column, and a short line right to left where a loop turns back.
    """
    depth = _depths(fid, edges)
    cols = max(depth.values()) + 1
    by_col = {}
    for node in depth:  # insertion order is discovery order
        by_col.setdefault(depth[node], []).append(node)
    rows = max(len(v) for v in by_col.values())
    width = PAD_LEFT + PAD + cols * BOX_W + (cols - 1) * COL_GAP
    height = PAD * 2 + rows * BOX_H + (rows - 1) * ROW_GAP

    pos = {}
    for d, nodes in by_col.items():
        x = PAD_LEFT + (cols - 1 - d) * (BOX_W + COL_GAP)
        top = PAD + (rows - len(nodes)) * (BOX_H + ROW_GAP) / 2
        for i, node in enumerate(nodes):
            pos[node] = (x, top + i * (BOX_H + ROW_GAP))

    def n(v):
        return f"{v:g}"

    paths = []
    for w, r, kind in edges:
        wx, wy = pos[w]
        rx, ry = pos[r]
        y1, y2 = wy + BOX_H / 2, ry + BOX_H / 2
        if depth[w] > depth[r]:
            x1, x2 = wx + BOX_W, rx - 2
            mid = (x1 + x2) / 2
            d = f"M{n(x1)},{n(y1)} C{n(mid)},{n(y1)} {n(mid)},{n(y2)} {n(x2)},{n(y2)}"
        elif depth[w] == depth[r]:
            # Same column: a bracket out to the left of both boxes.
            x1, x2, out = wx, rx - 2, wx - BRACKET
            y1, y2 = y1 + 6, y2 - 6 if ry > wy else y2 + 6
            d = f"M{n(x1)},{n(y1)} C{n(out)},{n(y1)} {n(out)},{n(y2)} {n(x2)},{n(y2)}"
        else:
            # A loop turning back: from the writer's left side to the reader's right side.
            x1, x2 = wx, rx + BOX_W + 2
            mid = (x1 + x2) / 2
            y1, y2 = y1 + 8, y2 + 8
            d = f"M{n(x1)},{n(y1)} C{n(mid)},{n(y1)} {n(mid)},{n(y2)} {n(x2)},{n(y2)}"
        dash = ' stroke-dasharray="5 4"' if kind == "helpful" else ""
        paths.append(
            f'<path class="edge {kind}" d="{d}" fill="none" stroke="currentColor" '
            f'stroke-width="1.5"{dash} marker-end="url(#arrow)"/>'
        )

    boxes = []
    for node, (x, y) in pos.items():
        full = name_of(node, data)
        lines = _wrap(full)
        first = y + BOX_H / 2 - (len(lines) - 1) * 8 + 5
        tspans = "".join(
            f'<tspan x="{n(x + BOX_W / 2)}" y="{n(first + i * 16)}">{text(line)}</tspan>'
            for i, line in enumerate(lines)
        )
        cls = "node self" if node == fid else "node"
        # The title holds the full name, which a wrapped box may cut short.
        shape = (
            f"<g><title>{text(full)}</title>"
            f'<rect class="{cls}"x="{n(x)}" y="{n(y)}" width="{BOX_W}" height="{BOX_H}" rx="5" '
            f'fill="none" stroke="currentColor"/><text text-anchor="middle">{tspans}</text></g>'
        )
        if node != fid and node in data["homes"]:
            shape = f'<a href="{text(node)}.html">{shape}</a>'
        boxes.append(shape)

    title = f"What comes before {text(name_of(fid, data))}"
    return (
        f'<svg class="graph" width="{n(width)}" height="{n(height)}" viewBox="0 0 {n(width)} {n(height)}" '
        f'role="img" aria-label="{title}">'
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>'
        + "".join(paths)
        + "".join(boxes)
        + "</svg>"
    )


KEY = (
    '<ul class="key">'
    '<li><svg width="34" height="8" aria-hidden="true"><line x1="0" y1="4" x2="34" y2="4" stroke="currentColor" stroke-width="1.5"/></svg>Must have</li>'
    '<li><svg width="34" height="8" aria-hidden="true"><line x1="0" y1="4" x2="34" y2="4" stroke="currentColor" stroke-width="1.5" stroke-dasharray="5 4"/></svg>Helps to have</li>'
    "</ul>"
)


def render_framework(fid, data):
    fw = data["frameworks"][fid]
    links = doc_links(fw)
    homes = "".join(f"<span>{text(h)}</span>" for h in home_labels(fid, data))
    advisor = data["advisors"].get(fw.get("advisor"))
    who = f'<span class="by">{text(advisor["name"])}</span>' if advisor else ""
    stage_chips = chips(fw)
    tags = f'\n    <div class="chips">{stage_chips}</div>' if stage_chips else ""

    body = [
        doc_section("Must have", [l for l in links if l["kind"] == "required"], data),
        doc_section("Helps to have", [l for l in links if l["kind"] == "helpful"], data),
    ]
    edges = upstream_edges(fid, data)
    if edges:
        body.append(
            '  <section class="before">\n    <h2>What comes before it</h2>\n'
            f'    <div class="graph-box">{render_graph(fid, edges, data)}</div>\n'
            f"    {KEY}\n  </section>"
        )
    if in_it(fid, data):
        body.append(f'  <p class="closing">{CLOSING}</p>')

    return fill(
        _template("framework.html"),
        title=text(name_of(fid, data)),
        homes=homes,
        advisor=who,
        purpose=sentence(fw.get("purpose", "")),
        command=f'<div class="cmd"><code>/aligned:use-framework {text(fid)}</code>'
        '<button type="button" class="copy">Copy</button></div>',
        chips=tags,
        body="\n".join(b for b in body if b),
    )


def build(data):
    """Return {path relative to the pages dir: file text} for every shipped file."""
    files = {"style.css": stylesheet(), "index.html": render_index(data)}
    for fid in sorted(data["homes"]):
        files[f"frameworks/{fid}.html"] = render_framework(fid, data)
    return files


def report(data):
    """Frameworks in two or more areas, then required documents from outside."""
    two = [fid for fid, homes in data["homes"].items() if len(homes) > 1]
    lines = ["Frameworks in two or more areas:"]
    lines += [f"- {name_of(f, data)} ({f}): {'; '.join(home_labels(f, data))}" for f in two] or ["- none"]
    lines.append("")
    lines.append("Required documents from outside:")
    registry = {"frameworks": list(data["frameworks"].values())}
    outside = outside_required(registry)
    lines += [f"- {name_of(f, data)}: {doc}" for f, doc in outside] or ["- none"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- write and check

PAGE_SUFFIXES = (".html", ".css")


def _on_disk(out):
    """Every page file under out, as paths relative to out (posix strings)."""
    if not out.is_dir():
        return set()
    return {
        p.relative_to(out).as_posix()
        for p in out.rglob("*")
        if p.is_file() and p.suffix in PAGE_SUFFIXES
    }


def _shown(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def check(files, out):
    """Return one ERROR line per page that differs from the fresh build."""
    errors = []
    for rel in sorted(set(files) | _on_disk(out)):
        path = out / rel
        fresh = files.get(rel)
        if fresh is None or not path.is_file() or path.read_bytes() != fresh.encode("utf-8"):
            errors.append(f"ERROR: stale page {_shown(path)}; run scripts/generate-playbook.py")
    return errors


def write(files, out):
    out.mkdir(parents=True, exist_ok=True)
    for rel in sorted(_on_disk(out) - set(files)):
        (out / rel).unlink()
    for rel, body in sorted(files.items()):
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = body.encode("utf-8")
        if not path.is_file() or path.read_bytes() != raw:
            path.write_bytes(raw)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build the playbook pages.")
    parser.add_argument("--layers", type=Path, default=LAYERS_FILE)
    parser.add_argument("--frameworks", type=Path, default=FRAMEWORKS_FILE)
    parser.add_argument("--advisors", type=Path, default=ADVISORS_FILE)
    parser.add_argument("--out", type=Path, default=PAGES_DIR)
    parser.add_argument(
        "--check", action="store_true",
        help="exit non-zero when the committed pages differ from a fresh build; write nothing",
    )
    parser.add_argument(
        "--report", action="store_true",
        help="print two-area frameworks and required documents from outside; write nothing",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    data, errors = load_and_validate(args.layers, args.frameworks, args.advisors)
    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        return 1
    if args.report:
        print(report(data), end="")
        return 0
    files = build(data)
    if args.check:
        stale = check(files, args.out)
        for line in stale:
            print(line, file=sys.stderr)
        return 1 if stale else 0
    write(files, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
