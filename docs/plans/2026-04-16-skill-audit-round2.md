# Skill Audit Round 2 Remediation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Resolve remaining issues from the round-2 skill audit at `/tmp/skill-audit-v2/SUMMARY.md` — scope Option 2: 3 description rewrites + 2 TOCs + 5 portability fixes + 5 step-numbering/dedupe fixes + `{base-directory}` resolution design and migration + verification.

**Source Design Doc:** N/A — the audit report at `/tmp/skill-audit-v2/SUMMARY.md` and per-skill files at `/tmp/skill-audit-v2/<skill>.md` serve as the spec.

**Architecture:** Pure markdown/YAML remediation inside the aligned plugin. One new shared doc (`skills/_shared/resolve-skill-path.md`) centralizes the `{base-directory}` resolution procedure; existing skills migrate from inline-duplicated fallback patterns to a single-source reference. All other changes are scoped edits to skill files. No code, no tests, no schema changes.

**Tech Stack:** Markdown + YAML frontmatter only. Plugin versioned in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

**Verification philosophy:** These are documentation edits, not code. Each task includes a grep-based "Verify" step to confirm the change landed. The final task re-runs sub-agent audits on affected skills to confirm measurable score improvements.

---

## Prerequisites

None.

---

## Phase 1: Description Rewrites

### Task 1: Rewrite use-framework description

**Files:**
- Modify: `skills/use-framework/SKILL.md` (the YAML frontmatter `description:` field)

**Current description:**
```
"Guides a user through a decision framework's interactive phases, respecting WAIT points. Use with a framework name for fuzzy match, or alone to list available frameworks. Triggers when a user mentions a framework by name in any request."
```

**New description:**
```
"Runs a user through a named decision framework interactively. Use with a framework name for fuzzy match, or alone to list available frameworks."
```

