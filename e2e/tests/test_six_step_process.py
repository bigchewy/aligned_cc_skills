"""Static checks on the 6-step process mind map page and its example data."""

import json
import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO / "frameworks" / "6-step-process"
TEMPLATE = FRAMEWORK / "mind-map-template.html"
EXAMPLE = REPO / "e2e" / "fixtures" / "six-step-example-map.json"

# Optional list of words that must stay out of shipped files, one per line. It lives
# outside the repo because this repo is distributed. Without it, those checks skip.
BANNED_WORDS_FILE = Path.home() / ".claude" / "aligned-banned-words.txt"


def banned_words():
    if not BANNED_WORDS_FILE.exists():
        pytest.skip("no local banned-words list")
    return set(BANNED_WORDS_FILE.read_text().lower().split())


def template():
    return TEMPLATE.read_text()


def test_template_has_its_three_script_blocks_in_order():
    html = template()
    assert html.index('<script id="map-logic">') < html.index('<script id="map-store">') < html.index('<script id="map-page">')


def test_template_has_no_wrapper_tags():
    html = template()
    assert not re.search(r"</?(html|head|body|title)[\s>]", html, re.I)
    assert html.startswith("<!DOCTYPE html>\n")


def test_template_sets_its_language_by_script_and_leaves_the_title_to_the_viewer():
    html = template()
    assert "document.documentElement.lang = 'en'" in html
    assert html.index("document.documentElement.lang") < html.index("<style>")
    assert "document.title" not in html


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


def whole_function(name):
    """The source of one function in the page code, up to the next function at the same indent."""
    html = template()
    page = html[html.index('id="map-page"'):]
    match = re.search(r"\n  (async )?function " + name + r"\(.*?\n  \}\n", page, re.S)
    assert match, name
    return match.group(0)


def test_saving_sits_in_the_top_right_and_the_page_has_no_footer():
    html = template()
    body = html[html.index("</style>"):html.index('<script id="map-logic">')]
    assert "<footer" not in body
    header = body[body.index("<header>"):body.index("</header>")]
    assert 'id="dirty"' not in html
    assert "el.dirty" not in html
    assert 'id="save"' not in html and "el.save" not in html
    assert "Click an item, then press a + to add under it. Double-click to change its words. Drag it onto a box or between two to move it." in header
    # The status takes the far right, after every other control.
    assert header.rindex("<button") < header.index('id="save-status"')


def test_save_messages_appear_under_the_top_right_controls():
    html = template()
    body = html[html.index("</style>"):html.index('<script id="map-logic">')]
    assert body.index("</header>") < body.index('id="notices"') < body.index('id="workspace"')
    notices = body[body.index('id="notices"'):body.index('id="workspace"')]
    assert 'id="message"' in notices
    assert "browser-note" not in html
    assert re.search(r"#notices \{[^}]*text-align: right", html)


def test_page_has_no_root_cause_tray_or_add_obstacle_button():
    for html in (template(), EXAMPLE.read_text()):
        for gone in ("root_cause", "root-toggle", "setRootCause", "canBeRootCause", ".item.root", "Root cause",
                     "root cause", "unplaced", "#tray", 'id="tray"', "el.tray", "drawTray", "add-obstacle",
                     "Add an obstacle<", "hasChildOfKind"):
            assert gone not in html, gone


def test_empty_map_hint_points_at_the_goal():
    html = template()
    header = html[html.index("<header>"):html.index("</header>")]
    assert re.search(r'id="first-hint"[^>]*>Click the goal, then press a \+ to add the first obstacle or solution\.', header)


def test_toolbar_offers_a_star_button_with_no_words():
    html = template()
    body = html[html.index("</style>"):html.index('<script id="map-logic">')]
    tools = body[body.index('id="item-tools"'):]
    star = tools[tools.index('id="star-button"'):tools.index("</button>", tools.index('id="star-button"'))]
    assert "<svg" in star and "currentColor" in star
    assert re.sub(r"<svg.*?</svg>", "", star, flags=re.S).split(">", 1)[1].strip() == ""
    assert "This is one of my picks" not in html and 'type="checkbox"' not in html
    assert "L.canPick(map, " in whole_function("showControls")
    assert "aria-pressed" in whole_function("showControls")
    assert "L.setStar(map, selected.id," in html
    assert "['star-button', 'Star']" in html


def test_header_has_no_picks_key():
    html = template()
    assert "My picks" not in html and "picks-key" not in html


def test_status_line_comes_from_the_store_block():
    assert "S.hostedStatus(" in whole_function("showStatus")
    assert "showStatus()" in whole_function("render")


def test_close_warning_is_unchanged():
    assert "L.shouldWarnOnClose(function () { finishTyping(); saveNotes(); }, isDirty)" in template()


def test_no_save_file_picker():
    assert "showSaveFilePicker" not in template()


def test_goal_has_one_text_box():
    assert "goalInput" not in template()
    assert "goal-line" not in template()
    assert "L.setGoal(map, { text: text })" in whole_function("finishTyping")


def test_prompt_json_goal_has_text_and_detail_only():
    rules = section("## The map")
    assert '"goal": {"text": "", "detail": ""}' in rules
    assert '"from": ""' not in rules


def test_goal_nudges_toward_a_number_but_takes_a_qualitative_goal():
    goal = section("## Step 2: Goal")
    assert "with a number if you can" in goal
    assert "Nudge once" in goal
    assert "qualitative goal is fine" in goal


