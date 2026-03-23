---
name: kickstart
description: "Scaffold a new project with Aligned conventions: CLAUDE.md, docs structure, eval infrastructure, quality gates, and design principles placeholder."
---

# Kickstart

## Overview

Scaffold a new or existing project with the Aligned development stack conventions. Creates the directory structure, seeds CLAUDE.md with skill invocation points, and sets up eval infrastructure.

**Invocation:** `/aligned:kickstart`

## Phase 1: Gather Context

Ask the user for (use AskUserQuestion, multiple choice where possible):

1. **Project name and one-sentence description**
2. **Any additional context** (linked via `@` symbol — brand guidelines, wireframes, prior art)
3. **Tech stack** (defaults: Next.js + TypeScript + Tailwind)
4. **Target deployment platform** (default: Vercel)
5. **Testing framework** (default: Jest for Node/TS, Vitest for Vite-based, pytest for Python)

## Phase 2: Scaffold Structure

Create the following directory structure (skip directories that already exist):

```
project/
├── .claude/
│   └── settings.json                    # Team settings: auto-enable aligned plugin
├── CLAUDE.md
├── docs/
│   ├── design/
│   │   └── design-principles.md        # Placeholder with instructions
│   ├── architecture.md                 # Empty Mermaid template with section stubs
│   ├── plans/
│   │   └── completed/
│   ├── kanban/
│   │   ├── todo/                       # Individual KB-NNN-slug.md files
│   │   ├── in-progress/
│   │   ├── completed/
│   │   ├── did_not_complete/
│   │   └── .counter                    # Auto-incrementing KB number
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
└── .gitignore                          # Append eval + .claude local patterns if not present
```

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

**e2e/.gitignore:**
```
eval-log.jsonl
.eval-audit-last-run
```

## Phase 3: Seed CLAUDE.md

Generate a project-specific CLAUDE.md including:

- Project overview (from Phase 1 answers)
- Tech stack
- Commands section (test, build, lint, dev — based on detected/specified stack)
- The Iron Rules:
  - Tests first, always (TDD)
  - Error path tests for every mock
  - Verify before claiming done
  - Root cause first, never symptom-fix
- Skill invocation points:
  - `/aligned:brainstorming` — before any creative work
  - `/aligned:writing-plans` — before implementation
  - `/aligned:executing-plans` — to implement a plan
  - `/aligned:finishing-a-development-branch` — to complete work
  - `/aligned:systematic-debugging` — for any bug
  - `/aligned:design-principles` — to define design direction
  - `/aligned:eval-failure-triage` — when evals fail
  - `/aligned:eval-audit` — to check eval coverage
- Architecture doc location: `docs/architecture.md`
- Design principles location: `docs/design/design-principles.md`
- Eval conventions: `e2e/` directory structure
- Kanban board location: `docs/kanban/` (folder-based with individual `KB-NNN-slug.md` files)
- Plans location: `docs/plans/`
- Lessons-learned location: `docs/lessons-learned/`

## Phase 4: Next Steps

Output: "Project scaffolded. Run `/aligned:design-principles` to define the design direction. The placeholder at `docs/design/design-principles.md` needs to be fleshed out."

Commit all scaffolded files:
```bash
git add -A
git commit -m "chore: scaffold project with Aligned conventions"
```
