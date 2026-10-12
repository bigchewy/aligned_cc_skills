# Evals Through the Claude Code Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every promptfoo eval in `e2e/` runs through the Claude Code login, and `npm run eval` runs only the scenarios touched by changed files.

**Architecture:** One shared provider file (`anthropic:claude-agent-sdk` on the login) and one shared plain-text judge prompt (1 to 5 scale) that every scenario references. A Python runner (`e2e/run_evals.py`) picks scenarios from changed files through `e2e/trigger-map.yaml`, runs promptfoo once per scenario with `ANTHROPIC_API_KEY` and `CLAUDE_PID` removed from the child env, and a scorer (`e2e/scorers/scenario_verdict.py`) turns each promptfoo JSON output into PASS, FAIL, or ERROR.

**Tech Stack:** promptfoo 0.124.1, @anthropic-ai/claude-agent-sdk 0.3.283, Node 22, Python 3 with PyYAML and pytest in `e2e/.venv`.

**Spec:** `docs/superpowers/specs/2026-10-12-evals-through-login-design.md`

## Global Constraints

- promptfoo pinned to exactly `0.124.1`; `@anthropic-ai/claude-agent-sdk` pinned to exactly `0.3.283`; `engines.node` is `>=22.22.0`.
- Provider config, verbatim: `id: anthropic:claude-agent-sdk`, `config: { apiKeyRequired: false, model: sonnet, custom_system_prompt: "", tools: [], max_turns: 1 }`.
- Scenario references, verbatim: `file://../../providers/claude-login.yaml` and `file://../../providers/rubric-prompt.txt`.
- Test kind labels: `full-stack`, `vanilla`, `aware`, `single`, stored at `tests[].metadata.arm`.
- Verdict bars: full-stack average >= 3.5; full-stack minus vanilla >= 1.0; full-stack minus aware >= 0.5 when an aware test exists; routing (`single`) scenarios pass when every test averages >= 3.5.
- promptfoo exit codes 0 and 100 mean "it ran". Any other exit code is ERROR.
- Runner concurrency: `--max-concurrency 2` and `PROMPTFOO_ASSERTIONS_MAX_CONCURRENCY=2`.
- With no arguments the runner never runs more than the scenarios mapped from changed files. Running everything takes `--all`.
- Never run an eval that calls a model during this build. Tests mock git and promptfoo. The controller runs the one real scenario after the build.
- Run Python from `e2e/` as `.venv/bin/python`. The system Python has no PyYAML.
- Documents follow `~/.claude/brand-voice.md`: no em dashes or en dashes in prose.
- Plugin version goes from `0.33.36` to `0.33.37` in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

## Review Focus

1. A shell that has `ANTHROPIC_API_KEY` set: the eval must still use the login. Pinned by `test_child_env_removes_api_key_and_claude_pid` (Task 3).
2. promptfoo exiting 100 because vanilla tests failed their rubrics: the scenario must be scored, not marked ERROR. Pinned by `test_exit_100_is_scored_not_error` (Task 3).
3. A judge call that errors: promptfoo scores it 0. The verdict must be ERROR, not a low-score FAIL. Pinned by `test_judge_error_is_error` (Task 2).
4. A changed file that is a deleted scenario: the runner must skip it, not crash. Pinned by `test_deleted_scenario_is_skipped` (Task 3).
5. A rate-limit error halfway through: the run stops, the partial output for that scenario is removed, and `--resume` reruns it. Pinned by `test_rate_limit_stops_run_and_resume_reruns_it` (Task 3).

---

### Task 1: Shared provider, judge prompt, pinned packages, and all 58 scenarios migrated

**Files:**
- Create: `e2e/providers/claude-login.yaml`
- Create: `e2e/providers/rubric-prompt.txt`
- Create (then delete in Step 7): `e2e/scripts/migrate_scenarios.py`
- Modify: every file under `e2e/scenarios/**/*.yaml` (58 files)
- Modify: `e2e/package.json`, `e2e/package-lock.json`
- Test: `e2e/tests/test_eval_scenario_config.py`

**Interfaces:**
- Produces: the two shared files at the paths above; every scenario test carries `metadata.arm`; `e2e/package.json` script `eval` is `.venv/bin/python run_evals.py` (the runner arrives in Task 3).

- [ ] **Step 1: Write the failing test**

Create `e2e/tests/test_eval_scenario_config.py`:

```python
"""Every eval scenario runs through the shared Claude Code login provider and judge prompt."""
import json
from pathlib import Path

import pytest
import yaml

E2E = Path(__file__).resolve().parents[1]
SCENARIOS = sorted((E2E / "scenarios").rglob("*.yaml"))
PROVIDER_REF = "file://../../providers/claude-login.yaml"
RUBRIC_REF = "file://../../providers/rubric-prompt.txt"
ARMS = {"full-stack", "vanilla", "aware", "single"}


def _ids(path):
    return str(path.relative_to(E2E))


def _load(path):
    return yaml.safe_load(path.read_text())


def test_all_scenarios_found():
    assert len(SCENARIOS) >= 58


def test_shared_provider_file():
    provider = yaml.safe_load((E2E / "providers" / "claude-login.yaml").read_text())
    assert provider == {
        "id": "anthropic:claude-agent-sdk",
        "config": {
            "apiKeyRequired": False,
            "model": "sonnet",
            "custom_system_prompt": "",
            "tools": [],
            "max_turns": 1,
        },
    }


def test_shared_rubric_prompt_is_plain_text_on_a_1_to_5_scale():
    text = (E2E / "providers" / "rubric-prompt.txt").read_text()
    assert "{{ output }}" in text
    assert "{{ rubric }}" in text
    assert "1 to 5" in text
    with pytest.raises(json.JSONDecodeError):
        json.loads(text)


def test_package_pins():
    pkg = json.loads((E2E / "package.json").read_text())
    assert pkg["devDependencies"]["promptfoo"] == "0.124.1"
    assert pkg["devDependencies"]["@anthropic-ai/claude-agent-sdk"] == "0.3.283"
    assert pkg["engines"]["node"] == ">=22.22.0"
    assert pkg["scripts"]["eval"] == ".venv/bin/python run_evals.py"


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_scenario_uses_shared_provider(path):
    assert _load(path)["providers"] == [PROVIDER_REF]
    assert (path.parent / "../../providers/claude-login.yaml").resolve().is_file()


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_judge_uses_shared_provider_and_prompt(path):
    options = _load(path)["defaultTest"]["options"]
    assert options["provider"] == PROVIDER_REF
    assert options["rubricPrompt"] == RUBRIC_REF


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_scenario_never_names_the_api_provider(path):
    assert "anthropic:messages" not in path.read_text()


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_every_test_has_a_kind_label(path):
    for test in _load(path)["tests"]:
        assert (test.get("metadata") or {}).get("arm") in ARMS, test.get("description")


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_paired_scenarios_have_one_full_stack_and_one_vanilla(path):
    arms = [t["metadata"]["arm"] for t in _load(path)["tests"]]
    if "single" in arms:
        assert set(arms) == {"single"}
    else:
        assert arms.count("full-stack") == 1
        assert arms.count("vanilla") == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `e2e/`): `.venv/bin/python -m pytest tests/test_eval_scenario_config.py -q`
Expected: FAIL, first with `FileNotFoundError` for `providers/claude-login.yaml`.

- [ ] **Step 3: Write the shared files**

`e2e/providers/claude-login.yaml`:

```yaml
# Shared promptfoo provider for every eval scenario: the model under test and the
# llm-rubric judge. Runs through the `claude` CLI on the Claude Code login, not
# ANTHROPIC_API_KEY. run_evals.py removes ANTHROPIC_API_KEY from the environment,
# because this provider would otherwise pass it to the SDK and bill the API.
id: anthropic:claude-agent-sdk
config:
  apiKeyRequired: false
  model: sonnet
  custom_system_prompt: ""
  tools: []
  max_turns: 1
