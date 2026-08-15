---
name: brainstorming
description: "Structures creative and strategic work through guided dialogue across three modes — content authoring, research synthesis, and roadmap-mode decomposition of a big intent into a queue of brainstorms. Use before authoring, research, or roadmap work that benefits from structured exploration and expert critique. Software design routes to a dev-workflow plugin such as superpowers."
---

# Brainstorming

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/brainstorming/`. See `skills/_shared/resolve-skill-path.md` for rationale. 

## Overview
A unified brainstorming skill that adapts its process based on what you're
working on. Three modes covering distinct shapes of brainstorm work:

- **Authoring** — structured-document arrangement with framework + domain-advisor panel and optional Research sub-phase; deliverable is a sequenced design doc — curricula, framework prompts, exercise programs, strategy memos, competitive analyses, positioning briefs, market analyses, GTM/sales documents, and diagnostic write-ups.
- **Research** — corpus survey + comparative synthesis with Skeptic Pass; deliverable is a research memo or KB artifact.
- **Roadmap** — decomposition scaffolding for intents too big for one brainstorm; deliverable is a spawn-list of 3–6 paste-ready brainstorming prompts.

## Step 1: Detect Mode and Confirm with User

**Signal precedence:** Topic keywords take priority over environment signals.
A user in a code repo asking about a positioning brief is Authoring mode.
Environment is a tiebreaker when topic keywords are absent.

**Software requests route out.** If the request is designing or building
software (features, components, APIs, refactoring, architecture,
implementation, code, data models — anything shaped as "build / design /
refactor X"): software design and implementation are out of scope for this
plugin. If the superpowers plugin is installed, use
`superpowers:brainstorming`; otherwise install a dev-workflow plugin.
Exception: *diagnosing why an existing system isn't behaving as expected*
("why don't I see the new onboarding flow", "why isn't X firing") stays
here — route to Authoring with the `root-cause-analysis` framework.

**Authoring mode** — structured-document arrangement (content design, strategic document, diagnostic write-up, or any named deliverable):
- Topic signals: curriculum, program design, sequence content,
  exercise sequencing, content design, "what to teach in what order",
  rewrite for audience, voice migration, framework prompt authoring,
  chapter sequencing, competitive analysis, positioning brief,
  strategy memo, market analysis, go-to-market doc, sales pitch,
  battle card, one-pager, deck, presentation, slides, pitch deck, memo,
  report, brief, executive summary, talking points, narrative,
  client deliverable, prospect-specific,
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

**Roadmap mode** — decompose a big intent into a queue of brainstorms:
- Topic signals: "too big for one brainstorm", break a big intent into
  smaller pieces, break down, decompose, components of, large initiative,
  multi-step, multi-phase, multi-stage workflow, spawn list,
  brainstorm queue, orchestrate multiple brainstorms,
  "research → insights → deck", "research first then …", multi-component build
- Environment (tiebreaker): prior spawn-lists (`*-spawn-list.md`) or
  related design docs the new components might reference are present
- **Does NOT match:** A request for a roadmap-shaped *document* (quarterly
  plan, prioritization memo, portfolio doc for stakeholders) — those are
  Authoring with a roadmap-shaped framework, not Roadmap mode

**Always ask the user to confirm.** Even when signals point cleanly at one mode, present an AskUserQuestion with the auto-detected mode pre-selected. The user confirms with one tap or picks another. Exceptions:
- Explicit `--mode authoring|research|roadmap` arg → skip the question.
- This is the second+ brainstorm in the conversation AND the auto-detected mode matches the prior brainstorm's mode → skip the question (session-scoped heuristic; on uncertainty, fall back to always-ask).

Present the 3-way picker AskUserQuestion with these task-vocabulary picker labels:

- **Write a document** — deck, memo, brief, positioning, sales pitch, curriculum, RCA write-up, competitive analysis, any named deliverable authored from a framework → *Authoring*
- **Synthesize research** — compare frameworks, literature review, prior art survey, evidence map → *Research*
- **Break a big intent into a queue of brainstorms** — when one brainstorm session won't fit it (research → insights → deck, multi-component build, multi-step initiative) → *Roadmap*

Pre-select the option that matches your auto-detected mode. The user confirms or redirects.

### Disambiguation Rules

Apply these in order when topic signals overlap multiple modes:

- **Code-design vs Authoring:** If the deliverable is *code that runs* (a feature, refactor, integration, API), the work routes out of this plugin per the routing block in Step 1 — `superpowers:brainstorming` if the superpowers plugin is installed. If the deliverable is *content humans consume* (curriculum, prompts, exercises) even when there's a code seam, Authoring — the canonical test: a brainstorm with a runtime adapter (code) but 70% content-sequencing work routes to Authoring. If the work is *diagnosing why existing code or an existing system isn't behaving as expected* ("why don't I see the new onboarding flow", "why isn't X firing", "this should happen but isn't"), that's Authoring with the `root-cause-analysis` framework — the deliverable is a diagnostic document (Gap → Obstacles → Root Causes → Solutions), not a design doc.
- **Authoring vs Research:** If the deliverable is *an arrangement* (sequence, registry, curriculum, framework-shaped strategic document), Authoring. If the deliverable is *an evidence map / ranked synthesis* with no arrangement output, Research. Authoring includes Research as an optional sub-phase (file-mediated sub-agent fork — see modes/authoring.md).
- **Authoring vs Roadmap:** A roadmap-shaped *document* (quarterly plan, prioritization memo, portfolio doc for stakeholders) is Authoring with a roadmap-shaped framework — the deliverable is a single document humans read. Roadmap mode is when the user wants to *run a sequence of brainstorms* against a big intent — the deliverable is a paste-ready queue, not a stakeholder document. Test: "Will the user paste each entry into a new brainstorming session?" → Roadmap. "Will the user share this with their team?" → Authoring.

**Disambiguation refusal handling:** If the user picks "Other" or types a free-form answer that doesn't map to any mode, ask one follow-up: "Could you describe in one sentence what you want as the deliverable — a design doc, a strategic document, an evidence map, a sequenced curriculum, or a spawn-list of brainstorms to run in sequence?" If still ambiguous after the second question, present an open-text re-prompt: "Describe in your own words what you're trying to produce." Run signal detection on the free-text answer and route to the closest match. If detection still fails, offer a final explicit list (all 3 modes, plus "I'm not sure — let me explore for a few questions first" which routes to Authoring mode since not-knowing-the-shape maps to the broadest container mode).

## Step 2: Project Scan

**Resolve placeholders before dispatching:**
- `{topic}` — a 1–3 word kebab-case slug derived from the user's request (e.g., "pricing-strategy", "auth-refactor"). Ask the user if the request is ambiguous.
- `{project-root}` — the current working directory unless the user specified a different path.

Dispatch a project scan agent via Task tool (subagent_type=general-purpose),
running in the background. Now that mode is known, pass it to the scanner:

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`.
Mode: {research|authoring|roadmap} — emphasize {emphasis-text}
accordingly."

