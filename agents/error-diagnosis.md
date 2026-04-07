---
name: error-diagnosis
description: |
  Use when Claude Code encounters repeated errors, when a session has been frustrating, or periodically to review accumulated error patterns as diagnostic signals for codebase and environment health. Examples: <example>Context: Multiple tool failures have occurred in the current session. user: "This session has been really frustrating with all these errors" assistant: "Let me analyze the accumulated error patterns to identify root causes." <commentary>Multiple errors suggest a systemic issue. Dispatch the error-diagnosis agent to classify patterns and identify root causes.</commentary></example>
model: sonnet
---

# Error Diagnosis

## Overview

Analyze errors captured by the PostToolUse/PostToolUseFailure hooks to identify patterns that signal codebase, environment, or configuration problems. Errors are symptoms — this skill maps them to root causes.

**Core principle:** Recurring errors are more diagnostic than individual errors. A single `command not found` is noise. The same error across 5 sessions points to a missing tool that should be installed or a skill that references the wrong command.

## When to Use

- After a frustrating session with many tool failures
- Periodically (weekly) to review accumulated error patterns
- When the same error keeps appearing across sessions
- When debugging feels harder than it should — errors may point to environment issues

## Error Log Location

`~/.claude/error-tracking/errors.jsonl`

Each line is a JSON entry:
```json
{
  "ts": "2026-02-11T...",
  "sid": "session-id",
  "type": "tool_failure|command_error",
  "tool": "Bash|Write|Edit|...",
  "input": "the command or file path",
  "error": "error description",
  "cwd": "/working/directory"
}
```

Read with the Read tool. Do NOT use jq or piped Bash commands.

## Process

### Step 1: Read and Group Errors

Read `~/.claude/error-tracking/errors.jsonl`. Group entries by:
1. **Error signature** — deduplicate by `tool + error pattern` (ignore timestamps and session IDs)
2. **Frequency** — count occurrences of each signature
3. **Recency** — note first and last occurrence

Sort by frequency descending. Focus on errors that appear 3+ times.

### Step 2: Classify Each Error Pattern

For each recurring error pattern, classify into one of these categories:

| Category | Signal | Examples |
|----------|--------|----------|
| **(E) Environment** | Missing tool or wrong version | `jq: command not found`, `python: not found`, wrong Node version |
| **(D) Dependency** | Missing or broken package | `Cannot find module`, `MODULE_NOT_FOUND`, version conflicts |
| **(C) Configuration** | Wrong paths, missing config | `ENOENT` on config files, env vars not set, wrong port |
| **(B) Build** | Compilation or transpilation failures | TypeScript errors, ESLint failures, build crashes |
| **(T) Test** | Failing tests | `npm test` exit code 1, assertion errors |
| **(P) Permission** | Access denied | `EACCES`, `Permission denied`, API auth failures |
| **(A) Architecture** | Codebase structural issues | Circular deps, import errors, file too large to edit |
| **(M) Misuse** | Claude using tools incorrectly | Wrong file paths, nonexistent commands, bad arguments |

### Step 3: Map to Root Causes

Each category maps to different root causes:

**Environment (E):** The development environment is missing tools that skills or workflows assume exist. **Fix:** Install missing tools or update skills to not assume them.

**Dependency (D):** Package.json or lock file is out of sync, or a dependency has a breaking change. **Fix:** Run dependency audit, update lock file, pin versions.

**Configuration (C):** Environment-specific config isn't documented or portable. **Fix:** Document required env vars, add config validation, update .env.example.

**Build (B):** Type errors or lint failures indicate code quality issues. If the same file keeps failing, it may have accumulated technical debt. **Fix:** Address type errors, consider refactoring complex files.

**Test (T):** Recurring test failures point to flaky tests or code that's being modified without test updates. **Fix:** Fix flaky tests, update tests alongside code changes.

**Permission (P):** File or API access issues suggest wrong permissions or expired credentials. **Fix:** Check file permissions, refresh API keys, verify RLS policies.

**Architecture (A):** Import failures, circular dependencies, or files too large to process suggest structural issues. **Fix:** Break up large files, resolve circular deps, simplify module graph.

**Misuse (M):** Claude repeatedly using wrong paths or commands suggests unclear project structure or misleading documentation. **Fix:** Update CLAUDE.md, add path conventions, improve error messages.

### Step 4: Generate Diagnosis Report

```
## Error Diagnosis Report — [date range]

**Errors analyzed:** N entries across M sessions

### Top Patterns (by frequency)

| # | Count | Category | Error Pattern | Root Cause | Suggested Fix |
|---|-------|----------|---------------|------------|---------------|
| 1 | 12    | (E)      | jq: not found | jq not installed | `brew install jq` or update skills to use Read tool |
| 2 | 8     | (T)      | npm test exit 1 | Tests failing after prompt changes | Run evals before committing |
| 3 | 5     | (M)      | ENOENT: /wrong/path | Claude using stale file paths | Update CLAUDE.md with current paths |

### Codebase Health Signals

**Environment health:** [good/needs attention/poor]
- Missing tools: [list]
- Version mismatches: [list]

**Code health:** [good/needs attention/poor]
- Build errors concentrated in: [files/modules]
- Test failures concentrated in: [areas]
- Architecture signals: [circular deps, large files]

**Documentation health:** [good/needs attention/poor]
- Misuse errors suggest: [what's unclear or misleading]
- Missing from CLAUDE.md: [conventions Claude keeps getting wrong]

### Action Plan (priority order)

**Quick wins (< 5 min):**
- [ ] Install missing tools: [list]
- [ ] Fix file permissions: [list]

**Short-term (< 1 hour):**
- [ ] Update CLAUDE.md with [conventions]
- [ ] Fix flaky tests: [list]

**Medium-term (plan needed):**
- [ ] Refactor [file] — build errors concentrated here
- [ ] Resolve [architectural issue]
```

### Step 5: Clean Up (Optional)

After diagnosing and addressing issues, optionally archive the error log:

```bash
mv ~/.claude/error-tracking/errors.jsonl ~/.claude/error-tracking/errors-$(date +%Y%m%d).jsonl
```

This starts fresh tracking so the next diagnosis only sees new errors.

## Integration

- **Capture layer:** `hooks/error-tracker.js` (PostToolUse + PostToolUseFailure hooks)
- **Deep debugging:** When diagnosis points to a specific bug, use `/aligned:root-cause-analysis` skill
- **Codebase audit:** For broader code health assessment, use **productivity-skills:code-auditor**
- **Environment fixes:** For project setup improvements, use **productivity-skills:project-bootstrapper**

## Known Limitations

- **PostToolUseFailure bug ([#6371](https://github.com/anthropics/claude-code/issues/6371)):** May not fire for failed Bash commands. The PostToolUse handler on Bash compensates by checking response text for error patterns.
- **Matcher bug ([#20334](https://github.com/anthropics/claude-code/issues/20334)):** PostToolUse matchers may run for all tools regardless of matcher. The hook handles this gracefully — non-Bash tools without error signals are ignored.
- **New session required:** Hooks load at session start. After installing the hook, restart Claude Code to begin capturing.
