# Skill Audit Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Remediate audit findings across 18 aligned plugin skills — rewrite 14 descriptions, add 8 TOCs, create 2 missing reference files, deduplicate Kanban format, and extract oversized SKILL.md content into reference files.

**Source Design Doc:** `docs/plans/2026-04-16-skill-audit-remediation-design.md`

**Mockups:** `docs/mockups/skill-audit-remediation.html` (analysis summary only — no UI work in this plan)

**Architecture:** Three sequential waves. Wave 1 (metadata, navigation, missing files) has many independent small edits. Wave 2 consolidates the shared Kanban entry template. Wave 3 extracts content out of three oversized SKILL.md files into new `references/` or `templates/` subdirectories. Each wave merges fully before the next begins.

**Tech Stack:** Markdown, YAML frontmatter, Bash, shell script, TypeScript example. No runtime code or tests — verification is structural (file exists, frontmatter parses, content matches anchors).

---

## Prerequisites

> Complete these steps manually before starting Task 1.

None. This plan runs autonomously against an existing git repo.

---

## Task Ordering Notes

Several tasks modify the same SKILL.md file. They MUST run in the order listed. Do not run them in parallel.

| File | Tasks (in required order) |
|------|---------------------------|
| `skills/add-advisor/SKILL.md` | Task 2 → Task 4 |
| `skills/add-framework/SKILL.md` | Task 5 (only) |
| `skills/brainstorming/modes/business.md` | Task 6 → Task 7 (TOC for business.md) |
| `skills/executing-plans/SKILL.md` | Task 1 (description) → Task 15 |
| `skills/finishing-a-development-branch/SKILL.md` | Task 16 → Task 25 |
| `skills/writing-plans/SKILL.md` | Task 1 (description) → Task 20 (extraction refs) |
| `skills/writing-plans/references/critique-panel-prompts.md` | Task 18 (create) → Task 20 (reference) |
| `skills/writing-plans/references/execution-handoff-templates.md` | Task 19 (create) → Task 20 (reference) |
| `skills/finishing-a-development-branch/references/mockup-fidelity-check.md` | Task 21 (create) → Task 25 (reference) |
| `skills/finishing-a-development-branch/references/deploy-smoke-test.md` | Task 22 (create) → Task 25 (reference + `cat`→Read fix) |
| `skills/finishing-a-development-branch/references/code-review-scan.md` | Task 23 (create) → Task 25 (reference) |
| `skills/finishing-a-development-branch/references/llm-eval-gate.md` | Task 24 (create) → Task 25 (reference) |
| `skills/kickstart/SKILL.md` | Task 3 (description) → Task 31 |
| `skills/_shared/kanban-entry-format.md` | Task 14 → Task 15 → Task 16 |

**Cross-wave ordering (strict):** Complete every Wave 1 task before starting Wave 2. Complete every Wave 2 task before starting Wave 3.

---

## Wave 1 — Metadata, Navigation, and Missing Files

### ✅ Task 1: Rewrite descriptions — core workflow skills (5 skills)

**Files:**
- Modify: `skills/use-advisor/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/use-framework/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/writing-plans/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/executing-plans/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/brainstorming/SKILL.md` (frontmatter `description:` field)

**Step 1: Verify each file exists and read current frontmatter**

Run Glob on each path. Read the first 5 lines of each to confirm the current `description:` text is what the design doc expects to replace.

**Step 2: Edit each `description:` field**

For each file, use Edit to replace only the `description:` line. Keep all other frontmatter keys (`name:`, etc.) untouched.

| File | New `description:` value |
|------|--------------------------|
| `skills/use-advisor/SKILL.md` | `Adopts an advisor's persona for the conversation. Use with an advisor name for fuzzy match, or alone to list available advisors. Triggers when a user mentions an advisor by name or asks to channel a specific expert's perspective.` |
| `skills/use-framework/SKILL.md` | `Guides a user through a decision framework's interactive phases, respecting WAIT points. Use with a framework name for fuzzy match, or alone to list available frameworks. Triggers when a user mentions a framework by name in any request.` |
| `skills/writing-plans/SKILL.md` | `Produces TDD implementation plans from specs or design docs, with parallel sub-agent critique and architectural review. Use when requirements are defined and the next step is a concrete, task-by-task build plan.` |
| `skills/executing-plans/SKILL.md` | `Executes written implementation plans with TDD discipline, batched task execution, and architecture verification. Use when a plan file exists in docs/plans/ and is ready for implementation.` |
| `skills/brainstorming/SKILL.md` | `Structures creative and strategic work through guided dialogue — software design or business strategy. Use before any creative, architectural, or strategic work that benefits from structured exploration and expert critique.` |

Wrap each new value in double quotes if it contains a colon (`:`). Most of these do — use double-quoted YAML strings to be safe.

**Step 3: Verify each frontmatter still parses**

Read the first 5 lines of each modified file. Confirm:
- The `---` delimiters are present at lines 1 and 4 (or 5, depending on quoting)
- `name:` line is unchanged
- `description:` contains the new text

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/use-advisor/SKILL.md skills/use-framework/SKILL.md skills/writing-plans/SKILL.md skills/executing-plans/SKILL.md skills/brainstorming/SKILL.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(skills): rewrite descriptions for 5 core workflow skills"
```

---

### ✅ Task 2: Rewrite descriptions — advisor/design skills and clean up add-advisor

**Files:**
- Modify: `skills/add-advisor/SKILL.md` (frontmatter `description:` field + remove Invocation section + remove editor note)
- Modify: `skills/create-design-principles/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/find-potential-advisors/SKILL.md` (frontmatter `description:` field)

**Step 1: Verify each file exists**

Run Glob on each path.

**Step 2: Edit each `description:` field**

| File | New `description:` value |
|------|--------------------------|
| `skills/add-advisor/SKILL.md` | `Adds a new advisor persona to the Virtual Board with system prompt, registry entry, and initial framework. Use when the user wants to add a new expert voice — either by naming a person or pointing to research in docs/advisors/.` |
| `skills/create-design-principles/SKILL.md` | `Interactive design system creation with Steve Jobs persona, producing design-principles.md with tokens, patterns, and anti-patterns. Use when building dashboards, admin interfaces, or any UI that needs a precise design direction.` |
| `skills/find-potential-advisors/SKILL.md` | `Researches and evaluates potential advisor candidates for the Virtual Board. Use when exploring a new domain or identifying experts before running add-advisor.` |

**Step 3: Remove the Invocation section from `skills/add-advisor/SKILL.md`**

Use Edit to delete the entire Invocation block. The block currently sits between the `# Add Advisor` heading and the `## Input` heading. Match the Invocation block using this exact `old_string`:

```
## Invocation

```
/aligned:add-advisor
"I want to add a new advisor based on Brene Brown"
```

## Input
```

Replace with:

```
## Input
```

**Step 4: Remove the editor note from `skills/add-advisor/SKILL.md`**

Use Edit to delete the editor-note blockquote. The blockquote sits between the environment detection summary and the `### 1. Load or Create Research` heading. Match using this `old_string`:

```
> **Editor note:** A parallel environment detection section exists in `skills/add-framework/SKILL.md` (Step 0). If you change the path-detection priority order here, apply the equivalent change there.

### 1. Load or Create Research
```

Replace with:

```
### 1. Load or Create Research
```

**Step 5: Verify all edits**

Read the full `skills/add-advisor/SKILL.md` file. Confirm:
- New `description:` is present
- No `## Invocation` heading exists
- No `> **Editor note:**` blockquote exists
- `# Add Advisor` is still present at line 6 (or near it)
- `## Input` still appears as a section

Read the first 5 lines of `skills/create-design-principles/SKILL.md` and `skills/find-potential-advisors/SKILL.md` — confirm new descriptions are present.

**Step 6: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/add-advisor/SKILL.md skills/create-design-principles/SKILL.md skills/find-potential-advisors/SKILL.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(skills): rewrite descriptions and clean up add-advisor"
```

---

### ✅ Task 3: Rewrite descriptions — utility skills (6 skills)

**Files:**
- Modify: `skills/kickstart/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/using-git-worktrees/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/create-image/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/codebase-audit/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/eval-audit/SKILL.md` (frontmatter `description:` field)
- Modify: `skills/kanban-resolve/SKILL.md` (frontmatter `description:` field)

**Step 1: Verify each file exists**

Glob each path.

**Step 2: Edit each `description:` field**

| File | New `description:` value |
|------|--------------------------|
| `skills/kickstart/SKILL.md` | `Scaffolds a new project with Aligned conventions, directory structure, and CLAUDE.md. Use when starting a new repo or adding Aligned structure to an existing codebase.` |
| `skills/using-git-worktrees/SKILL.md` | `Sets up isolated git worktrees for feature branches. Use when starting feature work that needs isolation from the current workspace or before executing implementation plans.` |
| `skills/create-image/SKILL.md` | `Generates hand-coded SVG diagrams, charts, flowcharts, and brand icons matching the project's design tokens. Use when a visual artifact is needed — charts, flowcharts, matrices, icons, or brand graphics.` |
| `skills/codebase-audit/SKILL.md` | `Comprehensive multi-dimensional codebase audit covering code quality, test quality, security, dead code, and architecture. Use when reviewing an unfamiliar codebase, before a major refactor, or as a periodic health check. Report-only — never edits source code.` |
| `skills/eval-audit/SKILL.md` | `Detects LLM behavior surface changes without eval coverage. Use when adding advisors, frameworks, or prompt logic to verify eval scenarios exist. Manual invocation only.` |
| `skills/kanban-resolve/SKILL.md` | `Triages and resolves all accumulated Kanban board items in a single automated pass. Use when the board has multiple pending items in docs/kanban/todo/ to process as a batch.` |

