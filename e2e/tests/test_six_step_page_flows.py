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
    assert "ok   ticking the picks box saves the star and shows the key" in proc.stdout, proc.stdout
