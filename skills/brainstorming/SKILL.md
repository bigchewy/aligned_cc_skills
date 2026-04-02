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
