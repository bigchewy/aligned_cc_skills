# Kanban HTML Generator

> **Cross-references:** This file is referenced by: `skills/writing-plans/SKILL.md`, `skills/executing-plans/SKILL.md`, `docs/ralph_loops/EXECUTE-PLAN.md`. Update all three if changing trigger behavior or regeneration conventions.

## When to Generate

Generate `.kanban.html` whenever a task status changes in the plan file, or when explicitly asked to regenerate the dashboard. The three integration points are:

1. **writing-plans** — after committing the plan (all tasks in Todo state)
2. **executing-plans** — after updating any task status in the plan file
3. **Ralph loop** — after marking a task with ✅ or 🔄 in the plan file

## Plan Parsing Rules

1. Read the plan file at its absolute path
2. Extract the plan title from the first `# ` heading
3. Scan for task headings matching these patterns:
   - `### Task N: [Title]` — status: **todo**
   - `### 🔄 Task N: [Title]` — status: **in-progress**
   - `### ✅ Task N: [Title]` — status: **done**
4. If a 🔄 task has a `> BLOCKED: [reason]` line immediately below the heading, capture the reason
5. Count tasks per status for the progress bar
6. If the plan file contains no headings matching `### Task N:` patterns (with or without emoji), show a warning message on the Plan Execution tab: "No tasks found — check plan heading format"

## Repo Registry

**File:** `~/.claude/kanban-repos.json`

A JSON array of absolute paths to repos with Kanban boards:

```json
[
  "/Users/ericpage/software/va-web-app",
  "/Users/ericpage/software/epch-projects",
  "/Users/ericpage/software/aligned_cc_skills",
  "/Users/ericpage/software/ewp-site"
]
```

**Auto-create on first use:** If `~/.claude/kanban-repos.json` does not exist when the generator runs, create it with the current project's root path as the sole entry. This ensures the Project Kanban tab works out of the box.

**Malformed JSON:** If the file exists but cannot be parsed as valid JSON, treat as missing (omit Project Kanban tab). Warn the user: "kanban-repos.json is malformed — Project Kanban tab omitted."

**Missing repo path:** If a path in the array no longer exists on disk, skip it silently.

## Project Kanban Parsing Rules

1. Read `~/.claude/kanban-repos.json` to get the list of repo paths
2. For each repo path, check if `{repo}/docs/kanban/` exists
3. For repos that have it, scan four subdirectories: `todo/`, `in-progress/`, `done/`, `did_not_complete/`
4. For each `.md` file in those directories, extract:
   - KB number and title from the `# KB-NNN: [Title]` heading
   - Type from `**Type:**` field
   - Severity from `**Severity:**` field
   - Created date from `**Created:**` field
5. If a `.md` file cannot be parsed (missing heading or required fields), show the filename as a card with an "unparseable" indicator rather than dropping it
6. Group items by repo, then by directory (column)
7. Derive a short repo label from the directory name (e.g., `va-web-app`, `epch-projects`)

## HTML Template

Generate a single self-contained `.kanban.html` file with ALL content inline (no external dependencies).

### Head

```html
<meta http-equiv="refresh" content="5">
<meta charset="utf-8">
<title>Kanban — [Plan Name]</title>
```

All CSS goes in a `<style>` block in the head.

### Tab Switching

Two tabs: "Plan Execution" and "Project Kanban". Use the CSS radio button hack for tab switching without JavaScript:

```html
<input type="radio" name="tab" id="tab-plan" checked>
<label for="tab-plan">Plan Execution</label>
<input type="radio" name="tab" id="tab-kanban">
<label for="tab-kanban">Project Kanban</label>

<div class="tab-content" id="content-plan">...</div>
<div class="tab-content" id="content-kanban">...</div>
```

With CSS:

```css
.tab-content { display: none; }
#tab-plan:checked ~ #content-plan { display: block; }
#tab-kanban:checked ~ #content-kanban { display: block; }
```

