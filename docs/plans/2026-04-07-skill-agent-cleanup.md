# Skill & Agent Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Remove orphaned/unused skills and agents, merge duplicates, rename systematic-debugging to root-cause-analysis, wire code-reviewer back into finishing workflow, and update all cross-references.

**Source Design Doc:** N/A (design emerged from conversation analysis)

**Architecture:** Delete 5 skill directories, rename 1 (systematic-debugging → root-cause-analysis), and delete 2 agent files. Merge design-principles into create-design-principles. Merge business-diagnosis into a renamed root-cause-analysis skill. Add code-reviewer step to finishing-a-development-branch. Update ~15 files with cross-reference changes.

**Tech Stack:** Markdown, SVG, JSON (plugin config)

---

### ✅ Task 1: Delete removed skill directories

**Files:**
- Delete: `skills/claude-profile/` (entire directory)
- Delete: `skills/business-executing/` (entire directory)
- Delete: `skills/business-write-plan/` (entire directory — includes a business-specific `plan-critique-checklist.md`; the main checklist at `skills/writing-plans/plan-critique-checklist.md` is unaffected)

**Step 1: Delete the directories**

```bash
rm -rf skills/claude-profile
rm -rf skills/business-executing
rm -rf skills/business-write-plan
```

**Step 2: Verify deletions**

Run: `ls skills/claude-profile skills/business-executing skills/business-write-plan 2>&1`
Expected: "No such file or directory" for all three.

**Step 3: Commit**

```bash
git add -u skills/claude-profile skills/business-executing skills/business-write-plan
git commit -m "remove: claude-profile, business-executing, business-write-plan skills"
```

---

### Task 2: Delete removed agent files

**Files:**
- Delete: `agents/worktree-setup.md`
- Delete: `agents/steve-jobs.md`

**Step 1: Delete the files**

```bash
rm agents/worktree-setup.md
rm agents/steve-jobs.md
```

**Step 2: Verify the advisor file still exists**

Read `advisors/prompts/steve-jobs.md` — must exist (this is the canonical Steve Jobs persona, NOT being deleted).

**Step 3: Commit**

> **Ordering note:** Tasks 2 and 3 must execute without interruption. Task 2 breaks `mockup-generator` (deletes the agent file it references). Task 3 patches the reference. Do not stop between these tasks.

```bash
git add -u agents/worktree-setup.md agents/steve-jobs.md
git commit -m "remove: worktree-setup and steve-jobs agents (advisor persona retained)"
```

---

### Task 3: Update mockup-generator agent to reference advisor instead of agent

**Files:**
- Modify: `agents/mockup-generator.md` (the `agents/steve-jobs.md` reference)

**Step 1: Read mockup-generator.md and find the steve-jobs agent reference**

Search for `agents/steve-jobs.md` in the file. It appears around line 164:
```
load `agents/steve-jobs.md` and adopt the Steve Jobs persona
```

**Step 2: Replace the reference**

Change `agents/steve-jobs.md` to `advisors/prompts/steve-jobs.md` wherever it appears in this file.

**Step 3: Commit**

```bash
git add agents/mockup-generator.md
git commit -m "fix: update mockup-generator to reference steve-jobs advisor instead of deleted agent"
```

---

### Task 4: Merge design-principles discovery into create-design-principles

**Files:**
- Modify: `skills/create-design-principles/SKILL.md` (add discovery questions)
- Delete: `skills/design-principles/` (entire directory, after merge)

**Step 1: Read both files**

Read `skills/design-principles/SKILL.md` — extract the Phase 1 discovery questions (the 5 numbered questions in the "Step 2: Ask discovery questions" section):
1. **The feeling** — "When someone opens this app, what do they feel?"
2. **The anti-feeling** — "What's the opposite? What should this never feel like?"
3. **The reference** — "Show me something that gets it right."
4. **Color direction** — "Warm or cool? Bold or quiet?"
5. **Density** — "Is this a journal or a cockpit?"

Read `skills/create-design-principles/SKILL.md` — this already has the Steve Jobs persona (find `## Persona: Steve Jobs (REQUIRED)`) and "Design Direction" section (find `## Design Direction (REQUIRED)`). The discovery questions should be inserted between the persona section and the Design Direction section as a required interactive step before the prescriptive guidance.

