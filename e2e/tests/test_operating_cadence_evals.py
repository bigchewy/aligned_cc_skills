"""Tests for the operating cadence evals: scenario files, the trigger map and the fixtures."""

import re

import yaml

from tests.test_operating_cadence import (
    FIXTURE_DIR,
    REPO_ROOT,
    SEVEN_SKILLS,
    SHARED,
    _banned_hits,
)

E2E = REPO_ROOT / "e2e"
SKILL_SCENARIOS = {name: f"use-skill/{name}.yaml" for name in SEVEN_SKILLS}
FRAMEWORK_SCENARIO = "use-framework/operating-cadence.yaml"
ALL_SCENARIOS = [*SKILL_SCENARIOS.values(), FRAMEWORK_SCENARIO]
SHARED_MD = sorted(p.name for p in SHARED.glob("*.md"))

# The files each scenario must load through file:// vars, so the model sees the same text a
# real session reads. Paths are relative to the scenario file.
_SH = "../../../skills/_shared/operating-cadence/"
_FX = "../../tests/fixtures/operating_cadence/"
EMBEDS = {
    "use-skill/create-wbr.yaml": ["../../../skills/create-wbr/SKILL.md", _SH + "wbr-template.md",
                                  _SH + "team-page.md", _SH + "team-tool.md"],
    "use-skill/wbr-rollup.yaml": ["../../../skills/wbr-rollup/SKILL.md", _SH + "meeting-template.md",
                                  _SH + "wbr-template.md", _SH + "team-page.md",
                                  _SH + "team-tool.md"],
    "use-skill/wbr-recap.yaml": ["../../../skills/wbr-recap/SKILL.md", _SH + "meeting-template.md",
                                 _SH + "team-page.md", _SH + "team-tool.md"],
    "use-skill/wbr-feedback.yaml": ["../../../skills/wbr-feedback/SKILL.md", _SH + "meeting-template.md",
                                    _SH + "team-page.md", _SH + "team-tool.md"],
    "use-skill/monthly-review.yaml": ["../../../skills/monthly-review/SKILL.md", _SH + "team-page.md"],
    "use-skill/quarterly-plan.yaml": ["../../../skills/quarterly-plan/SKILL.md", _SH + "team-page.md"],
    "use-skill/annual-plan.yaml": ["../../../skills/annual-plan/SKILL.md", _SH + "team-page.md"],
    FRAMEWORK_SCENARIO: ["../../../frameworks/operating-cadence/prompt.md",
                         _SH + "meeting-template.md"],
}


def _scenario(name: str) -> dict:
    return yaml.safe_load((E2E / "scenarios" / name).read_text())


def _scenario_tests(name: str, prefix: str) -> list:
    tests = [t for t in _scenario(name)["tests"] if t["description"].startswith(prefix)]
    assert tests, prefix
    return tests


def _rubric(test: dict) -> str:
    return test["assert"][0]["value"]


def _trigger_entries() -> list:
    return yaml.safe_load((E2E / "trigger-map.yaml").read_text())["triggers"]


def _scenarios_for(path: str) -> set:
    return {s.removeprefix("scenarios/") for e in _trigger_entries() if path in e["paths"]
            for s in e["scenarios"]}


def test_every_new_scenario_exists_parses_and_has_rubrics():
    assert len(ALL_SCENARIOS) == 8
    for rel in ALL_SCENARIOS:
        data = _scenario(rel)
        tests = data["tests"]
        assert len(tests) >= 2, rel
        rubrics = [a for t in tests for a in t.get("assert", [])] + data["defaultTest"].get("assert", [])
        assert rubrics, rel
        assert all(a["type"] == "llm-rubric" for a in rubrics), rel


def test_old_scenarios_and_fixtures_are_gone():
    for rel in ("use-framework/leadership-meeting.yaml", "use-skill/leadership-meeting-update.yaml",
                "use-skill/leadership-meeting-feedback.yaml"):
        assert not (E2E / "scenarios" / rel).exists(), rel
    assert not (E2E / "tests" / "fixtures" / "leadership_meeting").exists()


def test_scenarios_load_the_real_skill_and_the_shared_files_it_needs():
    for rel, wanted in EMBEDS.items():
        data = _scenario(rel)
        prompt = data["prompts"][0]
        for test in data["tests"]:
            files = {v.removeprefix("file://") for v in test["vars"].values()
                     if isinstance(v, str) and v.startswith("file://")}
            if test["metadata"]["arm"] != "vanilla":
                missing = [f for f in wanted if f not in files]
                assert not missing, (rel, test["description"], missing)
            for name, value in test["vars"].items():
                if isinstance(value, str) and value.startswith("file://"):
                    path = (E2E / "scenarios" / rel).parent / value.removeprefix("file://")
                    assert path.resolve().is_file(), (rel, value)
                    assert "{{" + name + "}}" in prompt, (rel, name)


