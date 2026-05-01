# Autopilot Orchestration Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Restructure the Ralph autopilot pipeline so plans declare their environment requirements via a YAML manifest, the bash orchestrator decomposes into typed phase scripts with shared libs, and any phase halts cleanly with a structured reason instead of crashing when the executor cannot proceed unattended.

**Source Design Doc:** `docs/plans/2026-04-30-autopilot-orchestration-redesign.md`

**Mockups:** N/A

**Architecture:** Three coordinated changes plus an enforcement add-on. (1) Decompose `autopilot.sh` (642 lines) into typed phase scripts under `docs/ralph_loops/phases/` with shared libs at `docs/ralph_loops/lib/process.sh`, `lib/halt.sh`, `lib/manifest.sh`, `lib/stages.sh`. (2) Add narrow YAML front-matter to plans declaring `mcp-tools-required` and `env-vars-required`; a new preflight phase validates against the executor environment. (3) Introduce `.autopilot-halt` sentinel with a structured reason taxonomy so any phase can halt cleanly with actionable user-facing details — halts are not failures. (4) writing-plans contract gains an explicit ban on mid-flow human-review tasks, enforced by the Verifier critic.

**Tech Stack:** Bash with `set -u` standardized, Markdown plans with YAML front-matter, Python pytest for static-parse tests + bash-function-level unit tests via subprocess (allowed at function boundary; no orchestrator subprocess testing).

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] Confirm `python3` with the `pyyaml` module is available on the executor host. `lib/manifest.sh` (Task 16) calls `python3 -c 'import sys, yaml; ...'` to parse plan front-matter. On macOS / most Linux distros, install via `pip3 install pyyaml` or `python3 -m pip install pyyaml` if missing. (Aligned-plugin repos already have `pyyaml` via `pytest`'s test-only deps; confirm before relying on that — `python3 -c 'import yaml'` must exit 0.)

---

## Sequencing notes

**Tasks 5, 7, 8, 9, 11, 12, 20 all modify `autopilot.sh`. Apply them in numerical order.** Line-number references in later tasks assume earlier tasks have committed. Use content anchors (function names, banner strings, `=== ENV-LINK BLOCK START ===`) when possible; do not rely on the line numbers in this plan after the first such commit lands.

**Tasks 13, 14, 15 all modify `skills/writing-plans/SKILL.md` or its references; apply in order** — Task 14 inserts a section anchored to a heading defined by the existing skill, and Task 15 modifies the Verifier prompt added by Task 14.

**Task 21 (`verify.sh` halt emission) requires Task 20 (`HALT_PATH` exported by orchestrator) to be applied first** — otherwise Task 21's end-to-end behavior cannot be validated because `HALT_PATH` is unset in the child shell.

---

## Tasks

### ✅ Task 1: Add `lib/process.sh` shared library (test + scaffold)

**Files:**
- Create: `e2e/tests/test_phase_contracts.py`
- Create: `docs/ralph_loops/lib/process.sh`

**Context:** Five process-management functions are defined identically in BOTH `autopilot.sh` (lines 109–168) and `run-ralph.sh` (lines 80–128): `start_heartbeat`, `stop_heartbeat`, `start_watchdog`, `stop_watchdog`, `cleanup` — ~50 lines of true duplication. Two more functions (`kill_claude`, `run_claude_phase`) live only in `autopilot.sh` (lines 116–122 and 179–211); they move to the lib too so future phase scripts can call `run_claude_phase` for `claude -p` invocations with shared timeout handling. The `handle_signal()` trap and signal-trap registration stay inline in each caller because they are caller-specific. Standardize on `set -u` only (per Decision 7 in the design doc).

**Heartbeat signature change:** The shared `start_heartbeat()` from `lib/process.sh` requires two args (`timeout`, `label`); `run-ralph.sh` currently calls `start_heartbeat` with zero args (line 165). Task 2 updates that call site. Defaults are intentionally NOT added to the lib — explicit args force the caller to acknowledge the heartbeat label that appears in user-facing output.

**Step 1: Write the failing test**

Create `e2e/tests/test_phase_contracts.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_phase_contracts.py -v`
Expected: FAIL with `AssertionError: lib/process.sh must exist` (file not yet created).

**Step 3: Create `lib/process.sh` by extracting from `autopilot.sh`**

Create `docs/ralph_loops/lib/process.sh`. Move the function bodies of `cleanup`, `kill_claude`, `start_heartbeat`, `stop_heartbeat`, `start_watchdog`, `stop_watchdog`, `run_claude_phase` verbatim from `autopilot.sh` lines 109–211. Wrap in a guard against double-sourcing:

```bash
#!/usr/bin/env bash
# lib/process.sh — shared process management for autopilot.sh and run-ralph.sh.
# Sourced by both. Provides heartbeat, watchdog, cleanup, run_claude_phase.

# Idempotent source guard
if [ -n "${_AUTOPILOT_PROCESS_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_PROCESS_SH_LOADED=1

set -u
# Note: NOT using set -e. Sourced libs inherit caller flags; we use explicit
# exit-code checks throughout (Decision 7 in the autopilot redesign).

# Callers must declare these globals before sourcing:
#   PROMPT_FILE, CLAUDE_PID, WATCHDOG_PID, HEARTBEAT_PID, LOG
# Initialise to "" if unset.
: "${PROMPT_FILE:=}"
: "${CLAUDE_PID:=}"
: "${WATCHDOG_PID:=}"
: "${HEARTBEAT_PID:=}"
: "${LOG:=}"

cleanup() {
  [ -n "$PROMPT_FILE" ] && rm -f "$PROMPT_FILE"
  stop_heartbeat
  stop_watchdog
  kill_claude
}

kill_claude() {
  if [ -n "$CLAUDE_PID" ]; then
    kill "$CLAUDE_PID" 2>/dev/null || true
    wait "$CLAUDE_PID" 2>/dev/null || true
    CLAUDE_PID=""
  fi
}

start_heartbeat() {
  local timeout="$1"
  local label="$2"
  (
    elapsed=0
    while true; do
      sleep 30
      elapsed=$((elapsed + 30))
      remaining=$((timeout - elapsed))
      if [ "$remaining" -lt 0 ]; then remaining=0; fi
      rem_min=$((remaining / 60))
      rem_sec=$((remaining % 60))
      printf "  [heartbeat] %s — %ds elapsed (%dm%02ds remaining)\n" "$label" "$elapsed" "$rem_min" "$rem_sec"
    done
  ) &
  HEARTBEAT_PID=$!
}

stop_heartbeat() {
  if [ -n "$HEARTBEAT_PID" ]; then
    kill "$HEARTBEAT_PID" 2>/dev/null || true
    wait "$HEARTBEAT_PID" 2>/dev/null || true
    HEARTBEAT_PID=""
  fi
}

start_watchdog() {
  local timeout="$1"
  local phase="$2"
  (
    sleep "$timeout"
    echo ""
    echo "  [timeout] $phase exceeded ${timeout}s — killing claude" >&2
    kill "$CLAUDE_PID" 2>/dev/null || true
  ) &
  WATCHDOG_PID=$!
}

stop_watchdog() {
  if [ -n "$WATCHDOG_PID" ]; then
    kill "$WATCHDOG_PID" 2>/dev/null || true
    wait "$WATCHDOG_PID" 2>/dev/null || true
    WATCHDOG_PID=""
  fi
}

# run_claude_phase <phase-name> <timeout-seconds>
# Reads prompt from $PROMPT_FILE. Sets CLAUDE_EXIT_CODE.
run_claude_phase() {
  local phase="$1"
  local timeout="$2"

  claude -p - < "$PROMPT_FILE" &
  CLAUDE_PID=$!

  start_watchdog "$timeout" "$phase"

  CLAUDE_EXIT_CODE=0
  if ! wait "$CLAUDE_PID" 2>/dev/null; then
    CLAUDE_EXIT_CODE=$?
  fi
  CLAUDE_PID=""

  stop_watchdog

  if [ "$CLAUDE_EXIT_CODE" -eq 143 ] || [ "$CLAUDE_EXIT_CODE" -eq 137 ]; then
    echo ""
    echo "ERROR: $phase timed out after ${timeout}s." >&2
    return 1
  elif [ "$CLAUDE_EXIT_CODE" -ne 0 ]; then
    echo ""
    echo "ERROR: $phase failed (claude -p exited with code $CLAUDE_EXIT_CODE)." >&2
    [ -n "$LOG" ] && echo "Check the log at $LOG for details." >&2
    return 1
  fi

  return 0
}
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_phase_contracts.py -v`
Expected: PASS (both tests).

**Step 5: Commit**

```bash
git add docs/ralph_loops/lib/process.sh e2e/tests/test_phase_contracts.py
git commit -m "feat(autopilot): extract shared process.sh lib for heartbeat/watchdog/cleanup"
```

---

### ✅ Task 2: Refactor `run-ralph.sh` to source `lib/process.sh` and switch to `set -u`

**Files:**
- Modify: `docs/ralph_loops/run-ralph.sh` (process management block + `set` flag on line 2)
- Modify: `e2e/tests/test_ralph_sentinels.py` (add source assertion)
- Modify: `e2e/tests/test_phase_contracts.py` (add caller assertions)

**Context:** Currently `run-ralph.sh:2` uses `set -euo pipefail` and re-defines `start_heartbeat/stop_heartbeat/start_watchdog/stop_watchdog/cleanup` (lines 80–128). After this task, `run-ralph.sh` sources `lib/process.sh` and uses `set -u` only. This is a **behavioral change** to `run-ralph.sh` (flag set), called out in design Decision 7.

> **Behavior change:** `run-ralph.sh` no longer aborts on the first non-zero exit (`set -e` removed). All existing exit-code checks in the file already use explicit handling (`EXIT_CODE=0; ... || EXIT_CODE=$?`), so semantics are unchanged for the documented paths. Test assertions added in this task pin the new flag.

**Step 1: Write the failing tests**

Append to `e2e/tests/test_ralph_sentinels.py`:

```python
def test_run_ralph_sources_lib_process():
    text = _read()
    assert 'source "$SCRIPT_DIR/lib/process.sh"' in text or \
           'source "$(dirname "$0")/lib/process.sh"' in text, \
        "run-ralph.sh must source lib/process.sh"


def test_run_ralph_uses_set_u_only():
    text = _read()
    # Decision 7: standardize on set -u across all callers
    assert "set -u" in text, "run-ralph.sh must declare 'set -u'"
    assert "set -euo pipefail" not in text, \
        "run-ralph.sh must not use 'set -euo pipefail' (Decision 7)"
```

Append to `e2e/tests/test_phase_contracts.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_ralph_sentinels.py e2e/tests/test_phase_contracts.py -v`
Expected: FAIL on the new assertions (set flag still `-euo pipefail`, lib not yet sourced, functions still defined locally).

**Step 3: Update `run-ralph.sh`**

In `docs/ralph_loops/run-ralph.sh`:
- Change line 2 from `set -euo pipefail` to `set -u`.
- After the `SCRIPT_DIR=...` block (currently around line 24), add:

```bash
# shellcheck source=lib/process.sh
source "$SCRIPT_DIR/lib/process.sh"
```

- Delete the function definitions for `start_heartbeat`, `stop_heartbeat`, `start_watchdog`, `stop_watchdog`, `cleanup` (lines 80–128 in the original). Keep the variable initialisations (`HEARTBEAT_PID=""`, etc.) — `lib/process.sh` checks for these.
- Keep `handle_signal()` and the `trap` calls inline (script-specific).
- **Fix the `start_heartbeat` call site** (currently `start_heartbeat` with no args, ~line 165). Update to:

  ```bash
  start_heartbeat "$ITERATION_TIMEOUT" "iteration $ITERATION"
  ```

  This passes the iteration's timeout and a label. Without these args, `start_heartbeat` runs under `set -u` and aborts on the unbound `$1`/`$2` references.

> **Behavior change:** The heartbeat output format changes from `[heartbeat] iteration N — Xs elapsed` to `[heartbeat] iteration N — Xs elapsed (XmYs remaining)`. The `(remaining)` suffix is the lib's format and is more informative; existing log scrapers parsing the old format must be updated. None are known in this repo (Grep `\[heartbeat\]` returns only `autopilot.sh` and `run-ralph.sh` themselves).

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_ralph_sentinels.py e2e/tests/test_phase_contracts.py -v`
Expected: PASS (all tests, including the existing `test_startup_cleanup_removes_both_sentinels` and `test_done_path_unchanged`).

**Step 5: Commit**

```bash
git add docs/ralph_loops/run-ralph.sh e2e/tests/test_ralph_sentinels.py e2e/tests/test_phase_contracts.py
git commit -m "refactor(autopilot): run-ralph.sh sources lib/process.sh; standardize set -u"
```

---

### ✅ Task 3: Refactor `autopilot.sh` to source `lib/process.sh`

**Files:**
- Modify: `docs/ralph_loops/autopilot.sh` (process management block, lines 102–211)
- Modify: `e2e/tests/test_phase_contracts.py` (add caller assertions)

**Context:** Mirror Task 2 for `autopilot.sh`. Current flag is `set -uo pipefail` (line 2) — change to `set -u`. Remove the duplicate function definitions; source `lib/process.sh` instead.

**Step 1: Write the failing tests**

Append to `e2e/tests/test_phase_contracts.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_phase_contracts.py -v`
Expected: FAIL on the three new assertions.

**Step 3: Update `autopilot.sh`**

- Change line 2 from `set -uo pipefail` to `set -u`.
- After the `PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"` line (~line 40), add:

```bash
# shellcheck source=lib/process.sh
source "$SCRIPT_DIR/lib/process.sh"
```

- Delete the function definitions for `cleanup`, `kill_claude`, `start_heartbeat`, `stop_heartbeat`, `start_watchdog`, `stop_watchdog`, `run_claude_phase` (lines 109–211 in the original). Keep the variable initialisations (`PROMPT_FILE=""`, `CLAUDE_PID=""`, etc.) and the `handle_signal()` + `trap` calls inline.

**Step 4: Run all autopilot tests to verify**

Run: `pytest e2e/tests/test_phase_contracts.py e2e/tests/test_ralph_sentinels.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/autopilot.sh e2e/tests/test_phase_contracts.py
git commit -m "refactor(autopilot): autopilot.sh sources lib/process.sh; standardize set -u"
```

---

### ✅ Task 4: Add `lib/stages.sh` reporter

**Files:**
- Create: `docs/ralph_loops/lib/stages.sh`
- Modify: `e2e/tests/test_phase_contracts.py`

**Context:** Replace ad-hoc `=== Phase N: ... ===` banners (autopilot.sh lines 243, 257, 319, 429, 472, 561) with a single `report_stage <phase-num> <total> <name> <status>` function, providing one source of truth for pipeline progress.

**Step 1: Write the failing test**

Append to `e2e/tests/test_phase_contracts.py`:

```python
def test_lib_stages_exists_with_report_stage():
    stages = LIB_DIR / "stages.sh"
    assert stages.is_file(), "lib/stages.sh must exist"
    text = _read(stages)
    assert "report_stage()" in text, "lib/stages.sh must define report_stage()"
    # Must accept four positional args (phase, total, name, status)
    assert "$1" in text and "$2" in text and "$3" in text and "$4" in text, \
        "report_stage must accept phase/total/name/status positional args"
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_phase_contracts.py::test_lib_stages_exists_with_report_stage -v`
Expected: FAIL — file does not exist.

**Step 3: Create `lib/stages.sh`**

```bash
#!/usr/bin/env bash
# lib/stages.sh — single source of truth for pipeline stage reporting.
# Usage: report_stage <phase-num> <total> <phase-name> <status>
#   status: running | passed | halted | skipped | failed

if [ -n "${_AUTOPILOT_STAGES_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_STAGES_SH_LOADED=1

set -u

report_stage() {
  local phase="$1"
  local total="$2"
  local name="$3"
  local status="$4"

  local glyph
  case "$status" in
    running)  glyph="▶" ;;
    passed)   glyph="✓" ;;
    halted)   glyph="✗" ;;
    skipped)  glyph="—" ;;
    failed)   glyph="✗" ;;
    *)        glyph="?" ;;
  esac

  printf "%s phase %s of %s: %-12s | %s\n" "$glyph" "$phase" "$total" "$name" "$status"
}
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_phase_contracts.py::test_lib_stages_exists_with_report_stage -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/lib/stages.sh e2e/tests/test_phase_contracts.py
git commit -m "feat(autopilot): add lib/stages.sh report_stage reporter"
```

---

### ✅ Task 5: Wire `lib/stages.sh` into `autopilot.sh` and fix `^### ` task-completion regex

**Files:**
- Modify: `docs/ralph_loops/autopilot.sh` (banners at lines ~243, 257, 319, 429, 472, 561; matchers at 434–436)
- Modify: `e2e/tests/test_phase_contracts.py`

**Context:** Two related cleanups bundled into one commit because both touch the same file. (1) Replace `=== Phase N: ===` banners with `report_stage`. (2) Replace coarse `^### ` matcher (matches any heading, including `### Notes`) with `^### (✅|🔄)?[[:space:]]*Task[[:space:]]*[0-9]` to match only task headings — pattern derived from the `### Task N:` convention in EXECUTE-PLAN.md.

> **Behavior change:** Stage banner format changes from `=== Phase 3: Ralph Loop ===` to `▶ phase 3 of 6: ralph        | running` then `✓ phase 3 of 6: ralph        | passed`. Any external log scrapers parsing the old `===` banners must be updated; none are known to exist in this repo (grep `===.*Phase` returns only `autopilot.sh` itself).

**Step 1: Write the failing tests**

Append to `e2e/tests/test_phase_contracts.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_phase_contracts.py -v -k "report_stage or strict_task"`
Expected: FAIL.

**Step 3: Update `autopilot.sh`**

Add `source "$SCRIPT_DIR/lib/stages.sh"` after the `lib/process.sh` source line.

Replace each `=== Phase N: ... ===` echo with `report_stage N 6 <name> running` at the start of the phase, and `report_stage N 6 <name> passed` (or `skipped`) at the end. The phases and totals are:

| Phase | Total | Name |
|---|---|---|
| 1 | 6 | preflight (added in Task 19) |
| 2 | 6 | plan |
| 3 | 6 | worktree |
| 4 | 6 | ralph |
| 5 | 6 | mockup |
| 6 | 6 | verify |

Until Task 19 wires up preflight, leave the totals as `6` and skip phase 1 (it'll exist but be a no-op).

Replace lines 434–436's task-counting block:

```bash
# Was:
#   if grep -q "^### " "$PLAN_IN_WORKTREE" 2>/dev/null; then
#     TOTAL_TASKS="$(grep -c "^### " "$PLAN_IN_WORKTREE" || true)"
#     DONE_TASKS="$(grep -c "^### ✅" "$PLAN_IN_WORKTREE" || true)"
#   fi
TASK_REGEX='^### (✅|🔄)?[[:space:]]*Task[[:space:]]*[0-9]'
DONE_REGEX='^### ✅[[:space:]]*Task[[:space:]]*[0-9]'
if grep -qE "$TASK_REGEX" "$PLAN_IN_WORKTREE" 2>/dev/null; then
  TOTAL_TASKS="$(grep -cE "$TASK_REGEX" "$PLAN_IN_WORKTREE" || true)"
  DONE_TASKS="$(grep -cE "$DONE_REGEX" "$PLAN_IN_WORKTREE" || true)"
fi
```

**Step 4: Run tests to verify**

Run: `pytest e2e/tests/test_phase_contracts.py e2e/tests/test_ralph_sentinels.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/autopilot.sh e2e/tests/test_phase_contracts.py
git commit -m "refactor(autopilot): use report_stage; strict task-heading regex"
```

---

### ✅ Task 6: Add phase script template and contract assertion

**Files:**
- Create: `docs/ralph_loops/phases/_TEMPLATE.sh`
- Modify: `e2e/tests/test_phase_contracts.py`

**Context:** Each `phases/*.sh` declares a typed contract in its header (`# PHASE:`, `# INPUTS:`, `# OUTPUTS:`, `# EXIT CODES:`). Define a single template + a static-parse test that walks every `phases/*.sh` and asserts the header structure. Tasks 8–11 will create real phases that conform.

**Step 1: Write the failing test**

Append to `e2e/tests/test_phase_contracts.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_phase_contracts.py::test_phase_template_declares_contract -v`
Expected: FAIL — directory does not exist.

**Step 3: Create the template**

Create `docs/ralph_loops/phases/_TEMPLATE.sh`:

```bash
#!/usr/bin/env bash
# PHASE: <phase-name>
# INPUTS:
#   PROJECT (env var, absolute path) — main repo path
#   PLAN_FILE (env var, absolute path) — plan path on main
# OUTPUTS:
#   <sentinels written, files created>
# EXIT CODES:
#   0 — phase passed, autopilot may proceed
#   2 — halt-with-reason; .autopilot-halt has structured details
#   3 — skip (phase not applicable for this run)

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=../lib/process.sh
source "$RALPH_DIR/lib/process.sh"

# Phase logic goes here. Each phase MUST exit with one of {0, 2, 3}; any
# other exit code is treated by the orchestrator as a crash and a halt
# sentinel is written with reason=phase_crashed.

exit 0
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_phase_contracts.py::test_phase_template_declares_contract -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/phases/_TEMPLATE.sh e2e/tests/test_phase_contracts.py
git commit -m "feat(autopilot): add phases/_TEMPLATE.sh contract template"
```

---

### ✅ Task 7: Extract `phases/plan.sh` from `autopilot.sh`

**Files:**
- Create: `docs/ralph_loops/phases/plan.sh`
- Modify: `docs/ralph_loops/autopilot.sh` (Phase 1 block, lines 222–300)
- Modify: `e2e/tests/test_phase_contracts.py`

**Context:** The current Phase 1 block in `autopilot.sh` (writes the plan via `claude -p` with `WRITE-PLAN.md`) becomes `phases/plan.sh`. The orchestrator invokes it as a subprocess and routes on its exit code per the phase contract.

> **Behavior change:** Plan writing now runs in a child shell. Environment variables exported by autopilot (`PROJECT`, `DESIGN_DOC`, `SENTINEL`, `LOG`, `PHASE_TIMEOUT`) must be exported (not just set) for the child to inherit them. Each task that extracts a phase will export these in `autopilot.sh` before invoking the phase.

**Step 1: Write the failing test**

Append to `e2e/tests/test_phase_contracts.py`:

```python
def test_phase_plan_exists_and_conforms():
    plan = PHASES_DIR / "plan.sh"
    assert plan.is_file(), "phases/plan.sh must exist"
    text = _read(plan)
    for field in PHASE_HEADER_FIELDS:
        assert field in text, f"phases/plan.sh missing header field: {field}"
    assert "lib/process.sh" in text, "phases/plan.sh must source lib/process.sh"
    assert "WRITE-PLAN.md" in text, "phases/plan.sh must reference WRITE-PLAN.md"
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_phase_contracts.py::test_phase_plan_exists_and_conforms -v`
Expected: FAIL.

**Step 3: Create `phases/plan.sh`**

Create `docs/ralph_loops/phases/plan.sh` by extracting `autopilot.sh:222–300` (the Phase 1 block). Key differences from the inline version:

```bash
#!/usr/bin/env bash
# PHASE: plan
# INPUTS:
#   PROJECT (env var)         — main repo path
#   DESIGN_DOC (env var)      — design doc absolute path
#   SENTINEL (env var)        — .autopilot-plan-path absolute path
#   LOG (env var)             — log file path
#   PHASE_TIMEOUT (env var)   — timeout seconds
#   WRITE_PLAN_PROMPT, SKILL_FILE, CHECKLIST_FILE, KANBAN_FORMAT (env vars)
# OUTPUTS:
#   Plan committed to main; SENTINEL written with design-doc + plan-path
# EXIT CODES:
#   0 — plan written; PLAN_FILE readable from sentinel
#   1 — claude -p failed or sentinel missing
#   3 — plan already exists for THIS design doc (sentinel match)

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=../lib/process.sh
source "$RALPH_DIR/lib/process.sh"

# Move the sentinel-check + claude invocation logic verbatim from autopilot.sh
# lines 226-300, replacing exit 0/1 to match the contract above.
# ...
```

In `autopilot.sh`, replace the Phase 1 block (lines 222–300) with:

```bash
export PROJECT DESIGN_DOC SENTINEL LOG PHASE_TIMEOUT WRITE_PLAN_PROMPT SKILL_FILE CHECKLIST_FILE KANBAN_FORMAT

report_stage 2 6 plan running
PLAN_PHASE_EXIT=0
bash "$SCRIPT_DIR/phases/plan.sh" || PLAN_PHASE_EXIT=$?
case "$PLAN_PHASE_EXIT" in
  0) report_stage 2 6 plan passed ;;
  3) report_stage 2 6 plan skipped ;;
  *) report_stage 2 6 plan failed; exit "$PLAN_PHASE_EXIT" ;;
esac

# Re-read PLAN_FILE from sentinel (phase wrote it)
if [ -f "$SENTINEL" ]; then
  PLAN_FILE="$(tail -1 "$SENTINEL")"
fi
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_phase_contracts.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/phases/plan.sh docs/ralph_loops/autopilot.sh e2e/tests/test_phase_contracts.py
git commit -m "refactor(autopilot): extract Phase 1 (plan) into phases/plan.sh"
```

---

### ✅ Task 8: Extract `phases/worktree.sh` from `autopilot.sh`

**Files:**
- Create: `docs/ralph_loops/phases/worktree.sh`
- Modify: `docs/ralph_loops/autopilot.sh` (Phase 2 block, lines 302–423)
- Modify: `e2e/tests/test_phase_contracts.py`

**Context:** The Phase 2 block (worktree creation + npm install + env-link mirroring + `git merge main`) becomes `phases/worktree.sh`. The env-link block (lines 365–392, between `=== ENV-LINK BLOCK START ===` and `=== ENV-LINK BLOCK END ===`) moves verbatim.

`worktree.sh` cannot use the orchestrator's stdout-capture pattern that an early draft considered, because diagnostic output (`echo "Linked $envfile..."`, etc.) would corrupt the captured value. Instead: the orchestrator computes `WORKTREE_DIR` deterministically (it already does — `autopilot.sh:317`) and exports it; `worktree.sh` reads `WORKTREE_DIR` from env and creates that directory. No stdout capture is required.

`worktree.sh` also gains a structured halt: when `git merge main` fails because main has uncommitted changes (which would manifest as a merge-conflict-like exit), emit halt-with-reason `uncommitted_main` instead of returning bare exit code 1.

> **Note (per design's deferred LOW item):** The env-link block is moved as-is; do not refactor its `find … -print0` walk. The block is recently shipped (commit 675315d) and any restructuring risks regressing the per-app symlink mirroring case it solves.

**Step 1: Write the failing test**

Append to `e2e/tests/test_phase_contracts.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_phase_contracts.py::test_phase_worktree_exists_and_conforms -v`
Expected: FAIL.

**Step 3: Create `phases/worktree.sh`**

Extract `autopilot.sh:302–423` to `phases/worktree.sh` with header contract. Inputs: `PROJECT, BRANCH, PLAN_FILE, WORKTREE_DIR` (env vars). Outputs: worktree directory created at `$WORKTREE_DIR`, `git merge main` performed. Exit codes: 0 = success, 2 = halt-with-reason `uncommitted_main` (merge conflict detected from clean working-tree assumption violated), 1 = other failure (worktree creation failed). The env-link block (lines 365–392) moves verbatim. The merge-conflict handling (lines 395–408) is replaced with a halt-emit:

```bash
# In phases/worktree.sh, after the merge attempt:
if [ "$MERGE_EXIT" -ne 0 ]; then
  if git -C "$WORKTREE_DIR" rev-parse MERGE_HEAD &>/dev/null 2>&1; then
    git -C "$WORKTREE_DIR" merge --abort 2>/dev/null || true
    HALT_PATH="$PROJECT/.autopilot-halt" \
      write_halt uncommitted_main worktree "git merge main aborted; resolve in $WORKTREE_DIR"
    exit 2
  fi
fi
```

Source `lib/halt.sh` at the top alongside `lib/process.sh`.

In `autopilot.sh`, replace the Phase 2 block with the `run_phase` invocation pattern (defined in Task 20). Until then, use this transitional shape:

```bash
export PROJECT BRANCH PLAN_FILE
WORKTREE_DIR="$PROJECT/.worktrees/$(echo "$BRANCH" | sed 's|^feature/||')"
export WORKTREE_DIR
report_stage 3 6 worktree running
WORKTREE_PHASE_EXIT=0
bash "$SCRIPT_DIR/phases/worktree.sh" || WORKTREE_PHASE_EXIT=$?
if [ "$WORKTREE_PHASE_EXIT" -ne 0 ]; then
  report_stage 3 6 worktree failed
  exit "$WORKTREE_PHASE_EXIT"
fi
report_stage 3 6 worktree passed
WORKTREE="$WORKTREE_DIR"
STATUS="$WORKTREE/.finish-status"
PLAN_IN_WORKTREE="$WORKTREE/docs/plans/$(basename "$PLAN_FILE")"
```

The orchestrator now computes `WORKTREE_DIR` deterministically (it already did at autopilot.sh:317; the value is now explicitly exported). `phases/worktree.sh` reads `$WORKTREE_DIR` from env and never touches stdout for value-passing — diagnostic prints stay normal.

**Step 4: Run tests to verify**

Run: `pytest e2e/tests/test_phase_contracts.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/phases/worktree.sh docs/ralph_loops/autopilot.sh e2e/tests/test_phase_contracts.py
git commit -m "refactor(autopilot): extract Phase 2 (worktree) into phases/worktree.sh"
```

---

### ✅ Task 9: Extract `phases/mockup.sh` and `phases/verify.sh` from `autopilot.sh`

**Files:**
- Create: `docs/ralph_loops/phases/mockup.sh`
- Create: `docs/ralph_loops/phases/verify.sh`
- Modify: `docs/ralph_loops/autopilot.sh` (Phase 3.5 block lines ~468–542; Phase 4 block lines ~544–599)
- Modify: `e2e/tests/test_phase_contracts.py`

**Context:** Final two extractions for Epic A. Phase 3.5 (mockup fidelity loop) and Phase 4 (verification) move to phases/. Both invoke `claude -p` and use `run_claude_phase` from `lib/process.sh`.

**Step 1: Write the failing tests**

Append to `e2e/tests/test_phase_contracts.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_phase_contracts.py -v -k "phase_mockup or phase_verify"`
Expected: FAIL.

**Step 3: Create the two phase scripts**

Move `autopilot.sh:472–542` to `phases/mockup.sh` and `autopilot.sh:548–599` to `phases/verify.sh`, each with the contract header. Both source `lib/process.sh`. Exit codes:
- `mockup.sh`: 0 = clean OR no mockups, 1 = max iterations exceeded with deviations remaining (warning only — do not exit 1 to autopilot since it's not a halt; print warning, exit 0).
- `verify.sh`: 0 = `.finish-status` `SUCCESS`, 1 = `.finish-status` `FAILED` or missing.

In `autopilot.sh`, replace both blocks with:

```bash
export WORKTREE PLAN_IN_WORKTREE MOCKUP_PROMPT MAX_MOCKUP_ITERATIONS MOCKUP_TIMEOUT
report_stage 5 6 mockup running
MOCKUP_EXIT=0
bash "$SCRIPT_DIR/phases/mockup.sh" || MOCKUP_EXIT=$?
if [ "$MOCKUP_EXIT" -eq 3 ]; then report_stage 5 6 mockup skipped
elif [ "$MOCKUP_EXIT" -eq 0 ]; then report_stage 5 6 mockup passed
else report_stage 5 6 mockup failed; exit "$MOCKUP_EXIT"
fi

export BRANCH WORKTREE PLAN_IN_WORKTREE PROJECT VERIFY_PROMPT PHASE_TIMEOUT STATUS
report_stage 6 6 verify running
VERIFY_EXIT=0
bash "$SCRIPT_DIR/phases/verify.sh" || VERIFY_EXIT=$?
if [ "$VERIFY_EXIT" -eq 0 ]; then report_stage 6 6 verify passed
else report_stage 6 6 verify failed; exit "$VERIFY_EXIT"
fi
```

**Step 4: Run all phase tests**

Run: `pytest e2e/tests/test_phase_contracts.py e2e/tests/test_ralph_sentinels.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/phases/mockup.sh docs/ralph_loops/phases/verify.sh docs/ralph_loops/autopilot.sh e2e/tests/test_phase_contracts.py
git commit -m "refactor(autopilot): extract Phases 3.5 (mockup) and 4 (verify)"
```

---

### ✅ Task 10: Resolve `FINISH-BRANCH.md` straggler reference in plugin-split-plan

**Files:**
- Modify: `docs/plans/2026-04-08-plugin-split-plan.md` (line 410)

**Context:** Per design Decision 8, `FINISH-BRANCH.md` is deleted. The Round 1 fact-check found one active reference at `docs/plans/2026-04-08-plugin-split-plan.md:410` instructing future work to update FINISH-BRANCH.md. Resolve before deletion in Task 11.

**Step 1: Read the current line**

Run: `grep -n FINISH-BRANCH /Users/ericpage/software/aligned_cc_skills/docs/plans/2026-04-08-plugin-split-plan.md`

Expected output includes line 410: ``In `aligned-works/docs/ralph_loops/FINISH-BRANCH.md`: replace any `/aligned:` references with correct new prefix.``

**Step 2: Edit the plan**

Replace line 410 with a strikethrough + note:

```markdown
~~In `aligned-works/docs/ralph_loops/FINISH-BRANCH.md`: replace any `/aligned:` references with correct new prefix.~~ *(Obsoleted: `FINISH-BRANCH.md` deleted in autopilot-orchestration-impl, see `docs/plans/2026-04-30-autopilot-orchestration-impl.md` Task 11.)*
```

**Step 3: Verify no other live references**

Run: Use Grep tool with pattern `FINISH-BRANCH` across `docs/plans/**/*.md` and `skills/**/*.md`. Expect: only design doc + this impl plan + `VERIFY-BRANCH.md:3` (acknowledged coupling note, removed in Task 13).

**Step 4: Commit**

```bash
git add docs/plans/2026-04-08-plugin-split-plan.md
git commit -m "chore: mark plugin-split-plan FINISH-BRANCH item obsolete (deletion incoming)"
```

---

### ✅ Task 11: Delete `FINISH-BRANCH.md`

**Files:**
- Delete: `docs/ralph_loops/FINISH-BRANCH.md`
- Modify: `e2e/tests/test_phase_contracts.py`

**Context:** Per design Decision 8, FINISH-BRANCH.md is a 224-line orphan. `autopilot.sh` does not reference it (lines 43–46 list only WRITE/EXECUTE/MOCKUP/VERIFY prompts). After Task 10 cleared the lone active reference, deletion is safe.

**Step 1: Write the regression test**

Append to `e2e/tests/test_phase_contracts.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_phase_contracts.py -v -k "finish_branch"`
Expected: FAIL — file still exists.

**Step 3: Delete the file**

```bash
git rm docs/ralph_loops/FINISH-BRANCH.md
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_phase_contracts.py -v -k "finish_branch"`
Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_phase_contracts.py
git commit -m "refactor(autopilot): delete orphaned FINISH-BRANCH.md"
```

---

### ✅ Task 12: Collapse `VERIFY-BRANCH.md` to thin wrapper around finishing-a-development-branch

**Files:**
- Modify: `docs/ralph_loops/VERIFY-BRANCH.md`
- Create: `e2e/tests/test_verify_branch_thin.py`

**Context:** Per design Decision 8 follow-up + Open Question 4 resolution. The triplicated verify-gate (VERIFY-BRANCH.md Steps 1–3, FINISH-BRANCH.md Steps 1–3, finishing-a-development-branch SKILL.md Steps 1–1b) collapses: FINISH-BRANCH.md is gone (Task 11), and VERIFY-BRANCH.md becomes a thin wrapper that points the agent at the canonical steps in `skills/finishing-a-development-branch/SKILL.md` Steps 1, 1a, 1b. The wrapper still scopes the agent to verify-only mode (no merge, no archive).

**Step 1: Write the failing test**

Create `e2e/tests/test_verify_branch_thin.py`:

```python
"""Verifies VERIFY-BRANCH.md was collapsed to a thin wrapper after the
verify-gate triplication was eliminated."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY = REPO_ROOT / "docs" / "ralph_loops" / "VERIFY-BRANCH.md"


def _read() -> str:
    return VERIFY.read_text(encoding="utf-8")


def test_verify_branch_is_thin():
    text = _read()
    # After collapse, the file is a wrapper — should be much shorter than
    # the pre-collapse 123 lines.
    assert len(text.splitlines()) < 60, \
        "VERIFY-BRANCH.md should be a thin wrapper (<60 lines) after Decision 8 collapse"


def test_verify_branch_delegates_to_finishing_skill():
    text = _read()
    assert "skills/finishing-a-development-branch/SKILL.md" in text, \
        "VERIFY-BRANCH.md must point at the canonical finishing skill"


def test_verify_branch_preserves_verify_only_scope():
    text = _read()
    # Must still forbid merge/cleanup/archive
    for forbid in ("Do NOT merge", "Do NOT clean up worktrees", "Do NOT archive"):
        assert forbid in text, f"VERIFY-BRANCH.md must still state: {forbid}"


def test_verify_branch_writes_finish_status():
    text = _read()
    assert ".finish-status" in text, \
        "VERIFY-BRANCH.md must still write .finish-status (autopilot reads it)"
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_verify_branch_thin.py -v`
Expected: FAIL on the line-count and delegation assertions.

**Step 3: Rewrite `VERIFY-BRANCH.md`**

Replace the entire file with:

```markdown
# Verify Branch (Pre-Review)

You are verifying a development branch after automated implementation. Run the canonical verify gate, write `.finish-status`, then exit. Do NOT merge, clean up worktrees, or archive plan documents.

**Run from:** The worktree directory (CWD should already be set).

## Parameters

Read from the lines appended below this prompt:
- **Branch:** the feature branch name
- **Worktree:** the worktree path (should match CWD)
- **Plan:** the plan file path
- **Main repo:** the main repository path

## Process

Read `skills/finishing-a-development-branch/SKILL.md` and execute exactly:
- **Step 1: Run the test suite.**
- **Step 1a: Run the build command** (if defined; skip with note otherwise).
- **Step 1b: LLM eval (if surface changed).** Apply the surface gate, scenario scoping, and per-scenario `npx promptfoo eval -c <scenario-path> --no-progress-bar` invocation as documented there.

Skip every other step in the finishing skill (deployment audit, manual-deploy gate, merge, cleanup, archival, simplification, architecture updates).

## Status File

Write `<worktree-path>/.finish-status` on every exit path:

```bash
# Success:
status: SUCCESS
branch: <feature-branch>
tests: passed
build: <passed/skipped>
eval: <passed/warned/skipped>

# Failure:
status: FAILED
branch: <feature-branch>
failed_at: <step name (tests | build | LLM eval)>
detail: <one-line error summary>
```

## Rules

- Non-interactive. No user prompts.
- Do NOT merge to any branch.
- Do NOT clean up worktrees.
- Do NOT archive plan documents.
- Do NOT run deployment audit (Step 0 in the finishing skill).
- Do NOT run code simplification scan (merge time).
- Do NOT update architecture docs (requires judgment).
- Write `.finish-status` on every exit path.
```

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_verify_branch_thin.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/VERIFY-BRANCH.md e2e/tests/test_verify_branch_thin.py
git commit -m "refactor(autopilot): VERIFY-BRANCH.md becomes thin wrapper around finishing skill"
```

---

### ✅ Task 13: Create `skills/_shared/plan-manifest-format.md` (manifest schema doc)

**Files:**
- Create: `skills/_shared/plan-manifest-format.md`
- Create: `e2e/tests/test_writing_plans_manifest_authoring.py`

**Context:** Define the YAML front-matter manifest schema in one canonical doc. writing-plans references it for authoring; `lib/manifest.sh` references it for parsing. This is Epic B's first task.

**Step 1: Write the failing test**

Create `e2e/tests/test_writing_plans_manifest_authoring.py`:

```python
"""Static-parse tests for the plan-manifest schema doc and writing-plans
authoring/critique additions."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SHARED_DIR = REPO_ROOT / "skills" / "_shared"
WRITING_PLANS = REPO_ROOT / "skills" / "writing-plans"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_manifest_format_doc_exists():
    p = SHARED_DIR / "plan-manifest-format.md"
    assert p.is_file(), "skills/_shared/plan-manifest-format.md must exist"
    text = _read(p)
    for field in ("mcp-tools-required", "env-vars-required"):
        assert field in text, f"manifest doc must specify field: {field}"
    # Must explain the .mcp.json resolution and the settings.local.json check
    assert ".mcp.json" in text
    assert "settings.local.json" in text or "permissions.allow" in text
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_writing_plans_manifest_authoring.py -v`
Expected: FAIL.

**Step 3: Create the schema doc**

Create `skills/_shared/plan-manifest-format.md`:

```markdown
# Plan Manifest Format

Plans MAY include an OPTIONAL YAML front-matter block declaring the executor environment requirements. The autopilot's preflight phase reads this manifest and halts cleanly when the environment cannot satisfy it.

## Schema

```yaml
---
mcp-tools-required:
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_snapshot
env-vars-required:
  - SUPABASE_URL
  - OPENAI_API_KEY
---
```

Both fields are arrays of strings. Both are optional; an empty list is equivalent to omitting the field. A plan with no front-matter is valid (preflight returns exit 3 = skip).

## Authoring

The `writing-plans` skill auto-generates this manifest from the plan body before the critique panel runs. The Verifier critic enforces structural coherence: every `mcp__*__*` body reference must appear in `mcp-tools-required`, and vice versa. The author does not edit the manifest by hand — it is regenerated whenever the plan body changes. (See "Manifest authoring visibility" in the design doc — manifest writes are autonomous; the user reviews the manifest by reading the committed plan, not via interactive prompt.)

## Validation (autopilot preflight)

Preflight applies these probes against the worktree environment:

**MCP tools.** For each `mcp-tools-required[i]`:
1. Extract the server prefix (e.g., `mcp__playwright__browser_navigate` → `playwright`).
2. Walk `.mcp.json` files **upward from the worktree CWD**: worktree → main repo → `$HOME/.claude/`. Build the merged server set (later levels do not override earlier). If no `.mcp.json` defines the server prefix, halt with `reason: mcp_unreachable`.
3. Read `.claude/settings.local.json` (in the worktree first, then main repo, then `$HOME/.claude/`). Concatenate the `permissions.allow` arrays. If the exact tool string is absent, halt with `reason: mcp_tool_not_allowlisted`.

**Edge cases:**
- Symlinked worktrees: resolve the worktree path with `pwd -P` before walking.
- Conflicting `.mcp.json` at different levels: first definition wins (worktree > main > home).
- Missing `permissions.allow` field: treat as empty array (every tool fails the allowlist check).
- Missing `settings.local.json`: treat as `{"permissions":{"allow":[]}}`.

**Env vars.** For each `env-vars-required[i]`, probe `[ -n "${VAR:-}" ]` against the worktree shell environment. Halt with `reason: env_var_missing` on the first unset variable. Multiple missing variables collapse into one halt sentinel listing all of them in `details:`.

## Coherence check (Verifier critic)

The writing-plans Verifier runs a deterministic structural diff:
- Every `mcp__*__*` reference in the plan body MUST appear in `mcp-tools-required`.
- Every `mcp-tools-required` entry MUST appear at least once in the plan body.
- Both directions: same rule for `env-vars-required` vs `process.env.*` / `os.environ.*` / shell `${VAR}` references.

**Scope:** the body scan SKIPS:
- Fenced code blocks (``` ``` `) with language tags `text`, `markdown`, or `yaml` (where examples shouldn't trigger detection)
- Blockquoted lines (`> ...`)
- Inline code spans (`` `...` ``) — only checked for env-var refs in surrounding prose, not the inline contents

Mismatch is flagged HIGH severity. The Verifier reports the missing entries in both directions; the author re-runs manifest generation rather than editing by hand.
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_writing_plans_manifest_authoring.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/_shared/plan-manifest-format.md e2e/tests/test_writing_plans_manifest_authoring.py
git commit -m "feat(writing-plans): add plan-manifest schema doc"
```

---

### ✅ Task 14: Add manifest-authoring step to `writing-plans/SKILL.md`

**Files:**
- Modify: `skills/writing-plans/SKILL.md`
- Modify: `e2e/tests/test_writing_plans_manifest_authoring.py`

**Context:** writing-plans must scan the plan body and prepend the YAML manifest before the critique panel runs. The section is inserted IMMEDIATELY BEFORE `## Manual Deploy Artifact Scan` (currently line 365 in `skills/writing-plans/SKILL.md`) so manifest generation happens before both the manual-deploy scan and the Fact-Check + Critique Panel — the Verifier coherence check needs the manifest already authored.

**Rationale for the anchor:** In SKILL.md document order today the sections appear as `## Verification Gate` (line ~290) → `## Manual Deploy Artifact Scan` (line 365) → `## Fact-Check + Critique Panel` (line 422) → ... `## Verification Gate` reappears around line 477 as a separate section. Inserting after either Verification Gate would place the manifest section AFTER the critique panel, defeating the coherence check. Anchoring before Manual Deploy Artifact Scan keeps the order: Verification Gate → Plan Manifest → Manual Deploy Artifact Scan → Fact-Check + Critique Panel.

**Step 1: Write the failing test**

Append to `e2e/tests/test_writing_plans_manifest_authoring.py`:

```python
def test_writing_plans_documents_manifest_authoring():
    skill = WRITING_PLANS / "SKILL.md"
    text = _read(skill)
    # Match the section heading specifically (`## Plan Manifest`), not a
    # casual mention earlier in the doc
    assert "## Plan Manifest" in text or "## Manifest Authoring" in text, \
        "writing-plans must document the manifest-authoring step"
    assert "plan-manifest-format.md" in text, \
        "writing-plans must reference _shared/plan-manifest-format.md"
    # Step must run BEFORE the manual-deploy scan AND before the critique
    # panel — so anchor on the heading positions, not a substring search
    manifest_idx = text.find("## Plan Manifest")
    if manifest_idx == -1:
        manifest_idx = text.find("## Manifest Authoring")
    deploy_idx = text.find("## Manual Deploy Artifact Scan")
    critique_idx = text.find("## Fact-Check + Critique Panel")
    assert manifest_idx >= 0
    assert deploy_idx > manifest_idx, \
        "Manifest-authoring section must precede ## Manual Deploy Artifact Scan"
    assert critique_idx > manifest_idx, \
        "Manifest-authoring section must precede ## Fact-Check + Critique Panel"
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_writing_plans_manifest_authoring.py::test_writing_plans_documents_manifest_authoring -v`
Expected: FAIL.

**Step 3: Edit `skills/writing-plans/SKILL.md`**

Insert a new section IMMEDIATELY BEFORE `## Manual Deploy Artifact Scan` (currently line 365). Use the literal heading `## Manual Deploy Artifact Scan` as the Edit `old_string` anchor; precede it with the new section + a `\n` separator. The new section content:

```markdown
## Plan Manifest (autonomous authoring)

After the plan body is drafted and verified, generate a YAML front-matter manifest declaring the executor environment requirements. Schema and validation rules: `skills/_shared/plan-manifest-format.md`.

**Procedure:**

1. Scan the plan body for `mcp__*__*` references using a regex that skips fenced code blocks (``` ``` ```) with language tags `text` / `markdown` / `yaml`, blockquotes (`> ...`), and ``inline code`` spans. Collect the unique tool strings.
2. Scan for env-var references: `process\.env\.[A-Z_][A-Z0-9_]*`, `os\.environ\[['"]([A-Z_][A-Z0-9_]*)['"]\]`, and shell `\$\{?[A-Z_][A-Z0-9_]*\}?` patterns. Same fenced-block exclusions. Collect unique names.
3. Prepend the manifest as YAML front-matter at the very top of the plan file (before the `# <Title>` heading). Format per `plan-manifest-format.md`.
4. If both lists are empty, prepend an empty front-matter block (`---\n---\n`) so preflight detects "manifest present, nothing to check" rather than "no manifest, skip preflight." (This signal is intentional — empty manifest = author confirmed no env requirements.)

**Visibility:** The manifest is written autonomously without user confirmation. The user reviews it as part of reading the committed plan. The Verifier critic catches mismatches between manifest and body.

**Idempotency:** Re-running the procedure on a plan with an existing manifest replaces it (do not append). Match the existing front-matter via `^---\n.*?\n---\n` (multiline) and substitute.

This step runs BEFORE the Manual Deploy Artifact Scan so both checks operate on a fully-authored plan.
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_writing_plans_manifest_authoring.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/writing-plans/SKILL.md e2e/tests/test_writing_plans_manifest_authoring.py
git commit -m "feat(writing-plans): add Plan Manifest authoring section"
```

---

### ✅ Task 15: Add manifest coherence check to Verifier critic prompt

**Files:**
- Modify: `skills/writing-plans/references/critique-panel-prompts.md` (Round 1 Verifier section, lines 38–69)
- Modify: `skills/writing-plans/plan-critique-checklist.md` (Criterion 10 gap-analysis table)
- Modify: `e2e/tests/test_writing_plans_manifest_authoring.py`

**Context:** The Verifier owns structural coherence between manifest and body. Adding the rule to the existing Round 1 Verifier prompt's Phase 3 (Critique) keeps the critique panel's HIGH-severity surface in one place.

**Step 1: Write the failing test**

Append to `e2e/tests/test_writing_plans_manifest_authoring.py`:

```python
def test_verifier_prompt_has_manifest_coherence_rule():
    prompts = WRITING_PLANS / "references" / "critique-panel-prompts.md"
    text = _read(prompts)
    # The rule must reference the manifest fields and the structural-diff check
    assert "mcp-tools-required" in text, \
        "Verifier prompt must reference mcp-tools-required for coherence check"
    assert "manifest" in text.lower() and "coherence" in text.lower(), \
        "Verifier prompt must describe manifest coherence check"


def test_checklist_criterion_10_has_manifest_row():
    checklist = WRITING_PLANS / "plan-critique-checklist.md"
    text = _read(checklist)
    # New row in the gap-analysis table
    assert "Manifest coherence" in text or "Plan manifest" in text, \
        "Criterion 10 table must add a manifest-coherence row"
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_writing_plans_manifest_authoring.py -v -k "verifier_prompt or criterion_10_has_manifest"`
Expected: FAIL.

**Step 3: Edit the Verifier prompt**

In `skills/writing-plans/references/critique-panel-prompts.md`, find the Round 1 Verifier prompt (line 38), specifically Phase 3. After the autonomy-violations rule sentence (currently ends at line 67's "cite task number and the exact step text."), append:

```
For checklist 10's manifest-coherence row: read the plan's YAML front-matter (between the leading `---` markers, if present). Walk the plan body, skipping fenced code blocks tagged `text`/`markdown`/`yaml`, blockquoted lines (`> ...`), and inline code spans, and extract every `mcp__*__*` reference and every env-var reference (`process.env.X`, `os.environ['X']`, shell `${X}` for uppercase X). For each manifest entry NOT in the body: HIGH severity finding "stale manifest". For each body reference NOT in the manifest: HIGH severity finding "missing manifest entry". Report both directions in one combined finding per category.
```

In `skills/writing-plans/plan-critique-checklist.md`, find the Criterion 10 table (around line 156–166). Add this row before the `Autonomy violations` row:

```markdown
| Manifest coherence | Does the plan have YAML front-matter? Does every `mcp__*__*` body reference appear in `mcp-tools-required`? Does every manifest entry appear in the body? Same for env vars. **Mismatch is HIGH severity** — see `skills/_shared/plan-manifest-format.md`. |
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_writing_plans_manifest_authoring.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/writing-plans/references/critique-panel-prompts.md skills/writing-plans/plan-critique-checklist.md e2e/tests/test_writing_plans_manifest_authoring.py
git commit -m "feat(writing-plans): Verifier critic enforces manifest coherence"
```

---

### ✅ Task 16: Add `lib/manifest.sh` (parse + validate)

**Files:**
- Create: `docs/ralph_loops/lib/manifest.sh`
- Create: `e2e/tests/test_manifest_validation.py`
- Create: `e2e/fixtures/manifest/plan_with_manifest.md` (test fixture)
- Create: `e2e/fixtures/manifest/plan_no_manifest.md` (test fixture)
- Create: `e2e/fixtures/manifest/plan_partial.md` (test fixture — interrupted YAML, per design's deferred QA H6)

**Context:** Bash library that parses YAML front-matter and validates it against the executor environment. The function-level boundary is testable via subprocess (per design Decision 5; allowed at function boundary, not orchestrator).

**Step 1: Create test fixtures**

Create `e2e/fixtures/manifest/plan_with_manifest.md`:

```markdown
---
mcp-tools-required:
  - mcp__playwright__browser_navigate
env-vars-required:
  - FAKE_TEST_VAR
---

# Test Plan
Body referencing mcp__playwright__browser_navigate and FAKE_TEST_VAR.
```

Create `e2e/fixtures/manifest/plan_no_manifest.md`:

```markdown
# Test Plan With No Front-Matter
Body has no manifest.
```

Create `e2e/fixtures/manifest/plan_partial.md` (simulates SIGKILL during plan write — incomplete YAML):

```markdown
---
mcp-tools-required:
  - mcp__playwright__browser_navigate
env-vars-required:
```

(File ends mid-list, no closing `---`.)

**Step 2: Write the failing test**

Create `e2e/tests/test_manifest_validation.py`:

```python
"""Bash-function-level tests for lib/manifest.sh — parse + validate. Subprocess
testing is allowed at function boundary (per design Decision 5)."""

from __future__ import annotations
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIB = REPO_ROOT / "docs" / "ralph_loops" / "lib" / "manifest.sh"
FIX = REPO_ROOT / "e2e" / "fixtures" / "manifest"


def _bash(cmd: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full = f'set -u; source "{LIB}"; {cmd}'
    return subprocess.run(["bash", "-c", full], capture_output=True, text=True, env=env)


def test_parse_manifest_present():
    r = _bash(f'parse_manifest "{FIX/"plan_with_manifest.md"}"')
    assert r.returncode == 0, r.stderr
    assert "mcp__playwright__browser_navigate" in r.stdout
    assert "FAKE_TEST_VAR" in r.stdout


def test_parse_manifest_absent_returns_skip():
    r = _bash(f'parse_manifest "{FIX/"plan_no_manifest.md"}"; echo "exit=$?"')
    # Convention: parse_manifest exits 3 (skip) when no front-matter
    assert "exit=3" in r.stdout, r.stdout + r.stderr


def test_parse_manifest_malformed_returns_error():
    r = _bash(f'parse_manifest "{FIX/"plan_partial.md"}"; echo "exit=$?"')
    # Partial/unparseable YAML must NOT silently skip — must error to trigger
    # halt-with-reason: manifest_malformed
    assert "exit=1" in r.stdout, r.stdout + r.stderr


def test_validate_env_var_missing():
    # FAKE_TEST_VAR is not set in the env passed
    r = _bash(
        f'parse_manifest "{FIX/"plan_with_manifest.md"}" >/dev/null; '
        f'check_env_var FAKE_TEST_VAR; echo "exit=$?"',
        env={"PATH": "/usr/bin:/bin"},
    )
    assert "exit=2" in r.stdout, r.stdout + r.stderr


def test_validate_env_var_present():
    r = _bash(
        'check_env_var FAKE_TEST_VAR; echo "exit=$?"',
        env={"PATH": "/usr/bin:/bin", "FAKE_TEST_VAR": "x"},
    )
    assert "exit=0" in r.stdout, r.stdout + r.stderr
```

**Step 3: Run test to verify it fails**

Run: `pytest e2e/tests/test_manifest_validation.py -v`
Expected: FAIL — `lib/manifest.sh` does not exist.

**Step 4: Create `lib/manifest.sh`**

```bash
#!/usr/bin/env bash
# lib/manifest.sh — parse YAML front-matter from plan files and validate
# against executor environment. See skills/_shared/plan-manifest-format.md.

if [ -n "${_AUTOPILOT_MANIFEST_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_MANIFEST_SH_LOADED=1

set -u

# Globals populated by parse_manifest. Reset on each call.
MANIFEST_MCP_TOOLS=()
MANIFEST_ENV_VARS=()

# parse_manifest <plan-file>
# Exit codes: 0 = manifest parsed, 1 = malformed, 3 = no manifest present.
# Echoes the parsed entries, one per line, prefixed with "mcp:" or "env:".
parse_manifest() {
  local plan="$1"
  MANIFEST_MCP_TOOLS=()
  MANIFEST_ENV_VARS=()

  [ -f "$plan" ] || { echo "ERROR: plan file not found: $plan" >&2; return 1; }

  # Detect front-matter: file MUST start with `---\n`, then YAML, then `\n---\n`.
  local first_line
  first_line="$(head -1 "$plan")"
  if [ "$first_line" != "---" ]; then
    return 3  # no manifest
  fi

  # Extract YAML between the two `---` markers using awk
  local yaml
  yaml="$(awk 'NR==1 && /^---$/ {flag=1; next} flag && /^---$/ {exit} flag {print}' "$plan")"

  # Detect malformed: no closing `---` means yaml read to EOF (file ended)
  # Use the line count of yaml vs the file: if file has no second '---' line, fail.
  if ! awk 'NR>1 && /^---$/ {found=1; exit} END {exit !found}' "$plan"; then
    echo "ERROR: malformed front-matter (no closing '---')" >&2
    return 1
  fi

  # Use Python (already a dev-dep via pytest) to parse YAML reliably.
  local parsed
  parsed="$(printf '%s\n' "$yaml" | python3 -c '
import sys, yaml
try:
  d = yaml.safe_load(sys.stdin) or {}
except yaml.YAMLError as e:
  print("YAML_ERROR", file=sys.stderr); sys.exit(1)
for t in (d.get("mcp-tools-required") or []):
  print(f"mcp:{t}")
for v in (d.get("env-vars-required") or []):
  print(f"env:{v}")
' 2>&1)" || { echo "ERROR: malformed YAML" >&2; return 1; }

  while IFS= read -r line; do
    case "$line" in
      mcp:*) MANIFEST_MCP_TOOLS+=("${line#mcp:}"); echo "$line" ;;
      env:*) MANIFEST_ENV_VARS+=("${line#env:}"); echo "$line" ;;
    esac
  done <<< "$parsed"

  return 0
}

# check_env_var <NAME>
# Exit 0 if set+nonempty, 2 if unset/empty.
check_env_var() {
  local var="$1"
  local val="${!var:-}"
  if [ -z "$val" ]; then
    return 2
  fi
  return 0
}

# check_mcp_tool <tool-string> [worktree-cwd]
# Walks .mcp.json upward from worktree → main repo → $HOME/.claude/.
# Exit 0 = server defined and tool allowlisted, 2 = halt (server unreachable
# or tool not allowlisted).
# Echoes one of: "ok", "mcp_unreachable", "mcp_tool_not_allowlisted"
check_mcp_tool() {
  local tool="$1"
  local cwd="${2:-$PWD}"
  local server="${tool#mcp__}"
  server="${server%%__*}"

  # Walk upward; accumulate .mcp.json paths in order
  local dir="$(cd "$cwd" && pwd -P)"
  local mcp_files=()
  while [ "$dir" != "/" ]; do
    [ -f "$dir/.mcp.json" ] && mcp_files+=("$dir/.mcp.json")
    dir="$(dirname "$dir")"
  done
  [ -f "$HOME/.claude/.mcp.json" ] && mcp_files+=("$HOME/.claude/.mcp.json")
  [ -f "$HOME/.mcp.json" ] && mcp_files+=("$HOME/.mcp.json")

  # Server check via python (jq may not be available)
  local found=0
  for f in "${mcp_files[@]+"${mcp_files[@]}"}"; do
    # Pass $f and $server via env, not string interpolation, to avoid
    # quoting hazards if a path contains apostrophes.
    if MCP_FILE="$f" MCP_SERVER="$server" python3 -c "
import json, os, sys
d = json.load(open(os.environ['MCP_FILE']))
sys.exit(0 if os.environ['MCP_SERVER'] in (d.get('mcpServers') or {}) else 1)
" 2>/dev/null; then
      found=1
      break
    fi
  done
  if [ "$found" -eq 0 ]; then
    echo "mcp_unreachable"
    return 2
  fi

  # Allowlist check: walk settings.local.json from worktree → main → $HOME/.claude
  local settings_files=()
  dir="$(cd "$cwd" && pwd -P)"
  while [ "$dir" != "/" ]; do
    [ -f "$dir/.claude/settings.local.json" ] && settings_files+=("$dir/.claude/settings.local.json")
    dir="$(dirname "$dir")"
  done
  [ -f "$HOME/.claude/settings.local.json" ] && settings_files+=("$HOME/.claude/settings.local.json")

  for f in "${settings_files[@]+"${settings_files[@]}"}"; do
    if SETTINGS_FILE="$f" MCP_TOOL="$tool" python3 -c "
import json, os
d = json.load(open(os.environ['SETTINGS_FILE']))
allow = ((d.get('permissions') or {}).get('allow') or [])
exit(0 if os.environ['MCP_TOOL'] in allow else 1)
" 2>/dev/null; then
      echo "ok"
      return 0
    fi
  done

  echo "mcp_tool_not_allowlisted"
  return 2
}
```

**Step 5: Run test to verify it passes**

Run: `pytest e2e/tests/test_manifest_validation.py -v`
Expected: PASS.

**Step 6: Commit**

```bash
git add docs/ralph_loops/lib/manifest.sh e2e/tests/test_manifest_validation.py e2e/fixtures/manifest/
git commit -m "feat(autopilot): add lib/manifest.sh for YAML parse + env validation"
```

---

### ✅ Task 17: Create `skills/_shared/autopilot-halt-format.md` (taxonomy doc)

**Files:**
- Create: `skills/_shared/autopilot-halt-format.md`
- Create: `e2e/tests/test_halt_protocol.py`

**Context:** Define the halt-with-reason taxonomy in one canonical doc — both `lib/halt.sh` and the orchestrator reference it. This is Epic C's first task.

**Step 1: Write the failing test**

Create `e2e/tests/test_halt_protocol.py`:

```python
"""Static-parse + bash-function tests for the halt protocol (lib/halt.sh
and the autopilot-halt-format.md taxonomy)."""

from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HALT_SH = REPO_ROOT / "docs" / "ralph_loops" / "lib" / "halt.sh"
HALT_DOC = REPO_ROOT / "skills" / "_shared" / "autopilot-halt-format.md"

EXPECTED_REASONS = [
    "mcp_unreachable",
    "mcp_tool_not_allowlisted",
    "env_var_missing",
    "manifest_drift",
    "manifest_malformed",
    "uncommitted_main",
    "verify_failed",
    "human_action_required",
    "phase_crashed",
]


def test_halt_format_doc_exists():
    assert HALT_DOC.is_file(), "skills/_shared/autopilot-halt-format.md must exist"


def test_halt_format_doc_lists_all_reasons():
    text = HALT_DOC.read_text(encoding="utf-8")
    for r in EXPECTED_REASONS:
        assert r in text, f"halt-format doc must list reason: {r}"
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_halt_protocol.py -v`
Expected: FAIL.

**Step 3: Create the doc**

Create `skills/_shared/autopilot-halt-format.md`:

```markdown
# Autopilot Halt Format

The autopilot pipeline halts cleanly via a `.autopilot-halt` sentinel written by any phase. The orchestrator detects the sentinel after a phase exits with code 2, prints the formatted reason, and exits 0 — halts are NOT failures.

## Sentinel format

Newline-delimited `key: value`, with `fix-instructions` as a YAML block-literal:

```
reason: <reason-id>
phase: <phase-name>
log: <absolute path to log file>
next-action: <one-line>
fix-instructions: |
  Multi-line, indent-friendly. Tells the user EXACTLY what to do.
```

Required fields: `reason`, `phase`, `log`, `next-action`. Optional: `fix-instructions` (centralized in `lib/halt.sh` keyed by reason; phase scripts pass details only).

## Write protocol

1. Phase script calls `write_halt <reason> <phase> [details]` from `lib/halt.sh`.
2. `write_halt` writes to `$HALT_PATH.tmp` then `mv` to `$HALT_PATH` (atomic; first writer wins).
3. If `$HALT_PATH` already exists, append a `secondary-halt:` block rather than overwriting — preserves evidence.
4. Phase exits with code 2.

## Lifecycle

- Written by phase script on exit-code-2.
- Read + formatted by orchestrator after each phase.
- **Deleted explicitly by the user after they apply the fix** — the orchestrator never auto-deletes a halt sentinel, even on a successful re-run. Preserving evidence outweighs auto-cleanup convenience.
- Re-running with a stale `.autopilot-halt` present surfaces the prior sentinel via `cat $HALT_PATH` and exits 0 with re-run guidance ("Resolve the issue per fix-instructions above, delete `.autopilot-halt`, then re-run."). The user must `rm .autopilot-halt` before progress can resume.

## Reason taxonomy

| Reason | Phase | Trigger |
|---|---|---|
| `mcp_unreachable` | preflight | Plan declares an MCP tool whose server is not defined in any reachable `.mcp.json` |
| `mcp_tool_not_allowlisted` | preflight | Server defined; tool string not in `permissions.allow` |
| `env_var_missing` | preflight | Plan declares an env var that is unset in the worktree env |
| `manifest_drift` | preflight | Plan body references an MCP tool not in the manifest, or vice versa |
| `manifest_malformed` | preflight | Front-matter present but unparseable / missing required fields |
| `uncommitted_main` | worktree | Main has uncommitted changes that block `git merge main` into the worktree |
| `verify_failed` | verify | Tests / build / eval failed |
| `human_action_required` | ralph (in-loop) | Existing `.ralph-human-blocked` aliases here — same protocol, unified surface |
| `phase_crashed` | any | Phase script exited unexpectedly; `details:` carries last 10 lines of stderr |

## Centralized fix-instructions (DevEx M7)

`lib/halt.sh` provides `format_halt <reason>` which echoes the canonical user-facing fix instructions for that reason. This means adding a new reason touches two surfaces (lib/halt.sh + this doc) instead of every phase script.

## Orchestrator response

When `autopilot.sh` detects `.autopilot-halt` after a phase exits with code 2:
1. Print the formatted reason to stdout (use `format_halt` output).
2. Exit 0 (NOT an error — clean halt).
3. Leave the sentinel in place so re-running surfaces "previous halt" guidance.
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_halt_protocol.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/_shared/autopilot-halt-format.md e2e/tests/test_halt_protocol.py
git commit -m "feat(autopilot): add autopilot-halt-format taxonomy doc"
```

---

### ✅ Task 18: Add `lib/halt.sh` (write/read/format)

**Files:**
- Create: `docs/ralph_loops/lib/halt.sh`
- Modify: `e2e/tests/test_halt_protocol.py`

**Context:** Bash library implementing `write_halt`, `read_halt`, `format_halt`. Tested at function boundary via subprocess.

**Step 1: Write the failing test**

Append to `e2e/tests/test_halt_protocol.py`:

```python
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
            f'write_halt env_var_missing preflight "FAKE_VAR is unset"',
            cwd=d,
        )
        assert r.returncode == 0, r.stderr
        sentinel = d / ".autopilot-halt"
        assert sentinel.is_file()
        text = sentinel.read_text()
        assert "reason: env_var_missing" in text
        assert "phase: preflight" in text


def test_write_halt_secondary_appends_not_overwrites():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        env = f'HALT_PATH="{d}/.autopilot-halt"'
        _bash(f'{env} write_halt env_var_missing preflight "first"', cwd=d)
        _bash(f'{env} write_halt mcp_unreachable preflight "second"', cwd=d)
        text = (d / ".autopilot-halt").read_text()
        assert "reason: env_var_missing" in text  # first preserved
        assert "secondary-halt:" in text  # second appended
        assert "mcp_unreachable" in text


def test_format_halt_echoes_canonical_fix():
    r = _bash('format_halt env_var_missing', cwd=Path("/tmp"))
    assert r.returncode == 0, r.stderr
    # Each canonical fix instruction must mention the reason name AND the user action
    assert "env_var_missing" in r.stdout or "env var" in r.stdout.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_halt_protocol.py -v -k "halt_sh or write_halt or format_halt"`
Expected: FAIL.

**Step 3: Create `lib/halt.sh`**

```bash
#!/usr/bin/env bash
# lib/halt.sh — structured halt sentinel write/read/format.
# Schema: skills/_shared/autopilot-halt-format.md.

if [ -n "${_AUTOPILOT_HALT_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_HALT_SH_LOADED=1

set -u

: "${HALT_PATH:=}"

# write_halt <reason> <phase> [details]
# Atomic write via mv; first writer wins. Subsequent writers append a
# secondary-halt block rather than overwriting.
write_halt() {
  local reason="$1"
  local phase="$2"
  local details="${3:-}"
  local target="${HALT_PATH:-.autopilot-halt}"
  local tmp="${target}.tmp.$$"
  local log="${LOG:-(unknown)}"

  if [ -f "$target" ]; then
    {
      echo ""
      echo "secondary-halt:"
      echo "  reason: $reason"
      echo "  phase: $phase"
      echo "  details: $details"
    } >> "$target"
    return 0
  fi

  {
    echo "reason: $reason"
    echo "phase: $phase"
    echo "log: $log"
    echo "next-action: see fix-instructions below"
    if [ -n "$details" ]; then
      echo "details: $details"
    fi
    echo "fix-instructions: |"
    format_halt "$reason" | sed 's/^/  /'
  } > "$tmp"
  mv "$tmp" "$target"
}

# read_halt [path]
# Echoes the sentinel content. Exit 0 if found, 1 otherwise.
read_halt() {
  local path="${1:-${HALT_PATH:-.autopilot-halt}}"
  [ -f "$path" ] || return 1
  cat "$path"
}

# format_halt <reason>
# Echoes the canonical fix-instructions for the reason. Add cases here when
# adding new reasons (and update skills/_shared/autopilot-halt-format.md).
format_halt() {
  local reason="$1"
  case "$reason" in
    mcp_unreachable)
      cat <<'EOF'
The plan declares an MCP tool whose server is not defined in any
.mcp.json reachable from the worktree.

Fix one of:
  1. Define the server in .mcp.json (worktree, repo root, or ~/.claude/).
  2. Remove the offending mcp__*__* reference from the plan body and
     regenerate the manifest (writing-plans does this automatically).

Then re-run autopilot.sh.
EOF
      ;;
    mcp_tool_not_allowlisted)
      cat <<'EOF'
The plan declares an MCP tool that is defined in .mcp.json but is not in
this project's .claude/settings.local.json allowlist.

Fix one of:
  1. Open a Claude session in this repo and accept the permission prompt
     once: this writes the tool to the allowlist.
  2. Remove the offending mcp__*__* reference from the plan body and
     regenerate the manifest.

Then re-run autopilot.sh.
EOF
      ;;
    env_var_missing)
      cat <<'EOF'
The plan declares an env var that is not set in the worktree environment.

Fix:
  Set the variable in your shell, in .env.local (root or per-app), or in
  the worktree's environment file. The autopilot mirrors per-app env
  symlinks from the main repo into the worktree.

Then re-run autopilot.sh.
EOF
      ;;
    manifest_drift)
      cat <<'EOF'
The plan body references an MCP tool or env var not in the manifest, or
the manifest declares a tool/var not in the body.

Fix:
  Re-run writing-plans to regenerate the manifest from the body. Do not
  hand-edit the front-matter.
EOF
      ;;
    manifest_malformed)
      cat <<'EOF'
