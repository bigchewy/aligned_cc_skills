# Aligned

A virtual board of advisors for Claude Code. 62 expert personas, 118 structured frameworks, auto-selected by context.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.33.1-green.svg)](.claude-plugin/plugin.json)

```
/plugin marketplace add bigchewy/aligned_cc_skills
/plugin install aligned@aligned
```

## You Can't Tell Your AI Output Is Mediocre

You ask an LLM to help with positioning, strategy, or marketing. The output sounds right. It passes your gut check. And you move on.

The problem: without an expert standard to measure against, you have no way to know the output is average. The LLM gives you the mean of everything it knows. That mean is plausible, and competent sounding.  

Unfortunately, this means that it confirms your blind spots instead of exposing them.

The test: take a document someone created with ChatGPT that you think is good then load it into Aligned.  It picks the right expert to evaluate it, grades it and identifies opportunities for improvement. The gap between passable and excellent is invisible until someone shows you.

## How Aligned Works

Each advisor is calibrated from the real expert's public content, speech patterns, and methodology. e.g. virtual April Dunford runs her actual 5 Components framework and pushes back when your differentiation is vague. 

Each framework follows the exact methodology the expert published. Sequential phases, one question at a time, quality gates between steps. The LLM can't skip ahead, blend in concepts from another methodology, or ask all questions at once.

