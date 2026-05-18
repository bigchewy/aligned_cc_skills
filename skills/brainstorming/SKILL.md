---
name: brainstorming
description: "Structures creative and strategic work through guided dialogue across four modes — software design, content authoring, research synthesis, and multi-feature roadmap. Use before any creative, architectural, or strategic work that benefits from structured exploration and expert critique."
---

# Brainstorming

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/brainstorming/`. See `skills/_shared/resolve-skill-path.md` for rationale. 

## Overview
A unified brainstorming skill that adapts its process based on what you're
working on. Four modes covering distinct shapes of brainstorm work:

- **Software** — fluid Q&A with Architect auto-consult; deliverable is a design doc.
- **Authoring** — structured-document arrangement with framework + domain-advisor panel and optional Research sub-phase; deliverable is a sequenced design doc — curricula, framework prompts, exercise programs, strategy memos, competitive analyses, positioning briefs, market analyses, GTM/sales documents, and diagnostic write-ups.
- **Research** — corpus survey + comparative synthesis with Skeptic Pass; deliverable is a research memo or KB artifact.
- **Roadmap** — multi-feature portfolio sequencing with strategy advisors; deliverable is a roadmap + spawn-list portfolio.

## Step 1: Detect Mode and Confirm with User

**Signal precedence:** Topic keywords take priority over environment signals.
A user in a code repo asking about a positioning brief is Authoring mode, not
Software mode. Environment is a tiebreaker when topic keywords are absent.

**Software mode** — building, modifying, or designing software (generative work):
- Topic signals: features, components, APIs, refactoring, architecture,
  implementation, code, testing, data models — anything shaped as
  "build / design / refactor X." Bug-shaped requests stay in Software ONLY
  when the work is *designing the fix* (e.g., "design the auth rewrite that
  resolves the bug") — *diagnosing why an existing bug is happening* routes
  to Authoring with the `root-cause-analysis` framework instead.
- Environment (tiebreaker): project contains code files (package.json,
  Cargo.toml, go.mod, pyproject.toml, etc.) AND the request is shaped as
  generative work, not diagnostic

**Authoring mode** — structured-document arrangement (content design, strategic document, diagnostic write-up, or any named deliverable):
- Topic signals: curriculum, program design, sequence content,
  exercise sequencing, content design, "what to teach in what order",
  rewrite for audience, voice migration, framework prompt authoring,
  chapter sequencing, competitive analysis, positioning brief,
  strategy memo, market analysis, go-to-market doc, sales pitch,
  battle card, one-pager, deck, presentation, pitch deck, memo,
  "write a [strategic document]", "build a [framework]-shaped document",
  any request whose deliverable is a named document authored from a framework,
  diagnostic-shaped questions about existing systems — "why isn't X working",
  "why don't I see Y", "this should happen but isn't", "what's causing Z",
  debug-flavored questions asking for an explanation of existing behavior
  rather than a new design (these route to Authoring with the
  `root-cause-analysis` framework and produce a diagnostic document —
  Gap → Obstacles → Root Causes → Solutions), "why isn't this working",
  RCA, diagnosis, "what should we do about X", stakeholder conflict,
  meeting prep for a decision
- Environment (tiebreaker): content registries, prior curricula,
  brand voice files are present, OR the request's topic matches a
  `domains:` entry in `frameworks/registry.yaml` (e.g.,
  `competitive-analysis`, `positioning`, `market-strategy`,
  `go-to-market`) — when a registered framework matches the topic,
  prefer Authoring

**Research mode** — evidence synthesis, comparative review, literature audit:
- Topic signals: literature review, evidence map, comparative review,
  instrument selection, framework comparison, KB design,
  "what does the literature say", systematic review,
  annotated bibliography
- Environment (tiebreaker): knowledge folders, prior research artifacts,
  or registries are present

**Roadmap mode** — multi-feature roadmap, portfolio sequencing:
- Topic signals: roadmap, prioritization, portfolio, "what to build next",
  milestone, sequence features, multi-feature build, project plan,
  "too big for one brainstorm", break a big idea into smaller pieces,
  decompose, big idea, spawn list
- Environment (tiebreaker): prior roadmaps, open kanban, or customer asks
  are present

**Always ask the user to confirm.** Even when signals point cleanly at one mode, present an AskUserQuestion with the auto-detected mode pre-selected. The user confirms with one tap or picks another. Exceptions:
- Explicit `--mode software|authoring|research|roadmap` arg → skip the question.
- This is the second+ brainstorm in the conversation AND the auto-detected mode matches the prior brainstorm's mode → skip the question (session-scoped heuristic; on uncertainty, fall back to always-ask).

Present the AskUserQuestion with these task-vocabulary picker labels:

- **Write a document** — deck, memo, brief, positioning, sales pitch, curriculum, RCA write-up, competitive analysis, any named deliverable authored from a framework → *Authoring*
- **Design a code change** — feature, refactor, integration, schema, architecture decision → *Software*
- **Synthesize research** — compare frameworks, literature review, prior art survey, evidence map → *Research*
- **Break a big initiative into smaller pieces** — roadmap, multi-feature breakdown, portfolio sequencing, spawn list → *Roadmap*

Pre-select the option that matches your auto-detected mode. The user confirms or redirects.

### Disambiguation Rules

Apply these in order when topic signals overlap multiple modes:

- **Software vs Authoring (content):** If the deliverable is *code that runs*, Software. If the deliverable is *content humans consume* (curriculum, prompts, exercises) even when there's a code seam, Authoring. The canonical test: a brainstorm with a runtime adapter (code) but 70% content-sequencing work routes to Authoring.
- **Software vs Authoring (diagnostic):** If the work is *designing or building new code* (a feature, refactor, integration, API), that's Software. If the work is *diagnosing why existing code or an existing system isn't behaving as expected* ("why don't I see the new onboarding flow", "why isn't X firing", "this should happen but isn't"), that's Authoring with the `root-cause-analysis` framework. The deliverable test: a code-side bug being diagnosed produces a diagnostic document (Gap → Obstacles → Root Causes → Solutions), not a design doc.
- **Authoring vs Research:** If the deliverable is *an arrangement* (sequence, registry, curriculum, framework-shaped strategic document), Authoring. If the deliverable is *an evidence map / ranked synthesis* with no arrangement output, Research. Authoring includes Research as an optional sub-phase (file-mediated sub-agent fork — see modes/authoring.md).

**Disambiguation refusal handling:** If the user picks "Other" or types a free-form answer that doesn't map to any mode, ask one follow-up: "Could you describe in one sentence what you want as the deliverable — a design doc, a strategic document, an evidence map, a sequenced curriculum, or a multi-feature roadmap?" If still ambiguous after the second question, present an open-text re-prompt: "Describe in your own words what you're trying to produce." Run signal detection on the free-text answer and route to the closest match. If detection still fails, offer a final explicit list (all 4 modes, plus "I'm not sure — let me explore for a few questions first" which routes to Authoring mode since not-knowing-the-shape maps to the broadest container mode).

### Mode Explanation Block (mandatory on every invocation)

After mode selection, present this block before starting any phase work:

> **Brainstorming** — guided dialogue from idea to validated design with expert critique.
>
> **Selected: {Mode Name}** — {one-sentence description of the process}
> *Why:* {brief reason this mode was selected based on topic/environment signals}
>
> **Other modes:**
> - **Build & ship:** Software, Authoring
> - **Synthesize or sequence:** Research, Roadmap
>
> *To switch modes or skip phases, just say so.*

**Software mode description:** "Fluid Q&A with automatic Architect consultation on technical decisions. Produces a validated design doc."

**Research mode description:** "Corpus survey, comparative synthesis with Skeptic Pass critique, ranked recommendations with caveats. Produces a research memo or KB artifact."

**Authoring mode description:** "Structured-document arrangement with framework + domain-advisor panel; optional Research sub-phase via file-mediated sub-agent fork. Produces a sequenced design doc — curricula, framework prompts, exercises, strategy memos, competitive analyses, positioning briefs, GTM/sales documents, or diagnostic write-ups."

**Roadmap mode description:** "Portfolio sequencing with strategy advisors (Christensen, Rumelt, Eric Ries — plus Cagan when available). Produces a roadmap + spawn-list portfolio whose entries seed future brainstorms."

## Step 2: Project Scan

**Resolve placeholders before dispatching:**
- `{topic}` — a 1–3 word kebab-case slug derived from the user's request (e.g., "pricing-strategy", "auth-refactor"). Ask the user if the request is ambiguous.
- `{project-root}` — the current working directory unless the user specified a different path.

Dispatch a project scan agent via Task tool (subagent_type=general-purpose),
running in the background. Now that mode is known, pass it to the scanner:

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`.
Mode: {software|business|research|authoring|roadmap} — emphasize {emphasis-text}
accordingly."

