---
name: kickstart
description: "Scaffolds a new project with Aligned conventions, directory structure, and CLAUDE.md. Use when starting a new repo or adding Aligned structure to an existing codebase."
---

# Kickstart

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/kickstart/`. See `skills/_shared/resolve-skill-path.md` for rationale.

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

Create the directory structure for the selected `project_type`. Read `{base-directory}/templates/scaffold-structures.md` for the directory trees (Base Structure + Software Additional Structure). Create each directory listed, skipping any that already exist.

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

**Kanban board generator + post-commit hook (Software only):**

Copy two tracked files from the skill's templates into the project, then wire up the git hook so the HTML view auto-regenerates whenever a Kanban item is committed:

```bash
mkdir -p scripts/hooks
cp {base-directory}/templates/scripts/generate-kanban-board.cjs scripts/generate-kanban-board.cjs
cp {base-directory}/templates/scripts/hooks/post-commit scripts/hooks/post-commit
chmod +x scripts/hooks/post-commit
```

If the project is already a git repo (`.git/` exists), redirect git's hooks to the tracked directory so the post-commit hook fires automatically when `docs/kanban/*.md` changes in a commit:

```bash
git config core.hooksPath scripts/hooks
```

If `.git/` does not exist yet, skip the `git config` line and tell the user to run it themselves after `git init`.

Append `docs/kanban/board.html` to the project's `.gitignore` — the HTML view is regenerated from the markdown and should not be tracked.

Generate the initial board once so the user has something to open:

```bash
node scripts/generate-kanban-board.cjs
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

Read the template for the selected `project_type` from `{base-directory}/templates/<project_type>.md`. Available templates:

- `templates/software.md` — for software projects
- `templates/business.md` — for business/consulting workspaces
- `templates/personal.md` — for personal knowledge workspaces
- `templates/general.md` — for general workspaces

Substitute `[project name]`, `[one-sentence description]`, and the Phase 2 tech stack values where placeholders appear. Write the resulting content to `CLAUDE.md` at the project root.

## Phase 5: Global Permission Setup (one-time)

Check whether `~/.claude/settings.json` already contains aligned skill permissions by looking for `Skill(aligned:brainstorming)` in the `permissions.allow` array.

**If already present:** Skip this phase silently — permissions have already been configured.

**If missing:** Enumerate the aligned plugin's skills at runtime and append one `Skill(aligned:<name>)` entry per skill to `permissions.allow`. Do not hardcode the list — it must derive from the filesystem so new skills are picked up automatically.

1. Resolve the plugin root per `skills/_shared/resolve-skill-path.md` (the "Plugin root" and "Edge case: multiple plugin installs" sections). In short: Glob `$HOME` for `**/.claude-plugin/plugin.json`; the plugin root is the parent directory of the matched `.claude-plugin/` dir. On multiple matches, follow the canonical tiebreaker sequence from that file (prefer `name: aligned` + sibling `skills/<skill-name>/SKILL.md`; then prefer matches under CWD or ancestors; if still ambiguous, stop and ask).
2. Glob `<plugin-root>/skills/*/SKILL.md` to discover all skill directories. The skill name is the parent directory name of each matched `SKILL.md`.
3. Filter out any directory starting with `_` (e.g., `_shared/`) — these are shared reference directories, not skills.
4. Sort the resulting names alphabetically for deterministic output.
5. Read `~/.claude/settings.json` (create the file with `{"permissions":{"allow":[],"deny":[]}}` if it doesn't exist). Preserve all existing keys (`permissions.deny`, `enabledPlugins`, etc.) and all existing `allow` entries.
6. For each enumerated skill, append `Skill(aligned:<name>)` to `permissions.allow` if not already present.
7. Write the file back as valid JSON (2-space indent, trailing newline).

Tell the user: "Set up skill permissions for N aligned skills in `~/.claude/settings.json` — you won't get permission prompts." (where N is the count of skills enumerated).

## Phase 6: Next Steps

Output the appropriate message based on `project_type`, then commit all scaffolded files:

**Software:** "Project scaffolded. Run `/aligned:create-design-principles` to define the design direction. The placeholder at `docs/design/design-principles.md` needs to be fleshed out."

**Business:** "Project scaffolded. Start with `/aligned:brainstorming` to define your first initiative, or fill in the CLAUDE.md guardrails section with confidentiality rules for this workspace."

**Personal:** "Project scaffolded. Start with `/aligned:brainstorming` to define your first initiative, or fill in the guardrails section of CLAUDE.md with any privacy constraints (health data, finances, etc.)."

**General:** "Project scaffolded. Start with `/aligned:brainstorming` to define your first initiative, or fill in the CLAUDE.md sections as you discover what conventions matter for this workspace."

Commit all scaffolded files. Stage each file created or modified during scaffolding explicitly — enumerate them from the list of files written in Phase 3 and Phase 4 (for software: `CLAUDE.md`, `.claude/settings.json`, `.gitignore`, `docs/architecture.md`, `docs/design/design-principles.md`, `docs/kanban/.counter`, `scripts/generate-kanban-board.cjs`, `scripts/hooks/post-commit`, `e2e/.gitignore`, any stub directories that contain `.gitkeep`; for business/personal/general: `CLAUDE.md`, `.claude/settings.json`, `.gitignore`).

```bash
git add <each file enumerated above>
git commit -m "chore: scaffold project with Aligned conventions"
```

## Phase 7: What to Try First

After scaffolding and the type-specific next step, output this section to guide the user toward experiencing value immediately:

```
## What to Try First

**Meet an advisor.** Try `/aligned:use-advisor april-dunford` — she'll challenge your positioning with her actual 5 Components methodology. Or try `/aligned:use-advisor rob-walling` for bootstrapped SaaS decision frameworks. The full catalog is in `advisors/registry.yaml`.

**Run a brainstorm.** Try `/aligned:brainstorming` with a real problem you're working on. The router auto-routes across five modes (software, business, research, authoring, roadmap) and selects relevant advisors for the critique panel.

**Layer in your context.** Once you've experienced the advisors, add your company context to CLAUDE.md — competitors, buyer personas, strategy docs. The advisors incorporate this context into every conversation, turning general methodology into company-specific guidance.
```

**Dual-level paths** — after the three steps above, add:

```
**Want to go deeper?** Read `skills/brainstorming/SKILL.md` to see how mode detection and advisor auto-selection work. Read `advisors/registry.yaml` for the full advisor catalog with domain metadata.
```
