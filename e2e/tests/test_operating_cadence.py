"""Tests for the operating cadence: shared files and the team page."""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SHARED = REPO_ROOT / "skills" / "_shared" / "operating-cadence"

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


def _read(name: str) -> str:
    return (SHARED / name).read_text()


def _section(text: str, heading: str) -> str:
    return text.split(f"\n## {heading}\n")[1].split("\n## ")[0]


def test_banned_word_check_catches_a_listed_word():
    stand_in = frozenset({"zebra"})
    assert _banned_hits("The Zebra's call.", stand_in) == ["zebra"]
    assert _banned_hits("A zebras call.", stand_in) == []


def test_local_word_list_is_read_and_may_be_absent(tmp_path):
    assert _local_banned_words(tmp_path / "missing") == frozenset()
    listed = tmp_path / "words"
    listed.write_text("Zebra\n\n  okapi \n")
    assert _local_banned_words(listed) == frozenset({"zebra", "okapi"})


def test_banned_phrase_check_catches_the_phrase():
    assert _banned_hits("Taken from Lex Sisney's book.") == ["lex sisney"]


def test_no_shared_file_names_a_client():
    files = sorted(SHARED.iterdir())
    assert len(files) >= 5
    for path in files:
        assert _banned_hits(path.read_text()) == [], path


def test_meeting_template_has_five_steps_in_order():
    text = _read("meeting-template.md")
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


def test_meeting_template_says_90_minutes_and_a_day_before():
    text = _read("meeting-template.md")
    assert "90 minutes" in text
    assert "A day before the meeting" in text


def test_meeting_template_has_no_banned_words():
    text = _read("meeting-template.md")
    for word in TEMPLATE_BANNED:
        assert word not in text.lower(), word
    assert not re.search(r"\bT[12]\b", text)


def test_meeting_template_points_to_the_wbr_form_and_drops_the_written_update():
    text = _read("meeting-template.md")
    day_before = text.split("## A day before the meeting")[1].split("## Agenda")[0]
    assert "wbr-template.md" in day_before
    assert "WBR" in day_before
    assert "Written update" not in text
    assert "written update" not in text.lower()
    assert "STATUS" not in text


def test_meeting_template_keeps_the_ten_rules_and_the_off_strategy_row():
    text = _read("meeting-template.md")
    rules = re.findall(r"^(\d+)\. ", text.split("## Ten rules")[1].split("## Roles")[0], re.M)
    assert rules == [str(n) for n in range(1, 11)]
    assert "Respect the time." in text
    assert "| Off strategy |" in text
    assert "[link]" in text


WBR_SECTIONS = ["STATUS", "METRICS", "LAST WEEK", "THE GOOD", "THE NOT GOOD", "THIS WEEK",
                "QUESTIONS TO ANSWER", "ASKS OF OTHER TEAMS"]


def test_wbr_template_has_every_section():
    text = _read("wbr-template.md")
    form = text.split("```")[1]
    positions = []
    for name in WBR_SECTIONS:
        match = re.search(rf"^{name}$", form, re.M)
        assert match, name
        positions.append(match.start())
    assert positions == sorted(positions)


def test_wbr_template_says_which_sections_are_required():
    text = _read("wbr-template.md")
    assert "Status and Last week are required" in text
    assert "## Saving" in text
    for name in WBR_SECTIONS:
        assert f"## {name.capitalize()}" in text.split("## Saving")[1], name


FIELDS = {
    "settings/team": ["company", "schedule", "purpose", "decisionMaker", "workstreamSource",
                      "dates", "files", "rules"],
    "keyActions/<code>": ["name", "owner", "dashboard", "draft"],
    "workstreams/<id>": ["name", "owner", "codes", "active", "source"],
    "weeks/<week>": ["meetingDate", "facilitator", "noteTaker"],
    "weeks/<week>/wbrs/<id>": ["markdown", "owner", "writtenAt", "statuses"],
    "weeks/<week>/docs/<preread | recap | teampage>": ["markdown", "writtenAt"],
    "decisions/<id>": ["decision", "owner", "date", "code", "week"],
    "reviews/<YYYY-MM>": ["markdown", "writtenAt"],
    "offsites/<YYYY-Qn | YYYY>": ["markdown", "writtenAt"],
}


def test_team_page_lists_every_path_and_field():
    text = _read("team-page.md")
    record = _section(text, "The record on the page")
    for path, fields in FIELDS.items():
        # A table cell writes a pipe inside code as \|
        lines = [line.replace("\\|", "|") for line in record.splitlines()]
        row = next((line for line in lines if line.startswith(f"| `{path}`")), None)
        assert row, path
        for field in fields:
            assert f"`{field}`" in row, (path, field)
    assert "`reviews/" in record
    assert "`offsites/" in record
    for sub in ("code", "color", "due", "moved", "label", "url", "event"):
        assert f"`{sub}`" in record, sub


def test_team_page_template_reads_only_listed_fields():
    html = (SHARED / "team-page-template.html").read_text()
    for path in ("settings/team", "keyActions", "workstreams", "weeks", "decisions", "reviews",
                 "offsites"):
        assert path in html, path
    listed = {field for fields in FIELDS.values() for field in fields}
    listed |= {"code", "color", "due", "moved", "label", "url", "event", "id"}
    for field in ("company", "schedule", "decisionMaker", "workstreamSource", "meetingDate",
                  "facilitator", "noteTaker", "writtenAt", "statuses", "dashboard"):
        assert field in listed, field
        assert field in html, field


def test_team_page_says_how_to_find_the_page():
    text = _read("team-page.md")
    finding = _section(text, "Finding the page")
    assert "operating-cadence.md" in finding
    assert "shared with the person" in finding
    assert "once" in finding
    order = [finding.index("operating-cadence.md"), finding.index("shared with the person"),
             finding.index("once")]
    assert order == sorted(order)


def test_team_page_covers_failed_writes():
    text = _read("team-page.md")
    failure = _section(text, "Writing and failure")
    assert "block" in failure
    assert "Contributor" in failure
    assert "Nothing retries in a different shape" in failure
    assert "mcp__" not in text


def test_team_page_keeps_the_private_note_off_the_page():
    text = _read("team-page.md")
    assert "never written to the page" in text.lower() or "never written here" in text.lower()


def test_team_page_covers_weeks_and_workstream_ids():
    text = _read("team-page.md")
    section = _section(text, "Weeks and workstream ids")
    assert "ISO week" in section
    assert "lower case with hyphens" in section
    assert "a rename keeps the id" in section.lower()


def test_team_page_template_cleans_shared_text():
    html = (SHARED / "team-page-template.html").read_text()
    assert "DOMPurify.sanitize" in html
    scripts = re.findall(r"<script\b[^>]*\bsrc=[^>]*>", html)
    assert len(scripts) == 2
    for tag in scripts:
        assert "integrity=" in tag, tag


