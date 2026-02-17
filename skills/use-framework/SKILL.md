---
name: use-framework
description: "Guide the user through a framework's phases interactively. Use with a framework name for fuzzy match, or alone to list available frameworks."
---

# Use Framework

Guide the user through a framework's phases interactively.

## Invocation

- `/aligned:use-framework the work` — fuzzy match, start framework session
- `/aligned:use-framework` — list available frameworks

## Step 1: Discover Available Frameworks

Discovery uses a two-stage process: plugin-shipped frameworks first, then user-added frameworks as a fallback.

**Step 1a: Read the plugin repo manifest**

Read the file `frameworks/.repos` (plugin-relative). Each line is a repo name (e.g., `va-web-app`). If the file doesn't exist or is empty, report: "No framework repos found in plugin. Check your plugin installation."

**Step 1b: Glob each repo (plugin frameworks)**

For each repo name from the manifest, glob:

```
frameworks/{repo-name}/**/prompt.md
```

Combine all results across repos. Each `prompt.md` represents one framework. The slug is the **parent directory** name of `prompt.md` (e.g., for `frameworks/va-web-app/clearing-model/prompt.md`, the slug is `clearing-model`).

If a repo from the manifest returns zero results, report: "No framework files found in `frameworks/{repo-name}/`. The directory may be empty."

**Step 1c: Discover user-added frameworks (fallback)**

Additionally, if `~/.claude/frameworks/prompts/.repos` exists, also discover frameworks from there:

For each repo name in that manifest, glob:

```
~/.claude/frameworks/prompts/{repo-name}/**/prompt.md
```

Merge these with plugin frameworks. If the same slug appears in both plugin and user locations, the plugin version takes precedence (skip the user-added duplicate).

This allows users to add their own frameworks beyond what the plugin ships. To add custom frameworks, create a directory in `~/.claude/frameworks/prompts/{repo-name}/{framework-name}/` containing `prompt.md` (required), `examples.md` (optional), and `anti-examples.md` (optional). Add the repo name to `~/.claude/frameworks/prompts/.repos`.

**Context management:** When listing all frameworks, glob first to get folder names, then read only the first line of each `prompt.md`. Do not read full file contents during discovery — full reads happen only after matching.

## Step 2: Extract Framework Names

Read the first line of each `prompt.md`, which follows the format:

```
You are {Advisor}, guiding someone through {Framework} - {purpose}.
```

Parse the framework name from between "guiding someone through" and the dash/period. Parse the advisor name from between "You are " and the comma. This gives the display name and associated advisor for matching and listing.

If a file doesn't match this format, skip it and continue. Do not fail the entire listing because one file is malformed.

## Step 3: Match User Input

If the user provided a framework name argument:

1. Match against both the folder slug (e.g., `the-work`) and the extracted display name (e.g., `The Work`)
2. Use case-insensitive substring matching
3. **Single match:** Use it
4. **Multiple matches:** Ask the user which one they meant
5. **No match:** List all available frameworks with their display names

If no argument was provided, list all available frameworks grouped by repo, then alphabetically within each group. Show each repo as a header (e.g., "**va-web-app**"), then list frameworks with display name, advisor, and purpose. If all frameworks come from a single repo, skip the repo header.

## Step 4: Load Framework Content

Read three files from the matched framework's directory (use the full path from the glob result):

1. `prompt.md` — the phase-by-phase guide (required)
2. `examples.md` — calibration examples per phase (read if exists, skip silently if missing)
3. `anti-examples.md` — failure modes to avoid (read if exists, skip silently if missing)

If `prompt.md` is missing or empty, report the error and stop. Do not attempt to run a framework without its prompt.

## Step 5: Run the Framework

1. Inject all loaded content as operating instructions
2. Begin Phase 1 immediately with the framework's scripted opening
3. Complete each phase fully before advancing to the next
4. **WAIT** for the user's response at each marked pause point — do not continue until they respond
5. Use examples from `examples.md` to calibrate responses
6. Actively avoid patterns described in `anti-examples.md`

A phase is complete when: (a) the scripted content for that phase has been delivered, (b) the user has responded to all prompts within the phase, and (c) any reflection or summary the phase calls for has been provided.

## Voice

- If an advisor persona is active (via `/aligned:use-advisor`): deliver the framework in that advisor's voice
- If no advisor is active: follow the framework prompt as-is — it already names an advisor in its opening line ("You are {Advisor}, guiding someone through..."), so adopt that advisor's voice as written in the prompt

## Composability with /aligned:use-advisor

When both `/aligned:use-advisor` and `/aligned:use-framework` appear in the same prompt (detectable because both skill instructions will be loaded into context simultaneously):

1. Load the advisor prompt (sets the voice)
2. Load the framework prompt + examples + anti-examples (sets the structure)
3. Begin Phase 1 immediately in the advisor's voice
4. No intermediate acknowledgment — straight into the framework

## Avoid These Mistakes

- **Skipping phases** — Complete every phase in order. Do not jump ahead even if the user's situation seems to warrant it.
- **Rushing past pause points** — When the framework says to wait for a response, stop. Do not continue with the next question or phase in the same message.
- **Combining multiple frameworks** — Run one framework per session. If the user wants another framework, start a new invocation.
- **Improvising structure** — Follow the framework's phases exactly as written. Add warmth and personality, but do not invent new steps or skip existing ones.
- **Ignoring anti-examples** — If `anti-examples.md` was loaded, treat those patterns as hard constraints to avoid, not suggestions.
