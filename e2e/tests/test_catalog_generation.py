"""The framework catalog groups by layer and area (from layers.yaml) and shows document names."""
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-catalogs.py"
TEMPLATE = ROOT / "scripts" / "catalog-template.html"
LAYERS = ROOT / "skills" / "playbook" / "layers.yaml"
CATALOG = ROOT / "docs" / "framework-catalog.html"

_spec = importlib.util.spec_from_file_location("generate_catalogs", SCRIPT)
gc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gc)


def embedded_config(path):
    html = path.read_text(encoding="utf-8")
    m = re.search(r'<script id="config-data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace("<\\/script>", "</script>"))


def test_framework_config_carries_the_playbook_in_layers_yaml_order():
    config = gc.build_config("framework", {"frameworks": []}, "now")
    layers = yaml.safe_load(LAYERS.read_text())
    assert [l["id"] for l in config["playbook"]["layers"]] == [l["id"] for l in layers["layers"]]
    first = config["playbook"]["layers"][0]["areas"][0]
    assert set(first) >= {"id", "name", "frameworks"}
    assert config["playbook"]["holding"] == layers["holding"]


def test_advisor_config_has_no_playbook():
    config = gc.build_config("advisor", {"advisors": []}, "now")
    assert "playbook" not in config


def test_missing_layers_file_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(gc, "LAYERS_PATH", tmp_path / "nope.yaml")
    with pytest.raises(FileNotFoundError):
        gc.build_config("framework", {"frameworks": []}, "now")


def test_published_framework_catalog_is_current():
    config = embedded_config(CATALOG)
    layers = yaml.safe_load(LAYERS.read_text())
    assert config["playbook"]["layers"] == [
        {
            "id": l["id"],
            "name": l["name"],
            "areas": [{"id": a["id"], "name": a["name"], "frameworks": a["frameworks"]} for a in l["areas"]],
        }
        for l in layers["layers"]
    ]
    assert all("category" not in e for e in config["registry"]["frameworks"])


def test_template_has_no_category_field_and_reads_document_names():
    text = TEMPLATE.read_text(encoding="utf-8")
    assert 'key: "category"' not in text
    assert "groupBy" not in text
    assert "function docName" in text
    assert 'type: "docs"' in text


def _run_doc_functions(tmp_path, body):
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("node not installed")
    text = TEMPLATE.read_text(encoding="utf-8")
    start = text.index("function docName")
    end = text.index("function renderRow")
    harness = tmp_path / "docs.js"
    harness.write_text(text[start:end] + "\n" + body)
    result = subprocess.run(["node", str(harness)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_document_name_with_a_comma_round_trips_with_its_from(tmp_path):
    out = _run_doc_functions(
        tmp_path,
        """
        const original = [
          { doc: "real content: names, emails, labels", from: ["a", "b"] },
          "plain, with comma",
          { doc: "business goals", from: "proximate-objectives" },
        ];
        const text = docsToString(original);
        const same = stringToDocs(text, original);
        const edited = stringToDocs(text + "\\nbrand new, doc", original);
        console.log(JSON.stringify({ text, same, edited }));
        """,
    )
    assert out["text"].split("\n") == [
        "real content: names, emails, labels",
        "plain, with comma",
        "business goals",
    ]
    assert out["same"] == [
        {"doc": "real content: names, emails, labels", "from": ["a", "b"]},
        "plain, with comma",
        {"doc": "business goals", "from": "proximate-objectives"},
    ]
    assert out["edited"][-1] == {"doc": "brand new, doc", "from": "outside"}
    assert out["edited"][:3] == out["same"]
