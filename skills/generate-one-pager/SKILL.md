---
name: generate-one-pager
description: Generate a branded one-pager or battle card for a specified audience using brand context
---

# Generate One-Pager

> **Status:** Placeholder — not yet implemented. **STOP.** Do not execute the steps below. Tell the user this skill is under construction.

Generate a branded one-pager or battle card for a specified audience.

## Planned Behavior

**Halt guard:** First, check if `brand/CLAUDE.md` exists at the project root. If not, halt with:
> No brand context found. This skill requires a `brand/` directory with a `CLAUDE.md` manifest at the project root. See the brand context contract in the Aligned plugin README.

1. Read `brand/CLAUDE.md` to find available assets
2. Load the audience profile matching the user's target
3. Load `brand-voice.md`, `competitive.md`, and `proof-points.md`
4. Load the one-pager template from `brand/templates/one-pager/`
5. Generate content using brand context
6. Output a markdown one-pager draft for review
7. Render output via context-aware delegation (same pattern as generate-deck Step 4b): produce a design brief, then delegate to the PowerPoint add-in (if available), Claude Code `pptx` skill (if in CLI), or fall back to markdown
