"""Tests for the SETTINGS-LINK block in phases/worktree.sh.

Verifies that the autopilot mirrors `.claude/settings.local.json` (and
`.claude/settings.json` if present) from the main repo into the worktree
via symlink — and `.mcp.json` as a filtered copy that strips
browser-automation servers — so sub-Claudes spawned in the worktree
(verify, mockup, ralph) inherit project-level Bash/MCP permissions. Without this the sub-
Claude only sees `~/.claude/` user-level settings and project allowlist
entries (e.g. `Bash(pytest *)`) are invisible — verify halts on
interactive permission prompts that never resolve.

Mirrors the structure of test_autopilot_env_linking.py: marker-bracketed
block, static-parse + behavioral subprocess tests against tmp fixtures.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKTREE_PHASE = REPO_ROOT / "scripts" / "autopilot" / "phases" / "worktree.sh"

START_MARKER = "# === SETTINGS-LINK BLOCK START ==="
END_MARKER = "# === SETTINGS-LINK BLOCK END ==="


def _read_script() -> str:
    return WORKTREE_PHASE.read_text(encoding="utf-8")


def _extract_block() -> str:
    text = _read_script()
    start = text.find(START_MARKER)
    end = text.find(END_MARKER)
    assert start != -1, f"Missing {START_MARKER} in phases/worktree.sh"
    assert end != -1, f"Missing {END_MARKER} in phases/worktree.sh"
    assert start < end, "Markers out of order"
    after_start = text.find("\n", start) + 1
    return text[after_start:end]


def _run_block(project: Path, worktree: Path) -> subprocess.CompletedProcess:
    block = _extract_block()
    script = (
        "set -uo pipefail\n"
        f"PROJECT={str(project)!r}\n"
        f"WORKTREE={str(worktree)!r}\n"
        + block
    )
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )


# --- Static-parse tests -------------------------------------------------


def test_block_has_markers():
    text = _read_script()
    assert START_MARKER in text
    assert END_MARKER in text


def test_block_handles_both_settings_files():
    block = _extract_block()
    # Both the local-only and the team-tracked settings should be mirrored.
    assert "settings.local.json" in block
    assert "settings.json" in block


def test_block_handles_mcp_config():
    block = _extract_block()
    # `.mcp.json` has the same project-root visibility gap inside worktrees
    # as the settings files (see manifest.sh:74-86 for the parallel walk).
    assert ".mcp.json" in block


def test_block_emits_warning_when_no_sources_present():
    block = _extract_block()
    # Defense in depth: when main has none of the mirrored files, the
    # sub-Claude in the worktree will only see ~/.claude/ — surface that
    # explicitly so a future maintainer doesn't chase the same ghost bug.
    assert "WARNING" in block


def test_block_uses_symlink_for_settings_and_filtered_copy_for_mcp():
    block = _extract_block()
    # Settings files are symlinked so the worktree stays in sync with
    # main edits. `.mcp.json` is deliberately NOT symlinked — it is a
    # python3-filtered copy that strips browser-automation servers
    # (80682bd, swap exhaustion). A raw `cp` would reintroduce them.
    assert "ln -s" in block
    assert "python3" in block
    assert "cp " not in block


def test_block_skips_existing_destinations():
    block = _extract_block()
    # Don't clobber a worktree-local settings file (e.g., one written by
    # the using-git-worktrees skill).
    assert "! -e" in block


def test_block_skips_when_source_missing():
    block = _extract_block()
    # Source check before symlinking — main may not have project settings.
    assert "-f" in block or "-e" in block


# --- Behavioral tests ---------------------------------------------------


def _make_fixture(tmp_path: Path, with_local: bool = True,
                  with_team: bool = False,
                  with_mcp: bool = False) -> tuple[Path, Path]:
    project = tmp_path / "project"
    worktree = tmp_path / "worktree"
    project.mkdir()
    worktree.mkdir()
    if with_local or with_team:
        (project / ".claude").mkdir()
    if with_local:
        (project / ".claude" / "settings.local.json").write_text(
            '{"permissions": {"allow": ["Bash(pytest *)"]}}\n'
        )
    if with_team:
        (project / ".claude" / "settings.json").write_text(
            '{"permissions": {"allow": ["Read(//main/**)"]}}\n'
        )
    if with_mcp:
        (project / ".mcp.json").write_text(
            '{"mcpServers": {'
            '"foo": {"command": "foo-bin"}, '
            '"playwright": {"command": "npx", '
            '"args": ["@playwright/mcp@latest"]}}}\n'
        )
    return project, worktree


def test_behavioral_local_settings_linked(tmp_path):
    project, worktree = _make_fixture(tmp_path, with_local=True)
    result = _run_block(project, worktree)
    assert result.returncode == 0, f"Block failed: {result.stderr}"

    dest = worktree / ".claude" / "settings.local.json"
    assert dest.is_symlink(), "Expected settings.local.json to be a symlink"
    assert dest.resolve() == (
        project / ".claude" / "settings.local.json"
    ).resolve()
    # Sanity: contents readable through the symlink.
    assert "pytest" in dest.read_text(encoding="utf-8")


def test_behavioral_team_settings_linked_when_present(tmp_path):
    project, worktree = _make_fixture(
        tmp_path, with_local=False, with_team=True
    )
    result = _run_block(project, worktree)
    assert result.returncode == 0, f"Block failed: {result.stderr}"

    dest = worktree / ".claude" / "settings.json"
    assert dest.is_symlink(), "Expected settings.json to be a symlink"
    assert dest.resolve() == (
        project / ".claude" / "settings.json"
    ).resolve()


def test_behavioral_both_settings_linked(tmp_path):
    project, worktree = _make_fixture(
        tmp_path, with_local=True, with_team=True
    )
    result = _run_block(project, worktree)
    assert result.returncode == 0, f"Block failed: {result.stderr}"

    assert (worktree / ".claude" / "settings.local.json").is_symlink()
    assert (worktree / ".claude" / "settings.json").is_symlink()


def test_behavioral_no_settings_in_main_is_noop(tmp_path):
    project, worktree = _make_fixture(
        tmp_path, with_local=False, with_team=False
    )
    result = _run_block(project, worktree)
    assert result.returncode == 0, f"Block failed: {result.stderr}"

    # Should not have created .claude/ in worktree if nothing to link.
    assert not (worktree / ".claude" / "settings.local.json").exists()
    assert not (worktree / ".claude" / "settings.json").exists()


def test_behavioral_warns_when_no_sources_present(tmp_path):
    """The original bug was silent — pytest just halted on a prompt. When
    main has nothing to mirror and the worktree starts empty, surface that
    explicitly so the same ghost bug isn't chased twice."""
    project, worktree = _make_fixture(
        tmp_path, with_local=False, with_team=False
    )
    result = _run_block(project, worktree)
    assert result.returncode == 0
    assert "WARNING" in result.stderr
    assert "user-level" in result.stderr


