---
name: test-auditor
description: |
  Audit the test suite for quality, value, coverage gaps, and anti-patterns. Dispatches 4 worker sub-agents in parallel, aggregates results into a unified report. Use when you want to evaluate whether existing tests are actually testing meaningful behavior. Examples: <example>Context: The [TEST AUDIT] hook tag fires. user: "[TEST AUDIT] Last test suite audit was 2 day(s) ago..." assistant: "A test suite audit is due. Let me run that now." <commentary>The hook tag fired, so dispatch the test-auditor agent to audit the test suite.</commentary></example>
model: inherit
---

# Test Suite Auditor

Orchestrates a comprehensive test suite audit across 4 quality dimensions using specialized worker sub-agents.

## What This Audits

| Worker | What It Finds |
|--------|---------------|
| Business Logic Auditor | Tests that validate framework behavior (Supabase, AI SDK, Zod) instead of app code |
| Value Auditor | Low-value tests (Usefulness Score < 15) that aren't worth maintaining |
| Coverage Gap Auditor | Critical business logic (auth, chat, sessions) with no test coverage |
| Isolation & Anti-Pattern Auditor | The Liar (no assertions), Happy Path Only, Mock Everything, Giant tests |

## Workflow

### Phase 1: Discovery

1. Detect test file patterns from the project's test config (jest.config.*, vitest.config.*, or `src/**/*.test.{ts,tsx,js,jsx}` as fallback)
2. Use Glob to find all test files matching the detected pattern
3. Count total test files and report to user

### Phase 2: Dispatch Workers

Launch all 4 workers in PARALLEL using the Task tool. Each worker gets the same prompt structure:

```
Task(
  description: "Test audit: [worker-name]",
  prompt: "Read agents/workers/test-audit-[worker-name].md in full. Follow its instructions exactly. Analyze the test suite in the current project directory. Detect test file patterns from the project's test config (jest.config.*, vitest.config.*, or `src/**/*.test.{ts,tsx,js,jsx}` as fallback). Return your findings as a single JSON code block.",
  subagent_type: "general-purpose"
)
```

Workers to dispatch (ALL in a single message for parallel execution):
1. `test-audit-business-logic.md`
2. `test-audit-value.md`
3. `test-audit-coverage-gap.md`
4. `test-audit-isolation-antipattern.md`

### Phase 3: Aggregate Results

1. Parse JSON output from each worker. If a worker failed or returned invalid JSON:
   - Report which worker failed and show the raw output for debugging
   - Continue aggregating results from successful workers (partial results are still useful)
2. Merge all findings into a single array, sorted by severity (CRITICAL → HIGH → MEDIUM → LOW)
3. Sum severity counts across all workers
4. Calculate overall score: average of 4 worker scores
5. De-duplicate: if two workers flag the same test file:line, keep the higher-severity finding

### Phase 4: Report

Present the unified report:

```markdown
## Test Suite Audit Report

### Executive Summary
[2-3 sentences: overall health, biggest concerns, top recommendation]

### Scores

| Category | Score | Issues |
|----------|-------|--------|
| Business Logic Focus | X/10 | X framework tests found |
| Test Value | X/10 | X low-value tests |
| Coverage Gaps | X/10 | X critical paths untested |
| Isolation & Anti-Patterns | X/10 | X anti-pattern instances |
| **Overall** | **X/10** | **X total issues** |

### Severity Summary

| Severity | Count |
|----------|-------|
| Critical | X |
| High | X |
| Medium | X |
| Low | X |

### Findings

[Table of all findings sorted by severity, with columns: Severity, Location, Issue, Category, Recommendation, Effort]

### Quick Wins (Effort = S)

[Filtered list of findings where effort = S, grouped by action type: DELETE vs. ADD vs. REFACTOR]
```

### Phase 5: Update Timestamp

After presenting the report, write the current Unix timestamp to `~/.claude/last-test-audit.timestamp` using the Write tool. This resets the 1-day timer for the UserPromptSubmit hook.

## Important Notes

- This is a READ-ONLY audit. Do not modify any test files.
- Workers may take 2-5 minutes each. All 4 run in parallel.
- Some findings may overlap between workers (e.g., business-logic-auditor and value-auditor may both flag the same trivial test). De-duplication in Phase 3 handles this.
- The report is displayed to the user, not written to a file. The user decides what to act on.