def test_team_page_template_has_paste_form():
    assert 'id="wbr-form"' in (SHARED / "team-page-template.html").read_text()


def test_team_page_template_has_a_title_and_no_client_name():
    html = (SHARED / "team-page-template.html").read_text()
    assert "<title>Weekly Review</title>" in html
    assert _banned_hits(html) == []


def test_team_tool_has_every_row_and_the_workstream_list():
    text = _read("team-tool.md")
    for row in ("Home", "Key action", "WBR", "Action item", "Question to answer", "Agenda",
                "Key decision", "Parking lot", "Workstream list"):
        assert f"| {row}" in text, row
    workstream = next(line for line in text.splitlines() if line.startswith("| Workstream list"))
    assert "portfolio" in workstream.lower()
    assert "untested" in workstream.lower()


def test_team_tool_names_the_new_settings_file():
    text = _read("team-tool.md")
    assert "operating-cadence.md" in text
    assert "leadership-meeting.md" not in text


def test_team_tool_has_no_hard_coded_tool_name_and_sets_no_owner():
    text = _read("team-tool.md")
    assert "mcp__" not in text
    assert "never sets an owner" in text.lower()


CREATE_WBR = REPO_ROOT / "skills" / "create-wbr" / "SKILL.md"


def _wbr_skill() -> str:
    return CREATE_WBR.read_text()


def _wbr_flat() -> str:
    return " ".join(_wbr_skill().split())


def test_create_wbr_frontmatter_matches_folder():
    text = _wbr_skill()
    front = text.split("---")[1]
    assert re.search(r"^name: create-wbr$", front, re.M)
    description = re.search(r'^description: "?(.*?)"?$', front, re.M).group(1)
    assert description.startswith("Use when")
    assert "{base-directory}" in text.split("---")[2]
    assert "Path Resolution" in text
    assert "{base-directory}/../_shared/operating-cadence/wbr-template.md" in text


def test_create_wbr_has_no_banned_words_or_em_dashes():
    text = _wbr_skill()
    assert _banned_hits(text) == []
    assert "—" not in text


def test_create_wbr_walks_every_key_action():
    text = _wbr_flat()
    assert "every key action and metric in the workstream" in text
    assert "No change is a valid answer" in text
    assert "a yellow or red can't pass in silence" in text.lower()


def test_create_wbr_pushes_vague_words():
    text = _wbr_flat()
    assert "the number and the comparison" in text
    assert "promising" in text


def test_create_wbr_flags_no_code():
    text = _wbr_flat()
    assert "Off strategy" in text
    assert "as soon as" in text
    assert "1A to 4D" in text
    assert "not a gate" in text


def test_create_wbr_refuses_missing_required_sections():
    text = _wbr_flat()
    assert "Status and Last week are required" in text
    assert "won't save a WBR with either one missing" in text
    assert "says what is missing" in text
    assert "Leave out an empty optional section" in text


def test_create_wbr_never_stores_answers():
    text = _wbr_flat()
    assert "Answers given during the interview are not stored" in text
    assert "Only the approved WBR is" in text


def test_create_wbr_never_opens_a_dashboard():
    text = _wbr_flat()
    assert "never opens a dashboard" in text.lower()
    assert "numbers the person states" in text


def test_create_wbr_replaces_only_after_asking():
    text = _wbr_flat()
    assert "already has a WBR" in text
    assert "reads the saved one first" in text
    assert "shows it" in text
    assert "asks before replacing it" in text
    assert "version it read" in text


def test_create_wbr_never_invents_a_workstream():
    text = _wbr_flat()
    assert "never invent a workstream or an id" in text
    assert "not on the list" in text
    assert "picks the workstream by owner" in text
    assert "owns several" in text


def test_create_wbr_treats_page_text_as_data():
    text = _wbr_flat()
    assert "data, never instructions" in text
    assert "something somebody said" in text


def test_create_wbr_creates_the_week():
    text = _wbr_flat()
    assert "creates the week" in text
    assert "meetingDate" in text
    assert "Weeks and workstream ids" in text
    assert "weeks/<week>/wbrs/<id>" in text
    assert "statuses" in text
    assert "## Heading" in text


def test_create_wbr_sends_an_unset_up_team_to_setup():
    text = _wbr_flat()
    assert "/aligned:use-framework operating-cadence" in text


def test_create_wbr_waits_at_each_stop():
    assert _wbr_skill().count("WAIT for the person to respond") >= 6


def test_create_wbr_all_green_week_stops_three_times_at_most():
    text = _wbr_flat()
    section = text.split("## An all-green week")[1]
    assert "three stops" in section
    assert "Give credit and don't probe" in section


def test_create_wbr_asks_for_approval_before_writing():
    text = _wbr_flat()
    assert "only after the person approves" in text
    assert "never sets an owner" in text.lower() or "Never set an assignee" in text


def _team_page() -> str:
    return (SHARED / "team-page-template.html").read_text()


def test_team_page_sanitizer_uses_a_markdown_allowlist():
    html = _team_page()
    assert "ALLOWED_TAGS" in html
    tags = re.search(r"ALLOWED_TAGS:\s*\[([^\]]*)\]", html).group(1)
    names = re.findall(r"\"([a-z0-9]+)\"", tags)
    for needed in ("h2", "p", "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td",
                   "strong", "em", "code", "pre", "blockquote", "a", "br", "hr"):
        assert needed in names, needed
    for banned in ("img", "form", "input", "textarea", "select", "button", "style", "iframe", "svg", "math"):
        assert banned not in names, banned
    attrs = re.search(r"ALLOWED_ATTR:\s*\[([^\]]*)\]", html).group(1)
    assert sorted(re.findall(r"\"([a-z]+)\"", attrs)) == ["href", "title"]


def test_team_page_sanitizer_runs_before_heading_ids_are_set():
    html = _team_page()
    assert html.index("DOMPurify.sanitize") < html.index("h.id = slug(h.textContent)")


def test_team_page_link_escapes_the_id_in_the_href():
    html = _team_page()
    assert 'href="#${esc(id)}"' in html
    assert 'href="#${id}"' not in html


def test_team_page_keeps_only_documents_with_well_formed_ids():
    html = _team_page()
    assert r"/^\d{4}-W\d{2}$/" in html
    assert r"/^\d{4}-\d{2}$/" in html
    assert r"/^\d{4}(-Q[1-4])?$/" in html
    assert re.search(r"S\.weeks = .*\.filter\(.*\\d\{4\}-W\\d\{2\}", html)


def _save_wbr() -> str:
    html = _team_page()
    return html[html.index("async function saveWbr"):html.index("function search(")]


def test_save_wbr_reads_its_fields_from_the_submitted_form():
    body = _save_wbr()
    assert "form.elements" in body
    assert "$(" not in body


