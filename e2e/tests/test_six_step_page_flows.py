"""Runs the real page code of the 6-step process mind map, using node only.

six_step_page_flows.js loads a map page's logic and page scripts against a stub DOM and fake file
handles, then walks through what a person does: turning on saving, editing, and hitting refusals.
"""

import subprocess
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
FRAMEWORK = TESTS.parent.parent / "frameworks" / "6-step-process"
DRIVER = TESTS / "six_step_page_flows.js"

# The driver prints one line per flow. This catches a flow list that went missing.
MIN_FLOWS = 40


@pytest.mark.parametrize("page", ["mind-map-template.html", "example-map.html"])
def test_page_flows(page):
    proc = subprocess.run(
        ["node", str(DRIVER), str(FRAMEWORK / page)],
        capture_output=True, text=True, cwd=TESTS,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    passed = [line for line in proc.stdout.splitlines() if line.startswith("ok   ")]
    assert len(passed) >= MIN_FLOWS, proc.stdout


@pytest.mark.parametrize("page", ["mind-map-template.html", "example-map.html"])
def test_star_button_flow_runs(page):
    proc = subprocess.run(
        ["node", str(DRIVER), str(FRAMEWORK / page)],
        capture_output=True, text=True, cwd=TESTS,
    )
    assert "ok   the star button changes the star, keeps focus, and has no key in the header" in proc.stdout, proc.stdout


@pytest.mark.parametrize("page", ["mind-map-template.html", "example-map.html"])
def test_the_page_is_always_light_and_has_no_list_to_style(page):
    import re
    css = re.search(r"<style>([\s\S]*?)</style>", (FRAMEWORK / page).read_text()).group(1)
    assert not re.search(r"(?m)^select", css)
    assert "prefers-color-scheme" not in css and "color-scheme: light" in css


@pytest.mark.parametrize("page", ["mind-map-template.html", "example-map.html"])
def test_delete_question_scrolls_inside_the_window(page):
    import re
    css = re.search(r"<style>([\s\S]*?)</style>", (FRAMEWORK / page).read_text()).group(1)
    rule = re.search(r"(?m)^#delete-question \{([^}]*)\}", css)
    assert rule and "max-height: min(40vh" in rule.group(1) and "overflow: auto" in rule.group(1)
