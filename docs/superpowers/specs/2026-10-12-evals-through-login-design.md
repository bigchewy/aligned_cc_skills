# Evals Through the Claude Code Login

Page job: Eric reads this once to confirm the design before the build, and comes back to it to see how evals are run and scored.

Subtitle: Promptfoo evals that run on the Claude Code login and only for what changed.

## The answer

Every eval in `e2e/` runs through the Claude Code login, and `npm run eval` runs only the scenarios touched by the files changed on the branch. Promptfoo is the eval tool. A scenario is one YAML file under `e2e/scenarios/` that sends the same task to Claude with and without an Aligned prompt and has a second Claude call (the judge) score each answer.

Numbers (tiles):

- 58: Scenario files
- 0: Ever scored
- ~15: Calls, one scenario
- ~875: Calls, all 58

### Your two requirements

Eric's words, each with what the design does:

1. "We're always using Claude Code to do evals." The runner removes `ANTHROPIC_API_KEY` from the eval process. The key is used only when someone passes `--use-api-key`.
2. "I don't want to be spending half of my weekly token allowance on Claude Code running an eval if it's not actually evaluating changes that I made." With no arguments, the runner runs only scenarios mapped to changed files. Running all 58 takes `--all`, and Claude asks Eric before using it.

## How a run picks its scenarios

Diagram: changed files go through the trigger map to a short list of scenarios.

Box labels: Changed files (commits, edits, new files) → trigger-map.yaml (prompt file to scenarios) → Scenarios to run (only the mapped ones) → promptfoo (one scenario at a time).
Side path: "changed scenario file: runs itself" and "changed shared file: runs nothing, suggests --all".

Caption: Changing one advisor's prompt runs that advisor's scenarios and nothing else.

### The rules the runner follows

- Changed files are the branch's commits against `main` (`--base` changes it), plus uncommitted and untracked files.
- `e2e/trigger-map.yaml` already maps each prompt file to its scenarios. The runner reads it.
- A changed scenario file runs that scenario.
- A changed shared file (`e2e/providers/claude-login.yaml` or `e2e/providers/rubric-prompt.txt`) affects every scenario. The runner prints that and runs nothing, because only Eric decides to spend a full run.
- Changed prompt files with no trigger-map entry are counted and printed, so missing coverage shows up.
- No mapped changes: the runner says so and exits 0 without a call.

### Commands you run from e2e/

```
npm run eval                                    # scenarios for changed files
npm run eval -- scenarios/use-advisor/steve-blank-consult.yaml   # one scenario
npm run eval -- --all                           # all 58, prints the call count first
npm run eval -- --resume <run id>               # finish a stopped run
```

## How a call reaches Claude

Diagram: before and after.

Before: Scenario → promptfoo (anthropic:messages) → Anthropic API (needs the key).
After: Runner (removes the key) → promptfoo (anthropic:claude-agent-sdk) → claude CLI (your login).

Caption: The answer and the judge both go through the same provider file.

### The shared provider file

`e2e/providers/claude-login.yaml`. Every scenario points `providers` and `defaultTest.options.provider` at it.

```yaml
id: anthropic:claude-agent-sdk
config:
  apiKeyRequired: false
  model: sonnet
  custom_system_prompt: ""
  tools: []
  max_turns: 1
```

- `apiKeyRequired: false` stops promptfoo from demanding a key.
- `custom_system_prompt: ""` keeps Claude Code's own system prompt out, so the vanilla baseline is a bare model.
- `model: sonnet`, because the old pinned model name fails under the login.

### Why the runner removes two variables

- ANTHROPIC_API_KEY: The provider passes any key it finds to the SDK, and the SDK then bills the API. Removing it from the child process is what keeps every call on the login.
- CLAUDE_PID: A child process that inherits it kills the parent Claude Code session.

### Load on your subscription

The runner runs 2 tests at a time and 2 judge calls per test. It stops the whole run on a rate-limit error, and `--resume` continues it later.

## How a scenario is scored

### One scale for every judge call

