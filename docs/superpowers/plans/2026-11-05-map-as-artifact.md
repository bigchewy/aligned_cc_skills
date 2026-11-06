# The Map as a Claude Artifact Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The 6-step map runs as a private Claude artifact that saves itself, updates live and can be shared. Eric removed the local file on 2026-11-05, so Tasks 9 and 10 replace the old fallback task.

**Architecture:** One template works both ways. A new `<script id="map-store">` holds pure logic for flat data, per-action changes, forgiving reads, the write queue and the status text. `map-page` picks shared data when `window.claude` is defined and file saving otherwise, and the existing tree code keeps drawing and editing.

**Tech Stack:** Plain JavaScript in one HTML file, the artifact `db` and `user` capabilities, pytest and node for tests.

**Spec:** `docs/superpowers/specs/2026-11-05-map-as-artifact-design.md`

Type definitions for the data calls: `/private/tmp/claude-501/bundled-skills/2.1.318/d1108cd29917e6c3102f316fea096ffe/artifact-capabilities/0.2.96/db.d.ts`, `user.d.ts`, `claude.d.ts`. If that folder has gone, load the `artifact-capabilities` skill for its current path.

## Global Constraints

- The status says "Saving..." then "All changes saved". "All changes saved" means nothing is waiting and the last write was confirmed.
- `window.claude` undefined means a local file. Defined means the viewer, and never file saving.
- A blank item never reaches the data.
- The page has no way to write `key_actions` or `execute`. Only Claude writes them.
- The page never compares what's on screen with what's stored. Each action sends only what that action changed.
- A repair made while reading is never written back.
- One write at a time to `maps/main`. Nothing writes from render code or a snapshot callback.
- Ids are random lowercase letters and digits. Reads ignore any other key in `items`.
- Data lives in collection `maps`, documents `main` and `baseline`. `version` is 1.
- File saving code and its flows in `e2e/tests/six_step_page_flows.js` keep passing unchanged, apart from Task 9.
- The pre-commit hook bumps the version. Never bump it by hand or hard-code the next version in a test.
- Never put a client name in a repo file. Don't push. Commit messages use `-m`, never a heredoc.
- Run one command per Bash call. Rebuild the example with `python3 /private/tmp/claude-501/-Users-ericpage-software-aligned-cc-skills/4a79a0fa-0010-4e50-a008-c2c02123d4e9/scratchpad/rebuild_example.py frameworks/6-step-process` after every template change.
- Suite: `/Users/ericpage/software/aligned_cc_skills/e2e/.venv/bin/python -m pytest e2e/tests -q`.

## Review Focus

- Claude or a colleague leaves a document with missing or wrong-typed fields: the page still draws what it can and doesn't throw (Task 2).
- A map with many items: moving one sends a change naming only that item (Task 2).
- Another person deletes the item that's selected, being dragged, being asked about or being typed on: nothing throws and no text is lost (Task 5).
- A person closes the tab within a moment of an edit: the page warns only while a change is unconfirmed (Task 6).
- Text holding `<`, quotes or `__proto__`-like words from another writer shows as plain text and round-trips (Tasks 2 and 5).

---

### Task 1: Stage 0 probes in the real viewer

No repo files change. This is a gate.

