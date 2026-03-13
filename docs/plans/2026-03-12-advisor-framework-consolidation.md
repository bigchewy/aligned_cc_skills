# Advisor & Framework Consolidation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Make this plugin the single source of truth for all advisors and frameworks by flattening repo-based subdirectories, removing `~/.claude/` symlinks, and merging `directory.md` into `registry.md`.

**Source Design Doc:** `docs/plans/2026-03-12-advisor-framework-consolidation-design.md`

**Architecture:** This is a file migration — no application code changes. All work is markdown skill files, markdown metadata files, and file moves via git. Discovery logic in `use-advisor` and `use-framework` skills switches from manifest-based multi-repo globs to single flat-directory globs. The `~/.claude/` discovery path is eliminated entirely.

**Tech Stack:** Git, Bash (file moves), Markdown

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] **Close all other Claude sessions** using this plugin. Concurrent sessions will see broken discovery paths during the transition.
- [ ] **Create safety tags** for rollback:
  ```bash
  git -C /Users/ericpage/software/aligned_cc_skills tag pre-consolidation
  git -C /Users/ericpage/.claude tag pre-consolidation
  ```
- [ ] **Pause `~/.claude/` autocommit:**
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.ericpage.claude-skills-autocommit.plist
  ```
- [ ] **Create a feature branch** for the migration (design doc requires atomic merge to main):
  ```bash
  git -C /Users/ericpage/software/aligned_cc_skills checkout -b consolidation/advisor-framework-flatten
  ```
- [ ] **Run the divergence audit** and record decisions. Launch a Claude session in this repo and run:
  > Compare every advisor file in `advisors/epch/` against `/Users/ericpage/software/epch-projects/src/lib/advisors/prompts/`, every advisor in `advisors/va-web-app/` against `/Users/ericpage/software/va-web-app/src/lib/advisors/prompts/`, and every framework directory in `frameworks/va-web-app/` and `frameworks/epch-projects/` against their source repos. Write a divergence report to `docs/plans/advisor-divergence-report.md` with status per file: IDENTICAL, DIVERGED (with diff summary), or MISSING_FROM_PLUGIN. Verify file counts: 14 EPCH advisors, 42 va-web-app advisors, 4 EPCH frameworks, 126 va-web-app frameworks.
- [ ] **Review the divergence report** at `docs/plans/advisor-divergence-report.md`. For each DIVERGED entry, annotate with your decision: `KEEP_PLUGIN`, `TAKE_SOURCE`, or `MERGE` (with merge notes). For MISSING_FROM_PLUGIN entries, annotate `COPY` or `SKIP`.

### Rollback

If migration is interrupted or verification fails:
- **Plugin repo:** `git checkout main` (discard the `consolidation/advisor-framework-flatten` branch). Or `git reset --hard pre-consolidation` if changes landed on main.
- **`~/.claude/` repo:** `git -C ~/.claude reset --hard pre-consolidation` to restore symlinks and manifests.
- Re-enable autocommit: `launchctl load ~/Library/LaunchAgents/com.ericpage.claude-skills-autocommit.plist`

---

### ✅ Task 1: Copy Missing Frameworks from EPCH Source

**Files:**
- Create: `frameworks/epch-projects/design-principles/prompt.md`
- Create: `frameworks/epch-projects/design-principles/examples.md`
- Create: `frameworks/epch-projects/design-principles/anti-examples.md`
- Create: `frameworks/epch-projects/landing-page-assembly/prompt.md`

**Step 1: Verify source files exist**

Run Glob for:
- `/Users/ericpage/software/epch-projects/src/lib/frameworks/prompts/design-principles/prompt.md`
- `/Users/ericpage/software/epch-projects/src/lib/frameworks/prompts/design-principles/examples.md`
- `/Users/ericpage/software/epch-projects/src/lib/frameworks/prompts/design-principles/anti-examples.md`
- `/Users/ericpage/software/epch-projects/src/lib/frameworks/prompts/landing-page-assembly/prompt.md`

All four must exist.

**Step 2: Verify targets don't already exist**

Run Glob for `frameworks/epch-projects/design-principles/` and `frameworks/epch-projects/landing-page-assembly/`. Must return no results.

**Step 3: Copy files**

```bash
mkdir -p frameworks/epch-projects/design-principles frameworks/epch-projects/landing-page-assembly
cp /Users/ericpage/software/epch-projects/src/lib/frameworks/prompts/design-principles/prompt.md frameworks/epch-projects/design-principles/
cp /Users/ericpage/software/epch-projects/src/lib/frameworks/prompts/design-principles/examples.md frameworks/epch-projects/design-principles/
cp /Users/ericpage/software/epch-projects/src/lib/frameworks/prompts/design-principles/anti-examples.md frameworks/epch-projects/design-principles/
cp /Users/ericpage/software/epch-projects/src/lib/frameworks/prompts/landing-page-assembly/prompt.md frameworks/epch-projects/landing-page-assembly/
```

**Step 4: Verify copies**

Read first line of each new file. Confirm content matches source.

**Step 5: Commit**

```bash
git add frameworks/epch-projects/design-principles/ frameworks/epch-projects/landing-page-assembly/
git commit -m "feat: add 2 missing EPCH frameworks (design-principles, landing-page-assembly)"
```

---

### ⏭️ Task 2: Apply Divergence Decisions

> SKIPPED: The prerequisite divergence report (`docs/plans/advisor-divergence-report.md`) was never created. Source repos (`epch-projects`, `va-web-app`) are outside the allowed working directories so the comparison cannot be performed from this session. Plugin copies are treated as authoritative. User can revisit post-consolidation if needed.

**Files:**
- Modify: various files in `advisors/` and `frameworks/` per divergence report

**Step 1: Read the divergence report**

Read `docs/plans/advisor-divergence-report.md`. For each entry annotated with a decision:

- `KEEP_PLUGIN` → no action needed
- `TAKE_SOURCE` → read the source file, overwrite the plugin copy
- `MERGE` → apply the merge notes from the annotation
- `COPY` → copy the source file into the plugin

**Step 2: Apply each decision**

For each file that needs updating, read the source, write to the plugin path.

**Step 3: Verify changes**

For each modified file, read the first line to confirm the update took effect.

**Step 4: Commit**

```bash
git add -u advisors/ frameworks/
git commit -m "fix: apply divergence decisions from audit report"
```

---

### ✅ Task 3: Delete Duplicate EPCH Advisors

**Files:**
- Delete: `advisors/epch/april-dunford.md`
- Delete: `advisors/epch/richard-rumelt.md`
- Delete: `advisors/epch/shirin-oreizy.md`

**Step 1: Verify duplicates exist in both locations**

Glob for each filename in both `advisors/epch/` and `advisors/va-web-app/`. All six files must exist.

**Step 2: Delete the EPCH copies**

```bash
git rm advisors/epch/april-dunford.md advisors/epch/richard-rumelt.md advisors/epch/shirin-oreizy.md
```

**Step 3: Verify only va-web-app copies remain**

Glob `advisors/va-web-app/april-dunford.md` — must exist.
Glob `advisors/epch/april-dunford.md` — must NOT exist.

**Step 4: Commit**

```bash
git commit -m "chore: remove 3 duplicate EPCH advisors (va-web-app versions are canonical)"
```

---

### Task 4: Update `use-advisor/SKILL.md` Discovery Logic

> **Behavior change:** The no-argument listing changes from repo-grouped headers (va-web-app, epch, .claude) to a single flat alphabetical list. This is intentional — the repo distinction no longer exists.

**Files:**
- Modify: `skills/use-advisor/SKILL.md` (Step 1 discovery logic, lines 15-41)

**Step 1: Read current file**

Read `skills/use-advisor/SKILL.md` in full.

**Step 2: Replace the three-stage discovery with single flat glob**

Replace the entire Step 1 section (from `## Step 1: Discover Available Advisors` through the end of Step 1c, just before `## Step 2: Extract Advisor Names`) with:

