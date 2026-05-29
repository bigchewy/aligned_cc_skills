# Usage Analysis

Token/cost analysis of your Claude Code transcripts: how much your usage
*would have cost on the API*, broken down by repo, by skill, and by how each
session was launched (interactive vs. headless `claude -p`).

This is for the Claude Max plan case — none of these dollar figures were
actually billed. They're the API-equivalent cost, useful for understanding
where tokens go and whether Max is paying off.

## How it works

Pricing is hard to get right (cache-read, 5m vs 1h cache-write tiers, per-model
rates). Rather than re-derive it, this tool **delegates pricing to
[`ccusage`](https://github.com/ryoppippi/ccusage)** — a well-maintained tool
that prices each session from published per-model API rates — and then *joins*
ccusage's per-session cost to metadata it reads out of the raw transcript files:

- **repo** — from the `cwd` field (git worktrees collapsed into their parent repo)
- **launch type** — from the `entrypoint` field: `cli` = interactive, `sdk-*` = headless `claude -p`
- **skill** — from `Skill` tool-use invocations in the transcript

The script prints a validation line: "Mapped to a Claude transcript" should
roughly equal ccusage's Claude-only total. If they diverge, the join broke.

## Usage

```bash
# Simplest — runs ccusage for you (slow; downloads via npx, re-reads all logs):
node scripts/usage-analysis/usage-report.mjs

# Faster — reuse a saved ccusage dump:
npx -y ccusage@latest session --json > /tmp/ccusage.json
node scripts/usage-analysis/usage-report.mjs --ccusage-json /tmp/ccusage.json

# More rows per table:
node scripts/usage-analysis/usage-report.mjs --top 25
```

Other handy ccusage commands (it reads the same local logs):

```bash
npx -y ccusage@latest monthly            # calendar-month totals
npx -y ccusage@latest monthly --breakdown # split by model
npx -y ccusage@latest daily              # per-day
npx -y ccusage@latest blocks             # Claude's 5-hour billing windows
```

## The autopilot gotcha (why "executing-plans" looks tiny)

`scripts/autopilot` does **not** invoke the `writing-plans` or `executing-plans`
skills through the Skill tool. It feeds the skill's `SKILL.md` *as prompt text*
into a headless `claude -p` (see `WRITE-PLAN.md`), and its execution phase is the
**ralph loop** (`run-ralph.sh` + `EXECUTE-PLAN.md`), a bespoke single-task
executor that doesn't reference the `executing-plans` skill at all.

Consequence: autopilot spend is invisible to skill-based attribution. It shows
up under **Headless** in the launch-type section, which the report further tags
by autopilot prompt signature (`ralph-execute`, `plan`). If you want to know
"how much did autopilot cost," read the Headless line, not the skill table.