**Behavior change:** The new `create-image` description says "diagrams, charts, flowcharts, and brand icons" but omits the `illustration mode` that the current description mentions. This matches the design doc. Note this in the commit message so the change is intentional and not drift.

**Step 3: Verify frontmatter parses**

Read the first 5 lines of each modified file. Confirm `---` delimiters and `name:` key are intact.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/kickstart/SKILL.md skills/using-git-worktrees/SKILL.md skills/create-image/SKILL.md skills/codebase-audit/SKILL.md skills/eval-audit/SKILL.md skills/kanban-resolve/SKILL.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(skills): rewrite descriptions for 6 utility skills

Note: create-image description drops 'illustration mode' mention
intentionally per audit remediation design doc."
```

---

### ✅ Task 4: (merged into Task 2 — no separate commit needed)

Skipped. The add-advisor cleanup was bundled into Task 2 for atomic commit semantics. Proceed to Task 5.

---

### ✅ Task 5: Remove editor note from add-framework SKILL.md

**Files:**
- Modify: `skills/add-framework/SKILL.md` (the editor-note blockquote near the environment detection summary)

**Step 1: Read the current section**

Read `skills/add-framework/SKILL.md` to locate the editor-note blockquote. Verify the surrounding context — the blockquote sits between the environment-detection summary and the `### 1. Create Framework Folder` heading.

**Step 2: Remove the editor note**

Use Edit with:

```
old_string:
> **Editor note:** A parallel environment detection section exists in `skills/add-advisor/SKILL.md` (Step 0). If you change the path-detection priority order here, apply the equivalent change there.

### 1. Create Framework Folder

new_string:
### 1. Create Framework Folder
```

**Step 3: Verify**

Read the file. Confirm no `> **Editor note:**` blockquote exists and `### 1. Create Framework Folder` heading is still present.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/add-framework/SKILL.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(add-framework): remove cross-skill editor note"
```

---

### Task 6: Fix stale elements-of-style reference in brainstorming business mode

**Files:**
- Modify: `skills/brainstorming/modes/business.md` (the "Documentation:" bullet list under Phase 4)

**Step 1: Read the section**

Read `skills/brainstorming/modes/business.md`. Locate the bullet list containing `Use elements-of-style:writing-clearly-and-concisely skill if available` (this sits under a `**Documentation:**` subsection in Phase 4).

**Step 2: Remove the stale skill reference**

Use Edit. The reference line is one of several bullets. Since the adjacent Mockups bullet is a long multi-sentence paragraph, the whole next bullet must appear verbatim in `old_string` — quoting only the first clause will fail the Edit tool's exact-match requirement. Use these exact strings:

```
old_string:
- Use elements-of-style:writing-clearly-and-concisely skill if available
- After visualization artifacts are generated, add a `**Mockups:**` field to the design document header listing the mockup path (e.g., `**Mockups:** docs/mockups/{session-name}.html`). This field is consumed by writing-plans and finishing-a-development-branch to locate mockups without guessing. If no visual artifacts were generated, omit the field.

new_string:
- After visualization artifacts are generated, add a `**Mockups:**` field to the design document header listing the mockup path (e.g., `**Mockups:** docs/mockups/{session-name}.html`). This field is consumed by writing-plans and finishing-a-development-branch to locate mockups without guessing. If no visual artifacts were generated, omit the field.
```

Before running Edit, read the surrounding section to confirm the long `**Mockups:**` bullet is still phrased exactly as above. If the wording has shifted, update `old_string` to the current wording before applying the edit.

**Behavior change:** The Documentation checklist no longer instructs users to invoke a skill that does not exist. The removed bullet referenced `elements-of-style:writing-clearly-and-concisely`, a skill that was removed from this plugin. No replacement skill is introduced.

**Step 3: Verify**

Read the file. Grep for `elements-of-style` — must return no matches.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/brainstorming/modes/business.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(brainstorming): remove stale elements-of-style skill reference"
```

---

### Task 7: Add TOCs to brainstorming reference files (3 files)

**Files:**
- Modify: `skills/brainstorming/modes/software.md` (add `## Contents` after first H1)
- Modify: `skills/brainstorming/modes/business.md` (add `## Contents` after first H1)
- Modify: `skills/brainstorming/references/brainstorm-components.md` (add `## Contents` after first H1)

**Step 1: Read each file's H2 headings**

For each file, use Grep with pattern `^## ` and output_mode `content` to enumerate its existing H2 section list.

**Step 2: Insert `## Contents` block after the H1 in each file**

Use Edit on each file. Match the H1 and the first blank line after it. Insert the `## Contents` block between the H1 and the existing first section.

**Do not pre-fill the bullet list from memory or from this plan.** Always derive it from the actual Grep output in Step 1 — heading text drifts between writes. Example template for `skills/brainstorming/modes/software.md`:

```
old_string:
# Brainstorming Ideas Into Designs

## {{first-H2-title}}

new_string:
# Brainstorming Ideas Into Designs

## Contents

- {{first-H2-title}}
- {{second-H2-title}}
- ... (one bullet per H2 returned by Step 1 Grep, in file order)

## {{first-H2-title}}
```

Repeat for `business.md` and `brainstorm-components.md`, using each file's Step 1 Grep output as the bullet content.

**Step 3: Verify**

Read each file. Confirm:
- `## Contents` is the first section after the H1
- Every H2 that appears later in the file is present as a bullet
- No H2 that doesn't exist is listed

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/brainstorming/modes/software.md skills/brainstorming/modes/business.md skills/brainstorming/references/brainstorm-components.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(brainstorming): add TOCs to mode and reference files"
```

---

### Task 8: Add TOCs to persona-panel reference files (2 files)

**Files:**
- Modify: `skills/persona-panel/references/aggregation-prompt.md`
- Modify: `skills/persona-panel/modes/persona-creation-flow.md`

**Step 1: Read each file's H2 headings**

Grep each file for `^## ` headings.

**Step 2: Insert `## Contents` block after the H1**

Use the same pattern as Task 7 — derive the bullet list from the Step 1 Grep output, not from memory. Each of these files has a non-trivial number of H2s (aggregation-prompt.md has 10 H2s; persona-creation-flow.md has 6+). Enumerate every H2 returned by Grep as a bullet in file order.

Template:

```
old_string:
# {{file H1}}

## {{first-H2-title}}

new_string:
# {{file H1}}

## Contents

- {{first-H2-title}}
- {{second-H2-title}}
- ... (one bullet per H2 returned by Step 1 Grep, in file order)

## {{first-H2-title}}
```

Apply this pattern to both `aggregation-prompt.md` and `persona-creation-flow.md` separately.

**Step 3: Verify**

Read each file. Confirm `## Contents` section appears immediately after the H1 and all listed bullets match existing H2 headings.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/persona-panel/references/aggregation-prompt.md skills/persona-panel/modes/persona-creation-flow.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(persona-panel): add TOCs to reference and mode files"
```

---

### Task 9: Add TOC to writing-plans critique checklist

**Files:**
- Modify: `skills/writing-plans/plan-critique-checklist.md`

**Step 1: Read the file's H2 headings**

Grep for `^## ` in `skills/writing-plans/plan-critique-checklist.md`. At the time of plan writing, the file contains 7 H2s (e.g., `Instructions`, `Critique Criteria`, `Critique Output Format`, `Summary`, `Issues`, `Checklist Results`, `Important`). Derive the actual bullet list from the Grep output at execution time — do not copy the above list blindly; it may drift.

Note: The `Summary`, `Issues`, and `Checklist Results` H2s appear inside a fenced markdown code block that illustrates the critique output format. Grep for `^## ` will include them. Keep them in the TOC — readers scanning the TOC still benefit from knowing the output format fields are documented.

**Step 2: Insert `## Contents` after the H1**

Use Edit to insert a `## Contents` block between the H1 and the first paragraph. Template:

```
old_string:
# Plan Critique Checklist

You are a plan reviewer. Your job is to find issues in implementation plans by verifying every claim against actual source code. You are skeptical, thorough, and evidence-driven. You do not manufacture issues — if something checks out, say Pass.

new_string:
# Plan Critique Checklist

## Contents

- {{bullets derived from Step 1 Grep, one per H2 in file order}}

You are a plan reviewer. Your job is to find issues in implementation plans by verifying every claim against actual source code. You are skeptical, thorough, and evidence-driven. You do not manufacture issues — if something checks out, say Pass.
```

