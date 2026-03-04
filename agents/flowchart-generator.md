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
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #fafafa;
      margin: 0;
      padding: 40px;
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
    .flowchart-container {
      background: white;
      border: 1px solid #e5e5e5;
      border-radius: 12px;
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
      color: #666;
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

        style A fill:#48bb78,stroke:#38a169,color:#fff
        style F fill:#48bb78,stroke:#38a169,color:#fff
        style B fill:#4299e1,stroke:#3182ce,color:#fff
        style D fill:#4299e1,stroke:#3182ce,color:#fff
        style E fill:#4299e1,stroke:#3182ce,color:#fff
        style C fill:#f59e0b,stroke:#d97706,color:#fff
    </pre>
  </div>

  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#48bb78"></div>Start / End</div>
    <div class="legend-item"><div class="legend-dot" style="background:#4299e1"></div>Process</div>
    <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>Decision</div>
    <div class="legend-item"><div class="legend-dot" style="background:#9f7aea"></div>Data / I/O</div>
  </div>

  <script>
    mermaid.initialize({
      startOnLoad: true,
      theme: 'base',
      themeVariables: {
        fontFamily: 'system-ui, -apple-system, sans-serif',
        fontSize: '14px',
        lineColor: '#666',
        primaryColor: '#4299e1',
        primaryTextColor: '#fff',
        primaryBorderColor: '#3182ce'
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
style A fill:#48bb78,stroke:#38a169,color:#fff   %% Start/End — green
style B fill:#4299e1,stroke:#3182ce,color:#fff   %% Process — blue
style C fill:#f59e0b,stroke:#d97706,color:#fff   %% Decision — orange
style D fill:#9f7aea,stroke:#805ad5,color:#fff   %% Data/IO — purple
style E fill:#e53e3e,stroke:#c53030,color:#fff   %% Error — red
```

## Semantic Color System

| Type | Color | Hex | Mermaid fill |
|------|-------|-----|-------------|
| Start/End | Green | #48bb78 | `fill:#48bb78,stroke:#38a169,color:#fff` |
| Process | Blue | #4299e1 | `fill:#4299e1,stroke:#3182ce,color:#fff` |
| Decision | Orange | #f59e0b | `fill:#f59e0b,stroke:#d97706,color:#fff` |
| Data/IO | Purple | #9f7aea | `fill:#9f7aea,stroke:#805ad5,color:#fff` |
| External/Error | Red | #e53e3e | `fill:#e53e3e,stroke:#c53030,color:#fff` |

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
