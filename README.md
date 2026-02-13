# Aligned

Opinionated development stack for Claude Code. 14 skills that enforce TDD, eval-driven development, systematic debugging, and design craft — connected into a pipeline from idea to working code.

## Installation

**For others (private repo):**
```bash
claude plugin add github:ericpage/aligned_cc_skills
```

**For local testing:**
```bash
claude --plugin-dir /path/to/aligned_cc_skills
```

## Quick Start

1. Run `/aligned:kickstart` on a new project to scaffold conventions
2. Run `/aligned:design-principles` to define the design direction
3. Run `/aligned:autopilot` for a feature — it chains the full pipeline automatically

## Skill Reference

| Skill | Layer | Invocation | Description |
|-------|-------|------------|-------------|
| kickstart | Foundation | `/aligned:kickstart` | Scaffold project with Aligned conventions |
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
| autopilot | Meta | `/aligned:autopilot` | Full pipeline: idea → design → plan → implement |

## Conventions

Aligned expects (and kickstart scaffolds) this structure:

- `CLAUDE.md` — Project guide referencing Aligned conventions
- `docs/Kanban-board.md` — Task and bug tracking
- `docs/plans/` — Design docs and implementation plans
- `docs/plans/completed/` — Archived completed plans
- `docs/design/design-principles.md` — Design tokens and craft rules (triggers Steve Jobs persona)
- `docs/lessons-learned/` — Folder-based post-mortems (individual files, promoted to `completed/`)
- `docs/architecture.md` — Mermaid diagrams for system architecture
- `docs/ralph_loops/` — Ralph loop prompts for autonomous execution
- `e2e/` — Eval infrastructure (scenarios, config, runner)

## Syncing from Local

Eric's `~/.claude/skills/` is the development environment. To update the plugin after local skill changes:

```bash
cd ~/software/aligned_cc_skills
./scripts/sync-from-local.sh
git diff  # review changes
git add -A && git commit -m "sync: update skills from local"
```

The sync script copies skills and applies sed transforms from `scripts/transforms.txt` to generalize VA-specific references. Skills authored directly in the plugin (kickstart, eval-audit, design-principles) are NOT overwritten by sync.

## Versioning

Semver. Pre-1.0 while building for initial users:
- **0.x.y** — Breaking changes expected, skills evolving
- **1.0.0** — Stable skill interfaces, committed to backward compatibility

Version bumps happen in `plugin.json`. No auto-versioning.

### Changelog

#### 0.1.0
- Initial release: 14 skills ported/created
- Steve Jobs persona integration for design skills
- Multi-agent debugging (high severity mode)
- Eval-audit daily cron
- Sync script for development workflow