def test_goal_questions_only_come_when_the_goal_is_unclear():
    goal = section("## Step 2: Goal")
    help_line = next(line for line in goal.splitlines() if line.startswith("**If they don't know the goal"))
    assert "a few at a time" in help_line
    assert "one question at a time" not in help_line
    assert "Don't mention obstacles or solutions" in help_line
    assert goal.index("What outcome do you want") < goal.index(help_line)
    # No extra step comes before the goal.
    assert "clarifying" not in section("## Opening").lower()


def test_goal_explanation_goes_in_the_appendix_with_nothing_invented():
    goal = section("## Step 2: Goal")
    line = next(l for l in goal.splitlines() if "`goal.detail`" in l)
    assert "a paragraph or two" in line
    assert "appendix" in line
    assert "Don't invent" in line
    assert "obstacles or solutions" in line


def test_people_can_type_in_the_appendix_and_claude_keeps_their_words():
    rules = section("## The map")
    assert "the page never writes it" not in rules
    assert "People can also type in it on the page" in rules
    assert "type in it" in section("## Step 2: Goal")


def test_advisor_check_comes_after_the_goal_before_the_first_write():
    goal = section("## Step 2: Goal")
    assert goal.index("**WAIT until the goal is confirmed.**") < goal.index("**Check the advisor.**") < goal.index("**Write the map.**")


def test_advisor_check_defaults_to_the_current_advisor_and_lets_the_person_choose():
    goal = section("## Step 2: Goal")
    assert "skills/_shared/resolve-advisor-source.md" in goal
    assert "`best_for`" in goal and "`not_for`" in goal
    assert "clearly" in goal
    assert "say nothing about advisors" in goal
    assert "**WAIT for their answer.**" in goal[goal.index("**Check the advisor.**"):]
    assert "skills/_shared/advisor-runner.md" in goal and "`greeting_mode=silent`" in goal


def test_a_new_advisor_changes_the_voice_and_never_the_process():
    goal = section("## Step 2: Goal")
    assert "The six steps, every WAIT and the private lists stay exactly as written" in goal


def test_prompt_puts_the_goal_in_one_sentence():
    goal = section("## Step 2: Goal")
    assert "one sentence" in goal
    assert "starting point not known yet" in goal


def test_template_copy_has_no_long_dashes():
    for page in (template(), EXAMPLE.read_text()):
        assert "—" not in page
        assert "–" not in page


def test_template_has_quiet_zoom_controls():
    html = template()
    for control in ("zoom-out", "zoom-in", "zoom-fit"):
        assert re.search(r'<button type="button" class="quiet" id="' + control + '"', html), control


def test_template_no_longer_draws_a_missing_solution():
    html = template()
    assert "makeMissing" not in html
    assert "This solution is missing" not in html
    assert "kind: 'missing'" not in html
    assert ".item.missing" not in html


def test_template_has_no_repeated_solution_code_left():
    html = template()
    for gone in ("repeatCount", "untiedSolutionIds", "solutionsOn", "sideOf", "moveSolution", "map.solutions",
                 "This solution is on", ".repeat {", ".item.repeat"):
        assert gone not in html, gone


def test_template_has_no_phone_layout_left():
    html = template()
    for gone in ("narrowLayout", "narrowPlaces", "isNarrow", "layOutNarrow", "max-width: 759px", "matchMedia"):
        assert gone not in html, gone


def test_template_is_always_light():
    html = template()
    assert ":root {" in html
    assert "prefers-color-scheme" not in html
    assert "color-scheme: light;" in html
    root = re.search(r":root \{(.*?)\}", html, re.S).group(1)
    assert "--bg: #ffffff;" in root and "--box: #ffffff;" in root
    body_rule = re.search(r"\nbody \{(.*?)\}", html, re.S)
    assert body_rule and "background: var(--bg)" in body_rule.group(1)


def test_the_goal_is_a_white_box_with_an_orange_border_and_round_corners():
    html = template()
    goal = re.search(r"\.item\.goal \{(.*?)\}", html, re.S).group(1)
    assert "background: var(--box)" in goal
    assert "border: 2px solid var(--obstacle-line)" in goal
    assert "border-radius: 28px" in goal


def test_item_boxes_are_wide_so_text_wraps_less():
    html = template()
    assert "var BOX_W = 240;" in html


def test_template_ships_no_drawn_map():
    assert '<div id="canvas"></div>' in template()


def test_example_data_is_a_flat_document_the_page_can_read():
    doc = json.loads(EXAMPLE.read_text())
    assert doc["version"] == 1
    assert "attendance" in doc["goal"]["text"].lower()
    assert doc["items"]
    assert "baseline" not in doc


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


def test_every_solution_placed_by_end():
    solutions = section("### 4a: Solutions")
    assert re.search(r"every solution", solutions, re.I)
    assert "placed" in solutions
    assert "missed" in solutions
    assert "directly under the goal" in section("## Step 5: Execute")


def test_placing_takes_one_solution_per_turn_and_waits_before_4b():
    solutions = section("### 4a: Solutions")
    assert "one per turn" in solutions
    placing = solutions.index("one per turn")
    each = solutions.index("**WAIT for their answer at each one.**")
    yes = solutions.index("**WAIT for their yes.**")
    last_write = solutions.rindex("**Write the map.**")
    assert placing < each < yes < last_write


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


