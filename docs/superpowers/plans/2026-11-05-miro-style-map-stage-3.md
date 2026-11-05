# Miro-Style Map, Stage 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eric tried stages 1 and 2. Take out root causes, the tray, the header's "Add an obstacle" and "Move to", then add dragging: drop an item on a box and it becomes a sub of that box.

**Architecture:** Decisions stay in `<script id="map-logic">` with no DOM. The page code draws from them. Drag state lives in the page code, and a drop goes through `moveItem`.

**Tech Stack:** One self-contained HTML file, pytest driving node, the page flows in `e2e/tests/six_step_page_flows.js`, and a check in real Chrome.

**Spec:** `docs/superpowers/specs/2026-11-05-miro-style-map-design.md`. This plan's Global Constraints win where the spec still says otherwise.

## Global Constraints

- Every item at every depth has five fields: `{"id": "o1", "kind": "obstacle", "text": "", "star": false, "children": []}`. `root_cause` and `unplaced` are gone, and the check refuses a map that has either.
- Any item can hold obstacles and solutions under it, at any depth. The goal can too. The old rules on root causes, on top-level solutions and on solutions under solutions are all gone.
- An item can move onto the goal or any other item, except itself, anything beneath it and its current parent. The goal can't move.
- Labels stay computed and obstacles get them. Solutions don't.
- Saving behavior stays as it is. Don't change how saving turns on. Eric has an open decision there, and it's outside this plan.
- The map is always white. Phones are out of scope. Keep the star, the trash can and the plus buttons as they are.
- No em or en dashes in the template or example map. No outside URLs. Never a client name in any file.
- `example-map.html` matches the template outside its `map-data` block. Rebuild it last with `python3 /private/tmp/claude-501/-Users-ericpage-software-aligned-cc-skills/4a79a0fa-0010-4e50-a008-c2c02123d4e9/scratchpad/rebuild_example.py frameworks/6-step-process`.
- Run tests with `/Users/ericpage/software/aligned_cc_skills/e2e/.venv/bin/python -m pytest e2e/tests -q`. Expected skips: 180.
- One shell command per Bash call, no `&&` or pipes. Commit with `-m`, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Don't bump versions by hand.

## Review Focus