```

`e2e/providers/rubric-prompt.txt`:

```
You are grading an answer against one rubric. The rubric names a quality and describes what low and high scores look like on a scale of 1 to 5.

Read the answer. Decide its score as a whole number from 1 to 5, using the rubric's own description of each level.

Reply with only a JSON object and no other text:
{"reason": "one or two sentences", "score": 3, "pass": false}

Set "pass" to true when the score is 4 or 5, and false otherwise.

<Output>
{{ output }}
</Output>
<Rubric>
{{ rubric }}
</Rubric>
```

- [ ] **Step 4: Pin the packages**

Replace `e2e/package.json` with:

```json
{
  "name": "aligned-evals",
  "version": "0.1.0",
  "private": true,
  "description": "Eval framework for Aligned plugin skills",
  "engines": {
    "node": ">=22.22.0"
  },
  "scripts": {
    "eval": ".venv/bin/python run_evals.py",
    "view": "promptfoo view",
    "test": ".venv/bin/python -m pytest tests/ -v",
    "test:scorer": ".venv/bin/python -m pytest tests/test_distinctness.py -v"
  },
  "devDependencies": {
    "@anthropic-ai/claude-agent-sdk": "0.3.283",
    "promptfoo": "0.124.1"
  }
}
```

Run (from `e2e/`): `npm install`
Expected: installs without error and rewrites `package-lock.json`. Then run `npx promptfoo --version` and expect `0.124.1`.

- [ ] **Step 5: Write the one-time migration script**

`e2e/scripts/migrate_scenarios.py` edits text in place so comments and the folded rubric blocks survive:

```python
"""One-time migration: point every scenario at the shared login provider and judge
prompt, and label each test with its kind. Deleted after it runs."""
import re
import sys
from pathlib import Path

E2E = Path(__file__).resolve().parents[1]
PROVIDER_BLOCK = "providers:\n  - file://../../providers/claude-login.yaml\n\n"
OPTIONS_BLOCK = (
    "  options:\n"
    "    provider: file://../../providers/claude-login.yaml\n"
    "    rubricPrompt: file://../../providers/rubric-prompt.txt\n"
)
DESCRIPTION = re.compile(r'^(  - description: "?)(.*?)("?)\s*$')


def arm_for(description):
    d = description.lower()
    if d.startswith(("full-stack", "with-skill")):
        return "full-stack"
    if d.startswith(("vanilla", "without-skill")):
        return "vanilla"
    if d.startswith("aware-but-unaided"):
        return "aware"
    return "single"


def migrate(text):
    lines = text.splitlines(keepends=True)
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("providers:"):
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                i += 1
            out.append(PROVIDER_BLOCK)
            continue
        out.append(line)
        if line.rstrip() == "defaultTest:":
            out.append(OPTIONS_BLOCK)
        match = DESCRIPTION.match(line)
        if match:
            out.append(f"    metadata:\n      arm: {arm_for(match.group(2))}\n")
        i += 1
    return "".join(out)


def main():
    paths = sorted((E2E / "scenarios").rglob("*.yaml"))
    for path in paths:
        path.write_text(migrate(path.read_text()))
    print(f"migrated {len(paths)} scenarios")


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run the migration and the test**

Run (from `e2e/`): `.venv/bin/python scripts/migrate_scenarios.py`
Expected: `migrated 58 scenarios`.

Run: `.venv/bin/python -m pytest tests/test_eval_scenario_config.py -q`
Expected: all pass.

Then open `scenarios/use-advisor/steve-blank-consult.yaml` and `scenarios/use-skill/always-ask-routing.yaml` and check by eye: the `providers` block is one line, `defaultTest` starts with the `options` block and keeps its `assert` list, and each test has its `metadata.arm` line. Run `git diff --stat` and expect 58 scenario files changed.

Then validate that promptfoo can load every scenario without calling a model. Run (from `e2e/`): `npx promptfoo validate -c scenarios/use-advisor/steve-blank-consult.yaml`
Expected: the config validates. If `validate` is not a command in this version, skip this check and say so in your report.

- [ ] **Step 7: Delete the script and commit**

The script was never committed, so delete it from disk:

```bash
rm -r e2e/scripts
```

Then commit:

```bash
git add e2e/providers e2e/scenarios e2e/package.json e2e/package-lock.json e2e/tests/test_eval_scenario_config.py
git commit -m "feat(e2e): run every scenario through the Claude Code login provider"
```

(End every commit message in this plan with the `Co-Authored-By` line from the session. Use plain `-m`, never a heredoc.)

---

### Task 2: Scenario verdict scorer

**Files:**
- Create: `e2e/scorers/scenario_verdict.py`
- Test: `e2e/tests/test_scenario_verdict.py`

**Interfaces:**
- Produces:
  - `RATE_LIMIT_MARKERS: tuple[str, ...]`
  - `@dataclass Verdict(verdict: str, reason: str, full_stack: float | None = None, gap_vanilla: float | None = None, gap_aware: float | None = None, model: str = "unknown", rate_limited: bool = False)`; `verdict` is one of `"PASS"`, `"FAIL"`, `"ERROR"`.
  - `score_results(results: list[dict]) -> Verdict`
  - `score_file(path: Path | str) -> Verdict`