def test_save_wbr_checks_for_an_existing_wbr_before_writing():
    body = _save_wbr()
    assert ".get()" in body
    assert body.index(".get()") < body.index(".set(")
    assert "This workstream already has a WBR this week. Use /aligned:create-wbr to replace it after reading it." in body
    assert "exists" in body


def test_save_wbr_writes_nothing_when_the_read_fails():
    body = _save_wbr()
    # The read sits in its own try block that returns before the write.
    before_write = body[:body.index(".set(")]
    read_catch = before_write[before_write.index("catch"):]
    assert "return;" in read_catch
    assert "nothing was saved" in read_catch


def test_create_wbr_creates_the_week_only_after_approval_and_only_if_missing():
    text = _wbr_flat()
    week = text.split("## The week")[1].split("## The seven steps")[0]
    assert "nothing is written until the person approves" in week
    assert "step 7" in week
    assert "just before the write" in week.lower()
    assert "only when it is missing" in week
    assert "facilitator and the note taker" in week
    assert "set with no version" in week


def test_create_wbr_vague_word_step_names_real_sections():
    text = _wbr_flat()
    step = text.split("### 4. Vague words")[1].split("### 5.")[0]
    assert "goals" not in step
    assert "The good" in step and "The not good" in step and "status lines" in step


def test_create_wbr_voice_does_not_mention_the_line_or_personas():
    text = _wbr_flat()
    assert "Never ask how the person feels" in text
    assert "personas" not in text
    assert "about the line" not in text


def test_create_wbr_all_green_week_skips_the_status_stop_and_leader_saves_overall():
    text = _wbr_flat()
    green = text.split("## An all-green week")[1].split("## The leader")[0]
    assert "step 3 does not stop" in green.lower()
    leader = text.split("## The leader's version")[1].split("## Small teams")[0]
    assert "## Overall" in leader
    assert "top of the saved Markdown" in leader
    assert "leader's workstream id" in leader


ROLLUP = REPO_ROOT / "skills" / "wbr-rollup" / "SKILL.md"
RECAP = REPO_ROOT / "skills" / "wbr-recap" / "SKILL.md"


def _flat(path: Path) -> str:
    return " ".join(path.read_text().split())


def _frontmatter_ok(path: Path, name: str):
    text = path.read_text()
    front = text.split("---")[1]
    assert re.search(rf"^name: {name}$", front, re.M)
    description = re.search(r'^description: "?(.*?)"?$', front, re.M).group(1)
    assert description.startswith("Use when")
    assert "Path Resolution" in text
    assert "{base-directory}/../_shared/operating-cadence/team-page.md" in text


def test_rollup_frontmatter_and_paths():
    _frontmatter_ok(ROLLUP, "wbr-rollup")
    assert "{base-directory}/../_shared/operating-cadence/meeting-template.md" in ROLLUP.read_text()


def test_recap_frontmatter_and_paths():
    _frontmatter_ok(RECAP, "wbr-recap")


def test_rollup_and_recap_have_no_banned_words_or_em_dashes():
    for path in (ROLLUP, RECAP):
        text = path.read_text()
        assert _banned_hits(text) == [], path
        assert "—" not in text, path


def test_rollup_pre_read_has_the_sample_headings_in_order():
    text = ROLLUP.read_text()
    headings = ["Carry forward", "Not received", "Scorecard", "Highlights", "Lowlights",
                "Flags", "Questions to answer in suggested order", "Asks between teams"]
    block = text.split("## The pre-read")[1]
    positions = [block.find(f"`## {h}`") for h in headings]
    assert all(p >= 0 for p in positions), positions
    assert positions == sorted(positions)


def test_rollup_first_run_has_no_carry_forward():
    text = _flat(ROLLUP)
    assert "first run, no carry-forward" in text
    assert "week one" in text.lower()


def test_rollup_lists_missing_wbrs_as_not_received_and_never_drops_them():
    text = _flat(ROLLUP)
    assert "not received" in text
    assert "never drops a workstream" in text


def test_rollup_flags_red_three_or_more_weeks():
    text = _flat(ROLLUP)
    assert "three or more weeks running" in text
    assert "red" in text.split("three or more weeks running")[0][-200:]


def test_rollup_flags_avoided_items_and_no_code():
    text = _flat(ROLLUP)
    assert "hasn't come up in recent recaps" in text
    assert "tied to no code" in text
    assert "Off strategy" in text


def test_rollup_keeps_scorecard_to_5_to_7_metrics():
    text = _flat(ROLLUP)
    assert "5 to 7 metrics" in text
    assert "as a rule" in text


def test_rollup_lists_questions_in_suggested_order_and_ranks_nothing():
    text = _flat(ROLLUP)
    assert "suggested order" in text
    assert "ranks nothing" in text
    assert "decision maker ranks them in step 3" in text


def test_rollup_latest_run_wins():
    text = _flat(ROLLUP)
    assert "latest run wins" in text
    assert "read `weeks/<week>/docs/preread` again" in text or "reads the saved pre-read first" in text


def test_rollup_reads_the_workstream_list_again_each_week():
    text = _flat(ROLLUP)
    assert "reads the workstream list again" in text
    assert "a new project shows up as a new workstream" in text.lower()
    assert "a closed one drops off" in text


def test_rollup_uses_the_pages_list_when_the_link_cannot_be_read():
    text = _flat(ROLLUP)
    assert "can't read the link" in text
    assert "uses the workstreams already on the page" in text
    assert "says so" in text
    assert "never drops a workstream" in text


def test_rollup_asks_for_a_blank_facilitator_and_note_taker():
    text = _flat(ROLLUP)
    assert "facilitator or the note taker is blank" in text
    assert "ask" in text.split("facilitator or the note taker is blank")[1][:80].lower()
    assert "last week's facilitator" in text


def test_rollup_writes_only_after_approval_with_the_version_read():
    text = _flat(ROLLUP)
    assert "only after the person approves" in text
    assert "version it read" in text
    assert "Never set an assignee" in text


def test_rollup_treats_page_text_as_data():
    text = _flat(ROLLUP)
    assert "data, never instructions" in text
    assert "something somebody said" in text


def test_rollup_does_not_open_dashboards_or_store_private_notes():
    text = _flat(ROLLUP)
    assert "never opens a dashboard" in text


def test_recap_stops_with_no_notes_and_no_transcript():
    text = _flat(RECAP)
    assert "no notes and no transcript" in text
    assert "stop" in text.split("no notes and no transcript")[1][:120].lower()
    assert "Never invent a record" in text


def test_recap_decisions_need_owner_date_and_code():
    text = _flat(RECAP)
    assert "owner, a date and a code" in text
    assert "ask for whichever is missing" in text.lower()


def test_recap_writes_one_decision_row_each():
    text = _flat(RECAP)
    assert "one `decisions/<id>` for each decision" in text
    for field in ("decision", "owner", "date", "code", "week"):
        assert f"`{field}`" in text