def test_behavioral_warning_suppressed_when_worktree_has_local_settings(
    tmp_path,
):
    """If the worktree already has its own settings.local.json (e.g., from
    the using-git-worktrees skill), the warning is noise — the worktree is
    already configured."""
    project, worktree = _make_fixture(
        tmp_path, with_local=False, with_team=False
    )
    (worktree / ".claude").mkdir()
    (worktree / ".claude" / "settings.local.json").write_text(
        '{"permissions": {"allow": ["Edit"]}}\n'
    )
    result = _run_block(project, worktree)
    assert result.returncode == 0
    assert "WARNING" not in result.stderr


def test_behavioral_mcp_config_filtered_copy(tmp_path):
    """`.mcp.json` is mirrored as a filtered COPY, not a symlink (changed
    in 80682bd): browser-automation servers launch Chromium eagerly at
    every claude spawn (~3 GB RSS per iteration) and caused swap
    exhaustion, so they are stripped from the worktree copy. A symlink
    can't filter — and must not be reintroduced."""
    import json

    project, worktree = _make_fixture(
        tmp_path, with_local=False, with_mcp=True
    )
    result = _run_block(project, worktree)
    assert result.returncode == 0, f"Block failed: {result.stderr}"

    dest = worktree / ".mcp.json"
    assert dest.is_file(), "Expected .mcp.json to exist in the worktree"
    assert not dest.is_symlink(), (
        "Expected .mcp.json to be a filtered copy, not a symlink — a "
        "symlink would reintroduce browser-automation servers (swap "
        "exhaustion, see worktree.sh SETTINGS-LINK block)"
    )
    servers = json.loads(dest.read_text(encoding="utf-8"))["mcpServers"]
    assert "foo" in servers, "Non-browser MCP servers must be preserved"
    assert "playwright" not in servers, (
        "Browser-automation MCP servers must be stripped from the "
        "worktree copy"
    )


def test_behavioral_mcp_config_not_overwritten(tmp_path):
    project, worktree = _make_fixture(
        tmp_path, with_local=False, with_mcp=True
    )
    pre_existing = worktree / ".mcp.json"
    pre_existing.write_text('{"mcpServers": {"local-only": {}}}\n')

    result = _run_block(project, worktree)
    assert result.returncode == 0
    assert not pre_existing.is_symlink()
    assert "local-only" in pre_existing.read_text(encoding="utf-8")


def test_behavioral_existing_destination_not_overwritten(tmp_path):
    """If the worktree already has a .claude/settings.local.json (e.g.
    written by the using-git-worktrees skill), do not clobber it."""
    project, worktree = _make_fixture(tmp_path, with_local=True)
    (worktree / ".claude").mkdir()
    pre_existing = worktree / ".claude" / "settings.local.json"
    pre_existing.write_text('{"permissions": {"allow": ["Edit"]}}\n')

    result = _run_block(project, worktree)
    assert result.returncode == 0, f"Block failed: {result.stderr}"

    # Pre-existing file preserved, not turned into a symlink.
    assert not pre_existing.is_symlink()
    assert "Edit" in pre_existing.read_text(encoding="utf-8")


def test_behavioral_idempotent_when_run_twice(tmp_path):
    project, worktree = _make_fixture(tmp_path, with_local=True)
    first = _run_block(project, worktree)
    assert first.returncode == 0
    second = _run_block(project, worktree)
    assert second.returncode == 0, f"Second run failed: {second.stderr}"

    dest = worktree / ".claude" / "settings.local.json"
    assert dest.is_symlink()
    assert dest.resolve() == (
        project / ".claude" / "settings.local.json"
    ).resolve()

# Autopilot is parked: non-functional since 0.33.0, retained for possible
# future revival. Its tests are skipped so the suite gates only active
# plugin surface. To revive, delete this block (and its counterparts in
# the other autopilot/ralph test files).
import pytest as _pytest_parked
pytestmark = _pytest_parked.mark.skip(
    reason="autopilot parked (non-functional since 0.33.0; see README changelog)"
)
