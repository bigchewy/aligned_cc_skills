<!-- Visualization protocol: Read into context by visualizing modes (software, business, authoring, roadmap) at the start of their Visualization step. Research mode does not generate a live HTML artifact and skips this protocol. Do not add YAML frontmatter. -->

# Visualization Protocol

This protocol governs the live HTML artifact produced during the visualization phase. It is invoked from each visualizing mode after the design document has been written and before the critique round. Each mode owns its own conditional trigger (whether visualization fires for this session) and its own template file; this protocol owns the procedure.

## Inputs

The invoking mode supplies these values:

- `{mode-template-path}` — absolute path to the mode's template, e.g. `{base-directory}/references/templates/software-template.html`. Each visualizing mode owns its own template; templates may diverge over time.
- `{topic}` — the brainstorm topic slug (kebab-case).
- `{timestamp}` — epoch seconds (or another collision-resistant value).
- `{session-name}` — derived as `YYYY-MM-DD-{topic}` using today's date and the topic slug, matching the design document base name (`docs/plans/YYYY-MM-DD-<topic>-design.md`). For example, a brainstorm on `mockup-deviations` on 2026-05-11 yields `{session-name}` = `2026-05-11-mockup-deviations` and a committed mockup at `docs/mockups/2026-05-11-mockup-deviations.html`. Modes that don't write a design document (e.g., Roadmap mode's portfolio/roadmap pair) must still derive this value from `YYYY-MM-DD-{topic}` for consistency.
- The validated design sections so far.

## Live phase

After the trigger fires, run these five steps before any critique work begins:

1. **Read the brand-token contract.** Read `{base-directory}/references/brainstorm-components.md` for the `:root` token rules and the component-class reference. Pay attention to the "Brand Token Injection" section — it specifies how to populate the template's `:root` block.

2. **Resolve the project's design tokens** so the artifact matches the project's brand, not the aligned plugin's. Find the right design-principles file using this lookup order (use `{project-root}` as resolved during the project scan):

   a. **Project root:** `{project-root}/docs/design/design-principles.md`
   b. **Monorepo apps:** if (a) is missing, Glob `{project-root}/apps/*/docs/design/design-principles.md`. Same for `{project-root}/packages/*/docs/design/design-principles.md`.
      - Exactly one match: use it.
      - Multiple matches: ask the user which app/package this brainstorm targets, then use that one.
      - Zero matches: continue to (c).
   c. **Global fallback:** `~/.claude/docs/design/design-principles.md`.

   **Placeholder check.** If the file found in (a), (b), or (c) is a kickstart-generated placeholder — heuristic: under 500 bytes, OR contains "This file is a placeholder", OR contains "Run `/aligned:create-design-principles`" — treat it as missing, advance to the next lookup step, and surface this warning to the user: *"Your project's `docs/design/design-principles.md` is still a placeholder. The brainstorm visualization will use the aligned plugin's default tokens. Run `/aligned:create-design-principles` to define the project's brand."*

   If no usable file is found at any step, skip token extraction — the template's built-in defaults will apply.

   Once a usable file is found, extract values per the "Brand Token Injection" / "Resolving project tokens" rules in `brainstorm-components.md`. If those rules' halt-and-ask trigger fires (genuine token-name ambiguity, unmappable brand-specific tokens), present the proposed mapping to the user before continuing.

3. **Copy and patch the template.** Read `{mode-template-path}` and Write its contents verbatim to `/tmp/brainstorm-{topic}-{timestamp}/live.html`. Then patch:
   - Replace `{title}`, `{subtitle}`, and `{context}` with session-specific values.
   - Populate the `:root` block at the top of the inline `<style>` with the project tokens you read in step 2 (or leave the built-in defaults if no design-principles file was found).
   - Do not change any `var(--color-*)` or `var(--font-*)` references elsewhere in the template — they resolve through `:root`.
   - Append the design sections validated so far.

   Do not rewrite the template from memory — the file copy is the contract.

4. **Open the file in the default browser** using a platform-aware pattern (separate Bash call — no `&&` chaining):

   `open /tmp/brainstorm-{topic}-{timestamp}/live.html || xdg-open /tmp/brainstorm-{topic}-{timestamp}/live.html`

   If both commands fail (headless environment), log a warning and continue — the artifact still gets written.

5. **Update the file as each subsequent design section is validated** (Write tool to add the new section's content). Preserve the `:root` block exactly as written in step 3 — do not regenerate it. The browser picks up changes within 15 seconds via the self-refresh script.

6. **Inject interactive widgets if the design produced a Decision Log (>=1 entry) or an Open Questions list (>=1 entry).** Read `{base-directory}/references/widgets.html` and perform three injections into `/tmp/brainstorm-{topic}-{timestamp}/live.html`:

   a. **WIDGETS-CSS block** — insert once into `<head>` after the inline `<style>` block. Copy verbatim between (and including) `<!-- WIDGETS-CSS-START -->` and `<!-- WIDGETS-CSS-END -->`.

   b. **WIDGETS-SCRIPT block** — insert once immediately before `</body>`. Copy verbatim between (and including) `<!-- WIDGETS-SCRIPT-START -->` and `<!-- WIDGETS-SCRIPT-END -->`. **The block MUST land outside the `<!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END -->` delimiters** so the strip-script rule preserves widget JS in committed snapshots.

   c. **WIDGET-HTML blocks** — for the Decision Log section, copy `WIDGET-HTML: decision-log-flat` (if <10 entries) or `WIDGET-HTML: decision-log-categorized` (if >=10 entries) into the Decision Log `<section>`, then append the `WIDGET-HTML: prompt-box` block with `{widget-id}` substituted to `decisions`. For the Open Questions section, mirror the same with `open-questions-*` and `{widget-id}` = `questions`. Every triage entry must carry `data-id="N"` and `data-title="..."` (decisions are `<div class="decision-card">`; questions are `<tr>`); section headers carry no `data-id` (see `brainstorm-components.md` § Interactive Widgets).

   Do not rewrite the widget code from memory — the file copy is the contract.

## Pre-critique snapshot

Before dispatching the critique panel, copy the live visualization to its permanent location so critics can access it:

1. Copy `/tmp/brainstorm-{topic}-{timestamp}/live.html` to `docs/mockups/{session-name}.html`.
2. Add `**Mockups:** docs/mockups/{session-name}.html` to the design document header (write AFTER the copy so the file exists at commit time).
2.5. **Verify the committed snapshot before continuing.** Two checks; both must pass.
   - **Mermaid syntax.** Run `node {plugin-root}/skills/brainstorming/scripts/validate-mermaid.mjs docs/mockups/{session-name}.html` (first use in a fresh checkout: `npm install` inside `skills/brainstorming/scripts/`). The script extracts every `<pre class="mermaid"|"mermaid-deferred">` block, decodes entities and elides `<br/>` to match what mermaid sees at runtime, and parses each block with the same library version the templates load from CDN. Exit 0 means all blocks parse. Exit 1 prints the offending block index, the source mermaid receives, and the parser's caret-pointer error — fix the source design doc, regenerate the snapshot (next step), and re-run. Do not proceed past 2.5 until exit is 0.
   - **Widgets.** If the design includes a Decision Log or Open Questions widget, verify the snapshot still contains the `<!-- WIDGETS-SCRIPT-START -->` marker and that the widget containers (`id="decisions-table"`, `id="questions-table"`) bind on load (open the file in a browser — the prompt textareas should populate without console errors).
3. The critique panel's `visual-artifacts` config references `docs/mockups/{session-name}.html` — this copy ensures it exists at that path.

## Post-critique regeneration

If the design document was modified by fact-check corrections or user-approved critique fixes, regenerate the HTML at `docs/mockups/{session-name}.html` by re-copying `{mode-template-path}` verbatim, then re-patching from the corrected design:

- Replace `{title}`, `{subtitle}`, and `{context}`.
- Populate the `:root` block by copying it verbatim from the live visualization at `/tmp/brainstorm-{topic}-{timestamp}/live.html` so the committed artifact stays on-brand.
- Append the corrected section content using the components reference.

Do not rewrite the template from memory — the file copy is the contract.

Skip regeneration if the design document is unchanged (all critique verdicts were APPROVE with no corrections applied).

- **Re-inject interactive widgets** if the corrected design still contains a Decision Log (>=1 entry) or Open Questions list (>=1 entry). Re-run the Live-phase step 6 widget-injection procedure (Read `{base-directory}/references/widgets.html`; inject CSS into `<head>`, SCRIPT before `</body>` outside LIVE-REFRESH delimiters, HTML blocks inside their owning sections). The widget JS must land in the regenerated file BEFORE the strip-script rule runs, otherwise the committed snapshot ships without the interactive surface.

After regeneration (or if no regeneration was needed), apply the strip-script rule from `{base-directory}/references/shared-rules.md` to `docs/mockups/{session-name}.html`.

## Nested sub-tabs

When a tabbed HTML document is generated (live visualization or any auxiliary mockup), use nested sub-tabs (progressive disclosure) whenever a single tab contains more detail than can be scanned in one view. Do not flatten into many top-level tabs or cram everything into one scrollable panel. The pattern is:

- **Top-level tabs** for major conceptual sections.
- **Sub-tabs within each** for natural subdivisions (phases, layers, concerns).
- Each sub-tab holds **one focused diagram or content block**.

The check: if a tab contains multiple diagrams, subgraphs, or sections that each deserve their own view, break them into nested sub-tabs rather than stacking vertically.
