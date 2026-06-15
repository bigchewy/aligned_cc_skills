# Visualization Runner

Shared engine for producing the on-brand, tabbed, Mermaid-validated HTML artifact. Invoked by `skills/brainstorming/references/visualization-protocol.md` (brainstorming lifecycle wrapper) and `skills/visualize-design/SKILL.md` (standalone caller). The caller owns *when* to render and *where* the final artifact lands; this runner owns *how* a single artifact is produced.

## Configuration

The calling skill passes these inputs (all absolute paths — the runner never self-resolves):

| Input | Meaning |
|---|---|
| `{template-path}` | The HTML template to copy verbatim |
| `{widgets-path}` | `widgets.html` (widget CSS/JS/HTML blocks) |
| `{components-path}` | `brainstorm-components.md` (token contract + component classes) |
| `{source-content}` | Validated sections or document body to render |
| `{title}` / `{subtitle}` / `{context}` | Header values patched into the template |
| `{output-path}` | Final committed artifact location |
| `{live-session}` | `yes`/`no` — self-refreshing `/tmp` artifact vs one-shot |
| `{project-root}` | For the token-resolution ladder |
| `{validate-mermaid-script}` | Absolute path to `validate-mermaid.mjs` |

## Configuration Validation (fail-closed)

Before Step 1, validate inputs. **STOP** with a named error if any check fails — do not improvise:
- Every path input (`{template-path}`, `{widgets-path}`, `{components-path}`, `{validate-mermaid-script}`) must exist.
- `{output-path}`'s parent directory must be writable (create it if missing).
- `{live-session}` must be exactly `yes` or `no`.
- A missing or unresolvable input halts the runner: "Visualization runner cannot proceed: `<input>` is missing/unresolvable."

## Step 1: Read the brand-token contract

Read `{components-path}` for the `:root` token rules and the component-class reference. Pay attention to the "Brand Token Injection" section — it specifies how to populate the template's `:root` block.

## Step 2: Resolve the project's design tokens

Resolve design tokens so the artifact matches the project's brand, not the aligned plugin's. Find the right design-principles file using this lookup order (use `{project-root}` as resolved by the caller):

a. **Project root:** `{project-root}/docs/design/design-principles.md`
b. **Monorepo apps:** if (a) is missing, Glob `{project-root}/apps/*/docs/design/design-principles.md`. Same for `{project-root}/packages/*/docs/design/design-principles.md`.
   - Exactly one match: use it.
   - Multiple matches: ask the user which app/package this brainstorm targets, then use that one.
   - Zero matches: continue to (c).
c. **Global fallback:** `~/.claude/docs/design/design-principles.md`.

**Placeholder check.** If the file found in (a), (b), or (c) is a kickstart-generated placeholder — heuristic: under 500 bytes, OR contains "This file is a placeholder", OR contains "Run `/aligned:create-design-principles`" — treat it as missing, advance to the next lookup step, and surface this warning to the user: *"Your project's `docs/design/design-principles.md` is still a placeholder. The brainstorm visualization will use the aligned plugin's default tokens. Run `/aligned:create-design-principles` to define the project's brand."*

If no usable file is found at any step, skip token extraction — the template's built-in defaults will apply.

Once a usable file is found, extract values per the "Brand Token Injection" / "Resolving project tokens" rules in `{components-path}`. If those rules' halt-and-ask trigger fires (genuine token-name ambiguity, unmappable brand-specific tokens), present the proposed mapping to the user before continuing.

## Step 3: Copy and patch the template

Read `{template-path}` and Write its contents verbatim to the working artifact location. Then patch:
- Replace `{title}`, `{subtitle}`, and `{context}` with session-specific values.
- Populate the `:root` block at the top of the inline `<style>` with the project tokens you read in Step 2 (or leave the built-in defaults if no design-principles file was found).
- Do not change any `var(--color-*)` or `var(--font-*)` references elsewhere in the template — they resolve through `:root`.
- Append `{source-content}`.

Do not rewrite the template from memory — the file copy is the contract.

The template carries a `COMPONENT CONTRACT` HTML comment at the top of `<body>` (content→component map, panel shape, class-inventory grep). Leave it in place — it must survive copy, patch, and the live-refresh strip into the committed snapshot, so the rules travel with the artifact into later editing sessions. Do not delete or summarize it.

**Anti-shortcut contract.** Copy `{template-path}` with a file-copy/Write command and patch it. NEVER hand-write or "compactly rewrite" the artifact HTML from memory, even when that seems faster. The compact-direct-write shortcut is the root cause of KB-085/086 — it bypasses the template, the widgets, the browser-open step, and the Overview gate.

