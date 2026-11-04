"""Static checks on the 6-step process mind map page and its example."""

import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO / "frameworks" / "6-step-process"
TEMPLATE = FRAMEWORK / "mind-map-template.html"
EXAMPLE = FRAMEWORK / "example-map.html"

SLOT = re.compile(r'(<script id="map-data" type="application/json">)(.*?)(</script>)', re.S)
# Optional list of words that must stay out of shipped files, one per line. It lives
# outside the repo because this repo is distributed. Without it, those checks skip.
BANNED_WORDS_FILE = Path.home() / ".claude" / "aligned-banned-words.txt"


def banned_words():
    if not BANNED_WORDS_FILE.exists():
        pytest.skip("no local banned-words list")
    return set(BANNED_WORDS_FILE.read_text().lower().split())


def template():
    return TEMPLATE.read_text()


def test_template_has_data_and_logic_blocks():
    html = template()
    assert SLOT.search(html)
    assert '<script id="map-logic">' in html
    assert html.index('id="map-data"') < html.index('id="map-logic"') < html.index('id="map-page"')


def test_template_data_is_an_empty_starter_map():
    data = json.loads(SLOT.search(template()).group(2))
    assert data["obstacles"] == []
    assert data["solutions"] == []
    assert data["revision"] == 1


def test_template_has_no_outside_urls():
    html = template()
    assert not re.search(r"https?://", html)
    assert not re.search(r'\bsrc\s*=', html)
    assert "@import" not in html
    assert "url(" not in html
    assert "<link" not in html
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html


def banned_word_count(text, banned):
    return sum(word in banned for word in re.findall(r"[a-z0-9]+", text.lower()))


def test_banned_word_check_finds_a_word_in_any_case():
    assert banned_word_count("We met ACMECO's team.", {"acmeco"}) == 1
    assert banned_word_count("We met nobody.", {"acmeco"}) == 0


def test_no_hashes_of_banned_words_in_this_file():
    assert not re.search(r'"[0-9a-f]{64}"', Path(__file__).read_text())


def test_template_names_no_client():
    banned = banned_words()
    for page in (template(), EXAMPLE.read_text(), Path(__file__).read_text()):
        assert banned_word_count(page, banned) == 0


def test_template_says_not_compared_outside_the_side_panel():
    html = template()
    assert re.search(r'<header>.*id="strategy-note"[^>]*>Not compared to strategy\.<.*</header>', html, re.S)


def test_refusal_copy_keeps_the_page_marked_unsaved():
    html = template()
    body = html[html.index("function saveACopy("):html.index("function showRefusal(")]
    assert "markSaved" not in body
    assert "L.replaceMapData(SOURCE, map)" in body
    assert "L.copyMessage(location.pathname, reason)" in body


def test_refusal_passes_its_reason_to_the_copy():
    html = template()
    body = html[html.index("function showRefusal("):html.index("async function writeToFile()")]
    assert "saveACopy(reason)" in body


def whole_function(name):
    """The source of one function in the page code, up to the next function at the same indent."""
    html = template()
    page = html[html.index('id="map-page"'):]
    match = re.search(r"\n  (async )?function " + name + r"\(.*?\n  \}\n", page, re.S)
    assert match, name
    return match.group(0)


def test_saving_sits_in_the_top_right_and_the_page_has_no_footer():
    html = template()
    body = html[html.index("<body>"):html.index('<script id="map-logic">')]
    assert "<footer" not in body
    header = body[body.index("<header>"):body.index("</header>")]
    assert 'id="dirty"' not in html
    assert "el.dirty" not in html
    assert "Not saved yet." not in header
    assert ">Save<" not in header
    assert header.count('id="save"') == 1
    assert "Click any item to edit it." in header
    # The status and its button take the far right, after every other control.
    assert header.index('id="toggle-plan"') < header.index('id="save-status"') < header.index('id="save"')
    assert header.rindex("<button") == header.index('id="save"') - len('<button type="button" class="quiet" ')


def test_save_messages_appear_under_the_top_right_controls():
    html = template()
    body = html[html.index("<body>"):html.index('<script id="map-logic">')]
    assert body.index("</header>") < body.index('id="notices"') < body.index('id="workspace"')
    notices = body[body.index('id="notices"'):body.index('id="workspace"')]
    assert 'id="message"' in notices
    assert 'id="browser-note"' in notices
    assert re.search(r"#notices \{[^}]*text-align: right", html)


def test_a_map_that_cant_be_drawn_hides_the_save_messages():
    assert "'header, #notices, #workspace, #tray'" in template()


def test_editor_offers_the_picks_checkbox():
    html = template()
    body = html[html.index("<body>"):html.index('<script id="map-logic">')]
    assert "To change a star" not in body
    assert "To change a star" not in html
    editor = whole_function("openEditor")
    solution_branch = editor[editor.index("if (ref.kind === 'solution')"):]
    assert "picksControl(ref)" in solution_branch
    control = whole_function("picksControl")
    assert "This is one of my picks" in control
    assert "type = 'checkbox'" in control
    assert "L.setStar(map, ref.sid, box.checked)" in control


