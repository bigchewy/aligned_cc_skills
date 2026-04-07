# Portability Audit Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Create a `/aligned:portability-audit` skill that scans the plugin repo for environment-specific hardcoding (absolute user paths, non-plugin external dependencies, platform-specific assumptions) and produces a severity-grouped report.

**Source Design Doc:** `docs/plans/2026-04-07-portability-audit-design.md`

**Mockups:** `docs/mockups/portability-audit.html`

**Architecture:** Single-pass SKILL.md with a reference catalog (`references/portability-pitfall-catalog.md`). Four phases: context gathering, file discovery, pattern scanning with Grep, false-positive filtering, and report generation. No sub-agents — the skill runs inline in one pass.

**Tech Stack:** Claude Code skill (Markdown), Grep/Glob/Read tools, `git ls-files` via Bash

---

### ✅ Task 1: Create the portability pitfall catalog

**Files:**
- Create: `skills/portability-audit/references/portability-pitfall-catalog.md`

**Step 1: Write the reference catalog**

Create the catalog following the format established by `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md`. The catalog defines three detection categories from the design doc:

```markdown
# Portability Pitfall Catalog

Reference document for the portability audit skill. Contains detection categories, regex patterns, false-positive rules, and suggested fixes for each violation type.

## How to Use This Catalog

For each category:
1. Run the **Detection** regex via Grep across the file set from Phase 1
2. For each match, read surrounding context and apply **False Positive Rules**
3. Report true positives with the **Severity**, file location, matched pattern, risk explanation, and suggested fix

---

## CRITICAL — Absolute User Paths

These contain a literal username directory. They work on exactly one machine and always break for other users.

### P1: Absolute User Paths

**Why it breaks:** Paths like `/Users/ericpage/` or `/home/alice/` are hardcoded to a specific machine. Any other user who clones the plugin gets immediate failures when skills reference these paths.

**Detection:**
- Grep for `/Users/[a-zA-Z][a-zA-Z0-9._-]+/` (macOS)
- Grep for `/home/[a-zA-Z][a-zA-Z0-9._-]+/` (Linux)
- Grep for `C:\\Users\\[a-zA-Z][a-zA-Z0-9._-]+\\` (Windows)

**False Positive Rules:**
- Match is inside a fenced code block AND uses a generic placeholder (e.g., `/Users/yourname/`) → SAFE
- Match is on the same line as an `e.g.` marker → SAFE (inline example like `e.g., /Users/alice/`)
- Match is inside a CLAUDE.md file that documents the path as intentional → SAFE (verify against Phase 0 CLAUDE.md content)
- Path uses `$HOME`, `${HOME}`, `process.env.HOME`, or `os.homedir()` instead of a literal username → SAFE (these are programmatic and resolve per-user)

**Fix:** Replace with:
- `~/.claude/...` for Claude Code convention paths
- `{base-directory}/...` for skill-relative paths
- `$HOME/...` or `${HOME}/...` for shell scripts
- `process.env.HOME` or `os.homedir()` for JS/TS

---

## HIGH — Non-Plugin External File Dependencies

References to files outside the plugin tree that aren't standard Claude Code paths. The skill will fail for other users if the file doesn't exist and there's no fallback.

### P2: Non-Plugin External File Dependencies

**Why it breaks:** If a skill references `~/some-custom-dir/file.md` that only exists on the author's machine, other users get a missing file error with no recovery path.

**Detection:**
- Grep for paths starting with `~/` followed by directories that are NOT `.claude/` or `.config/`
- Regex: `~/(?!\.claude/|\.config/)[a-zA-Z0-9._-]+/`
- For each match, verify the referenced file does NOT exist in the plugin repo using Glob
- Skip paths containing template variables: `{base-directory}`, `{project-root}`, `{plugin-root}`, `{design-file-path}`

**False Positive Rules:**
- `~/.claude/` paths → SAFE (tilde expands per-user, standard Claude Code convention)
- `~/.config/` paths → SAFE (XDG base directory convention)
- Path contains template variables (`{base-directory}`, `{project-root}`, etc.) → SAFE (runtime-resolved)
- `${CLAUDE_PLUGIN_ROOT}` → SAFE (plugin runtime environment variable)
- Shell `||` chaining on the same line → SAFE (graceful fallback)
- `command -v` feature detection on the same line → SAFE
- Shell conditional `if [ -f ... ]; then` wrapping the reference → SAFE
- Match is inside a fenced code block with generic placeholders → SAFE
- Match is on the same line as an `e.g.` marker → SAFE

**Fix:** Add a fallback chain: check local repo first, then `~/.claude/`, then plugin-bundled default. Or bundle the required file in the skill's `references/` directory.

---

## MEDIUM — Platform-Specific Assumptions

macOS-only commands or paths that break on Linux. Lower severity because the plugin primarily targets macOS Claude Code users, but still a portability concern.

### P3: Platform-Specific Assumptions

**Why it breaks:** Commands like `date -j`, `pbcopy`, or `open` (without fallback) only exist on macOS. Linux users get "command not found" errors.

**Detection — only in executable files (.sh, .js, .ts):**
- Grep for `date -j` (macOS-specific date flag)
- Grep for `pbcopy` or `pbpaste` (macOS clipboard)
- Grep for `\bopen ` followed by a URL or file path (macOS open command, not a generic word)
- Grep for `/usr/local/bin/` (assumes Homebrew)

**False Positive Rules:**
- Shell `||` chaining on the same line (e.g., `date -j ... || date -d ...`) → SAFE (has fallback)
- `command -v` feature detection wrapping the command → SAFE
- Match is in a `.md` documentation file (not executable) → SAFE (documentation describing macOS usage, not runtime code)

**Fix:** Add cross-platform fallback:
```bash
# date
date -j -f "%Y-%m-%d" "2026-01-01" "+%s" 2>/dev/null || date -d "2026-01-01" "+%s"