1. A drag that starts while a blank new item is open: the blank drops, nothing blank is written, and the drag still works. Pinned in Task 2.
2. A press and release with no movement is a click, a double-click still types, and the click after a real drag selects nothing new. Pinned in Task 2.
3. A cancelled drag (Escape, release on empty space, release on an item that can't take it) changes nothing and writes nothing. Pinned in Task 2.
4. A successful drop writes once, keeps the item selected and renumbers. Pinned in Task 2.
5. Claude's script has no leftover instruction to mark a root cause or use a tray. Pinned in Task 1.

---

### Task 1: Take out root causes, the tray and the header button

**Files:**
- Modify in `frameworks/6-step-process/`: `mind-map-template.html`, `example-map.html`, `prompt.md`, `examples.md`, `anti-examples.md`
- Test: `e2e/tests/test_six_step_map_logic.py`, `e2e/tests/test_six_step_process.py`, `e2e/tests/six_step_page_flows.js`

**Decisions:**
- Remove `setRootCause`, `canBeRootCause`, the Root cause button, `.item.root`, and every root cause rule in `canAdd`, `canMove`, `addItem` and the check. `canAdd` is true for any existing parent and either kind.
- Remove `map.unplaced`, the `#tray` part of the page, its CSS and its tests. `canPick` and `setStar` work on every solution.
- Remove the header's `#add-obstacle` button and the focus return to it. Escape or dropping a blank new item puts focus back on the item it came from. On an empty map, the hint tells the person to click the goal, and the goal's pluses add the first items. Update the hint in plain words.
- Move to and its code stay in this task. Task 2 removes them.
- **`prompt.md`:**
  - The JSON block and read-back rules move to the five fields.
  - Step 3c keeps asking "why" as today, and Claude adds each answer as a sub-obstacle. Claude doesn't mark anything as a root cause, and the person decides when to stop. The step's name and purpose stay, because finding root causes through asking why is still the framework.
  - Rules that say a solution usually ties to a root cause now say the deepest obstacle it gets past.
  - A solution offered before its obstacle exists goes directly under the goal in the map, and Step 4a nudges it to the obstacle it gets past. Remove the holding list wording that depends on the tray. The Resuming rule counts solutions directly under the goal the way it counted the tray.
  - Pick-up no longer mentions an item that stopped being a root cause.
- **Example map:** rewrite the data with no `root_cause` or `unplaced`, placing the tray solution on the map, and keep an obstacle under a solution and a solution under a solution.

- [ ] **Step 1: Write failing tests**: `test_every_item_takes_both_pluses`, `test_goal_takes_a_solution`, `test_check_refuses_root_cause_and_unplaced_fields`, `test_page_has_no_root_cause_tray_or_add_obstacle_button`, `test_prompt_never_marks_a_root_cause`, `test_prompt_puts_early_solutions_under_the_goal`. In the flows: `add the first obstacle on an empty map from the goal`, `escape on a new item returns focus to its parent`. Rewrite or delete tests only for what this task removes.
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** Rebuild the example last.
- [ ] **Step 4: Run the full suite. Expected: passes with 180 skips.**
- [ ] **Step 5: Commit** `feat: take root causes and the tray off the map`

### Task 2: Drag an item onto a box

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html`, `example-map.html`, `prompt.md` if it mentions Move to
- Test: `e2e/tests/test_six_step_map_logic.py`, `e2e/tests/test_six_step_process.py`, `e2e/tests/six_step_page_flows.js`

**Interfaces:**
- Consumes `canMove`, `moveItem`, `select`, `finishTyping` and `boxFor`.
- Produces in `MapLogic`: `isDragDistance(dx, dy) -> bool`, true at 5px or more.

**Decisions:**
- **Starting:** use pointer events on the canvas. A press on an item records it. Nothing else happens until the pointer has moved 5px. A press in the text box, on a control or on the goal never starts a drag. Only the main button counts.
- **At the start of a drag:** finish any open typing, which may redraw and may drop a blank new item. Then find the item again by id. If it no longer exists, cancel. Hide the controls and clear any delete question.
- **While dragging:** a ghost holding the item's text follows the pointer. It sits outside `#canvas`, is unscaled and has `pointer-events: none`. The original item dims. `document.elementFromPoint` finds the box under the pointer, and if `canMove` allows it, that box shows the `--focus` outline. Stop text from being selected. Near an edge of the map, scroll the map so a far target can be reached.
- **Dropping:** on a highlighted box, call `moveItem` through `setMap`, keep the item selected, and let the normal render and write happen. Anywhere else, or on Escape, or on `pointercancel`, or if the window loses focus, cancel: nothing changes and nothing is written.
- **The click after a drag:** a real drag must not select or clear anything through the click that follows. A press and release under 5px stays a plain click, so double-click still types.
- **Remove "Move to":** `moveControl`, `#move-to`, its CSS and flows. `moveTargets` goes too if nothing else uses it. Keep `canMove`.
- Clean up two leftovers: the "checkbox" comment near the toolbar focus code, and `subItems` in `deleteEffects` if nothing reads it.

- [ ] **Step 1: Write failing tests.** Extend the stub DOM for pointer events and `elementFromPoint`. In the logic file: `test_drag_distance_threshold`. In the process file: `test_page_has_no_move_to`. In the flows: `a small press is a click and selects`, `dragging onto a box makes it a sub and renumbers`, `a drop writes once and keeps the item selected`, `dragging onto the item's own parent or a descendant changes nothing`, `escape cancels a drag with no write`, `release on empty space cancels with no write`, `a drag with a blank new item open drops the blank and writes no blank`, `the click after a drag selects nothing new`, `the goal cannot be dragged`, `a press on a control starts no drag`.
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** Rebuild the example last.
- [ ] **Step 4: Run the full suite. Expected: passes with 180 skips.**
- [ ] **Step 5: Commit** `feat: drag an item onto a box to make it a sub`

### After the tasks (controller)

- Whole-branch review of this plan's commits.
- Real Chrome over localhost: drag at 100% and at low zoom, drag with a blank new item open, resize while typing.
- Refresh `~/Desktop/six-step-chrome-check/miro-test-map.html`.
- Update the spec and the design page to match.