def test_header_has_the_picks_key_before_the_map_controls():
    html = template()
    header = html[html.index("<header>"):html.index("</header>")]
    assert "★ My picks" in header
    assert header.index("★ My picks") < header.index('id="zoom-out"')
    assert header.index("★ My picks") > header.index('id="edit-hint"')


def test_browser_note_says_chrome_saves_by_itself():
    html = template()
    note = html[html.index('id="browser-note"'):html.index('id="workspace"')]
    assert "saves by itself" in note
    assert "Open With" in note
    assert "Downloads" in note


def test_status_line_comes_from_the_logic_block():
    assert "L.saveStatus(" in whole_function("showStatus")
    assert "showStatus()" in whole_function("render")


def test_status_does_not_call_a_blank_new_item_unsaved():
    assert "holdingNewItem()" in whole_function("showStatus")


def test_autosave_guards_against_retrying_the_same_json():
    assert "askToWrite()" in whole_function("render")
    body = whole_function("askToWrite")
    assert "if (!handle" in body
    assert body.index("savedJson") < body.index("autosaver.request()")
    assert body.index("lastTried") < body.index("autosaver.request()")
    assert "lastTried = L.serializeMap(saving)" in whole_function("writeToFile")


def test_blank_new_item_stays_out_of_the_file_until_it_has_text():
    assert "holdingNewItem()" in whole_function("askToWrite")


def test_write_returns_its_result_so_the_autosaver_keeps_or_drops_its_queue():
    body = whole_function("writeToFile")
    assert body.count("return result;") == 2


def test_edit_that_lands_on_the_old_file_contents_still_gets_written():
    body = whole_function("writeToFile")
    assert body.index("markSaved(saving)") < body.index("askToWrite()")
    assert body.index("if (!result.ok)") < body.index("askToWrite()")


def test_first_write_tells_the_person_to_tell_claude_once():
    body = whole_function("writeToFile")
    assert "When you finish, tell Claude you changed the map." in body
    assert "toldToTellClaude = true" in body
    assert "if (!toldToTellClaude)" in body


def test_good_write_clears_a_failure():
    assert "failed = false" in whole_function("writeToFile")


def test_handle_store_is_keyed_by_path_and_map_id():
    html = template()
    page = html[html.index('id="map-page"'):]
    assert "L.handleKey(location.pathname, map.map_id)" in page


def test_handle_store_survives_a_storage_failure():
    html = template()
    page = html[html.index('id="map-page"'):]
    uses = [m.start() for m in re.finditer(r"\bindexedDB\b", page)]
    assert uses
    for at in uses:
        before = page[:at]
        top_level_function = before.rindex("\n  async function ")
        opened = before[top_level_function:]
        assert opened.count("try {") > opened.count("} catch")


def test_bad_files_are_forgotten():
    body = whole_function("applyRefusal")
    branch = body[:body.index("reason === 'permission'")]
    for reason in ("wrong-map", "not-a-map", "unreadable"):
        assert "'" + reason + "'" in branch
    assert "forgetHandle()" in branch
    assert "remembered = null" in branch


def test_lost_permission_keeps_the_remembered_file():
    body = whole_function("applyRefusal")
    branch = body[body.index("reason === 'permission'"):body.index("} else {")]
    assert "handle = null" in branch
    assert "remembered = null" not in branch
    assert "forgetHandle" not in branch


def test_stale_and_failed_writes_stay_connected_and_marked_failed():
    body = whole_function("applyRefusal")
    assert "failed = true" in body[body.index("} else {"):]


def test_stale_refusal_uses_the_approved_words():
    assert (
        "'stale': 'Claude changed this map, so your last edit is not in the file. "
        "Reload to get the new version.'"
    ) in template()


def test_only_a_stale_refusal_offers_reload():
    body = whole_function("showRefusal")
    assert "reason === 'stale'" in body
    assert "location.reload()" in body
    assert body.index("reason === 'stale'") < body.index("location.reload()")


def test_first_click_opens_the_picker_with_no_step_before_it():
    body = whole_function("pickThenConnect")
    assert "L.pickMessage(location.pathname)" in body
    assert "await" not in body[:body.index("picked = await window.showOpenFilePicker")]
    assert "connect(picked[0])" in body
    assert "AbortError" in body


def test_button_uses_the_remembered_file_before_any_dialog():
    body = whole_function("onSave")
    picker_gone = body.index("!window.showOpenFilePicker")
    remembered = body.index("connect(remembered)")
    pick = body.index("pickThenConnect()")
    assert picker_gone < remembered < pick


def test_connecting_remembers_the_file_then_writes_only_through_the_guard():
    body = whole_function("startSaving")
    assert "handle = file" in body
    assert "rememberHandle(file)" in body
    assert "askToWrite()" in body
    assert "writeToFile" not in body


def test_load_connects_only_when_permission_is_already_granted():
    body = whole_function("reconnectOnLoad")
    assert "queryPermission({ mode: 'readwrite' })" in body
    assert body.index("queryPermission") < body.index("L.connectToHandle")
    assert body.index("=== 'granted'") < body.index("L.connectToHandle")
    assert "requestPermission" not in body


