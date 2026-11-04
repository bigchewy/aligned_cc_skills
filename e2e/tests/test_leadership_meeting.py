"""Tests for the leadership-meeting skill: entry point and template."""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "leadership-meeting"

# One lowercase word per line, in a git-ignored file. This repo is public, and a hash of a
# short name can be reversed, so neither the words nor their hashes go in a tracked file.
# Without the file, the name check covers only BANNED_PHRASES.
LOCAL_BANNED_WORDS = Path(__file__).resolve().parent / ".banned-words.local"
BANNED_PHRASES = ("lex sisney",)
TEMPLATE_BANNED = ("asana", "linear", "granola", "portfolio", "subtask", "not tracking",
                   "soapbox", "24 hours")


def _local_banned_words(path: Path = LOCAL_BANNED_WORDS) -> frozenset:
    if not path.exists():
        return frozenset()
    return frozenset(line.strip().lower() for line in path.read_text().splitlines() if line.strip())


def _banned_hits(text: str, words=None) -> list:
    """Return the words in text that are on the list, plus any banned phrase."""
    words = _local_banned_words() if words is None else words
    lowered = text.lower()
    hits = [phrase for phrase in BANNED_PHRASES if phrase in lowered]
    hits += [word for word in set(re.findall(r"[a-z]+", lowered)) if word in words]
    return hits


def _template() -> str:
    return (SKILL_DIR / "template.md").read_text()


def test_skill_frontmatter_name_matches_folder():
    text = (SKILL_DIR / "SKILL.md").read_text()
    assert text.startswith("---\n")
    frontmatter = text.split("---\n")[1]
    data = yaml.safe_load(frontmatter)
    assert data["name"] == "leadership-meeting"
    assert data["description"].startswith("Use when a leadership team wants to set up")


def test_template_has_five_steps_in_order():
    text = _template()
    headings = [
        "### 1. Set the stage",
        "### 2. Progress review",
        "### 3. Prioritize",
        "### 4. Work the questions to answer",
        "### 5. Close",
    ]
    positions = [text.index(h) for h in headings]
    assert positions == sorted(positions)
    assert "### 6." not in text


def test_template_says_90_minutes_and_a_day_before():
    text = _template()
    assert "90 minutes" in text
    assert "A day before the meeting" in text


def test_template_has_no_banned_words():
    text = _template().lower()
    for word in TEMPLATE_BANNED:
        assert word not in text, word
    assert not re.search(r"\bT[12]\b", _template())


def test_template_has_off_strategy_row_and_dashboard_link():
    text = _template()
    assert "| Off strategy |" in text
    assert "[link]" in text


def test_template_ten_rules_are_intact_and_unattributed():
    text = _template()
    rules = re.findall(r"^(\d+)\. ", text.split("## Ten rules")[1].split("## Roles")[0], re.M)
    assert rules == [str(n) for n in range(1, 11)]
    assert "Respect the time." in text


def test_banned_word_check_catches_a_listed_word():
    stand_in = frozenset({"zebra"})
    assert _banned_hits("The Zebra's call.", stand_in) == ["zebra"]
    assert _banned_hits("A zebras call.", stand_in) == []


def test_local_word_list_is_read_and_may_be_absent(tmp_path):
    assert _local_banned_words(tmp_path / "missing") == frozenset()
    listed = tmp_path / "words"
    listed.write_text("Zebra\n\n  okapi \n")
    assert _local_banned_words(listed) == frozenset({"zebra", "okapi"})


def test_local_word_list_is_git_ignored():
    assert ".banned-words.local" in (REPO_ROOT / ".gitignore").read_text()


def test_banned_phrase_check_catches_the_phrase():
    assert _banned_hits("Taken from Lex Sisney's book.") == ["lex sisney"]


def test_no_file_for_this_skill_names_a_client():
    scenarios = REPO_ROOT / "e2e" / "scenarios"
    files = [
        *SKILL_DIR.rglob("*.md"),
        *(REPO_ROOT / "frameworks" / "leadership-meeting").rglob("*.md"),
        *(REPO_ROOT / "e2e" / "tests" / "fixtures" / "leadership_meeting").rglob("*.md"),
        scenarios / "use-framework" / "leadership-meeting.yaml",
        scenarios / "use-skill" / "leadership-meeting-update.yaml",
        scenarios / "use-skill" / "leadership-meeting-feedback.yaml",
        REPO_ROOT / "docs" / "superpowers" / "plans" / "2026-11-03-leadership-meeting.md",
    ]
    assert len(files) >= 13
    for path in files:
        assert _banned_hits(path.read_text()) == [], path


