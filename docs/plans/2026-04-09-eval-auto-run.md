# Eval Auto-Run Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Wire the existing Promptfoo eval framework into the finishing-a-development-branch workflow so evals auto-run when LLM behavior surface files change on a branch.

**Source Design Doc:** `docs/plans/2026-04-09-eval-auto-run-design.md`

**Architecture:** Two new YAML config files (`e2e/eval-surface.yaml` and `e2e/trigger-map.yaml`) define the LLM behavior surface and map changed files to eval scenarios. The finishing-a-development-branch Step 1b reads these configs and runs scoped `npx promptfoo eval` commands. Six existing skill/workflow files get updated to replace phantom `eval-config.ts` references with the actual YAML-based infrastructure. (FINISH-BRANCH.md is also updated but to add new logic, not replace a phantom reference — it used generic prose.)

**Tech Stack:** Promptfoo (YAML scenarios), Python (pytest for config validation), Claude Code skills (Markdown prose instructions)

---

### ✅ Task 1: Create `e2e/eval-surface.yaml`

**Files:**
- Create: `e2e/eval-surface.yaml`

**Step 1: Create the surface config**

```yaml
# e2e/eval-surface.yaml
# Glob patterns identifying the LLM behavior surface.
# Consumers: finishing-a-development-branch Step 1b, eval-audit Phase 1
# Update when: new categories of LLM surface files are added

patterns:
  - advisors/prompts/**
  - frameworks/*/prompt.md
  - frameworks/*/examples.md
  - frameworks/*/anti-examples.md
  - skills/persona-panel/SKILL.md
  - skills/use-advisor/SKILL.md
  - skills/use-framework/SKILL.md
  - skills/brainstorming/modes/software.md
  - skills/brainstorming/modes/business.md
```

Write this to `e2e/eval-surface.yaml`.

**Step 2: Verify the file is valid YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('e2e/eval-surface.yaml')); print('OK')"`
Expected: `OK`

Note: If `pyyaml` is not installed system-wide, this may fail. That's fine — we'll validate via pytest in Task 5.

**Step 3: Commit**

```bash
git add e2e/eval-surface.yaml
git commit -m "feat(eval): add eval-surface.yaml defining LLM behavior surface patterns"
```

---

### ✅ Task 2: Create `e2e/trigger-map.yaml`

**Files:**
- Create: `e2e/trigger-map.yaml`

**Step 1: Create the trigger map**

```yaml
# e2e/trigger-map.yaml
# Maps changed files -> eval scenarios to run.
# Consumer: finishing-a-development-branch Step 1b
# Update when: new eval scenarios are added
# Note: scenario paths are e2e/-relative (for promptfoo -c), not repo-root-relative

triggers:
  - paths:
      - advisors/prompts/april-dunford.md
    scenarios:
      - scenarios/persona-panel/pricing-page.yaml
      - scenarios/use-advisor/april-dunford-blog-critique.yaml

  - paths:
      - frameworks/5-components-positioning/prompt.md
      - frameworks/5-components-positioning/examples.md
      - frameworks/5-components-positioning/anti-examples.md
    scenarios:
      - scenarios/use-framework/5-components-positioning.yaml

  - paths:
      - skills/persona-panel/SKILL.md
    scenarios:
      - scenarios/persona-panel/pricing-page.yaml

  - paths:
      - skills/use-advisor/SKILL.md
    scenarios:
      - scenarios/use-advisor/april-dunford-blog-critique.yaml

  - paths:
      - skills/use-framework/SKILL.md
    scenarios:
      - scenarios/use-framework/5-components-positioning.yaml
```

Write this to `e2e/trigger-map.yaml`.

**Step 2: Commit**

```bash
git add e2e/trigger-map.yaml
git commit -m "feat(eval): add trigger-map.yaml mapping files to eval scenarios"
```

---

### ✅ Task 3: Add PyYAML to e2e requirements

**Files:**
- Modify: `e2e/requirements.txt`

**Step 1: Add PyYAML dependency**

Append `pyyaml>=6.0` to `e2e/requirements.txt`. The file currently contains:

```
openai>=1.0.0,<2.0.0
pytest>=7.0.0
```

After edit:

```
openai>=1.0.0,<2.0.0
pytest>=7.0.0
pyyaml>=6.0
```

**Step 2: Install the updated requirements**

