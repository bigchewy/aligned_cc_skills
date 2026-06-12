"""Static-parse + bash-function tests for the halt protocol (lib/halt.sh
and the autopilot-halt-format.md taxonomy)."""

from __future__ import annotations
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HALT_SH = REPO_ROOT / "scripts" / "autopilot" / "lib" / "halt.sh"
HALT_DOC = REPO_ROOT / "skills" / "_shared" / "autopilot-halt-format.md"

EXPECTED_REASONS = [
    "mcp_unreachable",
    "mcp_tool_not_allowlisted",
    "manifest_malformed",
    "verify_failed",
    "phase_crashed",
    "executed_worktree_exists",
]


def test_halt_format_doc_exists():
    assert HALT_DOC.is_file(), "skills/_shared/autopilot-halt-format.md must exist"


def test_halt_format_doc_lists_all_reasons():
    text = HALT_DOC.read_text(encoding="utf-8")
    for r in EXPECTED_REASONS:
        assert r in text, f"halt-format doc must list reason: {r}"


def _bash(cmd: str, cwd: Path) -> subprocess.CompletedProcess:
    full = f'set -u; source "{HALT_SH}"; {cmd}'
    return subprocess.run(
        ["bash", "-c", full], capture_output=True, text=True, cwd=cwd
    )


def test_halt_sh_exists_with_required_functions():
    assert HALT_SH.is_file()
    text = HALT_SH.read_text(encoding="utf-8")
    for fn in ("write_halt()", "read_halt()", "format_halt()"):
        assert fn in text, f"lib/halt.sh must define {fn}"


def test_write_halt_creates_sentinel():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        r = _bash(
            f'HALT_PATH="{d}/.autopilot-halt" '
            f'write_halt mcp_unreachable preflight "playwright server undefined"',
            cwd=d,
        )
        assert r.returncode == 0, r.stderr
        sentinel = d / ".autopilot-halt"
        assert sentinel.is_file()
        text = sentinel.read_text()
        assert "reason: mcp_unreachable" in text
        assert "phase: preflight" in text