def test_plan_carries_no_meeting_id_and_points_to_the_spec():
    plan = (REPO_ROOT / "docs" / "superpowers" / "plans"
            / "2026-11-03-leadership-meeting.md").read_text()
    assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", plan)
    assert "the test reads the list from a git-ignored local file" in plan
    assert "The Nov 3 test" in plan


def test_skill_is_in_the_root_readme():
    assert "/aligned:leadership-meeting" in (REPO_ROOT / "README.md").read_text()


def _update() -> str:
    return (SKILL_DIR / "weekly-update.md").read_text()


def _tool() -> str:
    return (SKILL_DIR / "team-tool.md").read_text()


def test_update_job_has_the_seven_steps():
    text = _update()
    steps = ["Brain dump", "Last week's commitments", "Status", "Vague words",
             "New commitments", "Questions to answer", "Draft"]
    positions = []
    start = 0
    for step in steps:
        pos = text.index(step, start)
        positions.append(pos)
        start = pos + 1
    assert positions == sorted(positions)


def test_update_job_has_a_paste_path():
    assert "paste" in _update().lower()


def test_update_job_never_cuts_voice_loose():
    assert "advisors/prompts" not in _update()


def test_update_form_is_not_redefined():
    assert "template.md" in _update()


def test_tool_table_has_all_eight_rows():
    text = _tool()
    for row in ("Home", "Key action", "Written update", "Action item",
                "Question to answer", "Agenda", "Key decision", "Parking lot"):
        assert f"| {row}" in text, row


def test_tool_mapping_has_no_hard_coded_tool_name():
    assert "mcp__" not in _tool()


def test_tool_mapping_says_no_owner_set():
    assert "never sets an owner" in _tool().lower()


FIXTURE_DIR = REPO_ROOT / "e2e" / "tests" / "fixtures" / "leadership_meeting"


def _feedback() -> str:
    return (SKILL_DIR / "meeting-feedback.md").read_text()


def _section(text: str, heading: str) -> str:
    return text.split(f"\n## {heading}\n")[1].split("\n## ")[0]


def test_feedback_job_names_seven_checks():
    text = _feedback()
    checks = ["Agenda in a shared place before the meeting",
              "Decision maker and facilitator named, and the facilitator is not the CEO",
              "Status answered fast", "Due action items reviewed",
              "Questions in order before they are worked",
              "Every fix tied to an obstacle", "Close"]
    start = 0
    for number, check in enumerate(checks, start=1):
        row = f"| {number} | {check} |"
        assert row in text[start:], row
        start = text.index(row, start) + 1


def test_feedback_defines_each_result():
    text = _feedback()
    for result in ("Met", "Partly", "Missed", "Can't tell", "Not in use"):
        assert result in text, result


def test_feedback_has_two_documents():
    text = _feedback()
    assert "Team page" in text
    assert "Private note" in text


def test_feedback_never_reads_a_dashboard():
    assert "never opens a dashboard" in _feedback().lower()


def test_feedback_accepts_paste_for_each_input():
    text = _feedback()
    for heading in ("Inputs", "Last time"):
        assert "paste" in _section(text, heading).lower(), heading


def test_feedback_inputs_name_the_previous_team_page():
    assert "previous team page" in _section(_feedback(), "Inputs").lower()


def test_feedback_has_no_hard_coded_tool_name():
    assert "mcp__" not in _feedback()


def test_feedback_check_3_describes_the_talk_after_the_answer():
    text = _feedback()
    assert "the talk after the first direct answer" in text
    assert "Don't call it noise" in text


def test_feedback_check_6_lists_every_fix_before_counting():
    text = _feedback()
    assert "List every proposed fix with its time before you count" not in text
    assert ("Before you count, write the fix list in the chat summary, each with its time "
            "and whether it names an obstacle.") in text
    assert "An obstacle named only after the fix doesn't count" in text
    assert "each time someone sent the team back to obstacles" in text
    assert "the check 6 fix list" in text.split("### Chat summary")[1]


