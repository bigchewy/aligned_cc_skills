# Visualization Agent Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the three dead pre-visualization-runner agents, delete the fourth (mockup-generator) and swap its one live caller from a hand-rolled static-HTML dispatch to a direct `design` skill invocation, and reflect both changes in README.

**Architecture:** No runtime code changes — this plugin ships markdown skill/agent files, not application code. Every task is a set of file deletions and targeted markdown edits, verified by grep (no reference survives) and by reading the edited file back.

**Tech Stack:** Plain markdown files consumed by Claude Code's agent/skill discovery. No build step, no test runner for this content.

## Global Constraints

- Design source of truth: `docs/plans/2026-08-31-visualization-agent-cleanup-design.md` (committed as `fcb20bf`). Every task here traces to a decision in that file.
- This plugin has no automated tests over agent/skill markdown. "Testing" in every task below means: a grep that proves no live reference to the deleted file remains, and a direct read of any edited file to confirm the edit landed as intended.
- Never touch `skills/_shared/visualization-runner.md`, `skills/brainstorming/references/visualization-protocol.md`, or anything else in the current-generation visualization pipeline — out of scope per the design doc.
- Both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` must carry the same version string (project convention, `CLAUDE.md` "Version" section).

---

### Task 1: Delete the three orphaned diagram agents

**Files:**
- Delete: `agents/session-document-generator.md`
- Delete: `agents/flowchart-generator.md`
- Delete: `agents/architecture-diagram-generator.md`
- Modify: `README.md:106` (delete the `architecture-diagram-generator` row)
- Modify: `README.md:109` (delete the `flowchart-generator` row)
- Modify: `README.md:111` (delete the `session-document-generator` row)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: nothing later tasks depend on — Task 2 touches a disjoint set of files (`agents/mockup-generator.md`, `skills/brainstorming/modes/authoring.md`, and the `mockup-generator`/`architecture-diagram-generator` README rows are already gone by the time Task 2 runs `README.md:106-111` shifts up by three rows, but Task 2 edits `README.md`'s `mockup-generator` row by content match, not line number, so this ordering doesn't matter).

- [ ] **Step 1: Confirm no live caller exists for any of the three (repeat the audit from brainstorming, since this is the fact the whole task rests on)**

Run each of these three commands separately (do not chain with `&&` — each must show its own empty output):

```bash
grep -rln "session-document-generator" skills e2e 2>/dev/null
```
```bash
grep -rln "flowchart-generator" skills e2e 2>/dev/null
```
```bash
grep -rln "architecture-diagram-generator" skills e2e 2>/dev/null
```

Expected: all three print nothing. If any prints a file path, STOP — that means something now references the agent that didn't at design time. Do not delete that agent; report the new reference instead.

- [ ] **Step 2: Delete the three agent files**

```bash
rm agents/session-document-generator.md
rm agents/flowchart-generator.md
rm agents/architecture-diagram-generator.md
```

- [ ] **Step 3: Remove their rows from the README agent table**

Read `README.md` lines 102-113 first (the table shifts as you delete rows, so re-read after each removal rather than trusting stale line numbers). Starting content:

```
### Agents

| Agent | Description |
|-------|-------------|
| architecture-diagram-generator | Architecture diagrams with SVG and architecture.md updates |
| artifact-verifier | 98% accuracy gate for document fact-checking |
| critique-interactive-html-generator | Interactive HTML for accept/reject decisions on brainstorming critique findings, with copy-as-prompt round-trip |
| flowchart-generator | Mermaid.js flowcharts for data flows, processes, and decision trees |
| mockup-generator | Self-contained HTML mockups for design-phase visualization |
| session-document-generator | Orchestrates diagram agents to produce consolidated tabbed HTML documents |
| project-scanner | Fast codebase scan for brainstorming context (languages, structure, dependencies) |
```

Delete exactly these three rows (leave the `mockup-generator` row alone — Task 2 removes it):

```
| architecture-diagram-generator | Architecture diagrams with SVG and architecture.md updates |
```
```
| flowchart-generator | Mermaid.js flowcharts for data flows, processes, and decision trees |
```
```
| session-document-generator | Orchestrates diagram agents to produce consolidated tabbed HTML documents |
```

Resulting table body (order unchanged, gaps closed):

```
| Agent | Description |
|-------|-------------|
| artifact-verifier | 98% accuracy gate for document fact-checking |
| critique-interactive-html-generator | Interactive HTML for accept/reject decisions on brainstorming critique findings, with copy-as-prompt round-trip |
| mockup-generator | Self-contained HTML mockups for design-phase visualization |
| project-scanner | Fast codebase scan for brainstorming context (languages, structure, dependencies) |
```

- [ ] **Step 4: Verify**

```bash
ls agents/
```
Expected: `session-document-generator.md`, `flowchart-generator.md`, `architecture-diagram-generator.md` are gone; `mockup-generator.md`, `artifact-verifier.md`, `critique-interactive-html-generator.md`, `project-scanner.md` (and any others) remain.

```bash
grep -n "architecture-diagram-generator\|flowchart-generator\|session-document-generator" README.md
```
Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add -A -- agents/session-document-generator.md agents/flowchart-generator.md agents/architecture-diagram-generator.md README.md
git commit -m "chore: delete three orphaned pre-visualization-runner agents

session-document-generator, flowchart-generator, and architecture-diagram-generator have no live caller anywhere in skills/ or e2e/ — they predate the visualization-runner extraction and were never wired to it."
```

