"""Behavioral tests for observability instrumentation in
scripts/autopilot/lib/process.sh.

Covers snapshot_post_wait, log_marker, and the start/stop sampler
lifecycle. Tests source process.sh in a bash subshell, exercise each
function with controlled inputs, and read the resulting log files to
assert structure. The kill_claude tests in test_autopilot_kill_tree.py
establish the source pattern this file follows.

These tests guard against regressions in the field names, the SAMPLER_PID
lifecycle, and the cleanup() → stop_system_sampler chain. Without them,
silently broken instrumentation would let a real leak look like "no
evidence" in the logs.
"""

from __future__ import annotations

import re
import subprocess
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


def _pid_alive(pid: int) -> bool:
    r = subprocess.run(
        ["kill", "-0", str(pid)], capture_output=True, check=False
    )
    return r.returncode == 0


# --- snapshot_post_wait ---


def test_snapshot_post_wait_writes_expected_fields(tmp_path: Path):
    log = tmp_path / "test-log"
    processes_log = Path(f"{log}.processes")
    script = f"""
        set -uo pipefail
        export LOG={log}
        source {PROCESS_LIB}
        "${{_AUTOPILOT_SPAWN_SESSION[@]}}" bash -c 'sleep 30' &
        pid=$!
        sleep 0.3
        snapshot_post_wait "test-label" "$pid" "0"
        kill -- "-$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    """
    r = _bash(script)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    text = processes_log.read_text()
    assert "==== POST-WAIT" in text
    assert "label=test-label" in text
    assert "exit=0" in text
    assert "survivors_in_group=" in text
    assert "system_claude=" in text
    assert "system_node=" in text


def test_snapshot_handles_empty_pgid(tmp_path: Path):
    """Empty pgid path: header still written, no group-members block,
    survivors=0. Catches regressions where the empty branch crashes."""
    log = tmp_path / "test-log"
    processes_log = Path(f"{log}.processes")
    script = f"""
        set -uo pipefail
        export LOG={log}
        source {PROCESS_LIB}
        snapshot_post_wait "empty-pgid" "" "0"
    """
    r = _bash(script)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    text = processes_log.read_text()
    assert "==== POST-WAIT" in text
    assert "pgid=<empty>" in text
    assert "survivors_in_group=0" in text
    assert "group members" not in text


def test_snapshot_handles_dead_pgid(tmp_path: Path):
    """Dead pgid path: leader exited and was reaped; survivors=0 and no
    group block. Validates the post-wait state we expect on a clean
    success exit when nothing leaked."""
    log = tmp_path / "test-log"
    processes_log = Path(f"{log}.processes")
    script = f"""
        set -uo pipefail
        export LOG={log}
        source {PROCESS_LIB}
        "${{_AUTOPILOT_SPAWN_SESSION[@]}}" bash -c 'true' &
        pid=$!
        wait "$pid" 2>/dev/null || true
        snapshot_post_wait "dead-pgid" "$pid" "0"
    """
    r = _bash(script)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    text = processes_log.read_text()
    assert "survivors_in_group=0" in text
    assert "group members" not in text


def test_snapshot_silent_when_log_unset(tmp_path: Path):
    """No LOG → no files. Observability must never accidentally pollute
    the cwd."""
    script = f"""
        set -uo pipefail
        unset LOG
        cd {tmp_path}
        source {PROCESS_LIB}
        snapshot_post_wait "should-skip" "$$" "0"
    """
    r = _bash(script)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    assert list(tmp_path.iterdir()) == []


def test_snapshot_reports_system_counts_as_integers(tmp_path: Path):
    """system_claude and system_node must parse as non-negative integers
    even when no group/all-claudes detail rows are written."""
    log = tmp_path / "test-log"
    processes_log = Path(f"{log}.processes")
    script = f"""
        set -uo pipefail
        export LOG={log}
        source {PROCESS_LIB}
        snapshot_post_wait "counts" "" "0"
    """
    r = _bash(script)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    text = processes_log.read_text()
    m_claude = re.search(r"system_claude=(\d+)", text)
    m_node = re.search(r"system_node=(\d+)", text)
    assert m_claude, f"system_claude missing: {text!r}"
    assert m_node, f"system_node missing: {text!r}"
    assert int(m_claude.group(1)) >= 0
    assert int(m_node.group(1)) >= 0


