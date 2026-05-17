# KB-093: D11 vertical-slice biases toward favorable-case validation

- **Type:** design defect (test sequencing / validation rigor)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M10)
- **Critic:** Architect
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`

## Finding (verbatim from critique)

> **M10. D11 vertical-slice biases toward favorable-case validation** `[Architect]`
> Build step 3 picks `5-components-positioning` because it has no mode-detection — but that makes it the easiest case. Hard cases (verification-style frameworks) come later, after deletion. Action: re-sequence OQ-4 resolution to test `proof-points-audit` alongside the vertical slice.

## Proposed action

Re-sequence so OQ-4 is resolved against `proof-points-audit` (a verification-style framework) in parallel with the `5-components-positioning` vertical slice. Two-framework validation surface catches the hard case before irreversible deletions.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
