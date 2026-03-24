# Kickstart Expansion: Non-Technical Project Types

**Date:** 2026-03-24
**Status:** Draft
**Mockups:** docs/mockups/kickstart-expansion.html

## Problem

The kickstart skill only scaffolds software projects. The user frequently creates non-technical folders (business/consulting, personal, general) that need consistent structure and CLAUDE.md files but not code-centric scaffolding (e2e/, eslint-rules/, tech stack questions).

## Success Criteria

1. Running `/aligned:kickstart` in an empty directory and selecting any of the 4 types produces a valid scaffold with correct CLAUDE.md content for that type.
2. Non-software types scaffold in under 30 seconds with no tech stack questions asked.
3. All CLAUDE.md templates reference `~/.claude/about-me.md` in their reading priority.

## Design

### Phase 1: Project Type Selection (NEW)

Before gathering any other context, ask:

> **What type of project is this?**
> A. Software (code, tests, builds)
> B. Business (consulting, clients, deliverables)
> C. Personal (knowledge management, life domains)
> D. General (anything else that needs structure)

The answer determines which scaffold path and CLAUDE.md template to use.

### Phase 2: Gather Context (MODIFIED)

**All types ask:**
1. Project name and one-sentence description
2. Any additional context (linked via `@` symbol)

**Software additionally asks** (existing behavior, unchanged):
3. Tech stack (defaults: Next.js + TypeScript + Tailwind)
4. Target deployment platform (default: Vercel)
5. Testing framework (default: Jest/Vitest/pytest)

**Business, Personal, General** skip questions 3-5.

### Phase 3: Scaffold Structure (MODIFIED)

**Base structure (ALL types):**
```
project/
├── .claude/
│   └── settings.json          # Enable aligned plugin
├── CLAUDE.md
└── docs/
    └── lessons-learned/
```

**Software additionally creates** (existing behavior — note: the existing SKILL.md has a `done/` vs `completed/` inconsistency in kanban dirs; this design uses `done/` to match the mkdir commands):
```
├── docs/
│   ├── design/
│   │   └── design-principles.md
│   ├── architecture.md
│   ├── plans/
│   │   └── completed/
│   ├── kanban/
│   │   ├── todo/
│   │   ├── in-progress/
│   │   ├── done/
│   │   ├── did_not_complete/
│   │   └── .counter
│   ├── mockups/
│   └── lessons-learned/
│       └── completed/
├── e2e/
│   ├── scenarios/
│   ├── fixtures/
│   │   └── profiles/
│   ├── eval-config.ts
│   ├── eval-runner.ts
│   └── .gitignore
├── scripts/
├── eslint-rules/
└── .gitignore
```

**Business, Personal, General** get no additional folders beyond the base. Structure is flat — the user creates project-level folders at root as needed.

### Phase 4: Seed CLAUDE.md (MODIFIED)

All templates use a consistent 6-section structure. Content varies by type.

#### Section Structure

1. **Project Identity** — what this is, who it's for
2. **Folder Map** — where files go, naming conventions
3. **Reading Priority** — what Claude should front-load
4. **Communication Preferences** — output style, tone, format
5. **Guardrails** — sensitivity, privacy, constraints
6. **Workflows** — skill/agent triggers

#### Software Template (restructured into 6-section format; adds NEW `about-me.md` reading priority reference)

1. **Identity**: Project overview, tech stack
2. **Folder map**: Full directory structure (docs/, e2e/, scripts/, etc.), file locations (architecture, design principles, kanban, plans, lessons-learned)
3. **Reading priority**: CLAUDE.md → `~/.claude/about-me.md` (NEW) → docs/architecture.md
4. **Communication**: Commands section (test, build, lint, dev)
5. **Guardrails**: Iron Rules (TDD, error path tests, verify before claiming, root cause first)
6. **Workflows**: Skill invocation points (brainstorming, writing-plans, executing-plans, finishing-a-development-branch, systematic-debugging, design-principles, eval-failure-triage, eval-audit)

#### Business Template

1. **Identity**: "This is a business/consulting workspace for [project name]. [one-sentence description]."
2. **Folder map**: `docs/` for deliverables and reference material. `docs/lessons-learned/` for retrospectives. Project folders live at root.
3. **Reading priority**: This file → `~/.claude/about-me.md` → relevant project folders
4. **Communication**: Placeholder — "Define tone, format, and output style preferences here."
5. **Guardrails**: Placeholder — "Define confidentiality rules and client sensitivity constraints here."
6. **Workflows**: Seeded with business skill pipeline — `/aligned:business-brainstorming` before any business work, `/aligned:business-write-plan` for planning deliverables, `/aligned:business-executing` for execution, `/aligned:business-diagnosis` when something isn't working. Plus content skills: `/aligned:generate-one-pager` for prospect materials, `/aligned:generate-blog-post` for thought leadership.

#### Personal Template

