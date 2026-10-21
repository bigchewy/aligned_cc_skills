"""Jason Fried replaces The PM.

The PM was a generic archetype with no published method. Jason Fried
(Getting Real, Rework) takes its job: deciding whether a feature should exist,
cutting a feature list to its core, and saying no by default. Ryan Singer keeps
appetite and shaping. Nothing in the shipped plugin may still name the old
advisor, and every advisor that handed feature-value questions to The PM now
hands them to Jason Fried.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = REPO_ROOT / "advisors" / "registry.yaml"
PROMPT = REPO_ROOT / "advisors" / "prompts" / "jason-fried.md"
OLD_PROMPT = REPO_ROOT / "advisors" / "prompts" / "the-pm.md"
RESEARCH = REPO_ROOT / "docs" / "advisors" / "new_advisors" / "v_jason-fried.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "jason-fried-consult.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

# Shipped content that must not name the retired advisor.
SCANNED = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "advisors",
    REPO_ROOT / "frameworks",
    REPO_ROOT / "skills",
    REPO_ROOT / "agents",
    REPO_ROOT / "e2e" / "scenarios",
    TRIGGER_MAP,
]

# "The PMF test" is Sean Ellis's survey, not the retired advisor.
OLD_NAME = re.compile(r"the-pm\b|The PM\b")


def _registry():
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


def test_jason_fried_is_registered_with_a_prompt():
    entry = _registry()["jason-fried"]
    assert entry["name"] == "Jason Fried"
    assert entry["prompt"] == "advisors/prompts/jason-fried.md"
    assert PROMPT.is_file()
    assert RESEARCH.is_file()
    for field in ("best_for", "not_for", "evaluation_expertise", "summary"):
        assert entry.get(field, "").strip(), f"jason-fried needs {field}"


def test_jason_fried_covers_the_pms_review_domains():
    domains = set(_registry()["jason-fried"]["domains"])
    for needed in ("product-value", "scope-control", "user-problems"):
        assert needed in domains


def test_the_pm_is_retired():
    assert "the-pm" not in _registry()
    assert not OLD_PROMPT.exists()


def test_nothing_shipped_names_the_pm():
    hits = []
    for p in _files():
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if OLD_NAME.search(line):
                hits.append(f"{p.relative_to(REPO_ROOT)}:{n}: {line.strip()}")
    assert not hits, "Still names The PM:\n" + "\n".join(hits)


def test_hand_offs_now_name_jason_fried():
    for rel in ("advisors/prompts/annie-duke.md", "frameworks/launch-bet/prompt.md"):
        assert "Jason Fried" in (REPO_ROOT / rel).read_text(encoding="utf-8"), rel
    reg = _registry()
    for slug in ("ryan-singer", "annie-duke"):
        assert "Jason Fried" in reg[slug].get("not_for", ""), f"{slug} not_for should name Jason Fried"
    with open(REPO_ROOT / "frameworks" / "registry.yaml") as f:
        story_map = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["user-story-map"]
    assert "jason-fried" in story_map["default_critic_advisors"]


def test_prompt_is_built_on_getting_real_and_names_its_neighbors():
    text = PROMPT.read_text(encoding="utf-8")
    for term in ("Getting Real", "Build less", "Half, not half-assed", "epicenter"):
        assert term.lower() in text.lower(), f"prompt should use {term}"
    assert "what you never published" in text.lower()
    for neighbor in ("Ryan Singer", "Annie Duke", "Steve Krug", "Eric Ries"):
        assert neighbor in text, f"prompt should hand off to {neighbor}"


def test_consult_scenario_exists_and_is_wired_to_the_prompt():
    assert SCENARIO.is_file()
    assert "advisors/prompts/jason-fried.md" in SCENARIO.read_text(encoding="utf-8")
    flat = yaml.safe_dump(yaml.safe_load(TRIGGER_MAP.read_text(encoding="utf-8")))
    assert "advisors/prompts/jason-fried.md" in flat
    assert "scenarios/use-advisor/jason-fried-consult.yaml" in flat
