# KB-069: Decision-log widget applies wrong row class on reject

- **Type:** bug
- **Discovered during:** brainstorm-interactive-widgets
- **Location:** `skills/brainstorming/references/widgets.html:164-174`
- **Observed:** The decision-log widget's `updateRow` function adds `row-active` to the `<tr>` when a decision is rejected (`select.value === 'reject'`). `row-active` maps to `background: var(--color-accent-subtle) !important` — a teal/accent highlight. The CSS for rejected rows is defined on `tr.row-rejected td` (red background + strikethrough). The open-questions widget correctly adds `row-rejected` for rejected entries (line ~258). No test exercises the row-class assignment directly; `test_widget_isolation_guards_present` only checks that the `getElementById` guard string is present.
- **Expected:** When `select.value === 'reject'`, the decision-log widget should add `row-rejected` to the row (and `reject` to the select), matching the CSS rules at lines 54-56. When the value reverts to `approve`, `row-rejected` should be removed. This makes the row visually red with strikethrough, consistent with the open-questions widget's rejected-row treatment.
- **Why out of scope:** The bug produces no test failure because `test_brainstorm_widgets.py` does not assert the row-class applied per dropdown value — it only checks the existence of guard strings and structural markers. A browser-level behavioral test would be needed to catch this.
- **Severity:** HIGH
- **Created:** 2026-05-15
