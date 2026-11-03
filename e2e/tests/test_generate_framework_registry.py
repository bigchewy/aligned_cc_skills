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


DRAFT_LAYOUT = textwrap.dedent(
    """\
    frameworks:
      - id: renamed-one
        name: "Renamed One"
        market: b2b
        required_documents:
          - doc: "business goals"
            from: proximate-objectives
          - doc: "real content: actual names, emails"
            from: [sales-pitch-structure, strategic-narrative]
        helpful_documents:
          - doc: "an outside doc"
            from: outside
        stages:
          - idea
          - pilot

      - id: other-one
        name: "Other One"
        stages:
          - nail-it
    """
)


@needs_node
def test_from_is_read_back_from_the_layout_the_script_writes(tmp_path):
    out = run_node(
        tmp_path,
        f"""
        const froms = gen.loadExistingFroms({json.dumps(DRAFT_LAYOUT)});
        console.log(JSON.stringify([...froms.entries()]));
        """,
    )
    got = dict((k.replace("\u0000", "|"), v) for k, v in json.loads(out))
    assert got == {
        "renamed-one|business goals": "proximate-objectives",
        "renamed-one|real content: actual names, emails": ["sales-pitch-structure", "strategic-narrative"],
        "renamed-one|an outside doc": "outside",
    }


@needs_node
def test_stages_and_market_are_read_from_both_layouts(tmp_path):
    registry_text = CURRENT_REGISTRY.replace(
        "  id: first-one\n",
        "  id: first-one\n  market: b2c\n  stages:\n  - nail-it\n  - scale-it\n",
    )
    out = run_node(
        tmp_path,
        f"""
        const a = gen.loadExistingMeta({json.dumps(registry_text)});
        const b = gen.loadExistingMeta({json.dumps(DRAFT_LAYOUT)});
        console.log(JSON.stringify([[...a.entries()], [...b.entries()]]));
        """,
    )
    a, b = json.loads(out)
    assert dict(a) == {"first-one": {"market": "b2c", "stages": ["nail-it", "scale-it"]}}
    assert dict(b) == {
        "renamed-one": {"market": "b2b", "stages": ["idea", "pilot"]},
        "other-one": {"stages": ["nail-it"]},
    }


@needs_node
def test_meta_yaml_writes_market_and_stages_and_nothing_for_an_unknown_id(tmp_path):
    out = run_node(
        tmp_path,
        """
        const meta = gen.loadExistingMeta(registryText.replace("  id: first-one\\n",
          "  id: first-one\\n  market: b2c\\n  stages:\\n  - nail-it\\n"));
        console.log(gen.metaYaml("first-one", meta));
        console.log("---");
        console.log(JSON.stringify(gen.metaYaml("not-there", meta)));
        """,
    )
    first, second = out.split("---")
    assert yaml.safe_load(first) == {"market": "b2c", "stages": ["nail-it"]}
    assert json.loads(second.strip()) == ""


@needs_node
def test_real_registry_froms_stages_and_market_are_all_read(tmp_path):
    registry_path = ROOT / "frameworks" / "registry.yaml"
    real = yaml.safe_load(registry_path.read_text())["frameworks"]
    out = run_node(
        tmp_path,
        f"""
        import fs from "fs";
        const text = fs.readFileSync({json.dumps(str(registry_path))}, "utf8");
        console.log(JSON.stringify([[...gen.loadExistingFroms(text).entries()], [...gen.loadExistingMeta(text).entries()]]));
        """,
    )
    froms, meta = (dict(x) for x in json.loads(out))
    want_froms = {}
    want_meta = {}
    for f in real:
        for key in ("required_documents", "helpful_documents"):
            for d in f.get(key) or []:
                want_froms[f"{f['id']}\u0000{d['doc']}"] = d["from"]
        m = {k: f[k] for k in ("market", "stages") if f.get(k)}
        if m:
            want_meta[f["id"]] = m
    assert froms == want_froms
    assert meta == want_meta


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
