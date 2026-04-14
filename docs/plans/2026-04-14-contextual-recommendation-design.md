**Date:** 2026-04-14
**Status:** Draft
**Mockups:** docs/mockups/contextual-recommendation.html
**Depends on:** docs/plans/completed/2026-04-13-registry-unification-design.md (complete, merged to main)

# Contextual Recommendation Design

## Goal

When `use-advisor` or `use-framework` is invoked without a specific entry name, recommend the best match from the YAML registry based on task context. Present 2-3 alternatives and let the user proceed or override. Only auto-select when match confidence is high; show a filtered shortlist when confidence is low. Never dump a raw list of 65+ entries as the default experience.

**Problems solved:**
1. **No intent-based selection.** Users who don't know the catalog must browse a raw alphabetical list of 65 advisors or 139 frameworks. The middle case — "user knows the plugin but not which entry to pick" — is unserved.
2. **Context is wasted.** The user's conversation often contains strong signals about what they need, but the current skills ignore everything except the explicit args string.
3. **Bare invocations are unhelpful.** `/aligned:use-advisor` with no args produces a wall of names with no guidance on what fits the user's situation.

**Success criteria:**
- Named invocations continue to work identically (no regression)
- Contextual invocations produce a relevant recommendation when match confidence is high
- Weak matches produce a filtered shortlist rather than a bad guess
- Conversation context is used when no explicit args are provided
- Bare invocations with no context prompt the user rather than listing everything
- Both skills use the same scoring logic via a shared file
- The user can always escape to the full listing

## Prerequisites

1. **Registry unification complete.** `advisors/registry.yaml` and `frameworks/registry.yaml` must exist with all metadata fields populated. This design consumes the registries; it does not create them. (Status: merged to main.)

2. **Advisor profiling (incremental, not blocking).** 35 unprofiled advisors lack `best_for`, `not_for`, and `evaluation_expertise`. Unprofiled advisors are excluded from contextual scoring — they remain accessible via named invocation (`/aligned:use-advisor seth-godin`) but won't appear in recommendations or shortlists. As advisors are profiled, they automatically become eligible for scoring. Full profiling is tracked as a parallel workstream, not a prerequisite for shipping.

## Decision Log

| # | Decision | Rationale | Source |
|---|----------|-----------|--------|
| D1 | Same heuristic, different field mappings for advisors vs frameworks | Metadata is structurally parallel: advisor `best_for` maps to framework `use_when`, both share `domains`, advisor `not_for` is optional exclusion. Critique panel and auto-router precedents use the same decision structure for both entity types. | Architect |
| D2 | Name-first cascade, no detection heuristic | Try name matching first (deterministic). If no match, args are task context by elimination. Avoids impossible classification of ambiguous inputs like "marketing" or "landing page." | Architect |
| D3 | Use conversation context when no args provided | The LLM already has the full conversation when the skill fires. Instruction-only change, no infrastructure. | User |
| D4 | Prompt for context on true bare invocations | Better than dumping a raw list. "What problem are you working on?" with "list all" escape hatch. | User |
| D5 | Two-stage scoring (domain filter + semantic ranking) | Single-pass LLM scoring is viable at ~65 entries but risky at 139 (position bias, familiarity bias, lost-in-the-middle). LLM-assisted domain pre-filter narrows candidates to ~10-20 where semantic ranking is reliable. Applied to both entity types for consistency. | Architect |
| D6 | Natural language priority rules, not numeric scoring | Scoring runs in LLM instructions, not compiled code. Numeric weights on prose fields like `best_for` add a lossy translation step. Natural language matching plays to LLM strengths. Follows critique panel pattern, not auto-router pattern. Trade-off: recommendations are not fully deterministic and not auditable like numeric scoring. Acceptable for v1; precomputed index is the upgrade path if stability becomes an issue. | Architect |
| D7 | Structural confidence test, bias toward shortlisting | Auto-select only when the LLM can articulate why the top pick matches and the runner-up doesn't. If it can't articulate the gap, shortlist instead. | User + Architect |
| D8 | Brainstorming-style auto-select UX | "Selected: X" with reasoning, 2-3 alternatives, "to switch, just say so." Skill proceeds immediately with the selection. Faster than a confirmation gate. | User |
| D9 | Shared scoring logic in `skills/_shared/contextual-recommendation.md` | Single source of truth. Follows critique panel orchestration pattern (already in `skills/_shared/`). Prevents drift between the two skill files. | User |
| D10 | Exclude unprofiled advisors from scoring, profile incrementally | Unprofiled advisors (no `best_for`/`not_for`) are excluded from contextual recommendation — they can't compete meaningfully on `domains` alone. They remain accessible via named invocation. As profiles are added, advisors automatically become scoring-eligible. Avoids blocking the feature on a content project. | User (revised post-critique) |

