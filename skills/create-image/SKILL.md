---
name: create-image
description: "Use when a diagram, chart, flowchart, icon, or brand visual is
  needed. Routes to diagram mode (charts, flowcharts, matrices, org charts) or
  icon mode (brand icons, custom SVG icons) based on the request."
---

# Create Image

Router for visual artifact creation. Detects the request type and delegates
to the appropriate mode.

## Step 1: Detect Mode

Classify the user's request into one of two modes using keyword matching:

**Icon mode** — creating brand icons or custom SVG icons:
- Keywords: icon, glyph, symbol, brand icon, custom icon

**Diagram mode** — creating charts, flowcharts, or visual frameworks:
- Keywords: diagram, chart, flowchart, org chart, matrix, visual framework,
  bell curve, radial, timeline

**If signals are clear:** Auto-route and proceed to Step 2.

**If ambiguous:** Ask one question: "Are you looking for a brand icon/symbol
or a diagram/chart?"

## Step 2: Locate Design Principles (REQUIRED)

Search for the project's `design-principles.md` in order:
1. `brand/guidelines/design-principles.md`
2. `docs/design/design-principles.md`
3. `~/.claude/docs/design/design-principles.md` (global fallback)

Use Glob to check each path. Use the first match found.

**If none found:** STOP. Tell the user: "No design-principles.md found.
Create one with `/aligned:create-design-principles` or provide at minimum:
background, accent, text colors, and font."

## Step 3: Hand Off to Mode

**If icon mode:**
Read `{base-directory}/modes/icon.md` and follow its process.
Pass the resolved design-principles.md path.

**If diagram mode:**
Read `{base-directory}/modes/diagram.md` and follow its process.
Pass the resolved design-principles.md path.

**If the mode file cannot be Read, STOP and tell the user the plugin
installation may be incomplete.**