**Why:** "respecting WAIT points" is workflow-summary language (anti-pattern #1 lite — audit finding). The "Triggers when a user mentions a framework by name" sentence duplicates guidance already in global CLAUDE.md.

**Step 1:** Read `skills/use-framework/SKILL.md` (first 5 lines) to confirm current description matches the "Current" string above verbatim.

**Step 2:** Edit the `description:` field to the new string.

**Step 3:** Verify:
```bash
grep -c "respecting WAIT points" skills/use-framework/SKILL.md
```
Expected: `0`

**Step 4:** Commit.
```bash
git add skills/use-framework/SKILL.md
git commit -m "docs(use-framework): tighten description, remove workflow-summary phrasing"
```

---

### Task 2: Rewrite kanban-resolve description

**Files:**
- Modify: `skills/kanban-resolve/SKILL.md` (`description:` field)

**Current:**
```
"Triages and resolves all accumulated Kanban board items in a single automated pass. Use when the board has multiple pending items in docs/kanban/todo/ to process as a batch."
```

**New:**
```
"Batch resolves accumulated Kanban board items. Use when docs/kanban/todo/ holds multiple pending items ready for processing."
```

**Why:** Current opener "Triages and resolves … in a single automated pass" reads as a workflow summary. Noun-led form is cleaner and passes anti-pattern #1 check.

**Step 1:** Read `skills/kanban-resolve/SKILL.md` (lines 1-5) to confirm.
**Step 2:** Edit the `description:` field.
**Step 3:** Verify: `grep -c "in a single automated pass" skills/kanban-resolve/SKILL.md` → `0`.
**Step 4:** Commit.
```bash
git add skills/kanban-resolve/SKILL.md
git commit -m "docs(kanban-resolve): tighten description to noun-led form"
```

---

### Task 3: Rewrite persona-panel description

**Files:**
- Modify: `skills/persona-panel/SKILL.md` (`description:` field)

**Current:**
```
"Test content against simulated buyer/user personas. Use when: 'test this with personas', 'run the persona panel', 'how would buyers react to this', 'which copy variant is better'"
```

**New:**
```
"Tests content against simulated buyer/user personas, producing an aggregation report and appending results to a longitudinal scorecard. Use when testing copy with personas, running the persona panel, or comparing how buyers would react to content variants."
```

**Why:** Audit found description lists trigger phrases but omits the artifacts the skill produces (aggregation report, scorecard). New version names deliverables *and* retains trigger coverage.

**Step 1:** Read `skills/persona-panel/SKILL.md` (lines 1-5).
**Step 2:** Edit the `description:` field.
**Step 3:** Verify:
```bash
grep -c "aggregation report" skills/persona-panel/SKILL.md
```
Expected: at least `1`.
**Step 4:** Commit.
```bash
git add skills/persona-panel/SKILL.md
git commit -m "docs(persona-panel): name deliverables in description"
```

---

## Phase 2: TOC Additions

### Task 4: Add TOC to illustration.md

**Files:**
- Modify: `skills/create-image/modes/illustration.md` (137 lines, no TOC)

**Why:** Rubric requires a Contents TOC on reference files over 100 lines. Sibling `icon.md` and `diagram.md` have TOCs; this mode file is the outlier.

**Step 1:** Read `skills/create-image/modes/illustration.md` end-to-end. Note every `##` section heading in order.

**Step 2:** Edit the file — insert a Contents list immediately after the opening HTML comment block and the `# Illustration Mode` heading (before the first paragraph). Format:

```markdown
## Contents
- <Section 1 heading>
- <Section 2 heading>
- <etc>
```

Use the actual `##` section headings from Step 1, preserving order.

**Step 3:** Verify:
```bash
grep -c "^## Contents" skills/create-image/modes/illustration.md
```
Expected: `1`.

**Step 4:** Commit.
```bash
git add skills/create-image/modes/illustration.md
git commit -m "docs(create-image): add TOC to illustration mode file"
```

---

### Task 5: Add TOC to persona-prompt.md

**Files:**
- Modify: `skills/persona-panel/references/persona-prompt.md` (102 lines, no TOC — sibling `aggregation-prompt.md` has one)

**Step 1:** Read `skills/persona-panel/references/persona-prompt.md`. List `##` section headings in order.

**Step 2:** Edit — insert a Contents list after the opening `# …` heading and its introductory paragraph/placeholders block, following the same format as `aggregation-prompt.md`:

```markdown
---

## Contents
- <Section 1>
- <Section 2>
- ...
```

**Step 3:** Verify: `grep -c "^## Contents" skills/persona-panel/references/persona-prompt.md` → `1`.

**Step 4:** Commit.
```bash
git add skills/persona-panel/references/persona-prompt.md
git commit -m "docs(persona-panel): add TOC to persona-prompt reference"
```

---

## Phase 3: Portability Fixes

### Task 6: Remove hardcoded "65 advisors" from kickstart

**Files:**
- Modify: `skills/kickstart/SKILL.md` (the "What to Try First" block — currently at line ~184)

**Current text (anchor):**
```
Try `/aligned:use-advisor rob-walling` for bootstrapped SaaS decision frameworks. 65 advisors are available across business, technology, and creative domains.
```

**New text:**
```
Try `/aligned:use-advisor rob-walling` for bootstrapped SaaS decision frameworks. The full catalog is in `advisors/registry.yaml`.
```

**Why:** Hardcoded "65 advisors" is time-sensitive and drifts whenever a new advisor lands. Dynamic pointer to the registry file is the durable version.

**Step 1:** Grep for the exact string: `grep -n "65 advisors are available" skills/kickstart/SKILL.md` — confirm exactly one match.

**Step 2:** Edit: replace `65 advisors are available across business, technology, and creative domains.` with `The full catalog is in \`advisors/registry.yaml\`.`

**Step 3:** Verify:
```bash
grep -cE "[0-9]+ advisors are available" skills/kickstart/SKILL.md
```
Expected: `0`.

**Step 4:** Commit.
```bash
git add skills/kickstart/SKILL.md
git commit -m "docs(kickstart): replace hardcoded advisor count with registry reference"
```

---

### Task 7: Remove Substack CTA from kickstart

**Files:**
- Modify: `skills/kickstart/SKILL.md` (last line, currently line ~197)

**Current line:**
```
**Stay updated.** Want to know when new advisors and frameworks ship? [Subscribe on Substack](https://bigchewypretzels.substack.com)
```

**Action:** Delete this line entirely (it's the final line of the file).

**Why:** `bigchewypretzels.substack.com` is the plugin author's personal URL. Per CLAUDE.md Portability Rule, user-facing skills must not embed author-specific links. Skills run for every user who installs the plugin.

**Step 1:** Read the last 5 lines of `skills/kickstart/SKILL.md` to confirm the line exists at EOF.

**Step 2:** Edit — delete the line (and any trailing blank-line spacing that makes it an orphan).

**Step 3:** Verify:
```bash
grep -c "substack" skills/kickstart/SKILL.md
```
Expected: `0`.

**Step 4:** Commit.
```bash
git add skills/kickstart/SKILL.md
git commit -m "docs(kickstart): remove author-specific Substack link for portability"
```

---

### Task 8: Parameterize npm commands in kanban-resolve

**Files:**
- Modify: `skills/kanban-resolve/SKILL.md` (lines ~84-86 and ~105 contain hardcoded `npm run build` / `npm test`)

**Why:** Hardcoded `npm` commands break the skill for Python, Go, Rust, or any non-Node project. Per CLAUDE.md Portability Rule, skills must guard on project type or defer to CLAUDE.md's Tech Stack section.

**Step 1:** Read `skills/kanban-resolve/SKILL.md` lines 75-115 to see the plan-template block and the post-template sentence.

**Step 2:** Edit the template block: replace the two lines

```
**Step N:** Run `npm run build` to verify compilation
**Step N+1:** Run `npm test` to verify no regressions
```

with

```
**Step N:** Run the project's build command (from `CLAUDE.md` Tech Stack) to verify compilation
**Step N+1:** Run the project's test command (from `CLAUDE.md` Tech Stack) to verify no regressions
```

**Step 3:** Edit the sentence after the template block (currently line ~105): replace

```
Every task MUST end with build verification (`npm run build`), test verification (`npm test`), and a commit step.
```

with

```
Every task MUST end with build verification, test verification (both using the project's build/test commands from CLAUDE.md Tech Stack), and a commit step.
```

**Step 4:** Verify:
```bash
grep -c "npm " skills/kanban-resolve/SKILL.md
```
Expected: `0`.

**Step 5:** Commit.
```bash
git add skills/kanban-resolve/SKILL.md
git commit -m "fix(kanban-resolve): parameterize build/test commands per portability rule"
```

---

### Task 9: Gate e2e/trigger-map.yaml check in executing-plans

**Files:**
- Modify: `skills/executing-plans/SKILL.md` (LLM surface check — line ~49)

**Current text:**
```
**LLM surface check:** If the task involved changes to advisor prompts, framework prompts, prompt builders, or personalization logic, run the project's eval command. Check `e2e/trigger-map.yaml` for file-to-scenario mappings. If a mapping exists, run `npx promptfoo eval -c <scenario-path> --no-progress-bar` from the `e2e/` directory. …
```

**Problem:** `e2e/trigger-map.yaml` is author-specific infrastructure not present in most repos. The current wording tells Claude to "check" the file unconditionally, then gates the eval command only.

**New text:**
```
**LLM surface check:** If the task involved changes to advisor prompts, framework prompts, prompt builders, or personalization logic, check whether the project has eval infrastructure. If `e2e/trigger-map.yaml` exists, read it for file-to-scenario mappings; if a mapping matches the changed files, run `npx promptfoo eval -c <scenario-path> --no-progress-bar` from the `e2e/` directory. If no `e2e/trigger-map.yaml` exists, skip this check silently. Don't wait until all tasks are done — catching regressions early is cheaper than debugging across multiple steps. If evals fail, classify the failure (prompt issue, eval calibration, or model variance) and fix before continuing.
```

**Step 1:** Read `skills/executing-plans/SKILL.md` lines 45-55.

**Step 2:** Edit the LLM surface check paragraph per above.

**Step 3:** Verify that the phrase "If `e2e/trigger-map.yaml` exists" appears and no bare unconditional "Check \`e2e/trigger-map.yaml\`" remains:
```bash
grep -n "e2e/trigger-map.yaml" skills/executing-plans/SKILL.md
```
Every occurrence should be behind a conditional ("If … exists" or similar).

**Step 4:** Commit.
```bash
git add skills/executing-plans/SKILL.md
git commit -m "fix(executing-plans): gate e2e/trigger-map.yaml on existence"
```

---

### Task 10: Clarify cross-validation conditional in eval-audit

**Files:**
- Modify: `skills/eval-audit/SKILL.md` (line ~66)

**Current text:**
```
**Cross-validation (always runs, even if no gaps):** Read `e2e/trigger-map.yaml`. Verify every path in the trigger-map matches at least one `e2e/eval-surface.yaml` pattern. If any trigger-map path is not covered by a surface pattern, report: "Trigger-map path `<path>` does not match any eval-surface pattern — add a matching pattern to `e2e/eval-surface.yaml`."
```

**Problem:** "always runs" directly contradicts the existence guard used elsewhere in this skill, and `e2e/trigger-map.yaml` is author-specific.

**New text:**
```
**Cross-validation (if `e2e/trigger-map.yaml` exists):** Read `e2e/trigger-map.yaml`. Verify every path in the trigger-map matches at least one `e2e/eval-surface.yaml` pattern. If any trigger-map path is not covered by a surface pattern, report: "Trigger-map path `<path>` does not match any eval-surface pattern — add a matching pattern to `e2e/eval-surface.yaml`." If `e2e/trigger-map.yaml` does not exist, skip this check.
```

**Step 1:** Read `skills/eval-audit/SKILL.md` lines 60-70.
**Step 2:** Edit the cross-validation paragraph.
**Step 3:** Verify: `grep -c "always runs" skills/eval-audit/SKILL.md` → `0`.
**Step 4:** Commit.
```bash
git add skills/eval-audit/SKILL.md
git commit -m "fix(eval-audit): gate cross-validation on trigger-map.yaml existence"
```

---

## Phase 4: Step-Numbering and Duplication Fixes

### Task 11: Resolve Step 7 duplication in add-framework + renumber 7b

**Files:**
- Modify: `skills/add-framework/SKILL.md` (lines ~199-220)

**Problem:** Step 7 "Register Framework for Discovery" instructs placing the framework at `frameworks/{slug}/` — but Step 1 already created that folder. In the default case it's redundant; in the non-default case (Step 0 detected a different path like `src/lib/frameworks/`) it contradicts that detection. Additionally, the sequence jumps from Step 7 to Step 7b with no 7a, which is a readability smell.

**Fix approach:** Delete the content of Step 7 entirely (it is a restatement of Step 1). Renumber Step 7b → Step 7 and Step 8 → Step 8 (stays). Re-check all downstream cross-references.

**Step 1:** Read `skills/add-framework/SKILL.md` fully to map the current step sequence (Step 0 through Step 8) and any cross-references between them.

**Step 2:** Edit — remove the `### 7. Register Framework for Discovery` heading and its body (the two short paragraphs that duplicate Step 1). Renumber `### 7b. Update Advisor and Framework Counts` to `### 7. Update Advisor and Framework Counts`. Step 8 (Verify) stays as Step 8.

**Step 3:** Grep for any cross-references to the removed step or the old `7b` label:
```bash
grep -nE "(Step 7b|step 7b|### 7b)" skills/add-framework/SKILL.md
grep -nE "Register Framework for Discovery" skills/add-framework/SKILL.md
```
Both should return no matches.

**Step 4:** Also grep the rest of the plugin for references to `add-framework` Step 7/7b in case downstream skills or docs reference the label:
```bash
grep -rn "add-framework.*Step 7" skills/ README.md docs/
```
If any hits, update them to the new numbering.

**Step 5:** Commit.
```bash
git add skills/add-framework/SKILL.md
git commit -m "docs(add-framework): remove duplicate Step 7, renumber 7b to 7"
```

---

### Task 12: Resolve Step 8 duplication in add-advisor + renumber

**Files:**
- Modify: `skills/add-advisor/SKILL.md` (lines ~193-234)

**Problem:** Step 8 "Register Advisor for Discovery" writes the prompt file to `advisors/prompts/{advisor-id}.md` — but Step 4 already wrote the prompt to `{detected-prompt-path}/{advisor-id}.md` which defaults to that same location. In the default case Step 8 is a redundant write; in the non-default case it overrides Step 0's detection. The sequence also uses retrofitted labels: 8 → 8b → 8c → 9.

**Fix approach:** Delete Step 8's content (it's a restatement of Step 4). Renumber: 8b → 8, 8c → 9, 9 (Verify) → 10.

**Step 1:** Read `skills/add-advisor/SKILL.md` fully to map step structure and find all cross-references.

**Step 2:** Edit:
- Delete the `### 8. Register Advisor for Discovery` heading and its two-line body.
- Renumber `### 8b. Update the Registry` → `### 8. Update the Registry`.
- Renumber `### 8c. Update Advisor and Framework Counts` → `### 9. Update Advisor and Framework Counts`.
- Renumber `### 9. Verify` (or whatever the current Verify step is) → `### 10. Verify`.

**Step 3:** Grep for any internal cross-references to old labels:
```bash
grep -nE "(Step 8b|step 8b|Step 8c|step 8c|### 8b|### 8c)" skills/add-advisor/SKILL.md
grep -nE "Register Advisor for Discovery" skills/add-advisor/SKILL.md
```
All should return no matches.

**Step 4:** Check other skills/docs for references:
```bash
grep -rn "add-advisor.*Step [89]" skills/ README.md docs/
```

**Step 5:** Commit.
```bash
git add skills/add-advisor/SKILL.md
git commit -m "docs(add-advisor): remove duplicate Step 8, renumber to sequential 8-10"
```

---

### Task 13: Fix broken "Bug Board Entry Format below" reference in finishing-a-development-branch

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md` (line 170)

**Current text:**
```
If you find discrepancies in the diagrams you're editing, file bugs (see "Bug Board Entry Format below") with category `architecture-discrepancy`.
```

**Problem:** There is no "Bug Board Entry Format" section in this SKILL.md. The Kanban format lives in `_shared/kanban-entry-format.md`.

**New text:**
```
If you find discrepancies in the diagrams you're editing, file bugs (see `skills/_shared/kanban-entry-format.md`) with category `architecture-discrepancy`.
```

**Step 1:** Read `skills/finishing-a-development-branch/SKILL.md` lines 165-175 to confirm the anchor text.
**Step 2:** Edit the line.
**Step 3:** Verify:
```bash
grep -c 'Bug Board Entry Format below' skills/finishing-a-development-branch/SKILL.md
```
Expected: `0`.

**Step 4:** Confirm the new reference points to a real file:
```bash
ls skills/_shared/kanban-entry-format.md
```
Expected: file exists.

**Step 5:** Commit.
```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix(finishing-a-development-branch): repair broken cross-reference at L170"
```

---

### Task 14: Reconcile three competing default modes in executing-plans

**Files:**
- Modify: `skills/executing-plans/SKILL.md` (lines ~16, ~38-40, ~51-57)

**Problem:** Three statements of what the default execution mode is:
- Line ~16: `**Autonomous mode:** Execute all tasks without pausing for review between batches.`
- Line ~39: `### Step 2: Execute Build Tasks` followed by `**Default: First 5 tasks**`
- Lines ~51-55: Step 3 reports build-complete and asks the user to test — implies interactive checkpointing, not autonomous.

A reader cannot tell which default applies. Recent usage (visible in git log — see task-by-task commits for kickstart extraction on Apr 16) has been autonomous, and the skill header already presents Autonomous Mode as the default. Decision: **autonomous is the default; batched-with-checkpoint is an opt-in escape hatch.** (See Decision Log entry #3.)

**Fix approach:** Rewrite Step 2 to state the autonomous default, document batched mode as an opt-in variation, and scope Step 3's "instructions on what to test" guidance to batched mode only.

**Step 1:** Read `skills/executing-plans/SKILL.md` lines 10-65 to see the full pattern.

**Step 2:** Edit Step 2's opener. Replace:
```
### Step 2: Execute Build Tasks
**Default: First 5 tasks**

For each task:
```
with:
```
### Step 2: Execute Build Tasks

**Default mode: autonomous.** Execute all tasks without stopping for review. Only stop on task failure or a blocker.

**Batched mode (opt-in):** If the user explicitly requests checkpoints, or the plan is marked for batched execution, process tasks in groups of 3–7 and report between batches.

For each task:
```

**Step 3:** Edit Step 3. Replace:
```
### Step 3: Report
When Build Tasks are complete:
- Show what was implemented
- Show verification output
- Say: "Build is complete. Ready for testing".  give the user instructions on what to test and how to test it.  Include the bash command that the user should run to go to the worktree and start the dev server
```
with:
```
### Step 3: Report

**Autonomous mode:** When all tasks pass verification, stop. Summarize what was implemented and show verification output. Do not hand off to `finishing-a-development-branch` — the user runs that manually.

**Batched mode only:** Between batches, show what was implemented, show verification output, say "Build is complete. Ready for testing", give the user instructions on what to test, and include the bash command to enter the worktree and start the dev server.
```

**Step 4:** Verify the three conflicting phrasings are gone or resolved:
```bash
grep -n "Default: First 5 tasks" skills/executing-plans/SKILL.md
grep -n "execute all tasks without pausing" skills/executing-plans/SKILL.md
```
The first must return 0 matches. The second may still match (it remains in the autonomous-mode preamble).

**Step 5:** Commit.
```bash
git add skills/executing-plans/SKILL.md
git commit -m "docs(executing-plans): resolve three competing default modes to one"
```

---

### Task 15: Extract Phase 5 sub-agent dispatch prompt from root-cause-analysis

**Files:**
- Modify: `skills/root-cause-analysis/SKILL.md` (lines ~290-319 — the ~30-line inline dispatch prompt)
- Create: `skills/root-cause-analysis/post-fix-review-prompt.md`

**Why:** Progressive disclosure — a ~30-line verbatim prompt block should live in a reference file, leaving SKILL.md as a leaner orchestrator. The audit flagged this at 8.1/10 partly for the inline prompt mass.

**Step 1:** Read `skills/root-cause-analysis/SKILL.md` lines 280-325 to capture the full dispatch block.

**Step 2:** Create `skills/root-cause-analysis/post-fix-review-prompt.md`:

```markdown
# Post-Fix Review Prompt Template

> Read by the root-cause-analysis skill at Phase 5 dispatch time.

**Placeholders:**
- `{root-cause-statement}` — hypothesis confirmed during Phase 3
- `{diff}` — output of `git diff` (or `git diff HEAD~N`) capturing changes made during debugging
- `{base-directory}` — absolute path to the root-cause-analysis skill directory (resolve before dispatch; the sub-agent cannot read it from skill-load context)

---

You are a post-fix reviewer for a debugging session. Your job is to verify the fix is correct, complete, and safe — not just that it works.

You have access to Glob, Grep, and Read tools. Do not use Bash for searching — use the Grep tool instead.

**Context:**
- Root cause identified during investigation: {root-cause-statement}
- Changes made (git diff): {diff}

Read the supporting technique docs (the dispatching agent MUST resolve these to absolute paths before sending this prompt):
- `{base-directory}/fix-the-right-layer.md`
- `{base-directory}/defense-in-depth.md`

Then evaluate the fix against these five criteria:

| # | Criterion | What to check |
|---|-----------|---------------|
| 1 | Root cause consistency | Does the fix address the stated root cause, or does it patch a symptom? A symptom fix is one that suppresses the error without removing the condition that caused it. |
| 2 | Right layer | Per fix-the-right-layer.md: does the fix modify the producer of bad state, or does it patch the consumer/guard that detected it? Patching the detector is almost always wrong. |
| 3 | Defense in depth | Per defense-in-depth.md: does the fix add validation at multiple layers the data passes through, or does it only patch one layer? A single-layer fix leaves other code paths vulnerable to the same bug. |
| 4 | Blast radius | Grep for all files that import/reference/depend on the changed files. Are there ripple effects the fix didn't account for? Flag any dependent that may behave differently due to the change. |
| 5 | Completeness | Grep the codebase for similar patterns to the bug. If the same mistake exists elsewhere, flag every occurrence. |

For each criterion, report: PASS, FLAG (non-blocking concern), or FAIL (must fix before proceeding). Include specific file paths, line numbers, and evidence for every finding.

Output format:
- **Summary:** One sentence overall verdict
- **Criteria results:** Table with criterion, verdict, and evidence
- **Action items:** List of concrete changes needed (if any), ordered by severity
```

**Step 3:** Edit `skills/root-cause-analysis/SKILL.md`. Replace the inline dispatch block (starting from `**Dispatch** a sub-agent via Task tool …` through the closing `"Output format: …"` quote) with:

```markdown
**Dispatch** a sub-agent via Task tool (`subagent_type=general-purpose`, `model=sonnet`) using the prompt template in `{base-directory}/post-fix-review-prompt.md`. Read the template, substitute `{root-cause-statement}`, `{diff}`, and the resolved `{base-directory}`, and pass the result as the sub-agent's prompt.
```

Keep the "Before dispatching, gather three inputs:" lead-in and the "Gate:" block that follows — only the inline prompt body gets extracted.

**Step 4:** Verify the extraction:
```bash
wc -l skills/root-cause-analysis/post-fix-review-prompt.md
grep -c "You are a post-fix reviewer" skills/root-cause-analysis/SKILL.md
grep -c "You are a post-fix reviewer" skills/root-cause-analysis/post-fix-review-prompt.md
```
Expected: the new file has ≥30 lines; the SKILL.md grep returns `0`; the reference-file grep returns `1`.

**Step 5:** Commit.
```bash
git add skills/root-cause-analysis/post-fix-review-prompt.md skills/root-cause-analysis/SKILL.md
git commit -m "refactor(root-cause-analysis): extract Phase 5 review prompt to reference"
```

---

## Phase 5: `{base-directory}` Resolution Design and Migration

**Design context.** The audit flagged `{base-directory}` resolution fragility as the biggest remaining systemic issue — 49 occurrences across 16 skill files. Each affected skill currently carries a multi-line inline fallback block that tells Claude how to resolve the placeholder when the harness-printed "Base directory for this skill:" line has been compressed out of context. The fallbacks duplicate the same logic and use a slow `$HOME`-wide Glob on skill filenames.

**Design decision (see Decision Log entry #2):** Keep `{base-directory}` as the placeholder, but (a) switch the fallback from skill-filename Glob to `.claude-plugin/plugin.json`-anchored Glob (one match, unique anchor, fast), and (b) compress the multi-line fallback block to a single "Path Resolution" line near the top of each affected SKILL.md, with a shared reference doc (`skills/_shared/resolve-skill-path.md`) documenting the rationale and edge cases. Skills do NOT depend on reading the shared doc at runtime — the one-line summary is operationally sufficient. The shared doc is reference material for skill authors.

### Task 16: Write `skills/_shared/resolve-skill-path.md`

**Files:**
- Create: `skills/_shared/resolve-skill-path.md`

**Step 1:** Create the file with this exact content:

```markdown
# Resolving a Skill's Base Directory

Skills in the aligned plugin reference their own bundled files using a `{base-directory}` placeholder. This doc explains the single procedure every skill uses to resolve that placeholder.

## Contents
- Primary source
- Fallback
- Plugin root
- Usage pattern

## Primary source

When a skill loads, the Claude Code harness prints a line near the top of the conversation turn:

`Base directory for this skill: /absolute/path/to/skills/<skill-name>`

Use that path as `{base-directory}`. It's the fastest and most accurate source.

## Fallback

If the "Base directory for this skill:" line has been compressed out of context (long conversations), resolve via the plugin root:

1. Glob `$HOME` for `**/.claude-plugin/plugin.json`. This file uniquely identifies a Claude Code plugin's root; the aligned plugin's copy is the one whose parent directory contains a `skills/` subdirectory with the skill's name.
2. Take the parent of the matched `.claude-plugin/` directory — that is the plugin root.
3. Derive `{base-directory}` = `<plugin-root>/skills/<this-skill-name>/`.

This uses a single Glob with a unique anchor, which is faster and more reliable than `$HOME`-wide globbing on skill filenames.

If the Glob returns no matches, STOP and tell the user the plugin appears to be missing or misinstalled.

## Plugin root

If a skill needs the plugin root directly (e.g., to locate `docs/ralph_loops/` or reference sibling skill paths), perform steps 1–2 of the Fallback procedure. Do not derive the plugin root by string-manipulating `{base-directory}` — always anchor on `.claude-plugin/plugin.json`.

## Usage pattern in skill files

Each skill that references its own bundled files includes one "Path Resolution" note near the top of SKILL.md:

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/<this-skill-name>/`. See `skills/_shared/resolve-skill-path.md` for rationale.

All later references to `{base-directory}` in the same file use the placeholder without restating the resolution procedure.
```

**Step 2:** Verify:
```bash
wc -l skills/_shared/resolve-skill-path.md
grep -c "^## " skills/_shared/resolve-skill-path.md
```
Expected: ≥30 lines and ≥4 `##` sections.

**Step 3:** Commit.
```bash
git add skills/_shared/resolve-skill-path.md
git commit -m "docs(_shared): add shared base-directory resolution procedure"
```

---

### Task 17–28: Per-skill migration

**Shared pattern for all tasks 17–28:**

Each of the following per-file tasks follows the same three-step shape. The pattern is described once here; each task below lists only the target files and any file-specific notes.

**Per-file shape:**

1. **Read** the file. Identify every "Fallback (if the base-directory line was compressed out of context)" block — typically 4–8 lines, introducing a Glob against `$HOME` for the skill-name filename.

2. **Replace** the first such block per SKILL.md with the standardized one-line Path Resolution note (place it once near the top of the file, just below the frontmatter/initial heading if not already present):

   > **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/<this-skill-name>/`. See `skills/_shared/resolve-skill-path.md` for rationale.

   Where `<this-skill-name>` is the literal skill directory name (e.g., `brainstorming`, `writing-plans`).

   **Delete** every other inline "Fallback" block in the file — subsequent references just use `{base-directory}` directly.

3. **Verify** the file no longer contains duplicated fallback logic:
   ```bash
   grep -c "compressed out of context" <file>
   ```
   Expected: at most `1` (the Path Resolution note — or `0` if the note reworded the phrase). And:
   ```bash
   grep -c "**/\*-<skill-name>\*\*.md" <file>
   ```
   Should be `0` (no leftover skill-filename Glob patterns).

4. **Commit** per task.

Reference files and mode files under a skill's subdirectories (e.g., `modes/*.md`, `references/*.md`) follow the same rule: replace their fallback block with the one-line pointer, which can say "see the Path Resolution note in SKILL.md" rather than re-stating the procedure.

---

### Task 17: Migrate brainstorming

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (8 `{base-directory}` refs; carries the heaviest fallback blocks)
- Modify: `skills/brainstorming/modes/software.md` (4 refs incl. the plugin-root variant — preserve the "plugin root is two levels up" derivation but drop the inline $HOME Glob fallback)
- Modify: `skills/brainstorming/modes/business.md` (3 refs)

**File-specific note:** `modes/software.md` currently includes a separate plugin-root fallback that globs for `docs/ralph_loops/autopilot.sh`. Replace with the plugin.json-anchored approach from `_shared/resolve-skill-path.md`. Add a short inline pointer "see SKILL.md Path Resolution note" in each mode file rather than restating the full note.

**Step 1:** Apply the per-file shape from Task 17–28's shared pattern to each of the three files.
**Step 2:** Verify:
```bash
grep -c "autopilot.sh" skills/brainstorming/modes/software.md
```
Expected: `0` (no more filename-specific fallback anchor).

**Step 3:** Commit all three files together.
```bash
git add skills/brainstorming/
git commit -m "refactor(brainstorming): migrate to shared base-directory resolution"
```

---

### Task 18: Migrate writing-plans

**Files:**
- Modify: `skills/writing-plans/SKILL.md` (6 refs across plan-critique-checklist, templates, ralph_loops, and kanban resolution)

**File-specific note:** writing-plans' inline fallbacks appear in three places (critique checklist resolution, ralph-loops resolution in "Execution Handoff", and kanban entry format section). All three consolidate into the single Path Resolution note at the top plus a specialized "plugin root = {base-directory}/../.." derivation reminder where needed for ralph-loops specifically.

**Steps:** per-file shape. Commit:
```bash
git add skills/writing-plans/SKILL.md
git commit -m "refactor(writing-plans): migrate to shared base-directory resolution"
```

---

### Task 19: Migrate create-design-principles

**Files:**
- Modify: `skills/create-design-principles/SKILL.md` (3 refs)

**Steps:** per-file shape.
```bash
git add skills/create-design-principles/SKILL.md
git commit -m "refactor(create-design-principles): migrate to shared base-directory resolution"
```

---

### Task 20: Migrate create-image

**Files:**
- Modify: `skills/create-image/SKILL.md` (3 refs for router-to-modes delegation)

**File-specific note:** The audit also flagged the `{base-directory}` placeholder at lines 55/59/63 as "unusual phrasing". The Path Resolution note addresses this explicitly; the delegation lines can stay as `Read {base-directory}/modes/<mode>.md`.

**Steps:** per-file shape.
```bash
git add skills/create-image/SKILL.md
git commit -m "refactor(create-image): migrate to shared base-directory resolution"
```

---

### Task 21: Migrate root-cause-analysis

**Files:**
- Modify: `skills/root-cause-analysis/SKILL.md` (4 refs; note Task 15 already added `post-fix-review-prompt.md` which uses `{base-directory}` — that reference resolves via the same procedure)

**Steps:** per-file shape.
```bash
git add skills/root-cause-analysis/SKILL.md
git commit -m "refactor(root-cause-analysis): migrate to shared base-directory resolution"
```

---

### Task 22: Migrate persona-panel

**Files:**
- Modify: `skills/persona-panel/SKILL.md` (4 refs)
- Modify: `skills/persona-panel/modes/persona-creation-flow.md` (2 refs — includes the audit-flagged multi-match ambiguity at line ~82; the shared procedure's "unique anchor is plugin.json" phrasing resolves this)

**Steps:** per-file shape for both files.
```bash
git add skills/persona-panel/
git commit -m "refactor(persona-panel): migrate to shared base-directory resolution"
```

---

### Task 23: Migrate finishing-a-development-branch

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md` (4 refs — audit flagged repeated fallback instructions at lines 148/178/194/298)
- Modify: `skills/finishing-a-development-branch/references/code-review-scan.md` (1 ref)

**File-specific note:** the audit at this skill explicitly recommended "the repeated `{base-directory}` resolution instruction could be stated once at the top" — this task satisfies that.

**Steps:** per-file shape for both files.
```bash
git add skills/finishing-a-development-branch/
git commit -m "refactor(finishing-a-development-branch): migrate to shared base-directory resolution"
```

---

### Task 24: Migrate codebase-audit

**Files:**
- Modify: `skills/codebase-audit/SKILL.md` (2 refs — audit flagged lack of fallback)

**Steps:** per-file shape — note this skill did NOT have a fallback block; the migration ADDS the Path Resolution note once and leaves placeholder uses intact.
```bash
git add skills/codebase-audit/SKILL.md
git commit -m "docs(codebase-audit): add Path Resolution note for base-directory"
```

---

### Task 25: Migrate executing-plans

**Files:**
- Modify: `skills/executing-plans/SKILL.md` (1 ref, in Kanban Entry Format section)

**Steps:** per-file shape.
```bash
git add skills/executing-plans/SKILL.md
git commit -m "docs(executing-plans): add Path Resolution note for base-directory"
```

---

### Task 26: Migrate eval-audit

**Files:**
- Modify: `skills/eval-audit/SKILL.md` (1 ref — line 82, Kanban Entry Format)

**Steps:** per-file shape.
```bash
git add skills/eval-audit/SKILL.md
git commit -m "docs(eval-audit): add Path Resolution note for base-directory"
```

---

### Task 27: Migrate kickstart

**Files:**
- Modify: `skills/kickstart/SKILL.md` (2 refs — audit flagged both as abstract phrasing that Claude could guess wrong)

**Steps:** per-file shape.
```bash
git add skills/kickstart/SKILL.md
git commit -m "docs(kickstart): add Path Resolution note for base-directory"
```

---

### Task 28: Migrate `_shared/critique-panel-orchestration.md`

**Files:**
- Modify: `skills/_shared/critique-panel-orchestration.md` (1 ref — the one shared utility that also references `{base-directory}`)

**File-specific note:** A `_shared/` file is read by multiple skills; `{base-directory}` here must mean *the calling skill's* base directory, which is resolved by the caller before this file is read. Add a one-line preamble note: "`{base-directory}` refers to the calling skill's base directory; the calling skill is responsible for resolving it per `skills/_shared/resolve-skill-path.md`."

**Steps:** per-file shape + the preamble note above.
```bash
git add skills/_shared/critique-panel-orchestration.md
git commit -m "docs(_shared): clarify base-directory semantics in critique-panel-orchestration"
```

---

## Phase 6: Verification and Release

### Task 29: Re-audit affected skills and confirm score improvements

**Files:**
- No file modifications — this is a verification-only task.

**Why:** Closes the loop on whether the remediation actually improved measurable audit scores. Writes fresh per-skill audits to `/tmp/skill-audit-v3/` so the next iteration (if any) has a clean comparison point.

**Step 1:** Prepare the audit-v3 workspace:
```bash
mkdir -p /tmp/skill-audit-v3
cp /tmp/skill-audit-v2/rubrics.md /tmp/skill-audit-v3/rubrics.md
```

**Step 2:** For each skill touched by this plan, dispatch a sub-agent (via Task tool, `subagent_type=general-purpose`) to re-audit it against `/tmp/skill-audit-v3/rubrics.md` and write the result to `/tmp/skill-audit-v3/<skill-name>.md`. The skills to re-audit are:

- use-framework (Task 1)
- kanban-resolve (Tasks 2, 8)
- persona-panel (Tasks 3, 22)
- create-image (Tasks 4, 20)
- kickstart (Tasks 6, 7, 27)
- executing-plans (Tasks 9, 14, 25)
- eval-audit (Tasks 10, 26)
- add-framework (Task 11)
- add-advisor (Task 12)
- finishing-a-development-branch (Tasks 13, 23)
- root-cause-analysis (Tasks 15, 21)
- brainstorming (Task 17)
- writing-plans (Task 18)
- create-design-principles (Task 19)
- codebase-audit (Task 24)

**Sub-agent prompt template:** Reuse the exact prompt used in `/tmp/skill-audit-v2/` generation — point the agent at `/tmp/skill-audit-v3/rubrics.md` as the rubric, the skill directory as the subject, and `/tmp/skill-audit-v3/<skill-name>.md` as the output path. Instruct: "Do NOT read /tmp/skill-audit-v2/ — score independently."

**Step 3:** After all sub-agents complete, compute the mean score across the 15 touched skills and compare to v2 scores. Write a short delta summary to `/tmp/skill-audit-v3/SUMMARY.md` with:

- Per-skill table: v2 score | v3 score | delta
- Aggregate: v2 mean vs v3 mean, grade distribution shift
- Any skill whose score *decreased* — flag for investigation

**Step 4:** Report the summary to the user. If any skill regressed, pause for user decision before committing further; otherwise proceed to Task 30.

**Step 5 (no commit for this task — verification only):** This task produces audit files in `/tmp/` only. No git changes.

---

### Task 30: Bump plugin version to 0.24.0

**Files:**
- Modify: `.claude-plugin/plugin.json` (line 3: `"version": "0.23.0"` → `"0.24.0"`)
- Modify: `.claude-plugin/marketplace.json` (same version field — verify with grep first)

**Why:** Per the project CLAUDE.md "Adding a Skill" section, non-trivial skill changes bump the version. This remediation touches 15 skills and adds one shared doc. Semver: 0.23.0 → 0.24.0 (minor bump, pre-1.0).

**Step 1:** Read `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` to confirm current version is `0.23.0` in both.

**Step 2:** Edit both files, replacing the `version` field.

**Step 3:** Verify:
```bash
grep -nE '"version":' .claude-plugin/plugin.json .claude-plugin/marketplace.json
```
Expected: both show `0.24.0`.

**Step 4:** Commit.
```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump plugin version to 0.24.0 (skill audit round 2 remediation)"
```

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|-------------|------------------------|
| 1 | Scope of this plan | Option 2: quick wins + `{base-directory}` design and migration | Option 1 (quick wins only, no systemic work); Option 3 (descriptions + TOCs only, smallest fast win) |
| 2 | `{base-directory}` resolution strategy | Shared reference doc + one-line inline "Path Resolution" note + plugin.json-anchored Glob fallback | (a) env var `$CLAUDE_PLUGIN_ROOT` (not set by Claude Code), (b) bash helper script (adds runtime dependency), (c) leave inline duplication (no improvement) |
| 3 | executing-plans default execution mode | Autonomous (all tasks, no checkpoint) as default; batched-with-checkpoint as opt-in escape hatch | (a) batched-5 as default (contradicts top-of-file "Autonomous mode" preamble and recent usage); (b) leave the three-way ambiguity (no) |
| 4 | Step renumbering for add-advisor/add-framework | Close gaps (Step 8, 8b, 8c, 9 → 8, 9, 10; Step 7, 7b → 7) after removing duplicated steps | (a) keep legacy 8b/8c labels to minimize diff (preserves the smell); (b) renumber without removing duplicates (doesn't fix the duplication) |
| 5 | Sub-agent prompt extraction in root-cause-analysis | Extract to sibling file `post-fix-review-prompt.md`, reference from SKILL.md | (a) leave inline (audit flagged 8.1 partly for this); (b) extract to `references/` subdirectory (inconsistent with this skill's current layout — other technique docs are siblings, not nested) |

### Appendix: Decision Details

#### Decision 1: Scope

**Chose:** Option 2 — quick wins + `{base-directory}` design.

**Why:** Three scopes were offered in the plan-session preamble. Option 1 (quick wins only) would push the fleet mean from 8.37 → ~8.7 and move ~3-5 skills to A-grade. Option 2 adds the single largest remaining systemic issue (`{base-directory}` fragility, flagged on 7+ skills out of scope in round 1). Option 3 is smallest and would not tackle the systemic issue. The user selected Option 2 with awareness of the added work.

**Alternatives rejected:**
- **Option 1:** Leaves the systemic base-directory issue pending; would require a separate design cycle.
- **Option 3:** Too narrow — misses portability violations and step-numbering fixes, which are low-effort high-impact.

#### Decision 2: `{base-directory}` resolution strategy

**Chose:** Shared reference doc (`skills/_shared/resolve-skill-path.md`) + one-line "Path Resolution" note inline in each affected skill + plugin.json-anchored Glob fallback.

**Why:** The current pattern duplicates a 4–8 line fallback block in 16 files. The duplicated blocks Glob `$HOME` for skill-name filename matches (slow; ambiguous when multiple plugin installs exist). Plugin.json is unique and single-match per install — anchoring there is faster and less error-prone. Operationally, skills cannot *depend on reading* the shared doc at runtime, because reading it requires the same resolution procedure (circular). So the resolution logic stays inline as a one-liner; the shared doc is reference-only for authors. This is strictly better than the current state on three dimensions: file length, resolution speed, and single-source-of-truth for the procedure.

**Alternatives rejected:**
- **Env var `$CLAUDE_PLUGIN_ROOT`:** Claude Code does not set any skill-root env var at the time of this writing (verified by grep — zero references in the codebase). Could request the feature from Anthropic, but that's out of scope for this remediation.
- **Bash helper script (`_shared/find-plugin-root.sh`):** Adds a runtime dependency and a shell-portability surface. Current pattern doesn't touch shell; a Glob-based approach stays within Claude's native tools.
- **Leave inline duplication:** No improvement to the issue the audit flagged.

#### Decision 3: executing-plans default execution mode

**Chose:** Autonomous (all tasks, no checkpoint) as the declared default; batched-with-checkpoint as an opt-in escape hatch.

**Why:** SKILL.md line 16 already states "Autonomous mode: Execute all tasks without pausing" at the top. Recent usage (visible in `git log` for the April 16 kickstart extraction — 13 sequential task commits in one session) shows the skill is used autonomously in practice. The conflicting "Default: First 5 tasks" at line 40 is legacy wording that contradicts both the top-of-file claim and observed behavior. Picking autonomous-default aligns the text with usage; the batched mode remains as an opt-in path for plans that benefit from human checkpoints.

**Alternatives rejected:**
- **Batched-5 as default:** Would require removing the "Autonomous mode" preamble (a larger, behavior-changing edit) and contradicts recent usage.
- **Preserve three-way ambiguity:** The audit flagged this specifically as a workflow-clarity weakness; leaving it would waste the fix opportunity.

#### Decision 4: Step renumbering

**Chose:** Close the numbering gaps after removing the duplicated steps (add-framework: delete Step 7, rename 7b → 7; add-advisor: delete Step 8, rename 8b → 8, 8c → 9, push old Step 9 → 10).

**Why:** Retrofitted sub-step labels (8b, 8c, 7b with no 7a) are a readability smell and make it easy to skip a step. Once the *duplicated* Step 7 / Step 8 content is gone (the real audit finding), the remaining steps form a clean sequential list; collapsing the labels is a zero-cost cleanup that reinforces the fix.

**Alternatives rejected:**
- **Keep legacy 8b/8c labels:** Preserves the visual smell and invites future confusion.
- **Renumber without removing duplicates:** Doesn't address the actual audit finding (duplication); fixes cosmetics only.

#### Decision 5: Root-cause-analysis prompt extraction target

**Chose:** Extract to sibling file `skills/root-cause-analysis/post-fix-review-prompt.md`.

**Why:** The skill's current layout has four technique docs (`root-cause-tracing.md`, `fix-the-right-layer.md`, `defense-in-depth.md`, `condition-based-waiting.md`) and two example files (`find-polluter.sh`, `condition-based-waiting-example.ts`) all as siblings — not nested under `references/`. Following the established convention keeps the file organization coherent.

**Alternatives rejected:**
- **Leave inline:** The audit explicitly flagged the 30-line inline prompt block; skipping extraction wastes the fix opportunity.
- **`references/` subdirectory:** Inconsistent with this skill's existing layout — would create a new pattern for one file.

---