The plan's YAML front-matter is present but unparseable.

Fix:
  Inspect the plan file: the front-matter must start with `---` on line 1
  and end with `---` on its own line. Body content follows. If the file
  was truncated (e.g., SIGKILL during plan write), re-run writing-plans
  to regenerate.
EOF
      ;;
    uncommitted_main)
      cat <<'EOF'
Main branch has uncommitted changes that would block 'git merge main'
into the worktree.

Fix:
  Commit or stash the changes on main, then re-run autopilot.sh.
EOF
      ;;
    verify_failed)
      cat <<'EOF'
Verification failed (tests, build, or LLM eval).

Fix:
  Read .finish-status in the worktree for the failure category, fix the
  underlying issue, then re-run autopilot.sh. The autopilot will resume
  from the verify phase.
EOF
      ;;
    human_action_required)
      cat <<'EOF'
The Ralph loop encountered a task that requires human action that the
loop cannot perform autonomously.

Fix:
  Read the iteration's last output for the specific blocker. After
  completing the manual step, mark the task ✅ in the plan and re-launch.
EOF
      ;;
    phase_crashed)
      cat <<'EOF'
A phase script exited unexpectedly. The autopilot wrote this halt because
no other halt was emitted before the crash.

Fix:
  Read the log for the last 10 lines of stderr (in the details: field of
  this sentinel, if captured). Fix the underlying issue, then re-run.
