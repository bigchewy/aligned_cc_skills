# KB-091: Compound-question regex is undefined in PHASE 2.4

- **Type:** design defect (under-specified validator)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M7)
- **Critic:** QA Engineer
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Mockup:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

## Finding (verbatim from critique)

> **M7. Compound-question regex is undefined** `[QA Engineer]`
> PHASE 2.4 says "compound-question regex over each `question`" but never specifies the regex. Mockup questions like Q-12 ("pricing model — per-member, per-transport, or hybrid?") would trip a naive ` or `/`—` regex but are actually atomic. Action: specify the regex with positive/negative tests against mockup questions, or drop it.

## Proposed action

Either:
1. **Specify the regex** with worked positive and negative tests using actual questions from the mockup (Q-12 must be classified atomic, true compounds must be flagged); OR
2. **Drop the compound-question check** from PHASE 2.4 if a precise regex isn't defensible.

A vague check that misfires on atomic questions like Q-12 is worse than no check.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