# clipboard
command -v pbcopy >/dev/null && echo "text" | pbcopy || echo "text" | xclip -selection clipboard
```

---

## Maintenance

Update this catalog when:
- New portability violations are discovered during audits
- The plugin starts targeting additional platforms
- New false-positive patterns are identified

Last updated: 2026-04-07
```

**Step 2: Verify the file was created**

Run: `ls -la skills/portability-audit/references/portability-pitfall-catalog.md`
Expected: File exists

**Step 3: Commit**

```bash
git add skills/portability-audit/references/portability-pitfall-catalog.md
git commit -m "feat(portability-audit): add portability pitfall catalog"
```

---

### ✅ Task 2: Create the SKILL.md entry point

**Files:**
- Create: `skills/portability-audit/SKILL.md`

**Step 1: Write SKILL.md**

The SKILL.md follows the pattern from `skills/codebase-audit/SKILL.md` — frontmatter, then phased instructions. Key differences: no sub-agents (single-pass), uses `git ls-files` for file discovery (the only Bash allowed), and Grep for all pattern scanning.

```markdown
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
- Grep pattern: `C:\\\\Users\\\\[a-zA-Z][a-zA-Z0-9._-]+\\\\`

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
```

**Step 2: Verify the file was created**

Run: `ls -la skills/portability-audit/SKILL.md`
Expected: File exists

**Step 3: Commit**

```bash
git add skills/portability-audit/SKILL.md
git commit -m "feat(portability-audit): add SKILL.md entry point"
```

---

### ✅ Task 3: Add skill to README reference table

**Files:**
- Modify: `README.md` (the Skill Reference table, after the `kanban-resolve` row)

**Step 1: Add the portability-audit row**

Insert after the `kanban-resolve` row (which reads `| kanban-resolve | Maintenance | ...`):

```markdown
| portability-audit | Maintenance | `/aligned:portability-audit` | Scan plugin repo for environment-specific hardcoding that breaks portability |
```

This keeps the Maintenance skills grouped together.

**Step 2: Verify the table renders correctly**

Read `README.md` and confirm the new row appears in the table with correct alignment.

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add portability-audit to skill reference table"
```

---

### ✅ Task 4: Add skill permission to kickstart Phase 5

**Files:**
- Modify: `skills/kickstart/SKILL.md` (the Phase 5 permissions `allow` array)

**Step 1: Add the permission entry**

Add `"Skill(aligned:portability-audit)"` to the permissions allow array in Phase 5. Insert it after the `"Skill(aligned:codebase-audit)"` line to keep maintenance skills grouped:

```json
      "Skill(aligned:codebase-audit)",
      "Skill(aligned:portability-audit)",
      "Skill(aligned:create-new-skill)",
```

**Step 2: Verify the edit**

Read `skills/kickstart/SKILL.md` and confirm the new entry is in the array with correct JSON syntax (trailing comma).

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "feat(kickstart): add portability-audit to Phase 5 permissions"
```

---

### ✅ Task 5: Bump plugin version

> **Ordering dependency:** Complete Task 3 first — both tasks modify `README.md`.

**Files:**
- Modify: `.claude-plugin/plugin.json` (the `version` field)
- Modify: `.claude-plugin/marketplace.json` (the `version` field)

**Step 1: Bump version in plugin.json**

Change `"version": "0.14.0"` to `"version": "0.15.0"` in `.claude-plugin/plugin.json`.

**Step 2: Bump version in marketplace.json**

Change `"version": "0.14.0"` to `"version": "0.15.0"` in `.claude-plugin/marketplace.json`.

**Step 3: Add changelog entry to README**

Add a new changelog entry before the `0.14.0` entry. Find the line `##### 0.14.0: Skill/Agent Cleanup Refactor` and insert above it:

```markdown
##### 0.15.0: Portability Audit
- New `/aligned:portability-audit` skill scans the plugin repo for environment-specific hardcoding
- Detects: absolute user paths (CRITICAL), non-plugin external file dependencies (HIGH), platform-specific assumptions (MEDIUM)
- Reference catalog at `skills/portability-audit/references/portability-pitfall-catalog.md`
- **26 skills** (+1)

```