def test_goal_allows_stages_and_an_unknown_start():
    goal = section("## Step 2: Goal")
    assert "stage" in goal
    assert "one run per stage" in goal
    assert "first" in goal and "Execute" in goal


def test_missing_template_stops_and_never_builds_a_page_by_hand():
    rules = section("## The map")
    assert "If you can't find the template, say so plainly" in rules
    assert "Don't build a page by hand" in rules


def test_pick_up_covers_every_check():
    pick_up = section("## Picking up edits")
    assert "baseline" in pick_up
    assert "(1)" not in pick_up
    assert "directly under the goal" in pick_up
    assert re.search(r"star.*Step 5", pick_up)
    assert "key-action table" in pick_up
    assert "When you only list their edits" in pick_up
    assert "When you change content" in pick_up


def test_prompt_handles_a_pick_removed_on_the_page():
    pick_up = section("## Picking up edits")
    assert "Stars change only through you" not in prompt()
    assert "change picks on the page" in pick_up
    assert re.search(r"new pick.*no Step 5 row", pick_up)
    assert "whether to drop the Step 5 row" in pick_up
    assert "Agreed picks in Step 4b still get their stars from you" in pick_up
    assert "My picks" not in prompt()
    assert "clicking the star on a solution" in pick_up


def test_second_pick_up_compares_with_what_claude_last_read():
    pick_up = section("## Picking up edits")
    only_list = pick_up[pick_up.index("When you only list their edits"):pick_up.index("When you change content")]
    assert "pinned `set` of `maps/baseline` to `maps/main` as you just read it" in only_list
    assert "Touch nothing else" in only_list
    assert "shows only newer edits" in only_list
    change = pick_up[pick_up.index("When you change content"):]
    assert "Write the map" in change


def test_new_conversation_asks_which_step_when_the_map_cant_prove_it():
    pick_up = section("## Picking up edits")
    assert "no solutions means 4a" not in pick_up
    assert "no stars means 4b" not in pick_up
    assert "say what the map shows and ask which step to resume" in pick_up
    assert "doesn't record picks" in pick_up
    assert "If the only solutions are directly under the goal, that doesn't show 4a ran, and 4a nudges them when it runs." in pick_up
    assert "never count as 4a done" not in pick_up


def test_prompt_no_longer_says_press_save():
    assert "press Save" not in PROMPT.read_text()
    assert "press Save" not in EXAMPLES.read_text()


def test_no_change_reply_needs_them_to_have_said_they_changed_it():
    pick_up = section("## Picking up edits")
    assert "**If the map shows no changes and they said they changed it,**" in pick_up
    reply = pick_up.index("doesn't show your edits")
    assert pick_up.index("they said they changed it") < reply


def test_no_edits_or_a_second_empty_read_goes_to_resuming():
    pick_up = section("## Picking up edits")
    no_edits = pick_up.index("**If the map shows no changes and they didn't say they changed it,**")
    second = pick_up.index("If they say they made no edits, or the second read shows none")
    resume = pick_up.index("**Resuming.**")
    assert second < resume
    assert no_edits < resume
    resuming = pick_up[resume:]
    assert "carry on from the step you were on" in resuming
    assert "say what the map shows and ask which step to resume" in resuming


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
    assert "### Leaving a solution on the goal without asking" in anti
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


def test_no_edit_example_never_says_the_save_went_astray():
    examples = EXAMPLES.read_text()
    start = examples.index("### No edits, and they didn't say they changed it")
    body = examples[start:examples.index("\n### ", start + 1)]
    assert "doesn't show your edits" not in body


# The tree in the page and the prompt

def page_function(name, next_name):
    html = template()
    return html[html.index("function " + name + "("):html.index("function " + next_name + "(")]


def example_items():
    data = page_store("return S.inflate(D.doc);", doc=json.loads(EXAMPLE.read_text()))
    labels = {}

    def walk(items, depth, prefix, counter):
        for it in items:
            if it["kind"] == "solution":
                walk(it["children"], depth, prefix, counter)
                continue
            label = prefix + (str(counter[0] + 1) if depth % 2 == 0 else chr(65 + counter[0]))
            counter[0] += 1
            labels[label] = it
            walk(it["children"], depth + 1, label, [0])

    walk(data["obstacles"], 0, "", [0])
    return data, labels


def every_item(items):
    for it in items:
        yield it
        yield from every_item(it["children"])


def test_the_plus_buttons_come_from_the_plus_rules():
    body = whole_function("showControls")
    assert "L.canAdd(map, parentId, 'obstacle')" in body
    assert "L.canAdd(map, parentId, 'solution')" in body
    assert "'Add an obstacle under '" in body
    assert "'Add a solution under '" in body


def test_the_delete_control_is_a_trash_icon_with_no_words():
    html = template()
    tools = html[html.index('id="item-tools"'):html.index('<script id="map-logic">')]
    button = tools[tools.index('id="delete-item"'):tools.index("</button>", tools.index('id="delete-item"'))]
    assert "<svg" in button and "currentColor" in button
    assert "deleteLabel" not in html and "sub-item" not in html
    assert "['delete-item', 'Delete']" in html