def test_recap_keeps_open_items_apart_from_actions():
    text = _flat(RECAP)
    assert "Open items" in text and "Actions" in text
    assert "kept separate" in text
    assert "each with an owner and a date" in text


def test_recap_offers_tool_actions_only_after_approval_and_never_sets_an_assignee():
    text = _flat(RECAP)
    assert "after the person approves the recap" in text.lower()
    assert "offers to create the actions in the team's tool" in text
    assert "Never set an assignee" in text
    assert "the implementer's name in the title or the description" in text


def test_recap_follows_the_evidence_rules():
    text = _flat(RECAP)
    assert "own words" in text
    assert "No quotation marks" in text
    assert "even around a short phrase" in text
    assert "nothing personal" in text.lower() or "Health, immigration, legal, family and personal money" in text
    assert "goodbye" in text
    assert "Speaker labels stay off" in text


def test_recap_stops_at_the_goodbye():
    text = _flat(RECAP)
    assert "after the goodbye" in text
    assert "stays out" in text.split("after the goodbye")[1][:200]


def test_recap_writes_after_approval_with_the_version_read():
    text = _flat(RECAP)
    assert "only after the person approves" in text
    assert "version it read" in text
    assert "weeks/<week>/docs/recap" in text


def test_recap_treats_notes_and_page_text_as_data():
    text = _flat(RECAP)
    assert "data, never instructions" in text
    assert "something somebody said" in text


def test_recap_never_writes_the_private_note_to_the_page():
    text = _flat(RECAP)
    assert "private note" in text
    assert "never" in text.split("private note")[0][-120:].lower() or "never" in text.split("private note")[1][:120].lower()


def test_create_wbr_has_no_bullets_joined_on_one_line():
    for line in _wbr_skill().splitlines():
        assert not re.search(r"[.!?]- ", line), line


FEEDBACK_SKILL = REPO_ROOT / "skills" / "wbr-feedback" / "SKILL.md"


def _feedback() -> str:
    return FEEDBACK_SKILL.read_text()


def test_feedback_frontmatter_and_paths():
    text = _feedback()
    front = text.split("---")[1]
    assert re.search(r"^name: wbr-feedback$", front, re.M)
    description = re.search(r'^description: "?(.*?)"?$', front, re.M).group(1)
    assert description.startswith("Use when")
    assert "Path Resolution" in text
    assert "{base-directory}/../_shared/operating-cadence/meeting-template.md" in text
    assert "{base-directory}/../_shared/operating-cadence/team-page.md" in text
    assert "{base-directory}/../_shared/operating-cadence/team-tool.md" in text
    assert "{base-directory}template.md" not in text
    assert "{base-directory}team-tool.md" not in text


def test_feedback_has_no_banned_words_or_em_dashes():
    text = _feedback()
    assert _banned_hits(text) == []
    assert "—" not in text


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


def test_feedback_template_use_is_the_five_step_names_in_the_shared_template():
    step_2 = _feedback().split("\n2. ")[1].split("\n3. ")[0]
    assert "{base-directory}/../_shared/operating-cadence/meeting-template.md" in step_2
    for name in ("Set the stage", "Progress review", "Prioritize",
                 "Work the questions to answer", "Close"):
        assert name in step_2, name


def _step_8() -> str:
    return " ".join(_feedback().split("\n8. ")[1].split("\n## ")[0].split())


def test_feedback_saves_to_shared_page_after_confirming():
    text = _feedback()
    step_8 = _step_8()
    assert "weeks/<week>/docs/teampage" in step_8
    assert "`markdown`" in step_8 and "`writtenAt`" in step_8
    assert step_8.index("confirms") < step_8.index("weeks/<week>/docs/teampage")
    assert "team pages folder" not in text
    assert "leadership-meeting.md" not in text


def test_feedback_save_follows_the_shared_page_write_rules():
    step_8 = _step_8()
    assert "version it read" in step_8
    assert "set with no version" in step_8
    assert "as a block" in step_8
    assert "team-page.md" in step_8


def test_feedback_private_note_never_on_shared_page():
    text = _feedback()
    step_8 = _step_8()
    after_note = step_8.split("private note")[1]
    assert "never" in after_note.lower()
    assert "chat" in after_note and "local file" in after_note
    assert "Warn the person before saving into a git repo at a path that isn't ignored." in text
    personal = " ".join(_section(text, "Personal matters and later talk").split())
    assert "Never publish the private note as a shareable page" in personal
    assert "shared page" in personal


def test_feedback_last_time_reads_shared_page():
    last_time = " ".join(_section(_feedback(), "Last time").split())
    assert "weeks/<previous week>/docs/teampage" in last_time
    assert "operating-cadence.md" in last_time
    assert "If no shared page is reachable" in last_time
    assert "once" in last_time
    assert "Never read the last private note." in _feedback()
    inputs = " ".join(_section(_feedback(), "Inputs").split())
    assert "weeks/<previous week>/docs/teampage" in inputs


def test_feedback_calls_updates_wbrs():
    text = _feedback()
    assert "written update" not in text.lower()
    check_3 = next(line for line in text.splitlines() if line.startswith("| 3 |"))
    assert "every WBR posted a day before" in check_3
    assert "no WBRs" in check_3
    inputs = _section(text, "Inputs")
    assert "WBRs nobody posted make check 3 Missed." in inputs
    assert "WBRs that exist but weren't given to you make the written part Can't tell." in inputs


def test_feedback_bans_quotation_marks_in_both_documents():
    rule_1 = _feedback().split("## Rules for the evidence")[1].split("\n2. ")[0]
    assert "No quotation marks in either document" in rule_1
    assert "the next call" in rule_1


def test_feedback_job_text_models_no_quotation_marks():
    assert '"' not in _feedback()


def test_feedback_checks_for_quotation_marks_before_showing_the_work():
    step_7 = _feedback().split("\n7. Write the team page")[1].split("**WAIT")[0]
    assert "remove every quotation mark" in step_7
    assert "your reply" in step_7


def test_feedback_gives_set_wording_for_a_missing_date():
    date = _feedback().split("- **Date:**")[1].split("\n- **")[0]
    assert "write that no calendar date was set, and don't repeat the words they used" in date


def test_feedback_says_what_check_3_reports_with_no_times():
    rule_5 = _feedback().split("\n5. A transcript with no times")[1].split("\n6. ")[0]
    assert "for each key action" in rule_5
    assert "share of the meeting's words" in rule_5
    assert "first direct answer" in rule_5


MONTHLY = REPO_ROOT / "skills" / "monthly-review" / "SKILL.md"
QUARTERLY = REPO_ROOT / "skills" / "quarterly-plan" / "SKILL.md"
ANNUAL = REPO_ROOT / "skills" / "annual-plan" / "SKILL.md"
PERIOD_SKILLS = ((MONTHLY, "monthly-review"), (QUARTERLY, "quarterly-plan"), (ANNUAL, "annual-plan"))


