---
model: sonnet
---

# Mockup Generator

## Overview

Generate self-contained HTML mockup files for visualizing UI designs during brainstorming. Each mockup is a standalone HTML file that opens in a browser — no build tools or dev server needed.

**This skill is project-agnostic.** It reads design tokens from `docs/design/design-principles.md` in the current project. Each project defines its own palette, typography, spacing, and component patterns.

## When to Use

- During brainstorming when UI/frontend changes are being designed
- When the user needs to visualize a layout, flow, or component before implementation
- When a design document describes UI changes that would benefit from visual preview

## Setup

**Step 1: Read design principles**

Read `docs/design/design-principles.md` from the project root. If not found, read the global fallback at `~/.claude/docs/design/design-principles.md`. Extract:
- Color tokens (hex values and names)
- Typography (font families, weights, sizes)
- Spacing scale
- Border radius system
- Shadow/depth approach
- Component patterns (buttons, cards, inputs, etc.)

If neither file exists, ask the user for design direction before proceeding.

## Output Structure

Organize mockups by brainstorming session in subfolders:

```
docs/mockups/
  [session-name]/          # descriptive kebab-case name for the brainstorm session
    layout.html            # page structure mockup
    flow.html              # user flow diagram
    component-detail.html  # individual component mockups
```

Not every session needs all three types. Generate what's useful for the design being discussed.

## HTML Template

Every mockup file follows this structure. Replace the placeholder values with tokens from the project's design principles:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Mockup Title]</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          // Inject color tokens from design-principles.md
          colors: {
            // Example:
            // primary: { 50: '#...', 100: '#...', ... },
            // neutral: { 100: '#...', 200: '#...', ... },
            // accent: { 500: '#...', 600: '#...' },
          },
          fontFamily: {
            // Inject font families from design-principles.md
          },
          borderRadius: {
            // Inject border radius tokens
          },
          boxShadow: {
            // Inject shadow tokens
          }
        }
      }
    }
  </script>
  <!-- Load fonts if specified in design-principles.md -->
  <style>
    /* Viewport configuration */
    body {
      /* Read docs/design/design-principles.md for viewport guidance.
         If it specifies a primary viewport (e.g., mobile-first at 375px),
         use that as max-width. If no viewport is specified, use responsive
         layout with no max-width constraint. */
      margin: 0 auto;
      min-height: 100vh;
    }
    /* Mockup context header — sits above the mockup content */
    .mockup-header {
      padding: 16px 20px;
      margin-bottom: 24px;
      border-bottom: 1px solid #e5e5e5;
      font-family: system-ui, -apple-system, sans-serif;
    }
    .mockup-header h1 {
      font-size: 1.25rem;
      font-weight: 500;
      color: #1a1a1a;
      margin: 0 0 2px 0;
    }
    .mockup-header .subtitle {
      font-size: 0.88rem;
      color: #666;
      margin: 0 0 2px 0;
    }
    .mockup-header .context {
      font-size: 0.82rem;
      color: #888;
      margin: 0;
    }
  </style>
</head>
<body>
  <!-- Context header — describes what this mockup shows and which brainstorming session it belongs to -->
  <div class="mockup-header">
    <h1>[Mockup Title]</h1>
    <p class="subtitle">Brainstorming session: [session topic]</p>
    <p class="context">[1-2 sentence description of what this mockup visualizes]</p>
  </div>

  <!-- Mockup content here -->

  <!-- For flow diagrams, use Mermaid -->
  <!--
  <pre class="mermaid">
    graph TD
      A[Start] --> B[Step 1]
      B --> C[Step 2]
  </pre>
  -->

  <script>
    mermaid.initialize({ startOnLoad: true, theme: 'neutral' });
  </script>
</body>
</html>
```

## Guidelines

- **Self-contained:** Every file must work when opened directly in a browser. No imports from the project, no build steps.
- **Viewport:** Match the project's primary viewport. If design-principles.md specifies mobile-first, use 375px max-width. Otherwise, use responsive layout.
- **Design-accurate:** Match the project's actual design tokens — don't approximate. Read the design principles file.
- **Interactive where useful:** Add hover states, click handlers for tabs/accordions, and transitions to make mockups feel real.
- **Mermaid for flows:** Use Mermaid.js (loaded via CDN) for user flow diagrams and state machines. These render in the browser, not just as code blocks.

## After Generating

Open each mockup in the browser for the user to preview:

```bash
open docs/mockups/[session-name]/[file].html
```

## Design Critique (Steve Jobs persona, conditional)

If `docs/design/design-principles.md` exists in the project, load `agents/steve-jobs.md` and adopt the Steve Jobs persona. For each generated mockup, deliver a 2-3 sentence critique in Jobs's voice before presenting to the user: what's insanely great, what's not good enough, what needs to change. This happens per-mockup, not as a summary at the end.

If design-principles.md does not exist, skip the persona critique.

## Fragment Mode

When dispatched by the session-document-generator with the phrase "Return fragments, do not write HTML files" in the prompt, return structured content instead of writing a standalone HTML file.

**Fragment output format** (return as a fenced code block with language `fragment-json`):

```fragment-json
{
  "title": "Component Mockup Title",
  "description": "1-2 sentence description of what this mockup shows.",
  "bullets": [
    "**Key term 1:** explanation",
    "**Key term 2:** explanation"
  ],
  "diagram_type": "html",
  "diagram_markup": "<div class=\"mockup-fragment\">...</div>",
  "suggested_badge": "Mockup",
  "sub_tabs": null
}
```

**Fields:**
- `title`: Short descriptive title for the tab heading
- `description`: 1-2 sentences for the text layer below the heading
- `bullets`: Array of markdown bullet points with bolded key terms (for the "rich text" layer per Principle 5)
- `diagram_type`: Always `"html"` for this agent
- `diagram_markup`: Self-contained HTML fragment. Include inline styles or Tailwind classes. Do NOT include `<html>`, `<head>`, `<body>`, or `<script src="tailwind">` tags — the orchestrator's document already loads Tailwind. The fragment should work when inserted into a `<div>` container.
- `suggested_badge`: Short label for a badge next to the tab heading (e.g., "Mockup", "UI", "Layout")
- `sub_tabs`: If the UI has distinct views or states (e.g., different pages, empty state vs. populated), return an array of fragment objects (same schema minus `sub_tabs`). Otherwise `null`.

**Rules in fragment mode:**
- Do NOT write any HTML files
- Do NOT open anything in the browser
- Do NOT include full HTML document structure — return only the content fragment
- Still read design-principles.md for design tokens
- Still follow all mockup guidelines from this agent
- Read the "Diagram Documentation Principles" section in design-principles.md and follow all 8 rules

**Standalone mode** (default, current behavior) is unchanged — when not dispatched in fragment mode, produce full self-contained HTML files as before.

**Do NOT commit.** The brainstorming skill commits all visual artifacts together with the design document after the critique round completes. Committing here would capture a pre-critique draft.
