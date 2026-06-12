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

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RALPH_DIR = REPO_ROOT / "scripts" / "autopilot"


def _make_stub_claude(tmpdir: Path, env_dump_file: Path, args_dump_file: Path) -> Path:
    """Write a fake `claude` script that records its env AND its argv to
    separate files. argv capture lets us assert specific CLI flags (like
    the now-forbidden `--bare`) are absent — those don't show up in
    `env` output."""
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


def test_plan_phase_propagates_sonnet_to_claude():
    # Default downshifted opus -> sonnet in b390a1d (token-efficiency pass).
    env, _ = _run_phase_with_stub(RALPH_DIR / "phases" / "plan.sh", {})
    assert env.get("ANTHROPIC_MODEL") == "sonnet", (
        f"plan.sh should propagate ANTHROPIC_MODEL=sonnet to claude; got "
        f"{env.get('ANTHROPIC_MODEL')!r}"
    )
    assert env.get("CLAUDE_CODE_SUBAGENT_MODEL") == "sonnet", (
        f"plan.sh should propagate CLAUDE_CODE_SUBAGENT_MODEL=sonnet; got "
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
    # Override value must differ from the sonnet default, or this test
    # passes even when the override plumbing is broken.
    env, _ = _run_phase_with_stub(
        RALPH_DIR / "phases" / "plan.sh",
        {"PLAN_MODEL": "opus"},
    )
    assert env.get("ANTHROPIC_MODEL") == "opus", (
        "PLAN_MODEL=opus override must propagate to ANTHROPIC_MODEL"
    )


def test_plan_phase_does_not_invoke_claude_with_bare_flag():
    """Behavioral counterpart to the static-parse assertions in
    test_autopilot_model_selection.py. Confirms that when plan.sh runs
    end-to-end (with a stub claude), the actual argv passed to claude
    does NOT contain `--bare`.

    Why: --bare forces Anthropic auth to "strictly ANTHROPIC_API_KEY or
    apiKeyHelper via --settings (OAuth and keychain are never read)" per
    `claude --help`. Max-plan users authenticate via OAuth, so --bare
    breaks autopilot for them. Static-parse tests catch the obvious
    re-adoption; this behavioral test catches subtler regressions where
    the flag might get injected via a wrapper or env-driven indirection
    that the static scan would miss."""
    _, args = _run_phase_with_stub(RALPH_DIR / "phases" / "plan.sh", {})
    assert "--bare" not in args, (
        f"phases/plan.sh must NOT pass --bare to claude (forces "
        f"API-key-only auth, breaks Max-plan OAuth); got args={args!r}"
    )
