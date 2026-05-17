# KB-094: Layer 4 integration test anchors on stale Marley + possibly stale spec

- **Type:** design defect (test fixture staleness)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M11)
- **Critic:** QA Engineer
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Related:** `docs/brand-folder-spec.md`

## Finding (verbatim from critique)

> **M11. Layer 4 integration test anchors on stale Marley + possibly stale spec** `[QA Engineer]`
> Build step 5 explicitly calls Marley's JSON stale, yet Layer 4 uses Marley as the integration fixture and `docs/brand-folder-spec.md` as the structural anchor. The spec doc may be stale too. Action: add Layer 4 prerequisite to verify brand-folder-spec.md reflects post-revamp slice list, OR drop "compare to prior" framing.

## Proposed action

Either:
1. Add a Layer 4 prerequisite step: verify `docs/brand-folder-spec.md` reflects the post-revamp slice list before using it as the structural anchor; OR
2. Drop the "compare to prior" framing for Layer 4 and use a freshly-generated reference fixture instead.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