```markdown
## Step 1: Discover Available Advisors

Discover all advisors from the plugin's flat directory.

**Step 1a: Read the Quick Reference table (`advisors/registry.md`)**

Read the file `advisors/registry.md` (plugin-relative). Parse the Quick Reference table — rows give slug, name, domains, and summary. Use this as the primary listing source.

If `advisors/registry.md` does not exist, fall back to Step 1b.

**Step 1b: Plugin glob fallback (`advisors/prompts/`)**

Glob `advisors/prompts/*.md`. Each file is one advisor (slug = filename minus `.md`). Read the first line of each file to extract the display name and summary.
```

**Step 3: Update Step 2 to remove repo-based grouping**

In the Step 2 section, remove the repo-based grouping instructions. Replace the paragraph about noting "which repo it belongs to" (lines 49-53) with:

```markdown
List advisors alphabetically by display name. Do not group by repo — all advisors live in a single flat directory.
```

**Step 4: Remove the `~/.claude/` user files reference**

Find and remove the line referencing `~/.claude/` user files (line 50: `- User files in ~/.claude/advisors/prompts/{repo-name}/*.md → group: the repo name`).

**Step 5: Verify no old paths remain**

Grep `skills/use-advisor/SKILL.md` for `~/.claude/`, `.repos`, `directory.md`, `{repo-name}`. Must return 0 matches (except the new `registry.md` reference).

**Step 6: Commit**

```bash
git add skills/use-advisor/SKILL.md
git commit -m "refactor: simplify use-advisor discovery to single flat glob"
```

---

### Task 5: Update `use-framework/SKILL.md` Discovery Logic

> **Behavior change:** The no-argument listing changes from repo-grouped headers to a single flat alphabetical list. This is intentional — the repo distinction no longer exists.

**Files:**
- Modify: `skills/use-framework/SKILL.md` (Step 1 discovery logic, lines 15-49)

**Step 1: Read current file**

Read `skills/use-framework/SKILL.md` in full.

**Step 2: Replace the two-stage discovery with single flat glob**

Replace the entire Step 1 section (from `## Step 1: Discover Available Frameworks` through the end of Step 1c, just before `## Step 2: Extract Framework Names`) with:

```markdown
## Step 1: Discover Available Frameworks

Discover all frameworks from the plugin's flat directory.

**Step 1a: Glob plugin frameworks**

Glob `frameworks/*/prompt.md`. Each `prompt.md` represents one framework. The slug is the parent directory name (e.g., for `frameworks/clearing-model/prompt.md`, the slug is `clearing-model`).

If no results, report: "No framework files found. Check your plugin installation."

**Context management:** When listing all frameworks, glob first to get folder names, then read only the first line of each `prompt.md`. Do not read full file contents during discovery — full reads happen only after matching.
```

