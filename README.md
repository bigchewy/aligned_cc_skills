# Aligned

65 expert advisors with real methodologies, auto-selected by context, available 24/7 in Claude Code. 138 structured frameworks with quality gates that enforce the process — not generic AI advice.

Leaders of growing companies get world-class strategic thinking for their entire team without hiring consultants for every function.

**[Interactive workflow overview →](docs/workflow.html)** — visual pipeline from brainstorm to merge

## What This Looks Like

**Positioning exercise at 11pm.** Invoke `/aligned:brainstorming` and describe your product. The system detects it's a strategy problem and walks you through structured goal clarification, obstacle diagnosis, root cause analysis, and solution design — with gates between each phase so nothing gets skipped. Then a critique panel of 2-4 advisors evaluates the result through their real methodologies. For a positioning exercise, expect April Dunford challenging your differentiation, Richard Rumelt cutting through strategic fluff, or Rob Walling asking whether you've validated willingness to pay. Each critic uses their actual frameworks, not generic AI feedback.

**Sales deck for tomorrow's meeting.** Invoke `/aligned:generate-deck` with your prospect context. The system structures a 9-slide deck using April Dunford's 8-step sales pitch framework, personalized with your prospect's stakeholders, competitive context, and buying trigger. It applies your brand voice, messaging framework, and visual identity. Before delivery, three reviewers evaluate in parallel: a positioning expert checks framework adherence, a behavioral scientist checks cognitive load and decision architecture, and simulated buyer personas flag what resonates and what triggers skepticism. You triage the findings and get a final deck.

**New hire's first strategic decision.** They invoke `/aligned:use-advisor rob-walling` and get Rob Walling's actual decision frameworks — the Stair Step Method, 5 Stages of Product-Market Fit with specific MRR and churn benchmarks, Market-First evaluation. The advisor speaks in his real voice, pushes back on building without evidence, and asks his signature questions. When your project includes company context — competitors, personas, strategy docs — the advisor incorporates that context into the conversation. The quality of strategic thinking doesn't depend on who's in the room.

## Who This Is For

Leaders of growing companies who are scaling decision-making. Teams that need consistent, high-quality thinking without a consultant in every room. Technical and semi-technical founders comfortable with Claude Code.

This is not a prompt library. Not a template collection. Not "better prompts for ChatGPT." The advisors have real opinions, the frameworks enforce real process, and the quality gates don't let you skip steps.

<!-- Get notified when new advisors and frameworks ship: [newsletter signup](TBD) -->

## Start Here

Already installed? Try these to see what aligned does before diving into configuration:

1. **Meet an advisor.** `/aligned:use-advisor april-dunford` — she'll challenge your positioning with her actual methodology.
2. **Run a brainstorm.** `/aligned:brainstorming` with a real problem. The system auto-detects your domain and selects relevant advisors for the critique panel.
3. **Layer in context.** Add competitors, personas, and strategy docs to your project's `CLAUDE.md`. The advisors incorporate your company context into every conversation.

## How It Works

The system encodes expert methodology into executable workflows:

- **65 advisor personas** with real voices, signature questions, failure modes, and calibration data. April Dunford doesn't just "give positioning advice" — she runs her actual 5 Components framework and pushes back on vague differentiation.
- **138 structured frameworks** made interactive and sequential with quality gates. The system enforces the process order and challenges weak answers at each phase.
- **30 skills** that auto-select relevant advisors based on context. A brainstorming session about pricing pulls in different experts than one about product design.
- **Company context incorporation.** When you layer in your competitors, buyer personas, and strategy docs, the advisors operate with your company's specific context — not generic advice.

Think of it as a virtual board of advisors — world-class experts with real methodologies, available 24/7, that incorporate your company's institutional knowledge. The quality of decisions doesn't degrade as the company grows.

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

1. `/aligned:kickstart` — scaffold a new project with standard conventions
2. `/aligned:brainstorming` — explore ideas and strategies (auto-detects software vs business mode)
3. `/aligned:use-advisor` — adopt an expert persona (65 advisors across business, technology, and creative domains)
4. `/aligned:use-framework` — guided walkthroughs of 138 structured decision frameworks

For software projects, the full pipeline: `/aligned:brainstorming` → `/aligned:writing-plans` → auto-launch execution pipeline

### Permissions

