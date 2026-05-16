# KB-084: Brand-folder framework examples use four different fictional companies

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e, branch `feature/ai-native-brand-folder`)
- **Location:** `frameworks/brand-voice/examples.md`, `frameworks/buyer-persona/examples.md`, `frameworks/messaging-distillation/examples.md`, `frameworks/proof-points-audit/examples.md`, `frameworks/competitive-battle-card/examples.md`, `frameworks/reverse-engineered-brand/examples.md`
- **Observed:** Six examples files use four distinct fictional companies. Three of them are nearly identical field-service companies — "Fieldwise" (brand-voice), "Fieldpath" (competitive-battle-card), "Fieldline" (reverse-engineered-brand) — same vertical (HVAC/plumbing/electrical), same buyer profile. The other three use unrelated healthcare orgs ("CareSync" for messaging-distillation, "Carepath" for proof-points-audit, a payer-side CMO for buyer-persona). A reader cross-referencing examples cannot tell whether the near-identical field-service names are intentional or an editing artifact.
- **Expected:** Pick one fictional company per major vertical (e.g., one field-service example used across all six framework examples; one healthcare example as the secondary). Document the chosen running examples in a `frameworks/_shared/running-examples.md` index.
- **Why out of scope:** Discovered during finishing-a-development-branch — not part of the original plan and not blocking merge.
- **Severity:** LOW
- **Created:** 2026-05-16
