# Brainstorming Skill Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Merge `/aligned:brainstorming` and `/aligned:business-brainstorming` into a single unified skill with a thin router that auto-detects mode and dispatches to mode-specific process files.

**Source Design Doc:** `docs/plans/2026-04-02-brainstorming-skill-unification-design.md`

**Mockups:** `docs/mockups/brainstorming-skill-unification.html`

**Architecture:** The current two-skill setup (`skills/brainstorming/` and `skills/business-brainstorming/`) is replaced by a single `skills/brainstorming/` directory with a thin router SKILL.md that classifies user intent (software vs business) and reads the appropriate mode file from `skills/brainstorming/modes/`. Each mode file preserves the full process logic from its predecessor skill. Cross-references across the plugin are updated to remove all live references to `business-brainstorming`.

**Tech Stack:** Markdown skill files (no runtime code), Git for file operations, eval scenarios in TypeScript

---

### ✅ Task 1: Move the business critique checklist

**Files:**
- Move: `skills/business-brainstorming/design-critique-checklist.md` → `skills/brainstorming/business-critique-checklist.md`

**Step 1: Copy the file to its new location**

```bash
cp skills/business-brainstorming/design-critique-checklist.md skills/brainstorming/business-critique-checklist.md
```

**Step 2: Verify the copy**

Run: `diff skills/business-brainstorming/design-critique-checklist.md skills/brainstorming/business-critique-checklist.md`
Expected: No output (files are identical)

**Step 3: Commit**

```bash
git add skills/brainstorming/business-critique-checklist.md
git commit -m "chore: copy business critique checklist to brainstorming directory"
```

---

### ✅ Task 2: Create the software mode file

**Files:**
- Create: `skills/brainstorming/modes/software.md`
- Reference: `skills/brainstorming/SKILL.md` (source content to adapt)

**Step 1: Create the modes directory**

```bash
mkdir -p skills/brainstorming/modes
```

**Step 2: Write `modes/software.md`**

Adapt the current `skills/brainstorming/SKILL.md` content with these changes:

**Remove:**
- YAML frontmatter (`---` block with name/description)
- The project scan dispatch instruction (lines 20-23 of current SKILL.md: the `"Read agents/project-scanner.md..."` dispatch block)

**Add at the top (before the first heading):**
```markdown
<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->
```

**Change the scan reference.** Replace the dispatch block and surrounding text:

