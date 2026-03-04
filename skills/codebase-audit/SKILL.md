---
name: codebase-audit
description: "Comprehensive multi-dimensional codebase audit covering code quality, test quality, security, dead code, and architecture. Report-only — never edits source code."
---

# Codebase Audit

Orchestrates 5 parallel dimension-specific workers, aggregates their findings with confidence scoring, deduplicates, and presents a unified report. Read-only — diagnosis only, never edits source code.

## Phase 0: Discovery

1. Read `CLAUDE.md` (if it exists) for project conventions, iron rules, and intentional patterns. Save the content — workers need it to avoid false positives on intentional decisions.

2. Auto-detect source roots. Check in order and use ALL that exist:
   - `src/`
   - `app/`
   - `lib/`
   - `pages/`
   - If none exist, use root-level source files (exclude `node_modules`, `.git`, `dist`, `build`, `coverage`, `docs`, `.claude`, `.next`, `__pycache__`, `vendor`, `target`)

3. Auto-detect language/framework from config files:
   - `package.json` → Node/JS/TS (check for React, Next.js, Vue, etc.)
   - `requirements.txt` / `pyproject.toml` / `setup.py` → Python
   - `go.mod` → Go
   - `Cargo.toml` → Rust
   - `Gemfile` → Ruby
   - If multiple exist, note all

4. Glob all source files under detected roots. Common patterns by language:
   - JS/TS: `**/*.{ts,tsx,js,jsx,mjs,cjs}`
   - Python: `**/*.py`
   - Go: `**/*.go`
   - Rust: `**/*.rs`
   - Ruby: `**/*.rb`
   - If unknown, use `**/*.{ts,tsx,js,jsx,py,go,rs,rb,java,kt,swift,cs}`

5. Glob test files separately:
   - `**/*.test.*`, `**/*.spec.*`, `**/__tests__/**`, `**/test_*.py`, `**/*_test.go`, `**/tests/**`

6. Report to the user before proceeding:
   - Source roots detected
   - Language/framework detected
   - Number of source files
   - Number of test files
   - Which workers will run (skip test-quality if 0 test files)

**User override:** If the user provides source roots as arguments (e.g., `/aligned:codebase-audit src/ lib/`), use those instead of auto-detection.

## Phase 1: Dispatch Workers (parallel)

Launch all applicable workers simultaneously via Task tool. Each worker uses `subagent_type="general-purpose"`, `model="sonnet"`.

**CRITICAL: Launch all workers in a single message with multiple Task tool calls.** Do not dispatch sequentially.

For each worker, use this base dispatch template — replace placeholders with actual values. **Then apply the per-worker customizations below** before dispatching. Replace `{worker-instructions-path}` with the absolute path `{base-directory}/workers/{dimension}.md` (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load).

```
"You are a codebase audit worker specialized in {dimension}.

You have access to Glob, Grep, and Read tools. Do NOT use Bash for file search or content search — use Grep instead. Bash grep triggers permission prompts that halt execution.

Read your full instructions from `{worker-instructions-path}`.

Project context:
- Project root: `{project-root}`
- Language/framework: {detected-lang}
- CLAUDE.md conventions (respect these — do not flag intentional patterns):
{claude-md-content-or-'No CLAUDE.md found'}

{scope-section — see per-worker customizations below}

Execute your full analysis following the worker instructions. Return ONLY a valid JSON array of findings. No prose, no markdown fences, no explanation — just the raw JSON array starting with [ and ending with ]."
```

**Per-worker scope customizations:**

| Worker | File | Scope section to insert |
|--------|------|------------------------|
| code-quality | `workers/code-quality.md` | `Source files to analyze ({count} files): {file-list}` |
| test-quality | `workers/test-quality.md` | `Test files to analyze ({count} files): {test-file-list}` AND `Source files in the project ({count} files, for cross-referencing): {source-file-list}` — SKIP worker entirely if 0 test files |
| security | `workers/security.md` | `Source files in scope ({count} files): {file-list}` |
| dead-code | `workers/dead-code.md` | `Source root(s): {source-roots}` — do NOT send full file list (this worker uses Grep/Glob to discover references, not file-by-file reading) |
| architecture | `workers/architecture.md` | `Source root(s): {source-roots}` AND `docs/architecture.md exists: {yes/no}` — do NOT send full file list (this worker maps structure via Glob/Grep) |

**File list size limit:** If a worker's file list exceeds 100 paths, send only the first 100 and add: "There are {total} files total. The full list is too large — use Glob with pattern `{glob-pattern}` under `{source-root}` to discover the complete set. Prioritize the files listed above, then explore further as your turn budget allows."

## Phase 2: Aggregate

After all workers return, process the findings:

1. **Parse:** Each worker returns a JSON array. Parse all arrays into a single list. If a worker returns malformed output (prose mixed with JSON, markdown code fences around JSON, or invalid JSON), attempt to extract the JSON array from the response. If a worker's output is completely unparseable, note it in the report as "{dimension} worker: output could not be parsed" and continue with the other workers' results.

2. **Deduplicate:** If two findings reference the same file AND overlapping line ranges (any overlap), keep the one with higher severity. If same severity, keep higher confidence.

