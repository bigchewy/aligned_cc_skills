# Write Implementation Plan (Non-Interactive)

You are running in non-interactive (`claude -p`) mode. Your job is to write an implementation plan by following the writing-plans skill instructions.

## Step 1: Read the skill file

Read the skill file at the path specified in the Parameters section below. Follow ALL instructions in it, with the overrides listed in Step 2.

Also read the critique checklist at the path specified below — do NOT use the Glob fallback described in the skill. The path is provided directly.

## Step 2: Non-interactive overrides

These override specific sections of the skill:

1. **Skip the "Execution Handoff" section entirely.** Do not present "Next Steps" or execution options.
2. **After committing the plan to main**, write exactly two lines to the file specified as `Plan path sentinel` in the Parameters: line 1 is the design document path (from Parameters), line 2 is the plan file's absolute path. No other content.
3. **Do not pause for user input.** Run to completion autonomously.
4. **For the Kanban entry format**, the path is specified in Parameters. Do not search for it.
5. **After committing the plan to main**, if the project has worktrees, merge main forward into any relevant worktree (as the skill instructs). The autopilot handles its own worktree creation separately.
6. **Skip the "Fact-Check + Critique Panel" section entirely.** The critique panel runs as separate autopilot phases (2b and 2c) after the plan is written and committed. Do not dispatch any Architect or Verifier sub-agents during plan writing.
7. **Do not create a "final verification" task.** A task whose entire purpose is running the full test suite, building the project, or linting the codebase is a category error — that is Phase 9's job (the verify phase that runs automatically after the ralph loop). Do not create tasks titled "Final full-suite verification", "End-to-end verification", "Full build check", or any equivalent. The last plan task must be an implementation task with a scoped test command, not a verification sweep. This is not optional.

Everything else in the skill applies as written: codebase exploration, plan structure, TDD task format, verification gate, decision log.

## Parameters

Read these from the lines appended below this prompt:
- **Skill file:** absolute path to writing-plans/SKILL.md
- **Checklist:** absolute path to plan-critique-checklist.md
- **Kanban format:** absolute path to _shared/kanban-entry-format.md
- **Design document:** the design doc or spec to plan from
- **Project directory:** the project root
- **Plan path sentinel:** file to write the plan's absolute path to after committing

## Rules

- Run to completion without pausing
- Write plans to the main worktree (as the skill specifies)
- Do NOT run the critique panel (it runs in separate autopilot phases 2b/2c)
- Write the plan path sentinel before exiting
