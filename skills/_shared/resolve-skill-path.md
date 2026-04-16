# Resolving a Skill's Base Directory

Skills in the aligned plugin reference their own bundled files using a `{base-directory}` placeholder. This doc explains the single procedure every skill uses to resolve that placeholder.

## Contents
- Primary source
- Fallback
- Plugin root
- Usage pattern
- Shared library files (`skills/_shared/`)
- Edge case: multiple plugin installs

## Primary source

When a skill loads, the Claude Code harness prints a line near the top of the conversation turn:

`Base directory for this skill: /absolute/path/to/skills/<skill-name>`

Use that path as `{base-directory}`. It's the fastest and most accurate source.

## Fallback

If the "Base directory for this skill:" line has been compressed out of context (long conversations), resolve via the plugin root:

1. Glob `$HOME` for `**/.claude-plugin/plugin.json`. This file uniquely identifies a Claude Code plugin's root; the aligned plugin's copy is the one whose parent directory contains a `skills/` subdirectory with the skill's name.
2. Take the parent of the matched `.claude-plugin/` directory — that is the plugin root.
3. Derive `{base-directory}` = `<plugin-root>/skills/<this-skill-name>/`.

This uses a single Glob with a unique anchor, which is faster and more reliable than `$HOME`-wide globbing on skill filenames.

If the Glob returns no matches, STOP and tell the user the plugin appears to be missing or misinstalled.

## Plugin root

If a skill needs the plugin root directly (e.g., to locate `docs/ralph_loops/` or reference sibling skill paths), perform steps 1–2 of the Fallback procedure. Do not derive the plugin root by string-manipulating `{base-directory}` — always anchor on `.claude-plugin/plugin.json`.

## Usage pattern in skill files

Each skill that references its own bundled files includes one "Path Resolution" note near the top of SKILL.md:

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/<this-skill-name>/`. See `skills/_shared/resolve-skill-path.md` for rationale.

All later references to `{base-directory}` in the same file use the placeholder without restating the resolution procedure.

## Shared library files (`skills/_shared/`)

Files inside `skills/_shared/` (e.g., `critique-panel-orchestration.md`, `kanban-entry-format.md`) are read by multiple skills. When they reference `{base-directory}`, it means **the calling skill's base directory**, not `_shared/` itself. The caller is responsible for resolving `{base-directory}` (using the procedure above) BEFORE reading or quoting content from a `_shared/` file. Shared files do NOT perform their own resolution — do not add the Path Resolution note to `_shared/` files.

## Edge case: multiple plugin installs

If the Glob for `**/.claude-plugin/plugin.json` returns more than one match (e.g., a user has both a development clone and an installed marketplace copy of the aligned plugin), prefer the match whose `plugin.json` contains `"name": "aligned"` AND has a `skills/<this-skill-name>/SKILL.md` under its parent directory. If still ambiguous, prefer the match whose parent is under the current working directory or its ancestors. If still ambiguous, STOP and ask the user which install to use.
