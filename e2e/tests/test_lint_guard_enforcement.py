"""Pins the lint:guard enforcement points in the autopilot pipeline.

Custom ESLint guard rules (project-side `npm run lint:guard`) catch the
build-only defect class — non-whitelisted page.tsx exports, 'use client'
imports of fs-using modules — that Jest cannot see. `next build` does not
lint (Next 15+), so without these hooks the rules never gate the pipeline:
the ralph loop runs them scoped to changed files per task, and the verify
phase runs them repo-wide as the backstop. Both are conditional on the
project defining a lint:guard script.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY_BRANCH = REPO_ROOT / "scripts" / "autopilot" / "VERIFY-BRANCH.md"
EXECUTE_PLAN = REPO_ROOT / "scripts" / "autopilot" / "EXECUTE-PLAN.md"
VERIFY_TEXT = VERIFY_BRANCH.read_text(encoding="utf-8")
EXECUTE_TEXT = EXECUTE_PLAN.read_text(encoding="utf-8")


def test_verify_branch_runs_lint_guard():
    assert "lint:guard" in VERIFY_TEXT, (
        "VERIFY-BRANCH.md must run the project's lint:guard script (when "
        "defined) — the repo-wide backstop for the build-only defect class."
    )


def test_verify_branch_failed_at_includes_lint():
    assert "tests | lint | build | LLM eval" in VERIFY_TEXT, (
        ".finish-status failed_at taxonomy must include the lint step so "
        "the halt fix-instructions name the right failure category."
    )


def test_execute_plan_runs_scoped_lint_guard():
    assert "lint:guard" in EXECUTE_TEXT, (
        "EXECUTE-PLAN.md must run lint:guard scoped to changed files per "
        "task — catching guard violations minutes after introduction "
        "instead of at phase 9."
    )


def test_execute_plan_still_forbids_whole_codebase_lint():
    assert "`npm run lint` (whole-codebase)" in EXECUTE_TEXT, (
        "The scoped guard must not replace the prohibition on "
        "whole-codebase lint inside ralph iterations."
    )

# Autopilot is parked: non-functional since 0.33.0, retained for possible
# future revival. Its tests are skipped so the suite gates only active
# plugin surface. To revive, delete this block (and its counterparts in
# the other autopilot/ralph test files).
import pytest as _pytest_parked
pytestmark = _pytest_parked.mark.skip(
    reason="autopilot parked (non-functional since 0.33.0; see README changelog)"
)