**Step 3: Verify**

Read the file. Confirm the Contents section is directly below the H1 and all bullets match actual H2s found by Grep.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/writing-plans/plan-critique-checklist.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(writing-plans): add TOC to plan-critique-checklist"
```

---

### Task 10: Add TOC to create-design-principles checklist

**Files:**
- Modify: `skills/create-design-principles/design-critique-checklist.md`

**Step 1: Read the full file's H2 headings**

Grep `^## ` in `skills/create-design-principles/design-critique-checklist.md`.

**Step 2: Insert `## Contents` after the H1**

Use Edit to insert a `## Contents` block immediately after the `# Design Critique Checklist` H1. List every H2 discovered in Step 1 as a bullet.

**Step 3: Verify**

Read the file. Confirm Contents is right after H1 and bullets match real H2s.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/create-design-principles/design-critique-checklist.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(create-design-principles): add TOC to design-critique-checklist"
```

---

### Task 11: Add TOC to deployment pitfall catalog

**Files:**
- Modify: `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md`

**Step 1: Read the file's H2 headings**

Grep `^## ` in the catalog. At plan-writing time the file contained 6 H2s: `How to Use This Catalog`, `CRITICAL — Silent Production Failures`, `HIGH — Data/Performance Issues`, `MEDIUM — Potential Issues Under Load`, `LOW — Best Practice Recommendations`, `Maintenance`. (The individual pitfall entries — `C1:`, `C2:`, etc. — are H3s, not H2s, and should not appear in the TOC.) Derive the actual bullet list from the Step 1 Grep output at execution time.

**Step 2: Insert `## Contents` after the H1**

Use Edit. Insert a Contents section listing every H2 in the file.

**Step 3: Verify**

Read the file. Confirm every listed bullet matches an H2 that appears later in the file.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(finishing-a-development-branch): add TOC to deployment-pitfall-catalog"
```

---

### Task 12: Create find-polluter.sh

**Files:**
- Create: `skills/root-cause-analysis/find-polluter.sh`

**Step 1: Read the referencing document**

Read `skills/root-cause-analysis/root-cause-tracing.md` — locate the "Use the bisection script `find-polluter.sh`" section (around line 101). Verify the expected interface:

```bash
./find-polluter.sh '.git' 'src/**/*.test.ts'
```

Argument 1 is a sentinel (something the polluter is suspected of leaving behind). Argument 2 is a test glob. The script runs tests one-by-one and stops at the first test that produces the sentinel.

**Step 2: Create the script**

Write `skills/root-cause-analysis/find-polluter.sh`:

```bash
#!/usr/bin/env bash
#
# find-polluter.sh — Bisect a test suite to identify the test that pollutes
# shared state. Usage:
#
#   ./find-polluter.sh '<sentinel>' '<test-glob>'
#
# sentinel:  A string/path the polluter creates or modifies (e.g., '.git',
#            '/tmp/flag', 'cache-file'). The script checks for this sentinel
#            after each test run.
# test-glob: A glob matching the test files to bisect (e.g.,
#            'src/**/*.test.ts').
#
# The script iterates tests one at a time. After each test, it checks whether
# the sentinel exists. The first test after which the sentinel appears is the
# polluter.
#
# Intended to be run from a project root that has a test command. Set the
# TEST_CMD env var to override the default (which assumes `npm test`). The
# test command receives the current test file path as its final argument.

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 '<sentinel>' '<test-glob>'" >&2
  exit 2
fi

sentinel="$1"
glob="$2"
test_cmd="${TEST_CMD:-npm test --}"

# Collect files matching the glob (Bash 4+ globstar).
shopt -s globstar nullglob
# shellcheck disable=SC2206
files=( $glob )
shopt -u globstar nullglob

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No files matched glob: $glob" >&2
  exit 1
fi

echo "Bisecting ${#files[@]} test files for polluter that creates: $sentinel"

# Ensure the sentinel is absent before we start.
if [[ -e "$sentinel" ]]; then
  echo "Sentinel '$sentinel' already exists before any test ran. Remove it first." >&2
  exit 1
fi

for f in "${files[@]}"; do
  echo "-- Running: $f"
  $test_cmd "$f" >/dev/null 2>&1 || true

  if [[ -e "$sentinel" ]]; then
    echo ""
    echo "POLLUTER FOUND: $f"
    echo "Sentinel '$sentinel' appeared after this test."
    exit 0
  fi
done

echo ""
echo "No polluter found. Sentinel '$sentinel' was not produced by any test."
exit 0
```

**Step 3: Make the script executable**

```bash
chmod +x /Users/ericpage/software/aligned_cc_skills/skills/root-cause-analysis/find-polluter.sh
```

**Step 4: Verify it exists and is executable**

Run:

```bash
ls -l /Users/ericpage/software/aligned_cc_skills/skills/root-cause-analysis/find-polluter.sh
```

Expect the file to exist with `-rwxr-xr-x` (or similar executable permission) and a non-zero size.

Confirm the file's existence is detected by Glob (`skills/root-cause-analysis/find-polluter.sh`).

**Step 5: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/root-cause-analysis/find-polluter.sh
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(root-cause-analysis): add find-polluter.sh bisection script"
```

---

### Task 13: Create condition-based-waiting-example.ts

**Files:**
- Create: `skills/root-cause-analysis/condition-based-waiting-example.ts`

**Step 1: Read the referencing document**

Read `skills/root-cause-analysis/condition-based-waiting.md`. The reference around line 82 describes domain-specific helpers: `waitForEvent`, `waitForEventCount`, `waitForEventMatch`.

**Step 2: Create the TypeScript example**

Write `skills/root-cause-analysis/condition-based-waiting-example.ts`:

```typescript
// condition-based-waiting-example.ts
//
// Domain-specific helpers for condition-based waiting in event-driven test
// suites. Use these instead of fixed-duration sleeps. Each helper polls a
// predicate until it is satisfied or a deadline passes.
//
// Why not `await new Promise(r => setTimeout(r, N))`? Fixed sleeps are always
// wrong. Too short, the test is flaky; too long, the suite is slow. Poll the
// actual condition instead.

type EventRecord = {
  type: string
  payload: Record<string, unknown>
  timestamp: number
}

type WaitOptions = {
  timeoutMs?: number
  intervalMs?: number
}

const DEFAULT_TIMEOUT_MS = 5000
const DEFAULT_INTERVAL_MS = 25

async function poll<T>(
  predicate: () => T | null | undefined,
  timeoutMs: number,
  intervalMs: number,
  description: string,
): Promise<T> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const result = predicate()
    if (result !== null && result !== undefined) {
      return result
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }
  throw new Error(`Timed out after ${timeoutMs}ms waiting for: ${description}`)
}

// Wait until at least one event of the given type has been recorded.
export async function waitForEvent(
  events: EventRecord[],
  type: string,
  options: WaitOptions = {},
): Promise<EventRecord> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
  return poll(
    () => events.find((e) => e.type === type),
    timeoutMs,
    intervalMs,
    `event of type "${type}"`,
  )
}

// Wait until at least `count` events of the given type have been recorded.
export async function waitForEventCount(
  events: EventRecord[],
  type: string,
  count: number,
  options: WaitOptions = {},
): Promise<EventRecord[]> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
  return poll(
    () => {
      const matches = events.filter((e) => e.type === type)
      return matches.length >= count ? matches : null
    },
    timeoutMs,
    intervalMs,
    `${count} events of type "${type}"`,
  )
}

// Wait until at least one event matches a custom predicate.
export async function waitForEventMatch(
  events: EventRecord[],
  match: (event: EventRecord) => boolean,
  description: string,
  options: WaitOptions = {},
): Promise<EventRecord> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
  return poll(
    () => events.find(match),
    timeoutMs,
    intervalMs,
    `event matching "${description}"`,
  )
}
```

**Step 3: Verify the file exists**

Glob `skills/root-cause-analysis/condition-based-waiting-example.ts`. Confirm match.

Read the first 10 lines. Confirm the header comment is present and exports are declared.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/root-cause-analysis/condition-based-waiting-example.ts
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(root-cause-analysis): add condition-based-waiting TypeScript example"
```

---

## Wave 2 — Kanban Format Deduplication

Wave 1 must be fully committed to main before starting Wave 2.

### Task 14: Add CRITICAL severity option to shared Kanban entry format

**Files:**
- Modify: `skills/_shared/kanban-entry-format.md`

**Why:** The inline Kanban template in `executing-plans/SKILL.md` currently specifies `CRITICAL | HIGH | MEDIUM | LOW`. The shared template uses only `LOW | MEDIUM | HIGH`. Adding CRITICAL to the shared template is a prerequisite for Task 15 — otherwise removing the inline template would lose the CRITICAL option.

**Step 1: Read the shared file**

Read `skills/_shared/kanban-entry-format.md`.

**Step 2: Update the severity line**

Use Edit:

```
old_string:
- **Severity:** LOW | MEDIUM | HIGH

