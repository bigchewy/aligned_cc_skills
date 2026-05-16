# KB-072: decisionLogWidget and openQuestionsWidget share identical scaffolding that could be parameterized

- **Type:** simplification
- **Discovered during:** brainstorm-interactive-widgets
- **Location:** `skills/brainstorming/references/widgets.html:128-285`
- **Observed:** Both IIFEs implement the same four-function skeleton (`rows`, `buildPrompt`, `updateRow`, `refresh`) with identical event-binding and dirty-tracking logic. The only differences are element IDs (`decision-log` vs `open-questions`), the set of state values (`approve`/`reject` vs `defer`/`include`/`reject`), and the prompt text. The shared structure is ~60 lines of scaffolding duplicated. Adding a third widget would copy the same scaffolding a third time.
- **Expected:** Parameterize a `createWidget({ tableId, states, buildPrompt })` factory function and have both widgets call it. Adding new widget types becomes a config-only change.
- **Why out of scope:** The refactor is non-trivial JS work and would touch the very file we just landed. Worth doing once a third widget is needed, not preemptively.
- **Severity:** MEDIUM
- **Created:** 2026-05-15