To use aligned skills without permission prompts, add these to your `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Skill(aligned:brainstorming)",
      "Skill(aligned:writing-plans)",
      "Skill(aligned:executing-plans)",
      "Skill(aligned:finishing-a-development-branch)",
      "Skill(aligned:systematic-debugging)",
      "Skill(aligned:using-git-worktrees)",
      "Skill(aligned:eval-failure-triage)",
      "Skill(aligned:eval-audit)",
      "Skill(aligned:kickstart)",
      "Skill(aligned:design-principles)",
      "Skill(aligned:test-driven-development)",
      "Skill(aligned:verification-before-completion)",
      "Skill(aligned:use-advisor)",
      "Skill(aligned:use-framework)",
      "Skill(aligned:kanban-resolve)",
      "Skill(aligned:codebase-audit)",
      "Skill(aligned:create-new-skill)",
      "Skill(aligned:add-advisor)",
      "Skill(aligned:add-framework)",
      "Skill(aligned:find-potential-advisors)",
      "Skill(aligned:business-diagnosis)",
      "Skill(aligned:business-executing)",
      "Skill(aligned:business-write-plan)",
      "Skill(aligned:create-design-principles)",
      "Skill(aligned:generate-deck)",
      "Skill(aligned:generate-blog-post)",
      "Skill(aligned:generate-one-pager)",
      "Skill(aligned:persona-panel)",
      "Skill(aligned:create-svg-diagram)",
      "Skill(aligned:claude-profile)"
    ]
  }
}
```

Note: `/aligned:kickstart` auto-creates `.claude/settings.json` with `enabledPlugins: { "aligned": true }` in new projects and sets up skill-level permissions in `~/.claude/settings.json` on first run.

## Reference

### Skill Reference

| Skill | Layer | Invocation | Description |
|-------|-------|------------|-------------|
| brainstorming | Brainstorming | `/aligned:brainstorming` | Explore ideas and strategies — auto-detects software vs business mode |
| use-advisor | Advisor | `/aligned:use-advisor` | Adopt an advisor persona for the conversation |
| use-framework | Framework | `/aligned:use-framework` | Guide through a framework's phases interactively |
| add-advisor | Advisor | `/aligned:add-advisor` | Add a new advisor to the Virtual Board |
| add-framework | Framework | `/aligned:add-framework` | Add a new framework to an existing advisor |
| find-potential-advisors | Advisor | `/aligned:find-potential-advisors` | Research and evaluate potential advisors |
| persona-panel | Content | `/aligned:persona-panel` | Test content against simulated buyer/user personas |
| generate-deck | Content | `/aligned:generate-deck` | Generate branded sales decks with April Dunford framework and expert review panel |
| generate-blog-post | Content | `/aligned:generate-blog-post` | Generate thought leadership blog posts with PIEI narrative arc and 3-reviewer panel |
| generate-one-pager | Content | `/aligned:generate-one-pager` | Generate branded one-pagers and battle cards (placeholder) |
| create-svg-diagram | Content | `/aligned:create-svg-diagram` | Generate diagrams, charts, and visual frameworks for presentations and docs |
| kickstart | Foundation | `/aligned:kickstart` | Scaffold project with conventions, team settings, eval infrastructure |
| design-principles | Foundation | `/aligned:design-principles` | Interactive design discovery with Steve Jobs persona |
| create-design-principles | Foundation | `/aligned:create-design-principles` | Enforce precise, minimal design system (Linear/Notion/Stripe aesthetic) |
| business-diagnosis | Business | `/aligned:business-diagnosis` | Diagnose why business deliverables aren't landing |
| business-executing | Business | `/aligned:business-executing` | Execute business plans with deliverables |
| business-write-plan | Business | `/aligned:business-write-plan` | Write business plans with critique panel |
| writing-plans | Pipeline | `/aligned:writing-plans` | Write implementation plans with dual-critic (Architect + Verifier) |
| executing-plans | Pipeline | `/aligned:executing-plans` | Execute plans task-by-task with checkpoints |
| finishing-a-development-branch | Pipeline | `/aligned:finishing-a-development-branch` | Deployment audit, tests, build, code simplification, merge/PR, plan archival |
| test-driven-development | Methodology | (invoked by pipeline) | TDD enforcement with error path tests |
| verification-before-completion | Methodology | (invoked by pipeline) | Evidence before assertions |
| systematic-debugging | Problem-solving | `/aligned:systematic-debugging` | Root cause investigation with optional multi-agent mode |
| eval-failure-triage | Problem-solving | `/aligned:eval-failure-triage` | Classify LLM eval failures before fixing |
| eval-audit | Problem-solving | `/aligned:eval-audit` | Eval coverage auditor with hook trigger |
| using-git-worktrees | Infrastructure | `/aligned:using-git-worktrees` | Isolated worktree management |
| claude-profile | Infrastructure | `/aligned:claude-profile` | Switch Claude Code accounts and configure directory-specific overrides |
| codebase-audit | Maintenance | `/aligned:codebase-audit` | Multi-dimensional audit: code quality, tests, security, dead code, architecture |
| kanban-resolve | Maintenance | `/aligned:kanban-resolve` | Triage and resolve all Kanban board items in one pass |
| create-new-skill | Meta | `/aligned:create-new-skill` | TDD-based skill creation with pressure testing |

