"""Static-parse + bash-function tests for the halt protocol (lib/halt.sh
and the autopilot-halt-format.md taxonomy)."""

from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HALT_SH = REPO_ROOT / "docs" / "ralph_loops" / "lib" / "halt.sh"
HALT_DOC = REPO_ROOT / "skills" / "_shared" / "autopilot-halt-format.md"

EXPECTED_REASONS = [
    "mcp_unreachable",
    "mcp_tool_not_allowlisted",
    "env_var_missing",
    "manifest_drift",
    "manifest_malformed",
    "uncommitted_main",
    "verify_failed",
    "human_action_required",
    "phase_crashed",
]


def test_halt_format_doc_exists():
    assert HALT_DOC.is_file(), "skills/_shared/autopilot-halt-format.md must exist"


def test_halt_format_doc_lists_all_reasons():
    text = HALT_DOC.read_text(encoding="utf-8")
    for r in EXPECTED_REASONS:
        assert r in text, f"halt-format doc must list reason: {r}"
