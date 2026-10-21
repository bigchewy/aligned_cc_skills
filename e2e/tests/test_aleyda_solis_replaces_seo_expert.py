"""Aleyda Solis replaces SEO Expert.

SEO Expert was a generic archetype with no published method. Aleyda Solis
(Orainti, LearningSEO.io, LearningAIsearch.com, SEOFOMO, Crawling Mondays)
takes its job: judging whether a page can rank in Google and be cited by AI
search. She brings two fixed checklists from her own sites: the ten-question
"Why my Page Doesn't Rank" diagnostic and the twelve-step AI Search
Optimization Checklist. Nothing in the shipped plugin may still name the old
advisor, and the content and landing-page advisors that ruled out SEO now
hand it to her.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = REPO_ROOT / "advisors" / "registry.yaml"
PROMPT = REPO_ROOT / "advisors" / "prompts" / "aleyda-solis.md"
OLD_PROMPT = REPO_ROOT / "advisors" / "prompts" / "seo-expert.md"
RESEARCH = REPO_ROOT / "docs" / "advisors" / "new_advisors" / "v_aleyda-solis.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "aleyda-solis-consult.yaml"
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

OLD_NAME = re.compile(r"seo-expert|SEO Expert", re.IGNORECASE)


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


def test_aleyda_solis_is_registered_with_a_prompt():
    entry = _registry()["aleyda-solis"]
    assert entry["name"] == "Aleyda Solis"
    assert entry["prompt"] == "advisors/prompts/aleyda-solis.md"
    assert PROMPT.is_file()
    assert RESEARCH.is_file()
    for field in ("best_for", "not_for", "evaluation_expertise", "summary"):
        assert entry.get(field, "").strip(), f"aleyda-solis needs {field}"


def test_aleyda_solis_covers_the_seo_review_domains():
    domains = set(_registry()["aleyda-solis"]["domains"])
    for needed in ("seo", "search-optimization", "ai-search-optimization"):
        assert needed in domains


def test_seo_expert_is_retired():
    assert "seo-expert" not in _registry()
    assert not OLD_PROMPT.exists()


def test_nothing_shipped_names_seo_expert():
    hits = []
    for p in _files():
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if OLD_NAME.search(line):
                hits.append(f"{p.relative_to(REPO_ROOT)}:{n}: {line.strip()}")
    assert not hits, "Still names SEO Expert:\n" + "\n".join(hits)


def test_content_and_landing_page_advisors_hand_seo_to_aleyda():
    reg = _registry()
    for slug in ("joe-pulizzi", "joanna-wiebe", "oli-gardner"):
        assert "Aleyda Solis" in reg[slug].get("not_for", ""), f"{slug} not_for should name Aleyda Solis"


def test_research_file_meets_the_evidence_standard():
    text = RESEARCH.read_text(encoding="utf-8")
    assert text.count("✅") >= 40, "research file needs 40+ quotes read on her own pages this session"
    for section in ("## Sources", "## Master Concepts", "What she does NOT publish", "## Voice",
                    "## Known critiques", "## Framework Candidates", "## Voice mimicry rating"):
        assert section in text, f"research file missing {section}"
    assert "learningseo.io/seo_roadmap/train-test-troubleshoot-your-seo-further/why-my-page-doesnt-rank" in text


def test_prompt_is_built_on_her_checklists_and_names_its_neighbors():
    text = PROMPT.read_text(encoding="utf-8")
    for term in ("Why my Page Doesn't Rank", "Crawlable", "Indexable", "Top Ranked Pages",
                 "Search Console", "good SEO is good GEO", "citation"):
        assert term.lower() in text.lower(), f"prompt should use {term}"
    assert "what you never published" in text.lower()
    for neighbor in ("Joe Pulizzi", "Joanna Wiebe", "April Dunford", "Steve Krug"):
        assert neighbor in text, f"prompt should hand off to {neighbor}"


def test_prompt_lists_both_frameworks():
    text = PROMPT.read_text(encoding="utf-8")
    assert "`why-my-page-doesnt-rank`" in text
    assert "`ai-search-optimization-checklist`" in text


def test_consult_scenario_exists_and_is_wired_to_the_prompt():
    assert SCENARIO.is_file()
    assert "advisors/prompts/aleyda-solis.md" in SCENARIO.read_text(encoding="utf-8")
    flat = yaml.safe_dump(yaml.safe_load(TRIGGER_MAP.read_text(encoding="utf-8")))
    assert "advisors/prompts/aleyda-solis.md" in flat
    assert "scenarios/use-advisor/aleyda-solis-consult.yaml" in flat
