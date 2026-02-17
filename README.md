# Aligned

Opinionated development stack for Claude Code. 14 skills that enforce TDD, eval-driven development, systematic debugging, and design craft — connected into a pipeline from idea to working code.

## Installation

```
/plugin install github:bigchewy/aligned_cc_skills
```

Run this inside Claude Code. The plugin is then available across all your projects.

For local testing during development:
```bash
claude --plugin-dir /path/to/aligned_cc_skills
```

## Quick Start

1. `/aligned:kickstart` — scaffold a new project with standard conventions (also auto-enables the plugin in the project's `.claude/settings.json`)
2. `/aligned:design-principles` — define the design direction through an interactive session
3. `/aligned:autopilot` — go from idea to working code with minimal interaction

## Skill Reference

| Skill | Layer | Invocation | Description |
|-------|-------|------------|-------------|
| kickstart | Foundation | `/aligned:kickstart` | Scaffold project with conventions, team settings, eval infrastructure |
| design-principles | Foundation | `/aligned:design-principles` | Interactive design discovery with Steve Jobs persona |
| brainstorming | Pipeline | `/aligned:brainstorming` | Explore ideas, generate designs and mockups |
| writing-plans | Pipeline | `/aligned:writing-plans` | Write implementation plans with TDD and critique |
| executing-plans | Pipeline | `/aligned:executing-plans` | Execute plans task-by-task with checkpoints |
| finishing-a-development-branch | Pipeline | `/aligned:finishing-a-development-branch` | Deployment audit, tests, build, merge/PR |
| test-driven-development | Methodology | (invoked by pipeline) | TDD enforcement with error path tests |
| verification-before-completion | Methodology | (invoked by pipeline) | Evidence before assertions |
| systematic-debugging | Problem-solving | `/aligned:systematic-debugging` | Root cause investigation with optional multi-agent mode |
| eval-failure-triage | Problem-solving | `/aligned:eval-failure-triage` | Classify LLM eval failures before fixing |
| eval-audit | Problem-solving | `/aligned:eval-audit` | Daily eval coverage auditor |
| using-git-worktrees | Infrastructure | `/aligned:using-git-worktrees` | Isolated worktree management |
| mockup-generator | Infrastructure | `/aligned:mockup-generator` | Self-contained HTML mockups |
| autopilot | Meta | `/aligned:autopilot` | Full pipeline: idea to design to plan to implement |

## Team Setup

Aligned standardizes development environments across a team at two layers:

**Plugin (cross-project):** Each developer installs the plugin once. All skills are available everywhere.

**Per-project settings:** Running `/aligned:kickstart` creates `.claude/settings.json` with the plugin auto-enabled. Anyone who clones the project gets the same configuration without manual setup.

**Personal overrides:** `.claude/settings.local.json` and `.claude/CLAUDE.local.md` are gitignored — use these for per-developer preferences that shouldn't be shared.

## Project Conventions

Kickstart scaffolds this structure in each project:

- `.claude/settings.json` — Team settings (auto-enables aligned plugin)
- `CLAUDE.md` — Project guide with skill invocation points and iron rules
- `docs/Kanban-board.md` — Task and bug tracking
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

A legacy sync script (`scripts/sync-from-local.sh`) exists from when skills were authored in `~/.claude/skills/` and copied here. It is no longer the intended workflow.

### Versioning

Semver, pre-1.0:
- **0.x.y** — Breaking changes expected, skills evolving
- **1.0.0** — Stable skill interfaces, backward compatibility commitment

Version bumps happen in `.claude-plugin/plugin.json`.

### Changelog

#### 0.1.0
- Initial release: 14 skills
- Steve Jobs persona for design review
- Multi-agent debugging (high severity mode)
- Eval-audit daily cron hook
- Kickstart auto-enables plugin in project settings

## License

MIT
