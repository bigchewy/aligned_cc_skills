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
    held = {h["id"] for h in data["layers"]["holding"]}
    assert held == {"close-the-loop"}
    for fid in data["frameworks"]:
        assert fid in data["homes"] or fid in held
