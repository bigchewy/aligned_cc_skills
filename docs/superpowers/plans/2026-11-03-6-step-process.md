# 6-Step Process Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the `6-step-process` framework so one person works through the six steps with Claude and ends with an editable HTML mind map on their own machine.

**Architecture:** The framework stays a prompt plus examples. A new single-file HTML template holds the map in a JSON slot, draws and edits it, and saves over itself in Chrome. Its logic sits in a separate script block so `node` can test it with a fake file handle.

**Tech Stack:** Markdown prompts, plain HTML/CSS/JS with no dependencies, pytest running `node` subprocesses.

**Spec:** `/Users/ericpage/software/aligned_cc_skills/docs/plans/2026-11-03-6-step-process-design.md`. It's git-ignored, so read it from that absolute path. Every implementer reads it first.

## Global Constraints

- Nothing to install beyond the plugin. The template has no outside scripts, fonts or network calls.
- The map stays a local file and never gets published.
- The shipped prompt, examples and template name no real client.
- Claude skips every file ending in `-map.html` when it reads documents.
- File name: `{goal-slug}-{person}-map.html`.
- Never bump the plugin version by hand. The pre-commit hook does it, and tests must not hard-code the next version.
- Rebuild generated pages by script, never by hand.
- No dashes (em or en) in written copy. Plain language per `~/.claude/brand-voice.md`.
- One command per Bash call. Commit with `-m`, never a heredoc.

## Review Focus

- A person's text contains `</script>`, quotes, newlines or `$&`. The file still parses and the text comes back unchanged. Test in Task 2.
- Chrome no longer grants write permission after a reload, or the person denies it. The page keeps the edits on screen and says what happened. Test in Task 2.
- A very long item or a map with 12 obstacles. Text wraps and the map stays readable. Check in Task 3 with the sample map.
- A map with no key actions, no root causes or an unknown "from". The page draws it and shows "not compared to strategy" or the open item. Test in Task 3.
- A save to a Downloads copy named `name (1).html` that gets moved back. The map still loads because nothing depends on the file name. Test in Task 2.

---

### Task 1: Chrome check (done by the controller with Eric, before any subagent starts)

A throwaway page at `~/Desktop/six-step-chrome-check/check.html` tests the file API from `file://`. It stays out of the repo.

- [x] **Step 1:** Eric ran the open-picker and self-rewrite checks from `file://` in Chrome on 2026-11-03.
- [x] **Step 2:** Confirmed from the files on disk: the open picker kept the contents and wrote to the file, and the page rewrote itself with the counter at 1. Reopening a saved file and saving again still gets checked by hand in Task 7.
- [x] **Step 3:** The save-picker emptying question went untested, because macOS greys out existing files in that box and the design doesn't use it. Don't use `showSaveFilePicker` in the save path.

### Task 2: Map logic

**Files:**
- Create: `frameworks/6-step-process/mind-map-template.html` (logic block and data slot only in this task)
- Test: `e2e/tests/test_six_step_map_logic.py`

**Interfaces:**
- Produces, in `<script id="map-logic">`, assigned to `globalThis.MapLogic`, touching no DOM:
  - `untiedSolutionIds(map) -> string[]`
  - `repeatCount(map, solutionId) -> number`
  - `deleteSolutionFromObstacle(map, obstacleId, solutionId) -> map`
  - `deleteObstacle(map, obstacleId) -> map`
  - `markRootCause(map, obstacleId) -> map` (moves the last why into `root_cause`)
  - `serializeMap(map) -> string` (every `<` becomes the JSON unicode escape)
  - `parseMapData(html) -> map | null`
  - `replaceMapData(sourceHtml, map) -> string`
  - `checkTarget(fileHtml, map) -> {ok: true} | {ok: false, reason: "not-a-map" | "wrong-map" | "stale"}`
  - `async saveToHandle(handle, sourceHtml, map) -> {ok: true, revision: number} | {ok: false, reason: "not-a-map" | "wrong-map" | "stale" | "permission" | "unreadable" | "write-failed"}`. It bumps `revision` on success.
- JSON shape: the spec's "JSON shape" block, exactly.

- [ ] **Step 1: Write the failing tests.** The harness extracts the logic block from the template and runs it under `node` with a JSON test case. Tests: `test_untied_ids`, `test_repeat_count`, `test_delete_repeated_solution_only_leaves_that_obstacle`, `test_delete_last_tie_sends_solution_to_tray`, `test_delete_obstacle_keeps_solution_shared_elsewhere`, `test_mark_root_cause_moves_last_why`, `test_script_close_tag_round_trips`, `test_dollar_patterns_round_trip`, `test_check_target_stale_when_file_revision_newer`, `test_check_target_wrong_map_id`, `test_check_target_not_a_map`, `test_load_ignores_file_name`, `test_save_bumps_revision`, and with a fake handle: `test_save_permission_denied`, `test_save_unreadable_file`, `test_save_write_failure_keeps_file_intact`.
- [ ] **Step 2:** Run `e2e/.venv/bin/python -m pytest e2e/tests/test_six_step_map_logic.py -v`. Expected: FAIL, template missing.
- [ ] **Step 3:** Implement. `replaceMapData` uses a function replacer, so `$` patterns stay literal.
- [ ] **Step 4:** Run the same command. Expected: PASS.
- [ ] **Step 5:** Commit: `git add` both files, then `git commit -m "feat: mind map logic for the 6-step process"`.