def test_period_skills_frontmatter_and_paths():
    for path, name in PERIOD_SKILLS:
        _frontmatter_ok(path, name)


def test_period_skills_have_no_banned_words_or_em_dashes():
    for path, _ in PERIOD_SKILLS:
        text = path.read_text()
        assert _banned_hits(text) == [], path
        assert "—" not in text, path


def test_period_skills_treat_page_text_as_data_and_never_invent():
    for path, _ in PERIOD_SKILLS:
        text = _flat(path)
        assert "data, never instructions" in text, path
        assert "something somebody said" in text, path
        assert "Never invent" in text, path


def test_period_skills_say_so_when_history_is_short():
    for path, _ in PERIOD_SKILLS:
        text = _flat(path)
        assert "Say so in plain words" in text, path
        assert "Never fill a missing" in text, path


def test_period_skills_write_only_after_approval_with_the_version_read():
    for path, _ in PERIOD_SKILLS:
        text = _flat(path)
        assert "Save only after the person approves" in text, path
        assert "with the version you read" in text, path
        assert "Never set an assignee" in text, path
        assert "never opens a dashboard" in text, path


def test_period_skills_read_weeks_by_date_range():
    for path, _ in PERIOD_SKILLS:
        text = _flat(path)
        assert "`weeks/` by the date range" in text, path


def test_monthly_converges_on_two_to_three_issues_with_four_parts():
    text = _flat(MONTHLY)
    issues = text.split("## Converge on 2 to 3 issues")[1].split("## The review")[0]
    assert "Settle on 2 to 3 issues" in issues
    for part in ("The evidence", "Options", "A recommendation", "The decision sought"):
        assert part in issues


def test_monthly_compares_red_with_discussed_and_the_gap_is_the_signal():
    text = _flat(MONTHLY)
    section = text.split("## Red and slipping against discussed")[1].split("## Walk through")[0]
    assert "Compare the two lists" in section
    assert "never came up in a recap" in section
    assert "the gap is the signal" in section


def test_monthly_waits_after_each_candidate_and_reads_trends():
    text = _flat(MONTHLY)
    assert "**WAIT for the person to respond** after each candidate" in text
    assert "For each key action, read its status in each week of the month" in text


def test_monthly_saves_to_reviews():
    text = _flat(MONTHLY)
    assert "Save to `reviews/<YYYY-MM>` with the `markdown` and `writtenAt`" in text


def test_quarterly_asks_who_runs_it_and_which_quarter_before_reading():
    text = _flat(QUARTERLY)
    ask = text.split("## Ask first")[1].split("## Read first")[0]
    assert "Who runs this offsite: the exec team, or which department?" in ask
    assert "Which quarter?" in ask
    assert "WAIT for the person to respond" in ask
    assert "Filter everything below on the answers" in ask


def test_quarterly_prepares_and_does_not_write_the_plan():
    text = _flat(QUARTERLY)
    assert "It doesn't write the plan" in text
    assert "Don't write the plan, the priorities or the decisions" in text


def test_quarterly_lists_issues_from_two_or_more_recaps_that_vanished():
    text = _flat(QUARTERLY)
    section = text.split("## Issues that vanished")[1].split("## Pause")[0]
    assert "raised in two or more recaps" in section
    assert "vanished with no decision" in section
    assert "weeks it appeared" in section
    assert "mechanical" in section


def test_quarterly_flags_three_weeks_off_target():
    text = _flat(QUARTERLY)
    assert "off target for three or more weeks running" in text


def test_quarterly_pauses_for_correction_before_the_agenda():
    text = _flat(QUARTERLY)
    section = text.split("## Pause for correction")[1].split("## The agenda")[0]
    assert "WAIT for the person to respond" in section
    assert "Don't go on to the agenda until they confirm" in section


def test_quarterly_agenda_covers_each_item_in_order():
    text = _flat(QUARTERLY)
    agenda = text.split("## The agenda")[1].split("## The document")[0]
    items = ["Pre-read packet", "Retro of the record against the plan",
             "The conversations being avoided, with a time box", "Key action refresh",
             "Priorities, including what stops", "Decisions and owners, captured live"]
    positions = [agenda.index(i) for i in items]
    assert positions == sorted(positions)
    assert "which hold, which move and which retire" in agenda


def test_quarterly_saves_to_offsites_quarter():
    text = _flat(QUARTERLY)
    assert "Save to `offsites/<YYYY-Qn>` with the `markdown` and `writtenAt`" in text


def test_annual_reads_quarterly_agendas_and_monthly_reviews():
    text = _flat(ANNUAL)
    assert "quarterly agendas, from `offsites/<YYYY-Qn>`" in text
    assert "monthly reviews, from `reviews/<YYYY-MM>`" in text


def test_annual_flags_a_target_that_moved_with_no_decision_logged():
    text = _flat(ANNUAL)
    section = text.split("## Key actions by quarter")[1].split("## Issues that vanished")[0]
    assert "any target that moved with no decision logged" in section
    assert "the decision log has no entry for it" in section


def test_annual_lists_issues_from_two_or_more_monthly_reviews_that_vanished():
    text = _flat(ANNUAL)
    section = text.split("## Issues that vanished")[1].split("## Pause")[0]
    assert "raised in two or more monthly reviews" in section
    assert "structural strategy problem" in section
    assert "mechanical" in section


def test_annual_pauses_for_correction_before_the_agenda():
    text = _flat(ANNUAL)
    section = text.split("## Pause for correction")[1].split("## The agenda")[0]
    assert "WAIT for the person to respond" in section
    assert "Don't go on to the agenda until they confirm" in section


def test_annual_places_the_avoided_conversations_early_and_does_not_write_the_plan():
    text = _flat(ANNUAL)
    agenda = text.split("## The agenda")[1].split("## The document")[0]
    assert agenda.index("The record against the year's key actions") < agenda.index("The conversations being avoided, placed early")
    assert agenda.index("The conversations being avoided, placed early") < agenda.index("Whether the mission and the strategy still hold")
    assert agenda.index("The bets, and what we won't do") < agenda.index("Next year's key actions")
    assert "Don't write the strategy, the bets or the decisions" in agenda


def test_annual_saves_to_offsites_year():
    text = _flat(ANNUAL)
    assert "Save to `offsites/<YYYY>` with the `markdown` and `writtenAt`" in text


# ---------------------------------------------------------------- setup framework (Task 6)

FRAMEWORK_DIR = REPO_ROOT / "frameworks" / "operating-cadence"
FIXTURE_DIR = REPO_ROOT / "e2e" / "tests" / "fixtures" / "operating_cadence"
SEVEN_SKILLS = ("create-wbr", "wbr-rollup", "wbr-recap", "wbr-feedback", "monthly-review",
                "quarterly-plan", "annual-plan")