Current text (the "MANDATORY" paragraph through the dispatch template):
```
**MANDATORY: You MUST dispatch the project scan before proposing any design.** Do not skip the scan because the user's message seems clear — the scan reveals codebase context that shapes which questions to ask. Skipping the scan is a skill violation.

First, dispatch a project scan agent via Task tool (subagent_type=general-purpose), running in the background:

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`."
```

Replace with:
```
**MANDATORY: The router has already dispatched a project scan.** Results will be available at `/tmp/brainstorm-context-{topic}/project-scan.md`. Do not dispatch a second scan.
```

**Update critique panel config block.** In the "Fact-Check + Critique Panel" section, change `skill-name`:
- From: `Skill name: brainstorming`
- To: `Skill name: brainstorming` (unchanged — the unified skill is still named `brainstorming`)

This is a no-op confirmation — the skill name stays the same.

**Update the Design Critique section's checklist path.** The "Design Critique" section near the bottom of the file contains: "Use the checklist at `{base-directory}/design-critique-checklist.md`." Since this mode file lives in `modes/`, not at `{base-directory}` itself, update the path to: `{base-directory}/design-critique-checklist.md`. Note: `{base-directory}` is always the router's directory (passed down from the router in Step 3), not the mode file's own directory. The path is already correct as-is. Add a clarifying comment above the Design Critique section:

```markdown
<!-- Note: {base-directory} refers to the router's directory (skills/brainstorming/), not this file's directory. -->
```

**Preserve everything else intact:**
- The "Overlap with first business question" paragraph
- The "Scan gate" paragraph
- The minimum 3 business questions rule
- Full business/technical question classification
- Architect auto-consult (proxy + review modes) with all dispatch templates
- Gray area handling, mockup-generator dispatch
- Design presentation in 200-300 word sections
- The entire "After the Design" section: documentation, visualization (mandatory), nested sub-tabs rule, fact-check + critique panel (division-of-labor), visualization refresh, commit instruction, next step prompt
- The "Design Critique" section (with the clarifying comment added above it)
- The "Key Principles" section

**Step 3: Verify the file exists and has expected structure**

Run: Glob for `skills/brainstorming/modes/software.md`
Expected: File exists

Read the file and verify it:
- Has NO YAML frontmatter
- Has the HTML comment at the top
- Has "The router has already dispatched a project scan" text
- Has the "Overlap with first business question" section
- Has the "Scan gate" section
- Has the "Architect auto-consult" section
- Has the critique panel config with `Skill name: brainstorming` and `Checklist filename: design-critique-checklist.md` and `Fact-check mode: division-of-labor`
- Has the "Next step prompt" section

**Step 4: Commit**

```bash
git add skills/brainstorming/modes/software.md
git commit -m "feat: create software mode file for unified brainstorming skill"
```

---

### ✅ Task 3: Create the business mode file

**Files:**
- Create: `skills/brainstorming/modes/business.md`
- Reference: `skills/business-brainstorming/SKILL.md` (source content to adapt)

**Step 1: Write `modes/business.md`**

Adapt the current `skills/business-brainstorming/SKILL.md` content with these changes:

**Remove:**
- YAML frontmatter (`---` block with name/description)
- The project scan dispatch block in Phase 1 (lines 20-23 of current business-brainstorming/SKILL.md):
  ```
  Dispatch a project scan agent via Task tool (subagent_type=general-purpose), running in the background:

  "Read `agents/project-scanner.md` for your full workflow.
  Scan the project at `{project-root}` for brainstorm topic `{topic}`."
  ```

**Add at the top (before the first heading):**
```markdown
<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->
```

**Change the scan reference in Phase 1.** Replace the removed dispatch block with:
```
**The router has already dispatched a project scan.** Results will be available at `/tmp/brainstorm-context-{topic}/project-scan.md`. Do not dispatch a second scan.
```

**Update critique panel config block.** In the "Fact-Check + Critique Panel" section, change:
- From: `Skill name: business-brainstorming`
- To: `Skill name: brainstorming`

And change checklist filename:
- From: `Checklist filename: design-critique-checklist.md`
- To: `Checklist filename: business-critique-checklist.md`

**Update the Design Critique section's checklist path.** The "Design Critique" section near the bottom of the file contains: "Use the checklist at `{base-directory}/design-critique-checklist.md`." Update this to: `{base-directory}/business-critique-checklist.md` (since business mode uses the business checklist). Add a clarifying comment above the Design Critique section:

```markdown
<!-- Note: {base-directory} refers to the router's directory (skills/brainstorming/), not this file's directory. -->
```

**Preserve everything else intact:**
- 4-phase gated structure: Goal → Problems → Root Causes → Solutions (all gates mandatory)
- "Don't idle" guidance (the "Overlap with first goal question" paragraph)
- Problem categorization taxonomy, root cause probing, "Why?" chains
- 2-3 approaches with recommendation
- Design presentation in 200-300 word sections
- The entire "After the Design" section: documentation, visualization (conditional), nested sub-tabs rule, fact-check + critique panel (all-critics with WebSearch/WebFetch), visualization refresh, post-design steps, next step prompt
- The "Design Critique" section (with the clarifying comment added above it, and checklist path updated to `business-critique-checklist.md`)
- The "Key Principles" section

**Step 2: Verify the file exists and has expected structure**

Read the file and verify it:
- Has NO YAML frontmatter
- Has the HTML comment at the top
- Has "The router has already dispatched a project scan" text
- Has Phase 1 through Phase 4 with gates
- Has the critique panel config with `Skill name: brainstorming` and `Checklist filename: business-critique-checklist.md` and `Fact-check mode: all-critics`
- Has `fact-check tools: Glob, Grep, Read, WebSearch, WebFetch`
- Has the next step prompt routing to `/aligned:business-write-plan`

**Step 3: Commit**

```bash
git add skills/brainstorming/modes/business.md
git commit -m "feat: create business mode file for unified brainstorming skill"
```

---

### ✅ Task 4: Rewrite the brainstorming router SKILL.md

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (complete rewrite)

**Step 1: Write the new router**

Replace the entire contents of `skills/brainstorming/SKILL.md` with the router defined in the design doc's "Router SKILL.md" section. The router is ~60-80 lines and does three things:

1. Classifies mode from user's topic + environment context
2. Dispatches project scan (background) with mode context
3. Hands off to the appropriate mode file with explicit checklist path and `{base-directory}`

Use the exact markdown from the design doc's "Router SKILL.md" section (the code block starting with the `---` frontmatter through the closing ` ``` `). This is the full router content:

```markdown
---
name: brainstorming
description: "Use before any creative or strategic work — software features,
  business strategy, analysis, or decision-making. Detects whether the topic
  is software design or business strategy and adapts the process accordingly."
---

# Brainstorming

## Overview
A unified brainstorming skill that adapts its process based on what you're
working on. Software/technical topics get a fluid Q&A with Architect
auto-consult. Business/strategy topics get a structured 4-phase process
(Goal → Problems → Root Causes → Solutions).

## Step 1: Detect Mode
Classify the user's topic into one of two modes:

**Signal precedence:** Topic keywords take priority over environment signals.
A user in a code repo asking about "pricing strategy" is business mode, not
software mode. Environment is a tiebreaker when topic keywords are absent.

**Software mode** — building, modifying, or designing software:
- Topic signals: features, components, APIs, bugs, refactoring, architecture,
  implementation, code, testing, data models
- Environment (tiebreaker): project contains code files (package.json,
  Cargo.toml, go.mod, pyproject.toml, etc.)

**Business mode** — strategy, decisions, analysis, or non-code deliverables:
- Topic signals: strategy, sales, marketing, positioning, meeting prep,
  decisions, stakeholders, pricing, proposals, planning, analysis
- Environment (tiebreaker): project is docs-only, Obsidian vault, or
  non-code directory

**If signals are clear:** Auto-route and briefly tell the user which mode
was selected (e.g., "This looks like a software design problem — I'll use
the technical brainstorming process."). Add: "If this isn't right, just
say so and I'll switch." Proceed to Step 2.

**If signals are mixed or absent:** Ask one question: "Is this a
software/technical design or a business/strategy problem?" Then proceed
to Step 2 based on the answer.

## Step 2: Project Scan
Dispatch a project scan agent via Task tool (subagent_type=general-purpose),
running in the background. Now that mode is known, pass it to the scanner:

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`.
Mode: {software|business} — emphasize {code artifacts|domain materials}
accordingly."

Do not wait for the scan to complete before proceeding to Step 3.

## Step 3: Hand Off to Mode

**If software mode:**
Read `{base-directory}/modes/software.md` and follow its process.
The base directory for this skill is `{base-directory}`.
The critique checklist for this session is at
`{base-directory}/design-critique-checklist.md`.
The shared orchestration file is at
`{base-directory}/../_shared/critique-panel-orchestration.md`.

**If business mode:**
Read `{base-directory}/modes/business.md` and follow its process.
The base directory for this skill is `{base-directory}`.
The critique checklist for this session is at
`{base-directory}/business-critique-checklist.md`.
The shared orchestration file is at
`{base-directory}/../_shared/critique-panel-orchestration.md`.

