import textwrap
from pathlib import Path
import pytest
import yaml

from sync_framework_frontmatter import sync_framework_frontmatter, parse_frontmatter, write_frontmatter


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_adds_field_when_frontmatter_missing(tmp_path):
    fw = tmp_path / "frameworks" / "alpha"
    write(fw / "prompt.md", "You are Foo, guiding...\n\nPhase 1...\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: alpha\n    deliverable_type: content\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")

    fm, body = parse_frontmatter((fw / "prompt.md").read_text())
    assert fm["deliverable_type"] == "content"
    assert "You are Foo" in body


def test_updates_field_when_value_stale(tmp_path):
    fw = tmp_path / "frameworks" / "beta"
    write(fw / "prompt.md", "---\ndeliverable_type: plan\nrequired_documents: []\n---\nbody\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: beta\n    deliverable_type: decision\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")

    fm, _ = parse_frontmatter((fw / "prompt.md").read_text())
    assert fm["deliverable_type"] == "decision"
    assert fm.get("required_documents") == [], "must preserve sibling fields"


def test_idempotent(tmp_path):
    fw = tmp_path / "frameworks" / "gamma"
    write(fw / "prompt.md", "body\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: gamma\n    deliverable_type: analysis\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    first = (fw / "prompt.md").read_text()
    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    second = (fw / "prompt.md").read_text()
    assert first == second, "script must be idempotent"


def test_missing_prompt_logs_warning_and_continues(tmp_path, caplog):
    (tmp_path / "frameworks" / "delta").mkdir(parents=True)
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: delta\n    deliverable_type: content\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    assert "missing prompt.md" in caplog.text.lower()


def test_missing_registry_entry_logs_warning_and_continues(tmp_path, caplog):
    fw = tmp_path / "frameworks" / "epsilon"
    write(fw / "prompt.md", "body\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks: []\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    assert "no registry entry" in caplog.text.lower()


def test_handles_quoted_name_field_with_embedded_quotes(tmp_path):
    """Regression test for entries like 5-components-positioning whose name contains escaped quotes."""
    fw = tmp_path / "frameworks" / "5-components-positioning"
    write(fw / "prompt.md", "body\n")
    registry = tmp_path / "registry.yaml"
    write(registry, textwrap.dedent('''\
        frameworks:
          - id: 5-components-positioning
            name: "5 Components of Positioning"
            deliverable_type: content
        '''))

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    fm, _ = parse_frontmatter((fw / "prompt.md").read_text())
    assert fm["deliverable_type"] == "content"
