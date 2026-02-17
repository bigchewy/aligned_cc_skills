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
4. Bump version in `.claude-plugin/plugin.json`

## Editing Existing Skills

Three skills were authored directly in this repo: `kickstart`, `eval-audit`, `design-principles`. The rest were originally synced from `~/.claude/skills/` but this repo is now canonical — edit everything here.

The legacy sync script (`scripts/sync-from-local.sh`) still exists. If run, it overwrites skills listed in its `SYNC_SKILLS` array. Do not run it without checking which skills it touches.

## Version

`.claude-plugin/plugin.json` — semver, pre-1.0.

## What NOT to Duplicate

The `README.md` already contains the skill reference table, iron rules, installation instructions, team setup, and changelog. Do not duplicate that content here.
