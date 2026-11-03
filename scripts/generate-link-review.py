#!/usr/bin/env python3
"""Order the document-link review entries for Eric's review page.

Reads docs/framework-flows/link-review.yaml and the framework registry, sorts the
entries least sure first (guess, likely, sure), then by the needing framework's
name, then by document. Each entry gains framework_name, from_names and a plain
sentence. Writes docs/framework-flows/link-review.json as
{"links": [...], "counts": {"guess": n, "likely": n, "sure": n}}.

An entry that names a framework the registry does not have stops the run with an
ERROR line on stderr and exit 1.
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REVIEW_FILE = ROOT / "docs" / "framework-flows" / "link-review.yaml"
FRAMEWORKS_FILE = ROOT / "frameworks" / "registry.yaml"
OUT_FILE = ROOT / "docs" / "framework-flows" / "link-review.json"

OUTSIDE = "outside"
CONFIDENCE_ORDER = ["guess", "likely", "sure"]


def _writers(frm):
    return [frm] if isinstance(frm, str) else list(frm)


def sentence(framework_name, doc, kind, from_names):
    if from_names == [OUTSIDE]:
        source = "from outside the plugin"
    else:
        source = "written by " + " or ".join(from_names)
    if kind == "required":
        return f"{framework_name} needs {doc}, {source}. Must have."
    return f"{framework_name} is helped by {doc}, {source}."


def ordered(review, registry):
    """Return the review entries sorted guess, likely, sure, then framework name, then doc."""
    names = {f["id"]: f.get("name") or f["id"] for f in registry.get("frameworks") or []}
    out = []
    for e in review:
        if e["framework"] not in names:
            raise KeyError(f"unknown framework '{e['framework']}' in {e['id']}")
        from_names = []
        for w in _writers(e["from"]):
            if w == OUTSIDE:
                from_names.append(OUTSIDE)
            elif w in names:
                from_names.append(names[w])
            else:
                raise KeyError(f"unknown writer '{w}' in {e['id']}")
        item = dict(e)
        item["framework_name"] = names[e["framework"]]
        item["from_names"] = from_names
        item["sentence"] = sentence(item["framework_name"], e["doc"], e["kind"], from_names)
        out.append(item)
    out.sort(key=lambda i: (CONFIDENCE_ORDER.index(i["confidence"]), i["framework_name"].lower(), i["doc"].lower()))
    return out


def count_by_confidence(links):
    counts = {c: 0 for c in CONFIDENCE_ORDER}
    for link in links:
        counts[link["confidence"]] += 1
    return counts


def _read_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--review", type=Path, default=REVIEW_FILE, help="the link review YAML")
    parser.add_argument("--registry", type=Path, default=FRAMEWORKS_FILE, help="the framework registry")
    parser.add_argument("--out", type=Path, default=OUT_FILE, help="where to write the JSON")
    args = parser.parse_args(argv)

    try:
        links = ordered(_read_yaml(args.review) or [], _read_yaml(args.registry) or {})
    except KeyError as err:
        print(f"ERROR: {err.args[0]}", file=sys.stderr)
        sys.exit(1)

    data = {"links": links, "counts": count_by_confidence(links)}
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(links)} links: {data['counts']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
