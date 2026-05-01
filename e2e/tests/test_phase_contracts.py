"""Static-parse tests for the phase script + shared library decomposition.
Mirrors test_ralph_sentinels.py — no subprocess execution; assertions on
text content of bash files."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RALPH_DIR = REPO_ROOT / "docs" / "ralph_loops"
LIB_DIR = RALPH_DIR / "lib"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_lib_process_exists_with_required_functions():
    proc = LIB_DIR / "process.sh"
    assert proc.is_file(), "lib/process.sh must exist"
    text = _read(proc)
    for fn in (
        "start_heartbeat()",
        "stop_heartbeat()",
        "start_watchdog()",
        "stop_watchdog()",
        "cleanup()",
        "kill_claude()",
        "run_claude_phase()",
    ):
        assert fn in text, f"lib/process.sh must define {fn}"


def test_lib_process_uses_set_u_only():
    text = _read(LIB_DIR / "process.sh")
    assert "set -u" in text, "lib/process.sh must declare 'set -u'"
    assert "set -e" not in text, "lib/process.sh must NOT use 'set -e' (Decision 7)"


def test_run_ralph_does_not_redefine_shared_functions():
    """The 5 functions duplicated between autopilot.sh and run-ralph.sh
    must be defined ONCE — in lib/process.sh — after the refactor. Each
    must have count=0 in run-ralph.sh (the function definition has been
    removed; only the call site remains, and that uses bare names like
    'start_heartbeat ' not 'start_heartbeat()')."""
    text = (RALPH_DIR / "run-ralph.sh").read_text(encoding="utf-8")
    for fn in (
        "start_heartbeat()",
        "stop_heartbeat()",
        "start_watchdog()",
        "stop_watchdog()",
        "cleanup()",
    ):
        # Function-DEFINITION pattern is `name() {` — count must be 0.
        assert f"{fn} {{" not in text and f"{fn}\n{{" not in text, \
            f"run-ralph.sh must not define {fn} — sourced from lib/process.sh"


def test_autopilot_sources_lib_process():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    assert 'source "$SCRIPT_DIR/lib/process.sh"' in text, \
        "autopilot.sh must source lib/process.sh"


def test_autopilot_uses_set_u_only():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    assert "set -u" in text and "set -uo pipefail" not in text, \
        "autopilot.sh must declare 'set -u' (not '-uo pipefail') — Decision 7"


def test_autopilot_does_not_redefine_lib_functions():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    # Definition pattern is `name() {` — count must be 0 for all 7 lib functions.
    for fn in (
        "cleanup()",
        "kill_claude()",
        "start_heartbeat()",
        "stop_heartbeat()",
        "start_watchdog()",
        "stop_watchdog()",
        "run_claude_phase()",
    ):
        assert f"{fn} {{" not in text and f"{fn}\n{{" not in text, \
            f"autopilot.sh must not define {fn} — sourced from lib/process.sh"


def test_lib_stages_exists_with_report_stage():
    stages = LIB_DIR / "stages.sh"
    assert stages.is_file(), "lib/stages.sh must exist"
    text = _read(stages)
    assert "report_stage()" in text, "lib/stages.sh must define report_stage()"
    # Must accept four positional args (phase, total, name, status)
    assert "$1" in text and "$2" in text and "$3" in text and "$4" in text, \
        "report_stage must accept phase/total/name/status positional args"


def test_autopilot_uses_report_stage_not_banner():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    assert "source \"$SCRIPT_DIR/lib/stages.sh\"" in text, \
        "autopilot.sh must source lib/stages.sh"
    assert "report_stage " in text, "autopilot.sh must call report_stage"
    # Old banners removed
    assert "=== Phase 1:" not in text and "=== Phase 2:" not in text, \
        "autopilot.sh must not use legacy === Phase N: === banners"


def test_autopilot_uses_strict_task_regex():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    # The strict regex only matches task headings (### Task N: or ### ✅ Task N:)
    assert "^### (✅|🔄)?[[:space:]]*Task[[:space:]]*[0-9]" in text or \
           "^### (\\u2705|\\U0001f504)?\\\\s*Task" in text, \
        "autopilot.sh task counting must use a strict task-heading regex, " \
        "not the coarse '^### ' matcher"


PHASES_DIR = RALPH_DIR / "phases"

PHASE_HEADER_FIELDS = ("# PHASE:", "# INPUTS:", "# OUTPUTS:", "# EXIT CODES:")


def test_phases_dir_exists():
    assert PHASES_DIR.is_dir(), "docs/ralph_loops/phases/ must exist"


def test_phase_template_declares_contract():
    template = PHASES_DIR / "_TEMPLATE.sh"
    assert template.is_file(), "phases/_TEMPLATE.sh must exist"
    text = _read(template)
    for field in PHASE_HEADER_FIELDS:
        assert field in text, f"phases/_TEMPLATE.sh must declare {field}"
    assert "set -u" in text, "phases/_TEMPLATE.sh must use set -u"
    assert "lib/process.sh" in text, "phases must source lib/process.sh"


def test_phase_plan_exists_and_conforms():
    plan = PHASES_DIR / "plan.sh"
    assert plan.is_file(), "phases/plan.sh must exist"
    text = _read(plan)
    for field in PHASE_HEADER_FIELDS:
        assert field in text, f"phases/plan.sh missing header field: {field}"
    assert "lib/process.sh" in text, "phases/plan.sh must source lib/process.sh"
    assert "WRITE-PLAN.md" in text, "phases/plan.sh must reference WRITE-PLAN.md"


def test_phase_worktree_exists_and_conforms():
    wt = PHASES_DIR / "worktree.sh"
    assert wt.is_file(), "phases/worktree.sh must exist"
    text = _read(wt)
    for field in PHASE_HEADER_FIELDS:
        assert field in text
    # Env-link block must be preserved verbatim
    assert "=== ENV-LINK BLOCK START ===" in text
    assert "=== ENV-LINK BLOCK END ===" in text
    assert "git worktree add" in text or 'git -C "$PROJECT" worktree add' in text
    # Reads WORKTREE_DIR from environment (no stdout-capture pattern)
    assert "WORKTREE_DIR" in text
    # Emits the structured halt for uncommitted-main case
    assert "uncommitted_main" in text


def test_phase_mockup_exists_and_conforms():
    p = PHASES_DIR / "mockup.sh"
    assert p.is_file()
    text = _read(p)
    for f in PHASE_HEADER_FIELDS:
        assert f in text
    assert "MOCKUP-FIDELITY.md" in text
    assert "MAX_MOCKUP_ITERATIONS" in text


def test_phase_verify_exists_and_conforms():
    p = PHASES_DIR / "verify.sh"
    assert p.is_file()
    text = _read(p)
    for f in PHASE_HEADER_FIELDS:
        assert f in text
    assert "VERIFY-BRANCH.md" in text
    assert ".finish-status" in text


def test_phase_preflight_exists_and_conforms():
    p = PHASES_DIR / "preflight.sh"
    assert p.is_file()
    text = _read(p)
    for f in PHASE_HEADER_FIELDS:
        assert f in text
    assert "lib/manifest.sh" in text
    assert "lib/halt.sh" in text
    # Must accept the "no plan yet" path (exit 3)
    assert "exit 3" in text


def test_finish_branch_md_is_deleted():
    assert not (RALPH_DIR / "FINISH-BRANCH.md").exists(), \
        "FINISH-BRANCH.md is deleted per design Decision 8"


def test_no_active_finish_branch_references():
    """No skill or active plan should reference FINISH-BRANCH.md after deletion.
    Allowed: this impl plan and the source design doc (which document the
    deletion). Allowed if obsoleted (struck-through) in 2026-04-08-plugin-split-plan."""
    skills_dir = REPO_ROOT / "skills"
    refs = []
    for md in skills_dir.rglob("*.md"):
        if "FINISH-BRANCH.md" in md.read_text(encoding="utf-8"):
            refs.append(str(md.relative_to(REPO_ROOT)))
    assert refs == [], f"FINISH-BRANCH.md still referenced in skills: {refs}"