promptfoo's `-o out.json` file has the shape `{"results": {"results": [EvaluateResult, ...]}, ...}`. Each EvaluateResult has `testCase` (with `description` and `metadata`), `error` (string or null), `failureReason` (0 none, 1 assert, 2 error), `score`, `gradingResult` (`score`, `componentResults`, each with `pass`, `score`, `reason`, `metadata`), and `response` (with `metadata`). A failed judge call shows up as a component result with `metadata.graderError` true and score 0.

- [ ] **Step 1: Write the failing tests**

Create `e2e/tests/test_scenario_verdict.py`:

```python
import json

from scorers.scenario_verdict import Verdict, score_file, score_results


def result(arm, score, description=None, error=None, failure_reason=0, components=None, model=None):
    response = {"metadata": {"modelUsage": {model: {}}}} if model else {}
    return {
        "testCase": {"description": description or arm, "metadata": {"arm": arm}},
        "error": error,
        "failureReason": failure_reason,
        "score": score,
        "gradingResult": {"score": score, "componentResults": components or []},
        "response": response,
    }


def test_paired_pass():
    v = score_results([result("full-stack", 4.5, model="claude-sonnet-x"), result("vanilla", 2.0), result("aware", 3.0)])
    assert v.verdict == "PASS"
    assert v.full_stack == 4.5
    assert v.gap_vanilla == 2.5
    assert v.gap_aware == 1.5
    assert v.model == "claude-sonnet-x"


def test_paired_fails_when_full_stack_below_3_5():
    v = score_results([result("full-stack", 3.25), result("vanilla", 1.0)])
    assert v.verdict == "FAIL"
    assert "full-stack 3.25 below 3.5" in v.reason


def test_paired_fails_when_vanilla_gap_below_1():
    v = score_results([result("full-stack", 4.0), result("vanilla", 3.5)])
    assert v.verdict == "FAIL"
    assert "vanilla gap 0.50 below 1.0" in v.reason


def test_paired_fails_when_aware_gap_below_0_5():
    v = score_results([result("full-stack", 4.0), result("vanilla", 2.0), result("aware", 3.75)])
    assert v.verdict == "FAIL"
    assert "aware gap 0.25 below 0.5" in v.reason


def test_paired_without_aware_ignores_that_bar():
    v = score_results([result("full-stack", 4.0), result("vanilla", 2.5)])
    assert v.verdict == "PASS"
    assert v.gap_aware is None


def test_routing_pass_and_fail():
    assert score_results([result("single", 4.0), result("single", 3.5)]).verdict == "PASS"
    v = score_results([result("single", 4.0, "a"), result("single", 3.0, "b")])
    assert v.verdict == "FAIL"
    assert "1 of 2 tests below 3.5" in v.reason


def test_judge_error_is_error():
    judge_failed = {"pass": False, "score": 0, "reason": "Could not parse JSON", "metadata": {"graderError": True}}
    v = score_results([result("full-stack", 4.0, components=[judge_failed]), result("vanilla", 1.0)])
    assert v.verdict == "ERROR"
    assert "judge failed" in v.reason


def test_provider_error_is_error():
    v = score_results([result("full-stack", 0, error="spawn claude ENOENT", failure_reason=2), result("vanilla", 1.0)])
    assert v.verdict == "ERROR"
    assert "spawn claude ENOENT" in v.reason
    assert v.rate_limited is False


def test_rate_limit_error_is_flagged():
    v = score_results([result("full-stack", 0, error="Claude AI usage limit reached", failure_reason=2)])
    assert v.verdict == "ERROR"
    assert v.rate_limited is True


def test_missing_kind_label_is_error():
    bad = result("full-stack", 4.0)
    bad["testCase"]["metadata"] = {}
    v = score_results([bad, result("vanilla", 1.0)])
    assert v.verdict == "ERROR"
    assert "kind label" in v.reason


def test_paired_without_vanilla_is_error():
    assert score_results([result("full-stack", 4.0)]).verdict == "ERROR"


def test_empty_results_is_error():
    assert score_results([]).verdict == "ERROR"


def test_score_file_reads_promptfoo_output(tmp_path):
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"results": {"results": [result("single", 4.0)]}}))
    assert score_file(path).verdict == "PASS"


def test_score_file_missing_file_is_error(tmp_path):
    v = score_file(tmp_path / "nope.json")
    assert v.verdict == "ERROR"
    assert "cannot read promptfoo output" in v.reason


def test_score_file_unreadable_json_is_error(tmp_path):
    path = tmp_path / "out.json"
    path.write_text("{not json")
    assert score_file(path).verdict == "ERROR"


def test_score_file_wrong_shape_is_error(tmp_path):
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"results": []}))
    v = score_file(path)
    assert v.verdict == "ERROR"
    assert "no results list" in v.reason


def test_verdict_defaults():
    assert Verdict("PASS", "").model == "unknown"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `e2e/`): `.venv/bin/python -m pytest tests/test_scenario_verdict.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'scorers.scenario_verdict'`.

- [ ] **Step 3: Write the scorer**

Create `e2e/scorers/scenario_verdict.py`:

```python
"""Turn one promptfoo JSON output file into a PASS, FAIL, or ERROR verdict.

Paired scenarios compare the full-stack answer (Aligned prompt) with the vanilla
and aware-but-unaided answers. Routing scenarios label every test "single" and
have no baseline. Scores are on the 1 to 5 scale set by providers/rubric-prompt.txt.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

ARMS = {"full-stack", "vanilla", "aware", "single"}
FULL_STACK_MIN = 3.5
VANILLA_GAP_MIN = 1.0
AWARE_GAP_MIN = 0.5
SINGLE_MIN = 3.5
ERROR_FAILURE_REASON = 2
RATE_LIMIT_MARKERS = ("rate limit", "rate_limit", "429", "usage limit")


@dataclass
class Verdict:
    verdict: str
    reason: str
    full_stack: float | None = None
    gap_vanilla: float | None = None
    gap_aware: float | None = None
    model: str = "unknown"
    rate_limited: bool = False


def _description(result):
    return (result.get("testCase") or {}).get("description") or result.get("description") or "unnamed test"


def _errors(results):
    errors = []
    for r in results:
        if r.get("error") or r.get("failureReason") == ERROR_FAILURE_REASON:
            errors.append(f"{_description(r)}: {r.get('error') or 'provider error'}")
        for c in (r.get("gradingResult") or {}).get("componentResults") or []:
            if (c.get("metadata") or {}).get("graderError"):
                errors.append(f"{_description(r)}: judge failed: {c.get('reason')}")
    return errors


def _model(results):
    for r in results:
        usage = ((r.get("response") or {}).get("metadata") or {}).get("modelUsage") or {}
        if usage:
            return next(iter(usage))
    return "unknown"


def score_results(results):
    if not results:
        return Verdict("ERROR", "promptfoo output has no test results")
    errors = _errors(results)
    if errors:
        rate_limited = any(m in e.lower() for e in errors for m in RATE_LIMIT_MARKERS)
        return Verdict("ERROR", "; ".join(errors[:3]), rate_limited=rate_limited)

    by_arm = {}
    for r in results:
        arm = ((r.get("testCase") or {}).get("metadata") or {}).get("arm")
        if arm not in ARMS:
            return Verdict("ERROR", f"{_description(r)}: missing or unknown kind label {arm!r}")
        score = (r.get("gradingResult") or {}).get("score", r.get("score"))
        by_arm.setdefault(arm, []).append(float(score))
    model = _model(results)

    if "single" in by_arm:
        if set(by_arm) != {"single"}:
            return Verdict("ERROR", "scenario mixes single tests with paired tests", model=model)
        scores = by_arm["single"]
        low = [s for s in scores if s < SINGLE_MIN]
        avg = round(mean(scores), 2)
        if low:
            reason = f"{len(low)} of {len(scores)} tests below {SINGLE_MIN} (lowest {min(low):.2f})"
            return Verdict("FAIL", reason, full_stack=avg, model=model)
        return Verdict("PASS", "", full_stack=avg, model=model)

    if "full-stack" not in by_arm or "vanilla" not in by_arm:
        return Verdict("ERROR", "paired scenario needs a full-stack test and a vanilla test", model=model)
    full_stack = round(mean(by_arm["full-stack"]), 2)
    gap_vanilla = round(full_stack - mean(by_arm["vanilla"]), 2)
    gap_aware = round(full_stack - mean(by_arm["aware"]), 2) if "aware" in by_arm else None

    failures = []
    if full_stack < FULL_STACK_MIN:
        failures.append(f"full-stack {full_stack:.2f} below {FULL_STACK_MIN}")
    if gap_vanilla < VANILLA_GAP_MIN:
        failures.append(f"vanilla gap {gap_vanilla:.2f} below {VANILLA_GAP_MIN}")
    if gap_aware is not None and gap_aware < AWARE_GAP_MIN:
        failures.append(f"aware gap {gap_aware:.2f} below {AWARE_GAP_MIN}")
    return Verdict(
        "FAIL" if failures else "PASS",
        "; ".join(failures),
        full_stack=full_stack,
        gap_vanilla=gap_vanilla,
        gap_aware=gap_aware,
        model=model,
    )


def score_file(path):
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        return Verdict("ERROR", f"cannot read promptfoo output: {exc}")
    try:
        results = data["results"]["results"]
    except (KeyError, TypeError):
        return Verdict("ERROR", "promptfoo output has no results list")
    if not isinstance(results, list):
        return Verdict("ERROR", "promptfoo output has no results list")
    return score_results(results)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `e2e/`): `.venv/bin/python -m pytest tests/test_scenario_verdict.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add e2e/scorers/scenario_verdict.py e2e/tests/test_scenario_verdict.py
git commit -m "feat(e2e): score a promptfoo run as PASS, FAIL, or ERROR"
```

---

### Task 3: The runner

**Files:**
- Create: `e2e/run_evals.py`
- Test: `e2e/tests/test_run_evals.py`

**Interfaces:**
- Consumes: `score_file`, `Verdict`, `RATE_LIMIT_MARKERS` from `scorers.scenario_verdict` (Task 2); `e2e/trigger-map.yaml` (shape: `triggers: [{paths: [repo-relative], scenarios: [e2e-relative]}]`); `e2e/eval-surface.yaml` (shape: `patterns: [glob]`).
- Produces (all in `run_evals`):
  - `SHARED_FILES: set[str]` of repo-relative paths
  - `changed_files(base: str, run=subprocess.run) -> list[str]`
  - `@dataclass Selection(scenarios: list[str], shared_changed: list[str], unmapped: list[str])`
  - `select_scenarios(changed: list[str], triggers: list[dict], patterns: list[str]) -> Selection`
  - `estimate_calls(scenarios: list[str]) -> int`
  - `child_env(use_api_key: bool, base_env: dict) -> dict`
  - `promptfoo_command(scenario: str, out_path: Path) -> list[str]`
  - `output_name(scenario: str) -> str`
  - `run_scenario(scenario: str, run_dir: Path, env: dict, run=subprocess.run) -> Verdict`
  - `main(argv: list[str], run=subprocess.run) -> int`

Scenario paths inside the runner are e2e-relative, like `scenarios/use-advisor/steve-blank-consult.yaml`, which is how `trigger-map.yaml` writes them.

- [ ] **Step 1: Write the failing tests**

Create `e2e/tests/test_run_evals.py`:

```python
import json
import subprocess
from pathlib import Path

import pytest

import run_evals
from run_evals import (
    Selection,
    child_env,
    changed_files,
    estimate_calls,
    main,
    output_name,
    promptfoo_command,
    run_scenario,
    select_scenarios,
)

STEVE = "scenarios/use-advisor/steve-blank-consult.yaml"
GINO = "scenarios/use-advisor/gino-wickman-consult.yaml"
TRIGGERS = [
    {"paths": ["advisors/prompts/steve-blank.md"], "scenarios": [STEVE]},
    {"paths": ["advisors/prompts/gino-wickman.md"], "scenarios": [GINO]},
]
PATTERNS = ["advisors/prompts/**/*", "frameworks/*/prompt.md"]


def done(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def promptfoo_output(arms_and_scores, error=None):
    results = []
    for arm, score in arms_and_scores:
        results.append({
            "testCase": {"description": arm, "metadata": {"arm": arm}},
            "error": error,
            "failureReason": 2 if error else 0,
            "score": score,
            "gradingResult": {"score": score, "componentResults": []},
        })
    return {"results": {"results": results}}


class FakeRun:
    """Stands in for subprocess.run. Git calls return canned output; promptfoo calls
    write the output file named after -o and return the given exit code."""

    def __init__(self, git_lines=None, outputs=None, exit_code=0, raise_on_promptfoo=None):
        self.git_lines = git_lines or {}
        self.outputs = outputs or {}
        self.exit_code = exit_code
        self.raise_on_promptfoo = raise_on_promptfoo
        self.promptfoo_calls = []

    def __call__(self, cmd, **kwargs):
        if cmd[0] == "git":
            key = " ".join(cmd[1:])
            return done(stdout="\n".join(self.git_lines.get(key, [])))
        self.promptfoo_calls.append((cmd, kwargs))
        if self.raise_on_promptfoo:
            raise self.raise_on_promptfoo
        scenario = cmd[cmd.index("-c") + 1]
        out = Path(cmd[cmd.index("-o") + 1])
        if scenario in self.outputs:
            out.write_text(json.dumps(self.outputs[scenario]))
        return done(returncode=self.exit_code)


def test_changed_files_merges_branch_uncommitted_and_untracked():
    fake = FakeRun(git_lines={
        "diff --name-only main...HEAD": ["advisors/prompts/steve-blank.md"],
        "diff --name-only HEAD": ["README.md", "advisors/prompts/steve-blank.md"],
        "ls-files --others --exclude-standard": ["frameworks/new/prompt.md"],
    })
    assert changed_files("main", run=fake) == [
        "README.md",
        "advisors/prompts/steve-blank.md",
        "frameworks/new/prompt.md",
    ]


def test_changed_files_raises_when_git_fails():
    def failing(cmd, **kwargs):
        raise subprocess.CalledProcessError(128, cmd, stderr="fatal: bad revision 'nope...HEAD'")

    with pytest.raises(subprocess.CalledProcessError):
        changed_files("nope", run=failing)


def test_select_maps_changed_prompt_to_its_scenario():
    sel = select_scenarios(["advisors/prompts/steve-blank.md", "README.md"], TRIGGERS, PATTERNS)
    assert sel == Selection(scenarios=[STEVE], shared_changed=[], unmapped=[])


def test_changed_scenario_file_runs_itself():
    sel = select_scenarios(["e2e/" + GINO], TRIGGERS, PATTERNS)
    assert sel.scenarios == [GINO]


def test_deleted_scenario_is_skipped():
    sel = select_scenarios(["e2e/scenarios/use-advisor/deleted-advisor.yaml"], TRIGGERS, PATTERNS)
    assert sel.scenarios == []


def test_shared_file_change_runs_nothing_and_is_reported():
    sel = select_scenarios(["e2e/providers/rubric-prompt.txt"], TRIGGERS, PATTERNS)
    assert sel.scenarios == []
    assert sel.shared_changed == ["e2e/providers/rubric-prompt.txt"]


def test_unmapped_surface_file_is_reported():
    sel = select_scenarios(["frameworks/brand-new/prompt.md"], TRIGGERS, PATTERNS)
    assert sel.unmapped == ["frameworks/brand-new/prompt.md"]
    assert sel.scenarios == []


def test_estimate_calls_counts_answers_and_judge_calls():
    # steve-blank-consult has 3 tests and 4 rubrics: 3 * (1 + 4) = 15
    assert estimate_calls([STEVE]) == 15


def test_child_env_removes_api_key_and_claude_pid():
    env = child_env(False, {"ANTHROPIC_API_KEY": "sk-x", "CLAUDE_PID": "123", "PATH": "/bin"})
    assert "ANTHROPIC_API_KEY" not in env
    assert "CLAUDE_PID" not in env
    assert env["PATH"] == "/bin"
    assert env["PROMPTFOO_ASSERTIONS_MAX_CONCURRENCY"] == "2"


def test_child_env_keeps_api_key_only_when_asked():
    env = child_env(True, {"ANTHROPIC_API_KEY": "sk-x", "CLAUDE_PID": "123"})
    assert env["ANTHROPIC_API_KEY"] == "sk-x"
    assert "CLAUDE_PID" not in env


def test_promptfoo_command(tmp_path):
    cmd = promptfoo_command(STEVE, tmp_path / "x.json")
    assert cmd[0].endswith("node_modules/.bin/promptfoo")
    assert cmd[1:] == [
        "eval", "-c", STEVE, "-o", str(tmp_path / "x.json"),
        "--max-concurrency", "2", "--no-cache", "--no-write", "--no-progress-bar",
    ]


def test_output_name():
    assert output_name(STEVE) == "use-advisor__steve-blank-consult.json"


def test_exit_0_is_scored(tmp_path):
    fake = FakeRun(outputs={STEVE: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)])})
    assert run_scenario(STEVE, tmp_path, {}, run=fake).verdict == "PASS"


def test_exit_100_is_scored_not_error(tmp_path):
    fake = FakeRun(outputs={STEVE: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)])}, exit_code=100)
    assert run_scenario(STEVE, tmp_path, {}, run=fake).verdict == "PASS"


def test_other_exit_code_is_error(tmp_path):
    fake = FakeRun(outputs={STEVE: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)])}, exit_code=1)
    v = run_scenario(STEVE, tmp_path, {}, run=fake)
    assert v.verdict == "ERROR"
    assert "exited 1" in v.reason


def test_promptfoo_not_starting_is_error(tmp_path):
    fake = FakeRun(raise_on_promptfoo=FileNotFoundError("node_modules/.bin/promptfoo"))
    v = run_scenario(STEVE, tmp_path, {}, run=fake)
    assert v.verdict == "ERROR"
    assert "did not start" in v.reason


def test_run_passes_child_env_and_cwd(tmp_path):
    fake = FakeRun(outputs={STEVE: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)])})
    run_scenario(STEVE, tmp_path, {"PATH": "/bin"}, run=fake)
    _, kwargs = fake.promptfoo_calls[0]
    assert kwargs["env"] == {"PATH": "/bin"}
    assert kwargs["cwd"] == run_evals.E2E


def test_main_with_no_mapped_changes_runs_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    fake = FakeRun(git_lines={"diff --name-only HEAD": ["README.md"]})
    assert main([], run=fake) == 0
    assert fake.promptfoo_calls == []
    assert "Nothing to run" in capsys.readouterr().out


def test_main_runs_only_mapped_scenarios(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(run_evals, "load_triggers", lambda: TRIGGERS)
    fake = FakeRun(
        git_lines={"diff --name-only HEAD": ["advisors/prompts/steve-blank.md"]},
        outputs={STEVE: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)])},
    )
    assert main([], run=fake) == 0
    assert [c[0][c[0].index("-c") + 1] for c in fake.promptfoo_calls] == [STEVE]
    run_dir = next(tmp_path.iterdir())
    assert "PASS" in (run_dir / "summary.md").read_text()


def test_main_named_scenario_accepts_repo_relative_path(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    fake = FakeRun(outputs={STEVE: promptfoo_output([("full-stack", 3.0), ("vanilla", 2.5)])})
    assert main(["e2e/" + STEVE], run=fake) == 1


def test_main_unknown_scenario_is_usage_error(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    assert main(["scenarios/nope.yaml"], run=FakeRun()) == 2


def test_main_all_runs_every_scenario(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(run_evals, "all_scenarios", lambda: [STEVE, GINO])
    fake = FakeRun(outputs={
        STEVE: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)]),
        GINO: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)]),
    })
    assert main(["--all"], run=fake) == 0
    assert len(fake.promptfoo_calls) == 2
    assert "about" in capsys.readouterr().out


def test_rate_limit_stops_run_and_resume_reruns_it(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(run_evals, "all_scenarios", lambda: [STEVE, GINO])
    limited = FakeRun(outputs={
        STEVE: promptfoo_output([("full-stack", 0), ("vanilla", 0)], error="Claude AI usage limit reached"),
        GINO: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)]),
    })
    assert main(["--all"], run=limited) == 2
    assert len(limited.promptfoo_calls) == 1
    run_dir = next(tmp_path.iterdir())
    assert not (run_dir / output_name(STEVE)).exists()

    recovered = FakeRun(outputs={
        STEVE: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)]),
        GINO: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)]),
    })
    assert main(["--resume", run_dir.name], run=recovered) == 0
    assert len(recovered.promptfoo_calls) == 2


def test_resume_skips_finished_scenarios(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    run_dir = tmp_path / "20261012-120000"
    run_dir.mkdir()
    (run_dir / "scenarios.json").write_text(json.dumps([STEVE, GINO]))
    (run_dir / output_name(STEVE)).write_text(json.dumps(promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)])))
    fake = FakeRun(outputs={GINO: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)])})
    assert main(["--resume", "20261012-120000"], run=fake) == 0
    assert [c[0][c[0].index("-c") + 1] for c in fake.promptfoo_calls] == [GINO]


def test_resume_unknown_run_is_usage_error(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    assert main(["--resume", "nope"], run=FakeRun()) == 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `e2e/`): `.venv/bin/python -m pytest tests/test_run_evals.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_evals'`.

- [ ] **Step 3: Write the runner**

Create `e2e/run_evals.py`:

```python
"""Run promptfoo eval scenarios through the Claude Code login.