# --- comm-basename matching (regression guard for the full-path bug) ---


def test_snapshot_awk_matches_claude_when_comm_is_full_path():
    """macOS `ps -o comm=` returns the absolute path for processes launched
    by full path. The snapshot_post_wait awk filter must extract the
    basename and match either bare 'claude' or '/.../claude'. Before this
    guard, the all-claude detail block was empty whenever the claude
    binary was launched from a non-PATH location — system_claude counts
    kept working (pgrep -x matches basenames) but the per-process rows
    that identify *which* claudes are alive were silently dropped."""
    fake_ps = (
        " 12345 12345 100 12345 350000  5.0 00:01:23 00:00:08 /Users/ericpage/.local/bin/claude\n"
        " 12346 12346 100 12346 184320  2.1 00:00:42 00:00:00 node\n"
        " 12347 12347 100 12347  50000  0.0 00:00:01 00:00:00 sshd\n"
        " 12348 12348 100 12348 100000  1.0 00:00:10 00:00:01 claude\n"
        " 12349 12349 100 12349  60000  0.0 00:00:30 00:00:00 /opt/homebrew/bin/node\n"
    )
    awk = '{ n = split($NF, a, "/"); if (a[n] == "claude") print }'
    r = subprocess.run(
        ["awk", awk], input=fake_ps, capture_output=True, text=True, check=True
    )
    out = r.stdout
    assert "12345" in out, "full-path claude row missing"
    assert "12348" in out, "bare-comm claude row missing"
    assert "node" not in out, "false positive on node"
    assert "sshd" not in out, "false positive on sshd"


def test_sampler_awk_matches_node_and_claude_with_mixed_comm_forms():
    """The system sampler's awk must match both 'node' and 'claude'
    whether their comm column is bare or a full path."""
    fake_ps = (
        " 12345 12345 100 350000  5.0 00:01:23 00:00:08 /Users/ericpage/.local/bin/claude\n"
        " 12346 12346 100 184320  2.1 00:00:42 00:00:00 node\n"
        " 12347 12347 100  50000  0.0 00:00:01 00:00:00 sshd\n"
        " 12348 12348 100 100000  1.0 00:00:10 00:00:01 claude\n"
        " 12349 12349 100  60000  0.0 00:00:30 00:00:00 /opt/homebrew/bin/node\n"
        " 12350 12350 100  10000  0.0 00:00:05 00:00:00 node_exporter\n"
    )
    awk = '{ n = split($NF, a, "/"); name = a[n]; if (name == "claude" || name == "node") print }'
    r = subprocess.run(
        ["awk", awk], input=fake_ps, capture_output=True, text=True, check=True
    )
    out = r.stdout
    assert "12345" in out
    assert "12346" in out
    assert "12348" in out
    assert "12349" in out
    assert "12350" not in out, "node_exporter must not match — basename guard relies on exact 'node'"
    assert "sshd" not in out


# --- log_marker ---


def test_log_marker_writes_to_system_log(tmp_path: Path):
    log = tmp_path / "test-log"
    system_log = Path(f"{log}.system")
    script = f"""
        set -uo pipefail
        export LOG={log}
        source {PROCESS_LIB}
        log_marker "ralph-iter-7 starting"
    """
    r = _bash(script)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    text = system_log.read_text()
    assert "==== MARKER" in text
    assert "ralph-iter-7 starting" in text


def test_log_marker_silent_when_log_unset(tmp_path: Path):
    script = f"""
        set -uo pipefail
        unset LOG
        cd {tmp_path}
        source {PROCESS_LIB}
        log_marker "should be silent"
    """
    r = _bash(script)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    assert list(tmp_path.iterdir()) == []


# --- sampler lifecycle ---


