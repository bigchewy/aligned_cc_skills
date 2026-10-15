<!--
Source for docs/story-maps/{slug}-screens.html. Edit this file, then rebuild the HTML from it.
Each section maps to one part of screens-template.html:
  Sources            -> the header's meta line
  Parts              -> the Parts tab table
  Templates          -> the Templates tab, one grey-box column per place
  Pages              -> the Pages tab, one <section class="page"> per place, phone and desktop frames
  Variations         -> the Variations switch above each page, one <div class="variation"> per case
  Walk               -> the Walk tab table
  Values to add      -> the Parts tab, under the table
  Open questions     -> the Walk tab, under the table
Every element on a page names its breadboard item as "{Place} › {affordance}". That text becomes data-from.
-->

# {Product}: Slice 1 screens

## Sources

- Design principles: {path to design-principles.md}
- Breadboard: {path, or "given in conversation"}
- Story map: {docs/story-maps/{slug}.md, or "none"}

## Parts

| Part | Kind | Draws (breadboard items) | Component, recipe, or snowflake | Tokens used |
|---|---|---|---|---|
| {Button, primary} | atom | {Team Settings › Invite} | component | {--accent, --space-3, --radius-md} |

## Templates

### {Place}

| # | Part | Longest content | Type role | Text color |
|---|---|---|---|---|
| 1 | {Heading} | {"Thursday Morning Accountability Crew", 36 characters} | {headline} | {--text} |

## Pages

### {Place}

- Phone (390px): {what sits where, top to bottom}
- Desktop (1280px): {what moves beside what, and why}

| Element | Content | From |
|---|---|---|
| {Heading} | {Thursday Morning Accountability Crew} | {Team Settings › team name} |

## Variations

### {Place}

- **Empty:** {what shows}
- **One:** {what shows}
- **Many:** {what shows}
- **Long text:** {which value, and what happens}
- **Error:** {what failed, and the way out}
- **Loading:** {only when the place waits}
- **{Other role}:** {what is different}

## Values to add to the design principles

- {value, where it was needed, closest existing token}

## Walk

| Slice 1 step | Page | Element (from) | Leads to |
|---|---|---|---|
| {Invite a teammate} | {Team Settings} | {Team Settings › Invite} | {Invite sent} |

## Open questions

- {question someone can answer}
