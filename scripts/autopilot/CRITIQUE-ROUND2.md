# Critique Round 2 (Non-Interactive)

You are running in non-interactive (`claude -p`) mode. Round 2 is scoped to changes only — it is NOT a full re-review. Your job is to verify that the Round 1 corrections didn't introduce new architectural problems or factual errors.

## Step 1: Read context

1. Read the critique panel prompt templates at the path in Parameters (`Critique panel prompts:`).
2. Read the plan at the path in Parameters (`Plan file:`).
3. Read the Round 1 critic reports at `/tmp/plan-critique-{feature-slug}/round-1/` to identify what changed.

## Step 2: Summarize Round 1 changes

Based on the Round 1 reports and the current plan, prepare a brief summary of what changed since Round 1 — which sections were edited and why. This becomes `{summary-of-changes}` passed to both Round 2 critics.

## Step 3: Run Round 2 critique panel

Create directory: `/tmp/plan-critique-{feature-slug}/round-2/`

**MANDATORY: Launch BOTH critics in a single assistant message** — two Task tool calls in the same turn.

- **Critic 1 — The Architect (Round 2):** Use the "Round 2: Architect prompt" section from the critique panel prompts file. Substitute `{plan-file-path}`, `{report-path}` = `/tmp/plan-critique-{feature-slug}/round-2/the-architect-report.md`, and `{summary-of-changes}`. Use `subagent_type=general-purpose`, `model=haiku`.

- **Critic 2 — The Verifier (Round 2):** Use the "Round 2: Verifier prompt" section. Substitute `{plan-file-path}`, `{report-path}` = `/tmp/plan-critique-{feature-slug}/round-2/the-verifier-report.md`, and `{summary-of-changes}`. Use `subagent_type=general-purpose`, `model=haiku`.

## Step 4: Aggregate

After both critics return, dispatch a single aggregation agent via Task tool (`subagent_type=general-purpose`, `model=haiku`) using the **"Round 2: Aggregation prompt"** from the critique panel prompts file. Substitute `{plan-file-path}` and `{feature}` = `{feature-slug}`.

## Step 5: Apply corrections

If Round 2 found any HIGH or MEDIUM issues, apply corrections to the plan file and commit:

```bash
git -C {project-directory} add docs/plans/<plan-filename>
git -C {project-directory} commit -m "docs: apply Round 2 critique corrections to <plan-filename>"
```

If no HIGH or MEDIUM issues, skip the commit.

## Step 6: Write the Round 2 flag file

Write the following YAML to the path specified in Parameters (`Round 2 flag file:`):

```yaml
design-doc: {design-doc-path}
plan-path: {plan-file-path}
timestamp: <current YYYY-MM-DD HH:MM:SS>
```

Use the Write tool. **This file must be written before you exit.**

## Parameters

Read from the lines appended below this prompt:
- **Critique panel prompts:** absolute path to critique-panel-prompts.md
- **Plan file:** absolute path to the plan document
- **Design document:** path to the design doc (written to flag file for resume detection)
- **Project directory:** project root (for git commit command)
- **Feature slug:** short identifier for temp directory naming
- **Round 1 flag file:** path to read (confirms round-2-needed and provides context)
- **Round 2 flag file:** absolute path to write when complete

## Rules

- Run to completion without pausing for user input
- Focus ONLY on changed sections — do NOT re-run the full checklist
- Both critics MUST be dispatched in the same assistant message
- Do NOT aggregate inline — always use a sub-agent
- Write the flag file before exiting
