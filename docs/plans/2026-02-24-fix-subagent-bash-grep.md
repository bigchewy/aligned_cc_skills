# Fix Sub-Agent Bash Grep Usage — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Prevent critique sub-agents from using Bash `grep` instead of the Grep tool, which triggers security prompts that halt plan critique pipelines.

**Source Design Doc:** N/A — root cause analysis from systematic debugging session

**Architecture:** Sub-agents spawned by the Task tool always have Bash available regardless of agent type. The only control point is the sub-agent prompt text. Each prompt has a tool-access line ("You have access to Glob, Grep, Read...") that must explicitly prohibit Bash for searching and teach the Grep tool's `output_mode: "count"` alternative for the common counting use case.

**Tech Stack:** Markdown skill files (no code)

---

## Context

**The problem:** The Verifier critique sub-agent runs commands like `grep -c " it(" file1.ts && grep -c " it(" file2.ts` via Bash. The `&&` chaining triggers Claude Code's "ambiguous syntax with command separators" security warning, which blocks the critique pipeline and requires manual approval.

**Root cause:** Sub-agent prompts list available tools positively ("You have access to Glob, Grep, Read...") without prohibiting Bash. Since Task agents always have Bash in their tool palette, the LLM defaults to it — especially for counting patterns, where `grep -c` is a stronger association than the Grep tool's `output_mode: "count"`. The user's CLAUDE.md already says "Never use Bash for file search" but this instruction loses salience in sub-agents buried under thousands of tokens of plan/checklist content.

**The fix:** Add an explicit Bash prohibition with practical reasoning to every sub-agent tool-access line, at maximum salience (same sentence as the tool list).

**Scope:** 13 sub-agent prompts across 4 SKILL.md files, plus 2 checklist files (already fixed in prior session).

---

### Task 1: Add Bash restriction to writing-plans sub-agent prompts

**Files:**
- Modify: `skills/writing-plans/SKILL.md` (lines 325, 349, 367, 390, 405)

**What to change:** For each of the 5 tool-access lines, insert the Bash restriction after the tool list clause. Each old_string below includes enough surrounding text to be unique in the file. The new_string replaces that exact span — preserving all text before and after.

