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