## Step 4: Open the artifact in the browser (unconditional — do not skip)

This step is mandatory and runs every render. Open the artifact with a platform-aware command (separate Bash call, no `&&` chaining):

`open {output-path} || xdg-open {output-path}`

Only a headless environment (both commands fail) exempts this step — log the warning and continue. There is no other condition under which the browser-open is skipped.

## Step 5: Inject interactive widgets (conditional)

Only if the content has a Decision Log (>=1 entry) or Open Questions list (>=1 entry):

Read `{widgets-path}` and perform three injections:

a. **WIDGETS-CSS block** — insert once into `<head>` after the inline `<style>` block. Copy verbatim between (and including) `<!-- WIDGETS-CSS-START -->` and `<!-- WIDGETS-CSS-END -->`.

b. **WIDGETS-SCRIPT block** — insert once immediately before `</body>`. Copy verbatim between (and including) `<!-- WIDGETS-SCRIPT-START -->` and `<!-- WIDGETS-SCRIPT-END -->`. **The block MUST land outside the `<!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END -->` delimiters** so the strip-script rule preserves widget JS in committed snapshots.

c. **WIDGET-HTML blocks** — for the Decision Log section, copy `WIDGET-HTML: decision-log-flat` (if <10 entries) or `WIDGET-HTML: decision-log-categorized` (if >=10 entries) into the Decision Log `<section>`, then append the `WIDGET-HTML: prompt-box` block with `{widget-id}` substituted to `decisions`. For the Open Questions section, mirror the same with `open-questions-*` and `{widget-id}` = `questions`. Every triage entry must carry `data-id="N"` and `data-title="..."` (decisions are `<div class="decision-card">`; questions are `<tr>`); section headers carry no `data-id`.

Do not rewrite the widget code from memory — the file copy is the contract.

## Step 6: Validate Mermaid (hard gate)

Run `node {validate-mermaid-script} {output-path}`. Exit 0 means all Mermaid blocks parse and the runner may continue. Exit 1 prints the offending block index, the source Mermaid receives, and the parser's caret-pointer error — fix the source, re-run the relevant steps, and re-run this gate. Do not proceed past Step 6 until exit is 0.

## Executive-overview gate (before any snapshot is written)

The Overview tab is the first thing a non-engineer sees. Two checks gate it.

**Mechanical sub-check (assertable, fail-closed):** the `panel-overview` panel must contain zero `<pre class="mermaid">` / `<pre class="mermaid-deferred">` blocks and zero `.file-path` spans. This is a grep with the same pass/fail contract as the mermaid gate: nonzero match → rewrite the Overview before any snapshot is written.

**Semantic self-check (not unit-testable, never blocks):** is the goal stated in the first two sentences? Is the language plain (no implementation vocabulary)? Does it fit one screen? This is an LLM judgment with no mechanical assertion — it does NOT have parity with the mermaid exit-code gate. On failure, rewrite the Overview and re-check once. **On a second failure, write the artifact anyway** and tell the user in one line which check failed and where the lever is (e.g., "Overview still leads with implementation detail — committed as-is; edit the Overview tab's `{goal}` slot to fix"). A soft semantic judgment never holds the user's output hostage; only the mechanical checks block.

## Structural Self-Check gate (before any snapshot is written)

Two **blind** checks — run them against the file's text without looking at the rendered page. Same fail-closed contract as the Mermaid and Overview-mechanical gates: a positive finding blocks the snapshot until the source is fixed. The reference for both is the "Content-Type → Component Mapping" and "Sibling-Parity Rule" sections in `{components-path}`.

**a. Class inventory (assertable, fail-closed).** Run:

`grep -oE 'class="[a-z][a-z-]+' {output-path} | sort | uniq -c`

This grep emits only the **first** class token of each element (it stops at the first space), so an element's content class must come first — the documented components already follow that convention. The recognized content tokens are `card`, `card-grid`, `bullet-list`, `description`, and `callout` (callouts surface as the base `callout` token; the `callout-*` modifier is styling and never appears in this output). Read every content token in the output (ignore layout/widget plumbing — `tab-*`, `sub-*`, `phase-*`, `diagram-container`, `interactive-section`, `dropdown`, `decision-card*`, `q-*`). Any content token **not** named in the Content-Type → Component Mapping is drift — a class the artifact invented or a content type rendered the wrong way. Additionally, if the inventory shows the same content type carried by two different components (e.g., both `card` and a `<table>` describing named-item-plus-explanation content), that is a binding-rule violation. Fix the source and re-run before proceeding.