Every rubric says "Score 1-5". Promptfoo's built-in judge prompt asks for a 0 to 1 score, so scores mixed both scales. A shared judge prompt, `e2e/providers/rubric-prompt.txt`, tells the judge the scale is 1 to 5 and to return a whole number from 1 to 5. All 228 rubrics keep their wording, and the README bars work as written.

### How to read a verdict

Each test gets a label in its metadata saying which kind of answer it is: `full-stack` (the Aligned prompt), `vanilla` (no prompt), `aware` (names the expert, no Aligned prompt), or `single` (a routing check with no baseline).

| Scenario kind | Passes when |
|---|---|
| Paired | full-stack averages 3.5 or more, beats vanilla by 1.0 or more, and beats aware by 0.5 or more when an aware test exists |
| Routing | every test averages 3.5 or more |

- Promptfoo's own PASS/FAIL column is not the verdict. Vanilla tests are built to fail.
- A scenario is ERROR when promptfoo exits with anything other than 0 or 100, the output file is missing, a test has a provider error, or any judge call failed. A failed judge call scores 0 in promptfoo, so the scorer checks for it before averaging.
- The distinctness check (OpenAI embeddings) stays outside the verdict.
- The report names the model that answered, since `sonnet` moves to newer models over time.

### Where results land

`e2e/output/runs/<run id>/`, one JSON per scenario plus `summary.md` with a row per scenario: verdict, full-stack score, both gaps, and the reason for any ERROR.

## What changes in the repo

New:

- `e2e/providers/claude-login.yaml`: the shared provider.
- `e2e/providers/rubric-prompt.txt`: the shared judge prompt.
- `e2e/run_evals.py`: picks scenarios, runs promptfoo, writes the summary.
- `e2e/scorers/scenario_verdict.py`: turns one promptfoo output file into a verdict.
- `e2e/scripts/migrate_scenarios.py`: one-time edit of all 58 scenario files (provider, judge prompt, test labels). Deleted after it runs.

Changed:

- All 58 files in `e2e/scenarios/`.
- `e2e/package.json`: promptfoo pinned to 0.124.1, `@anthropic-ai/claude-agent-sdk` 0.3.283 added, Node 22 required, `eval` script points at the runner.
- `e2e/README.md`: the login replaces the key, the commands above, the verdict rules.
- `skills/add-advisor/SKILL.md` and `skills/add-framework/SKILL.md`: when `e2e/run_evals.py` exists, run only the new scenario with the runner and never skip for a missing key. Other users' projects keep the existing check.
- `skills/eval-audit/SKILL.md`: drop "missing credentials" as a reason to file a Kanban entry instead of running.
- `docs/plans/completed/2026-04-09-eval-auto-run.md`: the key check becomes a note pointing at the runner. The skill that plan built was removed on 2026-08-14, so this edit changes no behavior.
- Plugin version bump and changelog.

Deleted:

- `e2e/promptfooconfig.yaml`. Promptfoo cannot run these scenario files from it, and the runner finds scenarios by scanning the folder.
- `e2e/tests/test_trigger_map_scenarios.py`, which checked that list.

Left alone: `scripts/autopilot/VERIFY-BRANCH.md` (autopilot is parked) and `docs/mockups/` (history).

## Tests

### Tests, written first

- `e2e/tests/test_eval_scenario_config.py`: every scenario uses the shared provider and judge prompt, none uses `anthropic:messages`, every test has a kind label, and every paired scenario has one full-stack and one vanilla test.
- `e2e/tests/test_scenario_verdict.py`: paired pass, each of the three bars failing, aware missing, routing pass and fail, judge error, provider error, missing kind label, unreadable file.
- `e2e/tests/test_run_evals.py`, with git and promptfoo mocked: scenario picking from changed files, a changed scenario file, a changed shared file, no mapped changes, `--all`; the child env has no `ANTHROPIC_API_KEY` or `CLAUDE_PID` unless `--use-api-key`; exit codes 0 and 100 count as ran, any other is ERROR; a rate-limit error stops the run; `--resume` skips finished scenarios; promptfoo failing to start is ERROR.

### Proof after the build

Run `npm run eval -- scenarios/use-advisor/steve-blank-consult.yaml` to prove the path end to end. The full run of all 58 waits for Eric's OK.
