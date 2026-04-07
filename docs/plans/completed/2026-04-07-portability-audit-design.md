# Portability Audit Skill Design

**Date:** 2026-04-07
**Status:** Draft
**Skill:** `/aligned:portability-audit`
**Mockups:** docs/mockups/portability-audit.html

## Overview

Portability Audit scans the Aligned plugin repo for environment-specific hardcoding that would break the plugin for other users. It targets two classes of violations:

1. **Absolute user paths** — Any path containing a literal username directory (e.g., `/Users/ericpage/`, `/home/alice/`). These work on exactly one machine.
2. **Personal file dependencies** — References to files that exist on the author's machine but aren't shipped with the plugin and aren't standard Claude Code conventions. If another user clones this repo and a skill requires a file that doesn't exist in the repo or `~/.claude/`, that's a portability violation.

The skill is invoked manually via `/aligned:portability-audit`. It reads CLAUDE.md for documented conventions, scans all git-known files (tracked + untracked non-ignored), applies false-positive filtering from a reference catalog, and produces a severity-grouped report with suggested fixes.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Execution model | Single-pass SKILL.md with reference catalog | Matches `finishing-a-development-branch` Step 0 pattern. All 3 categories use the same method (Grep + filter). No analytical diversity that would benefit from parallel worker sub-agents. |
| False-positive handling | Inline rules in reference catalog | Follows `deployment-pitfall-catalog.md` pattern. Only 6 stable categories of safe patterns — an external allowlist would be scanner logic with extra steps. |
| File discovery | `git ls-files` via Bash | Git-aware filtering is a git concept, not a filesystem concept. Glob can't respect `.gitignore` rules. |
| Output format | Severity-grouped findings (CRITICAL/HIGH/MEDIUM) | Matches deployment audit report format. No confidence scores, no finding cap, no dimension tables. |
| Scope | This plugin repo only | Not designed as a general-purpose portability scanner for arbitrary repos. |

## Detection Categories

The reference catalog (`references/portability-pitfall-catalog.md`) defines three categories:

### P1: Absolute User Paths (CRITICAL)

