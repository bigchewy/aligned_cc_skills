---
name: use-framework
description: "Runs a user through a named decision framework interactively. Use with a framework name for fuzzy match, or alone to list available frameworks."
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

## Step 4: Run the Framework

After matching, hand off to the shared runner.

**Resolving the absolute framework path.** The runner requires an absolute directory path and fails closed otherwise. Construct it from the matched framework's registry `id`:

`<plugin-root>/frameworks/<id>/`

Where `<plugin-root>` is the parent of the matched `.claude-plugin/` directory. Resolve it via the procedure in `skills/_shared/resolve-skill-path.md` (Plugin root section). If Step 3 fell back to the project-local glob and produced a full path directly, use that path as-is.

Read `skills/_shared/framework-runner.md` and invoke it with:
- **Matched framework path:** the absolute path constructed above
- **`intake_gate_mode`:** `advisory` (preserves existing top-level invocation behavior — `required_documents` are noted to the user but execution proceeds)

The runner handles loading content, applying the intake gate, running phases with WAIT discipline, voice rules, and composability with `/aligned:use-advisor`.

## Avoid These Mistakes

- **Skipping phases** — Complete every phase in order. Do not jump ahead even if the user's situation seems to warrant it.
- **Rushing past pause points** — When the framework says to wait for a response, stop. Do not continue with the next question or phase in the same message.
- **Combining multiple frameworks** — Run one framework per session. If the user wants another framework, start a new invocation.
- **Improvising structure** — Follow the framework's phases exactly as written. Add warmth and personality, but do not invent new steps or skip existing ones.
- **Ignoring anti-examples** — If `anti-examples.md` was loaded, treat those patterns as hard constraints to avoid, not suggestions.
