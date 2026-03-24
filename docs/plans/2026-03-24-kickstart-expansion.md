# Kickstart Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Expand the kickstart skill to scaffold software, business, personal, and general project types with type-appropriate CLAUDE.md templates and a global about-me identity check.

**Source Design Doc:** `docs/plans/2026-03-24-kickstart-expansion-design.md`

**Mockups:** `docs/mockups/kickstart-expansion.html`

**Architecture:** The kickstart skill is a single SKILL.md file (150 lines) that guides Claude through a multi-phase scaffolding flow. This plan restructures it to branch by project type at the start, then use type-specific logic in each subsequent phase. No executable code — all changes are to markdown instruction files.

**Tech Stack:** Markdown skill files, Claude Code plugin system (`plugin.json`)

---

## Context for the Executor

The kickstart skill (`skills/kickstart/SKILL.md`) is a markdown instruction file that tells Claude how to scaffold new projects. It's not executable code — it's a prompt that Claude follows. "Testing" means creating eval scenario specifications, not traditional unit tests. The existing skill is 150 lines and software-only.

Key files:
- `skills/kickstart/SKILL.md` — the skill to modify (150 lines currently)
- `.claude-plugin/plugin.json` — version bump needed
- `docs/mockups/kickstart-expansion.html` — reference mockup (read-only)
- `docs/plans/2026-03-24-kickstart-expansion-design.md` — source design doc (read-only)

**Task ordering:** Tasks 1–9 must execute sequentially in order — all modify `skills/kickstart/SKILL.md`. Task 8 depends on Task 1 completing first (the Phase 6 heading must exist before Phase 5 can be inserted before it). Tasks 10–12 are independent of each other but should run after Tasks 1–9.

---

### ✅ Task 1: Update Frontmatter and Insert Phase 1 (Type Selection)

**Files:**
- Modify: `skills/kickstart/SKILL.md` (the frontmatter and Phase 1 section)

**Step 1: Read the current SKILL.md**

Read `skills/kickstart/SKILL.md` in full to have fresh context.

**Step 2: Update frontmatter description**

Replace the existing frontmatter (lines 1-4):
```yaml
---
name: kickstart
description: "Scaffold a new project with Aligned conventions: CLAUDE.md, docs structure, eval infrastructure, quality gates, and design principles placeholder."
---
```

With:
```yaml
---
name: kickstart
description: "Scaffold a new project with Aligned conventions. Supports software, business, personal, and general project types with appropriate structure and CLAUDE.md templates."
---
```

**Step 3: Insert Phase 1 (Type Selection) before existing Phase 1**

The current Phase 1 starts at line 14 with `## Phase 1: Gather Context`. Renumber this to Phase 2 and insert a new Phase 1 before it.

Insert after the `**Invocation:** \`/aligned:kickstart\`` line (line 12) and before the current Phase 1:

```markdown
## Phase 1: Project Type Selection

Before gathering any other context, ask the user (use AskUserQuestion):

> **What type of project is this?**
> A. Software (code, tests, builds)
> B. Business (consulting, clients, deliverables)
> C. Personal (knowledge management, life domains)
> D. General (anything else that needs structure)

The answer determines which scaffold path and CLAUDE.md template to use. Store the selection as `project_type`.
```

**Step 4: Renumber existing phases**

Renumber the existing phases:
- "Phase 1: Gather Context" → "Phase 2: Gather Context"
- "Phase 2: Scaffold Structure" → "Phase 3: Scaffold Structure"
- "Phase 3: Seed CLAUDE.md" → "Phase 4: Seed CLAUDE.md"
- "Phase 4: Next Steps" → "Phase 6: Next Steps" (leaving room for Phase 5)

**Step 5: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): add project type selection phase and renumber phases"
```

---

### ✅ Task 2: Modify Phase 2 (Context Gathering) for Type-Conditional Questions

**Files:**
- Modify: `skills/kickstart/SKILL.md` (the Phase 2 section, formerly Phase 1)

**Step 1: Read the current Phase 2 section**

Read `skills/kickstart/SKILL.md` to find the Phase 2 section.

**Step 2: Replace the context gathering section**

Replace the content of Phase 2 (the 5-question list) with type-conditional logic:

```markdown
## Phase 2: Gather Context

Ask the user for (use AskUserQuestion, multiple choice where possible):