### Agents

| Agent | Description |
|-------|-------------|
| architecture-diagram-generator | Architecture diagrams with SVG and architecture.md updates |
| artifact-verifier | 98% accuracy gate for document fact-checking |
| code-reviewer | Post-implementation review against plan and coding standards |
| code-simplifier | Scans branch changes for simplification opportunities |
| error-diagnosis | Classify error patterns from error-tracker hook data |
| flowchart-generator | Mermaid.js flowcharts for data flows, processes, and decision trees |
| kanban-triage | Validates Kanban items through 5-phase root cause analysis |
| mockup-generator | Self-contained HTML mockups for design-phase visualization |
| session-document-generator | Orchestrates diagram agents to produce consolidated tabbed HTML documents |
| steve-jobs | Design critique persona for brainstorming reviews |
| doc-staleness-detector | Detect stale docs by comparing git history — logs to Kanban, never edits directly |
| project-scanner | Fast codebase scan for brainstorming context (languages, structure, dependencies) |
| worktree-setup | Isolated git worktree creation with safety checks |

### Hooks

| Event | Script | What It Does |
|-------|--------|-------------|
| UserPromptSubmit | `check-eval-audit.sh` | Triggers `[EVAL AUDIT]` when eval audit is overdue |
| PreToolUse | `auto-approve-worktrees.js` | Auto-approves Edit/Write in worktree directories |
| PreToolUse | `auto-approve-safe-bash-paths.js` | Auto-approves Bash commands targeting `/tmp/` and `~/.claude/` only |
| PostToolUseFailure | `error-tracker.js` | Tracks error patterns for diagnosis |
| PostToolUse | `error-tracker.js` | Tracks Bash errors for diagnosis |
| PostToolUse | `usage-tracker.js` | Tracks Skill/Task usage patterns |

### Advisors

65 advisor prompts ship with the plugin in `advisors/prompts/`.

Use `/aligned:use-advisor` to list all available advisors and adopt one's persona. The `advisors/registry.md` contains per-advisor domain metadata, selection guidelines, and calibration data used by the brainstorming skill's multi-critic selection.

To add a new advisor, use `/aligned:add-advisor` which guides you through creation and registration in `advisors/prompts/`.

### Team Setup

Aligned standardizes development environments across a team at two layers:

**Plugin (cross-project):** Each developer installs the plugin once. All skills, agents, hooks, and advisors are available everywhere.

**Per-project settings:** Running `/aligned:kickstart` creates `.claude/settings.json` with the plugin auto-enabled. Anyone who clones the project gets the same configuration without manual setup.

**Personal overrides:** `.claude/settings.local.json` and `.claude/CLAUDE.local.md` are gitignored — use these for per-developer preferences that shouldn't be shared.

### Project Conventions

Kickstart scaffolds this structure in each project:

- `.claude/settings.json` — Team settings (auto-enables aligned plugin)
- `CLAUDE.md` — Project guide with skill invocation points and iron rules
- `docs/kanban/` — Folder-based task/bug tracking (individual `KB-NNN-slug.md` files)
- `docs/plans/` — Design docs and implementation plans
- `docs/plans/completed/` — Archived completed plans
- `docs/design/design-principles.md` — Design tokens and craft rules
- `docs/lessons-learned/` — Post-mortems (individual files)
- `docs/architecture.md` — Mermaid diagrams for system architecture

### Iron Rules (Software Development)

These rules are enforced by pipeline skills during software development:

1. **Tests first, always.** No production code without a failing test (TDD).
2. **Error path tests for every mock.** Both `mockResolvedValue` and `mockRejectedValue`.
3. **Verify before claiming done.** Run the command, read the output, then assert success.
4. **Root cause first.** Investigate before fixing. No symptom-patching.

### Development

Edit skills directly in this repo — it is the canonical source. All paths in skill files use the `skills/` prefix (not `~/.claude/skills/`).

To test changes locally before publishing:
```bash
claude --plugin-dir /path/to/aligned_cc_skills
```

#### Versioning

Semver, pre-1.0:
- **0.x.y** — Breaking changes expected, skills evolving
- **1.0.0** — Stable skill interfaces, backward compatibility commitment

Version bumps happen in `.claude-plugin/plugin.json`.

#### Changelog

##### 0.13.0 — Unified Brainstorming Skill
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
