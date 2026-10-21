"""Why My Page Doesn't Rank: Aleyda Solis's ten-question diagnostic for one page.

Quoted from learningseo.io. The questions run in order: crawlable, indexable,
more relevant than the top ranked pages, more helpful, better user experience,
internally linked and in the XML sitemap, more and better links, good links
disavowed, a manual action, a more compelling search result. This version is
for one person on one page of a small new site, with free tools (Search
Console, PageSpeed Insights), and says which questions rarely apply to a new
domain. It ends with one fix to make first, not a list of everything.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "why-my-page-doesnt-rank"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "aleyda-solis.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "why-my-page-doesnt-rank.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _phases(text: str) -> dict:
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    return {int(parts[i]): parts[i + 1].split("## Key Rules")[0] for i in range(1, len(parts), 2)}


def test_framework_files_exist():
    for p in (PROMPT, EXAMPLES, ANTI):
        assert p.is_file(), f"missing {p.relative_to(REPO_ROOT)}"


def test_registry_entry():
    with open(REPO_ROOT / "frameworks" / "registry.yaml") as f:
        e = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["why-my-page-doesnt-rank"]
    assert e["advisor"] == "aleyda-solis"
    assert e["name"] == "Why My Page Doesn't Rank"
    assert e["category"] == "content-strategy"
    assert e["deliverable_type"] == "analysis"
    assert "ai-search-optimization-checklist" in e.get("follow_on_frameworks", [])


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Aleyda Solis, guiding someone through Why My Page Doesn't Rank - ")


def test_every_phase_waits_for_the_user():
    phases = _phases(_read(PROMPT))
    assert len(phases) == 9
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"


def test_prompt_asks_all_ten_questions_in_her_words():
    text = _read(PROMPT)
    for q in ("Is the page Crawlable?",
              "Is the page Indexable?",
              "Is the Page Content More Relevant than the Top Ranked Pages for Target Queries?",
              "more Helpful/Comprehensive/Authoritative than Top Ranked Pages",
              "Is the Page giving a Good User Experience",
              "included in XML sitemap?",
              "attracting More and Better Quality Links",
              "being disavowed?",
              "affected by a Google Manual Action?",
              "more descriptive, attractive and compelling"):
        assert q in text, f"prompt should ask: {q}"


def test_crawl_and_index_come_before_content_and_links():
    text = _read(PROMPT)
    assert text.index("Is the page Crawlable?") < text.index("Is the Page Content More Relevant")
    assert text.index("Is the page Indexable?") < text.index("attracting More and Better Quality Links")


def test_prompt_uses_free_tools_and_flags_new_domain_questions():
    text = _read(PROMPT)
    for tool in ("Search Console", "URL Inspection", "PageSpeed Insights"):
        assert tool in text, f"prompt should use {tool}"
    low = text.lower()
    assert "new domain" in low
    assert "rarely applies" in low or "rarely apply" in low


def test_prompt_ends_with_one_first_fix():
    assert "one fix" in _read(PROMPT).lower()


def test_prompt_hands_off_what_she_does_not_do():
    text = _read(PROMPT)
    for handoff in ("`ai-search-optimization-checklist`", "Joanna Wiebe", "Steve Krug"):
        assert handoff in text


def test_anti_examples_cover_the_failure_modes():
    anti = _read(ANTI).lower()
    for failure in ("buy links", "disavow", "indexed", "keyword", "everything"):
        assert failure in anti, f"anti-examples should cover {failure}"


def test_examples_explain_why_they_work():
    ex = _read(EXAMPLES)
    assert ex.count("**Why it works:**") >= 6
    for kind in ("Golden path", "Struggle", "Edge case"):
        assert kind in ex


def test_advisor_prompt_lists_the_framework():
    assert "`why-my-page-doesnt-rank`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/why-my-page-doesnt-rank/prompt.md", "frameworks/why-my-page-doesnt-rank/examples.md",
              "frameworks/why-my-page-doesnt-rank/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/why-my-page-doesnt-rank.yaml" in flat
