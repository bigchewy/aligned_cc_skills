"""Tests for the AUTH-COMPAT block in phases/preflight.sh.

The block scans known headless `claude` call sites for the `--bare` flag.
If found, it calls `write_halt headless_auth_incompat preflight ...` and
exits 2. This is defense-in-depth against re-introducing the flag that
broke Max-plan OAuth users (see commit 2d883ef and
docs/lessons-learned/2026-05-14-autopilot-bare-oauth-incompat.md).

Behavioral tests run the extracted block standalone with a stub
`write_halt` that records its argv, mirroring the pattern used in
test_autopilot_env_linking.py.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PREFLIGHT_PHASE = REPO_ROOT / "docs" / "ralph_loops" / "phases" / "preflight.sh"

START_MARKER = "# === AUTH-COMPAT BLOCK START ==="
END_MARKER = "# === AUTH-COMPAT BLOCK END ==="


def _read_script() -> str:
    return PREFLIGHT_PHASE.read_text(encoding="utf-8")


def _extract_block() -> str:
    text = _read_script()
    start = text.find(START_MARKER)
    end = text.find(END_MARKER)
    assert start != -1, f"Missing {START_MARKER} in phases/preflight.sh"
    assert end != -1, f"Missing {END_MARKER} in phases/preflight.sh"
    assert start < end, "Markers out of order"
    after_start = text.find("\n", start) + 1
    return text[after_start:end]


def _run_block(ralph_dir: Path, log_file: Path) -> subprocess.CompletedProcess:
    """Run the extracted block with a stub `write_halt` that appends its
    argv to log_file. The block calls `exit 2` on halt, so we run under
    bash with no `set -e` and check returncode."""
    block = _extract_block()
    stub = (
        "set -u\n"
        f"RALPH_DIR={str(ralph_dir)!r}\n"
        f'write_halt() {{ printf "%s\\n" "$@" >> {str(log_file)!r}; }}\n'
        + block
    )
    return subprocess.run(
        ["bash", "-c", stub],
        capture_output=True,
        text=True,
        check=False,
    )


# --- Static-parse tests ---------------------------------------------------


def test_block_has_markers():
    text = _read_script()
    assert START_MARKER in text
    assert END_MARKER in text


def test_block_targets_both_known_call_sites():
    block = _extract_block()
    assert '"$RALPH_DIR/lib/process.sh"' in block, (
        "AUTH-COMPAT block must scan lib/process.sh"
    )
    assert '"$RALPH_DIR/run-ralph.sh"' in block, (
        "AUTH-COMPAT block must scan run-ralph.sh"
    )


def test_block_uses_canonical_halt_reason():
    block = _extract_block()
    assert "headless_auth_incompat" in block, (
        "AUTH-COMPAT block must use the canonical halt reason "
        "'headless_auth_incompat' — taxonomy is documented in "
        "skills/_shared/autopilot-halt-format.md and the case is in "
        "lib/halt.sh format_halt()."
    )


# --- Behavioral tests -----------------------------------------------------


def _make_fixture(tmp_path: Path, with_bare_in: list[str]) -> tuple[Path, Path]:
    """Build a fake ralph_loops/ tree with lib/process.sh and run-ralph.sh.
    `with_bare_in` is a list of relative paths (e.g., ['lib/process.sh'])
    that should contain `--bare`; the others contain the OAuth-safe form."""
    ralph_dir = tmp_path / "ralph_loops"
    (ralph_dir / "lib").mkdir(parents=True)
    safe = '  claude -p - < "$PROMPT_FILE" &\n'
    bare = '  claude -p --bare - < "$PROMPT_FILE" &\n'
    (ralph_dir / "lib" / "process.sh").write_text(
        bare if "lib/process.sh" in with_bare_in else safe
    )
    (ralph_dir / "run-ralph.sh").write_text(
        bare if "run-ralph.sh" in with_bare_in else safe
    )
    log_file = tmp_path / "write_halt.log"
    return ralph_dir, log_file


def test_behavioral_clean_call_sites_pass(tmp_path):
    ralph_dir, log_file = _make_fixture(tmp_path, with_bare_in=[])
    result = _run_block(ralph_dir, log_file)
    assert result.returncode == 0, (
        f"Block must exit 0 when neither call site has --bare. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert not log_file.exists(), (
        "write_halt must not be called when call sites are clean"
    )


def test_behavioral_bare_in_process_sh_halts(tmp_path):
    ralph_dir, log_file = _make_fixture(tmp_path, with_bare_in=["lib/process.sh"])
    result = _run_block(ralph_dir, log_file)
    assert result.returncode == 2, (
        f"Block must exit 2 (halt) when lib/process.sh contains --bare. "
        f"Got returncode={result.returncode}, stderr={result.stderr!r}"
    )
    assert log_file.exists(), "write_halt must be called"
    log = log_file.read_text()
    assert "headless_auth_incompat" in log
    assert "preflight" in log
    assert "lib/process.sh" in log, (
        "Halt details must name the offending call site so the user can "
        "find and remove --bare"
    )


def test_behavioral_bare_in_run_ralph_halts(tmp_path):
    ralph_dir, log_file = _make_fixture(tmp_path, with_bare_in=["run-ralph.sh"])
    result = _run_block(ralph_dir, log_file)
    assert result.returncode == 2
    assert log_file.exists()
    log = log_file.read_text()
    assert "headless_auth_incompat" in log
    assert "run-ralph.sh" in log


def test_behavioral_missing_call_site_files_pass(tmp_path):
    """If a referenced call-site file doesn't exist, the block must not
    crash — `[ -f ... ]` guards the grep. Future-proofs against rename
    or relocation of process.sh / run-ralph.sh."""
    ralph_dir = tmp_path / "ralph_loops"
    ralph_dir.mkdir()
    # Neither lib/process.sh nor run-ralph.sh exists.
    log_file = tmp_path / "write_halt.log"
    result = _run_block(ralph_dir, log_file)
    assert result.returncode == 0
    assert not log_file.exists()


def test_behavioral_comment_only_mention_does_not_halt(tmp_path):
    """A comment that documents *why* --bare is forbidden (e.g.,
    `# Do NOT use --bare here — breaks OAuth`) is welcome and must not
    trigger a halt. The grep pattern anchors on lines whose first
    non-whitespace token is `claude`, so comment lines (starting with
    `#`) are skipped. This test locks in that semantic — a future
    maintainer who broadens the pattern to a plain substring scan would
    break this test."""
    ralph_dir = tmp_path / "ralph_loops"
    (ralph_dir / "lib").mkdir(parents=True)
    safe_with_comment = (
        "# Do NOT add --bare here — breaks Max-plan OAuth.\n"
        '  claude -p - < "$PROMPT_FILE" &\n'
    )
    (ralph_dir / "lib" / "process.sh").write_text(safe_with_comment)
    (ralph_dir / "run-ralph.sh").write_text(safe_with_comment)
    log_file = tmp_path / "write_halt.log"
    result = _run_block(ralph_dir, log_file)
    assert result.returncode == 0, (
        f"Block must NOT halt when --bare appears only in a comment. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert not log_file.exists(), (
        "write_halt must not be called when --bare is only in a comment"
    )