def test_load_treats_a_stale_file_as_paused():
    body = whole_function("reconnectOnLoad")
    assert "result.reason !== 'stale'" in body
    assert "showRefusal" not in body


def test_load_and_autosave_code_stays_off_without_the_picker():
    html = template()
    assert "if (window.showOpenFilePicker) reconnectOnLoad();" in html


def test_close_warning_is_unchanged():
    assert "L.shouldWarnOnClose(commitEdit, isDirty)" in template()


def test_no_save_file_picker():
    assert "showSaveFilePicker" not in template()
    assert "showSaveFilePicker" not in EXAMPLE.read_text()


def test_browser_without_the_picker_names_the_folder_and_file():
    html = template()
    body = html[html.index("function onSave()"):html.index("/* Events */")]
    assert "L.moveCopyMessage(location.pathname)" in body
    assert "A copy went to your Downloads folder" not in html


def test_page_shows_a_message_when_the_data_cant_be_drawn():
    html = template()
    assert re.search(r'<div id="data-problem" role="alert" hidden>', html)
    page_script = html[html.index('id="map-page"'):]
    check = page_script.index("L.mapProblem(map)")
    assert check < page_script.index("L.serializeMap(map)")
    assert check < page_script.index("render();\n})();")
    guard = page_script[check:page_script.index("L.serializeMap(map)")]
    assert "showDataProblem" in guard
    assert "return;" in guard


def test_goal_editor_has_one_box():
    editor = whole_function("openEditor")
    goal_branch = editor[editor.index("ref.kind === 'goal'"):editor.index("ref.kind === 'missing'")]
    for label in ("'From'", "'To'", "'By'"):
        assert label not in goal_branch
    assert "goalInput" not in template()
    assert "goal-line" not in template()


def test_prompt_json_goal_has_only_text():
    rules = section("## The map file")
    assert '"goal": {"text": ""}' in rules
    assert '"from": ""' not in rules


def test_prompt_puts_the_goal_in_one_sentence():
    goal = section("## Step 2: Goal")
    assert "one sentence" in goal
    assert "starting point not known yet" in goal


def test_template_holds_no_escape_a_file_tool_could_decode():
    assert "\\u003c" not in template()
    assert "'\\\\' + 'u003c'" in template()


def test_template_has_downloads_note():
    html = template()
    assert "Downloads" in html
    assert "Open With" in html


def test_template_tells_person_to_tell_claude():
    html = template()
    assert "tell Claude you changed the map" in html


def test_template_copy_has_no_long_dashes():
    for page in (template(), EXAMPLE.read_text()):
        assert "—" not in page
        assert "–" not in page


def test_template_captures_source_before_drawing():
    html = template()
    page_script = html[html.index('id="map-page"'):]
    assert page_script.index("document.documentElement.outerHTML") < page_script.index("render()")
    assert '<div id="canvas"></div>' in html


def test_template_has_quiet_zoom_controls():
    html = template()
    for control in ("zoom-out", "zoom-in", "zoom-fit"):
        assert re.search(r'<button type="button" class="quiet" id="' + control + '"', html), control


def test_page_takes_the_baseline_from_the_save_result():
    html = template()
    body = html[html.index("async function writeToFile()"):html.index("async function pickThenConnect()")]
    assert "saving.baseline = result.baseline" in body
    assert "map.baseline = result.baseline" in body
    assert body.index("map.baseline = result.baseline") < body.index("markSaved(saving)")


def test_template_says_when_a_solution_is_missing():
    assert "This solution is missing" in template()


def test_template_defines_light_and_dark_tokens():
    html = template()
    assert ":root {" in html
    assert "prefers-color-scheme: dark" in html
    body_rule = re.search(r"\nbody \{(.*?)\}", html, re.S)
    assert body_rule and "background:" in body_rule.group(1)


def test_refusal_messages_cover_every_save_reason():
    html = template()
    for reason in ("wrong-map", "not-a-map", "stale", "permission", "unreadable", "write-failed"):
        assert re.search(r"['\"]" + reason + r"['\"]\s*:", html), reason
    assert "Save a copy" in html
    assert "AbortError" in html


def test_example_map_parses():
    data = json.loads(SLOT.search(EXAMPLE.read_text()).group(2))
    assert data["map_id"]
    assert "attendance" in data["goal"]["text"].lower()
    assert data["obstacles"]
    assert data["baseline"]["obstacles"] == data["obstacles"]


def test_example_map_is_the_template_with_new_data():
    strip = lambda html: SLOT.sub("", html)
    assert strip(EXAMPLE.read_text()) == strip(template())


def test_example_map_escapes_every_angle_bracket_in_its_data():
    assert "<" not in SLOT.search(EXAMPLE.read_text()).group(2)


# The framework prompt

PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI_EXAMPLES = FRAMEWORK / "anti-examples.md"
REGISTRY = REPO / "frameworks" / "registry.yaml"

