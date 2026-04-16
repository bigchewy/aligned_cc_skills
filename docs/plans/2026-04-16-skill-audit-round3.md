# Skill Audit Round 3 Remediation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Resolve the six new issues surfaced in the round-3 audit at `/tmp/skill-audit-v3/SUMMARY.md` §4: `executing-plans` triplicated autonomous-mode stop condition, `add-advisor` step-number coupling, `codebase-audit` `workers/security.md` missing TOC, `create-image` description omits illustrations, `brainstorming` undefined `{topic}`/`{project-root}` placeholders, `kickstart` hardcoded 18-skill permission list.

**Source Design Doc:** N/A — the audit report at `/tmp/skill-audit-v3/SUMMARY.md` §4 and the per-skill files at `/tmp/skill-audit-v3/<skill>.md` serve as the spec.

**Architecture:** Pure markdown edits inside the aligned plugin. Five of six tasks are narrow text edits (consolidate, rename reference, add TOC, extend description, define placeholders). Task 6 (kickstart) replaces a hardcoded list with runtime enumeration instructions that Claude executes at scaffold time — still a markdown edit, just changing what the skill tells Claude to do. No code, no tests, no schema changes.

**Tech Stack:** Markdown + YAML frontmatter only. Plugin versioned in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

**Verification philosophy:** Each task includes a grep-based "Verify" step to confirm the change landed. A final task bumps the plugin version. No re-audit task — the user can spawn one manually if desired.

---

## Prerequisites

None.

---

## Task 1: Consolidate executing-plans autonomous-mode stop condition

**Files:**
- Modify: `skills/executing-plans/SKILL.md` (lines 18, 42-44, 56-60)

**Issue:** The autonomous-mode stop condition is restated three times in slightly different wording, creating surface-area drift risk. The v3 auditor flagged this at `[SKILL.md:18]`, `[SKILL.md:42]`, and `[SKILL.md:57]`.

**Target state:** Define autonomous mode once at the Overview level (line 18). Steps 2 and 3 reference the definition rather than restating the stop condition.

**Step 1:** Read `skills/executing-plans/SKILL.md` lines 17-19, 40-45, and 55-60 to confirm current triplication.

Expected current state:
- Line 18: `**Autonomous mode:** Execute all tasks without pausing for review between batches. Only stop if a task fails verification or hits a blocker. When all tasks pass, stop. Do NOT invoke \`/aligned:finishing-a-development-branch\` — the user will run that manually.`
- Lines 42-44: `**Default mode: autonomous.** Execute all tasks without stopping for review. Only stop on task failure or a blocker.\n\n**Batched mode (opt-in):** ...`
- Lines 56-60: `### Step 3: Report\n\n**Autonomous mode:** When all tasks pass verification, stop. Summarize what was implemented and show verification output. Do not hand off to \`finishing-a-development-branch\` — the user runs that manually.\n\n**Batched mode only:** ...`

**Step 2:** Edit the Overview block (line 18) to define autonomous mode as the single canonical statement:

Replace line 18 exactly with:

```
**Default mode is autonomous:** execute all tasks without pausing between batches. Stop only when (a) a task fails verification, (b) you hit a blocker, or (c) all tasks have passed — in that final case, summarize and stop; do NOT invoke `/aligned:finishing-a-development-branch` (the user runs that manually). Batched mode (Step 2) is opt-in for reviews between batches.
```

**Step 3:** Replace the Step 2 mode block (lines 42-44) with a consolidated block — a back-reference for autonomous mode and the retained batched-mode opt-in description, merged into one paragraph:

```markdown
**Execution mode:** autonomous by default (defined in Overview). If the user explicitly requested checkpoints, or the plan is marked for batched execution, switch to batched mode: process tasks in groups of 3–7 and report between batches.
```

**Step 4:** Replace the Step 3 autonomous-mode line (line 58) with a back-reference. The Step 3 section should read:

```markdown
### Step 3: Report

**Autonomous mode (default):** on completion, summarize what was implemented and show verification output. Stop — do not hand off to `finishing-a-development-branch`.

**Batched mode only:** between batches, show what was implemented, show verification output, say "Build is complete. Ready for testing", give the user instructions on what to test, and include the bash command to enter the worktree and start the dev server.
```