def test_no_scenario_or_fixture_names_a_removed_path():
    removed = ("leadership-meeting", "leadership_meeting", "weekly-update.md", "meeting-feedback.md",
               "skills/leadership")
    files = [*(E2E / "scenarios").rglob("*.yaml"), *(E2E / "tests" / "fixtures").rglob("*.md")]
    assert len(files) > 60
    for path in files:
        text = path.read_text()
        for word in removed:
            assert word not in text, (path, word)


def test_no_scenario_or_fixture_names_a_client():
    files = [*(E2E / "scenarios" / rel for rel in ALL_SCENARIOS), *FIXTURE_DIR.glob("*.md")]
    assert len(files) >= 12
    for path in files:
        assert _banned_hits(path.read_text()) == [], path


def test_each_skill_maps_to_its_scenario_in_the_trigger_map():
    for name, scenario in SKILL_SCENARIOS.items():
        assert scenario in _scenarios_for(f"skills/{name}/SKILL.md"), name
    for name in ("prompt.md", "examples.md", "anti-examples.md"):
        assert FRAMEWORK_SCENARIO in _scenarios_for(f"frameworks/operating-cadence/{name}"), name


def test_a_skill_file_runs_its_own_scenario_and_no_other():
    for name, scenario in SKILL_SCENARIOS.items():
        assert _scenarios_for(f"skills/{name}/SKILL.md") == {scenario}, name


def test_each_shared_file_maps_to_every_scenario():
    assert len(SHARED_MD) == 4
    for name in SHARED_MD:
        assert _scenarios_for(f"skills/_shared/operating-cadence/{name}") == set(ALL_SCENARIOS), name


def test_trigger_map_runs_feedback_when_the_meeting_template_changes():
    assert "use-skill/wbr-feedback.yaml" in _scenarios_for(
        "skills/_shared/operating-cadence/meeting-template.md")


def test_eval_surface_lists_each_new_skill_and_the_shared_files():
    patterns = yaml.safe_load((E2E / "eval-surface.yaml").read_text())["patterns"]
    for name in SEVEN_SKILLS:
        assert f"skills/{name}/SKILL.md" in patterns, name
    assert "skills/_shared/operating-cadence/*.md" in patterns
    assert not any("leadership" in p for p in patterns)


# ---------------------------------------------------------------- the page record fixture

def _record_section(path: str) -> str:
    text = (FIXTURE_DIR / "wbrs.md").read_text()
    # A record starts at its own "### <path>" line and runs to the next "### " line. The
    # documents inside it use "## " headings of their own, so those don't end it.
    return text.split(f"\n### {path}\n")[1].split("\n### ")[0]


def test_period_scenarios_are_set_after_the_last_fixture_meeting():
    for name in ("monthly-review", "quarterly-plan", "annual-plan"):
        text = (E2E / "scenarios" / "use-skill" / f"{name}.yaml").read_text()
        assert "Today is 2026-11-12." in text, name
        assert "2026-11-04" not in text, name


def test_recap_scenarios_say_what_the_pre_read_and_decision_log_hold():
    for prefix in ("recap-b", "recap-c"):
        description = _scenario_tests("use-skill/wbr-recap.yaml", prefix)[0]["vars"]["scenario_description"]
        assert "pre-read" in description and "decision log" in description, prefix


def test_scenarios_that_need_the_page_record_load_the_fixture():
    wanted = {
        "use-skill/wbr-rollup.yaml": ("rollup-a", "rollup-b"),
        "use-skill/monthly-review.yaml": ("monthly-a", "monthly-b", "monthly-c"),
        "use-skill/quarterly-plan.yaml": ("quarterly-a", "quarterly-b", "quarterly-c"),
    }
    for rel, prefixes in wanted.items():
        for prefix in prefixes:
            test = _scenario_tests(rel, prefix)[0]
            assert test["vars"]["page_record"] == "file://" + _FX + "wbrs.md", (rel, prefix)


def test_page_record_fixture_holds_a_red_run_and_a_missing_wbr():
    for week in ("W44", "W45", "W46"):
        assert "Red" in _record_section(f"weeks/2026-{week}/wbrs/product"), week
    assert "Red" not in _record_section("weeks/2026-W41/wbrs/product")
    text = (FIXTURE_DIR / "wbrs.md").read_text()
    assert "### weeks/2026-W45/wbrs/support\n" in text
    assert "### weeks/2026-W46/wbrs/support\n" not in text


def test_page_record_fixture_keeps_the_red_item_out_of_every_recap():
    text = (FIXTURE_DIR / "wbrs.md").read_text()
    recaps = re.findall(r"### weeks/2026-W\d+/docs/recap\n(.*?)(?=\n### |\n## decisions\n|\Z)", text, re.S)
    assert len(recaps) >= 4
    for recap in recaps:
        assert "checkout" not in recap.lower()
    assert sum("renewal discount" in r.lower() for r in recaps) >= 2
    decisions = text.split("\n## decisions\n")[1].split("\n## ")[0]
    assert "renewal discount" not in decisions.lower()


