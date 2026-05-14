---
---
# Autopilot Model Downshift Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Route autopilot phases to the cheapest model that can do the work — Sonnet for ralph execute, mockup fidelity, and verify; Opus retained for plan writing — by exporting `ANTHROPIC_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL` per phase script. Adopt `--bare` mode for headless `claude -p` invocations per Anthropic guidance.

**Source Design Doc:** `docs/plans/2026-05-14-autopilot-model-downshift-design.md`

**Architecture:** Each phase script (`phases/plan.sh`, `phases/mockup.sh`, `phases/verify.sh`) and the ralph loop (`run-ralph.sh`) exports `ANTHROPIC_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL` before invoking `run_claude_phase`. Defaults are baked in per phase; user overrides via per-phase env vars (`PLAN_MODEL`, `MOCKUP_MODEL`, `VERIFY_MODEL`, `RALPH_MODEL`). Sub-agent model is set explicitly because Anthropic docs confirm subagents do not inherit the parent's `--model` selection. `--bare` is added to both `claude -p` call sites (`lib/process.sh:90`, `run-ralph.sh:238`) after a prompt audit confirms no phase relies on CLAUDE.md auto-discovery.

**Tech Stack:** Bash (autopilot scripts), Python pytest (static-parse tests in `e2e/tests/`).

---

## Prerequisites

None. All changes are within `docs/ralph_loops/` and `e2e/tests/`. No manual setup required.

---

### ✅ Task 1: Add per-phase model env vars to `phases/plan.sh` (Opus)

**Files:**
- Create: `e2e/tests/test_autopilot_model_selection.py`
- Modify: `docs/ralph_loops/phases/plan.sh` (immediately after the `set -u` line near the top)

**Step 1: Write the failing test**

Create `e2e/tests/test_autopilot_model_selection.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v`
Expected: 2 FAILs — the export lines do not yet exist in plan.sh.

**Step 3: Modify `phases/plan.sh`**

In `docs/ralph_loops/phases/plan.sh`, immediately after the `set -u` line near the top, insert the block below. Position relative to the `source "$RALPH_DIR/lib/process.sh"` line is cosmetic — `export` is process-wide and the child `claude -p` inherits regardless. Keeping the block adjacent to `set -u` makes the per-phase model config discoverable when scanning the top of the file.