DEFINITIONS = {
    "**Leader:**": "Check 2's CEO rule means this person when nobody holds that title.",
    "**Check 1:**": "an agenda given to you for grading doesn't show it was shared",
    "**Date:**": "The next call, the next meeting, next week, soon and later are not dates",
    "**Commitment:**": "A suggestion, or saying the team should do it, isn't one.",
    "**Direct answer:**": "yes, no or a color on whether the key action is on track",
    "**Check 3 across key actions:**": "give the check the worst result",
    "**Top item:**": "With no such statement, use the first item.",
    "**Finished:**": "Sending the item's own work to after the meeting",
    "**Where fixes count:**": "Talk inside a status answer isn't counted.",
    "**Fix:**": "These aren't fixes: work already under way or already planned",
    "**Repeated fix:**": "one idea counts once, at its first mention",
    "**Names an obstacle:**": "The problem restated, a benefit of the fix",
    "**Send-back:**": "Repeats inside one push count once.",
    "**Figures from later talk:**": "these never replace a measured time",
}


def test_feedback_defines_each_grading_term():
    section = _section(_feedback(), "Definitions for grading")
    for label, words in DEFINITIONS.items():
        assert f"- {label}" in section, label
        assert words in section, label


def test_feedback_definitions_follow_the_check_reports():
    text = _feedback()
    assert text.index("Each check also reports") < text.index("## Definitions for grading")
    assert text.index("## Definitions for grading") < text.index("## The two documents")


def test_feedback_check_6_missed_covers_send_backs_and_homework():
    assert ("| Under half do, or someone sent the team back to obstacles twice or more and it "
            "kept proposing fixes without listing them, or the obstacle list ended up as work "
            "after the meeting. |") in _feedback()


def test_feedback_names_appear_only_as_implementers():
    text = _feedback()
    assert "A name appears only as an implementer, when the words themselves name the person." in text
    assert "attendee list" not in text


def test_feedback_window_message_names_the_leader():
    assert "Say who you take as the leader, in the same message." in _feedback()


def test_feedback_team_page_form_handles_no_times():
    assert "With no times, write: Positions are line numbers." in _feedback()


def test_feedback_no_times_missed_rule_is_for_teams_not_using_the_template():
    text = _feedback()
    assert "For a team not using the template, only no date at all can still be Missed." in text
    assert "Only no date at all can still be Missed" not in text


def test_feedback_stops_without_a_transcript():
    assert "Without a transcript, stop." in _feedback()


def test_feedback_saves_the_confirmed_page_with_the_warning():
    text = _feedback()
    step_8 = text.split("\n8. ")[1].split("\n## ")[0]
    assert "team pages folder" in step_8
    assert "git repo" in step_8
    assert step_8.index("confirms") < step_8.index("Save")
    assert "team pages folder named in `leadership-meeting.md`" in _section(text, "Inputs")
    assert "team pages folder named in `leadership-meeting.md`" in _section(text, "Last time")


def test_feedback_bans_quotation_marks_in_both_documents():
    text = (SKILL_DIR / "meeting-feedback.md").read_text()
    rule_1 = text.split("## Rules for the evidence")[1].split("\n2. ")[0]
    assert "No quotation marks in either document" in rule_1
    assert "the next call" in rule_1


def test_feedback_job_text_models_no_quotation_marks():
    assert '"' not in (SKILL_DIR / "meeting-feedback.md").read_text()


def test_feedback_checks_for_quotation_marks_before_showing_the_work():
    text = (SKILL_DIR / "meeting-feedback.md").read_text()
    step_7 = text.split("\n7. Write the team page")[1].split("**WAIT")[0]
    assert "remove every quotation mark" in step_7
    assert "your reply" in step_7


def test_feedback_gives_set_wording_for_a_missing_date():
    text = (SKILL_DIR / "meeting-feedback.md").read_text()
    date = text.split("- **Date:**")[1].split("\n- **")[0]
    assert "write that no calendar date was set, and don't repeat the words they used" in date


def test_feedback_says_what_check_3_reports_with_no_times():
    text = (SKILL_DIR / "meeting-feedback.md").read_text()
    rule_5 = text.split("\n5. A transcript with no times")[1].split("\n6. ")[0]
    assert "for each key action" in rule_5
    assert "share of the meeting's words" in rule_5
    assert "first direct answer" in rule_5


def test_setup_warns_before_saving_settings_into_git():
    text = (REPO_ROOT / "frameworks" / "leadership-meeting" / "prompt.md").read_text()
    phase_9 = text.split("### PHASE 9: Close")[1]
    assert "Warn the person before saving into a git repo at a path that isn't ignored." in phase_9


