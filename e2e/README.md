# Aligned Eval Framework

Quantitative evaluation of Aligned plugin skills using Promptfoo.

**Core question:** Does a skill produce a measurably better deliverable than prompting the LLM directly?

Every eval runs through your Claude Code login. No `ANTHROPIC_API_KEY` is needed, and the runner removes it from the eval process if your shell has one, so a run never bills the API by accident.

## Prerequisites

- Node.js 22.22 or newer (promptfoo 0.124.1 requires it)
- Python 3.10+
- Claude Code installed and logged in. Check with `claude auth status`; it should show `"loggedIn": true`.
- `OPENAI_API_KEY`, only for the distinctness scorer

## Setup

```bash
cd e2e
npm install
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Running Evals

Run from `e2e/`. By default the runner evals only what you changed:

```bash
npm run eval
```

It collects the files changed on your branch against `main` (pass `--base <branch>` to compare with another branch), plus uncommitted and untracked files. Then it looks each one up in `trigger-map.yaml` and runs only the mapped scenarios. A changed scenario file runs itself. If nothing maps, it runs nothing.

Run named scenarios:

```bash
npm run eval -- scenarios/use-advisor/steve-blank-consult.yaml
```

Run every scenario. This is about 875 Claude calls, so Claude asks before running it:

```bash
npm run eval -- --all
```

If a run stops on a rate limit, finish it later:

```bash
npm run eval -- --resume <run id>
```

Contributors without a Claude Code login can pass `--use-api-key` to keep `ANTHROPIC_API_KEY`.

Each run prints how many Claude calls it will make, runs 2 tests at a time, and writes to `output/runs/<run id>/`: one promptfoo JSON file per scenario and `summary.md`.

## How Evals Reach Claude

Every scenario points at two shared files:

- `providers/claude-login.yaml` is the provider for both the answer and the judge. It uses promptfoo's `anthropic:claude-agent-sdk` provider, which runs the `claude` CLI on your login with no tools and no Claude Code system prompt.
- `providers/rubric-prompt.txt` is the judge prompt. It tells the judge each rubric is scored from 1 to 5.

New scenarios copy an existing one, keeping its `providers` and `defaultTest.options` lines. `tests/test_eval_scenario_config.py` fails for any scenario that doesn't.

## Three-Provider Comparison

Every paired scenario runs the same input three ways. Each test's `metadata.arm` says which:

| Arm | System Prompt | What It Proves |
|-----|--------------|----------------|
| `full-stack` | Advisor/framework prompt | What Aligned users get |
| `vanilla` | None | Baseline, no structure |
| `aware` | None (expert or framework named in the user prompt) | Competent ChatGPT user |

Routing scenarios in `scenarios/use-skill/` check one behavior with no baseline. Their tests use `arm: single`.

## Pass/Fail Thresholds

The runner's `summary.md` holds the verdict. Promptfoo's own PASS/FAIL column does not, because vanilla tests are built to fail.

| Scenario | Passes when |
|----------|-------------|
| Paired | full-stack averages >= 3.5 / 5.0, beats vanilla by >= 1.0, and beats aware by >= 0.5 when an aware test exists |
| Routing | every test averages >= 3.5 / 5.0 |

A scenario is ERROR when promptfoo exits with a code other than 0 or 100, the output file is missing, a test has a provider error, or a judge call failed.

`sonnet` points at newer models over time, so `summary.md` names the model that answered. Compare scores across runs only when the model matches.

Thresholds are starting points. Calibrate after the first few runs.

## Running the Distinctness Scorer

After an eval run, score inter-persona distinctness (needs `OPENAI_API_KEY`; not part of the verdict):

```bash
.venv/bin/python scorers/distinctness.py output/runs/<run id>/persona-panel__pricing-page.json
```

Adjust the similarity threshold (default 0.92):

```bash
.venv/bin/python scorers/distinctness.py output/runs/<run id>/persona-panel__pricing-page.json --threshold 0.90
```

## Running Tests

```bash
cd e2e
npm test
```

Tests mock git and promptfoo, so they make no Claude calls.
