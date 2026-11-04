# Map Branches, Labels, Goal and Picks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The map's goal is one box. Obstacles become a real tree with outline labels like 1B3. Stars get a plain label, and the person can change them on the page.

**Architecture:** New decisions go in `<script id="map-logic">` as functions with no DOM, tested under node. The page code draws from them. The JSON shape in `prompt.md` and the shape check in the template change together, because Claude writes what the page reads.

**Tech Stack:** One self-contained HTML file, pytest driving node, the committed page flows in `e2e/tests/six_step_page_flows.js`.

**Spec:** Eric's three requests on 2026-11-04, agreed in full. The spec file `docs/plans/2026-11-03-6-step-process-design.md` in the main checkout gets updated afterward by the controller.

## Global Constraints

- Label scheme: first level 1, 2, 3; under that A, B, C; under that 1, 2, 3; deeper levels keep alternating. Labels join with no separator: `1B3`, `1B3A`. Past Z, letters go AA, AB.
- Labels are computed from position and never stored. Deleting an item renumbers its later siblings.
- Solutions get no labels.
- A root cause is bold and ends its branch. One obstacle can have several root causes in different branches.
- No real maps need converting. A map in the old shape shows the page's "can't be drawn" message.
- Exact words: "★ My picks" / "This is one of my picks".
- All saving behavior stays as it is: status lines, refusals, top right placement, and no write over a file Claude changed.
- No em or en dashes in the template or example map. Don't write `<` into the template source. No outside URLs. Never put a client name in any file.
- `example-map.html` matches the template outside its `map-data` block.
- Run tests with `/Users/ericpage/software/aligned_cc_skills/e2e/.venv/bin/python -m pytest e2e/tests -q`. Expected skips: 180.
- One shell command per Bash call, no `&&` or pipes. Commit with `-m`. Don't bump versions by hand.

## Review Focus

1. Deleting an item with children: its whole branch goes, and solutions tied only there return to the tray instead of vanishing.
2. A solution on several items keeps working: `×2` counts every place in the tree, and removing it from one leaves the others.
3. A blank new sub-item being edited must not write to the file, under the existing hold on new items.
4. A deep or wide branch on one side of the goal must not overlap other branches or lose its connecting lines, including at phone width.
5. The shape check must reject a bad tree at any depth, including a duplicate id, and a root cause with children, and must name the problem.

---

### Task 1: The goal is one box

**Files:**
- Modify: `frameworks/6-step-process/mind-map-template.html`, `example-map.html`, `prompt.md`, `examples.md` as needed, in `frameworks/6-step-process/`
- Test: `e2e/tests/test_six_step_map_logic.py`, `e2e/tests/test_six_step_process.py`, `e2e/tests/six_step_page_flows.js`

**Decisions:**
- Shape becomes `"goal": {"text": ""}`. The shape check requires `text` and ignores nothing else specially. Remove `goalLine`, `setGoal`'s other fields, the From, To and By inputs and the goal line under the goal box.
- `prompt.md` still asks "What outcome do you want, with a number if you can? From what, to what, by when?" Claude writes the answer as one sentence in `goal.text`, such as "80% in-office attendance by end of Q2, up from 40%".
- The rule that "from" can stay unknown stays. Claude writes "starting point not known yet" into the sentence. The Step 5 rule becomes: if the starting point isn't known, the first Execute item is finding today's number.
- The example map's goal text becomes "80% in-office attendance by end of Q2, up from 40%".

- [ ] **Step 1: Write failing tests**: `test_goal_editor_has_one_box` (no `From`, `To`, `By` labels in `openEditor`), `test_map_with_only_goal_text_passes_the_shape_check`, `test_prompt_json_goal_has_only_text`, a flow that edits the goal and sees it in the file. Remove the `goalLine` tests.
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** Rebuild the example last.
- [ ] **Step 4: Run the full suite. Expected: passes with 180 skips.**
- [ ] **Step 5: Commit** `feat: make the map's goal one box`

### Task 2: Obstacles become a labeled tree

**Files:**
- Modify: template, example map, `prompt.md`, `examples.md`, `anti-examples.md` in `frameworks/6-step-process/`
- Test: `e2e/tests/test_six_step_map_logic.py`, `e2e/tests/test_six_step_process.py`, `e2e/tests/six_step_page_flows.js`

**Interfaces:**
- Shape of every item at every depth: `{"id": "o1", "text": "", "root_cause": false, "solution_ids": ["s1"], "children": []}`. `obstacles` is the top-level list. `whys`, the string form of `root_cause`, and `solution_at` are gone.
- Produces in `MapLogic`: `itemLabels(map) -> {id: label}`, and replaces the why and root-cause operations with `addChild(map, parentId, id, text)`, `deleteItem(map, id)`, `setRootCause(map, id, isRoot)`. Keep or adapt the other operations so they walk the tree.

