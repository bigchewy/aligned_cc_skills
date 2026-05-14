"""Behavioral test: each phase script, when executed with a stub `claude`
on PATH, propagates the expected ANTHROPIC_MODEL and
CLAUDE_CODE_SUBAGENT_MODEL into the claude subprocess env. Catches
regressions where the export is removed or guarded incorrectly.

The stub claude binary writes the env it observed to a file, then exits
0 immediately (does not consume stdin). This decouples env-propagation
correctness from real claude availability."""

from __future__ import annotations
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RALPH_DIR = REPO_ROOT / "docs" / "ralph_loops"


def _make_stub_claude(tmpdir: Path, env_dump_file: Path, args_dump_file: Path) -> Path:
    """Write a fake `claude` script that records its env AND its argv to
    separate files. argv capture is needed because `--bare` is a CLI
    flag, not an env var — it won't appear in `env` output."""
    stub = tmpdir / "claude"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'env > "{env_dump_file}"\n'
        f'printf "%s\\n" "$@" > "{args_dump_file}"\n'
        "exit 0\n"
    )
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return stub


def _run_phase_with_stub(phase_script: Path, env_overrides: dict) -> tuple:
    """Run a phase script with stub claude on PATH. Returns (env_dict, argv_list)
    that stub claude observed. Phase script will fail subsequent steps (no
    real sentinel/status file) — we only care that claude was invoked with
    the right env and args."""
    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        env_dump = tmpdir / "claude_env.txt"
        args_dump = tmpdir / "claude_args.txt"
        _make_stub_claude(tmpdir, env_dump, args_dump)

        env = os.environ.copy()
        env["PATH"] = f"{tmpdir}:{env['PATH']}"
        # Minimum env required by phase scripts. Real values don't matter
        # because stub claude exits 0 before phase script needs sentinel.
        env["PROJECT"] = str(tmpdir)
        env["DESIGN_DOC"] = str(tmpdir / "design.md")
        env["SENTINEL"] = str(tmpdir / "sentinel")
        env["LOG"] = str(tmpdir / "log")
        env["PHASE_TIMEOUT"] = "10"
        env["WRITE_PLAN_PROMPT"] = str(tmpdir / "prompt.md")
        env["SKILL_FILE"] = str(tmpdir / "skill.md")
        env["CHECKLIST_FILE"] = str(tmpdir / "checklist.md")
        env["KANBAN_FORMAT"] = str(tmpdir / "kanban.md")
        env["WORKTREE"] = str(tmpdir)
        env["PLAN_IN_WORKTREE"] = str(tmpdir / "plan.md")
        env["MOCKUP_PROMPT"] = str(tmpdir / "mockup-prompt.md")
        env["MAX_MOCKUP_ITERATIONS"] = "1"
        env["MOCKUP_TIMEOUT"] = "10"
        env["BRANCH"] = "test-branch"
        env["VERIFY_PROMPT"] = str(tmpdir / "verify-prompt.md")
        env["STATUS"] = str(tmpdir / "status")
        # Stub prompt files so heredoc concatenation in phase scripts doesn't fail
        (tmpdir / "prompt.md").write_text("test prompt")
        (tmpdir / "mockup-prompt.md").write_text("test prompt")
        (tmpdir / "verify-prompt.md").write_text("test prompt")
        # mockup.sh skips claude entirely when **Mockups:** is empty/none/N/A.
        # Use a non-empty value so it enters the claude-invocation path and
        # the stub captures env + argv.
        (tmpdir / "plan.md").write_text("**Mockups:** mockup-1.html\n")
        env.update(env_overrides)

        # Redirect to DEVNULL (not capture_output): phases/*.sh start
        # background heartbeat/watchdog subshells whose `sleep` children get
        # orphaned when the phase exits early (no real claude → no sentinel).
        # Those orphans inherit any captured stdout/stderr pipes and keep
        # them open until their sleep expires, blocking subprocess.run. We
        # never inspect stdout/stderr in this test — env_dump and args_dump
        # files are the only signal we need.
        subprocess.run(
            ["bash", str(phase_script)],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=15,
        )

        env_parsed = {}
        if env_dump.exists():
            for line in env_dump.read_text().splitlines():
                if "=" in line:
                    k, _, v = line.partition("=")
                    env_parsed[k] = v
        args_parsed = []
        if args_dump.exists():
            args_parsed = [a for a in args_dump.read_text().splitlines() if a]
        return env_parsed, args_parsed


def test_plan_phase_propagates_opus_to_claude():
    env, _ = _run_phase_with_stub(RALPH_DIR / "phases" / "plan.sh", {})
    assert env.get("ANTHROPIC_MODEL") == "opus", (
        f"plan.sh should propagate ANTHROPIC_MODEL=opus to claude; got "
        f"{env.get('ANTHROPIC_MODEL')!r}"
    )
    assert env.get("CLAUDE_CODE_SUBAGENT_MODEL") == "opus", (
        f"plan.sh should propagate CLAUDE_CODE_SUBAGENT_MODEL=opus; got "
        f"{env.get('CLAUDE_CODE_SUBAGENT_MODEL')!r}"
    )


def test_mockup_phase_propagates_sonnet_to_claude():
    env, _ = _run_phase_with_stub(RALPH_DIR / "phases" / "mockup.sh", {})
    assert env.get("ANTHROPIC_MODEL") == "sonnet"
    assert env.get("CLAUDE_CODE_SUBAGENT_MODEL") == "sonnet"


def test_verify_phase_propagates_sonnet_to_claude():
    env, _ = _run_phase_with_stub(RALPH_DIR / "phases" / "verify.sh", {})
    assert env.get("ANTHROPIC_MODEL") == "sonnet"
    assert env.get("CLAUDE_CODE_SUBAGENT_MODEL") == "sonnet"


def test_plan_phase_respects_plan_model_override():
    env, _ = _run_phase_with_stub(
        RALPH_DIR / "phases" / "plan.sh",
        {"PLAN_MODEL": "sonnet"},
    )
    assert env.get("ANTHROPIC_MODEL") == "sonnet", (
        "PLAN_MODEL=sonnet override must propagate to ANTHROPIC_MODEL"
    )


def test_plan_phase_invokes_claude_with_bare_flag():
    """Behavioral counterpart to the static-parse --bare assertion in
    test_autopilot_model_selection.py. Skip if Task 5 audit produced
    verdict: SKIP-BARE (in that case lib/process.sh has no --bare and
    this assertion will fail correctly)."""
    _, args = _run_phase_with_stub(RALPH_DIR / "phases" / "plan.sh", {})
    audit = REPO_ROOT / "docs" / "plans" / "2026-05-14-autopilot-model-downshift-audit.md"
    if audit.exists() and "verdict: SKIP-BARE" in audit.read_text(encoding="utf-8"):
        pytest.skip("--bare adoption skipped per Task 5 audit verdict")
    assert "--bare" in args, (
        f"phases/plan.sh should invoke claude with --bare; got args={args!r}"
    )
