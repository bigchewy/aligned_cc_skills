---
name: persona-panel
description: "Tests content against simulated buyer/user personas, producing an aggregation report and appending results to a longitudinal scorecard. Use when testing copy with personas, running the persona panel, or comparing how buyers would react to content variants."
---

# Persona Panel

**Announce:** "I'm using the persona-panel skill to test this content against buyer personas."

## Constants

- `CALIBRATION_WINDOW` = 5 — minimum scorecard rows per persona before running calibration checks
- `MAX_CONCURRENT_AGENTS` = 10 — cap on parallel persona sub-agents

## Stage 1: Discovery

Search for persona files in the current repo working directory. Glob both `docs/personas/` and `brand/personas/`, collecting results from whichever locations exist. Track the **persona root** (e.g., `docs/personas` or `brand/personas`) for each set of results — downstream steps (scorecard writes, calibration) use this root rather than a hardcoded path.

**If no personas found in either location:** Present the opt-out prompt:

> "No persona files found. I can create them now through a short Q&A, or you can add them manually using the template at `{base-directory}/references/persona-template.md`."

If the user chooses manual creation, stop. Otherwise, read `{base-directory}/modes/persona-creation-flow.md` and follow its process. If the mode file cannot be Read, STOP and tell the user the plugin installation may be incomplete. After the creation flow completes (user has been prompted for content), re-glob both `docs/personas/` and `brand/personas/` and continue from the group selection logic below (multiple groups → ask, one group → proceed).

**If personas found in both locations:** Treat each location's subdirectories as separate groups. Present all groups with their location prefix for clarity (e.g., "`brand/personas/` (3 personas)", "`docs/personas/buyers/` (2 personas)").

**If multiple subdirectories (groups) exist across either or both locations:** Ask the user which group to run. Example: "Found persona groups: `brand/personas/` (3 files), `docs/personas/enterprise/` (2 files). Which group should I run?"

**If one group (in either location):** Proceed automatically. Read all `.md` files in the group directory (excluding `scorecard.md`).

**If no content in conversation context and multiple groups exist:** Ask for clarification on both group and content.

## Stage 2: Mode Detection

Determine single vs. comparative mode from conversation context:
- **Single mode:** One piece of content to evaluate (the default)
- **Comparative mode:** Multiple variants where the user wants a winner (e.g., "which of these is better", "compare A and B")

If ambiguous, ask: "I see content but I'm not sure if you want a single evaluation or a comparison of variants. Which mode?"

## Stage 3: Content Extraction

Extract content from conversation context:
- Pasted text in the conversation
- A referenced file path (read it)
- Recent discussion context

**For comparative mode:** Label variants (A, B, C...) and confirm with the user before dispatching: "I'll compare these variants: [list]. Correct?"

## Stage 4: Sub-Agent Dispatch

### Session setup

1. **Derive session slug:** Infer `<topic>` from the content — use the first heading, source filename, or conversation topic. Only ask the user if inference completely fails.
2. **Create session directory:** `docs/interviews/YYYY-MM-DD-<topic>/` — use the Write tool to create a placeholder file if the directory doesn't exist.
3. **Read the prompt template:** Read `{base-directory}/references/persona-prompt.md` in full (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load).

### Dispatch

For each persona file in the selected group (up to MAX_CONCURRENT_AGENTS):

1. Read the persona file
2. Fill the prompt template placeholders:
   - `{PERSONA_CONTENT}` → full persona file content, verbatim
   - `{CONTENT}` → the content under test (for comparative mode, include all labeled variants)
   - `{MODE}` → `single` or `comparative`
   - `{SESSION_DIR}` → absolute path to session directory
   - `{PERSONA_SLUG}` → persona filename without `.md` extension
3. Dispatch via Agent tool: `subagent_type=general-purpose`, `model=sonnet`

**Launch ALL persona agents in parallel** — a single message with multiple Agent tool calls.

**If group has more than MAX_CONCURRENT_AGENTS personas:** Warn the user: "Group has {N} personas, capping at 10. Running first 10 alphabetically." Dispatch first 10 only.

### Error handling

If some sub-agents fail, proceed with available results. Track which personas completed and which failed (with error reason). A partial panel with 3/5 personas is more useful than no panel. Pass the list of missing personas to the aggregation stage.

## Stage 5: Aggregation

After all persona sub-agents complete (or fail):

1. **Read the aggregation template:** Read `{base-directory}/references/aggregation-prompt.md` in full (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load).
2. **Dispatch aggregation agent** via Agent tool: `subagent_type=general-purpose`, `model=sonnet`
   - Fill template with session directory path, list of available persona slugs, list of missing persona slugs, and mode
   - The agent reads all persona reports from the session directory
   - The agent writes `aggregation.md` to the session directory
   - The agent returns scorecard data lines in its response

3. **Parse scorecard data** from the aggregation agent's response. Expected format:
   ```
   SCORECARD:
   persona-slug|verdict|key-quote|actionable
   ```
   **If the SCORECARD block is missing or malformed** (no SCORECARD: header, invalid verdict values, wrong number of pipe-delimited fields), warn the user: "Could not parse scorecard data from aggregation. Skipping scorecard write. Check aggregation.md for raw results." Do not write partial or corrupted rows — the scorecard is longitudinal data and silent corruption is harmful.

4. **Write scorecard rows** (orchestrator responsibility — NOT the aggregation agent):
   - File: `<persona-root>/<group>/scorecard.md` (where `<persona-root>` is the location established in Stage 1, e.g., `brand/personas` or `docs/personas`)
   - If personas live at the root of the persona directory (no group subdirectory), use `<persona-root>/scorecard.md`
   - If file doesn't exist, create it with the header:
     ```markdown
     # Scorecard: <group>

     | Date | Content | Persona | Verdict | Key Quote | Actionable |
     |------|---------|---------|---------|-----------|------------|
     ```
   - Append one row per persona using the parsed scorecard data
   - Verdict must be one of: `engage`, `skeptical`, `bounce`

5. **Check calibration drift** (orchestrator responsibility):
   - Read the scorecard file
   - For each persona, count their total rows. If any persona has fewer than CALIBRATION_WINDOW (5) rows, skip calibration entirely for that persona.
   - For personas with 5+ rows, check the **last 5 entries** for:
     - **Monotone positive:** 5 consecutive `engage` → "Persona may be too agreeable. Sharpen `Gets skeptical when` and `Would click away if` in persona definition."
     - **Monotone negative:** 5 consecutive `bounce` → "Persona too hostile or wrong domain. Broaden `Keeps reading when` or check domain match."
     - **Never actionable:** 5 consecutive `no` in Actionable column → "Reactions aren't producing usable feedback. Review persona's `Communication Style`."
     - **Clone drift:** If 2 personas have identical verdict AND similar key quotes across 3+ consecutive runs → "Not differentiated enough. Differentiate their `Situation` and `Psychology` sections."
   - If any flags trigger, read `docs/interviews/YYYY-MM-DD-<topic>/aggregation.md` and append a `## Calibration Notes` section with the warnings. Do NOT modify scorecard.md — it stays as clean data.

6. **Present results** inline to the user: display the aggregation summary from aggregation.md.

## Boundaries

The skill does NOT:
- Write or edit content — it only evaluates
- Suggest improvements — personas are buyers, not consultants
- Persist across sessions — each invocation is independent (scorecard is the only longitudinal state)
- Run more than MAX_CONCURRENT_AGENTS persona sub-agents
