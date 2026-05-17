# KB-092: Sanitization for paste-back textarea content is unspecified

- **Type:** design defect (security / under-specified)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M8)
- **Critic:** QA Engineer
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Mockup:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

## Finding (verbatim from critique)

> **M8. Sanitization for paste-back textarea content unspecified** `[QA Engineer]`
> HTML render path preserves `</` sanitization; paste-back render path is asserted but not specified. Malicious source quote with `</textarea><script>` would break the widget. Action: add one-line sanitization spec for paste-back content.

## Proposed action

Add an explicit one-line sanitization spec in the design for paste-back content rendered into the `<textarea>` widget: at minimum, escape `</` sequences (matching the existing HTML render-path discipline), and document this in the renderer section.

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
