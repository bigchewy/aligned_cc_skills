# Aligned — Claude Code Skills Plugin

Canonical source for the `aligned` plugin. Edit skills here, not in `~/.claude/skills/`.

## Path Rule

All internal references use `skills/` prefix (e.g., `skills/brainstorming/design-critique-checklist.md`). Never `~/.claude/skills/`. When editing cross-references, verify paths are relative to this repo root.

## Skill Anatomy

```
skills/<name>/
  SKILL.md              — Entry point (frontmatter required)
  *.md                  — Supporting docs (checklists, catalogs)
  references/*.md       — Deeper reference material
```

Frontmatter `name` must match the directory name:

```yaml
---
name: writing-plans
description: "Use when you have a spec or requirements for a multi-step task"
---
```

## Cross-References

Skills reference each other by path and by `/aligned:<name>` invocation. Before renaming or moving any `.md` file, grep all `skills/**/*.md` for the old path — breakage is silent.

## Adding a Skill

1. Create `skills/<name>/SKILL.md` with frontmatter (`name` must match directory)
2. Test: `claude --plugin-dir /path/to/aligned_cc_skills`
3. Add entry to the skill reference table in `README.md`
4. Add `Skill(aligned:<name>)` to the permissions list in both `README.md` and `skills/kickstart/SKILL.md` Phase 5
5. Bump version in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`

## Version

`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — both must match. Semver, pre-1.0.

## What NOT to Duplicate

The `README.md` already contains the skill reference table, iron rules, installation instructions, team setup, and changelog. Do not duplicate that content here.

## Hook-Triggered Audits

Hooks inject `[TAG]` messages when audits find issues. Handle them before the user's request.

**Error diagnosis:** When a session has accumulated repeated tool failures, or the user reports frustration with errors, dispatch the `error-diagnosis` agent to classify patterns and identify root causes. The agent reads `~/.claude/error-tracking/errors.jsonl` (populated by the `error-tracker.js` PostToolUse hook).

**UserPromptSubmit hooks** (fire on every message, BLOCKING):
- `[EVAL AUDIT]` → suggest running `/aligned:eval-audit` to the user
