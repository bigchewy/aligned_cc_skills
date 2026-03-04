# Aligned

Opinionated development stack for Claude Code. 25 skills, 8 agents, 62 advisor personas, and automated quality gates — connected into a pipeline from idea to working code.

## Installation

Run these inside Claude Code (the repo is private — you'll need collaborator access):

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

1. `/aligned:kickstart` — scaffold a new project with standard conventions (also auto-enables the plugin in the project's `.claude/settings.json`)
2. `/aligned:design-principles` — define the design direction through an interactive session
3. `/aligned:brainstorming` → `/aligned:writing-plans` → auto-launch pipeline (brainstorm, plan, then confirm to execute + merge in background)

See [docs/workflow.html](docs/workflow.html) for an interactive visual overview of the full pipeline.

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
      "Skill(aligned:business-brainstorming)",
      "Skill(aligned:business-diagnosis)",
      "Skill(aligned:business-executing)",
      "Skill(aligned:business-write-plan)",
      "Skill(aligned:create-design-principles)"
    ]
  }
}
```

Note: `/aligned:kickstart` auto-creates `.claude/settings.json` with `enabledPlugins: { "aligned": true }` in new projects, but skill-level permissions must be added to the user's `~/.claude/settings.json`.

### Recommended: Bash path auto-approve hook

Reduces permission prompt noise from skills that use `/tmp/` and `~/.claude/` paths. See [docs/recommended-hooks.md](docs/recommended-hooks.md) for setup.

## Skill Reference

| Skill | Layer | Invocation | Description |
|-------|-------|------------|-------------|
| kickstart | Foundation | `/aligned:kickstart` | Scaffold project with conventions, team settings, eval infrastructure |
| design-principles | Foundation | `/aligned:design-principles` | Interactive design discovery with Steve Jobs persona |
| create-design-principles | Foundation | `/aligned:create-design-principles` | Enforce precise, minimal design system (Linear/Notion/Stripe aesthetic) |
| brainstorming | Pipeline | `/aligned:brainstorming` | Explore ideas, generate designs with multi-critic review |
| business-brainstorming | Business | `/aligned:business-brainstorming` | Explore business problems, strategies, decisions |
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
| use-advisor | Advisor | `/aligned:use-advisor` | Adopt an advisor persona for the conversation |
| use-framework | Framework | `/aligned:use-framework` | Guide through a framework's phases interactively |
| add-advisor | Advisor | `/aligned:add-advisor` | Add a new advisor to the Virtual Board |
| add-framework | Framework | `/aligned:add-framework` | Add a new framework to an existing advisor |
| find-potential-advisors | Advisor | `/aligned:find-potential-advisors` | Research and evaluate potential advisors |
| codebase-audit | Maintenance | `/aligned:codebase-audit` | Multi-dimensional audit: code quality, tests, security, dead code, architecture |
| kanban-resolve | Maintenance | `/aligned:kanban-resolve` | Triage and resolve all Kanban board items in one pass |
| create-new-skill | Meta | `/aligned:create-new-skill` | TDD-based skill creation with pressure testing |

## Agents

| Agent | Description |
|-------|-------------|
| steve-jobs | Design critique persona for brainstorming reviews |
| code-reviewer | Post-implementation review against plan and coding standards |
| code-simplifier | Scans branch changes for simplification opportunities |
| mockup-generator | Self-contained HTML mockups for design-phase visualization |
| kanban-triage | Validates Kanban items through 5-phase root cause analysis |
| worktree-setup | Isolated git worktree creation with safety checks |
| error-diagnosis | Classify error patterns from error-tracker hook data |
| artifact-verifier | 98% accuracy gate for document fact-checking |

## Hooks

| Event | Script | What It Does |
|-------|--------|-------------|
| UserPromptSubmit | `check-eval-audit.sh` | Triggers `[EVAL AUDIT]` when eval audit is overdue |
| PreToolUse | `auto-approve-worktrees.js` | Auto-approves Edit/Write in worktree directories |
| PreToolUse | `auto-approve-safe-bash-paths.js` | Auto-approves Bash commands targeting `/tmp/` and `~/.claude/` only (recommended, see Permissions) |
| PostToolUseFailure | `error-tracker.js` | Tracks error patterns for diagnosis |
| PostToolUse | `error-tracker.js` | Tracks Bash errors for diagnosis |
| PostToolUse | `usage-tracker.js` | Tracks Skill/Task usage patterns |

## Advisors

62 advisor prompts ship with the plugin across 3 categories:

| Category | Count | Source |
|----------|-------|--------|
| va-web-app | 42 | Virtual Board of Advisors app |
| epch-projects | 14 | Business and strategy advisors |
| .claude | 6 | Technical advisors for Claude Code |

Use `/aligned:use-advisor` to list all available advisors and adopt one's persona. The `advisors/registry.md` contains per-advisor domain metadata, selection guidelines, and calibration data used by the brainstorming skill's multi-critic selection.

To add custom advisors beyond what the plugin ships, create `.md` files in `~/.claude/advisors/prompts/{repo-name}/` following the "You are [Name], ..." format.

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
- `docs/ralph_loops/` — Ralph loop prompts for autonomous execution
- `e2e/` — Eval infrastructure (scenarios, config, runner)

## Iron Rules

These are enforced across all skills:

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

#### 0.3.0
- **25 skills** (+8: add-advisor, add-framework, find-potential-advisors, business-brainstorming, business-diagnosis, business-executing, business-write-plan, create-design-principles)
- **8 agents** (+3: worktree-setup, error-diagnosis, artifact-verifier)
- Enhanced eval-failure-triage with infrastructure pre-check and trend analysis
- Error-diagnosis agent wired in CLAUDE.md for hook-triggered dispatch

#### 0.2.0 (Breaking)
- **17 skills** (added: kanban-resolve, create-new-skill, use-advisor, use-framework)
- **5 agents** (added: code-reviewer, code-simplifier, mockup-generator, kanban-triage)
- **62 advisor prompts** shipped with plugin (va-web-app, epch-projects, .claude)
- **130 frameworks** shipped with plugin
- **5 hook scripts** with 4 event types configured
- Multi-critic brainstorming (opus, domain-selected from advisor pool)
- Dual-critic writing-plans (Architect + Verifier, parallel)
- Code simplification scan in finishing-a-development-branch (Step 1d)
- Plan archival in finishing-a-development-branch (Step 6)
- Eval-audit hook with threshold comparison
- Behavioral guardrails in CLAUDE.md (TDD, verification discipline, auto-critique)
- **Breaking:** Kanban format changed from single-file `docs/Kanban-board.md` to folder-based `docs/kanban/` with individual `KB-NNN-slug.md` files. Existing projects using v0.1.0 must migrate: create `docs/kanban/{todo,in-progress,done,did_not_complete}/` directories and a `.counter` file.

#### 0.1.0
- Initial release: 14 skills
- Steve Jobs persona for design review
- Multi-agent debugging (high severity mode)
- Eval-audit daily cron hook
- Kickstart auto-enables plugin in project settings

## License

MIT
