# Autopilot Phase Prompts — `--bare` Audit

Audit performed before adopting `claude -p --bare`. `--bare` skips
MCP/hooks/CLAUDE.md auto-discovery. This document records whether each
phase prompt can run safely without that auto-loaded context.

## WRITE-PLAN.md
- Relative-path skill refs: none in the prompt itself. The writing-plans `SKILL.md`, plan-critique-checklist, and kanban-entry-format paths are all supplied as absolute-path parameters appended below the prompt.
- CLAUDE.md conventions relied on: none. The prompt does not assume the `skills/` path-prefix rule, brand-voice file location, or any registry path — every path it needs is in Parameters.
- Hook-injected context: none. Runs to completion without expecting hook output.
- Verdict: SAFE

## EXECUTE-PLAN.md
- Relative-path skill refs: none. The prompt instructs Claude to use Grep/Read on the plan file (path passed in) and mentions `/aligned:finishing-a-development-branch` only in a negative rule ("Do NOT run"); no file path is required to honor that rule.
- CLAUDE.md conventions relied on: none. The prompt is self-contained — task-heading regex, sentinel filenames, and BLOCKED protocol are all spelled out inline.
- Hook-injected context: none.
- Verdict: SAFE

## MOCKUP-FIDELITY.md
- Relative-path skill refs: none. Reads only mockup HTML files (path discovered from the plan header) and implementation source files referenced by the plan.
- CLAUDE.md conventions relied on: none. The annotation format `MOCKUP DEVIATION:` is defined inline.
- Hook-injected context: none.
- Verdict: SAFE

## VERIFY-BRANCH.md
- Relative-path skill refs: `skills/finishing-a-development-branch/SKILL.md` (literal relative path). The prompt explicitly states "Run from: The worktree directory (CWD should already be set)," and that path resolves from the worktree root without any CLAUDE.md guidance — the `skills/` prefix is a concrete directory in the repo, not a CLAUDE.md-only convention for path resolution.
- CLAUDE.md conventions relied on: none. The prompt does not consult the path rule, registries, brand voice, or any other CLAUDE.md section to resolve `skills/finishing-a-development-branch/SKILL.md`; the path is given literally.
- Hook-injected context: none. `.finish-status` is written by Claude, not by a hook.
- Verdict: SAFE

## Overall verdict

All four phase prompts pass their file paths as explicit parameters or use literal repo-relative paths that resolve from the worktree CWD. None depend on CLAUDE.md auto-discovery, MCP servers, or hook-injected context to execute. The `--bare` flag is safe to adopt for these phases.

verdict: PROCEED
