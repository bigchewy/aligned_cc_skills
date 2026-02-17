# Mockup Generator

## Overview

Generate self-contained HTML mockup files for visualizing UI designs during brainstorming. Each mockup is a standalone HTML file that opens in a browser — no build tools or dev server needed.

**This skill is project-agnostic.** It reads design tokens from `docs/design/design-principles.md` in the current project. Each project defines its own palette, typography, spacing, and component patterns.

## When to Use

- During brainstorming when UI/frontend changes are being designed
- When the user needs to visualize a layout, flow, or component before implementation
- When a design document describes UI changes that would benefit from visual preview

## Setup

**Step 1: Read the project's design principles**

Read `docs/design/design-principles.md` from the project root. Extract:
- Color tokens (hex values and names)
- Typography (font families, weights, sizes)
- Spacing scale
- Border radius system
- Shadow/depth approach
- Component patterns (buttons, cards, inputs, etc.)

If the file doesn't exist, ask the user for design direction before proceeding.

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
  </style>
</head>
<body>
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

## Commit

Mockups are committed to version control as design reference:

```bash
git add docs/mockups/[session-name]/
git commit -m "docs: add mockups for [session-name]"
```
