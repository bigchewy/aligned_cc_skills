# Miro-Style Map, Stages 1 and 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The map becomes one tree that draws to the right of the goal on orange and green lines, and people edit it by selecting, pressing a plus and typing in place. Dragging is stage 3 and has its own plan.

**Architecture:** Decisions live in `<script id="map-logic">` as functions with no DOM, tested under node. The page code in `id="map-page"` draws from them. The JSON in `prompt.md` and the check in the template change in one commit, because Claude writes what the page reads.

**Tech Stack:** One self-contained HTML file, pytest driving node, the page flows in `e2e/tests/six_step_page_flows.js`.

**Spec:** `docs/superpowers/specs/2026-11-05-miro-style-map-design.md`, approved by Eric. Read it in full.

## Global Constraints

- Every item at every depth: `{"id": "o1", "kind": "obstacle", "text": "", "root_cause": false, "star": false, "children": []}`. `kind` is `"obstacle"` or `"solution"`. All six fields always exist.
- `map.obstacles` is the top-level list. `map.unplaced` is the tray. `map.solutions`, `solution_ids`, `repeatCount` and the `×2` mark are gone. `key_actions[].solution_ids` and `execute[].solution_id` stay.
- Labels are computed and never stored. Obstacles get them, and solutions don't.
- A root cause can't have an obstacle directly under it. A solution under a root cause can have obstacles of its own.
- Saving behavior stays as it is: status lines, refusals, top right placement, no write over a file Claude changed, and no write of a blank new item.
- No em or en dashes in the template or example map. Don't write `<` into the template's data. No outside URLs. Never put a client name in any file.
- `example-map.html` matches the template outside its `map-data` block. Rebuild it last in each task with `python3 /private/tmp/claude-501/-Users-ericpage-software-aligned-cc-skills/4a79a0fa-0010-4e50-a008-c2c02123d4e9/scratchpad/rebuild_example.py frameworks/6-step-process`, which reuses the example's current data.
- Run tests with `/Users/ericpage/software/aligned_cc_skills/e2e/.venv/bin/python -m pytest e2e/tests -q`. Expected skips: 180.
- One shell command per Bash call, no `&&` or pipes. Commit with `-m`. Don't bump versions by hand.

## Review Focus

1. Deleting an item with a pick or plan row: the page asks and names what goes, and a no changes nothing. A yes removes the Execute rows, takes the ids off key actions and keeps the key actions. Pinned in Task 4.
2. A blank new item never reaches the file, including when the person selects something else or Escapes out. Pinned in Task 3.
3. A redraw while typing, from a window resize or a status change, keeps the typed text and the focus. Pinned in Task 3.
4. A deep tree with obstacles under solutions has no overlapping items, keeps its lines, and works at phone width. Pinned in Task 1.
5. A tray solution attaches once, numbers correctly afterward, and can't become a pick before that. Pinned in Tasks 1 and 4.

---

### Task 1: The map becomes one tree

**Files:**
- Modify in `frameworks/6-step-process/`: `mind-map-template.html`, `example-map.html`, `prompt.md`, `examples.md`, `anti-examples.md`
- Test: `e2e/tests/test_six_step_map_logic.py`, `e2e/tests/test_six_step_process.py`, `e2e/tests/six_step_page_flows.js`

**Interfaces, all in `MapLogic`. `parentId` of `'goal'` means the top level:**
- `itemLabels(map) -> {id: label}`, obstacles only. One shared helper; the check and `drawnRows` use it too.
- `canAdd(map, parentId, kind) -> bool`, from the spec's plus table.
- `addItem(map, parentId, id, kind, text) -> map`. Unchanged map when `canAdd` is false.
- `canMove(map, itemId, targetId) -> bool`, from the spec's drop table. False on itself, anything beneath it, its current parent, and for any item into `unplaced`.
- `moveItem(map, itemId, targetId) -> map`. Attaches last under the target and also takes items out of `unplaced`.
- `moveTargets(map, itemId) -> [{id, name}]`, every target `canMove` allows, in reading order.
- `deleteItem(map, itemId) -> map`. Removes the item, everything under it, each removed solution's Execute rows and its ids on key actions. Key actions stay. Also works on `unplaced` items.
- `deleteEffects(map, itemId) -> {subItems: number, picks: [text], rows: [text]}`. `rows` lists the first move of each Execute row that would go and the text of each key action that would lose a solution.
- `setRootCause(map, id, isRoot)`, refused unless the item is an obstacle with no obstacle directly under it.
- `setStar(map, id, isStar)`, refused unless the item is a solution in the tree.
- `nextId(map, prefix)`, unique across the tree and `unplaced`.
- Layout: `wideLayout(map, heights, sizes)` keeps its name and returns lines as `{d, kind}`.

