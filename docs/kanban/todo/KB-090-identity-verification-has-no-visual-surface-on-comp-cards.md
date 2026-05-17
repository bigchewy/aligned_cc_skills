# KB-090: Identity-verification status has no visual surface on comp-cards

- **Type:** design defect (schema-vs-render gap + missing consumption policy)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M6)
- **Critics:** April Dunford, QA Engineer
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Mockup:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

## Finding (verbatim from critique)

> **M6. Identity-verification status has no visual surface** `[April Dunford, QA Engineer]`
> Schema has `identity_verification` field; mockup comp-cards show no chip/row for it. QA also notes downstream consumption policy for `mismatch_flagged` dossiers is unspecified. Action: render an `identity_verification` chip on every comp-card when not `matched`; add consumption-policy row to dossier schema ("treat as suggestive-only; emit P0 OQ if mismatch_flagged").

## Proposed action

1. **Mockup / renderer:** add an `identity_verification` chip to every comp-card. Hide it when status is `matched`; show prominently otherwise (`mismatch_flagged`, `unverified`, etc.).
2. **Schema doc:** add an explicit consumption-policy row to the dossier schema:
   > Downstream frameworks must treat `mismatch_flagged` dossiers as suggestive-only and emit a P0 open question to confirm identity before using competitor data.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
