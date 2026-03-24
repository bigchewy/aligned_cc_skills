---
name: kickstart
description: "Scaffold a new project with Aligned conventions. Supports software, business, personal, and general project types with appropriate structure and CLAUDE.md templates."
---

# Kickstart

## Overview

Scaffold a new or existing project with the Aligned development stack conventions. Creates the directory structure, seeds CLAUDE.md with skill invocation points, and sets up eval infrastructure.

**Invocation:** `/aligned:kickstart`

## Phase 1: Project Type Selection

Before gathering any other context, ask the user (use AskUserQuestion):

> **What type of project is this?**
> A. Software (code, tests, builds)
> B. Business (consulting, clients, deliverables)
> C. Personal (knowledge management, life domains)
> D. General (anything else that needs structure)

The answer determines which scaffold path and CLAUDE.md template to use. Store the selection as `project_type`.

## Phase 2: Gather Context

Ask the user for (use AskUserQuestion, multiple choice where possible):

**All types ask:**
1. **Project name and one-sentence description**
2. **Any additional context** (linked via `@` symbol — brand guidelines, wireframes, prior art)

**Software additionally asks** (skip for Business, Personal, General):
3. **Tech stack** (defaults: Next.js + TypeScript + Tailwind)
4. **Target deployment platform** (default: Vercel)
5. **Testing framework** (default: Jest for Node/TS, Vitest for Vite-based, pytest for Python)

## Phase 3: Scaffold Structure

Create the following directory structure (skip directories that already exist).

### Base Structure (ALL types)

```
project/
├── .claude/
│   └── settings.json          # Enable aligned plugin
├── .gitignore                 # .claude personal overrides (settings.local.json, CLAUDE.local.md)
├── CLAUDE.md
└── docs/
    └── lessons-learned/
```

### Software Additionally Creates (software type only)

```
├── docs/
│   ├── design/
│   │   └── design-principles.md        # Placeholder with instructions
│   ├── architecture.md                 # Empty Mermaid template with section stubs
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
│   ├── eval-config.ts                  # Starter eval configuration
│   ├── eval-runner.ts                  # Starter eval runner
│   └── .gitignore                      # eval-log.jsonl, .eval-audit-last-run
├── scripts/
├── eslint-rules/
└── .gitignore                          # Append eval patterns to the base .gitignore
```

**Business, Personal, General** get no additional folders beyond the base. Structure is flat — the user creates project-level folders at root as needed.

### File Templates (Software only)

For each file, generate appropriate starter content:

**design-principles.md (placeholder):**
```markdown
# Design Principles

> This file is a placeholder. Run `/aligned:design-principles` to define the design direction through an interactive discovery session.
```

**architecture.md (template):**
```markdown
# Architecture

## System Overview
<!-- High-level Mermaid diagram here -->

## Data Flow
<!-- Request/response flow diagram -->

## Module Dependencies
<!-- Module relationship diagram -->

## Database Schema
<!-- Schema diagram if applicable -->
```

**Kanban directory structure:**
Create the following directories and file:
```bash
mkdir -p docs/kanban/todo docs/kanban/in-progress docs/kanban/done docs/kanban/did_not_complete
echo "1" > docs/kanban/.counter
```

**e2e/.gitignore:**
```
eval-log.jsonl
.eval-audit-last-run
```

### Settings (ALL types)

**.claude/settings.json (create or merge):**

If `.claude/settings.json` does not exist, create it:
```json
{
  "enabledPlugins": {
    "aligned": true
  }
}
```

If `.claude/settings.json` already exists, read it and add the `enabledPlugins` key (preserving all existing settings). If `enabledPlugins` already exists, merge `"aligned": true` into it.

Also ensure `.claude/settings.local.json` and `.claude/CLAUDE.local.md` are in the project's `.gitignore` (these are per-developer personal overrides that should never be committed).

## Phase 4: Seed CLAUDE.md

Generate a project-specific CLAUDE.md using the template for the selected `project_type`. All templates use a consistent 6-section structure:

