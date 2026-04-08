# Persona Creation Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add a guided persona creation flow to persona-panel's cold-start path so users can create personas through Q&A instead of hitting a dead end.

**Source Design Doc:** `docs/plans/2026-04-08-persona-creation-flow-design.md`

**Mockups:** `docs/mockups/persona-creation-flow.html`

**Architecture:** The creation flow lives in a new `modes/persona-creation-flow.md` file, following the same pattern as `skills/brainstorming/modes/`. SKILL.md gets a minimal change — replace the dead-end "no personas found" message with an opt-out prompt and delegation to the flow document. The flow is a four-phase conversational process (Context Detection → Q&A → Summary Approval → File Generation) that writes persona files using the existing template, then hands back to Stage 1.

**Tech Stack:** Markdown skill files (no runtime code — this is a Claude Code skill plugin)

**Task ordering:** Complete Task 1 before Task 2 — Task 2 references `modes/persona-creation-flow.md` which Task 1 creates. Verify Tasks 1 and 2 produce correct output before proceeding to Tasks 3 and 4 (version bump and changelog).

**Post-execution note:** After all tasks are committed, validate the new flow by running through the design doc's 13 manual testing scenarios (`docs/plans/2026-04-08-persona-creation-flow-design.md`, Testing section). These are manual-only and cannot be automated.

---

### ✅ Task 1: Create the persona creation flow document

**Files:**
- Create: `skills/persona-panel/modes/persona-creation-flow.md`
- Reference: `skills/persona-panel/references/persona-template.md` (read for template structure)
- Reference: `skills/brainstorming/modes/software.md` (read for modes/ file convention)

**Step 1: Read the reference files**

Read `skills/brainstorming/modes/software.md` (first 5 lines) to confirm the modes convention: no YAML frontmatter, HTML comment on line 1 identifying it as a mode file read by the router.

Read `skills/persona-panel/references/persona-template.md` in full to confirm all 20 bullet fields.

**Step 2: Write the flow document**

Create `skills/persona-panel/modes/persona-creation-flow.md` with the following content. Use the HTML comment convention from other mode files.

```markdown
<!-- Mode file: Read into context by persona-panel Stage 1. Do not add YAML frontmatter. -->

# Persona Creation Flow

Guided creation of buyer personas when `docs/personas/` is empty. Four phases: Context Detection, Q&A, Summary Approval, File Generation.

## Phase 1: Context Detection

Scan for existing buyer/persona documentation before asking questions. Sources in order of specificity:

1. **`docs/` directory** — files with buyer, persona, ICP, audience, or customer keywords in filename or content
2. **`content/` and `marketing/` directories** — marketing briefs, sales collateral, positioning docs
3. **`CLAUDE.md` / project instructions** — target audience, product description, market context
4. **`README.md`** — product description, value prop, who it's for

**If directories don't exist:** Silently skip them. Only report what was found, not what wasn't.

**False-positive handling:** Keyword matches on filenames alone are low-confidence (e.g., `api-customers.md` may be an API doc, not buyer research). When presenting found docs, show at most 5 files and frame as opt-in:

> "I found these docs that might describe your buyers: [list]. Should I use any of these as a starting point, or skip straight to questions?"

**If the user declines the found docs:** Proceed to Phase 2 using the minimal/no-context path (full Q&A).

**If nothing found:** Skip to Phase 2: "I didn't find existing buyer documentation. I'll ask a few questions to understand your buyers."

## Phase 2: Q&A

Adapts depth based on how much context Phase 1 found.

**If rich context was found and accepted:** Extract buyer types from docs and confirm:

> "Based on [source], I see these buyer types: [list]. Is this right, or should I add/remove any?"

Then 1-2 targeted questions to fill gaps (psychology, objections, communication style).

**If minimal/no context:** Ask sequentially, one at a time:

1. "What does your product/service do, in one sentence?" *(skip if obvious from CLAUDE.md/README)*
2. "Who are the distinct buyer types you sell to? Could be one, could be several — just roles or titles."
3. "For each buyer, what's the main problem they're trying to solve when they find you?"
4. "What makes each buyer type skeptical? What turns them off?"
5. "How do these buyers talk — formal/casual, data-driven/story-driven, technical/non-technical?"

**Adaptive depth heuristics:**
- **Rich answer** (2+ sentences per buyer, covers motivations or objections without prompting) → skip follow-up questions on that topic.
- **Thin answer** (single phrase, role title only, no detail on motivations) → ask a follow-up to deepen (e.g., "What keeps [role] up at night about this problem?").
- Cap at 7 total questions regardless. After 7, proceed with what you have.

**Single-buyer case:** If the user names only one buyer type, proceed normally. Note that a single-persona panel has reduced diagnostic value since there's no cross-persona contrast, but it's still useful.

**Group naming:** Infer group directory name from the buyer set (e.g., `b2b-buyers/`, `enterprise/`). If unclear, ask.

## Phase 3: Summary Approval

Display a table of all personas before writing anything:

```
I'll create these personas in docs/personas/<group>/:

| File | Name | Archetype | Key Differentiator |
|------|------|-----------|--------------------|
| vp-engineering.md | Dana Chen | The Build-vs-Buy Evaluator | Technical depth, allergic to vendor lock-in |
| head-of-sales.md | Marcus Rivera | The Revenue Operator | ROI-first, wants proof not promises |
| founder-ceo.md | Sarah Kim | The Scaling Founder | Speed over polish, pattern-matches against past burns |

These are rough drafts — the panel will reveal which personas need sharpening over time. Proceed, or adjust?
```

User can adjust names, add/remove personas, or change archetypes before proceeding.

## Phase 4: File Generation

**Resolve the template path:** Read the persona template at `{base-directory}/references/persona-template.md` (resolve `{base-directory}` from the "Base directory for this skill:" line printed when persona-panel loaded). **Fallback** (if the base-directory line was compressed out of context): Use Glob to search for `**/persona-panel/references/persona-template.md`. Use the match that lives under a directory containing `.claude-plugin/plugin.json`. If the template cannot be found after both strategies, STOP and tell the user — do not generate persona files without the template.

**On approval:**

- Generate all persona files using the template structure from the resolved template path
- Every field populated — no TODOs, no placeholders
- Use Q&A answers + extracted doc context to fill all 20 bullet fields:
  - Demographics (5): Role, Company stage, Industry, Years in role, Background
  - Situation (3): Scaling trigger, What they've tried, Current pressure
  - Psychology (4): What they won't say out loud, Personal definition of success, How they evaluate consultants, Decision style
  - Communication Style (3): How they talk, Language that resonates, Language that repels
  - Review Lens (5): Scans for, Gets skeptical when, Keeps reading when, Would reach out if, Would click away if
- Infer reasonable defaults for fields not explicitly addressed (e.g., "Years in role" estimated from archetype)
- File naming: slugified from role/title, lowercase, hyphenated (e.g., `vp-engineering.md`)
- Create group directory if it doesn't exist

**After generation:** Prompt the user for content to evaluate:

> "Personas created. To run your first panel, paste or reference the content you'd like to test."

Then return control to Stage 1. Stage 1 re-globs `docs/personas/`, finds the new group, continues to Stage 2.

## Edge Cases

**User aborts mid-flow:** If the user says "stop", "nevermind", "I'll do this later", or otherwise signals exit, stop cleanly. Don't write partial files. Confirm: "No files written. Next time you invoke the persona panel, it'll offer this flow again."

**Very thin answers:** Generate complete personas anyway — lean on reasonable inference. The calibration system flags generic personas over time (5+ runs of monotone verdicts).

**Personas already exist elsewhere:** The creation flow only triggers when `docs/personas/` has no persona files at all. Existing groups are handled by Stage 1's normal group selection logic.

## Boundaries

The creation flow does NOT:
- Edit or update existing personas
- Create personas for a second group in the same invocation
- Validate personas against real content (that's the panel's job)
- Run more than 7 Q&A questions

<!-- Note: {base-directory} refers to the skill's root directory (skills/persona-panel/), not this file's directory (skills/persona-panel/modes/). -->
```

**Step 3: Verify the file was written**

Read `skills/persona-panel/modes/persona-creation-flow.md` — confirm it starts with the HTML comment and contains all four phases.

**Step 4: Commit**

```bash
git add skills/persona-panel/modes/persona-creation-flow.md
git commit -m "feat(persona-panel): add persona creation flow document"
```

---

### ✅ Task 2: Update SKILL.md to delegate to the creation flow

**Files:**
- Modify: `skills/persona-panel/SKILL.md` (the "If no personas found" block in Stage 1)

**Step 1: Read the current SKILL.md**

Read `skills/persona-panel/SKILL.md` in full. Locate the "If no personas found" block (currently line 19).

Current text:
```
**If no personas found:** Stop and tell the user: "No persona files found in `docs/personas/`. Create persona files using the template at `{base-directory}/references/persona-template.md`."
```

**Step 2: Replace the block**

Replace the single "If no personas found" line with:

```markdown
**If no personas found:** Present the opt-out prompt:

> "No persona files found. I can create them now through a short Q&A, or you can add them manually using the template at `{base-directory}/references/persona-template.md`."

If the user chooses manual creation, stop. Otherwise, read `{base-directory}/modes/persona-creation-flow.md` and follow its process. If the mode file cannot be Read, STOP and tell the user the plugin installation may be incomplete. After the creation flow completes (user has been prompted for content), re-glob `docs/personas/` and continue from the group selection logic below (multiple groups → ask, one group → proceed).
```

> **Behavior change:** Users who already have personas in `docs/personas/` are completely unaffected — this block only triggers when the glob finds zero persona files. The change replaces a dead-end error message with an interactive creation flow.

**Step 3: Verify the edit**

Read `skills/persona-panel/SKILL.md` lines 17-28 to confirm the replacement landed correctly and the surrounding Stage 1 logic is intact.

**Step 4: Commit**

```bash
git add skills/persona-panel/SKILL.md
git commit -m "feat(persona-panel): replace dead-end with creation flow delegation"
```

---

### Task 3: Bump plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json` (the `version` field)
- Modify: `.claude-plugin/marketplace.json` (the `version` field)

**Step 1: Read both files**

Read `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Confirm current version is `0.16.0`.

**Step 2: Bump version in both files**

Change `"version": "0.16.0"` to `"version": "0.17.0"` in both files.

This is a minor version bump: new feature (creation flow), no breaking changes.

**Step 3: Verify both files show the same version**

Read both files and confirm `0.17.0` appears in each.

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version to 0.17.0"
```

---

### Task 4: Update README.md changelog

**Files:**
- Modify: `README.md` (the changelog section)

**Step 1: Read README.md**

Read `README.md` to find the changelog section and the current format.

**Step 2: Add changelog entry**

Add a new entry at the top of the changelog for version 0.17.0:

```markdown
### 0.17.0
- **persona-panel:** Add guided persona creation flow for cold-start path — four-phase Q&A replaces dead-end when no personas exist
```

Follow the existing changelog entry format exactly (indentation, bullet style, skill prefix pattern).

**Step 3: Verify the entry**

Read the changelog section to confirm the new entry appears at the top and follows the format of surrounding entries.

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add 0.17.0 changelog entry for persona creation flow"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Task granularity | 4 tasks (flow doc, SKILL.md edit, version bump, changelog) | Single monolithic task, or splitting flow doc into multiple tasks |
| 2 | No test tasks | Skill files are markdown — no automated tests applicable | Adding manual verification tasks, adding schema validation |
| 3 | Version bump as 0.17.0 (minor) | Follows semver: new feature, no breaking changes | Patch bump (0.16.1) — wrong, this is a feature not a fix |

### Appendix: Decision Details

#### Decision 1: Task granularity
**Chose:** 4 separate tasks with individual commits
**Why:** Each task produces a logically independent artifact: the flow document, the SKILL.md integration, the version bump, and the changelog entry. Independent commits make it easy to revert the SKILL.md delegation without losing the flow document, or to adjust the flow document without touching the integration point. The flow document itself is a single file with no code dependencies, so splitting it further would create artificial boundaries.
**Alternatives rejected:**
- Single monolithic task: Would create one giant commit mixing new files, edits, and metadata changes — harder to review and revert.
- Splitting flow doc into phases: Each phase references the others (e.g., Phase 2 adapts based on Phase 1 results). Splitting would create partial files that can't be validated independently.

#### Decision 2: No test tasks
**Chose:** No automated test tasks
**Why:** This plugin is a collection of markdown skill files processed by the Claude Code harness at runtime. There is no test runner, no build step, no type system — the "tests" in the design doc are manual invocation scenarios (e.g., "invoke in a repo with no personas"). The skill files are plain markdown read into LLM context; their correctness is verified by the critique panel checking structure, cross-references, and template field coverage. Adding a test task that just says "manually invoke the skill" would violate the Manual Steps Policy (can't be automated by Ralph loop).
**Alternatives rejected:**
- Manual verification tasks: Violates the plan's Manual Steps Policy — Ralph loop can't pause for manual invocation.
- Schema validation script: Over-engineering. The template has 20 fields documented in plain markdown; a validation script would need to parse natural language instructions, which is exactly what the LLM already does.

#### Decision 3: Version bump as 0.17.0
**Chose:** Minor version bump from 0.16.0 to 0.17.0
**Why:** Semver: this adds a new feature (persona creation flow) without breaking any existing behavior. The persona-panel skill works identically for users who already have personas — the creation flow only activates on cold start. A patch bump would be incorrect because this isn't a bug fix.
**Alternatives rejected:**
- Patch bump (0.16.1): Wrong semver signal — this is new functionality, not a fix.
