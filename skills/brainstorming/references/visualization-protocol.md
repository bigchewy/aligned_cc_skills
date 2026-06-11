<!-- Visualization protocol: Read into context by visualizing modes (software, authoring) at the start of their Visualization step. Research and Roadmap modes do not generate a live HTML artifact and skip this protocol. Do not add YAML frontmatter. -->

# Visualization Protocol

This protocol governs the live HTML artifact produced during the visualization phase. It is invoked from each visualizing mode after the design document has been written and before the critique round. Each mode owns its own conditional trigger (whether visualization fires for this session) and its own template file; this protocol owns the procedure.

## Configuration

The invoking mode supplies these values to the shared runner (all absolute paths):

| Input | Value in brainstorming context |
|---|---|
| `{template-path}` | `{base-directory}/references/templates/software-template.html` (absolute) |
| `{widgets-path}` | `{base-directory}/references/widgets.html` |
| `{components-path}` | `{base-directory}/references/brainstorm-components.md` |
| `{validate-mermaid-script}` | `{plugin-root}/skills/brainstorming/scripts/validate-mermaid.mjs` |
| `{session-name}` | Derived as `YYYY-MM-DD-{topic}` using today's date and the topic slug, matching the design document base name (`docs/plans/YYYY-MM-DD-<topic>-design.md`) |
| `{output-path}` | `docs/mockups/{session-name}.html` |
| `{live-session}` | `yes` |

Follow `skills/_shared/visualization-runner.md` end-to-end with the Configuration above.

> Copy the template file and patch it — NEVER hand-write or compactly rewrite the artifact HTML, even when that seems faster. See the runner's anti-shortcut contract.

## Live phase

Call the runner once after the trigger fires, before any critique work begins. As each subsequent design section is validated, call the runner again to update the live artifact (the runner's Step 5 handles the incremental write; preserve the `:root` block as written in the first call).

## Pre-critique snapshot

Before dispatching the critique panel, copy the live visualization to its permanent location so critics can access it:

1. Copy `/tmp/brainstorm-{topic}-{timestamp}/live.html` to `docs/mockups/{session-name}.html`.
2. Add `**Mockups:** docs/mockups/{session-name}.html` to the design document header (write AFTER the copy so the file exists at commit time).
2.5. **Verify the committed snapshot before continuing.** Two checks; both must pass.
   - **Mermaid syntax.** Run `node {plugin-root}/skills/brainstorming/scripts/validate-mermaid.mjs docs/mockups/{session-name}.html` (first use in a fresh checkout: `npm install` inside `skills/brainstorming/scripts/`). Exit 0 means all blocks parse. Exit 1 prints the offending block index and parser error — fix the source design doc, regenerate, and re-run. Do not proceed past 2.5 until exit is 0.
   - **Widgets.** If the design includes a Decision Log or Open Questions widget, verify the snapshot still contains the `<!-- WIDGETS-SCRIPT-START -->` marker and that the widget containers (`id="decisions-table"`, `id="questions-table"`) bind on load.
3. The critique panel's `visual-artifacts` config references `docs/mockups/{session-name}.html` — this copy ensures it exists at that path.

## Post-critique regeneration

If the design document was modified by fact-check corrections or user-approved critique fixes, re-run the runner against the corrected design to regenerate `docs/mockups/{session-name}.html`. Copy the `:root` block verbatim from the live visualization at `/tmp/brainstorm-{topic}-{timestamp}/live.html` so the committed artifact stays on-brand.

Skip regeneration if the design document is unchanged (all critique verdicts were APPROVE with no corrections applied).

After regeneration (or if no regeneration was needed), apply the strip-script rule from `{base-directory}/references/shared-rules.md` to `docs/mockups/{session-name}.html`.

## Audience contract (hard precondition)

Every visualization artifact is built for one fixed audience: **an executive who understands details.** This is not configurable per session and must not be re-asked. It resolves the density question before drawing begins:

- **Overview (top level / first tab):** summary-level only — the high-level flow, key inputs, outputs, and decision points. No file-level or implementation detail here.
- **Tabs and sub-tabs:** detail is allowed and welcome. An executive who understands details will drill in — give them real depth (file paths, schemas, sequencing) behind progressive disclosure, never on the surface.
- **Before simplifying any draft,** list the must-keep inputs/outputs from the design document and treat that list as non-negotiable. Simplification means pushing detail down into sub-tabs, never dropping a must-keep element.