# Stable user-facing substrings — a typo in the corresponding heredoc would
# fail this and force the author to look at what users actually read.
@pytest.mark.parametrize("reason,needle", [
    ("mcp_unreachable", "Define the server in .mcp.json"),
    ("mcp_tool_not_allowlisted", ".claude/settings.local.json allowlist"),
    ("manifest_malformed", "must start with `---`"),
    ("verify_failed", ".finish-status"),
    ("executed_worktree_exists", "recreate the plan-path sentinel"),
])
def test_format_halt_echoes_canonical_fix(reason, needle, tmp_path):
    r = _bash(f"format_halt {reason}", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert needle in r.stdout, (
        f"format_halt {reason} fix-instructions missing expected text: {needle!r}\n"
        f"actual stdout:\n{r.stdout}"
    )


@pytest.mark.parametrize("log_tail", [
    "API Error: Stream idle timeout - partial response received",
    "API Error: 503 service unavailable",
    "API Error: 502 Bad Gateway",
    "API Error: Overloaded",
    "API Error: Connection error",
    "API Error: fetch failed",
    "Bedrock invocation failed: ThrottlingException",
    "Request timed out after 30s",
])
def test_is_transient_error_detects_known_signatures(tmp_path, log_tail):
    """Patterns the Anthropic CLI emits on transient infrastructure
    failures must be classified as transient so the orchestrator skips
    the phase_crashed halt and lets a plain re-run recover."""
    log = tmp_path / "autopilot.log"
    log.write_text(f"some earlier output\n[heartbeat] ...\n{log_tail}\n")
    r = _bash(f'is_transient_error "{log}"', cwd=tmp_path)
    assert r.returncode == 0, (
        f"expected transient classification for tail {log_tail!r}; "
        f"got rc={r.returncode}, stderr={r.stderr}")


@pytest.mark.parametrize("log_tail", [
    "TypeError: cannot read property 'x' of undefined",
    "ERROR: Plan file does not exist: /tmp/missing.md",
    "permission denied",
    "",
])
def test_is_transient_error_rejects_real_crashes(tmp_path, log_tail):
    """Non-transient errors (application bugs, missing files, permission
    errors) must NOT be misclassified as transient — they need the halt
    sentinel so the user investigates rather than reruns blindly."""
    log = tmp_path / "autopilot.log"
    log.write_text(f"some earlier output\n{log_tail}\n")
    r = _bash(f'is_transient_error "{log}"', cwd=tmp_path)
    assert r.returncode == 1, (
        f"expected non-transient for tail {log_tail!r}; "
        f"got rc={r.returncode}, stdout={r.stdout}")


def test_is_transient_error_handles_missing_log(tmp_path):
    """Defensive: a missing log path must return non-transient rather than
    crashing — we'd rather write a halt than swallow a real failure."""
    r = _bash(f'is_transient_error "{tmp_path}/nonexistent.log"', cwd=tmp_path)
    assert r.returncode == 1


def test_autopilot_run_phase_skips_halt_on_transient():
    """autopilot.sh's run_phase catch-all must call is_transient_error and
    skip the write_halt when it returns true. This is the structural
    guarantee that transient API errors don't require manual halt deletion."""
    autopilot = REPO_ROOT / "scripts" / "autopilot" / "autopilot.sh"
    text = autopilot.read_text(encoding="utf-8")
    # The is_transient_error check must appear in run_phase before the
    # write_halt phase_crashed callsite — otherwise transient errors
    # still write the halt and the fix is dead.
    transient_idx = text.find("is_transient_error")
    crashed_idx = text.find("write_halt phase_crashed")
    assert transient_idx != -1, \
        "autopilot.sh must check is_transient_error in run_phase"
    assert crashed_idx != -1, \
        "autopilot.sh must still write_halt phase_crashed for real crashes"
    assert transient_idx < crashed_idx, \
        "is_transient_error check must precede write_halt phase_crashed"


def test_phase_verify_emits_halt_on_failure():
    verify = REPO_ROOT / "scripts" / "autopilot" / "phases" / "verify.sh"
    text = verify.read_text(encoding="utf-8")
    assert "lib/halt.sh" in text, "verify.sh must source lib/halt.sh"
    assert "write_halt verify_failed" in text, \
        "verify.sh must emit halt-with-reason verify_failed when .finish-status is FAILED"


def test_format_halt_cases_match_write_halt_callsites():
    """Every reason in format_halt must have a write_halt callsite (static or
    dynamic-via-check_mcp_tool), and every emitted reason must have a
    format_halt case. Drift in either direction is a bug — phantom reasons
    advertise halts users will never see; undocumented reasons fall through to
    the *) catch-all and print 'Unknown halt reason'."""
    halt_text = HALT_SH.read_text(encoding="utf-8")
    fmt_match = re.search(
        r'format_halt\(\)\s*\{.*?case\s+"\$reason"\s+in(.*?)esac',
        halt_text, re.DOTALL)
    assert fmt_match, "format_halt case block not found in lib/halt.sh"
    format_halt_cases = set(re.findall(
        r'^\s*([a-z][a-z_0-9]*)\)\s*$', fmt_match.group(1), re.MULTILINE))
    assert format_halt_cases, "extracted zero case labels — regex likely stale"

    sh_files = sorted(
        (REPO_ROOT / "scripts" / "autopilot" / "lib").glob("*.sh"))
    sh_files += sorted(
        (REPO_ROOT / "scripts" / "autopilot" / "phases").glob("*.sh"))
    sh_files.append(REPO_ROOT / "scripts" / "autopilot" / "autopilot.sh")
    static_callsites: set[str] = set()
    for f in sh_files:
        text = f.read_text(encoding="utf-8")
        # Skip the function definition itself in lib/halt.sh
        text = re.sub(r'^write_halt\(\)\s*\{', '', text, flags=re.MULTILINE)
        # Match `write_halt <bare-word>` only — `write_halt "$RESULT" ...`
        # at preflight.sh:58 starts with `"` so won't match [a-z].
        for m in re.finditer(r'\bwrite_halt\s+([a-z][a-z_0-9]*)\b', text):
            static_callsites.add(m.group(1))

    manifest_sh = REPO_ROOT / "scripts" / "autopilot" / "lib" / "manifest.sh"
    manifest_text = manifest_sh.read_text(encoding="utf-8")
    check_mcp = re.search(
        r'check_mcp_tool\(\)\s*\{(.*?)^\}', manifest_text,
        re.DOTALL | re.MULTILINE)
    assert check_mcp, "check_mcp_tool function not found in manifest.sh"
    # An echo immediately followed by `return 2` is a halt reason emission.
    # `echo "ok"` is followed by `return 0` and is correctly excluded.
    dynamic_reasons = set(re.findall(
        r'echo\s+"([a-z][a-z_0-9]*)"\s*\n\s*return\s+2',
        check_mcp.group(1)))

    callsite_reasons = static_callsites | dynamic_reasons
    phantom = format_halt_cases - callsite_reasons
    undocumented = callsite_reasons - format_halt_cases
    assert not phantom, (
        f"format_halt has reasons that no code emits (phantom halts): "
        f"{sorted(phantom)}. Either delete the case from lib/halt.sh or "
        f"add a write_halt callsite.")
    assert not undocumented, (
        f"write_halt callsites emit reasons missing from format_halt: "
        f"{sorted(undocumented)}. These will fall through to the *) "
        f"catch-all and print 'Unknown halt reason: <name>' to users.")