**Line 325 (Architect R1):**
```
Old: "You have access to Glob, Grep, Read, and Write tools. Read `{checklist-path}` in full, then read `{plan-file-path}` in full. Then read key source files"
New: "You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{plan-file-path}` in full. Then read key source files"
```

**Line 349 (Verifier R1):**
```
Old: "You have access to Glob, Grep, Read, and Write tools for verifying claims. Read `{checklist-path}` in full"
New: "You have access to Glob, Grep, Read, and Write tools for verifying claims. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full"
```

**Line 367 (Aggregator):**
```
Old: "You have access to Glob and Read tools. Read all report files in `/tmp/plan-critique-{feature}/round-1/`."
New: "You have access to Glob and Read tools. Do not use Bash for searching. Read all report files in `/tmp/plan-critique-{feature}/round-1/`."
```

Note: The aggregator only reads report files — it doesn't search the codebase. A short restriction suffices since it's unlikely to reach for grep. But include it for consistency.

**Line 390 (Architect R2):**
```
Old: "You have access to Glob, Grep, Read, and Write tools. Read `{plan-file-path}` in full. Focus ONLY on the sections that changed (listed below). For each change, assess:"
New: "You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{plan-file-path}` in full. Focus ONLY on the sections that changed (listed below). For each change, assess:"
```

**Line 405 (Verifier R2):**
```
Old: "You have access to Glob, Grep, Read, and Write tools. Read `{plan-file-path}` in full. Focus ONLY on the sections that changed (listed below). For each change, verify:"
New: "You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{plan-file-path}` in full. Focus ONLY on the sections that changed (listed below). For each change, verify:"
```

**Verification:** Read lines 325, 349, 367, 390, 405 after editing. Each must contain the Bash restriction text.

---

### Task 2: Add Bash restriction to brainstorming sub-agent prompts

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (lines 20, 65, 165, 174, 183)

**Special case — Line 20 (Project Scanner):** This agent explicitly lists Bash in its tool access because it surveys projects (may need `npm test`, `wc -l`, etc.). Keep Bash in the tool list but add a restriction on using it for content search:

```
Old: "You have access to Bash, Glob, Grep, Read, and Write tools."
New: "You have access to Bash, Glob, Grep, Read, and Write tools. Use Bash only for system commands (e.g., npm, git) — never for content search. Use the Grep tool for searching file contents."
```

**Line 65 (Architect):**
```
Old: "You have access to Glob, Grep, and Read tools. For project context, first read"
New: "You have access to Glob, Grep, and Read tools. Do not use Bash for searching — use the Grep tool instead. For project context, first read"
```

**Line 165 (Fact-check critic):**
```
Old: "You have access to Glob, Grep, Read, and Write tools. Read `skills/brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. Also review the visual artifacts"
New: "You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `skills/brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. Also review the visual artifacts"
```

**Line 174 (Domain critic):**
```
Old: "You have access to Glob, Grep, Read, and Write tools. Read `skills/brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. Also review the visual artifacts at `docs/mockups/{session-name}/`"
New: "You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead. Bash grep triggers security prompts that halt execution. Read `skills/brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. Also review the visual artifacts at `docs/mockups/{session-name}/`"
```

Note: Lines 165 and 174 are disambiguated by including different amounts of trailing context. Line 165 ends at "Also review the visual artifacts" (mid-sentence), while line 174 extends through `docs/mockups/{session-name}/`.

**Line 183 (Aggregator):**
```
Old: "You are a critique aggregator. You have access to Glob and Read tools. Read all report files in `/tmp/brainstorm-critique-{topic}/round-1/`."
New: "You are a critique aggregator. You have access to Glob and Read tools. Do not use Bash for searching. Read all report files in `/tmp/brainstorm-critique-{topic}/round-1/`."
```

**Verification:** Read lines 20, 65, 165, 174, 183 after editing. Each must contain Bash restriction text. Line 20 must still list Bash as available.

---

### Task 3: Add Bash restriction to business-brainstorming sub-agent prompt

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md` (line 118)

```
Old: "You have access to Glob, Grep, Read, WebSearch, and WebFetch tools for verifying claims. Read `skills/business-brainstorming/design-critique-checklist.md` in full"
New: "You have access to Glob, Grep, Read, WebSearch, and WebFetch tools for verifying claims. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `skills/business-brainstorming/design-critique-checklist.md` in full"
```

Note: This critic runs Phase 1 fact-checking (counting, verifying claims), so it gets the full restriction with `output_mode` guidance.

**Verification:** Read line 118 after editing. Must contain Bash restriction.

---

### Task 4: Add Bash restriction to business-write-plan sub-agent prompts

**Files:**
- Modify: `skills/business-write-plan/SKILL.md` (lines 149, 163)

**Line 149 (Richard Rumelt):**
```
Old: "You have access to Glob, Grep, and Read tools for verifying claims. Read `{checklist-path}` in full, then read `{plan-file-path}` in full.\n\n   Evaluate the plan through your strategic lens."
New: "You have access to Glob, Grep, and Read tools for verifying claims. Do not use Bash for searching — use the Grep tool instead. Read `{checklist-path}` in full, then read `{plan-file-path}` in full.\n\n   Evaluate the plan through your strategic lens."
```

