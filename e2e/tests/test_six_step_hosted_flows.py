"""Runs the real page code of the 6-step process mind map as the Claude viewer would, using node only.

six_step_hosted_flows.js loads the template's scripts against a stub DOM and a fake shared data store,
then walks through what a person does: selecting, typing, pressing pluses and stars, dragging, zooming,
reading the plan and deleting, while the data changes under them.
"""

import re
import subprocess
from pathlib import Path

TESTS = Path(__file__).resolve().parent
TEMPLATE = TESTS.parent.parent / "frameworks" / "6-step-process" / "mind-map-template.html"
DRIVER = TESTS / "six_step_hosted_flows.js"

# The driver prints one line per flow. This catches a flow list that went missing.
MIN_FLOWS = 170


def run_driver():
    return subprocess.run(["node", str(DRIVER), str(TEMPLATE)], capture_output=True, text=True, cwd=TESTS)


def style():
    return re.search(r"<style>([\s\S]*?)</style>", TEMPLATE.read_text()).group(1)


def test_hosted_flows():
    proc = run_driver()
    assert proc.returncode == 0, proc.stdout + proc.stderr
    passed = [line for line in proc.stdout.splitlines() if line.startswith("ok   ")]
    assert len(passed) >= MIN_FLOWS, proc.stdout


def test_star_button_flow_runs():
    assert "ok   the star button changes the star, keeps focus, and has no key in the header" in run_driver().stdout


def test_the_outside_claude_flow_runs():
    assert "ok   opened outside Claude says the map opens inside Claude, and allows no edits" in run_driver().stdout


def test_the_page_is_always_light_and_has_no_list_to_style():
    css = style()
    assert not re.search(r"(?m)^select", css)
    assert "prefers-color-scheme" not in css and "color-scheme: light" in css


def test_the_delete_card_floats_above_the_map_and_has_no_scrolling_list():
    rule = re.search(r"(?m)^#delete-card \{([^}]*)\}", style())
    assert rule and "position: fixed" in rule.group(1) and "z-index: 13" in rule.group(1)
    assert "overflow" not in rule.group(1)
