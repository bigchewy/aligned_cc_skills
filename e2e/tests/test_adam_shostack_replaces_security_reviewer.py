"""Adam Shostack replaces The Security Reviewer.

The Security Reviewer was a generic archetype with no published method. Adam
Shostack (Threat Modeling: Designing for Security, the Four Question
Framework, STRIDE, PHANTOM-B) takes its job: reviewing a design for what can
go wrong with auth, access control, data exposure, injection, and LLM parts.
He also takes Boris Cherny's hand-off for threat review of hooks, MCP servers,
and plugins. Nothing in the shipped plugin may still name the old advisor.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = REPO_ROOT / "advisors" / "registry.yaml"
PROMPT = REPO_ROOT / "advisors" / "prompts" / "adam-shostack.md"
OLD_PROMPT = REPO_ROOT / "advisors" / "prompts" / "the-security-reviewer.md"
RESEARCH = REPO_ROOT / "docs" / "advisors" / "new_advisors" / "v_adam-shostack.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "adam-shostack-consult.yaml"
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

OLD_NAME = re.compile(r"the-security-reviewer|Security Reviewer")


def _registry():
    with open(REGISTRY) as f:
        return yaml.safe_load(f)


def _advisors():
    return {a["id"]: a for a in _registry()["advisors"]}


def _files():
    for root in SCANNED:
        paths = [root] if root.is_file() else root.rglob("*")
        for p in paths:
            if "node_modules" in p.parts:
                continue
            if not p.is_file() or p.suffix not in {".md", ".yaml", ".yml", ".html", ".json"}:
                continue
            yield p


def test_adam_shostack_is_registered_with_a_prompt():
    entry = _advisors()["adam-shostack"]
    assert entry["name"] == "Adam Shostack"
    assert entry["prompt"] == "advisors/prompts/adam-shostack.md"
    assert PROMPT.is_file()
    assert RESEARCH.is_file()
    for field in ("best_for", "not_for", "evaluation_expertise", "summary"):
        assert entry.get(field, "").strip(), f"adam-shostack needs {field}"


def test_adam_shostack_covers_the_security_reviewers_domains():
    domains = set(_advisors()["adam-shostack"]["domains"])
    for needed in ("authentication", "access-control", "data-exposure", "injection", "threat-modeling"):
        assert needed in domains


def test_research_file_meets_the_evidence_standard():
    text = RESEARCH.read_text(encoding="utf-8")
    assert text.count("✅") >= 40
    for section in ("## Sources", "## Master Concepts", "What he does NOT publish", "## Voice",
                    "## Known critiques", "## Framework Candidates", "## Voice mimicry rating"):
        assert section in text, f"research file needs {section}"
    for q in ("What are we working on?", "What can go wrong?", "What are we going to do about it?",
              "Did we do a good job?"):
        assert q in text


def test_the_security_reviewer_is_retired():
    assert "the-security-reviewer" not in _advisors()
    assert not OLD_PROMPT.exists()


def test_nothing_shipped_names_the_security_reviewer():
    hits = []
    for p in _files():
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if OLD_NAME.search(line):
                hits.append(f"{p.relative_to(REPO_ROOT)}:{n}: {line.strip()}")
    assert not hits, "Still names The Security Reviewer:\n" + "\n".join(hits)


def test_hand_offs_now_name_adam_shostack():
    assert "Adam Shostack" in (REPO_ROOT / "advisors" / "prompts" / "boris-cherny.md").read_text(encoding="utf-8")
    assert "Adam Shostack" in _advisors()["boris-cherny"]["not_for"]


def test_critic_calibration_examples_use_adam_shostack():
    examples = _registry()["selection_guidelines"]["calibration_examples"]
    picked = [e for e in examples if "adam-shostack" in e["critics"]]
    assert len(picked) == 2
    assert any("RLS" in e["scope"] for e in picked)


def test_prompt_carries_his_method_and_names_its_neighbors():
    text = PROMPT.read_text(encoding="utf-8")
    for term in ("What are we working on?", "What can go wrong?", "What are we going to do about it?",
                 "Did we do a good job?", "STRIDE", "Spoofing", "Tampering", "Repudiation",
                 "Information Disclosure", "Denial of Service", "Elevation of Privilege", "PHANTOM-B",
                 "boundary"):
        assert term.lower() in text.lower(), f"prompt should use {term}"
    assert "what you never published" in text.lower()
    # Eric's stack: the persona applies STRIDE to it and says where the method stops.
    for stack in ("Supabase", "row-level security", "Vercel", "Resend", "hook", "MCP"):
        assert stack.lower() in text.lower(), f"prompt should cover {stack}"
    for neighbor in ("Boris Cherny", "The Architect", "Kim Wuyts"):
        assert neighbor in text, f"prompt should hand off to {neighbor}"


def test_consult_scenario_exists_and_is_wired_to_the_prompt():
    assert SCENARIO.is_file()
    assert "advisors/prompts/adam-shostack.md" in SCENARIO.read_text(encoding="utf-8")
    flat = yaml.safe_dump(yaml.safe_load(TRIGGER_MAP.read_text(encoding="utf-8")))
    assert "advisors/prompts/adam-shostack.md" in flat
    assert "scenarios/use-advisor/adam-shostack-consult.yaml" in flat