EOF
      ;;
    *)
      echo "Unknown halt reason: $reason"
      echo "Add a case to lib/halt.sh format_halt() and update"
      echo "skills/_shared/autopilot-halt-format.md."
      ;;
  esac
}
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_halt_protocol.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/lib/halt.sh e2e/tests/test_halt_protocol.py
git commit -m "feat(autopilot): add lib/halt.sh write/read/format protocol"
```

---

### ✅ Task 19: Add `phases/preflight.sh` (manifest validation)

**Files:**
- Create: `docs/ralph_loops/phases/preflight.sh`
- Modify: `e2e/tests/test_phase_contracts.py`
- Modify: `e2e/tests/test_manifest_validation.py`

**Context:** The preflight phase reads the plan's manifest, walks each declared MCP tool against `.mcp.json` + `permissions.allow`, probes each declared env var, and emits halt-with-reason on the first violation.

**Step 1: Write the failing tests**

Append to `e2e/tests/test_phase_contracts.py`:

```python
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
```

Append to `e2e/tests/test_manifest_validation.py`:

```python
def test_preflight_halts_on_missing_env_var():
    """End-to-end: invoke preflight against a fixture plan with an env var
    requirement that the test env does not satisfy."""
    PREFLIGHT = REPO_ROOT / "docs" / "ralph_loops" / "phases" / "preflight.sh"
    fixture = FIX / "plan_with_manifest.md"
    import os, tempfile
    with tempfile.TemporaryDirectory() as d:
        env = {"PATH": "/usr/bin:/bin", "PROJECT": d, "PLAN_FILE": str(fixture),
               "HALT_PATH": f"{d}/.autopilot-halt", "LOG": f"{d}/.log"}
        r = subprocess.run(
            ["bash", str(PREFLIGHT)], capture_output=True, text=True,
            env=env, cwd=d,
        )
        # FAKE_TEST_VAR is not set → halt with env_var_missing → exit 2
        assert r.returncode == 2, f"preflight should halt (exit 2), got {r.returncode}: {r.stderr}"
        sentinel = Path(d) / ".autopilot-halt"
        assert sentinel.is_file(), "preflight must write .autopilot-halt"
        assert "env_var_missing" in sentinel.read_text()
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_phase_contracts.py e2e/tests/test_manifest_validation.py -v`
Expected: FAIL on the new assertions.

**Step 3: Create `phases/preflight.sh`**

```bash
#!/usr/bin/env bash
# PHASE: preflight
# INPUTS:
#   PROJECT (env var)    — main repo path
#   PLAN_FILE (env var)  — plan path on main; may not exist yet on first invocation
#   HALT_PATH (env var)  — absolute path to .autopilot-halt (orchestrator sets this)
# OUTPUTS:
#   .autopilot-halt (sentinel) — written if preflight halts
# EXIT CODES:
#   0 — preflight passed (manifest valid OR no plan yet)
#   2 — halt-with-reason; .autopilot-halt has structured details
#   3 — skip (plan exists but has no manifest — backward-compat path)

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=../lib/manifest.sh
source "$RALPH_DIR/lib/manifest.sh"
# shellcheck source=../lib/halt.sh
source "$RALPH_DIR/lib/halt.sh"

