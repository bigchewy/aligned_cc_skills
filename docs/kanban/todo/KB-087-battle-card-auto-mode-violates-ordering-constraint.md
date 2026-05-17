# KB-087: `competitive-battle-card` AUTO_MODE violates its own ordering constraint

- **Type:** design defect (framework / orchestration ordering)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M1)
- **Critic:** Architect
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Related artifacts:** `frameworks/competitive-battle-card/prompt.md` (line 20)

## Finding (verbatim from critique)

> **M1. `competitive-battle-card` AUTO_MODE violates its own ordering constraint** `[Architect]`
> Framework prompt line 20 says positioning is the canonical source of competitor names; AUTO_MODE dispatches all frameworks in parallel, so battle-card runs before positioning is finalized. Action: have the preamble flag this for verification-style frameworks, or escalate D11 (per Issue H4).

## Proposed action

Either:
1. Update the AUTO_MODE preamble to flag verification-style frameworks (battle-card, proof-points-audit) about cross-framework ordering — they must treat upstream slice outputs as unverified when running in parallel; OR
2. Escalate D11 from a single shared preamble to per-framework preambles that encode each framework's ordering / verification requirements.

This is tied to H4 (AUTO_MODE preamble enforcement) and may be resolved together.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
