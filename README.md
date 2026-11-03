# Aligned

A virtual board of advisors for running a company, inside Claude Code and Cowork. 59 expert personas and 102 structured frameworks for strategy, positioning, marketing, sales, product, leadership, and operations, picked for you by context.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.33.98-green.svg)](.claude-plugin/plugin.json)

```
/plugin marketplace add bigchewy/aligned_cc_skills
/plugin install aligned@aligned
```

**See every seat it covers:** [the Aligned org chart](https://claude.ai/artifact/Gy9Hz3geUxwRmzMWrkxJaL) shows a 100-person company seat by seat, which advisors and frameworks fit each role, and where the gaps are.

## What This Is (and Isn't)

Aligned is entirely about business and advisory work: deciding, positioning, selling, leading, and writing the deliverables a company runs on. It is not a coding toolkit. The software-development loop (planning, executing, finishing branches, debugging code) lives in the [superpowers](https://github.com/obra/superpowers) plugin, and Aligned routes software work there.

## You Can't Tell Your AI Output Is Mediocre

You ask an LLM to help with positioning, strategy, or marketing. The output sounds right. It passes your gut check. And you move on.

The problem: without an expert standard to measure against, you have no way to know the output is average. The LLM gives you the mean of everything it knows. That mean is plausible and competent sounding.

Unfortunately, this means it confirms your blind spots instead of exposing them.

The test: take a document someone created with ChatGPT that you think is good, then load it into Aligned. It picks the right expert to evaluate it, grades it, and identifies opportunities for improvement. The gap between passable and excellent is invisible until someone shows you.

## How Aligned Works

Each advisor is calibrated from the real expert's public content, speech patterns, and methodology. Virtual April Dunford runs her actual 5 Components framework and pushes back when your differentiation is vague.

Each framework follows the exact methodology the expert published. Sequential phases, one question at a time, quality gates between steps. The LLM can't skip ahead, blend in concepts from another methodology, or ask all questions at once.

Without these guardrails, the LLM fails in three specific ways. It asks all questions at once instead of gating phase by phase. It often gets the framework partially wrong (or doesn't use one at all). And it is subservient: no request for supporting documents up front, no summary of gaps at the end.

You can also load a document and have 2-4 advisors each read it through their own lens, then debate each other. April Dunford checks positioning, Richard Rumelt cuts through strategic fluff, Rob Walling asks about willingness to pay. You catch blind spots no single perspective would find.

## The Org Chart

Advisors and frameworks are organized around the seats in a real company. `/aligned:org-chart` opens the B2B and B2C charts that ship with the plugin (`skills/org-chart/pages/`): every seat from CEO to support, whether it is **Covered**, **Thin**, or has **Nothing yet**, and for each job in that seat, the command to run.

- [Published org chart](https://claude.ai/artifact/Gy9Hz3geUxwRmzMWrkxJaL)
- Local pages: `skills/org-chart/pages/index.html` (B2B), `b2c.html`, and `background.html` (how the counts were made)

Today marketing, product, sales, people, and the leadership team are well covered. Finance, legal, support, DevOps, and IT have nothing yet. That gap list is the roadmap for new advisors and frameworks.

## What This Looks Like

**New market entry evaluation.** `/aligned:brainstorming` with a brief description. The system detects it's a strategy problem, walks you through goal clarification, obstacle diagnosis, root cause analysis, and solution design with gates between phases. Then a critique panel of 2-4 advisors evaluates the result through their real methodologies.

**A decision to pivot your business model.** `/aligned:use-advisor` and describe the problem. The system finds the right advisor. If it's about finding product-market fit, you'll get Paul Graham or Garry Tan, pushing back based on their documented frameworks and perspectives.

**A seat you haven't hired for yet.** `/aligned:org-chart` and ask "who handles sales development?" It names the seat, its jobs, and the framework to run for each until you hire.

## Who This Is For

Founders, CEOs, and operators using Claude Code or Cowork. You create business deliverables (positioning docs, strategy, operating reviews, sales materials, content) and you want them held to the standard of someone who's done it 200 times.

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

1. **Find your seat.** `/aligned:org-chart` shows which advisors and frameworks fit your role.
2. **Converse with an advisor.** `/aligned:use-advisor April Dunford` and describe a positioning challenge. She runs her actual methodology.
3. **Run a brainstorm.** `/aligned:brainstorming` with a real problem. The system detects your domain and selects relevant advisors for the critique panel.
4. **Try a framework.** `/aligned:use-framework` to browse 102 structured decision frameworks with interactive, phase-gated walkthroughs.
5. **Layer in context.** Add competitors, personas, and strategy docs to your project folder and point to them from your `CLAUDE.md`. The advisors bring your company context into every conversation.

## Reference

### Skill Reference

| Skill | Invocation | Description |
|-------|------------|-------------|
| org-chart | `/aligned:org-chart` | Open the B2B and B2C org charts: every seat, its jobs, and the command to run for each |
| use-advisor | `/aligned:use-advisor` | Adopt an advisor persona for the conversation |
| use-framework | `/aligned:use-framework` | Guide through a framework's phases interactively |
| brainstorming | `/aligned:brainstorming` | Explore ideas and strategies across three modes: authoring, research, roadmap |
| root-cause-analysis | `/aligned:root-cause-analysis` | Root cause investigation for business and process problems, with an optional multi-agent mode |
| persona-panel | `/aligned:persona-panel` | Test content against simulated buyer/user personas |
| create-design-principles | `/aligned:create-design-principles` | Interactive design discovery producing tokens, patterns, and anti-patterns for a brand or product |
| create-image | `/aligned:create-image` | Diagrams, charts, icons, illustrations, and brand visuals |
| visualize-design | `/aligned:visualize-design` | Render any markdown doc or the current conversation as an on-brand, tabbed HTML page |
| add-advisor | `/aligned:add-advisor` | Add a new advisor to the Virtual Board |
| add-framework | `/aligned:add-framework` | Add a new framework to an existing advisor |
| find-potential-advisors | `/aligned:find-potential-advisors` | Research and evaluate potential advisors |
| kickstart | `/aligned:kickstart` | Set up a project folder with Aligned conventions and a `CLAUDE.md` |
| eval-audit | `/aligned:eval-audit` | Check that advisor, framework, and prompt changes have eval coverage (plugin maintainers) |

### Agents

| Agent | Description |
|-------|-------------|
| artifact-verifier | 98% accuracy gate for document fact-checking |
| critique-interactive-html-generator | Interactive HTML for accept/reject decisions on brainstorming critique findings, with copy-as-prompt round-trip |
| project-scanner | Fast project scan for brainstorming context |

### Advisors

59 advisor prompts ship in `advisors/prompts/`, registered in `advisors/registry.yaml` with each advisor's domains, best-for and not-for lines, and the calibration data the brainstorming critique panel uses to pick critics. Browse them in `docs/advisor-catalog.html`, or run `/aligned:use-advisor` with no name to list them.

Advisors built for a single client now live in that client's repo as project-local advisors (see below), so the plugin carries only advisors useful to any company.

To add an advisor, run `/aligned:add-advisor`.

### Frameworks

102 frameworks live in `frameworks/<id>/` (each with `prompt.md`, examples, and anti-examples) and are registered in `frameworks/registry.yaml`. The largest categories are strategy (19), leadership (12), psychology (12), startup (10), and sales (8), followed by product design (7) and positioning (6). Browse them in `docs/framework-catalog.html`.

Framework prompts are interactive scripts with hard WAIT points. Run them through `/aligned:use-framework`, one question at a time.

### Project-Local Advisors and Frameworks

A project can keep its own `advisors/` and `frameworks/` at the project root. Each has a `registry.yaml`, plus `prompts/` for advisors or one folder per framework. They merge with the plugin's registries, and a local entry wins on a matching id. Local frameworks show as `(local)` in listings. Use this for client-specific advisors and internal playbooks.

### Team Setup

**Plugin (cross-project):** Each person installs the plugin once. All skills, agents, and advisors are available everywhere.

**Per-project settings:** `/aligned:kickstart` creates `.claude/settings.json` with the plugin auto-enabled, so anyone who opens the project gets the same setup.

**Personal overrides:** `.claude/settings.local.json` and `.claude/CLAUDE.local.md` are gitignored. Use these for preferences that shouldn't be shared.

## What This Plugin Does NOT Include

This plugin is distributed to many users. It does not ship anything that writes to a user-global path or assumes the author's personal infrastructure.

- **Software-development workflow.** Planning, executing, finishing branches, worktrees, and code debugging live in the superpowers plugin.
- **Usage tracking hooks.** A reference copy of the tracker lives at `tools/optional-usage-tracker.js`. It is **not wired** via `hooks/hooks.json`. To enable it, copy it to `~/.claude/hooks/usage-tracker.js` and add the hook entry shown in that file's header comment.
- **Eval infrastructure.** The `e2e/` directory is for plugin-author QA; skills check for it and skip silently if it is absent.

## Development

Edit skills directly in this repo; it is the canonical source. All paths in skill files use the `skills/` prefix (not `~/.claude/skills/`). See `CLAUDE.md` and `CONTRIBUTING.md` for conventions.

To test changes locally:
```bash
claude --plugin-dir /path/to/aligned_cc_skills
```

### Versioning

Semver, pre-1.0. `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` must match.
- **0.x.y**: Breaking changes expected, skills evolving
- **1.0.0**: Stable skill interfaces, backward compatibility commitment

### Changelog

#### 0.33.x: Business Focus and the Org Chart (2026-08 to 2026-11)
- New `/aligned:org-chart` skill with B2B and B2C org chart pages: every seat, its coverage, its jobs, and the command for each.
- Narrowed to business and advisory work. Advisors built for single clients moved to those clients' repos as project-local advisors; nonprofit and solo-creator advisors were removed. Coach Eric is now a CEO coach.
- New advisors since 0.33.1 include Adham Dannaway, Annie Duke, Jason Fried, Aleyda Solis, Michael Bolton, Adam Shostack, Michael Bierut, and Cole Nussbaumer Knaflic.
- **59 advisors, 102 frameworks, 14 skills, 3 agents.**

#### 0.33.1: Green Suite (2026-08-14)
- Test suite is fully green: fixed the `advisors/prompts/**` eval-surface
  pattern (Python 3.9 glob semantics), refreshed advisor/framework registry
  READMEs (60 advisors, 114 frameworks across 22 categories, including the
  missing Matt Mochary / Claire Hughes Johnson and operating-cadence entries).
- Parked autopilot's tests: all 18 autopilot/ralph test files carry a
  module-level skip marker. Autopilot itself stays in `scripts/autopilot/`
  unchanged, non-functional, revivable by deleting the markers.
- README badge and framework-count prose aligned with the registries.

#### 0.33.0: Superpowers Split (2026-08-14)
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

#### 0.30.0: AI-Native Brand Folder
- **Canonical brand folder spec** (`docs/brand-folder-spec.md`): schema reference for the AI-native `brand/` folder — directory tree, frontmatter contract, provenance/confidence model, slice-loading mechanics, composition contracts, versioning, and consumer-side eval scenarios.
- **Shared loader** (`skills/_shared/load-brand-slices.md`): single loader that every brand-consuming generator delegates to; resolves `{folder}/{file-stem}#{slice-slug}` references, validates frontmatter, and degrades gracefully on missing slices.
- **6 new frameworks** for authoring an AI-native brand folder:
  - `reverse-engineered-brand` — orchestrator that auto-synthesizes a draft brand folder from a URL + local content + competitor research, dispatches owning frameworks in AUTO_MODE per slice, and opens a tabbed review.html with atomic confirm/correct cards per assumption + question
  - `buyer-persona`, `messaging-distillation`, `brand-voice`, `proof-points-audit`, `competitive-battle-card`
- **154 frameworks** (+6)

#### 0.26.0: Manual Deploy Artifact Catalog
- **Manual-deploy artifact catalog** (`skills/_shared/manual-deploy-artifact-catalog.md`): detects files whose creation requires a manual production step (v1: Supabase migrations, env-var additions). Consumed by `writing-plans` (auto-populates the plan's Post-Automation section) and `finishing-a-development-branch` (Step 0.5 hard-gates merge on missing evidence). See the design doc at `docs/plans/2026-04-20-manual-deploy-artifacts-rca-design.md`.

#### 0.22.0: Remove create-new-skill
- Removed `create-new-skill` skill — no longer used
- Removed from README skill tables and kickstart permissions

#### 0.17.0: Persona Creation Flow
- **persona-panel:** Add guided persona creation flow for cold-start path — four-phase Q&A replaces dead-end when no personas exist

#### 0.16.0: Personal Skill Extraction
- Extracted generate-deck, generate-blog-post, generate-one-pager, portability-audit to `~/.claude/skills/` as personal global skills (not plugin-distributed)
- **22 skills** (-4)

#### 0.15.0: Portability Audit
- New portability-audit skill scans the plugin repo for environment-specific hardcoding
- Detects: absolute user paths (CRITICAL), non-plugin external file dependencies (HIGH), platform-specific assumptions (MEDIUM)
- **26 skills** (+1)

#### 0.14.0: Skill/Agent Cleanup Refactor
- **BREAKING:** `/aligned:systematic-debugging` renamed to `/aligned:root-cause-analysis` (now handles both software and business problems). `/aligned:business-diagnosis` merged into it. `/aligned:design-principles` merged into `/aligned:create-design-principles`. Removed: `/aligned:business-executing`, `/aligned:business-write-plan`, `/aligned:claude-profile`. Removed agents: `steve-jobs`, `worktree-setup`.
- **25 skills** (-5), **11 agents** (-2)

#### 0.13.0: Unified Brainstorming Skill
- **BREAKING:** `/aligned:business-brainstorming` merged into `/aligned:brainstorming`. The unified skill auto-detects whether your topic is software/technical or business/strategy and adapts accordingly. Update any project CLAUDE.md files that reference `/aligned:business-brainstorming`.

#### 0.6.0
- **25 skills** (-1: removed autopilot, replaced by automated post-plan pipeline)
- New `FINISH-BRANCH.md` Ralph loop prompt for non-interactive merge-to-main
- Writing-plans handoff restructured: 3 options (Interactive / Automated background / Manual command)
- Option B auto-launches Ralph loop + finish as a single background pipeline
- `.finish-status` sentinel file for background pipeline observability

#### 0.5.0
- **26 skills** (+1: codebase-audit)
- Multi-dimensional codebase audit with 5 parallel workers (code quality, test quality, security, dead code, architecture)
- Confidence-scored findings with deduplication and severity filtering
- Project-agnostic source discovery (auto-detects language and source roots)

Earlier changelog history is available in git (`git log --oneline`).

## License

MIT
