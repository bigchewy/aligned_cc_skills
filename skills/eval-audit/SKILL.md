---
name: eval-audit
description: "Eval coverage auditor. Detects LLM behavior surface changes without eval coverage. Manual invocation only."
---

# Eval Coverage Audit

## Overview

Ensure every LLM behavior surface change has eval coverage. Catches gaps the pipeline missed and triggers the standard pipeline to fill them.

**Invocation:** `/aligned:eval-audit` (manual only).

**Core principle:** Every change to prompts, prompt builders, personalization logic, or framework routing should have a corresponding eval scenario that verifies the behavior.

## When to Use

- Run manually after adding new advisors, frameworks, or prompt logic
- Run after completing a batch of LLM-related changes

## The Process

### Phase 1: Detect Changes Since Last Audit

Read the last audit timestamp from `e2e/.eval-audit-last-run` (Unix epoch or ISO date, gitignored).

Gather two sources of change:

1. **Git commits since last audit:**
   ```bash
   git log --since="<last-run>" --name-only --pretty=format:""
   ```
   Filter for files matching the LLM surface patterns. Read `e2e/eval-surface.yaml` for the pattern list. If the file doesn't exist, use these default patterns:
   - `**/prompts/**` — advisor/system prompts
   - `**/prompt-builders/**` — prompt construction logic
   - `**/frameworks/**` — framework definitions
   - `**/personalization/**` or `**/user-profile/**` — personalization logic
   - Any file containing `systemPrompt`, `generateText`, `streamText`, or `generateObject`

2. **Recently completed plans:**
   Read `docs/plans/completed/` for plan files moved there since last audit. Parse goal and task descriptions to identify LLM behavior changes that might not show up as file-path matches.

### Phase 2: Cross-Reference Against Existing Coverage

For each changed LLM surface file:

1. Read `e2e/scenarios/` and map each scenario to the surface files it exercises (by reading scenario configs and matching against the changed files)
2. Identify gaps:
   - Surface files that changed but have no scenario covering them
   - Scenarios that exist but haven't been updated to reflect the changes

### Phase 3: Report or Trigger Pipeline

**If no gaps found:** Write current Unix epoch (`date +%s`) to `e2e/.eval-audit-last-run`, report clean, done.

**If gaps found but minor** (existing scenarios need keyword/threshold updates):
- Report the gaps as a checklist
- Offer to auto-fix calibration issues inline (keyword/threshold adjustments)

**If gaps found and substantial** (new scenarios needed):
- Report what's missing with specifics (e.g., "New advisor added in commit abc123, no eval scenario exists")
- Create a Kanban board entry for each gap in `docs/kanban/todo/` (see Kanban Entry Format below). If `e2e/trigger-map.yaml` exists in the project, include in the Expected field: "Create eval scenario AND add corresponding entry to `e2e/trigger-map.yaml`."
- Ask: "Should I trigger the pipeline to create these eval scenarios now?"
- If yes, kick off `/aligned:brainstorming` → `/aligned:writing-plans` → `/aligned:executing-plans` → `/aligned:finishing-a-development-branch` for the eval scenario creation work

**Cross-validation (always runs, even if no gaps):** Read `e2e/trigger-map.yaml`. Verify every path in the trigger-map matches at least one `e2e/eval-surface.yaml` pattern. If any trigger-map path is not covered by a surface pattern, report: "Trigger-map path `<path>` does not match any eval-surface pattern — add a matching pattern to `e2e/eval-surface.yaml`."

### Phase 4: Classification Pattern Maintenance

After the coverage check, if new LLM surface patterns were added (new advisor types, framework structures, personalization sources):

1. **Generate real examples immediately.** Read the new prompt/framework, run a single eval scenario against it (or make a direct API call), and use the actual output to write a concrete classification example.

2. **Classify the example.** Determine if the failure is (a) a prompt issue, (b) model variance, or (c) eval calibration (wrong keywords/thresholds).

3. **Write the pattern entry** to the project's classification patterns file (if it exists, typically at `e2e/references/classification-patterns.md`).

4. **If the API call can't run** (missing credentials, rate limits, CI environment), file a Kanban entry (see format below) with the specific instruction: "Run one eval pass against [scenario] and document the classification pattern."

## Kanban Entry Format

When filing a Kanban entry, read `{base-directory}/../_shared/kanban-entry-format.md` for the template and counter instructions (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load). Use `eval-audit` as the "Discovered during" value.

## Integration

- **kickstart** — Scaffolds the `e2e/` infrastructure this skill audits
- **executing-plans** — Implements eval scenarios when gaps are substantial
