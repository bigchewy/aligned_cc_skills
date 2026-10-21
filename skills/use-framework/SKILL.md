---
name: use-framework
description: "Runs a user through a named decision framework interactively. Use with a framework name for fuzzy match, or alone to list available frameworks."
---

# Use Framework

Guide the user through a framework's phases interactively.

## Invocation

- `/aligned:use-framework the work` — fuzzy match, start framework session
- `/aligned:use-framework` — with a task in the conversation, recommend a framework; with no task in the conversation, list every framework

## Step 1: Discover Available Frameworks

**Step 1a: Resolve the merged framework set**

Read `skills/_shared/resolve-framework-source.md` (plugin-relative path) and follow its procedure to obtain the merged framework set (plugin global + project-local, deduped, local-wins). Use the returned `frameworks` list as the listing source. Each entry carries `id`, `name`, `advisor`, `purpose`, `category`, `domains`, `use_when`, `absolute_framework_dir`, `source`, and `registered`.

> The resolver's own error paths already handle degradation (absent local registry → plugin-only result; malformed local YAML → degrade and warn). No additional fallback is needed here — a resolver file that cannot be read indicates a plugin installation failure, which is a distinct failure mode and not something `use-framework` should silently paper over.

**Context management:** When listing all frameworks, use the resolver's metadata (name, advisor, purpose) directly. Do not read full `prompt.md` contents during discovery — full reads happen only after matching.

## Step 2: Extract Framework Names

Registered entries already carry `name` and `advisor`. Use them as-is.

For `registered: false` entries only (a project-local folder with no registry entry), the resolver parsed the first line of `prompt.md`, which follows the format:

```
You are {Advisor}, guiding someone through {Framework} - {purpose}.
```

If the resolver could not parse that line, the entry's `name` is the folder name and its `advisor` is empty. List it anyway. Do not fail the entire listing because one folder is malformed.

List frameworks alphabetically by display name. When the resolver returned entries with `source: "local"`, annotate each one with a trailing `(local)` marker so the user can tell project-specific frameworks from global ones.

**List all.** Do this for a bare call with no task in the conversation, and for a "list all" reply to any recommendation prompt. List every entry from Step 1a. Put the `source: "local"` entries first under their own heading, each name followed by `(local)`. Then list the plugin entries alphabetically. Never shorten or summarize the local group. Show the name and advisor on each line.

## Step 3: Match User Input

If the user provided a framework name argument:

1. Match against both the folder slug (the entry `id`, e.g., `the-work`) and the display `name` (e.g., `The Work`), over the merged list from Step 1a
2. Use case-insensitive substring matching
3. **Single match:** Use it
4. **Multiple matches:** Ask the user which one they meant
5. **No match → contextual recommendation:** The args didn't match any entry name, so treat them as task context. Read `skills/_shared/contextual-recommendation.md` (plugin-relative path) and follow its process. Pass entity type: `framework`, frameworks: the pre-merged list from Step 1a, task context: the user's original args.

If no argument was provided:

- **No task in the conversation** (the shared file's Path 4 condition): do not ask a question. List all frameworks as described in Step 2.
- **A task in the conversation** (Path 3): read `skills/_shared/contextual-recommendation.md` and follow its process. Pass entity type: `framework`, frameworks: the pre-merged list from Step 1a, task context: empty (the shared file will check conversation context and score it — see its Path 3/4 boundary logic).

If the user replies "list all" to any recommendation prompt, list all frameworks as described in Step 2. Do not score the reply as task context.

If `skills/_shared/contextual-recommendation.md` cannot be read, fall back to listing all available frameworks alphabetically.

## Step 4: Run the Framework

After matching, hand off to the shared runner.

**Resolving the absolute framework path.** The runner requires an absolute directory path and fails closed otherwise. Use the matched entry's `absolute_framework_dir` from Step 1a. The resolver already anchors plugin frameworks on the plugin root and project-local frameworks on the project directory.

Read `skills/_shared/framework-runner.md` and invoke it with:
- **Matched framework path:** the matched entry's `absolute_framework_dir`
- **`framework_entry`:** the matched merged entry (so the runner can find the framework's advisor)
- **`intake_gate_mode`:** `advisory` (preserves existing top-level invocation behavior — `required_documents` are noted to the user but execution proceeds)

The runner handles loading content, applying the intake gate, running phases with WAIT discipline, voice rules, and composability with `/aligned:use-advisor`.

## Avoid These Mistakes

- **Skipping phases** — Complete every phase in order. Do not jump ahead even if the user's situation seems to warrant it.
- **Rushing past pause points** — When the framework says to wait for a response, stop. Do not continue with the next question or phase in the same message.
- **Combining multiple frameworks** — Run one framework per session. If the user wants another framework, start a new invocation.
- **Improvising structure** — Follow the framework's phases exactly as written. Add warmth and personality, but do not invent new steps or skip existing ones.
- **Ignoring anti-examples** — If `anti-examples.md` was loaded, treat those patterns as hard constraints to avoid, not suggestions.