---

### Task 2: Delete mockup-generator and rewire its one live caller to the `design` skill

**Files:**
- Delete: `agents/mockup-generator.md`
- Modify: `README.md` (delete the `mockup-generator` row)
- Modify: `skills/brainstorming/modes/authoring.md:98-102`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Confirm the only live caller is `authoring.md`, and confirm the fragment-mode caller is already gone**

```bash
grep -rln "mockup-generator" skills e2e 2>/dev/null
```

Expected: exactly one file — `skills/brainstorming/modes/authoring.md`. If more than one file appears, or a different file appears, STOP and report before continuing (the plan assumes this single caller).

`mockup-generator.md`'s fragment mode existed only to serve `session-document-generator`, which Task 1 already deleted — so no separate check is needed for the fragment-mode path; it has no caller left by construction.

- [ ] **Step 2: Delete the agent file**

```bash
rm agents/mockup-generator.md
```

- [ ] **Step 3: Remove its README row**

Read `README.md`'s `### Agents` table. Delete this row:

```
| mockup-generator | Self-contained HTML mockups for design-phase visualization |
```

Resulting table body:

```
| Agent | Description |
|-------|-------------|
| artifact-verifier | 98% accuracy gate for document fact-checking |
| critique-interactive-html-generator | Interactive HTML for accept/reject decisions on brainstorming critique findings, with copy-as-prompt round-trip |
| project-scanner | Fast codebase scan for brainstorming context (languages, structure, dependencies) |
```

- [ ] **Step 4: Rewire `authoring.md`'s dispatch (this is the core change)**

Read `skills/brainstorming/modes/authoring.md`. Find this exact block (currently lines 98-102):

```
3. Dispatch the mockup-generator agent with the advisor-refined options to create a comparison mockup with all options as switchable tabs. Use this dispatch template — replace placeholders with actual values. Uses `subagent_type=general-purpose`.

   "Read `agents/mockup-generator.md` for your full workflow. Generate a comparison mockup showing {number} approach options for: {brief description of what's being compared}. Project root: `{project-root}`. Brainstorming session topic: `{topic}`. Create a single HTML file at `docs/mockups/{session-name}/approach-comparison.html` with tabbed navigation to switch between options. Each tab should be labeled with the approach name and include a short description of the trade-offs. Open the file in the browser after generating."

4. After the user has reviewed the HTML mockup in the browser, proceed with the approach selection question.
```

Replace it with:

```
3. Invoke the `design` skill directly (Skill tool, `skill: "design"`) with the advisor-refined options, asking for one artboard per option on a single canvas. Use this args template — replace placeholders with actual values:

   "Compare {number} approach options for: {brief description of what's being compared}. One artboard per option, laid out on a single canvas so they can be viewed side by side. Label each artboard with the approach name and a short description of the trade-offs. Brainstorming session topic: {topic}."

4. After the user has reviewed the design in the published Artifact, proceed with the approach selection question.
```

- [ ] **Step 5: Verify**

```bash
grep -n "mockup-generator" skills/brainstorming/modes/authoring.md README.md
```
Expected: no output.

```bash
grep -n "Invoke the \`design\` skill directly" skills/brainstorming/modes/authoring.md
```
Expected: one match.

Read the edited section of `authoring.md` (around the former lines 91-103) back in full to confirm steps 1-2 (advisor consult) and the renumbered steps 3-4 read as a coherent sequence — no dangling reference to `agents/mockup-generator.md`, `docs/mockups/{session-name}/approach-comparison.html`, or "HTML mockup in the browser" anywhere in that section.

- [ ] **Step 6: Commit**

```bash
git add -A -- agents/mockup-generator.md README.md skills/brainstorming/modes/authoring.md
git commit -m "refactor: swap mockup-generator for the design skill in authoring mode

mockup-generator's only live caller (authoring.md step 3) built a hand-rolled,
CDN-loaded, light-mode-only HTML comparison file opened via \`open\`. Replace it
with a direct design-skill invocation, which publishes N options as artboards
on one canvas through the Artifact tool — theme-aware, native Mermaid,
shareable. mockup-generator.md itself is now dead (its fragment-mode caller,
session-document-generator, was deleted in the prior commit) and is deleted."
```

---

### Task 3: Bump the plugin version

**Superseded during execution:** this repo's pre-commit hook (`scripts/hooks/pre-commit`) auto-bumps both manifest files whenever a commit touches shipped-content paths. Task 2's commit modified `skills/brainstorming/modes/authoring.md`, which triggered the hook and produced exactly this task's target state (0.33.6 → 0.33.7) as a side effect. This task's steps below were not executed separately — the target state they describe was already reached. See commit `893dbc9` and the SDD ledger for the full story (an incorrect revert-and-restore happened along the way before this was understood).

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: nothing (can run after Task 1 and Task 2 land, or standalone — but run it last so the version bump reflects the finished change).
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Bump both files**

In `.claude-plugin/plugin.json`, change:
```
  "version": "0.33.6",
```
to:
```
  "version": "0.33.7",
```

In `.claude-plugin/marketplace.json`, change:
```
      "version": "0.33.6"
```
to:
```
      "version": "0.33.7"
```

- [ ] **Step 2: Verify both match**

```bash
grep -n "\"version\"" .claude-plugin/plugin.json .claude-plugin/marketplace.json
```
Expected: both show `0.33.7`.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(release): 0.33.7 — retire orphaned visualization agents"
```