**b. Panel-shape audit (assertable, fail-closed).** For each group of sibling panels/sub-panels that present the same kind of content, list the `<h2>` section headings (each `.section > h2`) present in each sibling. Assert every sibling carries the same label set in the same order. A label present in one sibling but missing from another fails the gate — add the section, or add an explicit N/A note in that panel, before proceeding. This is the mechanical enforcement of the Sibling-Parity Rule.

Neither check requires opening the browser; both read the committed HTML text directly. Do not write the snapshot until both pass.

## Stripping the live-refresh script

Before committing the snapshot, verify that both `<!-- LIVE-REFRESH-START -->` and `<!-- LIVE-REFRESH-END -->` delimiters exist in the file. If either delimiter is missing, STOP and flag the issue — a committed artifact with an active refresh script is a silent bug. If both are present, remove the block (inclusive of delimiters). The final committed artifact must not auto-refresh.

**Widget survival.** After stripping, any widget tables (`decisions-table`, `questions-table`) and their `WIDGETS-SCRIPT` block MUST still be present and bind on load. Widget code lives in a separate `<script>` block delimited by `<!-- WIDGETS-SCRIPT-START -->` / `<!-- WIDGETS-SCRIPT-END -->`, outside the LIVE-REFRESH delimiters. If a committed snapshot is missing the widget script after a strip, the widget block was injected inside the LIVE-REFRESH delimiters by mistake — re-run Step 5 and verify the block lands before `</body>` and AFTER `<!-- LIVE-REFRESH-END -->`.

## Nested sub-tabs

When a tabbed HTML document is generated (live visualization or any auxiliary mockup), use nested sub-tabs (progressive disclosure) whenever a single tab contains more detail than can be scanned in one view. Do not flatten into many top-level tabs or cram everything into one scrollable panel. The pattern is:

- **Top-level tabs** for major conceptual sections.
- **Sub-tabs within each** for natural subdivisions (phases, layers, concerns).
- Each sub-tab holds **one focused diagram or content block**.

The check: if a tab contains multiple diagrams, subgraphs, or sections that each deserve their own view, break them into nested sub-tabs rather than stacking vertically.

## Editing an existing artifact

The steps above describe generating an artifact. A second, distinct mode is **hand-editing a committed `docs/mockups/*.html`** — adding a panel, extending a section, revising content in place — without regenerating from the template. This is where rendering drift historically crept in (the same content type rendered three different ways across edit turns, siblings diverging). When you modify a committed artifact rather than regenerate it:

a. **Re-read the contract before the first edit of the session.** Read this file's "Structural Self-Check gate" and the "Content-Type → Component Mapping" + "Sibling-Parity Rule" in `{components-path}` (or read the COMPONENT CONTRACT comment at the top of the artifact's `<body>`, which restates them). Do this once, before the first edit — not after.

b. **Match new content to an existing component.** Before adding anything, find how that content type is already rendered in this file and reuse the exact same component. Never introduce a second rendering of a content type the file already contains. If the new content is a new content type, resolve it through the mapping table — never invent a class.

c. **Re-run the Structural Self-Check gate after editing, before declaring done.** Both checks (class inventory + panel-shape audit) must pass on the edited file, exactly as they would for a fresh generation. An edit session is not complete until they do.

## Avoid These Mistakes

- **The compact-direct-write shortcut** — hand-writing tighter HTML directly instead of copying the template. Forbidden: it skips every gate below. Always copy the file.
- **Rewriting the template or widgets from memory** — always copy the file and patch it.
- **Skipping the browser-open or mermaid gate** — both are unconditional numbered steps.
- **Injecting the widget script inside the LIVE-REFRESH delimiters** — it must land outside them or the strip rule removes it.
- **Rendering one content type two different ways** — a "named item + its explanation" pair must be a `.card` everywhere it appears, never also a table or a bulleted-card. Resolve every content type through the Content-Type → Component Mapping and reuse the file's existing component. The Structural Self-Check gate catches this.
- **Letting sibling panels diverge** — sub-panels of the same content kind must share the same section sequence. A section in one sibling but not another is drift; the panel-shape audit blocks it.
- **Editing a committed artifact without re-reading the contract** — hand-edits to `docs/mockups/*.html` follow the "Editing an existing artifact" section, including re-running the Structural Self-Check before done.