STEP_HEADINGS = [
    "## Step 1: Locate",
    "## Step 2: Goal",
    "## Step 3: Root-cause the problems",
    "## Step 4: Solutions",
    "## Step 5: Execute",
    "## Step 6: Feedback",
]
LIST_STOPS = ["### 3a: Obstacles", "### 3b: Pick the obstacles", "### 4a: Solutions", "### 4b: Pick the solutions"]
LATER_STEPS = LIST_STOPS + ["### 3c: Root cause", "## Step 2: Goal", "## Step 5: Execute", "## Step 6: Feedback"]


def prompt():
    return PROMPT.read_text()


def section(heading):
    """The text under a heading, up to the next heading at the same level or higher."""
    text = prompt()
    start = text.index("\n" + heading + "\n") + 1
    level = len(heading) - len(heading.lstrip("#"))
    rest = text[start + len(heading):]
    following = re.search(r"^#{1," + str(level) + r"} ", rest, re.M)
    return heading + (rest[: following.start()] if following else rest)


def test_six_steps_in_spoken_order():
    text = prompt()
    positions = [text.index("\n" + h + "\n") for h in STEP_HEADINGS]
    assert positions == sorted(positions)
    opening = section("## Opening").lower()
    named = [opening.index(w) for w in ("locate", "goal", "root-cause the problems", "solutions", "execute", "feedback")]
    assert named == sorted(named)


def test_opens_by_asking_about_picking_up_a_map():
    text = prompt()
    assert text.index("\n## Opening\n") < text.index("\n## Step 1: Locate\n")
    opening = section("## Opening")
    ask = opening.index("pick up a map you already have")
    wait = opening.index("WAIT")
    read = opening.index("read the documents")
    assert ask < wait < read
    assert "## Picking up edits" in opening
    assert "pick up edits" not in opening


def test_reading_documents_asks_only_when_the_folder_has_nothing_useful():
    opening = section("## Opening")
    assert "one line" in opening
    assert re.search(r"holds nothing useful.*asks? once", opening, re.S | re.I)
    assert "thinner" in opening


def test_private_writing_waits_before_claudes_list():
    for heading in LIST_STOPS:
        body = section(heading)
        private = body.index("not here")
        done = body.index('"done"')
        wait = body.index('**WAIT for "done".**')
        after = body.index('After "done')
        assert private < done < wait < after, heading
        assert "End your turn" in body, heading
        shown = re.search(r"\b(build|show) your (list|picks)\b", body, re.I)
        assert shown and shown.start() > after, heading


def test_merged_lists_wait_before_moving_on():
    obstacles = section("### 3a: Obstacles")
    assert obstacles.index("**WAIT for their yes.**") < obstacles.index("**Write the map.**")
    solutions = section("### 4a: Solutions")
    assert solutions.index("**WAIT for their yes.**") < solutions.rindex("**Write the map.**")


def test_stop_rules_block_hints_and_handle_a_typed_list():
    rules = section("## How every stop works")
    assert re.search(r"(no|never) examples?", rules, re.I)
    assert "hint" in rules
    assert "gravitate" in rules
    assert re.search(r"takes? it as theirs", rules, re.I)
    assert "heard" in rules
    assert re.search(r"still show", rules, re.I)


def test_lists_are_presented_as_what_the_documents_suggest():
    rules = section("## How every stop works")
    assert "the documents and the goal suggest" in rules
    assert "never as Eric's view" in rules


def test_every_solution_tied_by_end():
    solutions = section("### 4a: Solutions")
    assert re.search(r"every solution", solutions, re.I)
    assert "tied" in solutions
    assert "missed" in solutions
    assert "already tied" in section("### 4b: Pick the solutions")
    assert "untied" in section("## Step 5: Execute")


def test_tying_takes_one_solution_per_turn_and_waits_before_4b():
    solutions = section("### 4a: Solutions")
    assert "one per turn" in solutions
    tying = solutions.index("one per turn")
    each = solutions.index("**WAIT for their answer at each one.**")
    yes = solutions.index("**WAIT for their yes.**")
    last_write = solutions.rindex("**Write the map.**")
    assert tying < each < yes < last_write


def test_goal_asks_the_first_name_once_after_the_goal():
    goal = section("## Step 2: Goal")
    confirmed = goal.index("**WAIT until the goal is confirmed.**")
    asked = goal.index("first name")
    assert confirmed < asked < goal.index("**WAIT for their name.**") < goal.index("**Write the map.**")
    assert goal.count("first name") == 1
    assert "in the same message, because the map" not in goal


def test_name_wait_only_applies_when_the_name_is_unknown():
    goal = section("## Step 2: Goal")
    ask = next(line for line in goal.splitlines() if "first name" in line)
    assert ask.startswith("If you don't know")
    assert "**WAIT for their name.**" in ask


def test_solution_picks_and_ratings_are_separate_asks():
    picks = section("### 4b: Pick the solutions")
    assert "the picks and the ratings" not in picks
    differ = picks.index("Ask where they differ")
    picks_wait = picks.index("**WAIT until the picks are agreed.**")
    ratings = picks.index("ask which ratings are wrong")
    ratings_wait = picks.index("**WAIT for their corrections.**")
    stars_wait = picks.index("**WAIT until the stars are agreed.**")
    assert differ < picks_wait < ratings < ratings_wait < stars_wait


