# Brainstorming Skill Unification Design

**Date:** 2026-04-02
**Status:** Draft
**Version bump:** 0.12.0 → 0.13.0
**Mockups:** docs/mockups/brainstorming-skill-unification.html

## Problem

External users of the Aligned plugin must choose between `/aligned:brainstorming` (software) and `/aligned:business-brainstorming` (business/strategy) without understanding the distinction. This creates friction for new users and forces a decision they're not equipped to make.

## Solution

Merge both skills into a single `/aligned:brainstorming` entry point with a thin router that auto-detects mode and hands off to mode-specific process files.

## Architecture

### File Layout

```
skills/brainstorming/
  SKILL.md                          — Router (~60-80 lines)
  modes/
    software.md                     — Software brainstorming process
    business.md                     — Business brainstorming process (4-phase gated)
  design-critique-checklist.md      — Software critique checklist (unchanged)
  business-critique-checklist.md    — Business critique checklist (moved + renamed)
```

The `business-brainstorming/` directory is deleted. `modes/` is a new subdirectory convention for router-dispatched process files (Read into the current context at runtime). This differs from the `workers/` pattern in `codebase-audit`, where files are dispatched as independent sub-agents via Task tool. `modes/` = inline Read, `workers/` = sub-agent dispatch.

### Router SKILL.md

The router is ~60-80 lines and does three things:

1. **Classifies mode** from user's topic + environment context
2. **Dispatches project scan** (background) with mode context so the scanner knows what to emphasize
3. **Hands off** to the appropriate mode file with explicit checklist path and `{base-directory}`

```markdown
---
name: brainstorming
description: "Use before any creative or strategic work — software features,
  business strategy, analysis, or decision-making. Detects whether the topic
  is software design or business strategy and adapts the process accordingly."
---

# Brainstorming

## Overview
A unified brainstorming skill that adapts its process based on what you're
working on. Software/technical topics get a fluid Q&A with Architect
auto-consult. Business/strategy topics get a structured 4-phase process
(Goal → Problems → Root Causes → Solutions).

## Step 1: Detect Mode
Classify the user's topic into one of two modes:

**Signal precedence:** Topic keywords take priority over environment signals.
A user in a code repo asking about "pricing strategy" is business mode, not
software mode. Environment is a tiebreaker when topic keywords are absent.

**Software mode** — building, modifying, or designing software:
- Topic signals: features, components, APIs, bugs, refactoring, architecture,
  implementation, code, testing, data models
- Environment (tiebreaker): project contains code files (package.json,
  Cargo.toml, go.mod, pyproject.toml, etc.)

**Business mode** — strategy, decisions, analysis, or non-code deliverables:
- Topic signals: strategy, sales, marketing, positioning, meeting prep,
  decisions, stakeholders, pricing, proposals, planning, analysis
- Environment (tiebreaker): project is docs-only, Obsidian vault, or
  non-code directory

**If signals are clear:** Auto-route and briefly tell the user which mode
was selected (e.g., "This looks like a software design problem — I'll use
the technical brainstorming process."). Add: "If this isn't right, just
say so and I'll switch." Proceed to Step 2.

**If signals are mixed or absent:** Ask one question: "Is this a
software/technical design or a business/strategy problem?" Then proceed
to Step 2 based on the answer.

## Step 2: Project Scan
Dispatch a project scan agent via Task tool (subagent_type=general-purpose),
running in the background. Now that mode is known, pass it to the scanner:

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`.
Mode: {software|business} — emphasize {code artifacts|domain materials}
accordingly."

Do not wait for the scan to complete before proceeding to Step 3.

## Step 3: Hand Off to Mode

**If software mode:**
Read `{base-directory}/modes/software.md` and follow its process.
The base directory for this skill is `{base-directory}`.
The critique checklist for this session is at
`{base-directory}/design-critique-checklist.md`.
The shared orchestration file is at
`{base-directory}/../_shared/critique-panel-orchestration.md`.

**If business mode:**
Read `{base-directory}/modes/business.md` and follow its process.
The base directory for this skill is `{base-directory}`.
The critique checklist for this session is at
`{base-directory}/business-critique-checklist.md`.
The shared orchestration file is at
`{base-directory}/../_shared/critique-panel-orchestration.md`.

