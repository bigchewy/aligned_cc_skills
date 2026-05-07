---
name: brainstorming
description: "Structures creative and strategic work through guided dialogue across five modes — software design, business strategy, research synthesis, content authoring, and multi-feature planning. Use before any creative, architectural, or strategic work that benefits from structured exploration and expert critique."
---

# Brainstorming

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/brainstorming/`. See `skills/_shared/resolve-skill-path.md` for rationale.

## Overview
A unified brainstorming skill that adapts its process based on what you're
working on. Five modes covering distinct shapes of brainstorm work:

- **Software** — fluid Q&A with Architect auto-consult; deliverable is a design doc.
- **Business** — structured 4-phase process (Goal → Problems → Root Causes → Solutions); deliverable is a strategic plan.
- **Research** — corpus survey + comparative synthesis with Skeptic Pass; deliverable is a research memo or KB artifact.
- **Authoring** — content sequencing with domain-advisor panel and optional Research sub-phase; deliverable is a sequenced design doc (curriculum, framework prompts, exercise programs).
- **Planning** — multi-feature portfolio sequencing with strategy advisors; deliverable is a roadmap + spawn-list portfolio.

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

**If signals are clear:** Auto-route and present the mode explanation
block (see below). Proceed to Step 2.

**If signals are mixed or absent:** Ask one question: "Is this a
software/technical design or a business/strategy problem?" Once answered,
present the mode explanation block and proceed to Step 2.

### Mode Explanation Block (mandatory on every invocation)

After mode selection, present this block before starting any phase work:

> **Brainstorming** structures creative and strategic work through guided
> dialogue — from loose idea to validated design with expert critique.
>
> **Selected: {Mode Name}** — {one-sentence description of the process}
> *Why:* {brief reason this mode was selected based on topic/environment signals}
>
> **Other available modes:**
> - {Other mode name} — {one-sentence description}
>
> *To switch modes or skip phases, just say so.*

**Software mode description:** "Fluid Q&A with automatic Architect
consultation on technical decisions. Produces a validated design doc."

**Business mode description:** "Structured phases (Goal, Problems, Root
Causes, Solutions) with gates. Adapts depth to task complexity — tactical
tasks move faster, strategic challenges get full diagnostic treatment."

## Step 2: Project Scan

**Resolve placeholders before dispatching:**
- `{topic}` — a 1–3 word kebab-case slug derived from the user's request (e.g., "pricing-strategy", "auth-refactor"). Ask the user if the request is ambiguous.
- `{project-root}` — the current working directory unless the user specified a different path.

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