Run: `pip install -r e2e/requirements.txt`
Expected: Successfully installed (or already satisfied)

**Step 3: Commit**

```bash
git add e2e/requirements.txt
git commit -m "chore(eval): add pyyaml dependency for config validation tests"
```

---

### ✅ Task 4: Write test for eval-surface patterns

**Files:**
- Create: `e2e/tests/test_eval_surface_patterns.py`

This is a retroactive test — the config file already exists from Task 1.

**Step 1: Write the test**

```python
"""Validate eval-surface.yaml: every pattern matches at least one file on disk."""

from pathlib import Path

import pytest
import yaml

E2E_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = E2E_DIR.parent
SURFACE_FILE = E2E_DIR / "eval-surface.yaml"


def load_surface_patterns():
    """Load patterns from eval-surface.yaml."""
    with open(SURFACE_FILE) as f:
        data = yaml.safe_load(f)
    return data["patterns"]


def expand_pattern(pattern: str) -> list[Path]:
    """Expand a glob pattern relative to repo root.

    Handles both directory globs (advisors/prompts/**)
    and specific-file patterns (skills/persona-panel/SKILL.md).
    """
    return list(REPO_ROOT.glob(pattern))


PATTERNS = load_surface_patterns()


@pytest.mark.parametrize("pattern", PATTERNS)
def test_pattern_matches_at_least_one_file(pattern):
    """Each surface pattern must match at least one file on disk."""
    matches = expand_pattern(pattern)
    assert len(matches) > 0, f"Orphan pattern — no files match: {pattern}"


def test_surface_file_is_flat_list():
    """eval-surface.yaml must be a flat list of strings under 'patterns' key."""
    with open(SURFACE_FILE) as f:
        data = yaml.safe_load(f)
    assert "patterns" in data, "Missing 'patterns' key"
    assert isinstance(data["patterns"], list), "'patterns' must be a list"
    for item in data["patterns"]:
        assert isinstance(item, str), f"Pattern must be a string, got: {type(item)}"
```

Write to `e2e/tests/test_eval_surface_patterns.py`.

**Step 2: Run test to verify it passes**

Run (from repo root): `python -m pytest e2e/tests/test_eval_surface_patterns.py -v`
Expected: All tests PASS (9 pattern tests + 1 structure test)

**Step 3: Commit**

```bash
git add e2e/tests/test_eval_surface_patterns.py
git commit -m "test(eval): add validation tests for eval-surface.yaml patterns"
```

---

### ✅ Task 5: Write test for trigger-map paths and cross-validation

**Files:**
- Create: `e2e/tests/test_trigger_map_paths.py`

Retroactive test — config file exists from Task 2.

**Step 1: Write the test**

