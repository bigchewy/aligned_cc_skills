<!--
  User Story Map — Markdown source template (frameworks/user-story-map).
  Copy this to docs/story-maps/{slug}.md when the frame locks in Phase 1, and fill it in phase by phase.
  This file is the source. story-map-template.html is the picture, rebuilt from it after every phase.
  A finished example of both: example/team-course.md and example/team-course.html.

  How each section becomes the JSON inside <script id="map-data"> in the HTML:

  | Markdown                                  | JSON                                                              |
  |-------------------------------------------|-------------------------------------------------------------------|
  | # title, and the line under it            | "title", "subtitle"                                               |
  | ## Frame                                  | "frame": { "user", "outcome", "problem", "why" }                  |
  | ## Roles, one row per role                | "roles": [{ "name", "about" }]                                    |
  | ## Slices, one row per slice              | "slices": [{ "id", "name", "outcome", "measure" }]                |
  | ## Map, ### {activity}                    | one entry in "activities", with "name"                            |
  | Row with Tier = task                      | one entry in that activity's "tasks": { "text", "role", "slice" } |
  | Row with Tier = detail                    | one entry in the task above it, in "details": { "text", "kind", "slice" } |
  | Kind = workaround (tasks only)            | "workaround": true                                                |
  | Kind = detail, rule, alternative, exception | the detail's "kind"                                             |
  | Slice column                              | the slice number; "Later" becomes "slice": null                   |
  | Gap column says yes                       | "gap": true                                                       |
  | Note column                               | "note"                                                            |
  | ## Open questions                         | "questions"                                                       |
  | ## Slice 1 breadboard, ### {Place} ({Role}) | one entry in "breadboard", with "place" and "role"             |
  | Breadboard table row                      | one entry in "affordances": { "text", "to", "card" }              |
  | ## Screens, the one line under it         | "screens"                                                         |

  The Card column holds the words on the card. An activity's role chips come from the roles of its tasks,
  in task order. A breadboard row's Card column must be a Slice 1 task or detail, word for word. Leave
  Leads to empty when the affordance stays on the same place.

  Leave a section empty until its phase: Roles and Map after Phase 2, Slices after Phase 6, Breadboard
  after Phase 8, Screens after Phase 10. Empty sections become empty arrays or strings, and the page draws
  what exists. Delete this comment in the copy.
-->

# {Story map title}

{One line naming the product or feature}

## Frame

- **User:** {the one person whose story comes first}
- **Outcome:** {what's different for them when this works}
- **Problem:** {what goes wrong for them today, and what the business gets if it's fixed}
- **Why:** {why this is worth building now}

## Roles

| Role | Who they are |
|---|---|
| {Primary role} | {who they are, in one line} |
| {Other role} | {who they are, in one line} |

## Slices

| Slice | Name | Outcome | Measure |
|---|---|---|---|
| 1 | {Slice 1: short name} | {what the user can do after this slice} | {what you'd measure to know it worked} |
| 2 | {Slice 2: short name} | {outcome} | {measure} |

## Map

### {Activity, a verb phrase the user would say}

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| {Task the user always does} | task | step | {Primary role} | 1 | | |
| {A rule that applies to that task} | detail | rule | {Primary role} | 1 | | |
| {Task that matters less} | task | step | {Primary role} | Later | | |
| {Task found on the walk} | task | step | {Primary role} | 1 | yes | Found on the walk |

### {Next activity}

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| {Task done by hand today} | task | workaround | {Other role} | 1 | | |

## Open questions

1. {A gap from the walk that wasn't filled, written as a question someone can answer}

## Slice 1 breadboard

### {Place} ({Primary role})

| Affordance | Leads to | Card |
|---|---|---|
| {Thing the user can act on} | | {Slice 1 task} |
| {Another thing they can act on} | {Another place} | {Slice 1 task} |

## Screens

{Link to the screens, added in Phase 10}
