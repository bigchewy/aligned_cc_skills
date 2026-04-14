---
name: use-framework
description: "Guide the user through a framework's phases interactively. Use with a framework name for fuzzy match, or alone to list available frameworks. TRIGGER when a user mentions a framework by name in any request — including 'use the strategic narrative framework to build my homepage,' 'apply The Work to this situation,' 'run me through the 5-element narrative for my pitch.' When a user says 'use [framework] to build/write/create [thing],' the framework IS the process. Invoke this skill to run the framework interactively first. Build the artifact from the collaborative output afterward. Never read framework prompts as reference material — they are interactive conversation scripts with WAIT points."
---

# Use Framework

Guide the user through a framework's phases interactively.

## Invocation

- `/aligned:use-framework the work` — fuzzy match, start framework session
- `/aligned:use-framework` — list available frameworks

## Step 1: Discover Available Frameworks

Discover all frameworks from the plugin's flat directory.

**Step 1a: Discover frameworks from registry and filesystem**

**Primary source:** Read `frameworks/registry.yaml` (plugin-relative). Parse the `frameworks` list — each entry has `id`, `name`, `advisor`, `purpose`, `category`, `domains` (list), and `use_when`. Use this as the primary listing source.

**Fallback:** If `frameworks/registry.yaml` does not exist or fails to parse, glob `frameworks/*/prompt.md` from both plugin and project directories (deduplicate by slug, project-local wins). This also discovers project-local frameworks not in the plugin registry.

**Merge:** If both the registry and project-local glob return results, merge them. Registry entries are the canonical source for plugin frameworks. Project-local frameworks (found via glob but not in registry) are appended to the list.

**Context management:** When listing all frameworks, use registry metadata (name, advisor, purpose) directly. Do not read full `prompt.md` contents during discovery — full reads happen only after matching.

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
5. **No match → contextual recommendation:** The args didn't match any entry name, so treat them as task context. Read `skills/_shared/contextual-recommendation.md` (plugin-relative path) and follow its process. Pass entity type: `framework`, registry path: `frameworks/registry.yaml`, task context: the user's original args.

If no argument was provided, read `skills/_shared/contextual-recommendation.md` and follow its process. Pass entity type: `framework`, registry path: `frameworks/registry.yaml`, task context: empty (the shared file will check conversation context and decide whether to score or prompt — see its Path 3/4 boundary logic).

If `skills/_shared/contextual-recommendation.md` cannot be read, fall back to listing all available frameworks alphabetically.

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