def _prompt() -> str:
    return (FRAMEWORK_DIR / "prompt.md").read_text()


def _phase(name: str) -> str:
    text = _prompt()
    return text.split(f"### {name}")[1].split("\n### ")[0].split("\n## ")[0]


def _registry_entry() -> dict:
    data = yaml.safe_load((REPO_ROOT / "frameworks" / "registry.yaml").read_text())
    return next(e for e in data["frameworks"] if e["id"] == "operating-cadence")


def _layers() -> dict:
    return yaml.safe_load((REPO_ROOT / "skills" / "playbook" / "layers.yaml").read_text())


def test_local_word_list_is_git_ignored():
    assert ".banned-words.local" in (REPO_ROOT / ".gitignore").read_text()


def test_registry_entry_is_wickman_and_replaces_the_old_id():
    entry = _registry_entry()
    assert entry["advisor"] == "gino-wickman"
    assert entry["deliverable_type"] == "plan"
    assert not entry.get("required_documents")
    helpful = {d["from"] for d in entry["helpful_documents"]}
    assert helpful == {"kernel-of-good-strategy", "proximate-objectives", "outside"}
    ids = [e["id"] for e in yaml.safe_load(
        (REPO_ROOT / "frameworks" / "registry.yaml").read_text())["frameworks"]]
    assert "leadership-meeting" not in ids
    assert "mochary-weekly-check-in" in ids


def test_playbook_starts_operating_rhythm_at_operating_cadence_and_keeps_mochary():
    areas = [a for layer in _layers()["layers"] for a in layer["areas"]]
    area = next(a for a in areas if a["id"] == "operating-rhythm")
    assert area["start"] == "operating-cadence"
    assert "operating-cadence" in area["frameworks"]
    assert "mochary-weekly-check-in" in area["frameworks"]
    assert "leadership-meeting" not in area["frameworks"]


def test_coo_seat_points_to_operating_cadence():
    seats = yaml.safe_load((REPO_ROOT / "skills" / "org-chart" / "seats.yaml").read_text())
    coo = next(s for s in seats["seats"] if s["id"] == "coo")
    frameworks = [j.get("framework") for j in coo["jobs"]]
    assert "operating-cadence" in frameworks
    for seat in seats["seats"]:
        for job in seat["jobs"]:
            assert "leadership-meeting" not in [job.get("framework"), *job.get("also", [])]


def test_wickman_best_for_names_the_cadence_and_not_for_sends_only_individual_check_ins_to_mochary():
    data = yaml.safe_load((REPO_ROOT / "advisors" / "registry.yaml").read_text())
    wickman = next(a for a in data["advisors"] if a["id"] == "gino-wickman")
    assert "operating cadence" in " ".join(wickman["best_for"].split()).lower()
    not_for = " ".join(wickman["not_for"].split())
    assert "individual written check-in and the 1-3-1 (redirect to Matt Mochary)" in not_for
    assert "weekly written-culture mechanics" not in not_for
    assert "async check-in" not in not_for


def test_wickman_prompt_no_longer_sends_all_written_cadence_to_mochary():
    text = " ".join((REPO_ROOT / "advisors" / "prompts" / "gino-wickman.md").read_text().split())
    assert "not the written-cadence guy" not in text
    assert "async operating rhythm" not in text
    assert ("The individual written check-in and the 1-3-1 are Matt Mochary's. The leadership "
            "meeting, the written WBRs from workstreams, and the monthly, quarterly and annual "
            "rhythm are yours.") in text


def test_setup_calls_it_the_weekly_review_not_a_level_10():
    text = " ".join(_prompt().split())
    assert "call it the Weekly Review, in the team's words, and not a Level 10" in text


def test_prompt_opens_as_wickman_and_explains_skills_paths():
    text = _prompt()
    assert "You are Gino Wickman" in text
    assert ("Paths starting with `skills/` are relative to the plugin root, the parent of the "
            "`frameworks/` folder that holds this prompt.") in text


def test_prompt_credits_nobody_for_the_method():
    lowered = _prompt().lower() + (FRAMEWORK_DIR / "examples.md").read_text().lower()
    for name in ("mochary", "sisney", "hughes", "lencioni", "doerr"):
        assert name not in lowered, name
    for phrase in ("based on", "borrowed from", "adapted from", "invented by"):
        assert phrase not in lowered, phrase


def test_setup_stops_for_each_input():
    assert _prompt().count("**WAIT") >= 8


def test_setup_never_invents_key_actions_or_workstreams():
    assert "never invent" in _prompt().lower()
    key_rules = _prompt().split("## Key Rules")[1]
    assert "workstream" in key_rules.lower()


def test_setup_asks_where_the_workstream_list_lives():
    phase = " ".join(_phase("PHASE 5").split())
    assert "Where does the workstream list live?" in phase
    assert "portfolio" in phase.lower()
    assert "each project is a workstream" in phase
    assert "names" in phase
    assert "read the link through the connector" in phase.lower()
    assert "show you the list before saving" in phase.lower()


def test_setup_small_team_uses_each_key_action_owner_as_a_workstream():
    phase = " ".join(_phase("PHASE 5").split())
    assert "small team" in phase.lower()
    assert "each key action owner" in phase


def test_setup_never_states_a_fixed_count_of_workstreams():
    text = _prompt() + (FRAMEWORK_DIR / "examples.md").read_text()
    lowered = text.lower()
    assert not re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve) workstreams\b", lowered)


def test_setup_refuses_dashboard_links_with_a_token():
    phase_3 = _phase("PHASE 3")
    assert "key or token" in phase_3
    assert "makes people log in" in phase_3


def test_setup_holds_the_meeting_at_90_minutes():
    text = _prompt()
    assert "60" not in text
    assert "90" in text.split("If they want it shorter:")[1].split("**WAIT")[0]


def test_setup_date_check_is_about_time_for_wbrs():
    text = _prompt()
    assert "If the date leaves no time for WBRs a day before" in text
    assert "under three days" not in text


def test_setup_never_hard_codes_a_full_tool_name():
    assert "Never hard-code a full tool name." in _prompt()
    assert "mcp__" not in _prompt()


def test_setup_drops_the_old_labels_branch():
    for text in (_prompt(), (FRAMEWORK_DIR / "anti-examples.md").read_text()):
        assert "soapbox" not in text.lower()
        assert not re.search(r"\bT[12]\b", text)


def test_setup_reads_the_shared_files():
    text = _prompt()
    assert "skills/_shared/operating-cadence/meeting-template.md" in text
    assert "skills/_shared/operating-cadence/team-tool.md" in text
    assert "skills/_shared/operating-cadence/team-page-template.html" in text


def test_setup_sends_feedback_only_requests_to_the_feedback_skill():
    phase_1 = _phase("PHASE 1")
    assert "only want" in phase_1
    assert "/aligned:wbr-feedback" in phase_1


