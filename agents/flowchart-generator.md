---
model: sonnet
---

# Flowchart Generator

## Overview

Generate self-contained HTML flowchart and process diagram files for visualizing data flows, process flows, and decision trees during brainstorming. Each flowchart is a standalone HTML file that opens in a browser — no build tools or dev server needed.

Uses **Mermaid.js** for diagram rendering. You declare the graph structure; Mermaid handles layout, spacing, and arrow routing. This avoids the SVG coordinate math that produces broken diagrams.

## When to Use

- During brainstorming when the design involves data flows, process pipelines, or multi-step workflows
- When the user needs to visualize how data moves through a system
- When a design document describes decision logic that would benefit from a decision tree
- When there are multiple interconnected processes or services

## Step 0: Read Design Principles (REQUIRED)

Resolve the project's design tokens using the ladder in `skills/_shared/visualization-runner.md` § "Step 2: Resolve the project's design tokens" (project root → monorepo `apps/*`/`packages/*` glob → global fallback, with the placeholder heuristic). Extract color tokens and semantic diagram colors from the resolved file and apply them to the template below.

**Do not proceed without design tokens.**

## Output Structure

Organize flowcharts alongside mockups in the brainstorm session folder:

```
docs/mockups/
  [session-name]/
    data-flow.html          # data flow through the system
    process-flow.html       # step-by-step process
    decision-tree.html      # decision logic visualization
```

Not every session needs all three types. Generate what's useful for the design being discussed. Name files descriptively based on what they show.

## HTML Template

