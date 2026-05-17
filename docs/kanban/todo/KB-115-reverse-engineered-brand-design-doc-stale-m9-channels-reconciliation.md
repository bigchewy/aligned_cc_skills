# KB-115: reverse-engineered-brand design doc has stale M9 channels reconciliation note

- **Type:** bug
- **Discovered during:** writing-plans
- **Location:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md:215` and `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md:367`
- **Observed:** The design document's M9 reconciliation note claims "the locked mockup currently renders `<dt>Channels</dt>` rows on every comp-card; the mockup must be updated to remove those rows in a subsequent iteration." Grep against the actual mockup (`docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`) shows zero `<dt>Channels</dt>` rows on competitor cards. The only `Channels` reference in the mockup is at line 947 in the Overview "Sections at a glance" GAP indicator, which is intentional.
- **Expected:** Update the M9 reconciliation note in the design doc (lines 215 + 367) to reflect that the mockup is already aligned with the dossier schema (no `channels` field). Either delete the M9 note entirely or rewrite it as "M9 — RESOLVED: the locked mockup was updated to remove `<dt>Channels</dt>` rows; no further reconciliation needed."
- **Why out of scope:** Surfaced during plan-write critique (Round 1 Verifier finding L6). The plan executes against the framework code; the design doc is upstream context that isn't on the plan's modify-list. Filing as a follow-up so the design doc gets corrected without blocking the implementation.
- **Severity:** LOW
- **Created:** 2026-05-17