### Task 3: Map page

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html`
- Create: `frameworks/6-step-process/example-map.html` (the template filled with the attendance case from `examples.md`, used to look at the page)
- Test: `e2e/tests/test_six_step_process.py`

**Interfaces:**
- Consumes: `MapLogic` from Task 2.

- [ ] **Step 1: Write the failing tests.** `test_template_has_data_and_logic_blocks`, `test_template_has_no_outside_urls`, `test_template_names_no_client`, `test_template_has_downloads_note` (asserts the words "Downloads" and "Open With"), `test_template_tells_person_to_tell_claude`, `test_example_map_parses`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Build the page per the spec's "The map" section: goal in the center, obstacles as lines off it, bold root cause, repeat counts, stars, side panel, person's name, tray with untied count, "planned, not done" labels, "not compared to strategy" when `key_actions` is empty, an open "from". Edits: text, add, delete, add a why, mark root cause, move a solution. Warn before closing with unsaved changes. Capture the source on load before drawing. Chrome saves with `showOpenFilePicker` and names the folder from `location.pathname` first. On a refusal, keep the edits on screen and offer a save-as-a-copy download. Other browsers download a copy and show the note. Light and dark tokens live in `:root` only.
- [ ] **Step 4:** Run the tests. Expected: PASS.
- [ ] **Step 5:** Look at `example-map.html` through `python3 -m http.server 8765 --bind 127.0.0.1` and Claude in Chrome, from the main checkout if the worktree guard refuses it. Check a 12-obstacle version at shared-screen size and at phone width.
- [ ] **Step 6:** Commit: `git commit -m "feat: editable mind map page for the 6-step process"` after `git add`.

### Task 4: The framework prompt

**Files:**
- Modify: `frameworks/6-step-process/prompt.md`, `examples.md`, `anti-examples.md`
- Test: `e2e/tests/test_six_step_process.py`

**Interfaces:**
- Consumes: the template's data slot and JSON shape from Task 2.

- [ ] **Step 1: Write the failing tests.** `test_six_steps_in_spoken_order`, `test_opens_by_asking_about_picking_up_a_map`, `test_private_writing_waits_before_claudes_list` (a WAIT falls between the private-writing instruction and Claude's list, for obstacles, obstacle picks, solutions and solution picks), `test_every_solution_tied_by_end`, `test_skips_map_files`, `test_skips_personal_notes_and_transcripts`, `test_below_the_line_offers_above_below_and_person_decides`, `test_file_written_at_each_step_after_goal`, `test_no_change_reply_exists`, `test_prompt_names_no_client`, `test_has_local_artifact_section`, `test_anti_examples_drop_challenge_solo`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Write the prompt per the spec's step table and pick-up section. Include the exact escape rule and how to copy the template from this framework's folder. Examples use the in-office attendance case. Anti-examples per the spec's file table.
- [ ] **Step 4:** Run them. Expected: PASS.
- [ ] **Step 5:** Commit: `git commit -m "feat: rewrite the 6-step process on the spoken order with private lists"` after `git add`.

### Task 5: Local-file results in the runner

**Files:**
- Modify: `skills/_shared/framework-runner.md`, `skills/add-framework/SKILL.md`, `skills/add-framework/report-template.md`, `frameworks/user-story-map/prompt.md`, `frameworks/breadboard-to-pages/prompt.md`
- Test: `e2e/tests/test_framework_artifacts.py`

- [ ] **Step 1: Write the failing tests.** `test_runner_skips_publish_for_local_file_artifact_section`, `test_add_framework_allows_local_file_result`, `test_story_map_and_breadboard_declare_local_file`. Keep every existing test in the file.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Add the rule to runner Step 4. The default stays publish. Add a short `## Artifact` section to the two prompts. Update the add-framework wording.
- [ ] **Step 4:** Run the file. Expected: PASS.
- [ ] **Step 5:** Run only the two scenarios the runner edit triggers: `scenarios/use-skill/framework-runner-extraction.yaml` and `scenarios/use-skill/use-framework-backward-compat.yaml`, using the Claude Code login.
- [ ] **Step 6:** Commit: `git commit -m "feat: a framework can name a local file as its result"` after `git add`.

### Task 6: Registry and generated pages

**Files:**
- Modify: `frameworks/registry.yaml`, `frameworks/README.md`, generated pages

- [ ] **Step 1:** Update `purpose` and `use_when` to cover any person with a goal or problem, ending in an editable map. Keep the id and name. If `scripts/generate-framework-registry.mjs` writes the registry from frontmatter, change the source and run it. Follow what `e2e/tests/test_readme_freshness.py` expects for the README.
- [ ] **Step 2:** Run `scripts/generate-playbook.py`, `scripts/generate-org-chart.py` and `scripts/generate-catalogs.py`, then each one's `--check` where it has one.
- [ ] **Step 3:** Run `e2e/.venv/bin/python -m pytest e2e/tests -q`. Skip-marked autopilot tests stay skipped. Expected: PASS.
- [ ] **Step 4:** Commit: `git commit -m "docs: update the 6-step process listing and rebuild pages"` after `git add`.

### Task 7: Hand checks

- [ ] **Step 1:** Eric runs `example-map.html` from `file://` in Chrome: first save, second save, wrong file, stale tab, cancelled picker, reopen and save again.
- [ ] **Step 2:** Eric checks Safari and Firefox: the note and the download.
- [ ] **Step 3:** Fix what fails, through a new subagent, and re-run the tests.
