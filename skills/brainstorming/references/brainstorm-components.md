# Brainstorm Live Visualization — Component Reference

> **For the agent:** Read this file once at the start of the visualization phase. The active mode's HTML template lives in `templates/{mode}-template.html` — open it directly to copy. This file documents the brand-token contract you must apply to the copied template, and the component classes you can use to populate it. Do not invent custom classes — use only what's documented here.

## Contents

- Content-Type → Component Mapping
- Sibling-Parity Rule
- Brand Token Injection
- Templates
- Components

## Content-Type → Component Mapping

The "Components" section below is a *menu of classes that exist*. This table is the *binding* — which component a given kind of content MUST use. The menu tells you what is legal; this table tells you what is correct.

**Binding rule:** one content type resolves to **exactly one** component. And if that content type **already appears in the file**, reuse the same component the file already uses — never render one content type two different ways across panels, tabs, or edit sessions.

| Content type | Use exactly this | Never |
|---|---|---|
| **Named item + its explanation** — a "here is a thing and what it does" pair: capabilities, wiring paths, failure modes, source/producer/critics, options, components, etc. | A surface card: `<div class="card">` holding a bold title (`<h3>`) + body (`<p>`), stacked inside a `<div class="card-grid">`. **ONE component for all of these.** | Never an HTML `<table>`. Never a card whose body is a `<ul>`/bulleted list. Never override the card font — `<h3>`/`<p>` inherit `--font-sans` from the template; leave them. |
| **Ordered contents / outline of a deliverable** | `<ol class="bullet-list">` | A card grid; a table |
| **Decision / constraint / risk / note** | a `callout` box carrying a `callout-*` modifier (`callout callout-decision`, `callout callout-constraint`, `callout callout-risk`, `callout callout-note`) — `callout` is the content class; the variant is styling | A plain card; a callout used for non-decision content |
| **Section header** | an `<h2>` inside the section's `<div class="section">` wrapper (styled by `.section h2`), present on **every** section | Skipping it on some sections but not siblings; inventing an uppercase/label class — the template has none |
| **Panel intro** | exactly one `<p class="description">` directly under the panel's `<h2>` | More than one intro paragraph; an intro rendered as a card or callout |

> **Font note (divergence from a "serif" instruction).** This template is entirely sans-serif — `.card h3` is `font-weight: 600` sans and `.card p` is sans body, both resolving through `--font-sans` (see `templates/software-template.html`, `.card h3`/`.card p`). There is no `--font-serif` token. The "named item + explanation" content type is pinned to the `.card` component precisely so every instance shares that one built-in font. Do not introduce a serif face or any per-card font override — using the single `.card` component IS the font-consistency guarantee.

This rule **composes with** the "do not invent classes" rule at the top of this file. Together: use only documented classes, **and** do not render one content type two different ways.

## Sibling-Parity Rule

