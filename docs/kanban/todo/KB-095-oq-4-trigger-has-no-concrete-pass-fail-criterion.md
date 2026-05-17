# KB-095: OQ-4 trigger has no concrete pass/fail criterion

- **Type:** design defect (under-specified rollback gate)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M13)
- **Critics:** April Dunford, QA Engineer
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`

## Finding (verbatim from critique)

> **M13. OQ-4 trigger has no concrete pass/fail criterion** `[April Dunford, QA Engineer]`
> Re-evaluation points exist but no observable signal. Will get re-read three times and hand-waved closed. QA adds: rollback path (per-framework preambles, deferred by D11) is a 30-day path. Action: add concrete criterion — "5-components-positioning sub-agent emits OQs for all 5 phases without skipping or merging; otherwise escalate to per-framework AUTO_MODE."

## Proposed action

Add a concrete observable criterion to OQ-4 in the design, e.g.:

> OQ-4 is resolved PASS when `5-components-positioning` running in AUTO_MODE emits open questions for all 5 phases without skipping or merging phases. If any phase is skipped or merged, escalate to per-framework AUTO_MODE preambles.

Also document the rollback path's calendar cost (per-framework preambles is a 30-day path) so the trigger isn't hand-waved closed.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
