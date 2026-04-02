# Public Release Preparation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Prepare the aligned Claude Code plugin repo for public release by consolidating infrastructure, removing internal artifacts, reframing for a universal audience, and adding community infrastructure.

**Source Design Doc:** `docs/plans/2026-04-02-public-release-prep-design.md`

**Architecture:** Two workstreams executed sequentially: (1) port the doc-staleness-detector agent into the plugin, (2) remove internal development artifacts, reframe the README for community-building, and add contribution infrastructure. A release gate checklist verifies everything before the repo goes public.

**Tech Stack:** Markdown, JSON (plugin.json/marketplace.json), shell scripts, git

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] Ensure all in-progress work is committed or stashed — this plan makes destructive deletions on main

---

### ✅ Task 1: Create backup branch

**Files:**
- None modified

**Step 1: Create the pre-public-release backup branch**

Run:
```bash
git branch pre-public-release
```
Expected: Branch created successfully (no output)

**Step 2: Verify the branch exists**

Run:
```bash
git branch --list pre-public-release
```
Expected: `  pre-public-release` appears in output

**Step 3: Commit**

No commit needed — branch creation doesn't require a commit.

---

### ✅ Task 2: Port doc-staleness-detector agent into plugin

**Files:**
- Create: `agents/doc-staleness-detector.md`

**Step 1: Copy the agent from the author's global config**

Read `~/.claude/agents/doc-staleness-detector.md` in full. Copy its contents to `agents/doc-staleness-detector.md` with one modification:

Remove the analytics dashboard generation call. Find and delete these lines from Step 5:
```markdown
3. Regenerate the analytics dashboard:
   ```bash
   node ~/.claude/analytics/generate.js
   ```
```

This is a personal infrastructure dependency that won't exist on other users' machines.

**Step 2: Verify the patched agent**

Read `agents/doc-staleness-detector.md` and confirm:
- The frontmatter (name, description, model) is preserved
- All 6 steps are present (Step 0 through Step 5)
- The `node ~/.claude/analytics/generate.js` line is gone
- The timestamp update in Step 5 still works (items 1 and 2 remain)

> **Note:** The design doc requires a live dispatch test ("verify the agent can be dispatched from a project with `docs/` directory"). Static file verification here is insufficient for that. A live dispatch test is included in the Manual Steps (Post-Automation) section.

**Step 3: Commit**

```bash
git add agents/doc-staleness-detector.md
git commit -m "feat: port doc-staleness-detector agent into plugin

Remove personal analytics dependency (generate.js call).
Agent is general-purpose — works on any project with docs/ and kanban board."
```

---

### ✅ Task 3: Remove tracked internal artifacts — docs/ directories

**Files:**
- Delete: all files in `docs/plans/completed/`
- Delete: `docs/plans/2026-03-23-ewp-site-blog-integration.md`
- Delete: all files in `docs/kanban/todo/`, `docs/kanban/done/`, `docs/kanban/did_not_complete/` (but NOT `.counter` or `.gitkeep` files)
- Delete: `docs/investigations/` (entire directory)
- Delete: `docs/mockups/` (entire directory)
- Delete: `docs/prompts/` (entire directory)
- Delete: `docs/2026-03-13-autopilot-phase1-heartbeat-design.md`

**Important:** Do NOT delete `docs/plans/2026-04-02-public-release-prep-design.md` (the design doc) or `docs/plans/2026-04-02-public-release-prep.md` (this plan) yet — they are needed during execution and will be cleaned up in the post-automation manual steps.

**Step 1: Verify the files exist before deletion**

Use Glob to confirm:
- `docs/plans/completed/*.md` returns files
- `docs/kanban/todo/KB-*.md` returns files
- `docs/kanban/done/KB-*.md` returns files
- `docs/kanban/did_not_complete/KB-*.md` returns files
- `docs/investigations/` contains files
- `docs/mockups/` contains files
- `docs/prompts/` contains files
- `docs/2026-03-13-autopilot-phase1-heartbeat-design.md` exists