```bash
# --- Model selection (override via PLAN_MODEL / PLAN_SUBAGENT_MODEL) ---
export ANTHROPIC_MODEL="${PLAN_MODEL:-opus}"
export CLAUDE_CODE_SUBAGENT_MODEL="${PLAN_SUBAGENT_MODEL:-opus}"
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v`
Expected: both plan-phase tests PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_autopilot_model_selection.py docs/ralph_loops/phases/plan.sh
git commit -m "feat(autopilot): pin plan phase to Opus via ANTHROPIC_MODEL export"
```

---

### ✅ Task 2: Add per-phase model env vars to `phases/mockup.sh` (Sonnet)

**Files:**
- Modify: `e2e/tests/test_autopilot_model_selection.py` (add 2 tests)
- Modify: `docs/ralph_loops/phases/mockup.sh` (immediately after the `set -u` line)

**Step 1: Add failing tests**

Append to `e2e/tests/test_autopilot_model_selection.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k mockup`
Expected: 2 FAILs.

**Step 3: Modify `phases/mockup.sh`**

In `docs/ralph_loops/phases/mockup.sh`, immediately after the `set -u` line near the top, insert the block below. (Position relative to the `source` line is cosmetic — see Task 1 for the explanation.)

```bash
# --- Model selection (override via MOCKUP_MODEL / MOCKUP_SUBAGENT_MODEL) ---
export ANTHROPIC_MODEL="${MOCKUP_MODEL:-sonnet}"
export CLAUDE_CODE_SUBAGENT_MODEL="${MOCKUP_SUBAGENT_MODEL:-sonnet}"
```

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k mockup`
Expected: both PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_autopilot_model_selection.py docs/ralph_loops/phases/mockup.sh
git commit -m "feat(autopilot): downshift mockup phase to Sonnet via env var"
```

---

### ✅ Task 3: Add per-phase model env vars to `phases/verify.sh` (Sonnet)

**Files:**
- Modify: `e2e/tests/test_autopilot_model_selection.py` (add 2 tests)
- Modify: `docs/ralph_loops/phases/verify.sh` (immediately after the `set -u` line)

**Step 1: Add failing tests**

Append to `e2e/tests/test_autopilot_model_selection.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k verify`
Expected: 2 FAILs.

**Step 3: Modify `phases/verify.sh`**

In `docs/ralph_loops/phases/verify.sh`, immediately after the `set -u` line near the top, insert the block below. (Position relative to the two `source` lines is cosmetic — see Task 1 for the explanation.)

```bash
# --- Model selection (override via VERIFY_MODEL / VERIFY_SUBAGENT_MODEL) ---
# Sonnet (not Haiku): verify interprets failing stack traces and build
# errors. A misclassification of a real failure as transient is the
# worst-case outcome of model downshifting.
export ANTHROPIC_MODEL="${VERIFY_MODEL:-sonnet}"
export CLAUDE_CODE_SUBAGENT_MODEL="${VERIFY_SUBAGENT_MODEL:-sonnet}"
```

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k verify`
Expected: both PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_autopilot_model_selection.py docs/ralph_loops/phases/verify.sh
git commit -m "feat(autopilot): downshift verify phase to Sonnet via env var"
```

---

### Task 4: Add per-phase model env vars to `run-ralph.sh` (Sonnet)

**Files:**
- Modify: `e2e/tests/test_autopilot_model_selection.py` (add 2 tests)
- Modify: `docs/ralph_loops/run-ralph.sh` (in the env-var/defaults block near top — same block that sets `MAX_ITERATIONS` and `ITERATION_TIMEOUT`)

**Step 1: Add failing tests**

Append to `e2e/tests/test_autopilot_model_selection.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k ralph`
Expected: 2 FAILs.

**Step 3: Modify `run-ralph.sh`**

In `docs/ralph_loops/run-ralph.sh`, locate the env-var defaults block — it begins with `MAX_ITERATIONS="${MAX_ITERATIONS:-50}"` and ends with `MAX_BLOCKED_ITERATIONS="${MAX_BLOCKED_ITERATIONS:-3}"` (the block has 5 entries: `MAX_ITERATIONS`, `ITERATION_TIMEOUT`, `MAX_TIMEOUTS`, `HEARTBEAT_INTERVAL`, `MAX_BLOCKED_ITERATIONS`, with an explanatory comment block between the last two). Insert the new export lines **after the `MAX_BLOCKED_ITERATIONS="${MAX_BLOCKED_ITERATIONS:-3}"` line and before the next non-default assignment (`SCRIPT_DIR="$(...)"`).** Specifically, add:

```bash
# --- Model selection (override via RALPH_MODEL / RALPH_SUBAGENT_MODEL) ---
# Sonnet for the ralph execute loop: up to 50 iterations of TDD task
# execution dominate total autopilot cost. Anthropic docs call Sonnet
# "for daily coding tasks" — this is the canonical use case.
export ANTHROPIC_MODEL="${RALPH_MODEL:-sonnet}"
export CLAUDE_CODE_SUBAGENT_MODEL="${RALPH_SUBAGENT_MODEL:-sonnet}"
```

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k ralph`
Expected: both PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_autopilot_model_selection.py docs/ralph_loops/run-ralph.sh
git commit -m "feat(autopilot): downshift ralph execute loop to Sonnet via env var"
```

---

### Task 5: Audit phase prompts for CLAUDE.md auto-discovery dependencies

**Files:**
- Read-only: `docs/ralph_loops/WRITE-PLAN.md`, `docs/ralph_loops/EXECUTE-PLAN.md`, `docs/ralph_loops/MOCKUP-FIDELITY.md`, `docs/ralph_loops/VERIFY-BRANCH.md`, `CLAUDE.md` (repo root)
- Create: `docs/plans/2026-05-14-autopilot-model-downshift-audit.md` (audit findings doc)

**Step 1: Read each phase prompt and the repo CLAUDE.md**

Read these four prompt files and the repo root `CLAUDE.md`. For each prompt, identify:
- Does it reference skill files by relative path (e.g., `skills/finishing-a-development-branch/SKILL.md`)?
- Does it rely on any convention only documented in CLAUDE.md (path prefixes, banned phrases, registry locations, brand voice files)?
- Does it assume any hook-injected context?

**Step 2: Write the audit document**

Create `docs/plans/2026-05-14-autopilot-model-downshift-audit.md` with this exact structure (do NOT vary the verdict line format — Task 6's skip condition parses it as a literal string):

```markdown
# Autopilot Phase Prompts — `--bare` Audit

