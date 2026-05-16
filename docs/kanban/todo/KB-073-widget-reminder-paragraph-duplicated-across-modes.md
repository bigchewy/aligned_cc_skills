# KB-073: Interactive-widgets reminder paragraph copied verbatim into all four mode files instead of living in shared visualization protocol

- **Type:** simplification
- **Discovered during:** brainstorm-interactive-widgets
- **Location:** `skills/brainstorming/modes/{software,business,authoring,planning}.md` (the 3-4 line "Interactive widgets (conditional, mandatory when triggered)" block added in commit 2a32db3)
- **Observed:** The same reminder block was added identically to four mode files. Canonical content already exists in `skills/brainstorming/references/visualization-protocol.md` (step 6). The four-mode duplication creates four places to update when widget injection rules change.
- **Expected:** Either (a) remove the reminder from mode files and link to visualization-protocol.md from a single sentence in each mode, or (b) consolidate to a shared mode header included by reference. The current duplication was chosen for prominence (the rule must fire reliably), so option (a) needs careful copy-test to ensure injection still triggers reliably.
- **Why out of scope:** Same as KB-072 — refactor target for a future cleanup branch, not a fix that should hold up the feature merge.
- **Severity:** MEDIUM
- **Created:** 2026-05-15