**Step 5:** Verify the triplication is gone.

```bash
grep -c "When all tasks pass" skills/executing-plans/SKILL.md
```
Expected: `0` (the phrase was the common pattern across the three definitions).

```bash
grep -cE "Default mode:? autonomous" skills/executing-plans/SKILL.md
```
Expected: `0` (old label gone — the canonical definition now uses "Default mode is autonomous").

```bash
grep -c "Default mode is autonomous" skills/executing-plans/SKILL.md
```
Expected: `1` (single canonical definition).

**Step 6:** Commit.

```bash
git add skills/executing-plans/SKILL.md
git commit -m "docs(executing-plans): consolidate triplicated autonomous-mode stop condition into one definition"
```

---

## Task 2: Replace add-advisor's step-number cross-skill reference

**Files:**
- Modify: `skills/add-advisor/SKILL.md` (line 177)

**Issue:** Step 6 cites `add-framework`'s "Step 5" by number. If add-framework is reorganized (steps inserted/renumbered), this reference silently goes stale. The v3 auditor flagged this at `[SKILL.md:177]` as "fragile coupling".

**Current text (line 177):**
```
> **Critical:** The add-framework skill updates `frameworks/registry.yaml` (Step 5 in that skill). If you write the framework `prompt.md` directly instead of invoking the skill, you MUST also append an entry to `frameworks/registry.yaml` with id, name, advisor, purpose, category, domains, and use_when fields. A framework that exists on disk but not in the registry will have degraded discovery — use-framework falls back to filesystem glob but loses metadata-based matching and routing.
```

**New text:**
```
> **Critical:** The add-framework skill updates `frameworks/registry.yaml` as part of its registry-entry step. If you write the framework `prompt.md` directly instead of invoking the skill, you MUST also append an entry to `frameworks/registry.yaml` with id, name, advisor, purpose, category, domains, and use_when fields. A framework that exists on disk but not in the registry will have degraded discovery — use-framework falls back to filesystem glob but loses metadata-based matching and routing.
```

**Why:** Behavioral anchor ("registry-entry step") survives renumbering. add-framework currently has a Step 5 titled "Add Registry Entry" — confirmed by `grep '^### 5' skills/add-framework/SKILL.md` — but that number is not stable.

**Step 1:** Read `skills/add-advisor/SKILL.md` lines 173-178 to confirm current text.

**Step 2:** Edit the line to replace `(Step 5 in that skill)` with `as part of its registry-entry step`.

**Step 3:** Verify:
```bash
grep -cE "Step 5 in that skill|Step [0-9]+ in that skill" skills/add-advisor/SKILL.md
```
Expected: `0`.

```bash
grep -c "registry-entry step" skills/add-advisor/SKILL.md
```
Expected: `1`.

**Step 4:** Commit.
```bash
git add skills/add-advisor/SKILL.md
git commit -m "docs(add-advisor): replace fragile cross-skill step-number reference with behavior anchor"
```

---

## Task 3: Add TOC to codebase-audit workers/security.md

**Files:**
- Modify: `skills/codebase-audit/workers/security.md`

**Issue:** `workers/security.md` is 114 lines — over the rubric's 100-line TOC threshold. Peer files (`code-quality.md`, `test-quality.md`, `dead-code.md`, `architecture.md`) are all under 100 lines and don't need one. The v3 auditor flagged this at `[workers/*.md]`.

**Target state:** A `## Contents` section inserted immediately after the one-paragraph intro (between the opening paragraph and the "## Observation Phase (MANDATORY)" heading), listing the major `##` section headings.

**Step 1:** Read `skills/codebase-audit/workers/security.md` lines 1-10 to confirm the current structure (intro paragraph, then "## Observation Phase (MANDATORY)").

**Step 2:** Read the full file to enumerate the existing `##` headings that will feed the TOC. Use Grep to list them:

```bash
grep -n "^## " skills/codebase-audit/workers/security.md
```

