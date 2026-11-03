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


def load_and_validate(layers_path, frameworks_path):
    """Load the layers file and the registry. Return (data, errors)."""
    layers = _read_yaml(layers_path)
    registry = _read_yaml(frameworks_path)
    errors = check_layers(layers, registry)
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
