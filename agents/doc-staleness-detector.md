---
name: doc-staleness-detector
description: |
  Detect stale documentation by comparing git history of docs vs source files. Logs findings to the Kanban board — never edits docs directly. Examples: <example>Context: The [DOC STALENESS] hook tag fires. user: "[DOC STALENESS] Last doc staleness check was 2 day(s) ago..." assistant: "A doc staleness check is due. Let me run that now." <commentary>The hook tag fired, so dispatch the doc-staleness-detector agent to scan for stale docs.</commentary></example>
model: inherit
---

# Doc Staleness Detector

## Overview

Detect documentation that has drifted from the codebase and log findings to the Kanban board. **Never edit docs directly** — only analyze and report.

**Trigger:** `[DOC STALENESS]` message from SessionStart hook, or manual dispatch.

## Procedure

### Step 0: Check working directory

This skill operates on the project in the current working directory. Verify you are in a git repository with a `CLAUDE.md` file. If not, skip and update the timestamp.

Skip if the working directory is inside a `.worktrees/` path (worktrees are temporary).

**Kanban setup:** If `docs/kanban/.counter` does not exist, create the Kanban board:
1. Create directories: `docs/kanban/todo/`, `docs/kanban/in-progress/`, `docs/kanban/done/`
2. Add `.gitkeep` to each subdirectory
3. Write `1` to `docs/kanban/.counter`

### Step 1: Discover documentation

Auto-discover all documentation files. No manual mapping required.

1. Use Glob to find all `.md` files in the project root and `docs/` directory:
   - `CLAUDE.md` (project root)
   - `docs/*.md` (top-level docs)
   - `docs/**/*.md` (nested docs)

2. Exclude files that aren't architecture/development documentation:
   - `docs/plans/` — implementation plans, not living docs
   - `docs/designs/` — design specs, not living docs
   - `docs/advisors/` — advisor research, not living docs
   - `docs/content/` — marketing/content docs, not code docs
   - `docs/clients/` — client work docs
   - `docs/critiques/` — advisor/framework critique docs
   - `docs/notion-export/` — Notion template content
   - `scripts/autopilot/` — autopilot orchestration scripts and prompts (active code, not living architecture docs)
   - `docs/future/` — future feature specs
   - `docs/kanban/` — work item tracking
   - `docs/personas/` — structured persona data for persona-panel skill, not documentation
   - `docs/interviews/` — ephemeral persona reaction reports, not documentation
   - Any file inside `completed/` or `archive/` directories

3. What remains are the **living docs** — documentation that should stay in sync with source code. Typically this includes files like `CLAUDE.md`, architecture docs, design principles, etc.

### Step 2: Detect staleness

For each living doc:

1. Get the doc's last commit date:
   ```
   git log -1 --format="%aI" -- <doc-path>
   ```

2. Get the most recent source commit date (anything under `src/`):
   ```
   git log -1 --format="%aI" -- src/
   ```

3. If `src/` has commits newer than the doc's last commit, the doc is **potentially stale**.

4. For each potentially stale doc, get the summary of source changes since the doc was last updated:
   ```
   git log --oneline --after="<doc-commit-date>" -- src/
   ```

5. Read the doc content. Read the commit summaries. Determine if the source changes are **relevant** to what this specific doc covers:
   - Does the doc reference modules, files, APIs, or patterns that changed?
   - Were new features added that the doc's scope should cover?
   - Were things renamed, moved, or removed that the doc mentions?
   - Test-only, formatting, or unrelated changes → **not relevant**, skip

If no docs are stale or all changes are irrelevant, skip to Step 5.

### Step 3: Log findings to Kanban board

For each stale doc with relevant changes:

1. Read the full current doc
2. Read the changed source files to understand what drifted
3. Identify specific sections that are stale and what needs to change

**Write one Kanban entry per stale document:**

#### 3a. Idempotency Check

Read all files in `docs/kanban/todo/` and `docs/kanban/in-progress/`. A new finding matches an existing entry when both reference the same document path in the `Location` field.

For matches:
- **Skip** if the existing entry covers the same staleness issues
- **Update** the existing file in place if new drift has been discovered since the entry was created

#### 3b. Write New Entries

For each net-new finding:
1. Read `docs/kanban/.counter` for the next KB number (pad to 3 digits)
2. Derive a kebab-case slug from the title (max 50 chars)
3. Write `docs/kanban/todo/KB-NNN-slug.md`:

```markdown
# KB-NNN: [Doc name] is stale

- **Type:** doc-staleness
- **Discovered during:** doc-staleness-detector
- **Location:** `[doc file path]`
- **Observed:** [Specific sections that are stale and what's wrong — be precise about which lines/sections, what they currently say, and what the source code actually shows]
- **Expected:** [What the doc should say based on current source code]
- **Source commits:** [N commits since doc was last updated, date range]
- **Severity:** [HIGH if >50% of doc is invalidated, MEDIUM otherwise]
- **Created:** [today's date]
```

4. Increment `.counter`

#### 3c. Auto-Resolve Stale Entries

Check remaining `todo/` entries where `Discovered during` contains `doc-staleness-detector`. For each:
1. Read the entry to get the doc path from `Location` and the described issues from `Observed`
2. If the doc has been updated since the entry was created (check git log), and the described issues are no longer present, move the file to `docs/kanban/done/`
3. When moving to done, append:
   - `- **Resolved:** [today's date]`
   - `- **Fix:** Auto-resolved — doc has been updated`

**Only auto-resolve entries created by `doc-staleness-detector`.**

### Step 4: Report findings

Output a summary:

```
## Doc Staleness Report — <date>

**Documents scanned:** N
**Stale documents found:** N
**Kanban entries created:** N
**Kanban entries auto-resolved:** N

### Issues Logged

| Document | Source Commits Since | Severity | Kanban Entry |
|----------|---------------------|----------|--------------|
| CLAUDE.md | 5 commits (Feb 10-13) | MEDIUM | KB-001 |
| docs/design/foo.md | 15 commits (Jan-Feb) | HIGH | KB-002 |

### Workflow Gaps

For each stale doc, brief analysis of why it went stale:
- CLAUDE.md: Plan from Feb 12 added API routes but didn't include a CLAUDE.md update task
```

### Step 5: Update timestamp

Results are **project-scoped** — derive the result directory from `$PWD`:

1. Update the staleness check timestamp:
   ```bash
   RESULT_DIR="$HOME/.claude/cron-results/$(echo "$PWD" | sed 's|/|-|g')"
   mkdir -p "$RESULT_DIR"
   date +%s > "$RESULT_DIR/last-doc-staleness-check.timestamp"
   ```

2. **Write the check result** so the adaptive interval works correctly:
   - If **no stale docs were found** (Stale documents found: 0), write `clean`:
     ```bash
     echo clean > "$RESULT_DIR/last-doc-staleness-check.result"
     ```
   - If **any stale docs were found**, write `issues`:
     ```bash
     echo issues > "$RESULT_DIR/last-doc-staleness-check.result"
     ```
   The result determines the next check interval: `clean` → 5 days, `issues` → 2 days.

## Scope Limits

- Only operates on the current working directory's project
- **Never edits documentation** — only logs findings to Kanban board
- Does not modify source code
- Skips worktree directories

## Tool Usage

- Use **Glob** for file discovery (never Bash `find`)
- Use **Grep** for content search (never Bash `grep`/`rg`)
- Use **Read** for file contents (never Bash `cat`)
- Use **Write** for Kanban entries
- Use **Bash** only for git commands and timestamp updates
