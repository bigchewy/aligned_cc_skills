---
name: create-image
description: "Generates hand-coded SVG diagrams, charts, flowcharts, brand icons, and decorative illustrations matching the project's design tokens. Use when a visual artifact is needed — charts, flowcharts, matrices, icons, brand graphics, or botanical/decorative illustrations."
---

# Create Image

Router for visual artifact creation. Detects the request type and delegates
to the appropriate mode.

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/create-image/`. See `skills/_shared/resolve-skill-path.md` for rationale.

## Step 1: Detect Mode

Classify the user's request into one of three modes using keyword matching:

**Icon mode** — creating brand icons or custom SVG icons:
- Keywords: icon, glyph, symbol, brand icon, custom icon

**Diagram mode** — creating charts, flowcharts, or visual frameworks:
- Keywords: diagram, chart, flowchart, org chart, matrix, visual framework,
  bell curve, radial, timeline

**Illustration mode** — creating decorative organic/botanical art:
- Keywords: illustration, botanical, decorative, nature art, watermark,
  background art

**If signals are clear:** Auto-route and proceed to Step 2.

**If ambiguous between icon and diagram:** Ask one question: "Are you
looking for a brand icon/symbol or a diagram/chart?"

**If ambiguous between illustration and diagram:** Ask one question: "Are
you looking for a decorative botanical illustration or a data
diagram/chart?"

**If ambiguous between illustration and icon** (e.g., "decorative leaf
symbol," "small botanical glyph"): Ask one question: "Is this a small
functional glyph (UI icon, typically 32x32, gets a React wrapper) or a
larger decorative illustration (atmosphere, background art, no wrapper)?"

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

**If illustration mode:**
Read `{base-directory}/modes/illustration.md` and follow its process.
Pass the resolved design-principles.md path.

**If the mode file cannot be Read, STOP and tell the user the plugin
installation may be incomplete.**
