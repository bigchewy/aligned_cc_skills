"""create-design-principles keeps taste out of the quality floor and checks the floor mechanically.

Guards the contract added in 0.33.23: the floor holds only things you can
measure (contrast, line length in characters, tap targets, states, themed
browser defaults). Taste calls the skill used to hand every product (Phosphor
Icons, weight-600 headlines at -0.02em, no native form elements, "margins >
48px" as an anti-pattern) are Phase 1 questions instead. Every generated file
carries a Motion section and a States section, and after the critique panel
the skill runs `npx impeccable detect`, with the principles file overruling
any finding that conflicts with a choice it makes on purpose.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL = REPO_ROOT / "skills" / "create-design-principles" / "SKILL.md"


def _skill() -> str:
    return SKILL.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Body of a `## heading` section, up to the next `## ` heading."""
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    assert match, f"missing '## {heading}' section"
    return match.group(1)


class TestTasteIsNotTheFloor:
    def test_no_icon_library_is_prescribed(self):
        assert "phosphor" not in _skill().lower()

    def test_no_headline_weight_or_tracking_is_prescribed(self):
        text = _skill()
        assert "-0.02em" not in text
        assert not re.search(r"Headlines?:\s*600", text)

    def test_native_form_elements_are_not_banned(self):
        assert "Never use native form elements" not in _skill()

    def test_generous_section_spacing_is_not_an_anti_pattern(self):
        text = _skill()
        assert "margins > 48px" not in text
        assert "Excessive spacing" not in text

    def test_the_old_floor_heading_is_gone(self):
        assert "## Core Craft Principles" not in _skill()


class TestDiscoveryAsksTheTasteCalls:
    def test_phase_one_asks_each_taste_call(self):
        discovery = _section(_skill(), "Phase 1: Discovery (Interactive)").lower()
        for topic in ("icon", "headline", "between sections", "native"):
            assert topic in discovery, f"Phase 1 must ask about {topic!r}"

    def test_the_brand_file_beats_the_skill_defaults(self):
        text = _skill()
        assert "The principles file wins" in text


class TestQualityFloor:
    def test_floor_names_each_measurable_check(self):
        floor = _section(_skill(), "Quality Floor")
        assert "4.5:1" in floor
        assert "44px" in floor
        for state in ("loading", "error", "empty", "focus"):
            assert state in floor.lower(), f"floor must require a {state} state"
        assert "selection" in floor.lower() and "focus ring" in floor.lower()

    def test_line_length_is_in_characters_checked_in_the_font(self):
        floor = _section(_skill(), "Quality Floor")
        assert "characters" in floor
        assert "width of a zero" in floor, "the floor must say why a ch limit is not a character limit"


class TestRequiredOutputSections:
    def test_motion_and_states_are_required_sections(self):
        output = _section(_skill(), "Output: design-principles.md")
        assert "## Motion" in output
        assert "## States and Browser Defaults" in output
        assert "REQUIRED" in output

    def test_iconography_stays_a_section_for_create_image(self):
        """create-image's icon mode stops if the file has no Iconography section."""
        output = _section(_skill(), "Output: design-principles.md")
        assert "## Iconography" in output


class TestMechanicalCheck:
    def test_runs_impeccable_after_the_critique(self):
        text = _skill()
        critique = text.index("## Design Critique")
        check = text.index("## Mechanical Check")
        assert check > critique, "the mechanical check runs after the three-voice critique"
        body = _section(text, "Mechanical Check")
        assert "npx impeccable detect" in body
        assert "--json" in body
        assert "localhost" in body or "dev server" in body

    def test_principles_file_overrules_conflicting_findings(self):
        body = _section(_skill(), "Mechanical Check").lower()
        assert "overrule" in body
        assert "everything else gets fixed" in body

    def test_does_not_adopt_impeccable_formats_or_hooks(self):
        text = _skill()
        assert "DESIGN.md" not in text
        assert "impeccable install" not in text