**Decisions:**
- **Solution placement:** a solution sits on the item whose `solution_ids` holds it. On an item with children, it's drawn directly under that item in the same column. On an item with no children, it's drawn in the next column out. This replaces `solution_at`, and also fixes "directly under the selected item".
- **Root cause:** only an item with no children can be one. Adding a sub-obstacle to a root cause is refused the way adding a why is today, so the editor doesn't offer it.
- **Editor:** every item that isn't a root cause offers "Add a sub-obstacle". An item with no children offers a way to mark or unmark it as the root cause. Keep the existing delete and "Move to" controls, listing every item in the tree by label and text.
- **Delete:** removes the item and everything under it. Solutions left with no place go back to the tray. The editor's delete control says how many sub-items go with it when there are any.
- **Labels:** drawn at the start of each obstacle box, in the box's text, in a muted bold style. The label also appears anywhere the page names an obstacle, including "Move to" and the plan panel.
- **Sides:** the first half of the top-level obstacles go on the right, top to bottom, and the rest on the left, top to bottom. An odd count puts the extra one on the right. So 1, 2, 3 read down the right and 4, 5, 6 down the left.
- **Goal stays in the true center** with the existing fit-to-window scale and floor.
- **Phone width:** indent by depth, with labels.
- **Prompt:** the JSON block and every rule that names `whys`, `root_cause` as text, or `solution_at` change to the new shape. In the root-cause step, each answer to "why" becomes a child of the item being asked about. When the person gives two different reasons, each becomes its own child. Keep the existing rules on how deep to go and that the person decides. Claude uses labels when talking about items: "1B3". The rule that a solution with no named place goes at the end of the chain becomes: tie it to the item it gets past, usually a root cause.
- **Example map:** rewrite its data so it shows real branching: at least one obstacle with two sub-obstacles (1A, 1B) and one branch three levels deep (1B1), plus root causes and a solution on an item with children.

- [ ] **Step 1: Write failing tests**, including in the logic file:
  - `test_item_labels_alternate_by_depth`: a tree gives `1`, `2`, `1A`, `1B`, `1B1`, `1B2`, `1B2A`.
  - `test_item_labels_past_z`: the 27th child at the letter level is `1AA`.
  - `test_delete_item_removes_the_branch_and_returns_lone_solutions_to_the_tray`
  - `test_delete_item_keeps_a_solution_tied_elsewhere`
  - `test_repeat_count_covers_the_whole_tree`
  - `test_root_cause_cannot_have_children`, both ways.
  - `test_shape_check_rejects_old_shape`, `test_shape_check_rejects_a_bad_child_at_depth`, `test_shape_check_rejects_duplicate_ids`, `test_shape_check_rejects_a_root_cause_with_children`
  - `test_sides_put_first_half_on_the_right`
  - In the flows: add a sub-obstacle and see its label; delete a branch; hold back a blank new sub-item from the file.
  - In the process file: `test_prompt_json_shape_is_the_tree`, `test_prompt_no_longer_names_whys_or_solution_at`.
  Rewrite existing tests that use the old shape so they keep protecting the same behavior.
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** Rebuild the example last.
- [ ] **Step 4: Run the full suite. Expected: passes with 180 skips.**
- [ ] **Step 5: Commit** `feat: make the map's obstacles a labeled tree`

### Task 3: Picks are labeled and the person can change them

**Files:**
- Modify: template, example map, `prompt.md`, `examples.md` as needed
- Test: same three test files

**Interfaces:**
- Produces in `MapLogic`: `setStar(map, solutionId, isStar) -> map`.

**Decisions:**
- The header's right-hand group shows a key, "★ My picks", whenever at least one solution has a star.
- The solution editor replaces "To change a star, tell Claude." with a checkbox labeled "This is one of my picks". Changing it saves like any other edit.
- `prompt.md`: "Stars change only through you" goes. The person can change picks on the page. On pick-up, Claude asks about any new pick with no Step 5 row, and asks whether to drop the Step 5 row of a pick the person removed, listing each in plain words. Agreed picks in Step 4b still get their stars from Claude. When Claude first adds stars, it says what they mean in one line.

- [ ] **Step 1: Write failing tests**: `test_set_star_changes_only_that_solution`, `test_star_key_shows_only_with_stars`, a flow that ticks the box and sees the star in the file and the key appear, `test_editor_offers_the_picks_checkbox`, `test_prompt_handles_a_pick_removed_on_the_page`. Update tests that assert the old star sentence.
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** Rebuild the example last.
- [ ] **Step 4: Run the full suite. Expected: passes with 180 skips.**
- [ ] **Step 5: Commit** `feat: label the map's picks and let the person change them`

### After the tasks (controller)

- Whole-branch review of these three tasks.
- Look at the example map in Chrome over localhost, wide and narrow, with the Show plan panel open.
- Refresh the check map on the Desktop for Eric.
- Update the spec in the main checkout.