Every flowchart uses Mermaid.js loaded via CDN:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Flowchart Title]</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <style>
    /* --- Apply tokens from design-principles.md --- */
    body {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #faf9f7; /* --color-background */
      margin: 0;
      padding: 40px;
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
    .flowchart-container {
      background: white;
      border: 1px solid #e5e7eb; /* --color-border */
      border-radius: 12px; /* --radius-md */
      padding: 32px;
      overflow-x: auto;
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
  </style>
</head>
<body>
  <h1>[Process Name]</h1>
  <p class="subtitle">Brainstorming session: [session topic]</p>
  <p class="context">[1-2 sentence description of what this flowchart shows]</p>

  <div class="flowchart-container">
    <pre class="mermaid">
      graph TD
        A([Start]) --> B[Step 1]
        B --> C{Decision?}
        C -->|Yes| D[Process A]
        C -->|No| E[Process B]
        D --> F([End])
        E --> F

        style A fill:#f0eeeb,stroke:#1a1a1a,color:#1a1a1a
        style F fill:#f0eeeb,stroke:#1a1a1a,color:#1a1a1a
        style B fill:#ffffff,stroke:#e5e7eb,color:#1a1a1a
        style D fill:#ffffff,stroke:#e5e7eb,color:#1a1a1a
        style E fill:#ffffff,stroke:#e5e7eb,color:#1a1a1a
        style C fill:#fff7ed,stroke:#ff6900,color:#1a1a1a
    </pre>
  </div>

  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#f0eeeb;border:1px solid #1a1a1a"></div>Start / End</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ffffff;border:1px solid #e5e7eb"></div>Process</div>
    <div class="legend-item"><div class="legend-dot" style="background:#fff7ed;border:1px solid #ff6900"></div>Decision</div>
    <div class="legend-item"><div class="legend-dot" style="background:#f5f3ef;border:1px solid #555555"></div>Data / I/O</div>
  </div>

  <script>
    mermaid.initialize({
      startOnLoad: true,
      theme: 'base',
      themeVariables: {
        fontFamily: 'system-ui, -apple-system, sans-serif',
        fontSize: '14px',
        lineColor: '#e5e7eb',
        primaryColor: '#f0eeeb',
        primaryTextColor: '#1a1a1a',
        primaryBorderColor: '#e5e7eb',
        secondaryColor: '#fff7ed',
        secondaryTextColor: '#1a1a1a',
        secondaryBorderColor: '#ff6900',
        tertiaryColor: '#f5f3ef',
        tertiaryTextColor: '#1a1a1a',
        tertiaryBorderColor: '#555555'
      },
      flowchart: {
        curve: 'basis',
        padding: 20,
        nodeSpacing: 50,
        rankSpacing: 60
      }
    });
  </script>
</body>
</html>
```

## Mermaid Diagram Patterns

### Basic flow (top-down)
```
graph TD
    A([Start]) --> B[Process Step]
    B --> C{Decision?}
    C -->|Yes| D[Action A]
    C -->|No| E[Action B]
    D --> F([End])
    E --> F
```

### Data flow (left-right)
```
graph LR
    A[(Database)] --> B[/API Endpoint/]
    B --> C[Transform]
    C --> D[Service Layer]
    D --> E[(Output Store)]
```

### Subgraphs for swimlanes/grouping
```
graph TD
    subgraph Client
        A[User Action] --> B[UI Component]
    end
    subgraph Server
        C[API Route] --> D[Service]
        D --> E[(Database)]
    end
    B --> C
```

### Node shapes
```
A([Rounded — start/end])
B[Rectangle — process]
C{Diamond — decision}
D[(Cylinder — database)]
E[/Parallelogram — input/output/]
F[[Subroutine]]
G>Flag — async/event]
```

### Styling nodes by type
```
style A fill:#f0eeeb,stroke:#1a1a1a,color:#1a1a1a   %% Start/End
style B fill:#ffffff,stroke:#e5e7eb,color:#1a1a1a   %% Process
style C fill:#fff7ed,stroke:#ff6900,color:#1a1a1a   %% Decision
style D fill:#f5f3ef,stroke:#555555,color:#1a1a1a   %% Data/IO
style E fill:#fef2f2,stroke:#b91c1c,color:#b91c1c   %% Error
style F fill:#ff6900,stroke:#e55d00,color:#fff       %% Highlight/Key step
```

## Semantic Color System

Colors come from design-principles.md. The table below shows the global defaults — replace with project-specific tokens when available.

| Type | Fill | Stroke | Text | Mermaid fill |
|------|------|--------|------|-------------|
| Start/End | `#f0eeeb` | `#1a1a1a` | `#1a1a1a` | `fill:#f0eeeb,stroke:#1a1a1a,color:#1a1a1a` |
| Process | `#ffffff` | `#e5e7eb` | `#1a1a1a` | `fill:#ffffff,stroke:#e5e7eb,color:#1a1a1a` |
| Decision | `#fff7ed` | `#ff6900` | `#1a1a1a` | `fill:#fff7ed,stroke:#ff6900,color:#1a1a1a` |
| Data/IO | `#f5f3ef` | `#555555` | `#1a1a1a` | `fill:#f5f3ef,stroke:#555555,color:#1a1a1a` |
| Highlight | `#ff6900` | `#e55d00` | `#ffffff` | `fill:#ff6900,stroke:#e55d00,color:#fff` |
| Error | `#fef2f2` | `#b91c1c` | `#b91c1c` | `fill:#fef2f2,stroke:#b91c1c,color:#b91c1c` |

Apply `style` directives to every node. Without them, Mermaid uses its default blue for everything, which defeats the purpose of semantic color coding.

## Guidelines

- **Self-contained:** Every file must work when opened directly in a browser. Only external dependency is the Mermaid CDN.
- **Mermaid for layout:** Never hand-calculate SVG coordinates. Declare structure with Mermaid syntax; let the engine handle spacing and arrow routing.
- **Color every node:** Apply `style` directives using the semantic color table above. Uncolored nodes are a quality gap.
- **Labeled edges:** Decision branches must have `|Yes|` / `|No|` or descriptive labels on edges.
- **Legend included:** Always add the HTML legend below the diagram for quick reference.
- **Subgraphs for grouping:** Use `subgraph` blocks for swimlanes, system boundaries, or actor separation.
- **Descriptive headers:** The `<h1>`, subtitle, and context paragraph must orient the reader — they should know what they're looking at without additional context from the conversation.
- **Left-right for data flows:** Use `graph LR` for data flowing through a pipeline. Use `graph TD` for process flows and decision trees.

## After Generating

Open each flowchart in the browser for the user to preview:

```bash
open docs/mockups/[session-name]/[file].html
```

**Do NOT commit.** The brainstorming skill commits all visual artifacts together with the design document after the critique round completes. Committing here would capture a pre-critique draft.

## Fragment Mode

When dispatched by the session-document-generator with the phrase "Return fragments, do not write HTML files" in the prompt, return structured content instead of writing a standalone HTML file.

**Fragment output format** (return as a fenced code block with language `fragment-json`):

````fragment-json
{
  "title": "Process Flow Title",
  "description": "1-2 sentence description of what this diagram shows.",
  "bullets": [
    "**Key term 1:** explanation",
    "**Key term 2:** explanation"
  ],
  "diagram_type": "mermaid",
  "diagram_markup": "graph LR\n    A([Start]) --> B[Step 1]\n    B --> C{Decision?}\n    ...\n    style A fill:#f0eeeb,...",
  "suggested_badge": "Flow",
  "sub_tabs": null
}
````

**Fields:**
- `title`: Short descriptive title for the tab heading
- `description`: 1-2 sentences for the text layer below the heading
- `bullets`: Array of markdown bullet points with bolded key terms (for the "rich text" layer per Principle 5)
- `diagram_type`: Always `"mermaid"` for this agent
- `diagram_markup`: Raw Mermaid code (no `<pre>` wrapper). Use `graph LR` per Principle 4 unless parallel branches require `graph TD`. Apply semantic color styles to every node.
- `suggested_badge`: Short label for a badge next to the tab heading (e.g., "Flow", "Pipeline", "Decision Tree")
- `sub_tabs`: If the flow has distinct phases (>6 nodes total), return an array of fragment objects (same schema minus `sub_tabs`) — one per phase. The orchestrator renders these as nested sub-tabs. Otherwise `null`.

**Rules in fragment mode:**
- Do NOT write any HTML files
- Do NOT open anything in the browser
- Do NOT include `<pre>`, `<script>`, or any HTML wrapper — just the raw diagram code
- Still read design-principles.md for color tokens and apply them in Mermaid style directives
- Still follow all Mermaid diagram patterns and semantic color rules from this agent
- Keep diagrams to 4-6 nodes per fragment (split into sub_tabs if more)
- Read the "Diagram Documentation Principles" section in design-principles.md and follow all 8 rules

**Standalone mode** (default, current behavior) is unchanged — when not dispatched in fragment mode, produce full self-contained HTML files as before.
