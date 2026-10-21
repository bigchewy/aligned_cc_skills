import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILLS = ["add-framework", "add-advisor"]


def read(name):
    return (REPO / "skills" / name / "SKILL.md").read_text()


def counts_section(text):
    m = re.search(r"### \d+\. Update Advisor and Framework Counts\n(.*?)(?=\n### |\n## |\Z)", text, re.S)
    assert m, "counts step missing"
    return m.group(1)


@pytest.mark.parametrize("name", SKILLS)
def test_documents_plugin_vs_project_detection(name):
    text = read(name)
    assert "Writing to the plugin itself" in text
    assert ".claude-plugin/plugin.json" in text
    assert "`aligned`" in text


@pytest.mark.parametrize("name", SKILLS)
def test_project_repo_writes_local_framework_registry(name):
    text = read(name)
    assert "<project-cwd>/frameworks/registry.yaml" in text
    assert "create it" in text.lower()
    assert "frameworks:" in text


@pytest.mark.parametrize("name", SKILLS)
def test_keeps_parse_after_append_check(name):
    text = read(name).lower()
    assert "parse" in text and "revert" in text
    assert "delete the newly created file" in text


@pytest.mark.parametrize("name", SKILLS)
def test_counts_only_when_writing_plugin(name):
    section = counts_section(read(name))
    assert "only when writing to the plugin itself" in section.lower()
    assert "skip" in section.lower()


def test_registry_step_no_longer_requires_plugin_directory():
    assert "exists in the plugin directory" not in read("add-framework")


def test_project_repo_writes_local_advisor_registry():
    text = read("add-advisor")
    assert "<project-cwd>/advisors/registry.yaml" in text
    assert "advisors:" in text
    # full schema when creating
    for field in ["id:", "name:", "summary:", "domains:", "note:"]:
        assert field in text
