---
name: kickstart
description: "Scaffolds a new project with Aligned conventions, directory structure, and CLAUDE.md. Use when starting a new repo or adding Aligned structure to an existing codebase."
---

# Kickstart

## Overview

Scaffold a new or existing project with the Aligned development stack conventions. Creates the directory structure, seeds CLAUDE.md with skill invocation points, and sets up eval infrastructure.

**Invocation:** `/aligned:kickstart`

## Phase 1: Project Type Selection

Before gathering any other context, ask the user:

> **What type of project is this?**
> A. Software (code, tests, builds)
> B. Business (consulting, clients, deliverables)
> C. Personal (knowledge management, life domains)
> D. General (anything else that needs structure)

The answer determines which scaffold path and CLAUDE.md template to use. Store the selection as `project_type`.

## Phase 2: Gather Context

Ask the user for (multiple choice where possible):

**All types ask:**
1. **Project name and one-sentence description**
2. **Any additional context** (linked via `@` symbol — brand guidelines, wireframes, prior art)

**Software additionally asks** (skip for Business, Personal, General):
3. **Tech stack** (defaults: Next.js + TypeScript + Tailwind)
4. **Target deployment platform** (default: Vercel)
5. **Testing framework** (default: Jest for Node/TS, Vitest for Vite-based, pytest for Python)

## Phase 3: Scaffold Structure

Create the directory structure for the selected `project_type`. See `templates/scaffold-structures.md` for the directory trees (Base Structure + Software Additional Structure). Resolve `{base-directory}` using the "Base directory for this skill:" line printed when the skill loads, then read the template file. Create each directory listed, skipping any that already exist.

### File Templates (Software only)

For each file, generate appropriate starter content:

**design-principles.md (placeholder):**
```markdown
# Design Principles

> This file is a placeholder. Run `/aligned:create-design-principles` to define the design direction through an interactive discovery session.
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

Read the template for the selected `project_type` from `templates/<project_type>.md` (resolve `{base-directory}` using the "Base directory for this skill:" line printed at skill load). Available templates:

- `templates/software.md` — for software projects
- `templates/business.md` — for business/consulting workspaces
- `templates/personal.md` — for personal knowledge workspaces
- `templates/general.md` — for general workspaces

Substitute `[project name]`, `[one-sentence description]`, and the Phase 2 tech stack values where placeholders appear. Write the resulting content to `CLAUDE.md` at the project root.

## Phase 5: Global Permission Setup (one-time)

Check whether `~/.claude/settings.json` already contains aligned skill permissions by looking for `Skill(aligned:brainstorming)` in the `permissions.allow` array.

**If already present:** Skip this phase silently — permissions have already been configured.

**If missing:** Read the current `~/.claude/settings.json` (create the file if it doesn't exist). Append the following skill entries to the existing `permissions.allow` array, skipping any that are already present. Preserve all other keys in the file (`permissions.deny`, `enabledPlugins`, etc.):

```json
{
  "permissions": {
    "allow": [
      "Skill(aligned:brainstorming)",
      "Skill(aligned:writing-plans)",
      "Skill(aligned:executing-plans)",
      "Skill(aligned:finishing-a-development-branch)",
      "Skill(aligned:root-cause-analysis)",
      "Skill(aligned:using-git-worktrees)",
      "Skill(aligned:eval-audit)",
      "Skill(aligned:kickstart)",
      "Skill(aligned:use-advisor)",
      "Skill(aligned:use-framework)",
      "Skill(aligned:kanban-resolve)",
      "Skill(aligned:codebase-audit)",
      "Skill(aligned:add-advisor)",
      "Skill(aligned:add-framework)",
      "Skill(aligned:find-potential-advisors)",
      "Skill(aligned:create-design-principles)",
      "Skill(aligned:persona-panel)",
      "Skill(aligned:create-image)"
    ]
  }
}
```

Tell the user: "Set up skill permissions in `~/.claude/settings.json` — you won't get permission prompts for aligned skills."

## Phase 6: Next Steps

Output the appropriate message based on `project_type`, then commit all scaffolded files:

**Software:** "Project scaffolded. Run `/aligned:create-design-principles` to define the design direction. The placeholder at `docs/design/design-principles.md` needs to be fleshed out."

**Business:** "Project scaffolded. Start with `/aligned:brainstorming` to define your first initiative, or fill in the CLAUDE.md guardrails section with confidentiality rules for this workspace."

**Personal:** "Project scaffolded. Start with `/aligned:brainstorming` to define your first initiative, or fill in the guardrails section of CLAUDE.md with any privacy constraints (health data, finances, etc.)."

**General:** "Project scaffolded. Start with `/aligned:brainstorming` to define your first initiative, or fill in the CLAUDE.md sections as you discover what conventions matter for this workspace."

Commit all scaffolded files. Stage each file created or modified during scaffolding explicitly — enumerate them from the list of files written in Phase 3 and Phase 4 (for software: `CLAUDE.md`, `.claude/settings.json`, `.gitignore`, `docs/architecture.md`, `docs/design/design-principles.md`, `docs/kanban/.counter`, `e2e/.gitignore`, any stub directories that contain `.gitkeep`; for business/personal/general: `CLAUDE.md`, `.claude/settings.json`, `.gitignore`).

```bash
git add <each file enumerated above>
git commit -m "chore: scaffold project with Aligned conventions"
```

## Phase 7: What to Try First

After scaffolding and the type-specific next step, output this section to guide the user toward experiencing value immediately:

```
## What to Try First

**Meet an advisor.** Try `/aligned:use-advisor april-dunford` — she'll challenge your positioning with her actual 5 Components methodology. Or try `/aligned:use-advisor rob-walling` for bootstrapped SaaS decision frameworks. The full catalog is in `advisors/registry.yaml`.

**Run a brainstorm.** Try `/aligned:brainstorming` with a real problem you're working on. The system auto-detects whether it's a software or business problem and selects relevant advisors for the critique panel.

**Layer in your context.** Once you've experienced the advisors, add your company context to CLAUDE.md — competitors, buyer personas, strategy docs. The advisors incorporate this context into every conversation, turning general methodology into company-specific guidance.
```

**Dual-level paths** — after the three steps above, add:

```
**Want to go deeper?** Read `skills/brainstorming/SKILL.md` to see how mode detection and advisor auto-selection work. Read `advisors/registry.yaml` for the full advisor catalog with domain metadata.
```

**Stay updated.** Want to know when new advisors and frameworks ship? [Subscribe on Substack](https://bigchewypretzels.substack.com)
