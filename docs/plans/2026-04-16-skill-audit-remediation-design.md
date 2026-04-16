# Skill Audit Remediation Plan

**Date:** 2026-04-16
**Status:** Design
**Audit source:** `/tmp/skill-audit/SUMMARY.md` (18 skills audited against Anthropic best practices)
**Mockups:** docs/mockups/skill-audit-remediation.html

## Goal

Maximize the quality floor across all 18 aligned plugin skills, with priority attention to the 5 most-used skills: brainstorming, use-advisor, use-framework, writing-plans, executing-plans.

## Approach: Three Waves

Strict ordering — each wave merges before the next begins.

### Wave 1: Metadata, Navigation, and Missing Files (1-3 PRs)

Wave 1 changes are independent across skills. The implementer may split into sub-PRs (e.g., descriptions, TOCs, other fixes) if a single PR creates review bottleneck. The wave-ordering constraint (Wave 1 merges before Wave 2) applies to the wave as a whole.

**Description rewrites (14 skills):**

Descriptions are the `description:` field in each SKILL.md's YAML frontmatter block (`---` delimiters at top of file). All rewrites follow the pattern: third-person voice, what it does + "Use when..." trigger, no workflow summary.

| Skill | New description |
|-------|----------------|
| use-advisor | `Adopts an advisor's persona for the conversation. Use with an advisor name for fuzzy match, or alone to list available advisors. Triggers when a user mentions an advisor by name or asks to channel a specific expert's perspective.` |
| use-framework | `Guides a user through a decision framework's interactive phases, respecting WAIT points. Use with a framework name for fuzzy match, or alone to list available frameworks. Triggers when a user mentions a framework by name in any request.` |
| writing-plans | `Produces TDD implementation plans from specs or design docs, with parallel sub-agent critique and architectural review. Use when requirements are defined and the next step is a concrete, task-by-task build plan.` |
| executing-plans | `Executes written implementation plans with TDD discipline, batched task execution, and architecture verification. Use when a plan file exists in docs/plans/ and is ready for implementation.` |
| brainstorming | `Structures creative and strategic work through guided dialogue — software design or business strategy. Use before any creative, architectural, or strategic work that benefits from structured exploration and expert critique.` |
| add-advisor | `Adds a new advisor persona to the Virtual Board with system prompt, registry entry, and initial framework. Use when the user wants to add a new expert voice — either by naming a person or pointing to research in docs/advisors/.` |
| create-design-principles | `Interactive design system creation with Steve Jobs persona, producing design-principles.md with tokens, patterns, and anti-patterns. Use when building dashboards, admin interfaces, or any UI that needs a precise design direction.` |
| find-potential-advisors | `Researches and evaluates potential advisor candidates for the Virtual Board. Use when exploring a new domain or identifying experts before running add-advisor.` |
| kickstart | `Scaffolds a new project with Aligned conventions, directory structure, and CLAUDE.md. Use when starting a new repo or adding Aligned structure to an existing codebase.` |
| using-git-worktrees | `Sets up isolated git worktrees for feature branches. Use when starting feature work that needs isolation from the current workspace or before executing implementation plans.` |
| create-image | `Generates hand-coded SVG diagrams, charts, flowcharts, and brand icons matching the project's design tokens. Use when a visual artifact is needed — charts, flowcharts, matrices, icons, or brand graphics.` |
| codebase-audit | `Comprehensive multi-dimensional codebase audit covering code quality, test quality, security, dead code, and architecture. Use when reviewing an unfamiliar codebase, before a major refactor, or as a periodic health check. Report-only — never edits source code.` |
| eval-audit | `Detects LLM behavior surface changes without eval coverage. Use when adding advisors, frameworks, or prompt logic to verify eval scenarios exist. Manual invocation only.` |
| kanban-resolve | `Triages and resolves all accumulated Kanban board items in a single automated pass. Use when the board has multiple pending items in docs/kanban/todo/ to process as a batch.` |

**TOC additions (8 files):**

Each file gets a markdown section list after its opening heading. Example format:

```markdown
## Contents
- Section one title
- Section two title
- Section three title
```

- `brainstorming/modes/software.md` (271 lines)
- `brainstorming/modes/business.md` (226 lines)
- `brainstorming/references/brainstorm-components.md` (749 lines)
- `writing-plans/plan-critique-checklist.md` (204 lines)
- `persona-panel/references/aggregation-prompt.md` (109 lines)
- `persona-panel/modes/persona-creation-flow.md` (111 lines)
- `create-design-principles/design-critique-checklist.md` (205 lines)
- `finishing-a-development-branch/references/deployment-pitfall-catalog.md` (284 lines)

