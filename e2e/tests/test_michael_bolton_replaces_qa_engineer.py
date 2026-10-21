"""Michael Bolton replaces The QA Engineer.

The QA Engineer was a generic archetype with no published method. Michael
Bolton (DevelopSense, co-creator of Rapid Software Testing with James Bach,
co-author of Taking Testing Seriously) takes its three jobs: critic in design
reviews, first-choice fact-checker in the critique panel, and the voice of
proof-points-audit. His method is FEW HICCUPPS (consistency oracles) and the
testing-versus-checking distinction. Eric's TDD tests are checks, and welcome
ones; the persona aims at what they miss. Nothing in the shipped plugin may
still name the old advisor.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = REPO_ROOT / "advisors" / "registry.yaml"
FW_REGISTRY = REPO_ROOT / "frameworks" / "registry.yaml"
PROMPT = REPO_ROOT / "advisors" / "prompts" / "michael-bolton.md"
OLD_PROMPT = REPO_ROOT / "advisors" / "prompts" / "the-qa-engineer.md"
RESEARCH = REPO_ROOT / "docs" / "advisors" / "new_advisors" / "v_michael-bolton.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "michael-bolton-consult.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"
ORCHESTRATION = REPO_ROOT / "skills" / "_shared" / "critique-panel-orchestration.md"
PROOF = REPO_ROOT / "frameworks" / "proof-points-audit"
PROOF_SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "proof-points-audit.yaml"

# Shipped content that must not name the retired advisor.
# docs/kanban and docs/mockups are history and are not scanned.
SCANNED = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "advisors",
    REPO_ROOT / "frameworks",
    REPO_ROOT / "skills",
    REPO_ROOT / "agents",
    REPO_ROOT / "e2e" / "scenarios",
    TRIGGER_MAP,
]

OLD_NAME = re.compile(r"the-qa-engineer|QA Engineer", re.IGNORECASE)


def _registry():
    with open(REGISTRY) as f:
        return yaml.safe_load(f)


def _advisors():
    return {a["id"]: a for a in _registry()["advisors"]}


def _frameworks():
    with open(FW_REGISTRY) as f:
        return {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}


def _files():
    for root in SCANNED:
        paths = [root] if root.is_file() else root.rglob("*")
        for p in paths:
            if "node_modules" in p.parts:
                continue
            if not p.is_file() or p.suffix not in {".md", ".yaml", ".yml", ".html", ".json"}:
                continue
            yield p


def test_michael_bolton_is_registered_with_a_prompt():
    entry = _advisors()["michael-bolton"]
    assert entry["name"] == "Michael Bolton"
    assert entry["prompt"] == "advisors/prompts/michael-bolton.md"
    assert PROMPT.is_file()
    assert RESEARCH.is_file()
    for field in ("best_for", "not_for", "evaluation_expertise", "summary"):
        assert entry.get(field, "").strip(), f"michael-bolton needs {field}"


def test_michael_bolton_covers_the_qa_engineers_review_domains():
    domains = set(_advisors()["michael-bolton"]["domains"])
    for needed in ("edge-cases", "failure-modes", "testing", "fact-checking"):
        assert needed in domains


def test_the_qa_engineer_is_retired():
    assert "the-qa-engineer" not in _advisors()
    assert not OLD_PROMPT.exists()


def test_nothing_shipped_names_the_qa_engineer():
    hits = []
    for p in _files():
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if OLD_NAME.search(line):
                hits.append(f"{p.relative_to(REPO_ROOT)}:{n}: {line.strip()}")
    assert not hits, "Still names The QA Engineer:\n" + "\n".join(hits)


def test_michael_bolton_is_the_first_choice_fact_checker():
    text = ORCHESTRATION.read_text(encoding="utf-8")
    assert "Priority: Michael Bolton > The Architect > first selected critic" in text


def test_calibration_example_names_michael_bolton():
    examples = _registry()["selection_guidelines"]["calibration_examples"]
    critics = [c for ex in examples for c in ex["critics"]]
    assert "michael-bolton" in critics


def test_proof_points_audit_moves_to_michael_bolton():
    entry = _frameworks()["proof-points-audit"]
    assert entry["advisor"] == "michael-bolton"
    prompt = (PROOF / "prompt.md").read_text(encoding="utf-8")
    first = [l for l in prompt.split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Michael Bolton, guiding someone through Proof Points Audit - ")
    assert "Claims" in prompt and "oracle" in prompt.lower()
    readme = (REPO_ROOT / "frameworks" / "README.md").read_text(encoding="utf-8")
    assert "| proof-points-audit | Proof Points Audit | michael-bolton |" in readme
    assert "- **proof-points-audit** — Proof Points Audit (michael-bolton)" in readme


def test_proof_points_audit_keeps_its_seven_phases_and_waits():
    text = (PROOF / "prompt.md").read_text(encoding="utf-8")
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    phases = {int(parts[i]): parts[i + 1].split("## Key Rules")[0] for i in range(1, len(parts), 2)}
    assert sorted(phases) == [1, 2, 3, 4, 5, 6, 7]
    for n, body in phases.items():
        assert "WAIT for user" in body, f"proof-points-audit PHASE {n} lost its WAIT"


def test_proof_points_audit_has_an_eval_wired_to_it():
    assert PROOF_SCENARIO.is_file()
    assert "frameworks/proof-points-audit/prompt.md" in PROOF_SCENARIO.read_text(encoding="utf-8")
    flat = yaml.safe_dump(yaml.safe_load(TRIGGER_MAP.read_text(encoding="utf-8")))
    assert "frameworks/proof-points-audit/prompt.md" in flat
    assert "scenarios/use-framework/proof-points-audit.yaml" in flat


def test_prompt_is_built_on_his_method_and_names_its_neighbors():
    text = PROMPT.read_text(encoding="utf-8")
    lower = text.lower()
    for term in ("FEW HICCUPPS", "oracle", "checking", "Rapid Software Testing", "Claims", "heuristic"):
        assert term.lower() in lower, f"prompt should use {term}"
    assert "what you never published" in lower
    # Bach's model may be taught only with credit to Bach.
    assert "James Bach" in text
    for neighbor in ("The Architect", "Adam Shostack", "Annie Duke", "Steve Krug"):
        assert neighbor in text, f"prompt should hand off to {neighbor}"


def test_prompt_welcomes_automated_checks():
    lower = PROMPT.read_text(encoding="utf-8").lower()
    assert "tdd" in lower
    assert "never tell" in lower and "stop writing" in lower


def test_consult_scenario_exists_and_is_wired_to_the_prompt():
    assert SCENARIO.is_file()
    assert "advisors/prompts/michael-bolton.md" in SCENARIO.read_text(encoding="utf-8")
    flat = yaml.safe_dump(yaml.safe_load(TRIGGER_MAP.read_text(encoding="utf-8")))
    assert "advisors/prompts/michael-bolton.md" in flat
    assert "scenarios/use-advisor/michael-bolton-consult.yaml" in flat