**Decisions:**
- **Label algorithm:** each obstacle owns one counter, and so does the goal. Walk its children in order. An obstacle child takes the next value at the owner's depth plus one and starts its own counter. A solution child adds nothing and its children count on the same counter. So `1B` with a child obstacle, then a solution holding an obstacle, gives `1B1` and `1B2`.
- **Layout:** the goal sits on the left and everything runs right. Every item sits one column out from its parent. Remove `sideOf`, the left side, and the rule that puts solutions under their obstacle. The band model stays. Top-level order reads straight down.
- **Phone width:** indent by depth in the tree, keeping the existing clamp. Add `→` before the text of a solution past the clamp so it keeps a depth cue.
- **The check refuses**, each with a plain sentence naming the item: every case in the spec's "The page's check refuses a map when" list. A map with `solutions` gets the existing old-shape wording. A plan row naming a missing id is refused here, so remove the page's "missing solution" drawing (`makeMissing`, `kind: 'missing'`) and the panel's filtering of unknown ids.
- **Form, minimal:** it keeps working on the new data. Obstacles offer "Add a sub-obstacle" and "Add a solution", root causes only "Add a solution", solutions "Add an obstacle". `moveControl` lists targets from `moveTargets`, for solutions only. Remove the "on N obstacles" note. Don't improve anything else, because Task 3 replaces it.
- **`prompt.md`:** update line by line:
  - The JSON block and the read-back rules in "The map file", including the root cause rule and `unplaced`.
  - The label paragraph gets: "An obstacle under a solution continues the numbering of the nearest obstacle above it, so 1B2 can be an answer to why on 1B or an obstacle in the way of a solution on 1B. The map shows which."
  - The holding list and every "tied" rule become placing the solution under an item. Rewrite "A solution that serves several obstacles sits on each one" to: ask which obstacle it belongs to, or whether it should be two separate solutions. Never write two items with the same text without asking.
  - Pick-up compares items by id and parent. It reports moved obstacles with what's under them, moved solutions, and deleted items with what went with them.
- **Example map:** rewrite its data for the new format with no repeated solutions: an obstacle under a solution, a solution under a root cause, one pick, at least one tray solution, and plan rows that all resolve. Change the data in `example-map.html` directly, then run the rebuild.

- [ ] **Step 1: Write failing tests.** In the logic file:
  - `test_labels_count_across_solutions`: the `1B` case above gives `1B1` and `1B2`.
  - `test_labels_have_no_duplicates_on_a_deep_mixed_tree`
  - `test_labels_skip_solutions_and_unplaced`
  - `test_plus_rules` and `test_move_rules`: every cell of both spec tables.
  - `test_move_refuses_self_descendant_and_current_parent`
  - `test_move_attaches_last` and `test_move_out_of_unplaced_removes_it_from_the_tray`
  - `test_delete_removes_rows_and_ids_but_keeps_key_actions`
  - `test_delete_effects_name_picks_and_rows`
  - `test_root_cause_rule_looks_only_at_direct_children`: root cause, then solution, then obstacle passes the check.
  - `test_star_refused_in_tray_and_on_obstacles`
  - One `test_check_refuses_*` for each spec case.
  - `test_layout_has_no_overlaps_on_a_deep_mixed_tree` and `test_layout_keeps_a_line_per_item_with_its_kind`
  - `test_narrow_layout_indents_by_tree_depth`

  In the process file: `test_prompt_json_is_the_one_tree`, `test_prompt_no_longer_names_solution_ids_or_a_solutions_list`, `test_prompt_asks_when_a_solution_serves_two_obstacles`, `test_prompt_explains_numbers_under_solutions`, `test_pick_up_covers_moved_obstacles`.

  In the flows: add an obstacle under a solution and see its label; delete an item and see its plan row go; attach a tray solution through the form.

  Rewrite existing tests that use the old format so they keep protecting the same behavior. Delete tests only for what the spec removes.
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** Rebuild the example last.
- [ ] **Step 4: Run the full suite. Expected: passes with 180 skips.**
- [ ] **Step 5: Commit** `feat: make the map one tree with solutions inside it`

### Task 2: The map looks like a Miro map

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html`, `example-map.html`
- Test: `e2e/tests/test_six_step_map_logic.py`, `e2e/tests/test_six_step_process.py`

**Decisions:**
- Tokens replace the current box and line colors. Light: obstacle `#c9502a`, solution `#4a9a2d`. Dark: obstacle `#ef7d57`, solution `#7fce62`. Both go through the existing light and dark blocks.
- Each line takes its child's kind for its color, at 2px. The goal's lines are orange because the top level is obstacles.
- Items are plain text with no border or fill, and they keep a hit area. The goal stays a box with rounded corners and an orange border. A root cause is bold. A pick shows `★` before its text. The label stays in muted bold.
- The selected state is a thin outline in the existing `--focus` token. Task 3 uses it.
- The solution text gets no colored fill. Color lives on the line.

- [ ] **Step 1: Write failing tests**: `test_lines_carry_their_kind` (the drawn `path` has a class per kind) and `test_template_defines_line_colors_for_both_themes`.
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** Rebuild the example last.
- [ ] **Step 4: Run the full suite. Expected: passes with 180 skips.**
- [ ] **Step 5: Commit** `feat: draw the map on orange and green lines`

