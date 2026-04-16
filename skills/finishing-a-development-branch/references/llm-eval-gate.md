# LLM Eval Gate — Workflow Reference

Extracted from finishing-a-development-branch SKILL.md. Runs the eval suite when the changed files touch any surface pattern defined in `e2e/eval-surface.yaml`.

## Contents

- Step 1b: LLM Eval (auto-run if surface changed)
  - Surface-pattern matching rules
  - Scenario scoping via trigger-map.yaml
  - Coverage summary
  - Scoped eval execution

## Step 1b: LLM Eval (auto-run if surface changed)

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
- Any exit 1 → hard stop, show scorecard, classify failure (prompt issue, eval calibration, or model variance) and fix before continuing

**8. Completion summary entry:**

| Branch state | Summary text |
|---|---|
| No surface changes | `Skipped — no surface changes` |
| All mapped, pass | `Passed — N scenarios` |
| Partial mapping | `Partial — ran N scenarios, M surface files unmapped` |
| Failure | `Failed — [scenario name]` |
| Config/API key missing | `Skipped — [reason]` |

**If no surface files changed:** Skip silently, continue to Step 1c.
