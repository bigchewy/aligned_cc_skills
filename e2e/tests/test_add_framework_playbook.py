"""add-framework places a new framework on the playbook map (design Part 5)."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "add-framework" / "SKILL.md"
TEMPLATE = REPO / "skills" / "add-framework" / "report-template.md"


def read(path):
    return path.read_text(encoding="utf-8")


def section(text, heading):
    m = re.search(rf"\*\*{re.escape(heading)}\.?\*\*.*?(?=\n\*\*[A-Z]|\n### |\Z)", text, re.S)
    assert m, f"{heading} missing"
    return m.group(0)


def test_plugin_framework_gets_an_area_or_a_reason_to_hold_it():
    block = section(read(SKILL), "Place the framework on the playbook")
    assert "skills/playbook/layers.yaml" in block
    assert "holding" in block
    assert "reason" in block
    assert "start" in block


def test_plugin_framework_is_asked_its_seat():
    text = read(SKILL)
    assert "skills/org-chart/seats.yaml" in text


def test_plugin_framework_is_asked_stages_and_market():
    block = section(read(SKILL), "Place the framework on the playbook")
    for word in ["stages", "market", "idea", "pilot", "nail-it", "scale-it", "milk-it", "b2b", "b2c"]:
        assert word in block, word


def test_every_document_is_asked_which_framework_writes_it():
    text = read(SKILL)
    step5 = text[text.index("### 5. Add Registry Entry") : text.index("### 6.")]
    assert "which framework writes" in step5
    assert "outside" in step5


def test_project_local_framework_is_asked_only_the_document_question():
    block = section(read(SKILL), "Place the framework on the playbook")
    low = block.lower()
    assert "project" in low and "only" in low
    assert "plugin frameworks only" in low
    assert "document" in low


def test_playbook_rebuild_runs_only_when_the_generator_exists():
    block = section(read(SKILL), "Place the framework on the playbook")
    assert "scripts/generate-playbook.py" in block
    assert "does not exist" in block
    assert "e2e/tests/test_playbook.py" in block


def test_readme_row_is_added_under_the_area():
    text = read(SKILL)
    assert "frameworks/README.md" in section(text, "Place the framework on the playbook")


def test_report_template_checks_the_placement():
    text = read(TEMPLATE).lower()
    assert "playbook" in text