def test_setup_refuses_dashboard_links_with_a_token():
    text = (REPO_ROOT / "frameworks" / "leadership-meeting" / "prompt.md").read_text()
    phase_3 = text.split("### PHASE 3:")[1].split("### PHASE 4:")[0]
    assert "key or token" in phase_3


def test_setup_records_the_team_pages_folder():
    phase_9 = _prompt().split("### PHASE 9: Close")[1].split("## Artifact")[0]
    assert "team pages folder" in phase_9


def test_feedback_written_updates_have_two_meanings():
    inputs = _section(_feedback(), "Inputs")
    assert "Updates nobody posted make check 3 Missed." in inputs
    assert "Updates that exist but weren't given to you make the written part Can't tell." in inputs


def test_update_only_step_1_always_waits():
    text = _update()
    for start, end in (("### 2. ", "### 3. "), ("### 3. ", "### 4. "), ("### 4. ", "### 5. ")):
        step = text.split(start)[1].split(end)[0]
        assert "**If you asked, WAIT for the person to respond.**" in step, start
    step_1 = text.split("### 1. ")[1].split("### 2. ")[0]
    assert "**WAIT for the person to respond.**" in step_1


def test_update_all_green_counts_a_vague_word_as_not_all_green():
    section = _section(_update(), "An all-green week")
    assert "A vague word with no Definition line makes the week not all green for this purpose" in section


def test_update_voice_line_is_ask_once_push_once():
    text = _update()
    assert "Ask once, and push once if the answer dodges. Then record what they said." in text
    assert "Push once per item" not in text


def _scenario(name: str) -> dict:
    return yaml.safe_load((REPO_ROOT / "e2e" / "scenarios" / "use-skill" / name).read_text())


def _scenario_tests(name: str, prefix: str) -> list:
    tests = [t for t in _scenario(name)["tests"] if t["description"].startswith(prefix)]
    assert tests, prefix
    return tests


def _rubric(test: dict) -> str:
    return test["assert"][0]["value"]


def test_update_scenario_walks_a_whole_all_green_week():
    tests = _scenario_tests("leadership-meeting-update.yaml", "update-i")
    assert len(tests) >= 3
    joined = " ".join(_rubric(t) for t in tests)
    for stop in ("brain dump", "new commitments", "approv"):
        assert stop in joined.lower(), stop


def test_update_scenario_stops_for_a_vague_word_in_a_green_week():
    test = _scenario_tests("leadership-meeting-update.yaml", "update-j")[0]
    assert "Definition" in test["vars"]["scenario_description"] or "promising" in _rubric(test)


def test_both_transcripts_hold_a_commitment_by_the_next_call():
    for name in ("transcript.md", "transcript-no-times.md"):
        assert "by the next call" in (FIXTURE_DIR / name).read_text(), name


def test_both_transcripts_say_the_same_words():
    timed = re.sub(r"^\[\d+:\d+\] ", "", (FIXTURE_DIR / "transcript.md").read_text(), flags=re.M)
    assert timed == (FIXTURE_DIR / "transcript-no-times.md").read_text()


def test_feedback_scenario_pins_the_next_call_failure():
    rubric = _rubric(_scenario_tests("leadership-meeting-feedback.yaml", "feedback-j")[0])
    for words in ("check 1", "check 5", "check 7", "next call"):
        assert words in rubric, words


def test_feedback_scenario_pins_send_backs():
    test = _scenario_tests("leadership-meeting-feedback.yaml", "feedback-k")[0]
    assert "sent the team back" in _rubric(test) or "send-back" in _rubric(test).lower()
    assert "obstacles" in test["vars"]["transcript"]


def test_feedback_scenario_keeps_later_commitments_out_of_the_action_table():
    rubric = _rubric(_scenario_tests("leadership-meeting-feedback.yaml", "feedback-l")[0])
    assert "Action items heard" in rubric
    assert "Friday" in rubric and "Thursday" in rubric


def test_feedback_g_keeps_the_instruction_out_of_both_documents():
    rubric = _rubric(_scenario_tests("leadership-meeting-feedback.yaml", "feedback-g")[0])
    assert "both documents" in rubric
    assert "chat summary" in rubric


def test_feedback_i_tally_ignores_the_repeated_fix():
    rubric = _rubric(_scenario_tests("leadership-meeting-feedback.yaml", "feedback-i")[0])
    assert "23:55" in rubric