new_string:
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW
```

**Behavior change:** Any future Kanban entry written by any skill can now mark its severity as CRITICAL. This matches what `executing-plans` already allows inline; downstream skills that file KB entries (`finishing-a-development-branch`, `root-cause-analysis`, `writing-plans`) will also accept CRITICAL. This is a widening, not a narrowing — no existing entries break.

**Step 3: Verify**

Read the file. Confirm the Severity line contains all four levels in descending order.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/_shared/kanban-entry-format.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(_shared): add CRITICAL severity to Kanban entry template"
```

---

### Task 15: Remove inline Kanban entry template from executing-plans

**Files:**
- Modify: `skills/executing-plans/SKILL.md` (remove the inline template; keep the `_shared/` reference)

**Step 1: Read the current state**

Read `skills/executing-plans/SKILL.md`. The "Bug Discovery During Execution" section currently contains both the inline template (under the "Log it" bullet) AND a reference to `{base-directory}/../_shared/kanban-entry-format.md` further down in its own "Kanban Entry Format" H2 section.

**Step 2: Replace the inline template with a reference**

Use Edit:

```
old_string:
2. **Don't stop** — this isn't a blocker for the current work
3. **Log it** to the Kanban board:

Read `docs/kanban/.counter` for the next KB number (pad to 3 digits). Derive a kebab-case slug from the description (max 50 chars). Write `docs/kanban/todo/KB-NNN-slug.md`:

```markdown
# KB-NNN: [Short description]