If no repos have `docs/kanban/` directories (or `kanban-repos.json` doesn't exist / is empty), omit the Project Kanban tab and radio buttons entirely — show only the Plan Execution content.

### Tab 1 — Plan Execution

- **Header:** plan title, progress bar (done/total), task counts per status
- **Progress bar:** green fill (`#4caf50`) on dark track (`#2a2a4a`)
- **Three columns:** Todo, In Progress, Done
- **Column headers** show count: `TODO (5)`, `IN PROGRESS (1)`, `DONE (6)`
- **Cards:** task number (bold) + title
- 🔄 cards show the blocker note below the title if present (in smaller, dimmer text)

### Tab 2 — Project Kanban (multi-repo)

- One section per repo that has a `docs/kanban/` directory
- **Section header:** repo name (e.g., "va-web-app", "epch-projects")
- **Four columns per repo:** Todo, In Progress, Done, Did Not Complete
- **Cards:** KB number (bold), title, type badge, severity badge
- **Severity coloring:** HIGH = `#ff4444` red accent, MEDIUM = `#ffaa00` yellow, LOW = `#888` gray
- **Column headers** show count
- Repos with zero KB items show an empty state message: "No items"
- `did_not_complete/` column uses grayed-out card styling (opacity 0.6)

### Styling (dark theme, minimal)

```css
body { background: #1a1a2e; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
.board { display: flex; gap: 16px; }
.column { flex: 1; min-width: 200px; }
.column-header { background: #222244; padding: 10px 14px; border-radius: 8px 8px 0 0; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
.card { background: #16213e; border: 1px solid #2a2a5a; border-radius: 6px; padding: 10px 12px; margin: 6px 0; font-size: 14px; }
.card .task-num { font-weight: 700; }
.card .blocker { font-size: 12px; color: #ff9800; margin-top: 4px; }
.progress-bar { background: #2a2a4a; border-radius: 4px; height: 8px; margin: 12px 0; }
.progress-fill { background: #4caf50; height: 100%; border-radius: 4px; }
.badge { display: inline-block; font-size: 11px; padding: 1px 6px; border-radius: 3px; margin-left: 4px; }
.badge-high { background: #ff4444; color: white; }
.badge-medium { background: #ffaa00; color: black; }
.badge-low { background: #444; color: #aaa; }
.in-progress .column-header { border-bottom: 2px solid #2196f3; }
.done .column-header { border-bottom: 2px solid #4caf50; }
.did-not-complete .card { opacity: 0.6; }
```

Responsive: on narrow viewports (`max-width: 768px`), columns stack vertically:

```css
@media (max-width: 768px) { .board { flex-direction: column; } }
```

### Standalone Mode (no plan file)

When generating outside a plan execution context (e.g., after filing KB items directly), omit the Plan Execution tab entirely. Show only the Project Kanban tab without radio buttons or tab switching.

## Output Location

Write `.kanban.html` to the worktree root (or project root if not in a worktree). Determine the root from:
- The `Worktree:` parameter (Ralph loop)
- The current working directory (executing-plans)
- The project root if not in a worktree

**Never commit this file.** It must be in `.gitignore`.

## Atomic Write

To prevent the browser from loading a partially-written file during a refresh cycle:
1. Write HTML content to `.kanban.html.tmp`
2. Rename `.kanban.html.tmp` to `.kanban.html`

Use the Write tool for the `.tmp` file, then `mv` via Bash for the atomic rename:

```bash
mv .kanban.html.tmp .kanban.html
```

## Error Handling

- **Plan file not found:** Skip HTML generation. Warn the user. Never fail a task over dashboard issues.
- **Empty plan (zero tasks):** Show the Plan Execution tab with warning message instead of empty board.
- **Missing `kanban-repos.json`:** Auto-create with current project root. If current project has no `docs/kanban/`, the file still exists for future repos.
- **Malformed `kanban-repos.json`:** Treat as missing, warn user.
- **Repo path doesn't exist:** Skip silently.
- **Malformed KB entries:** Show filename as card with "unparseable" indicator.
