"""The DevEx Engineer is retired, with no replacement.

The DevEx Engineer was a generic archetype with no published method. No skill
or framework used it. Its one hand-off, from Boris Cherny, sent CI pipelines,
SDK ergonomics, and tooling that isn't Claude Code to it. Those now go to The
Architect. Nothing in the shipped plugin may still name the old advisor.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = REPO_ROOT / "advisors" / "registry.yaml"
OLD_PROMPT = REPO_ROOT / "advisors" / "prompts" / "the-devex-engineer.md"
BORIS = REPO_ROOT / "advisors" / "prompts" / "boris-cherny.md"

# Shipped content that must not name the retired advisor.
SCANNED = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "advisors",
    REPO_ROOT / "frameworks",
    REPO_ROOT / "skills",
    REPO_ROOT / "agents",
    REPO_ROOT / "e2e" / "scenarios",
    REPO_ROOT / "e2e" / "trigger-map.yaml",
]

OLD_NAME = re.compile(r"the-devex-engineer|DevEx Engineer")


def _advisors():
    with open(REGISTRY) as f:
        return {a["id"]: a for a in yaml.safe_load(f)["advisors"]}


def _files():
    for root in SCANNED:
        paths = [root] if root.is_file() else root.rglob("*")
        for p in paths:
            if "node_modules" in p.parts:
                continue
            if not p.is_file() or p.suffix not in {".md", ".yaml", ".yml", ".html", ".json"}:
                continue
            yield p


def test_the_devex_engineer_is_retired():
    assert "the-devex-engineer" not in _advisors()
    assert not OLD_PROMPT.exists()


def test_nothing_shipped_names_the_devex_engineer():
    hits = []
    for p in _files():
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if OLD_NAME.search(line):
                hits.append(f"{p.relative_to(REPO_ROOT)}:{n}: {line.strip()}")
    assert not hits, "Still names The DevEx Engineer:\n" + "\n".join(hits)


def test_boris_cherny_sends_ci_and_sdk_work_to_the_architect():
    prompt = BORIS.read_text(encoding="utf-8")
    line = next(l for l in prompt.splitlines() if "CI pipelines" in l)
    assert "The Architect" in line
    not_for = _advisors()["boris-cherny"]["not_for"]
    assert "CI pipelines" in not_for
    assert "redirect to The Architect" in not_for.split("CI pipelines", 1)[1]
