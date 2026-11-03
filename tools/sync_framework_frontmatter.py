"""Mirror registry fields into each framework's prompt.md YAML frontmatter.

Mirrors deliverable_type, and the plain document names of required_documents and
helpful_documents. Registry document entries are a name or a {doc, from} mapping;
the frontmatter keeps only the names, in registry order. A prompt that has no
document list gets none added when the registry has none.

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
    # No line wrapping: one list item per line, so line-based readers of the
    # frontmatter (scripts/generate-framework-registry.mjs) see whole names.
    fm_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=10**6).rstrip()
    return f"---\n{fm_text}\n---\n{body}"


DOC_KEYS = ("required_documents", "helpful_documents")


def doc_names(entries) -> list:
    """Plain document names from registry entries, which are names or {doc, from} mappings."""
    return [e["doc"] if isinstance(e, dict) else e for e in entries or []]


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

        prompt = folder / "prompt.md"
        if not prompt.exists():
            LOG.warning("missing prompt.md for framework: %s", fid)
            continue

        text = prompt.read_text()
        fm, body = parse_frontmatter(text)
        new_fm = dict(fm)

        if "deliverable_type" in entry:
            new_fm["deliverable_type"] = entry["deliverable_type"]
        else:
            LOG.warning("registry entry %s missing deliverable_type — not mirrored", fid)

        for key in DOC_KEYS:
            names = doc_names(entry.get(key))
            if names or key in new_fm:
                new_fm[key] = names

        if new_fm == fm:
            continue  # idempotent: nothing to change
        prompt.write_text(write_frontmatter(new_fm, body))
        LOG.info("updated %s", fid)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("frameworks/registry.yaml"))
    parser.add_argument("--frameworks-dir", type=Path, default=Path("frameworks"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sync_framework_frontmatter(args.registry, args.frameworks_dir)


if __name__ == "__main__":
    main()
