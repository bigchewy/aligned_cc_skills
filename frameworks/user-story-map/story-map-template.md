<!--
  User Story Map — Markdown source template (frameworks/user-story-map).
  Copy this to docs/story-maps/{slug}.md when the frame locks in Phase 1, and fill it in phase by phase.
  This file is the source. story-map-template.html is the picture, rebuilt from it after every phase.
  A finished example of both: example/team-course.md and example/team-course.html.

  How each section becomes the JSON inside <script id="map-data"> in the HTML:

  | Markdown                              | JSON                                                        |
  |---------------------------------------|-------------------------------------------------------------|
  | # title, and the line under it        | "title", "subtitle"                                         |
  | ## Frame                              | "frame": { "user", "outcome", "problem" }                   |
  | ## Slices, one row per slice          | "slices": [{ "id", "name", "outcome" }]. Measure stays here |
  | ## Lane: {role}                       | one entry in "lanes", with "role"                           |
  | ### {activity}                        | one entry in that lane's "activities", with "name"          |
  | Touches: line under the activity      | "touches": ["Member: Do the week's lesson"]                 |
  | Step table row                        | { "text", "slice" } — Slice "Later" becomes "slice": null   |
  | Gap column says yes                   | "gap": true                                                 |
  | Note column                           | "note"                                                      |
  | ## Open questions                     | "questions"                                                 |
  | ## Slice 1 wireframes, ### lane: activity | one entry in "wireframes", with "lane" and "activity"   |
  | Wireframe table row                   | { "kind", "text" or "rows", "card" }                        |

  Wireframe kinds: heading, text, list, button, link, field. For a list, separate the rows with " / "
  in the Text column; they become "rows". The Card column must be a Slice 1 step or an activity name
  in the same lane, word for word.

  Leave a section empty until its phase: Lanes after Phase 2, Slices after Phase 6, wireframes after
  Phase 8. Empty sections become empty arrays, and the page draws what exists. Delete this comment
  in the copy.
-->

# {Story map title}

{One line naming the product or feature}

## Frame

- **User:** {the one person whose story comes first}
- **Outcome:** {what's different for them when this works}
- **Problem:** {what goes wrong for them today, and what the business gets if it's fixed}

## Slices

| Slice | Name | Outcome | Measure |
|---|---|---|---|
| 1 | {Slice 1: short name} | {what the user can do after this slice} | {what you'd measure to know it worked} |
| 2 | {Slice 2: short name} | {outcome} | {measure} |

## Lane: {Primary role}

### {Activity, a verb phrase the user would say}

Touches: {Other role: the activity where their stories meet}

| Step | Slice | Gap | Note |
|---|---|---|---|
| {Step the user always does} | 1 | | |
| {Step that matters less} | Later | | |
| {Step found on the walk} | 1 | yes | Found on the walk |

### {Next activity}

| Step | Slice | Gap | Note |
|---|---|---|---|
| {Step} | 1 | | |

## Lane: {Other role}

### {Activity}

Touches: {Primary role: the activity where their stories meet}

| Step | Slice | Gap | Note |
|---|---|---|---|
| {Step} | 1 | | |

## Open questions

1. {A gap from the walk that wasn't filled, written as a question someone can answer}

## Slice 1 wireframes

### {Primary role}: {Activity}

| Kind | Text | Card |
|---|---|---|
| heading | {Words from the card} | {Activity or Slice 1 step} |
| list | {One row} / {Another row} | {Slice 1 step} |
| button | {Main action} | {Slice 1 step} |