**If the mode file cannot be Read, STOP and tell the user the plugin
installation may be incomplete.**
```

### Mode File Contents

**Software mode (`modes/software.md`)**

Derived from current `brainstorming/SKILL.md`.

Removed:
- YAML frontmatter (router owns this)
- Project scan dispatch instruction (router handles it)
- The dispatch half of the "overlap" block

Preserved intact:
- Minimum 3 business questions rule
- Scan gate ("before any technical question, scan MUST have completed")
- "Don't idle" guidance — if user responds before scan finishes, keep asking business questions
- Full business/technical question classification
- Architect auto-consult (proxy + review modes) with all dispatch templates
- Gray area handling, mockup-generator dispatch
- Design presentation in 200-300 word sections
- After-design: mandatory visualization → division-of-labor critique → refresh → commit → Option A/B next-step prompt
- Design Critique section (for critiquing existing designs, uses software checklist)

Changes:
- Critique panel config block (carried in full): `skill-name: brainstorming`, `checklist-filename: design-critique-checklist.md`, `fact-check-mode: division-of-labor`, `fact-check-tools: Glob, Grep, Read, Write`, `aggregation: sub-agent`, `criteria-assignment: yes`
- Scan referenced as "already dispatched by the router" with note: "The router has already dispatched a project scan. Results will be at `/tmp/brainstorm-context-{topic}/project-scan.md`."

**Business mode (`modes/business.md`)**

Derived from current `business-brainstorming/SKILL.md`.

Removed:
- YAML frontmatter
- Project scan dispatch instruction

Preserved intact:
- 4-phase gated structure: Goal → Problems → Root Causes → Solutions (all gates mandatory)
- "Don't idle" guidance while scan completes
- Problem categorization taxonomy, root cause probing, "Why?" chains
- 2-3 approaches with recommendation
- Design presentation in 200-300 word sections
- After-design: conditional visualization → all-critics critique with WebSearch/WebFetch → refresh → commit
- Design Critique section (for critiquing existing designs, uses business checklist)
- Simple one-line next-step format: routes to `/aligned:business-write-plan` (no Option A/B)

Changes:
- Critique panel config block (carried in full): `skill-name: brainstorming`, `checklist-filename: business-critique-checklist.md`, `fact-check-mode: all-critics`, `fact-check-tools: Glob, Grep, Read, WebSearch, WebFetch`, `aggregation: sub-agent`, `criteria-assignment: no`
- Scan referenced as "already dispatched by the router" with note: "The router has already dispatched a project scan. Results will be at `/tmp/brainstorm-context-{topic}/project-scan.md`."

### Shared Infrastructure (Untouched)

- `_shared/critique-panel-orchestration.md` — consumed by both modes as before
- `agents/project-scanner.md` — dispatched by router
- KB-023/24/25 (visualization duplication) — orthogonal, closed as resolved-by-unification

## Migration Plan

### Operation Sequence (order matters)

1. **Move** `skills/business-brainstorming/design-critique-checklist.md` → `skills/brainstorming/business-critique-checklist.md`
2. **Create** `skills/brainstorming/modes/software.md` (adapted from current `brainstorming/SKILL.md`)
3. **Create** `skills/brainstorming/modes/business.md` (adapted from current `business-brainstorming/SKILL.md`)
4. **Rewrite** `skills/brainstorming/SKILL.md` as router
5. **Delete** `skills/business-brainstorming/` directory entirely (including `critic-registry.md`)
6. **Verify** Grep for `business-brainstorming` across all file types in the repo. Confirm no live references remain — only historical artifacts (see exclusion list below)

### Cross-Reference Updates

| File | What to change |
|------|---------------|
| `skills/business-write-plan/SKILL.md:18` | Predecessor reference → `/aligned:brainstorming` |
| `skills/kickstart/SKILL.md:239` | Workflow list item |
| `skills/kickstart/SKILL.md:355` | Permission entry `Skill(aligned:business-brainstorming)` |
| `skills/kickstart/SKILL.md:379,381,383` | Three next-step messages |
| `skills/_shared/critique-panel-orchestration.md:9` | Example `skill-name` value |
| `README.md:57` | Permission entry in settings example |
| `README.md:83` | Merge business-brainstorming row into brainstorming row in skill table |

### Explicitly NOT Updated (historical records)

- `README.md:213` — changelog entry for v0.3.0 (historical)
- `docs/mockups/*.html`, `docs/workflow.html` — historical visualization artifacts
- `docs/plans/completed/*.md` — completed plan documents
- `docs/kanban/done/*.md` — completed kanban items (KB-005, KB-006 reference the old skill)

**Note on existing user projects:** Users who scaffolded projects with `/aligned:kickstart` before v0.13.0 will have `/aligned:business-brainstorming` baked into their CLAUDE.md files. These stale references will silently fail (skill not found). The v0.13.0 changelog should call this out explicitly.

### Kanban Cleanup

- Close KB-023, KB-024, KB-025 as resolved-by-unification

### Version Bump

- `0.12.0` → `0.13.0` in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`

### Changelog Entry (v0.13.0)

```
### 0.13.0 — Unified Brainstorming Skill

- **BREAKING:** `/aligned:business-brainstorming` has been merged into
  `/aligned:brainstorming`. The unified skill auto-detects whether your
  topic is software/technical or business/strategy and adapts accordingly.
  If you have `/aligned:business-brainstorming` in any project CLAUDE.md
  files, update them to `/aligned:brainstorming`.
```

## Testing

| Scenario | Example Input | Expected Observable Output | Failure Criteria |
|----------|--------------|---------------------------|------------------|
| Software auto-route | `/aligned:brainstorming` with "add a caching layer to the API" in a Node.js repo | Prints "software design" mode selection, asks first business question, no mode prompt | Routes to business mode or asks clarifying question |
| Business auto-route | `/aligned:brainstorming` with "pricing strategy for our SaaS product" in an Obsidian vault | Prints "business/strategy" mode selection, starts Phase 1 (Goal), no mode prompt | Routes to software mode or skips 4-phase gates |
| Business in code repo | `/aligned:brainstorming` with "sales positioning for this product" in a code repo | Topic signals override environment → business mode (topic > environment precedence) | Routes to software mode because code files are present |
| Ambiguous | `/aligned:brainstorming` with "let's brainstorm" (no topic keywords, no code files) | Asks one clarifying question about mode | Auto-routes without asking |
| Mode switch | User says "actually this is a business problem" after software auto-route | Switches to business mode, starts 4-phase gates | Continues in software mode |
| Software critique panel | Complete a software brainstorm through critique | Critique uses `design-critique-checklist.md`, division-of-labor fact-checking | Uses business checklist or wrong fact-check mode |
| Business critique panel | Complete a business brainstorm through critique | Critique uses `business-critique-checklist.md`, all-critics fact-checking with WebSearch | Uses software checklist or wrong fact-check mode |
| Missing mode file | Delete `modes/software.md` temporarily, invoke software mode | STOP message about incomplete plugin installation | Silent failure or error buried in output |

## Decision Log

| # | Decision | Rationale | Alternatives Considered |
|---|----------|-----------|------------------------|
| D1 | Thin router + mode files over full merge | Processes are fundamentally different (flat Q&A vs 4-phase gated); a merged file would be 400+ lines of conditionals | Full merge (rejected: maintenance burden), keep separate + alias (rejected: doesn't solve the problem) |
| D2 | `modes/` subdirectory convention | New convention for files Read inline into context by a router. Distinct from `workers/` (sub-agent dispatch) and `references/` (static reference material). The directory layout resembles `workers/` but the execution model differs. | Inline in SKILL.md (rejected: file too long), `references/` (rejected: wrong semantic — these are processes, not reference material), reuse `workers/` name (rejected: different execution model would confuse contributors) |
| D3 | Auto-detect with fallback question | Users often work in non-code contexts where environment signals alone aren't sufficient; one clarifying question is acceptable | Fully automatic (rejected: unreliable without code signals), always ask (rejected: unnecessary friction when signals are clear) |
| D4 | Preserve business 4-phase gates | User confirmed gates are valuable for business users — prevents jumping to solutions | Flatten to fluid Q&A like software (rejected: loses discipline that business problems need) |
| D5 | Router passes explicit checklist path | Checklists have different filenames after colocation; deriving from mode name was fragile | Derive from mode name (rejected: naming mismatch), same filename in subdirectories (rejected: Glob fallback ambiguity) |
| D6 | Remove scan dispatch from mode files | Cleaner than "do not dispatch again" prose instruction; mode files reference scan results, not dispatch logic | Keep dispatch + "don't re-dispatch" instruction (rejected: fragile LLM instruction) |
| D7 | Dispatch scan after mode detection, not before | Scanner should know the mode so it can emphasize code artifacts (software) or domain materials (business). Dispatching before mode detection wastes the opportunity to give the scanner useful context. | Dispatch before detection (rejected: scanner does broad sweep without mode context) |
| D8 | Topic signals take priority over environment for mode detection | A user in a code repo asking about "pricing strategy" is doing business work. Environment is a tiebreaker, not a primary signal. | Environment-first (rejected: misclassifies business work in code repos) |
| D9 | Design Critique stays in each mode file, not a third router path | Design Critique is a secondary capability (2-3 lines), not a distinct brainstorming process. Each mode uses its own checklist for critique. | Third router path (rejected: elevates a minor section to a full mode), shared critique file (rejected: checklists differ per mode) |