def test_unknown_from_is_a_first_execute_item_with_no_star():
    execute = section("## Step 5: Execute")
    assert "first Execute item" in execute
    assert "no star" in execute
    assert "starred solution for it" not in execute


def test_free_form_solutions_go_in_a_holding_list():
    rules = section("## Solutions that come early")
    assert "holding list" in rules
    assert "one line" in rules
    assert "holding list" in section("### 4a: Solutions")


def test_skips_map_files():
    opening = section("## Opening")
    assert "-map.html" in opening
    assert re.search(r"skip", opening, re.I)
    assert re.search(r"names? it", opening)


def test_skip_rule_covers_copies_a_browser_downloads():
    opening = section("## Opening")
    assert "every copy of a map" in opening
    assert "`-map` followed by an optional space and `(n)` before `.html`" in opening
    assert "`x-map (1).html`" in opening
    assert "`x-map(1).html`" in opening


def test_skips_personal_notes_and_transcripts():
    opening = section("## Opening").lower()
    assert "personal notes" in opening
    assert "transcripts" in opening
    assert "skip" in opening


def test_below_the_line_offers_above_below_and_person_decides():
    locate = section("## Step 1: Locate")
    assert "above-below-the-line" in locate
    assert "/aligned:use-framework" in locate
    assert "The person decides" in locate
    assert "restart" in locate
    assert "this run ends" in locate
    assert "without pushing back" in locate
    assert "Diana" not in prompt()


def test_file_written_at_each_step_after_goal():
    for heading in LATER_STEPS:
        assert "**Write the map.**" in section(heading), heading
    assert "**Write the map.**" not in section("## Step 1: Locate")


def test_goal_gives_the_path_and_says_to_double_click():
    goal = section("## Step 2: Goal")
    assert "double-click" in goal
    assert re.search(r"\bpath\b", goal)


def test_goal_allows_stages_and_an_unknown_start():
    goal = section("## Step 2: Goal")
    assert "stage" in goal
    assert "one run per stage" in goal
    assert "first" in goal and "Execute" in goal


def test_map_file_rules():
    rules = section("## The map file")
    assert "mind-map-template.html" in rules
    assert "this framework's folder" in rules
    assert "{goal-slug}-{person}-map.html" in rules
    assert '<script id="map-data"' in rules
    assert "revision" in rules
    assert "baseline" in rules
    assert "map_id" in rules
    assert re.search(r"`map_id`.*\bonce\b", rules)


def test_map_id_comes_from_the_final_file_name():
    rules = section("## The map file")
    assert "{goal-slug}-{person}-{today's date}" not in rules
    assert "`map_id` once, to the final file name without `.html`" in rules
    assert rules.index("add `-2` before") < rules.index("`map_id` once")


def test_missing_template_stops_and_never_builds_a_page_by_hand():
    rules = section("## The map file")
    assert "If you can't find the template, say so plainly" in rules
    assert "Don't build a page by hand" in rules


def test_read_back_checks_the_shape():
    rules = section("## The map file")
    read_back = next(line for line in rules.splitlines() if "Read the data block back" in line)
    assert "non-empty `map_id`" in read_back
    assert "`children`" in read_back
    assert "`solution_ids`" in read_back
    assert re.search(r"fix it", read_back)


def test_reload_line_warns_about_unsaved_edits():
    rules = section("## The map file")
    line = next(line for line in rules.splitlines() if "reload the page" in line)
    assert "drops" in line
    assert "Not saved" in line
    assert "changes aren't being saved" in line
    assert "saving is paused" in line
    assert "Turn on saving" in line
    assert "Turn saving back on" in line
    assert "Save a copy" in line
    assert "Save to Downloads" in line
    assert "another name" in line


def test_reload_line_sends_saving_off_to_the_button_the_page_shows():
    # With saving off the page has no Save a copy until the button brings a refusal up.
    rules = section("## The map file")
    line = next(line for line in rules.splitlines() if "reload the page" in line)
    off = line[line.index("changes aren't being saved"):line.index("Not saved")]
    assert off.index("Turn on saving") < off.index("Save a copy")
    assert "refuses" in off


def test_handoff_names_the_button_and_telling_claude():
    close = section("## Close")
    assert "Turn on saving" in close
    assert "tell" in close
    assert "Turn saving back on" in section("## Picking up edits")


def test_write_says_so_when_the_file_went_backward():
    rules = section("## The map file")
    assert re.search(r"`revision` is lower than the one you last wrote", rules)
    line = next(line for line in rules.splitlines() if "lower than the one you last wrote" in line)
    assert line.index("lower than") < line.index("Say so") < line.index("**WAIT")
    assert "the higher of the file's number and the one you last wrote" in rules


def test_map_file_states_the_escape_rule_in_words_and_as_characters():
    rules = section("## The map file")
    # Stated in words, because a file tool can turn the escape itself back into the character.
    assert "six characters: a backslash, then the letters `u003c`" in rules
    assert "never the less-than sign itself" in rules
    assert "</script>" in rules
    assert re.search(r"Read the data block back.*hold no less-than sign", rules)


def test_map_file_reads_the_file_before_rewriting():
    rules = section("## The map file")
    assert re.search(r"Before (each|every) rewrite, read", rules)


