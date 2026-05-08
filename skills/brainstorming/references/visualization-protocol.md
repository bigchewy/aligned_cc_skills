<!-- Visualization protocol: Read into context by visualizing modes (software, business, authoring, planning) at the start of their Visualization step. Research mode does not generate a live HTML artifact and skips this protocol. Do not add YAML frontmatter. -->

# Visualization Protocol

This protocol governs the live HTML artifact produced during the visualization phase. It is invoked from each visualizing mode after the design document has been written and before the critique round. Each mode owns its own conditional trigger (whether visualization fires for this session) and its own template file; this protocol owns the procedure.

## Inputs

The invoking mode supplies these values:

- `{mode-template-path}` — absolute path to the mode's template, e.g. `{base-directory}/references/templates/software-template.html`. Each visualizing mode owns its own template; templates may diverge over time.
- `{topic}` — the brainstorm topic slug.
- `{timestamp}` — epoch seconds (or another collision-resistant value).
- `{session-name}` — the kebab-case session name used for the committed mockup at `docs/mockups/{session-name}.html`.
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

## Pre-critique snapshot

Before dispatching the critique panel, copy the live visualization to its permanent location so critics can access it:

1. Copy `/tmp/brainstorm-{topic}-{timestamp}/live.html` to `docs/mockups/{session-name}.html`.
2. Add `**Mockups:** docs/mockups/{session-name}.html` to the design document header (write AFTER the copy so the file exists at commit time).
3. The critique panel's `visual-artifacts` config references `docs/mockups/{session-name}.html` — this copy ensures it exists at that path.

## Post-critique regeneration

If the design document was modified by fact-check corrections or user-approved critique fixes, regenerate the HTML at `docs/mockups/{session-name}.html` by re-copying `{mode-template-path}` verbatim, then re-patching from the corrected design:

- Replace `{title}`, `{subtitle}`, and `{context}`.
- Populate the `:root` block by copying it verbatim from the live visualization at `/tmp/brainstorm-{topic}-{timestamp}/live.html` so the committed artifact stays on-brand.
- Append the corrected section content using the components reference.

Do not rewrite the template from memory — the file copy is the contract.

Skip regeneration if the design document is unchanged (all critique verdicts were APPROVE with no corrections applied).

After regeneration (or if no regeneration was needed), apply the strip-script rule from `{base-directory}/references/shared-rules.md` to `docs/mockups/{session-name}.html`.

## Nested sub-tabs

When a tabbed HTML document is generated (live visualization or any auxiliary mockup), use nested sub-tabs (progressive disclosure) whenever a single tab contains more detail than can be scanned in one view. Do not flatten into many top-level tabs or cram everything into one scrollable panel. The pattern is:

- **Top-level tabs** for major conceptual sections.
- **Sub-tabs within each** for natural subdivisions (phases, layers, concerns).
- Each sub-tab holds **one focused diagram or content block**.

The check: if a tab contains multiple diagrams, subgraphs, or sections that each deserve their own view, break them into nested sub-tabs rather than stacking vertically.
