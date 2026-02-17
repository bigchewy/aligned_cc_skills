---
name: eval-failure-triage
description: Use when LLM eval scenarios fail and the cause is unclear. Guides systematic classification of failures into prompt issues, eval calibration problems, or model variance, then applies targeted fixes.
---

# Eval Failure Triage

> This skill assumes the `e2e/` directory convention: `e2e/scenarios/` for scenario files, `e2e/eval-config.ts` for configuration, `e2e/eval-runner.ts` for the runner, `e2e/eval-log.jsonl` for output. If the project uses different paths, check `CLAUDE.md` for overrides.

## Overview

LLM eval failures have multiple possible causes. The most common mistake is treating every failure as a prompt problem. This skill provides a systematic classification process to identify root cause before applying fixes.

**Core principle:** Classify before fixing. A miscalibrated eval wastes time if you fix the prompt instead.

**Complements:** `systematic-debugging` (deterministic bugs). This skill fills the gap for probabilistic failures where reproducibility is variable and root causes span prompt quality, eval calibration, and model variance.

## When to Use

- After running the project's eval command and seeing failures
- When eval failures persist after prompt changes
- When adding new eval scenarios that fail on first run
- When judge scores are inconsistent across runs

## The Process

### Phase 0: Infrastructure Pre-Check

Before classifying quality failures, check for infrastructure errors — these mean the eval runner itself broke, not that the prompt is bad.

| Symptom | Classification | Fix |
|---------|---------------|-----|
| Runner crashed / timeout | Infrastructure | Check runner config, increase timeout |
| Sibling tool call errors | Infrastructure | Isolate eval scenarios, run sequentially |
| Missing CLI tools (jq, etc.) | Infrastructure | Install dependency or remove from eval |
| Judge output truncated | Infrastructure | Reduce response length or increase judge token limit |
| Incoherent judge reasoning | Calibration | Rewrite judge rubric with concrete examples |

Fix infrastructure errors first, re-run, then proceed to Phase 1.

### Phase 1: Gather Evidence

**Run the eval and capture results.** For intermittent failures, run 2-3 times to distinguish consistent from variable failures.

Run the project's eval command with the failing scenario (e.g., `npm run eval -- --scenario <name>` or the equivalent defined in `CLAUDE.md`).

For each failing scenario, record:
1. Which dimensions failed (the project's configured eval dimensions)
2. Whether the heuristic or judge (or both) failed
3. The judge score and reasoning
4. The actual response text (first 100 chars in the output)

Read the eval log (location defined in project's eval config, typically `e2e/eval-log.jsonl`) for full details.

### Phase 2: Classify Each Failure

For each failing dimension in each scenario, classify using the decision tree. Load `references/classification-patterns.md` for the full taxonomy and examples.

**Quick classification:**

| Signal | Likely Classification |
|--------|----------------------|
| Heuristic fails, judge passes | **(c) Eval calibration** — heuristic thresholds or keywords are wrong |
| Heuristic passes, judge fails | **(d) Judge variance** or **(a) real prompt issue** — check if judge score varies across runs |
| Both fail consistently | **(a) Prompt issue** or **(d) combination** — read the actual response to determine |
| Heuristic fails on opening turn only | **(c) Eval calibration** — opening turns have different characteristics than response turns |
| Scenario tests wrong advisor | **(c) Eval calibration** — check framework routing (framework path loads framework's primary advisor, not the scenario's named advisor) |
| Judge says "No response was provided" | **(c) Infrastructure** — judge truncation or prompt parsing issue |

### Phase 3: Fix by Category

Apply fixes in this order — cheapest/fastest first:

**1. (c) Eval calibration fixes** (change eval, not prompts)
- Adjust scenario-specific heuristic parameters to match what the model can actually produce in that turn context
- Update voice/style fingerprint patterns to match the actual advisor being tested
- Adjust flow thresholds in the project's eval configuration file if they're too strict for the advisor type
- Skip heuristics that don't apply to specific turn types (e.g., personalization on opening turns)

**2. (b) Prompt template fixes** (minor prompt adjustments)
- Add missing instructions (e.g., pacing, voice distinctiveness)
- Bridge personalization context into framework prompts
- Add length/conciseness guidance where absent

**3. (a) Voice/prompt quality fixes** (substantive prompt rewrites)
- Add or revise voice calibration sections
- Restructure prompt to better guide the model
- These are real improvements, not calibration — proceed carefully

**4. (d) Judge/model variance** (accept or mitigate)
- If judge scores swing 2-5 across runs on the same response, the judge rubric or model is unreliable for this dimension
- Options: increase judge truncation limit, improve judge rubric specificity, accept variance as inherent

### Phase 4: Verify

After applying fixes, re-run the specific scenario using the project's eval command.

If the fix was (c) eval calibration, a single run should confirm. If the fix was (a) or (b) prompt changes, run 2-3 times to account for response model variance.

### Phase 5: Report

Present results as a table:

```
| Scenario | Dimension | Before | After | Fix Type |
|----------|-----------|--------|-------|----------|
| name     | voice     | FAIL   | PASS  | (c) keywords |
```

If failures remain, return to Phase 2 and reclassify.

## Trend Analysis

When reviewing results across multiple eval runs:

- **Same scenario failing across runs** → likely (a) prompt issue or (c) calibration, not variance
- **Same dimension failing across scenarios** → systemic issue — shared threshold or template constraint
- **Intermittent pass/fail** → likely (d) model/judge variance
- **New failures after prompt change** → likely prompt regression — diff the change and check for removed guidance

## Key Principles

**Opening turns are different from response turns.** First-turn behavior differs from response turns — eval heuristics may need turn-type awareness. Either skip the heuristic on opening turns or use opening-specific keywords.

**Framework routing may change the responding advisor.** When a scenario specifies a framework, the prompt builder may load the framework's primary advisor, not the scenario's named advisor. Voice fingerprints and anti-patterns must match the actual advisor.

**Judge truncation affects reliability.** Long system prompts get truncated before reaching the judge. If the voice-defining section falls beyond the truncation limit, the judge can't evaluate voice accurately. Check the judge's max prompt/response length configuration.

**Deterministic vs variable failures require different responses.** A failure that happens 5/5 runs is likely a real issue (prompt or calibration). A failure that happens 2/5 runs is likely variance. Don't over-engineer fixes for variance.

## Lessons-Learned Gate

BEFORE completing this skill's process:
  IF eval failures were misclassified (prompt fix applied to calibration issue or vice versa):
    Write a lesson to docs/lessons-learned/YYYY-MM-DD-short-description.md
    using the lesson template (see kickstart scaffold docs).

## Integration

- **systematic-debugging** — For deterministic bugs. This skill handles probabilistic failures.
- **writing-plans** — When triage reveals substantive prompt work needed, write a plan before implementing.
- **executing-plans** — For multi-fix implementation.

## References

- `references/classification-patterns.md` — Full failure taxonomy with examples.