def test_the_delete_card_is_a_small_white_card_with_one_red_button():
    html = template()
    css = html[html.index("<style>"):html.index("</style>")]
    card_css = css[css.index("#delete-card {"):]
    card_css = card_css[:card_css.index("}")]
    assert "position: fixed" in card_css and "border-radius" in card_css and "box-shadow" in card_css
    assert "background: var(--box)" in card_css
    yes_css = css[css.index("#delete-yes {"):]
    yes_css = yes_css[:yes_css.index("}")]
    assert "color: #fff" in yes_css and "background:" in yes_css
    assert "#delete-yes:focus-visible" in css
    markup = html[html.index('id="delete-card"'):html.index('<script id="map-logic">')]
    assert 'role="alertdialog"' in html[html.index('id="delete-card"') - 20:html.index('id="delete-card"') + 120]
    assert markup.count("<button") == 1
    inside = markup[markup.index(">") + 1:markup.index("</div>")]
    words = re.sub(r"<[^>]+>", " ", inside)
    assert " ".join(words.split()) == "Confirm Delete Delete"


def test_page_has_no_form_editor_left():
    html = template()
    for gone in ("openEditor", "editorActions", "moveControl", "closeEditor", "commitEdit", "cancelEdit",
                 "positionEditor", "afterCommit", "actionButton", "labeled(", 'id="editor"', "#editor", "el.editor",
                 "Click any item", "Click here"):
        assert gone not in html, gone


def test_page_has_no_move_to():
    page = template()
    for gone in ("move-to", "move-control", "moveControl", "showMoveList", "moveListKey", "moveTargets", "Move to",
                 "<select", "subItems", "checkbox"):
        assert gone not in page, gone
    assert "canMove" in page


def test_the_drag_ghost_sits_outside_the_canvas_and_takes_no_pointer():
    html = template()
    body = html[html.index("</style>"):html.index('<script id="map-logic">')]
    workspace = body[body.index('id="workspace"'):body.index('id="typing"')]
    assert 'id="drag-ghost"' in body and 'id="drag-ghost"' not in workspace
    rule = re.search(r"#drag-ghost \{([^}]*)\}", html)
    assert rule and "pointer-events: none" in rule.group(1) and "position: fixed" in rule.group(1)
    target = re.search(r"\.drop-target \{([^}]*)\}", html)
    assert target and "var(--focus)" in target.group(1)
    dragging = re.search(r"body\.dragging[^{]*\{([^}]*)\}", html)
    assert dragging and "user-select: none" in dragging.group(1)


def test_a_stacked_ghost_is_drawn_with_css_and_no_words():
    rule = re.search(r"#drag-ghost\.stacked \{([^}]*)\}", template())
    assert rule and "box-shadow" in rule.group(1) and "content" not in rule.group(1)


def test_items_show_they_can_be_grabbed_but_the_goal_does_not():
    html = template()
    rule = re.search(r"\.item:not\(\.goal\) \{([^}]*)\}", html)
    assert rule and "cursor: grab" in rule.group(1)


def test_the_first_write_tells_the_person_they_can_drag():
    first_write = next(line for line in section("## Step 2: Goal").splitlines() if "This is the first write" in line)
    assert "they can drag an item onto a box to move it, or between two others to reorder it" in first_write


def test_the_data_rules_say_how_to_place_an_item_between_two_others():
    rules = section("## The map")
    assert "`order` may be a decimal" in rules
    assert "use a value between theirs" in rules


def test_the_drop_line_is_blue_sits_in_the_unscaled_frame_and_takes_no_pointer():
    html = template()
    rule = re.search(r"#drop-line \{([^}]*)\}", html)
    assert rule and "var(--focus)" in rule.group(1) and "pointer-events: none" in rule.group(1)
    assert '<div id="canvas"></div><div id="drop-line" aria-hidden="true" hidden></div></div>' in html


def test_solutions_under_the_goal_get_one_nudge_unless_they_said_it_belongs():
    said = "unless they already said in this conversation that it belongs there"
    step5 = section("## Step 5: Execute")
    assert "nudge it once" in step5 and said in step5
    pick_up = section("## Picking up edits")
    assert "directly under the goal toward an obstacle once" in pick_up and said in pick_up


def test_the_example_says_that_obstacle_sits_there():
    assert "because that obstacle sits there" in EXAMPLES.read_text()
    assert "because the deepest obstacle sits there" not in EXAMPLES.read_text()


def test_the_controls_sit_outside_the_canvas():
    html = template()
    body = html[html.index("</style>"):html.index('<script id="map-logic">')]
    workspace = body[body.index('id="workspace"'):body.index('id="typing"')]
    for part in ('id="typing"', 'id="plus-obstacle"', 'id="plus-solution"', 'id="item-tools"'):
        assert part in body, part
        assert part not in workspace, part


def test_selecting_never_draws_the_map_or_asks_for_a_write():
    for name in ("select", "markSelected", "showControls", "positionControls"):
        body = whole_function(name)
        assert "render()" not in body, name
        assert "setMap(" not in body, name


def test_the_layout_uses_the_pure_layout_code():
    assert "L.wideLayout(" in page_function("layOutWide", "scaleFor")


def test_labels_have_a_muted_bold_style():
    rule = re.search(r"\.label \{([^}]*)\}", template())
    assert rule
    assert "var(--muted)" in rule.group(1)
    assert "font-weight" in rule.group(1)


def test_template_has_no_chain_code_left():
    html = template()
    for gone in ("whys", "solution_at", "addWhy", "deleteWhy", "markRootCause", "chainPlaces", "function rowLayout"):
        assert gone not in html, gone


def test_example_map_shows_real_branching():
    data, labels = example_items()
    assert "attendance" in data["goal"]["text"].lower()
    for label in ("1A", "1B", "1B1"):
        assert label in labels, label


