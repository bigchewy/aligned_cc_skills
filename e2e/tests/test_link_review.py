"""docs/framework-flows/link-review.yaml: every review entry matches a document link in the registry."""
import importlib.util
import json
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


def test_every_review_entry_matches_a_registry_link():
    # One way only: the review file shrinks as links are answered and nothing
    # writes it when a framework is added, so the registry may have more links.
    links = registry_links()
    for e in review_entries():
        assert e["id"] in links, f"review entry {e['id']} has no registry link"
        link = links[e["id"]]
        assert e["framework"] == link["framework"]
        assert e["doc"] == link["doc"]
        assert e["kind"] == link["kind"], e["id"]
        assert e["from"] == link["from"], e["id"]


def test_confidence_is_sure_likely_or_guess():
    for e in review_entries():
        assert e["confidence"] in {"sure", "likely", "guess"}, e["id"]


def test_reason_is_not_empty():
    for e in review_entries():
        assert isinstance(e["reason"], str) and e["reason"].strip(), e["id"]


def test_list_links_are_never_sure():
    for e in review_entries():
        if isinstance(e["from"], list):
            assert e["confidence"] != "sure", e["id"]


def test_outside_links_are_sure_or_guess_and_say_which_case():
    for e in review_entries():
        if e["from"] != "outside":
            continue
        assert e["confidence"] in {"sure", "guess"}, e["id"]
        if e["confidence"] == "sure":
            assert "user's own material" in e["reason"], e["id"]
        else:
            assert "might write it" in e["reason"], e["id"]


# ---- ordering, counts and sentences (scripts/generate-link-review.py) ----
_spec = importlib.util.spec_from_file_location("generate_link_review", ROOT / "scripts" / "generate-link-review.py")
glr = importlib.util.module_from_spec(_spec)

FAKE_REGISTRY = {"frameworks": [
    {"id": "alpha", "name": "Alpha Framework"},
    {"id": "beta", "name": "Beta Framework"},
    {"id": "gamma", "name": "Gamma Framework"},
]}


def entry(fw, doc, kind, frm, confidence):
    return {"id": f"{fw}/{slug(doc)}", "framework": fw, "doc": doc, "kind": kind, "from": frm,
            "confidence": confidence, "reason": "r"}


def load_glr():
    _spec.loader.exec_module(glr)
    return glr


def test_ordered_sorts_guess_likely_sure_then_name_then_doc():
    g = load_glr()
    review = [
        entry("alpha", "b doc", "required", "beta", "sure"),
        entry("beta", "z doc", "required", "alpha", "guess"),
        entry("alpha", "z doc", "required", "beta", "guess"),
        entry("alpha", "a doc", "required", "beta", "guess"),
        entry("gamma", "d", "helpful", "alpha", "likely"),
    ]
    out = g.ordered(review, FAKE_REGISTRY)
    assert [(e["confidence"], e["framework"], e["doc"]) for e in out] == [
        ("guess", "alpha", "a doc"), ("guess", "alpha", "z doc"), ("guess", "beta", "z doc"),
        ("likely", "gamma", "d"), ("sure", "alpha", "b doc"),
    ]


def test_ordered_adds_names():
    g = load_glr()
    out = g.ordered([entry("alpha", "a doc", "required", "beta", "sure")], FAKE_REGISTRY)[0]
    assert out["framework_name"] == "Alpha Framework"
    assert out["from_names"] == ["Beta Framework"]


def test_sentence_required():
    g = load_glr()
    e = g.ordered([entry("alpha", "the plan", "required", "beta", "sure")], FAKE_REGISTRY)[0]
    assert e["sentence"] == "Alpha Framework needs the plan, written by Beta Framework. Must have."


def test_sentence_helpful_with_two_writers():
    g = load_glr()
    e = g.ordered([entry("alpha", "the plan", "helpful", ["beta", "gamma"], "likely")], FAKE_REGISTRY)[0]
    assert e["from_names"] == ["Beta Framework", "Gamma Framework"]
    assert e["sentence"] == "Alpha Framework is helped by the plan, written by Beta Framework or Gamma Framework."


def test_sentence_outside():
    g = load_glr()
    req = g.ordered([entry("alpha", "notes", "required", "outside", "sure")], FAKE_REGISTRY)[0]
    hlp = g.ordered([entry("alpha", "notes", "helpful", "outside", "sure")], FAKE_REGISTRY)[0]
    assert req["from_names"] == ["outside"]
    assert req["sentence"] == "Alpha Framework needs notes, from outside the plugin. Must have."
    assert hlp["sentence"] == "Alpha Framework is helped by notes, from outside the plugin."


def test_real_review_counts_sum_to_review_entries():
    g = load_glr()
    registry = yaml.safe_load(FRAMEWORKS.read_text())
    out = g.ordered(review_entries(), registry)
    counts = g.count_by_confidence(out)
    assert sum(counts.values()) == len(review_entries())
    assert list(counts) == ["guess", "likely", "sure"]
    rank = {"guess": 0, "likely": 1, "sure": 2}
    ranks = [rank[e["confidence"]] for e in out]
    assert ranks == sorted(ranks)


def test_main_writes_json(tmp_path):
    g = load_glr()
    out_file = tmp_path / "out.json"
    assert g.main(["--out", str(out_file)]) == 0
    data = json.loads(out_file.read_text())
    assert set(data) == {"links", "counts"}
    assert sum(data["counts"].values()) == len(data["links"])


def test_main_fails_on_unknown_framework(tmp_path):
    g = load_glr()
    bad = tmp_path / "r.yaml"
    bad.write_text(yaml.safe_dump([entry("nope", "d", "required", "outside", "sure")]))
    try:
        g.main(["--review", str(bad), "--out", str(tmp_path / "o.json")])
    except SystemExit as e:
        assert e.code != 0
    else:
        raise AssertionError("expected a failure for an unknown framework")


def test_zone_of_genius_entry_is_not_among_declutter_entries():
    ids = [e["framework"] for e in review_entries()]
    i = ids.index("zone-of-genius")
    assert ids[i - 1] != "declutter-and-focus" and ids[i + 1] != "declutter-and-focus"


def test_fixed_reasons():
    by_id = {e["id"]: e for e in review_entries()}
    vc = by_id["5-components-positioning/value-curve"]
    assert "someone else's work" not in vc["reason"]
    assert "neither prompt mentions" in vc["reason"].lower()
    lm = by_id["sales-pitch-structure/language-messaging-md"]
    assert lm["confidence"] == "sure"