**Step 3: Update inline example path**

Find `frameworks/va-web-app/clearing-model/prompt.md` and replace with `frameworks/clearing-model/prompt.md`.

**Step 4: Remove `~/.claude/` fallback instructions**

Remove the paragraph about adding custom frameworks to `~/.claude/frameworks/prompts/` (the "This allows users to add their own frameworks..." paragraph near old Step 1c).

**Step 5: Verify no old paths remain**

Grep `skills/use-framework/SKILL.md` for `~/.claude/`, `.repos`, `{repo-name}`. Must return 0 matches.

**Step 6: Commit**

```bash
git add skills/use-framework/SKILL.md
git commit -m "refactor: simplify use-framework discovery to single flat glob"
```

---

### Task 6: Update `add-advisor/SKILL.md` — Remove Symlink Option, Update Paths

**Files:**
- Modify: `skills/add-advisor/SKILL.md` (Step 8 symlink option, line 102 canonical example, Step 8b directory reference)

**Step 1: Read current file**

Read `skills/add-advisor/SKILL.md` in full.

**Step 2: Update canonical example path (line 102)**

Replace:
```
Reference `advisors/va-web-app/diana-chapman.md` as the canonical example
```
With:
```
Reference `advisors/prompts/diana-chapman.md` as the canonical example
```

**Step 3: Simplify Step 8 — Remove Option B**

Replace the entire Step 8 section (from `### 8. Register Advisor for Discovery` through the verify step at line 209) with:

```markdown
### 8. Register Advisor for Discovery

Add the advisor prompt file to `advisors/prompts/` in the plugin directory. This makes the advisor available in all plugin-enabled sessions.

Place the file at `advisors/prompts/{advisor-id}.md`.
```

**Step 4: Update Step 8b — directory.md → registry.md**

Replace the Step 8b section with:

```markdown
### 8b. Update the Registry

Append one row to the Quick Reference table in `advisors/registry.md`:

```
| {slug} | {display-name} | {domains} | {summary} |
```

Where:
- **slug:** The advisor's kebab-case filename (without `.md`)
- **display-name:** The advisor's full name
- **domains:** Comma-separated expertise areas
- **summary:** One-line description
```

**Step 5: Verify no old paths remain**

Grep `skills/add-advisor/SKILL.md` for `~/.claude/`, `directory.md`, `advisors/va-web-app/`, `{repo-name}`. Must return 0 matches.

**Step 6: Commit**

```bash
git add skills/add-advisor/SKILL.md
git commit -m "refactor: simplify add-advisor to flat directory, remove symlink option"
```

---

### Task 7: Update `add-framework/SKILL.md` — Remove Symlink Option, Update Paths, Fix Step 0

**Files:**
- Modify: `skills/add-framework/SKILL.md` (Step 0 path detection, Step 7 symlink option, lines 64, 106, 117 canonical examples)

**Step 1: Read current file**

Read `skills/add-framework/SKILL.md` in full.

**Step 2: Fix Step 0 environment detection path**

In Step 0 (the `### 0. Environment Detection` section), the framework path detection checks for `frameworks/prompts/` at repo root (line 26). Post-migration, frameworks live directly in `frameworks/` with no `prompts/` subdirectory. Update:

Replace:
```
2. If `frameworks/prompts/` exists at repo root → use it
```
With:
```
2. If `frameworks/` exists at repo root and contains subdirectories with `prompt.md` files → use it
```

Also update the default path (line 28):
Replace:
```
4. Else → default to `frameworks/prompts/` at repo root (will create on first use)
```
With:
```
4. Else → default to `frameworks/` at repo root (will create on first use)
```

**Step 3: Update canonical example paths**

