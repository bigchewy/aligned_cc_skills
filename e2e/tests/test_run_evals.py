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
    matches_surface,
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


def test_child_env_drops_dotenv_pointers_always():
    base = {"DOTENV_PATH": "/x/.env", "DOTENV_CONFIG_PATH": "/y/.env", "PATH": "/bin"}
    for use_key in (False, True):
        env = child_env(use_key, base)
        assert "DOTENV_PATH" not in env
        assert "DOTENV_CONFIG_PATH" not in env


def test_child_env_points_promptfoo_at_an_empty_dotenv_file(tmp_path):
    empty = tmp_path / "empty.env"
    env = child_env(False, {"DOTENV_PATH": "/x/.env"}, empty_env_file=empty)
    assert env["DOTENV_PATH"] == str(empty)
    assert "DOTENV_CONFIG_PATH" not in env


def test_child_env_drops_routing_vars_unless_api_key_wanted():
    base = {"ANTHROPIC_AUTH_TOKEN": "t", "ANTHROPIC_BASE_URL": "http://x", "ANTHROPIC_API_KEY": "k"}
    env = child_env(False, base)
    assert "ANTHROPIC_AUTH_TOKEN" not in env
    assert "ANTHROPIC_BASE_URL" not in env
    env = child_env(True, base)
    assert env["ANTHROPIC_AUTH_TOKEN"] == "t"
    assert env["ANTHROPIC_BASE_URL"] == "http://x"


def test_promptfoo_command(tmp_path):
    cmd = promptfoo_command(STEVE, tmp_path / "x.json", tmp_path / "empty.env")
    assert cmd[0].endswith("node_modules/.bin/promptfoo")
    assert cmd[1:] == [
        "eval", "-c", STEVE, "-o", str(tmp_path / "x.json"),
        "--env-file", str(tmp_path / "empty.env"),
        "--max-concurrency", "2", "--no-cache", "--no-write", "--no-progress-bar",
    ]


def test_main_creates_empty_env_file_and_passes_it(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    fake = FakeRun(outputs={STEVE: promptfoo_output([("full-stack", 4.5), ("vanilla", 2.0)])})
    monkeypatch.setenv("DOTENV_PATH", "/elsewhere/.env")
    main(["e2e/" + STEVE], run=fake)
    cmd, kwargs = fake.promptfoo_calls[0]
    run_dir = next(tmp_path.iterdir())
    empty = run_dir / "empty.env"
    assert empty.read_text() == ""
    assert cmd[cmd.index("--env-file") + 1] == str(empty)
    assert kwargs["env"]["DOTENV_PATH"] == str(empty)


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


def test_flat_advisor_prompt_without_trigger_is_unmapped():
    sel = select_scenarios(["advisors/prompts/new-advisor.md"], TRIGGERS, PATTERNS)
    assert sel.unmapped == ["advisors/prompts/new-advisor.md"]


def test_matches_surface_double_star_matches_zero_or_more_directories():
    assert matches_surface("advisors/prompts/a/b.md", "advisors/prompts/**/*")
    assert matches_surface("advisors/prompts/new-advisor.md", "advisors/prompts/**/*")


def test_matches_surface_single_star_stays_in_one_directory():
    assert matches_surface("frameworks/x/prompt.md", "frameworks/*/prompt.md")
    assert not matches_surface("frameworks/x/y/prompt.md", "frameworks/*/prompt.md")


def test_matches_surface_exact_path_matches_itself():
    assert matches_surface("skills/use-advisor/SKILL.md", "skills/use-advisor/SKILL.md")


PASSING = [("full-stack", 4.5), ("vanilla", 2.0)]
RUN_ID = "20261012-130000"


def make_run_dir(tmp_path, scenarios, saved):
    run_dir = tmp_path / RUN_ID
    run_dir.mkdir()
    (run_dir / "scenarios.json").write_text(json.dumps(scenarios))
    for scenario, data in saved.items():
        (run_dir / output_name(scenario)).write_text(json.dumps(data))
    return run_dir


def test_resume_reruns_scenario_whose_saved_output_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    make_run_dir(tmp_path, [STEVE, GINO], {
        STEVE: promptfoo_output([("full-stack", 0), ("vanilla", 0)], error="provider crashed"),
        GINO: promptfoo_output(PASSING),
    })
    fake = FakeRun(outputs={STEVE: promptfoo_output(PASSING)})
    assert main(["--resume", RUN_ID], run=fake) == 0
    assert [c[0][c[0].index("-c") + 1] for c in fake.promptfoo_calls] == [STEVE]


def test_resume_call_count_ignores_scenarios_that_will_not_run(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    make_run_dir(tmp_path, [STEVE, GINO], {STEVE: promptfoo_output(PASSING), GINO: promptfoo_output(PASSING)})
    fake = FakeRun()
    assert main(["--resume", RUN_ID], run=fake) == 0
    assert "about 0 Claude calls" in capsys.readouterr().out
    assert fake.promptfoo_calls == []


def test_resume_call_count_counts_errored_saved_outputs(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    make_run_dir(tmp_path, [STEVE, GINO], {
        STEVE: promptfoo_output([("full-stack", 0), ("vanilla", 0)], error="boom"),
        GINO: promptfoo_output(PASSING),
    })
    main(["--resume", RUN_ID], run=FakeRun(outputs={STEVE: promptfoo_output(PASSING)}))
    assert f"about {estimate_calls([STEVE])} Claude calls" in capsys.readouterr().out


def test_summary_after_rate_limit_stop_names_unrun_scenarios_and_resume_command(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(run_evals, "all_scenarios", lambda: [GINO, STEVE])
    limited = FakeRun(outputs={
        GINO: promptfoo_output(PASSING),
        STEVE: promptfoo_output([("full-stack", 0), ("vanilla", 0)], error="You've hit your limit"),
    })
    assert main(["--all"], run=limited) == 2
    run_dir = next(tmp_path.iterdir())
    text = (run_dir / "summary.md").read_text()
    head = text.split("| Scenario |")[0]
    assert "rate limit" in text.splitlines()[0]
    assert STEVE in head
    assert GINO not in head
    assert f"npm run eval -- --resume {run_dir.name}" in head


def many_scenarios():
    return run_evals.all_scenarios()[:11]


def patch_selection(monkeypatch, scenarios):
    monkeypatch.setattr(run_evals, "changed_files", lambda base, run=None: ["x"])
    monkeypatch.setattr(
        run_evals, "select_scenarios", lambda *a: Selection(scenarios=scenarios, shared_changed=[], unmapped=[])
    )
    monkeypatch.setattr(run_evals, "load_triggers", lambda: [])
    monkeypatch.setattr(run_evals, "load_patterns", lambda: [])


def test_large_changed_files_selection_needs_yes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    scenarios = many_scenarios()
    assert len(scenarios) == 11
    patch_selection(monkeypatch, scenarios)
    fake = FakeRun()
    assert main([], run=fake) == 2
    out = capsys.readouterr().out
    assert "11 scenarios" in out
    assert "Pass --yes to run them, or name scenarios" in out
    assert fake.promptfoo_calls == []
    assert list(tmp_path.iterdir()) == []


def test_large_changed_files_selection_runs_with_yes(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    patch_selection(monkeypatch, many_scenarios())
    fake = FakeRun()
    main(["--yes"], run=fake)
    assert len(fake.promptfoo_calls) == 11


def test_ten_scenario_changed_files_selection_runs_without_yes(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS_DIR", tmp_path)
    patch_selection(monkeypatch, many_scenarios()[:10])
    fake = FakeRun()
    main([], run=fake)
    assert len(fake.promptfoo_calls) == 10
