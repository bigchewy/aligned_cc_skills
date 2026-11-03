#!/usr/bin/env python3
"""Build the playbook pages from skills/playbook/layers.yaml and the framework registry.

Steps: load -> validate -> render -> write. A data error stops the build before
anything is written: the script prints one ERROR line per problem to stderr and
exits 1.

This file holds the validation half. Later steps add the build, the --check
comparison against what is on disk, and the writer.
"""
import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LAYERS_FILE = ROOT / "skills" / "playbook" / "layers.yaml"
FRAMEWORKS_FILE = ROOT / "frameworks" / "registry.yaml"


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


def load_and_validate(layers_path, frameworks_path):
    """Load the layers file and the registry. Return (data, errors)."""
    layers = _read_yaml(layers_path)
    registry = _read_yaml(frameworks_path)
    errors = check_layers(layers, registry) + check_links(registry)
    data = {
        "layers": layers,
        "frameworks": {f["id"]: f for f in registry.get("frameworks") or []},
        "homes": _homes(layers),
    }
    return data, errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build the playbook pages.")
    parser.add_argument("--layers", type=Path, default=LAYERS_FILE)
    parser.add_argument("--frameworks", type=Path, default=FRAMEWORKS_FILE)
    parser.add_argument("--check", action="store_true", help="validate only; write nothing")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    _, errors = load_and_validate(args.layers, args.frameworks)
    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