Replace all occurrences of `frameworks/va-web-app/clearing-model/` with `frameworks/clearing-model/`:
- Line 64: `frameworks/va-web-app/clearing-model/prompt.md` → `frameworks/clearing-model/prompt.md`
- Line 64: `frameworks/va-web-app/braving-trust-inventory/prompt.md` → `frameworks/braving-trust-inventory/prompt.md`
- Line 106: `frameworks/va-web-app/clearing-model/examples.md` → `frameworks/clearing-model/examples.md`
- Line 117: `frameworks/va-web-app/clearing-model/anti-examples.md` → `frameworks/clearing-model/anti-examples.md`

**Step 4: Simplify Step 7 — Remove Option B**

Replace the entire Step 7 section (from `### 7. Register Framework for Discovery` through the verify step at line 193) with:

```markdown
### 7. Register Framework for Discovery

Add the framework folder to `frameworks/` in the plugin directory. This makes the framework available in all plugin-enabled sessions.

Place the framework at `frameworks/{framework-slug}/` containing `prompt.md` (required), `examples.md` (optional), and `anti-examples.md` (optional).
```

**Step 5: Verify no old paths remain**

Grep `skills/add-framework/SKILL.md` for `~/.claude/`, `.repos`, `frameworks/va-web-app/`, `frameworks/prompts/`, `{repo-name}`. Must return 0 matches.

**Step 6: Commit**

```bash
git add skills/add-framework/SKILL.md
git commit -m "refactor: simplify add-framework to flat directory, remove symlink option, fix Step 0 path"
```

---

### Task 8: Update `brainstorming/SKILL.md` Advisor Path References

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (lines 59, 88, 114)

**Step 1: Read current file**

Read `skills/brainstorming/SKILL.md` in full.

**Step 2: Update steve-krug reference (line 59)**

Replace:
```
advisors/.claude/steve-krug.md
```
With:
```
advisors/prompts/steve-krug.md
```

**Step 3: Update the-architect references (lines 88 and 114)**

Replace all occurrences of `advisors/.claude/the-architect.md` with `advisors/prompts/the-architect.md`. This includes inline dispatch template strings like `"[Full contents of advisors/.claude/the-architect.md]"` — replace those too, not just bare path references.

**Step 4: Verify no old paths remain**

Grep `skills/brainstorming/SKILL.md` for `advisors/.claude/`. Must return 0 matches (this catches both bare references and inline template strings).

**Step 5: Commit**

```bash
git add skills/brainstorming/SKILL.md
git commit -m "fix: update brainstorming advisor paths to flat directory"
```

---

### Task 9: Update `create-design-principles` Advisor Path References

**Files:**
- Modify: `skills/create-design-principles/SKILL.md` (lines 12, 270)
- Modify: `skills/create-design-principles/design-critique-checklist.md` (line 9)

**Step 1: Read both files**

Read `skills/create-design-principles/SKILL.md` and `skills/create-design-principles/design-critique-checklist.md`.

**Step 2: Update SKILL.md references**

Replace all occurrences of `advisors/va-web-app/steve-jobs.md` with `advisors/prompts/steve-jobs.md` in `skills/create-design-principles/SKILL.md`.

**Step 3: Update checklist reference**

Replace `advisors/va-web-app/steve-jobs.md` with `advisors/prompts/steve-jobs.md` in `skills/create-design-principles/design-critique-checklist.md`.

**Step 4: Verify no old paths remain**

Grep both files for `advisors/va-web-app/`. Must return 0 matches.

**Step 5: Commit**

```bash
git add skills/create-design-principles/SKILL.md skills/create-design-principles/design-critique-checklist.md
git commit -m "fix: update create-design-principles advisor paths to flat directory"
```

---

### Task 10: Update `README.md`

**Files:**
- Modify: `README.md` (framework count, any old path references)

**Step 1: Read current file**

Read `README.md` in full.

**Step 2: Update framework count**

Find `130 frameworks` and replace with `132 frameworks`.

**Step 3: Remove `~/.claude/` custom advisor instructions**

Find and remove any instructions about `~/.claude/advisors/prompts/{repo-name}/` for custom advisors. If such instructions exist, replace with a note that all advisors live in `advisors/prompts/` in the plugin directory.

**Step 4: Update any remaining old path references**

Grep `README.md` for `advisors/va-web-app/`, `advisors/epch/`, `advisors/.claude/`, `frameworks/va-web-app/`, `frameworks/epch-projects/`. Replace any matches with the new flat paths (`advisors/prompts/`, `frameworks/`).

**Step 5: Verify no old paths remain**

Grep `README.md` for old path patterns. Must return 0 matches.

**Step 6: Commit**

```bash
git add README.md
git commit -m "docs: update README for flat advisor/framework directories"
```

---

### Task 11: Pre-Move Collision Check

Complete Task 3 before starting — Step 3 depends on the Task 3 deletion commit.

**Files:**
- No file changes — verification only

**Step 1: Check advisor filename collisions**

