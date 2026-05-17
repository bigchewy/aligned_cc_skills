# KB-088: `synthesize.md` deletion creates a stale-reference window in anti-examples

- **Type:** design defect (build ordering)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M2)
- **Critic:** Architect
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`

## Finding (verbatim from critique)

> **M2. `synthesize.md` deletion creates a stale-reference window** `[Architect]`
> Build order step 8 (prompt.md changes) precedes step 10 (anti-examples rewrites). Between them, anti-examples.md still references behavior the orchestrator no longer has. Note: OQ-2 can be resolved now — `use-framework/SKILL.md` reads only prompt.md / examples.md / anti-examples.md (verified by Architect). Action: resolve OQ-2 in design; re-order steps 8/10 so anti-examples updates ship with prompt.md.

## Proposed action

Re-order the build steps in the design so anti-examples.md updates ship in the same step (or atomic commit) as the prompt.md changes that remove `synthesize.md` references. No intermediate window where anti-examples.md describes orchestrator behavior that no longer exists.

OQ-2 resolution (use-framework reads only prompt/examples/anti-examples — deletion is safe) is being applied in the design directly (M12 from this critique round), so it is not filed as a separate Kanban entry.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