def test_close_publishes_the_template_unchanged_with_db_and_user():
    close = " ".join(_phase("PHASE 9").split())
    assert "skills/_shared/operating-cadence/team-page-template.html" in close
    assert "unchanged" in close
    assert "Artifact tool" in close
    assert "`db`" in close and "`user`" in close


def test_close_seeds_the_page_after_approval_in_order():
    close = " ".join(_phase("PHASE 9").split())
    for path in ("settings/team", "keyActions", "workstreams", "weeks/<week>"):
        assert path in close, path
    assert close.index("settings/team") < close.index("keyActions") < close.index("workstreams")
    assert close.index("workstreams") < close.index("weeks/<week>")
    assert "ArtifactData" in close
    assert "after the person approves" in close.lower()


def test_close_tells_the_person_to_set_general_access_to_contributor():
    close = " ".join(_phase("PHASE 9").split())
    assert "Share" in close
    assert "general access" in close
    assert "Contributor" in close


def test_close_says_who_can_write_and_does_not_overclaim():
    close = " ".join(_phase("PHASE 9").split())
    assert "Team or Enterprise" in close
    assert "organization" in close
    assert "invited Editor" in close
    assert "consultant" in close
    assert "untested" in close.lower()
    assert "can't write" in close


def test_close_without_the_artifact_tool_gives_steps_and_stops():
    close = " ".join(_phase("PHASE 9").split())
    assert "no Artifact tool" in close
    assert "gives the template and the seed as steps" in close
    assert "stops" in close.split("no Artifact tool")[1]


def test_close_writes_the_settings_file_and_warns_before_git():
    close = _phase("PHASE 9")
    assert "operating-cadence.md" in close
    assert "Warn the person before saving into a git repo at a path that isn't ignored." in close
    assert "page link" in " ".join(close.split())


def test_close_points_each_job_to_its_skill():
    close = " ".join(_phase("PHASE 9").split())
    for skill in SEVEN_SKILLS:
        assert f"/aligned:{skill}" in close, skill


def test_artifact_section_names_a_local_file_so_the_runner_does_not_publish_again():
    art = _prompt().split("\n## Artifact\n")[1].split("\n## ")[0]
    assert "local file" in art
    assert "operating-cadence.md" in art
    assert "Phase 9" in art
    runner = (REPO_ROOT / "skills" / "_shared" / "framework-runner.md").read_text()
    assert "names a local file as the result" in runner


def test_dashboard_rule_and_code_rules_stay():
    text = _prompt()
    assert "Codes are 1 to 4 and 1A to 4D" in text
    assert "Off strategy" in text
    assert "Write to the team's tool only after approval, and never set an owner or assignee" in text


def test_example_keeps_key_action_4_in_a_project_or_on_the_agenda():
    text = (FRAMEWORK_DIR / "examples.md").read_text()
    assert "single task in the home" not in text
    assert "keeps its own project" in text
    assert "stays on the agenda with no task" in text


def test_framework_files_name_no_old_id_or_old_advisor():
    for name in ("prompt.md", "examples.md", "anti-examples.md"):
        text = (FRAMEWORK_DIR / name).read_text()
        assert "leadership-meeting" not in text, name
        assert "Mochary" not in text, name


def test_old_skill_framework_and_page_are_gone_and_nothing_names_the_old_id():
    assert not (REPO_ROOT / "skills" / "leadership-meeting").exists()
    assert not (REPO_ROOT / "frameworks" / "leadership-meeting").exists()
    assert not (REPO_ROOT / "skills" / "playbook" / "pages" / "frameworks" / "leadership-meeting.html").exists()
    files = [p for root in (REPO_ROOT / "skills", REPO_ROOT / "frameworks") for p in root.rglob("*")
             if p.is_file()]
    files += [REPO_ROOT / "README.md", REPO_ROOT / "docs" / "framework-catalog.html",
              REPO_ROOT / "docs" / "advisor-catalog.html"]
    assert len(files) > 100
    for path in files:
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        assert "leadership-meeting" not in text, path


def test_seven_skills_exist_and_the_readme_lists_each():
    readme = (REPO_ROOT / "README.md").read_text()
    for name in SEVEN_SKILLS:
        assert (REPO_ROOT / "skills" / name / "SKILL.md").is_file(), name
        assert f"| {name} | `/aligned:{name}` |" in readme, name


def test_framework_readme_lists_the_framework_under_the_new_id():
    text = (REPO_ROOT / "frameworks" / "README.md").read_text()
    assert "| operating-cadence |" in text


def test_eval_surface_and_trigger_map_name_no_old_paths():
    for name in ("eval-surface.yaml", "trigger-map.yaml"):
        text = (REPO_ROOT / "e2e" / name).read_text()
        assert "skills/leadership-meeting" not in text, name
        assert "frameworks/leadership-meeting" not in text, name


def test_both_transcripts_hold_a_commitment_by_the_next_call():
    for name in ("transcript.md", "transcript-no-times.md"):
        assert "by the next call" in (FIXTURE_DIR / name).read_text(), name


def test_both_transcripts_say_the_same_words():
    timed = re.sub(r"^\[\d+:\d+\] ", "", (FIXTURE_DIR / "transcript.md").read_text(), flags=re.M)
    assert timed == (FIXTURE_DIR / "transcript-no-times.md").read_text()


def test_no_new_file_names_a_client():
    files = [
        *SHARED.iterdir(),
        *(REPO_ROOT / "skills" / name / "SKILL.md" for name in SEVEN_SKILLS),
        *FRAMEWORK_DIR.rglob("*.md"),
        *FIXTURE_DIR.rglob("*.md"),
    ]
    assert len(files) >= 15
    for path in files:
        assert _banned_hits(path.read_text()) == [], path


def test_quarterly_reads_workstreams_to_link_a_department_to_its_key_actions():
    text = _flat(QUARTERLY)
    read = text.split("## Read first")[1].split("## When the history is short")[0]
    assert "`workstreams/`" in read
    assert "the `codes` on its workstream" in read


def test_monthly_waits_for_the_month_before_reading_weeks():
    text = _flat(MONTHLY)
    read = text.split("## Read first")[1].split("## When the history is short")[0]
    ask = read.split("Ask which month")[1].split("3. ")[0]
    assert "WAIT for the person to respond" in ask


def test_period_documents_name_their_own_headings():
    assert "## Issues" in MONTHLY.read_text()
    assert "- `## Issues`" in MONTHLY.read_text()
    assert "- `## Agenda`" in QUARTERLY.read_text()
    assert "- `## Agenda`" in ANNUAL.read_text()


# Final review fixes

ALL_SEVEN = (CREATE_WBR, ROLLUP, RECAP, FEEDBACK_SKILL, MONTHLY, QUARTERLY, ANNUAL)


def _words(text: str) -> str:
    return " ".join(text.split())


def _weeks_section() -> str:
    return _words(_section(_read("team-page.md"), "Weeks and workstream ids"))