Audit performed before adopting `claude -p --bare`. `--bare` skips
MCP/hooks/CLAUDE.md auto-discovery. This document records whether each
phase prompt can run safely without that auto-loaded context.

## WRITE-PLAN.md
- Relative-path skill refs: <list>
- CLAUDE.md conventions relied on: <list or "none">
- Verdict: SAFE | NEEDS_FIX | BLOCKED

## EXECUTE-PLAN.md
<same structure>

## MOCKUP-FIDELITY.md
<same structure>

## VERIFY-BRANCH.md
<same structure>

## Overall verdict

verdict: PROCEED | SKIP-BARE | BLOCKED
```

Fill out each section based on the read. The `## Overall verdict` section MUST contain a line of the exact form `verdict: <VALUE>` where `<VALUE>` is one of `PROCEED`, `SKIP-BARE`, or `BLOCKED`.

Decision rules for the overall verdict:
- All four prompts SAFE → `verdict: PROCEED`
- Any prompt NEEDS_FIX (and none BLOCKED) → `verdict: SKIP-BARE`
- Any prompt BLOCKED → `verdict: BLOCKED`

**Step 3: Validate the verdict format**

Confirm the audit doc contains exactly one line matching the regex `^verdict: (PROCEED|SKIP-BARE|BLOCKED)$`. If not, fix the audit doc before commit. If the verdict is `BLOCKED`, mark this task `🔄 BLOCKED` (the autopilot wrapper will retry; after `MAX_BLOCKED_ITERATIONS` it auto-skips and the user reviews).

**Step 4: Commit**

```bash
git add docs/plans/2026-05-14-autopilot-model-downshift-audit.md
git commit -m "docs: audit phase prompts for --bare compatibility"
```

---

### Task 6: Add `--bare` flag to `claude -p` call sites

> ORDERING: Task 4 modifies `run-ralph.sh` (adds env exports). Task 6 also modifies `run-ralph.sh` (adds `--bare`). Task 4 must complete before Task 6 begins — otherwise the test/implementation in Task 4 will conflict with this task's edits.

> SKIP CONDITION: This task reads the audit doc produced by Task 5 at `docs/plans/2026-05-14-autopilot-model-downshift-audit.md`. Search for a line matching `verdict: PROCEED`. If found, proceed with all steps. If the line is `verdict: SKIP-BARE` or `verdict: BLOCKED`, add the test (Step 1) regardless, but xfail it with `@pytest.mark.xfail(reason="--bare blocked by Task 5 audit verdict")` and skip Steps 3-5. Mark the task ✅ with a deviation note `> AUDIT-VERDICT: SKIP-BARE — implementation deferred` and commit only the xfailed tests.

> BEHAVIORAL-CHANGE CALLOUT: `lib/process.sh` is sourced by `phases/plan.sh`, `phases/mockup.sh`, AND `phases/verify.sh`. Adding `--bare` to its `run_claude_phase` function changes the invocation flag for all three phases simultaneously. The audit in Task 5 covered all three prompts, so this is intentional — but the implementer should know one edit ripples to three phases.

