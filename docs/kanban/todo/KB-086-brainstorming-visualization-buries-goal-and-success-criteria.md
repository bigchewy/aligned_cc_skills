# KB-086: Brainstorming visualization HTML buries the design's goal and success criteria — opens straight into details

- **Type:** bug (recurring agent-behavior + protocol-clarity gap)
- **Discovered during:** software-mode brainstorm session for exercise-renderers Phase 2 (2026-05-16), surfaced by user with direct quote
- **Location:** `skills/brainstorming/references/visualization-protocol.md` and `skills/brainstorming/references/brainstorm-components.md`

## Observed

Today's session produced `docs/mockups/2026-05-16-exercise-renderers-phase-2.html`. Eric's feedback verbatim:

> "The HTML document is not giving me what I want. Specifically, the goal of the design doc is unclear. It goes straight into details without giving me any summary of what we're trying to accomplish, what success looks like, et cetera."

The opening sequence of the mockup is:
1. Title + date subtitle
2. A "Status" callout describing what got simplified (Whisper removed, nudges skipped, etc.)
3. A tab-bar with 5 tabs: Overview / Build phases / Decision Log / Fresh D29–D33 / Risks
4. The "Overview" tab opens straight into a "What ships in Phase 2" table — three renderer rows

The design document itself HAS a §2 "Goal" section (one paragraph) and a §3 "Success criteria" section (eight bullet points). Neither is surfaced in the mockup. A reader who opens the HTML cold cannot answer "what is this design trying to accomplish?" or "what does success look like?" without leaving the mockup and reading the .md file.

## Why it happened

Two contributing causes — both worth fixing independently:

1. **Agent shortcut:** the agent wrote a compact mockup rather than following the full template-copy-and-patch protocol. The `templates/software-template.html` supports a Success-criteria component (lines 437-465 define `.criteria-list` styling) and the `brainstorm-components.md` reference documents it. Skipping the template skipped the structural slot. Same agent-shortcut pattern as KB-085's "open in browser" miss.
2. **Protocol gap:** even if the agent had followed the template, `visualization-protocol.md` does NOT explicitly require that the **Goal** and **Success criteria** sections from the design document be rendered FIRST in the visualization. The protocol covers tab structure (nested sub-tabs rule, sections 91-97), brand tokens, and widget injection — but not "lead with intent." The implicit assumption is "use the components in `brainstorm-components.md` appropriately," which is too soft for a recurring miss.

## Expected

A reader opening the visualization HTML should within the first viewport understand:
- **What this design is trying to accomplish** (the Goal section from the design doc, rendered verbatim or as a 1-2 sentence summary)
- **What success looks like** (the Success criteria bullets, as a visible list — not hidden in a tab)

Then tabs / details can follow. The pattern in a written design doc (Goal → Success criteria → details) should be preserved in the visualization, not flattened.

## Suggested fixes

- **F1 (protocol):** Add a "Section ordering contract" subsection to `visualization-protocol.md` that says: the first viewport of the visualization MUST surface the design's Goal and Success criteria. Tabs (if used) start AFTER that section, not over it. Make this load-bearing language, not advisory.
- **F2 (template):** Update `templates/software-template.html` so the structural slot for Goal + Success criteria appears BEFORE the tab-bar — even when tabs are used. Currently the template's tab structure swallows everything; the agent has to know to put Goal+Success outside the tabs.
- **F3 (component reference):** Add a "Hero section pattern" component to `brainstorm-components.md` that bundles a Goal paragraph + Success criteria list as the canonical opening block of every software-mode visualization. Currently the components are individually documented but no opening pattern is named.
- **F4 (mode files):** Add a step in `modes/software.md` (and the other modes) that says: "Before generating any visualization HTML, verify the design document has explicit Goal and Success criteria sections. If absent, that's a design-completeness gap to fix BEFORE visualizing."

## Severity

MEDIUM. The information IS in the design doc, so the user can navigate to it — but the visualization's purpose is to make the design easier to grok at a glance, and right now it fails at that purpose at the first viewport. Eric had to call this out twice in one session (this critique + KB-085's "open the browser" miss) which suggests the visualization workflow is currently under-serving the brainstorm contract.

## Cross-references

- KB-085 — visualization protocol step 4 (open in browser) is reliably skipped. Both bugs are downstream of the same root cause: the visualization protocol's instructions are easy to skip when the agent takes a "compact direct-write" shortcut.

## Created

2026-05-16