3. **Filter:** Remove any finding with confidence below 80 (default threshold). If the user specified a custom threshold, use that.

4. **Sort:** By severity (CRITICAL > HIGH > MEDIUM) then confidence descending within each severity level.

5. **Cap:** Maximum 25 findings in the report. If more than 25 pass the filter, keep the top 25 by the sort order above.

## Phase 3: Report

Present the unified report in this format:

```markdown
# Codebase Audit Report

**Project:** {project-root}
**Date:** {YYYY-MM-DD}
**Files analyzed:** {count} source, {count} test
**Confidence threshold:** {threshold}

## Executive Summary

{2-3 sentences: overall health, most critical dimension, biggest risk}

## Dimension Scores

| Dimension | Findings | Health |
|-----------|----------|--------|
| Code Quality | {count} | {GOOD / FAIR / NEEDS ATTENTION / CRITICAL} |
| Test Quality | {count} | {GOOD / FAIR / NEEDS ATTENTION / CRITICAL} |
| Security | {count} | {GOOD / FAIR / NEEDS ATTENTION / CRITICAL} |
| Dead Code | {count} | {GOOD / FAIR / NEEDS ATTENTION / CRITICAL} |
| Architecture | {count} | {GOOD / FAIR / NEEDS ATTENTION / CRITICAL} |

Health ratings (evaluate in order, first match wins):
- CRITICAL: any CRITICAL-severity finding in this dimension
- NEEDS ATTENTION: any HIGH-severity finding, or 4+ findings of any severity
- FAIR: 1-3 MEDIUM-severity findings
- GOOD: 0 findings

## Severity Breakdown

- CRITICAL: {count}
- HIGH: {count}
- MEDIUM: {count}

## Findings

| # | Sev | Conf | Dimension | Location | Issue |
|---|-----|------|-----------|----------|-------|
| 1 | CRITICAL | 95 | security | `src/auth.ts:45-92` | {title} |
| 2 | HIGH | 88 | code-quality | `src/utils.ts:120-180` | {title} |
| ... | | | | | |

### Finding Details

**1. {title}** (CRITICAL, 95% confidence)
- **File:** `src/auth.ts:45-92`
- **Dimension:** Security
- **Observed:** {what the code does and why it's a problem}

{repeat for each finding}

## Quick Wins

{List 3-5 findings that are HIGH confidence + LOW effort to fix, if any exist. These are items a developer could resolve in under 30 minutes each.}
```

## Phase 4: Kanban Handoff

If zero findings passed the filter, skip this phase — the skill is done after the report.

Otherwise, ask the user:

> "Would you like me to file these as KB entries for `/aligned:kanban-resolve`?"

If the user declines, the skill is done.

If the user agrees, file each finding using the `{base-directory}/../_shared/kanban-entry-format.md` template (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load) with these field mappings:

| Finding field | KB field |
|---------------|----------|
| `title` | Title (`KB-NNN: {title}`) |
| `file:line_range` | Location |
| `observed` | Observed |
| _(derive: inverse of observed, one sentence)_ | Expected |
| `CRITICAL` severity → `HIGH` | Severity (KB has no CRITICAL level) |
| `dimension` | Type as `audit-{dimension}` |
| `"codebase-audit"` | Discovered during |
| `"Audit finding — requires separate assessment before fixing"` | Why out of scope |

After filing all entries, report:

> "Filed N entries: KB-NNN through KB-MMM. Run `/aligned:kanban-resolve` to triage and resolve them."

## Finding Schema

Every worker must return findings in this exact JSON format:

```json
{
  "title": "Short imperative description",
  "file": "src/path/to/file.ts",
  "line_range": "45-92",
  "severity": "HIGH",
  "confidence": 85,
  "dimension": "security",
  "observed": "What the code does and why it's a problem (1-2 sentences)"
}
```

Severity levels: `CRITICAL`, `HIGH`, `MEDIUM`. No LOW — if it's not at least MEDIUM, don't report it.

Confidence range: 0-100 (but only 80+ makes it to the report by default).

## Confidence Scoring Rubric

All workers use this rubric consistently:

| Score | Meaning | Example |
|-------|---------|---------|
| 90-100 | Definitive issue, clear evidence, would flag in any review | SQL injection with string concatenation, 500-line function, exported function with zero references anywhere |
| 70-89 | Likely issue, some judgment involved | Function doing 3+ distinct things, test with no assertions, overly broad catch block |
| 50-69 | Possible issue, needs human verification | Naming inconsistency, slightly high complexity, potentially unused variable |
| Below 50 | Too speculative — do not report | |

## Red Flags — Things This Skill Must Never Do

- **Never edit source code.** This is a read-only audit. Diagnosis only.
- **Never file Kanban entries without user approval.** Always ask first. If the user declines, the skill is done after the report.
- **Never flag patterns documented in CLAUDE.md as issues.** If the project explicitly says "we use X pattern," that's intentional.
- **Never report LOW severity.** Minimum severity is MEDIUM. If it's not worth reporting, skip it.
- **Never exceed 25 findings.** More than 25 creates noise, not signal.
