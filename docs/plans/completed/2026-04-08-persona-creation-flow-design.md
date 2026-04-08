# Persona Creation Flow — Design Document

**Date:** 2026-04-08
**Scope:** Add guided persona creation to persona-panel skill's cold-start path
**Architecture:** Flow document (`modes/persona-creation-flow.md`) delegated from Stage 1
**Mockups:** docs/mockups/persona-creation-flow.html

## Problem

The persona-panel skill dead-ends when no persona files exist in `docs/personas/`. It tells the user to create files using a template and stops. Every other evaluation skill in the plugin auto-selects from pre-built resources; persona-panel is the only one that requires users to build infrastructure from scratch before it works.

## Success Criteria

1. **Cold-start elimination:** A user invoking `/aligned:persona-panel` in a repo with no personas reaches their first panel evaluation without leaving the skill or manually creating files.
2. **Structural validity:** Every generated persona file passes template validation — all 20 bullet fields populated, no TODOs, no placeholders. Review Lens fields are specific enough to differentiate persona reactions (not generic "wants value" statements).
3. **Time to first panel:** The creation flow completes in under 10 conversational turns (context detection + Q&A + approval), getting users to their first evaluation quickly.

## Decision Log

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Flow document in `modes/`, not separate skill or inline | Avoids bloating SKILL.md from 121 to 250+ lines. A separate skill would add plugin surface (README table, kickstart permissions, version bump) for a flow that only triggers from one place. Placed in `modes/` because it's a flow-control document — `references/` stores data files (templates, prompts) in this codebase. |
| 2 | Auto-detect existing docs (eliminates need for a mode menu) | Users likely have buyer knowledge already, possibly documented. The flow scans for context opportunistically and adapts Q&A depth based on what it finds — no explicit "Q&A mode" vs. "document import mode" choice needed. |
| 3 | Full set in one session | Get users to a working panel quickly. One-at-a-time would slow adoption. Trade-off: with a 7-question cap across 1-4 personas, many fields are filled by inference. These are intentionally rough drafts — the calibration system flags generic personas after 5+ panel runs, and users can refine individual files anytime. |
| 4 | Summary approval, then batch generate | Users approve the set of personas (name, archetype, differentiator) before any files are written. No per-persona review — that's what the panel itself is for. |
| 5 | Return control to Stage 1 after creation | After generating personas, prompt for content, re-glob, and continue to Stage 2. The user flows straight into their first panel run. |

## Design

### SKILL.md Change

Replace the current "If no personas found" block in Stage 1 with:

```
**If no personas found:** Read `{base-directory}/modes/persona-creation-flow.md`
and follow its process. After the creation flow completes, prompt the user for
content to evaluate, then re-glob `docs/personas/` and continue from the group
selection logic (multiple groups → ask, one group → proceed).
```

Add a one-line opt-out before entering the flow:

```
"No persona files found. I can create them now through a short Q&A, or you can
add them manually using the template at `{base-directory}/references/persona-template.md`."
```

No other changes to SKILL.md.

### Creation Flow (`modes/persona-creation-flow.md`)

The flow has four phases: Context Detection, Q&A, Summary Approval, and File Generation.

#### Phase 1: Context Detection

Scan for existing context before asking anything. Sources in order of specificity:

1. **`docs/` directory** — files with buyer/persona/ICP/audience/customer keywords in filename or content
2. **`content/` and `marketing/` directories** — marketing briefs, sales collateral, positioning docs
3. **`CLAUDE.md` / project instructions** — target audience, product description, market context
4. **`README.md`** — product description, value prop, who it's for

**False-positive handling:** Keyword matches on filenames alone are low-confidence (e.g., `api-customers.md` may be an API doc, not buyer research). When presenting found docs, show at most 5 files and frame as opt-in: "I found these docs that might describe your buyers: [list]. Should I use any of these as a starting point, or skip straight to questions?"

**If the user declines the found docs:** Proceed to Phase 2 using the minimal/no-context path (full Q&A).

**If nothing found:** Skip to Q&A: "I didn't find existing buyer documentation. I'll ask a few questions to understand your buyers."

**If directories don't exist:** Silently skip them. Only report what was found, not what wasn't.

No mode selection, no menu. Use what's there, ask for what's missing.

#### Phase 2: Q&A

Adapts depth based on how much context Phase 1 found.

**If rich context was found and accepted:** Extract buyer types from docs and confirm: "Based on [source], I see these buyer types: [list]. Is this right, or should I add/remove any?" Then 1-2 targeted questions to fill gaps (psychology, objections, communication style).

**If minimal/no context:** Ask sequentially, one at a time:

1. "What does your product/service do, in one sentence?" *(skip if obvious from CLAUDE.md/README)*
2. "Who are the distinct buyer types you sell to? Could be one, could be several — just roles or titles."
3. "For each buyer, what's the main problem they're trying to solve when they find you?"
4. "What makes each buyer type skeptical? What turns them off?"
5. "How do these buyers talk — formal/casual, data-driven/story-driven, technical/non-technical?"

**Single-buyer case:** If the user names only one buyer type, proceed normally. Note that a single-persona panel has reduced diagnostic value since there's no cross-persona contrast, but it's still useful.

**Adaptive depth heuristics:**
- **Rich answer:** 2+ sentences per buyer, covers motivations or objections without prompting → skip follow-up questions on that topic.
- **Thin answer:** Single phrase, role title only, no detail on motivations → ask a follow-up to deepen (e.g., "What keeps [role] up at night about this problem?").
- Cap at 7 total questions regardless. After 7, proceed with what you have.

**Group naming:** Infer group directory name from the buyer set (e.g., `b2b-buyers/`, `enterprise/`). If unclear, ask.

#### Phase 3: Summary Approval

Display a table of all personas before writing anything:

```markdown
I'll create these personas in docs/personas/<group>/:

| File | Name | Archetype | Key Differentiator |
|------|------|-----------|--------------------|
| vp-engineering.md | Dana Chen | The Build-vs-Buy Evaluator | Technical depth, allergic to vendor lock-in |
| head-of-sales.md | Marcus Rivera | The Revenue Operator | ROI-first, wants proof not promises |
| founder-ceo.md | Sarah Kim | The Scaling Founder | Speed over polish, pattern-matches against past burns |

These are rough drafts — the panel will reveal which personas need sharpening over time. Proceed, or adjust?
```

User can adjust names, add/remove personas, or change archetypes before proceeding.

#### Phase 4: File Generation

**On approval:**

- Generate all persona files using the template structure at `{base-directory}/references/persona-template.md`
- Every field populated — no TODOs, no placeholders
- Use Q&A answers + extracted doc context to fill all 20 bullet fields
- Infer reasonable defaults for fields not explicitly addressed (e.g., "Years in role" estimated from archetype)
- File naming: slugified from role/title, lowercase, hyphenated (e.g., `vp-engineering.md`)
- Create group directory if it doesn't exist

**After generation:** Prompt the user for content to evaluate: "Personas created. To run your first panel, paste or reference the content you'd like to test." Then return control to Stage 1. Stage 1 re-globs, finds the new group, continues to Stage 2.

### Edge Cases

**User aborts mid-flow:** If the user says "stop", "nevermind", "I'll do this later", or otherwise signals they want to exit, stop cleanly. Don't write partial files. Confirm: "No files written. Next time you invoke the persona panel, it'll offer this flow again." Re-invocation always restarts from Phase 1 (no resume) — the Q&A is short enough that restart cost is low.

**User wants to abort but isn't told they can:** The opt-out prompt at flow start and the approval gate in Phase 3 are the two natural exit points. No additional abort prompts mid-Q&A — interrupting the flow with "you can stop anytime" messaging adds friction to the common case.

**Very thin answers:** Generate complete personas anyway — lean on reasonable inference. The calibration system flags generic personas over time (5+ runs of monotone verdicts).

**Personas already exist elsewhere:** The creation flow only triggers when `docs/personas/` has no persona files at all. Existing groups are handled by Stage 1's normal group selection logic.

### Boundaries

The creation flow does NOT:
- Edit or update existing personas
- Create personas for a second group in the same invocation
- Validate personas against real content (that's the panel's job)
- Run more than 7 Q&A questions

## Files Changed

| File | Change |
|------|--------|
| `skills/persona-panel/SKILL.md` | Replace "If no personas found" block (1 line) with opt-out prompt + delegation to modes/ |
| `skills/persona-panel/modes/persona-creation-flow.md` | New file — the entire creation flow |

## Testing

- Invoke `/aligned:persona-panel` in a repo with no `docs/personas/` directory → should trigger creation flow
- Invoke in a repo with existing personas → should skip creation flow entirely
- User selects manual creation at opt-out prompt → should show template path and stop
- Context detection with rich docs present → should present docs, cap at 5, accept user's selection
- Context detection with no relevant docs → should skip straight to Q&A
- User declines found docs → should fall back to full Q&A path
- Q&A with single buyer type → should proceed normally with note about reduced contrast
- Q&A hits 7-question cap → should stop asking and proceed to summary
- User adjusts personas at summary approval → should update and re-present
- User aborts at any point → should write no files, confirm clean exit
- Generated persona files → should have all 20 bullet fields populated, no TODOs
- Template file missing → should error clearly, not generate malformed files
- After generation, Stage 1 re-globs and prompts for content → should transition to Stage 2
