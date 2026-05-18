# KB-141: "No asks" success-state copy ships partial version of deferred decision and uses banned em-dash

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (mockup fidelity check, reverse-engineered-brand-input-asks)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:2126`
- **Observed:** The per-tab callout renderer hardcodes "This area has no outstanding asks — coverage is sufficient." when a single-instance folder has `provided_summary` but no asks. Two issues: (1) The design doc Open Question 5 explicitly defers the "no inputs needed" success state, so shipping any version here pre-empts that decision (the Overview sub-tab correctly renders empty tier containers when there are no asks, which IS the deferred behavior — the inconsistency is only on per-tab callouts). (2) The em-dash in this string conflicts with the verification gate's ban on em-dashes in client-facing input-ask copy. The gate scopes the rule to generated `ask`/`provided_summary` strings, so this hardcoded template string sneaks past it, but the spirit of the rule applies.
- **Expected:** Either (a) remove the conditional success copy entirely (matches deferred Open Question 5 and the Overview sub-tab's empty-state behavior), or (b) revisit the deferred decision and ship a consistent success state on both surfaces with em-dash replaced by hyphen, comma, or period.
- **Why out of scope:** Resolving this requires settling the deferred design decision; that is a design call, not a bug fix.
- **Severity:** LOW
- **Created:** 2026-05-18
