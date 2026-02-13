---
name: design-principles
description: "Interactive design system discovery with Steve Jobs persona. Two phases: collaborative exploration of the project's design direction, then generation of design-principles.md with tokens, patterns, and anti-patterns."
---

# Design Principles

## Overview

Discover and codify a project's design direction through interactive conversation, then generate `docs/design/design-principles.md` with concrete tokens and component patterns.

**Invocation:** `/aligned:design-principles`

## Phase 1: Interactive Discovery (Steve Jobs Persona)

**Step 1: Load persona and context**

Load the Steve Jobs advisor prompt from `agents/steve-jobs.md` and adopt his persona. Then read project context:
- `CLAUDE.md` (project description, tech stack)
- Any `@`-linked content the user provided (brand guidelines, wireframes, screenshots)
- Existing UI files if the project already has code

**Step 2: Ask discovery questions in Jobs's voice**

Ask these questions one at a time. Skip questions the user already answered via linked context.

1. **The feeling** — "When someone opens this app, what do they feel? Not what they see — what they *feel*. Are we talking warmth? Power? Calm? If you can't describe the feeling in one word, you haven't thought about it hard enough."

2. **The anti-feeling** — "What's the opposite? What should this *never* feel like? Corporate? Cluttered? Playful? The anti-pattern tells me more than the aspiration."

3. **The reference** — "Show me something that gets it right. An app, a website, a magazine — something where you said 'that's what I want.' And tell me what specifically nails it."

4. **Color direction** — "Warm or cool? Bold or quiet? One accent color — what emotion does it carry?" (Multiple choice where possible, but Jobs will have opinions.)

5. **Density** — "Is this a journal or a cockpit? Generous breathing room, or every pixel earns its place?"

Push back on vague answers. "That's not a design direction, that's a mood board. Pick one."

## Phase 2: File Generation

After discovery, drop the Jobs persona and generate `docs/design/design-principles.md`.

The file must include these sections:

### Design Direction
- The one-word feeling
- The anti-feeling
- Reference inspirations

### Color Foundation
- Primary palette (with hex values)
- Neutral scale
- Accent color(s)
- Semantic colors (success, warning, error, info)

### Typography
- Font families (heading, body, monospace)
- Scale (sizes, weights, line heights)

### Spacing
- Base unit (e.g., 4px)
- Scale multipliers

### Border Radius and Depth
- Radius scale
- Shadow/elevation strategy

### Component Patterns
- Buttons (primary, secondary, ghost)
- Cards
- Inputs
- Navigation

### Core Craft Principles

These apply regardless of design direction. This is the quality floor.

To populate this section, read the existing craft principles from the local design-principles skill if available (`~/.claude/skills/design-principles/skill.md`, lines 73-237). Extract these subsections verbatim:
- The 4px Grid
- Symmetrical Padding
- Border Radius Consistency
- Depth & Elevation Strategy
- Card Layouts
- Isolated Controls
- Typography Hierarchy
- Monospace for Data
- Iconography
- Animation
- Contrast Hierarchy
- Color for Meaning Only
- Navigation Context
- Dark Mode Considerations

If the local skill file is not available, include a minimal version:
- Use a 4px grid for all spacing
- Symmetrical padding inside interactive elements
- Consistent border radius per component type
- Maximum 3 shadow depths
- Typography hierarchy: max 3 sizes per context
- Color for meaning, not decoration

### Anti-Patterns

Combine project-specific anti-patterns (derived from Phase 1's "anti-feeling" answer) with universal craft anti-patterns:

Universal anti-patterns:
- Inconsistent spacing (mixing px values arbitrarily)
- Color for decoration rather than meaning
- More than 3 font sizes in one view
- Shadows that don't match light source
- Borders AND shadows on the same element
- Hover states without transitions
- Disabled states that are hard to distinguish

### Four Questions

Every design decision should pass these questions:

1. Does this feel [the-one-word-feeling], or [the-anti-feeling]?
2. Would this look at home in [reference inspiration]?
3. Am I using color for meaning, or for decoration?
4. Is the spacing generous enough for the intended density?

### The Standard

Before shipping any UI change:
- Does it follow the 4px grid?
- Are interactive elements symmetrically padded?
- Does the color serve meaning?
- Is the depth consistent?
- Would the user notice the craft?

## How Other Skills Read This File

- **mockup-generator** reads this file at runtime — extracts tokens and injects into the Tailwind config of each HTML mockup.
- **brainstorming** reads the Four Questions section when evaluating designs.
- The file path `docs/design/design-principles.md` is a convention. No runtime discovery — every skill that cares just reads the known path.

## After Generation

Commit the generated file:

```bash
git add docs/design/design-principles.md
git commit -m "docs: add design principles"
```

Report: "Design principles generated at `docs/design/design-principles.md`. This file is now read by mockup-generator and brainstorming skills."
