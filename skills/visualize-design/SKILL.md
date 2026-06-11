---
name: visualize-design
description: "Render any markdown design doc or the current conversation's validated content as an on-brand, tabbed, Mermaid-validated HTML artifact. Use when you want a standalone visualization without the brainstorming flow."
---

# Visualize Design

Standalone caller for the visualization engine. Renders a document or the current thread's validated content into the same on-brand artifact brainstorming produces.

> **Path Resolution:** Resolve the plugin root per `skills/_shared/resolve-skill-path.md`. Template, widgets, components doc, and the mermaid validator live under `{plugin-root}/skills/brainstorming/`.

## Anti-shortcut contract

Copy the template file and patch it. NEVER hand-write or "compactly rewrite" the artifact HTML from memory, even when that seems faster — that shortcut bypasses the template, the widgets, the browser-open, and the Overview gate (KB-085/086).

## Step 1: Resolve the source

- **Path argument given:** read that markdown document; it is `{source-content}`.
- **No argument:** use the validated content from the current conversation.
- **Neither yields renderable content:** ask exactly this question (fixed wording):

  > No document path was given and this conversation has no renderable content yet. Give me either: (a) a path to a markdown doc to visualize, or (b) a one-sentence description of what to visualize and I'll build it with you here.

## Step 2: Resolve Configuration and call the runner

Resolve the runner's Configuration inputs (all absolute):
- `{template-path}` = `{plugin-root}/skills/brainstorming/references/templates/software-template.html` (resolved via plugin root — NEVER `{base-directory}`-relative; no templates live under `visualize-design/`).
- `{widgets-path}` = `{plugin-root}/skills/brainstorming/references/widgets.html`
- `{components-path}` = `{plugin-root}/skills/brainstorming/references/brainstorm-components.md`
- `{validate-mermaid-script}` = `{plugin-root}/skills/brainstorming/scripts/validate-mermaid.mjs`
- `{session-name}` = `YYYY-MM-DD-<topic-slug>`
- `{output-path}` = `{project-root}/docs/design-visualizations/{session-name}.html`
- `{live-session}` = `yes`

Follow `skills/_shared/visualization-runner.md` end-to-end with that Configuration. Open the self-refreshing `/tmp` artifact immediately and update as the user iterates. Inject widgets only if the content actually contains a Decision Log or Open Questions section.

## Step 3: Finish

On user confirmation: run the runner's mermaid gate and executive-overview gate, write the final copy to `{project-root}/docs/design-visualizations/{session-name}.html` (create the directory if missing), strip the live-refresh script, and open the committed copy. **If `{output-path}` already exists, overwrite it** — re-rendering the same doc the same day is the expected workflow, not an error.
