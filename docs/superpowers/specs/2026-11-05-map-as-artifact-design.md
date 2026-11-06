# The Map as a Claude Artifact

The 6-step map becomes a private Claude artifact that saves itself, updates live, and can be shared so colleagues edit the same map. Eric reads this to approve the design before the build starts.

## Intent

Eric wants people in his organization to open one link and update the same map, with nothing to save and no file dialog. A local file can't do that. It makes people pick the file, and copies drift apart once it's emailed around.

## What we tested

| Check | Result |
|---|---|
| Publish from Cowork, write data, read it back | Worked. Eric ran it in Cowork, and +1 went to 42 and stayed after a reload |
| Real mouse drag inside an artifact | Worked. Eric's drag was recorded |
| Page draws, selects, types, stars, deletes in the viewer | Worked with keys and simulated clicks in a test copy |
| Claude changes the data and the open page updates | Worked, about a second later |
| Claude's write with an out-of-date version | Refused, nothing written |
| One saved document with two people editing | Lost an edit while both screens said saved |
| One document updated by changed fields only | Lost nothing in one run of two tabs writing within 3 ms |
| Size | 262,144 bytes per document. The example map is about 6,640 bytes |
| Depth of nested data | 15 levels saved, 16 refused |
| A second person editing | Not tested |
| Reading an artifact from a Claude session on another account | Refused, so a map must be shared first |

## Goals

- A new map is a private artifact, and its creator gets the link.
- Every edit saves by itself, with no button and no dialog.
- The creator shares it from the page's Share menu. Colleagues with edit access change the same map, and everyone's screen updates live.
- Claude reads and changes the same map through its data tool.
- Everything built so far stays: tree, labels, white look, plus buttons, typing in place, star, trash can, dragging and the plan panel.

## Non-goals

- Live cursors or showing who's editing.
- Comments on the map.
- Undo or version history.
- One link holding many maps, because access is per artifact.
- A local file version. Eric removed it on 2026-11-05.

## Anti-goals

The work has failed if any of these is true:

- Two people editing at once silently loses an edit to a different item.
- Claude's or a colleague's change gets wiped by someone who opened a text box and didn't change anything.
- The page says "All changes saved" when a write failed.
- A map gets shared without its creator choosing to share it. A map made inside a Claude project is open to that project's members through the project, and that is fine.

## Approaches

| Way to build it | What it costs | Result |
|---|---|---|
| Shared data, with one document holding items by id, and writes that send only what changed | Page needs a tree-to-flat step and a queue of changes | Picked |
| Shared data, with the whole map in one document | Silently loses edits, as tested | Dropped |
| Shared data, with one document per item | Claude's rewrite stops at 50 writes per batch, so it can't be one step on a big map | Dropped |
| The page republishes itself on each edit | A conflict reloads every open page and drops the edit | Dropped |
| Artifact only, with no local file | Someone without the Artifact tools gets a plain message and no map | Picked by Eric |
| Artifact, with the local file as a fallback | Two ways of saving to keep working | Dropped by Eric |

## How it works for a person

1. They run the framework. Claude publishes their map privately and gives them the link.
2. They open the link and edit. Saving just happens, and the status says "Saving..." then "All changes saved".
3. When they want others in, they use the page's Share menu. Each map is private until then, so the framework's rule that each person works alone first still holds.
4. People with edit access change the map, and everyone sees it live. People with view access see it live but get no plus buttons, toolbar or dragging. Without other members on the plan, only the owner and editors invited by email can write, and a public link takes editing away from outside editors.
5. To pick up, they give Claude the link. If Claude can't open it, Claude says the map needs sharing with that account and stops.

## Data

Stored in the artifact's shared data, under the collection `maps`.

**`maps/main`** holds the map:

