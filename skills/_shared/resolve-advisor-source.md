# Resolving the Merged Advisor Source

Shared procedure that returns the merged advisor set (plugin global + project-local)
plus the plugin's panel `selection_guidelines`. Every advisor read path calls this so
the merge logic cannot drift across callers. This is the advisor-side parallel of the
framework merge already implemented in `skills/use-framework/SKILL.md` Step 1.

> **Note:** This is a `skills/_shared/` library file. `{base-directory}` refers to the
> CALLING skill's base directory; the caller resolves it per `skills/_shared/resolve-skill-path.md`
> before reading this file. Do NOT add a Path Resolution note here.

## Procedure

1. **Load the plugin registry (canonical).** Read the plugin `advisors/registry.yaml`
   (resolve the plugin root per `skills/_shared/resolve-skill-path.md` — Plugin root section).
   Parse both its `advisors:` list and its top-level `selection_guidelines:` block. Tag every
   advisor entry `source: "plugin"`.

2. **Merge the project-local registry (if present).** If `<project-cwd>/advisors/registry.yaml`
   exists, load it and merge its `advisors:` list. Tag those entries `source: "local"`.
   **Dedupe by `id` before returning** — on a duplicate `id`, **local-wins** (the local entry
   replaces the plugin entry). Deduping before return guarantees a shadowed plugin advisor
   never double-lists in a panel candidate set.

3. **Compute the absolute prompt path for every entry.**
   `absolute_prompt_path = <scope-root>/<prompt-dir>/<id>.md` where:
   - `<scope-root>` = **plugin-root** for `source: "plugin"` entries, **project-cwd** for
     `source: "local"` entries.
   - `<prompt-dir>` = the CLAUDE.md-configured advisor prompt path if present (the same key
     `add-advisor` Step 0 reads), else the default `advisors/prompts`.

   The stored `prompt:` field is **ignored for resolution** — it is plugin-relative on every
   entry and would mis-resolve a local advisor. It remains as human-readable metadata only.

**Anchoring rule:** local advisors resolve against **project-cwd**, never plugin-root.
`resolve-skill-path.md` is for plugin-bundled files only and is NOT reused for locals.
Local advisors live at `<project-root>/advisors/` (registry + `prompts/`), not a `.claude/`-nested
path — the personal repo is not a plugin and has no `.claude-plugin/plugin.json`.

## Return contract

Return a single object. Callers couple to this shape — do not vary it.

```
{
  advisors: [
    { id, name, summary, domains, evaluation_expertise, best_for, not_for,
      absolute_prompt_path, source: "plugin" | "local" }
  ],
  selection_guidelines: { ... }   // PLUGIN-CANONICAL — local repos do NOT override
                                  // panel selection rules (no use case; YAGNI)
}
```

- `selection_guidelines` is a sibling of `advisors`, taken from the **plugin** registry only.
- Every per-advisor field is present for both plugin and local advisors. A local registry entry
  MUST carry the full advisor schema (`id`, `name`, `summary`, `prompt`, `domains`; profiled
  fields when applicable).

## Error paths

- **Local `advisors/registry.yaml` absent** → return the plugin-only result. No error.
- **Local registry malformed YAML** → **degrade to plugin-only and emit a one-line warning
  naming the file.** A broken local registry must not lock the user out of plugin advisors.
  (This differs from `add-advisor`'s write-side revert-on-parse-failure, which is correct for a
  write but wrong for a read.)
- **Prompt-dir CLAUDE.md override absent** → use the default `<scope-root>/advisors/prompts/<id>.md`.
- **Resolved prompt file missing** → the resolver does NOT error. `advisor-runner.md`
  fail-closes at use time (preserved behavior).
- **Resolver file itself unreadable** → this is outside the resolver's own error contract.
  It indicates a plugin installation failure, not a merge failure. The resolver cannot handle
  its own non-existence; each call site handles it independently. `use-advisor` does NOT degrade
  silently — an unreadable resolver signals a broken plugin install, not a recoverable condition.
  `critique-panel-orchestration` falls back to the glob path (plugin-only; documented in Task 5).