**Step 2: Add discovery phase to create-design-principles**

In `skills/create-design-principles/SKILL.md`, after the Steve Jobs persona section (after the closing of the persona instructions, before the `---` separator that precedes the "Design Direction" section), insert a new section:

```markdown
## Phase 1: Discovery (Interactive)

Before prescribing a design direction, discover the project's intent through these questions. Ask one at a time in Steve's voice. Skip questions already answered by linked context (brand guidelines, wireframes, screenshots).

1. **The feeling** — "When someone opens this app, what do they feel? Not what they see — what they *feel*. Are we talking warmth? Power? Calm? If you can't describe the feeling in one word, you haven't thought about it hard enough."

2. **The anti-feeling** — "What's the opposite? What should this *never* feel like? Corporate? Cluttered? Playful? The anti-pattern tells me more than the aspiration."

3. **The reference** — "Show me something that gets it right. An app, a website, a magazine — something where you said 'that's what I want.' And tell me what specifically nails it."

4. **Color direction** — "Warm or cool? Bold or quiet? One accent color — what emotion does it carry?"

5. **Density** — "Is this a journal or a cockpit? Generous breathing room, or every pixel earns its place?"

Push back on vague answers. "That's not a design direction, that's a mood board. Pick one."

Use the answers to guide the Design Direction choices below. If the user's answers clearly point to a direction (e.g., "warmth and approachability" → Warmth & Approachability personality), commit to it rather than presenting all options.

---
```

Also update the description frontmatter to reflect the merged capability:
```yaml
description: Interactive design system discovery and enforcement with Steve Jobs persona. Explores the project's design direction through conversation, then generates design-principles.md with tokens, patterns, and anti-patterns. Use when building dashboards, admin interfaces, or any UI that needs precision.
```

**Step 3: Delete design-principles directory**

```bash
rm -rf skills/design-principles
```

**Step 4: Verify**

Read `skills/create-design-principles/SKILL.md` — confirm the discovery questions are present and the file is well-formed.
Run: `ls skills/design-principles 2>&1`
Expected: "No such file or directory"

**Step 5: Commit**

```bash
git add skills/create-design-principles/SKILL.md
git add -u skills/design-principles
git commit -m "merge: fold design-principles discovery into create-design-principles, delete original"
```

---

### Task 5: Rename systematic-debugging directory to root-cause-analysis

**Files:**
- Rename: `skills/systematic-debugging/` → `skills/root-cause-analysis/`

**Step 1: Rename the directory**

```bash
git mv skills/systematic-debugging skills/root-cause-analysis
```

**Step 2: Verify**

Run: `ls skills/root-cause-analysis/`
Expected: SKILL.md, root-cause-tracing.md, defense-in-depth.md, condition-based-waiting.md, fix-the-right-layer.md

**Step 3: Commit**

```bash
git commit -m "rename: systematic-debugging → root-cause-analysis"
```

---

### Task 6: Rewrite root-cause-analysis SKILL.md as domain-neutral unified skill

> **Prerequisite:** Task 5 must be committed. The file at `skills/root-cause-analysis/SKILL.md` does not exist until Task 5's `git mv` completes.

**Files:**
- Modify: `skills/root-cause-analysis/SKILL.md`

This is the most substantial edit. The current file is software-focused. Merge in business-diagnosis content to create a single domain-neutral skill.

**Step 1: Read both source files**

Read `skills/root-cause-analysis/SKILL.md` (the renamed systematic-debugging).
Read `skills/business-diagnosis/SKILL.md`.

**Step 2: Rewrite SKILL.md**

Replace the content of `skills/root-cause-analysis/SKILL.md` with a unified version. Key changes:

1. **Frontmatter:** Change `name: systematic-debugging` to `name: root-cause-analysis`. Update description to be domain-neutral: `"Use when encountering any bug, test failure, unexpected behavior, or business problem that isn't resolving. Supports low (default) and high severity with multi-agent investigation."`

2. **Title and overview:** Change "Systematic Debugging" → "Root Cause Analysis". Change "debugging" → "diagnosis" in domain-neutral language. "ALWAYS find root cause before attempting fixes/solutions."

3. **When to Use:** Combine both lists. Software: test failures, bugs, build failures, integration issues. Business: deliverable not landing, strategy not producing results, process breakdown, client friction.

