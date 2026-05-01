"""Tests for the env-linking block in phases/worktree.sh. Verifies that
per-app/per-package env symlinks in the main repo are mirrored into the
worktree, while regular files at the root are still linked. Behavioral
via subprocess against a fixture monorepo; static-parse for regression-
guard on key patterns. (Block was extracted from autopilot.sh in Task 8.)"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKTREE_PHASE = REPO_ROOT / "docs" / "ralph_loops" / "phases" / "worktree.sh"

START_MARKER = "# === ENV-LINK BLOCK START ==="
END_MARKER = "# === ENV-LINK BLOCK END ==="


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


def test_block_uses_dash_e_for_existence_checks():
    block = _extract_block()
    # Source check should use -e (not -f) so symlinks are detected.
    assert '-e "$PROJECT/$envfile"' in block
    assert '! -e "$WORKTREE/$envfile"' in block


def test_block_walks_per_app_symlinks():
    block = _extract_block()
    # Mirror symlinks from main, not regular files.
    assert "find" in block
    assert "-type l" in block
    assert "-name '.env*'" in block
    assert "readlink" in block


def test_block_prunes_internal_dirs():
    block = _extract_block()
    # Avoid recursion into git internals, prior worktrees, and node_modules.
    assert ".git/" in block
    assert ".worktrees/" in block
    assert "node_modules/" in block


def test_block_skips_existing_destinations():
    block = _extract_block()
    assert '[ -e "$dest" ] && continue' in block


# --- Behavioral tests ---------------------------------------------------


def _make_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Build a fake monorepo and corresponding empty worktree tree."""
    project = tmp_path / "project"
    worktree = tmp_path / "worktree"

    (project / "apps" / "planted").mkdir(parents=True)
    (project / "apps" / "aligned").mkdir(parents=True)
    (project / "packages" / "engine").mkdir(parents=True)
    (project / ".env.local").write_text("ROOT=1\n")
    os.symlink("../../.env.local", project / "apps" / "planted" / ".env.local")
    os.symlink("../../.env.local", project / "apps" / "aligned" / ".env.local")
    os.symlink("../../.env.local", project / "packages" / "engine" / ".env.local")

    (worktree / "apps" / "planted").mkdir(parents=True)
    (worktree / "apps" / "aligned").mkdir(parents=True)
    (worktree / "packages" / "engine").mkdir(parents=True)

    return project, worktree


def test_behavioral_root_env_linked(tmp_path):
    project, worktree = _make_fixture(tmp_path)
    result = _run_block(project, worktree)
    assert result.returncode == 0, f"Block failed: {result.stderr}"

    root_link = worktree / ".env.local"
    assert root_link.is_symlink()
    assert root_link.resolve() == (project / ".env.local").resolve()


def test_behavioral_per_app_symlinks_mirrored(tmp_path):
    project, worktree = _make_fixture(tmp_path)
    result = _run_block(project, worktree)
    assert result.returncode == 0, f"Block failed: {result.stderr}"

    for rel in (
        "apps/planted/.env.local",
        "apps/aligned/.env.local",
        "packages/engine/.env.local",
    ):
        link = worktree / rel
        assert link.is_symlink(), f"Missing symlink at {rel}"
        # Target should match what's in main verbatim — relative target preserved.
        assert os.readlink(link) == "../../.env.local", (
            f"Unexpected target for {rel}: {os.readlink(link)}"
        )


def test_behavioral_idempotent_when_run_twice(tmp_path):
    project, worktree = _make_fixture(tmp_path)
    _run_block(project, worktree)
    result2 = _run_block(project, worktree)
    assert result2.returncode == 0

    link = worktree / "apps" / "planted" / ".env.local"
    assert link.is_symlink()
    assert os.readlink(link) == "../../.env.local"


def test_behavioral_existing_destination_not_overwritten(tmp_path):
    project, worktree = _make_fixture(tmp_path)
    pre_existing = worktree / "apps" / "planted" / ".env.local"
    os.symlink("/nonexistent/somewhere", pre_existing)

    result = _run_block(project, worktree)
    assert result.returncode == 0
    assert os.readlink(pre_existing) == "/nonexistent/somewhere"


def test_behavioral_single_package_repo_no_crash(tmp_path):
    project = tmp_path / "project"
    worktree = tmp_path / "worktree"
    project.mkdir()
    worktree.mkdir()
    (project / ".env.local").write_text("ROOT=1\n")

    result = _run_block(project, worktree)
    assert result.returncode == 0, (
        f"Block failed on single-package repo: {result.stderr}"
    )
    assert (worktree / ".env.local").is_symlink()


def test_behavioral_skips_worktrees_dir(tmp_path):
    """A stray .env.local symlink under .worktrees/ must NOT be mirrored
    (avoids recursion when WORKTREE itself lives under PROJECT/.worktrees/)."""
    project, worktree = _make_fixture(tmp_path)
    stray = project / ".worktrees" / "old" / "apps" / "foo"
    stray.mkdir(parents=True)
    os.symlink("../../../../.env.local", stray / ".env.local")

    result = _run_block(project, worktree)
    assert result.returncode == 0
    assert not (worktree / ".worktrees").exists()


def test_behavioral_skips_when_app_dir_missing_in_worktree(tmp_path):
    project = tmp_path / "project"
    worktree = tmp_path / "worktree"
    (project / "apps" / "foo").mkdir(parents=True)
    (project / ".env.local").write_text("ROOT=1\n")
    os.symlink("../../.env.local", project / "apps" / "foo" / ".env.local")
    worktree.mkdir()

    result = _run_block(project, worktree)
    assert result.returncode == 0
    assert not (worktree / "apps" / "foo" / ".env.local").exists()


def test_behavioral_does_not_mirror_regular_files(tmp_path):
    """Regular env files in app dirs are user-managed state; only symlinks
    are mirrored."""
    project = tmp_path / "project"
    worktree = tmp_path / "worktree"
    (project / "apps" / "foo").mkdir(parents=True)
    (worktree / "apps" / "foo").mkdir(parents=True)
    (project / ".env.local").write_text("ROOT=1\n")
    (project / "apps" / "foo" / ".env.local").write_text("APP_REAL=1\n")

    result = _run_block(project, worktree)
    assert result.returncode == 0
    assert not (worktree / "apps" / "foo" / ".env.local").exists()
