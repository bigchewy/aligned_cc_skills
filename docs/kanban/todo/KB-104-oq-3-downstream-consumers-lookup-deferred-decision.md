# KB-104: OQ-3 (downstream-consumers lookup location) is a deferred near-trivial decision

- **Type:** design defect (unresolved trivial open question)
- **Severity:** LOW
- **Source:** Round 1 critique of reverse-engineered-brand revamp (L2)
- **Critic:** Architect
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`

## Finding (verbatim from critique)

> **L2. OQ-3 (downstream-consumers lookup location) is a deferred near-trivial decision** `[Architect]`
> Embedding lookup data in a reference doc means parsing markdown for control flow. Action: resolve in design (recommend new `slice-dependencies.yaml`).

## Proposed action

Resolve OQ-3 in the design now. Recommended: create a new `slice-dependencies.yaml` for downstream-consumers lookup data, avoiding markdown parsing for control flow. Alternative: co-locate the data in the open-questions schema doc as structured YAML.

## Created

2026-05-16