4. **Phase 0 high-severity agents:** Include all 6 agents. Keep Forward Tracer (software) and add Stakeholder Mapper (business): "Map the human system around this problem. Who benefits from the status quo? Who has veto power?" Add note: "Software problems: use Forward Tracer. Business problems: use Stakeholder Mapper. Ambiguous: use both."

5. **Phase 1:** Add "Define the Gap" substep from business-diagnosis (useful for both domains): "Is this a gap in correctness, performance, reliability, direction, scope, or understanding?" Keep the multi-component instrumentation section but mark it "(software)" and add the business layered analysis "(business)": "Strategy → Messaging → Deliverables → Execution."

6. **Phases 2-4:** Use domain-neutral language. "working examples" instead of "working code" where appropriate. Keep "Create Failing Test Case" in Phase 4 with note "(software — use test-driven-development skill)" and add "(business — define measurable success criteria)" alternative.

7. **Invocation:** Change to `/aligned:root-cause-analysis` and `/aligned:root-cause-analysis high`.

8. **Supporting Techniques:** Keep the note about software-specific technique files. Add: "Business diagnosis uses the same phases but does not require these technique files."

9. **Kanban entry:** Change "Discovered during" value to `root-cause-analysis`.

10. **Related skills:** Keep TDD and verification-before-completion references.

**Step 3: Verify the rewritten file**

Read back `skills/root-cause-analysis/SKILL.md` and confirm it contains both software and business guidance in a single domain-neutral document.

**Step 4: Commit**

```bash
git add skills/root-cause-analysis/SKILL.md
git commit -m "feat: merge business-diagnosis into root-cause-analysis as domain-neutral skill"
```

---

### Task 7: Delete business-diagnosis skill directory

**Files:**
- Delete: `skills/business-diagnosis/` (entire directory)

**Step 1: Delete**

```bash
rm -rf skills/business-diagnosis
```

**Step 2: Commit**

```bash
git add -u skills/business-diagnosis
git commit -m "remove: business-diagnosis (merged into root-cause-analysis)"
```

---

### Task 8: Add TDD skill reference to executing-plans

**Files:**
- Modify: `skills/executing-plans/SKILL.md` (add explicit TDD reference)

**Step 1: Read the file and find the right insertion point**

Read the file. Find the "### Step 2: Execute Build Tasks" section. After the per-task instruction list (the numbered 1-4 steps ending with "Mark as completed"), add a TDD discipline note.

**Step 2: Add TDD reference**

After the Step 2 task execution instructions (the "Mark as completed" line), add:

```markdown
**TDD discipline:** Every task follows RED-GREEN-REFACTOR. Write the failing test first, verify it fails, write minimal implementation, verify it passes. Reference: `test-driven-development` skill. If a task skips TDD steps, STOP and follow the TDD process before continuing.
```

Also add to the "Related skills" or imports area near the top. If no such section exists, add before the "## When to Stop" section:

```markdown
**Required sub-skills:**
- **test-driven-development** — RED-GREEN-REFACTOR cycle for every task
- **verification-before-completion** — verify claims with fresh evidence before marking tasks complete
```

**Step 3: Commit**

```bash
git add skills/executing-plans/SKILL.md
git commit -m "feat: add explicit TDD and verification skill references to executing-plans"
```

---

### Task 9: Wire code-reviewer into finishing-a-development-branch

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

This is the second most substantial edit. Insert a new Step 1d (Code Review) before the current Step 1d (Code Simplification Scan), then renumber all subsequent Step 1x references.

**Step 1: Read the current step numbering**

Current order:
- Step 0: Deployment Platform Audit
- Step 1: Verify Tests
- Step 1a: Verify Build
- Step 1b: LLM Eval
- Step 1c: Architecture Doc Update
- Step 1d: Code Simplification Scan ← insert BEFORE this
- Step 1e: Mockup Fidelity Check
- Step 1f: Fix Mockup Deviations
- Step 2+: unchanged

New order after insertion:
- Step 1d: **Code Review (NEW)**
- Step 1e: Code Simplification Scan (was 1d)
- Step 1f: Mockup Fidelity Check (was 1e)
- Step 1g: Fix Mockup Deviations (was 1f)

**Step 2: Insert new Step 1d before current Step 1d**

