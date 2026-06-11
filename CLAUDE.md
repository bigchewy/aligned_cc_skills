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

## Registries — Sources of Truth

Two YAML registries track all advisors and frameworks. Skills use these for discovery, routing, and selection. Any skill that creates or removes an advisor or framework MUST update the corresponding registry.

- **`advisors/registry.yaml`** — All advisor personas. Used by use-advisor, code-reviewer, persona-panel, and contextual recommendation.
- **`frameworks/registry.yaml`** — All decision frameworks. Used by use-framework and contextual recommendation.

## Framework Prompts Are Interactive Scripts

Framework files (`frameworks/*/prompt.md`) contain explicit WAIT points where the user must respond before continuing. The framework IS the process; skipping WAIT points defeats the purpose.

Anti-patterns to refuse:
- Reading a `prompt.md` file and answering all its questions in one shot
- Using existing positioning docs to fill in framework elements without user input
- Treating WAIT points as optional pauses rather than hard stops
- Skipping `/aligned:use-framework` because "I already know what the framework says"

## Testing

**Always use TDD.** When planning or implementing features, always include test updates. Every design document and implementation plan must specify which test files need to be created, renamed, or updated. Do not ask whether tests should be included - they always should be.

**CRITICAL: Error Path Tests for Mocks.** When tests use mocks (mockResolvedValue, mockReturnValue), you MUST also write tests for error paths (mockRejectedValue). Every async operation that can fail in production must have both success AND error tests.

## Cross-References

Skills reference each other by path and by `/aligned:<name>` invocation. Before renaming or moving any `.md` file, grep all `skills/**/*.md` for the old path — breakage is silent.

## Adding a Skill

1. Create `skills/<name>/SKILL.md` with frontmatter (`name` must match directory)
2. Test: `claude --plugin-dir /path/to/aligned_cc_skills`
3. Add entry to the skill reference table in `README.md`
4. Bump version in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`

The kickstart skill enumerates `Skill(aligned:<name>)` permissions from the filesystem at runtime, so no manual allow-list updates are needed when adding a skill.

## Version

`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — both must match. Semver, pre-1.0.

## Portability Rule

This is a distributed plugin — never hard-code to the author's personal environment. Every feature, skill, config reference, and workflow must work for any user who installs the plugin. When building or modifying anything:

- **Guard on file existence**, not assumed paths. If a feature depends on `e2e/trigger-map.yaml`, check that it exists before referencing it.
- **User-facing skills must not assume internal infrastructure.** Skills like `add-advisor` and `add-framework` are invoked by all users. Don't embed instructions that only make sense for the plugin author (eval configs, Kanban boards, internal QA workflows).
- **Conditional blocks for author-only features.** If a skill step only applies when author-specific infrastructure exists (e.g., `e2e/` eval directory), gate it behind an existence check and skip silently for other users.
- **Test the mental model:** "If someone installs this plugin fresh and runs this skill, does every step make sense to them?" If not, the step needs a guard or shouldn't be there.

## What NOT to Duplicate

The `README.md` already contains the skill reference table, iron rules, installation instructions, team setup, and changelog. Do not duplicate that content here.