**Per-mode emphasis text:**

| Mode | `{emphasis-text}` |
|---|---|
| Software | code artifacts (package.json, src/, architecture.md, recent commits) |
| Business | domain materials (positioning, meeting notes, prior strategy, stakeholders) |
| Research | literature/KB/registries (`knowledge/`, `frameworks/registry.yaml`, `advisors/registry.yaml`, prior `*-research.md`) |
| Authoring | document corpus — frameworks, advisors, prior arrangements (`frameworks/`, `advisors/`, exercise/lesson registries, `*-design.md` files, brand voice files; for strategic-document work also surface prior competitive/positioning/market memos and any `clients/<name>/` material on the subject) |
| Roadmap  | prior roadmaps + open kanban + customer asks (`*-roadmap.md`, `*-portfolio.md`, `docs/kanban/`, `clients/*/`) |

Do not wait for the scan to complete before proceeding to Step 3.

## Step 3: Hand Off to Mode

Read `{base-directory}/references/shared-rules.md` once now. Its three rules (Path Resolution, Re-reading the project scan, Stripping the live-refresh script) apply to every mode. Mode files do not repeat them.

Then read the mode file and the critique checklist for the selected mode using the table below. The shared orchestration file is at `{base-directory}/../_shared/critique-panel-orchestration.md` for every mode.

| Mode      | Mode file                              | Critique checklist                                  |
| --------- | -------------------------------------- | --------------------------------------------------- |
| Software  | `{base-directory}/modes/software.md`   | `{base-directory}/design-critique-checklist.md`     |
| Business  | `{base-directory}/modes/business.md`   | `{base-directory}/business-critique-checklist.md`   |
| Research  | `{base-directory}/modes/research.md`   | `{base-directory}/research-critique-checklist.md`   |
| Authoring | `{base-directory}/modes/authoring.md`  | `{base-directory}/authoring-critique-checklist.md`  |
| Roadmap   | `{base-directory}/modes/roadmap.md`    | `{base-directory}/roadmap-critique-checklist.md`    |

**If the mode file cannot be Read, STOP and tell the user the plugin installation may be incomplete.**
