"""create-design-principles is run by Adham Dannaway and critiqued by three real advisors.

Dannaway interviews the builder and writes the file from his published method
(colour by role, a type scale from a base and a ratio, two weights, t-shirt
spacing, three radii, two shadows, one primary button). He asks about feeling
plainly but never claims a method for it. Steve Jobs (feeling and point of
view), Brad Frost (can screens be built from it), and Steve Krug (can people
use it) critique the file; the two generic voices are gone. The skill ships
examples.md and anti-examples.md.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "create-design-principles"
SKILL = SKILL_DIR / "SKILL.md"
CHECKLIST = SKILL_DIR / "design-critique-checklist.md"
EXAMPLES = SKILL_DIR / "examples.md"
ANTI = SKILL_DIR / "anti-examples.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-skill" / "design-principles-dannaway.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    assert match, f"missing '## {heading}' section"
    return match.group(1)


class TestPersona:
    def test_dannaway_runs_the_skill(self):
        text = _read(SKILL)
        assert "advisors/prompts/adham-dannaway.md" in text
        assert "Adham Dannaway" in text.split("\n## ")[0] + _section(text, "Persona: Adham Dannaway (REQUIRED)")

    def test_jobs_no_longer_runs_the_interview(self):
        text = _read(SKILL)
        assert "You ARE Steve Jobs" not in text
        assert "Persona: Steve Jobs" not in text
        assert "That's shit" not in text
        discovery = _section(text, "Phase 1: Discovery (Interactive)")
        assert "Steve" not in discovery

    def test_feeling_is_asked_but_not_claimed_as_his(self):
        persona = _section(_read(SKILL), "Persona: Adham Dannaway (REQUIRED)").lower()
        assert "feeling" in persona
        assert "never published" in persona or "not his method" in persona


class TestDefaultsComeFromHisMethod:
    def test_colour_roles(self):
        text = _read(SKILL)
        for role in ("Brand", "Text strong", "Text weak", "Stroke strong", "Stroke weak", "Fill"):
            assert role in text

    def test_type_spacing_depth_buttons(self):
        defaults = _section(_read(SKILL), "Starting Defaults").lower()
        for rule in ("1.2", "divisible by 4", "regular and bold", "t-shirt", "8px, 16px, and 32px",
                     "raised and overlay", "one primary", "48px"):
            assert rule in defaults, f"Starting Defaults should state {rule}"

    def test_defaults_are_credited(self):
        assert "Practical UI" in _section(_read(SKILL), "Starting Defaults")

    def test_floor_still_wins(self):
        floor = _section(_read(SKILL), "Quality Floor")
        assert "44px" in floor


class TestCritiquePanel:
    def test_three_named_advisors(self):
        text = _read(SKILL) + _read(CHECKLIST)
        for path in ("advisors/prompts/steve-jobs.md", "advisors/prompts/brad-frost.md",
                     "advisors/prompts/steve-krug.md"):
            assert path in text, f"critique must load {path}"

    def test_generic_voices_are_gone(self):
        text = _read(SKILL) + _read(CHECKLIST)
        assert "Senior Product Designer" not in text
        assert "Customer Experience Lead" not in text

    def test_dannaway_aggregates_but_does_not_critique(self):
        critique = _section(_read(SKILL), "Design Critique (mandatory after design work)")
        assert "Aggregation (in Adham Dannaway's voice)" in critique
        assert "Steve Jobs' voice" not in _read(SKILL)

    def test_feeling_findings_go_to_the_builder(self):
        critique = _section(_read(SKILL), "Design Critique (mandatory after design work)").lower()
        assert "builder" in critique and "feeling" in critique


class TestExamples:
    def test_files_exist_and_are_read(self):
        assert EXAMPLES.is_file() and ANTI.is_file()
        text = _read(SKILL)
        assert "examples.md" in text and "anti-examples.md" in text

    def test_examples_show_roles_with_ratios(self):
        ex = _read(EXAMPLES)
        assert "Text strong" in ex and ":1" in ex

    def test_anti_examples_cover_his_failures(self):
        anti = _read(ANTI).lower()
        for failure in ("pure black", "primary button", "colour alone", "weights"):
            assert failure in anti


class TestEval:
    def test_scenario_is_wired(self):
        assert SCENARIO.is_file()
        text = _read(SCENARIO)
        assert "skills/create-design-principles/SKILL.md" in text
        assert "advisors/prompts/adham-dannaway.md" in text
        tm = _read(TRIGGER_MAP)
        assert "scenarios/use-skill/design-principles-dannaway.yaml" in tm
        assert "skills/create-design-principles/SKILL.md" in tm
