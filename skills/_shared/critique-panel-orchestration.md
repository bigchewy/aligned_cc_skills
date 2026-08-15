# Critique Panel Orchestration

Shared orchestration protocol for brainstorming critique panels. Read this file after setting configuration parameters in your SKILL.md.

> **Note:** `{base-directory}` in this file refers to the calling skill's base directory. The calling skill is responsible for resolving it per `skills/_shared/resolve-skill-path.md` before reading this file.

## Configuration Validation

Before proceeding, verify all required parameters are present in the SKILL.md context above:

- `skill-name` must be set (e.g., "brainstorming")
- `checklist-filename` must be set (e.g., "design-critique-checklist.md")
- `fact-check-mode` must be either "division-of-labor" or "all-critics"
- `fact-check-tools` must be a non-empty tool list
- `aggregation` must be either "sub-agent" or "inline"
- `criteria-assignment` must be "yes" (with mapping table provided) or "no"
- `visual-artifacts` must be a path or "none"
- `critique-temp-directory` must be set
- At least one critic prompt template must be provided

If any required parameter is missing, STOP and tell the user which parameter is missing from their SKILL.md configuration block.

## Mandatory Sub-Agent Rule

You MUST use the Task tool to launch fresh sub-agents for every critique round. NEVER run the critique in the main context window. The sub-agents provide independent evaluation — they haven't seen the brainstorming conversation, so they won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.

## Checklist Resolution

The checklist is at `{base-directory}/{checklist-filename}`. Verify the path exists with Read. **If the checklist cannot be found, STOP and tell the user — do not proceed with the critique panel without it.** Use the verified absolute path as `{checklist-path}` in the sub-agent prompts below.

## Competition Framing

When 2 or more critics are launched in parallel, append the block below to **each** critic's prompt (after its tooling paragraph, before its per-criteria instructions). With a single critic there is no competition — omit it entirely.

> **🍪 Competition — you are not the only reviewer.** Other critics are reviewing this same design in parallel right now. Two prizes are on the table:
> - **One cookie** for whoever surfaces the most genuinely serious, *valid* issues. Judged on real defects, not volume — inflated severity, padded counts, or findings that don't survive scrutiny disqualify you. A false positive costs you more than a missed nitpick. Be right, not loud.
> - **Two cookies** for whoever identifies the most justified *cuts* — extraneous scope, speculative abstractions, over-engineering, or anything that fails the test "what specifically breaks if this is removed?" In this solo-developer codebase with a fixed workflow, deleting unneeded work is worth more than adding caveats. The same severity discipline applies: a cut you can't justify with a concrete "this is never used / never reached" doesn't count.
>
> Play to win on both axes.

## Round 1

