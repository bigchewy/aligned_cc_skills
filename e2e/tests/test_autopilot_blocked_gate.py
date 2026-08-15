"""Behavioral tests for scripts/autopilot/lib/blocked-gate.sh.

The gate decides whether the next ralph iteration must spawn a fresh
claude or can skip the spawn because nothing has changed since the
previous iteration. These tests exercise the snapshot / comparison /
skip-decision logic in isolation, sourcing the lib in a bash subshell
and asserting against $? and the on-disk snapshot file.

Without these guards, a regression that breaks the gate would silently
reintroduce the back-to-back claude spawn pattern on BLOCKED tasks
(observed 2026-05-18 to coincide with system-wide swap thrashing).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GATE_LIB = REPO_ROOT / "scripts" / "autopilot" / "lib" / "blocked-gate.sh"


def _write_plan(tmp_path: Path, contents: str) -> Path:
    plan = tmp_path / "plan.md"
    plan.write_text(contents)
    return plan


def _bash(cmd: str, cwd: Path, timeout: float = 5.0) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", cmd],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


_PLAN_WITH_ONE_BLOCKED = """\
# Some Plan

### ✅ Task 1: done
Body.

### 🔄 Task 2: needs interactive
> BLOCKED: requires interactive framework session

### Task 3: future work
Body.
"""

_PLAN_WITH_BLOCKED_REASON_CHANGED = """\
# Some Plan

### ✅ Task 1: done
Body.

### 🔄 Task 2: needs interactive
> BLOCKED: different reason now

### Task 3: future work
Body.
"""

_PLAN_ALL_OPEN_BLOCKED = """\
# Some Plan

### ✅ Task 1: done
Body.

### 🔄 Task 2: needs interactive
> BLOCKED: same reason
"""


# --- snapshot_blocked_state ---


def test_snapshot_writes_one_line_per_blocked_task(tmp_path: Path):
    plan = _write_plan(tmp_path, _PLAN_WITH_ONE_BLOCKED)
    r = _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && snapshot_blocked_state',
        cwd=tmp_path,
    )
    assert r.returncode == 0, r.stderr
    snap = (tmp_path / ".ralph-blocked-snapshot").read_text()
    assert snap.strip() == "2|requires interactive framework session"


def test_snapshot_is_empty_when_no_blocked_tasks(tmp_path: Path):
    plan = _write_plan(
        tmp_path,
        "### ✅ Task 1: done\nBody.\n\n### Task 2: open\nBody.\n",
    )
    r = _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && snapshot_blocked_state',
        cwd=tmp_path,
    )
    assert r.returncode == 0, r.stderr
    snap = (tmp_path / ".ralph-blocked-snapshot").read_text()
    assert snap == ""


# --- should_skip_blocked_spawn ---


def test_should_not_skip_when_no_snapshot_exists(tmp_path: Path):
    """First iteration has no prior snapshot to compare against — must spawn."""
    plan = _write_plan(tmp_path, _PLAN_WITH_ONE_BLOCKED)
    r = _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && should_skip_blocked_spawn',
        cwd=tmp_path,
    )
    assert r.returncode == 1, "must NOT skip when snapshot is absent"


def test_should_not_skip_when_no_blocked_tasks_currently(tmp_path: Path):
    """No 🔄 tasks → claude has work to do on the open task; don't skip."""
    plan = _write_plan(
        tmp_path,
        "### ✅ Task 1: done\nBody.\n\n### Task 2: open\nBody.\n",
    )
    (tmp_path / ".ralph-blocked-snapshot").write_text("")
    r = _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && should_skip_blocked_spawn',
        cwd=tmp_path,
    )
    assert r.returncode == 1


def test_should_not_skip_when_non_blocked_open_task_exists(tmp_path: Path):
    """🔄 Task 2 BLOCKED but Task 3 is still open — claude must spawn to work it."""
    plan = _write_plan(tmp_path, _PLAN_WITH_ONE_BLOCKED)
    _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && snapshot_blocked_state',
        cwd=tmp_path,
    )
    r = _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && should_skip_blocked_spawn',
        cwd=tmp_path,
    )
    assert r.returncode == 1, "must NOT skip while non-BLOCKED open tasks remain"


def test_should_skip_when_all_open_tasks_blocked_and_unchanged(tmp_path: Path):
    """🔄 is the only open task and its reason is identical to the snapshot
    → skip the spawn. This is the path that prevents back-to-back claudes."""
    plan = _write_plan(tmp_path, _PLAN_ALL_OPEN_BLOCKED)
    _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && snapshot_blocked_state',
        cwd=tmp_path,
    )
    r = _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && should_skip_blocked_spawn',
        cwd=tmp_path,
    )
    assert r.returncode == 0, "must skip when all open tasks are BLOCKED with unchanged reasons"


def test_should_not_skip_when_blocked_reason_changed(tmp_path: Path):
    """Same BLOCKED task, but the reason text changed → state is new info,
    claude must re-evaluate."""
    plan = _write_plan(tmp_path, _PLAN_ALL_OPEN_BLOCKED)
    _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && snapshot_blocked_state',
        cwd=tmp_path,
    )
    plan.write_text(
        "### ✅ Task 1: done\nBody.\n\n### 🔄 Task 2: needs interactive\n> BLOCKED: a different reason now\n"
    )
    r = _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && should_skip_blocked_spawn',
        cwd=tmp_path,
    )
    assert r.returncode == 1


def test_should_not_skip_when_new_blocked_task_appears(tmp_path: Path):
    """Snapshot has 1 BLOCKED, plan now has 2 — state diverged, must spawn."""
    plan = _write_plan(tmp_path, _PLAN_ALL_OPEN_BLOCKED)
    _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && snapshot_blocked_state',
        cwd=tmp_path,
    )
    plan.write_text(
        "### ✅ Task 1: done\nBody.\n\n"
        "### 🔄 Task 2: needs interactive\n> BLOCKED: same reason\n\n"
        "### 🔄 Task 3: also stuck\n> BLOCKED: a different blocker\n"
    )
    r = _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && should_skip_blocked_spawn',
        cwd=tmp_path,
    )
    assert r.returncode == 1


def test_snapshot_is_stable_across_two_calls(tmp_path: Path):
    """Calling snapshot_blocked_state twice in a row on an unchanged plan
    must produce identical output — otherwise the gate's equality check
    would never trigger."""
    plan = _write_plan(tmp_path, _PLAN_ALL_OPEN_BLOCKED)
    _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && snapshot_blocked_state',
        cwd=tmp_path,
    )
    first = (tmp_path / ".ralph-blocked-snapshot").read_text()
    _bash(
        f'export PLAN="{plan}"; source "{GATE_LIB}" && snapshot_blocked_state',
        cwd=tmp_path,
    )
    second = (tmp_path / ".ralph-blocked-snapshot").read_text()
    assert first == second

# Autopilot is parked: non-functional since 0.33.0, retained for possible
# future revival. Its tests are skipped so the suite gates only active
# plugin surface. To revive, delete this block (and its counterparts in
# the other autopilot/ralph test files).
import pytest as _pytest_parked
pytestmark = _pytest_parked.mark.skip(
    reason="autopilot parked (non-functional since 0.33.0; see README changelog)"
)