### Task 3: Select, press a plus, type in place

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html`, `example-map.html`, `prompt.md` if it names the form
- Test: `e2e/tests/six_step_page_flows.js`, `e2e/tests/test_six_step_page_flows.py`, `e2e/tests/test_six_step_process.py`

**Interfaces:**
- Consumes `canAdd`, `addItem`, `setRootCause`, `setStar` from Task 1.
- Produces in the page: `selected` (a ref or null), `select(ref)`, `startTyping(ref, isNew)`, `finishTyping()`, `cancelTyping()`, and `#item-tools`, the overlay Task 4 adds to.

**Decisions:**
- **Selection is separate from typing.** A click selects, shows the controls and changes nothing in the map. Clicking empty space clears it.
- **Overlay, unscaled, outside `#canvas`.** The text box, the plus buttons and the toolbar live outside the canvas like today's `#editor`, because `render` clears the canvas. They get positioned over the selected item, including on scroll, zoom and resize. A redraw must not touch them.
- **Plus buttons:** real buttons beside the item, one orange and one green, shown by `canAdd`. Names: `Add an obstacle under 1B`, `Add a solution under 1B`. On a solution with no label, use its text.
- **Typing:** a double-click, Enter while selected, or the toolbar's "Edit text" button starts it. A new item opens ready to type. Enter finishes, Shift+Enter adds a line, Escape cancels. Finishing selects the item.
- **"Edit text" is my addition to the spec,** because a phone has no double-click and no Enter on a selected item. Log it as a ruling.
- **Holding back:** `holdingNewItem` is true only for a blank new item being typed. Selecting something else with a blank new item open removes it and writes nothing. Selection alone never asks for a write.
- **Toolbar on the selected item:** Pick checkbox labeled "This is one of my picks" on placed solutions, Mark or Unmark root cause on obstacles that `setRootCause` allows, Edit text, Delete. Goal shows Edit text only. Task 4 adds the ask on delete and "Move to".
- **Keyboard:** items take focus with Tab and select with Enter or Space. After every render, focus returns to the selected item or the open text box, found by id. Escape clears the selection.
- **Scroll:** after each render, the selected item stays in the same place on screen. Keep the existing first-load scroll.
- **Phone width:** the toolbar and plus buttons dock like today's editor does there.
- The form's `openEditor`, `editorActions`, `fieldList` parts and `moveControl` go when nothing calls them.

- [ ] **Step 1: Write failing tests.** Extend the stub DOM for `closest`, `contains` and `dblclick` as these need. In the flows:
  - `a click selects and writes nothing`
  - `plus adds an obstacle, typing fills it, and only then the file changes`
  - `a blank new item is removed when something else is selected, with no write`
  - `escape on a new item removes it, with no write`
  - `a resize while typing keeps the text and focus`
  - `root cause shows only the green plus`, `solution shows only the orange plus`
  - `selection returns focus after a render`
  - `the pick box changes the star and the key`

  In the process file: `test_page_has_no_form_editor_left`.
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** Rebuild the example last.
- [ ] **Step 4: Run the full suite. Expected: passes with 180 skips.**
- [ ] **Step 5: Commit** `feat: edit the map by selecting, pressing a plus and typing in place`

### Task 4: Delete asks first, and "Move to" covers every item

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html`, `example-map.html`
- Test: `e2e/tests/six_step_page_flows.js`

**Interfaces:**
- Consumes `deleteItem`, `deleteEffects`, `moveItem`, `moveTargets` from Task 1, and `#item-tools` from Task 3.

**Decisions:**
- **Delete with nothing at stake** deletes straight away, even with sub-items. With a pick or a row in `deleteEffects`, the toolbar swaps to a question inside the page, because this must not rely on `confirm()`. Wording: "Delete this? It would also remove: " then each pick and row by its text, with buttons "Delete" and "Keep". Keep changes nothing.
- **"Move to"** is a select in the toolbar on any item but the goal, listing `moveTargets` by label and text. Choosing one moves the item, keeps it selected and writes. Hide it when there are no targets.
- **Tray:** selecting a tray solution shows Edit text, Delete and "Move to". It shows no pick box and no plus buttons.

- [ ] **Step 1: Write failing tests** in the flows:
  - `delete with a pick asks, and keep changes nothing`
  - `delete with a plan row asks, and yes removes the row but keeps the key action`
  - `delete with nothing at stake deletes straight away, including sub-items`
  - `move to moves an obstacle with what is under it and renumbers`
  - `a tray solution attaches through move to and leaves the tray`
  - `a tray solution offers no pick box or plus`
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** Rebuild the example last.
- [ ] **Step 4: Run the full suite. Expected: passes with 180 skips.**
- [ ] **Step 5: Commit** `feat: ask before deleting picks and let Move to cover every item`

### After the tasks (controller)

- Whole-branch review of these four tasks.
- Look at the example map in real Chrome over localhost, at wide and phone widths, with a blank new item open, and with a resize while typing.
- Refresh the check map on the Desktop for Eric, and report the rulings, including "Edit text".
- Stop there. Stage 3 waits for Eric to look at stage 2.
