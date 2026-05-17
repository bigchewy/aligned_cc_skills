# KB-110: Toggle-off behavior on Approve/Reject buttons is invisible

- **Type:** UX defect (missing affordance for de-select)
- **Severity:** LOW
- **Source:** Round 1 critique of reverse-engineered-brand revamp (L8)
- **Critic:** Steve Krug
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Mockup:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

## Finding (verbatim from critique)

> **L8. Toggle-off behavior on Approve/Reject buttons is invisible** `[Steve Krug]`
> User clicking "Approve" again to deselect will think they broke something. Action: add visual hint ("Click again to clear") or remove toggle-off.

## Proposed action

Either:
1. Add a visual hint near the selected button ("Click again to clear"); OR
2. Remove the toggle-off behavior entirely and require an explicit Clear action.

Current state: clicking an active Approve button silently deselects — user has no signal that the click was intentional vs. broken.

## Created

2026-05-16
