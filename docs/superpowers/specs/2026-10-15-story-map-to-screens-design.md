# Story Map to Screens in One Session — Design

**Date:** 2026-10-15
**Framework:** `frameworks/user-story-map/` (advisor: Jeff Patton)
**Depends on:** `frameworks/breadboard-to-pages/` (advisor: Brad Frost, committed in fdcf6c8)

## What Eric does with this

Eric reads this to approve how one conversation goes from "here's the thing I want to build" to exact screens his coding agent builds from.

## Intent

Eric builds small apps alone, often with AI coding agents. He wants one session that starts with a story map and ends with rendered screens built in the project's design tokens. The screens are a guide for development. They are not the shipped page.

Today the User Story Map framework ends with rough wireframes that we invented (Phase 8). Two reviews changed the plan:

1. **Jeff Patton's critique** of the worked example, checked against his published maps (Story Mapping Quick Reference, "The New User Story Backlog is a Map" 2008, "It's All in How You Slice It" 2005). The framework cites his 2005 swim lanes wrongly. His maps use one shared timeline and three tiers of cards. Ours use stacked role lanes and two tiers.
2. **A research pass** on whether story mapping is still current. It is: nothing published since 2014 covers the whole job, and newer methods sit upstream (Teresa Torres, JTBD job maps, NN/g journey maps) or downstream (Ryan Singer's breadboarding). The weak spot was our invented wireframe phase. Singer's breadboard is the published method for that step.

Meanwhile another thread retired The Designer, added Brad Frost, and built `breadboard-to-pages`, which turns a breadboard plus `design-principles.md` into exact static screens at 390px and 1280px. It already expects to find the breadboard at the end of the story map Markdown.

## Goals

- One conversation, three advisors, each running their own published method:
  - **Phases 1–7, Jeff Patton:** frame, backbone, tasks and details, walk, other roles, slices, write the result.
  - **Phase 8, Ryan Singer:** breadboard Slice 1.
  - **Phase 9, Brad Frost:** run `breadboard-to-pages` in the same conversation.
- The map picture matches how Patton draws his maps: one timeline, three tiers, slices drawn once across the whole map.
- Every source citation in the framework is accurate.
- The worked example and both templates show the new shape.

## Non-goals

- No change to `breadboard-to-pages`. It already does the screen step. This design only feeds it.
- No new advisor and no new framework.
- No worked example of the screens page. `breadboard-to-pages` has its own examples.
- No upstream discovery step (Torres's opportunity solution tree). That's a different job.

## Anti-goals

- Anything that needs a second session or a new `/aligned:...` command typed by the user to get from map to screens.
- Team-process steps aimed at a design team ("who else should hear this walk," "walk both again with the people who'll build it"). Eric works alone.
- Any visual polish that makes the map look less like a wall of cards.

## Constraints

- Plugin portability (CLAUDE.md): every step works for any user who installs the plugin. Nothing may depend on superpowers or on Eric's environment.
- `use-framework` says "Run one framework per session. If the user wants another framework, start a new invocation." Phase 9 is a new invocation of `/aligned:use-framework breadboard-to-pages` inside the same conversation. It doesn't merge the two frameworks.
- The Markdown map is the source. The HTML is rebuilt from it, never hand-edited.
- The other thread has uncommitted work in `frameworks/registry.yaml`, `README.md`, `frameworks/README.md`, `advisors/prompts/brad-frost.md`, and `e2e/trigger-map.yaml`. This work must not overwrite it. Edits to shared files are line-level and land after that thread commits, or are coordinated.
- TDD. Tests in `e2e/tests/test_user_story_map_picture.py`.
- The pre-commit hook bumps the version. Never bump by hand.

## The flow, as decided

| Phase | Advisor | What happens | Drawn |
|---|---|---|---|
| 1 Frame it | Patton | User, outcome, problem, **why** (what the business gets), and the chooser if there is one | Frame tiles, empty map |
| 2 Big picture | Patton | Backbone of activities on one timeline, in story order, each activity naming the role or roles who do it | Backbone row |
| 3 Tasks and details | Patton | Under each activity, the user tasks left to right; under each task, sub-tasks, alternatives, exceptions, details, and rules, ranked by necessity | Three tiers |
| 4 Walk the map | Patton | Tell the story aloud as the user; name every gap. No "who else should hear this" step | Gap cards marked |
| 5 Other roles | Patton | Other roles join the **same** timeline where they enter the story. Tasks carry their role. When two roles act at the same point, their tasks share the activity | Role chips, role persona strip |
| 6 Slice | Patton | Slices with name, outcome, measure. Slice 1 runs start to finish; a column may be empty above the line only when a **workaround card** says how the user gets by | Slice bands once across the map |
| 7 Write result | Patton | Final Markdown | Map |
| 8 Breadboard Slice 1 | Ryan Singer | Places, affordances, connections for every Slice 1 task. Each affordance names its card. Then walk the breadboard against the map | Breadboard tab |
| 9 Screens | Brad Frost | Check for `design-principles.md`; if none, run `/aligned:create-design-principles` first. Then invoke `/aligned:use-framework breadboard-to-pages` in the same conversation. It reads the breadboard from the story map Markdown | Separate screens page |
| 10 Link back | Patton | Write the screens link into the map, rebuild, republish, give both links | Screens link on the map page |

### Advisor hand-offs

Each hand-off is one line spoken in the conversation, then the next advisor's voice:

- Into Phase 8: Patton says the map's agreed and Ryan Singer takes it from here to wire up Slice 1. Phase 8 is written in Singer's voice. The runner reads `advisors/prompts/ryan-singer.md` for his voice before Phase 8.
- Into Phase 9: Singer says the places are set and Brad Frost turns them into screens. Then invoke `/aligned:use-framework breadboard-to-pages`. Frost's framework runs its own phases and WAIT points unchanged.

### Phase 8 method (from *Shape Up* chapter 4, in Singer's words, not his archived Claude Code skills)

- **Places:** "things you can navigate to, like screens, dialogs, or menus that pop up."
- **Affordances:** "things the user can act on, like buttons and fields."
- **Connection lines:** how affordances take the user from place to place.
- Words only, no visual design. Quote only lines verified against basecamp.com/shapeup/1.3-chapter-04. (Builder: confirm each quote against the page before shipping it.)
- Every Slice 1 task on the map must appear as at least one affordance. Every affordance names the card it serves. An affordance with no card is a gap: add the card or drop the affordance.

## The map page

Template stays one HTML file whose only per-map changes are the `:root` tokens and the `map-data` JSON.

Visual changes, from Patton's critique:

1. **One timeline.** One backbone row. Each activity shows its role chip(s). No stacked lanes.
2. **Three tiers.** Activity (accent) spans its task columns. Task row (card color) runs left to right; the top task row in Slice 1 reads as the walking skeleton. Details hang under their task as smaller, quieter cards; rules are details.
3. **Slices drawn once** across the whole map, with name, outcome, and **measure** in the left label.
4. **Frame tiles:** User, Outcome, Problem, Why.
5. **Roles strip:** one small persona card per role (name and one line about them), in story order of first entry.
6. **Denser cards:** columns narrow from 180px to about 150px, tighter gaps, smaller detail type. Activity cards in a row stay equal height (Eric's earlier fix). Text stays readable without zoom.
7. **Tabs:** Map, Breadboard (appears once the breadboard has entries), and a "Screens" link out to the screens page once Phase 9 writes it.
8. Gap cards keep the dashed border. Workaround cards get their own mark (builder's call on the exact style, within the tokens).

### JSON shape

```json
{
  "title": "", "subtitle": "",
  "frame": { "user": "", "outcome": "", "problem": "", "why": "" },
  "roles": [ { "name": "Facilitator", "about": "Runs one team through the course" } ],
  "slices": [ { "id": 1, "name": "", "outcome": "", "measure": "" } ],
  "activities": [
    {
      "name": "Run the session",
      "tasks": [
        {
          "text": "Open the live exercise", "role": "Facilitator", "slice": 1,
          "gap": false, "workaround": false, "note": "",
          "details": [ { "text": "", "slice": 1, "kind": "detail | rule | alternative | exception", "gap": false } ]
        }
      ]
    }
  ],
  "questions": [],
  "breadboard": [
    { "place": "Who's ready for Thursday", "role": "Facilitator",
      "affordances": [ { "text": "Member row", "to": "", "card": "See who finished the lesson" } ] }
  ],
  "screens": ""
}
```

An activity's roles are the set of its tasks' roles. `screens` is a relative link to the screens page, empty until Phase 9.

### Markdown shape (`story-map-template.md`)

- `## Frame` — User, Outcome, Problem, Why.
- `## Roles` — table: Role | Who they are.
- `## Slices` — table: Slice | Name | Outcome | Measure.
- `## Map`, then `### {Activity}` with one table per activity: Card | Tier (task or detail) | Kind | Role | Slice | Gap | Note. Detail rows follow their task.
- `## Open questions`.
- `## Slice 1 breadboard`, then `### {Place} ({Role})` with a table: Affordance | Leads to | Card. This is the section `breadboard-to-pages` reads.
- The opening comment keeps the Markdown-to-JSON mapping table, updated.

## Files

| File | Change |
|---|---|
| `frameworks/user-story-map/prompt.md` | Rewrite "Other roles" (fix the 2005 citation: his lanes are vertical columns on one timeline; the Quick Reference places users along the backbone). Phases 1, 3, 4, 5, 6, 7 revised as in the table. Phase 8 becomes Singer's breadboard. Phase 9 hand-off added. Key Rules updated. Wireframe language removed. |
| `frameworks/user-story-map/story-map-template.html` | New JSON shape and rendering as above. |
| `frameworks/user-story-map/story-map-template.md` | New Markdown shape. |
| `frameworks/user-story-map/examples.md` | Examples redone on one timeline with tasks and details; Phase 6 workaround card for "Wrap up the unit"; stronger Slice 2 measure; Phase 8 breadboard golden path in Singer's voice; Phase 9 hand-off. "The Designer" references become Brad Frost. |
| `frameworks/user-story-map/anti-examples.md` | Anti-examples that cite wireframes updated; add one for stacked lanes, and one for a breadboard affordance with no card. |
| `frameworks/user-story-map/example/team-course.md` and `.html` | Rebuilt in the new shape, through Phase 8. Why line: "Teams that finish a unit sign up for the next." Review page: https://claude.ai/artifact/KrSkaz8sJu8RWd3YxrU1ot |
| `advisors/prompts/jeff-patton.md` | Core Frameworks line: map ends in a breadboard and hands off to Brad Frost for screens. Any "own lane" wording fixed. |
| `advisors/prompts/ryan-singer.md` | Note that breadboarding now runs as Phase 8 of User Story Map. |
| `frameworks/registry.yaml` | `user-story-map` entry description updated (after the other thread commits). |
| `e2e/tests/test_user_story_map_picture.py` | Tests below. |
| `e2e/scenarios/use-framework/user-story-map.yaml`, `user-story-map-picture.yaml` | Updated for the new phases; rerun only these two plus `jeff-patton-consult`. |

## Tests (`e2e/tests/test_user_story_map_picture.py`)

Replace the wireframe tests with:

- prompt.md no longer says the lanes "follow the swim lanes Patton described"; it says his 2005 lanes are vertical columns on one timeline.
- Phase 4 has no "who else should hear" step; the closing has no team walk.
- Phase 6 allows an empty column only with a workaround card.
- Phase 8 is titled for breadboarding, names Ryan Singer and *Shape Up*, and requires every affordance to name a card.
- Phase 9 names `breadboard-to-pages` and Brad Frost, says it runs in the same conversation, and checks for `design-principles.md` first, running `/aligned:create-design-principles` when none exists.
- Phase 10 writes the screens link into the map and republishes.
- No file in the framework names "The Designer".
- Template: JSON has `frame.why`, `roles`, `slices[].measure`, `activities[].tasks[].details`, `breadboard`, `screens`; tabs are Map and Breadboard; no `wireframes`.
- Worked example: built from the template (only JSON differs); one timeline (no `lanes`); Slice 1 reaches every activity or that activity has a workaround card in Slice 1; every Slice 1 task that isn't a workaround has an affordance on the breadboard; every affordance's card is a Slice 1 task or detail; every `to` is a place on the breadboard or empty; every JSON string appears in the Markdown; rendered with node: the backbone, the task row, details, and the breadboard places all draw, and the tabs are visible.

## Settled after the builder check

These came back from a builder review of the first draft. Items marked "my call" are Claude's, for Eric to check.

1. **Workaround cards need no breadboard affordance (my call).** A workaround is done outside the app, so it has nothing to tap. The Phase 8 rule reads: every Slice 1 task that isn't a workaround has at least one affordance. The test skips workaround cards.
2. **Phase 10: link the screens back (my call).** After `breadboard-to-pages` finishes and returns, the story map runs one short closing phase. It writes the screens page link into `screens`, rebuilds and republishes the map, and names both links. No WAIT; nothing for the user to decide.
3. **The `screens` link is the artifact URL when the screens page was published as an artifact, otherwise the relative path to `{slug}-screens.html` (my call).** The template renders whichever is there as a plain link.
4. **No design principles before Phase 9.** Settled in conversation with Eric: exact screens need real tokens. Before the hand-off, the story map checks for `design-principles.md` the same way Phase 1 did. If none exists, it runs `/aligned:create-design-principles` in the same conversation, then hands off. The map itself still draws with the template's tokens in Phases 1–8.
5. **One new eval scenario for Phases 8–10 (my call).** It starts from a locked map and scores the Singer hand-off, the affordance-to-card rule, the design-principles check, and the Phase 9 invocation. Its `e2e/trigger-map.yaml` entry lands after the other thread commits that file. Evals run only for `user-story-map`, `user-story-map-picture`, the new scenario, and `jeff-patton-consult`.
6. **Baseline.** The uncommitted story map work in this checkout (the worked example, `story-map-template.md`, the equal-height fix, and 12 tests) is this session's own. It is the starting point for this change, and it has to be committed on `main` before the worktree branches from it.

## Left to the builder

- Exact card sizes, gap widths, and chip styling, within the template's tokens.
- How the breadboard tab draws connections (text arrows under each affordance is acceptable; an SVG is a plus if it stays legible in both themes).
- Wording of examples, as long as it follows the voice rules already in `prompt.md` and quotes only verified sources.
