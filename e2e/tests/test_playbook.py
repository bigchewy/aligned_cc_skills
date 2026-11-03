"""Playbook map file: skills/playbook/layers.yaml checked against the framework registry."""
import copy
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-playbook.py"
LAYERS = ROOT / "skills" / "playbook" / "layers.yaml"
FRAMEWORKS = ROOT / "frameworks" / "registry.yaml"

_spec = importlib.util.spec_from_file_location("generate_playbook", SCRIPT)
gp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gp)


def fake_registry(*ids):
    return {"frameworks": [{"id": i, "name": i} for i in ids]}


def fake_layers():
    return {
        "layers": [
            {
                "id": "i",
                "name": "I",
                "does": "Work on yourself.",
                "areas": [
                    {"id": "a1", "name": "A1", "note": "n", "start": "f1", "frameworks": ["f1", "f2"]},
                    {"id": "a2", "name": "A2", "note": "n", "start": "f3", "frameworks": ["f3"]},
                ],
            }
        ],
        "holding": [{"id": "f4", "why": "elsewhere"}],
    }


def write(tmp_path, layers, registry):
    lp = tmp_path / "layers.yaml"
    fp = tmp_path / "registry.yaml"
    lp.write_text(yaml.safe_dump(layers, sort_keys=False))
    fp.write_text(yaml.safe_dump(registry, sort_keys=False))
    return lp, fp


REG = fake_registry("f1", "f2", "f3", "f4")


def test_fake_file_is_valid(tmp_path):
    lp, fp = write(tmp_path, fake_layers(), REG)
    data, errors = gp.load_and_validate(lp, fp)
    assert errors == []
    assert set(data) >= {"layers", "frameworks", "homes"}
    assert data["homes"]["f1"] == [("i", "a1")]
    assert set(data["frameworks"]) == {"f1", "f2", "f3", "f4"}


def test_homes_list_every_area_a_framework_sits_in(tmp_path):
    layers = fake_layers()
    layers["layers"][0]["areas"][1]["frameworks"].append("f1")
    lp, fp = write(tmp_path, layers, REG)
    data, errors = gp.load_and_validate(lp, fp)
    assert errors == []
    assert data["homes"]["f1"] == [("i", "a1"), ("i", "a2")]


def test_unplaced_framework_errors(tmp_path):
    lp, fp = write(tmp_path, fake_layers(), fake_registry("f1", "f2", "f3", "f4", "f5"))
    _, errors = gp.load_and_validate(lp, fp)
    assert "ERROR: unplaced framework 'f5'" in errors


def test_unknown_framework_errors(tmp_path):
    layers = fake_layers()
    layers["layers"][0]["areas"][0]["frameworks"].append("ghost")
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "'ghost'" in e for e in errors)


def test_unknown_held_framework_errors(tmp_path):
    layers = fake_layers()
    layers["holding"].append({"id": "ghost", "why": "x"})
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "'ghost'" in e for e in errors)


def test_placed_and_held_errors(tmp_path):
    layers = fake_layers()
    layers["holding"].append({"id": "f1", "why": "x"})
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "'f1'" in e and "holding" in e for e in errors)


def test_duplicate_area_id_errors(tmp_path):
    layers = fake_layers()
    layers["layers"][0]["areas"][1]["id"] = "a1"
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "'a1'" in e for e in errors)


def test_missing_start_errors(tmp_path):
    layers = fake_layers()
    del layers["layers"][0]["areas"][0]["start"]
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "start" in e and "'a1'" in e for e in errors)


def test_start_not_in_area_errors(tmp_path):
    layers = fake_layers()
    layers["layers"][0]["areas"][0]["start"] = "f3"
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "start" in e and "'a1'" in e for e in errors)


def test_check_layers_does_not_mutate_input():
    layers = fake_layers()
    before = copy.deepcopy(layers)
    assert gp.check_layers(layers, REG) == []
    assert layers == before


def test_check_layers_rejects_duplicate_framework_in_one_area():
    layers = fake_layers()
    layers["layers"][0]["areas"][0]["frameworks"].append("f1")
    errors = gp.check_layers(layers, REG)
    assert any(e.startswith("ERROR:") and "'f1'" in e for e in errors)


def test_real_file_passes_with_5_5_10_areas():
    data, errors = gp.load_and_validate(LAYERS, FRAMEWORKS)
    assert errors == []
    counts = {layer["id"]: len(layer["areas"]) for layer in data["layers"]["layers"]}
    assert counts == {"i": 5, "we": 5, "it": 10}


def test_real_file_places_or_holds_every_registry_id():
    data, errors = gp.load_and_validate(LAYERS, FRAMEWORKS)
    assert errors == []
    held = {h["id"] for h in data["layers"]["holding"]}
    assert held == {"close-the-loop"}
    for fid in data["frameworks"]:
        assert fid in data["homes"] or fid in held


# --- Document links: each required/helpful document names the framework that writes it ---

LINK_FIXTURE = ROOT / "e2e" / "tests" / "fixtures" / "playbook" / "registry.yaml"


def link_fixture():
    return yaml.safe_load(LINK_FIXTURE.read_text())


def fixture_entry(fid):
    return next(f for f in link_fixture()["frameworks"] if f["id"] == fid)