def test_example_map_shows_the_new_format():
    data, _ = example_items()
    assert "solutions" not in data
    items = list(every_item(data["obstacles"]))
    assert "unplaced" not in data
    for it in items:
        assert sorted(it) == ["children", "id", "kind", "star", "text"]
    solutions = [it for it in items if it["kind"] == "solution"]
    assert any(c["kind"] == "obstacle" for it in solutions for c in it["children"]), "an obstacle under a solution"
    assert any(c["kind"] == "solution" for it in solutions for c in it["children"]), "a solution under a solution"
    assert any(it["text"] == "Run a monthly pulse survey" for it in items), "the pulse survey is on the map"
    assert any(it["star"] for it in solutions), "a pick"
    texts = [it["text"] for it in items]
    assert len(texts) == len(set(texts)), "no repeated items"
    ids = {it["id"] for it in solutions}
    assert all(row["solution_id"] in ids for row in data["execute"])
    assert all(i in ids for action in data["key_actions"] for i in action["solution_ids"])
    assert data["execute"], "plan rows"


def test_prompt_no_longer_names_solution_ids_or_a_solutions_list():
    data = map_json()
    assert "solutions" not in data
    assert "solution_ids" not in next(iter(data["items"].values()))
    assert "solution_ids" in data["key_actions"][0]
    text = prompt()
    assert "`solutions`" not in text
    assert "sit on an item" not in text
    for line in text.splitlines():
        if "`solution_ids`" in line:
            assert "key_actions" in line, line


def test_prompt_asks_when_a_solution_serves_two_obstacles():
    solutions = section("### 4a: Solutions")
    assert "A solution that serves several obstacles sits on each one" not in prompt()
    assert "which obstacle it belongs to, or whether it should be two separate solutions" in solutions
    assert "Never write two items with the same text without asking" in solutions


def test_prompt_explains_numbers_under_solutions():
    rules = section("## The map")
    assert ("An obstacle under a solution continues the numbering of the nearest obstacle above it, so 1B2 can be "
            "an answer to why on 1B or an obstacle in the way of a solution on 1B. The map shows which.") in rules


def test_prompt_lets_any_item_hold_either_kind():
    rules = section("## The map")
    assert "Any item can hold obstacles and solutions, at any depth, and so can the goal" in rules
    assert "same five fields" in rules
    assert "Only obstacles sit at the top level" not in rules
    assert "A solution can hold only obstacles" not in rules


def test_prompt_never_marks_a_root_cause():
    for page in (prompt(), EXAMPLES.read_text(), ANTI_EXAMPLES.read_text()):
        assert "root_cause" not in page
        assert "unplaced" not in page
    step = section("### 3c: Root cause")
    assert "Don't mark anything as a root cause" in step
    assert "The person decides when to stop" in step
    assert "becomes a child of the item" in step
    assert "**WAIT at each why.**" in step
    assert "### 3c: Root cause" in prompt()
    assert "## Step 3: Root-cause the problems" in prompt()
    assert "stopped being a root cause" not in prompt()
    assert "Is that it?" not in EXAMPLES.read_text()


def test_prompt_puts_early_solutions_under_the_goal():
    rules = section("## Solutions that come early")
    assert "directly under the goal" in rules
    assert "one line" in rules
    assert "the obstacle it gets past" in rules
    solutions = section("### 4a: Solutions")
    assert "directly under the goal" in solutions
    assert "one per turn" in solutions
    for page in (prompt(), EXAMPLES.read_text(), ANTI_EXAMPLES.read_text()):
        assert "holding list" not in page
        assert not re.search(r"\btray\b", page)


def test_solutions_go_under_the_deepest_obstacle_they_get_past():
    assert "the deepest obstacle it gets past" in section("### 4a: Solutions")
    assert "usually a root cause" not in prompt()
    assert "usually a root cause" not in EXAMPLES.read_text()
    assert "the deepest obstacle it gets past" in EXAMPLES.read_text()


def test_pick_up_covers_moved_obstacles():
    pick_up = section("## Picking up edits")
    line = next(line for line in pick_up.splitlines() if "by `id` and parent" in line)
    assert "moved obstacle" in line
    assert "what's under" in line
    assert "moved solution" in line
    assert "deleted item" in line
    assert "what went with" in line


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


def test_prompt_explains_labels_and_says_never_to_store_them():
    rules = section("## The map")
    assert "`1B3`" in rules
    assert "AA" in rules
    assert re.search(r"Never store a label", rules)
    assert "Solutions get no labels" in rules


def test_prompt_says_what_delete_does():
    rules = section("## The map")
    assert "everything under it" in rules
    assert "Execute row" in rules


def test_root_cause_step_builds_children_and_splits_two_reasons():
    step = section("### 3c: Root cause")
    assert "becomes a child of the item" in step
    assert "two different reasons" in step
    assert "its own child" in step
    assert "one question per turn" in step
    assert "When the person can act on the answer" in step
    assert "**Write the map.**" in step
    assert '"1B"' in step or "1B" in step


def test_placing_goes_under_the_item_it_gets_past():
    solutions = section("### 4a: Solutions")
    line = next(line for line in solutions.splitlines() if "the deepest obstacle it gets past" in line)
    assert "If the person names a different item, put it there" in line
    assert "every solution gets placed" in solutions
    assert "one per turn" in solutions


def test_pick_up_compares_by_id_and_names_a_moved_solution():
    pick_up = section("## Picking up edits")
    line = next(line for line in pick_up.splitlines() if "by `id` and parent" in line)
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
    assert "### Adding under a root cause" not in anti


