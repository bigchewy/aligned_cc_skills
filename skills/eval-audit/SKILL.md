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
   Filter for files matching the LLM surface patterns defined in the project's eval config (typically `e2e/eval-config.ts` under `llmSurfacePatterns`). If no config exists, use these default patterns:
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
- Offer to auto-fix calibration issues inline (category (c) fixes from `/aligned:eval-failure-triage`)

**If gaps found and substantial** (new scenarios needed):
- Report what's missing with specifics (e.g., "New advisor added in commit abc123, no eval scenario exists")
- Create a Kanban board entry for each gap in `docs/kanban/todo/` (see Kanban Entry Format below)
- Ask: "Should I trigger the pipeline to create these eval scenarios now?"
- If yes, kick off `/aligned:brainstorming` → `/aligned:writing-plans` → `/aligned:executing-plans` → `/aligned:finishing-a-development-branch` for the eval scenario creation work

### Phase 4: Classification Pattern Maintenance

After the coverage check, if new LLM surface patterns were added (new advisor types, framework structures, personalization sources):

1. **Generate real examples immediately.** Read the new prompt/framework, run a single eval scenario against it (or make a direct API call), and use the actual output to write a concrete classification example.

2. **Classify the example.** Apply the decision tree from `{base-directory}/../eval-failure-triage/references/classification-patterns.md` (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load).

3. **Write the pattern entry** to the project's classification patterns file (if it exists, typically at `e2e/references/classification-patterns.md`).

4. **If the API call can't run** (missing credentials, rate limits, CI environment), file a Kanban entry (see format below) with the specific instruction: "Run one eval pass against [scenario] and document the classification pattern."

## Kanban Entry Format

When filing a Kanban entry, read `{base-directory}/../_shared/kanban-entry-format.md` for the template and counter instructions (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load). Use `eval-audit` as the "Discovered during" value.

## Integration

- **eval-failure-triage** — Diagnoses failures this skill discovers
- **kickstart** — Scaffolds the `e2e/` infrastructure this skill audits
- **executing-plans** — Implements eval scenarios when gaps are substantial