def errors_about(errors, fid):
    return [e for e in errors if f"'{fid}'" in e]


def test_doc_links_reads_plain_string_as_outside():
    links = gp.doc_links(fixture_entry("plain"))
    assert links == [{"doc": "a plain string doc", "from": ["outside"], "kind": "helpful"}]


def test_doc_links_turns_single_id_into_list_and_keeps_order():
    links = gp.doc_links(fixture_entry("branch"))
    assert links == [
        {"doc": "doc x", "from": ["writer-a"], "kind": "required"},
        {"doc": "doc y", "from": ["writer-b"], "kind": "helpful"},
        {"doc": "doc z", "from": ["writer-a", "writer-b"], "kind": "helpful"},
    ]


def test_doc_links_on_framework_with_no_documents_is_empty():
    assert gp.doc_links(fixture_entry("writer-a")) == []


def test_good_fixture_cases_raise_no_errors():
    errors = gp.check_links(link_fixture())
    for fid in ("branch", "help-1", "help-2", "plain", "writer-a", "writer-b", "b2b-writer", "any-reader"):
        assert errors_about(errors, fid) == [], fid


def test_unknown_from_names_framework_doc_and_bad_id():
    errors = gp.check_links(link_fixture())
    hits = [e for e in errors if "'ghost'" in e]
    assert len(hits) == 1
    assert hits[0].startswith("ERROR:")
    assert "'unknown-from'" in hits[0] and "'list doc'" in hits[0]


def test_self_link_names_framework_doc_and_value():
    errors = gp.check_links(link_fixture())
    hits = [e for e in errors if "'self doc'" in e]
    assert len(hits) == 1
    assert hits[0].startswith("ERROR:") and "'self-link'" in hits[0] and "itself" in hits[0]


def test_required_loop_is_an_error_and_names_each_link():
    errors = gp.check_links(link_fixture())
    hits = [e for e in errors if "loop" in e and "'loop-1'" in e]
    assert len(hits) == 1
    msg = hits[0]
    assert msg.startswith("ERROR:")
    assert "'loop-2'" in msg and "'loop doc 1'" in msg and "'loop doc 2'" in msg


def test_helpful_loop_is_not_an_error():
    errors = gp.check_links(link_fixture())
    assert not any("'help-1'" in e or "'help-2'" in e for e in errors)


def test_b2c_writer_feeding_only_b2b_is_an_error():
    errors = gp.check_links(link_fixture())
    hits = errors_about(errors, "b2c-writer")
    assert len(hits) == 1
    msg = hits[0]
    assert msg.startswith("ERROR:") and "b2c" in msg and "'b2c doc'" in msg and "'b2b-reader'" in msg


def test_fixture_has_exactly_the_four_planted_errors():
    assert len(gp.check_links(link_fixture())) == 4


def test_entry_that_is_neither_string_nor_mapping_errors():
    reg = {"frameworks": [{"id": "x", "helpful_documents": [{"doc": "d"}]}]}
    errors = gp.check_links(reg)
    assert len(errors) == 1 and errors[0].startswith("ERROR:") and "'x'" in errors[0]


def test_outside_required_lists_required_outside_docs_only():
    reg = {"frameworks": [
        {"id": "a", "required_documents": ["plain need", {"doc": "own", "from": "outside"},
                                           {"doc": "linked", "from": "b"}],
         "helpful_documents": [{"doc": "nice", "from": "outside"}]},
        {"id": "b"},
    ]}
    assert gp.outside_required(reg) == [("a", "plain need"), ("a", "own")]


def test_load_and_validate_includes_link_errors(tmp_path):
    lp, fp = write(tmp_path, fake_layers(), link_fixture())
    _, errors = gp.load_and_validate(lp, fp)
    assert any("'ghost'" in e for e in errors)


def real_registry():
    return yaml.safe_load(FRAMEWORKS.read_text())


def test_real_registry_links_pass():
    assert gp.check_links(real_registry()) == []


def test_real_registry_entries_are_all_doc_from_mappings():
    for f in real_registry()["frameworks"]:
        for key in ("required_documents", "helpful_documents"):
            for entry in f.get(key) or []:
                assert isinstance(entry, dict), f"{f['id']} {key}: {entry!r}"
                assert set(entry) == {"doc", "from"}, f"{f['id']} {key}: {entry!r}"
                assert isinstance(entry["doc"], str) and entry["doc"]


def test_real_registry_single_writer_is_plain_id_not_one_item_list():
    for f in real_registry()["frameworks"]:
        for key in ("required_documents", "helpful_documents"):
            for entry in f.get(key) or []:
                if isinstance(entry["from"], list):
                    assert len(entry["from"]) > 1, f"{f['id']}: {entry!r}"


def test_check_ins_take_quarterly_goals_from_proximate_objectives():
    by_id = {f["id"]: f for f in real_registry()["frameworks"]}
    for fid, doc in (("mochary-weekly-check-in", "OKRs or quarterly goals"),
                     ("chj-operating-review", "OKRs or quarterly priorities")):
        links = {l["doc"]: l for l in gp.doc_links(by_id[fid])}
        assert links[doc]["from"] == ["proximate-objectives"]