**All types ask:**
1. **Project name and one-sentence description**
2. **Any additional context** (linked via `@` symbol — brand guidelines, wireframes, prior art)

**Software additionally asks** (skip for Business, Personal, General):
3. **Tech stack** (defaults: Next.js + TypeScript + Tailwind)
4. **Target deployment platform** (default: Vercel)
5. **Testing framework** (default: Jest for Node/TS, Vitest for Vite-based, pytest for Python)
```

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): make context gathering type-conditional"
```

---

### ✅ Task 3: Restructure Phase 3 (Scaffold) Into Base + Software-Only

**Files:**
- Modify: `skills/kickstart/SKILL.md` (the Phase 3 section, formerly Phase 2)

**Step 1: Read the current Phase 3 section**

Read `skills/kickstart/SKILL.md` to find the Phase 3 section (Scaffold Structure).

**Step 2: Replace the scaffold section with base + software-only split**

Replace the entire Phase 3 content (from the `## Phase 3:` heading through the `.gitignore` section, up to but not including Phase 4) with:

```markdown
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
```

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): split scaffold into base structure and software-only additions"
```

---

### ✅ Task 4: Restructure Phase 4 With 6-Section Template System and Software Template

**Files:**
- Modify: `skills/kickstart/SKILL.md` (the Phase 4 section, formerly Phase 3)

**Step 1: Read the current Phase 4 section**

Read `skills/kickstart/SKILL.md` to find Phase 4 (Seed CLAUDE.md).

**Step 2: Replace Phase 4 with the 6-section template system**

Replace the entire Phase 4 content with the section structure definition and the Software template. The other type templates will be added in subsequent tasks.

```markdown
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
```

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): add 6-section CLAUDE.md template system with software template"
```

---

### ✅ Task 5: Add Business CLAUDE.md Template

**Files:**
- Modify: `skills/kickstart/SKILL.md` (append to Phase 4, after the Software Template section)

**Step 1: Read SKILL.md to find the end of the Software Template section**

Read `skills/kickstart/SKILL.md` and locate the end of the Software Template subsection within Phase 4.

**Step 2: Insert Business Template after the Software Template**

Add the following after the Software Template section (before any Phase 5 content):

```markdown
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
```

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): add business CLAUDE.md template"
```

---

### ✅ Task 6: Add Personal CLAUDE.md Template

**Files:**
- Modify: `skills/kickstart/SKILL.md` (append to Phase 4, after the Business Template section)

**Step 1: Read SKILL.md to find the end of the Business Template section**

Read `skills/kickstart/SKILL.md` and locate the end of the Business Template subsection.

**Step 2: Insert Personal Template after the Business Template**

```markdown
### Personal Template

**Section 1 — Project Identity:**
```markdown
This is a personal knowledge workspace for [project name]. [one-sentence description].
```

**Section 2 — Folder Map:**
Same as Business template.

**Section 3 — Reading Priority:**
Same as Business template.

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
```

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): add personal CLAUDE.md template"
```

---

### ✅ Task 7: Add General CLAUDE.md Template

**Files:**
- Modify: `skills/kickstart/SKILL.md` (append to Phase 4, after the Personal Template section)

**Step 1: Read SKILL.md to find the end of the Personal Template section**

Read `skills/kickstart/SKILL.md` and locate the end of the Personal Template subsection.

**Step 2: Insert General Template after the Personal Template**

```markdown
### General Template

**Section 1 — Project Identity:**
```markdown
This is a workspace for [project name]. [one-sentence description].
```

**Section 2 — Folder Map:**
```markdown
## Folder Map

- `docs/` — reference material
- `docs/lessons-learned/` — retrospectives
```

**Section 3 — Reading Priority:**
```markdown
## Reading Priority

1. This file (CLAUDE.md)
2. `~/.claude/about-me.md` — global identity and preferences
```

**Section 4 — Communication Preferences:**
Empty placeholder.

**Section 5 — Guardrails:**
Empty placeholder.

**Section 6 — Workflows:**
Empty placeholder.
```

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): add general CLAUDE.md template"
```

---

### ✅ Task 8: Add Phase 5 (Global About-Me Check)

**Files:**
- Modify: `skills/kickstart/SKILL.md` (insert Phase 5 between Phase 4 and Phase 6)

**Step 1: Read SKILL.md to find where Phase 6 begins**

Read `skills/kickstart/SKILL.md` and locate the Phase 6 heading.

**Step 2: Insert Phase 5 before Phase 6**

Insert the following before the `## Phase 6:` heading:

```markdown
## Phase 5: Global About-Me Check

After scaffolding, check whether `~/.claude/about-me.md` exists.

**If missing:** Ask the user (use AskUserQuestion):

> No global about-me found at `~/.claude/about-me.md`. Want to create one now?

If yes, create `~/.claude/about-me.md` with this template:
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

If `~/.claude/CLAUDE.md` exists, read it to understand its current structure, then suggest adding a reading priority reference to it at an appropriate insertion point (do not modify without user confirmation).

If `~/.claude/` does not exist, create it first. If directory creation fails (permission error), skip with a note and continue.

**If exists:** Do nothing. CLAUDE.md templates already reference it.
```

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): add global about-me identity check phase"
```

---

### ✅ Task 9: Modify Phase 6 (Next Steps) Per Type

**Files:**
- Modify: `skills/kickstart/SKILL.md` (the Phase 6 section, formerly Phase 4)

**Step 1: Read the current Phase 6 section**

Read `skills/kickstart/SKILL.md` and locate Phase 6 (Next Steps).

**Step 2: Replace Phase 6 with type-conditional next steps**

Replace the entire Phase 6 content with:

```markdown
## Phase 6: Next Steps

Output the appropriate message based on `project_type`, then commit all scaffolded files:

**Software:** "Project scaffolded. Run `/aligned:design-principles` to define the design direction. The placeholder at `docs/design/design-principles.md` needs to be fleshed out."
> Note: The extra sentence about the placeholder is preserved from the existing SKILL.md behavior. The design doc omits it, but it provides useful guidance.

**Business:** "Project scaffolded. Start with `/aligned:business-brainstorming` to define your first initiative, or fill in the CLAUDE.md guardrails section with confidentiality rules for this workspace."

**Personal:** "Project scaffolded. Start with `/aligned:business-brainstorming` to define your first initiative, or fill in the guardrails section of CLAUDE.md with any privacy constraints (health data, finances, etc.)."

**General:** "Project scaffolded. Start with `/aligned:business-brainstorming` to define your first initiative, or fill in the CLAUDE.md sections as you discover what conventions matter for this workspace."