---

## Section 1: Invocation Cascade

The skill follows a four-step cascade, evaluated in order. The first match wins.

**Path 1 — Named match** (args match a slug or display name):
Existing behavior, unchanged. Case-insensitive substring match against registry entries. Single match → adopt/run. Multiple matches → disambiguate. This path short-circuits before any scoring runs.

**Path 2 — Contextual from args** (args present, no name match):
Args didn't match any entry name, so treat them as task context. Read the full registry, run two-stage scoring against the args. Route to either auto-select or shortlist based on confidence.

**Path 3 — Contextual from conversation** (no args, conversation has task context):
No args provided, but recent conversation contains relevant context — the user has been discussing a topic, project, or problem domain. Extract task context from conversation, then score identically to Path 2.

**Path 4 — Prompt for context** (no args, no useful conversation context):
Nothing to score against. Ask: "What problem are you working on, or what are you trying to accomplish? I'll recommend the best fit." Include escape hatch: "Or say 'list all' to browse the full catalog."

**Transition between Paths 3 and 4:** The LLM judges whether the conversation contains "useful context." Instruction: if recent messages describe a task, project, or problem domain, use that as context (Path 3). If the conversation is empty, generic, or unrelated to advisory/framework work, prompt the user (Path 4).

**Path 3/4 boundary examples:**

| Conversation state | Path | Reasoning |
|---|---|---|
| User has been discussing their landing page copy for 5 messages | Path 3 | Clear task context: landing page, copywriting |
| User asked about git commands, then invoked use-advisor | Path 4 | Conversation is about tooling, not an advisory-relevant task |
| User said "I'm preparing for a sales call next week" 3 messages ago | Path 3 | Task context: sales preparation |
| Fresh conversation, first message is `/aligned:use-advisor` | Path 4 | No conversation history at all |
| User discussed multiple unrelated topics across a long session | Path 4 | Ambiguous — multiple topics, no clear dominant task |

---

## Section 2: Two-Stage Scoring

### Stage 1 — Domain Filter (LLM-assisted keyword extraction)

Extract domain signals from the user's task context — the LLM maps natural language input (e.g., "I need a landing page") to domain tags (e.g., `[landing-pages, conversion-optimization]`). Then match extracted tags against each registry entry's `domains` tag list. Any entry sharing at least one domain tag passes to Stage 2. Entries with zero overlap are excluded.

**Note:** The extraction step is LLM-assisted (mapping prose to tags), but the matching step is straightforward tag overlap. This is not full semantic inference — it's constrained to the vocabulary of existing `domains` tags in the registry.

**Scoring eligibility:** Entries with `domains: []` (empty tag list) are invisible to Stage 1 — they cannot match any extracted tag. For advisors, this means unprofiled entries with empty domains are naturally excluded. If Stage 1 is skipped (zero-candidate fallback), these entries become eligible but compete at a disadvantage since Stage 2's primary match field (`best_for`) is also empty.

Expected reduction: 30 profiled advisors → ~5-10 candidates, 139 frameworks → ~10-20 candidates. To mitigate position bias in Stage 2, present candidates in shuffled order rather than registry order.

