"""Brad Frost replaces The Designer.

The Designer was a generic archetype with no published method. Brad Frost
(Atomic Design) takes its two jobs: rendering a breadboard into exact static
screens, and reviewing UI craft and design-system consistency. Nothing in the
shipped plugin may still name the old advisor, and every advisor that used to
hand visual work to The Designer now hands it to Brad Frost.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = REPO_ROOT / "advisors" / "registry.yaml"
PROMPT = REPO_ROOT / "advisors" / "prompts" / "brad-frost.md"
OLD_PROMPT = REPO_ROOT / "advisors" / "prompts" / "the-designer.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "brad-frost-consult.yaml"
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

# Another session owns uncommitted work here and repoints it itself.
# Remove this entry once that work lands.
PENDING_ELSEWHERE = [REPO_ROOT / "frameworks" / "user-story-map"]

OLD_NAME = re.compile(r"the-designer|The Designer")


def _registry():
    with open(REGISTRY) as f:
        return {a["id"]: a for a in yaml.safe_load(f)["advisors"]}


def _files():
    for root in SCANNED:
        paths = [root] if root.is_file() else root.rglob("*")
        for p in paths:
            if not p.is_file() or p.suffix not in {".md", ".yaml", ".yml", ".html", ".json"}:
                continue
            if any(p.is_relative_to(skip) for skip in PENDING_ELSEWHERE):
                continue
            yield p


def test_brad_frost_is_registered_with_a_prompt():
    reg = _registry()
    assert "brad-frost" in reg
    entry = reg["brad-frost"]
    assert entry["name"] == "Brad Frost"
    assert entry["prompt"] == "advisors/prompts/brad-frost.md"
    assert PROMPT.is_file()
    for field in ("best_for", "not_for", "evaluation_expertise", "summary"):
        assert entry.get(field, "").strip(), f"brad-frost needs {field}"


def test_brad_frost_covers_the_designers_review_domains():
    domains = set(_registry()["brad-frost"]["domains"])
    for needed in ("design-systems", "design-tokens", "component-consistency", "responsiveness"):
        assert needed in domains


def test_the_designer_is_retired():
    assert "the-designer" not in _registry()
    assert not OLD_PROMPT.exists()


def test_nothing_shipped_names_the_designer():
    hits = []
    for p in _files():
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if OLD_NAME.search(line):
                hits.append(f"{p.relative_to(REPO_ROOT)}:{n}: {line.strip()}")
    assert not hits, "Still names The Designer:\n" + "\n".join(hits)


def test_advisors_that_handed_off_visual_work_now_name_brad_frost():
    for slug in ("jeff-patton", "steve-krug", "james-gurney"):
        text = (REPO_ROOT / "advisors" / "prompts" / f"{slug}.md").read_text(encoding="utf-8")
        assert "Brad Frost" in text, f"{slug}.md should hand visual work to Brad Frost"
    reg = _registry()
    for slug in ("jeff-patton", "steve-krug", "james-gurney"):
        entry = reg[slug]
        text = entry.get("best_for", "") + entry.get("not_for", "")
        assert "Brad Frost" in text, f"{slug} registry entry should name Brad Frost"


def test_prompt_is_built_on_atomic_design_and_names_its_neighbors():
    text = PROMPT.read_text(encoding="utf-8")
    for term in ("Atomic Design", "template", "interface inventory"):
        assert term.lower() in text.lower(), f"prompt should use {term}"
    for neighbor in ("Steve Krug", "Ryan Singer", "create-design-principles"):
        assert neighbor in text, f"prompt should hand off to {neighbor}"


def test_consult_scenario_exists_and_is_wired_to_the_prompt():
    assert SCENARIO.is_file()
    scenario = SCENARIO.read_text(encoding="utf-8")
    assert "advisors/prompts/brad-frost.md" in scenario
    with open(TRIGGER_MAP) as f:
        entries = yaml.safe_load(f)
    flat = yaml.safe_dump(entries)
    assert "advisors/prompts/brad-frost.md" in flat
    assert "scenarios/use-advisor/brad-frost-consult.yaml" in flat
