"""The Rumelt frameworks lock each element at page size and close with pages sized to targets.

Guards the contract added in 0.33.11: kernel-of-good-strategy delivers a
short deck (page one about 200 words, detail pages about 120) assembled from
lines locked in the phase that produced them, and ships a one-page SVG
example plus a deck-building script next to it; finding-the-crux delivers
one 200-word page the same way. The examples use REM Medical's kernel with
its founder's permission and must carry no other client's material.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORKS = REPO_ROOT / "frameworks"
KERNEL_DIR = FRAMEWORKS / "kernel-of-good-strategy"
CRUX_DIR = FRAMEWORKS / "finding-the-crux"
ONE_PAGE_SVG = KERNEL_DIR / "kernel-one-page-example.svg"
DECK_SCRIPT = KERNEL_DIR / "build-example-deck.py"
DECK_PPTX = KERNEL_DIR / "example-strategy-kernel.pptx"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

OTHER_CLIENT_MATERIAL = ("vindara", "paddy", "me/cfs", "long covid", "acme hr")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _svg_words(text: str) -> int:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    visible = " ".join(m for m in re.findall(r">([^<]+)<", text) if m.strip())
    visible = re.sub(r"&#\d+;", " ", visible)
    return len(visible.split())


class TestKernelPrompt:
    def test_prompt_states_page_targets(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        assert re.search(r"\b200 words\b", prompt), "page one must target 200 words"
        assert re.search(r"\b120 words\b", prompt), "detail pages must target 120 words"
        assert "350 words" not in prompt and "150 words" not in prompt

    def test_prompt_locks_in_the_producing_phases_not_at_the_end(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        locks = re.findall(r"^Lock:", prompt, flags=re.MULTILINE)
        assert len(locks) >= 5, (
            f"expected Lock steps after diagnosis, actions, coherence, kill list, and assumptions; found {len(locks)}"
        )
        assembly = prompt.split("### PHASE 9")[1]
        assert "Nothing is written new here" in assembly
        assert "go back to that phase" in assembly

    def test_prompt_demands_one_sentence_challenge(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        assert "**Challenge:** [one sentence, about 25 words" in prompt

    def test_prompt_demands_three_owned_actions_with_goals_and_no_shares(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        assert "Exactly three" in prompt
        assert "3-5 specific actions" not in prompt
        assert "each one has an owner" in prompt
        assert "a number, a date, and an owner" in prompt
        assert "sum to 100" not in prompt and "[share]" not in prompt, "effort shares are gone"

    def test_prompt_refuses_exit_conditions_on_key_actions(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        assert "A key action has no exit condition" in prompt
        assert "metric or an exit condition" not in prompt

    def test_prompt_keeps_the_kill_list_off_page_one(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        assert "re-entry condition" in prompt.lower()
        page_one = prompt.split("Page one, about 200 words")[1].split("The detail pages")[0]
        assert "Kill list" not in page_one, "page one is what the company is doing; the kill list has its own page"
        assert "| The kill list | Two columns" in prompt
        assert "never on page one" in prompt

    def test_prompt_elicits_assumptions_and_questions(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        assert "### PHASE 8: What We're Standing On" in prompt
        assert "break condition" in prompt.lower()
        assert "question without an owner" in prompt

    def test_prompt_references_the_svg_and_the_deck_script(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        assert ONE_PAGE_SVG.name in prompt
        assert DECK_SCRIPT.name in prompt
        assert "Never hand-edit the deck" in prompt


class TestKernelExamples:
    def test_one_page_svg_exists_and_is_complete(self):
        assert ONE_PAGE_SVG.exists(), f"missing {ONE_PAGE_SVG}"
        text = _read(ONE_PAGE_SVG).strip()
        assert text.startswith("<svg ") and text.endswith("</svg>")
        assert 'viewBox="0 0 1200 660"' in text

    def test_one_page_svg_is_rem_medical_near_the_target(self):
        text = _read(ONE_PAGE_SVG)
        assert "REM MEDICAL" in text
        lowered = text.lower()
        for client in OTHER_CLIENT_MATERIAL:
            assert client not in lowered, f"SVG carries other client material: {client!r}"
        assert "KEY ACTION 1" in text and "KEY ACTION 3" in text and "KEY ACTION 4" not in text
        assert "% of effort" not in text, "effort shares are gone"
        assert "Owner:" in text
        assert "THIS YEAR" in text, "the year's goals belong on page one"
        assert text.count("THIS YEAR") == 3
        assert "Exit:" not in text, "no exit conditions on key actions"
        assert "KILL LIST" not in text, "page one is what the company is doing; the kill list has its own page"
        words = _svg_words(text)
        assert 150 <= words <= 260, f"page one should land near 200 words, got {words}"

    def test_challenge_and_policy_are_centered_in_their_bands(self):
        """Label and sentence share a baseline inside each band (the earlier layout sat the sentence low)."""
        text = _read(ONE_PAGE_SVG)
        label_y = int(re.search(r'y="(\d+)"[^>]*>CHALLENGE<', text).group(1))
        sentence_y = int(re.search(r'y="(\d+)"[^>]*>It is likely', text).group(1))
        assert abs(label_y - sentence_y) <= 2

    def test_deck_script_and_deck_exist(self):
        assert DECK_SCRIPT.exists() and DECK_PPTX.exists()
        script = _read(DECK_SCRIPT)
        for marker in ("KILL_LIST", "ASSUMPTIONS", "QUESTIONS", "WHAT WE'RE STANDING ON"):
            assert marker in script
        assert "Exit:" not in script, "no exit conditions on key actions"
        assert '"share"' not in script, "effort shares are gone"
        assert len(re.findall(r'"goals": \[', script)) == 3
        assert "Fuel the engine" in script
        assert "sleep technologists" not in script, "only the goals from the original plan"
        lowered = script.lower()
        for client in OTHER_CLIENT_MATERIAL:
            assert client not in lowered, f"deck script carries other client material: {client!r}"
        assert "illustrative" in script, "the script must say which content was not on the original page"

    def test_deck_has_seven_slides(self):
        pptx = pytest.importorskip("pptx")
        prs = pptx.Presentation(str(DECK_PPTX))
        assert len(prs.slides) == 7, "kernel, challenge+policy, three actions, kill list, assumptions+questions"

    def test_examples_and_anti_examples_show_the_pages(self):
        examples = _read(KERNEL_DIR / "examples.md")
        anti = _read(KERNEL_DIR / "anti-examples.md")
        assert "PHASE 8: What We're Standing On" in examples
        assert "PHASE 9" in examples
        assert "exit" in examples.lower(), "examples.md needs the refused-exit-condition example"
        assert "Phase 9" in anti
        assert "lock" in anti.lower()


class TestCruxPage:
    def test_prompt_states_page_word_target(self):
        prompt = _read(CRUX_DIR / "prompt.md")
        assert re.search(r"\b200 words\b", prompt)

    def test_prompt_locks_in_the_producing_phases(self):
        prompt = _read(CRUX_DIR / "prompt.md")
        locks = re.findall(r"^Lock:", prompt, flags=re.MULTILINE)
        assert len(locks) >= 2
        assert "Nothing is written new here" in prompt.split("### PHASE 7")[1]

    def test_prompt_references_kernel_one_page_for_style(self):
        prompt = _read(CRUX_DIR / "prompt.md")
        assert ONE_PAGE_SVG.name in prompt


class TestEvalCoverage:
    @pytest.mark.parametrize("framework", ["kernel-of-good-strategy", "finding-the-crux"])
    def test_framework_files_are_trigger_mapped(self, framework):
        data = yaml.safe_load(_read(TRIGGER_MAP))
        mapped = {p for entry in data["triggers"] for p in entry["paths"]}
        for name in ("prompt.md", "examples.md", "anti-examples.md"):
            assert f"frameworks/{framework}/{name}" in mapped