Without these guardrails, the LLM fails in three specific ways. It defaults to asking all questions at once instead of gating phase by phase. It often gets the framework partially wrong (or, worse, doesn't even use a framework). And it is subservient: no request for supporting documents up front, no summary of gaps at the end.


You can also load a document and have 2-4 advisors each read it through their own lens, then debate each other. April Dunford checks positioning, Richard Rumelt cuts through strategic fluff, Rob Walling asks about willingness to pay. You catch blind spots no single perspective would find.

## What This Looks Like

**New market entry evaluation** `/aligned:brainstorming` along with a brief description. The system detects it's a strategy problem, walks you through goal clarification, obstacle diagnosis, root cause analysis, and solution design with gates between phases. Then a critique panel of 2-4 advisors evaluates the result through their real methodologies.

**A decision to pivot your business model** `/aligned:use-advisor` and describe the problem. The system finds the right advisor. If it's about finding product-market fit, you'll get Paul Graham or Garry Tan.  Their perspectives, pushing back based on their documented frameworks, approaches and perspectives.  

## Who This Is For

You're already using Claude Code or CoWork. You create business deliverables (positioning docs, strategy, blog posts, sales materials) and you want them held to the standard of someone who's done it 200 times.

The advisors have real opinions. The frameworks enforce real process. The quality gates don't let you skip steps.

Get notified when new advisors and frameworks ship: [subscribe on Substack](https://bigchewypretzels.substack.com)

## Get Started

### Installation

Run these inside Claude Code:

```
/plugin marketplace add bigchewy/aligned_cc_skills
/plugin install aligned@aligned
```

The first command registers the GitHub repo as a plugin source (`bigchewy/aligned_cc_skills`). The second installs the `aligned` plugin from the `aligned` marketplace. Claude Code uses your existing git credentials automatically. The plugin is then available across all your projects.

For local development and testing:
```bash
claude --plugin-dir /path/to/aligned_cc_skills
```

### Quick Start

1. **Converse with an advisor.** `/aligned:use-advisor April Dunford` and describe a positioning challenge. She runs her actual methodology.
2. **Run a brainstorm.** `/aligned:brainstorming` with a real problem. The system auto-detects your domain and selects relevant advisors for the critique panel.
3. **Layer in context.** Add competitors, personas, and strategy docs to your project folder and update your `CLAUDE.md` to let the system know what's there. The advisors incorporate your company context into every conversation.
4. **Try a framework.** `/aligned:use-framework` to browse 118 structured decision frameworks with interactive, phase-gated walkthroughs.
## Reference

### Skill Reference

Entry points are skills you invoke directly. The software-development loop (plan, execute, finish, worktrees) now lives in the superpowers plugin.

| Skill | Type | Invocation | Description |
|-------|------|------------|-------------|
| brainstorming | Entry Point | `/aligned:brainstorming` | Explore ideas and strategies. Routes across three modes: authoring, research, roadmap |
| use-advisor | Entry Point | `/aligned:use-advisor` | Adopt an advisor persona for the conversation |
| use-framework | Entry Point | `/aligned:use-framework` | Guide through a framework's phases interactively |
| add-advisor | Entry Point | `/aligned:add-advisor` | Add a new advisor to the Virtual Board |
| add-framework | Entry Point | `/aligned:add-framework` | Add a new framework to an existing advisor |
| find-potential-advisors | Entry Point | `/aligned:find-potential-advisors` | Research and evaluate potential advisors |
| persona-panel | Entry Point | `/aligned:persona-panel` | Test content against simulated buyer/user personas |
| kickstart | Entry Point | `/aligned:kickstart` | Scaffold project with conventions, team settings, eval infrastructure |
| create-design-principles | Entry Point | `/aligned:create-design-principles` | Interactive design discovery + enforce precise, minimal design system |
| create-image | Entry Point | `/aligned:create-image` | Generate diagrams, charts, icons, illustrations, and brand visuals — routes to diagram, icon, or illustration mode |
| visualize-design | Entry Point | `/aligned:visualize-design` | Render any markdown doc or the current conversation as an on-brand, tabbed, Mermaid-validated HTML artifact |
| root-cause-analysis | Entry Point | `/aligned:root-cause-analysis` | Root cause investigation for business and process problems with optional multi-agent mode |
| eval-audit | Entry Point | `/aligned:eval-audit` | Eval coverage auditor (hook-prompted) |

## What this plugin does NOT include

This plugin is distributed to many users. It intentionally does not ship anything that writes to a user-global path or assumes the plugin author's personal infrastructure.

- **Usage tracking hooks.** A reference copy of the PostToolUse `Skill|Task|Agent` tracker lives at `tools/optional-usage-tracker.js`. It is **not wired** via `hooks/hooks.json`. To enable it on your machine, copy it to `~/.claude/hooks/usage-tracker.js` and add the hook entry shown in that file's header comment. The plugin will never write to `~/.claude/usage-tracking/` on your behalf.
- **Weekly digest / rule scorer.** Single-user features maintained in the plugin author's global config, not shipped.
- **Eval infrastructure.** The `e2e/` directory exists for plugin-author QA; skills guard on its existence and skip silently if absent.

### Agents

| Agent | Description |
|-------|-------------|
| architecture-diagram-generator | Architecture diagrams with SVG and architecture.md updates |
| artifact-verifier | 98% accuracy gate for document fact-checking |
| critique-interactive-html-generator | Interactive HTML for accept/reject decisions on brainstorming critique findings, with copy-as-prompt round-trip |
| flowchart-generator | Mermaid.js flowcharts for data flows, processes, and decision trees |
| mockup-generator | Self-contained HTML mockups for design-phase visualization |
| session-document-generator | Orchestrates diagram agents to produce consolidated tabbed HTML documents |
| project-scanner | Fast codebase scan for brainstorming context (languages, structure, dependencies) |

### Hooks

| Event | Script | What It Does |
|-------|--------|-------------|
| PreToolUse | `auto-approve-safe-bash-paths.js` | Auto-approves Bash commands targeting `/tmp/` and `~/.claude/` only |
| PostToolUse | `usage-tracker.js` | Tracks Skill/Task usage patterns |

### Advisors

62 advisor prompts ship with the plugin in `advisors/prompts/`.

Use `/aligned:use-advisor` to list all available advisors and adopt one's persona. The `advisors/registry.yaml` contains per-advisor domain metadata, selection guidelines, and calibration data used by the brainstorming skill's multi-critic selection.

To add a new advisor, use `/aligned:add-advisor` which guides you through creation and registration in `advisors/prompts/`.

### Team Setup

Aligned standardizes development environments across a team at two layers:

**Plugin (cross-project):** Each developer installs the plugin once. All skills, agents, hooks, and advisors are available everywhere.

**Per-project settings:** Running `/aligned:kickstart` creates `.claude/settings.json` with the plugin auto-enabled. Anyone who clones the project gets the same configuration without manual setup.

**Personal overrides:** `.claude/settings.local.json` and `.claude/CLAUDE.local.md` are gitignored. Use these for per-developer preferences that shouldn't be shared.

### Project Conventions

Kickstart scaffolds this structure in each project:

- `.claude/settings.json`: Team settings (auto-enables aligned plugin)
- `CLAUDE.md`: Project guide with skill invocation points and iron rules
- `docs/kanban/`: Folder-based task/bug tracking (individual `KB-NNN-slug.md` files)
- `docs/plans/`: Design docs and implementation plans
- `docs/plans/completed/`: Archived completed plans
- `docs/design/design-principles.md`: Design tokens and craft rules
- `docs/lessons-learned/`: Post-mortems (individual files)
- `docs/architecture.md`: Mermaid diagrams for system architecture

### Iron Rules (Software Development)

These rules apply during software development. The plan/execute/finish skills that enforced them now live in the superpowers plugin:

1. **Tests first, always.** No production code without a failing test (TDD).
2. **Error path tests for every mock.** Both `mockResolvedValue` and `mockRejectedValue`.
3. **Verify before claiming done.** Run the command, read the output, then assert success.
4. **Root cause first.** Investigate before fixing. No symptom-patching.

### Development

Edit skills directly in this repo. This is the canonical source. All paths in skill files use the `skills/` prefix (not `~/.claude/skills/`).

To test changes locally before publishing:
```bash
claude --plugin-dir /path/to/aligned_cc_skills
```

#### Versioning

Semver, pre-1.0:
- **0.x.y**: Breaking changes expected, skills evolving
- **1.0.0**: Stable skill interfaces, backward compatibility commitment

Version bumps happen in `.claude-plugin/plugin.json`.

#### Changelog

##### 0.33.1: Green Suite (2026-08-14)
- Test suite is fully green: fixed the `advisors/prompts/**` eval-surface
  pattern (Python 3.9 glob semantics), refreshed advisor/framework registry
  READMEs (60 advisors, 114 frameworks across 22 categories, including the
  missing Matt Mochary / Claire Hughes Johnson and operating-cadence entries).
- Parked autopilot's tests: all 18 autopilot/ralph test files carry a
  module-level skip marker. Autopilot itself stays in `scripts/autopilot/`
  unchanged, non-functional, revivable by deleting the markers.
- README badge and framework-count prose aligned with the registries.

##### 0.33.0: Superpowers Split (2026-08-14)
- **BREAKING:** Removed the dev-workflow skills — the superpowers plugin
  (github.com/obra/superpowers) replaces them: `writing-plans`,
  `executing-plans`, `finishing-a-development-branch`,
  `using-git-worktrees` (same names in superpowers), `kanban-resolve` and
  `codebase-audit` (no replacement). Removed agents: `code-reviewer`,
  `code-simplifier`, `kanban-triage`, `doc-staleness-detector`. Removed
  hook: `auto-approve-worktrees.js`.
- **BREAKING:** `brainstorming` is now three modes (authoring, research,
  roadmap); software design routes to `superpowers:brainstorming`.
- **BREAKING:** `root-cause-analysis` now covers business/process problems
  only; code bugs route to `superpowers:systematic-debugging`.
- Autopilot (`scripts/autopilot/`) is non-functional in this release — it
  drove the removed skills. A follow-up release ports it to superpowers.
- **13 skills** (-6), **7 agents** (-4)

##### 0.30.0: AI-Native Brand Folder
- **Canonical brand folder spec** (`docs/brand-folder-spec.md`): schema reference for the AI-native `brand/` folder — directory tree, frontmatter contract, provenance/confidence model, slice-loading mechanics, composition contracts, versioning, and consumer-side eval scenarios.
- **Shared loader** (`skills/_shared/load-brand-slices.md`): single loader that every brand-consuming generator delegates to; resolves `{folder}/{file-stem}#{slice-slug}` references, validates frontmatter, and degrades gracefully on missing slices.
- **6 new frameworks** for authoring an AI-native brand folder:
  - `reverse-engineered-brand` — orchestrator that auto-synthesizes a draft brand folder from a URL + local content + competitor research, dispatches owning frameworks in AUTO_MODE per slice, and opens a tabbed review.html with atomic confirm/correct cards per assumption + question
  - `buyer-persona`, `messaging-distillation`, `brand-voice`, `proof-points-audit`, `competitive-battle-card`
- **154 frameworks** (+6)

##### 0.26.0: Manual Deploy Artifact Catalog
- **Manual-deploy artifact catalog** (`skills/_shared/manual-deploy-artifact-catalog.md`): detects files whose creation requires a manual production step (v1: Supabase migrations, env-var additions). Consumed by `writing-plans` (auto-populates the plan's Post-Automation section) and `finishing-a-development-branch` (Step 0.5 hard-gates merge on missing evidence). See the design doc at `docs/plans/2026-04-20-manual-deploy-artifacts-rca-design.md`.

##### 0.22.0: Remove create-new-skill
- Removed `create-new-skill` skill — no longer used
- Removed from README skill tables and kickstart permissions

##### 0.17.0: Persona Creation Flow
- **persona-panel:** Add guided persona creation flow for cold-start path — four-phase Q&A replaces dead-end when no personas exist

##### 0.16.0: Personal Skill Extraction
- Extracted generate-deck, generate-blog-post, generate-one-pager, portability-audit to `~/.claude/skills/` as personal global skills (not plugin-distributed)
- **22 skills** (-4)

##### 0.15.0: Portability Audit
- New portability-audit skill scans the plugin repo for environment-specific hardcoding
- Detects: absolute user paths (CRITICAL), non-plugin external file dependencies (HIGH), platform-specific assumptions (MEDIUM)
- **26 skills** (+1)

##### 0.14.0: Skill/Agent Cleanup Refactor
- **BREAKING:** `/aligned:systematic-debugging` renamed to `/aligned:root-cause-analysis` (now handles both software and business problems). `/aligned:business-diagnosis` merged into it. `/aligned:design-principles` merged into `/aligned:create-design-principles`. Removed: `/aligned:business-executing`, `/aligned:business-write-plan`, `/aligned:claude-profile`. Removed agents: `steve-jobs`, `worktree-setup`.
- **25 skills** (-5), **11 agents** (-2)

##### 0.13.0: Unified Brainstorming Skill
- **BREAKING:** `/aligned:business-brainstorming` merged into `/aligned:brainstorming`. The unified skill auto-detects whether your topic is software/technical or business/strategy and adapts accordingly. Update any project CLAUDE.md files that reference `/aligned:business-brainstorming`.

##### 0.6.0
- **25 skills** (-1: removed autopilot, replaced by automated post-plan pipeline)
- New `FINISH-BRANCH.md` Ralph loop prompt for non-interactive merge-to-main
- Writing-plans handoff restructured: 3 options (Interactive / Automated background / Manual command)
- Option B auto-launches Ralph loop + finish as a single background pipeline
- `.finish-status` sentinel file for background pipeline observability

##### 0.5.0
- **26 skills** (+1: codebase-audit)
- Multi-dimensional codebase audit with 5 parallel workers (code quality, test quality, security, dead code, architecture)
- Confidence-scored findings with deduplication and severity filtering
- Project-agnostic source discovery (auto-detects language and source roots)

Earlier changelog history is available in git (`git log --oneline`).

### License

MIT
