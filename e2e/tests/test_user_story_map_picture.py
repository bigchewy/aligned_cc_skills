"""The User Story Map framework always draws the map and ends with Slice 1 wireframes.

Guards the contract added after the 2026-10-13 planted run, where "build the
map as text for me to review before any screens" was read as "no picture."
The picture starts as soon as the frame locks in Phase 1, wording in a request
can't turn it off, and Phase 8 wireframes Slice 1 into a second tab of the same
page. The design-principles lookup also finds monorepo files under
brand/*/guidelines/.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "user-story-map"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
TEMPLATE = FRAMEWORK / "story-map-template.html"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "jeff-patton.md"
PICTURE_SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "user-story-map-picture.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _phase(text: str, n: int) -> str:
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        if int(parts[i]) == n:
            return parts[i + 1].split("## Key Rules")[0]
    raise AssertionError(f"PHASE {n} not found")


class TestPictureCannotBeTurnedOff:
    def test_map_on_screen_reads_text_wording_as_no_screens_yet(self):
        prompt = _read(PROMPT)
        section = prompt.split("### The map on screen")[1].split("### PHASE 1")[0]
        for phrase in ('"as text', '"for review', '"before any screens'):
            assert phrase in section, f"{phrase} must be named as wording that keeps the picture"
        assert "no screens yet" in section
        assert "confirm once" in section

    def test_key_rules_repeat_it(self):
        rules = _read(PROMPT).split("## Key Rules")[1]
        assert "can't turn it off" in rules
        assert "confirm once" in rules


class TestPictureStartsAtPhaseOne:
    def test_phase_one_draws_after_the_frame_locks(self):
        phase1 = _phase(_read(PROMPT), 1)
        lock = phase1.index("**Lock:**")
        assert "**Draw the map.**" in phase1[lock:], "Phase 1 must draw the map after its lock"
        assert "empty backbone" in phase1[lock:]

    def test_setup_happens_in_phase_one_not_before_phase_two(self):
        prompt = _read(PROMPT)
        assert "before Phase 2" not in prompt
        assert "do the setup in" not in _phase(prompt, 2)

    def test_template_renders_with_no_activities(self):
        data = _template_data()
        assert "lanes" in data and "wireframes" in data


class TestPhaseEight:
    def test_phase_eight_wireframes_slice_one(self):
        prompt = _read(PROMPT)
        assert re.search(r"^### PHASE 8: Wireframe Slice 1$", prompt, flags=re.MULTILINE)
        phase8 = _phase(prompt, 8)
        assert "one wireframe per activity" in phase8
        assert "**WAIT for the user to respond.**" in phase8
        assert "card" in phase8 and "design-principles.md" in phase8
        assert "second tab" in phase8 or "Wireframes tab" in phase8

    def test_phase_seven_no_longer_stops_at_ready_for_wireframes(self):
        phase7 = _phase(_read(PROMPT), 7)
        assert "ready for wireframes" not in phase7
        assert "No screens and no wireframes." not in phase7
        assert "Phase 8" in phase7

    def test_no_rule_still_bans_wireframes_outright(self):
        prompt = _read(PROMPT)
        assert "never draws a screen, a wireframe" not in prompt
        assert "No wireframes, page layouts, or field lists at any phase" not in prompt
        rules = prompt.split("## Key Rules")[1]
        assert "Slice 1" in rules and "wirefram" in rules.lower()

    def test_examples_have_a_phase_eight_golden_path(self):
        examples = _read(EXAMPLES)
        assert "## PHASE 8: Wireframe Slice 1" in examples
        phase8 = examples.split("## PHASE 8: Wireframe Slice 1")[1]
        assert "### Golden path" in phase8
        assert "Check who's ready" in phase8, "Phase 8 example must use the team-course map"


class TestAntiExample:
    def test_map_as_text_before_screens_anti_example(self):
        anti = _read(ANTI)
        m = re.search(r"^## \d+\. .*as text before screens.*$", anti, flags=re.IGNORECASE | re.MULTILINE)
        assert m, "an anti-example must be titled for 'map as text before screens'"
        block = anti[m.end() :].split("\n## ")[0]
        assert "**Wrong:**" in block and "**Right:**" in block
        assert "Slice 1" in block.split("**Right:**")[1]


class TestAdvisor:
    def test_core_frameworks_summary_includes_wireframes(self):
        advisor = _read(ADVISOR)
        assert "No screens. Produces a map ready for wireframes." not in advisor
        core = advisor.split("## Core Frameworks")[1].split("## ")[0]
        assert "wirefram" in core.lower() and "Slice 1" in core

    def test_no_screens_first_says_wireframes_follow_slice_one(self):
        advisor = _read(ADVISOR)
        section = advisor.split("**No screens first.**")[1].split("**No ")[0]
        assert "Slice 1" in section and "wirefram" in section.lower()


class TestDesignPrinciplesLookup:
    def test_lookup_checks_monorepo_brand_folders(self):
        prompt = _read(PROMPT)
        assert "brand/*/guidelines/design-principles.md" in prompt

    def test_lookup_asks_which_app_when_several_match(self):
        section = _read(PROMPT).split("### The map on screen")[1].split("### PHASE 1")[0]
        assert "which app" in section


def _template_data() -> dict:
    html = _read(TEMPLATE)
    m = re.search(r'<script type="application/json" id="map-data">(.*?)</script>', html, flags=re.S)
    assert m, "template must keep the map-data JSON block"
    return json.loads(m.group(1))


class TestTemplate:
    def test_template_has_map_and_wireframe_tabs(self):
        html = _read(TEMPLATE)
        assert 'data-tab="map"' in html
        assert 'data-tab="wireframes"' in html

    def test_template_wireframe_elements_name_their_card(self):
        data = _template_data()
        assert data["wireframes"], "template must show the wireframe data shape"
        for wf in data["wireframes"]:
            assert wf.get("activity")
            for element in wf["elements"]:
                assert element.get("card"), "every wireframe element names the map card it comes from"

    def test_only_one_template(self):
        htmls = sorted(p.name for p in FRAMEWORK.glob("*.html"))
        assert htmls == ["story-map-template.html"]

    @pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
    def test_template_script_parses(self, tmp_path):
        html = _read(TEMPLATE)
        scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
        assert scripts
        js = tmp_path / "template.js"
        js.write_text("\n".join(scripts), encoding="utf-8")
        result = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


class TestEval:
    def test_picture_scenario_exists_and_is_triggered(self):
        assert PICTURE_SCENARIO.exists()
        assert "scenarios/use-framework/user-story-map-picture.yaml" in _read(TRIGGER_MAP)
