"""add-advisor and add-framework are checked at the end, and their content is sourced.

Audits of 13 add-advisor runs and 16 add-framework runs (Sept 29 to Oct 28, 2026)
found steps done thinly rather than merged. In one run, the model built one framework
per advisor ("the skill's own minimum") and said "I didn't read the work." Voice phrases
and framework phases came from memory: one framework's phases were invented, and another
turned out to be a different group's method. The count step missed the two registry
READMEs, which broke the freshness tests twice. Nothing at the end checked any of it.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ADVISOR = REPO / "skills" / "add-advisor"
FRAMEWORK = REPO / "skills" / "add-framework"


def read(path):
    return path.read_text(encoding="utf-8")


def step(text, number):
    # Stop at the next numbered step or a top-level section. Step 4 holds a code block
    # with its own "## " headings, so a bare "\n## " can't end a step.
    m = re.search(rf"### {number}\. (.*?)(?=\n### \d+\. |\n## [A-Z][^\n]*\n\n(?!```)|\Z)", text, re.S)
    assert m, f"step {number} missing"
    return m.group(0)


# --- shared shape --------------------------------------------------------------


@pytest.mark.parametrize("skill", [ADVISOR, FRAMEWORK])
def test_report_template_has_a_skipped_section_and_check_instructions(skill):
    text = read(skill / "report-template.md")
    assert "## What was skipped or not done" in text
    assert "## Check agent" in text
    assert "Nothing" in text


@pytest.mark.parametrize("skill", [ADVISOR, FRAMEWORK])
def test_skill_ends_with_a_fresh_agent_check_and_report(skill):
    text = read(skill / "SKILL.md")
    assert "report-template.md" in text
    assert "fresh agent" in text.lower()
    assert "What was skipped or not done" in text


@pytest.mark.parametrize("skill", [ADVISOR, FRAMEWORK])
def test_anti_examples_come_from_real_runs(skill):
    text = read(skill / "anti-examples.md")
    assert text.count("## ") >= 4
    assert "Right:" in text and "Wrong:" in text


@pytest.mark.parametrize("skill", [ADVISOR, FRAMEWORK])
def test_counts_step_covers_both_registry_readmes(skill):
    text = read(skill / "SKILL.md")
    m = re.search(r"### \d+\. Update Advisor and Framework Counts\n(.*?)(?=\n### |\n## |\Z)", text, re.S)
    section = m.group(1)
    assert "advisors/README.md" in section
    assert "frameworks/README.md" in section
    assert "test_readme_freshness.py" in section


@pytest.mark.parametrize("skill", [ADVISOR, FRAMEWORK])
def test_skill_says_to_finish_when_started_inside_another_task(skill):
    assert "inside another task" in read(skill / "SKILL.md").lower()


# --- add-advisor ----------------------------------------------------------------


def test_add_advisor_builds_every_selected_framework():
    text = read(ADVISOR / "SKILL.md")
    assert "Add First Framework" not in text
    five = step(text, 5)
    assert "every framework" in five.lower()
    assert "/aligned:add-framework" in five


def test_add_advisor_always_writes_a_research_file():
    text = read(ADVISOR / "SKILL.md")
    assert "in-memory" not in text
    one = step(text, 1)
    assert "URL" in one


def test_add_advisor_voice_phrases_come_from_the_research_file():
    text = read(ADVISOR / "SKILL.md")
    assert "word for word" in step(text, 4).lower()


def test_add_advisor_puts_repo_specific_frameworks_in_the_project():
    two = step(read(ADVISOR / "SKILL.md"), 2).lower()
    assert "one project" in two
    assert "project repo" in two


def test_add_advisor_batch_agents_read_the_skill_themselves():
    text = read(ADVISOR / "SKILL.md").lower()
    assert "several advisors at once" in text
    assert "read this skill" in text


# --- add-framework --------------------------------------------------------------


def test_add_framework_checks_the_method_is_the_experts_own():
    text = read(FRAMEWORK / "SKILL.md")
    assert "own published method" in text.lower()


def test_add_framework_writes_sources_for_every_phase():
    text = read(FRAMEWORK / "SKILL.md")
    assert "sources.md" in step(text, 1)
    assert "Added:" in text


def test_add_framework_does_not_invent_categories():
    text = read(FRAMEWORK / "SKILL.md").lower()
    assert "existing category" in text
    assert "new category" in text


def test_add_framework_check_tests_the_first_line_loads():
    text = read(FRAMEWORK / "report-template.md")
    assert "You are {Advisor}, guiding someone through" in text
