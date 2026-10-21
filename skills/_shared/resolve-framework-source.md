# Resolving the Merged Framework Source

Shared procedure that returns the merged framework set (plugin global + project-local).
Every framework read path calls this so the merge logic cannot drift across callers. This is
the framework-side parallel of `skills/_shared/resolve-advisor-source.md`.

> **Note:** This is a `skills/_shared/` library file. `{base-directory}` refers to the
> CALLING skill's base directory; the caller resolves it per `skills/_shared/resolve-skill-path.md`
> before reading this file. Do NOT add a Path Resolution note here.

## Procedure

1. **Load the plugin registry (canonical).** Read the plugin `frameworks/registry.yaml`
   (resolve the plugin root per `skills/_shared/resolve-skill-path.md` — Plugin root section).
   Tag every entry `source: "plugin"` and `registered: true`.

2. **Merge the project-local registry (if present).** If `<project-cwd>/frameworks/registry.yaml`
   exists, load it and merge its `frameworks:` list. Tag those entries `source: "local"` and
   `registered: true`. **Dedupe by `id` before returning** — on a duplicate `id`, **local-wins**
   (the local entry replaces the plugin entry). Deduping before return guarantees a shadowed
   plugin framework never double-lists.

3. **Find unregistered local folders.** Glob `<project-cwd>/frameworks/*/prompt.md`. For every
   folder whose name is not already a local `id`, add an entry with `registered: false`,
   `source: "local"`, and `id` = the folder name. Read the first `You are ...` line of its
   `prompt.md` (skip any frontmatter); it follows the standard format
   `You are {Advisor}, guiding someone through {Framework} - {purpose}.` Take `advisor` and
   `name` from it. If the first line does not match that format, use the folder name as `name`
   and leave `advisor` empty. Set `purpose`, `category`, `domains`, and `use_when` to empty.
   If the folder name matches a plugin `id`, local still wins.

4. **Compute the absolute paths for every entry.**
   `absolute_framework_dir = <scope-root>/frameworks/<id>/` and
   `absolute_prompt_path = <absolute_framework_dir>prompt.md`, where `<scope-root>` is
   **plugin-root** for `source: "plugin"` entries and **project-cwd** for `source: "local"`
   entries.

Skip steps 2 and 3 when project-cwd is the plugin root. The plugin's own folders are already
loaded in step 1.

**Anchoring rule:** local frameworks resolve against **project-cwd**, never plugin-root.
`resolve-skill-path.md` is for plugin-bundled files only and is NOT reused for locals.
Local frameworks live at `<project-root>/frameworks/` (registry + one folder per framework),
not a `.claude/`-nested path.

## Finding a framework's advisor

Look up the entry's `advisor` in the merged advisor set from
`skills/_shared/resolve-advisor-source.md`, and use that entry's `absolute_prompt_path`. Match
by `id` first, then by display `name`, ignoring case. Unregistered folders need the name match,
because their `advisor` is a display name such as "Example Local Advisor", not an id. If nothing
matches, the framework-runner falls back to its generic facilitator. A local framework may name
a plugin advisor or a local advisor; the merged set holds both.

## Return contract

Return a single object. Callers couple to this shape — do not vary it.

```
{
  frameworks: [
    { id, name, advisor, purpose, category, domains, use_when,
      deliverable_type?, default_critic_advisors?, required_documents?, helpful_documents?,
      absolute_framework_dir, absolute_prompt_path, source: "plugin" | "local",
      registered: true | false }
  ]
}
```

- A local registry entry MUST carry the full framework schema (`id`, `name`, `advisor`,
  `purpose`, `category`, `domains`, `use_when`). The `?` fields are optional.
- Unregistered local folders get `registered: false` and only the fields step 3 fills in.

## Error paths

- **Local `frameworks/registry.yaml` absent** → return the plugin-only result, plus any folders
  the glob in step 3 finds. No error.
- **Local registry malformed YAML** → **degrade to plugin-only, keep the glob from step 3, and
  emit a one-line warning naming the file:**
  `Warning: could not parse <path>; using plugin frameworks only.` A broken local registry must
  not lock the user out of plugin frameworks.
- **Resolved `prompt.md` missing** → the resolver does NOT error. The framework-runner
  fails closed at use time.
- **Resolver file itself unreadable** → outside the resolver's own error contract. It indicates
  a plugin installation failure, not a merge failure. Each call site handles it independently.
