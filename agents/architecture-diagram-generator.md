---
model: sonnet
---

# Architecture Diagram Generator

## Overview

Generate self-contained HTML architecture diagrams AND update the project's `docs/architecture.md` when architectural decisions are made during brainstorming. This agent serves dual purposes: visual artifact for human review and living documentation maintenance.

## When to Use

- During brainstorming when the design introduces new modules, services, routes, or data flows
- When the system architecture is changing and needs visual documentation
- When `docs/architecture.md` needs updating based on design decisions

## Dual Output

This agent produces up to two artifacts:

1. **HTML visualization** (always) — Rich architecture diagram saved to `docs/mockups/{session-name}/architecture.html`. Includes a descriptive header tying it back to the brainstorming session.
2. **architecture.md update** (when `docs/architecture.md` exists) — Updates the affected Mermaid diagrams to reflect new architectural decisions.

## Step 1: Read Context

1. Read the design document at the provided path
2. Read `docs/architecture.md` if it exists — note which diagrams exist and their current state
3. Identify what architectural changes the design introduces (new modules, changed data flows, new services, restructured boundaries)

## Step 2: Generate HTML Visualization

Save to `docs/mockups/{session-name}/architecture.html`.

**Required header structure** — every HTML file must include:
- `<h1>` with the project name and "Architecture"
- `<p class="subtitle">` describing what changed and linking to the brainstorming session topic
- `<p class="context">` with a 1-2 sentence summary of the architectural changes being visualized

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Project] Architecture — [Session Topic]</title>
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #fafafa;
      margin: 0;
      padding: 40px;
      max-width: 1200px;
      margin: 0 auto;
    }
    h1 {
      font-size: 1.5rem;
      font-weight: 500;
      color: #1a1a1a;
      margin-bottom: 4px;
    }
    .subtitle {
      font-size: 0.95rem;
      color: #666;
      margin-bottom: 4px;
    }
    .context {
      font-size: 0.88rem;
      color: #888;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid #e5e5e5;
    }
    .section {
      background: white;
      border: 1px solid #e5e5e5;
      border-radius: 12px;
      padding: 24px;
      margin: 24px 0;
    }
    .section h2 {
      font-size: 1.1rem;
      font-weight: 500;
      color: #333;
      margin-bottom: 16px;
    }
    /* Semantic layer colors */
    .layer-data { fill: #4299e1; }
    .layer-processing { fill: #ed8936; }
    .layer-service { fill: #9f7aea; }
    .layer-output { fill: #48bb78; }
    .layer-external { fill: #e53e3e; }
    .component-label {
      fill: white;
      font-family: system-ui;
      font-size: 12px;
      font-weight: 500;
      text-anchor: middle;
      dominant-baseline: central;
    }
    .connector {
      stroke: #999;
      stroke-width: 1.5;
      fill: none;
      marker-end: url(#arrow);
    }
    .connector-label {
      fill: #666;
      font-family: system-ui;
      font-size: 11px;
      text-anchor: middle;
    }
    /* New/changed indicators */
    .new-component {
      stroke: #48bb78;
      stroke-width: 2;
      stroke-dasharray: 6 3;
    }
    .changed-component {
      stroke: #f59e0b;
      stroke-width: 2;
    }
    /* Legend */
    .legend {
      margin-top: 24px;
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.85rem;
      color: #666;
    }
    .legend-dot {
      width: 12px;
      height: 12px;
      border-radius: 3px;
    }
    /* Component reference table */
    .ref-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }
    .ref-table th {
      text-align: left;
      padding: 8px 12px;
      border-bottom: 2px solid #e5e5e5;
      color: #666;
      font-weight: 500;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .ref-table td {
      padding: 8px 12px;
      border-bottom: 1px solid #f0f0f0;
      color: #333;
    }
    .ref-table td code {
      font-family: 'SF Mono', 'Fira Code', monospace;
      font-size: 0.82rem;
      background: #f5f5f5;
      padding: 1px 6px;
      border-radius: 3px;
    }
    .badge-new {
      font-size: 0.7rem;
      padding: 1px 6px;
      border-radius: 4px;
      background: rgba(72, 187, 120, 0.12);
      color: #2f855a;
      font-weight: 500;
    }
    .badge-changed {
      font-size: 0.7rem;
      padding: 1px 6px;
      border-radius: 4px;
      background: rgba(245, 158, 11, 0.12);
      color: #b45309;
      font-weight: 500;
    }
  </style>
</head>
<body>
  <h1>[Project Name] — Architecture</h1>
  <p class="subtitle">Brainstorming session: [session topic]</p>
  <p class="context">[1-2 sentence summary of what architectural changes are being visualized]</p>

  <!-- Data Flow Section -->
  <div class="section">
    <h2>Data Flow</h2>
    <svg viewBox="0 0 800 300">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5"
          markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#999"/>
        </marker>
      </defs>
      <!-- Sources → Processing → Outputs -->
    </svg>
  </div>

  <!-- System Layers Section -->
  <div class="section">
    <h2>System Architecture</h2>
    <svg viewBox="0 0 800 400">
      <!-- Layered architecture diagram -->
      <!-- Use .new-component and .changed-component classes to highlight changes -->
    </svg>
  </div>

  <!-- Component Reference -->
  <div class="section">
    <h2>Component Reference</h2>
    <table class="ref-table">
      <thead>
        <tr><th>Component</th><th>File Path</th><th>Purpose</th><th>Status</th></tr>
      </thead>
      <tbody>
        <!-- One row per component, with badge-new or badge-changed where applicable -->
      </tbody>
    </table>
  </div>

  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#4299e1"></div>Data Layer</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ed8936"></div>Processing</div>
    <div class="legend-item"><div class="legend-dot" style="background:#9f7aea"></div>Services</div>
    <div class="legend-item"><div class="legend-dot" style="background:#48bb78"></div>Output</div>
    <div class="legend-item"><div class="legend-dot" style="background:#e53e3e"></div>External</div>
    <div class="legend-item" style="gap:4px"><span style="border:2px dashed #48bb78;width:12px;height:12px;border-radius:3px;display:inline-block"></span>New</div>
    <div class="legend-item" style="gap:4px"><span style="border:2px solid #f59e0b;width:12px;height:12px;border-radius:3px;display:inline-block"></span>Changed</div>
  </div>
</body>
</html>
```

## Step 3: Update architecture.md

**Only when `docs/architecture.md` exists.**

1. Read the existing file
2. Identify which Mermaid diagrams are affected by the new design
3. Update only the affected diagrams — do not rewrite unrelated sections
4. Verify updated diagrams against actual source files (architecture docs may be stale — trust code over existing diagrams)
5. If you find pre-existing inaccuracies in diagrams you're editing, fix those too and note what you corrected

**Do NOT create architecture.md from scratch** — that's the kickstart skill's job. If the file doesn't exist, skip this step and only produce the HTML visualization.

## Guidelines

- **Self-contained HTML:** Every visualization works when opened in a browser. No external dependencies.
- **Semantic colors:** Blue=data, orange=processing, purple=services, green=outputs, red=external.
- **Highlight changes:** Use dashed green borders for new components, solid orange borders for changed components.
- **Component reference:** Always include a table mapping components to actual file paths.
- **Descriptive header:** The `<h1>`, subtitle, and context paragraph must orient the reader — they should know what they're looking at without additional context.
- **Responsive:** Use `viewBox` on SVG so it scales to any container width.

## After Generating

Open the HTML visualization in the browser for the user to preview:

```bash
open docs/mockups/[session-name]/architecture.html
```

**Do NOT commit.** The brainstorming skill commits all visual artifacts and the architecture.md update together with the design document after the critique round completes. Committing here would capture a pre-critique draft.

## Fragment Mode

When dispatched by the session-document-generator with the phrase "Return fragments, do not write HTML files" in the prompt, return structured content instead of writing a standalone HTML file.

**Fragment output format** (return as a fenced code block with language `fragment-json`):

```fragment-json
{
  "title": "System Architecture Title",
  "description": "1-2 sentence description of what this diagram shows.",
  "bullets": [
    "**Key term 1:** explanation",
    "**Key term 2:** explanation"
  ],
  "diagram_type": "svg",
  "diagram_markup": "<svg viewBox=\"0 0 800 400\">...</svg>",
  "suggested_badge": "Architecture",
  "sub_tabs": null
}
```

**Fields:**
- `title`: Short descriptive title for the tab heading
- `description`: 1-2 sentences for the text layer below the heading
- `bullets`: Array of markdown bullet points with bolded key terms (for the "rich text" layer per Principle 5)
- `diagram_type`: Always `"svg"` for this agent
- `diagram_markup`: Raw SVG markup (the `<svg>` element with all children). Use design-principles.md tokens for all colors, strokes, and text styles. Use `viewBox` for responsive scaling.
- `suggested_badge`: Short label for a badge next to the tab heading (e.g., "Architecture", "Layers", "Components")
- `sub_tabs`: If the architecture has distinct sections that each need focused diagrams (e.g., separate layers), return an array of fragment objects (same schema minus `sub_tabs`) — one per section. Otherwise `null`.

**Rules in fragment mode:**
- Do NOT write any HTML files
- Do NOT open anything in the browser
- Do NOT update `docs/architecture.md` — that is standalone mode's responsibility
- Still read design-principles.md for color tokens and apply them in SVG styles
- Still follow all SVG diagram conventions from this agent
- Use architecture layer colors for tonal depth in layered diagrams
- Read the "Diagram Documentation Principles" section in design-principles.md and follow all 8 rules

**Standalone mode** (default, current behavior) is unchanged — when not dispatched in fragment mode, produce full self-contained HTML files and update `docs/architecture.md` as before.
