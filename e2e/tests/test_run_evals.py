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

    def __init__(self, git_lines=None, outputs=None, exit_code=0, raise_on_promptfoo=None, stderr=""):
        self.git_lines = git_lines or {}
        self.outputs = outputs or {}
        self.exit_code = exit_code
        self.raise_on_promptfoo = raise_on_promptfoo
        self.stderr = stderr
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
        return done(returncode=self.exit_code, stderr=self.stderr)


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


def test_exit_1_with_429_stderr_is_rate_limited_error(tmp_path):
    fake = FakeRun(exit_code=1, stderr="Error: 429 Too Many Requests")
    v = run_scenario(STEVE, tmp_path, {}, run=fake)
    assert v.verdict == "ERROR"
    assert v.rate_limited is True


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