1. **Identity**: "This is a personal knowledge workspace for [project name]. [one-sentence description]."
2. **Folder map**: Same as business.
3. **Reading priority**: Same as business.
4. **Communication**: Defaults to "Direct, informal. Skip formalities."
5. **Guardrails**: Placeholder — "Define privacy constraints here. Consider: health data, financial data, personal relationships."
6. **Workflows**: Placeholder — "Define triggers here. Examples: periodic reviews, check-ins."

#### General Template

1. **Identity**: "This is a workspace for [project name]. [one-sentence description]."
2. **Folder map**: `docs/` and `docs/lessons-learned/` only.
3. **Reading priority**: This file → `~/.claude/about-me.md`
4. **Communication**: Empty placeholder.
5. **Guardrails**: Empty placeholder.
6. **Workflows**: Empty placeholder.

### Phase 5: Global About-Me Check (NEW)

After scaffolding, check whether `~/.claude/about-me.md` exists. Create `~/.claude/` first if the directory doesn't exist.

- **If missing**: Ask "No global about-me found at `~/.claude/about-me.md`. Want to create one now?" If yes, scaffold a template:
  ```markdown
  # About Me

  ## Role & Identity
  <!-- Who you are, what you do -->

  ## Expertise
  <!-- Your domain knowledge and experience -->

  ## Methodology
  <!-- How you approach work, key frameworks -->

  ## Communication Style
  <!-- How you prefer Claude to communicate -->
  ```
  Also suggest adding a reading priority reference to `~/.claude/CLAUDE.md` (do not modify without confirmation). If `~/.claude/` cannot be created (permission failure), skip with a note and continue.

- **If exists**: Do nothing. CLAUDE.md templates already reference it.

### Phase 6: Next Steps (MODIFIED)

**Software**: "Project scaffolded. Run `/aligned:design-principles` to define the design direction." (existing behavior)

**Business**: "Project scaffolded. Start with `/aligned:business-brainstorming` to define your first initiative, or fill in the CLAUDE.md guardrails section with confidentiality rules for this workspace."

**Personal**: "Project scaffolded. Fill in the guardrails section of CLAUDE.md with any privacy constraints (health data, finances, etc.), then start working."

**General**: "Project scaffolded. Fill in the CLAUDE.md sections as you discover what conventions matter for this workspace."

Commit all scaffolded files.

### Skill Metadata Update

Update frontmatter description:
```yaml
---
name: kickstart
description: "Scaffold a new project with Aligned conventions. Supports software, business, personal, and general project types with appropriate structure and CLAUDE.md templates."
---
```

## Testing Strategy

**Test file:** `e2e/scenarios/kickstart-expansion.test.ts` (new)

Tests to write:
1. **Type selection routing** — each of the 4 types triggers the correct scaffold path (no tech stack questions for non-software)
2. **Base structure (all types)** — verify `CLAUDE.md`, `.claude/settings.json`, `docs/`, `docs/lessons-learned/` exist after scaffold
3. **Software additions** — verify software-specific dirs (e2e/, scripts/, eslint-rules/, kanban/) are created only for software type
4. **CLAUDE.md content per type** — verify each template has the correct 6 sections with type-appropriate content (business has business skills in workflows, personal has privacy hints in guardrails, etc.)
5. **About-me check — missing** — verify prompt is shown when `~/.claude/about-me.md` doesn't exist
6. **About-me check — exists** — verify no prompt when file already exists
7. **About-me check — permission failure** — verify graceful skip when `~/.claude/` can't be created
8. **Idempotency** — running kickstart in a directory with existing files doesn't overwrite them (existing SKILL.md behavior, verify preserved)

## Decision Log

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Ask project type every time (no auto-detection) | User preference for explicit control |
| 2 | Flat folder structure for non-technical types | User is removing `domains/` nesting from existing vaults |
| 3 | Global identity lives at `~/.claude/about-me.md` | Identity doesn't change between folders. Named `about-me.md` (not `profile.md`) to avoid collision with existing `claude-profile` skill which handles account switching. |
| 4 | No content pipeline add-on | Superseded by existing skills (`kanban-resolve`, etc.) |
| 5 | No frameworks folder | Frameworks live in the skills plugin now |
| 6 | `lessons-learned/` under `docs/` for all types | User preference for consistency, nested under docs |
| 7 | 6-section CLAUDE.md structure for all types | Derived from analysis of 18 existing CLAUDE.md files across user's Obsidian vaults plus external practitioner patterns (Stockton, HumanLayer, Anthropic docs) |
| 8 | Non-technical templates use placeholders with hints | Lean scaffolding, user fills in as needed. Business template pre-seeds workflows with actual business skill pipeline rather than leaving fully empty. |
| 9 | Keep Business/Personal/General as separate types | Types may evolve differently over time (e.g., business gains client-specific patterns, personal gains review workflows). Cost of maintaining three templates is low. |