```python
"""Validate trigger-map.yaml: paths exist, scenarios resolve, cross-validate against surface."""

from pathlib import Path

import pytest
import yaml

E2E_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = E2E_DIR.parent
TRIGGER_MAP_FILE = E2E_DIR / "trigger-map.yaml"
SURFACE_FILE = E2E_DIR / "eval-surface.yaml"


def load_trigger_map():
    with open(TRIGGER_MAP_FILE) as f:
        return yaml.safe_load(f)


def load_surface_patterns():
    with open(SURFACE_FILE) as f:
        data = yaml.safe_load(f)
    return data["patterns"]


def expand_pattern(pattern: str) -> list[Path]:
    return list(REPO_ROOT.glob(pattern))


TRIGGER_DATA = load_trigger_map()
SURFACE_PATTERNS = load_surface_patterns()


def all_trigger_paths():
    """Extract all unique paths from trigger-map entries."""
    paths = []
    for entry in TRIGGER_DATA["triggers"]:
        for p in entry["paths"]:
            paths.append(p)
    return paths


def all_scenario_paths():
    """Extract all unique scenario paths from trigger-map entries."""
    scenarios = []
    for entry in TRIGGER_DATA["triggers"]:
        for s in entry["scenarios"]:
            scenarios.append(s)
    return scenarios


@pytest.mark.parametrize("trigger_path", all_trigger_paths())
def test_trigger_path_exists_on_disk(trigger_path):
    """Every path in trigger-map.yaml must exist in the repo."""
    full_path = REPO_ROOT / trigger_path
    assert full_path.exists(), f"Trigger path not found: {trigger_path}"


@pytest.mark.parametrize("scenario_path", all_scenario_paths())
def test_scenario_resolves_relative_to_e2e(scenario_path):
    """Every scenario path must resolve relative to e2e/ directory."""
    full_path = E2E_DIR / scenario_path
    assert full_path.exists(), f"Scenario not found: {scenario_path} (resolved to {full_path})"


@pytest.mark.parametrize("trigger_path", all_trigger_paths())
def test_trigger_path_matches_surface_pattern(trigger_path):
    """Every trigger-map path must match at least one eval-surface pattern.

    This is the cross-validation invariant from the design doc:
    trigger-map is a subset of eval-surface.
    """
    matched = False
    for pattern in SURFACE_PATTERNS:
        matches = expand_pattern(pattern)
        for m in matches:
            if m == REPO_ROOT / trigger_path:
                matched = True
                break
        if matched:
            break
    assert matched, (
        f"Trigger path '{trigger_path}' does not match any eval-surface pattern. "
        f"Add a matching pattern to eval-surface.yaml."
    )


def test_trigger_map_is_flat_structure():
    """trigger-map.yaml must be a flat structure: triggers array of objects with string arrays."""
    assert "triggers" in TRIGGER_DATA, "Missing 'triggers' key"
    assert isinstance(TRIGGER_DATA["triggers"], list), "'triggers' must be a list"
    for i, entry in enumerate(TRIGGER_DATA["triggers"]):
        assert "paths" in entry, f"Entry {i} missing 'paths'"
        assert "scenarios" in entry, f"Entry {i} missing 'scenarios'"
        assert isinstance(entry["paths"], list), f"Entry {i} 'paths' must be a list"
        assert isinstance(entry["scenarios"], list), f"Entry {i} 'scenarios' must be a list"
        for p in entry["paths"]:
            assert isinstance(p, str), f"Entry {i} path must be string, got: {type(p)}"
        for s in entry["scenarios"]:
            assert isinstance(s, str), f"Entry {i} scenario must be string, got: {type(s)}"
```

Write to `e2e/tests/test_trigger_map_paths.py`.

**Step 2: Run test to verify it passes**

Run (from repo root): `python -m pytest e2e/tests/test_trigger_map_paths.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add e2e/tests/test_trigger_map_paths.py
git commit -m "test(eval): add validation tests for trigger-map.yaml paths and cross-validation"
```

---

### ✅ Task 6: Write test for trigger-map scenario registration

> **Ordering dependency:** Complete Tasks 1–5 before this task. Step 3 runs the full suite which includes tests from Tasks 4 and 5.

**Files:**
- Create: `e2e/tests/test_trigger_map_scenarios.py`

Retroactive test — verifies that every scenario in trigger-map is also imported by `promptfooconfig.yaml`.

**Step 1: Write the test**

```python
"""Validate trigger-map scenarios are registered in promptfooconfig.yaml."""

from pathlib import Path

import yaml

E2E_DIR = Path(__file__).resolve().parent.parent
TRIGGER_MAP_FILE = E2E_DIR / "trigger-map.yaml"
PROMPTFOO_CONFIG = E2E_DIR / "promptfooconfig.yaml"


def test_all_trigger_scenarios_in_promptfoo_config():
    """Every scenario in trigger-map.yaml must appear in promptfooconfig.yaml imports."""
    with open(TRIGGER_MAP_FILE) as f:
        trigger_data = yaml.safe_load(f)

    with open(PROMPTFOO_CONFIG) as f:
        promptfoo_data = yaml.safe_load(f)

    # Extract scenario imports from promptfooconfig.yaml
    # Format: "file://scenarios/persona-panel/pricing-page.yaml"
    registered = set()
    for entry in promptfoo_data.get("scenarios", []):
        if isinstance(entry, str) and entry.startswith("file://"):
            registered.add(entry[len("file://"):])
        elif isinstance(entry, dict) and "file" in entry:
            registered.add(entry["file"])

    # Extract all unique scenarios from trigger-map
    trigger_scenarios = set()
    for entry in trigger_data["triggers"]:
        for s in entry["scenarios"]:
            trigger_scenarios.add(s)

    missing = trigger_scenarios - registered
    assert not missing, (
        f"Trigger-map scenarios not registered in promptfooconfig.yaml: {missing}. "
        f"Add 'file://<path>' entries to promptfooconfig.yaml's scenarios list."
    )
```