**Step 4: Verify both files have matching versions**

Read both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` and confirm both show `"version": "0.15.0"`.

**Step 5: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
git commit -m "chore: bump version to 0.15.0 for portability-audit skill"
```

---

### ✅ Task 6: Verify the complete skill works end-to-end

**Files:**
- Read: `skills/portability-audit/SKILL.md`
- Read: `skills/portability-audit/references/portability-pitfall-catalog.md`

**Step 1: Verify skill structure matches anatomy**

Confirm the skill directory matches the expected anatomy from `CLAUDE.md`:
```
skills/portability-audit/
  SKILL.md                                    # Frontmatter + scanning process
  references/portability-pitfall-catalog.md   # Detection categories, regexes, false-positive rules
```

Run: `ls -R skills/portability-audit/`
Expected: `SKILL.md` and `references/portability-pitfall-catalog.md`

**Step 2: Verify frontmatter**

Read `skills/portability-audit/SKILL.md` and confirm:
- `name: portability-audit` matches the directory name
- `description` is present and descriptive

**Step 3: Verify cross-references**

Use Grep to confirm no broken cross-references:
- Grep for `portability-pitfall-catalog` in `skills/portability-audit/SKILL.md` — should find the reference to `{base-directory}/references/portability-pitfall-catalog.md`
- Grep for `portability-audit` in `README.md` — should find the table row
- Grep for `portability-audit` in `skills/kickstart/SKILL.md` — should find the permission entry

**Step 4: Verify catalog references match design doc categories**

Read the catalog and confirm all three categories from the design doc are present: P1 (Absolute User Paths), P2 (Non-Plugin External File Dependencies), P3 (Platform-Specific Assumptions).

**Step 5: Commit (no changes expected — verification only)**

No commit needed. If any verification step fails, fix the issue and commit the fix.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Catalog naming | `portability-pitfall-catalog.md` | `portability-catalog.md`, `detection-rules.md` |
| 2 | Skill layer in README | Maintenance | Infrastructure, Pipeline |
| 3 | Version bump size | 0.14.0 → 0.15.0 (minor) | 0.14.1 (patch) |
| 4 | P3 scope restriction | Executable files only (.sh, .js, .ts) | All files |
| 5 | Task ordering | Catalog first, then SKILL.md | SKILL.md first |

### Appendix: Decision Details

#### Decision 1: Catalog naming
**Chose:** `portability-pitfall-catalog.md`
**Why:** Follows the naming convention of the existing `deployment-pitfall-catalog.md` in `skills/finishing-a-development-branch/references/`. The design doc also references this name. Consistency across skills makes the repo easier to navigate.
**Alternatives rejected:**
- `portability-catalog.md`: Loses the "pitfall" framing that signals this is a list of things that go wrong
- `detection-rules.md`: Too generic, doesn't match existing conventions

#### Decision 2: Skill layer in README
**Chose:** Maintenance
**Why:** The `codebase-audit` skill — the closest analog — uses the Maintenance layer. Both are diagnostic, read-only audit skills. The Maintenance layer groups skills that check repo health rather than build features.
**Alternatives rejected:**
- Infrastructure: Reserved for operational tooling like `using-git-worktrees`
- Pipeline: Reserved for the build/deploy pipeline (writing-plans → executing-plans → finishing-a-development-branch)

#### Decision 3: Version bump size
**Chose:** 0.15.0 (minor bump)
**Why:** A new skill is new functionality, which is a minor version bump under semver. The changelog shows that all previous skill additions used minor bumps (0.5.0 for codebase-audit, 0.13.0 for unified brainstorming, 0.14.0 for the cleanup refactor).
**Alternatives rejected:**
- 0.14.1 (patch): Patches are for bug fixes, not new features

#### Decision 4: P3 scope restriction
**Chose:** Executable files only (.sh, .js, .ts)
**Why:** The design doc explicitly states P3 should only scan executable files: "Only in executable files (.sh, .js) — not in documentation describing macOS usage." This prevents false positives from docs that describe macOS commands without running them. Extended to `.ts` since the plugin has TypeScript hook files. `.html` files (included in Phase 1 scannable extensions) are excluded from P3 because they are documentation/mockup format, not executable code.
**Alternatives rejected:**
- All files: Would flood the report with documentation references to macOS commands

#### Decision 5: Task ordering
**Chose:** Catalog first, then SKILL.md
**Why:** The SKILL.md references the catalog via `{base-directory}/references/portability-pitfall-catalog.md`. Writing the catalog first means the reference target exists when SKILL.md is written, which matches the natural dependency order. Also lets the executor verify the catalog independently before building the orchestration layer on top.
**Alternatives rejected:**
- SKILL.md first: Would reference a file that doesn't exist yet, making verification harder during that task
