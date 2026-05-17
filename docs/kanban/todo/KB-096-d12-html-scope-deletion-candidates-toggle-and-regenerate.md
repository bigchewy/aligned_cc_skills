# KB-096: D12 HTML scope has small deletion candidates — custom toggle and Regenerate button

- **Type:** design defect (necessity test / YAGNI)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M14)
- **Critic:** Architect
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Mockup:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

## Finding (verbatim from critique)

> **M14. D12 HTML scope has small deletion candidates** `[Architect]`
> Custom `oq-context-toggle` duplicates native `<details>` (already in original render-review-html.md). Regenerate button reproduces what auto-rebuild does. Action: replace custom toggle with `<details>`; demote/remove Regenerate (or relabel as "discard manual edits").

## Proposed action

1. Replace custom `oq-context-toggle` with the native `<details>`/`<summary>` element already used by `render-review-html.md`. Drop custom JS.
2. Demote or remove the Regenerate button. If kept, relabel as "Discard manual edits" so its actual behavior is named accurately (auto-rebuild handles refresh).

## Notes

This is one of the deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
