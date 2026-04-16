# Design: Restructure create-svg-diagram into create-image Router

**Date:** 2026-04-15
**Status:** Draft
**Repo:** `aligned_cc_skills`
**Related:** Planted repo also needs a design-principles.md expansion (separate design doc in that repo)

## Goal

Restructure the `create-svg-diagram` skill into a generic `create-image` router that handles both diagrams and brand icons via keyword-based routing to separate mode files.

### Success Criteria

1. The `create-image` skill routes correctly to icon or diagram mode based on keywords
2. Icon mode reads all existing project icons and the design-principles.md iconography section before generating
3. Icons produced by the skill match the existing brand style (verified against at least two of the five construction dimensions: path count 3-6, opacity uses the 4-tier system)
4. Old `create-svg-diagram` directory is removed; no dangling references remain

### Follow-up (out of scope)

- Update the `create-design-principles` skill to generate construction-grade iconography sections when a project uses custom brand icons instead of an icon library

## Root Cause Context

This design addresses a failure where 15 nature-themed SVG icons were generated that didn't match Planted's brand. Root cause analysis identified three systemic issues:

1. **Wrong skill:** `create-svg-diagram` is architected for diagrams (boxes, arrows, connectors), not icons
2. **No icon skill exists:** No dedicated process for icon creation, so the diagram skill was the closest match
3. **Iconography spec too vague:** Planted's `design-principles.md` describes the vibe but not the construction patterns (addressed in the Planted repo's companion design)

## Architecture

### Router Pattern

Follows the brainstorming skill's architecture: one `SKILL.md` with detection logic, then delegates to `modes/*.md` files.

```
skills/create-image/
  SKILL.md              # Router (~45 lines)
  modes/
    diagram.md          # Current create-svg-diagram content, migrated
    icon.md             # New icon creation process (~70 lines)
```

### Router (SKILL.md)

**Frontmatter:**
```yaml
name: create-image
description: "Use when a diagram, chart, flowchart, icon, or brand visual is
  needed. Routes to diagram mode (charts, flowcharts, matrices, org charts) or
  icon mode (brand icons, custom SVG icons) based on the request."
```

**Routing logic — keyword-based:**
- Icon mode keywords: icon, glyph, symbol, brand icon, custom icon
- Diagram mode keywords: diagram, chart, flowchart, org chart, matrix, visual framework, bell curve, radial, timeline
- If ambiguous: ask one question

**Shared precondition:** Locate the project's design-principles.md. Search order:
1. `brand/guidelines/design-principles.md`
2. `docs/design/design-principles.md` (the original `create-svg-diagram` search path)
3. `~/.claude/docs/design/design-principles.md` (global fallback)

STOP if none found. **Note:** This broadens the search path from the original skill, which only checked option 2. Option 1 is added because projects like Planted store design principles under `brand/guidelines/`.

### Icon Mode (modes/icon.md)

Three-step process, no sub-agents, no critique panel:

**Step 1 — Read existing artifacts (mandatory):**
- Read the design-principles.md Iconography section. If no Iconography section exists, STOP and tell the user to add one (or run `/aligned:create-design-principles`).
- Glob for existing icons in the project's icon directory. Read all of them (for projects with more than 20 icons, read 3 from each category listed in the registry file, up to 15 total).
- Read the icon registry file if one exists (e.g., `ICONS.md`).
- Extract output locations from the design-principles.md Technical Spec table: SVG source directory, React component directory, barrel file path. If the table is missing these fields, ask the user.

**Step 2 — Generate:**
- Analyze construction patterns from existing icons: path count, opacity tiers, shape vocabulary, abstraction level.
- Generate the new icon following the project's spec.
- Apply fallback defaults for any dimension the project's spec is silent on: viewBox 0 0 32 32, fill currentColor, 3-6 paths, 4-tier opacity system.

**Step 3 — Output pipeline (paths from Step 1):**
- Write SVG to the project's icon source directory (extracted from Technical Spec)
- Write React component to the project's component directory (extracted from Technical Spec)
- Add the new component to the barrel file (don't fix pre-existing gaps — just register the new icon)
- Update icon registry if one exists

### Diagram Mode (modes/diagram.md)

Migrated directly from current `skills/create-svg-diagram/SKILL.md`. Content preserved; YAML frontmatter stripped (mode files don't have frontmatter, per brainstorming convention). One change: Step 1 ("Read Design Principles") can reference the router's located path instead of re-searching.

## File Changes

| File | Action |
|------|--------|
| `skills/create-image/SKILL.md` | Create (router) |
| `skills/create-image/modes/diagram.md` | Create (migrated from create-svg-diagram) |
| `skills/create-image/modes/icon.md` | Create (new) |
| `skills/create-svg-diagram/SKILL.md` | Delete |

## Decision Log

### D1: Router pattern over separate skills
**Chosen:** Single `create-image` skill with modes, not two separate skills.
**Alternatives:** Separate `create-brand-icon` and `create-svg-diagram` skills.
**Reasoning:** User preference to avoid skill proliferation. The brainstorming skill provides the structural pattern (one router, multiple modes). The shared logic between icon and diagram modes is thinner than brainstorming's modes (only the design-principles.md lookup is shared, not generation logic or output pipelines), so the router's main value is discoverability, not code reuse.

### D2: Keyword routing, not context detection
**Chosen:** Route based on request keywords only.
**Alternatives:** Detect mode by checking whether the project has an iconography section in design-principles.md.
**Reasoning:** User direction — "if someone says create me an icon, it's an icon." Simple, deterministic, no false positives from project structure sniffing.

### D3: No critique panel for icon generation
**Chosen:** Icon mode has no critique sub-agents.
**Alternatives:** Run a mini design critique after icon generation.
**Reasoning:** Icon correctness is defined by the design-principles.md spec and existing icon analysis (Step 1). The skill front-loads quality by reading all constraints before generating, making post-generation critique redundant. The original failure was caused by insufficient input (reading 3 of 23 icons, using the wrong skill), not insufficient review of the output.

### D4: Project's design-principles.md as authority, skill as fallback
**Chosen:** Icon mode reads the project's spec first, applies skill-internal defaults only for undocumented dimensions.
**Alternatives:** Skill carries its own comprehensive icon style guide.
**Reasoning:** Each project's design-principles.md defines what icons look like for that project. The skill's job is process (what to read, in what order, what to output), not aesthetic prescription.

## Testing Strategy

Manual validation:

1. **Routing — icon mode:** Invoke `/aligned:create-image` with "create a seedling icon." Pass: skill reads `modes/icon.md` and outputs an SVG. Fail: skill reads `modes/diagram.md` or produces diagram boilerplate.
2. **Routing — diagram mode:** Invoke `/aligned:create-image` with "create a flowchart showing the auth flow." Pass: skill reads `modes/diagram.md` and produces a diagram with boxes/arrows. Fail: skill reads `modes/icon.md`.
3. **Icon quality:** Generate an icon in the Planted project. Pass: generated icon uses 3-6 paths, uses opacity values from the 4-tier system (1.0, 0.4-0.55, 0.15-0.3, 0.12-0.15), uses no `<rect>` or `<line>` for primary shapes. Fail: exceeds 8 paths, uses opacity values outside the tier system, uses geometric primitives for primary shapes.
4. **Diagram regression:** Generate a diagram with the migrated mode. Pass: output matches the format of existing diagrams generated by `create-svg-diagram`. Fail: missing boilerplate, wrong element vocabulary, off-palette colors.