List all `.md` filenames across `advisors/va-web-app/`, `advisors/epch/`, and `advisors/.claude/`. Check for any filename that appears in more than one source directory.

Known collisions (already handled by Task 3 deletion): `april-dunford.md`, `richard-rumelt.md`, `shirin-oreizy.md`. These must already be deleted. Verify they're gone from `advisors/epch/`.

If any NEW collisions are found (beyond the 3 already deleted), STOP and report.

**Step 2: Check framework directory name collisions**

List all framework directory names across `frameworks/va-web-app/` and `frameworks/epch-projects/`. Check for any name that appears in both. If any collisions are found, STOP and report.

**Step 3: Verify Task 3 deletions are committed**

Run: `git log --oneline -1 -- advisors/epch/april-dunford.md`
Expected: shows the deletion commit from Task 3.

---

### Task 12: Flatten Advisors Directory

Complete Task 11 first — this task depends on the collision check passing.

**Files:**
- Create: `advisors/prompts/` (directory)
- Move: all `.md` files from `advisors/va-web-app/`, `advisors/epch/`, `advisors/.claude/` → `advisors/prompts/`
- Delete: `advisors/va-web-app/` (empty after move)
- Delete: `advisors/epch/` (empty after move)
- Delete: `advisors/.claude/` (empty after move)
- Delete: `advisors/.repos`

**Step 1: Create target directory**

```bash
mkdir -p advisors/prompts
```

**Step 2: Move all advisor files**

```bash
git mv advisors/va-web-app/*.md advisors/prompts/
git mv advisors/epch/*.md advisors/prompts/
git mv advisors/.claude/*.md advisors/prompts/
```

**Step 3: Remove empty directories and manifest**

```bash
rmdir advisors/va-web-app advisors/epch advisors/.claude
git rm advisors/.repos
```

**Step 4: Verify file count**

Glob `advisors/prompts/*.md`. Expected: 60 files (63 original minus 3 duplicates deleted in Task 3).

**Step 5: Verify no files left behind**

Glob `advisors/va-web-app/*.md`, `advisors/epch/*.md`, `advisors/.claude/*.md`. All must return no results.

**Step 6: Commit**

```bash
git add advisors/prompts/
git commit -m "refactor: flatten advisors into single advisors/prompts/ directory"
```

---

### Task 13: Flatten Frameworks Directory

**Files:**
- Move: all framework directories from `frameworks/va-web-app/` and `frameworks/epch-projects/` up one level into `frameworks/`
- Delete: `frameworks/va-web-app/` (empty after move)
- Delete: `frameworks/epch-projects/` (empty after move)
- Delete: `frameworks/.repos`

**Step 1: Move all va-web-app frameworks**

List all directories in `frameworks/va-web-app/` and move each one:

```bash
for dir in frameworks/va-web-app/*/; do
  git mv "$dir" "frameworks/$(basename "$dir")"
done
```

**Step 2: Move all epch-projects frameworks**

```bash
for dir in frameworks/epch-projects/*/; do
  git mv "$dir" "frameworks/$(basename "$dir")"
done
```

**Step 3: Remove empty directories and manifest**

```bash
rmdir frameworks/va-web-app frameworks/epch-projects
git rm frameworks/.repos
```

**Step 4: Verify framework count**

Glob `frameworks/*/prompt.md`. Expected: 132 files (130 original + 2 added in Task 1).

**Step 5: Verify no files left behind**

Glob `frameworks/va-web-app/*` and `frameworks/epch-projects/*`. Both must return no results.

**Step 6: Commit**

```bash
git commit -m "refactor: flatten frameworks into single-level directories"
```

---

### Task 14: Stale Path Verification Gate

**Files:**
- No file changes — verification only

**Step 1: Grep all markdown files for old paths**

Grep all `**/*.md` files (excluding `docs/plans/completed/` and `node_modules/`) for these patterns:
- `advisors/va-web-app/`
- `advisors/epch/`
- `advisors/.claude/`
- `frameworks/va-web-app/`
- `frameworks/epch-projects/`

Must return 0 results across all patterns.

**Step 2: If any stale paths found, fix them**

For each file with a stale path:
- Read the file
- Replace the old path with the correct new path
- `advisors/{repo}/` → `advisors/prompts/`
- `frameworks/{repo}/` → `frameworks/`

**Step 3: If fixes were needed, commit**

```bash
git add -u
git commit -m "fix: update remaining stale advisor/framework path references"
```

---

### Task 15: Rewrite `advisors/registry.md` — Merge directory.md, Add Quick Reference

**Files:**
- Modify: `advisors/registry.md` (add Quick Reference table, update all `prompt:` paths)

This is the most complex task. Complete Task 12 (flatten advisors) first — this task depends on it.

> **Note:** Between Tasks 12-14 and this task, `registry.md` still references old `advisors/{repo}/` paths in its `prompt:` fields. The closed-sessions prerequisite mitigates this — no skill will read the stale paths during migration.

