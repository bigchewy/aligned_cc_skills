"""Runs the real page code of the 6-step process mind map as the Claude viewer would, using node only.

six_step_hosted_flows.js loads a map page's scripts against a stub DOM and a fake shared data store,
then walks through what a person does while the data changes under them.
"""

import subprocess
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
FRAMEWORK = TESTS.parent.parent / "frameworks" / "6-step-process"
DRIVER = TESTS / "six_step_hosted_flows.js"

# The driver prints one line per flow. This catches a flow list that went missing.
MIN_FLOWS = 40


@pytest.mark.parametrize("page", ["mind-map-template.html", "example-map.html"])
def test_hosted_flows(page):
    proc = subprocess.run(
        ["node", str(DRIVER), str(FRAMEWORK / page)],
        capture_output=True, text=True, cwd=TESTS,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    passed = [line for line in proc.stdout.splitlines() if line.startswith("ok   ")]
    assert len(passed) >= MIN_FLOWS, proc.stdout