- **Detection:** Grep for patterns matching `/Users/<name>/`, `/home/<name>/`, `C:\Users\<name>\`
- **Regex:** `/Users/[a-zA-Z][a-zA-Z0-9._-]+/` and equivalents for Linux/Windows
- **Severity:** CRITICAL — always breaks on another machine, no ambiguity
- **Note:** This category subsumes hardcoded home directory values (e.g., `/Users/ericpage/.config/...` instead of `$HOME/.config/...`) — same regex catches both

### P2: Non-Plugin External File Dependencies (HIGH)

- **Detection:** References to files outside the plugin tree that aren't standard Claude Code paths (`~/.claude/`). Identified by: paths containing `~/` followed by directories that aren't `.claude/` or `.config/`. Verify the referenced file doesn't exist in the plugin repo using Glob against the file set from Phase 1. Skip paths containing template variables (`{base-directory}`, `{project-root}`, etc.).
- **Severity:** HIGH — skill will fail for other users if the file doesn't exist and there's no fallback
- **Note:** References with fallback chains (local → global → plugin default) are handled by false-positive rules

### P3: Platform-Specific Assumptions (MEDIUM)

- **Detection:** macOS-only commands like `date -j`, `pbcopy`, `open` (without fallback), or paths like `/usr/local/bin/` that assume Homebrew
- **Severity:** MEDIUM — breaks on Linux but not on other macOS machines
- **Scope:** Only in executable files (.sh, .js) — not in documentation describing macOS usage

## False-Positive Rules

Five cross-cutting rules that apply across categories, plus category-specific rules in the catalog.

### Portable Home Directory References (P1, P2)

- `~/.claude/` paths → SAFE (tilde expands per-user, standard Claude Code convention)
- `~/.config/` paths → SAFE (XDG base directory convention)
- `$HOME`, `${HOME}`, `process.env.HOME`, `os.homedir()` → SAFE (programmatic home directory resolution)

### Runtime-Resolved Placeholders (P1, P2)

- `{base-directory}`, `{project-root}`, `{plugin-root}`, `{design-file-path}` → SAFE (template variables resolved by Claude Code at skill load time)
- `${CLAUDE_PLUGIN_ROOT}` → SAFE (plugin runtime environment variable)

### Graceful Fallback Chains (P2, P3)

Mechanically detectable patterns only — no natural-language heuristics:
- Shell `||` chaining on the same line (e.g., `date -j ... || date -d ...`) → SAFE
- `command -v` feature detection (e.g., `command -v gstdbuf || stdbuf`) → SAFE
- Shell conditionals (`if [ -f ... ]; then ... else ...`) → SAFE

Fallback chains expressed only in natural language (e.g., "If not found, read ~/.claude/Y") are NOT auto-suppressed. These are reported as findings for human review — the user decides whether the fallback is adequate.

### Documentation References (all categories)

- Paths inside fenced code blocks that use generic placeholders → SAFE
- Paths on the same line as an `e.g.` marker → SAFE (covers inline examples like `~/software/project-a`)

### CLAUDE.md Documented Conventions (all categories)

- Phase 0 reads the repo's CLAUDE.md files. Any path pattern explicitly documented there as intentional is SAFE.

## Scanning Process

### Phase 0: Context Gathering & Validation

1. Verify the skill is running in the correct repo by checking for `.claude-plugin/plugin.json` at the repo root. If absent, report: "This skill is designed for the Aligned plugin repo. Run it from the plugin root directory." and stop.
2. Read the repo's CLAUDE.md (and any nested CLAUDE.md files in subdirectories) to identify documented conventions and intentional path patterns.
3. Read `references/portability-pitfall-catalog.md` for detection categories and false-positive rules.

### Phase 1: File Discovery

Two Bash commands (the only Bash allowed in this skill):

1. `git ls-files` — all tracked files
2. `git ls-files --others --exclude-standard` — untracked non-ignored files

Combine and filter to scannable text extensions: `.md`, `.json`, `.yaml`, `.yml`, `.sh`, `.js`, `.ts`, `.toml`, `.txt`, `.html`

If either `git ls-files` command fails (e.g., not a git repo), report the error and stop — do not proceed with an incomplete file set.

### Phase 2: Pattern Scanning

For each detection category (P1–P3), run Grep across the file set with the category's detection regex. Collect matches with file path, line number, and 2 lines of surrounding context for false-positive evaluation. If a Grep command fails for a category, report it as "SCAN ERROR: [category] — [error]" in the output rather than silently skipping.

### Phase 3: False-Positive Filtering

For each match:

1. Check cross-cutting rules first (portable home dir, runtime placeholders, fallback chains, CLAUDE.md conventions)
2. Check category-specific rules
3. If any rule marks the match as SAFE, exclude it
4. Use Read for rules that need multi-line context (e.g., fallback chain detection)

### Phase 4: Report Generation

Group surviving findings by severity (CRITICAL → HIGH → MEDIUM), then by category within each severity. Include a "Clean Categories" section listing any categories with zero findings.

When all categories are clean, emit a short summary: "No portability violations found. The plugin is portable." — no verbose empty report.

## Output Format

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

#### P3: Non-Plugin External File Dependency
- **File:** agents/some-agent.md:28
- **Match:** `~/.claude/docs/design/design-principles.md`
- **Risk:** References file outside plugin tree with no fallback
- **Suggested fix:** Add fallback chain: check local repo first, then `~/.claude/`, then plugin-bundled default

### MEDIUM
...

### Clean Categories
- P3: Platform-Specific Assumptions — no findings
```

When clean:

```
## Portability Audit Report

**Scanned:** N files (N tracked, N untracked)

No portability violations found. The plugin is portable.
```

## Skill Structure

```
skills/portability-audit/
  SKILL.md                                    # Frontmatter + scanning process
  references/portability-pitfall-catalog.md   # Detection categories, regexes, false-positive rules
```

SKILL.md frontmatter:

```yaml
---
name: portability-audit
description: "Scan the plugin repo for environment-specific hardcoding that breaks portability"
---
```

The skill is self-contained — no agents, no workers, no sub-agent dispatching. Detection knowledge lives in the reference catalog. The SKILL.md orchestrates the scanning process.

## Codebase Validation

The Architect validated this design against the actual repo:

| Check | Result | Evidence |
|-------|--------|----------|
| P1 violations in tracked files | 0 | No `/Users/<name>/` matches in tracked files |
| P2 edge case | 1 inline example | `skills/writing-plans/SKILL.md:45` — `~/software/project-a` (false positive, handled by documentation rules) |
| P3 near-miss | 1, correctly handled | `hooks/check-eval-audit.sh:23` — `date -j` with `||` fallback |
| `{base-directory}` uses | 30+ across 12 skills | Runtime-resolved — correctly excluded |
| `~/.claude/` uses | 16 across 12 files | Tilde-expansion — correctly excluded |
| `${CLAUDE_PLUGIN_ROOT}` uses | 4 in hooks.json | Runtime variable — correctly excluded |
| Skill anatomy compatibility | Clean | `references/` dir used by 3 existing skills identically |

## Action Items (Pre-Implementation)

1. Fix `agents/doc-staleness-detector.md:46` — remove "(legacy, now at ~/.claude/ralph_loops/)" comment
