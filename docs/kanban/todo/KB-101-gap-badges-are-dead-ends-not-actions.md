# KB-101: GAP badges are dead-ends, not actions

- **Type:** UX defect (missing actionable affordance)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M21)
- **Critic:** Steve Krug
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Mockup:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

## Finding (verbatim from critique)

> **M21. GAP badges are dead-ends, not actions** `[Steve Krug]`
> `GAP — no owning framework` is information. Design intent (point to `/aligned:add-framework`) doesn't surface. Action: make the badge a clickable action that copies `/aligned:add-framework {slug}`.

## Proposed action

Make every `GAP — no owning framework` badge a clickable element that copies `/aligned:add-framework {slug}` to the clipboard, with a brief toast/confirmation on copy. The slug should be derived from the gap's folder context.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