Insert before `### Step 1d: Code Simplification Scan`:

```markdown
### Step 1d: Code Review

**After all verification passes, dispatch a comprehensive code review against the plan.**

This step catches plan drift, missing error paths, and quality issues that tests and builds don't cover. The reviewer is a fresh sub-agent that hasn't seen the implementation conversation — it provides independent evaluation.

**Spawn the `aligned:code-reviewer` agent** via the Task tool:

```
subagent_type: "aligned:code-reviewer"
prompt: "Review the branch changes for this feature against the implementation plan.

  Branch: <branch-name>
  Base branch: <base-branch>
  Working directory: <worktree-path>
  Plan file: <plan-file-path>

  Run `git diff <base-branch>...HEAD` to see all changes on this branch.
  Read the plan file for context on what was intended.
  Follow all 7 review sections in your agent prompt.
  Pay special attention to Section 5 (Mock Error Path Coverage).

  Write your report as structured output to stdout.
  Use Read for files, Grep/Glob for searching. Do not use Bash for searching."
```

**If CRITICAL issues found:**
```
Code review found CRITICAL issues. Must fix before proceeding:

[Show CRITICAL findings]

Cannot proceed until critical issues are resolved.
```
Stop. Fix the issues in the worktree, commit, re-run tests (Step 1) and build (Step 1a), then re-dispatch the code reviewer.

**If only Important or Suggestions:** Show findings as context, continue to Step 1e. File Important findings to Kanban board using the standard entry format.

**If clean review:** Report clean, continue to Step 1e.
```

**Step 3: Renumber Step 1d → 1e**

Find `### Step 1d: Code Simplification Scan` and change to `### Step 1e: Code Simplification Scan`.

Update all internal references within this section: "Continue to Step 1e." → "Continue to Step 1f." (at the end of the simplification scan section).

**Step 4: Renumber Step 1e → 1f**

Find `### Step 1e: Mockup Fidelity Check` and change to `### Step 1f: Mockup Fidelity Check`.

Update all references: "Continue to Step 1f." → "Continue to Step 1g." and "Step 1e found" → "Step 1f found".

**Step 5: Renumber Step 1f → 1g**

Find `### Step 1f: Fix Mockup Deviations` and change to `### Step 1g: Fix Mockup Deviations`.

Update references within: "Step 1f-i" → "Step 1g-i", "Step 1f-ii" → "Step 1g-ii", "Step 1f-iii" → "Step 1g-iii". Also update "Step 1e" references within this section to "Step 1f".

**Step 6: Update the summary table**

The file has a summary table at the bottom listing all steps. Find it and update the numbering:
```
| 1d. Code review | Spawn code-reviewer agent, fix CRITICAL issues | Yes (CRITICAL) |
| 1e. Simplification scan | Spawn code-simplifier agent, file Kanban entries | No |
| 1f. Mockup fidelity | Compare implementation against mockups | No |
| 1g. Fix deviations | User-directed mockup fixes with root-cause diagnosis | No |
```

**Step 7: Add verification-before-completion reference**

Add to the skill's core principle or overview section a reference:
```markdown
**Required sub-skill:** verification-before-completion — every success claim requires fresh evidence in the current message.
```

**Step 8: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "feat: wire code-reviewer into finishing workflow as Step 1d, add verification reference"
```

---

### Task 10: Update brainstorming/modes/business.md

**Files:**
- Modify: `skills/brainstorming/modes/business.md`

**Step 1: Read the file and find the business-write-plan reference**

Around line 208:
```
> Use `/aligned:business-write-plan` to write an execution plan...
```

**Step 2: Replace with writing-plans reference**

Change the execution handoff to use the standard writing-plans skill instead of the removed business-write-plan:

```
> Use `/aligned:writing-plans` to write an execution plan based on the design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`.
```

**Step 3: Commit**

```bash
git add skills/brainstorming/modes/business.md
git commit -m "fix: update brainstorming business mode to use writing-plans instead of removed business-write-plan"
```

---

### Task 11: Update kickstart/SKILL.md

**Files:**
- Modify: `skills/kickstart/SKILL.md`

**Step 0: Read the file first**

Read `skills/kickstart/SKILL.md` in full to confirm current line positions before editing. Line numbers below are approximate — use content anchors to locate the actual positions.

