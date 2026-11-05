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
def test_star_key_shows_only_with_stars(page):
    proc = subprocess.run(
        ["node", str(DRIVER), str(FRAMEWORK / page)],
        capture_output=True, text=True, cwd=TESTS,
    )
    assert "ok   star key shows only with stars" in proc.stdout, proc.stdout
    assert "ok   the pick box changes the star and the key" in proc.stdout, proc.stdout


@pytest.mark.parametrize("page", ["mind-map-template.html", "example-map.html"])
def test_select_uses_the_page_colors_in_both_themes(page):
    # The browser draws a select on white by default, so dark mode got faint text on a white ground.
    # The page's colors are tokens that change in dark mode, so styling select with them covers both.
    import re
    css = re.search(r"<style>([\s\S]*?)</style>", (FRAMEWORK / page).read_text()).group(1)
    rule = re.search(r"(?m)^select \{([^}]*)\}", css)
    assert rule, "no select rule"
    assert "background: var(--box)" in rule.group(1)
    assert "color: var(--ink)" in rule.group(1)
    assert "prefers-color-scheme: dark" in css and "--box:" in css.split("prefers-color-scheme: dark")[1]


@pytest.mark.parametrize("page", ["mind-map-template.html", "example-map.html"])
def test_delete_question_scrolls_inside_the_window(page):
    import re
    css = re.search(r"<style>([\s\S]*?)</style>", (FRAMEWORK / page).read_text()).group(1)
    rule = re.search(r"(?m)^#delete-question \{([^}]*)\}", css)
    assert rule and "max-height: min(40vh" in rule.group(1) and "overflow: auto" in rule.group(1)
