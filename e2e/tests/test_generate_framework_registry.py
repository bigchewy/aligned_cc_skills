"""scripts/generate-framework-registry.mjs writes {doc, from} document entries, strips quotes
from frontmatter names, and writes no category."""
import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-framework-registry.mjs"

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

CURRENT_REGISTRY = textwrap.dedent(
    """\
    frameworks:
    - advisor: april-dunford
      helpful_documents:
      - doc: business goals
        from: proximate-objectives
      - doc: the story map the breadboard came from (docs/story-maps/{slug}.md), so the
          screens can be walked against it
        from: user-story-map
      - doc: 'real content: actual names, emails'
        from:
        - sales-pitch-structure
        - strategic-narrative
      id: first-one
      name: First One
    - advisor: brad-frost
      required_documents:
      - doc: business goals
        from: outside
      id: second-one
      name: Second One
    """
)


def run_node(tmp_path, body):
    harness = tmp_path / "harness.mjs"
    harness.write_text(
        f"import * as gen from {json.dumps(SCRIPT.as_uri())};\n"
        f"const registryText = {json.dumps(CURRENT_REGISTRY)};\n" + body
    )
    result = subprocess.run(["node", str(harness)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_script_writes_no_category():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "categor" not in text.lower()


@needs_node
def test_frontmatter_names_lose_surrounding_quotes(tmp_path):
    out = run_node(
        tmp_path,
        """
        const content = "---\\nrequired_documents:\\n  - 'a doc: with a colon'\\n  - \\"double quoted\\"\\n  - plain doc\\nhelpful_documents: []\\n---\\nBody\\n";
        console.log(JSON.stringify(gen.parseFrontmatter(content).frontmatter));
        """,
    )
    fm = json.loads(out)
    assert fm["required_documents"] == ["a doc: with a colon", "double quoted", "plain doc"]
    assert fm["helpful_documents"] == []


@needs_node
def test_from_is_carried_over_when_id_and_doc_match(tmp_path):
    out = run_node(
        tmp_path,
        """
        const froms = gen.loadExistingFroms(registryText);
        const yaml = gen.documentsYaml("helpful_documents",
          ["business goals", "the story map the breadboard came from (docs/story-maps/{slug}.md), so the screens can be walked against it",
           "real content: actual names, emails", "a brand new doc"], "first-one", froms);
        console.log(yaml);
        """,
    )
    entries = yaml.safe_load(out)["helpful_documents"]
    assert entries == [
        {"doc": "business goals", "from": "proximate-objectives"},
        {
            "doc": "the story map the breadboard came from (docs/story-maps/{slug}.md), so the screens can be walked against it",
            "from": "user-story-map",
        },
        {"doc": "real content: actual names, emails", "from": ["sales-pitch-structure", "strategic-narrative"]},
        {"doc": "a brand new doc", "from": "outside"},
    ]


@needs_node
def test_from_is_not_carried_across_ids(tmp_path):
    out = run_node(
        tmp_path,
        """
        const froms = gen.loadExistingFroms(registryText);
        console.log(gen.documentsYaml("required_documents", ["business goals"], "second-one", froms));
        console.log("---");
        console.log(gen.documentsYaml("required_documents", ["business goals"], "not-in-registry", froms));
        """,
    )
    first, second = out.split("---")
    assert yaml.safe_load(first)["required_documents"] == [{"doc": "business goals", "from": "outside"}]
    assert yaml.safe_load(second)["required_documents"] == [{"doc": "business goals", "from": "outside"}]


@needs_node
def test_missing_registry_text_gives_outside(tmp_path):
    out = run_node(
        tmp_path,
        """
        const froms = gen.loadExistingFroms("");
        console.log(gen.documentsYaml("required_documents", ["x"], "any", froms));
        """,
    )
    assert yaml.safe_load(out)["required_documents"] == [{"doc": "x", "from": "outside"}]