**If the mode file cannot be Read, STOP and tell the user the plugin
installation may be incomplete.**
```

**Step 2: Verify the router**

Read the new `skills/brainstorming/SKILL.md` and verify:
- Frontmatter `name: brainstorming` is present
- Description mentions both software and business/strategy
- Step 1 has signal precedence rule (topic > environment)
- Step 2 dispatches project scan with mode context
- Step 3 hands off to `modes/software.md` or `modes/business.md`
- Step 3 passes explicit checklist paths (`design-critique-checklist.md` for software, `business-critique-checklist.md` for business)
- Step 3 passes `{base-directory}` and shared orchestration path
- Has the "mode file cannot be Read" guard

**Step 3: Commit**

```bash
git add skills/brainstorming/SKILL.md
git commit -m "feat: rewrite brainstorming SKILL.md as unified router"
```

---

### ✅ Task 5: Delete the business-brainstorming directory

**Files:**
- Delete: `skills/business-brainstorming/SKILL.md`
- Delete: `skills/business-brainstorming/design-critique-checklist.md`
- Delete: `skills/business-brainstorming/critic-registry.md`

**Step 1: Remove the directory**

```bash
git rm -r skills/business-brainstorming/
```

**Step 2: Verify deletion**

Run: Glob for `skills/business-brainstorming/*`
Expected: No matches

**Step 3: Commit**

```bash
git commit -m "feat: remove business-brainstorming directory (merged into brainstorming)"
```

---

### ✅ Task 6: Update cross-reference in business-write-plan

**Files:**
- Modify: `skills/business-write-plan/SKILL.md` (the predecessor reference on line 18)

**Step 1: Update the reference**

Change:
```
**Context:** This should follow a design created by /aligned:business-brainstorming, or a clear objective from the user.
```
To:
```
**Context:** This should follow a design created by /aligned:brainstorming, or a clear objective from the user.
```

**Step 2: Verify**

Read the modified line and confirm it says `/aligned:brainstorming`.

**Step 3: Commit**

```bash
git add skills/business-write-plan/SKILL.md
git commit -m "fix: update business-write-plan predecessor reference to unified brainstorming"
```

---

### ✅ Task 7: Update cross-references in kickstart

**Files:**
- Modify: `skills/kickstart/SKILL.md` (4 locations)

This task modifies the same file in all 4 locations. Apply all changes before committing.

**Step 1: Update the workflow list item (line 239)**

Change:
```
- `/aligned:business-brainstorming` — before any business work
```
To:
```
- `/aligned:brainstorming` — before any creative or strategic work
```

**Step 2: Update the permission entry (line 355)**

Delete the line `      "Skill(aligned:business-brainstorming)",` entirely (not replaced with blank — the line is removed so the surrounding entries become adjacent). The `Skill(aligned:brainstorming)` entry already exists in the permissions list (line 335 of the current file), so no replacement is needed. Verify no trailing comma issue by checking that the preceding line's comma is followed by a valid entry on the next line.

**Step 3: Update the three next-step messages (lines 379, 381, 383)**

For each of the three template messages (Business, Personal, General), change `/aligned:business-brainstorming` to `/aligned:brainstorming`.

Line 379 (Business):
```
**Business:** "Project scaffolded. Start with `/aligned:business-brainstorming` to define your first initiative, or fill in the CLAUDE.md guardrails section with confidentiality rules for this workspace."
```
→
```
**Business:** "Project scaffolded. Start with `/aligned:brainstorming` to define your first initiative, or fill in the CLAUDE.md guardrails section with confidentiality rules for this workspace."
```

Line 381 (Personal):
```
**Personal:** "Project scaffolded. Start with `/aligned:business-brainstorming` to define your first initiative, or fill in the guardrails section of CLAUDE.md with any privacy constraints (health data, finances, etc.)."
```
→
```
**Personal:** "Project scaffolded. Start with `/aligned:brainstorming` to define your first initiative, or fill in the guardrails section of CLAUDE.md with any privacy constraints (health data, finances, etc.)."
```

Line 383 (General):
```
**General:** "Project scaffolded. Start with `/aligned:business-brainstorming` to define your first initiative, or fill in the CLAUDE.md sections as you discover what conventions matter for this workspace."
```
→
```
**General:** "Project scaffolded. Start with `/aligned:brainstorming` to define your first initiative, or fill in the CLAUDE.md sections as you discover what conventions matter for this workspace."
```

**Step 4: Verify**

Grep `skills/kickstart/SKILL.md` for `business-brainstorming`.
Expected: 0 matches

**Step 5: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "fix: update kickstart cross-references from business-brainstorming to brainstorming"
```

---

### ✅ Task 8: Update cross-reference in critique-panel-orchestration

**Files:**
- Modify: `skills/_shared/critique-panel-orchestration.md` (line 9, the example value)

**Step 1: Update the example**

Change:
```
- `skill-name` must be set (e.g., "brainstorming", "business-brainstorming")
```
To:
```
- `skill-name` must be set (e.g., "brainstorming")
```

**Step 2: Verify**

Read line 9 and confirm the change.

**Step 3: Commit**

```bash
git add skills/_shared/critique-panel-orchestration.md
git commit -m "fix: remove business-brainstorming example from critique-panel-orchestration"
```

---

### ✅ Task 9: Update README.md cross-references

**Files:**
- Modify: `README.md` (2 locations: permission entry and skill table)

**Step 1: Remove the permission entry (line 57)**

Delete this line entirely from the permissions allow array:
```
      "Skill(aligned:business-brainstorming)",
```

**Step 2: Merge the skill table row (line 83)**

Change the brainstorming row:
```
| brainstorming | Pipeline | `/aligned:brainstorming` | Explore ideas, generate designs with multi-critic review |
```
To:
```
| brainstorming | Pipeline | `/aligned:brainstorming` | Explore ideas and strategies — auto-detects software vs business mode |
```

Delete the business-brainstorming row entirely:
```
| business-brainstorming | Business | `/aligned:business-brainstorming` | Explore business problems, strategies, decisions |
```

**Step 3: Add changelog entry**

Before line 199 (`#### 0.6.0`), insert:

```markdown
#### 0.13.0 — Unified Brainstorming Skill
- **BREAKING:** `/aligned:business-brainstorming` merged into `/aligned:brainstorming`. The unified skill auto-detects whether your topic is software/technical or business/strategy and adapts accordingly. Update any project CLAUDE.md files that reference `/aligned:business-brainstorming`.

```

**Step 4: Verify**

Grep `README.md` for `business-brainstorming`.
Expected: Only the 0.3.0 changelog entry (line ~215, historical) should remain.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: update README for brainstorming unification (permissions, skill table, changelog)"
```

---

### ✅ Task 10: Version bump

**Files:**
- Modify: `.claude-plugin/plugin.json` (version field)
- Modify: `.claude-plugin/marketplace.json` (version field)

**Step 1: Bump plugin.json**

Change:
```json
  "version": "0.12.0",
```
To:
```json
  "version": "0.13.0",
```

**Step 2: Bump marketplace.json**

Change:
```json
      "version": "0.12.0"
```
To:
```json
      "version": "0.13.0"
```

**Step 3: Verify both match**

Read both files and confirm version is `0.13.0` in each.

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version to 0.13.0"
```

---

### ✅ Task 11: Close kanban items KB-023, KB-024, KB-025

**Files:**
- Move: `docs/kanban/todo/KB-023-extract-visualization-refresh-block.md` → `docs/kanban/done/`
- Move: `docs/kanban/todo/KB-024-consolidate-nested-sub-tabs-rule.md` → `docs/kanban/done/`
- Move: `docs/kanban/todo/KB-025-extract-initial-visualization-dispatch.md` → `docs/kanban/done/`

**Step 1: Move all three files**

```bash
git mv docs/kanban/todo/KB-023-extract-visualization-refresh-block.md docs/kanban/done/
git mv docs/kanban/todo/KB-024-consolidate-nested-sub-tabs-rule.md docs/kanban/done/
git mv docs/kanban/todo/KB-025-extract-initial-visualization-dispatch.md docs/kanban/done/
```

**Step 2: Verify**

Run: Glob for `docs/kanban/done/KB-02[345]*`
Expected: 3 files found

**Step 3: Commit**

```bash
git commit -m "chore: close KB-023, KB-024, KB-025 as resolved-by-unification"
```

---

### Task 12: Add eval scenario for brainstorming mode routing

**Files:**
- Modify: `e2e/scenarios/kickstart-expansion.test.ts` (add scenario documenting the unification)

Note: The existing eval file has no direct references to `business-brainstorming` — the business template workflows comment says "business skills + content generation skills" generically. No edits to existing scenarios are needed. Instead, add a new scenario documenting the behavioral change.

**Step 1: Add a new scenario comment block**

After the existing Scenario 7 (Idempotency), append:

```typescript
// Scenario 8: Brainstorming unification (v0.13.0)
// Context: /aligned:business-brainstorming was merged into /aligned:brainstorming
// Expected (business template): Workflows section references /aligned:brainstorming, not /aligned:business-brainstorming
// Expected (personal template): Next-step message references /aligned:brainstorming
// Expected (general template): Next-step message references /aligned:brainstorming
// Expected (software template): No change — already used /aligned:brainstorming
```

**Step 2: Verify**

Read `e2e/scenarios/kickstart-expansion.test.ts` and confirm Scenario 8 is present at the end.

**Step 3: Commit**

```bash
git add e2e/scenarios/kickstart-expansion.test.ts
git commit -m "test: add eval scenario for brainstorming unification (v0.13.0)"
```

---

### Task 13: Final verification sweep

**Files:**
- No changes — verification only

**Step 1: Grep for stale references**

Grep the entire repo for `business-brainstorming`, excluding:
- `docs/plans/completed/` (historical plans)
- `docs/kanban/done/` (closed kanban items)
- `docs/mockups/` (historical visualization artifacts)
- `docs/workflow.html` (historical)
- `.obsidian/` (workspace state)
- `docs/plans/2026-04-02-brainstorming-skill-unification-design.md` (the design doc itself)

Expected: 0 matches in live files. Only historical artifacts should reference `business-brainstorming`.

Explicitly confirm these directories were surveyed clean (not excluded):
- `skills/` (all skill files)
- `agents/` (all agent files)
- `advisors/` (all advisor prompt files)
- `hooks/` (hook scripts and config)
- `e2e/` (eval scenarios)

If any live references are found, fix them before proceeding.

**Step 2: Verify file structure**

Confirm the following using Glob:
- `skills/brainstorming/SKILL.md` exists
- `skills/brainstorming/modes/software.md` exists
- `skills/brainstorming/modes/business.md` exists
- `skills/brainstorming/design-critique-checklist.md` exists
- `skills/brainstorming/business-critique-checklist.md` exists
- `skills/brainstorming/critic-registry.md` exists
- `skills/business-brainstorming/` does NOT exist

**Step 3: Verify version consistency**

Read `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
Expected: Both show `"version": "0.13.0"`

**Step 4: Verify the README changelog**

Read `README.md` and confirm the 0.13.0 changelog entry exists and appears before the 0.6.0 entry.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Task ordering follows design doc's operation sequence | Sequential: move checklist → create modes → rewrite router → delete old dir → update cross-refs | Parallel cross-ref updates (rejected: ordering matters for `git rm`) |
| 2 | Copy-then-delete for checklist move instead of `git mv` | `cp` in Task 1, `git rm -r` in Task 5 | `git mv` in Task 1 (rejected: can't `git mv` a file out of a directory we later `git rm -r`) |
| 3 | Cross-reference updates as separate tasks per file | One task per target file (Tasks 6-9) | Single mega-task (rejected: too large, violates 15-min task sizing) |
| 4 | Delete `Skill(aligned:business-brainstorming)` permission line rather than rename | Remove from kickstart and README permission arrays | Rename to comment (rejected: dead entries in JSON arrays are noise) |
| 5 | Eval scenario adds new scenario rather than editing existing | Append Scenario 8 documenting the unification | Edit existing scenario comments (rejected: no existing `business-brainstorming` string to replace) |

### Appendix: Decision Details

#### Decision 1: Task ordering follows design doc's operation sequence
**Chose:** Sequential ordering matching the design doc's "Operation Sequence (order matters)" section.
**Why:** The design doc explicitly calls out that ordering matters. Moving the checklist first ensures it exists at the destination before the old directory is deleted. Creating mode files before rewriting the router means the router can be tested immediately. Deleting the old directory last avoids dangling references.
**Alternatives rejected:**
- Parallel cross-ref updates: Could work in theory since they touch different files, but the `git rm -r` in Task 5 must happen after Task 1's copy. Keeping everything sequential is simpler and matches the design doc's intent.

#### Decision 2: Copy-then-delete for checklist move
**Chose:** `cp` the checklist in Task 1, then `git rm -r` the entire business-brainstorming directory in Task 5.
**Why:** If we used `git mv` in Task 1 to move the checklist out, Task 5's `git rm -r skills/business-brainstorming/` would fail or produce unexpected results since one file is already gone. Copying first, then bulk-deleting the directory, is cleaner.
**Alternatives rejected:**
- `git mv` the checklist first: Creates an awkward state where the directory has one fewer file, complicating the later bulk delete.

#### Decision 3: Cross-reference updates as separate tasks per file
**Chose:** Tasks 6, 7, 8, 9 each update one target file.
**Why:** Each file has a different number of changes and different verification criteria. Keeping them separate means each task is a clean commit with a clear scope. This also matches the plan skill's sizing guidance of ~15 minutes per task.
**Alternatives rejected:**
- Single task updating all cross-references: Would touch 4 files across different directories, making the commit message vague and the verification complex.

#### Decision 4: Delete permission line rather than rename
**Chose:** Remove `Skill(aligned:business-brainstorming)` from the permissions arrays entirely.
**Why:** `Skill(aligned:brainstorming)` already exists in both the kickstart permissions list and the README example. After unification, the brainstorming permission covers both modes. Leaving a dead permission entry is noise.
**Alternatives rejected:**
- Rename to `Skill(aligned:brainstorming)`: Would create a duplicate since that entry already exists.

#### Decision 5: Eval scenario adds new scenario rather than editing existing
**Chose:** Append a new Scenario 8 to `kickstart-expansion.test.ts` documenting the v0.13.0 unification behavioral change.
**Why:** The existing eval file has no direct references to `business-brainstorming` — Scenario 4 describes business workflows generically. Trying to "update" a non-existent string would produce a silent no-op. Adding a new scenario that explicitly documents the change (business/personal/general templates now reference `/aligned:brainstorming`) is honest and verifiable.
**Alternatives rejected:**
- Edit existing scenario comments: No `business-brainstorming` string exists to replace — the edit would be a phantom no-op.
- New eval test file for brainstorming routing: The design doc's testing section describes routing scenarios, but these are integration tests for the brainstorming skill itself, not kickstart. They should be created as a separate task after the unification ships.