def test_sampler_starts_and_stops_cleanly(tmp_path: Path):
    """start_system_sampler spawns a background sampler; stop reaps it
    and clears SAMPLER_PID. Without this guard, the sampler can orphan
    across phases and leak its own subshell."""
    log = tmp_path / "test-log"
    script = f"""
        set -uo pipefail
        export LOG={log}
        export SAMPLER_INTERVAL=1
        source {PROCESS_LIB}
        start_system_sampler
        echo "PID_AT_START=$SAMPLER_PID"
        sleep 0.5
        if kill -0 "$SAMPLER_PID" 2>/dev/null; then echo "STATUS=alive"; else echo "STATUS=dead"; fi
        stop_system_sampler
        echo "PID_AFTER_STOP=$SAMPLER_PID"
    """
    r = _bash(script, timeout=10.0)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    m = re.search(r"^PID_AT_START=(\d+)$", r.stdout, re.MULTILINE)
    assert m, f"missing PID_AT_START in {r.stdout!r}"
    sampler_pid = int(m.group(1))
    assert "STATUS=alive" in r.stdout
    assert "PID_AFTER_STOP=\n" in r.stdout or r.stdout.rstrip().endswith(
        "PID_AFTER_STOP="
    ), f"SAMPLER_PID not cleared: {r.stdout!r}"
    assert not _pid_alive(sampler_pid), (
        f"sampler pid {sampler_pid} still alive after stop_system_sampler"
    )


def test_sampler_writes_sample_blocks(tmp_path: Path):
    """SAMPLER_INTERVAL=1 should produce at least one SAMPLE block within
    2s. Verifies the loop body, not just the lifecycle."""
    log = tmp_path / "test-log"
    system_log = Path(f"{log}.system")
    script = f"""
        set -uo pipefail
        export LOG={log}
        export SAMPLER_INTERVAL=1
        source {PROCESS_LIB}
        start_system_sampler
        sleep 2
        stop_system_sampler
    """
    r = _bash(script, timeout=10.0)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    assert system_log.exists(), "$LOG.system was not created"
    text = system_log.read_text()
    assert "==== SAMPLE" in text
    assert "load:" in text


def test_cleanup_stops_sampler(tmp_path: Path):
    """cleanup() must call stop_system_sampler. Regression guard for the
    EXIT trap path: if a future edit removes the call, a SIGINT'd run
    leaks the sampler subshell."""
    log = tmp_path / "test-log"
    script = f"""
        set -uo pipefail
        export LOG={log}
        export SAMPLER_INTERVAL=30
        source {PROCESS_LIB}
        start_system_sampler
        echo "SAMPLER_PID=$SAMPLER_PID"
        cleanup
        echo "AFTER_CLEANUP=$SAMPLER_PID"
    """
    r = _bash(script, timeout=10.0)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    m = re.search(r"^SAMPLER_PID=(\d+)$", r.stdout, re.MULTILINE)
    assert m, f"missing SAMPLER_PID in {r.stdout!r}"
    sampler_pid = int(m.group(1))
    assert not _pid_alive(sampler_pid), (
        f"sampler {sampler_pid} still alive after cleanup"
    )
    assert "AFTER_CLEANUP=\n" in r.stdout or r.stdout.rstrip().endswith(
        "AFTER_CLEANUP="
    )


def test_sampler_start_is_idempotent(tmp_path: Path):
    """A second start_system_sampler call must NOT spawn a second
    sampler. Prevents the phase-script-orphan footgun the Architect
    review flagged."""
    log = tmp_path / "test-log"
    script = f"""
        set -uo pipefail
        export LOG={log}
        export SAMPLER_INTERVAL=10
        source {PROCESS_LIB}
        start_system_sampler
        first="$SAMPLER_PID"
        start_system_sampler
        second="$SAMPLER_PID"
        echo "FIRST=$first"
        echo "SECOND=$second"
        stop_system_sampler
    """
    r = _bash(script, timeout=10.0)
    assert r.returncode == 0, f"bash failed: {r.stderr}"
    m1 = re.search(r"^FIRST=(\d+)$", r.stdout, re.MULTILINE)
    m2 = re.search(r"^SECOND=(\d+)$", r.stdout, re.MULTILINE)
    assert m1 and m2, f"missing PIDs in {r.stdout!r}"
    assert m1.group(1) == m2.group(1), (
        "second start_system_sampler started a NEW sampler — idempotency broken"
    )

# Autopilot is parked: non-functional since 0.33.0, retained for possible
# future revival. Its tests are skipped so the suite gates only active
# plugin surface. To revive, delete this block (and its counterparts in
# the other autopilot/ralph test files).
import pytest as _pytest_parked
pytestmark = _pytest_parked.mark.skip(
    reason="autopilot parked (non-functional since 0.33.0; see README changelog)"
)