def test_pick_up_uses_current_labels_and_names_deleted_items_by_text():
    pick_up = section("## Picking up edits")
    assert "Use labels from the map as it is now" in pick_up
    assert "Name a deleted item by its text and say how many sub-items went with it" in pick_up
    assert "3c may need another look" not in pick_up


def test_template_defines_each_logic_function_once():
    logic = template()[template().index('id="map-logic"'):template().index('id="map-store"')]
    names = re.findall(r"^  (?:async )?function (\w+)\(", logic, re.M)
    assert len(names) == len(set(names)), [n for n in names if names.count(n) > 1]


def test_examples_no_longer_say_a_root_cause_ends_its_branch():
    assert "ends its branch" not in EXAMPLES.read_text()
    assert "ends that line of asking why" not in EXAMPLES.read_text()


def test_mid_run_edits_point_to_the_pick_up_checks():
    rules = section("## The map")
    line = next(line for line in rules.splitlines() if "differs from `maps/baseline`" in line)
    assert "Picking up edits" in line


def test_step_five_row_is_written_with_the_person():
    pick_up = section("## Picking up edits")
    assert "you write the Step 5 row with the person" in pick_up


def test_lines_carry_their_kind():
    page = page_function("drawLines", "drawMap")
    assert "<path class=\"' + kind" in page
    assert "line.kind + ' drag-source' : line.kind" in page
    css = template()
    assert "#lines path.obstacle" in css
    assert "#lines path.solution" in css


def test_template_defines_line_colors_for_the_one_theme():
    html = template()
    assert "--obstacle-line: #ef6c46;" in html and "--solution-line: #77c94b;" in html
    assert "--focus: #3b5bdb;" in html
    assert re.search(r"#lines path\.obstacle\s*\{[^}]*var\(--obstacle-line\)", html)
    assert re.search(r"#lines path\.solution\s*\{[^}]*var\(--solution-line\)", html)


def test_prompt_lets_a_solution_sit_under_a_solution_and_explains_the_star():
    text = prompt()
    assert "a solution has no solution directly under it" not in text
    assert "Any item can hold obstacles and solutions" in text
    assert "click the star in the toolbar on any solution to add or remove a pick" in text
    assert "a star marks one of their picks" in text


# The map as an artifact

def test_template_holds_nothing_of_the_local_file():
    html = template()
    for gone in ("showOpenFilePicker", "indexedDB", "createWritable", "Save a copy", "Turn on saving", "map_id",
                 "map-data"):
        assert gone not in html, gone


def test_outside_claude_the_page_says_where_the_map_opens():
    html = template()
    assert re.search(r'<div id="outside-claude" hidden>\s*<h1>This map opens inside Claude\.</h1>', html)
    page = html[html.index('id="map-page"'):]
    check = page.index("window.claude === undefined")
    # The check comes before any map data or drawing, and nothing after it runs.
    assert check < page.index("S.inflate({})") and check < page.index("function render()")
    guard = page[check:page.index("S.inflate({})")]
    assert "'header, #notices, #workspace'" in guard and "return;" in guard


def test_the_delete_card_words_live_only_in_the_markup():
    html = template()
    assert "Confirm Delete</span>" in html and ">Delete</button>" in html
    page = html[html.index('id="map-page"'):]
    assert "'delete-title'" not in page
    assert "el['delete-yes'].textContent" not in page


def map_json():
    rules = section("## The map")
    start = rules.index("```json") + len("```json")
    return json.loads(rules[start:rules.index("```", start)])


def test_prompt_stops_plainly_without_the_artifact_tools():
    opening = section("## Opening")
    assert "both the Artifact and ArtifactData tools" in opening
    check = opening.index("both the Artifact and ArtifactData tools")
    assert check < opening.index("We'll work through six steps")
    assert "needs Claude's artifact tools" in opening
    assert "Then stop" in opening
    assert check < opening.index("Then stop") < opening.index("We'll work through six steps")


def test_prompt_counts_a_tool_it_can_load_before_deciding():
    opening = section("## Opening")
    load = opening.index("A tool you can load counts as one you have, so load it before deciding.")
    assert load < opening.index("needs Claude's artifact tools") < opening.index("Then stop")


def test_prompt_stops_plainly_when_a_publish_fails():
    rules = section("## The map")
    path_try = rules.index("Publish that file directly, by its path")
    refused = rules.index("If that's refused")
    whole = rules.index("read the whole file")
    write = rules.index("write it unchanged to a working or temporary folder")
    copy = rules.index("publish that copy")
    stop = rules.index("If that fails too, say so plainly and stop.")
    assert path_try < refused < whole < write < copy < stop
    assert "If a publish fails" not in rules


def test_prompt_publishes_the_template_itself_with_its_capabilities():
    rules = section("## The map")
    assert "mind-map-template.html" in rules
    assert "this framework's folder" in rules
    assert "Publish that file directly" in rules
    assert '{"db": {}}' in rules
    assert '"user"' not in rules
    assert "title" in rules
    assert "Read all of" in rules


def test_prompt_gives_a_second_map_its_own_link():
    rules = section("## The map")
    assert "For a second map, tell them to start a new conversation and run the framework again there." in rules
    # The tool reuses a link when one path publishes twice in a conversation, so the refusal stays as the guard.
    assert "already holds a map" in rules
    assert "second map in one conversation" not in rules
    assert "for a second map" not in section("## Opening")
    assert "when a publish by path is refused" in section("## Opening")