**Missing files (root-cause-analysis):**

Create minimal working implementations matching the interfaces described in the referencing documents:
- `find-polluter.sh` — referenced in `root-cause-tracing.md:101`. The referencing text describes a bisection script for identifying test polluters. Create a shell script implementing this interface.
- `condition-based-waiting-example.ts` — referenced in `condition-based-waiting.md:82`. The referencing text describes condition-based waiting patterns. Create a TypeScript example matching the described function signatures.

**Other low-hanging fruit:**
- Remove "Invocation" section from add-advisor SKILL.md (lines 12-16)
- Remove editor notes from add-advisor (line 52) and add-framework (line 47)
- Fix stale `elements-of-style:writing-clearly-and-concisely` reference in brainstorming business mode

### Wave 2: Kanban Format Deduplication (single PR)

Remove inline Kanban entry format copies, keeping only `_shared/kanban-entry-format.md` as the single source of truth.

| Skill | Action |
|-------|--------|
| executing-plans | Remove inline template at lines 120-135. Keep `_shared/` reference at line 169. If `CRITICAL` severity is intentional, add it to the shared file. |
| finishing-a-dev-branch | Remove duplicate kanban instructions at lines 822-824. Keep single `_shared/` reference at line 289. |
| root-cause-analysis | Normalize path reference style to match other skills. No content duplication to remove. |

### Wave 3: File Extractions (up to 3 PRs)

Each skill gets its own PR. Order is independent.

Note: Each file extraction adds a path reference dependent on `{base-directory}` resolution. Use existing fallback patterns (base-directory line + Glob fallback) and track these as motivation for the deferred `{base-directory}` design work.

**writing-plans (596 → ~395 lines):**

| Extract to | Lines | Content |
|------------|-------|---------|
| `references/critique-panel-prompts.md` | ~130 | Fact-checker and regular critic prompt templates |
| `references/execution-handoff-templates.md` | ~78 | Option A and Option B worktree templates |
| *(keep inline)* | ~67 | Error-path testing section stays in SKILL.md — it contains a plan-writer-specific gate function and operations table distinct from `_shared/testing-anti-patterns.md` |

**finishing-a-development-branch (834 → ~430 lines):**

| Extract to | Lines | Content |
|------------|-------|---------|
| `references/mockup-fidelity-check.md` | ~186 | Mockup deviation detection and fix workflow |
| `references/deploy-smoke-test.md` | ~74 | Vercel deployment and smoke test workflow |
| `references/code-review-scan.md` | ~80 | Code review + simplification orchestration |
| `references/llm-eval-gate.md` | ~56 | LLM eval surface check workflow |

Additional fixes: remove meta-commentary (line 173), replace `cat` with Read (line 625).

**kickstart (396 → ~150 lines):**

| Extract to | Lines | Content |
|------------|-------|---------|
| `templates/software.md` | ~60 | Software project CLAUDE.md template |
| `templates/business.md` | ~50 | Business project CLAUDE.md template |
| `templates/personal.md` | ~40 | Personal project CLAUDE.md template |
| `templates/general.md` | ~40 | General project CLAUDE.md template |
| `templates/scaffold-structures.md` | ~60 | Directory trees for each project type |

Additional fixes: replace `git add -A` with explicit file staging. Remove `AskUserQuestion` parenthetical references (lines 16, 28) — the surrounding question text already makes the interaction clear without naming a tool.

## Out of Scope

- **`{base-directory}` resolution fragility** (10 skills — includes create-design-principles, create-image, finishing-a-development-branch beyond the 7 originally counted) — systemic issue requiring a design decision about how skills resolve their own paths. Wave 3 extractions add further `{base-directory}` dependencies, increasing urgency. Tracked separately.
- **Existing Kanban items** (KB-028 through KB-039) — no overlap with this work per Architect analysis.
- **Testing and eval gaps** — the audit checklist flagged missing evals but that's a separate initiative.

## Expected Impact

| Metric | Before | After |
|--------|--------|-------|
| Skills at B-grade or above | 11/18 (61%) | 16-18/18 (89-100%) |
| Skills with anti-pattern #1 description | 9 | 0 |
| Reference files missing TOCs | 8 | 0 |
| Inline Kanban format duplicates | 3 | 0 |
| SKILL.md files over 500 lines | 2 | 0 |
| Phantom file references | 2 | 0 |
