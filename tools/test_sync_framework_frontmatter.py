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


DOC_REGISTRY = textwrap.dedent('''\
    frameworks:
      - id: zeta
        deliverable_type: plan
        required_documents:
          - doc: "positioning.md (Component 1: alternatives)"
            from: 5-components-positioning
        helpful_documents:
          - doc: customer research
            from: outside
          - doc: company strategy
            from: [kernel-of-good-strategy, lifecycle-strategy]
          - plain old name
    ''')


def test_mirrors_plain_doc_names_in_registry_order(tmp_path):
    fw = tmp_path / "frameworks" / "zeta"
    write(fw / "prompt.md", "---\nrequired_documents:\n- stale\nhelpful_documents: []\n---\nbody\n")
    registry = tmp_path / "registry.yaml"
    write(registry, DOC_REGISTRY)

    sync_framework_frontmatter(registry, tmp_path / "frameworks")

    fm, body = parse_frontmatter((fw / "prompt.md").read_text())
    assert fm["required_documents"] == ["positioning.md (Component 1: alternatives)"]
    assert fm["helpful_documents"] == ["customer research", "company strategy", "plain old name"]
    assert body == "body\n"


def test_doc_sync_is_idempotent(tmp_path):
    fw = tmp_path / "frameworks" / "zeta"
    write(fw / "prompt.md", "body\n")
    registry = tmp_path / "registry.yaml"
    write(registry, DOC_REGISTRY)

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    first = (fw / "prompt.md").read_text()
    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    assert (fw / "prompt.md").read_text() == first


def test_prompt_without_lists_gets_none_added_when_registry_has_none(tmp_path):
    fw = tmp_path / "frameworks" / "eta"
    write(fw / "prompt.md", "---\ndeliverable_type: plan\n---\nbody\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: eta\n    deliverable_type: plan\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")

    fm, _ = parse_frontmatter((fw / "prompt.md").read_text())
    assert "required_documents" not in fm
    assert "helpful_documents" not in fm


def test_empty_lists_stay_empty_when_registry_has_none(tmp_path):
    fw = tmp_path / "frameworks" / "theta"
    text = "---\ndeliverable_type: plan\nrequired_documents: []\nhelpful_documents: []\n---\nbody\n"
    write(fw / "prompt.md", text)
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: theta\n    deliverable_type: plan\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    assert (fw / "prompt.md").read_text() == text


def test_stale_list_is_emptied_when_registry_has_none(tmp_path):
    fw = tmp_path / "frameworks" / "iota"
    write(fw / "prompt.md", "---\ndeliverable_type: plan\nhelpful_documents:\n- gone\n---\nbody\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: iota\n    deliverable_type: plan\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    fm, _ = parse_frontmatter((fw / "prompt.md").read_text())
    assert fm["helpful_documents"] == []


def test_real_prompts_match_registry_doc_names():
    root = Path(__file__).resolve().parent.parent
    registry = yaml.safe_load((root / "frameworks" / "registry.yaml").read_text())
    for entry in registry["frameworks"]:
        prompt = root / "frameworks" / entry["id"] / "prompt.md"
        if not prompt.exists():
            continue
        fm, _ = parse_frontmatter(prompt.read_text())
        for key in ("required_documents", "helpful_documents"):
            want = [d["doc"] if isinstance(d, dict) else d for d in entry.get(key) or []]
            if key in fm or want:
                assert (fm.get(key) or []) == want, f"{entry['id']} {key}"
