# KB-107: `recent_positioning_shift` dossier field is noise-prone

- **Type:** design defect (low-signal optional field)
- **Severity:** LOW
- **Source:** Round 1 critique of reverse-engineered-brand revamp (L5)
- **Critic:** April Dunford
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`

## Finding (verbatim from critique)

> **L5. `recent_positioning_shift` dossier field is noise-prone** `[April Dunford]`
> Optional field that produces low-signal observations. Action: drop from v1 schema (keep `pricing_signal`).

## Proposed action

Drop `recent_positioning_shift` from the v1 dossier schema. Keep `pricing_signal` (which is higher-signal and more actionable). Can be reintroduced in a later schema rev if a concrete consumer for it emerges.

## Created

2026-05-16