def test_baseline_gets_set_on_the_first_write_too():
    every_write = section("## The map file").split("**At every write, including the first.**")[1]
    assert re.search(r"Set `baseline` to a copy.*own `baseline` empty", every_write)


def test_pick_up_covers_every_check():
    pick_up = section("## Picking up edits")
    assert "baseline" in pick_up
    assert "(1)" in pick_up
    assert "untied" in pick_up
    assert re.search(r"star.*Step 5", pick_up)
    assert "no longer exist" in pick_up
    assert "key-action table" in pick_up
    assert "Rewrite the file only when" not in pick_up
    assert "When you only list their edits" in pick_up
    assert "When you change content" in pick_up


def test_prompt_handles_a_pick_removed_on_the_page():
    pick_up = section("## Picking up edits")
    assert "Stars change only through you" not in prompt()
    assert "change picks on the page" in pick_up
    assert re.search(r"new pick.*no Step 5 row", pick_up)
    assert "whether to drop the Step 5 row" in pick_up
    assert "Agreed picks in Step 4b still get their stars from you" in pick_up
    assert "★ My picks" in prompt()


def test_second_pick_up_compares_with_what_claude_last_read():
    pick_up = section("## Picking up edits")
    only_list = pick_up[pick_up.index("When you only list their edits"):pick_up.index("When you change content")]
    assert "update `baseline` in the file to the version you just read" in only_list
    assert "leave `revision` alone" in only_list
    assert "no reload" in only_list
    assert "a later save that went astray shows as no changes" in only_list
    change = pick_up[pick_up.index("When you change content"):]
    assert "Write the map" in change
    assert "bumps `revision`" in change


def test_new_conversation_asks_which_step_when_the_map_cant_prove_it():
    pick_up = section("## Picking up edits")
    assert "no solutions means 4a" not in pick_up
    assert "no stars means 4b" not in pick_up
    assert "say what the map shows and ask which step to resume" in pick_up
    assert "doesn't record picks" in pick_up
    assert "Solutions only in the tray never count as 4a done" in pick_up


def test_no_change_reply_exists():
    pick_up = section("## Picking up edits")
    assert "doesn't have your edits" in pick_up
    assert "somewhere else" in pick_up
    assert "Downloads" in pick_up
    assert pick_up.index("Turn on saving") < pick_up.index("Downloads")


def test_prompt_no_longer_says_press_save():
    assert "press Save" not in PROMPT.read_text()
    assert "press Save" not in EXAMPLES.read_text()


def test_no_change_reply_needs_them_to_have_said_they_changed_it():
    pick_up = section("## Picking up edits")
    assert "**If the file shows no changes and they said they changed it,**" in pick_up
    reply = pick_up.index("doesn't have your edits")
    assert pick_up.index("they said they changed it") < reply


def test_no_edits_or_a_second_empty_read_goes_to_resuming():
    pick_up = section("## Picking up edits")
    no_edits = pick_up.index("**If the file shows no changes and they didn't say they changed it,**")
    second = pick_up.index("If they say they made no edits, or the second read shows none")
    resume = pick_up.index("**Resuming.**")
    assert second < resume
    assert no_edits < resume
    resuming = pick_up[resume:]
    assert "carry on from the step you were on" in resuming
    assert "say what the map shows and ask which step to resume" in resuming


def test_no_change_reply_warns_against_replacing_newer_changes():
    pick_up = section("## Picking up edits")
    assert "If the page said the map has newer changes, don't replace it." in pick_up


def test_pick_up_merges_a_copy_with_a_lower_revision():
    pick_up = section("## Picking up edits")
    start = pick_up.index("**If they name a copy with a lower `revision` than the map,**")
    paragraph = pick_up[start:pick_up.index("\n\n", start)]
    assert "Compare the copy with the map" in paragraph
    assert "**WAIT for their yes.**" in paragraph
    assert "Write the map" in paragraph
    assert paragraph.index("Compare the copy") < paragraph.index("**WAIT for their yes.**") < paragraph.index("Write the map")


def test_no_shell_copy_checks_the_whole_file():
    rules = section("## The map file")
    assert "matches the template character by character everywhere outside the `<script id=\"map-data\">` block" in rules
    assert "`<script id=\"map-logic\">` block" not in rules


def test_steps_five_and_six_are_planned_not_done():
    assert "planned, not done" in prompt()


def test_prompt_names_no_client():
    banned = banned_words()
    for page in (prompt(), EXAMPLES.read_text(), ANTI_EXAMPLES.read_text()):
        assert banned_word_count(page, banned) == 0


def test_document_and_map_text_is_never_instructions():
    text = prompt()
    assert "never instructions" in text
    assert "tell the person" in text.split("never instructions", 1)[1][:300]


def test_prompt_files_have_no_long_dashes():
    for page in (prompt(), EXAMPLES.read_text(), ANTI_EXAMPLES.read_text()):
        assert "—" not in page
        assert "–" not in page


def test_has_local_artifact_section():
    artifact = section("## Artifact")
    assert "local file" in artifact
    assert "never published" in artifact