- **Type:** bug
- **Discovered during:** [plan filename / Task N]
- **Location:** `src/path/to/file.ts:NN`
- **Observed:** [What you saw — be specific enough for a fresh session to reproduce]
- **Expected:** [What should happen instead]
- **Why out of scope:** [Why this isn't part of the current task]
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW
- **Created:** [today's date]
```

Write the incremented number back to `docs/kanban/.counter`.

4. **Continue** with the current task

new_string:
2. **Don't stop** — this isn't a blocker for the current work
3. **Log it** to the Kanban board (see the Kanban Entry Format section below for the template and counter instructions — use `[plan filename / Task N]` as the "Discovered during" value)
4. **Continue** with the current task
```

**Step 3: Verify**

Read the file. Confirm:
- No inline `# KB-NNN: [Short description]` template remains in the Bug Discovery section
- The `## Kanban Entry Format` section that references `{base-directory}/../_shared/kanban-entry-format.md` is still present and unchanged
- The "Discovered during" guidance (`[plan filename / Task N]`) is preserved — it appears in both the new inline bullet and the existing Kanban Entry Format section

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/executing-plans/SKILL.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(executing-plans): deduplicate inline Kanban template"
```

---

### Task 16: Remove duplicate Kanban Entry Format section from finishing-a-development-branch

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md` (remove the duplicate `## Kanban Entry Format` H2 section near end of file; keep the Step 1e reference in the body)

**Step 1: Read the current state**

Read `skills/finishing-a-development-branch/SKILL.md`. There are two references to the shared Kanban format:
- Inside Step 1e (Code Simplification Scan): "Read `{base-directory}/../_shared/kanban-entry-format.md` for the KB template..."
- A standalone `## Kanban Entry Format` H2 section later in the document: `When filing a Kanban entry, read ...`

**Step 2: Remove the duplicate standalone section**

Use Edit:

```
old_string:
## Kanban Entry Format

When filing a Kanban entry, read `{base-directory}/../_shared/kanban-entry-format.md` for the template and counter instructions (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load). Use `finishing-a-development-branch` as the "Discovered during" value.

## Integration

new_string:
## Integration
```

**Step 3: Update the Step 1e reference to include the "Discovered during" guidance**

The removed standalone section carried a specific instruction: "Use `finishing-a-development-branch` as the 'Discovered during' value." That guidance must be preserved in the only remaining reference so it is not lost.

Read the Step 1e block. Use Edit to insert the "Discovered during" guidance at the end of the numbered-list item that reads "Read `{base-directory}/../_shared/kanban-entry-format.md`..." — but only if the guidance is not already present in that block. If the block already specifies the `Discovered during` value (`finishing-a-development-branch (code-simplifier)`), leave it unchanged.

If the existing Step 1e text already specifies a more specific "Discovered during" value (e.g., `finishing-a-development-branch (code-simplifier)`), that is preferred — do not downgrade it to the generic value. Simply confirm the value is specified somewhere within Step 1e.

**Step 4: Verify**

Read the file. Confirm:
- No standalone `## Kanban Entry Format` H2 section exists
- `## Integration` H2 still exists
- Step 1e still references `{base-directory}/../_shared/kanban-entry-format.md`
- A `"Discovered during"` value is specified within Step 1e (either `finishing-a-development-branch` or a more specific variant such as `finishing-a-development-branch (code-simplifier)`)

**Step 5: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/finishing-a-development-branch/SKILL.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(finishing-a-development-branch): deduplicate Kanban Entry Format section"
```

---

### Task 17: Verify root-cause-analysis Kanban reference is consistent

**Files:**
- Inspect (no modification expected): `skills/root-cause-analysis/SKILL.md`

**Step 1: Read the existing reference**

Read the `## Kanban Entry Format` section in `skills/root-cause-analysis/SKILL.md`.

**Step 2: Compare phrasing with other skills**

Grep for `{base-directory}/../_shared/kanban-entry-format.md` in `skills/executing-plans/SKILL.md`, `skills/writing-plans/SKILL.md`, and `skills/finishing-a-development-branch/SKILL.md`. Read the surrounding sentence in each.

**Step 3: Decide**

- If the root-cause-analysis phrasing already matches one of the sibling skills' phrasing exactly, stop. No change needed. Report "root-cause-analysis already consistent; no edit made."
- If it differs in a way that creates inconsistency (e.g., different wording order, missing `"Discovered during"` guidance), use Edit to bring it in line with the majority pattern: `When filing a Kanban entry, read \`{base-directory}/../_shared/kanban-entry-format.md\` for the template and counter instructions (resolve \`{base-directory}\` from the "Base directory for this skill:" line printed at skill load). Use \`root-cause-analysis\` as the "Discovered during" value.`

**Step 4: Commit (only if a change was made)**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/root-cause-analysis/SKILL.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(root-cause-analysis): normalize Kanban format reference"
```

If no change was made, skip the commit step.

---

## Wave 3 — File Extractions

Wave 2 must be fully committed to main before starting Wave 3.

### Task 18: Extract writing-plans critique panel prompts

**Files:**
- Create: `skills/writing-plans/references/critique-panel-prompts.md`

**Step 1: Ensure the `references/` directory exists**

Run:

```bash
mkdir -p /Users/ericpage/software/aligned_cc_skills/skills/writing-plans/references
```

**Step 2: Read the source section in writing-plans SKILL.md**

Read `skills/writing-plans/SKILL.md`. Locate the "Fact-Check + Critique Panel (mandatory, 2 parallel technical critics)" H2 section. The content to extract is every sub-section from that H2 down to (but not including) the next H2 — specifically, the Round 1 Critic 1 prompt, the Round 1 Critic 2 prompt, the aggregation agent prompt, and the Round 2 sub-agent prompts.

**Step 3: Write the extracted file**

Write `skills/writing-plans/references/critique-panel-prompts.md`. Start with a header that identifies the file and its purpose, then append each extracted sub-section verbatim:

```markdown
# Plan Critique Panel — Sub-Agent Prompt Templates

This file contains the full prompt templates for the two technical critics (The Architect, The Verifier) and the aggregation agent used by the writing-plans skill's critique panel.

## Contents

- Round 1: Architect prompt
- Round 1: Verifier prompt
- Round 1: Aggregation prompt
- Round 2: Architect prompt
- Round 2: Verifier prompt

## Round 1: Architect prompt

<!-- Verbatim copy of the current Critic 1 — The Architect prompt -->
<existing prompt text>

## Round 1: Verifier prompt

<!-- Verbatim copy of the current Critic 2 — The Verifier prompt -->
<existing prompt text>

## Round 1: Aggregation prompt

<!-- Verbatim copy of the aggregation agent prompt -->
<existing prompt text>

## Round 2: Architect prompt

<!-- Verbatim copy of the Round 2 Architect prompt -->
<existing prompt text>

## Round 2: Verifier prompt

<!-- Verbatim copy of the Round 2 Verifier prompt -->
<existing prompt text>
```

When filling in `<existing prompt text>`, copy verbatim from the current SKILL.md — preserve every word, placeholder (`{checklist-path}`, `{plan-file-path}`, `{report-path}`, `{summary-of-changes}`, etc.), and markdown formatting.

**Step 4: Verify**

Read the new file. Confirm:
- H1 and `## Contents` are present
- All five prompt sections are populated
- Placeholders like `{checklist-path}` and `{plan-file-path}` are intact

**Step 5: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/writing-plans/references/critique-panel-prompts.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(writing-plans): extract critique panel prompts to references/"
```

---

### Task 19: Extract writing-plans execution handoff templates

**Files:**
- Create: `skills/writing-plans/references/execution-handoff-templates.md`

**Step 1: Read the source section**

Read the `## Execution Handoff` H2 section in `skills/writing-plans/SKILL.md`. Content to extract: the two option templates (Option A Interactive, Option B Ralph loop) plus the "When worktree path is unknown" sub-section. The verification gate and recommendation heuristics stay inline in SKILL.md — they are decision logic, not user-facing templates.

**Step 2: Write the extracted file**

Write `skills/writing-plans/references/execution-handoff-templates.md`:

```markdown
# Plan Execution Handoff — Output Templates

This file contains the user-facing message templates that writing-plans outputs after saving a plan. The writing-plans SKILL.md uses its own logic to pick between Option A and Option B, then substitutes `{worktree-path}`, `{plan-file-path}`, `{feature-name}`, and `{plugin-root}` before presenting the selected option.

## Contents

- Standard handoff (worktree path known)
- Worktree-not-created handoff (worktree path unknown)

## Standard handoff (worktree path known)

<!-- Verbatim copy of the current ### Option A / ### Option B templates from SKILL.md's "Next Steps" block, including the "After execution completes" trailer -->
<existing text>

## Worktree-not-created handoff (worktree path unknown)

<!-- Verbatim copy of the current "When worktree path is unknown" sub-section -->
<existing text>
```

Fill `<existing text>` with verbatim content from SKILL.md. Preserve every placeholder (`{worktree-path}`, `{plan-file-path}`, `{feature-name}`, `{plugin-root}`, `YYYY-MM-DD-<feature-name>`) and markdown code fence exactly.

**Step 3: Verify**

Read the new file. Confirm both handoff templates are present and placeholders are intact.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/writing-plans/references/execution-handoff-templates.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(writing-plans): extract execution handoff templates to references/"
```

---

### Task 20: Update writing-plans SKILL.md to reference extracted files

**Files:**
- Modify: `skills/writing-plans/SKILL.md` (replace extracted sections with references)

**Step 1: Replace the critique panel prompts with a reference**

In the `## Fact-Check + Critique Panel` section, keep the narrative structure (Round 1 / Round 2 headings and the orchestration steps). Remove the verbatim prompt strings and point to the extracted file.

Replace each occurrence of a full prompt quotation block with a bullet of the form:

```
**Critic 1 — The Architect:** See `references/critique-panel-prompts.md` — section "Round 1: Architect prompt". Resolve `{base-directory}` using the "Base directory for this skill:" line printed when the skill loads, then read that reference file. Substitute `{plan-file-path}`, `{checklist-path}`, and `{report-path}` as described above before launching the sub-agent.
```

Apply the same pattern to: Round 1 Verifier, Round 1 Aggregation, Round 2 Architect, Round 2 Verifier.

**Step 2: Replace the execution handoff templates with a reference**

Rewrite the `## Execution Handoff` section's Next Steps block so that instead of embedding the full Option A / Option B template text, it directs the reader to `references/execution-handoff-templates.md`. Keep inline: the `{plugin-root}` resolution, the recommendation heuristics, the verification gate, and the substitution instructions.

**Step 3: Verify line count shrank**

Use Grep with output_mode `count` (pattern `.` to count every non-empty line, or `^` to include blank lines) to count lines in `skills/writing-plans/SKILL.md`. Target is ~395 lines (down from 596). If the count is over 440 lines, treat as extraction failure — re-check whether both extraction targets (critique panel prompts AND execution handoff templates) were actually replaced with pointers.

**Step 4: Verify references resolve**

Read `skills/writing-plans/references/critique-panel-prompts.md` and `skills/writing-plans/references/execution-handoff-templates.md` — both must exist and contain the extracted content. Grep SKILL.md for the bare filenames (`critique-panel-prompts.md`, `execution-handoff-templates.md`) — every reference path must include `references/` as its subdirectory.

**Step 5: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/writing-plans/SKILL.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "refactor(writing-plans): move critique prompts and handoff templates to references/"
```

---

### Task 21: Extract mockup fidelity check workflow

**Files:**
- Create: `skills/finishing-a-development-branch/references/mockup-fidelity-check.md`

**Step 1: Read the source sections**

Read `skills/finishing-a-development-branch/SKILL.md`. Locate:
- `### Step 1f: Mockup Fidelity Check`
- `### Step 1g: Fix Mockup Deviations (user-directed)` and its sub-steps (`Step 1g-i: Root-cause diagnosis`, `Step 1g-ii: Synthesize and fix`, `Step 1g-iii: Re-verify`)

**Step 2: Write the extracted file**

Write `skills/finishing-a-development-branch/references/mockup-fidelity-check.md`:

```markdown
# Mockup Fidelity Check — Workflow Reference

Extracted from finishing-a-development-branch SKILL.md to keep that file under 500 lines. This workflow detects UI drift between mockups and implementation, then guides a user-directed fix cycle.

## Contents

- Step 1f: Mockup Fidelity Check
- Step 1g: Fix Mockup Deviations (user-directed)
  - Step 1g-i: Root-cause diagnosis
  - Step 1g-ii: Synthesize and fix
  - Step 1g-iii: Re-verify

<verbatim content>
```

Paste the current Step 1f and Step 1g content verbatim into `<verbatim content>`. Preserve every code block, placeholder, and sub-step heading.

**Step 3: Verify**

Read the new file. Confirm H1, Contents, and all extracted sub-sections are present.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/finishing-a-development-branch/references/mockup-fidelity-check.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(finishing-a-development-branch): extract mockup fidelity check to references/"
```

---

### Task 22: Extract deploy smoke test workflow

**Files:**
- Create: `skills/finishing-a-development-branch/references/deploy-smoke-test.md`

**Step 1: Read the source section**

Read `skills/finishing-a-development-branch/SKILL.md`. Locate `#### Option 2: Deploy to Production + Smoke Test` and its numbered sub-steps (`Step 4a` through `Step 4f`).

**Step 2: Write the extracted file**

Write `skills/finishing-a-development-branch/references/deploy-smoke-test.md`:

```markdown
# Deploy to Production + Smoke Test — Workflow Reference

Extracted from finishing-a-development-branch SKILL.md. Invoked from Step 4 Option 2.

## Contents

- Step 4a: Pre-deploy checks
- Step 4b: Read vercel project config
- Step 4c: Trigger deploy
- Step 4d: Verify build logs
- Step 4e: Smoke test against deployed URL
- Step 4f: Announce success

<verbatim content>
```

(The actual step headings in the source may differ — match them exactly as they appear in SKILL.md.)

Paste the current Option 2 content verbatim under `<verbatim content>`.

**Step 3: Verify**

Read the new file. Confirm every Step 4a/b/c/d/e/f (or the actual heading set) is present.

Grep the new file for `cat <main-repo-path>/.vercel/project.json` with `output_mode=count` — it MUST return exactly `1`. Task 25 Step 3 depends on this `cat` line being preserved verbatim so it can replace it with a Read-tool instruction. If the count is 0, the verbatim copy was paraphrased — re-extract before proceeding.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/finishing-a-development-branch/references/deploy-smoke-test.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(finishing-a-development-branch): extract deploy smoke test to references/"
```

---

### Task 23: Extract code review + simplification scan workflow

**Files:**
- Create: `skills/finishing-a-development-branch/references/code-review-scan.md`

**Step 1: Read the source sections**

Read `skills/finishing-a-development-branch/SKILL.md`. Locate `### Step 1d: Code Review` and `### Step 1e: Code Simplification Scan`.

**Step 2: Write the extracted file**

Write `skills/finishing-a-development-branch/references/code-review-scan.md`:

```markdown
# Code Review + Simplification Scan — Workflow Reference

Extracted from finishing-a-development-branch SKILL.md. Orchestrates the code-reviewer and code-simplifier sub-agents before merge.

## Contents

- Step 1d: Code Review
- Step 1e: Code Simplification Scan

<verbatim content>
```

Paste current Step 1d and Step 1e content verbatim.

**Step 3: Verify**

Read the new file. Confirm both steps are present and intact, including any sub-agent prompt text.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/finishing-a-development-branch/references/code-review-scan.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(finishing-a-development-branch): extract code review scan to references/"
```

---

### Task 24: Extract LLM eval gate workflow

**Files:**
- Create: `skills/finishing-a-development-branch/references/llm-eval-gate.md`

**Step 1: Read the source section**

Read `skills/finishing-a-development-branch/SKILL.md`. Locate `### Step 1b: LLM Eval (auto-run if surface changed)` and all its numbered sub-steps (1-6+).

**Step 2: Write the extracted file**

Write `skills/finishing-a-development-branch/references/llm-eval-gate.md`:

```markdown
# LLM Eval Gate — Workflow Reference

Extracted from finishing-a-development-branch SKILL.md. Runs the eval suite when the changed files touch any surface pattern defined in `e2e/eval-surface.yaml`.

## Contents

- Step 1b: LLM Eval (auto-run if surface changed)
  - Surface-pattern matching rules
  - Scenario scoping via trigger-map.yaml
  - Coverage summary
  - Scoped eval execution

<verbatim content>
```

Paste the current Step 1b content verbatim, including the pattern-matching rules and trigger-map logic.

**Step 3: Verify**

Read the new file. Confirm all numbered sub-steps of Step 1b are present.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/finishing-a-development-branch/references/llm-eval-gate.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(finishing-a-development-branch): extract LLM eval gate to references/"
```

---

### Task 25: Update finishing-a-development-branch SKILL.md — reference extracted files and clean up

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Replace extracted sections with pointers**

For each of Step 1b, Step 1d, Step 1e, Step 1f, Step 1g, and Option 2 (Deploy), replace the full section body with a short pointer block. Keep the H3 heading so the overall flow remains readable. Example replacement for Step 1f:

```markdown
### Step 1f: Mockup Fidelity Check

See `references/mockup-fidelity-check.md` for the full workflow. Resolve `{base-directory}` using the "Base directory for this skill:" line printed when the skill loads, then read the referenced file. Summary:

- Detect mockup drift against implementation in `docs/mockups/{session}/`
- Produce a drift report per mockup element
- If drift is found, proceed to Step 1g (user-directed fix cycle)
```

Apply the same pattern to each extracted section. Each pointer should summarize in 2-4 bullets what the reference file covers so a reader skimming SKILL.md can understand the flow without opening the reference.

**Step 2: Remove meta-commentary**

Locate the "Behavior change" blockquote in Step 1b (the paragraph that starts `> **Behavior change:** The old Step 1b was vague about pattern matching...`). This commentary is authoring notes, not part of the runtime workflow. If Step 1b is fully extracted to `references/llm-eval-gate.md`, the meta-commentary should move to the reference file (preserving it for context) OR be removed entirely if it no longer applies. Decision: move it into `references/llm-eval-gate.md` as a `## Notes` section at the bottom, then delete it from SKILL.md.

Actually, since Step 1b's body is extracted, this commentary already moved to the reference file in Task 24. Verify by reading `references/llm-eval-gate.md` — if the commentary block is present, this sub-step is done. If not, add a `## Notes` section at the end of that reference file containing the commentary, commit it separately as part of this task.

**Step 3: Replace `cat` with Read tool guidance**

Locate Path A in Step 4 Option 2 where the workflow currently reads `.vercel/project.json` via `cat`. Since Step 4 Option 2 is now extracted to `references/deploy-smoke-test.md`, this change must be applied inside that reference file — not SKILL.md.

Open `skills/finishing-a-development-branch/references/deploy-smoke-test.md`. Find the `cat <main-repo-path>/.vercel/project.json` block. Use Edit to replace the Bash command with a Read-tool instruction:

```
old_string:
Read `.vercel/project.json` from the main repo path to get `projectId` and `orgId`:

```bash
cat <main-repo-path>/.vercel/project.json
```

new_string:
Read `.vercel/project.json` from the main repo path using the Read tool (absolute path: `<main-repo-path>/.vercel/project.json`) to get `projectId` and `orgId`.
```

**Behavior change:** Replaces a Bash `cat` command with the Read tool. Rationale: the project CLAUDE.md prohibits using Bash for file reads (`Bash Tool Restrictions` section). This change brings the workflow into compliance. No output format change — both approaches return the JSON content.

**Step 4: Verify SKILL.md line count shrank**

Use Grep `output_mode=count` (pattern `^`) on `skills/finishing-a-development-branch/SKILL.md`. Target ~430 lines (down from 834). If the count is over 500 lines, treat as extraction failure — check which of Steps 1b / 1d / 1e / 1f / 1g / Option 2 are still inline and complete the replacement.

**Step 5: Verify references resolve**

Read every new references file:
- `skills/finishing-a-development-branch/references/mockup-fidelity-check.md`
- `skills/finishing-a-development-branch/references/deploy-smoke-test.md`
- `skills/finishing-a-development-branch/references/code-review-scan.md`
- `skills/finishing-a-development-branch/references/llm-eval-gate.md`

Grep SKILL.md for each filename — confirm every mention includes the `references/` prefix. Grep SKILL.md for `cat <main-repo-path>` — must return no matches.

**Step 6: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/finishing-a-development-branch/SKILL.md skills/finishing-a-development-branch/references/deploy-smoke-test.md skills/finishing-a-development-branch/references/llm-eval-gate.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "refactor(finishing-a-development-branch): replace extracted sections with references and fix cat usage"
```

---

### Task 26: Extract kickstart software CLAUDE.md template

**Files:**
- Create: `skills/kickstart/templates/software.md`

**Step 1: Ensure the `templates/` directory exists**

```bash
mkdir -p /Users/ericpage/software/aligned_cc_skills/skills/kickstart/templates
```

**Step 2: Read the source section**

Read `skills/kickstart/SKILL.md`. Locate `### Software Template` under `## Phase 4: Seed CLAUDE.md`. Capture all 6 sections (Project Identity, Folder Map, Reading Priority, Communication Preferences, Guardrails, Workflows).

**Step 3: Write the extracted file**

Write `skills/kickstart/templates/software.md`:

```markdown
# Software Project CLAUDE.md Template

Template for software projects (code, tests, builds). Referenced by `skills/kickstart/SKILL.md` Phase 4.

## Contents

- Section 1: Project Identity
- Section 2: Folder Map
- Section 3: Reading Priority
- Section 4: Communication Preferences
- Section 5: Guardrails
- Section 6: Workflows

## Section 1 — Project Identity

<verbatim content from SKILL.md Phase 4 Software Template Section 1>

## Section 2 — Folder Map

<verbatim content>

## Section 3 — Reading Priority

<verbatim content>

## Section 4 — Communication Preferences

<verbatim content>

## Section 5 — Guardrails (Iron Rules)

<verbatim content>

## Section 6 — Workflows

<verbatim content>
```

Fill each `<verbatim content>` block exactly as it appears in the current SKILL.md. Preserve the inline code blocks (```markdown ... ```) that appear inside each section.

**Step 4: Verify**

Read the new file. Confirm all 6 sections are present and bullet content matches SKILL.md exactly.

**Step 5: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/kickstart/templates/software.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(kickstart): extract software CLAUDE.md template"
```

---

### Task 27: Extract kickstart business CLAUDE.md template

**Files:**
- Create: `skills/kickstart/templates/business.md`

**Step 1: Read the source section**

Read `skills/kickstart/SKILL.md`. Locate `### Business Template` under `## Phase 4: Seed CLAUDE.md`.

**Step 2: Write the extracted file**

Write `skills/kickstart/templates/business.md`:

```markdown
# Business Project CLAUDE.md Template

Template for business/consulting workspaces. Referenced by `skills/kickstart/SKILL.md` Phase 4.

## Contents

- Section 1: Project Identity
- Section 2: Folder Map
- Section 3: Reading Priority
- Section 4: Communication Preferences
- Section 5: Guardrails
- Section 6: Workflows

<verbatim content of every section from the Business Template in SKILL.md>
```

Preserve every fenced code block exactly.

**Step 3: Verify**

Read the new file. Confirm the six sections are populated with content that matches the current SKILL.md Business Template.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/kickstart/templates/business.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(kickstart): extract business CLAUDE.md template"
```

---

### Task 28: Extract kickstart personal CLAUDE.md template

**Files:**
- Create: `skills/kickstart/templates/personal.md`

**Step 1: Read the source section**

Read `skills/kickstart/SKILL.md`. Locate `### Personal Template`.

**Step 2: Write the extracted file**

Write `skills/kickstart/templates/personal.md`:

```markdown
# Personal Workspace CLAUDE.md Template

Template for personal knowledge workspaces. Referenced by `skills/kickstart/SKILL.md` Phase 4.

## Contents

- Section 1: Project Identity
- Section 2: Folder Map
- Section 3: Reading Priority
- Section 4: Communication Preferences
- Section 5: Guardrails
- Section 6: Workflows

<verbatim content>
```

**Step 3: Verify**

Read the new file. Confirm sections match the source.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/kickstart/templates/personal.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(kickstart): extract personal CLAUDE.md template"
```

---

### Task 29: Extract kickstart general CLAUDE.md template

**Files:**
- Create: `skills/kickstart/templates/general.md`

**Step 1: Read the source section**

Read `skills/kickstart/SKILL.md`. Locate `### General Template`.

**Step 2: Write the extracted file**

Write `skills/kickstart/templates/general.md`:

```markdown
# General Workspace CLAUDE.md Template

Template for workspaces that don't fit software, business, or personal categories. Referenced by `skills/kickstart/SKILL.md` Phase 4.

## Contents

- Section 1: Project Identity
- Section 2: Folder Map
- Section 3: Reading Priority
- Section 4: Communication Preferences
- Section 5: Guardrails
- Section 6: Workflows

<verbatim content>
```

**Step 3: Verify**

Read the new file. Confirm sections are present and populated.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/kickstart/templates/general.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(kickstart): extract general CLAUDE.md template"
```

---

### Task 30: Extract kickstart scaffold structures

**Files:**
- Create: `skills/kickstart/templates/scaffold-structures.md`

**Step 1: Read the source section**

Read `skills/kickstart/SKILL.md`. Locate `## Phase 3: Scaffold Structure` and its sub-sections: `### Base Structure (ALL types)`, `### Software Additionally Creates (software type only)`. Extract only the directory-tree code blocks (the content between triple backticks). Phase 3's `### File Templates (Software only)` (with design-principles.md, architecture.md, Kanban directory structure, e2e/.gitignore blocks) and `### Settings (ALL types)` STAY inline in SKILL.md — they are not directory trees.

**Step 2: Write the extracted file**

Write `skills/kickstart/templates/scaffold-structures.md`:

```markdown
# Scaffold Directory Structures

Directory trees created by the kickstart skill's Phase 3, split by project type. Referenced by `skills/kickstart/SKILL.md` Phase 3.

## Contents

- Base Structure (ALL types)
- Software Additional Structure (software type only)

## Base Structure (ALL types)

```
<verbatim directory tree from SKILL.md Phase 3 Base Structure block>
```

## Software Additional Structure (software type only)

```
<verbatim directory tree from SKILL.md Phase 3 Software Additionally Creates block>
```

> **Note:** YAML-based eval projects (like this plugin) use `eval-surface.yaml` + `trigger-map.yaml` instead of the `.ts` files. The TS scaffold is for general-purpose projects with TypeScript eval runners.

**Business, Personal, General** get no additional folders beyond the base. Structure is flat — the user creates project-level folders at root as needed.
```

Copy the directory trees verbatim, preserving indentation and comments.

**Step 3: Verify**

Read the new file. Confirm both trees are intact and the explanatory note block is preserved.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/kickstart/templates/scaffold-structures.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(kickstart): extract scaffold directory structures"
```

---

### Task 31: Update kickstart SKILL.md — reference templates, fix git add, remove AskUserQuestion mentions

**Files:**
- Modify: `skills/kickstart/SKILL.md`

**Step 1: Replace Phase 3 directory trees with a reference**

In the `## Phase 3: Scaffold Structure` section, replace `### Base Structure (ALL types)` and `### Software Additionally Creates (software type only)` blocks with a pointer to `templates/scaffold-structures.md`. Retain `### File Templates (Software only)` and `### Settings (ALL types)` inline — they contain file content templates, not directory trees.

Example replacement:

```markdown
## Phase 3: Scaffold Structure

Create the directory structure for the selected `project_type`. See `templates/scaffold-structures.md` for the directory trees (Base Structure + Software Additional Structure). Resolve `{base-directory}` using the "Base directory for this skill:" line printed when the skill loads, then read the template file. Create each directory listed, skipping any that already exist.

### File Templates (Software only)

<unchanged — keep the existing content>

### Settings (ALL types)

<unchanged — keep the existing content>
```

**Step 2: Replace Phase 4 CLAUDE.md templates with references**

Rewrite `## Phase 4: Seed CLAUDE.md` so its body reads:

```markdown
## Phase 4: Seed CLAUDE.md

Generate a project-specific CLAUDE.md using the template for the selected `project_type`. All templates use a consistent 6-section structure:

1. **Project Identity** — what this is, who it's for
2. **Folder Map** — where files go, naming conventions
3. **Reading Priority** — what Claude should front-load
4. **Communication Preferences** — output style, tone, format
5. **Guardrails** — sensitivity, privacy, constraints
6. **Workflows** — skill/agent triggers

Read the template for the selected `project_type` from `templates/<project_type>.md` (resolve `{base-directory}` using the "Base directory for this skill:" line printed at skill load). Available templates:

- `templates/software.md` — for software projects
- `templates/business.md` — for business/consulting workspaces
- `templates/personal.md` — for personal knowledge workspaces
- `templates/general.md` — for general workspaces

Substitute `[project name]`, `[one-sentence description]`, and the Phase 2 tech stack values where placeholders appear. Write the resulting content to `CLAUDE.md` at the project root.
```

Delete every `### Software Template`, `### Business Template`, `### Personal Template`, `### General Template` H3 block under Phase 4.

**Step 3: Replace `git add -A` with an explicit file list**

Locate the commit block in Phase 6:

```
old_string:
Commit all scaffolded files:
```bash
git add -A
git commit -m "chore: scaffold project with Aligned conventions"
```

new_string:
Commit all scaffolded files. Stage each file created or modified during scaffolding explicitly — enumerate them from the list of files written in Phase 3 and Phase 4 (for software: `CLAUDE.md`, `.claude/settings.json`, `.gitignore`, `docs/architecture.md`, `docs/design/design-principles.md`, `docs/kanban/.counter`, `e2e/.gitignore`, any stub directories that contain `.gitkeep`; for business/personal/general: `CLAUDE.md`, `.claude/settings.json`, `.gitignore`).

```bash
git add <each file enumerated above>
git commit -m "chore: scaffold project with Aligned conventions"
```

**Behavior change:** Replaces a blanket `git add -A` with an explicit file list. Rationale: the user's global CLAUDE.md forbids `git add .` or `git add -A` to avoid accidentally staging sensitive files (.env, credentials). The new instruction forces the skill to enumerate actual scaffolded files. Added files are those the skill itself wrote — no user content is at risk.
```

**Step 4: Remove AskUserQuestion tool names**

Rationale: `executing-plans` and `writing-plans` already phrase their interactive prompts without naming the `AskUserQuestion` tool. Removing the `(use AskUserQuestion)` parenthetical brings kickstart in line with that convention. No behavior change — the surrounding question text still tells the skill to ask.

Use Edit to replace the Phase 1 prompt line:

```
old_string:
Before gathering any other context, ask the user (use AskUserQuestion):

new_string:
Before gathering any other context, ask the user:
```

And the Phase 2 prompt line:

```
old_string:
Ask the user for (use AskUserQuestion, multiple choice where possible):

new_string:
Ask the user for (multiple choice where possible):
```

**Step 5: Verify**

- Grep `skills/kickstart/SKILL.md` for `AskUserQuestion` — must return 0 matches
- Grep for `git add -A` — must return 0 matches
- Grep for `templates/` — must return at least 5 matches (one per template reference)
- Use Grep `output_mode=count` (pattern `^`) to measure line count. Target is ~150 lines (down from 395). If over 200 lines, treat as extraction failure — check whether all 4 CLAUDE.md template H3 blocks (Software, Business, Personal, General) and the Phase 3 directory-tree blocks were actually removed.

**Step 6: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/kickstart/SKILL.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "refactor(kickstart): reference extracted templates, explicit git add, drop AskUserQuestion mentions"
```

---

### Task 32: Bump plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Read current versions**

Read both files. Confirm current version is `0.22.0` in both (if not, adjust the new version accordingly — both files must match).

**Step 2: Bump version**

Use Edit on each file to change `"version": "0.22.0"` to `"version": "0.23.0"`.

**Step 3: Verify**

Read both files. Confirm both contain `"version": "0.23.0"` and no other content was changed.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git -C /Users/ericpage/software/aligned_cc_skills commit -m "chore: bump version to 0.23.0 for skill audit remediation"
```

---

## Eval Scenarios

This plan does not change any advisor prompts, framework prompts, prompt construction, or personalization logic. The `description:` field changes affect skill discovery (via description-match routing) but not runtime LLM behavior once a skill is invoked. No new eval scenarios are required.

The audit surface in `e2e/eval-surface.yaml` should continue to pass unchanged. If the LLM eval auto-run in `finishing-a-development-branch` fires, it will run only for skills whose surface files were touched — mostly no-ops given the nature of these edits.

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Wave 1 task granularity for description rewrites | Three batches (5 + 3 + 6 skills) | One task per skill (14 tasks); one task for all 14 |
| 2 | Bundle add-advisor cleanup with its description change | Bundled into Task 2 | Separate tasks (Task 2 for description, another task for cleanup) |
| 3 | TOC insertion strategy | Manual `## Contents` block right after H1 | Auto-generated via a tooling pass |
| 4 | `find-polluter.sh` complexity | Minimal one-at-a-time iteration, with `TEST_CMD` override | True bisection (divide-and-conquer); pytest/Jest-specific implementations |
| 5 | `condition-based-waiting-example.ts` design | Self-contained file with local `poll` helper and 3 exported helpers | Pull in an existing polling library (p-wait-for, etc.) |
| 6 | Where to route "Discovered during" guidance after Kanban dedup | Inline in each calling skill's Kanban reference sentence | Embed in the shared `_shared/kanban-entry-format.md` template |
| 7 | Whether to extract kickstart File Templates (Software only) | Keep inline in SKILL.md | Extract to `templates/scaffold-structures.md` with the directory trees |
| 8 | Meta-commentary in Step 1b ("Behavior change: The old Step 1b was vague...") | Move it into the extracted `references/llm-eval-gate.md` as a `## Notes` section | Delete it; or keep it in SKILL.md |
| 9 | Version bump size | 0.22.0 → 0.23.0 (minor bump) | Patch bump (0.22.1); major bump (1.0.0) |
| 10 | Handling of `create-image` description losing "illustration mode" | Adopt the design doc's new description as-is | Keep existing mention of illustration mode |

### Appendix: Decision Details

#### Decision 1: Wave 1 task granularity for description rewrites

**Chose:** Three batches of 5 + 3 + 6 skills (Tasks 1-3).

**Why:** Fourteen single-file tasks (one per skill) would produce fourteen 1-line commits — noisy, hard to review, and pointless given each edit is a trivial YAML-frontmatter replacement. A single bundled task of all 14 would violate the "~15 min per task" sizing guideline and couple unrelated skill groups in one commit. Three batches group skills by loose category (core workflow, advisor/design, utilities), keeping each commit scannable while respecting the TDD-adjacent "bite-sized tasks" principle the plugin's own writing-plans skill advocates. Batches are independent — Task 2's add-advisor cleanup pulls in a second round of edits that couldn't be bundled into Task 1 without creating a heterogeneous commit.

**Alternatives rejected:**
- **One task per skill (14 tasks):** Too granular. Each task would run in under a minute. The overhead of 14 context switches per wave outweighs any benefit.
- **One task for all 14:** Commits should tell a story. A "rewrite all descriptions" commit hides which skill's description moved from what to what — that's the exact blast radius reviewers need to evaluate.

#### Decision 2: Bundle add-advisor cleanup with its description change

**Chose:** Task 2 does three things to `skills/add-advisor/SKILL.md` — rewrites the description, removes the Invocation section, removes the editor note.

**Why:** All three edits are small, touch the same file, and are ordering-dependent (can't run in parallel). Keeping them in one task avoids three separate commits to the same file in rapid succession, which would clutter git log without adding review value. The `add-framework` editor note is a separate task (Task 5) only because `add-framework`'s description doesn't need rewriting — there's nothing to bundle it with.

**Alternatives rejected:**
- **Separate tasks for each edit:** Would produce commits like "rewrite add-advisor description" → "remove Invocation section" → "remove editor note" on the same file, consecutively. The intermediate states are meaningful to no one.

#### Decision 3: TOC insertion strategy

**Chose:** Manually insert a `## Contents` block immediately after the H1 in each file, listing every subsequent H2.

**Why:** The audit found 8 reference files without TOCs. Writing them by hand takes ~30 seconds per file and produces zero ambiguity. The content is stable — reference files don't rev their section structure often. No infrastructure investment is warranted.

**Alternatives rejected:**
- **Auto-generated TOC via a script or GitHub action:** Would require writing and testing tooling. The tooling would itself need maintenance (what if someone adds an H3 that shouldn't appear?). Hand-writing 8 short lists is strictly cheaper.

#### Decision 4: `find-polluter.sh` complexity

**Chose:** A minimal shell script that runs tests one-by-one, checks a sentinel after each, and reports the first test that produces it. Supports `TEST_CMD` env var for custom test runners.

**Why:** The referencing documentation says the script "runs tests one-by-one, stops at first polluter." That's exactly what the implementation does — no more, no less. YAGNI applies: the bisection metaphor is aspirational; a linear scan is what the doc describes and what a 30-line script can deliver reliably. The `TEST_CMD` override lets any project (npm, pytest, cargo) plug in without forking the script.

**Alternatives rejected:**
- **True divide-and-conquer bisection:** Faster in theory (O(log n) vs O(n)) but requires running multiple tests per bisection step, which compounds side effects — if test A pollutes for B but B is quarantined, the bisection misdiagnoses. Linear scan is correct and simple.
- **Framework-specific implementations (pytest-polluter, jest-circus flags):** Locks the script to one ecosystem. Shell + env var keeps it portable.

#### Decision 5: `condition-based-waiting-example.ts` design

**Chose:** Self-contained TypeScript file with a private `poll` helper and three exported helpers (`waitForEvent`, `waitForEventCount`, `waitForEventMatch`) matching the names the doc references.

**Why:** The referencing doc (`condition-based-waiting.md`) names three specific helpers. The example file must show their call signatures, defaults, and bodies so a reader can copy-paste a starting point. Including a polling library would mean the example doesn't stand alone — the reader can't run it without `npm install`. A 100-line self-contained file demonstrates the pattern clearly.

**Alternatives rejected:**
- **Depend on `p-wait-for` or similar:** The example becomes "look at their README" rather than a concrete pattern. Misses the didactic point.
- **Heavy abstraction (event bus, Rx subjects):** Overkill. Three helpers and a poll loop are enough to show the pattern.

#### Decision 6: Where to route "Discovered during" guidance after Kanban dedup

**Chose:** Keep each calling skill's `_shared/kanban-entry-format.md` reference inline with a "Discovered during" value (e.g., `Use 'finishing-a-development-branch' as the 'Discovered during' value`).

**Why:** The shared template can't know who's calling it. The calling skill is the only place that knows what identifier belongs in "Discovered during." Embedding calling-specific guidance in the shared template would require either branching (`if caller == X, use Y`) or a placeholder convention the caller has to override — both add complexity. A one-line sentence per caller is the simplest solution.

**Alternatives rejected:**
- **Embed a `{caller-name}` placeholder in the shared template:** Adds a substitution step. Doesn't actually reduce duplication — each caller still has to substitute.

#### Decision 7: Whether to extract kickstart File Templates (Software only)

**Chose:** Keep File Templates inline in SKILL.md (design-principles.md placeholder, architecture.md template, Kanban directory structure, e2e/.gitignore).

**Why:** These are short content snippets (the whole block is under 40 lines) tightly coupled to the surrounding Phase 3 scaffolding logic. Extracting them would spread a coherent "what files get created + what their initial content is" story across two files for minimal size savings. The design doc's extraction targets are the 4 CLAUDE.md templates and the scaffold trees — File Templates aren't listed.

**Alternatives rejected:**
- **Extract to `templates/scaffold-structures.md`:** Mixes directory trees (structural) with file content (textual). They're different kinds of thing; combining them makes the reference file harder to scan.

#### Decision 8: Meta-commentary in Step 1b

**Chose:** Move the "Behavior change: The old Step 1b was vague..." blockquote into `references/llm-eval-gate.md` as a trailing `## Notes` section rather than deleting it.

**Why:** The commentary records *why* the current pattern-matching rules exist. Deleting it loses that history. But it doesn't belong in the runtime workflow — readers following the SKILL.md step-by-step don't need authoring rationale mid-flow. The right home is alongside the section it annotates. Task 24 already captures Step 1b verbatim; Task 25 confirms the commentary traveled with it and, if not, adds it explicitly.

**Alternatives rejected:**
- **Delete it entirely:** Loses historical context that may matter if someone later proposes "simplifying" the pattern-matching rules.
- **Keep it in SKILL.md:** Contradicts the extraction — readers expect Step 1b's body to be in the reference file.

#### Decision 9: Version bump size

**Chose:** Minor bump 0.22.0 → 0.23.0.

**Why:** The plugin is pre-1.0. The README's changelog convention treats user-visible description changes as minor bumps. This release reshuffles three SKILL.md files' structure, renames 14 descriptions, and adds new reference files — user-visible enough for a minor, not breaking enough for a major. Patch (0.22.1) would underscore changes that users will notice in their `/help` listings.

**Alternatives rejected:**
- **Patch (0.22.1):** Underscales. Description rewrites change discovery behavior.
- **Major (1.0.0):** Overscales. Pre-1.0 plugin, no API contract broken.

#### Decision 10: `create-image` description loses "illustration mode" mention

**Chose:** Adopt the design doc's new description as-is — omits the explicit "illustration mode" label.

**Why:** The design doc's replacement description still covers illustration-like work implicitly ("visual artifact is needed — charts, flowcharts, matrices, icons, or brand graphics"). Illustration was the most recent mode added to `create-image`; the audit's description pattern treats all modes uniformly by describing the *outputs* rather than enumerating internal modes. This is a stylistic unification, not a capability removal.

**Alternatives rejected:**
- **Keep the illustration mode mention explicit:** Creates inconsistency with the other 13 rewrites which don't enumerate modes. If this causes discovery regressions in practice, it can be reverted after measurement; but absent evidence, consistency wins.

---

## Manual Steps (Post-Automation)

None. Every task in this plan is automatable. After Task 32 is complete, the plugin is ready to ship. The version bump in Task 32 signals the release.

No architecture doc update is required — this plan does not change system architecture (no new routes, modules, or database changes). It restructures documentation within existing skills.