1. **Project Identity** — what this is, who it's for
2. **Folder Map** — where files go, naming conventions
3. **Reading Priority** — what Claude should front-load
4. **Communication Preferences** — output style, tone, format
5. **Guardrails** — sensitivity, privacy, constraints
6. **Workflows** — skill/agent triggers

### Software Template

**Section 1 — Project Identity:**
- Project name and one-sentence description (from Phase 2)
- Tech stack (from Phase 2)

**Section 2 — Folder Map:**
- Full directory structure: docs/ (architecture, design principles, kanban, plans, mockups, lessons-learned), e2e/, scripts/, eslint-rules/
- File locations: `docs/architecture.md`, `docs/design/design-principles.md`, `docs/kanban/`, `docs/plans/`, `docs/lessons-learned/`

**Section 3 — Reading Priority:**
```markdown
## Reading Priority

1. This file (CLAUDE.md)
2. `~/.claude/about-me.md` — global identity and preferences
3. `docs/architecture.md` — system structure
```

**Section 4 — Communication Preferences:**
- Commands section (test, build, lint, dev — based on detected/specified stack from Phase 2)

**Section 5 — Guardrails (Iron Rules):**
- Tests first, always (TDD)
- Error path tests for every mock
- Verify before claiming done
- Root cause first, never symptom-fix

**Section 6 — Workflows:**
```markdown
## Workflows

- `/aligned:brainstorming` — before any creative work
- `/aligned:writing-plans` — before implementation
- `/aligned:executing-plans` — to implement a plan
- `/aligned:finishing-a-development-branch` — to complete work
- `/aligned:systematic-debugging` — for any bug
- `/aligned:design-principles` — to define design direction
- `/aligned:eval-failure-triage` — when evals fail
- `/aligned:eval-audit` — to check eval coverage
```

### Business Template

**Section 1 — Project Identity:**
```markdown
This is a business/consulting workspace for [project name]. [one-sentence description].
```

**Section 2 — Folder Map:**
```markdown
## Folder Map

- `docs/` — deliverables and reference material
- `docs/lessons-learned/` — retrospectives
- Project folders live at root
```

**Section 3 — Reading Priority:**
```markdown
## Reading Priority

1. This file (CLAUDE.md)
2. `~/.claude/about-me.md` — global identity and preferences
3. Relevant project folders
```

**Section 4 — Communication Preferences:**
```markdown
## Communication Preferences

Define tone, format, and output style preferences here.
```

**Section 5 — Guardrails:**
```markdown
## Guardrails

Define confidentiality rules and client sensitivity constraints here.
```

**Section 6 — Workflows:**
```markdown
## Workflows

- `/aligned:business-brainstorming` — before any business work
- `/aligned:business-write-plan` — for planning deliverables
- `/aligned:business-executing` — for execution
- `/aligned:business-diagnosis` — when something isn't working
- `/aligned:generate-one-pager` — for prospect materials
- `/aligned:generate-blog-post` — for thought leadership
```

### Personal Template

**Section 1 — Project Identity:**
```markdown
This is a personal knowledge workspace for [project name]. [one-sentence description].
```

**Section 2 — Folder Map:**
```markdown
## Folder Map

- `docs/` — deliverables and reference material
- `docs/lessons-learned/` — retrospectives
- Project folders live at root
```

**Section 3 — Reading Priority:**
```markdown
## Reading Priority

1. This file (CLAUDE.md)
2. `~/.claude/about-me.md` — global identity and preferences
3. Relevant project folders
```

**Section 4 — Communication Preferences:**
```markdown
## Communication Preferences

Direct, informal. Skip formalities.
```

**Section 5 — Guardrails:**
```markdown
## Guardrails

Define privacy constraints here. Consider: health data, financial data, personal relationships.
```

**Section 6 — Workflows:**
```markdown
## Workflows

Define triggers here. Examples: periodic reviews, check-ins.
```

## Phase 6: Next Steps

Output: "Project scaffolded. Run `/aligned:design-principles` to define the design direction. The placeholder at `docs/design/design-principles.md` needs to be fleshed out."

Commit all scaffolded files:
```bash
git add -A
git commit -m "chore: scaffold project with Aligned conventions"
```