**Step 2: Remove all tracked files**

```bash
git rm -r docs/plans/completed/
git rm docs/plans/2026-03-23-ewp-site-blog-integration.md
git rm docs/kanban/todo/KB-*.md
git rm docs/kanban/done/KB-*.md
git rm docs/kanban/did_not_complete/KB-*.md
git rm -r docs/investigations/
git rm -r docs/mockups/
git rm -r docs/prompts/
git rm docs/2026-03-13-autopilot-phase1-heartbeat-design.md
```

Note: Some of these paths may be untracked (not in git). For untracked files/directories, use `rm -rf` instead of `git rm`. Check `git status` first to determine which are tracked vs untracked.

**Step 3: Verify deletions**

Use Glob to confirm:
- `docs/plans/completed/*.md` returns no results
- `docs/kanban/todo/KB-*.md` returns no results
- `docs/kanban/done/KB-*.md` returns no results
- `docs/investigations/` is gone
- `docs/mockups/` is gone
- `docs/prompts/` is gone

**Step 4: Commit**

```bash
git add -A docs/
git commit -m "chore: remove internal development artifacts from docs/

Remove completed plans, kanban items, investigations, mockups,
prompts, and stray design doc. Preparing for public release."
```

---

### ✅ Task 4: Remove tracked internal artifacts — top-level directories and files

**Files:**
- Delete: `e2e/` (entire directory)
- Delete: `scripts/` (entire directory)
- Delete: `visual-documentation-plugin/` (entire directory)
- Delete: `.skip-doc-staleness`
- Delete: `skills/generate-blog-post/references/ewp-site-setup.md`

**Step 1: Verify targets exist**

Use Glob to confirm each path exists:
- `e2e/**/*` returns files
- `scripts/*` returns files
- `visual-documentation-plugin/**/*` returns files
- `.skip-doc-staleness` exists
- `skills/generate-blog-post/references/ewp-site-setup.md` exists

**Step 2: Remove tracked files and directories**

```bash
git rm -r e2e/
git rm -r scripts/
git rm -r visual-documentation-plugin/
git rm .skip-doc-staleness
git rm skills/generate-blog-post/references/ewp-site-setup.md
```

As with Task 3, check `git status` first — some paths may be untracked and need `rm -rf` instead.

**Step 3: Update the ewp-site reference in generate-blog-post**

Modify: `skills/generate-blog-post/SKILL.md` (the fallback message referencing `ewp-site-setup.md`)

Find the line containing:
```
For richer rendering, see the setup guide at `skills/generate-blog-post/references/ewp-site-setup.md`.
```

Replace the reference with a generic message:
```
For richer rendering, add Callout and CTA components to your mdx-components.tsx.
```

**Step 4: Verify deletions and reference update**

- Glob: `e2e/**/*` returns no results
- Glob: `scripts/*` returns no results
- Glob: `visual-documentation-plugin/**/*` returns no results
- Glob: `.skip-doc-staleness` returns no results
- Read `skills/generate-blog-post/SKILL.md` and confirm the ewp-site reference is gone

**Step 5: Commit**

```bash
git add -A e2e/ scripts/ visual-documentation-plugin/ .skip-doc-staleness skills/generate-blog-post/
git commit -m "chore: remove e2e/, scripts/, visual-documentation-plugin/, and personal references

Remove eval infrastructure placeholder, dev scripts, separate plugin,
doc-staleness flag, and ewp-site setup guide."
```

---

### ✅ Task 5: Delete untracked files

**Files:**
- Delete: `erics-advisory-skills.plugin`
- Delete: `zid1vQxP`
- Delete: `docs/diagrams/` (untracked directory)

**Step 1: Verify these files are untracked**

Run:
```bash
git status --short
```

Confirm these appear with `??` prefix (untracked).

**Step 2: Delete untracked files**

