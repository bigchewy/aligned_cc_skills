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

## Version

`.claude-plugin/plugin.json` — semver, pre-1.0.

## What NOT to Duplicate

The `README.md` already contains the skill reference table, iron rules, installation instructions, team setup, and changelog. Do not duplicate that content here.

## Bash Tool Restrictions

**Never use Bash for file search or content search.** Permission rules like `Bash(find *)` and `Bash(grep *)` use `*` which does NOT match across shell operators (`|`, `&&`, `;`). Any Bash command with pipes or chaining triggers interactive approval prompts. Instead:
- Use **Glob** instead of `find`
- Use **Grep** instead of `grep`/`rg`
- Use **Read** instead of `cat`/`head`/`sed`/`awk`

If you need to process multiple files, use Glob to find them, Read to inspect them, and analyze the results in context.

## Communication Style

**No sycophancy.** Never open with "Great question!", "This is fascinating", "Excellent point", or similar filler. Skip preamble and get to substance. Just answer.

## Testing

**Always use TDD.** When planning or implementing features, always include test updates. Every design document and implementation plan must specify which test files need to be created, renamed, or updated. Do not ask whether tests should be included - they always should be.

**CRITICAL: Error Path Tests for Mocks.** When tests use mocks (mockResolvedValue, mockReturnValue), you MUST also write tests for error paths (mockRejectedValue). Every async operation that can fail in production must have both success AND error tests. See `skills/test-driven-development/testing-anti-patterns.md` for details.

## Auto-Critique for Design Documents

**After completing brainstorming or writing-plans, automatically critique the document you just created.** Present specific weaknesses, gaps, or concerns. After the first critique, address any concerns the user wants fixed. Run a second critique round only if the first found medium or high severity issues.

## Git Commits

**Never use heredoc syntax for commit messages.** Use plain `-m "message"` format. Heredoc (`$(cat <<'EOF'...EOF)`) contains shell operators that bypass the `Bash(git *)` permission rule and trigger interactive approval prompts. Multi-line messages work fine with a regular quoted string.

## Hook-Triggered Audits

Hooks inject `[TAG]` messages when audits find issues. Handle them before the user's request.

**Error diagnosis:** When a session has accumulated repeated tool failures, or the user reports frustration with errors, dispatch the `error-diagnosis` agent to classify patterns and identify root causes. The agent reads `~/.claude/error-tracking/errors.jsonl` (populated by the `error-tracker.js` PostToolUse hook).

**UserPromptSubmit hooks** (fire on every message, BLOCKING):
- `[EVAL AUDIT]` → suggest running `/aligned:eval-audit` to the user

## Verification Discipline

**Every success claim requires fresh evidence in the current message.** This is non-negotiable and applies everywhere: mid-task, between tasks, before commits.

- Never use "should," "probably," "seems to," or "looks correct" — RUN THE COMMAND
- Never express satisfaction ("Done!", "Perfect!") before running verification
- Never trust agent success reports without checking VCS diff independently
- Never claim "tests pass" without test command output showing 0 failures in this message
- Never claim "build succeeds" without build command output showing exit 0 in this message
- Linter passing does NOT mean build passes — verify each independently

| Excuse | Reality |
|--------|---------|
| "Should work now" | Run the verification |
| "I'm confident" | Confidence is not evidence |
| "Partial check is enough" | Partial proves nothing |
| "Agent said success" | Verify independently |

Run the command. Read the output. THEN claim the result.