**Step 1: Update the permissions list**

Find the `permissions.allow` array (inside the Phase 5 settings.json block). Remove these entries:
- `"Skill(aligned:claude-profile)"`
- `"Skill(aligned:business-brainstorming)"` (stale — no such skill exists)
- `"Skill(aligned:business-diagnosis)"`
- `"Skill(aligned:business-executing)"`
- `"Skill(aligned:business-write-plan)"`
- `"Skill(aligned:design-principles)"`
- `"Skill(aligned:systematic-debugging)"`

Replace `"Skill(aligned:systematic-debugging)"` with:
- `"Skill(aligned:root-cause-analysis)"`

(Net effect: remove 7 entries, add 1.)

**Step 2: Update documentation references**

Find each reference by content anchor (not line number — positions may have shifted):

- Find `/aligned:systematic-debugging` in the Software Workflows list → change to `/aligned:root-cause-analysis` with description "for root cause investigation"
- Find `/aligned:design-principles` in the Software Workflows list → change to `/aligned:create-design-principles` with description "to define design direction"
- Find the Business Workflows list containing `/aligned:business-write-plan`, `/aligned:business-executing`, `/aligned:business-diagnosis` → remove all three. Add `/aligned:root-cause-analysis` — "when something isn't working"
- Find the Software scaffold output message containing `/aligned:design-principles` → change to `/aligned:create-design-principles`
- Find the design-principles.md placeholder template containing `/aligned:design-principles` → change to `/aligned:create-design-principles`

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "fix: update kickstart skill references for cleanup refactor"
```

---

### Task 12: Update remaining cross-references

> **Prerequisite:** Complete Task 8 first — both Task 8 and this task modify `skills/executing-plans/SKILL.md`.

**Files:**
- Modify: `skills/executing-plans/SKILL.md` (systematic-debugging reference)
- Modify: `skills/eval-failure-triage/SKILL.md` (systematic-debugging references)
- Modify: `agents/error-diagnosis.md` (systematic-debugging reference)
- Modify: `skills/create-new-skill/SKILL.md` (systematic-debugging reference)

**Step 0: Read each file to confirm reference locations before editing**

Read all 4 files. Use Grep to find `systematic-debugging` in each. Confirm the exact lines before making edits.

**Step 1: Update executing-plans**

Find the `/aligned:systematic-debugging` reference in the Kanban/bug discovery section (near "pick up in a fresh session") → change to `/aligned:root-cause-analysis`

**Step 2: Update eval-failure-triage**

Find `systematic-debugging` in the "Complements" line near the top → change to `root-cause-analysis`
Find `systematic-debugging` in the "Related skills" section near the bottom → change to `root-cause-analysis`

**Step 3: Update error-diagnosis agent**

Find `/aligned:systematic-debugging` in the "Deep debugging" recommendation → change to `/aligned:root-cause-analysis`

**Step 4: Update create-new-skill**

Find `systematic-debugging` in the REQUIRED BACKGROUND example → change to `root-cause-analysis`

**Step 5: Commit**

```bash
git add skills/executing-plans/SKILL.md skills/eval-failure-triage/SKILL.md agents/error-diagnosis.md skills/create-new-skill/SKILL.md
git commit -m "fix: update systematic-debugging → root-cause-analysis cross-references"
```

---

### Task 13: Update README.md

**Files:**
- Modify: `README.md`

**Step 1: Read the current README**

Find the skill reference table and agent reference table.

**Step 2: Update skill reference table**

Remove rows for:
- claude-profile
- business-executing
- business-write-plan
- business-diagnosis
- design-principles

Rename row:
- systematic-debugging → root-cause-analysis, update description to "Root cause investigation for software bugs and business problems"

**Step 3: Update agent reference table**

Remove rows for:
- worktree-setup
- steve-jobs

**Step 4: Update any other README references**

Search for any other mentions of the removed/renamed items in the README and update them.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: update README tables for skill/agent cleanup refactor"
```

---

### Task 14: Bump plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Read current versions**

Read both files and find the current version string.

**Step 2: Bump minor version**