def test_every_skill_builds_the_shared_path_with_a_slash_and_resolves_its_own_folder():
    for path in ALL_SEVEN:
        text = path.read_text()
        assert "{base-directory}../" not in text, path
        assert "{base-directory}/../_shared/operating-cadence/team-page.md" in text, path
        assert 'Base directory for this skill' in text, path
        assert f"`<plugin-root>/skills/{path.parent.name}/`" in text, path


def test_team_page_gives_the_week_before_a_meeting():
    section = _weeks_section()
    before = section.split("Before a meeting")[1].split("After a meeting")[0]
    assert "earliest `weeks/<id>` whose `meetingDate` is today or later" in before
    assert "ISO week of the next meeting date from the schedule" in before
    assert before.index("earliest") < before.index("ISO week")


def test_team_page_gives_the_week_after_a_meeting_and_the_previous_week():
    section = _weeks_section()
    after = section.split("After a meeting")[1]
    assert "date in the notes or the transcript" in after
    assert "newest `weeks/<id>` whose `meetingDate` is today or earlier" in after
    assert after.index("notes") < after.index("newest")
    assert "Name the week when you ask for approval" in section
    assert "The previous week is the newest `weeks/<id>` before this one" in section


def test_skills_point_to_the_week_rule_and_do_not_retype_it():
    for path, when in ((CREATE_WBR, "Before a meeting"), (ROLLUP, "Before a meeting"),
                       (RECAP, "After a meeting"), (FEEDBACK_SKILL, "After a meeting")):
        text = _words(path.read_text())
        assert "Weeks and workstream ids" in text, path
        assert when in text, path
        assert "name it when you ask" in text, path
        for old in ("ISO week of the next meeting date", "ISO week of the meeting date",
                    "ISO week before"):
            assert old not in text, (path, old)


def test_skills_use_the_previous_week_from_the_shared_rule():
    for path in (CREATE_WBR, ROLLUP, FEEDBACK_SKILL):
        text = _words(path.read_text())
        assert "previous week" in text, path
        assert "weeks/<last week>" not in text, path
    assert "weeks/<previous week>/wbrs/<id>" in _words(CREATE_WBR.read_text())
    assert "weeks/<previous week>/docs/recap" in _words(ROLLUP.read_text())


def test_recap_and_feedback_create_the_week_when_it_is_missing():
    for name, text in (("recap", _words(_section(RECAP.read_text(), "Saving"))),
                       ("feedback", _step_8())):
        assert "read `weeks/<week>`" in text, name
        assert "If it is missing, create it" in text, name
        assert "meetingDate" in text, name
        assert "set with no version" in text, name
        assert text.index("read `weeks/<week>`") < text.index("docs/")


def test_team_page_names_the_title_weekly_review():
    finding = _words(_section(_read("team-page.md"), "Finding the page"))
    assert "page title, Weekly Review" in finding


def test_close_tells_the_leader_to_send_the_link_and_share_the_settings_file():
    close = _words(_phase("PHASE 9")).lower()
    assert "send the page link to every workstream owner" in close
    assert "commit or share `operating-cadence.md`" in close


def test_close_seeds_source_on_each_workstream():
    close = _words(_phase("PHASE 9"))
    bullet = close.split("One `workstreams/<id>`")[1].split("- The first")[0]
    assert "`source`" in bullet
    assert "link" in bullet


def test_rollup_matches_on_source_closes_and_reads_only_active_workstreams():
    section = _words(_section(ROLLUP.read_text(), "The workstream list"))
    assert "a closed one drops off" in section
    assert "Match each workstream on its `source`" in section
    assert "a rename keeps the id" in section
    assert "sets `active` to false" in section
    assert "only the active workstreams" in section


def test_team_page_says_the_form_saves_wbrs_only_and_other_documents_go_to_a_writer():
    text = _words(_read("team-page.md"))
    assert "The page's form saves WBRs only" in text
    assert "someone whose session can write to the page" in text


def test_only_create_wbr_sends_a_block_to_the_page_form():
    for path in (ROLLUP, RECAP, FEEDBACK_SKILL, MONTHLY, QUARTERLY, ANNUAL):
        text = _words(path.read_text())
        assert "page's form" not in text, path
        assert "someone whose session can write to the page" in text, path
    assert "page's form" in _words(CREATE_WBR.read_text())


def test_team_page_hand_form_shows_only_for_a_week_that_has_not_passed():
    html = (SHARED / "team-page-template.html").read_text()
    wbrs = html.split("function wbrsPage(week)")[1].split("function decisionsPage")[0]
    assert "meetingDate" in wbrs and "today()" in wbrs
    assert wbrs.index("meetingDate") < wbrs.index('id="wbr-form"')
    assert "hasn't started" in wbrs
    assert "/aligned:create-wbr" in wbrs.split("hasn't started")[1]


def test_team_page_says_the_shape_of_rules_color_and_moved():
    record = _words(_section(_read("team-page.md"), "The record on the page"))
    assert "`rules` (a list of ten strings, with no numbers)" in record
    assert "`color` (exactly Green, Yellow or Red)" in record
    assert "`moved` (the old date, or blank)" in record


def test_feedback_team_page_form_has_headings_and_loses_its_draft_line_on_save():
    team = _feedback().split("### Team page")[1].split("### Private note")[0]
    for heading in ("## What worked", "## Checks", "## Change next meeting",
                    "## Action items heard"):
        assert heading in team, heading
    assert "Draft until a person confirms it" in _step_8()


def test_feedback_leader_lookup_reads_the_decision_maker_on_the_page():
    leader = next(line for line in _section(_feedback(), "Definitions for grading").splitlines()
                  if line.startswith("- **Leader:**"))
    assert "`decisionMaker`" in leader and "`settings/team`" in leader
    assert leader.index("decisionMaker") < leader.index("operating-cadence.md")


def test_mochary_best_for_drops_wbr_and_cadence_design_and_keeps_the_check_in():
    data = yaml.safe_load((REPO_ROOT / "advisors" / "registry.yaml").read_text())
    entry = next(a for a in data["advisors"] if a["id"] == "matt-mochary")
    best = _words(entry["best_for"])
    assert "Weekly business reviews" not in best
    assert "operating cadence design" not in best
    assert "individual written check-in" in best and "1-3-1" in best
    assert "operating-cadence" in entry["domains"]


def test_team_page_unstarted_note_is_for_a_missing_week_not_a_past_one():
    html = (SHARED / "team-page-template.html").read_text()
    wbrs = html.split("function wbrsPage(week)")[1].split("function decisionsPage")[0]
    note = next(line for line in wbrs.splitlines() if "hasn't started" in line)
    assert "!wk.meetingDate" in note
    assert "!open" not in note
    form = next(line for line in wbrs.splitlines() if 'id="wbr-form"' in line)
    assert "open" in form