def test_prompt_first_write_batches_main_and_baseline():
    rules = section("## The map")
    first = rules[rules.index("**The first write.**"):rules.index("**Every point marked")]
    assert "`batch`" in first
    assert "`maps/main`" in first
    assert "`maps/baseline`" in first
    assert "`set`" in first
    assert "no `if_version`" in first


def test_prompt_each_write_reads_then_pins_if_version():
    rules = section("## The map")
    each = rules[rules.index("**Every point marked"):rules.index("**The data.**")]
    read = each.index("read `maps/main` and `maps/baseline`")
    pin = each.index("`if_version`")
    batch = each.index("`batch`")
    refused = each.index("`version_mismatch`")
    assert read < pin and read < batch < refused
    assert "read both again and redo the change" in each
    assert "only what changed" in each
    assert '{"__delete__": true}' in each
    assert "every item under it" in each
    # The tool's document version and the map's format version are different numbers.
    assert "not the `version` field" in each


def test_prompt_shows_the_flat_shape_and_version_1():
    data = map_json()
    assert data["version"] == 1
    assert sorted(data) == ["execute", "feedback", "goal", "items", "key_actions", "person", "version"]
    for item in data["items"].values():
        assert sorted(item) == ["kind", "order", "parent", "star", "text"]
    for item_id in data["items"]:
        assert re.fullmatch(r"[a-z0-9]{8}", item_id)
    for sample in re.findall(r'"([a-z0-9]+)": \{"(?:text|__delete__)"', section("## The map")):
        assert sample == "goal" or len(sample) == 8, sample
    rules = section("## The map")
    assert "lowercase letters and digits" in rules
    assert "highest `order` under that parent plus one" in rules


