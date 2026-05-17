# KB-097: Per-card action labels (Skip vs. Leave) and "what does Approve do?" disclosure

- **Type:** UX defect (per-card affordance language)
- **Severity:** MEDIUM
- **Source:** Round 1 critique of reverse-engineered-brand revamp (M16 + M19, combined)
- **Critic:** Steve Krug
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`
- **Mockup:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

## Combination note

M16 and M19 are both about clarifying — at the card / button level — what the user's actions actually do. Combined into one entry so a single pass through the card UI addresses both.

## Findings (verbatim from critique)

> **M16. "Skip" vs. "Leave for framework" labels read as synonyms** `[Steve Krug]`
> Two distinct actions, similar verbs. Action: rename to `Skip — not relevant` / `Defer — ask me later in Claude Code`.

> **M19. No "what does Approve do?" disclosure** `[Steve Krug]`
> Nothing on page tells the exec their toggles don't write to disk. Action: one-line reassurance above first card on each folder tab.

## Proposed action

1. **Rename action buttons** on every card:
   - `Skip` → `Skip — not relevant`
   - `Leave for framework` → `Defer — ask me later in Claude Code`
2. **Add a one-line reassurance** above the first card on each folder tab, e.g.:
   > Your toggles here don't write to disk. They only shape the paste-back prompt you'll hand to the framework in Claude Code.

Both are local edits to the review HTML template / mockup.

## Notes

These are deferred MEDIUM items (not in the M3/M5/M9/M12/M15 applied set).

## Created

2026-05-16