```bash
rm -f erics-advisory-skills.plugin
rm -f zid1vQxP
rm -rf docs/diagrams/
```

**Step 3: Verify deletion**

Run:
```bash
git status --short
```

Confirm the deleted files no longer appear.

**Step 4: Commit**

No commit needed — these were untracked files, so git has nothing to record.

---

### ✅ Task 6: Preserve directory structure with .gitkeep files

**Files:**
- Create: `docs/plans/.gitkeep` (if not already present)
- Create: `docs/plans/completed/.gitkeep`
- Verify: `docs/kanban/todo/.gitkeep`, `docs/kanban/in-progress/.gitkeep`, `docs/kanban/done/.gitkeep`, `docs/kanban/did_not_complete/.gitkeep` exist
- Verify: `docs/kanban/.counter` exists and is NOT reset

**Step 1: Check current state of .gitkeep files**

Use Glob to find existing `.gitkeep` files:
- `docs/kanban/**/.gitkeep`
- `docs/plans/**/.gitkeep`

**Step 2: Create missing .gitkeep files**

For each directory that needs preserving, create a `.gitkeep` if one doesn't exist:
- `docs/plans/.gitkeep`
- `docs/plans/completed/.gitkeep`
- `docs/kanban/did_not_complete/.gitkeep` (this directory had only `KB-008...md` — no `.gitkeep` existed)

The `docs/plans/completed/` directory was deleted in Task 3 along with its contents. Recreate it:
```bash
mkdir -p docs/plans/completed
```

Then create all missing `.gitkeep` files (empty files).

**Step 3: Verify .counter is preserved**

Read `docs/kanban/.counter`. It should contain `26` (the current value). Do NOT reset it — the design doc explicitly says to preserve the counter to avoid KB ID collisions with git history.

**Step 4: Verify all .gitkeep files exist**

Use Glob: `docs/**/.gitkeep` — should return entries for:
- `docs/plans/.gitkeep`
- `docs/plans/completed/.gitkeep`
- `docs/kanban/todo/.gitkeep` (or verify this dir exists)
- `docs/kanban/in-progress/.gitkeep`
- `docs/kanban/done/.gitkeep`
- `docs/kanban/did_not_complete/.gitkeep`

**Step 5: Commit**

```bash
git add docs/plans/.gitkeep docs/plans/completed/.gitkeep docs/kanban/
git commit -m "chore: preserve directory structure with .gitkeep files

Keep docs/plans/, docs/plans/completed/, and all docs/kanban/
subdirectories. Kanban .counter preserved at 26."
```

---

### ✅ Task 7: Fix cross-references to deleted paths

> **Ordering dependency:** Must run after Tasks 3 and 4 (file deletions). Running earlier would produce false positives from files about to be deleted.

**Files:**
- Modify: any remaining `.md` files that reference deleted paths (specific files identified below)

**Step 1: Search for references to deleted paths**

Use Grep across all `.md` files for each deleted path pattern:
- `docs/investigations/`
- `docs/prompts/`
- `e2e/` (but NOT references to consumer project `e2e/` directories in skill templates — those are about consumer projects, not this repo)
- `scripts/`
- `visual-documentation-plugin/`
- `ewp-site` (excluding the design doc which will be deleted later)

**Important:** References to `docs/mockups/` in skills like `writing-plans/SKILL.md`, `brainstorming/modes/software.md`, and `brainstorming/modes/business.md` should be LEFT ALONE. These tell skills where to write mockups in consumer projects — they are NOT references to this repo's deleted mockups directory.

Similarly, references to `docs/plans/` in skills are about consumer projects' plan directories and should be left alone.

**Step 2: Fix any remaining references**

Based on the codebase exploration, the references to deleted paths in remaining files are primarily in:
- The design doc itself (being deleted post-automation, skip)
- `skills/generate-blog-post/SKILL.md` — already fixed in Task 4