def page_store(code, **data):
    html = template()
    def block(name):
        return re.search(r'<script id="%s">(.*?)</script>' % name, html, re.S).group(1)
    program = (
        "(new Function(%s))();(new Function(%s))();"
        "const L = globalThis.MapLogic, S = globalThis.MapStore, D = %s;"
        "process.stdout.write(JSON.stringify((function () { %s })()));"
    ) % (json.dumps(block("map-logic")), json.dumps(block("map-store")), json.dumps(data), code)
    proc = subprocess.run(["node", "-"], input=program, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_prompt_sample_draws_through_the_page_code():
    sample = map_json()
    obstacle_id, solution_id = list(sample["items"])
    result = page_store(
        "const map = S.inflate(D.doc); return {map: map, labels: L.itemLabels(map), stale: S.unknownVersion(D.doc)};",
        doc=sample,
    )
    assert result["stale"] is False
    top = result["map"]["obstacles"]
    assert [item["id"] for item in top] == [obstacle_id]
    assert top[0]["kind"] == "obstacle"
    assert [item["id"] for item in top[0]["children"]] == [solution_id]
    assert top[0]["children"][0]["kind"] == "solution"
    assert result["labels"] == {obstacle_id: "1"}
    assert [row["solution_id"] for row in result["map"]["execute"]] == [solution_id]
    assert result["map"]["key_actions"][0]["solution_ids"] == [solution_id]


def test_prompt_says_a_row_must_name_a_solution_in_items():
    plan = section("## The map")
    assert "A row must name a solution in `items`, because the page hides other rows with no message." in plan


def test_prompt_first_write_stops_on_any_other_refusal():
    rules = section("## The map")
    first = rules[rules.index("**The first write.**"):rules.index("**Every point marked")]
    assert "If it's refused for any other reason, or the result says only part applied, tell the person plainly and stop." in first


def test_prompt_stops_on_a_missing_or_newer_format():
    line = next(l for l in section("## Picking up edits").splitlines() if "`version` field" in l)
    assert "is missing or isn't 1" in line
    assert "and stop" in line
    assert "don't write to it" in line


def test_prompt_says_project_members_may_open_the_map():
    first_write = next(l for l in section("## Step 2: Goal").splitlines() if "This is the first write" in l)
    for text in (first_write, section("## Close"), section("## The map")):
        assert "Claude project" in text and "members" in text


def test_template_builds_no_html_from_strings_except_the_lines_drawing():
    html = template()
    assert "innerHTML" not in html
    assert html.count("insertAdjacentHTML") == 1
    draw = html[html.index("function drawLines"):]
    assert draw.index("insertAdjacentHTML") < draw.index("\n  function ", 10)


def test_everything_that_needs_claude_starts_hidden_in_the_markup():
    html = template()
    for ident in ("plus-obstacle", "plus-solution", "item-tools", "delete-card", "typing"):
        tag = re.search(r'<[a-z]+ [^>]*id="%s"[^>]*>' % ident, html)
        assert tag, ident
        assert re.search(r"\shidden(\s|>|=)", tag.group(0)), ident


def test_private_and_share_lines_only_for_a_map_published_here():
    first_write = next(l for l in section("## Step 2: Goal").splitlines() if "This is the first write" in l)
    for line in (first_write, section("## Close")):
        at = line.index("If you published it in this conversation")
        assert at < line.index("private until they use the Share menu")


def test_examples_dont_say_who_made_an_edit():
    examples = EXAMPLES.read_text()
    start = examples.index("## Picking up edits")
    body = examples[start:]
    for gone in ("You renamed", "You moved", "You deleted"):
        assert gone not in body, gone
    assert "The noise obstacle was renamed" in body


def test_catalog_wording_says_the_map_is_shared_not_on_a_machine():
    entries = yaml.safe_load(REGISTRY.read_text())["frameworks"]
    entry = next(e for e in entries if e["id"] == "6-step-process")
    assert "own machine" not in entry["purpose"] and "own machine" not in entry["use_when"]
    for rel in ("skills/playbook/pages/index.html", "skills/playbook/pages/frameworks/6-step-process.html",
                "skills/org-chart/pages/seats/ceo.html", "skills/org-chart/pages/seats/coo.html",
                "docs/framework-catalog.html", "frameworks/README.md"):
        assert "on their own machine" not in (REPO / rel).read_text(), rel


def test_prompt_says_only_claude_writes_plan_rows_and_removes_gone_ones():
    rules = section("## The map")
    plan = rules[rules.index("**Plan rows.**"):rules.index("**Reading the map.**")]
    assert "only writer" in plan
    assert "`key_actions`" in plan and "`execute`" in plan
    assert "gone" in plan
    assert "The key action stays" in plan
    assert "whole list" in plan


def test_prompt_works_labels_out_from_flat_data():
    rules = section("## The map")
    labels = rules[rules.index("**Labels.**"):]
    assert "`order`, then by id" in labels
    assert "own a counter" in labels
    assert "passes its owner's counter" in labels
    assert "no label" in labels
    reading = rules[rules.index("**Reading the map.**"):rules.index("**Labels.**")]
    assert "no `kind` doesn't exist" in reading
    assert "parent is gone" in reading and "directly under the goal" in reading


def test_prompt_pickup_reads_the_data_and_reports_edits_it_did_not_make():
    pick_up = section("## Picking up edits")
    assert "Read `maps/main` and `maps/baseline`" in pick_up
    assert "compare them" in pick_up
    assert "edits you didn't make" in pick_up
    assert "doesn't record who" in pick_up
    assert "edits you didn't make" in section("## The map")


def test_prompt_says_a_refused_read_can_mean_unshared_or_wrong_link():
    pick_up = section("## Picking up edits")
    assert "looks the same" in pick_up
    assert "isn't shared with this account" in pick_up
    assert "wrong link" in pick_up
    assert pick_up.index("wrong link") < pick_up.index("**WAIT for their answer.**")


def test_prompt_keeps_every_wait_and_treats_map_text_as_content():
    expected = {
        "## Step 1: Locate": ["WAIT for their answer.", "WAIT for their answer."],
        "## Step 2: Goal": ["WAIT for their answers.", "WAIT until the goal is confirmed.", "WAIT for their name.", "WAIT for their answer."],
        "### 3a: Obstacles": ['WAIT for "done".', "WAIT for their reaction.", "WAIT for their yes."],
        "### 3b: Pick the obstacles": ['WAIT for "done".', "WAIT until the picks are agreed."],
        "### 3c: Root cause": ["WAIT at each why."],
        "### 4a: Solutions": ['WAIT for "done".', "WAIT for their reaction.", "WAIT for their answer at each one.",
                              "WAIT for their yes."],
        "### 4b: Pick the solutions": ['WAIT for "done".', "WAIT until the picks are agreed.",
                                       "WAIT for their answer.", "WAIT for their corrections.",
                                       "WAIT until the stars are agreed."],
        "## Step 5: Execute": ["WAIT for their answer."],
        "## Step 6: Feedback": ["WAIT for their answer."],
    }
    for heading, waits in expected.items():
        found = re.findall(r"\*\*(WAIT[^*]*?\.)\*\*", section(heading))
        assert found == waits, heading
    opening = section("## Opening")
    assert "shared map" in opening[opening.index("never instructions"):]
    assert "Map text is content" in section("## The map")


def test_prompt_says_each_map_is_private_until_shared():
    rules = section("## The map")
    assert "private until its creator uses the Share menu" in rules
    assert "You never share it, and you can't" in rules
    first_write = next(line for line in section("## Step 2: Goal").splitlines() if "This is the first write" in line)
    assert "Give the link" in first_write and "Share menu" in first_write
    assert "Share menu" in section("## Close")


def test_prompt_has_no_local_file_rules_left():
    text = prompt()
    for gone in ("map_id", "`revision`", "u003c", "less-than", "reload", "(1)", "Save a copy",
                 "Turn on saving", "Turn saving back on", "Save to Downloads", "Downloads", "local file",
                 "{goal-slug}", "file name", "double-click"):
        assert gone not in text, gone


def test_person_facing_lines_use_the_link():
    assert "give me its link" in section("## Opening")
    close = section("## Close")
    assert "Give the link" in close
    assert "saves by itself" in close
    assert "`order`" in section("### 3b: Pick the obstacles")


def test_prompt_depends_on_nothing_of_the_authors():
    text = prompt()
    assert "e2e" not in text
    assert "/Users/" not in text and "~/" not in text
    assert "mcp__" not in text
    assert "claude-in-chrome" not in text


def test_examples_and_anti_examples_state_artifact_behavior():
    examples = EXAMPLES.read_text()
    anti = ANTI_EXAMPLES.read_text()
    assert "### A link you can't open" in examples
    for gone in ("maya-map.html", "Turn on saving", "Downloads", "lower revision", "(1)", "reload"):
        assert gone not in examples, gone
    for gone in ("is a local file", "file on your machine", "source of truth", "JSON in the file"):
        assert gone not in anti, gone