Write to `e2e/tests/test_trigger_map_scenarios.py`.

**Step 2: Run test to verify it passes**

Run (from repo root): `python -m pytest e2e/tests/test_trigger_map_scenarios.py -v`
Expected: PASS

**Step 3: Run the full test suite to verify nothing is broken**

Run (from repo root): `python -m pytest e2e/tests/ -v`
Expected: All tests pass (existing tests + new tests)

**Step 4: Commit**

```bash
git add e2e/tests/test_trigger_map_scenarios.py
git commit -m "test(eval): add validation test for trigger-map scenario registration"
```

---

### ✅ Task 7: Update `finishing-a-development-branch` Step 1b with canonical inline logic

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md` (Step 1b section, lines 146-167)

This is the largest single change. Replace the entire Step 1b placeholder with the canonical inline logic from the design doc (Component 3).

**Step 1: Replace Step 1b content**

Find the section starting at `### Step 1b: LLM Eval (auto-run if surface changed)` (line 146) and ending just before `### Step 1c: Architecture Doc Update` (line 169). Replace with:

```markdown
### Step 1b: LLM Eval (auto-run if surface changed)

**After tests pass, check if LLM behavior surface files were changed on this branch.**

**1. API key guard.** Check `ANTHROPIC_API_KEY` is set:

```bash
printenv ANTHROPIC_API_KEY
```

If not set, report: "ANTHROPIC_API_KEY not set — skipping LLM eval." Continue to Step 1c. Non-blocking.

**2. Config guard.** Read `e2e/eval-surface.yaml` and `e2e/trigger-map.yaml`. If either file is missing or empty, report: "Eval config missing — skipping LLM eval. Expected `e2e/eval-surface.yaml` and `e2e/trigger-map.yaml`." Continue to Step 1c. Non-blocking.

**3. Surface gate.** Get changed files:

```bash
git diff --name-only <base-branch>...HEAD
```

Match each changed file against the surface patterns in `e2e/eval-surface.yaml`. Pattern matching rules:
- **Directory globs** (e.g., `advisors/prompts/**`): match any path starting with the directory prefix (`advisors/prompts/`)
- **Wildcard-in-path patterns** (e.g., `frameworks/*/prompt.md`): match paths like `frameworks/X/prompt.md` where `X` is any single directory component
- **Specific-file patterns** (e.g., `skills/persona-panel/SKILL.md`): exact string match

If no changed files match any surface pattern, skip silently. Continue to Step 1c.

> **Behavior change:** The old Step 1b was vague about pattern matching. These three explicit rules (directory prefix, wildcard-in-path, exact match) are new specified behavior. They approximate recursive glob expansion for the current pattern set but may differ from true glob semantics if new patterns with complex wildcards are added. If a future pattern needs true glob matching, update these rules or add a glob-expansion utility.

**4. Scenario scoping.** For each changed surface file, look up matching trigger entries in `e2e/trigger-map.yaml`. A trigger entry matches if the changed file path exactly equals any path in the entry's `paths` array. Collect the deduplicated set of scenarios to run.

**5. Coverage summary.** Count how many changed surface files have trigger-map entries vs. don't. If any are unmapped, log: "N surface files changed, M have eval coverage, K do not. Run `/aligned:eval-audit` to check coverage." Non-blocking.

**6. Run scoped evals.** For each unique scenario, run sequentially (not in parallel — avoids API rate limit collisions):

```bash
npx promptfoo eval -c <scenario-path> --no-progress-bar
```

Run from the `e2e/` directory (use the Bash tool's working directory, not `cd e2e && ...`).

**7. Interpret results:**
- All exit 0, no warnings → pass, continue silently
- Exit 0 with warnings → continue with warning shown
- Any exit 1 → hard stop, show scorecard, invoke `/aligned:eval-failure-triage`

**8. Completion summary entry:**

| Branch state | Summary text |
|---|---|
| No surface changes | `Skipped — no surface changes` |
| All mapped, pass | `Passed — N scenarios` |
| Partial mapping | `Partial — ran N scenarios, M surface files unmapped` |
| Failure | `Failed — [scenario name]` |
| Config/API key missing | `Skipped — [reason]` |

**If no surface files changed:** Skip silently, continue to Step 1c.
```