If Grep finds additional references in non-deleted files, update them:
- Remove the reference if it's no longer relevant
- Replace with a generic equivalent if the reference was instructional

**Step 3: Search for hardcoded personal paths**

Use Grep for `/Users/ericpage/` across all `.md` files. References in the Wise Eric advisor prompt and personal examples are acceptable per the design doc's business decisions. Flag any other occurrences.

**Step 4: Verify no stale references remain**

Re-run all Grep searches from Step 1. Confirm zero matches in non-deleted files (excluding the design doc and this plan file).

**Step 5: Commit (if changes were made)**

```bash
git add -A
git commit -m "chore: fix cross-references to deleted paths"
```

If no changes were needed, skip the commit.

---

### ✅ Task 8: Update plugin.json and marketplace.json

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Verify current counts**

Run these verification commands:
- Glob `skills/*/SKILL.md` and count results (expected: 30 — v0.13.0 merged business-brainstorming into brainstorming)
- Glob `agents/*.md` and count results (expected: 13, including the newly ported doc-staleness-detector)
- Glob `advisors/prompts/*.md` and count results (expected: 62)
- Glob `frameworks/*/` and count directories (expected: 135)

**Step 2: Update plugin.json**

Read `.claude-plugin/plugin.json`. Update:

```json
{
  "name": "aligned",
  "version": "0.13.0",
  "description": "Skill stack for Claude Code: brainstorming, structured thinking, 62 advisor personas, 135 frameworks, content generation, TDD pipeline, automated quality gates",
  "author": {
    "name": "Eric Page"
  },
  "repository": "https://github.com/bigchewy/aligned_cc_skills",
  "license": "MIT",
  "keywords": ["brainstorming", "advisors", "frameworks", "tdd", "pipeline", "design-system"]
}
```

Key changes:
- Description: reframed to lead with universal value (brainstorming, thinking, advisors) not TDD
- Description: updated counts (62 advisors, 135 frameworks)
- Keywords: added brainstorming, advisors, frameworks

**Step 3: Update marketplace.json**

Read `.claude-plugin/marketplace.json`. Update the description and version to match plugin.json exactly.

**Step 4: Verify both files are valid JSON and match**

Read both files. Confirm:
- Versions match (0.13.0)
- Descriptions match exactly
- Both are valid JSON (no trailing commas, proper quoting)

**Step 5: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: update plugin metadata for public release

Reframe description to lead with universal value. Fix advisor
count (61→62) and framework count (134→135)."
```

---

### ✅ Task 9: README overhaul

**Files:**
- Modify: `README.md`

This is the largest task. Make all changes in a single pass to avoid merge conflicts.

**Step 1: Read current README.md in full**

Read `README.md`. Identify all sections that need changes per the design doc.

**Step 2: Apply all changes**

Make the following edits to `README.md`:

**A. Headline (line 1):**
```markdown
# Aligned