# If plan doesn't exist yet (first-ever invocation), skip — phase 1.5 catches it.
if [ ! -f "${PLAN_FILE:-}" ]; then
  echo "preflight: no plan file yet; deferring manifest checks to post-plan re-run"
  exit 0
fi

# Parse manifest. parse_manifest exits: 0 = parsed, 1 = malformed, 3 = absent.
PARSE_EXIT=0
parse_manifest "$PLAN_FILE" >/dev/null || PARSE_EXIT=$?
case "$PARSE_EXIT" in
  3)
    echo "preflight: no manifest in plan — skip (backward-compat)"
    exit 3
    ;;
  1)
    write_halt manifest_malformed preflight "Front-matter present but unparseable"
    exit 2
    ;;
esac

# Validate env vars
for var in "${MANIFEST_ENV_VARS[@]+"${MANIFEST_ENV_VARS[@]}"}"; do
  if ! check_env_var "$var"; then
    write_halt env_var_missing preflight "Variable '$var' is unset or empty"
    exit 2
  fi
done

# Validate MCP tools — walk from worktree CWD upward
for tool in "${MANIFEST_MCP_TOOLS[@]+"${MANIFEST_MCP_TOOLS[@]}"}"; do
  RESULT="$(check_mcp_tool "$tool" "${PROJECT:-$PWD}")"
  RC=$?
  case "$RC" in
    0) ;;  # ok
    *)
      write_halt "$RESULT" preflight "Tool '$tool' failed: $RESULT"
      exit 2
      ;;
  esac
