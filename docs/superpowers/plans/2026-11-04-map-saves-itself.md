# The Map Saves Itself Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In Chrome, the person connects the map's file once and every later edit writes to the file by itself. Safari and Firefox get a button named "Save to Downloads".

**Architecture:** All new decisions go in `<script id="map-logic">` as functions with no DOM, tested under node. The page code in `id="map-page"` calls them, draws the status line, and keeps the file handle in IndexedDB, keyed by the map's path and `map_id`.

**Tech Stack:** One self-contained HTML file, File System Access API, IndexedDB, pytest driving node.

**Spec:** `docs/plans/2026-11-03-6-step-process-design.md` in the main checkout (git-ignored), plus Option A on https://claude.ai/artifact/BiwsqwbeVJgSogGm9UgkDi, which Eric chose on 2026-11-04.

## Global Constraints

- Exact words on the page: "Changes aren't being saved yet." / "Turn on saving" / "Saving is paused." / "Turn saving back on" / "All changes saved" / "Saving..." / "Not saved" / "Save to Downloads" / "Click any item to edit it." / "When you finish, tell Claude you changed the map."
- Stale refusal wording: "Claude changed this map, so your last edit is not in the file. Reload to get the new version."
- Never use `showSaveFilePicker`. Nothing gets installed. No outside URLs in the template.
- No em or en dashes in the template or example map. Don't write `<` into the template source.
- A refused write never overwrites the file, and edits stay on the page.
- Never put a client name in any file in this repo.
- Run one shell command per Bash call, with no `&&` or pipes. Use `-m` for commit messages. Don't bump the version by hand; the pre-commit hook does it.

## Review Focus

1. A write fails or is refused, and the page must not retry in a loop. It retries only on the next edit.
2. The person edits while a write is running, and the newer edit must reach the file.
3. A map is copied to another folder and keeps its `map_id`. The copy must never write to the original's remembered file.
4. The remembered file was deleted or replaced by a different map. The page must forget it and ask for the file again.
5. IndexedDB throws or is empty. The page must still work, and the person chooses the file after each reload.

---

### Task 1: Save decisions in the logic block

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html` (`map-logic` block; add to `globalThis.MapLogic`)
- Test: `e2e/tests/test_six_step_map_logic.py`

**Interfaces:**
- Produces:
  - `saveStatus({picker, connected, remembered, dirty, writing, failed}) -> {text, tone, button}`, where `tone` is `''`, `'saved'` or `'unsaved'`, and `button` is `''` when there is none.
  - `createAutosaver(write) -> {request()}`. `write` is an async function that returns `{ok, ...}`. `request()` returns a promise for the last result.
  - `handleKey(pathname, mapId) -> string`
  - `connectToHandle(handle, map) -> Promise<{ok, reason?}>`, which never writes.
  - `saveToHandle` keeps its signature and result.

- [ ] **Step 1: Write failing tests**

Add `def test_save_status_table()` covering every row:

| picker | connected | remembered | dirty | writing | failed | text | tone | button |
|---|---|---|---|---|---|---|---|---|
| false | | | false | | | `''` | `''` | Save to Downloads |
| false | | | true | | | Not saved yet. | unsaved | Save to Downloads |
| true | false | false | false | | | Changes aren't being saved yet. | `''` | Turn on saving |
| true | false | false | true | | | Changes aren't being saved yet. | unsaved | Turn on saving |
| true | false | true | false | | | Saving is paused. | `''` | Turn saving back on |
| true | false | true | true | | | Saving is paused. | unsaved | Turn saving back on |
| true | true | | false | false | false | All changes saved | saved | `''` |
| true | true | | true | false | false | Saving... | `''` | `''` |
| true | true | | false | true | false | Saving... | `''` | `''` |
| true | true | | true | false | true | Not saved | unsaved | `''` |

Add `test_handle_key_differs_by_folder`: `handleKey('/a/m-map.html','id1') != handleKey('/b/m-map.html','id1')`, and it differs when only the id differs.

Add `test_connect_never_writes`: `call("connectToHandle", "__HANDLE__", make_map(), handle={"content": page(make_map())})` gives `result == {"ok": True}`, `writes == 0`, and `permissionMode == "readwrite"`.

Add `test_connect_refusals`: a wrong `map_id` gives `wrong-map`, junk gives `not-a-map`, a higher file revision gives `stale`, `permission: "denied"` and `permission: "throw"` give `permission`, and `getFileFails` gives `unreadable`. `writes` stays 0 or null in each.

Add autosaver tests through a new helper `run_autosaver(script)` that runs its own node program built from `logic_source()`. It takes a list of per-write outcomes (`"ok"`, `"fail"`, `"throw"`), holds each write open until released, and returns the write count and each `request()` result:
- `test_autosaver_runs_one_write_at_a_time`: three requests during one running write give 2 writes in total, and the second starts after the first finishes.
- `test_autosaver_writes_again_for_edits_made_during_a_write`: the second write happens with no further request.
- `test_autosaver_drops_the_queued_write_after_a_failure`: a first write of `"fail"` with a request queued gives 1 write.
- `test_autosaver_retries_on_the_next_request_after_a_failure`: a later request gives a second write.
- `test_autosaver_reports_a_thrown_write_as_write_failed`: `"throw"` resolves to `{"ok": false, "reason": "write-failed"}`, and the next request still writes.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest e2e/tests/test_six_step_map_logic.py -q -k "save_status or handle_key or connect or autosaver"`
Expected: FAIL because the functions don't exist.