Tabs and sub-panels that present the **same kind of content** must share the **same section sequence**. A section that appears in one sibling must appear in **all** of them, in the same order, unless it is explicitly marked N/A for that sibling (state the N/A in the panel, don't silently omit it).

Concretely: if the "Source" sub-panel has section labels *Overview → Wiring → Failure Modes*, then the "Producer" and "Critics" sub-panels — siblings presenting the same kind of content — must carry the same three labels. A sibling missing a section its peers have is drift; add the section (or an explicit N/A note) before declaring the artifact done. This rule is enforced by the panel-shape audit in `skills/_shared/visualization-runner.md` (Structural Self-Check gate).

## Brand Token Injection

The template's color and font values are defined as CSS variables in a `:root` block at the top of the inline `<style>`. Every other reference in the template — Tailwind config, inline CSS rules, Mermaid theme — reads from those variables. Rebrand the artifact by editing only the `:root` block.

### Token contract

The template uses these CSS-variable names. Default values match the aligned plugin's own brand and apply when no project tokens are found.

| Token (in :root)         | Purpose                                                |
|--------------------------|--------------------------------------------------------|
| `--color-background`     | Page/diagram background                                |
| `--color-surface`        | Container regions, card backgrounds                    |
| `--color-muted`          | Inset areas, subtle fills                              |
| `--color-foreground`     | Primary text, headings                                 |
| `--color-secondary`      | Supporting text, captions                              |
| `--color-dimmed`         | Tertiary info (timestamps, axis labels)                |
| `--color-border`         | Dividers, card borders                                 |
| `--color-accent`         | Signature accent (CTAs, highlights, decisions)         |
| `--color-accent-hover`   | Accent hover state                                     |
| `--color-accent-subtle`  | Accent background tint (badges, decision callouts)     |
| `--font-sans`            | Body and UI text                                       |
| `--font-mono`            | Code, file paths                                       |

### Resolving project tokens

Project design-principles files don't always use the exact `--color-*` naming above. Use this resolution order:

1. **Direct match.** If the source file defines `--color-accent`, `--color-foreground`, etc. with the contract names verbatim, use them.
2. **Alias match.** Otherwise, apply this alias table. Project token names appear in many shapes — the table treats `kebab-case`, `camelCase`, and `snake_case` as equivalent (compare case-insensitively after stripping separators).

   | Project token name(s)                                              | Contract token            |
   |--------------------------------------------------------------------|---------------------------|
   | `accent`                                                           | `--color-accent`          |
   | `accent-hover`, `primary-hover`                                    | `--color-accent-hover`    |
   | `accent-subtle`, `accent-bg`, `primary-subtle`                     | `--color-accent-subtle`   |
   | `background`, `bg`, `page`                                         | `--color-background`      |
   | `surface`, `card`, `panel`                                         | `--color-surface`         |
   | `muted`, `inset`                                                   | `--color-muted`           |
   | `foreground`, `text`, `fg`                                         | `--color-foreground`      |
   | `secondary`, `text-secondary`                                      | `--color-secondary`       |
   | `dimmed`, `text-muted`, `muted-foreground`                         | `--color-dimmed`          |
   | `border`                                                           | `--color-border`          |
   | `sans`, `body`, `font-sans`                                        | `--font-sans`             |
   | `mono`, `code`, `font-mono`                                        | `--font-mono`             |

3. **Missing tokens.** If the source provides only some contract tokens (common: it has `accent` but no `accent-hover` or `accent-subtle`), leave the missing ones at the template defaults. **Do not derive colors by darkening/lightening** — agents are unreliable at color math, and the visible brand is dominated by the main accent and background.

### Placeholder files

Some projects have a `docs/design/design-principles.md` that's a kickstart-generated 4-line placeholder. Heuristic: the file is under 500 bytes, OR contains the literal string "This file is a placeholder", OR contains "Run `/aligned:create-design-principles`". Treat placeholders as if no file exists — fall back to the next lookup location and surface this warning to the user before writing the artifact:

> Your project's `docs/design/design-principles.md` is still a placeholder. The brainstorm visualization will use the aligned plugin's default tokens. Run `/aligned:create-design-principles` to define the project's brand.

### Writing :root

Once tokens are resolved, populate the `:root` block in the inline `<style>` with the values. Leave every other `var(--color-*)` / `var(--font-*)` reference throughout the template untouched — they resolve through `:root` automatically.

### Semantic colors

`#b91c1c` (error), `#047857` (success), `#0284c7` (info), and the `#fef2f2`/`#ecfdf5`/`#f0f9ff` callout fills are intentionally hardcoded. They convey meaning that should be consistent across all brands and are not part of the contract.

## Templates

The visualizing mode owns its own HTML template file.

| Mode      | Template path                                                   |
| --------- | --------------------------------------------------------------- |
| Authoring | `{base-directory}/references/templates/authoring-template.html` |

Research and Roadmap modes do not generate a live HTML artifact and have no template. (The `roadmap-template.html` and `software-template.html` files remain on disk for backward compatibility — `software-template.html` is still consumed by the standalone visualize-design skill — but neither is wired into a brainstorming mode.)

### Copy-and-patch contract

The model's job during visualization is **file copy plus targeted patch**, not regeneration. Specifically:

1. Read the active mode's template file with the Read tool.
2. Write its contents verbatim to the live HTML path (`/tmp/brainstorm-{topic}-{timestamp}/live.html`).
3. Replace `{title}`, `{subtitle}`, and `{context}` with session-specific values.
4. Populate the `:root` block at the top of the inline `<style>` with the resolved project tokens per "Brand Token Injection" above. Leave every `var(--color-*)` and `var(--font-*)` reference outside `:root` untouched — they resolve through `:root` automatically.
5. Append section content using the component classes documented below.

Do not regenerate the HTML by writing it from memory. The file copy is the contract — it eliminates the drift mode where the model recreates the template subtly differently each session. When a post-critique regeneration is needed, re-copy the template fresh and re-patch.

The `<!-- LIVE-REFRESH-START -->` / `<!-- LIVE-REFRESH-END -->` block stays in place during the live phase. The shared-rules.md "Stripping the live-refresh script" instruction tells you when to remove it for the committed snapshot.

## Components

### Phase Tracker

Shows the current brainstorm phase. Use at the top of the visualization to orient the user.

**Workflow step:** All phases — updates as the session progresses.

```html
<div class="phase-tracker">
  <div class="phase-item phase-current">Problem Space</div>
  <div class="phase-item">Root Causes</div>
  <div class="phase-item">Solutions</div>
  <div class="phase-item">Architecture</div>
</div>
```

**Notes:** Add `phase-current` to the active phase. Only one phase should be current at a time. Previous phases lose the class as the session advances.

---

### Card Grid

Displays a grid of items — problems, root causes, solutions, components, or modules. Cards auto-fill to fit available width.

**Workflow step:** Problem exploration, root-cause analysis, solution generation, architecture decomposition.

```html
<div class="card-grid">
  <div class="card">
    <h3>Card Title</h3>
    <p>Description of the item.</p>
  </div>
  <div class="card">
    <h3>Another Card</h3>
    <p>More detail here.</p>
  </div>
</div>
```

**Notes:** Cards expand to fill the row. For fewer than 3 items, cards will be wider. Content within cards is flexible — use `<ul>`, `<p>`, or other elements as needed.

---

### Comparison Grid

Side-by-side comparison of 2–3 approaches or trade-offs.

**Workflow step:** Solution evaluation, architecture trade-off analysis.

```html
<div class="compare-grid compare-2col">
  <div class="col">
    <h3>Option A</h3>
    <p class="pro">+ Fast to implement</p>
    <p class="con">- Limited scalability</p>
  </div>
  <div class="col">
    <h3>Option B</h3>
    <p class="pro">+ Scales well</p>
    <p class="con">- Complex setup</p>
  </div>
</div>
```

**Notes:** Use `compare-2col` for two options, `compare-3col` for three. Use `.pro` and `.con` classes for green/red coloring of trade-off items.

---

### Tabbed Navigation

Organizes content into switchable tabs. Already included in the template — use `switchTab()` and `switchSubTab()` for interaction.

**Workflow step:** Top-level organization (e.g., Overview / Details / Architecture) and sub-sections within tabs.

```html
<div class="tab-bar" id="main-tabs">
  <button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
  <button class="tab-btn" onclick="switchTab('details')">Details</button>
</div>

<div id="panel-overview" class="tab-panel active">
  <!-- Overview content -->
</div>

<div id="panel-details" class="tab-panel">
  <!-- Sub-tabs example -->
  <div class="sub-tab-bar">
    <button class="sub-tab-btn active" onclick="switchSubTab('details','problems')">Problems</button>
    <button class="sub-tab-btn" onclick="switchSubTab('details','causes')">Root Causes</button>
  </div>
  <div id="sub-problems" class="sub-panel active"><!-- content --></div>
  <div id="sub-causes" class="sub-panel"><!-- content --></div>
</div>
```

**Notes:** Panel IDs must be `panel-{tabId}`. Sub-panel IDs must be `sub-{subId}`. The first tab and sub-tab should have `active` class by default.

---

### Callout Boxes

Highlight decisions, constraints, risks, or notes that need attention.

**Workflow step:** Any phase — use when surfacing key findings or decisions.

```html
<div class="callout callout-decision">
  <strong>Decision</strong>
  We will use a microservices architecture for the backend.
</div>

<div class="callout callout-constraint">
  <strong>Constraint</strong>
  Budget limited to $50k for initial implementation.
</div>

<div class="callout callout-risk">
  <strong>Risk</strong>
  Third-party API may have rate limits that affect throughput.
</div>

<div class="callout callout-note">
  <strong>Note</strong>
  This approach requires team training on the new framework.
</div>
```

**Notes:** Four variants: `callout-decision` (orange), `callout-constraint` (gray), `callout-risk` (red), `callout-note` (blue). The `<strong>` label is optional but recommended.

---

### Mermaid Containers

Wraps Mermaid diagrams for architecture diagrams, flows, and state machines. Use `mermaid-deferred` for diagrams in hidden tabs (rendered on first activation).

**Workflow step:** Architecture phase — system diagrams, data flows, state machines.

```html
<!-- Immediate render (visible on load) -->
<div class="diagram-container">
  <pre class="mermaid">
graph TD
  A[Client] --> B[API Gateway]
  B --> C[Service]
  </pre>
</div>

<!-- Deferred render (in a hidden tab) -->
<div class="diagram-container">
  <pre class="mermaid-deferred">
graph TD
  A[Start] --> B[End]
  </pre>
</div>
```

**Notes:** Use `mermaid` class for diagrams visible on initial load. Use `mermaid-deferred` for diagrams inside hidden tabs — they render automatically when the tab is first activated. The `.diagram-container` provides horizontal scroll for wide diagrams.

#### Label-safety rules

Mermaid reads `<pre>` content via `textContent` and lexes it with a grammar that reserves several characters. Violations render as a bomb icon + "Syntax error in text" in the browser; the validator (see below) catches them before commit.

- **Never embed unescaped `"` inside a node label.** Mermaid lexes `"…"` as a STR token, which the bracketed-label production rejects. If you need to quote a verbatim string inside a label, use single quotes (`'topic'`), smart quotes (`"topic"`), or wrap the whole label in quotes — `node["User invokes /cmd 'topic'"]`. Same rule for `()`/`[]`/`{}` inside their own kind of bracket.
- **Use HTML-encoded `&lt;br/&gt;` for line breaks inside `<pre class="mermaid">` blocks**, not literal `<br/>`. The browser HTML-parses `<br/>` into an element node whose `textContent` is empty, silently collapsing label line breaks (`Auto-route silently<br/>to detected mode` becomes `Auto-route silentlyto detected mode` by the time mermaid sees it).
- **Don't write diagrams from memory.** Test risky-looking labels against `scripts/validate-mermaid.mjs` rather than guessing what mermaid accepts.

| Broken | Fixed |
| --- | --- |
| `in([User invokes /cmd "topic"])` | `in([User invokes /cmd 'topic'])` |
| `route1[Auto-route silently<br/>to mode]` | `route1[Auto-route silently&lt;br/&gt;to mode]` |

#### Validation

Every committed snapshot must pass `node scripts/validate-mermaid.mjs <html>` (see the visualization protocol's pre-critique snapshot step). The validator extracts each block as mermaid will see it, parses with the same library version the templates load from CDN, and exits non-zero with the offending block index + caret-pointer error if any fail. First use in this checkout requires `npm install` inside `skills/brainstorming/scripts/`.

---

### Section Containers

General-purpose content wrapper with white background, border, and rounded corners. Already in the template CSS.

**Workflow step:** Any phase — use to group related content within a tab panel.

```html
<div class="section">
  <h2>Section Title</h2>
  <p class="description">Supporting description text.</p>
  <ul class="bullet-list">
    <li>First point</li>
    <li>Second point</li>
  </ul>
</div>
```

**Notes:** Sections stack vertically with 24px spacing. Use `.description` for secondary text and `.bullet-list` for lists within sections.

---

### Interactive Widgets

Triage UI for the design doc's Decision Log and Open Questions sections. Lets the user toggle Approve/Reject (decisions) or Defer/Include/Reject (questions); a textarea below auto-builds a prompt the user can copy back into the conversation.

**Workflow step:** Post-critique snapshot — wire onto the committed mockup at `docs/mockups/{session-name}.html` whenever the design produced a Decision Log (>=1 entry) OR an Open Questions list (>=1 entry).

**Source:** All widget markup, CSS, and JS lives in `{base-directory}/references/widgets.html`. The model copies the relevant blocks verbatim into the live HTML during visualization — never regenerated from memory.

#### When to use each block

| Entries  | Decision Log block               | Open Questions block             |
| -------- | -------------------------------- | -------------------------------- |
| 1–9      | `WIDGET-HTML: decision-log-flat` | `WIDGET-HTML: open-questions-flat` |
| 10+      | `WIDGET-HTML: decision-log-categorized` | `WIDGET-HTML: open-questions-categorized` |

The categorized variants add section headers grouping entries into themes (A, B, C ...). Below 10 entries, the flat layout is clearer.

**Two different DOM shapes.** Decision Log entries are `<div class="decision-card">` elements (one per decision) wrapped in `<div id="decisions-table" data-widget-root>`. Open Questions entries are still `<tr>` rows inside `<table id="questions-table">`. The shapes diverged when decisions gained click-to-expand detail; questions kept the compact table layout because the three-state defer/include/reject UI reads better as a grid.

#### Sidecar contract

The model performs three injections during visualization:

1. **WIDGETS-CSS** — one copy, inside `<head>` after the inline `<style>` block.
2. **WIDGETS-SCRIPT** — one copy, immediately before `</body>`. **MUST land outside the `<!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END -->` delimiters** — otherwise the strip-script rule destroys the widget JS in the committed snapshot.
3. **WIDGET-HTML blocks** — inside the owning `<section>` (Decision Log section gets a `decision-log-*` block; Open Questions section gets an `open-questions-*` block). Both wrap in `.interactive-section`. The reusable `WIDGET-HTML: prompt-box` block follows each table.

#### data-id contract (stable IDs)

Every triage entry — decision card OR question row — carries:
- `data-id="N"` — the decision/question number. Stable across reorderings; cross-references in prose (e.g., "see Decision #14") survive categorization.
- `data-title="..."` — the headline used in the generated prompt text.

Section headers (decisions: `<div class="decision-card-section">`; questions: `<tr class="section-divider">`) do **not** carry `data-id`. The widget JS selects `.decision-card[data-id]` for decisions and `tbody tr[data-id]` for questions, so headers are skipped automatically. Never use bare `tbody tr` or bare `.decision-card` — both will pick up headers.

#### Decision-card extended detail (optional)

A decision card may include a `<div class="decision-card-detail" hidden>` block after the description. When present, the card becomes clickable: clicking anywhere outside the dropdown toggles a `.expanded` class on the card and unhides the detail. Use this for 1–2 short paragraphs of rationale, tradeoff context, or links to specific files that would have overwhelmed the brief description. Omit the block entirely when there is nothing useful to add — the card stays non-interactive, no chevron renders.

#### Widget-root contract (live-refresh persistence)

The decision-card container `<div id="decisions-table" data-widget-root>` carries `data-widget-root` so the `saveState` IIFE can find it (cards aren't inside a `<table>`). The question table `<table id="questions-table">` is found via the `table` half of the same selector. Any future card-style widget MUST set `data-widget-root` on its container or its select state will be lost on the 15s live-refresh.

#### Selector contract (state-composition hook)

Every widget `<select>` MUST include `dropdown` in its `class` attribute (e.g., `class="dropdown"` for decisions, `class="dropdown q-dropdown"` for questions). The `saveState`/`restoreState` IIFE uses the selector `select.dropdown[data-id]` to detect widget state — a select that carries `data-id` but lacks the `dropdown` class token is invisible to the persistence layer and its value will be lost on reload. The `q-dropdown` class is a styling-only addition; `dropdown` is the contract.

#### `{widget-id}` substitution contract

The `WIDGET-HTML: prompt-box` block contains a `{widget-id}` placeholder. Valid values are exactly:
- `decisions` — for the Decision Log widget (produces IDs `decisions-prompt`, `copy-decisions`, `regenerate-decisions`).
- `questions` — for the Open Questions widget (produces IDs `questions-prompt`, `copy-questions`, `regenerate-questions`).

The widget JS hardcodes these IDs. A third triage type would substitute syntactically but never bind at runtime — adding a new widget requires editing both the sidecar JS and this contract.

#### State composition (live-refresh persistence)

The template's `saveState`/`restoreState` IIFE captures and restores widget state across the 15-second refresh. The author of the widget HTML doesn't need to wire anything extra — the IIFE auto-detects `select.dropdown[data-id]` and `textarea.prompt-textarea` instances and stores them under `state.widgets.selects` / `state.widgets.textareas`. After reload, dispatched `change` events re-trigger the widget IIFEs' row-class and prompt-textarea rebuild paths.

User edits to the prompt textarea are protected by a dirty flag (`data-dirty="true"`) — auto-refresh respects it so a hand-edited prompt is not clobbered on next dropdown change or next 15-second reload.

#### Empty-state behavior

If a widget's `<tbody>` has zero `tr[data-id]` rows, the prompt textarea renders the hint *"No {decisions|open questions} captured for this design. Either remove this section or add entries before triaging."* — not a false "all approved" message.

#### Clipboard fallback

Committed snapshots open at `file://` (not a secure context). The Copy button uses `navigator.clipboard.writeText` when available and falls back to `document.execCommand('copy')` via a temporary `<textarea>` otherwise. Failure surfaces in the button label as "Copy failed — select & Cmd-C" for 3 seconds, then reverts.