**Line 163 (The PM):**
```
Old: "You have access to Glob, Grep, and Read tools for verifying claims. Read `{checklist-path}` in full, then read `{plan-file-path}` in full. Your job has two phases:"
New: "You have access to Glob, Grep, and Read tools for verifying claims. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{plan-file-path}` in full. Your job has two phases:"
```

Note: Lines 149 and 163 are disambiguated by their trailing context — 149 continues with a blank line then "Evaluate the plan through your strategic lens", while 163 continues with "Your job has two phases:". The PM does fact-checking with counts (Phase 1), so it gets the full restriction with `output_mode` guidance. Rumelt does strategic evaluation, so a shorter restriction suffices.

**Verification:** Read lines 149, 163 after editing. Both must contain Bash restriction.

---

### Task 5: Verify checklist fixes from prior session

**Files:**
- Read: `skills/writing-plans/plan-critique-checklist.md` (line 174)
- Read: `skills/brainstorming/design-critique-checklist.md` (line 178)

These were already fixed in the prior session (changed "run greps" → "use Read, Grep, and Glob tools (never Bash grep)"). Verify the fixes are still in place and consistent with the sub-agent prompt changes.

**Verification:** Both lines must say "use Read, Grep, and Glob tools (never Bash grep)" — not "run greps".

---

### Task 6: Commit

**Depends on:** Tasks 1–5 must be complete before this task.

```bash
git add skills/writing-plans/SKILL.md skills/brainstorming/SKILL.md skills/business-brainstorming/SKILL.md skills/business-write-plan/SKILL.md skills/writing-plans/plan-critique-checklist.md skills/brainstorming/design-critique-checklist.md
git commit -m "fix: add explicit Bash grep prohibition to all sub-agent prompts"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Where to place the restriction | Sub-agent prompt tool-access line | CLAUDE.md only, checklist only, agent type change |
| 2 | How to phrase the restriction | Practical consequence ("triggers security prompts") | Authoritative ("never use Bash"), lying ("you don't have Bash") |
| 3 | Project scanner Bash access | Keep Bash, restrict to system commands | Remove Bash entirely, no restriction |
| 4 | Aggregator agents | Short restriction for consistency | Skip entirely (low risk) |

### Appendix: Decision Details

#### Decision 1: Where to place the restriction
**Chose:** Sub-agent prompt tool-access line (same sentence as "You have access to...")
**Why:** This is the highest-salience location for the LLM when it decides which tool to use. The user's CLAUDE.md already says "Never use Bash for file search" — and sub-agents inherit it — but it doesn't work because it gets buried under thousands of tokens of plan/checklist/codebase content by the time the agent reaches for grep. The restriction must be at the point of decision, not in a distant system instruction.
**Alternatives rejected:**
- CLAUDE.md only: Already exists, already fails for sub-agents.
- Checklist only: Weaker behavioral signal (data vs. instruction). Fixed as a contributing factor but insufficient alone.
- Agent type change: No Task agent type excludes Bash. Not a viable lever.

#### Decision 2: How to phrase the restriction
**Chose:** Practical consequence — "Bash grep triggers security prompts that halt execution"
**Why:** LLMs respond better to practical reasoning than authority. "Don't do X because it breaks the pipeline" is more persuasive than "Don't do X because rules say so." The `output_mode: 'count'` guidance also addresses the specific use case (counting matches) that drives the Bash grep behavior — the agent reaches for `grep -c` because it doesn't know the Grep tool can count.
**Alternatives rejected:**
- "You don't have Bash": A lie — the agent does have Bash and would discover this if it tried. Deception in prompts has unpredictable downstream effects.
- "Never use Bash" (bare authority): Weaker signal without the practical consequence.

#### Decision 3: Project scanner Bash access
**Chose:** Keep Bash available, add "Use Bash only for system commands, never for content search"
**Why:** The project scanner surveys the project — it may legitimately need `npm test`, `git log`, `wc -l`, etc. Removing Bash would break valid use cases. The restriction is scoped to content search specifically.
**Alternatives rejected:**
- Remove Bash entirely: Would break project survey functionality.
- No restriction: Would leave the scanner vulnerable to the same Bash grep pattern.

#### Decision 4: Aggregator agents
**Chose:** Add short restriction ("Do not use Bash for searching") for consistency
**Why:** Aggregators only read report files and are unlikely to reach for grep. But consistency across all sub-agent prompts prevents future confusion and costs nothing. The restriction is minimal (one short sentence) since the full `output_mode` guidance isn't needed for agents that don't search codebases.
**Alternatives rejected:**
- Skip entirely: Creates an inconsistency that could confuse future skill authors who look at aggregator prompts as templates.
