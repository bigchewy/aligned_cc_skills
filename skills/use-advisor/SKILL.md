---
name: use-advisor
description: "Adopts an advisor's persona for the conversation. Use with an advisor name for fuzzy match, or alone to list available advisors. Triggers when a user mentions an advisor by name or asks to channel a specific expert's perspective."
---

# Use Advisor

Adopt an advisor's persona for the current conversation.

## Invocation

- `/aligned:use-advisor byron katie` — fuzzy match, adopt persona
- `/aligned:use-advisor` — list available advisors

## Step 1: Discover Available Advisors

**Step 1a: Resolve the merged advisor set**

Read `skills/_shared/resolve-advisor-source.md` (plugin-relative path) and follow its procedure
to obtain the merged advisor set (plugin global + project-local, deduped, local-wins). Use the
returned `advisors` list as the listing source — each entry carries `id`, `name`, `summary`,
`domains`, `absolute_prompt_path`, and `source`.

> The resolver's own error paths already handle degradation (absent local registry → plugin-only
> result; malformed local YAML → degrade + warn). No additional fallback is needed here — a
> resolver file that cannot be read indicates a plugin installation failure, which is a distinct
> failure mode and not something `use-advisor` should silently paper over.

## Step 2: Extract Advisor Names

Read the first line of each file. All files follow the format: "You are [Name], ..." — extract the name after "You are " and before the first comma. Do not split on periods (names like "Sue B. Zimmerman" contain periods).

If a file doesn't match this format, skip it and continue. Do not fail the entire listing because one file is malformed.

List advisors alphabetically by display name. When both scopes contribute (the resolver returned
entries with `source: "local"` as well as `source: "plugin"`), annotate each local advisor with a
trailing `(local)` marker so the user can tell repo-specific advisors from global ones.

## Step 3: Match User Input

If the user provided an advisor name argument:

1. Match against both the filename slug (e.g., `byron-katie`) and the extracted display name (e.g., `Byron Katie`)
2. Use case-insensitive substring matching
3. **Single match:** Use it
4. **Multiple matches:** Ask the user which one they meant
5. **No match → contextual recommendation:** The args didn't match any entry name, so treat them as task context. Read `skills/_shared/contextual-recommendation.md` (plugin-relative path) and follow its process. Pass entity type: `advisor`, advisors: the pre-merged list from Step 1a, task context: the user's original args.

**Important:** Match ONLY against the slug (filename) and display name (extracted from first line). Do not match against descriptions, framework names, or other content in the file.

If no argument was provided, read `skills/_shared/contextual-recommendation.md` and follow its process. Pass entity type: `advisor`, advisors: the pre-merged list from Step 1a, task context: empty (the shared file will check conversation context and decide whether to score or prompt — see its Path 3/4 boundary logic).

If `skills/_shared/contextual-recommendation.md` cannot be read, fall back to listing all available advisors alphabetically.

## Step 4: Run the Advisor

After matching, hand off to the shared runner.

**Resolving the absolute advisor path.** The runner requires a file that exists and fails closed otherwise. Use the matched advisor's `absolute_prompt_path` returned by the resolver in Step 1a
(it already anchors plugin advisors on plugin-root via `skills/_shared/resolve-skill-path.md` and local advisors on project-cwd). Plugin advisor paths follow the pattern `<plugin-root>/advisors/prompts/<id>.md`.

Read `skills/_shared/advisor-runner.md` and invoke it with:
- **Matched advisor path:** the absolute path constructed above
- **`greeting_mode`:** `full` (preserves existing top-level invocation behavior — brief greeting + Core Frameworks listing)

The runner handles persona adoption, voice rules, the switching/ending lifecycle, and composability with `/aligned:use-framework`.