**Debuggability note:** Natural language scoring is not auditable the way numeric scoring is. Recommendations may vary across invocations for the same input. This is an acceptable v1 trade-off — the LLM's semantic matching strength outweighs the consistency loss at this scale. If recommendation stability becomes a user-reported issue, a precomputed index approach (matching the auto-router's `skill-router.json` pattern) is the upgrade path.

### Stage 2 — Semantic Ranking (LLM, natural language priority rules)

On the filtered candidate set only, apply the priority rules in order:

1. **Hard exclusion** — Remove any entry whose exclusion field matches the task's primary domain. A match here means "this entry explicitly says it's not for this kind of work."

2. **Primary match** — Semantic comparison of the user's task against each entry's inclusion field. This is the strongest signal — it describes what kind of work this entry is designed for. Entries with a clear match advance; weak or irrelevant entries drop out.

3. **Domain depth** — Among passing entries, those with more domain tag overlap rank higher. Tiebreaker role only.

4. **Disambiguation** — Used when steps 2-3 produce a tie. Finer-grained fields provide additional context about how the entry operates.

### Field Mapping

| Scoring role | Advisor field | Framework field |
|---|---|---|
| Hard exclusion | `not_for` | *(none today — deliberate; add if frameworks need exclusion rules later)* |
| Primary match | `best_for` | `use_when` |
| Domain overlap | `domains` | `domains` |
| Disambiguation | `evaluation_expertise`, `summary` | `purpose`, `category` |

### Edge Case: Zero Candidates from Stage 1

If no entry shares a domain tag with the user's context, skip Stage 1 and fall back to full-registry Stage 2 ranking. This handles novel or cross-cutting tasks that don't map cleanly to existing domain tags. This is a rare fallback, not the default path.

---

## Section 3: Confidence Threshold & UX Modes

After Stage 2 ranking, the LLM decides how to present results. Two modes, determined by a structural confidence test — not a numeric score.

### Auto-select mode (high confidence)

One entry's primary match field clearly describes the user's task, and the runner-up is noticeably less relevant. The LLM must be able to articulate *why* the top pick matches and *why* the second-best doesn't match as well. If it can't articulate the gap, it's not confident.

Presentation (mirrors brainstorming mode selection):

```
**Selected: {Name}** — {one-sentence why this fits your task}
*Alternatives:*
- {Runner-up 1} — {one-sentence rationale}
- {Runner-up 2} — {one-sentence rationale}

*To switch, re-invoke the skill with a different name. Or say "list all" to browse the full catalog.*
```

