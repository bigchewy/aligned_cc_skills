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
KILL_LIST_SVG = KERNEL_DIR / "kernel-kill-list-example.svg"
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

    def test_prompt_asks_for_four_to_seven_kill_list_lines(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        kill = prompt.split("### PHASE 7")[1].split("### PHASE 8")[0]
        assert "Four to seven" in kill
        assert "four to seven names" in kill
        assert "Three to five" not in kill and "three to five" not in kill

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

    def test_prompt_describes_the_one_page_svg_without_a_kill_list_card(self):
        """The one-pager is page one. The kill list gets its own SVG page, in the same style."""
        prompt = _read(KERNEL_DIR / "prompt.md")
        assert "kill-list card" not in prompt
        assert KILL_LIST_SVG.name in prompt
        rendering = prompt.split("**Want this as a one-page diagram, a deck, or both?**")[1]
        assert "second SVG" in rendering or "second page" in rendering

    def test_prompt_tells_the_renderer_what_the_deck_script_needs(self):
        prompt = _read(KERNEL_DIR / "prompt.md")
        rendering = prompt.split("**Want this as a one-page diagram, a deck, or both?**")[1]
        assert "python-pptx" in rendering, "the deck script's dependency belongs in the prompt, not only in the script"
        assert "company name" in rendering and "output file" in rendering, (
            "the content block includes the deck's name and file name, or the user ships a deck called REM Medical"
        )


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

    def test_one_page_svg_has_no_subtitle_under_the_action_titles(self):
        """A key action is a short title, an owner, and the year's goals. The explanation lives on the detail page."""
        text = _read(ONE_PAGE_SVG)
        assert "fee-for-service business" not in text
        assert "extend into" not in text
        for title in ("FUEL THE ENGINE", "NEW DELIVERY MODELS", "GEOGRAPHIC REACH"):
            assert title in text
        # The line after each title is the owner, not a subtitle.
        for title in ("FUEL THE ENGINE", "NEW DELIVERY MODELS", "GEOGRAPHIC REACH"):
            after = text.split(title, 1)[1]
            next_text = next(m for m in re.findall(r">([^<]+)<", after) if m.strip())
            assert next_text.startswith("Owner:"), f"{title} is followed by {next_text!r}, expected the owner line"

    def test_kill_list_svg_exists_in_the_same_style(self):
        assert KILL_LIST_SVG.exists(), f"missing {KILL_LIST_SVG}"
        text = _read(KILL_LIST_SVG).strip()
        assert text.startswith("<svg ") and text.endswith("</svg>")
        assert 'viewBox="0 0 1200 ' in text, "same page width as the one-pager"
        assert "REM MEDICAL" in text
        assert "KILL LIST" in text
        assert "NOT NOW" in text and "COMES BACK WHEN" in text
        lowered = text.lower()
        for client in OTHER_CLIENT_MATERIAL:
            assert client not in lowered, f"kill-list SVG carries other client material: {client!r}"
        for name in ("In-lab beds", "Price cuts", "Consumer sleep products", "Acquiring other sleep labs"):
            assert name in text, f"kill-list SVG must carry the deck's kill list; missing {name!r}"
        one_page = _read(ONE_PAGE_SVG)
        assert re.search(r'fill="#faf9f7"', text) and re.search(r'fill="#faf9f7"', one_page), "same paper"
        assert "#1e2847" in text, "same navy accent as the one-pager"

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

    def test_deck_script_has_no_subtitle_field(self):
        """Titles stay short; the explanation is the 'what it is' text on the action's detail page."""
        script = _read(DECK_SCRIPT)
        assert '"sub"' not in script
        assert 'a["sub"]' not in script
        content = script.split("# ---------------------------------------------------------------- content")[1]
        titles = re.findall(r'"title": "([^"]+)"', content)
        assert len(titles) == 3
        for title in titles:
            assert len(title.split()) <= 4, f"title too long: {title!r}"
        whats = re.findall(r'"what": \(([^)]+)\)', content, flags=re.S)
        assert len(whats) == 3
        assert "fee-for-service" in whats[0], "the old subtitle's idea moves into 'what it is'"
        for what in whats:
            assert what.count(".") >= 2, "what it is: a couple of sentences"

    def test_deck_name_and_output_file_live_in_the_content_block(self):
        script = _read(DECK_SCRIPT)
        marker = "# ---------------------------------------------------------------- content"
        before, after = script.split(marker, 1)
        assert "DECK_NAME =" not in before and "OUT =" not in before
        assert re.search(r"^COMPANY = ", after, flags=re.M)
        assert re.search(r"^DECK_NAME = ", after, flags=re.M)
        assert re.search(r"^OUT = ", after, flags=re.M)
        code_above = re.sub(r'""".*?"""', "", before, count=1, flags=re.S)
        code_above = "\n".join(l for l in code_above.splitlines() if not l.lstrip().startswith("#"))
        assert "REM Medical" not in code_above, "only the docstring above the marker may name the example company"

    def test_challenge_page_lines_live_in_the_content_block(self):
        """The 'why', 'wrong if', 'why it fits', and 'gate' lines are locked lines, so they are content."""
        script = _read(DECK_SCRIPT)
        marker = "# ---------------------------------------------------------------- content"
        content = script.split(marker, 1)[1]
        for name in ("CHALLENGE_WHY", "CHALLENGE_WRONG_IF", "POLICY_WHY", "POLICY_GATE"):
            assert re.search(rf"^{name} = ", content, flags=re.M), f"{name} must be set in the content block"
        pages = content.split("# Two-column geometry shared by the detail pages.", 1)[1]
        assert "Medicare" not in pages and "polysomnography" not in pages, (
            "page-building code must not carry the example's text"
        )

    def test_deck_pages_flow_at_the_framework_maximum_sizes(self, tmp_path):
        """Fill the content block with lines at the framework's upper targets and check nothing runs off the page."""
        pptx = pytest.importorskip("pptx")
        script = _read(DECK_SCRIPT)
        marker = "# ---------------------------------------------------------------- content"
        layout_above, rest = script.split(marker, 1)
        _, layout_below = rest.split("# Two-column geometry shared by the detail pages.", 1)
        filler = "the market owner and client year through review plan".split()  # average word length
        w = lambda n, word=None: " ".join([word] * n if word else [filler[i % len(filler)] for i in range(n)])
        content = f"""
COMPANY = "Test Co"
DECK_NAME = f"{{COMPANY}} strategy kernel"
OUT = Path(r"{tmp_path / 'max.pptx'}")
PURPOSE = "{w(14)}"
CHALLENGE = "{w(28)}."
CHALLENGE_WHY = "{w(46)}."
CHALLENGE_WRONG_IF = "{w(24)}."
POLICY = "{w(28)}."
POLICY_WHY = ["{w(14)}", "{w(14)}", "{w(14)}"]
POLICY_GATE = "{w(24)}?"
ACTIONS = [
    {{"n": str(i), "title": "{w(4, 'word')}", "owner": "Owner",
      "what": "{w(44)}.",
      "goals": [("{w(12)}", "Owner")] * 4,
      "depends": ["{w(16)}", "{w(16)}", "{w(16)}"],
      "signal": "{w(24)}"}}
    for i in (1, 2, 3)
]
KILL_LIST = [("{w(6)}", "{w(14)}")] * 7
ASSUMPTIONS = [("{w(12)}", "{w(12)}")] * 5
QUESTIONS = [("{w(15)}?", "Owner")] * 5
# Two-column geometry shared by the detail pages."""
        test_script = tmp_path / "build.py"
        test_script.write_text(layout_above + marker + content + layout_below)
        import runpy
        runpy.run_path(str(test_script))
        prs = pptx.Presentation(str(tmp_path / "max.pptx"))
        assert len(prs.slides) in (7, 8), "five long assumptions and questions may split onto two pages"
        page_h = prs.slide_height
        footer_top = int(6.90 * 914400)
        for n, slide in enumerate(prs.slides, 1):
            for sh in slide.shapes:
                if sh.width == prs.slide_width:
                    continue  # the page background
                bottom = sh.top + sh.height
                if sh.top >= footer_top:
                    assert sh.height <= 914400 * 0.25, f"slide {n}: content pushed into the footer zone"
                    continue  # the footer itself
                assert bottom <= footer_top + 914400 * 0.05, (
                    f"slide {n}: shape at y={sh.top / 914400:.2f}in runs to {bottom / 914400:.2f}in, past the footer"
                )
                assert bottom <= page_h

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
