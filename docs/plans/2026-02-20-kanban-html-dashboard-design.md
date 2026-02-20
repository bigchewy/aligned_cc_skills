# Kanban HTML Dashboard — Design Document

**Goal:** A self-contained HTML Kanban board that shows real-time task status during plan execution and a persistent view of `docs/kanban/` boards across all active repos, updated by both the Ralph loop and executing-plans skill.

**Source:** Brainstorming session 2026-02-20.

---

## Architecture

```
Plan .md file (single source of truth for execution state)
  ├── Task headings marked with ✅/🔄/unmarked
  ├── Read by execution agents after each task
  └── Parsed to generate ↓

~/.claude/kanban-repos.json (repo registry)
  ├── Lists absolute paths to active repos
  └── Generator scans each for docs/kanban/

Multiple repos' docs/kanban/ (persistent project Kanban boards)
  ├── ~/software/va-web-app/docs/kanban/
  ├── ~/software/epch-projects/docs/kanban/
  ├── ~/software/aligned_cc_skills/docs/kanban/
  ├── ~/software/ewp-site/docs/kanban/ (if/when created)
  └── Each has: todo/, in-progress/, done/, did_not_complete/

.kanban.html (generated artifact, must be added to .gitignore)
  ├── Self-contained HTML with embedded CSS + data
  ├── Two tabs: Plan Execution | Project Kanban
  ├── Project Kanban tab shows boards from ALL registered repos
  ├── Auto-refreshes every 5 seconds via <meta> tag
  └── Written to worktree root (or project root if no worktree)
```

### Data Flow

1. **writing-plans** creates the plan → generates initial `.kanban.html` (all tasks in Todo)
2. **executing-plans** completes a task → marks ✅ in plan file → regenerates `.kanban.html`
3. **Ralph loop** completes a task → marks ✅ in plan file (already does this) → regenerates `.kanban.html`
4. User opens `.kanban.html` in browser → auto-refreshes every 5s → sees current state

### State Unification

Both execution modes mark tasks in the plan `.md` file using the same emoji convention:
- `### Task N: [Title]` — Todo (not started)
- `### 🔄 Task N: [Title]` — In Progress (currently executing or blocked)
- `### ✅ Task N: [Title]` — Done (completed and verified)

The plan file becomes the single source of truth. The HTML is a derived view.

---

## Component 1: Shared Kanban HTML Generator

**New file:** `skills/_shared/kanban-html-generator.md`

Contains the complete instructions for parsing plan files and `docs/kanban/` directories, plus the HTML template. All execution modes reference this single doc.

**Cross-reference header (include at top of file):**
> This file is referenced by: `skills/writing-plans/SKILL.md`, `skills/executing-plans/SKILL.md`, `docs/ralph_loops/EXECUTE-PLAN.md`. Update all three if changing trigger behavior or regeneration conventions.

### Plan Parsing Rules

1. Read the plan file at its absolute path
2. Extract the plan title from the first `# ` heading
3. Scan for task headings matching these patterns:
   - `### Task N: [Title]` → status: todo
   - `### 🔄 Task N: [Title]` → status: in-progress
   - `### ✅ Task N: [Title]` → status: done
4. If a 🔄 task has a `> BLOCKED: [reason]` line immediately below, capture the reason
5. Count tasks per status for the progress bar

### Repo Registry

**New file:** `~/.claude/kanban-repos.json`

A simple JSON array of absolute paths to active repos:

```json
[
  "/Users/ericpage/software/va-web-app",
  "/Users/ericpage/software/epch-projects",
  "/Users/ericpage/software/aligned_cc_skills",
  "/Users/ericpage/software/ewp-site"
]
```

The generator reads this file and scans each path for `docs/kanban/`. Repos without a `docs/kanban/` directory are silently skipped.

**Auto-create on first use:** If `~/.claude/kanban-repos.json` does not exist when the generator runs, auto-create it with the current project's root path as the sole entry. This ensures the Project Kanban tab works out of the box without manual setup. The user can add more repos later by editing the file.

### Project Kanban Parsing Rules

1. Read `~/.claude/kanban-repos.json` to get the list of repo paths
2. For each repo path, check if `{repo}/docs/kanban/` exists
3. For repos that have it, scan the four subdirectories: `todo/`, `in-progress/`, `done/`, `did_not_complete/`
4. For each `KB-NNN-slug.md` file, extract:
   - KB number and title from the `# KB-NNN: [Title]` heading
   - Type from `**Type:**` field
   - Severity from `**Severity:**` field
   - Created date from `**Created:**` field
5. Group items by repo, then by directory (column)
6. Derive a short repo label from the directory name (e.g., `va-web-app`, `epch-projects`)

### HTML Template

