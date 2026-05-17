# KB-089: Paste-back data flow only works with framework regular-mode resumption (which is out of scope)

- **Type:** design defect (scope / user expectation mismatch)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M4)
- **Critic:** QA Engineer
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Mockup:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

## Finding (verbatim from critique)

> **M4. Paste-back data flow only works with framework regular-mode resumption (which is out of scope)** `[QA Engineer]`
> Pasted prompt becomes a long preamble; regular-mode frameworks start at PHASE 1 every time and have no concept of pre-existing agenda. Out-of-scope list admits resumption logic doesn't exist. Action: either move resumption into scope, or lower expectations in the design ("framework will see your pre-review; may still ask questions you've already answered").

## Proposed action

One of:
1. **Promote resumption into scope.** Add framework regular-mode resumption (so a framework can ingest a pre-reviewed agenda and skip already-answered questions) as an explicit deliverable.
2. **Lower paste-back expectations.** Update the design — and the page's user-facing copy — to say plainly: "Pasting this back will give the framework your decisions as context, but it may still ask some questions you've already answered."

The second option is cheaper and preserves the current scope boundary; the first is the right end-state but a separate effort.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