**Step 1: Read both files**

Read `advisors/registry.md` and `advisors/directory.md` in full.

**Step 2: Add Quick Reference table**

Insert a `## Quick Reference` section at the top of `advisors/registry.md` (after the header/intro). Build the table from `directory.md` data, converting to a single alphabetical list:

```markdown
## Quick Reference

| slug | name | domains | summary |
|------|------|---------|---------|
| andreo-spina | Dr. Andreo Spina | sports medicine, mobility | Creator of FRC and founder of Functional Anatomy Seminars |
| andy-raskin | Andy Raskin | strategic narrative | Strategic narrative consultant |
...
```

Include ALL advisors — both profiled and unprofiled. Add Steve Krug (missing from `directory.md` but present as `advisors/prompts/steve-krug.md`). List alphabetically, not grouped by repo.

**Step 3: Update all `prompt:` paths in profiled advisor entries**

Replace all occurrences of `advisors/{repo}/slug.md` with `advisors/prompts/slug.md`. The pattern is:
- `advisors/va-web-app/` → `advisors/prompts/`
- `advisors/epch/` → `advisors/prompts/`
- `advisors/.claude/` → `advisors/prompts/`

**Step 4: Update "Adding advisors" instruction**

Find the instruction about adding advisors (near line 9). Replace `advisors/{repo-name}/` with `advisors/prompts/`.

**Step 5: Update "Not Yet Profiled" section**

Find the "Not Yet Profiled" note (near line 251). Update path reference from `advisors/va-web-app/` to `advisors/prompts/`. Convert the comma-separated list of unprofiled advisors into full table rows in the Quick Reference table.

**Step 6: Remove any remaining repo-based path references**

Grep `advisors/registry.md` for `advisors/va-web-app/`, `advisors/epch/`, `advisors/.claude/`, `{repo-name}`, `{repo}`. Must return 0 matches.

**Step 7: Commit**

```bash
git add advisors/registry.md
git commit -m "refactor: merge directory.md into registry.md, add Quick Reference table"
```

---

### Task 16: Delete `advisors/directory.md` and Update Cross-References

**Files:**
- Delete: `advisors/directory.md`
- Modify: `skills/use-advisor/SKILL.md` (if any remaining `directory.md` reference)
- Modify: `skills/add-advisor/SKILL.md` (if any remaining `directory.md` reference)

Complete Task 15 first — this task depends on it.

**Step 1: Verify registry.md has the Quick Reference table**

Read `advisors/registry.md`. Confirm the `## Quick Reference` section exists and has a table with 60 rows.

**Step 2: Grep for remaining `directory.md` references**

Grep all `**/*.md` for `directory.md`. List all files that reference it.

**Step 3: Update any remaining references**

For each file that still references `directory.md`, replace with `registry.md` (specifically the Quick Reference section).

**Step 4: Delete `directory.md`**

```bash
git rm advisors/directory.md
```

**Step 5: Verify**

Glob `advisors/directory.md` — must NOT exist.
Grep all `**/*.md` for `directory.md` — must return 0 matches (excluding `docs/plans/` which may reference it historically).

**Step 6: Commit**

```bash
git add -u
git commit -m "chore: delete directory.md (merged into registry.md Quick Reference)"
```

---

### Task 17: Clean Up `~/.claude/` Artifacts

**Files:**
- Delete: `~/.claude/advisors/prompts/epch-projects` (symlink)
- Delete: `~/.claude/advisors/prompts/va-web-app` (symlink)
- Delete: `~/.claude/advisors/prompts/.claude/` (directory with 6 files: the-architect, the-designer, the-devex-engineer, the-pm, the-qa-engineer, the-security-reviewer)
- Delete: `~/.claude/advisors/prompts/.repos` (manifest)
- Delete: `~/.claude/advisors/registry.md` (diverged copy)
- Delete: `~/.claude/frameworks/prompts/epch-projects` (symlink)
- Delete: `~/.claude/frameworks/prompts/va-web-app` (symlink)
- Delete: `~/.claude/frameworks/prompts/.repos` (manifest)

**Step 1: Verify artifacts exist and check git tracking**

```bash
ls -la /Users/ericpage/.claude/advisors/prompts/
ls -la /Users/ericpage/.claude/frameworks/prompts/
ls -la /Users/ericpage/.claude/advisors/registry.md
```

Confirm the symlinks, `.claude/` directory (7 files), `.repos` files, and `registry.md` exist.

Then check which files are git-tracked:

```bash
git -C /Users/ericpage/.claude ls-files advisors/ frameworks/
```

For tracked files, use `git rm`. For untracked files, use plain `rm`.

**Step 2: Remove all artifacts**

Use `git rm` for tracked items, plain `rm` for untracked:

```bash
git -C /Users/ericpage/.claude rm advisors/prompts/epch-projects 2>/dev/null || rm /Users/ericpage/.claude/advisors/prompts/epch-projects
git -C /Users/ericpage/.claude rm advisors/prompts/va-web-app 2>/dev/null || rm /Users/ericpage/.claude/advisors/prompts/va-web-app
rm -rf /Users/ericpage/.claude/advisors/prompts/.claude/
git -C /Users/ericpage/.claude rm advisors/prompts/.repos 2>/dev/null || rm /Users/ericpage/.claude/advisors/prompts/.repos
git -C /Users/ericpage/.claude rm advisors/registry.md 2>/dev/null || rm /Users/ericpage/.claude/advisors/registry.md
git -C /Users/ericpage/.claude rm frameworks/prompts/epch-projects 2>/dev/null || rm /Users/ericpage/.claude/frameworks/prompts/epch-projects
git -C /Users/ericpage/.claude rm frameworks/prompts/va-web-app 2>/dev/null || rm /Users/ericpage/.claude/frameworks/prompts/va-web-app
git -C /Users/ericpage/.claude rm frameworks/prompts/.repos 2>/dev/null || rm /Users/ericpage/.claude/frameworks/prompts/.repos
```

For the `.claude/` directory (7 advisor files), check if any are tracked and use `git rm` accordingly:

```bash
git -C /Users/ericpage/.claude ls-files advisors/prompts/.claude/
```

If tracked, use `git -C /Users/ericpage/.claude rm -r advisors/prompts/.claude/` instead of `rm -rf`.

**Step 3: Remove empty parent directories**

```bash
rmdir /Users/ericpage/.claude/advisors/prompts/ 2>/dev/null
rmdir /Users/ericpage/.claude/advisors/ 2>/dev/null
rmdir /Users/ericpage/.claude/frameworks/prompts/ 2>/dev/null
rmdir /Users/ericpage/.claude/frameworks/ 2>/dev/null
```

**Step 4: Verify cleanup**

```bash
ls /Users/ericpage/.claude/advisors/ 2>&1
ls /Users/ericpage/.claude/frameworks/ 2>&1
```

Both should show "No such file or directory."

**Step 5: Check for staged changes before committing**

```bash
git -C /Users/ericpage/.claude status
```

If there are staged deletions or untracked deletions, stage them:

```bash
git -C /Users/ericpage/.claude add -u advisors/ frameworks/
```

Verify changes are staged, then commit:

```bash
git -C /Users/ericpage/.claude commit -m "chore: remove advisor/framework symlinks — plugin is now single source of truth"
```

If `git status` shows "nothing to commit" (all artifacts were untracked), skip the commit — no git changes needed.

---

### Task 18: Version Bump

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: Read current version**

Read `.claude-plugin/plugin.json`. Current version: `0.7.0`.

**Step 2: Bump to next minor version**

This is a breaking change in discovery behavior. Update version to `0.8.0`. Also update the description to reflect the correct advisor count (60 unique advisors after deduplication).

Replace:
```json
{
  "name": "aligned",
  "version": "0.7.0",
  "description": "Opinionated dev stack: TDD pipeline, eval-driven development, design system, multi-agent debugging, 62 advisor personas, automated quality gates"
}
```

