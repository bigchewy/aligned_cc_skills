"""Static-parse tests asserting each phase script exports the correct
ANTHROPIC_MODEL and CLAUDE_CODE_SUBAGENT_MODEL defaults, and that the
claude -p call sites use --bare. No subprocess execution — assertions
on text content of bash files."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RALPH_DIR = REPO_ROOT / "docs" / "ralph_loops"
PHASES_DIR = RALPH_DIR / "phases"
LIB_DIR = RALPH_DIR / "lib"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_plan_phase_exports_anthropic_model_opus():
    text = _read(PHASES_DIR / "plan.sh")
    assert 'export ANTHROPIC_MODEL="${PLAN_MODEL:-opus}"' in text, (
        "phases/plan.sh must export ANTHROPIC_MODEL with PLAN_MODEL override "
        "defaulting to opus"
    )


def test_plan_phase_exports_subagent_model_opus():
    text = _read(PHASES_DIR / "plan.sh")
    assert 'export CLAUDE_CODE_SUBAGENT_MODEL="${PLAN_SUBAGENT_MODEL:-opus}"' in text, (
        "phases/plan.sh must export CLAUDE_CODE_SUBAGENT_MODEL with "
        "PLAN_SUBAGENT_MODEL override defaulting to opus"
    )


def test_mockup_phase_exports_anthropic_model_sonnet():
    text = _read(PHASES_DIR / "mockup.sh")
    assert 'export ANTHROPIC_MODEL="${MOCKUP_MODEL:-sonnet}"' in text, (
        "phases/mockup.sh must export ANTHROPIC_MODEL with MOCKUP_MODEL "
        "override defaulting to sonnet"
    )


def test_mockup_phase_exports_subagent_model_sonnet():
    text = _read(PHASES_DIR / "mockup.sh")
    assert 'export CLAUDE_CODE_SUBAGENT_MODEL="${MOCKUP_SUBAGENT_MODEL:-sonnet}"' in text, (
        "phases/mockup.sh must export CLAUDE_CODE_SUBAGENT_MODEL with "
        "MOCKUP_SUBAGENT_MODEL override defaulting to sonnet"
    )


def test_verify_phase_exports_anthropic_model_sonnet():
    text = _read(PHASES_DIR / "verify.sh")
    assert 'export ANTHROPIC_MODEL="${VERIFY_MODEL:-sonnet}"' in text, (
        "phases/verify.sh must export ANTHROPIC_MODEL with VERIFY_MODEL "
        "override defaulting to sonnet (NOT haiku — verify must interpret "
        "failing stack traces and build errors)"
    )


def test_verify_phase_exports_subagent_model_sonnet():
    text = _read(PHASES_DIR / "verify.sh")
    assert 'export CLAUDE_CODE_SUBAGENT_MODEL="${VERIFY_SUBAGENT_MODEL:-sonnet}"' in text, (
        "phases/verify.sh must export CLAUDE_CODE_SUBAGENT_MODEL with "
        "VERIFY_SUBAGENT_MODEL override defaulting to sonnet"
    )


def test_run_ralph_exports_anthropic_model_sonnet():
    text = _read(RALPH_DIR / "run-ralph.sh")
    assert 'export ANTHROPIC_MODEL="${RALPH_MODEL:-sonnet}"' in text, (
        "run-ralph.sh must export ANTHROPIC_MODEL with RALPH_MODEL "
        "override defaulting to sonnet (highest-leverage downshift — "
        "up to 50 iterations dominate total cost)"
    )


def test_run_ralph_exports_subagent_model_sonnet():
    text = _read(RALPH_DIR / "run-ralph.sh")
    assert 'export CLAUDE_CODE_SUBAGENT_MODEL="${RALPH_SUBAGENT_MODEL:-sonnet}"' in text, (
        "run-ralph.sh must export CLAUDE_CODE_SUBAGENT_MODEL with "
        "RALPH_SUBAGENT_MODEL override defaulting to sonnet"
    )


def test_lib_process_uses_bare_flag():
    text = _read(LIB_DIR / "process.sh")
    assert 'claude -p --bare - < "$PROMPT_FILE"' in text, (
        "lib/process.sh must invoke claude -p with --bare flag "
        "(Anthropic-recommended mode for scripted calls, skips "
        "MCP/hooks/CLAUDE.md auto-discovery, reduces token spend)"
    )


def test_run_ralph_uses_bare_flag():
    text = _read(RALPH_DIR / "run-ralph.sh")
    assert 'claude -p --bare - < "$PROMPT_FILE"' in text, (
        "run-ralph.sh must invoke claude -p with --bare flag"
    )


def test_autopilot_header_documents_model_env_vars():
    text = _read(RALPH_DIR / "autopilot.sh")
    # Anchor on the comment-prefix form to verify the HEADER documents
    # the var — not the export line from earlier tasks, which would
    # produce a false-pass.
    for var in ("PLAN_MODEL", "MOCKUP_MODEL", "VERIFY_MODEL", "RALPH_MODEL"):
        assert f"#   {var}" in text, (
            f"autopilot.sh header must document the {var} env var so users "
            "can discover the override knob (look for the '#   NAME' line)"
        )


def test_run_ralph_header_documents_model_env_vars():
    text = _read(RALPH_DIR / "run-ralph.sh")
    # Same anchor as above — comment-prefix form distinguishes the
    # header doc line from the export statement added in Task 4.
    for var in ("RALPH_MODEL", "RALPH_SUBAGENT_MODEL"):
        assert f"#   {var}" in text, (
            f"run-ralph.sh header must document the {var} env var "
            "(look for the '#   NAME' line)"
        )