**Code block nesting:** The replacement text above contains embedded ` ```bash ` fenced blocks. When editing the skill file, use 4-space indented code blocks for the bash commands instead of triple-backtick fences, OR use a higher-count fence (e.g., ```` ```` ````) as the outer delimiter in the Edit tool's replacement string. Read the existing file first to see how other Step sections handle embedded code blocks and follow the same pattern.

**Step 2: Verify the edit is correct**

Read `skills/finishing-a-development-branch/SKILL.md` from line 146 onward and confirm the new Step 1b is present and Step 1c follows immediately after.

**Step 3: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "feat(eval): replace Step 1b placeholder with canonical inline eval logic"
```

---

### ✅ Task 8: Update `VERIFY-BRANCH.md` Step 3 with reduced variant

**Files:**
- Modify: `docs/ralph_loops/VERIFY-BRANCH.md` (Step 3 section, lines 38-55)

Replace the placeholder Step 3 with a reduced non-interactive variant. This version has no coverage summary and no eval-failure-triage dispatch — just surface gate + run + pass/fail.

**Step 1: Replace Step 3 content**

Find the section starting at `## Step 3: LLM Eval (if surface changed)` (line 38) and ending just before `## Step 4: Write Status and Report` (line 57). Replace with:

```markdown
## Step 3: LLM Eval (if surface changed)

> Reduced non-interactive variant. Canonical logic is in `skills/finishing-a-development-branch/SKILL.md` Step 1b.

Determine the base branch (try `main`, then `master`).

**1. Config guard.** Check `ANTHROPIC_API_KEY` is set (`printenv ANTHROPIC_API_KEY`). If not set, skip with note "ANTHROPIC_API_KEY not set." Read `e2e/eval-surface.yaml` and `e2e/trigger-map.yaml`. If either is missing, skip with note "Eval config missing."

**2. Surface gate.** Get changed files via `git diff --name-only <base-branch>...HEAD`. Match against patterns in `e2e/eval-surface.yaml`:
- Directory globs (`advisors/prompts/**`): match paths starting with the directory prefix
- Wildcard patterns (`frameworks/*/prompt.md`): match paths like `frameworks/X/prompt.md`
- Specific files: exact string match

If no surface files changed, skip silently. Continue.

**3. Scenario scoping.** Look up changed surface files in `e2e/trigger-map.yaml`. Collect deduplicated scenarios.

**4. Run scoped evals.** For each scenario, run sequentially from the `e2e/` directory:

```bash
npx promptfoo eval -c <scenario-path> --no-progress-bar
```

**5. Interpret:**
- All exit 0 → Continue.
- Any exit 1 → Write status file with `status: FAILED` and `failed_at: LLM eval`. Exit.

**If no eval command exists:** Skip, report "No eval configured — skipped." Continue.
```

**Step 2: Verify the edit**

Read the modified file and confirm Step 3 content is correct and Step 4 follows.

**Step 3: Commit**

```bash
git add docs/ralph_loops/VERIFY-BRANCH.md
git commit -m "feat(eval): update VERIFY-BRANCH Step 3 with reduced eval variant"
```

---

### ✅ Task 9: Update `FINISH-BRANCH.md` Step 3 with reduced variant

**Files:**
- Modify: `docs/ralph_loops/FINISH-BRANCH.md` (Step 3 section, lines 40-55)

Same reduced variant as VERIFY-BRANCH.

**Step 1: Replace Step 3 content**

Find the section starting at `## Step 3: LLM Eval (if surface changed)` (line 40) and ending just before `## Step 4: Code Simplification Scan` (line 57). Replace with:

```markdown
## Step 3: LLM Eval (if surface changed)

> Reduced non-interactive variant. Canonical logic is in `skills/finishing-a-development-branch/SKILL.md` Step 1b.

Determine the base branch (try `main`, then `master`).

**1. Config guard.** Check `ANTHROPIC_API_KEY` is set (`printenv ANTHROPIC_API_KEY`). If not set, skip with note "ANTHROPIC_API_KEY not set." Read `e2e/eval-surface.yaml` and `e2e/trigger-map.yaml`. If either is missing, skip with note "Eval config missing."

**2. Surface gate.** Get changed files via `git diff --name-only <base-branch>...HEAD`. Match against patterns in `e2e/eval-surface.yaml`:
- Directory globs (`advisors/prompts/**`): match paths starting with the directory prefix
- Wildcard patterns (`frameworks/*/prompt.md`): match paths like `frameworks/X/prompt.md`
- Specific files: exact string match

If no surface files changed, skip silently. Continue.

**3. Scenario scoping.** Look up changed surface files in `e2e/trigger-map.yaml`. Collect deduplicated scenarios.

**4. Run scoped evals.** For each scenario, run sequentially from the `e2e/` directory:

```bash
npx promptfoo eval -c <scenario-path> --no-progress-bar
```

**5. Interpret:**
- All exit 0 → Continue.
- Any exit 1 → Print scorecard. Write status file with `status: FAILED` and `failed_at: LLM eval`. Exit. Do not proceed.

**If no eval command exists:** Skip, report "No eval configured — skipped."
```

**Step 2: Verify the edit**

Read the modified file and confirm Step 3 is correct and Step 4 follows.

**Step 3: Commit**

```bash
git add docs/ralph_loops/FINISH-BRANCH.md
git commit -m "feat(eval): update FINISH-BRANCH Step 3 with reduced eval variant"
```

---

### ✅ Task 10: Update `eval-audit` Phase 1 and Phase 3

**Files:**
- Modify: `skills/eval-audit/SKILL.md` (Phase 1 at lines 23-39, Phase 3 at lines 52-64)

Two changes: (1) Phase 1 reads `e2e/eval-surface.yaml` instead of `e2e/eval-config.ts`, (2) Phase 3 adds trigger-map cross-validation.

**Step 1: Update Phase 1**

In `skills/eval-audit/SKILL.md`, find the text on line 33:

```
Filter for files matching the LLM surface patterns defined in the project's eval config (typically `e2e/eval-config.ts` under `llmSurfacePatterns`). If no config exists, use these default patterns:
```

Replace with:

```
Filter for files matching the LLM surface patterns. Read `e2e/eval-surface.yaml` for the pattern list. If the file doesn't exist, use these default patterns:
```

**Step 2: Update Phase 3**

In `skills/eval-audit/SKILL.md`, find the section at Phase 3 `**If gaps found and substantial**` (around line 60). After the existing bullet about creating Kanban entries, add trigger-map cross-validation. Find:

```
- Report what's missing with specifics (e.g., "New advisor added in commit abc123, no eval scenario exists")
- Create a Kanban board entry for each gap in `docs/kanban/todo/` (see Kanban Entry Format below)
```

Replace with:

```
- Report what's missing with specifics (e.g., "New advisor added in commit abc123, no eval scenario exists")
- Create a Kanban board entry for each gap in `docs/kanban/todo/` (see Kanban Entry Format below). If `e2e/trigger-map.yaml` exists in the project, include in the Expected field: "Create eval scenario AND add corresponding entry to `e2e/trigger-map.yaml`."
```

**Step 3: Add Phase 3 cross-validation check**

Insert before `### Phase 4: Classification Pattern Maintenance`:

```markdown

**Cross-validation (always runs, even if no gaps):** Read `e2e/trigger-map.yaml`. Verify every path in the trigger-map matches at least one `e2e/eval-surface.yaml` pattern. If any trigger-map path is not covered by a surface pattern, report: "Trigger-map path `<path>` does not match any eval-surface pattern — add a matching pattern to `e2e/eval-surface.yaml`."
```

**Step 4: Verify edits**

Read the modified file and confirm both Phase 1 and Phase 3 changes are correct.

**Step 5: Commit**

```bash
git add skills/eval-audit/SKILL.md
git commit -m "feat(eval): update eval-audit to read eval-surface.yaml and cross-validate trigger-map"
```

---

### ✅ Task 11: Update `eval-failure-triage` header note

**Files:**
- Modify: `skills/eval-failure-triage/SKILL.md` (line 8)

**Step 1: Replace the header note**

Find:

```
> This skill assumes the `e2e/` directory convention: `e2e/scenarios/` for scenario files, `e2e/eval-config.ts` for configuration, `e2e/eval-runner.ts` for the runner, `e2e/eval-log.jsonl` for output. If the project uses different paths, check `CLAUDE.md` for overrides.
```

Replace with:

```
> This skill assumes the `e2e/` directory convention: `e2e/scenarios/` for scenario files, `e2e/eval-surface.yaml` for surface patterns, `e2e/trigger-map.yaml` for file-to-scenario mapping, `e2e/promptfooconfig.yaml` for the master config, `e2e/eval-log.jsonl` for output. If the project uses different paths, check `CLAUDE.md` for overrides.
```

**Step 2: Commit**

```bash
git add skills/eval-failure-triage/SKILL.md
git commit -m "fix(eval): update eval-failure-triage header to reference YAML configs"
```

---

### Task 12: Update `executing-plans` eval reference

**Files:**
- Modify: `skills/executing-plans/SKILL.md` (line 49, the `LLM surface check` paragraph)

**Step 1: Replace the eval reference**

Find:

```
**LLM surface check:** If the task involved changes to advisor prompts, framework prompts, prompt builders, or personalization logic, run the project's eval command (as defined in `CLAUDE.md` or `e2e/eval-config.ts`) to verify quality. Don't wait until all tasks are done — catching regressions early is cheaper than debugging across multiple steps. If evals fail, run the `/aligned:eval-failure-triage` skill to classify and fix before continuing.
```

Replace with:

```
**LLM surface check:** If the task involved changes to advisor prompts, framework prompts, prompt builders, or personalization logic, run the project's eval command. Check `e2e/trigger-map.yaml` for file-to-scenario mappings. If a mapping exists, run `npx promptfoo eval -c <scenario-path> --no-progress-bar` from the `e2e/` directory. Don't wait until all tasks are done — catching regressions early is cheaper than debugging across multiple steps. If evals fail, run the `/aligned:eval-failure-triage` skill to classify and fix before continuing.
```

**Step 2: Commit**

```bash
git add skills/executing-plans/SKILL.md
git commit -m "fix(eval): update executing-plans to reference trigger-map.yaml"
```

---

### Task 13: Update `kickstart` scaffold

**Files:**
- Modify: `skills/kickstart/SKILL.md` (lines 73-82, the Software scaffold `e2e/` section)

**Step 1: Update the scaffold**

Find the `e2e/` section in the scaffold tree:

```
├── e2e/
│   ├── scenarios/
│   ├── fixtures/
│   │   └── profiles/
│   ├── eval-config.ts                  # Starter eval configuration
│   ├── eval-runner.ts                  # Starter eval runner
│   └── .gitignore                      # eval-log.jsonl, .eval-audit-last-run
```

Replace with:

```
├── e2e/
│   ├── scenarios/
│   ├── fixtures/
│   │   └── profiles/
│   ├── eval-config.ts                  # Starter eval configuration (TS-based projects)
│   ├── eval-runner.ts                  # Starter eval runner (TS-based projects)
│   └── .gitignore                      # eval-log.jsonl, .eval-audit-last-run
```

Add a comment after the scaffold tree (after line 82, before the "Business, Personal, General" paragraph):

```markdown
> **Note:** YAML-based eval projects (like this plugin) use `eval-surface.yaml` + `trigger-map.yaml` instead of the `.ts` files. The TS scaffold is for general-purpose projects with TypeScript eval runners.
```

