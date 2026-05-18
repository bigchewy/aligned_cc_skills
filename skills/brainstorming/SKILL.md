---
name: brainstorming
description: "Structures creative and strategic work through guided dialogue across five modes — software design, business strategy, research synthesis, content authoring, and multi-feature roadmap. Use before any creative, architectural, or strategic work that benefits from structured exploration and expert critique."
---

# Brainstorming

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/brainstorming/`. See `skills/_shared/resolve-skill-path.md` for rationale. 

## Overview
A unified brainstorming skill that adapts its process based on what you're
working on. Five modes covering distinct shapes of brainstorm work:

- **Software** — fluid Q&A with Architect auto-consult; deliverable is a design doc.
- **Business** — structured 4-phase diagnostic process (Goal → Problems → Root Causes → Solutions); deliverable is an action plan for resolving a diagnosed problem (not a strategic document — those go to Authoring).
- **Research** — corpus survey + comparative synthesis with Skeptic Pass; deliverable is a research memo or KB artifact.
- **Authoring** — structured-document arrangement with framework + domain-advisor panel and optional Research sub-phase; deliverable is a sequenced design doc — curricula, framework prompts, exercise programs, OR strategy memos, competitive analyses, positioning briefs, market analyses, GTM/sales documents.
- **Roadmap** — multi-feature portfolio sequencing with strategy advisors; deliverable is a roadmap + spawn-list portfolio.

## Step 1: Detect Mode
Classify the user's topic into one of five modes:

**Signal precedence:** Topic keywords take priority over environment signals.
A user in a code repo asking about "pricing strategy" is business mode, not
software mode. Environment is a tiebreaker when topic keywords are absent.

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

**Business mode** — diagnostic work with an action-plan deliverable:
- Topic signals (all diagnostic in shape — "something isn't working,
  help me figure out what to do"): "why isn't this working", RCA,
  diagnosis, "what should we do about X", strategy *problem* (not
  strategy *document*), sales/marketing/positioning *issues to
  resolve* (not documents to author), meeting prep for a decision,
  stakeholder conflict, pricing/proposal review where the question
  is "what's wrong" or "what next"
- Environment (tiebreaker): project is docs-only, Obsidian vault, or
  non-code directory AND the request is shaped as a problem to solve

**Research mode** — evidence synthesis, comparative review, literature audit:
- Topic signals: literature review, evidence map, comparative review,
  instrument selection, framework comparison, KB design,
  "what does the literature say", systematic review,
  annotated bibliography
- Environment (tiebreaker): knowledge folders, prior research artifacts,
  or registries are present

**Authoring mode** — structured-document arrangement (content design, strategic document, OR diagnostic write-up):
- Topic signals: curriculum, program design, sequence content,
  exercise sequencing, content design, "what to teach in what order",
  rewrite for audience, voice migration, framework prompt authoring,
  chapter sequencing, **competitive analysis, positioning brief,
  strategy memo, market analysis, go-to-market doc, sales pitch,
  battle card, one-pager, "write a [strategic document]", "build a
  [framework]-shaped document", any request whose deliverable is a
  named document authored from a framework**, **diagnostic-shaped
  questions about existing systems — "why isn't X working", "why
  don't I see Y", "this should happen but isn't", "what's causing
  Z", debug-flavored questions that are asking for an explanation
  of existing behavior rather than a new design (these route to
  Authoring with the `root-cause-analysis` framework and produce a
  diagnostic document — Gap → Obstacles → Root Causes → Solutions)**
- Environment (tiebreaker): content registries, prior curricula,
  brand voice files are present, OR the request's topic matches a
  `domains:` entry in `frameworks/registry.yaml` (e.g.,
  `competitive-analysis`, `positioning`, `market-strategy`,
  `go-to-market`) — when a registered framework matches the topic,
  prefer Authoring

**Roadmap mode** — multi-feature roadmap, portfolio sequencing:
- Topic signals: roadmap, prioritization, portfolio, "what to build next",
  milestone, sequence features, multi-feature build, project plan,
  "too big for one brainstorm"
- Environment (tiebreaker): prior roadmaps, open kanban, or customer asks
  are present

**If signals are clear:** Auto-route and present the mode explanation
block (see below). Proceed to Step 2.

**If signals are mixed or absent:** Apply the disambiguation rules below before asking. If they resolve to one mode, auto-route. Otherwise ask the 5-way question:

> "Which best describes this work: Software design / Business strategy / Research synthesis / Content authoring / Multi-feature roadmap?"

Once answered, present the mode explanation block and proceed to Step 2.

### Disambiguation Rules

Apply these in order when topic signals overlap multiple modes:

- **Software vs Authoring (content):** If the deliverable is *code that runs*, Software. If the deliverable is *content humans consume* (curriculum, prompts, exercises) even when there's a code seam, Authoring. The canonical test: a brainstorm with a runtime adapter (code) but 70% content-sequencing work routes to Authoring.
- **Software vs Authoring (diagnostic):** If the work is *designing or building new code* (a feature, refactor, integration, API), that's Software. If the work is *diagnosing why existing code or an existing system isn't behaving as expected* ("why don't I see the new onboarding flow", "why isn't X firing", "this should happen but isn't"), that's Authoring with the `root-cause-analysis` framework. The deliverable test: a code-side bug being diagnosed produces a diagnostic document (Gap → Obstacles → Root Causes → Solutions), not a design doc. Software's "bugs" signal applies only when the work is *designing the fix*, not when it's *understanding the cause*.
- **Authoring vs Research:** If the deliverable is *an arrangement* (sequence, registry, curriculum, framework-shaped strategic document), Authoring. If the deliverable is *an evidence map / ranked synthesis* with no arrangement output, Research. Authoring includes Research as an optional sub-phase (file-mediated sub-agent fork — see modes/authoring.md).
- **Business vs Roadmap:** If the work is *diagnostic* (why isn't X working, what should we do about Y problem), Business. If the work is *generative portfolio sequencing* (which N things should we build, in what order), Roadmap.
- **Business vs Authoring:** The clarifying test is *what's on the page when we're done.* If the deliverable is an *action plan* — what we'll do differently to address a problem — that's Business (diagnostic four-phase flow). If the deliverable is a *strategic document shaped by a named framework* (competitive analysis, positioning brief, market memo, sales pitch, GTM doc), that's Authoring. "Our positioning isn't landing — why?" is Business (problem to diagnose). "Write a competitive analysis of PLANTED" or "build a positioning brief using Dunford" is Authoring (document to author from a framework). When the topic matches a framework's `domains:` in `frameworks/registry.yaml`, that is a strong signal for Authoring.

**Disambiguation refusal handling:** If the user picks "Other" or types a free-form answer that doesn't map to any of the 5 modes, ask one follow-up: "Could you describe in one sentence what you want as the deliverable — a design doc, a strategy memo, an evidence map, a sequenced curriculum, or a multi-feature roadmap?" If still ambiguous after the second question, do NOT silent-default. Instead, present an open-text re-prompt: "Describe in your own words what you're trying to produce." Run signal detection on the free-text answer and route to the closest match. If detection still fails, offer a final explicit list (all 5 modes, plus "I'm not sure — let me explore for a few questions first" which routes to Business mode for RCA-shaped exploration since not-knowing-the-shape is itself a diagnostic stance).

### Mode Explanation Block (mandatory on every invocation)

After mode selection, present this block before starting any phase work:

> **Brainstorming** — guided dialogue from idea to validated design with expert critique.
>
> **Selected: {Mode Name}** — {one-sentence description of the process}
> *Why:* {brief reason this mode was selected based on topic/environment signals}
>
> **Other modes:**
> - **Build & ship:** Software, Authoring
> - **Diagnose & decide:** Business, Research
> - **Sequence work:** Roadmap
>
> *To switch modes or skip phases, just say so.*

Grouping is editorial display only — no enum in code. "Build & ship" both produce design docs that feed `/aligned:writing-plans`; "Diagnose & decide" both produce decision artifacts; "Sequence work" is the portfolio outlier.

**Software mode description:** "Fluid Q&A with automatic Architect consultation on technical decisions. Produces a validated design doc."

**Business mode description:** "Structured *diagnostic* phases (Goal, Problems, Root Causes, Solutions) with gates. For problems being diagnosed and resolved with an action plan — not for strategic documents being authored. If the deliverable is a document shaped by a framework (competitive analysis, positioning brief, market memo), Authoring mode is the right fit."

**Research mode description:** "Corpus survey, comparative synthesis with Skeptic Pass critique, ranked recommendations with caveats. Produces a research memo or KB artifact."

**Authoring mode description:** "Structured-document arrangement with framework + domain-advisor panel; optional Research sub-phase via file-mediated sub-agent fork. Produces a sequenced design doc — curricula, framework prompts, exercises, OR strategy memos, competitive analyses, positioning briefs, GTM/sales documents."

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
