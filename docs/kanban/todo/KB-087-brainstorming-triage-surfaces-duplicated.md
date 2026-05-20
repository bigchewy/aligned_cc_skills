# KB-087: Brainstorming skill ships three triage surfaces with the same UX pattern

**Status:** todo
**Source:** Root-cause investigation during brainstorm `2026-05-17-reverse-engineered-brand-input-asks`
**Severity:** Medium

## What was observed

A user running the `brainstorming` skill in `authoring` mode ends up with three browser surfaces using the same triage UX pattern (toggle/select per row, "Copy follow-up prompt" textarea):

1. `live.html` Decision Log widget (decisions the author flagged)
2. `live.html` Open Questions widget (questions the author flagged)
3. `*-critique.html` (critique findings raised about the design)

The first two ship as injected widgets per `skills/brainstorming/references/visualization-protocol.md` Live phase step 6 and `references/widgets.html`. The third ships from `agents/critique-interactive-html-generator.md`, dispatched by `skills/_shared/critique-panel-orchestration.md` line 95.

## User complaint

"I'm confused as to why we have what seems like a new document that gets created that has questions, but we already have a questions tab. So this file has an open questions tab and this file also got opened up with different open questions. This seems like a bloated process."

The UX patterns are near-identical, the data sources are different, and nothing in the flow reconciles them.

## Root cause

The `live.html` widgets and the `*-critique.html` were added in separate evolutionary moments. Neither file references the other. Both ship from `docs/mockups/` with the same triage idiom. The skill flow opens both within minutes of each other at the end of an authoring session.

## Recommended fix (Simplification 1 from the root-cause sub-agent)

Merge critique findings as a fourth tab on the committed snapshot HTML at `docs/mockups/{session-name}.html`. Drop the standalone `*-critique.html`. The user opens one browser surface per session that grows through: design content, Decision Log triage, Open Questions triage, Critique findings triage. One copy-prompt-back pattern, one URL.

Trade-off: the critique-interactive-html-generator becomes more complex (must inject into existing HTML rather than write standalone). Live-refresh script timing needs care. The payoff is the user mental model: "your session lives at this URL."

## Alternative fixes (less recommended)

- Drop the in-doc widgets (Decision Log, Open Questions) from `live.html` entirely; let the critique panel be the sole interactive surface. Loses pre-critique triage. Smallest change.
- Inverse: drop the critique HTML; append critique findings to `live.html` via widgets. Couples the critique panel to the visualization protocol; harder for non-brainstorming critique flows to reuse.

## Files to change (for Simplification 1)

- `agents/critique-interactive-html-generator.md` — restructure to inject into existing HTML
- `skills/brainstorming/references/visualization-protocol.md` § "Post-critique regeneration" — orchestrate the merge
- `skills/_shared/critique-panel-orchestration.md` lines 93-108 — update the "tell the user" message to point at the single merged surface

## Why this is filed separately

The originating brainstorm produced its own design doc (`docs/plans/2026-05-17-reverse-engineered-brand-input-asks-design.md`) on a different topic (the `reverse-engineered-brand` framework's per-tab input asks). The brainstorming skill simplification is a separate concern that surfaced during that session and belongs as its own work item, not as scope creep into the original design.