```json
{
  "person": "Maya",
  "goal": {"text": ""},
  "items": {
    "k3f9a": {"kind": "obstacle", "text": "", "star": false, "parent": "goal", "order": 1},
    "m2x7c": {"kind": "solution", "text": "", "star": false, "parent": "k3f9a", "order": 1}
  },
  "key_actions": [{"text": "", "risk": "high", "solution_ids": ["m2x7c"]}],
  "execute": [{"solution_id": "m2x7c", "first_move": "", "owner": "", "others_decide": ""}],
  "feedback": {"number": "", "check_on": "", "redraw_if": ""}
}
```

**`maps/baseline`** holds what Claude last wrote, for the "what changed" report at pick-up.

- Ids are random lowercase letters and digits, so two people adding at once can't collide.
- A `version` field in `maps/main` names the data format, for later changes.
- `order` sets the order under a parent. A new or moved item goes last, taking the highest order under that parent plus one, and ties go by id. A drag can't land between two siblings.
- The page turns this into the tree the rest of its code already uses, and turns its changes back into fields to send.
- Labels stay computed.

**When two people's edits collide:**

| What happened | Result |
|---|---|
| Two people edit different items | Both kept |
| Two people edit the same item's text | The last one wins for that item, with a notice |
| Someone opens a text box and changes nothing while another edits that item | The other edit stays |
| Someone stars an item as another deletes it | It stays deleted |
| Someone deletes a box while another adds under it | The new item shows directly under the goal, so nothing vanishes |
| Two people each drag one box under the other | One goes directly under the goal, so nothing vanishes |

Plan rows and key actions stay lists, and only Claude writes them, so people can't collide there.

## How the page saves

**Which saving a page uses.** The page decides before it reads any map data. `window.claude` undefined means the page is outside Claude. The `artifact-capabilities` skill and its type definitions are the source of truth for the data calls.

| Where the page is running | What it does |
|---|---|
| Opened outside Claude | Says the map opens inside Claude. No editing |
| In the viewer, and the data opens | Runs from the shared data |
| In the viewer, signed out or the data can't open | Says it can't open the map. No editing |
| In the viewer, with no map in the data | Says the map isn't set up. No editing |

**Each action makes its own change.** Moving, typing, starring and deleting each work out exactly what that action changed, and that change joins a queue. One write goes at a time, as the platform requires. The page never compares what's on screen with what's stored, because that's the way an edit gets lost or an old value gets sent back over someone else's.

**The shape of a change.** A change to an item is a nested object naming only what changed, like `{items: {k3f9a: {text: "new"}}}`. A new item sends all its fields. A delete sends `{items: {k3f9a: {__delete__: true}}}` for the item and for everything under it. If Stage 0 shows the page can't delete that way, a delete sets `deleted: true`, and reads ignore those items.

**What's on screen** is the last data received plus any changes still waiting to send, so a live update can never erase an edit waiting its turn.

**An open text box.** The page remembers the text at the moment the box opened. If it's unchanged when the box closes, nothing is written. If the person did change it and someone else changed the same item meanwhile, the last one wins and the page shows a short notice.

**Reading is forgiving, and it never writes repairs back,** so tabs can't fight:
- An item with no `kind`, left by a delete racing an edit, is ignored.
- An item whose parent is gone shows directly under the goal.
- Two boxes that ended up under each other are broken at the lowest id, so every tab agrees.
- A plan row naming a missing solution is hidden.

**The plan.** The page has no way to write `key_actions` or `execute`. Claude is the only writer of those, and the page only reads and filters them. Deleting a solution hides its rows every time the map draws, and Claude cleans them up the next time it writes, if that ever happens.

**An unknown `version`.** The page shows the map without editing controls and says it needs a newer page.

**Status.** "All changes saved" means nothing is waiting and the last write was confirmed. A write that fails because the connection dropped retries. If a write takes too long, or the live connection dies, the page says so and keeps the edit on screen. A refused write keeps the edit on screen, marked as not saved, with a plain message and no automatic revert. A star or move on an item someone deleted meanwhile is dropped. Words typed on a deleted item are kept under the goal, with a notice saying the item was deleted.

