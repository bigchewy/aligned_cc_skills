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
])
def test_format_halt_echoes_canonical_fix(reason, needle, tmp_path):
    r = _bash(f"format_halt {reason}", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert needle in r.stdout, (
        f"format_halt {reason} fix-instructions missing expected text: {needle!r}\n"
        f"actual stdout:\n{r.stdout}"
    )


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
