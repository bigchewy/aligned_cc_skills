# Critique Round 1 (Non-Interactive)

You are running in non-interactive (`claude -p`) mode. Your job is to run the Round 1 critique panel on the implementation plan, apply corrections, and record whether Round 2 is needed.

## Step 1: Read the critique materials

1. Read the checklist at the path specified in Parameters (`Checklist:`).
2. Read the plan at the path specified in Parameters (`Plan file:`).
3. Read the critique panel prompt templates at the path specified in Parameters (`Critique panel prompts:`).

## Step 2: Run Round 1 critique panel

Create a temporary directory: `/tmp/plan-critique-{feature-slug}/round-1/`

**MANDATORY: Launch BOTH critics in a single assistant message** — two Task tool calls in the same turn. Sequential dispatch doubles wall-clock time and is a skill violation.

- **Critic 1 — The Architect:** Use the "Round 1: Architect prompt" section from the critique panel prompts file. Substitute `{plan-file-path}` with the value from `Plan file:`, `{checklist-path}` with the value from `Checklist:`, and `{report-path}` with `/tmp/plan-critique-{feature-slug}/round-1/the-architect-report.md`. Use `subagent_type=general-purpose`, `model=sonnet`.

- **Critic 2 — The Verifier:** Use the "Round 1: Verifier prompt" section from the critique panel prompts file. Substitute same `{plan-file-path}` and `{checklist-path}`; `{report-path}` = `/tmp/plan-critique-{feature-slug}/round-1/the-verifier-report.md`. Use `subagent_type=general-purpose`, `model=sonnet`.

## Step 3: Aggregate

After both critics return, dispatch a single aggregation agent via Task tool (`subagent_type=general-purpose`, `model=sonnet`) using the "Round 1: Aggregation prompt" from the critique panel prompts file. Substitute `{plan-file-path}` and `{feature}` = `{feature-slug}`.

## Step 4: Assess severity

After aggregation, determine: did Round 1 find any HIGH or MEDIUM severity issues? Record this as `round-2-needed: true` if yes, `round-2-needed: false` if only LOW or no findings.

## Step 5: Apply corrections

Apply all corrections from Round 1 findings to the plan file:
- Fix every INCORRECT fact-check claim.
- Fix every HIGH severity finding.
- Fix every MEDIUM severity finding.
- LOW severity findings are informational — apply judgment, not required.

After editing the plan file, commit to the main worktree:

```bash
git -C {project-directory} add docs/plans/<plan-filename>
git -C {project-directory} commit -m "docs: apply Round 1 critique corrections to <plan-filename>"
```

If there are no corrections to apply (all findings are LOW or informational), skip the commit.

## Step 6: Write the flag file

Write the following YAML to the path specified in Parameters (`Round 1 flag file:`):

```yaml
design-doc: {design-doc-path}
plan-path: {plan-file-path}
timestamp: <current YYYY-MM-DD HH:MM:SS>
round-2-needed: true
```

Replace `round-2-needed: true` with `round-2-needed: false` if no HIGH or MEDIUM issues were found.

Use the Write tool to create this file. **This file must be written before you exit — it is how the shell phase verifies completion.**

## Parameters

Read from the lines appended below this prompt:
- **Checklist:** absolute path to plan-critique-checklist.md
- **Critique panel prompts:** absolute path to critique-panel-prompts.md
- **Plan file:** absolute path to the plan document
- **Design document:** path to the design doc (written to flag file for resume detection)
- **Project directory:** project root (for git commit command)
- **Feature slug:** short identifier used for `/tmp/plan-critique-{feature-slug}/` directory naming
- **Round 1 flag file:** absolute path to write the result flag

## Rules

- Run to completion without pausing for user input
- Both critics MUST be dispatched in the same assistant message (one turn, two Task calls)
- Do NOT aggregate inline — always use a sub-agent for aggregation
- After applying corrections, commit the plan file to main
- Write the flag file before exiting
