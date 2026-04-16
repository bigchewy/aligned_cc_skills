# Software Project CLAUDE.md Template

Template for software projects (code, tests, builds). Referenced by `skills/kickstart/SKILL.md` Phase 4.

## Contents

- Section 1: Project Identity
- Section 2: Folder Map
- Section 3: Reading Priority
- Section 4: Communication Preferences
- Section 5: Guardrails
- Section 6: Workflows

## Section 1 — Project Identity

- Project name and one-sentence description (from Phase 2)
- Tech stack (from Phase 2)

## Section 2 — Folder Map

- Full directory structure: docs/ (architecture, design principles, kanban, plans, mockups, lessons-learned), e2e/, scripts/, eslint-rules/
- File locations: `docs/architecture.md`, `docs/design/design-principles.md`, `docs/kanban/`, `docs/plans/`, `docs/lessons-learned/`

## Section 3 — Reading Priority

```markdown
## Reading Priority

1. This file (CLAUDE.md)
2. `docs/architecture.md` — system structure
```

## Section 4 — Communication Preferences

- Commands section (test, build, lint, dev — based on detected/specified stack from Phase 2)

## Section 5 — Guardrails (Iron Rules)

- Tests first, always (TDD)
- Error path tests for every mock
- Verify before claiming done
- Root cause first, never symptom-fix

## Section 6 — Workflows

```markdown
## Workflows

- `/aligned:brainstorming` — before any creative work
- `/aligned:writing-plans` — before implementation
- `/aligned:executing-plans` — to implement a plan
- `/aligned:finishing-a-development-branch` — to complete work
- `/aligned:root-cause-analysis` — for root cause investigation
- `/aligned:create-design-principles` — to define design direction
- `/aligned:eval-audit` — to check eval coverage
```
