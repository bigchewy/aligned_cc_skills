"""docs/framework-flows/link-review.yaml: one review entry per document link in the registry."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "docs" / "framework-flows" / "link-review.yaml"
FRAMEWORKS = ROOT / "frameworks" / "registry.yaml"

KINDS = {"required_documents": "required", "helpful_documents": "helpful"}
FIELDS = ["id", "framework", "doc", "kind", "from", "confidence", "reason"]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def registry_links():
    links = {}
    for f in yaml.safe_load(FRAMEWORKS.read_text())["frameworks"]:
        for key, kind in KINDS.items():
            for entry in f.get(key) or []:
                lid = f"{f['id']}/{slug(entry['doc'])}"
                assert lid not in links, f"two registry links share the id {lid}"
                links[lid] = {"framework": f["id"], "doc": entry["doc"], "kind": kind, "from": entry["from"]}
    return links


def review_entries():
    return yaml.safe_load(REVIEW.read_text())


def test_review_file_is_a_list_with_exact_fields():
    entries = review_entries()
    assert isinstance(entries, list) and entries
    for e in entries:
        assert list(e) == FIELDS, e


def test_review_ids_are_unique_and_built_from_framework_and_doc():
    seen = set()
    for e in review_entries():
        assert e["id"] not in seen, e["id"]
        seen.add(e["id"])
        assert e["id"] == f"{e['framework']}/{slug(e['doc'])}"


def test_every_registry_link_has_one_matching_review_entry():
    links = registry_links()
    by_id = {e["id"]: e for e in review_entries()}
    for lid, link in links.items():
        assert lid in by_id, f"no review entry for {lid}"
        e = by_id[lid]
        assert e["framework"] == link["framework"]
        assert e["doc"] == link["doc"]
        assert e["kind"] == link["kind"], lid
        assert e["from"] == link["from"], lid


def test_every_review_entry_has_a_registry_link():
    links = registry_links()
    for e in review_entries():
        assert e["id"] in links, f"review entry {e['id']} has no registry link"


def test_confidence_is_sure_likely_or_guess():
    for e in review_entries():
        assert e["confidence"] in {"sure", "likely", "guess"}, e["id"]


def test_reason_is_not_empty():
    for e in review_entries():
        assert isinstance(e["reason"], str) and e["reason"].strip(), e["id"]


def test_outside_and_list_links_are_never_sure():
    for e in review_entries():
        if e["from"] == "outside":
            assert e["confidence"] == "guess", e["id"]
        if isinstance(e["from"], list):
            assert e["confidence"] != "sure", e["id"]