Opinionated skill stack for Claude Code. 30 skills, 13 agents, 62 advisor personas, 135 frameworks, and automated quality gates — from brainstorm to working code.
```

Changes: "development stack" → "skill stack", count fixes (31→30 skills, 11→13 agents), added framework count, "connected into a pipeline from idea to working code" → "from brainstorm to working code".

**B. Installation section — remove private repo language:**

Replace:
```markdown
Run these inside Claude Code (the repo is private — you'll need collaborator access):
```

With:
```markdown
Run these inside Claude Code:
```

**C. Quick Start — lead with universal value:**

Replace the current Quick Start with:
```markdown
## Quick Start

1. `/aligned:kickstart` — scaffold a new project with standard conventions
2. `/aligned:brainstorming` — explore ideas and strategies (auto-detects software vs business mode)
3. `/aligned:use-advisor` — adopt an expert persona (62 advisors across business, technology, and creative domains)
4. `/aligned:use-framework` — guided walkthroughs of 135 structured decision frameworks

For software projects, the full pipeline: `/aligned:brainstorming` → `/aligned:writing-plans` → auto-launch execution pipeline
```

**D. Agent table — add project-scanner and doc-staleness-detector:**

Add these two rows to the agents table:
```markdown
| doc-staleness-detector | Detect stale docs by comparing git history — logs to Kanban, never edits directly |
| project-scanner | Fast codebase scan for brainstorming context (languages, structure, dependencies) |
```

**E. Skill table — reorder to lead with universal skills:**

Reorder the table rows so universal skills come first:
1. Brainstorming and advisor skills (brainstorming, use-advisor, use-framework, add-advisor, add-framework, find-potential-advisors, persona-panel)
2. Content skills (generate-deck, generate-blog-post, generate-one-pager, create-svg-diagram)
3. Foundation skills (kickstart, design-principles, create-design-principles)
4. Business skills (business-diagnosis, business-executing, business-write-plan)
5. Pipeline skills (writing-plans, executing-plans, finishing-a-development-branch)
6. Methodology skills (test-driven-development, verification-before-completion)
7. Problem-solving skills (systematic-debugging, eval-failure-triage, eval-audit)
8. Infrastructure skills (using-git-worktrees, claude-profile)
9. Maintenance skills (codebase-audit, kanban-resolve)
10. Meta skills (create-new-skill)

**F. Iron Rules — reframe as software-specific:**

Replace the heading:
```markdown
## Iron Rules
```

With:
```markdown
## Iron Rules (Software Development)
```

Add a note after the heading:
```markdown
These rules are enforced by pipeline skills during software development:
```

**G. Changelog — trim to recent versions:**

The changelog currently covers v0.1.0 through v0.13.0. For a public release, trim to the last 3 major versions (v0.5.0+) and add a note that earlier history is available in git. This keeps the README focused while preserving discoverability.

**H. Project Conventions — remove references to non-scaffolded directories:**

The Project Conventions section describes what `/aligned:kickstart` scaffolds in consumer projects. Remove entries for directories that kickstart does NOT scaffold:
```markdown
- `docs/ralph_loops/` — Ralph loop prompts for autonomous execution
- `e2e/` — Eval infrastructure (scenarios, config, runner)
```

`docs/ralph_loops/` is a plugin-internal directory (lives in the aligned plugin repo, not scaffolded per-project). `e2e/` was removed from the plugin repo entirely. Both are incorrect entries in a "what kickstart creates" list.

**Step 3: Verify the changes**

Read the updated `README.md`. Verify:
- Headline counts match actual counts (30 skills, 13 agents, 62 advisors, 135 frameworks)
- No "private" or "collaborator access" language remains
- Quick Start leads with universal value
- Agent table has 13 rows (11 original + project-scanner + doc-staleness-detector)
- Skill table has 30 rows
- Iron Rules section is clearly scoped to software development
- Changelog section begins at v0.5.0 or later (earlier history trimmed with a git note)

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: overhaul README for public release

Reframe from TDD-centric to universal skill stack. Lead Quick Start
with brainstorming and advisors. Fix counts (30 skills, 13 agents,
135 frameworks). Remove private repo language. Reorder skill table
to lead with universal skills. Scope Iron Rules to software dev."
```

---

### ✅ Task 10: Create CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

**Step 1: Verify CONTRIBUTING.md does not already exist**

Use Glob: `CONTRIBUTING.md` — should return no results.

**Step 2: Write CONTRIBUTING.md**

Create `CONTRIBUTING.md` with the following content:

```markdown
# Contributing to Aligned

Thanks for your interest in contributing! This document covers the basics.

## Skill Anatomy

Skills live in `skills/<name>/` directories:

```
skills/<name>/
  SKILL.md              — Entry point (frontmatter required)
  *.md                  — Supporting docs (checklists, catalogs)
  references/*.md       — Deeper reference material
```

The `SKILL.md` frontmatter must include `name` (matching the directory) and `description`:

```yaml
---
name: my-skill
description: "One-line description of when to use this skill"
---
```

## Adding a New Skill

1. Create `skills/<name>/SKILL.md` with frontmatter
2. Test locally: `claude --plugin-dir /path/to/aligned_cc_skills`
3. Add an entry to the skill reference table in `README.md`
4. Add `Skill(aligned:<name>)` to the permissions list in `README.md`
5. Bump the version in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`

## Adding an Advisor

Use `/aligned:add-advisor` within Claude Code — it guides you through creation, calibration, and registration.

## Adding a Framework

Use `/aligned:add-framework` within Claude Code — it guides you through adding a framework to an advisor's domain.

## Testing

- Test your changes locally with `claude --plugin-dir /path/to/aligned_cc_skills`
- For software-related skills: TDD is enforced. Write failing tests first, then implement.
- Verify your skill loads and executes correctly before submitting a PR.

## Pull Request Guidelines

- One skill or feature per PR
- Include a clear description of what the skill does and when it should be used
- Update `README.md` counts and tables if adding skills, agents, or advisors
- Bump the version in both `plugin.json` and `marketplace.json`

## Code of Conduct

Be respectful. We're building tools to help people think better — bring that spirit to collaboration.

## Questions?

Open an issue or start a discussion. We're happy to help you get oriented.
```

**Step 3: Verify the file was written correctly**

Read `CONTRIBUTING.md` and confirm it contains all sections.

**Step 4: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING.md for community contributors

Covers skill anatomy, adding skills/advisors/frameworks, testing
approach, and PR guidelines."
```

---

### Task 11: Create GitHub issue and PR templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/pull_request_template.md`

**Step 1: Verify .github/ does not exist**

Use Glob: `.github/**/*` — should return no results.

**Step 2: Create directory structure**

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

**Step 3: Create bug report template**

Write `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: Report a skill, agent, or hook that isn't working correctly
labels: bug
---

## Describe the bug

A clear description of what went wrong.

## Skill / Agent / Hook

Which skill, agent, or hook is affected? (e.g., `/aligned:brainstorming`, `code-reviewer` agent)

## Steps to reproduce

1. Run `...`
2. Provide input `...`
3. Observe `...`

## Expected behavior

What should have happened instead.

## Environment

- Claude Code version: [e.g., 1.2.3]
- Plugin version: [e.g., 0.13.0]
- OS: [e.g., macOS 14.5, Ubuntu 24.04]

## Additional context

Paste any relevant error messages or screenshots.
```

**Step 4: Create feature request template**

Write `.github/ISSUE_TEMPLATE/feature_request.md`:

```markdown
---
name: Feature Request
about: Suggest a new skill, advisor, framework, or improvement
labels: enhancement
---

## What problem does this solve?

Describe the problem or workflow gap.

## Proposed solution

Describe what you'd like to see — a new skill, a new advisor, a framework, or an improvement to an existing one.

## Alternatives considered

What other approaches have you thought about?

## Additional context

Any examples, references, or mockups that help illustrate the idea.
```

**Step 5: Create PR template**

Write `.github/pull_request_template.md`:

```markdown
## Summary

Brief description of what this PR does.

## Changes

- [ ] New skill / Updated skill
- [ ] New advisor / Updated advisor
- [ ] New framework
- [ ] New agent / Updated agent
- [ ] Bug fix
- [ ] Documentation update

## Testing

How did you verify this works?

- [ ] Tested locally with `claude --plugin-dir`
- [ ] Skill loads and executes correctly
- [ ] README updated (if adding skills/agents/advisors)
- [ ] Version bumped in plugin.json and marketplace.json (if applicable)
```

**Step 6: Verify all templates exist**

Use Glob: `.github/**/*.md` — should return 3 files.

**Step 7: Commit**

```bash
git add .github/
git commit -m "chore: add GitHub issue and PR templates

Bug report, feature request, and pull request templates for
community contributions."
```

---

### Task 12: Release gate verification

**Files:**
- Modify: any files where verification reveals issues

This task runs every check from the design doc's Release Gate Checklist. Fix any issues found inline.

**Step 1: Reference integrity — grep for deleted paths**

Use Grep across all remaining `.md` files (excluding this plan and the design doc) for:
- `docs/mockups/` — OK in skills (consumer project references), flag if referencing THIS repo's mockups
- `docs/investigations/`
- `docs/prompts/`
- `visual-documentation-plugin/`
- `ewp-site` (outside of generate-blog-post skill's generic reference)
- `/Users/ericpage/` (acceptable in Wise Eric advisor and personal examples only)

Fix any stale references found.

**Step 2: Count verification**

Run these counts and compare to README and plugin.json:

| Check | Command | Expected |
|-------|---------|----------|
| Skills | Glob `skills/*/SKILL.md`, count results | 30 |
| Agents | Glob `agents/*.md`, count results | 13 (12 existing + doc-staleness-detector) |
| Advisors | Glob `advisors/prompts/*.md`, count results | 62 |
| Frameworks | Count directories in `frameworks/` | 135 |

Wait — the README agent table should have 13 entries now (11 original + project-scanner + doc-staleness-detector). Verify the README agent table row count matches the actual agent count.

Also verify:
- `plugin.json` version matches `marketplace.json` version
- `plugin.json` description matches `marketplace.json` description

**Step 3: Verify community files exist**

Use Glob to confirm:
- `CONTRIBUTING.md` exists
- `.github/ISSUE_TEMPLATE/bug_report.md` exists
- `.github/ISSUE_TEMPLATE/feature_request.md` exists
- `.github/pull_request_template.md` exists
- `LICENSE` exists

**Step 4: Verify no secrets or API keys**

Use Grep for common secret patterns across all tracked files:
- `sk-` (API keys)
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `password.*=`
- `token.*=` (but filter out template references)

**Step 5: Verify .gitignore covers sensitive files and add missing patterns**

Read `.gitignore`. Confirm it includes `.autopilot-log` and `aligned-cowork.zip`. If the following patterns are missing, add them:
- `.env*` (environment variable files)
- `*.plugin` (plugin binary files — prevents accidental commits like `erics-advisory-skills.plugin`)

**Step 5a: Verify critical runtime files survived deletions**

The Ralph loop scripts are hard runtime dependencies — `skills/writing-plans/SKILL.md` treats a missing `run-ralph.sh` as a hard stop. Verify both exist:
- Read `docs/ralph_loops/run-ralph.sh` — must exist and be non-empty
- Read `docs/ralph_loops/autopilot.sh` — must exist and be non-empty

If either is missing, something in Tasks 3-5 accidentally deleted it — this is a **blocking** issue that must be investigated before proceeding.

**Step 6: Verify README has no private repo language**

Use Grep for "private" and "collaborator" in `README.md`. Should return zero matches.

**Step 7: Fix any issues found and commit**

If any issues were found in steps 1-6, fix them and commit:

```bash
git add -A
git commit -m "chore: release gate fixes

Fix issues found during release gate verification."
```

If no issues were found, skip the commit.

---

## Manual Steps (Post-Automation)

> Complete these steps after all automated tasks finish.

- [ ] Delete the design doc: `rm docs/plans/2026-04-02-public-release-prep-design.md`
- [ ] Delete this plan file: `rm docs/plans/2026-04-02-public-release-prep.md`
- [ ] Commit: `git add -A docs/plans/ && git commit -m "chore: remove release prep plan and design doc"`
- [ ] Run `claude --plugin-dir /path/to/aligned_cc_skills` and verify all skills load
- [ ] Test `/aligned:kickstart` in a temp directory
- [ ] Test `/aligned:brainstorming` starts correctly
- [ ] Test `/aligned:use-advisor` lists all advisors
- [ ] Review the full diff: `git diff pre-public-release..HEAD`
- [ ] Author's machine cleanup (workstream 1b from design doc): Remove duplicated hook entries from `~/.claude/settings.json`:
  - PreToolUse: `auto-approve-worktrees.js`, `auto-approve-safe-bash-paths.js`
  - PostToolUseFailure: `error-tracker.js`
  - PostToolUse: `error-tracker.js`, `usage-tracker.js`
  - Keep: SessionStart → `check-cron-results.sh`, UserPromptSubmit → `check-test-audit.sh`

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Plan file self-deletion | Post-automation manual step | Auto-delete in last task |
| 2 | Batch all docs/ deletions in one task | Single commit for all docs/ removals | Separate commits per directory |
| 3 | Keep mockup references in skills | Leave references to `docs/mockups/` in skills unchanged | Remove all mockup references |
| 4 | README edit as single task | One task for all README changes | Split into 3 separate tasks |
| 5 | Skill count: 30 (not 31) | README headline updated to 30 | Keep 31 and investigate |
| 6 | Delete all kanban done/ items | Remove closed KB items for clean public slate | Keep done/ items as history |

### Appendix: Decision Details

#### Decision 1: Plan file self-deletion
**Chose:** Post-automation manual step
**Why:** The Ralph loop re-reads the plan file for each task to find the next incomplete task. Deleting the plan during execution would break subsequent task discovery. The design doc itself is also untracked and can be cleaned up after execution.
**Alternatives rejected:**
- Auto-delete in last task: Would work only in interactive mode, not Ralph loops

#### Decision 2: Batch all docs/ deletions in one task
**Chose:** Single commit grouping all `docs/` directory removals
**Why:** These are all internal development artifacts being removed for the same reason (public release prep). Separate commits add git noise without meaningful semantic separation. Each deletion is a simple `git rm` — the risk of any individual failure is low.
**Alternatives rejected:**
- One commit per directory: 7+ tiny commits with no independent value

#### Decision 3: Keep mockup references in skills
**Chose:** Leave `docs/mockups/` references in writing-plans, brainstorming/modes/software.md, and brainstorming/modes/business.md unchanged
**Why:** These references describe where skills should write mockups in CONSUMER projects. They are templates/instructions, not references to this repo's own mockups directory. Removing them would break the mockup workflow for users of the plugin.
**Alternatives rejected:**
- Remove all mockup references: Would break the brainstorming → mockup generation pipeline

#### Decision 4: README edit as single task
**Chose:** One task with multiple edit steps
**Why:** All README changes are interdependent — count fixes affect the headline, identity reframe affects Quick Start and skill ordering, and table updates depend on knowing which rows exist. Splitting into multiple commits risks intermediate inconsistent states and merge conflicts between steps.
**Alternatives rejected:**
- 3 separate tasks (headline+install, tables, changelog): Higher risk of inconsistency between commits

#### Decision 5: Skill count: 30 (not 31)
**Chose:** Update README headline from 31 to 30
**Why:** Globbing `skills/*/SKILL.md` returns exactly 30 files. The v0.13.0 changelog confirms `business-brainstorming` was merged into `brainstorming`, reducing the count by 1. The README headline was not updated during that change. The `_shared` directory is a utility directory, not a skill.
**Alternatives rejected:**
- Keep 31 and investigate: Already investigated — the count is definitively 30

#### Decision 6: Delete all kanban done/ items
**Chose:** Remove all closed KB items (KB-004 through KB-025) for a clean public slate
**Why:** These items reference internal development decisions, personal file paths, and plugin-specific bugs that have no value to community users. The `.counter` is preserved at 26 to avoid ID collisions with git history — new contributors will see KB-027+ without confusion about the gap, since the counter file documents the state. The full history remains accessible via `git log` on the `pre-public-release` backup branch.
**Alternatives rejected:**
- Keep done/ items as history: Exposes internal development artifacts to community users with no benefit
