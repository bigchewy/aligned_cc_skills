# Public Release Preparation — Design Document

**Date:** 2026-04-02
**Status:** Draft (post-critique)
**Version target:** 0.13.0 (alongside brainstorming unification)

## Goal

Prepare the aligned Claude Code plugin repo for public release. Two workstreams: (1) consolidate split-brain infrastructure between `~/.claude/` and the plugin repo, (2) remove internal development artifacts and reframe for a community-building launch.

## Business Decisions

- **Audience:** Both individual Claude Code power users and teams
- **Goal:** Community building — welcoming, well-documented, invites contribution
- **Identity:** Lead with universal value (brainstorming, advisors, structured thinking), not software-specific
- **Personal references:** Keep as-is, including Wise Eric advisor — authenticity is the brand
- **Placeholder skills:** Ship generate-one-pager as-is with under-construction message
- **Community infra:** Add CONTRIBUTING.md + GitHub issue/PR templates

## Execution Order

Workstreams have implicit dependencies. Execute in this order:

1. **1a.** Port doc-staleness-detector (copy, patch, test, commit)
2. **2a.** Remove internal artifacts (plans, kanban items, mockups, investigations, etc.)
3. **2b.** Preserve directory structure (kanban, plans with .gitkeep files)
4. **2c.** README overhaul (after file removals so counts are accurate)
5. **2e.** Identity reframe (part of README overhaul)
6. **2d.** Add community infrastructure (CONTRIBUTING.md, GitHub templates)
7. **Release gate checklist** — run all verification steps
8. **1b.** Author's machine cleanup (after release is verified)

## Workstream 1: Infrastructure Consolidation

### 1a. Move doc-staleness-detector agent into plugin

1. Copy `~/.claude/agents/doc-staleness-detector.md` to `agents/doc-staleness-detector.md` in the plugin repo
2. Patch: remove the `node ~/.claude/analytics/generate.js` call (personal infrastructure dependency)
3. Test: verify the agent can be dispatched from a project with `docs/` directory
4. Commit the agent

The agent is general-purpose — works on any project with a `docs/` directory and kanban board.

### 1b. Author's machine cleanup (not a repo change — do AFTER release is verified)

Remove 4 duplicated hook entries from `~/.claude/settings.json`:
- PreToolUse: `auto-approve-worktrees.js`, `auto-approve-safe-bash-paths.js`
- PostToolUseFailure: `error-tracker.js`
- PostToolUse: `error-tracker.js`, `usage-tracker.js`

The plugin's `hooks.json` handles all of these via `${CLAUDE_PLUGIN_ROOT}`. Keep in `~/.claude/settings.json`:
- SessionStart → `check-cron-results.sh`
- UserPromptSubmit → `check-test-audit.sh`

### 1c. Items that stay global (NOT in plugin)

- `code-simplifier-full.md` — hardcoded to specific Next.js project paths, not general-purpose
- `audit-settings.md` — audits `~/.claude/settings.json` specifically
- `crons/` — requires macOS launchd, can't be plugin-managed
- `check-cron-results.sh` — reads launchd cron state
- `check-test-audit.sh` — personal workflow enforcement

## Workstream 2: Public Release Cleanup

### 2a. Remove from repo

| Path | Reason |
|------|--------|
| `docs/plans/*` (all contents, including `completed/`) | Internal development plans with personal paths |
| `docs/kanban/todo/*`, `done/*`, `did_not_complete/*` | Internal bug tracking for the plugin itself |
| `docs/investigations/` | Internal bug investigation notes |
| `docs/mockups/` | Design mockups from development |
| `docs/prompts/` | Internal ralph loop prompt templates |
| `docs/2026-03-13-autopilot-phase1-heartbeat-design.md` | Stray plan doc |
| `e2e/` | One file with commented-out test specs |
| `scripts/` | autocommit.log (228KB) + packaging script |
| `visual-documentation-plugin/` | Separate plugin, wrong repo |
| `.skip-doc-staleness` | Internal flag file |
| `skills/generate-blog-post/references/ewp-site-setup.md` | Personal website setup guide |

Untracked files to delete (not in git):
- `erics-advisory-skills.plugin`
- `zid1vQxP`

Already gitignored (verify):
- `.autopilot-log`
- `aligned-cowork.zip`

### 2b. Preserve directory structure

Keep these directories with `.gitkeep` files:
- `docs/kanban/todo/`, `in-progress/`, `done/`, `did_not_complete/` — keep existing `.counter` value (do NOT reset — avoids KB ID collisions with git history)
- `docs/plans/`, `docs/plans/completed/` — skills write plan files here in consumer projects