The skill immediately proceeds with the selected entry (adopts the advisor persona or begins the framework's Phase 1). To switch after auto-select, the user re-invokes the skill (e.g., `/aligned:use-advisor april-dunford`). This matches the existing switching mechanism — there is no inline switch; persona/framework changes require a new invocation.

### Shortlist mode (low confidence)

Two or more entries are plausibly relevant, or the best match is only tangentially related. No auto-selection.

```
**Based on your context, these look relevant:**
1. {Name} — {one-sentence rationale}
2. {Name} — {one-sentence rationale}
3. {Name} — {one-sentence rationale}

*Which would you like to use? Or say "list all" to browse the full catalog.*
```

### Confidence bias

The instruction explicitly states that auto-select is reserved for unambiguous matches. When in doubt, shortlist. This mirrors the brainstorming mode detection pattern: auto-route when signals are clear, ask when signals are mixed.

---

## Section 4: Shared Infrastructure

A single file `skills/_shared/contextual-recommendation.md` defines the scoring logic, referenced by both `use-advisor/SKILL.md` and `use-framework/SKILL.md` via a Read instruction.

### File structure

The file contains three instruction blocks:

**Block 1 — Context extraction.** Instructions for extracting task context from the available sources. If args are present and didn't match a name, use them. If no args, scan recent conversation for task/problem/domain references. If neither yields signal, prompt the user (Path 4).

**Block 2 — Two-stage scoring.** The domain filter and semantic ranking instructions, parameterized by entity type. The calling skill passes which registry to read and which field mapping to use. The file defines:
- How to extract domain keywords from task context
- How to match against the `domains` tag list (Stage 1)
- The priority rule set for semantic ranking (Stage 2)
- The field mapping table (advisor fields vs framework fields)
- The zero-candidates fallback (skip Stage 1, full-registry Stage 2)

**Block 3 — Confidence and presentation.** The structural confidence test and both UX templates (auto-select and shortlist). Includes the "bias toward shortlisting" instruction and the "list all" escape hatch.

### How skills reference it

Each SKILL.md adds a new step between name matching (existing) and the current "no match → list all" behavior:

> If no name match was found and args are present (or conversation has task context), read `skills/_shared/contextual-recommendation.md` (plugin-relative path) and follow its process. Pass entity type: `advisor` (or `framework`).

**Path resolution:** Both `use-advisor` and `use-framework` already use plugin-relative paths for registry reads (e.g., `advisors/registry.yaml`). The shared file follows the same convention — `skills/_shared/contextual-recommendation.md` is relative to the plugin root directory, consistent with how both skills reference other plugin files. No `{base-directory}` mechanism needed.

The shared file is self-contained — it produces the recommendation/shortlist output directly without reading back into the calling skill.

### Fallback if file is missing

Degrade to existing behavior (list all). Same pattern as the YAML registry's glob fallback.

---

## Section 5: Skill File Changes

Both `use-advisor/SKILL.md` and `use-framework/SKILL.md` need the same structural change: insert the contextual path between the existing name-match step and the existing bare-listing step.

### Current flow (both skills)

1. Discover entries (read registry)
2. Extract names
3. If args provided → match against names → success or "list all"
4. If no args → list all

### New flow

1. Discover entries (read registry) — *unchanged*
2. Extract names — *unchanged*
3. If args provided → match against names
   - Match found → adopt/run — *unchanged*
   - Multiple matches → disambiguate — *unchanged*
   - **No match → read `skills/_shared/contextual-recommendation.md`, pass args as task context** — *new*
4. If no args → check conversation for task context
   - **Context found → read shared file, pass extracted context** — *new*
   - **No context → prompt user for context, with "list all" escape** — *new*

### What doesn't change

- Named matching logic (match-found path)
- Framework Phase 1 execution / advisor persona adoption
- Composability between use-advisor and use-framework
- Voice handling
- The "Avoid These Mistakes" sections

### Net change per skill file

~10-15 lines added to the matching step, replacing the single "No match → list all" line. No structural reorganization of the existing steps.

### Critique panel is unaffected

The critique panel has its own selection logic in `critique-panel-orchestration.md` with calibration examples tuned for design review. It selects critics for a different purpose — it doesn't use the contextual recommendation path.

---

## Section 6: Calibration & Testing

### Calibration examples

Embedded in the shared scoring file. These anchor the LLM's scoring behavior at runtime and define the acceptance criteria for manual testing.

**Single-signal examples (clear matches):**

| User context | Entity type | Expected result | Mode |
|---|---|---|---|
| "I need to build a landing page" | advisor | Oli Gardner (auto-select) | High confidence |
| "I need to build a landing page" | framework | Landing Page Assembly (auto-select) | High confidence |
| "help me with pricing" | advisor | Shortlist: Robbie Kellman Baxter, April Dunford, Patrick Campbell | Low confidence |
| "I'm paralyzed by a big decision" | framework | Fear Setting (auto-select) | High confidence |
| "my back hurts" | framework | Shortlist: health-movement frameworks | Low confidence |

**Multi-domain and boundary examples:**

| User context | Entity type | Expected result | Mode |
|---|---|---|---|
| "I need to position my product and build the landing page for it" | advisor | Shortlist: April Dunford (positioning), Oli Gardner (landing pages) | Low confidence (cross-domain) |
| "negotiation" | advisor | Chris Voss (auto-select if profiled; shortlist if multiple negotiation advisors) | Depends on profiling |
| "I want to grow my podcast audience on social media" | framework | Shortlist: podcasting + social-media category frameworks | Low confidence (cross-category) |
| "help me be a better manager" | advisor | Shortlist: leadership-domain advisors (Lara Hogan, Ram Charan) | Low confidence |

**Near-miss naming examples (Path 1 vs Path 2 boundary):**

| Args | Expected path | Reasoning |
|---|---|---|
| "fear setting" | Path 1 (named) | Matches framework slug `fear-setting` |
| "I'm afraid to make this decision" | Path 2 (contextual) | No name match; scored against `use_when` fields |
| "the work" | Path 1 (named) | Matches framework slug `the-work` |
| "I need to do the work on my beliefs" | Path 2 (contextual) | No exact name match; task context about belief work |

### Manual verification scenarios

| Scenario | Expected behavior |
|---|---|
| `/aligned:use-advisor steve-jobs` | Named match, no scoring (existing behavior preserved) |
| `/aligned:use-advisor I need to position my product` | Contextual → auto-select April Dunford |
| `/aligned:use-advisor` after discussing landing pages | Conversation context → recommend Oli Gardner |
| `/aligned:use-advisor` cold start, no conversation | Prompt for context with "list all" escape |
| `/aligned:use-framework` with vague context ("help me think") | Prompt for context (insufficient signal) |
| Shared file missing | Degrade to list all |

### Eval scenarios

If `e2e/` exists, add contextual recommendation scenarios to `e2e/eval-surface.yaml` and corresponding promptfoo test cases:

**Scenarios to add:**

| Scenario | Assertion |
|---|---|
| `use-advisor` with clear single-domain context | Recommends a profiled advisor whose `best_for` matches |
| `use-advisor` with ambiguous multi-domain context | Produces a shortlist, not an auto-select |
| `use-advisor` with no args, no conversation | Prompts for context (does not list all) |
| `use-framework` with clear `use_when` match | Recommends the matching framework |
| `use-framework` with cross-category context | Produces a shortlist spanning categories |
| `use-advisor` with args matching a name | Takes Path 1, no scoring |
| `use-advisor` with unprofiled advisor name | Named match works (Path 1 bypasses scoring eligibility) |

Each scenario should verify both the path taken and the output format (auto-select template vs shortlist template vs prompt template).

---

## Section 7: Implementation Order

| Phase | What | Depends on |
|---|---|---|
| 1 | Create `skills/_shared/contextual-recommendation.md` with scoring logic and calibration examples | — |
| 2a | Update `skills/use-advisor/SKILL.md` — add contextual path, scoring eligibility filter | 1 |
| 2b | Update `skills/use-framework/SKILL.md` — add contextual path | 1 |
| 3 | Manual verification against scenario table | 2a, 2b |
| 4 | Add eval scenarios to `e2e/eval-surface.yaml` and promptfoo test cases (if `e2e/` exists) | 2a, 2b |

**Parallel workstream (not blocking):** Profile 35 unprofiled advisors (`best_for`, `not_for`, `evaluation_expertise`). As each advisor is profiled, they automatically become eligible for contextual scoring — no code changes needed.

---

## Impact Summary

### Files created (new)

| File | Purpose |
|---|---|
| `skills/_shared/contextual-recommendation.md` | Shared two-stage scoring logic and UX templates |

### Files modified

| File | Change |
|---|---|
| `skills/use-advisor/SKILL.md` | Insert contextual path between name-match and bare-listing steps |
| `skills/use-framework/SKILL.md` | Insert contextual path between name-match and bare-listing steps |

### Files unaffected

| File | Reason |
|---|---|
| `advisors/registry.yaml` | Consumed as-is, no schema changes |
| `frameworks/registry.yaml` | Consumed as-is, no schema changes |
| `skills/_shared/critique-panel-orchestration.md` | Separate selection logic for different purpose |
| `skills/add-advisor/SKILL.md` | No interaction with contextual recommendation |
| `skills/add-framework/SKILL.md` | No interaction with contextual recommendation |