1. Read `skills/_shared/resolve-advisor-source.md` and follow its procedure. Take the `advisors`
   list (each entry carries `id`, `name`, `domains`, `evaluation_expertise`, `best_for`, `not_for`,
   `absolute_prompt_path`, `source`) **and** the `selection_guidelines` block from its return — the
   resolver returns `selection_guidelines` as a plugin-canonical sibling of `advisors`. Use
   `selection_guidelines` for count rules, hard-exclude logic, and diversity preferences. If the
   resolver cannot be read, fall back to globbing `advisors/prompts/*.md` and parsing first lines
   for name/domain extraction (selection guidelines then default to: 2-3 critics, hard-exclude on
   `not_for`, prefer lens diversity). **Behavior note: this fallback path is intentionally
   plugin-only — after migration it will not surface local advisors. It fires only when the
   resolver file itself is unreadable (a plugin installation failure), not for absent or malformed
   local registries (those are handled by the resolver's own error paths).**
2. Based on the design document's content, select 1-4 critics following the registry's selection guidelines. Hard-exclude any critic whose `not_for` matches the design's primary domain. Prefer diversity of lens — avoid selecting critics with overlapping domains. State which critics you selected and why (one sentence each).
3. Read each selected critic's full prompt file using that entry's `absolute_prompt_path` from the
   resolver (NOT the registry `prompt:` field, which is plugin-relative and mis-resolves local
   critics).

**If `fact-check-mode` is "division-of-labor":**

4. **Assign roles before launching agents:**

   **Fact-checker designation:** Exactly one critic owns Phase 1 (exhaustive fact-checking). Priority: The QA Engineer > The Architect > first selected critic. The fact-checker also gets domain critique work (Phase 2) — they do both jobs.

   **Criteria assignment (only if `criteria-assignment` is "yes"):** Assign each checklist criterion to the one critic whose domain best matches it, using the mapping table provided in the SKILL.md configuration. Criterion 9 (Decision quality) goes to all critics. Each other criterion goes to exactly one critic. If no selected critic's domain matches a criterion, assign it to the fact-checker as catch-all. **Exception:** YAGNI-shaped criteria (`design-critique-checklist.md` Crit 3 + 8) go to The Architect when selected, because The Architect's prompt carries explicit deletion authority and a Necessity Test. If The Architect is not selected, fall back to the fact-checker as today. Target 2-4 criteria per critic.

   State the full assignment table before launching agents.

5. Create temp directory: `{critique-temp-directory}/round-1/`. Launch all critics in parallel (single message, multiple Task tool calls, `subagent_type=general-purpose`, `model=opus`). Use the fact-checker prompt template for the designated fact-checker, regular critic prompt template for others. If 2+ critics are being launched, append the Competition Framing block to each critic's prompt. Each critic writes their report to `{critique-temp-directory}/round-1/{critic-slug}-report.md` and returns only a one-line confirmation.

**If `fact-check-mode` is "all-critics":**

4. Create temp directory: `{critique-temp-directory}/round-1/`. Launch all critics in parallel using the universal critic prompt template. If 2+ critics are being launched, append the Competition Framing block to each critic's prompt. Each critic writes their report to `{critique-temp-directory}/round-1/{critic-slug}-report.md` and returns only a one-line confirmation.

**Aggregation:**

**If `aggregation` is "sub-agent":**

After all critics finish, dispatch one aggregation agent via Task tool (`subagent_type=general-purpose`, `model=opus`):

"You are a critique aggregator. You have access to Glob, Read, and Write tools. Do not use Bash for searching. Read all report files in `{critique-temp-directory}/round-1/`. Also read the design document at `{design-file-path}` for context.

Produce a unified report:
- **Fact-checks:** The fact-check report (from the designated fact-checker if division-of-labor, or merged from all critics if all-critics) is the authoritative source. Summarize: total claims checked, accuracy percentage, list every INCORRECT claim with the correction. If another critic flagged a factual issue incidentally, include it.
- **Critique findings:** Merge all critic findings, preserving persona tags. De-duplicate — when two or more critics flag the same issue, keep the highest-severity version and note all sources. Group by severity (high → medium → low).
- **Action items:** List concrete changes needed, ordered by severity. For each, note which critic(s) raised it.

Be concise — the goal is to give the design author a clear, actionable summary without needing to read the raw reports. Keep the unified report under 1500 words.

Write TWO output files using the Write tool:
1. `{critique-temp-directory}/round-1/aggregated.md` — the prose unified report (the content described above).
2. `{critique-temp-directory}/round-1/aggregated.json` — a structured snapshot of the same data for the downstream interactive decision HTML. Schema:

    {
      \"fact_checks\": [
        {\"id\": \"fc-1\", \"claim\": \"<original>\", \"correction\": \"<corrected>\", \"critic\": \"<critic-name>\"}
      ],
      \"findings\": [
        {\"id\": \"h-1\", \"severity\": \"high\",   \"text\": \"<finding>\", \"action\": \"<suggested fix>\", \"critics\": [\"<name>\"]},
        {\"id\": \"m-1\", \"severity\": \"medium\", \"text\": \"<finding>\", \"action\": \"<suggested fix>\", \"critics\": [\"<name>\"]},
        {\"id\": \"l-1\", \"severity\": \"low\",    \"text\": \"<finding>\", \"action\": \"<suggested fix>\", \"critics\": [\"<name>\"]}
      ]
    }

IDs are stable kebab strings (h-1, h-2, m-1, fc-1, ...). Return only a one-line confirmation that both files were written."

Present the aggregation agent's unified report to the user.

**If `aggregation` is "inline":**

Merge all critic reports in the main thread. De-duplicate, preserve persona tags, group by severity (high → medium → low). Present the unified report to the user. Then write the same data to two files using the Write tool:
1. `{critique-temp-directory}/round-1/aggregated.md` — the prose unified report.
2. `{critique-temp-directory}/round-1/aggregated.json` — the structured snapshot using the schema documented in the sub-agent aggregator instruction above (`fact_checks` and `findings` arrays with stable kebab IDs).

## Interactive Decision HTML

After the aggregation step writes `aggregated.md` and `aggregated.json` (both paths produce the same files), dispatch the critique-interactive-html-generator agent via Task tool (`subagent_type=general-purpose`):

"Read `agents/critique-interactive-html-generator.md` for your full workflow. Generate an interactive critique decisions HTML.
- Aggregated JSON: `{critique-temp-directory}/round-1/aggregated.json`
- Design file: `{design-file-path}`
- Session name: `{session-name}`
- Mode: `{mode}` (one of: authoring | research | roadmap — supplied by the calling mode file context)
- Project root: `{project-root}`"

Then tell the user:

> "Critique findings are open in your browser at `docs/mockups/{session-name}-critique.html`. Toggle accept/reject on each finding, add modify notes per tab if needed, then click **Copy follow-up prompt** and paste it back here. Or approve findings in chat directly — both paths work."

The chat path remains the fallback: any user who skips the browser can approve findings inline and the Apply Fixes step proceeds normally.

## Apply Fixes

Apply corrections for any INCORRECT fact-check claims. Apply fixes for medium/high critique issues the user approves. If you need to review a specific critic's raw findings in detail, read the report file directly — do not ask the user to summarize it.

## Round 2 (conditional)

Only run if Round 1 found medium or high severity issues AND fixes were applied (at least one correction applied to the design document). Use the same critics and role assignments from Round 1 with fresh sub-agents (do NOT resume Round 1 agents). Keep the Competition Framing block on each prompt when 2+ critics are launched, same as Round 1. Write to `{critique-temp-directory}/round-2/`.

Prepare a brief summary of what changed since Round 1 and pass it to each agent. Scope to changes only:
- If division-of-labor: the fact-checker re-verifies only changed claims. Other critics re-evaluate only changed sections against their assigned criteria.
- If all-critics: all critics re-evaluate only changed sections.

Aggregate Round 2 the same way as Round 1 (sub-agent or inline, per configuration).

## Escalation

If Round 1 revealed concerns in a domain not covered by the selected critics, add one specialist critic for Round 2. State the escalation reason. Maximum one additional critic per round.

Apply any remaining fixes. Present final results to the user.

## Handoff

The critique panel is a sub-process, not the end of the workflow. After presenting final results:

1. **Re-read the invoking skill's mode file** — the file you were handed off from at `{base-directory}/modes/<mode-name>.md`. The original content has likely been compressed out of context by now. Use the Read tool to load it again.
2. **Find the "POST-CRITIQUE CHECKLIST" section** and execute every numbered step in order. Announce each step before executing it (e.g., "Executing Step 1 of 3 — Visualization refresh"). Do not stop after the commit — the checklist continues after it.

The checklist includes steps that feel "post-completion" (like presenting next-step options) but are mandatory parts of the brainstorming workflow. The session is not complete until the final step of the checklist has been presented to the user.