**During a live update:** an open text box and a drag keep going. A drag of an item someone just deleted cancels. A blank new item stays. An open Confirm Delete closes if the item is gone.

**Who can write.** A person who can't write sees the map with no editing controls. If the page can't tell in advance, as with outside guests, it finds out from the first refused write.

## What changes for Claude

Without both the Artifact and ArtifactData tools, or if a publish fails, Claude says so plainly and stops.

- **Publishing:** the template has no `<title>` or html, head and body tags of its own, and its language is set by script. Claude publishes that file directly, naming the artifact with the tool's title setting, and declares `db` only.
- **First write:** write `maps/main` and `maps/baseline` together in one batch.
- **Each write:** read `maps/main`, then send only what changed, pinned to the version just read, with the matching `maps/baseline` in the same batch. Removals must be marked for deletion, because updates merge. If it's refused, read again and redo the change.
- **Plan rows:** Claude is the only writer, and it removes rows naming a solution that's gone.
- **Labels:** Claude works them out from flat data, which is new, so an eval tests it.
- **Pick-up:** read `maps/main` and compare with `maps/baseline`. A refused read looks the same as a map that wasn't shared, so Claude says both possibilities.
- **"Each map is one person's"** changes: a shared map can change while Claude is working, and Claude reports edits it didn't make.
- **Stays:** all six steps, every WAIT, private lists, labels, and the rule that map text is content and never instructions. That rule matters more when several people write to the map.

## The local file fallback

There is none. Eric removed it on 2026-11-05. File saving, the file dialog, Save a copy, Turn on saving, the file revision checks and the browser note all come out of the template.

## Deleting

Every delete asks, every time. A small card at the trash can says "Confirm Delete" with a Delete button. Escape or clicking elsewhere cancels. The old question listing what a delete removes is gone.

## The build, in stages

0. **Probes in the real viewer, before any build.** This is a gate: the plan assumes they pass, and a failure comes back to Eric before Stage 1. Edit a second item while the first is saving. Delete an item against someone starring it. See what a deletion looks like while it's waiting. Try saving while offline. Publish the one-file template directly. A real colleague edits the test copy. Any of these can change the design.
1. **Flat data.** Tree-to-flat, per-action changes, forgiving reads, random ids, all pure logic.
2. **Saving through shared data.** The queue, first load, live updates, status, view-only mode, on the real page in the viewer.
3. **Claude's script.** `prompt.md`, examples, the runner's artifact section and an eval of Claude's writes.
4. **Confirm Delete.** The card on every delete.
5. **Take out the local file.** Remove file saving from the template and its tests.

## Tests

- `e2e/tests/test_six_step_map_logic.py`: flat data, per-action changes, forgiving reads.
- `e2e/tests/test_six_step_process.py`: `prompt.md` rules on both paths.
- `e2e/tests/test_framework_artifacts.py`: this framework's artifact section, which conflicts with the runner today.
- A new test driver for the artifact page with a fake data store, covering load, the queue, live updates during typing and during a drag, a failed write, the host checks, and view-only mode. Flows for editing move onto this driver when the local file comes out.
- An eval: Claude rewrites a shared map through its data tool.
- Real viewer, by Claude: two tabs racing, Claude writing while a tab types.
- By hand: a real colleague editing a shared map.

## Calls I made

- A map stays private until its creator uses Share, except that members of the Claude project it was made in can open it.
- One artifact per map.
- When two people change the same item's text, the last one wins and the page shows a notice.
- A box's new sub-items move directly under the goal if the box was deleted.
- Claude is the only writer of plan rows, so a person deleting a solution doesn't race Claude.

## What we still don't know

- Whether the undocumented limit on an organization's databases matters at scale.
- What a colleague really sees until one tries it.

## Left to the builder

- Function names and the exact wording of status messages.
- How live updates schedule a redraw.