From e2e/:
  npm run eval                          scenarios mapped from changed files
  npm run eval -- <scenario.yaml> ...   named scenarios
  npm run eval -- --all                 every scenario (ask the user first)
  npm run eval -- --resume <run id>     finish a stopped run

Exit codes: 0 all passed or nothing to run, 1 a scenario failed or errored,
2 usage error or the run stopped on a rate limit.
"""
import argparse
import datetime
import fnmatch
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from scorers.scenario_verdict import RATE_LIMIT_MARKERS, Verdict, score_file

E2E = Path(__file__).resolve().parent
REPO = E2E.parent
RUNS_DIR = E2E / "output" / "runs"
PROMPTFOO = E2E / "node_modules" / ".bin" / "promptfoo"
SHARED_FILES = {"e2e/providers/claude-login.yaml", "e2e/providers/rubric-prompt.txt"}
OK_EXIT_CODES = {0, 100}


@dataclass
class Selection:
    scenarios: list
    shared_changed: list
    unmapped: list


def all_scenarios():
    return sorted(str(p.relative_to(E2E)) for p in (E2E / "scenarios").rglob("*.yaml"))


def load_triggers():
    return yaml.safe_load((E2E / "trigger-map.yaml").read_text())["triggers"]


def load_patterns():
    return yaml.safe_load((E2E / "eval-surface.yaml").read_text())["patterns"]


def changed_files(base, run=subprocess.run):
    commands = [
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    files = set()
    for cmd in commands:
        proc = run(cmd, cwd=REPO, capture_output=True, text=True, check=True)
        files.update(line.strip() for line in proc.stdout.splitlines() if line.strip())
    return sorted(files)


def select_scenarios(changed, triggers, patterns):
    picked, shared, unmapped = set(), [], []
    for path in changed:
        if path in SHARED_FILES:
            shared.append(path)
            continue
        if path.startswith("e2e/scenarios/") and path.endswith(".yaml"):
            picked.add(path[len("e2e/"):])
            continue
        hits = [t for t in triggers if path in t["paths"]]
        for trigger in hits:
            picked.update(trigger["scenarios"])
        if not hits and any(fnmatch.fnmatch(path, p) for p in patterns):
            unmapped.append(path)
    scenarios = sorted(s for s in picked if (E2E / s).is_file())
    return Selection(scenarios=scenarios, shared_changed=shared, unmapped=unmapped)


def estimate_calls(scenarios):
    total = 0
    for scenario in scenarios:
        data = yaml.safe_load((E2E / scenario).read_text())
        rubrics = len((data.get("defaultTest") or {}).get("assert") or [])
        total += len(data.get("tests") or []) * (1 + rubrics)
    return total


def child_env(use_api_key, base_env):
    env = dict(base_env)
    env.pop("CLAUDE_PID", None)
    if not use_api_key:
        env.pop("ANTHROPIC_API_KEY", None)
    env["PROMPTFOO_ASSERTIONS_MAX_CONCURRENCY"] = "2"
    return env


def output_name(scenario):
    return scenario.removeprefix("scenarios/").removesuffix(".yaml").replace("/", "__") + ".json"


def promptfoo_command(scenario, out_path):
    return [
        str(PROMPTFOO), "eval", "-c", scenario, "-o", str(out_path),
        "--max-concurrency", "2", "--no-cache", "--no-write", "--no-progress-bar",
    ]


def run_scenario(scenario, run_dir, env, run=subprocess.run):
    out = run_dir / output_name(scenario)
    try:
        proc = run(promptfoo_command(scenario, out), cwd=E2E, env=env, capture_output=True, text=True)
    except OSError as exc:
        return Verdict("ERROR", f"promptfoo did not start: {exc}")
    if proc.returncode not in OK_EXIT_CODES:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:] or ["no output"]
        rate_limited = any(m in (proc.stderr or "").lower() for m in RATE_LIMIT_MARKERS)
        return Verdict("ERROR", f"promptfoo exited {proc.returncode}: {tail[0]}", rate_limited=rate_limited)
    return score_file(out)


def _fmt(value):
    return "" if value is None else f"{value:.2f}"


def write_summary(run_dir, rows):
    models = sorted({v.model for _, v in rows if v.model != "unknown"}) or ["unknown"]
    lines = [
        f"# Eval run {run_dir.name}",
        "",
        f"Model: {', '.join(models)}",
        "",
        "| Scenario | Verdict | Full-stack | Gap vs vanilla | Gap vs aware | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for scenario, v in rows:
        lines.append(
            f"| {scenario} | {v.verdict} | {_fmt(v.full_stack)} | {_fmt(v.gap_vanilla)} "
            f"| {_fmt(v.gap_aware)} | {v.reason} |"
        )
    text = "\n".join(lines) + "\n"
    (run_dir / "summary.md").write_text(text)
    return text


def _normalize(path):
    path = path.removeprefix("e2e/")
    return path if (E2E / path).is_file() and path.startswith("scenarios/") else None


def _parse(argv):
    parser = argparse.ArgumentParser(prog="npm run eval --", description=__doc__.splitlines()[0])
    parser.add_argument("scenarios", nargs="*", help="scenario files to run")
    parser.add_argument("--all", action="store_true", help="run every scenario")
    parser.add_argument("--resume", metavar="RUN_ID", help="finish a stopped run")
    parser.add_argument("--base", default="main", help="branch to compare against (default main)")
    parser.add_argument("--use-api-key", action="store_true", help="keep ANTHROPIC_API_KEY for contributors with no Claude Code login")
    return parser.parse_args(argv)


def main(argv, run=subprocess.run):
    args = _parse(argv)
    if sum([bool(args.scenarios), args.all, bool(args.resume)]) > 1:
        print("Pick one: scenario paths, --all, or --resume.")
        return 2

    if args.resume:
        run_dir = RUNS_DIR / args.resume
        if not (run_dir / "scenarios.json").is_file():
            print(f"No run named {args.resume} in {RUNS_DIR}.")
            return 2
        scenarios = json.loads((run_dir / "scenarios.json").read_text())
    else:
        if args.all:
            scenarios = all_scenarios()
        elif args.scenarios:
            scenarios = [_normalize(p) for p in args.scenarios]
            if None in scenarios:
                bad = [p for p, s in zip(args.scenarios, scenarios) if s is None]
                print(f"Not a scenario file: {', '.join(bad)}")
                return 2
        else:
            try:
                changed = changed_files(args.base, run=run)
            except subprocess.CalledProcessError as exc:
                print(f"git failed: {(exc.stderr or '').strip()}")
                return 2
            sel = select_scenarios(changed, load_triggers(), load_patterns())
            for path in sel.shared_changed:
                print(f"{path} changed. It affects every scenario. Run `npm run eval -- --all` if you want all of them.")
            if sel.unmapped:
                print(f"{len(sel.unmapped)} changed prompt files have no scenario in trigger-map.yaml: {', '.join(sel.unmapped)}")
            scenarios = sel.scenarios
            if not scenarios:
                print("No changed files map to an eval scenario. Nothing to run.")
                return 0
        run_dir = RUNS_DIR / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "scenarios.json").write_text(json.dumps(scenarios, indent=2))

    print(f"Run {run_dir.name}: {len(scenarios)} scenarios, about {estimate_calls(scenarios)} Claude calls.")
    env = child_env(args.use_api_key, os.environ)
    rows = []
    for scenario in scenarios:
        out = run_dir / output_name(scenario)
        if out.is_file():
            verdict = score_file(out)
        else:
            print(f"Running {scenario}")
            verdict = run_scenario(scenario, run_dir, env, run=run)
        if verdict.rate_limited:
            out.unlink(missing_ok=True)
            print(f"Stopped on a rate limit at {scenario}: {verdict.reason}")
            print(f"Resume later with: npm run eval -- --resume {run_dir.name}")
            write_summary(run_dir, rows)
            return 2
        rows.append((scenario, verdict))

    print(write_summary(run_dir, rows))
    return 0 if all(v.verdict == "PASS" for _, v in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `e2e/`): `.venv/bin/python -m pytest tests/test_run_evals.py tests/test_scenario_verdict.py -q`
Expected: all pass.

- [ ] **Step 5: Check the real selection without calling a model**

Run (from `e2e/`): `.venv/bin/python -c "import run_evals as r; print(r.select_scenarios(['advisors/prompts/steve-blank.md'], r.load_triggers(), r.load_patterns()))"`
Expected: a Selection whose scenarios include `scenarios/use-advisor/steve-blank-consult.yaml`.

- [ ] **Step 6: Commit**

```bash
git add e2e/run_evals.py e2e/tests/test_run_evals.py
git commit -m "feat(e2e): runner that evals only scenarios touched by changed files"
```

---

### Task 4: Remove the broken master config and rewrite the eval README

**Files:**
- Delete: `e2e/promptfooconfig.yaml`
- Delete: `e2e/tests/test_trigger_map_scenarios.py`
- Modify: `e2e/README.md` (full rewrite below)
- Modify: `e2e/trigger-map.yaml:5` (comment only)

**Interfaces:**
- Consumes: the commands and verdict rules from Tasks 1 to 3.

- [ ] **Step 1: Delete the files**

```bash
git rm e2e/promptfooconfig.yaml e2e/tests/test_trigger_map_scenarios.py
```

- [ ] **Step 2: Fix the trigger-map comment**

In `e2e/trigger-map.yaml`, replace line 5:

```
# Note: scenario paths are e2e/-relative (for promptfoo -c), not repo-root-relative
```

with:

```
# Note: scenario paths are e2e/-relative, not repo-root-relative.
# Consumer: run_evals.py, which runs only the scenarios mapped from changed files.
```

- [ ] **Step 3: Rewrite `e2e/README.md`**

Replace the whole file with:

````markdown
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
````

- [ ] **Step 4: Run the full test suite**

Run (from `e2e/`): `.venv/bin/python -m pytest tests/ -q`
Expected: no failures other than tests that also fail on `main` before this branch. If anything else fails, read the error, fix the cause, and say what you fixed in your report. A reference to `promptfooconfig.yaml` in any test is a failure this task owns.

- [ ] **Step 5: Commit**

```bash
git add e2e/README.md e2e/trigger-map.yaml
git commit -m "docs(e2e): document running evals on the Claude Code login"
```

---

### Task 5: Skills stop treating a missing key as a reason to skip, and version bump

**Files:**
- Modify: `skills/add-advisor/SKILL.md:164-176`
- Modify: `skills/add-framework/SKILL.md:182-197`
- Modify: `skills/eval-audit/SKILL.md:80`
- Modify: `docs/plans/completed/2026-04-09-eval-auto-run.md:440-446`
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
- Test: `e2e/tests/test_eval_skill_instructions.py`

- [ ] **Step 1: Write the failing test**

Create `e2e/tests/test_eval_skill_instructions.py`:

```python
"""Skills that run evals must use the runner when it exists and never skip for a missing key."""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EVAL_SKILLS = ["skills/add-advisor/SKILL.md", "skills/add-framework/SKILL.md"]


@pytest.mark.parametrize("rel", EVAL_SKILLS)
def test_eval_step_uses_runner_when_present(rel):
    text = (REPO / rel).read_text()
    assert "e2e/run_evals.py" in text
    assert "npm run eval -- <scenario-path>" in text
    assert "promptfooconfig.yaml" not in text


@pytest.mark.parametrize("rel", EVAL_SKILLS)
def test_eval_step_never_skips_for_missing_key(rel):
    text = (REPO / rel).read_text()
    assert "Never skip the run because `ANTHROPIC_API_KEY` is not set" in text


def test_eval_audit_does_not_defer_on_credentials():
    text = (REPO / "skills/eval-audit/SKILL.md").read_text()
    assert "missing credentials" not in text
    assert "Claude Code login" in text


def test_versions_match():
    plugin = json.loads((REPO / ".claude-plugin/plugin.json").read_text())["version"]
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())["plugins"][0]["version"]
    assert plugin == market == "0.33.37"
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `e2e/`): `.venv/bin/python -m pytest tests/test_eval_skill_instructions.py -q`
Expected: FAIL on the `e2e/run_evals.py` assertion.

- [ ] **Step 3: Edit add-advisor Step 6**

In `skills/add-advisor/SKILL.md`, replace this paragraph (line 168):

```
If the project has eval infrastructure, create a quick-consult eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format. If `e2e/trigger-map.yaml` exists, add an entry mapping the new advisor prompt path to the new scenario path. If `e2e/promptfooconfig.yaml` exists, add `file://<scenario-path>` to its `scenarios` list.
```

with:

```
If the project has eval infrastructure, create a quick-consult eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format, and copy an existing scenario's provider and options lines exactly. If `e2e/trigger-map.yaml` exists, add an entry mapping the new advisor prompt path to the new scenario path.
```

And replace the paragraph that starts `Run the scenario to verify baseline quality.` (line 176) with:

```
Run the new scenario to verify baseline quality. If `e2e/run_evals.py` exists, run only the new scenario from `e2e/` with `npm run eval -- <scenario-path>`. The runner uses the Claude Code login. Never skip the run because `ANTHROPIC_API_KEY` is not set, and never run `--all` without asking the user. If `e2e/run_evals.py` does not exist, use the project's own eval command. If the scenario fails, classify the failure (prompt issue, eval calibration, or model variance) and fix before continuing. First-run failures are common and usually eval calibration — adjust keywords and fingerprints before changing the voice prompt.
```

- [ ] **Step 4: Edit add-framework Step 6**

In `skills/add-framework/SKILL.md`, replace this paragraph (line 186):

```
If the project has eval infrastructure, create an eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format. If `e2e/trigger-map.yaml` exists, add an entry mapping the new framework file paths (prompt.md, examples.md, anti-examples.md) to the new scenario path. If `e2e/promptfooconfig.yaml` exists, add `file://<scenario-path>` to its `scenarios` list.
```

with:

```
If the project has eval infrastructure, create an eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format, and copy an existing scenario's provider and options lines exactly. If `e2e/trigger-map.yaml` exists, add an entry mapping the new framework file paths (prompt.md, examples.md, anti-examples.md) to the new scenario path.
```

And replace the paragraph that starts `Run the scenario to verify baseline quality.` (line 197) with:

```
Run the new scenario to verify baseline quality. If `e2e/run_evals.py` exists, run only the new scenario from `e2e/` with `npm run eval -- <scenario-path>`. The runner uses the Claude Code login. Never skip the run because `ANTHROPIC_API_KEY` is not set, and never run `--all` without asking the user. If `e2e/run_evals.py` does not exist, use the project's own eval command. If the scenario fails, classify the failure (prompt issue, eval calibration, or model variance) and fix. First-run failures are common — usually eval calibration.
```

(The em dashes in these two paragraphs are existing text in those files; leave them as they are.)

- [ ] **Step 5: Edit eval-audit**

In `skills/eval-audit/SKILL.md`, replace line 80:

```
4. **If the API call can't run** (missing credentials, rate limits, CI environment), file a Kanban entry (see format below) with the specific instruction: "Run one eval pass against [scenario] and document the classification pattern."
```

with:

```
4. **If the eval can't run** (a rate limit, a CI environment with no Claude Code login), file a Kanban entry (see format below) with the specific instruction: "Run one eval pass against [scenario] and document the classification pattern." Evals run on the Claude Code login, so a missing `ANTHROPIC_API_KEY` is never a reason to defer.
```

- [ ] **Step 6: Edit the completed auto-run plan**

In `docs/plans/completed/2026-04-09-eval-auto-run.md`, replace lines 440-446 (from `**1. API key guard.**` through the line ending `Continue to Step 1c. Non-blocking.` that follows the `printenv` block) with:

```
**1. Login, not key.** Superseded on 2026-10-12: evals run through the Claude Code login with `e2e/run_evals.py`, which picks scenarios from changed files. Never skip an eval because `ANTHROPIC_API_KEY` is not set. The skill this plan built was removed on 2026-08-14.
```

Read the lines first to confirm the range covers exactly the key guard step, including its fenced `printenv ANTHROPIC_API_KEY` block.

- [ ] **Step 7: Bump the version**

In `.claude-plugin/plugin.json` change `"version": "0.33.36"` to `"version": "0.33.37"`. In `.claude-plugin/marketplace.json` make the same change.

- [ ] **Step 8: Run the tests**

Run (from `e2e/`): `.venv/bin/python -m pytest tests/ -q`
Expected: the new test passes, and nothing fails that also passed on `main`.

- [ ] **Step 9: Commit**

```bash
git add skills/add-advisor/SKILL.md skills/add-framework/SKILL.md skills/eval-audit/SKILL.md docs/plans/completed/2026-04-09-eval-auto-run.md .claude-plugin/plugin.json .claude-plugin/marketplace.json e2e/tests/test_eval_skill_instructions.py
git commit -m "fix: eval steps use the login runner and never skip for a missing API key"
```

---

### After the tasks (controller, not a subagent)

1. Run `npm run eval -- scenarios/use-advisor/steve-blank-consult.yaml` from `e2e/` in the worktree, with `ANTHROPIC_API_KEY` unset. About 15 Claude calls. Read `summary.md` and one JSON output: confirm the judge returned 1 to 5 scores, `graderError` is absent, and the model name is not `unknown`. Fix anything this shows before finishing.
2. Ask Eric before `npm run eval -- --all`.
