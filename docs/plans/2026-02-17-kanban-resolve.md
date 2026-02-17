# Kanban Board Resolution Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Resolve 5 Kanban board items (4 actionable, 1 skipped)
**Source Design Doc:** N/A
**Architecture:** Mechanical refactoring — no architectural changes
**Tech Stack:** Markdown files, JavaScript (hooks)

---

## Skipped Items

| KB | Title | Reason |
|----|-------|--------|
| KB-008 | create-design-principles embeds critique prompts inline | False positive — all critique-capable skills use the same inline dispatch pattern. Not a deviation. |

---

### Task 1: Factor shared fields in error-tracker.js

**KBs:** KB-004

**Files:**
- Modify: `hooks/error-tracker.js`

**Step 1:** Read `hooks/error-tracker.js` in full.

**Step 2:** In the `processEvent` function, extract the 5 shared fields from the two return branches into a `base` object at the top of the function:

```js
const base = {
  ts: new Date().toISOString(),
  sid: data.session_id,
  tool: data.tool_name,
  input: summarize(data.tool_name, data.tool_input),
  cwd: data.cwd
};
```

**Step 3:** Replace the `PostToolUseFailure` branch return (currently lines ~33-42) with:

```js
return {
  ...base,
  type: 'tool_failure',
  error: data.error || 'Unknown tool failure',
  interrupt: data.is_interrupt || false,
};
```

**Step 4:** Replace the `PostToolUse` branch return (currently lines ~49-57) with:

```js
return {
  ...base,
  type: 'command_error',
  error: sig,
};
```

**Step 5:** Verify syntax: `node -c hooks/error-tracker.js` — expected output: no errors.

**Step 6:** Commit:

```bash
git add hooks/error-tracker.js
git commit -m "refactor: factor shared fields into base object in error-tracker processEvent"
```

---

### Task 2: Add conditional gate to business-write-plan Round 2 critique

**KBs:** KB-005

**Files:**
- Modify: `skills/business-write-plan/SKILL.md`

**Step 1:** Read `skills/business-write-plan/SKILL.md` in full.

**Step 2:** Find the Round 2 section (around line 120). Change `**Round 2:**` to `**Round 2 (conditional):**`.

**Step 3:** Insert as the first line of the Round 2 section: `Only run if Round 1 found medium or high severity issues. Use fresh sub-agents (do NOT resume Round 1 agents).`

This matches the pattern used in `skills/brainstorming/SKILL.md`, `skills/business-brainstorming/SKILL.md`, and `skills/writing-plans/SKILL.md`.

**Step 4:** Re-read the modified section to verify it reads naturally and matches peer skills.

**Step 5:** Commit:

```bash
git add skills/business-write-plan/SKILL.md
git commit -m "fix: gate business-write-plan Round 2 critique on Round 1 severity"
```

---

### Task 3: Update stale critic-registry reference in business-brainstorming

**KBs:** KB-006

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md`

**Step 1:** Read `skills/business-brainstorming/SKILL.md` in full.

**Step 2:** Find line 109 where it reads `skills/brainstorming/critic-registry.md`. Change this to `advisors/registry.md`.

This matches how `skills/brainstorming/SKILL.md` (the sibling skill) already references the canonical registry directly.

**Step 3:** Verify that `advisors/registry.md` exists in the repo (Glob check).

**Step 4:** Re-read the modified section to verify it reads naturally.

**Step 5:** Commit:

```bash
git add skills/business-brainstorming/SKILL.md
git commit -m "fix: update business-brainstorming critic-registry ref to canonical advisors/registry.md"
```

---

### Task 4: Add mutual editor notes to add-advisor and add-framework

**KBs:** KB-007

**Files:**
- Modify: `skills/add-advisor/SKILL.md`
- Modify: `skills/add-framework/SKILL.md`

**Step 1:** Read `skills/add-advisor/SKILL.md` and `skills/add-framework/SKILL.md` in parallel.

**Step 2:** In `skills/add-advisor/SKILL.md`, after the Step 0 print summary block (around line 48), add:

```
> **Editor note:** A parallel environment detection section exists in `skills/add-framework/SKILL.md` (Step 0). If you change the path-detection priority order here, apply the equivalent change there.
```

**Step 3:** In `skills/add-framework/SKILL.md`, after the Step 0 print summary block (around line 45), add:

```
> **Editor note:** A parallel environment detection section exists in `skills/add-advisor/SKILL.md` (Step 0). If you change the path-detection priority order here, apply the equivalent change there.
```

**Step 4:** Re-read both modified sections to verify they read naturally.

**Step 5:** Commit:

```bash
git add skills/add-advisor/SKILL.md skills/add-framework/SKILL.md
git commit -m "docs: add mutual cross-references between add-advisor and add-framework env detection"
```

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|-------------|------------------------|
| 1 | Item grouping | No grouping — all 4 items are structurally different | Group KB-005/KB-006 (both single-line markdown changes) — rejected because they modify different files for different reasons |
| 2 | KB-007 fix approach | Mutual editor notes (triage recommendation) | Extract to shared file — rejected by triage: markdown has no import mechanism, would add indirection without enforcement |
| 3 | Verification approach | `node -c` for JS, content re-read for markdown | `npm test`/`npm run build` — not applicable, no test/build infrastructure in this repo |
