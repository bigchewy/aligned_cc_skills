# Scaffold Directory Structures

Directory trees created by the kickstart skill's Phase 3, split by project type. Referenced by `skills/kickstart/SKILL.md` Phase 3.

## Contents

- Base Structure (ALL types)
- Software Additional Structure (software type only)

## Base Structure (ALL types)

```
project/
├── .claude/
│   └── settings.json          # Enable aligned plugin
├── .gitignore                 # .claude personal overrides (settings.local.json, CLAUDE.local.md)
├── CLAUDE.md
└── docs/
    └── lessons-learned/
```

## Software Additional Structure (software type only)

```
├── docs/
│   ├── design/
│   │   └── design-principles.md        # Placeholder with instructions
│   ├── architecture.md                 # Empty Mermaid template with section stubs
│   ├── plans/
│   │   └── completed/
│   ├── kanban/
│   │   ├── todo/
│   │   ├── in-progress/
│   │   ├── done/
│   │   ├── did_not_complete/
│   │   └── .counter
│   ├── mockups/
│   └── lessons-learned/
│       └── completed/
├── e2e/
│   ├── scenarios/
│   ├── fixtures/
│   │   └── profiles/
│   ├── eval-config.ts                  # Starter eval configuration (TS-based projects)
│   ├── eval-runner.ts                  # Starter eval runner (TS-based projects)
│   └── .gitignore                      # eval-log.jsonl, .eval-audit-last-run
├── scripts/
├── eslint-rules/
└── .gitignore                          # Append eval patterns to the base .gitignore
```

> **Note:** YAML-based eval projects (like this plugin) use `eval-surface.yaml` + `trigger-map.yaml` instead of the `.ts` files. The TS scaffold is for general-purpose projects with TypeScript eval runners.

**Business, Personal, General** get no additional folders beyond the base. Structure is flat — the user creates project-level folders at root as needed.