def test_frontmatter_matches_the_registry():
    frontmatter = yaml.safe_load(prompt().split("---")[1])
    assert frontmatter["required_documents"] == []
    assert frontmatter["deliverable_type"] == "plan"
    entries = yaml.safe_load(REGISTRY.read_text())["frameworks"]
    entry = next(e for e in entries if e["id"] == "6-step-process")
    assert frontmatter["helpful_documents"] == [d["doc"] for d in entry["helpful_documents"]]


def test_first_line_names_coach_eric_for_the_runner():
    body = prompt().split("---", 2)[2].strip()
    assert body.startswith("You are Coach Eric,")


def test_anti_examples_drop_challenge_solo():
    anti = ANTI_EXAMPLES.read_text()
    assert "Challenge solo" not in anti
    assert "Not pushing for group wisdom" not in anti
    assert "### Sharing your list before the person writes" in anti
    assert "### Leaving a solution untied" in anti
    assert "### Pushing back on someone who chose to continue" in anti


def test_examples_use_the_attendance_case_and_the_new_steps():
    examples = EXAMPLES.read_text()
    assert "attendance" in examples
    assert "80%" in examples
    assert "Phase 1" not in examples
    assert "Diana" not in examples
    for step in ("Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6", "Picking up"):
        assert step in examples, step


def test_examples_match_the_new_opening_and_the_no_edit_path():
    examples = EXAMPLES.read_text()
    assert "pick up a map you already have" in examples
    assert "pick up edits" not in examples
    assert "### No edits, and they didn't say they changed it" in examples
    assert "### The second read still shows no edits" in examples
    assert "### A copy with a lower revision than the map" in examples


def test_no_edit_example_never_says_the_save_went_astray():
    examples = EXAMPLES.read_text()
    start = examples.index("### No edits, and they didn't say they changed it")
    body = examples[start:examples.index("\n### ", start + 1)]
    assert "doesn't have your edits" not in body


# The tree in the page and the prompt

def page_function(name, next_name):
    html = template()
    return html[html.index("function " + name + "("):html.index("function " + next_name + "(")]


def example_items():
    data = json.loads(SLOT.search(EXAMPLE.read_text()).group(2))
    labels = {}

    def walk(items, depth, prefix):
        for i, it in enumerate(items):
            label = prefix + (str(i + 1) if depth % 2 == 0 else chr(65 + i))
            labels[label] = it
            walk(it["children"], depth + 1, label)

    walk(data["obstacles"], 0, "")
    return data, labels


def test_every_item_offers_add_a_solution():
    body = page_function("editorActions", "openEditor")
    line = body[body.rindex("if (", 0, body.index("add('Add a solution'")):body.index("add('Add a solution'")]
    assert "item" in line
    assert "root_cause" not in line


def test_the_editor_offers_sub_obstacles_except_on_a_root_cause():
    body = page_function("editorActions", "openEditor")
    at = body.index("add('Add a sub-obstacle'")
    line = body[body.rindex("if (", 0, at):at]
    assert "!item.root_cause" in line


def test_the_editor_offers_the_root_cause_mark_only_with_no_children():
    body = page_function("editorActions", "openEditor")
    assert "Mark as root cause" in body
    at = body.index("Mark as root cause")
    line = body[body.rindex("if (", 0, at):at]
    assert "!item.children.length" in line


def test_the_delete_control_says_how_many_sub_items_go():
    body = page_function("deleteLabel", "editorActions")
    assert "L.subItemCount(map, " in body
    assert "sub-item" in body
    assert "deleteLabel(ref)" in page_function("editorActions", "openEditor")


def test_page_move_control_lists_items_by_label_and_text():
    body = page_function("moveControl", "editorActions")
    assert "L.moveTargets(map, ref.sid)" in body
    assert "L.moveTargetName(target)" in body
    assert "target.id" in body


def test_both_layouts_use_the_pure_layout_code():
    assert "L.wideLayout(" in page_function("layOutWide", "layOutNarrow")
    narrow = page_function("layOutNarrow", "scaleFor")
    assert "L.narrowPlaces(" in narrow
    assert "L.narrowLayout(" in narrow


def test_narrow_layout_sets_widths_before_it_measures():
    narrow = page_function("layOutNarrow", "scaleFor")
    assert narrow.index("style.width") < narrow.index("offsetHeight")


def test_labels_have_a_muted_bold_style():
    rule = re.search(r"\.label \{([^}]*)\}", template())
    assert rule
    assert "var(--muted)" in rule.group(1)
    assert "font-weight" in rule.group(1)


def test_template_has_no_chain_code_left():
    html = template()
    for gone in ("whys", "solution_at", "addWhy", "deleteWhy", "markRootCause", "chainPlaces", "function rowLayout"):
        assert gone not in html.replace("'whys' in item", "").replace("'solution_at' in item", ""), gone


def test_example_map_shows_real_branching():
    data, labels = example_items()
    assert "attendance" in data["goal"]["text"].lower()
    for label in ("1A", "1B", "1B1"):
        assert label in labels, label
    assert any(it["root_cause"] for it in labels.values())
    assert sum(it["root_cause"] for it in labels["1"]["children"] + labels["1B"]["children"]) >= 2
    assert any(it["children"] and it["solution_ids"] for it in labels.values())
    assert data["baseline"]["obstacles"] == data["obstacles"]