- [ ] **Step 3: Implement the four functions**

`connectToHandle` does the permission request, file read and `checkTarget` that open `saveToHandle`. Pull those into one shared helper so both use the same checks and return the same reasons. `handleKey` joins the id and path with a separator that can't make two different pairs equal, such as `JSON.stringify([mapId, pathname])`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest e2e/tests/test_six_step_map_logic.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

Run `git add` on the template and the test file, then `git commit -m "feat: add the save decisions the self-saving map needs"`.

### Task 2: The page saves by itself

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html` (markup in `<footer>`, page code)
- Modify: `frameworks/6-step-process/example-map.html` (rebuilt from the template, keeping its own `map-data` block)
- Test: `e2e/tests/test_six_step_process.py`

**Interfaces:**
- Consumes: everything Task 1 produces.

**Behavior:**
- **Footer:** one status line plus one button, both drawn from `L.saveStatus`, then "Click any item to edit it." The Save button and `#dirty` go. Keep `#message` and `#browser-note`.
- **Star wording:** "To change a star, tell Claude." moves out of the footer and into the editor that opens on a solution.
- **Browser note:** says Chrome saves by itself, and otherwise saves go to Downloads and the person moves the file back under its original name. It keeps the words "Open With" and "Downloads".
- **Button, first time (`picker`, not remembered):** the click opens `showOpenFilePicker` straight away, with the file name shown in `#message` ("Choose {file} in the {folder} folder."; change `pickMessage` and its tests to this wording). Then `connectToHandle`, then remember the handle, then write once only if the page is dirty.
- **Button, remembered:** the click calls `connectToHandle` on the remembered handle, with no file dialog.
- **Button, no picker:** the existing download path in `onSave`, unchanged.
- **Writes:** `render()` asks the autosaver to write when a handle is connected, the map's JSON differs from `savedJson`, and that JSON differs from the last JSON it tried. The last-tried check is what stops a refused write from looping.
- **First write:** after the first write of an actual edit, show "When you finish, tell Claude you changed the map." once per page load.
- **Refusals:**
  - `wrong-map`, `not-a-map`, `unreadable`: forget the handle in memory and in IndexedDB. The status goes back to "Changes aren't being saved yet."
  - `permission`: keep the remembered handle. The status shows "Saving is paused."
  - `stale`, `write-failed`: stay connected with `failed` true, so the status says "Not saved". Show the refusal message and Save a copy. `stale` also gets a Reload button that calls `location.reload()`.
  - A later good write clears `failed`.
- **`REFUSALS.stale`:** use the exact wording in Global Constraints.
- **Remembering:** a small IndexedDB store keyed by `L.handleKey(location.pathname, map.map_id)`. Every read and write sits in try/catch, and a failure means nothing is remembered.
- **On load:** if a handle is found, set `remembered`. If `queryPermission({mode:'readwrite'})` says granted, call `connectToHandle` with no click. Handle a refusal by the rules above, except that a `stale` result on load can't occur in normal use and is treated as paused.
- **Close warning:** `beforeunload` stays as it is. It warns only when something is unsaved, which covers a write still running.

- [ ] **Step 1: Write failing tests**