**Step 3:** Insert the following TOC block on a new section between the intro paragraph and the "## Observation Phase (MANDATORY)" heading. The headings below are the six `##` headings currently in the file (verified by Grep during plan writing) — confirm against Step 2's Grep output and drop/add bullets if the file has changed since:

```markdown
## Contents
- Observation Phase (MANDATORY)
- What to Look For
- What NOT to Look For
- High-Risk Grep Patterns
- Confidence Rubric
- Output Format
```

**Step 4:** Verify:

```bash
grep -c "^## Contents$" skills/codebase-audit/workers/security.md
```
Expected: `1`.

```bash
grep -c "" skills/codebase-audit/workers/security.md
```
Expected: `114 + <n>` where `<n>` is the number of lines added for the TOC (~8).

(Note: `grep -c ""` counts lines without invoking disallowed Bash file-content tools like `wc`.)

**Step 5:** Commit.
```bash
git add skills/codebase-audit/workers/security.md
git commit -m "docs(codebase-audit): add TOC to workers/security.md (114 lines, over TOC threshold)"
```

---

## Task 4: Add illustrations to create-image description

**Files:**
- Modify: `skills/create-image/SKILL.md` (line 3, the `description:` field)

**Issue:** The description lists "diagrams, charts, flowcharts, and brand icons" but the skill has a full `modes/illustration.md` mode (botanical, decorative, watermark, background art). A user asking for a "botanical hero illustration" would not match the description and the skill would be skipped. The v3 auditor flagged this at `[SKILL.md:3]`.

**Current description (line 3):**
```
"Generates hand-coded SVG diagrams, charts, flowcharts, and brand icons matching the project's design tokens. Use when a visual artifact is needed — charts, flowcharts, matrices, icons, or brand graphics."
```

**New description:**
```
"Generates hand-coded SVG diagrams, charts, flowcharts, brand icons, and decorative illustrations matching the project's design tokens. Use when a visual artifact is needed — charts, flowcharts, matrices, icons, brand graphics, or botanical/decorative illustrations."
```

**Why:** Adds "illustrations" to both the capability list and the trigger list so requests for decorative/botanical art route into this skill instead of being missed.

**Step 1:** Read `skills/create-image/SKILL.md` lines 1-5 to confirm current description matches verbatim.

**Step 2:** Edit the `description:` field to the new string.

**Step 3:** Verify:

```bash
grep -c "decorative illustrations" skills/create-image/SKILL.md
```
Expected: `1`.

```bash
grep -c "botanical/decorative illustrations" skills/create-image/SKILL.md
```
Expected: `1`.

**Step 4:** Commit.
```bash
git add skills/create-image/SKILL.md
git commit -m "docs(create-image): add illustrations to description to match modes/illustration.md coverage"
```

---

## Task 5: Define `{topic}` and `{project-root}` in brainstorming SKILL.md

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (before or inside Step 2, around lines 64-72)

**Issue:** Step 2 dispatches a project-scan agent with a prompt referencing `{topic}` and `{project-root}`, but these placeholders are never defined in SKILL.md. A Claude reading this literally could substitute the braces as-is or ask the user to clarify. The v3 auditor flagged this at `[SKILL.md:65-72]`.

**Current text (lines 64-72):**
```
## Step 2: Project Scan
Dispatch a project scan agent via Task tool (subagent_type=general-purpose),
running in the background. Now that mode is known, pass it to the scanner:

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`.
Mode: {software|business} — emphasize {code artifacts|domain materials}
accordingly."

Do not wait for the scan to complete before proceeding to Step 3.
```

**New text:**
```
## Step 2: Project Scan

**Resolve placeholders before dispatching:**
- `{topic}` — a 1–3 word kebab-case slug derived from the user's request (e.g., "pricing-strategy", "auth-refactor"). Ask the user if the request is ambiguous.
- `{project-root}` — the current working directory unless the user specified a different path.

Dispatch a project scan agent via Task tool (subagent_type=general-purpose),
running in the background. Now that mode is known, pass it to the scanner:

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`.
Mode: {software|business} — emphasize {code artifacts|domain materials}
accordingly."

Do not wait for the scan to complete before proceeding to Step 3.
```

