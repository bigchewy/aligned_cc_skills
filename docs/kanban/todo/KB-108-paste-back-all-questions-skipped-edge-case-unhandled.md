# KB-108: Paste-back all-questions-skipped edge case is unhandled

- **Type:** design defect (edge case under-specified)
- **Severity:** LOW
- **Source:** Round 1 critique of reverse-engineered-brand revamp (L6)
- **Critic:** QA Engineer
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Mockup:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

## Finding (verbatim from critique)

> **L6. Paste-back: all-questions-skipped edge case unhandled** `[QA Engineer]`
> Paste-back outputs "drop everything" with no anchor. Action: specify behavior — either warn user or suppress paste-back.

## Proposed action

Specify in the design what the paste-back widget does when every question is skipped:
- **Option A:** Show a warning ("You've skipped every question — paste-back will tell the framework to drop everything. Continue?")
- **Option B:** Suppress the paste-back button entirely until at least one question has a non-Skip decision.

Either is fine; current behavior (silent "drop everything" payload) is the bad case.

## Created

2026-05-16
