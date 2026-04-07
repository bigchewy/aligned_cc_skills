---
name: portability-audit
description: "Scan the plugin repo for environment-specific hardcoding that breaks portability"
---

# Portability Audit

Scans the Aligned plugin repo for environment-specific hardcoding that would break the plugin for other users. Targets three violation classes: absolute user paths (CRITICAL), non-plugin external file dependencies (HIGH), and platform-specific assumptions (MEDIUM). Read-only — diagnosis only, never edits source code.

**Announce at start:** "Running portability audit on the plugin repo."

## Phase 0: Context Gathering & Validation

1. Verify the skill is running in the correct repo by checking for `.claude-plugin/plugin.json` at the repo root using Glob. If absent, report: "This skill is designed for the Aligned plugin repo. Run it from the plugin root directory." and stop.

2. Read the repo's `CLAUDE.md` (and any nested CLAUDE.md files in subdirectories found via `Glob("**/CLAUDE.md")`). Save content — used in Phase 3 to check whether path patterns are documented as intentional.

3. Read `{base-directory}/references/portability-pitfall-catalog.md` for detection categories, regexes, and false-positive rules. (Resolve `{base-directory}` from the "Base directory for this skill:" line printed when this skill loaded.)

## Phase 1: File Discovery

Two Bash commands (the ONLY Bash allowed in this skill):

1. `git ls-files` — all tracked files
2. `git ls-files --others --exclude-standard` — untracked non-ignored files

Filter the combined list to scannable text extensions: `.md`, `.json`, `.yaml`, `.yml`, `.sh`, `.js`, `.ts`, `.toml`, `.txt`, `.html`

Store the file count (tracked vs untracked) for the report header.

If either `git ls-files` command fails (e.g., not a git repo), report the error and stop — do not proceed with an incomplete file set.

## Phase 2: Pattern Scanning

For each detection category (P1–P3), run Grep across the repo with the category's detection regex. Use Grep with `output_mode: "content"` and `-C 2` for surrounding context (needed for false-positive evaluation in Phase 3).

**Do NOT use Bash for content search — use Grep tool exclusively.** Bash grep triggers permission prompts that halt execution.

**P1 scans (CRITICAL):**
- Grep pattern: `/Users/[a-zA-Z][a-zA-Z0-9._-]+/`
- Grep pattern: `/home/[a-zA-Z][a-zA-Z0-9._-]+/`
- Grep pattern: `C:\\Users\\[a-zA-Z][a-zA-Z0-9._-]+\\`

**P2 scans (HIGH):**
- Grep pattern: `~/(?!\.claude/|\.config/)[a-zA-Z0-9._-]+/`

**P3 scans (MEDIUM) — restrict to executable files only:**
- Grep pattern: `date -j` with glob `*.{sh,js,ts}`
- Grep pattern: `pbcopy|pbpaste` with glob `*.{sh,js,ts}`
- Grep pattern: `\bopen ` with glob `*.{sh,js,ts}`
- Grep pattern: `/usr/local/bin/` with glob `*.{sh,js,ts}`

Run all Grep calls in parallel where possible.

If a Grep command fails for a category, report it as `SCAN ERROR: [category] — [error]` in the output rather than silently skipping.

## Phase 3: False-Positive Filtering

For each match from Phase 2, apply filters from the catalog in this order:

1. **Cross-cutting rules first:**
   - Portable home directory references (`~/.claude/`, `~/.config/`, `$HOME`, `${HOME}`, `process.env.HOME`, `os.homedir()`) → SAFE
   - Runtime-resolved placeholders (`{base-directory}`, `{project-root}`, `{plugin-root}`, `{design-file-path}`, `${CLAUDE_PLUGIN_ROOT}`) → SAFE
   - Graceful fallback chains: shell `||` on the same line, `command -v` detection, `if [ -f ... ]` conditionals → SAFE
   - Documentation references: inside fenced code blocks with generic placeholders, or on the same line as `e.g.` → SAFE
   - CLAUDE.md documented conventions: path pattern documented as intentional in Phase 0 content → SAFE

2. **Category-specific rules** from the catalog

3. If any rule marks a match as SAFE, exclude it from findings

4. Use Read for rules that need multi-line context (e.g., verifying fallback chains that span multiple lines)

## Phase 4: Report Generation

Group surviving findings by severity (CRITICAL → HIGH → MEDIUM), then by category within each severity.

**When findings exist:**

```
## Portability Audit Report

**Scanned:** N files (N tracked, N untracked)
**Findings:** N total (N critical, N high, N medium)

### CRITICAL

#### P1: Absolute User Path
- **File:** skills/some-skill/SKILL.md:42
- **Match:** `/Users/ericpage/.claude/skills/`
- **Risk:** Path contains literal username — fails on any other machine
- **Suggested fix:** Replace with `~/.claude/skills/` or `{base-directory}`

### HIGH

#### P2: Non-Plugin External File Dependency
...

### MEDIUM
...

### Clean Categories
- P3: Platform-Specific Assumptions — no findings
```

**When all categories are clean:**

```
## Portability Audit Report

**Scanned:** N files (N tracked, N untracked)

No portability violations found. The plugin is portable.
```

## Red Flags — Things This Skill Must Never Do

- **Never edit source code.** This is a read-only audit. Diagnosis only.
- **Never use Bash for content search.** Use Grep tool exclusively.
- **Never flag patterns documented in CLAUDE.md as issues.** Documented conventions are intentional.
- **Never suppress findings based on natural-language fallback descriptions.** Only mechanically detectable fallback chains (shell `||`, `command -v`, `if [ -f ]`) are auto-suppressed.

## Kanban Entry Format

When filing a Kanban entry, read `{base-directory}/../_shared/kanban-entry-format.md` for the template and counter instructions. Use `portability-audit` as the "Discovered during" value.