Update these tests in place and add the new ones, matching page source text the way this file already does:
- `test_template_tells_person_to_tell_claude`: keep both phrases.
- `test_refusal_copy_keeps_the_page_marked_unsaved`, `test_page_takes_the_baseline_from_the_save_result`, `test_browser_without_the_picker_names_the_folder_and_file`: keep them passing against the new function names.
- `test_footer_has_no_save_button_or_dirty_line`: `id="save"` keeps only as the single status button if you reuse the id. `id="dirty"` and "Not saved yet." in static markup are gone.
- `test_status_line_comes_from_the_logic_block`: page code contains `L.saveStatus(`.
- `test_autosave_guards_against_retrying_the_same_json`: the render path compares against the last-tried JSON before calling `request()`.
- `test_handle_store_is_keyed_by_path_and_map_id`: page code contains `L.handleKey(location.pathname, map.map_id)`.
- `test_handle_store_survives_a_storage_failure`: each `indexedDB` use sits inside `try`.
- `test_bad_files_are_forgotten`: the code for `wrong-map`, `not-a-map` and `unreadable` calls the forget function.
- `test_stale_refusal_uses_the_approved_words`.
- `test_example_map_matches_the_template_outside_its_data`: the two files are identical once the `map-data` block is cut from each.
- `test_no_save_file_picker`: `showSaveFilePicker` is absent.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest e2e/tests/test_six_step_process.py -q`
Expected: the new tests fail.

- [ ] **Step 3: Implement the behavior above**

Rebuild `example-map.html` from the template last, keeping its `map-data` block byte for byte.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest e2e/tests/test_six_step_process.py e2e/tests/test_six_step_map_logic.py -q`
Expected: all pass, apart from any tests Task 3 owns. List those in the report.

- [ ] **Step 5: Commit**

Run `git add` on the template, example map and test file, then `git commit -m "feat: save map edits to the file automatically once saving is on"`.

### Task 3: Claude's instructions match the new page

**Files:**
- Modify: `frameworks/6-step-process/prompt.md` (lines near 50, 240, 253)
- Modify: `frameworks/6-step-process/examples.md` (lines near 156, 190)
- Test: `e2e/tests/test_six_step_process.py`

**Required wording changes:**
- **Handoff (`prompt.md` near 240, `examples.md` near 156):** the map is theirs to edit and show to others. To keep edits, they click Turn on saving once in Chrome. When they change it, they tell Claude.
- **Reload line (near 50):** after a rewrite, tell them to reload the page if it's open. Reloading drops edits not yet in the file. If the page shows Not saved or says changes aren't being saved, those edits aren't in the file, and they should use Save a copy, or Save to Downloads in Safari or Firefox. That copy goes in the folder under another name, and they tell Claude the name. This also fixes the old line that was wrong for Safari and Firefox.
- **No-change reply (near 253, `examples.md` near 190):** if the page is still open and says changes aren't being saved, click Turn on saving or Turn saving back on first. Otherwise look in Downloads, as the reply says today.

- [ ] **Step 1: Update the failing tests**

`test_reload_line_warns_about_unsaved_edits` asserts "drops", "Not saved", "Save a copy", "Save to Downloads", "another name". `test_no_change_reply_exists` asserts `pick_up.index("Turn on saving") < pick_up.index("Downloads")`. Add `test_prompt_no_longer_says_press_save`: "press Save" is absent from `prompt.md` and `examples.md`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest e2e/tests/test_six_step_process.py -q`
Expected: those tests fail.

- [ ] **Step 3: Change the prompt and examples**

- [ ] **Step 4: Run the full suite**

Run: `python3 -m pytest e2e/tests -q`
Expected: all pass, with the same 180 skips.

- [ ] **Step 5: Commit**

Run `git add` on the prompt, examples and test file, then `git commit -m "docs: tell Claude's map instructions about automatic saving"`.

### After the tasks (controller, not a subagent)

- Drive the real template in Chrome over localhost with a stubbed `showOpenFilePicker` and fake handle: first connect, edit, write, stale refusal, reload.
- Eric's hand check from `file://`, which needs the real file dialog: connect, edit, close the tab with no box, reopen, Turn saving back on with no file dialog. This is also the first real test of remembering the file.
- Update the spec in the main checkout: the save flow, the decision log, and the `solution_at` and sandbox-path items still owed.