Commit all scaffolded files (note: this `git add -A` is content written into SKILL.md for the user's scaffolded project — not a command to run in the skills repo):
```bash
git add -A
git commit -m "chore: scaffold project with Aligned conventions"
```
```

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): add type-specific next steps messages"
```

---

### ✅ Task 10: Bump Plugin Version

**Files:**
- Modify: `.claude-plugin/plugin.json` (the `version` field)

**Step 1: Read plugin.json**

Read `.claude-plugin/plugin.json`.

**Step 2: Bump the version**

Change the version from `"0.10.0"` to `"0.11.0"` (minor bump — new feature, backwards compatible).

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump plugin version to 0.11.0 for kickstart expansion"
```

---

### ✅ Task 11: Create E2E Test Scenario Specifications

**Files:**
- Create: `e2e/scenarios/kickstart-expansion.test.ts`

**Step 1: Verify the target directory exists**

Note: `e2e/` does not exist in this repo — `mkdir -p e2e/scenarios` will create both levels.

**Step 2: Write the test scenario file**

This file specifies eval scenarios for the kickstart skill expansion. These are specification-style tests that describe expected behavior for each project type. They follow the project's eval scenario conventions.

```typescript
/**
 * Kickstart Expansion — Eval Scenarios
 *
 * These scenarios verify the kickstart skill correctly scaffolds
 * all 4 project types with appropriate structure and CLAUDE.md content.
 *
 * Run context: Each scenario should be executed in a fresh temp directory
 * with the aligned plugin enabled.
 */

// Scenario 1: Type selection routing
// Input: User selects each of the 4 types (A/B/C/D)
// Expected: Software type asks tech stack questions (3-5)
// Expected: Business/Personal/General skip tech stack questions
// Expected: All types ask project name and description (questions 1-2)

// Scenario 2: Base structure — all types
// Input: Any project type, project name "test-project"
// Expected: CLAUDE.md exists at root
// Expected: .claude/settings.json exists with enabledPlugins.aligned = true
// Expected: docs/ directory exists
// Expected: docs/lessons-learned/ directory exists

// Scenario 3: Software additions — software type only
// Input: Software type selected
// Expected: docs/design/design-principles.md exists with placeholder content
// Expected: docs/architecture.md exists with Mermaid template
// Expected: docs/plans/completed/ exists
// Expected: docs/kanban/todo/, in-progress/, done/, did_not_complete/ exist
// Expected: docs/kanban/.counter exists with content "1"
// Expected: docs/mockups/ exists
// Expected: docs/lessons-learned/completed/ exists
// Expected: e2e/scenarios/, e2e/fixtures/profiles/ exist
// Expected: e2e/eval-config.ts, e2e/eval-runner.ts exist
// Expected: e2e/.gitignore exists
// Expected: scripts/ exists
// Expected: eslint-rules/ exists
// NOT expected for Business/Personal/General types

// Scenario 4: CLAUDE.md content per type
// Input: Each project type with name "test-project", description "A test"
// Expected (all types): Has 6 sections (Identity, Folder Map, Reading Priority,
//   Communication, Guardrails, Workflows)
// Expected (all types): Reading Priority references ~/.claude/about-me.md
// Expected (software): Workflows lists 8 aligned skills (brainstorming through eval-audit)
// Expected (software): Guardrails contains Iron Rules (TDD, error paths, verify, root cause)
// Expected (software): Communication has Commands section
// Expected (business): Workflows lists business skills + content generation skills
// Expected (business): Guardrails mentions confidentiality
// Expected (personal): Communication says "Direct, informal"
// Expected (personal): Guardrails mentions privacy (health, financial, relationships)
// Expected (general): Workflows is empty placeholder

// Scenario 5: About-me check — missing
// Input: ~/.claude/about-me.md does not exist
// Expected: User is prompted to create about-me.md
// Expected: If user says yes, file is created with 4-section template
//   (Role & Identity, Expertise, Methodology, Communication Style)
// Expected: User is asked about adding reference to ~/.claude/CLAUDE.md

// Scenario 6: About-me check — exists
// Input: ~/.claude/about-me.md already exists
// Expected: No prompt about about-me.md
// Expected: Scaffolding continues without interruption

// Scenario 7: About-me check — permission failure
// Input: ~/.claude/ cannot be created (simulated permission error)
// Expected: Graceful skip with informational note
// Expected: Scaffolding continues without error

// Scenario 8: Idempotency
// Input: Run kickstart in directory with existing CLAUDE.md and .claude/settings.json
// Expected: Existing files are not overwritten
// Expected: Missing directories are created
// Expected: .claude/settings.json is merged (aligned: true added, existing keys preserved)
```

**Step 3: Commit**

```bash
git add e2e/scenarios/kickstart-expansion.test.ts
git commit -m "test: add eval scenario specifications for kickstart expansion"
```

---

### Task 12: Final Verification

**Files:**
- Read: `skills/kickstart/SKILL.md` (full file)
- Read: `.claude-plugin/plugin.json`
- Read: `e2e/scenarios/kickstart-expansion.test.ts`

**Step 1: Read the complete SKILL.md and verify structure**

Read `skills/kickstart/SKILL.md` in full. Verify:
- Frontmatter has updated description mentioning 4 project types
- 6 phases in order: Type Selection → Gather Context → Scaffold Structure → Seed CLAUDE.md → About-Me Check → Next Steps
- Phase 2 has type-conditional questions (all types: 1-2, software only: 3-5)
- Phase 3 has base structure (all types) and software-only additions
- Phase 3 uses `done/` not `completed/` for kanban directory (except `docs/plans/completed/` and `docs/lessons-learned/completed/` which are different)
- Phase 4 has 6-section template structure defined, plus 4 type templates (Software, Business, Personal, General)
- All templates reference `~/.claude/about-me.md` in Reading Priority
- Phase 5 has about-me check logic
- Phase 6 has 4 type-specific next-steps messages

**Step 2: Verify plugin.json version**

Read `.claude-plugin/plugin.json` and confirm version is `0.11.0`.

**Step 3: Verify test file exists**

Read `e2e/scenarios/kickstart-expansion.test.ts` and confirm all 8 scenarios are present.

**Step 4: Run git status to verify clean state**

```bash
git status
```

Expected: Clean working tree, all changes committed.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Single SKILL.md file | Keep all templates inline in SKILL.md | Separate template files per type |
| 2 | Kanban dir naming | Use `done/` in kanban, keep `completed/` elsewhere | Use `completed/` everywhere |
| 3 | Test format | TypeScript eval scenario specs | Markdown test specs, no test file |
| 4 | Task granularity | One task per template type | Single task for all templates |
| 5 | Version bump | Minor bump 0.10.0 → 0.11.0 | Patch bump, no bump |
| 6 | Base `.gitignore` for all types | Add minimal `.gitignore` to base structure | Only create `.gitignore` for software type |

### Appendix: Decision Details

#### Decision 1: Single SKILL.md file
**Chose:** Keep all 4 CLAUDE.md templates inline in SKILL.md
**Why:** The existing skill is a single file. The templates are short (each is ~30-40 lines of markdown). Splitting into separate files would add complexity without meaningful benefit — Claude reads the entire skill file anyway, and having everything in one place makes it easier to maintain consistency across templates. The skill anatomy in CLAUDE.md says supporting docs are optional (`*.md — Supporting docs`).
**Alternatives rejected:**
- Separate template files (e.g., `skills/kickstart/templates/business.md`): Adds indirection. The templates are small enough that a single file stays readable. Would also require the skill to reference external files, adding a failure mode.

#### Decision 2: Kanban dir naming
**Chose:** Use `done/` in kanban mkdir commands, keep `completed/` for `docs/plans/completed/` and `docs/lessons-learned/completed/`
**Why:** The design doc explicitly calls out a `done/` vs `completed/` inconsistency in the existing SKILL.md. The mkdir commands on line 89 of the current SKILL.md already use `done/`, but the directory tree on line 43 shows `completed/`. The design doc says to use `done/` to match the mkdir commands. The `docs/plans/completed/` and `docs/lessons-learned/completed/` directories are different — they use `completed/` for archived plan files and aren't part of the kanban board.
**Alternatives rejected:**
- Use `completed/` everywhere: Would require changing the mkdir commands and is inconsistent with how the kanban board currently operates in other projects.

#### Decision 3: Test format
**Chose:** TypeScript eval scenario specifications
**Why:** The design doc specifies `e2e/scenarios/kickstart-expansion.test.ts`. This repo has no test runner or package.json, so these are specification-style tests (comments describing expected behavior) rather than executable tests. They serve as documentation for future eval implementation and provide clear acceptance criteria for the skill changes.
**Alternatives rejected:**
- No test file: The design doc explicitly specifies test scenarios. Omitting them would be spec drift.
- Markdown test specs: Would work but the design doc specifies `.test.ts` format, and using TypeScript comment syntax keeps the door open for future test runner integration.

#### Decision 4: Task granularity
**Chose:** One task per CLAUDE.md template type (Tasks 4-7)
**Why:** Each template has distinct content and the executor benefits from focused context per edit. Grouping all 4 templates into one task would make a large edit to a file that's already being substantially restructured. Separate tasks also make it easier to verify each template independently.
**Alternatives rejected:**
- Single task for all templates: Would create a very large edit step. The writing-plans skill says each step should be 2-5 minutes.

#### Decision 5: Version bump
**Chose:** Minor version bump (0.10.0 → 0.11.0)
**Why:** This is a new feature (non-software project types), not a bug fix or breaking change. Semver minor bump is appropriate for backwards-compatible feature additions. The kickstart skill's existing software scaffolding behavior is preserved — selecting "Software" produces the same result as before.
**Alternatives rejected:**
- Patch bump: This is a feature, not a fix.
- No bump: CLAUDE.md says to bump version when adding features.

#### Decision 6: Base `.gitignore` for all types
**Chose:** Add a minimal `.gitignore` to the base structure (all types) containing `.claude/settings.local.json` and `.claude/CLAUDE.local.md` entries.
**Why:** The Settings section (ALL types) instructs Claude to "ensure `.claude/settings.local.json` and `.claude/CLAUDE.local.md` are in the project's `.gitignore`". Without a `.gitignore` in the base structure, this instruction is a no-op for non-software types. The design doc's base structure omits `.gitignore`, but the design doc also says all types get `.claude/settings.json` — and the personal override files should be excluded from version control for all project types, not just software.
**Alternatives rejected:**
- Only create `.gitignore` for software type: Leaves non-software projects with `.claude` personal overrides potentially committed to git. The Settings block's instruction becomes inconsistent.