def test_page_record_fixture_has_no_recap_for_the_latest_week():
    text = (FIXTURE_DIR / "wbrs.md").read_text()
    assert "weeks/2026-W47" not in text
    assert "### weeks/2026-W46/docs/recap" not in text
    assert "### weeks/2026-W45/docs/recap" in text


# ---------------------------------------------------------------- scenario rubrics

def test_create_wbr_scenario_walks_a_whole_all_green_week():
    tests = _scenario_tests("use-skill/create-wbr.yaml", "create-wbr-i")
    assert [t["description"].split(":")[0] for t in tests] == [
        "create-wbr-i-1", "create-wbr-i-2", "create-wbr-i-3"]
    joined = " ".join(_rubric(t) for t in tests)
    for stop in ("brain dump", "new commitments", "approv"):
        assert stop in joined.lower(), stop


def test_create_wbr_scenario_stops_for_a_vague_word_in_a_green_week():
    test = _scenario_tests("use-skill/create-wbr.yaml", "create-wbr-j")[0]
    assert "Definition" in test["vars"]["scenario_description"] or "promising" in _rubric(test)


def test_create_wbr_scenario_refuses_a_wbr_with_a_required_section_missing():
    test = _scenario_tests("use-skill/create-wbr.yaml", "create-wbr-k")[0]
    rubric = _rubric(test)
    assert "Last week" in rubric and "will not save" in rubric.lower()
    assert "Last week" in test["vars"]["scenario_description"]


def test_create_wbr_scenario_pushes_a_vague_word_once_then_writes_not_defined():
    test = _scenario_tests("use-skill/create-wbr.yaml", "create-wbr-l")[0]
    assert "not defined" in _rubric(test)
    assert "one push" in test["vars"]["scenario_description"].lower()


def test_rollup_scenarios_cover_not_received_the_trend_flag_and_week_one():
    tests = _scenario_tests("use-skill/wbr-rollup.yaml", "rollup-")
    assert len(tests) >= 3
    joined = " ".join(_rubric(t) for t in tests).lower()
    for words in ("not received", "three", "first run, no carry-forward"):
        assert words in joined, words


def test_recap_scenarios_cover_no_notes_and_decisions_with_owner_date_and_code():
    stop = _rubric(_scenario_tests("use-skill/wbr-recap.yaml", "recap-a")[0])
    assert "neither" in stop.lower()
    decisions = _rubric(_scenario_tests("use-skill/wbr-recap.yaml", "recap-b")[0])
    for words in ("owner", "date", "code"):
        assert words in decisions, words


def test_period_scenarios_have_two_or_three_rubrics_each():
    for name in ("monthly-review", "quarterly-plan", "annual-plan"):
        assert 2 <= len(_scenario(f"use-skill/{name}.yaml")["tests"]) <= 3, name


def test_feedback_scenario_carries_all_twelve_checks():
    tests = _scenario("use-skill/wbr-feedback.yaml")["tests"]
    assert [t["description"].split(":")[0] for t in tests] == [f"feedback-{c}" for c in "abcdefghijkl"]


def test_feedback_scenario_pins_the_instruction_line_in_the_transcript():
    assert "31:05" in _rubric(_scenario_tests("use-skill/wbr-feedback.yaml", "feedback-g")[0])
    assert "[31:05]" in (FIXTURE_DIR / "transcript.md").read_text()


def test_feedback_scenario_pins_the_next_call_failure():
    rubric = _rubric(_scenario_tests("use-skill/wbr-feedback.yaml", "feedback-j")[0])
    for words in ("check 1", "check 5", "check 7", "next call"):
        assert words in rubric, words


def test_feedback_scenario_pins_send_backs():
    test = _scenario_tests("use-skill/wbr-feedback.yaml", "feedback-k")[0]
    assert "sent the team back" in _rubric(test) or "send-back" in _rubric(test).lower()
    assert "obstacles" in test["vars"]["transcript"]


def test_feedback_scenario_keeps_later_commitments_out_of_the_action_table():
    rubric = _rubric(_scenario_tests("use-skill/wbr-feedback.yaml", "feedback-l")[0])
    assert "Action items heard" in rubric
    assert "Friday" in rubric and "Thursday" in rubric


def test_feedback_g_keeps_the_instruction_out_of_both_documents():
    rubric = _rubric(_scenario_tests("use-skill/wbr-feedback.yaml", "feedback-g")[0])
    assert "both documents" in rubric
    assert "chat summary" in rubric


def test_feedback_i_tally_ignores_the_repeated_fix():
    assert "23:55" in _rubric(_scenario_tests("use-skill/wbr-feedback.yaml", "feedback-i")[0])


def test_feedback_h_expects_march_2_from_the_previous_team_page():
    test = _scenario_tests("use-skill/wbr-feedback.yaml", "feedback-h")[0]
    assert "March 2" in test["vars"]["previous_team_page"]
    assert "March 2" in _rubric(test)