**Files:**
- Create: `<workspace>/stage-0-findings.md` (the plan's SDD workspace, git-ignored)

**Interfaces:**
- Produces: the findings file, which Tasks 2, 3, 4 and 8 read for the delete form, the offline behavior and the publish form.

- [ ] **Step 1: Publish a throwaway probe page** declaring `{db: {}, user: {}}`, with buttons and an on-screen log that also records to a `probe-results` collection. Reuse what you need from the scratchpad's `artifact-spike/db-block.js`. No real data.
- [ ] **Step 2: Record what actually happens for each probe**
  - P1: Start `update` of field a and, before it resolves, change b locally. Record every snapshot's body and `metadata`, in order, and whether a confirmed snapshot can arrive without b.
  - P2: One tab sends `{items: {k: {__delete__: true}}}` while another sends `{items: {k: {star: true}}}`, in both orders. Record the final document.
  - P3: Send `{__delete__: true}` from the page. Record whether the pending snapshot shows the marker literally and whether the confirmed one drops the key. Note that `db.d.ts` doesn't document this form.
  - P4: `update` while offline, if the tools can make the page offline: does it hang or reject, and how long until it does? If they can't, record that it needs a hand check.
  - P5: Make a copy of `frameworks/6-step-process/mind-map-template.html` with the `<html>`, `<head>`, `<body>` and `<title>` tags removed, and publish it from a path in the repo with no other changes. Record whether the tool accepts it, whether a leading doctype is accepted, and whether the page's scripts run in the viewer.
- [ ] **Step 3: Write `stage-0-findings.md`** with a pass or fail per probe. Fail means the spec's design can't work as written: P1 shows edits can't be overlaid, P2 can bring a deleted item back with a `kind`, P3 can't delete by any means including the spec's `deleted: true` fallback, or P5 can't publish one template.
- [ ] **Step 4: Report.** On any fail, the controller stops and takes it to Eric before Task 2. If P3's marker fails but `deleted: true` works, that's a pass: use `deleted: true` in Tasks 2 and 8. A real colleague's edit is Eric's check, and it doesn't hold up the build.

### Task 2: Flat data logic

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html` (new `<script id="map-store">` directly after `map-logic`)
- Create: `e2e/tests/test_six_step_map_store.py`, loading `map-store` under node the way `test_six_step_map_logic.py` loads `map-logic`

**Interfaces:**
- Consumes: `globalThis.MapLogic` tree shape: items `{id, kind, text, star, children}`, `map.obstacles`, `map.goal.text`.
- Produces on `globalThis.MapStore`:
  - `FORMAT_VERSION`: `1`
  - `newId() -> string` matching `/^[a-z0-9]{8}$/`
  - `flatten(map) -> doc`: `{version, person, goal, items, key_actions, execute, feedback}`, with `order` counting from 1 under each parent
  - `inflate(doc) -> map`: a tree map with `map_id: ''`, `revision: 1`, `baseline: {}`
  - `overlay(doc, changes) -> doc`: merges each change in turn without changing `doc`, as `update` does. Nested objects merge, anything else replaces, and `{__delete__: true}` removes the key.
  - `changeBetween(doc, before, after, skipId) -> change | null`
  - `unknownVersion(doc) -> boolean`

- [ ] **Step 1: Write the failing tests**
  - `test_flatten_then_inflate_keeps_the_example_tree`: inflating the flattened `example-map.html` data gives the same tree, and `MapLogic.mapProblem` finds no problem once `map_id` is set.
  - `test_inflate_orders_by_order_then_id`: equal orders sort by id.
  - `test_inflate_ignores_items_with_no_kind`: `{star: true}` and `{__delete__: true}` values vanish.
  - `test_inflate_ignores_bad_ids`: keys `__proto__`, `A1` and `a-b` vanish, and `Object.prototype` is unchanged.
  - `test_inflate_puts_an_orphan_under_the_goal`
  - `test_inflate_breaks_a_cycle_at_the_lowest_id`: `a` under `b` and `b` under `a` gives `a` under the goal and `b` under `a`, whatever the key order.
  - `test_inflate_hides_plan_rows_naming_a_gone_solution`: same outcome as `MapLogic.deleteItem` gives for those rows.
  - `test_inflate_survives_a_thin_document`: `{version: 1}` and non-string `text` draw with defaults and don't throw; an obstacle's `star` reads false.
  - `test_overlay_merges_replaces_and_deletes`: the input is unchanged afterward.
  - `test_change_for_text_names_one_field`: `{items: {k: {text: 'new'}}}` and nothing else.
  - `test_change_for_star_names_one_field`
  - `test_change_for_a_new_item_sends_all_its_fields`, with `parent` and an `order` one above the highest under that parent in `doc`.
  - `test_change_for_a_move_sends_parent_and_order_only`, on a map of 100 items.
  - `test_change_for_a_delete_marks_the_item_and_everything_under_it`
  - `test_change_never_names_the_plan`: a `MapLogic.deleteItem` that rewrites plan rows yields a change with only `items`.
  - `test_change_skips_the_held_blank_item`: `skipId` leaves it out.
  - `test_no_change_gives_null`
  - `test_goal_change_is_goal_text_only`
  - `test_odd_text_round_trips`: text with `<`, quotes and the word `__proto__`.
- [ ] **Step 2: Run them.** `/Users/ericpage/software/aligned_cc_skills/e2e/.venv/bin/python -m pytest e2e/tests/test_six_step_map_store.py -q`. Expected: FAIL, no `MapStore`.
- [ ] **Step 3: Implement** the interface above, using the delete form Task 1 found. `inflate` first attaches every item whose parent is present or `goal`, sends orphans to the goal, then walks from the goal. While items remain unreached, it attaches the lowest remaining id to the goal and walks again. Use `Object.create(null)` or `Object.keys` rather than plain key assignment on untrusted keys.
- [ ] **Step 4: Rebuild the example, run these tests and `test_six_step_page_flows.py`.** Expected: PASS.
- [ ] **Step 5: Commit** with `git commit -m "feat: add flat data logic for the shared map"`.

### Task 3: One template that publishes directly

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html`, `e2e/tests/test_six_step_process.py`

**Interfaces:**
- Produces: a template with no `<html>`, `<head>`, `<body>` or `<title>` tags, which sets `document.documentElement.lang = 'en'` and, on a local file, `document.title = 'Mind map'` by script. Keep or drop the doctype line as Task 1's P5 found.

- [ ] **Step 1: Write the failing tests** in `test_six_step_process.py`: `test_template_has_no_wrapper_tags` and `test_template_sets_its_language_and_title_by_script`.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Remove the tags, add the script lines.** `SOURCE` in `map-page` still rebuilds a whole document, so a saved local file stays complete. Add a flow to `six_step_page_flows.js`: a save writes a page whose scripts and map data are all present.
- [ ] **Step 4: Rebuild the example and run the full suite.** Expected: PASS, apart from any test pinning the old tags, which you update and name in your report.
- [ ] **Step 5: Commit** with `git commit -m "feat: let the map template publish as an artifact"`.

### Task 4: Write queue and status text

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html` (`map-store`), `e2e/tests/test_six_step_map_store.py`

**Interfaces:**
- Produces on `MapStore`:
  - `createChangeQueue({write, onChange, wait}) -> {add(change), pending() -> change[], retryNow()}`. `write(change)` returns a promise. `wait(ms)` returns a promise, so tests control time. `pending()` includes the change in flight, in order. `onChange` fires on every state change with `{saving, failed, code}`.
  - `hostedStatus({ready, readOnly, unreachable, stale, saving, slow, failed}) -> {text, tone}`, using the same tone names as `MapLogic.saveStatus`.

- [ ] **Step 1: Write the failing tests, with both success and rejected writes**
  - `test_queue_sends_one_write_at_a_time_in_order`
  - `test_queue_keeps_a_change_pending_until_its_write_confirms`
  - `test_queue_retries_unavailable_once_after_a_delay` of 1000 to 2000 ms
  - `test_queue_keeps_trying_every_30s_after_a_second_failure`, reporting `failed` until one succeeds
  - `test_queue_treats_an_unknown_code_as_unavailable`
  - `test_queue_stops_on_invalid_argument`: reports `failed` with the code, keeps the change, and tries again on the next `add` or `retryNow`
  - `test_queue_stops_on_revoked_and_quota_exceeded`
  - `test_status_says_saved_only_with_nothing_waiting`
  - `test_status_says_saving_while_waiting`, and a different message when `slow`
  - `test_status_says_not_saved_when_failed`, `..._out_of_date_when_stale`, `..._cant_open_when_unreachable`, `..._view_only`
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** Plain words in the status text. No mention of files or reloading.
- [ ] **Step 4: Rebuild the example and run them.** Expected: PASS.
- [ ] **Step 5: Commit** with `git commit -m "feat: add the write queue and status for the shared map"`.

### Task 5: The page runs from shared data

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html` (`map-page`)
- Create: `e2e/tests/six_step_page_stub.js` (the stub DOM moved out of `six_step_page_flows.js`, which then requires it), `e2e/tests/six_step_hosted_flows.js`, `e2e/tests/test_six_step_hosted_flows.py`

**Interfaces:**
- Consumes: all of `MapStore`.
- Produces: `hosted` in `map-page`. The fake store in `six_step_hosted_flows.js` offers `window.claude.use`, `db.doc().onSnapshot/update/get`, lets a test deliver a snapshot or hold a write, and lets a test set `user.can`.

The page holds `doc` (last snapshot), and the queue's pending changes. `view()` is `MapStore.inflate(MapStore.overlay(doc, queue.pending()))`. `map` is always `view()` plus the blank new item, if one is held.

- [ ] **Step 1: Move the stub.** Run `six_step_page_flows.js` on both pages. Expected: same flow count, all passing.
- [ ] **Step 2: Write the failing hosted flows**
  - `no window.claude uses file saving, with no store call`
  - `window.claude with a null db shows it can't open, allows no edits and never uses the picker`
  - `no map in the data says the map isn't set up and allows no edits`
  - `unknown version shows the map with no editing controls and asks for a newer page`
  - `no edits until the first snapshot, and 10 seconds of silence says it can't reach the map`
  - `a star sends only that field, once`
  - `a second edit while the first is in flight survives the first's confirmed snapshot`: the second stays on screen and is sent, and the status isn't saved until it confirms
  - `a live update changes the screen and writes nothing`
  - `an open text box with no change writes nothing, even after a remote change to that item`, and the remote text stays
  - `a changed text box over a remote change writes, and shows a notice`
  - `typing survives a live update`
  - `a new blank item survives a live update and never reaches the store`
  - `finishing a new item sends all its fields with a random id`
  - `a remote delete of the item being typed on keeps the box open, and finishing adds the text as a new item under the goal`
  - `a remote delete of the dragged item cancels the drag`
  - `a remote delete of the selected item clears the selection`
  - `a remote delete while the delete question is open closes the question`
  - `a live update during a drag keeps the drag`
  - `deleting a solution hides its plan rows and sends no plan fields`
  - `odd text from another writer shows as plain text`
- [ ] **Step 3: Run them.** `node e2e/tests/six_step_hosted_flows.js frameworks/6-step-process/mind-map-template.html`. Expected: FAIL.
- [ ] **Step 4: Implement**
  - Decide `hosted` first thing in `map-page`, before `parseMapData` and `mapProblem`.
  - On the hosted path, start with an empty inflated map, skip `reconnectOnLoad` and file handles, and subscribe once to `maps/main` in a new `startHosted()`. Add `canEdit()`, true only once `ready` and not read-only, and return early on it from `startTyping`, `addUnder`, `startDrag` and the star and delete handlers.
  - `setMap(next)` on the hosted path: work out `MapStore.changeBetween(doc-with-pending, view(), next, heldId)` and add it to the queue, then rebuild `map`. Nothing else may write.
  - `addUnder` uses `MapStore.newId()` when hosted.
  - `finishTyping`: `startTyping` keeps the text at open in `editing.openedText`. When unchanged and not new, close with no `setMap`. This rule also runs on the file path, where it changes nothing.
  - Snapshot callback: store `doc`, handle anything gone (selected, typing, drag, question, as the flows say), rebuild, `render()`. A frozen snapshot isn't mutated.
  - `askToWrite` returns at once when hosted. `render` stays free of writes.
- [ ] **Step 5: Run the hosted flows, `six_step_page_flows.js` on both pages, and add `test_six_step_hosted_flows.py`** on the same pattern as `test_six_step_page_flows.py`, with a minimum flow count. Rebuild the example first. Expected: PASS.
- [ ] **Step 6: Commit** with `git commit -m "feat: run the map from shared data in the viewer"`.

### Task 6: Status, failures and who can write

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html` (`map-page`), `e2e/tests/six_step_hosted_flows.js`

**Interfaces:**
- Consumes: `hostedStatus`, `createChangeQueue`, `claude.use('user')`.

- [ ] **Step 1: Write the failing flows**
  - `status goes Saving... then All changes saved only after the write confirms`
  - `a write held past 15 seconds says so and keeps the edit`
  - `a refused write keeps the edit on screen, marked not saved, with a plain message`
  - `can("data.write") false hides pluses, toolbar and dragging, and draws live`
  - `can("data.write") null keeps editing until invalid_argument, then goes read-only for the visit`
  - `invalid_argument with can("data.write") true stays editable and says not saved`
  - `10 seconds with no fromCache:false says the map may be out of date, and the next definitive snapshot clears it`
  - `a listener ended with unavailable subscribes again once`
  - `revoked shows the map can't be reached and allows no edits`
  - `a change to an item someone deleted is dropped from the screen with no throw`
  - `the hosted page hides Save a copy, Turn on saving and the browser note, and shows no reload or file-name text`
  - `closing the tab warns only while a change is unconfirmed`, and an open text box's text counts as a change. This is a plan ruling: the spec skips the file warning, and this narrower one stops a just-made edit from vanishing silently.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** `showStatus` branches to `hostedStatus`. Don't touch `saveStatus` or the file saving functions.
- [ ] **Step 4: Rebuild the example and run the flows on both drivers.** Expected: PASS.
- [ ] **Step 5: Commit** with `git commit -m "feat: show honest status and respect who can write"`.

### Task 7: The real page in the real viewer

No code unless a fault appears, and then test first.

**Files:**
- Create: `<workspace>/viewer-check.md`

- [ ] **Step 1: Publish the template** as a private test artifact declaring `{db: {}, user: {}}`. Write `maps/main` and `maps/baseline` with `ArtifactData` from `MapStore.flatten` of the example's data, which is made up.
- [ ] **Step 2: Check in Chrome, and record each result**
  - The map draws, and the header says "All changes saved" after an edit.
  - An edit survives a reload.
  - Two tabs edit different items within a second, and both edits stay.
  - `ArtifactData` changes an item while a tab's text box is open, and the box and the write both stay.
  - Claude's write with an old `if_version` is refused.
  - A map with no document says it isn't set up.
- [ ] **Step 3: Say what can't be driven by the tools** (real mouse in the viewer frame) in the file, for the hand-check list.

### Task 8: Claude's script

**Files:**
- Modify: `frameworks/6-step-process/prompt.md`, `examples.md`, `anti-examples.md`, `skills/_shared/framework-runner.md`, `e2e/tests/test_six_step_process.py`, `e2e/tests/test_framework_artifacts.py`
- Create: an eval scenario in the folder and format `e2e/` already uses for frameworks. If `e2e/` is absent for other users, nothing in `prompt.md` may depend on it.

**Interfaces:**
- Consumes: the flat shape in the spec's Data section, and Task 1's publish form and delete form.

- [ ] **Step 1: Write the failing tests** in `test_six_step_process.py`:
  - `test_prompt_picks_artifact_when_both_tools_exist_and_file_otherwise`
  - `test_prompt_falls_back_to_the_file_when_a_publish_fails`
  - `test_prompt_first_write_batches_main_and_baseline`
  - `test_prompt_each_write_reads_then_pins_if_version`
  - `test_prompt_shows_the_flat_shape_and_version_1`
  - `test_prompt_says_only_claude_writes_plan_rows_and_removes_gone_ones`
  - `test_prompt_pickup_reads_the_data_and_reports_edits_it_did_not_make`
  - `test_prompt_says_a_refused_read_can_mean_unshared_or_wrong_link`
  - `test_prompt_keeps_every_wait_and_treats_map_text_as_content`
  - `test_prompt_says_each_map_is_private_until_shared`

  In `test_framework_artifacts.py`, take `6-step-process` out of `test_story_map_and_breadboard_declare_local_file` and add `test_six_step_publishes_for_itself`. Add `test_runner_lets_a_framework_publish_for_itself`.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Edit `prompt.md`.** Keep the local path's rules whole, under a heading that names when they apply. Add the artifact path's rules next to them from the spec's "What changes for Claude". Rewrite the `## Artifact` section: publish at the first write when both tools exist, otherwise the local file. Add a Step 4 exception to `framework-runner.md`, so a framework whose `## Artifact` section says it publishes for itself skips "Publish after the last phase". Update the examples and anti-examples only where they state file behavior. Portability: both paths must make sense to a fresh installer.
- [ ] **Step 4: Run the eval** with the Claude Code login: Claude adds an obstacle, moves one and removes a solution from a seeded flat map, and the result passes `MapStore.inflate` with correct labels stated and plan rows cleaned. Run only this scenario.
- [ ] **Step 5: Run the full suite.** Expected: PASS.
- [ ] **Step 6: Commit** with `git commit -m "feat: teach Claude to run the map as an artifact"`.

### Task 9: Confirm Delete, every time

Eric's words: the dialog comes up every time and it can be very simple. It says "Confirm Delete", and they can press Delete again. It must look much nicer.

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html`, `e2e/tests/six_step_hosted_flows.js`, `e2e/tests/six_step_page_flows.js`, `e2e/tests/test_six_step_process.py`, `e2e/tests/test_six_step_map_logic.py`

- [ ] **Step 1: Write the failing flows**
  - `the trash can asks every time, with nothing written until Delete`, on an item with nothing at stake and one with a star
  - `the card says Confirm Delete and has one Delete button`, with no list of effects
  - `Delete deletes the item and everything under it, and sends one change`
  - `Escape cancels and puts focus back on the trash can`
  - `clicking elsewhere cancels and writes nothing`
  - `Enter on the focused Delete button deletes`
  - `a remote delete of that item closes the card`
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** Remove `deleteEffects`, `listOf`, the Keep button and the question's wording. The card sits by the trash can, on the page's white look: rounded corners, a soft shadow, the words in the page's type, and a solid red Delete button with white text.
- [ ] **Step 4: Rebuild the example and run the flows and the full suite.** Expected: PASS.
- [ ] **Step 5: Publish to the test map** `https://claude.ai/artifact/P81Nau1vcwjsSYpNKL3Tbh` and look at a screenshot of the card in the viewer, opened by keyboard. Fix what looks wrong.
- [ ] **Step 6: Commit** with `git commit -m "feat: ask Confirm Delete on every delete"`.

### Task 10: Take out the local file

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html`, `e2e/tests/six_step_hosted_flows.js`, `e2e/tests/test_six_step_hosted_flows.py`, `e2e/tests/six_step_page_stub.js`, `e2e/tests/test_six_step_process.py`, `e2e/tests/test_six_step_map_logic.py`, `e2e/tests/test_six_step_map_store.py`, `e2e/tests/test_playbook.py` and `e2e/tests/test_coach_eric.py` if they name removed things
- Delete: `frameworks/6-step-process/example-map.html`, `e2e/tests/six_step_page_flows.js`, `e2e/tests/test_six_step_page_flows.py`
- Create: `e2e/fixtures/six-step-example-map.json`, the example's flat document

- [ ] **Step 1: Move every editing flow in `six_step_page_flows.js` onto the hosted driver:** selecting, typing, pluses, stars, dragging, zoom, the plan panel. Flows about files, handles, refusals, copies, revisions and the autosaver go. List in your report each flow removed and why. Run the moved flows. Expected: PASS.
- [ ] **Step 2: Write the failing flow** `opened outside Claude says the map opens inside Claude, and allows no edits`, and a test that the template holds none of `showOpenFilePicker`, `indexedDB`, `createWritable`, `Save a copy`, `Turn on saving`, `map_id`, `map-data`.
- [ ] **Step 3: Run them.** Expected: FAIL.
- [ ] **Step 4: Remove from `map-page`:** `hosted` as a choice, `SOURCE`, handles, the autosaver, refusals, copies, downloads, the browser note, the save button, and `document.title`. Remove from `map-logic` whatever is then unused, including `parseMapData`, `replaceMapData`, `copyHtml`, `checkTarget`, `fileIsKnown`, `connectToHandle`, `createAutosaver`, `saveStatus` and the file messages. Remove the `<script id="map-data">` block. Keep the close warning for unconfirmed changes. Grep `skills/` and `frameworks/` for `example-map` and fix references.
- [ ] **Step 5: Run the full suite.** Expected: PASS, with fewer tests. Report the old and new counts and the template's old and new line counts.
- [ ] **Step 6: Republish the test map and check in the viewer by keyboard** that it draws, adds an item and saves. Wait for "All changes saved" before closing a tab.
- [ ] **Step 7: Commit** with `git commit -m "feat: make the artifact the map's only home"`.