**Step 2: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "docs(eval): annotate kickstart scaffold with YAML-based eval note"
```

---

### Task 14: Update `add-advisor` Step 7 conditional eval block

**Files:**
- Modify: `skills/add-advisor/SKILL.md` (Step 7 section, around line 184)

**Step 1: Add trigger-map instruction inside the conditional block**

Find the paragraph at line 188:

```
If the project has eval infrastructure, create a quick-consult eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format.
```

Replace with:

```
If the project has eval infrastructure, create a quick-consult eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format. If `e2e/trigger-map.yaml` exists, add an entry mapping the new advisor prompt path to the new scenario path. If `e2e/promptfooconfig.yaml` exists, add `file://<scenario-path>` to its `scenarios` list.
```

**Step 2: Commit**

```bash
git add skills/add-advisor/SKILL.md
git commit -m "feat(eval): add trigger-map update to add-advisor eval block"
```

---

### Task 15: Update `add-framework` Step 6 conditional eval block

**Files:**
- Modify: `skills/add-framework/SKILL.md` (Step 6 section, around line 165)

**Step 1: Add trigger-map instruction inside the conditional block**

Find the paragraph at line 169:

```
If the project has eval infrastructure, create an eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format.
```

Replace with:

```
If the project has eval infrastructure, create an eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format. If `e2e/trigger-map.yaml` exists, add an entry mapping the new framework file paths (prompt.md, examples.md, anti-examples.md) to the new scenario path. If `e2e/promptfooconfig.yaml` exists, add `file://<scenario-path>` to its `scenarios` list.
```

**Step 2: Commit**

```bash
git add skills/add-framework/SKILL.md
git commit -m "feat(eval): add trigger-map update to add-framework eval block"
```

---

### Task 16: Add `.eval-audit-last-run` to e2e `.gitignore`

**Files:**
- Modify: `e2e/.gitignore`

The `eval-audit` skill writes `.eval-audit-last-run` (gitignored timestamp). The current `e2e/.gitignore` doesn't list it.

**Step 1: Append the entry**

Add `.eval-audit-last-run` to `e2e/.gitignore`. After edit:

```
node_modules/
output/
.promptfoo/
.venv/
*.cache
__pycache__/
.pytest_cache/
*.pyc
.eval-audit-last-run
```

**Step 2: Commit**

```bash
git add e2e/.gitignore
git commit -m "chore(eval): gitignore .eval-audit-last-run timestamp file"
```

---

### Task 17: Run full test suite and verify

**Files:** None (verification only)

**Step 1: Run full pytest suite**

Run (from repo root): `python -m pytest e2e/tests/ -v`
Expected: All tests pass — existing tests (test_fixtures.py, test_distinctness.py) plus new tests (test_eval_surface_patterns.py, test_trigger_map_paths.py, test_trigger_map_scenarios.py).

**Step 2: Verify no unexpected files are staged**

Run: `git status`
Expected: Clean working tree (all changes committed in previous tasks).

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Test framework for config validation | pytest (existing infra) | Shell script, Node.js test |
| 2 | One test file per concern vs. monolith | Three separate test files | Single `test_eval_config.py` |
| 3 | Commit granularity | One commit per logical unit | Single "big bang" commit |
| 4 | Reduced variant for VERIFY/FINISH-BRANCH | Inline but abbreviated | Reference-only ("see SKILL.md") |

### Appendix: Decision Details

#### Decision 1: pytest for config validation
**Chose:** Use pytest, matching the existing `e2e/tests/` infrastructure
**Why:** The project already has pytest set up with `conftest.py`, `requirements.txt`, and a `test` script in `package.json`. Adding more pytest files is zero-friction. The tests need to parse YAML, which Python handles natively (with pyyaml). Shell-based validation would be fragile and hard to parameterize. Node.js testing would require a separate test runner since promptfoo doesn't include a general-purpose test framework.
**Alternatives rejected:**
- Shell script: No parameterization, fragile string matching, poor error messages
- Node.js test: Would require installing jest/vitest, separate from existing pytest infra

#### Decision 2: Three separate test files
**Chose:** One file per concern — surface patterns, trigger-map paths, trigger-map scenario registration
**Why:** Each file validates a different invariant and can be run independently. `test_eval_surface_patterns.py` validates the surface config alone. `test_trigger_map_paths.py` validates trigger-map integrity and the cross-validation invariant. `test_trigger_map_scenarios.py` validates promptfooconfig.yaml alignment. Grouping them would mix concerns and make failure diagnosis harder.
**Alternatives rejected:**
- Single file: Harder to run selectively, mixed concerns, longer test output

#### Decision 3: Commit granularity
**Chose:** One commit per logical unit (config file, test file, skill update)
**Why:** Each commit is independently reviewable and revertable. If a skill update introduces a regression, it can be reverted without touching the config files or tests. This matches the project's existing commit style (small, descriptive commits).
**Alternatives rejected:**
- Single commit: Harder to review, impossible to revert individual changes

#### Decision 4: Reduced variant for ralph loop files
**Chose:** Inline but abbreviated — include the actual logic steps but skip coverage summary and eval-failure-triage dispatch
**Why:** VERIFY-BRANCH.md and FINISH-BRANCH.md run non-interactively and can't invoke interactive skills. They need enough logic to gate on surface changes and run evals, but don't need the full diagnostic workflow. The canonical reference back to SKILL.md ensures maintainers know where the full logic lives.
**Alternatives rejected:**
- Reference-only: Would leave the ralph loop files unable to actually run evals — they'd just point elsewhere. The non-interactive context can't "follow" a reference to another skill file mid-execution.