The generated `.kanban.html` must be a single self-contained file with:

**Head:**
- `<meta http-equiv="refresh" content="5">` for auto-reload
- `<meta charset="utf-8">`
- `<title>Kanban — [Plan Name]</title>`
- All CSS inline in a `<style>` block

**Tab bar:**
- Two tabs: "Plan Execution" and "Project Kanban"
- Tabs are plain HTML/CSS — no JavaScript required for switching
- Use CSS `:target` pseudo-class or radio button hack for tab switching without JS
- If no repos have `docs/kanban/` directories (or `~/.claude/kanban-repos.json` doesn't exist), omit the Project Kanban tab entirely

**Tab 1 — Plan Execution:**
- Header: plan title, progress bar (filled/total), task counts
- Three columns: Todo, In Progress, Done
- Each card: task number (bold) + title
- 🔄 cards show blocker note if present
- Column headers show count: "TODO (5)", "IN PROGRESS (1)", "DONE (6)"

**Tab 2 — Project Kanban (multi-repo):**
- One section per repo that has a `docs/kanban/` directory
- Section header: repo name (e.g., "va-web-app", "epch-projects")
- Four columns per repo: Todo, In Progress, Done, Did Not Complete
- Each card: KB number (bold), title, type badge, severity badge
- Severity coloring: HIGH = red accent, MEDIUM = yellow, LOW = gray
- Column headers show count
- Repos with zero KB items across all columns are shown with an empty state message
- Repos that don't have `docs/kanban/` are silently omitted

**Styling (dark theme, minimal):**
- Background: `#1a1a2e` (deep navy)
- Cards: `#16213e` with subtle border
- Text: `#e0e0e0`
- Progress bar: green fill on dark track
- Column headers: slightly lighter background
- Status colors: todo = default, in-progress = blue accent, done = green accent
- Cards use minimal padding, no shadows — flat and clean
- Responsive: columns stack vertically on narrow viewports

### Output Location

Write `.kanban.html` to the worktree root. Determine the worktree root from:
- The `Worktree:` parameter (Ralph loop)
- The current working directory (executing-plans)
- The project root if not in a worktree

**Never commit this file.** It is a transient artifact. Must be added to `.gitignore` in each repo that uses this feature.

### Atomic Write

To prevent the browser from loading a partially-written HTML file during a refresh cycle, the generator must use an atomic write pattern:
1. Write HTML content to `.kanban.html.tmp`
2. Rename `.kanban.html.tmp` to `.kanban.html` (rename is atomic on macOS/Linux filesystems)

This eliminates the race condition between agent writes and browser auto-refresh.

---

## Component 2: Changes to writing-plans

**File:** `skills/writing-plans/SKILL.md`

**Where:** In the "Execution Handoff" section, after saving and committing the plan but before generating the ready-to-paste prompts.

**Add:**

> After committing the plan, generate the initial Kanban HTML dashboard:
> 1. Read `skills/_shared/kanban-html-generator.md` for the template and parsing instructions
> 2. Parse the plan file — all tasks will be in Todo state
> 3. Also parse `docs/kanban/` across all repos listed in `~/.claude/kanban-repos.json` for the Project Kanban tab
> 4. Write `.kanban.html` to the project root (main worktree)
> 5. Tell the user: "Kanban dashboard generated at `.kanban.html` — open in your browser to track progress during execution."

Also add `.kanban.html` to the "ready-to-paste prompt" section so that executing agents know to continue updating it.

---

## Component 3: Changes to executing-plans

**File:** `skills/executing-plans/SKILL.md`

### Change 1: Plan file marking (new convention)

Add to Step 2 (Execute Build Tasks), after "Mark as completed":

> **Plan file status marking:** After completing each task, update the task heading in the plan file:
> - Replace `### Task N:` with `### ✅ Task N:` when the task passes verification
> - Replace `### Task N:` with `### 🔄 Task N:` if the task is blocked, and add `> BLOCKED: [reason]` below
> - When starting a task, replace `### Task N:` with `### 🔄 Task N:` (in-progress)
>
> This matches the Ralph loop convention and keeps the plan file as the single source of truth for all execution modes.

### Change 2: HTML regeneration

Add to Step 2, after the plan file marking instruction:

> **Kanban dashboard update:** After updating any task status in the plan file, regenerate `.kanban.html` by following the instructions in `skills/_shared/kanban-html-generator.md`. Parse the plan file's current state and the `docs/kanban/` directories across all repos in `~/.claude/kanban-repos.json`. Write the result to `.kanban.html` at the worktree root.

---

## Component 4: Changes to EXECUTE-PLAN.md (Ralph Loop)

**File:** `docs/ralph_loops/EXECUTE-PLAN.md`

**Where:** After step 6 (mark the task with ✅ in the plan file), before step 7 (commit).

**Add step 6.5:**

> 6.5. Regenerate `.kanban.html` at the worktree root. Read `skills/_shared/kanban-html-generator.md` and follow the generation instructions using the plan file's current state. Also include the multi-repo Project Kanban tab per `~/.claude/kanban-repos.json`.

---

## Edge Cases

1. **Plan file on main, worktree elsewhere** — Parse the plan at its absolute path (on main). Write `.kanban.html` to the worktree root. Both paths are known to the agent.

2. **No worktree (running on main)** — Write `.kanban.html` to the project root. Same logic, different base path.

3. **No `docs/kanban/` in any repo** — Omit the Project Kanban tab entirely. The Plan Execution tab still works.

4. **`~/.claude/kanban-repos.json` missing** — Auto-create with the current project's root path as the sole entry (see Repo Registry section). If the current project has no `docs/kanban/`, the auto-created config still exists for future repos.

5. **Empty `docs/kanban/` subdirectories** — Show the columns with zero cards. Don't hide empty columns.

6. **Large plans (30+ tasks)** — Minimal cards keep the HTML small. 50 tasks ≈ 10KB of HTML. No concern.

7. **Stale browser tab** — After execution finishes, the HTML shows all tasks Done. The meta-refresh keeps reloading a static file — harmless.

8. **Plan file not found** — Skip HTML generation. Log a warning. Never fail a task over dashboard issues.

9. **`did_not_complete/` items in Project Kanban** — Show in a fourth column styled differently (grayed out or strikethrough) to distinguish from Done items.

10. **Repo path in config no longer exists** — Skip silently. Don't error on missing repos — they may be temporarily unmounted or deleted.

11. **Malformed KB entries** — If a `.md` file in `docs/kanban/` cannot be parsed (missing heading, missing required fields), show the filename as a card with an "unparseable" indicator rather than silently dropping it.

12. **Malformed `kanban-repos.json`** — If the file exists but cannot be parsed as valid JSON, treat as missing (omit Project Kanban tab). Log a warning to the user.

13. **Zero tasks in plan file** — If the plan file contains no headings matching `### Task N:` patterns, show a warning message on the Plan Execution tab ("No tasks found — check plan heading format") instead of an empty board.

---

## Standalone Regeneration

The Project Kanban tab only updates during plan execution. To regenerate the dashboard outside of a plan execution context (e.g., after filing KB items directly), any agent can run:

> Read `skills/_shared/kanban-html-generator.md` and generate `.kanban.html` at the project root. No plan file needed — generate with only the Project Kanban tab (omit the Plan Execution tab or show it empty).

This is a one-off instruction, not integrated into any skill. The user can paste it into any Claude Code session.

---

## Verification Strategy

Since this feature is instruction-driven (markdown files directing LLM agents), traditional unit tests don't apply. Verification happens during implementation:

1. **After implementing the generator:** Run it manually with a sample plan file. Open the resulting `.kanban.html` in a browser. Verify: both tabs render, columns are correct, cards show task number + title, progress bar is accurate, auto-refresh works (modify the plan file, wait 5s, check the browser updates).

2. **After implementing executing-plans changes:** Run a 3-task plan through executing-plans. Verify: plan file gets ✅ markers, `.kanban.html` updates after each task, cards move from Todo → In Progress → Done.

3. **After implementing Ralph loop changes:** Run a 3-task plan through the Ralph loop. Same verification as #2.

4. **Edge case spot-checks during implementation:** Verify at least: malformed KB entry (should show "unparseable" card), missing `kanban-repos.json` (should auto-create), zero-task plan (should show warning message).

---

## Files Changed

| File | Change |
|------|--------|
| `skills/_shared/kanban-html-generator.md` | **New** — shared parsing rules + HTML template + cross-reference list of consumers |
| `~/.claude/kanban-repos.json` | **New** — list of repo paths for multi-repo Kanban tab |
| `skills/writing-plans/SKILL.md` | Add initial HTML generation in Execution Handoff section |
| `skills/executing-plans/SKILL.md` | Add plan-file marking convention + HTML regeneration to Step 2 |
| `docs/ralph_loops/EXECUTE-PLAN.md` | Add HTML regeneration step 6.5 |
| `.gitignore` (each repo) | Add `.kanban.html` and `.kanban.html.tmp` |

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Data delivery | Self-contained HTML | Background watcher, local dev server |
| 2 | Card detail level | Minimal (number + title) | Medium (+ files + steps), Rich (+ timing + blockers) |
| 3 | State tracking | Unified plan-file emoji markers | Separate tracking per mode |
| 4 | Tab for project Kanban | Include as second tab | Separate HTML file, exclude entirely |
| 5 | Shared instructions location | `skills/_shared/kanban-html-generator.md` | Inline in each skill, standalone script |
| 6 | Multi-repo Kanban scope | All repos via `kanban-repos.json` | Current repo only, hardcoded list |

### Appendix: Decision Details

#### Decision 1: Data delivery — Self-contained HTML
**Chose:** Self-contained HTML file regenerated by execution agents
**Why:** Zero infrastructure. No server to start, no watcher to manage, no ports to allocate. The agent already has the data (it just marked the task in the plan file), so regenerating a small HTML file adds ~2 seconds per task with no operational overhead. Browsers can't fetch local files from `file://` pages, so the HTML must embed its own data. The `<meta http-equiv="refresh" content="5">` tag gives auto-refresh without JavaScript.
**Alternatives rejected:**
- Background watcher script: Requires starting a separate process before execution, managing its lifecycle, and maintaining a parser that understands plan format. More moving parts for no real benefit.
- Local dev server: Most infrastructure — port management, process lifecycle, graceful shutdown. Overkill for reading a markdown file and rendering cards.

#### Decision 2: Card detail level — Minimal (with blocker exception)
**Chose:** Task number + title + status only, with one exception: 🔄 cards show their blocker note if present (since a blocked task with no explanation is useless as a dashboard signal)
**Why:** The primary use case is "glance at the board to see overall progress." Task numbers and titles provide enough context to identify what's happening. Adding file lists, step counts, or timing data increases parsing complexity and clutters the visual. The plan file itself has all the detail if the user needs it. Blocker notes are the one exception because they answer the critical question "why is this stuck?" without requiring the user to open the plan file.
**Alternatives rejected:**
- Medium (file list + step progress): Step progress would require sub-task tracking that neither execution mode currently does. File lists add visual noise without actionable information.
- Rich (timing + all metadata): Timing requires recording start/end timestamps, which means additional state management. Beyond blockers, other metadata is not actionable from the dashboard view.

#### Decision 3: State tracking — Unified plan-file markers
**Chose:** Both modes mark tasks with ✅/🔄 in the plan markdown file
**Why:** The Ralph loop already does this. Adding the same convention to executing-plans is a small change (a few lines of instruction). Having one source of truth means the HTML generator has one parsing path. It also means if a Ralph loop takes over from an interactive session (or vice versa), the state transfers seamlessly.
**Alternatives rejected:**
- Separate tracking per mode: Each mode would need its own HTML generation logic. State wouldn't transfer between modes. More complex for no benefit.

#### Decision 4: Project Kanban tab
**Chose:** Include as a second tab in the same HTML file
**Why:** The `docs/kanban/` board is a persistent project artifact that accumulates KB entries across sessions. Surfacing it alongside the execution board gives the user a unified view. The parsing is simple (read files from four directories, extract structured fields). The tab only appears when `docs/kanban/` exists, so it doesn't add noise for projects that don't use it.
**Alternatives rejected:**
- Separate HTML file: Requires managing two files and opening two browser tabs. Less convenient.
- Exclude entirely: Misses the opportunity to visualize an existing data structure.

#### Decision 5: Shared instructions in `skills/_shared/`

**Chose:** A single reference doc at `skills/_shared/kanban-html-generator.md`
**Why:** Three different integration points (writing-plans, executing-plans, Ralph loop) all need to generate the same HTML. A shared doc ensures consistency. If the HTML template changes, it changes in one place. The `_shared/` directory was recently created for cross-skill resources (currently contains `kanban-entry-format.md`) — this will be its second tenant.
**Alternatives rejected:**
- Inline in each skill: Triplicates the HTML template. Any visual change requires editing three files. Drift is inevitable.
- Standalone script: Would need a runtime (Node/Python), making the feature dependent on project toolchain. The goal was zero infrastructure.

#### Decision 6: Multi-repo Kanban scope
**Chose:** All repos via `~/.claude/kanban-repos.json` config file
**Why:** The user works across 4 repos (`va-web-app`, `epch-projects`, `aligned_cc_skills`, `ewp-site`) and wants a unified view of all Kanban boards. A config file at `~/.claude/kanban-repos.json` is the simplest approach — it's a flat JSON array of paths, easy to edit, and lives in the user's Claude config directory alongside other personal settings. The generator reads it and scans each repo for `docs/kanban/`. Three of four repos already have Kanban boards.
**Alternatives rejected:**
- Current repo only: Would miss the cross-repo visibility the user wants. They'd need to open separate dashboards per repo.
- Hardcoded list in the generator instructions: Couples the generator to specific repo paths. Adding or removing a repo means editing a skill file instead of a config file.
