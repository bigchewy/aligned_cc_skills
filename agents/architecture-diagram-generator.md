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

1. **Read design principles** — resolve the project's design tokens using the ladder in `skills/_shared/visualization-runner.md` § "Step 2: Resolve the project's design tokens" (project root → monorepo `apps/*`/`packages/*` glob → global fallback, with the placeholder heuristic). Extract color tokens and semantic diagram colors from the resolved file. **Do not proceed without design tokens.**
2. Read the design document at the provided path
3. Read `docs/architecture.md` if it exists — note which diagrams exist and their current state
4. Identify what architectural changes the design introduces (new modules, changed data flows, new services, restructured boundaries)

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
    /* --- Apply tokens from design-principles.md --- */
    body {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #faf9f7; /* --color-background */
      margin: 0;
      padding: 40px;
      max-width: 1200px;
      margin: 0 auto;
    }
    h1 {
      font-size: 1.5rem;
      font-weight: 500;
      color: #1a1a1a; /* --color-foreground */
      margin-bottom: 4px;
    }
    .subtitle {
      font-size: 0.95rem;
      color: #555555; /* --color-secondary */
      margin-bottom: 4px;
    }
    .context {
      font-size: 0.88rem;
      color: #6b7280; /* --color-dimmed */
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid #e5e7eb; /* --color-border */
    }
    .section {
      background: white;
      border: 1px solid #e5e7eb; /* --color-border */
      border-radius: 12px; /* --radius-md */
      padding: 24px;
      margin: 24px 0;
    }
    .section h2 {
      font-size: 1.1rem;
      font-weight: 500;
      color: #1a1a1a; /* --color-foreground */
      margin-bottom: 16px;
    }
    /* Architecture layer colors — warm tonal progression from design-principles.md */
    .layer-1 { fill: #f5f3f0; } /* Presentation / UI */
    .layer-2 { fill: #f2efec; } /* Application / Services */
    .layer-3 { fill: #eeeae6; } /* Domain / Business Logic */
    .layer-4 { fill: #eae6e1; } /* Infrastructure / Data */
    .layer-5 { fill: #e5e1dc; } /* External / Platform */
    .component-label {
      fill: #1a1a1a; /* --color-foreground */
      font-family: system-ui;
      font-size: 12px;
      font-weight: 500;
      text-anchor: middle;
      dominant-baseline: central;
    }
    .connector {
      stroke: #ff6900; /* --color-accent */
      stroke-width: 1.5;
      fill: none;
      marker-end: url(#arrow);
    }
    .connector-label {
      fill: #555555; /* --color-secondary */
      font-family: system-ui;
      font-size: 11px;
      text-anchor: middle;
    }
    /* New/changed indicators */
    .new-component {
      stroke: #ff6900; /* --color-accent */
      stroke-width: 2;
      stroke-dasharray: 6 3;
    }
    .changed-component {
      stroke: #1a1a1a; /* --color-foreground */
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
      color: #555555; /* --color-secondary */
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
      border-bottom: 2px solid #e5e7eb; /* --color-border */
      color: #555555; /* --color-secondary */
      font-weight: 500;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .ref-table td {
      padding: 8px 12px;
      border-bottom: 1px solid #f0eeeb; /* --color-muted */
      color: #1a1a1a; /* --color-foreground */
    }
    .ref-table td code {
      font-family: Menlo, Consolas, Monaco, "Courier New", monospace;
      font-size: 0.82rem;
      background: #f0eeeb; /* --color-muted */
      padding: 1px 6px;
      border-radius: 6px; /* --radius-sm */
    }
    .badge-new {
      font-size: 0.7rem;
      padding: 1px 6px;
      border-radius: 9999px; /* --radius-full */
      background: #fff7ed; /* --color-accent-subtle */
      color: #ff6900; /* --color-accent */
      font-weight: 500;
    }
    .badge-changed {
      font-size: 0.7rem;
      padding: 1px 6px;
      border-radius: 9999px; /* --radius-full */
      background: #f0eeeb; /* --color-muted */
      color: #1a1a1a; /* --color-foreground */
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
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#ff6900"/> <!-- --color-accent -->
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
    <div class="legend-item"><div class="legend-dot" style="background:#f5f3f0"></div>Layer 1 (UI)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#f2efec"></div>Layer 2 (Services)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#eeeae6"></div>Layer 3 (Domain)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#eae6e1"></div>Layer 4 (Infra)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#e5e1dc"></div>Layer 5 (External)</div>
    <div class="legend-item" style="gap:4px"><span style="border:2px dashed #ff6900;width:12px;height:12px;border-radius:3px;display:inline-block"></span>New</div>
    <div class="legend-item" style="gap:4px"><span style="border:2px solid #1a1a1a;width:12px;height:12px;border-radius:3px;display:inline-block"></span>Changed</div>
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
- **Design-token driven:** All colors come from design-principles.md. Use architecture layer colors for tonal depth. Use `--color-accent` for connectors and new-component highlights.
- **Highlight changes:** Use dashed `--color-accent` borders for new components, solid `--color-foreground` borders for changed components.
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
