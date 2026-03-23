---
name: create-svg-diagram
description: "Use when a diagram, chart, flowchart, org chart, matrix, or visual framework is needed for presentations, documentation, or slide decks in a repo with a design-principles file."
---

# Create SVG Diagram

Hand-coded SVG diagrams matching a project's design tokens from the local repo's `docs/design/design-principles.md`.

## Step 1: Read Design Principles (REQUIRED)

**Read `docs/design/design-principles.md` in the current repo before creating any SVG.** If not found, read the global fallback at `~/.claude/docs/design/design-principles.md`.

Extract: background, foreground, secondary, accent, border, muted colors + font stack + border radii.

**If neither file exists:** STOP. Ask the user for a design-principles file or at minimum: background, accent, text colors, and font. Never generate without design tokens.

## Step 2: Read Existing Diagrams

Read 2-3 existing SVGs in the output directory for style consistency. **If no SVGs exist yet**, follow the element vocabulary and patterns below as your baseline.

## SVG Boilerplate

All `{token}` placeholders below must be replaced with actual hex values from design-principles.md.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H" width="W" height="H">
  <defs>
    <style>text { font-family: {font-sans}; }</style>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="{accent}"/>
    </marker>
  </defs>
  <rect width="W" height="H" fill="{background}"/>
  <!-- content -->
</svg>
```

## Element Vocabulary

| Element | SVG Pattern |
|---------|------------|
| **Primary box** | `fill="{muted}" stroke="{border}" stroke-width="1" rx="{radius-sm}"` |
| **Secondary box** | `fill="white" stroke="{border}" stroke-width="1" rx="{radius-sm}"` |
| **Emphasized box** | `fill="white" stroke="{foreground}" stroke-width="1.5" rx="{radius-sm}"` |
| **Dot on curve** | `<circle r="7" fill="white" stroke="{accent}" stroke-width="2.5"/>` |
| **Arrow connector** | `stroke="{accent}" stroke-width="2" marker-end="url(#arrowhead)"` |
| **Pennant arrow** | `<polygon points="cx-15,cy+25 cx,cy cx+15,cy+25" fill="{accent}"/>` — apex at (cx,cy) |
| **Title bar** | `<rect fill="{foreground}"/>` with white text |
| **Tagline** | Centered, `fill="{secondary}"`, 14px |

### Text Centering in Boxes

Box at `(x, y)` with height `h`:
- **Single line:** `text y = box_y + (h/2) + 4`
- **Two lines:** `line1 y = box_y + (h/2) - 4`, `line2 y = box_y + (h/2) + 12`

Use stacked `<text>` elements with computed y values.

## Layout Patterns

- **Horizontal flow** (1000-1200 x 300-400): Boxes with arrow connectors. Sequences, pipelines.
- **Vertical stack** (900-1000 x 800-1000): Layered rectangles with pennant arrows. Hierarchies.
- **2x2 grid** (800-1100 x 700-820): Four quadrants with axis labels. Matrices.
- **Bell curve** (1000 x 540-580): Cubic bezier path with labeled dots. Lifecycle/progression.
- **Radial circle** (1200-1400 x 1000-1100): Items around center using trig. For N items at radius R from (cx,cy), item i (0-indexed, clockwise from 12 o'clock): `x = cx + R*sin(i*360/N*π/180)`, `y = cy - R*cos(i*360/N*π/180)`. Tuck secondary boxes behind primary (~8px overlap); above-center items get secondary above, below-center get secondary below.

## Paired Diagrams (Animation)

For sequential "reveal" SVGs: identical `viewBox`, identical shared element coordinates. Second SVG = first + additions only. Name with `N.1` suffix.

## Z-Order & Conventions

Draw order: background rect → grid/axes → connecting lines → behind boxes → front boxes → text/labels. Comment every section: `<!-- Section Name -->`. File naming: `N-descriptive-name.svg`.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Generating without design-principles | STOP. Read the file or ask user. |
| Radial overlap at 12/6 o'clock | Shift items ±25px along axis |
| Text wider than box | Split to two lines, reduce font 1px |
| Lines visible through boxes | Draw lines before boxes in source |
| Off-palette colors | Only use tokens from design-principles.md |
| Bare `&` in text | Use `&amp;` (XML entity encoding) |
| Duplicate marker IDs in paired SVGs | Use unique IDs per file if embedding together |