Increment the minor version (e.g., 0.13.0 → 0.14.0) in both files. They must match.

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version to 0.14.0 for skill/agent cleanup"
```

---

### Task 15: Verify all cross-references resolve

**Files:** All modified files from previous tasks

**Step 1: Grep for removed skill names in remaining files**

Search the entire repo (excluding `docs/plans/`, `docs/diagrams/`, `.git/`) for references to removed/renamed items:

```
Grep for: /aligned:claude-profile
Grep for: /aligned:design-principles  (should only appear in create-design-principles context)
Grep for: /aligned:business-executing
Grep for: /aligned:business-write-plan
Grep for: /aligned:business-diagnosis
Grep for: /aligned:systematic-debugging
Grep for: agents/steve-jobs.md
Grep for: agents/worktree-setup.md
```

Expected: Zero matches for each (except historical references in completed plans or docs/plans/).

**Step 2: Verify renamed skill exists**

```
ls skills/root-cause-analysis/SKILL.md
```
Expected: File exists.

**Step 3: Verify deleted items are gone**

```
ls skills/claude-profile skills/business-executing skills/business-write-plan skills/business-diagnosis skills/design-principles skills/systematic-debugging agents/worktree-setup.md agents/steve-jobs.md 2>&1
```
Expected: "No such file or directory" for all.

**Step 4: Verify advisor file survives**

Read `advisors/prompts/steve-jobs.md` — must still exist.

**Step 5: If stale references found, fix them and commit**

```bash
git add -u
git commit -m "fix: resolve remaining stale cross-references from cleanup"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Where to insert code-reviewer in finishing | Step 1d (after arch docs, before simplification) | After build (1a), after LLM eval (1b), after all Step 1x |
| 2 | How to merge business-diagnosis | Single doc with inline domain callouts | Brainstorming-style mode files, separate "business" section |
| 3 | Task ordering for deletions | Delete first, then update cross-refs | Update cross-refs first, then delete |
| 4 | SVG diagram update | Excluded from plan | Include regeneration task |

### Appendix: Decision Details

#### Decision 1: Code reviewer placement at Step 1d
**Chose:** Insert between architecture doc update (1c) and code simplification scan (1d→1e).
**Why:** Code review should happen after all automated verification (tests, build, eval) passes but before cosmetic/optional scans (simplification, mockup fidelity). If code review finds CRITICAL issues, there's no point running the simplification scanner on code that needs to change. Placing it here means the reviewer sees verified-clean code but can catch architectural and quality issues before the optional scans run.
**Alternatives rejected:**
- After build (1a): Too early — LLM eval and architecture doc updates would run on potentially flawed code.
- After all Step 1x: Too late — simplification scan and mockup checks would run on code that might need CRITICAL fixes, wasting time.

#### Decision 2: Single doc with inline callouts for root-cause-analysis
**Chose:** One SKILL.md with domain-neutral language and small inline "(software)" / "(business)" callouts where techniques differ.
**Why:** The subagent comparison found the two skills share 90%+ of their structure, phases, and anti-patterns. The differences amount to: vocabulary, one Phase 0 agent swap, one extra substep, and software-specific technique files. This is well below the threshold where mode files add value. Two 280-line mode files that are 90% identical would be a maintenance nightmare.
**Alternatives rejected:**
- Brainstorming-style mode files: Overkill. Brainstorming uses modes because software and business processes are structurally different. Root cause analysis uses the same algorithm for both.
- Separate "business" section: Would create awkward duplication within a single file. Inline callouts are cleaner.

#### Decision 3: Delete first, update cross-refs after
**Chose:** Delete skill/agent files in early tasks, update cross-references in later tasks.
**Why:** Cross-reference updates are easier to verify when the deleted files are already gone — grep will catch any missed references. If we updated cross-refs first, we'd need to remember which files still exist to distinguish stale refs from valid ones.
**Alternatives rejected:**
- Update first: Makes verification harder since the "old" files still exist when grepping.

#### Decision 4: Exclude SVG diagram regeneration
**Chose:** The current SVG diagram at `docs/diagrams/skill-agent-mind-map.svg` will become stale after this refactor but is NOT included as a task. It should be regenerated in a follow-up session using `/aligned:create-svg-diagram` with the updated skill/agent inventory.
**Why:** The diagram was just created in this conversation as an analysis tool. Regenerating it as part of this plan adds complexity to an already large refactor. The diagram is not referenced by any skill or agent — it's a standalone documentation artifact.
