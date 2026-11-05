# Miro-Style Mind Map

The 6-step mind map should edit like a Miro mind map: click an item, press a plus to add to it, type in place, and drag it onto another item. Eric reads this to approve the design before the build starts.

## Intent

Eric finds the current map harder to use than a Miro mind map. He likes that the page knows obstacles from solutions and that picks carry a star. He wants those kept and the editing made simpler. He also wants to break any solution down into the obstacles standing in its way.

The framework is a skill people run on their own machines. Each person ends up with one HTML file they open in Chrome, and nothing else to install or run.

## Goals

- Click an item to select it. An orange plus adds an obstacle and a green plus adds a solution.
- Type an item's text in place. The form editor goes away.
- Drag an item onto another item to attach it there. The page keeps the layout tidy.
- Any solution can have obstacles under it, and those can have solutions, to any depth.
- Text on orange lines for obstacles and green lines for solutions. The goal sits in a box on the left, and everything runs to the right.

## Non-goals

- Free placement. An item can't stay where it's dropped. The file stores no positions.
- A renumber button. Labels stay based on position, so they update when items move or get deleted.
- Repeated solutions. A solution lives in one place. If two obstacles need the same fix, each gets its own separate copy.
- Converting old maps. No real maps exist in the old format, and an old file shows the "can't be drawn" message.
- Changing how saving works.

## Anti-goals

The work has failed, even if every feature runs, if any of these is true:

- A person needs a server, an install beyond the plugin, or an internet connection to use the map.
- A delete or drop silently loses a pick or a plan row.
- Dragging or typing writes half-finished work to the file.
- Claude can't reliably create or rewrite the file.

## Constraints

- One self-contained HTML file, no outside URLs.
- Saving rules stay: no write over a file Claude changed, and no write of a blank new item.
- Claude and the page read and write the same JSON, so the data format, the page's check, and `prompt.md` change together.
- Works at phone width and by keyboard.
- No em or en dashes in the template or example map. No client names in any file.

## Approaches

| Way to build it | What it costs | Result |
|---|---|---|
| Extend the page's own code | More code in the template | Picked |
| Paste a mind map library into every map file | Larger file that Claude may have to copy by hand, plus conflicts with the label, save and hold-back rules | Dropped |

The architect saw no third option worth considering. Eric asked whether this is getting too complicated for a skill people run themselves. People still get one file and run no server. The added complexity is in the page's code and in the file size.

## How it looks

- The goal is in a rounded box on the left. Top-level obstacles run down its right side as 1, 2, 3.
- Obstacles have orange lines and solutions have green lines. Items are plain text with no box, except the selected item, which gets a thin outline.
- A root cause is bold. A pick shows a star. The "★ My picks" key stays in the header.
- Every item sits in the next column out from its parent, including solutions. This drops today's rule that puts some solutions directly under their obstacle, and it makes maps wider.

## How editing works

**Selecting.** A click selects an item and shows its controls. Selecting doesn't change the map.

**Plus buttons.**

| Selected item | Orange plus (obstacle) | Green plus (solution) |
|---|---|---|
| The goal | Yes | No |
| An obstacle | Yes | Yes |
| A root cause | No | Yes |
| A solution | Yes | No |

**Typing.** A new item opens ready to type. Typing on an existing item starts from a double-click, or from Enter while it's selected. Enter finishes and Escape cancels. A new item stays out of the file until it has text.

**Toolbar on the selected item.** Pick (placed solutions), Root cause (obstacles with no obstacle directly under them), Delete and the "Move to" list.

**The root cause rule, everywhere.** A root cause can't have an obstacle directly under it. A solution under a root cause can still have obstacles of its own. The toolbar, the plus buttons, drops, "Move to" and the page's check all use this one rule.

**Dragging.** Pressing an item and moving it starts a drag. Dropping attaches it to the item under the pointer as its last child.

| Dropped | On a goal | On an obstacle | On a root cause | On a solution |
|---|---|---|---|---|
| An obstacle | Yes | Yes | No | Yes |
| A solution | No | Yes | Yes | No |

Dropping on the item's own parent, on itself or on anything beneath it does nothing. A drop anywhere else does nothing either. On a phone, only an item already selected can drag, so a swipe still scrolls the page.

**Moving by list.** "Move to" stays and now covers obstacles too. It does what a drag does, for keyboard users and for phones.

**Deleting.** Delete removes the item and everything under it. If that holds a pick or a plan row, the page asks first and names what would go. Otherwise it deletes straight away. After a yes, each deleted solution's Execute row goes too, and its id comes off any key action. The key action itself stays, even with no solutions left, because it comes from the strategy.

