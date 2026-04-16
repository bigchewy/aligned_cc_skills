<!-- Mode file: Read into context by persona-panel Stage 1. Do not add YAML frontmatter. -->

# Persona Creation Flow

Guided creation of buyer personas when `docs/personas/` is empty. Four phases: Context Detection, Q&A, Summary Approval, File Generation.

## Contents

- Phase 1: Context Detection
- Phase 2: Q&A
- Phase 3: Summary Approval
- Phase 4: File Generation
- Edge Cases
- Boundaries

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

Then return control to Stage 1. Stage 1 re-globs both `docs/personas/` and `brand/personas/`, finds the new group, continues to Stage 2.

## Edge Cases

**User aborts mid-flow:** If the user says "stop", "nevermind", "I'll do this later", or otherwise signals exit, stop cleanly. Don't write partial files. Confirm: "No files written. Next time you invoke the persona panel, it'll offer this flow again."

**Very thin answers:** Generate complete personas anyway — lean on reasonable inference. The calibration system flags generic personas over time (5+ runs of monotone verdicts).

**Personas already exist elsewhere:** The creation flow only triggers when neither `docs/personas/` nor `brand/personas/` has persona files. Existing groups in either location are handled by Stage 1's normal group selection logic.

## Boundaries

The creation flow does NOT:
- Edit or update existing personas
- Create personas for a second group in the same invocation
- Validate personas against real content (that's the panel's job)
- Run more than 7 Q&A questions

<!-- Note: {base-directory} refers to the skill's root directory (skills/persona-panel/), not this file's directory (skills/persona-panel/modes/). -->