**Files:**
- Modify: `e2e/tests/test_autopilot_model_selection.py` (add 2 tests)
- Modify: `docs/ralph_loops/lib/process.sh` (the `claude -p` line inside `run_claude_phase`)
- Modify: `docs/ralph_loops/run-ralph.sh` (the `claude -p` line inside the iteration loop)

**Step 1: Add failing tests**

Append to `e2e/tests/test_autopilot_model_selection.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k bare`
Expected: 2 FAILs.

**Step 3: Modify `lib/process.sh`**

**Note: this edit propagates to all three phase scripts** (`phases/plan.sh`, `phases/mockup.sh`, `phases/verify.sh`) because they all source `lib/process.sh` and call `run_claude_phase`. The Task 5 audit verdict covers all three prompts.

In `docs/ralph_loops/lib/process.sh`, locate the line inside `run_claude_phase` that invokes claude (currently `claude -p - < "$PROMPT_FILE" &`). Change it to:

```bash
  claude -p --bare - < "$PROMPT_FILE" &
```

**Step 4: Modify `run-ralph.sh`**

In `docs/ralph_loops/run-ralph.sh`, locate the line inside the main iteration `while :` loop that invokes claude (currently `claude -p - < "$PROMPT_FILE" &` with the comment `# Run claude in background so we can enforce a timeout` immediately above). Change it to:

```bash
  claude -p --bare - < "$PROMPT_FILE" &
```

