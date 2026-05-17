# KB-106: D15 sweeps 5 framework files in one batch — split for lower blast radius

- **Type:** design defect (batch size / blast radius)
- **Severity:** LOW
- **Source:** Round 1 critique of reverse-engineered-brand revamp (L4)
- **Critic:** Architect
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`

## Finding (verbatim from critique)

> **L4. D15 sweeps 5 framework files in one batch** `[Architect]`
> Build step 4 is one batch of 5; safer to split 4a (one) + 4b (rest). Lowers blast radius. Action: split build step 4.

## Proposed action

Split build step 4 into:
- **4a:** Apply changes to one framework file first (smoke test).
- **4b:** Apply changes to the remaining four.

If 4a surfaces an issue, the blast radius is one file instead of five.

## Created

2026-05-16
