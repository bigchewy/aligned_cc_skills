"""Static-parse tests for autopilot resume-sentinel namespacing (KB-068).

The plan-path sentinel was a single shared per-project file
(`$PROJECT/.autopilot-plan-path`), so two runs against different design
docs in the same project clobbered each other's resume state: plan.sh
deleted a "different design doc" sentinel, and any completed run's
cleanup deleted the shared file. Without the sentinel, a re-run of a
halted pipeline rewrites the plan from scratch — a data-loss vector
(incidents 2026-05-14 and 2026-06-12).

Fix contract pinned here:
1. The sentinel is namespaced by design-doc slug, matching the
   critique-flag convention.
2. Both `rm -f "$SENTINEL"` sites log what they remove and why.
3. plan.sh refuses a fresh plan-write when a worktree for the predicted
   branch already has commits ahead of main (halt: executed_worktree_exists).

Mirrors the file-reading style of test_ralph_sentinels.py — no
subprocess execution.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOPILOT = REPO_ROOT / "scripts" / "autopilot" / "autopilot.sh"
PLAN_PHASE = REPO_ROOT / "scripts" / "autopilot" / "phases" / "plan.sh"
AUTOPILOT_TEXT = AUTOPILOT.read_text(encoding="utf-8")
PLAN_TEXT = PLAN_PHASE.read_text(encoding="utf-8")


# --- Task 1: sentinel namespaced by design-doc slug ---


def test_sentinel_is_namespaced_by_design_doc_slug():
    assert (
        'SENTINEL="$PROJECT/.autopilot-plan-path-${_DESIGN_DOC_SLUG}"'
        in AUTOPILOT_TEXT
    ), (
        "SENTINEL must be namespaced by design-doc slug — a shared "
        "per-project sentinel lets one run delete another run's resume "
        "state (KB-068)."
    )


def test_slug_is_defined_before_sentinel():
    slug_pos = AUTOPILOT_TEXT.find("_DESIGN_DOC_SLUG=")
    sentinel_pos = AUTOPILOT_TEXT.find("SENTINEL=")
    assert slug_pos != -1 and sentinel_pos != -1
    assert slug_pos < sentinel_pos, (
        "_DESIGN_DOC_SLUG must be assigned before SENTINEL uses it; "
        "with set -u an unset expansion would abort the script."
    )


def test_unnamespaced_sentinel_literal_is_gone():
    assert '.autopilot-plan-path"' not in AUTOPILOT_TEXT, (
        "The un-namespaced sentinel path must not appear in autopilot.sh."
    )


# --- Task 2: both deletion sites are observable ---


def test_plan_phase_logs_sentinel_removal():
    assert "[sentinel] removing" in PLAN_TEXT, (
        "plan.sh must log sentinel removals — the 2026-05-14 incident "
        "was unresolvable because neither rm site left an audit trail."
    )


def test_plan_phase_logs_both_removal_reasons():
    assert "design-doc-mismatch" in PLAN_TEXT
    assert "plan-file-missing" in PLAN_TEXT


def test_completion_cleanup_logs_sentinel_removal():
    assert "[sentinel] removing" in AUTOPILOT_TEXT, (
        "autopilot.sh's run-complete cleanup must log what it removes."
    )
    assert "run-complete" in AUTOPILOT_TEXT


# --- Task 3: integrity guard before fresh plan-write ---


def test_plan_phase_sources_halt_library():
    assert "lib/halt.sh" in PLAN_TEXT, (
        "plan.sh must source lib/halt.sh to emit the "
        "executed_worktree_exists halt."
    )


def test_plan_phase_has_executed_worktree_guard():
    assert "write_halt executed_worktree_exists" in PLAN_TEXT, (
        "Before a fresh plan-write, plan.sh must halt if a worktree for "
        "the predicted branch already has commits — the second line of "
        "defense against clobbering an executed plan (KB-068 item 4)."
    )


def test_guard_checks_commits_ahead_of_main():
    assert "rev-list --count main..HEAD" in PLAN_TEXT, (
        "The guard must trigger only when the existing worktree has "
        "commits ahead of main (an empty worktree is safe to replan)."
    )