def test_prompt_json_shape_is_the_tree():
    rules = section("## The map file")
    block = rules[rules.index("```json"):rules.index("```\n", rules.index("```json") + 8)]
    assert '"root_cause": false' in block
    assert '"children": [' in block
    assert '"solution_ids": ["s1"]' in block
    data = json.loads(block[len("```json"):])
    top = data["obstacles"][0]
    assert sorted(top) == ["children", "id", "root_cause", "solution_ids", "text"]
    assert sorted(top["children"][0]) == sorted(top)
    assert top["children"][0]["root_cause"] is True


def test_prompt_no_longer_names_whys_or_solution_at():
    text = prompt()
    assert "whys" not in text
    assert "solution_at" not in text
    assert "why:" not in text
    assert "end of the chain" not in text
    for page in (EXAMPLES.read_text(), ANTI_EXAMPLES.read_text()):
        assert "whys" not in page
        assert "solution_at" not in page
        assert "end of the chain" not in page


def test_read_back_checks_the_tree_at_every_depth():
    rules = section("## The map file")
    read_back = next(line for line in rules.splitlines() if "Read the data block back" in line)
    assert "`children`" in read_back
    assert "`solution_ids`" in read_back
    assert "`root_cause`" in read_back
    assert "every depth" in read_back
    assert "`id`" in read_back
    assert "`text`" in read_back


def test_prompt_explains_labels_and_says_never_to_store_them():
    rules = section("## The map file")
    assert "`1B3`" in rules
    assert "AA" in rules
    assert re.search(r"Never store a label", rules)
    assert "Solutions get no labels" in rules


def test_prompt_says_where_solutions_draw_and_what_delete_does():
    rules = section("## The map file")
    assert "directly under" in rules
    assert "next column out" in rules
    assert "tray" in rules
    assert "everything under it" in rules


def test_root_cause_step_builds_children_and_splits_two_reasons():
    step = section("### 3c: Root cause")
    assert "becomes a child of the item" in step
    assert "two different reasons" in step
    assert "its own child" in step
    assert "one question per turn" in step
    assert "Stop when the person can act on the answer" in step
    assert "The person can stop it sooner" in step
    assert "**WAIT at each why and at each root cause.**" in step
    assert "**Write the map.**" in step
    assert "`root_cause` to true" in step
    assert '"1B"' in step or "1B" in step


def test_tying_goes_on_the_item_it_gets_past():
    solutions = section("### 4a: Solutions")
    line = next(line for line in solutions.splitlines() if "usually a root cause" in line)
    assert "the item it gets past" in line
    assert "every solution gets tied" in solutions
    assert "one per turn" in solutions


def test_pick_up_compares_by_id_and_names_a_moved_solution():
    pick_up = section("## Picking up edits")
    line = next(line for line in pick_up.splitlines() if "counts as a change" in line)
    assert "another item" in line
    assert "`id`" in line
    assert "label" in line


def test_examples_show_branches_labels_and_a_moved_solution():
    examples = EXAMPLES.read_text()
    assert "### 3c: Two reasons become two branches" in examples
    assert "### 4a: A solution on a specific item" in examples
    assert "### A solution moved to another item" in examples
    assert "1B" in examples


def test_anti_examples_cover_two_reasons_in_one_item():
    anti = ANTI_EXAMPLES.read_text()
    assert "### Putting two reasons in one item" in anti
    assert "### Adding under a root cause" in anti


def test_pick_up_uses_current_labels_and_names_deleted_items_by_text():
    pick_up = section("## Picking up edits")
    assert "Use labels from the file as it is now" in pick_up
    assert "Name a deleted item by its text and say how many sub-items went with it" in pick_up
    assert "stopped being a root cause" in pick_up
    assert "3c may need another look" in pick_up


def test_stale_copy_comparison_matches_by_id_and_reissues_clashing_ids():
    pick_up = section("## Picking up edits")
    line = next(line for line in pick_up.splitlines() if "lower `revision`" in line)
    assert "Match items by `id`" in line
    assert "new id" in line
    assert "by their text" in line


def test_read_back_names_the_item_fields_exactly():
    rules = section("## The map file")
    read_back = next(line for line in rules.splitlines() if "Read the data block back" in line)
    assert "`id` and `text` as strings" in read_back
    assert "`solution_ids` and `children` as lists even when they're empty" in read_back


def test_root_cause_is_set_only_after_the_person_confirms():
    step = section("### 3c: Root cause")
    assert "set its `root_cause` to true only after they confirm" in step
    assert "If they say no, leave it false and keep asking why." in step


def test_mid_run_edits_point_to_the_pick_up_checks():
    rules = section("## The map file")
    line = next(line for line in rules.splitlines() if "differs from `baseline`" in line)
    assert "Picking up edits" in line


def test_step_five_row_is_written_with_the_person():
    pick_up = section("## Picking up edits")
    assert "you write the Step 5 row with the person" in pick_up
