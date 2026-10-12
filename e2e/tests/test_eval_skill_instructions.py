"""Skills that run evals must use the runner when it exists and never skip for a missing key."""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EVAL_SKILLS = ["skills/add-advisor/SKILL.md", "skills/add-framework/SKILL.md"]


@pytest.mark.parametrize("rel", EVAL_SKILLS)
def test_eval_step_uses_runner_when_present(rel):
    text = (REPO / rel).read_text()
    assert "e2e/run_evals.py" in text
    assert "npm run eval -- <scenario-path>" in text
    assert "promptfooconfig.yaml" not in text


@pytest.mark.parametrize("rel", EVAL_SKILLS)
def test_eval_step_never_skips_for_missing_key(rel):
    text = (REPO / rel).read_text()
    assert "Never skip the run because `ANTHROPIC_API_KEY` is not set" in text


def test_eval_audit_does_not_defer_on_credentials():
    text = (REPO / "skills/eval-audit/SKILL.md").read_text()
    assert "missing credentials" not in text
    assert "Claude Code login" in text


def test_versions_match():
    plugin = json.loads((REPO / ".claude-plugin/plugin.json").read_text())["version"]
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())["plugins"][0]["version"]
    assert plugin == market
