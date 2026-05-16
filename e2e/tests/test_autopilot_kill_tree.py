"""Behavioral tests for kill_claude tree-kill semantics in
scripts/autopilot/lib/process.sh.

Regression guard for the orphaned-MCP-server bug: prior to the
session-spawn + negative-PID kill, `kill_claude` only signalled the
top-level claude PID. Children (playwright-mcp Node servers, sub-agent
claude processes spawned via the Task tool) survived and re-parented to
launchd, leaking CPU/RAM across iterations.

Strategy: stand in for `claude` with a `bash -c '...'` that spawns its
own children, capture the session-leader PID, call kill_claude, then
verify no member of that process group survives the grace period.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESS_LIB = REPO_ROOT / "scripts" / "autopilot" / "lib" / "process.sh"


def _bash(script: str, timeout: float = 30.0) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _pgrep_group(pgid: int) -> list[int]:
    """Return PIDs in process group `pgid` (macOS-compatible)."""
    r = subprocess.run(
        ["pgrep", "-g", str(pgid)], capture_output=True, text=True, check=False
    )
    return [int(x) for x in r.stdout.split() if x.strip().isdigit()]


def test_spawn_prefix_is_defined_after_sourcing():
    """Sanity check: sourcing process.sh must set _AUTOPILOT_SPAWN_SESSION
    to a non-empty array. If perl is missing the source fails loudly per
    the explicit `return 1` guard — that's also worth catching here."""
    script = f"""
        set -uo pipefail
        source {PROCESS_LIB}
        printf '%s\\n' "${{#_AUTOPILOT_SPAWN_SESSION[@]}}"
    """
    r = _bash(script)
    assert r.returncode == 0, f"sourcing process.sh failed: {r.stderr!r}"
    n = int(r.stdout.strip())
    assert n >= 1, f"_AUTOPILOT_SPAWN_SESSION must have ≥1 element; got {n}"


def test_spawned_child_is_session_leader():
    """The whole point of the spawn prefix: the spawned process must have
    pid == pgid (it leads a new session). Without that, negative-PID kill
    can't target the tree."""
    script = f"""
        set -uo pipefail
        source {PROCESS_LIB}
        "${{_AUTOPILOT_SPAWN_SESSION[@]}}" bash -c 'sleep 5' &
        PID=$!
        # Give exec time to land so PGID reads the post-exec process
        sleep 1
        # pid and pgid columns from ps; compare them
        ps -o pid,pgid -p "$PID" | tail -n +2
        kill -KILL -- "-$PID" 2>/dev/null || true
        wait "$PID" 2>/dev/null || true
    """
    r = _bash(script)
    assert r.returncode == 0, f"script failed: {r.stderr!r}"
    line = r.stdout.strip().splitlines()[-1].split()
    pid, pgid = int(line[0]), int(line[1])
    assert pid == pgid, (
        f"Spawned child must be its own process-group leader so the tree "
        f"is killable via -PGID. Got pid={pid}, pgid={pgid}."
    )


def test_kill_claude_kills_descendant_tree():
    """End-to-end: spawn a fake claude that itself spawns two long sleeps,
    call kill_claude, verify the whole process group is gone within the
    SIGTERM grace + SIGKILL escalation budget."""
    # Use a script that prints its own pid and spawns two children
    # via wait. The two sleeps stay alive until killed.
    script = f"""
        set -uo pipefail
        source {PROCESS_LIB}
        "${{_AUTOPILOT_SPAWN_SESSION[@]}}" bash -c 'sleep 60 & sleep 60 & wait' &
        CLAUDE_PID=$!
        # Give the inner bash + its two child sleeps time to launch
        sleep 1
        echo "pgid=$CLAUDE_PID"
        echo "before_count=$(pgrep -g "$CLAUDE_PID" | wc -l | tr -d ' ')"
        kill_claude
        echo "after_count=$(pgrep -g "$CLAUDE_PID" 2>/dev/null | wc -l | tr -d ' ')"
    """
    r = _bash(script, timeout=20.0)
    assert r.returncode == 0, f"script failed: stderr={r.stderr!r}"

    out = dict(line.split("=", 1) for line in r.stdout.strip().splitlines() if "=" in line)
    pgid = int(out["pgid"])
    before = int(out["before_count"])
    after = int(out["after_count"])

    # Belt-and-suspenders: even if the assertion fails, don't leave orphans
    # behind for the next test run.
    try:
        assert before >= 3, (
            f"Test setup did not produce the expected tree (bash + 2 sleeps). "
            f"before_count={before}; the regression-guard nature of this test "
            f"depends on actually having descendants to kill."
        )
        assert after == 0, (
            f"kill_claude must tear down the whole process group. "
            f"pgid={pgid} still has {after} live members after the 3s grace + "
            f"SIGKILL escalation. The negative-PID kill is not reaching the "
            f"tree — check that _AUTOPILOT_SPAWN_SESSION actually creates a "
            f"new session (pid == pgid) and that kill_claude uses `-$PGID`."
        )
    finally:
        # Mop up any survivors so a failure here doesn't pollute future runs.
        subprocess.run(["pkill", "-KILL", "-g", str(pgid)], check=False)


def test_cleanup_is_idempotent():
    """cleanup() is wired to both the EXIT trap and called from handle_signal
    via exit; double-entry must be safe. A second call must not blow up on
    an already-cleared CLAUDE_PID or attempt a second kill that could hit a
    recycled PID."""
    script = f"""
        set -uo pipefail
        source {PROCESS_LIB}
        "${{_AUTOPILOT_SPAWN_SESSION[@]}}" sleep 60 &
        CLAUDE_PID=$!
        sleep 1
        cleanup
        # Second entry must be a no-op, not a re-kill
        cleanup
        echo "ok"
    """
    r = _bash(script, timeout=15.0)
    assert r.returncode == 0, f"cleanup re-entry crashed: stderr={r.stderr!r}"
    assert r.stdout.strip().endswith("ok"), (
        f"cleanup did not complete cleanly on second call. stdout={r.stdout!r}"
    )