def test_trigger_map_runs_feedback_when_the_template_changes():
    data = yaml.safe_load((REPO_ROOT / "e2e" / "trigger-map.yaml").read_text())
    text = yaml.safe_dump(data)
    assert "template.md" in text
    entries = []

    def walk(node):
        if isinstance(node, dict):
            if "paths" in node and "scenarios" in node:
                entries.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    feedback = next(e for e in entries
                    if "scenarios/use-skill/leadership-meeting-feedback.yaml" in e["scenarios"])
    assert "skills/leadership-meeting/template.md" in feedback["paths"]


def test_skill_checks_for_the_prompt_before_the_runner():
    setup = _section((SKILL_DIR / "SKILL.md").read_text(), "Setup")
    assert "parent of `skills/`" in setup
    assert setup.index("prompt.md") < setup.index("framework-runner.md")


FRAMEWORK_DIR = REPO_ROOT / "frameworks" / "leadership-meeting"


def _prompt() -> str:
    return (FRAMEWORK_DIR / "prompt.md").read_text()


def _registry_entry() -> dict:
    data = yaml.safe_load((REPO_ROOT / "frameworks" / "registry.yaml").read_text())
    return next(e for e in data["frameworks"] if e["id"] == "leadership-meeting")


def test_registry_entry():
    entry = _registry_entry()
    assert entry["advisor"] == "matt-mochary"
    assert entry["deliverable_type"] == "plan"
    assert not entry.get("required_documents")
    helpful = {d["from"] for d in entry["helpful_documents"]}
    assert helpful == {"kernel-of-good-strategy", "proximate-objectives", "outside"}


def test_placed_in_operating_rhythm_without_changing_start():
    layers = yaml.safe_load((REPO_ROOT / "skills" / "playbook" / "layers.yaml").read_text())
    areas = [a for layer in layers["layers"] for a in layer["areas"]]
    area = next(a for a in areas if a["id"] == "operating-rhythm")
    assert "leadership-meeting" in area["frameworks"]
    assert area["start"] == "mochary-weekly-check-in"


def test_on_the_coo_seat():
    seats = yaml.safe_load((REPO_ROOT / "skills" / "org-chart" / "seats.yaml").read_text())
    coo = next(s for s in seats["seats"] if s["id"] == "coo")
    assert "leadership-meeting" in [j.get("framework") for j in coo["jobs"]]


def test_setup_stops_for_each_input():
    assert _prompt().count("**WAIT") >= 8


def test_setup_reads_the_template_from_the_skill():
    assert "skills/leadership-meeting/template.md" in _prompt()


def test_setup_never_invents_key_actions():
    assert "never invent" in _prompt().lower()


def test_setup_writes_through_the_tool_file_and_settings_file():
    text = _prompt()
    assert "skills/leadership-meeting/team-tool.md" in text
    assert "leadership-meeting.md" in text


def test_setup_explains_where_skills_paths_start():
    assert ("Paths starting with `skills/` are relative to the plugin root, the parent of the "
            "`frameworks/` folder that holds this prompt.") in _prompt()


def test_setup_holds_the_meeting_at_90_minutes():
    text = _prompt()
    assert "60" not in text
    assert "90" in text.split("If they want it shorter:")[1].split("**WAIT")[0]


def test_setup_sends_feedback_only_requests_to_the_skill():
    phase_1 = _prompt().split("### PHASE 1: Who Attends")[1].split("### PHASE 2")[0]
    assert "only want" in phase_1
    assert "/aligned:leadership-meeting" in phase_1


def test_setup_drops_the_old_labels_branch():
    text = _prompt()
    assert "soapbox" not in text.lower()
    assert not re.search(r"\bT[12]\b", text)
    anti = (FRAMEWORK_DIR / "anti-examples.md").read_text()
    assert "soapbox" not in anti.lower()
    assert not re.search(r"\bT[12]\b", anti)


def test_setup_never_hard_codes_a_full_tool_name():
    assert "Never hard-code a full tool name." in _prompt()


def test_setup_date_check_is_about_time_for_updates():
    text = _prompt()
    assert "If the date leaves no time for updates a day before" in text
    assert "under three days" not in text


def test_example_keeps_key_action_4_in_a_project_or_on_the_agenda():
    text = (FRAMEWORK_DIR / "examples.md").read_text()
    assert "single task in the home" not in text
    assert "keeps its own project" in text
    assert "stays on the agenda with no task" in text
