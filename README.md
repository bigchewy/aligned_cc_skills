# Aligned

Opinionated skill stack for Claude Code. 30 skills, 13 agents, 62 advisor personas, 135 frameworks, and automated quality gates — from brainstorm to working code.

**[Interactive workflow overview →](docs/workflow.html)** — visual pipeline from brainstorm to merge

## Installation

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

## Quick Start

1. `/aligned:kickstart` — scaffold a new project with standard conventions
2. `/aligned:brainstorming` — explore ideas and strategies (auto-detects software vs business mode)
3. `/aligned:use-advisor` — adopt an expert persona (62 advisors across business, technology, and creative domains)
4. `/aligned:use-framework` — guided walkthroughs of 135 structured decision frameworks

For software projects, the full pipeline: `/aligned:brainstorming` → `/aligned:writing-plans` → auto-launch execution pipeline

## Permissions

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

## Skill Reference

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

## Agents

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

## Hooks

| Event | Script | What It Does |
|-------|--------|-------------|
| UserPromptSubmit | `check-eval-audit.sh` | Triggers `[EVAL AUDIT]` when eval audit is overdue |
| PreToolUse | `auto-approve-worktrees.js` | Auto-approves Edit/Write in worktree directories |
| PreToolUse | `auto-approve-safe-bash-paths.js` | Auto-approves Bash commands targeting `/tmp/` and `~/.claude/` only |
| PostToolUseFailure | `error-tracker.js` | Tracks error patterns for diagnosis |
| PostToolUse | `error-tracker.js` | Tracks Bash errors for diagnosis |
| PostToolUse | `usage-tracker.js` | Tracks Skill/Task usage patterns |

## Advisors

62 advisor prompts ship with the plugin in `advisors/prompts/`.

Use `/aligned:use-advisor` to list all available advisors and adopt one's persona. The `advisors/registry.md` contains per-advisor domain metadata, selection guidelines, and calibration data used by the brainstorming skill's multi-critic selection.

To add a new advisor, use `/aligned:add-advisor` which guides you through creation and registration in `advisors/prompts/`.

## Team Setup

Aligned standardizes development environments across a team at two layers:

**Plugin (cross-project):** Each developer installs the plugin once. All skills, agents, hooks, and advisors are available everywhere.

**Per-project settings:** Running `/aligned:kickstart` creates `.claude/settings.json` with the plugin auto-enabled. Anyone who clones the project gets the same configuration without manual setup.

**Personal overrides:** `.claude/settings.local.json` and `.claude/CLAUDE.local.md` are gitignored — use these for per-developer preferences that shouldn't be shared.

## Project Conventions

Kickstart scaffolds this structure in each project:

- `.claude/settings.json` — Team settings (auto-enables aligned plugin)
- `CLAUDE.md` — Project guide with skill invocation points and iron rules
- `docs/kanban/` — Folder-based task/bug tracking (individual `KB-NNN-slug.md` files)
- `docs/plans/` — Design docs and implementation plans
- `docs/plans/completed/` — Archived completed plans
- `docs/design/design-principles.md` — Design tokens and craft rules
- `docs/lessons-learned/` — Post-mortems (individual files)
- `docs/architecture.md` — Mermaid diagrams for system architecture

## Iron Rules (Software Development)

These rules are enforced by pipeline skills during software development:

1. **Tests first, always.** No production code without a failing test (TDD).
2. **Error path tests for every mock.** Both `mockResolvedValue` and `mockRejectedValue`.
3. **Verify before claiming done.** Run the command, read the output, then assert success.
4. **Root cause first.** Investigate before fixing. No symptom-patching.

## Development

Edit skills directly in this repo — it is the canonical source. All paths in skill files use the `skills/` prefix (not `~/.claude/skills/`).

To test changes locally before publishing:
```bash
claude --plugin-dir /path/to/aligned_cc_skills
```

### Versioning

Semver, pre-1.0:
- **0.x.y** — Breaking changes expected, skills evolving
- **1.0.0** — Stable skill interfaces, backward compatibility commitment

Version bumps happen in `.claude-plugin/plugin.json`.

### Changelog

#### 0.13.0 — Unified Brainstorming Skill
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