With:
```json
{
  "name": "aligned",
  "version": "0.8.0",
  "description": "Opinionated dev stack: TDD pipeline, eval-driven development, design system, multi-agent debugging, 60 advisor personas, 132 frameworks, automated quality gates"
}
```

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 0.8.0 for advisor/framework consolidation"
```

---

### Task 19: Final Verification

**Files:**
- No file changes — verification only

**Step 1: Stale path gate**

Grep all `**/*.md` (excluding `docs/plans/`) for:
- `advisors/va-web-app/`
- `advisors/epch/`
- `advisors/.claude/`
- `frameworks/va-web-app/`
- `frameworks/epch-projects/`
- `~/.claude/advisors/`
- `~/.claude/frameworks/`
- `directory.md` (in skill files only)

All must return 0 results.

**Step 2: Advisor glob sanity**

Glob `advisors/prompts/*.md`. Expected: 60 files.

**Step 3: Framework glob sanity**

Glob `frameworks/*/prompt.md`. Expected: 132 files.

**Step 4: Registry integrity**

Read `advisors/registry.md`. For each `prompt:` path in profiled advisor entries, verify the file exists via Glob.

**Step 5: No `~/.claude/` artifacts**

```bash
ls /Users/ericpage/.claude/advisors/ 2>&1
ls /Users/ericpage/.claude/frameworks/ 2>&1
```

Both should show "No such file or directory."

**Step 6: Verify all commits landed**

```bash
git log --oneline -20
```

Should show commits for Tasks 1-18.

## Manual Steps (Post-Automation)

> Complete these steps after all tasks finish.

- [ ] **Merge feature branch to main:**
  ```bash
  git -C /Users/ericpage/software/aligned_cc_skills checkout main
  git -C /Users/ericpage/software/aligned_cc_skills merge --no-ff consolidation/advisor-framework-flatten -m "feat: consolidate advisors and frameworks into flat directories"
  ```
- [ ] **Re-enable `~/.claude/` autocommit:**
  ```bash
  launchctl load ~/Library/LaunchAgents/com.ericpage.claude-skills-autocommit.plist
  ```
- [ ] **Smoke test discovery:** Start a new Claude session with the plugin and run:
  - `/aligned:use-advisor` — verify all ~60 advisors listed alphabetically
  - `/aligned:use-framework` — verify all ~132 frameworks listed
  - `/aligned:use-advisor steve jobs` — verify loads successfully
  - `/aligned:use-framework the work` — verify loads successfully
- [ ] **Remove safety tags** (after smoke tests pass):
  ```bash
  git -C /Users/ericpage/software/aligned_cc_skills tag -d pre-consolidation
  git -C /Users/ericpage/.claude tag -d pre-consolidation
  ```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Divergence audit timing | Prerequisite (before automated tasks) | Mid-plan task, skip entirely |
| 2 | Task ordering for skill updates vs file moves | Update skill references BEFORE moving files (Phase 3 before Phase 4) | Move files first then update references |
| 3 | `~/.claude/` cleanup approach | `git rm` for tracked files, plain `rm` for untracked | Blanket `rm` + `git add -u` |
| 4 | registry.md Quick Reference table format | 4-column table (slug, name, domains, summary) | Keep directory.md format (3-column: slug, name, summary) |
| 5 | Version bump magnitude | Minor version (0.7.0 → 0.8.0) | Patch (0.7.1) |

### Appendix: Decision Details

#### Decision 1: Divergence audit timing
**Chose:** Run as a prerequisite before automated tasks
**Why:** The divergence audit requires user decisions per file (keep plugin, take source, or merge). The plan's manual steps policy prohibits interactive steps mid-plan. Running the audit as a prerequisite means the user makes all decisions before automation begins, and Task 2 simply applies those recorded decisions. This also means the Ralph loop can execute Tasks 1-19 without pausing.
**Alternatives rejected:**
- Mid-plan task: Violates manual steps policy; Ralph loop cannot pause for user input
- Skip entirely: Risks moving diverged files without the user's knowledge; design doc explicitly requires per-file review

#### Decision 2: Task ordering — skill updates before file moves
**Chose:** Update all skill file references (Tasks 4-9) BEFORE flattening directories (Tasks 12-13)
**Why:** The design doc specifies this order (Phase 3 before Phase 4): "Update all references first so discovery paths point to new locations before files move." However, there's a nuance — between Tasks 4-9 and Tasks 12-13, the skill files will reference paths that don't exist yet (`advisors/prompts/` won't exist until Task 12). This is acceptable because the skills aren't being invoked during migration. The alternative (move first, update after) would leave a window where skills reference old paths that no longer exist — worse because someone might invoke a skill during migration.
**Alternatives rejected:**
- Move files first: Creates a window where discovery is broken because skills still reference old repo-based paths

#### Decision 3: `~/.claude/` cleanup approach
**Chose:** `git rm` for tracked files, plain `rm` for untracked files, with a pre-deletion `git ls-files` check
**Why:** The `~/.claude/` repo tracks some of these artifacts (symlinks are tracked by git as symlink objects, `.repos` manifests and `registry.md` are regular tracked files, the `.claude/` subdirectory with 7 advisor files may or may not be tracked). Using `git rm` for tracked files provides immediate feedback if something is unexpected. Using plain `rm` for untracked files avoids `git rm` errors. A `git status` check before committing confirms deletions were staged correctly.
**Alternatives rejected:**
- Blanket `rm` + `git add -u`: If any artifact is not git-tracked, `rm` succeeds silently but `git add -u` stages nothing for that file — the commit could silently skip deletions without feedback

#### Decision 4: Quick Reference table format
**Chose:** 4-column table (slug, name, domains, summary) matching what `use-advisor` needs for listing
**Why:** The `use-advisor` skill needs to display domains to help users pick the right advisor. The existing `directory.md` only has 3 columns (no domains). Adding domains to the Quick Reference means `use-advisor` can parse a single table instead of cross-referencing profiled entries for domain data.
**Alternatives rejected:**
- Keep 3-column format: Would require `use-advisor` to read profiled entries for domain data, defeating the purpose of a quick reference

#### Decision 5: Version bump magnitude
**Chose:** Minor version bump (0.7.0 → 0.8.0)
**Why:** This is a breaking change — discovery paths change, `directory.md` is deleted, `~/.claude/` fallback is removed. Any tooling or scripts that reference old paths will break. Minor version bump signals this is a significant change with potential for breakage.
**Alternatives rejected:**
- Patch version (0.7.1): Understates the scope of the change; users expect patch versions to be backward-compatible