**The tray.** The tray holds solutions Claude wrote before they were tied to anything. A person can edit one, delete one, or attach one by dragging it or using "Move to". Attaching is one-way, so nothing sends a solution back to the tray. Tray solutions can't have picks or obstacles under them until they're attached, because they have no number to continue.

## Numbering

Labels stay computed and are never stored. Obstacles get them and solutions don't.

- Top-level obstacles: 1, 2, 3. Under those: A, B, C. Under those: 1, 2, 3. Deeper levels keep alternating.
- An obstacle under a solution continues the numbering of the nearest obstacle above it. All of them count together in reading order, so they can't produce a duplicate.
- Example: 1B has a child obstacle and a solution, in that order, and the solution has an obstacle under it. The child is 1B1 and the obstacle under the solution is 1B2.

`prompt.md` will explain that 1B2 could be an answer to "why" on 1B, or an obstacle in the way of a solution on 1B, and that the map shows which.

## Data

The whole map is one tree. Every item has the same six fields, so Claude and the page check the same thing.

```json
{"id": "o1", "kind": "obstacle", "text": "", "root_cause": false, "star": false, "children": []}
```

- `obstacles` stays the top-level list. The `solutions` list and `solution_ids` go away.
- `unplaced` is a new top-level list for solutions in the tray. Items there have no children.
- `key_actions[].solution_ids` and `execute[].solution_id` still name solution ids.

The page's check refuses a map when:

- an id repeats anywhere in the tree or `unplaced`
- a field is missing, or `kind` is anything else
- the old `solutions` list is present
- a root cause has an obstacle under it, or a non-obstacle is marked as one
- a solution has a solution directly under it
- an `unplaced` item has children
- a non-solution has a star, or an `unplaced` item has one
- a plan row names a solution id that doesn't exist

## What changes for Claude

`prompt.md`, `examples.md`, `anti-examples.md` and `example-map.html` all move to the new format.

- A solution serving two obstacles gets asked about: which one does it belong to, or should it be two separate solutions?
- Pick-up compares items by id and parent, and reports moved obstacles with what's under them, along with moved solutions.
- The root cause rule becomes "no obstacle directly under a root cause". Solutions can sit there.
- The example map is rewritten so it shows an obstacle under a solution and no repeats.

## The build, in three stages

1. **New data format.** Tree, page check, labels, layout, prompt and examples. The form gets only the changes it needs to keep the page usable, because stage 2 replaces it.
2. **Editing and look.** Selecting, plus buttons, typing in place, toolbar, keyboard and the orange and green lines. This stage ends with a usable map that moves items through the list.
3. **Dragging.** Eric can stop before this stage if stage 2 feels like enough.

Each stage's tests are written first.

## What the architect changed

1. A root cause keeps the green plus and loses the orange one. The old rule would have failed every finished map.
2. Delete asks first when a pick or plan row would go.
3. Tray solutions stay simple until attached, which prevents duplicate numbers.
4. Labels count in reading order across a whole level, with one shared function.
5. The text box and toolbar sit above the map, unscaled, so a redraw can't destroy what someone is typing and a low zoom stays usable.
6. A press that starts a drag finishes any open edit first, then finds the item again by id, because finishing the edit redraws the page.
7. The "Move to" list stays and covers obstacles.
8. Three stages instead of one plan.

## Tests

- `e2e/tests/test_six_step_map_logic.py`: tree operations, labels, drop rules, delete warnings and the page's check. Rewrite the tests built on the old format.
- `e2e/tests/test_six_step_process.py`: the rules and the JSON in `prompt.md`, and the template's page source.
- `e2e/tests/test_six_step_page_flows.py` and `e2e/tests/six_step_page_flows.js`: add, type, delete and move through the page code.
- Real Chrome on localhost: the stub page can't simulate gestures, so these get checked by hand, first thing in stage 3:
  - with a blank new item open, press another item and drag it, at 0.8 zoom and at phone width
  - resize the window while typing

## Calls I made

- Double-click or Enter starts typing on an existing item.
- A drop attaches an item as its parent's last child. Reordering items under the same parent uses "Move to" or waits for a later change.
- The goal takes the orange plus only, because the map's top level is obstacles.
- A solution can't be dropped on the goal or on another solution.
- Plan rows keep working as they do now, and the page's check now refuses one that names a missing solution.
- After a yes on delete, Execute rows go with their solutions, and key actions stay.
- The tray is attach-only, and tray solutions can't be picks.
- A root cause only limits what sits directly under it.
- The stage 1 form stays minimal.

## Left to the builder

- Function names, the drag ghost's look and exact spacing.
- How far the layout's scale floor goes for wide maps.