### 2c. README overhaul

1. **Headline:** Change from "Opinionated development stack" to something universal (e.g., "Opinionated skill stack for Claude Code")
2. **Description:** Lead with brainstorming, advisors, structured thinking — not TDD and evals
3. **Private repo language:** Remove "you'll need collaborator access"
4. **Agent table:** Add `project-scanner.md` (12 agents, not 11)
5. **Changelog:** Stale (stops at v0.6.0). Either update through v0.12.0 or trim to recent versions.
6. **plugin.json description:** Update to 62 advisor personas, 135 frameworks. Reframe description to match universal positioning.

### 2d. Add community infrastructure

- `CONTRIBUTING.md` — contributor guidelines, skill anatomy, testing approach, PR expectations
- `.github/ISSUE_TEMPLATE/bug_report.md` — bug report template
- `.github/ISSUE_TEMPLATE/feature_request.md` — feature request template
- `.github/pull_request_template.md` — PR template

### 2e. Reframe identity

The README Quick Start, Iron Rules, and Workflows sections are software-centric. Update to:
- Quick Start: Lead with kickstart → brainstorming → advisors (universal), then mention the software pipeline as one track
- Iron Rules: Keep for software projects but frame them as "Software Development Rules" rather than universal rules
- Skill table: Reorder to lead with universal skills, then domain-specific

## Decision Log

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Keep Wise Eric advisor | User decision: authenticity is the brand |
| 2 | Ship generate-one-pager placeholder | User decision: signals work in progress |
| 3 | Don't move code-simplifier-full to plugin | Architect: hardcoded to specific project paths (src/app/api, ApiErrors, lib/chat) |
| 4 | Move doc-staleness-detector to plugin | Architect: general-purpose, no personal dependencies beyond analytics call |
| 5 | Ship ralph loop scripts (autopilot.sh, run-ralph.sh) | Architect: all paths relative via $SCRIPT_DIR, portable |
| 6 | Remove ewp-site-setup.md | User decision: personal website reference |
| 7 | Lead with universal value, not software | User decision: most users aren't building software |
| 8 | Add CONTRIBUTING.md + full templates | User decision: community building goal |
| 9 | Don't reset kanban .counter | Critique: avoids KB ID collisions with git history |
| 10 | Keep identity reframe bundled with release | User decision: README must make sense for target audience from day one |
| 11 | Preserve docs/plans/ directory | Critique: 13 skills write plan files here |

## Release Gate Checklist

All gates must pass before the repo is made public.

### Pre-cleanup snapshot
- [ ] Create a backup branch: `git branch pre-public-release`

### Reference integrity (run after all deletions)
- [ ] Grep all remaining `.md` files for references to deleted paths (`docs/mockups/`, `docs/investigations/`, `docs/prompts/`, `e2e/`, `scripts/`, `visual-documentation-plugin/`)
- [ ] Grep for any remaining `ewp-site` references
- [ ] Grep for any hardcoded `/Users/ericpage/` paths outside of completed plans (acceptable in Wise Eric and personal examples per business decisions)

### Plugin functionality
- [ ] `claude --plugin-dir /path/to/aligned_cc_skills` loads without errors
- [ ] All 31 skills appear in the skill list
- [ ] `/aligned:kickstart` scaffolds correctly in a temp directory
- [ ] `/aligned:brainstorming` starts correctly (project scan + first question)
- [ ] `/aligned:use-advisor` lists all advisors
- [ ] hooks.json is valid JSON (already verified)

### Counts and descriptions
- [ ] `ls advisors/prompts/*.md | wc -l` matches plugin.json description (62)
- [ ] `ls frameworks/ | wc -l` matches plugin.json description (135)
- [ ] `ls agents/*.md | wc -l` matches README agent table count
- [ ] `ls skills/*/SKILL.md | wc -l` matches README skill table count (31)
- [ ] plugin.json version matches marketplace.json version

### Community readiness
- [ ] CONTRIBUTING.md exists and references current skill anatomy
- [ ] .github/ISSUE_TEMPLATE/ contains bug_report.md and feature_request.md
- [ ] .github/pull_request_template.md exists
- [ ] LICENSE file present (MIT)
- [ ] No secrets, API keys, or tokens in any tracked file

### Final
- [ ] README "private repo" language removed
- [ ] All changes committed
- [ ] One clean `git diff main` review before pushing