**Per-mode emphasis text:**

| Mode | `{emphasis-text}` |
|---|---|
| Research | literature/KB/registries (`knowledge/`, `frameworks/registry.yaml`, `advisors/registry.yaml`, prior `*-research.md`) |
| Authoring | document corpus — frameworks, advisors, prior arrangements (`frameworks/`, `advisors/`, exercise/lesson registries, `*-design.md` files, brand voice files; for strategic-document work also surface prior competitive/positioning/market memos and any `clients/<name>/` material on the subject) |
| Roadmap  | prior spawn-lists and related design docs that components might reference (`*-spawn-list.md`, `*-design.md`) |

Do not wait for the scan to complete before proceeding to Step 3.

## Step 3: Hand Off to Mode

Read `{base-directory}/references/shared-rules.md` once now. Its three rules (Path Resolution, Re-reading the project scan, Stripping the live-refresh script) apply to every mode. Mode files do not repeat them.

Then read the mode file and the critique checklist for the selected mode using the table below. The shared orchestration file is at `{base-directory}/../_shared/critique-panel-orchestration.md` for every mode.

| Mode      | Mode file                              | Critique checklist                                  |
| --------- | -------------------------------------- | --------------------------------------------------- |
| Research  | `{base-directory}/modes/research.md`   | `{base-directory}/research-critique-checklist.md`   |
| Authoring | `{base-directory}/modes/authoring.md`  | `{base-directory}/authoring-critique-checklist.md`  |
| Roadmap   | `{base-directory}/modes/roadmap.md`    | `{base-directory}/roadmap-critique-checklist.md`    |

**If the mode file cannot be Read, STOP and tell the user the plugin installation may be incomplete.**