**Step 5: Run tests to verify they pass**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k bare`
Expected: both PASS.

**Step 6: Commit**

```bash
git add e2e/tests/test_autopilot_model_selection.py docs/ralph_loops/lib/process.sh docs/ralph_loops/run-ralph.sh
git commit -m "feat(autopilot): adopt claude -p --bare for headless calls"
```

---

### Task 7: Behavioral integration test — env propagation to a stub `claude` binary

**Files:**
- Create: `e2e/tests/test_autopilot_model_env_propagation.py`

**Step 1: Write the failing behavioral test**

Create `e2e/tests/test_autopilot_model_env_propagation.py`:

```python
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
        # mockup.sh checks plan.md for **Mockups:** field
        (tmpdir / "plan.md").write_text("**Mockups:** none\n")
        env.update(env_overrides)

        subprocess.run(
            ["bash", str(phase_script)],
            env=env,
            capture_output=True,
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
```

**Step 2: Run tests to verify behavior**

Run: `pytest e2e/tests/test_autopilot_model_env_propagation.py -v`

Possible outcomes:
- All 3 PASS → behavior is correct, proceed to commit.
- A test FAILs because the stub claude was not invoked (env_dump file empty) → the phase script aborted earlier than expected; mark task `🔄 BLOCKED` and document which phase aborted (likely missing a required env var; extend the env-overrides dict accordingly in a follow-up iteration). Do NOT loosen the assertions to make tests pass.
- A test FAILs because `ANTHROPIC_MODEL` is wrong → real bug; return to the corresponding Task 1-4 and fix the export line.

**Step 3: Commit**

```bash
git add e2e/tests/test_autopilot_model_env_propagation.py
git commit -m "test(autopilot): behavioral check that phase scripts propagate model env vars to claude"
```

---

### Task 8: Document new env vars in `autopilot.sh` and `run-ralph.sh` headers

**Files:**
- Modify: `docs/ralph_loops/autopilot.sh` (the env-var documentation comment block at the top)
- Modify: `docs/ralph_loops/run-ralph.sh` (the env-var documentation comment block at the top)

**Step 1: Write the failing test**

Append to `e2e/tests/test_autopilot_model_selection.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k header`
Expected: 2 FAILs.

**Step 3: Modify `autopilot.sh` header comments**

In `docs/ralph_loops/autopilot.sh`, locate the existing env-var documentation block at the top (the comments listing `MAX_ITERATIONS`, `ITERATION_TIMEOUT`, `PHASE_TIMEOUT`, `MAX_MOCKUP_ITERATIONS`, `MOCKUP_TIMEOUT`). Immediately after the last existing entry, append:

```bash
#   PLAN_MODEL          — Model for plan phase (default: opus)
#   PLAN_SUBAGENT_MODEL — Subagent model for plan phase (default: opus)
#   MOCKUP_MODEL        — Model for mockup phase (default: sonnet)
#   MOCKUP_SUBAGENT_MODEL — Subagent model for mockup phase (default: sonnet)
#   VERIFY_MODEL        — Model for verify phase (default: sonnet)
#   VERIFY_SUBAGENT_MODEL — Subagent model for verify phase (default: sonnet)
#   RALPH_MODEL         — Model for ralph execute loop (default: sonnet)
#   RALPH_SUBAGENT_MODEL — Subagent model for ralph execute (default: sonnet)
```

**Step 4: Modify `run-ralph.sh` header comments**

In `docs/ralph_loops/run-ralph.sh`, locate the existing env-var documentation block (lines documenting `MAX_ITERATIONS` and `ITERATION_TIMEOUT`). Immediately after, append:

```bash
#   RALPH_MODEL         — Model for the loop (default: sonnet)
#   RALPH_SUBAGENT_MODEL — Subagent model for the loop (default: sonnet)
```

**Step 5: Run tests to verify they pass**

Run: `pytest e2e/tests/test_autopilot_model_selection.py -v -k header`
Expected: both PASS.

**Step 6: Run the full new test file plus existing autopilot tests**

Run: `pytest e2e/tests/test_autopilot_model_selection.py e2e/tests/test_autopilot_model_env_propagation.py e2e/tests/test_phase_contracts.py -v`
Expected: all PASS. No regressions in existing phase-contract tests.

**Step 7: Commit**

```bash
git add e2e/tests/test_autopilot_model_selection.py docs/ralph_loops/autopilot.sh docs/ralph_loops/run-ralph.sh
git commit -m "docs(autopilot): document per-phase model env vars in script headers"
```

---

## Manual Steps (Post-Automation)

After all tasks complete and the branch is merged, the user should:

1. **Run one real autopilot cycle on a representative design doc** to confirm the downshift behaves as expected end-to-end. Watch for: (a) any iteration that fails on Sonnet but would have succeeded on Opus, (b) verify phase correctly classifying a deliberately-failing test (e.g., introduce a `expect(true).toBe(false)` in a test, confirm Sonnet verify flags it FAILED rather than SUCCESS).

2. **Audit `agents/*.md` frontmatter** for any agent pinned to `model: opus` that the autopilot phases might spawn. Currently `agents/project-scanner.md` is pinned to opus. If autopilot phases never invoke project-scanner, no action needed. If they do, decide whether the opus pin is intentional or stale and update accordingly. (No code change required here — this is a one-time audit.)

3. **Watch programmatic credit consumption** on the Anthropic console after 2026-06-15 to confirm projected savings. Baseline against a recent Opus-only run.

4. **Review the audit doc if Task 6 ended with `verdict: SKIP-BARE`.** Read `docs/plans/2026-05-14-autopilot-model-downshift-audit.md` to see which prompt(s) flagged `NEEDS_FIX`. Decide whether to fix those prompts and re-run the audit (which would unlock `--bare` in a follow-up), or accept the missing token-spend optimization. The model-downshift work (the primary cost lever) is already done; `--bare` is secondary.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|-------------|-------------------------|
| 1 | How to control per-phase model | Per-phase `export ANTHROPIC_MODEL` inside each phase script | `--model` flag at call sites; global `settings.json` model key |
| 2 | Verify-phase default model | Sonnet | Haiku (rejected — risk of misclassifying failures) |
| 3 | Mockup-phase default model | Sonnet | Haiku (deferred — no published benchmark for multi-file diff reasoning) |
| 4 | Subagent model handling | Explicit `CLAUDE_CODE_SUBAGENT_MODEL` export per phase | Rely on inheritance (rejected — subagents do not inherit `--model`) |
| 5 | `--bare` adoption | Add to both call sites after audit gate (Task 5) | Skip entirely; adopt unconditionally |
| 6 | Test strategy | Static-parse + one behavioral test with stub `claude` | Pure static-parse (insufficient evidence of env propagation); full integration (requires real claude, breaks CI) |
| 7 | `autopilot.sh` env exports | Do not extend exports — user env propagates automatically | Add `PLAN_MODEL` etc. to `export` lines (unnecessary; Bash inherits) |

### Appendix: Decision Details

#### Decision 1: Per-phase `export` inside each phase script
**Chose:** Each phase script (`plan.sh`, `mockup.sh`, `verify.sh`) and `run-ralph.sh` writes its own `export ANTHROPIC_MODEL="${<PHASE>_MODEL:-<default>}"` near the top, before any `source` or `run_claude_phase` call.

**Why:** Anthropic publishes `ANTHROPIC_MODEL` as the supported env var for session model selection ([model-config](https://code.claude.com/docs/en/model-config)). Setting it inside the phase script gives a single source of truth per phase, makes the default discoverable by reading one file, and avoids plumbing a new parameter through `run_claude_phase` in `lib/process.sh`. User overrides via `PLAN_MODEL`, `RALPH_MODEL`, etc. work because `${PLAN_MODEL:-opus}` defers to the user's env if set.

**Alternatives rejected:**
- **`--model` flag at call sites:** would require changing the call site in `lib/process.sh:90` and `run-ralph.sh:238` to read a phase-specific variable. Couples phase identity to the shared launcher; harder to grep "what model does the verify phase use" — answer would be split across two files.
- **Global `settings.json` model key:** process-global, no per-phase granularity. Defeats the entire point of routing different phases to different models.

#### Decision 2: Verify-phase = Sonnet, not Haiku
**Chose:** Sonnet as the verify-phase default.

**Why:** The Architect's pushback (recorded during plan-writing): verify must interpret failing stack traces and build errors. The failure mode of Haiku-on-verify is misclassifying a real bug as a transient flake — exactly the worst-case outcome of the entire downshifting effort. Sonnet is the conservative floor.

**Alternatives rejected:**
- **Haiku:** my initial recommendation. Architect overruled with a concrete failure-mode argument. If post-deployment data shows Sonnet is overkill for verify, A/B Haiku in a follow-up — but Sonnet is the right starting position.

#### Decision 3: Mockup-phase = Sonnet, not Haiku
**Chose:** Sonnet as the mockup-phase default.

**Why:** Mockup fidelity is multi-file diff reasoning (HTML mockup vs. source). No published Anthropic benchmark exists for Haiku on this task profile. Conservative default reduces risk. A/B Haiku in a follow-up once Sonnet baseline is established.

**Alternatives rejected:**
- **Haiku:** plausible on theoretical grounds (pattern matching) but unverified for this specific task.

#### Decision 4: Explicit `CLAUDE_CODE_SUBAGENT_MODEL` per phase
**Chose:** Each phase exports both `ANTHROPIC_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL`.

**Why:** Anthropic docs ([model-config](https://code.claude.com/docs/en/model-config)) confirm sub-agents do NOT inherit the parent's `--model` selection — they use the dedicated `CLAUDE_CODE_SUBAGENT_MODEL` env var. Without this, Ralph's research sub-agents and Plan's critique sub-agents would silently stay on whatever default applies (likely the user's session model — Opus for this user), leaking most of the cost savings. This is the single highest-risk implementation detail in the plan.

**Caveat:** Subagent frontmatter `model:` field (per [sub-agents docs](https://code.claude.com/docs/en/sub-agents)) overrides `CLAUDE_CODE_SUBAGENT_MODEL`. The post-automation audit step lists `agents/project-scanner.md` (pinned to opus) as one to verify.

**Alternatives rejected:**
- **Rely on inheritance:** would silently leak savings. Not viable.

#### Decision 5: `--bare` adoption gated on Task 5 audit
**Chose:** Audit phase prompts (Task 5) before adopting `--bare` (Task 6). Skip Task 6 if any prompt is found to depend on CLAUDE.md auto-loaded conventions.

**Why:** `--bare` skips MCP / hooks / CLAUDE.md auto-discovery ([headless docs](https://code.claude.com/docs/en/headless)). Anthropic markets it as recommended for scripted calls. But this repo's `CLAUDE.md` establishes conventions (skill path prefixes, banned phrases, brand voice file location) — if any phase prompt assumes these are loaded, `--bare` regresses behavior. Cheap audit eliminates the unknown.

**Alternatives rejected:**
- **Adopt `--bare` unconditionally:** would create a silent behavior regression if any phase prompt relies on auto-loaded conventions.
- **Skip `--bare` entirely:** abandons the secondary token-spend reduction. The audit is cheap; do it.

#### Decision 6: Hybrid static-parse + behavioral test (env AND argv capture)
**Chose:** Static-parse tests (`test_autopilot_model_selection.py`) for each env-var export and the `--bare` flag presence, plus a behavioral test (`test_autopilot_model_env_propagation.py`) using a stub `claude` binary that records BOTH its env (to verify `ANTHROPIC_MODEL` propagation) AND its argv (to verify `--bare` actually reaches the subprocess).

**Why:** Static-parse catches the "forgot to add the export line" regression cheaply. But it cannot prove the env actually reaches `claude -p`'s process — a subtle bug (export in the wrong scope, or after the launcher invocation) would slip through. The behavioral test with a stub `claude` proves end-to-end propagation without requiring a real Claude binary or API call. Initial draft captured env only, which would not have caught a `--bare` flag dropped between `lib/process.sh` and the subprocess; the dual-capture form fixes that.

**Behavioral coverage scope:** Three phase scripts are tested behaviorally (`plan.sh`, `mockup.sh`, `verify.sh`). `run-ralph.sh` is NOT — it expects two required positional args (`worktree-path`, `plan-file-path`) and runs an inner loop that drains a real plan file. Stubbing the entire loop infrastructure for a single env-propagation check would dwarf the test it produces. The static-parse test in Task 4 plus the shared-launcher behavioral test (via `lib/process.sh`, exercised by the three phase scripts) provides sufficient coverage. If a future regression specifically targets `run-ralph.sh`'s env propagation, add a dedicated test then.

**Alternatives rejected:**
- **Pure static-parse:** insufficient — would miss scope/ordering bugs.
- **Full integration test with real claude:** breaks in CI environments without API credentials; flaky under network conditions; expensive.

#### Decision 7: `autopilot.sh` does not need new `export` lines
**Chose:** Do not extend the `export` statements in `autopilot.sh` at lines 188, 307, 315 (which the original design doc listed as files to modify).

**Why:** On second look, this is unnecessary. When a user runs `PLAN_MODEL=opus ./autopilot.sh`, the env var is automatically in autopilot.sh's environment and is inherited by child processes (phase scripts) without explicit re-export. The existing `export` lines in autopilot.sh re-export *locally-assigned* defaults (like `PHASE_TIMEOUT="${PHASE_TIMEOUT:-3600}"`). Since phase scripts define their own defaults for the new vars, autopilot.sh doesn't need to know about them at all. The only autopilot.sh change is the header comment update in Task 8 (documentation, not behavior).

**Alternatives rejected:**
- **Extend the `export` lines:** would add code with no behavioral effect. YAGNI.

---

## References

- Anthropic — [Claude Code model configuration](https://code.claude.com/docs/en/model-config)
- Anthropic — [Run Claude Code programmatically (headless)](https://code.claude.com/docs/en/headless)
- Anthropic — [Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- Anthropic — [Use the Claude Agent SDK with your Claude plan](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)
- Design doc: `docs/plans/2026-05-14-autopilot-model-downshift-design.md`