done

echo "preflight: all manifest checks passed"
exit 0
```

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_phase_contracts.py e2e/tests/test_manifest_validation.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/phases/preflight.sh e2e/tests/test_phase_contracts.py e2e/tests/test_manifest_validation.py
git commit -m "feat(autopilot): add phases/preflight.sh manifest+env validator"
```

---

### ✅ Task 20: Wire preflight into `autopilot.sh` orchestrator

**Files:**
- Modify: `docs/ralph_loops/autopilot.sh`
- Modify: `e2e/tests/test_phase_contracts.py`

**Context:** Preflight runs twice (per design's data flow + Open Question 1 resolution). Phase 1 (pre-plan): env-only. Phase 1.5 (post-plan): full manifest validation. The orchestrator routes phase exit codes per the contract: 0 → next, 2 → halt cleanly (exit 0 from autopilot), 3 → skip, anything else → halt with `phase_crashed`.

> **Behavior change:** When phases halt-with-reason (exit 2), `autopilot.sh` now exits 0 (clean halt) instead of erroring out. The shell-level signal "did the autopilot finish without intervention?" is now `[ ! -f .autopilot-halt ]` after a successful run, not the autopilot's exit code.

> **Display note:** Both preflight invocations display the same banner format `▶ phase 1 of 6: preflight | running`. The duplication is intentional — Phase 1.5 is a re-run of Phase 1 with a now-present plan, not a separate phase in the user's mental model. Resolving the "of 6" with a 7-instance display is deferred to a v2 cleanup; the redundant invocation surfaces clearly enough in the log timeline.

> **HALT_PATH locality:** The orchestrator sets `HALT_PATH="$PROJECT/.autopilot-halt"` for phases 1, 2 (plan), 1.5 (post-plan preflight). Once `WORKTREE` is known (after Task 8's worktree phase), the orchestrator REASSIGNS `HALT_PATH="$WORKTREE/.autopilot-halt"` for phases 4 (ralph), 5 (mockup), 6 (verify). The orchestrator's own `read_halt` calls always use the current `$HALT_PATH`. This means: pre-worktree halts live in the main repo; post-worktree halts live in the worktree; the orchestrator's halt-detection-on-entry check at the top of the script (looking for a stale halt) covers only `$PROJECT/.autopilot-halt` because that's where the next run starts.

> **Ralph phase exemption from `run_phase`:** Phase 4 (ralph) does NOT use the `run_phase` helper because `run-ralph.sh` takes positional args (`$WORKTREE $PLAN_IN_WORKTREE`) and produces `.ralph-human-blocked` / `.ralph-done` sentinels rather than exit codes 0/2/3. Ralph keeps its existing invocation pattern; the orchestrator wraps the call to translate sentinels into the unified halt protocol (see code below).

**Step 1: Write the failing tests**

Append to `e2e/tests/test_phase_contracts.py`:

```python
def test_autopilot_invokes_preflight_twice():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    # Two invocations — once before plan, once after
    count = text.count('phases/preflight.sh')
    assert count >= 2, \
        f"autopilot.sh must invoke preflight twice (pre-plan and post-plan), found {count}"


def test_autopilot_halts_cleanly_on_exit_2():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    # Orchestrator must source halt lib and surface .autopilot-halt sentinel
    assert "lib/halt.sh" in text, "autopilot.sh must source lib/halt.sh to format halts"
    assert ".autopilot-halt" in text
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_phase_contracts.py -v -k "invokes_preflight or halts_cleanly"`
Expected: FAIL.

**Step 3: Edit `autopilot.sh`**

After the `source "$SCRIPT_DIR/lib/stages.sh"` line, add:

```bash
# shellcheck source=lib/halt.sh
source "$SCRIPT_DIR/lib/halt.sh"

# Pre-worktree halts live in the main repo; post-worktree halts live in the
# worktree (HALT_PATH is reassigned after Task 8's worktree phase).
HALT_PATH="$PROJECT/.autopilot-halt"
export HALT_PATH

# Pre-existing halt: surface and exit cleanly (re-run guidance)
if [ -f "$HALT_PATH" ]; then
  echo ""
  echo "Previous run halted. Sentinel content:"
  echo ""
  cat "$HALT_PATH"
  echo ""
  echo "Resolve the issue per fix-instructions above, delete .autopilot-halt, then re-run."
  exit 0
fi

# Helper to dispatch on phase exit code per the contract.
# Used for: preflight, plan, worktree, mockup, verify.
# NOT used for ralph (it has its own positional-arg signature; see below).
run_phase() {
  local n="$1" total="$2" name="$3" script="$4"
  report_stage "$n" "$total" "$name" running
  local exit_code=0
  bash "$script" || exit_code=$?
  case "$exit_code" in
    0) report_stage "$n" "$total" "$name" passed; return 0 ;;
    2)
      report_stage "$n" "$total" "$name" halted
      echo ""
      read_halt "$HALT_PATH"
      echo ""
      exit 0  # Clean halt — not a failure
      ;;
    3) report_stage "$n" "$total" "$name" skipped; return 3 ;;
    *)
      report_stage "$n" "$total" "$name" failed
      # Phase crashed (non-2 non-3 non-zero); write halt if no other halt exists
      if [ ! -f "$HALT_PATH" ]; then
        write_halt phase_crashed "$name" "Phase exited with code $exit_code"
      fi
      exit 1
      ;;
  esac
}
```

Add **Phase 1: preflight (pre-plan)** before the existing Phase 1 (now Phase 2):

```bash
export PROJECT PLAN_FILE LOG
PLAN_FILE="${PLAN_FILE:-}"  # may be empty pre-Phase-2; preflight handles
run_phase 1 6 preflight "$SCRIPT_DIR/phases/preflight.sh" || true
```

Refactor the plan, mockup, and verify invocations to use `run_phase`:

```bash
run_phase 2 6 plan "$SCRIPT_DIR/phases/plan.sh" || PLAN_PHASE_EXIT=$?
# Re-read PLAN_FILE from sentinel after plan phase
[ -f "$SENTINEL" ] && PLAN_FILE="$(tail -1 "$SENTINEL")"
export PLAN_FILE

# Phase 1.5 — re-run preflight now that plan exists. Same banner format
# as Phase 1 above; the duplication is intentional (see Display note).
run_phase 1 6 preflight "$SCRIPT_DIR/phases/preflight.sh" || true

# Worktree phase (Task 8 wired the WORKTREE_DIR computation)
run_phase 3 6 worktree "$SCRIPT_DIR/phases/worktree.sh"
WORKTREE="$WORKTREE_DIR"
STATUS="$WORKTREE/.finish-status"
PLAN_IN_WORKTREE="$WORKTREE/docs/plans/$(basename "$PLAN_FILE")"

# Reassign HALT_PATH to the worktree for post-worktree phases
HALT_PATH="$WORKTREE/.autopilot-halt"
export HALT_PATH
```

For Phase 4 (ralph), use the inline wrapper below — NOT `run_phase`. Ralph's positional-arg invocation and sentinel-based halt signal don't fit the helper's exit-code contract. The wrapper translates `.ralph-human-blocked` → halt-with-reason `human_action_required`:

```bash
report_stage 4 6 ralph running
RALPH_EXIT=0
bash "$RALPH_SCRIPT" "$WORKTREE" "$PLAN_IN_WORKTREE" || RALPH_EXIT=$?
if [ -f "$WORKTREE/.ralph-human-blocked" ]; then
  # write_halt uses $HALT_PATH from env; we just re-assigned it to the
  # worktree path above, so this writes to $WORKTREE/.autopilot-halt and
  # the read_halt below targets the same file.
  write_halt human_action_required ralph "Ralph loop halted; see $WORKTREE/.ralph-log"
  rm "$WORKTREE/.ralph-human-blocked"
  report_stage 4 6 ralph halted
  read_halt "$HALT_PATH"
  exit 0
fi
if [ "$RALPH_EXIT" -ne 0 ]; then
  report_stage 4 6 ralph failed
  exit 1
fi
report_stage 4 6 ralph passed

# Mockup and verify use run_phase (their phase scripts conform to the contract)
run_phase 5 6 mockup "$SCRIPT_DIR/phases/mockup.sh" || true  # mockup never halts
run_phase 6 6 verify "$SCRIPT_DIR/phases/verify.sh"
```

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_phase_contracts.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/autopilot.sh e2e/tests/test_phase_contracts.py
git commit -m "feat(autopilot): wire preflight + halt protocol into orchestrator"
```

---

### Task 21: Translate `verify.sh` failure into halt-with-reason

**Files:**
- Modify: `docs/ralph_loops/phases/verify.sh`
- Modify: `e2e/tests/test_halt_protocol.py`

**Context:** Currently the verify phase writes `.finish-status: FAILED` and `autopilot.sh` prints a generic error. With halt protocol, verify failure becomes `halt-with-reason: verify_failed` so the user sees the same structured surface as preflight halts.

**Step 1: Write the failing test**

Append to `e2e/tests/test_halt_protocol.py`:

```python
def test_phase_verify_emits_halt_on_failure():
    verify = REPO_ROOT / "docs" / "ralph_loops" / "phases" / "verify.sh"
    text = verify.read_text(encoding="utf-8")
    assert "lib/halt.sh" in text, "verify.sh must source lib/halt.sh"
    assert "write_halt verify_failed" in text, \
        "verify.sh must emit halt-with-reason verify_failed when .finish-status is FAILED"
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_halt_protocol.py::test_phase_verify_emits_halt_on_failure -v`
Expected: FAIL.

**Step 3: Update `phases/verify.sh`**

Add `source "$RALPH_DIR/lib/halt.sh"` at the top. After the claude -p invocation, when `.finish-status` indicates FAILED:

```bash
if [ -f "$STATUS" ]; then
  RESULT="$(grep '^status:' "$STATUS" 2>/dev/null | awk '{print $2}')"
  if [ "$RESULT" = "FAILED" ]; then
    FAILED_AT="$(grep '^failed_at:' "$STATUS" 2>/dev/null | awk '{print $2}')"
    HALT_PATH="$WORKTREE/.autopilot-halt" \
      write_halt verify_failed verify "Failed at: ${FAILED_AT:-unknown}; see $STATUS"
    exit 2
  fi
fi
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_halt_protocol.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/ralph_loops/phases/verify.sh e2e/tests/test_halt_protocol.py
git commit -m "feat(autopilot): verify.sh emits halt-with-reason verify_failed"
```

---

### Task 22: Add Anti-Pattern: Mid-Flow Human Review section to writing-plans

**Files:**
- Modify: `skills/writing-plans/SKILL.md`
- Modify: `skills/writing-plans/plan-critique-checklist.md` (Criterion 10)
- Modify: `skills/writing-plans/references/critique-panel-prompts.md` (Verifier prompt)
- Create: `e2e/tests/test_writing_plans_anti_review.py`

**Context:** Per Decision 9, writing-plans gets an explicit ban on mid-flow human-review tasks. The Verifier critic flags violations as HIGH severity. This is Epic D.

**Step 1: Write the failing test**

Create `e2e/tests/test_writing_plans_anti_review.py`:

```python
"""Static-parse tests for the Mid-Flow Human Review anti-pattern enforcement."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL = REPO_ROOT / "skills" / "writing-plans" / "SKILL.md"
CHECKLIST = REPO_ROOT / "skills" / "writing-plans" / "plan-critique-checklist.md"
PROMPTS = REPO_ROOT / "skills" / "writing-plans" / "references" / "critique-panel-prompts.md"

BANNED_PHRASES = [
    "human review",
    "user verifies",
    "review the UI",
    "wait for user",
    "confirm with user",
    "before proceeding ask",
    "user signs off",
    "get user approval",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_skill_has_anti_pattern_section():
    text = _read(SKILL)
    assert "Mid-Flow Human Review" in text, \
        "writing-plans/SKILL.md must contain a 'Mid-Flow Human Review' section"


def test_skill_lists_banned_phrases():
    text = _read(SKILL).lower()
    # At minimum, three of the banned phrases must appear in the policy text
    hits = sum(1 for p in BANNED_PHRASES if p.lower() in text)
    assert hits >= 3, f"writing-plans must list banned phrasings; found {hits}"


def test_checklist_criterion_10_has_mid_flow_row():
    text = _read(CHECKLIST)
    # New row in the gap-analysis table OR a dedicated subsection
    assert "Mid-flow human review" in text or "human review" in text.lower(), \
        "Criterion 10 must reference mid-flow human review"


def test_verifier_prompt_has_mid_flow_review_check():
    text = _read(PROMPTS)
    assert "human review" in text.lower() or "user verifies" in text.lower(), \
        "Verifier prompt must include the mid-flow review check"
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_writing_plans_anti_review.py -v`
Expected: FAIL.

**Step 3: Edit `writing-plans/SKILL.md`**

Insert a new section AFTER `## Manual Steps Policy` (currently ends at line 113) and BEFORE `## Standalone Scripts and Environment Variables`:

```markdown
## Anti-Pattern: Mid-Flow Human Review (BANNED)

**The autopilot's whole value is unattended completion.** The user reviews ONCE, at the end. Plan tasks that ask for user *judgment* mid-pipeline defeat that proposition — even when framed as "verification," "confirmation," or "review."

This is distinct from the Manual Steps Policy above. That policy governs *execution* the user must perform (Prerequisites, Post-Automation). This ban governs *judgment* the plan author wanted the user to provide between tasks. Different framing — same effect: the loop halts or improvises.

### Banned task body patterns

writing-plans MUST NOT produce plan tasks containing language like:

| Pattern | Why banned |
|---|---|
| "Get user feedback on X before proceeding" | Pipeline doesn't pause for feedback |
| "Have the user verify the UI looks correct" | Mockup fidelity loop is the machine check; user reviews at end |
| "Pause and ask if X is acceptable" | No human present to ask |
| "Review the interface before continuing to Task N+1" | User reviews when autopilot completes |
| "Confirm with user before proceeding" | No conversational surface; loop halts or guesses |
| "Show user the [output/screenshot/result] and wait" | Headless `claude -p` cannot wait for human input |
| "User signs off on the design before implementation" | Sign-off happened during brainstorming; not a plan task |

The pattern is "task body asks for *judgment* mid-pipeline." NOT banned: machine checks (mockup fidelity, eval scoring, verify gate are all machine-judged).

### What's allowed

- **Prerequisites (before Task 1)** — execution work the user does to unblock autopilot.
- **Manual Steps (Post-Automation)** — execution work the user does after autopilot completes.
- **Halt-with-reason (`.autopilot-halt`)** — environment failures the executor cannot resolve.
- **End-of-autopilot review** — the user reviews everything at the end.

### Enforcement

The Verifier critic flags any task body containing "human review", "user verifies", "review the [UI/interface/mockup/output]", "wait for user", "confirm with user", "before proceeding ask", "user signs off", "get user approval", or semantically equivalent language as HIGH severity. Suggested fix: relocate to Manual Steps (Post-Automation) if it's real verification work; remove if it's a gratuitous gate.

Exemption: Prerequisites, Manual Steps (Post-Automation), and Decision Log sections — these sections are explicitly user-facing and not part of the autopilot's task flow. Task bodies are not exempt regardless of where in the plan they sit.
```

**Step 4: Edit checklist + Verifier prompt**

In `skills/writing-plans/plan-critique-checklist.md`, append a row to the Criterion 10 table (just under the autonomy-violations row):

```markdown
| Mid-flow human review | Does any task body ask for user judgment between tasks ("human review", "user verifies", "review the [X]", "wait for user", "confirm with user", "user signs off", "get user approval")? Mid-flow review tasks defeat unattended autopilot completion. **HIGH severity**; relocate to Manual Steps (Post-Automation) or remove. See `skills/writing-plans/SKILL.md` "Anti-Pattern: Mid-Flow Human Review". |
```

In `skills/writing-plans/references/critique-panel-prompts.md`, in the Round 1 Verifier prompt's Phase 3, append after the manifest-coherence sentence (added in Task 15):

```
For checklist 10's mid-flow human review row: walk every Task body and scan for these phrasings (case-insensitive): "human review", "user verifies", "review the UI", "review the interface", "review the mockup", "review the output", "wait for user", "confirm with user", "before proceeding ask", "user signs off", "get user approval". Any match inside a Task body block is HIGH severity — cite task number, exact step text, and recommend "relocate to Manual Steps (Post-Automation) or remove." Exempt: Prerequisites, Manual Steps (Post-Automation), and Decision Log sections.
```

**Step 5: Run tests to verify they pass**

Run: `pytest e2e/tests/test_writing_plans_anti_review.py -v`
Expected: PASS.

**Step 6: Commit**

```bash
git add skills/writing-plans/SKILL.md skills/writing-plans/plan-critique-checklist.md skills/writing-plans/references/critique-panel-prompts.md e2e/tests/test_writing_plans_anti_review.py
git commit -m "feat(writing-plans): ban mid-flow human review tasks (Decision 9)"
```

---

### Task 23: Run full test suite

**Files:**
- (No file changes; verification task)

**Context:** All preceding tasks added or modified tests in `e2e/tests/`. Run the full suite to confirm no regressions.

**Step 1: Run the full e2e test suite**

Run: `pytest e2e/tests/ -v`
Expected: ALL PASS.

If any test fails, the Ralph loop should re-investigate the originating task. Failing tests at this point indicate a missed step in earlier tasks.

**Step 2: Commit (no-op if clean)**

If the suite passes with no changes needed, mark this task complete in the plan with no commit. Otherwise, fix the failing test in the appropriate task surface and commit:

```bash
git commit -m "test(autopilot): fix regressions discovered in full suite run"
```

---

## Manual Steps (Post-Automation)

> Complete these steps manually after all tasks finish.

None for this plan. The autopilot's `verify.sh` will run the full pytest suite as part of Phase 6. After verification passes, run `/aligned:finishing-a-development-branch` to merge.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Test pattern for bash | Static-parse pytest + bash-function unit tests via subprocess (function boundary only) | Subprocess testing of full orchestrator with PATH-shimmed `claude` |
| 2 | Manifest authoring visibility | Autonomous (no user prompt); user reviews via committed plan | Interactive prompt before plan commit |
| 3 | Phase invocation pattern | Subprocess `bash $SCRIPT_DIR/phases/foo.sh` with exported env | LIB_DIR/PHASES_DIR exports + sourced phases |
| 4 | Double-preflight | Yes — Phase 1 (env-only, plan may not exist) + Phase 1.5 (full manifest validation) | Single preflight after plan |
| 5 | `.ralph-human-blocked` migration | Coexist as alias indefinitely; orchestrator translates to `human_action_required` halt | Hard-deprecate after migration window |
| 6 | Existing-plan migration | Optional manifest in v1; preflight skips when absent | Bulk-migrate all 21 active plans |
| 7 | Centralized fix-instructions | `format_halt <reason>` in `lib/halt.sh` echoes canonical instructions; phase scripts pass details only | Each phase emits its own fix-instructions string |
| 8 | VERIFY-BRANCH.md collapse target | Thin wrapper directly referencing `skills/finishing-a-development-branch/SKILL.md` | New `_shared/verify-gate.md` referenced by both |
| 9 | Mid-flow review enforcement surface | Verifier critic + writing-plans contract section | Pure post-hoc detection; auto-rephrase |
| 10 | Discoverability gap | Defer to follow-up (brainstorming/modes/software.md:250-257 already covers autopilot; only execution-handoff-templates.md is missing) | Address inline in this plan |

### Appendix: Decision Details

#### Decision 1: Test pattern for bash

**Chose:** Static-parse pytest for orchestrator + phase contracts; bash-function unit tests via subprocess for `lib/manifest.sh` and `lib/halt.sh`.

**Why:** Consistent with `2026-04-28-ralph-autonomy-enforcement.md` Decision 7 and the design doc's Decision 5 — explicitly rejected adding orchestrator subprocess test infrastructure (PATH shimming, fake `claude` binaries). The function-level boundary IS testable via subprocess: `bash -c 'source lib/halt.sh; write_halt env_var_missing preflight "details"'` is a clean unit boundary that doesn't require shimming external commands. The orchestrator-level test (run autopilot.sh end-to-end) is what we're avoiding — those need fake claude.

**Alternatives rejected:**
- Full subprocess testing of orchestrator: PATH-shimming `claude`, mocking `git`, simulating `npm install` — high infra cost, slow, flaky.
- Pure static-parse for everything: misses behavioral bugs in `parse_manifest` / `write_halt` round-trip; function-level subprocess tests are cheap and high-value.

#### Decision 2: Manifest authoring visibility

**Chose:** writing-plans generates the manifest autonomously; user reviews via the committed plan.

**Why:** Resolves design doc's deferred HIGH item DevEx H3. writing-plans is already an autonomous skill (per its frontmatter and design). Adding an interactive prompt for the manifest is inconsistent with that posture. The Verifier critic catches manifest/body drift, so the user gets a verification surface without an interactive prompt. The user reads the plan after commit and can edit the manifest by hand if needed (changes in plan body re-trigger manifest generation on the next writing-plans run).

**Alternatives rejected:**
- Interactive prompt: breaks autonomy; not all writing-plans invocations have a conversational surface (autopilot uses `claude -p`).

#### Decision 3: Phase invocation pattern

**Chose:** Subprocess `bash $SCRIPT_DIR/phases/foo.sh` with required env vars exported by the orchestrator.

**Why:** Resolves design doc's deferred MEDIUM item (phase invocation pattern: LIB_DIR/PHASES_DIR exports vs absolute-path resolution). Subprocess invocation has clean boundaries — phase scripts cannot accidentally mutate orchestrator globals like `WORKTREE` or `PLAN_FILE`. Each phase resolves `$SCRIPT_DIR/.../lib/process.sh` from its own `$SCRIPT_DIR`, so the lib path is unambiguous.

**Alternatives rejected:**
- Sourced phases: would let phases mutate orchestrator globals; testing in isolation is harder (must also source the orchestrator's setup).
- LIB_DIR/PHASES_DIR exports: extra coupling without payoff — `$SCRIPT_DIR/../lib/foo.sh` resolution is local and works under all invocation paths.

#### Decision 4: Double-preflight

**Chose:** Phase 1 (env-only, plan may not exist) + Phase 1.5 (full manifest validation, after plan exists).

**Why:** Resolves design doc Open Question 1. Phase 1 catches "the plan-writing process itself depends on env vars or MCP tools that aren't available" — without it, plan.sh crashes mid-write instead of halting cleanly. Phase 1.5 catches plan-vs-env drift once the plan body exists. The QA H6 concern (SIGKILL during plan write leaves partial YAML) is addressed by `parse_manifest` returning exit-1 on malformed front-matter, which routes to `manifest_malformed` halt — covered by `e2e/fixtures/manifest/plan_partial.md` test.

**Alternatives rejected:**
- Single preflight after plan: simpler but environment issues that block plan-writing surface as plan.sh crashes (currently `phase_crashed`) instead of clean halts (`mcp_unreachable`). Worse UX for the most common failure class.

#### Decision 5: `.ralph-human-blocked` migration

**Chose:** Coexist as alias; orchestrator translates `.ralph-human-blocked` → `.autopilot-halt(human_action_required)`.

**Why:** Resolves design Open Question 2. `run-ralph.sh` is also user-facing (can be run standalone, not just via autopilot). Forcing it to write `.autopilot-halt` directly would be a behavioral change to the standalone path. The orchestrator-level translation keeps both surfaces working. The translation is in `autopilot.sh` Phase 4 wrapper (Task 20).

**Alternatives rejected:**
- Hard-deprecate after a migration window: no clear migration trigger; orphan complexity.

#### Decision 6: Existing-plan migration

**Chose:** Optional manifest in v1; preflight skips (exit 3) when manifest absent.

**Why:** Per design Decision 6. Mandatory migration of 21 active plans is a blocking change with no failure to motivate it (those plans don't currently break for the recurring MCP class — only future plans referencing missing tools would). Preflight-skip preserves backward compatibility.

**Alternatives rejected:**
- Bulk-migrate: blocks Epic B's ship; cost unjustified upfront.

#### Decision 7: Centralized fix-instructions

**Chose:** `format_halt <reason>` in `lib/halt.sh` echoes canonical fix-instructions; phase scripts pass `details:` only.

**Why:** Adopts deferred MEDIUM DevEx M7. Adding a new halt reason currently would touch ~6 surfaces (each phase that emits it). Centralizing to lib/halt.sh + the schema doc = 2 surfaces. Phase scripts know the situation-specific *details* but the *fix instructions* are reason-keyed and identical regardless of which phase emitted.

**Alternatives rejected:**
- Per-phase fix-instructions: every new halt site must be updated when guidance evolves; copy-paste drift.

#### Decision 8: VERIFY-BRANCH.md collapse target

**Chose:** Thin wrapper directly referencing `skills/finishing-a-development-branch/SKILL.md` Steps 1, 1a, 1b.

**Why:** Resolves design Open Question 4. The cleaner alternative (new `_shared/verify-gate.md` referenced by both) touches more surfaces — finishing skill must update its own wording, plus a new file. The thin-wrapper approach has VERIFY-BRANCH.md serve as the autopilot-specific scope-restrictor (no merge, no archive) while delegating the canonical steps.

**Alternatives rejected:**
- New `_shared/verify-gate.md`: more files, more references to keep aligned.

#### Decision 9: Mid-flow review enforcement surface

**Chose:** Verifier critic flags HIGH severity; writing-plans contract section documents the ban.

**Why:** Per design Decision 9. The user reports recurring incidents where writing-plans produces "human review" tasks; existing Manual Steps Policy uses "manual" too narrowly to catch them. The Verifier already enforces autonomy violations and TDD discipline — adding mid-flow review fits the pattern. Documenting in writing-plans/SKILL.md gives plan authors (and future maintainers) the canonical statement.

**Alternatives rejected:**
- Pure post-hoc detection (no contract section): plan authors don't see the rule until they get a Verifier finding; missed authoring-time prevention.
- Auto-rephrase: heuristic rewrites lose author intent; explicit refusal forces a real fix.

#### Decision 10: Discoverability gap

**Chose:** Defer to follow-up.

**Why:** The design Open Question 5 raised whether to address `references/execution-handoff-templates.md` (autopilot not surfaced) and `brainstorming/modes/software.md:250-257` (already covers autopilot per survey). Survey confirmed the latter — only execution-handoff-templates.md remains. That file lives under the writing-plans skill's "Execution Handoff" section, which the non-interactive override in this plan's invocation already skipped. Adding autopilot to that template surface is independent of the orchestration redesign and can ship as a small follow-up PR. Adding it here would scope-creep this plan beyond the design doc.

**Alternatives rejected:**
- Address inline: scope creep; the redesign is large enough.