**Why:** Defines the two placeholders inline so Claude substitutes concrete values into the dispatch prompt rather than passing the braces literally.

**Step 1:** Read `skills/brainstorming/SKILL.md` lines 64-75 to confirm current text.

**Step 2:** Edit the Step 2 section to insert the "Resolve placeholders before dispatching" block immediately after the heading and before the "Dispatch a project scan agent" paragraph.

**Step 3:** Verify:

```bash
grep -c "Resolve placeholders before dispatching" skills/brainstorming/SKILL.md
```
Expected: `1`.

```bash
grep -cE '^\s*- `\{topic\}` — ' skills/brainstorming/SKILL.md
```
Expected: `1`.

```bash
grep -cE '^\s*- `\{project-root\}` — ' skills/brainstorming/SKILL.md
```
Expected: `1`.

**Step 4:** Commit.
```bash
git add skills/brainstorming/SKILL.md
git commit -m "docs(brainstorming): define {topic} and {project-root} placeholders used in Step 2 dispatch"
```

---

## Task 6: Replace kickstart Phase 5 hardcoded skill list with runtime enumeration

**Files:**
- Modify: `skills/kickstart/SKILL.md` (Phase 5 block, lines ~125-156)

**Issue:** Phase 5 hardcodes the full 18-skill permission list. Each new skill requires updating two places (this file and `README.md`) — a dual-update burden already called out in CLAUDE.md. The v3 auditor flagged this at `[SKILL.md:131-156]` and it also appeared in the round-2 audit as a Theme-E portability item.

**Target state:** Phase 5 instructs Claude to enumerate skills from the plugin's `skills/` directory at scaffold time and generate the allow-list dynamically. The skill list is derived from the filesystem (single source of truth), not restated.

**Why runtime enumeration, not plugin.json lookup:** `.claude-plugin/plugin.json` in this repo does not enumerate skills — it only carries plugin metadata. The filesystem (`skills/<name>/SKILL.md`) is the authoritative list. Glob-based enumeration matches the existing Path Resolution pattern (Glob `$HOME` for `**/.claude-plugin/plugin.json`) and does not introduce new resolution semantics.

**Behavior changes** (non-breaking but user-visible):
- The completion message now includes a dynamic skill count: `"Set up skill permissions for N aligned skills..."` instead of the current fixed wording.
- A fork that adds or removes skills will produce a different allow-list than the previously hardcoded 18-entry output. This is the intended fix.

**Step 1:** Read `skills/kickstart/SKILL.md` lines 125-160 to confirm current text (the hardcoded JSON block and surrounding prose).

**Step 2:** Read `skills/kickstart/SKILL.md` lines 1-15 to see how the file resolves `{base-directory}` (same Path Resolution pattern as other skills). Also read `skills/_shared/resolve-skill-path.md` in full — it specifies the canonical plugin-root resolution (Glob for `.claude-plugin/plugin.json`; take the parent directory) and explicitly forbids string-manipulating `{base-directory}` up to the plugin root.

**Step 3:** Replace the hardcoded JSON block and its introductory sentence. The new Phase 5 body should read exactly:

```markdown
Check whether `~/.claude/settings.json` already contains aligned skill permissions by looking for `Skill(aligned:brainstorming)` in the `permissions.allow` array.

**If already present:** Skip this phase silently — permissions have already been configured.

**If missing:** Enumerate the aligned plugin's skills at runtime and append one `Skill(aligned:<name>)` entry per skill to `permissions.allow`. Do not hardcode the list — it must derive from the filesystem so new skills are picked up automatically.

1. Resolve the plugin root per `skills/_shared/resolve-skill-path.md` (the "Plugin root" and "Edge case: multiple plugin installs" sections). In short: Glob `$HOME` for `**/.claude-plugin/plugin.json`; the plugin root is the parent directory of the matched `.claude-plugin/` dir. On multiple matches, follow the canonical tiebreaker sequence from that file (prefer `name: aligned` + sibling `skills/<skill-name>/SKILL.md`; then prefer matches under CWD or ancestors; if still ambiguous, stop and ask).
2. Glob `<plugin-root>/skills/*/SKILL.md` to discover all skill directories. The skill name is the parent directory name of each matched `SKILL.md`.
3. Filter out any directory starting with `_` (e.g., `_shared/`) — these are shared reference directories, not skills.
4. Sort the resulting names alphabetically for deterministic output.
5. Read `~/.claude/settings.json` (create the file with `{"permissions":{"allow":[],"deny":[]}}` if it doesn't exist). Preserve all existing keys (`permissions.deny`, `enabledPlugins`, etc.) and all existing `allow` entries.
6. For each enumerated skill, append `Skill(aligned:<name>)` to `permissions.allow` if not already present.
7. Write the file back as valid JSON (2-space indent, trailing newline).

Tell the user: "Set up skill permissions for N aligned skills in `~/.claude/settings.json` — you won't get permission prompts." (where N is the count of skills enumerated).
```

**Step 4:** Verify the hardcoded list is gone and the enumeration instructions are present:

```bash
grep -c "Skill(aligned:brainstorming)" skills/kickstart/SKILL.md
```
Expected: `1` (the sentinel check on line ~125 that detects prior installation — this one stays; it's a pattern to grep for, not a hardcoded list).

```bash
grep -cE 'Skill\(aligned:writing-plans\)|Skill\(aligned:executing-plans\)|Skill\(aligned:use-advisor\)' skills/kickstart/SKILL.md
```
Expected: `0` (the hardcoded list is gone).

```bash
grep -c "Glob" skills/kickstart/SKILL.md
```
Expected: `1` or more (the enumeration step now references Glob).

```bash
grep -c "enumerate the aligned plugin's skills at runtime" skills/kickstart/SKILL.md
```
Expected: `1`.

**Step 5:** Commit.
```bash
git add skills/kickstart/SKILL.md
git commit -m "fix(kickstart): derive Phase 5 skill permission list from filesystem at runtime"
```

---

## Task 7: Bump plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json` (`version` field)
- Modify: `.claude-plugin/marketplace.json` (`plugins[0].version` field)

**Why:** Per CLAUDE.md, both files must match. Round-3 remediation is a patch-level release (documentation tightening, no API changes).

**Step 1:** Read both files and confirm current version is `0.24.0`.

**Step 2:** Edit `.claude-plugin/plugin.json` to change `"version": "0.24.0"` → `"version": "0.25.0"`.

**Step 3:** Edit `.claude-plugin/marketplace.json` to change `"version": "0.24.0"` → `"version": "0.25.0"` (inside the `plugins[0]` object).

**Step 4:** Verify:

```bash
grep -c '"version": "0.25.0"' .claude-plugin/plugin.json
```
Expected: `1`.

```bash
grep -c '"version": "0.25.0"' .claude-plugin/marketplace.json
```
Expected: `1`.

```bash
grep -c '"version": "0.24.0"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
```
Expected: `0` for both (grep across both files — the round-2 version should be gone).

**Step 5:** Commit.
```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump plugin version to 0.25.0 (skill audit round 3 remediation)"
```

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | executing-plans consolidation location | Define autonomous mode once in Overview (line 18); back-reference from Steps 2 and 3 | Define in Step 2 and cross-ref; define in a new "## Modes" section; leave all three definitions and reconcile wording only |
| 2 | add-advisor cross-skill anchor | Behavioral: "registry-entry step" | Named: "Add Registry Entry step"; no anchor — remove the cross-reference entirely |
| 3 | security.md TOC granularity | `##`-level only (6 top-level sections) | `###`-level (would list every subcategory — ~15 lines of TOC for a 114-line file) |
| 4 | create-image description wording | "decorative illustrations" + "botanical/decorative illustrations" trigger | "illustrations" (too broad); enumerate each illustration subtype |
| 5 | brainstorming placeholder definition location | Inline "Resolve placeholders" block in Step 2 | Global glossary section at top of SKILL.md; separate `brainstorming/glossary.md` reference |
| 6 | kickstart skill-list derivation source | Filesystem Glob of `skills/*/SKILL.md` | Derive from `plugin.json` (doesn't enumerate skills); derive from `README.md` table (fragile scraping); derive from `advisors/registry.yaml` (wrong registry) |
| 7 | Re-audit task | Omitted — user can spawn manually | Include as Task 8 per round-2 pattern |

### Appendix: Decision Details

#### Decision 1: executing-plans consolidation location

**Chose:** Define autonomous mode once at the Overview level (line 18), reference from Steps 2 and 3.

**Why:** The Overview block is where a reader first encounters the skill's mode model. Putting the canonical definition there matches how other skills expose mode selection (brainstorming defines "Software mode" / "Business mode" up front). Step 2 and Step 3 then cite the already-established definition rather than re-deriving it. This is the tightest disambiguation — the three current statements exist because no single location is "obviously" authoritative, so each step restated in self-defense.

**Alternatives rejected:**
- Define in Step 2 and cross-reference: Step 3's report behavior depends on the mode, so Step 3 would still need its own mode awareness. Moving the definition to Step 2 just shifts the duplication.
- Introduce a new "## Modes" section: adds structural overhead for two modes. Overkill.
- Reconcile wording only, keep three statements: solves the immediate audit flag but leaves the structural issue (three touch-points that can drift again).

#### Decision 2: add-advisor cross-skill anchor

**Chose:** Behavioral anchor — "registry-entry step".

**Why:** Step numbers are the most volatile part of a skill file. Titles change rarely. Behavior anchors ("the registry-entry step") are even stabler than titles because they describe what the step does rather than what it's called. The add-framework skill could rename "Add Registry Entry" to "Write Registry YAML" without breaking this reference.

**Alternatives rejected:**
- "Add Registry Entry step" (quoting the current title): still breaks if the title is rewritten. Slightly better than step number but not the tightest.
- Remove the cross-reference entirely: the warning is useful context for Claude when a user skips add-framework — removing it drops real information.

#### Decision 6: kickstart skill-list derivation source

**Chose:** Filesystem Glob of `skills/*/SKILL.md`.

**Why:** The filesystem is already the source of truth — `CLAUDE.md`'s "Adding a Skill" checklist directs authors to create `skills/<name>/SKILL.md` first, then update derived listings (README table, Phase 5 allow-list). By having kickstart Glob at runtime, the derived listing stops being a derived listing — it's computed fresh every time the skill runs. This matches the Path Resolution pattern (Glob for `.claude-plugin/plugin.json`) so the pattern is already in the skill's repertoire.

**Alternatives rejected:**
- `.claude-plugin/plugin.json`: the file does not enumerate skills (confirmed by reading it). Plugins don't list their contained skills — Claude Code discovers them by convention.
- `README.md` table scraping: fragile (table format could change). Also inverts the flow — kickstart would be reading an auto-maintained doc rather than the source.
- `advisors/registry.yaml`: wrong registry — that lists advisor personas, not skills.

#### Decision 7: Re-audit task

**Chose:** Omit. The user can spawn a round-4 audit manually after this plan completes.

**Why:** Round-3's re-audit (round-2's Task 29) confirmed the score delta was measurable — +0.25 mean, +2 A-grades. The edits in this plan are narrow and individually verifiable via grep. A re-audit would consume significant LLM budget to confirm what grep already confirms. Leave it to the user to decide whether to run round 4.

**Alternatives rejected:**
- Include as Task 8: round-2 did this (Task 29) and it took significant tokens to run 16 sub-agents in parallel. For six narrow fixes, the cost-to-signal ratio is lower.

**Known verification gap for Task 6:** The grep-based verify steps in Task 6 confirm the hardcoded list is gone and the enumeration prose is present, but they cannot confirm that Claude, executing the new instructions at scaffold time, produces a correctly-formatted `settings.json` with the expected allow-list entries. The earliest signal on correctness will be the first live kickstart run after this lands. If that concerns you, manually run the kickstart flow against a throwaway test project after Task 6 merges and before cutting a release.
