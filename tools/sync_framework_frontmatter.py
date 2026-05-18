"""Mirror deliverable_type from frameworks/registry.yaml into each framework's prompt.md YAML frontmatter.

Idempotent. Safe to re-run. Logs warnings for missing prompt.md or missing registry entries.

Usage:
    python tools/sync_framework_frontmatter.py [--registry PATH] [--frameworks-dir PATH]
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import yaml

LOG = logging.getLogger("sync_framework_frontmatter")

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


def parse_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def write_frontmatter(fm: dict, body: str) -> str:
    fm_text = yaml.safe_dump(fm, sort_keys=False).rstrip()
    return f"---\n{fm_text}\n---\n{body}"


def sync_framework_frontmatter(registry_path: Path, frameworks_dir: Path) -> None:
    registry = yaml.safe_load(Path(registry_path).read_text()) or {}
    entries_by_id = {e["id"]: e for e in registry.get("frameworks", [])}

    for folder in sorted(Path(frameworks_dir).iterdir()):
        if not folder.is_dir():
            continue
        fid = folder.name
        entry = entries_by_id.get(fid)
        if entry is None:
            LOG.warning("no registry entry for framework folder: %s", fid)
            continue
        if "deliverable_type" not in entry:
            LOG.warning("registry entry %s missing deliverable_type — skipping", fid)
            continue

        prompt = folder / "prompt.md"
        if not prompt.exists():
            LOG.warning("missing prompt.md for framework: %s", fid)
            continue

        text = prompt.read_text()
        fm, body = parse_frontmatter(text)
        if fm.get("deliverable_type") == entry["deliverable_type"]:
            continue  # idempotent: nothing to change
        fm["deliverable_type"] = entry["deliverable_type"]
        prompt.write_text(write_frontmatter(fm, body))
        LOG.info("updated %s with deliverable_type=%s", fid, entry["deliverable_type"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("frameworks/registry.yaml"))
    parser.add_argument("--frameworks-dir", type=Path, default=Path("frameworks"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sync_framework_frontmatter(args.registry, args.frameworks_dir)


if __name__ == "__main__":
    main()
