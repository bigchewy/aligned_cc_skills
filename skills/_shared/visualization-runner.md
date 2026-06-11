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

**Anti-shortcut contract.** Copy `{template-path}` with a file-copy/Write command and patch it. NEVER hand-write or "compactly rewrite" the artifact HTML from memory, even when that seems faster. The compact-direct-write shortcut is the root cause of KB-085/086 — it bypasses the template, the widgets, the browser-open step, and the Overview gate.

## Step 4: Open the artifact in the browser

Open the artifact using a platform-aware pattern (separate Bash call — no `&&` chaining):

`open {output-path} || xdg-open {output-path}`

If both commands fail (headless environment), log a warning and continue — the artifact still gets written.

## Step 5: Inject interactive widgets (conditional)

Only if the content has a Decision Log (>=1 entry) or Open Questions list (>=1 entry):

Read `{widgets-path}` and perform three injections:

a. **WIDGETS-CSS block** — insert once into `<head>` after the inline `<style>` block. Copy verbatim between (and including) `<!-- WIDGETS-CSS-START -->` and `<!-- WIDGETS-CSS-END -->`.

b. **WIDGETS-SCRIPT block** — insert once immediately before `</body>`. Copy verbatim between (and including) `<!-- WIDGETS-SCRIPT-START -->` and `<!-- WIDGETS-SCRIPT-END -->`. **The block MUST land outside the `<!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END -->` delimiters** so the strip-script rule preserves widget JS in committed snapshots.

c. **WIDGET-HTML blocks** — for the Decision Log section, copy `WIDGET-HTML: decision-log-flat` (if <10 entries) or `WIDGET-HTML: decision-log-categorized` (if >=10 entries) into the Decision Log `<section>`, then append the `WIDGET-HTML: prompt-box` block with `{widget-id}` substituted to `decisions`. For the Open Questions section, mirror the same with `open-questions-*` and `{widget-id}` = `questions`. Every triage entry must carry `data-id="N"` and `data-title="..."` (decisions are `<div class="decision-card">`; questions are `<tr>`); section headers carry no `data-id`.

Do not rewrite the widget code from memory — the file copy is the contract.

## Step 6: Validate Mermaid (hard gate)

Run `node {validate-mermaid-script} {output-path}`. Exit 0 means all Mermaid blocks parse and the runner may continue. Exit 1 prints the offending block index, the source Mermaid receives, and the parser's caret-pointer error — fix the source, re-run the relevant steps, and re-run this gate. Do not proceed past Step 6 until exit is 0.

## Stripping the live-refresh script

Before committing the snapshot, verify that both `<!-- LIVE-REFRESH-START -->` and `<!-- LIVE-REFRESH-END -->` delimiters exist in the file. If either delimiter is missing, STOP and flag the issue — a committed artifact with an active refresh script is a silent bug. If both are present, remove the block (inclusive of delimiters). The final committed artifact must not auto-refresh.

**Widget survival.** After stripping, any widget tables (`decisions-table`, `questions-table`) and their `WIDGETS-SCRIPT` block MUST still be present and bind on load. Widget code lives in a separate `<script>` block delimited by `<!-- WIDGETS-SCRIPT-START -->` / `<!-- WIDGETS-SCRIPT-END -->`, outside the LIVE-REFRESH delimiters. If a committed snapshot is missing the widget script after a strip, the widget block was injected inside the LIVE-REFRESH delimiters by mistake — re-run Step 5 and verify the block lands before `</body>` and AFTER `<!-- LIVE-REFRESH-END -->`.

## Nested sub-tabs

When a tabbed HTML document is generated (live visualization or any auxiliary mockup), use nested sub-tabs (progressive disclosure) whenever a single tab contains more detail than can be scanned in one view. Do not flatten into many top-level tabs or cram everything into one scrollable panel. The pattern is:

- **Top-level tabs** for major conceptual sections.
- **Sub-tabs within each** for natural subdivisions (phases, layers, concerns).
- Each sub-tab holds **one focused diagram or content block**.

The check: if a tab contains multiple diagrams, subgraphs, or sections that each deserve their own view, break them into nested sub-tabs rather than stacking vertically.

## Avoid These Mistakes

- **The compact-direct-write shortcut** — hand-writing tighter HTML directly instead of copying the template. Forbidden: it skips every gate below. Always copy the file.
- **Rewriting the template or widgets from memory** — always copy the file and patch it.
- **Skipping the browser-open or mermaid gate** — both are unconditional numbered steps.
- **Injecting the widget script inside the LIVE-REFRESH delimiters** — it must land outside them or the strip rule removes it.
