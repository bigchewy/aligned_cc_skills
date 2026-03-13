# Design: Advisor & Framework Consolidation — Standalone Plugin

**Date:** 2026-03-12
**Status:** Draft
**Topic:** advisor-framework-consolidation
**Mockups:** docs/mockups/advisor-framework-consolidation/

## Problem

Advisor and framework files live in three overlapping locations: this plugin repo, `~/.claude/advisors/prompts/` (via symlinks to source repos), and the source repos themselves (`epch`, `va-web-app`). The `use-advisor` and `use-framework` skills search `~/.claude/` first, creating a shadowing problem where plugin copies are overridden by symlinked originals. Content has diverged in some cases. Two EPCH frameworks are missing from the plugin. The `advisors/.repos` manifest says `epch-projects` but the actual directory is `advisors/epch/`, causing silent glob failures.

## Goal

Make this plugin the single source of truth for all advisors and frameworks. Remove all symlinks, `~/.claude/` discovery paths, and repo-based directory grouping. Flatten everything into clean, single-level directories. Resolve all content divergences with user approval.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Flatten advisors into `advisors/prompts/` | Repo-based grouping (va-web-app, epch, .claude) is an implementation artifact with no user value |
| Flatten frameworks into `frameworks/{slug}/` | Same rationale; no slug collisions exist between repos |
| Delete 3 duplicate EPCH advisors | april-dunford, richard-rumelt, shirin-oreizy exist in both va-web-app and epch; va-web-app versions are strictly superior (more voice detail, more frameworks, more guardrails); registry already points to va-web-app |
| `epch` is the correct repo name | `epch-projects` is the old name; `epch` is current |
| Per-advisor divergence review | User decides each diverged file individually rather than blanket "source wins" or "plugin wins" |
| Remove all `~/.claude/` advisor/framework artifacts | Plugin-only lookup; no symlinks, no manifests, no duplicate registries |
| Leave source repos untouched | Source repos keep their advisor files (will become stale) — not our concern |
| Merge directory.md into registry.md | Two files duplicated data and created a sync obligation; merged file ~300 lines (~10K tokens); `use-advisor` reads only the Quick Reference section, not the full file |
| Keep `advisors/prompts/` subdirectory | Cleanly separates metadata (registry.md) from prompt files; avoids filtering registry.md out of advisor globs |

## New Directory Structure

```
advisors/
  registry.md              # Single source: quick-reference table + detailed critic metadata
  prompts/
    steve-jobs.md          # All ~60 advisors, flat, alphabetical
    the-architect.md
    april-dunford.md
    copywriter.md
    steve-krug.md
    ...

frameworks/
  clearing-model/          # All ~132 frameworks, flat
    prompt.md
    examples.md
    anti-examples.md
  content-inc-model/
    prompt.md
  design-principles/       # NEW — copied from EPCH source
    prompt.md
    examples.md
    anti-examples.md
  landing-page-assembly/   # NEW — copied from EPCH source
    prompt.md
  ...
```

**Eliminated:**
- `advisors/.repos` and `frameworks/.repos` (manifests)
- `advisors/va-web-app/`, `advisors/epch/`, `advisors/.claude/` (repo subdirectories)
- `frameworks/va-web-app/`, `frameworks/epch-projects/` (repo subdirectories)
- All symlinks and files in `~/.claude/advisors/` and `~/.claude/frameworks/`

## Phase 1: Divergence Audit

Launch sub-agents in parallel to diff every file between plugin and source repos:

### 1a. EPCH advisors (11 unique, after removing 3 duplicates)
Compare each `.md` in `advisors/epch/` against `/Users/ericpage/software/epch-projects/src/lib/advisors/prompts/`.
Report per file: IDENTICAL | DIVERGED (with diff summary) | MISSING_FROM_PLUGIN

### 1b. va-web-app advisors (42 files)
Compare each `.md` in `advisors/va-web-app/` against `/Users/ericpage/software/va-web-app/src/lib/advisors/prompts/`.
Same report format.

### 1c. All frameworks
Compare `frameworks/va-web-app/` against va-web-app source and `frameworks/epch-projects/` against EPCH source.
Identify the 2 known missing frameworks plus any other divergences.

### 1d. Present divergence report
For each DIVERGED or MISSING_FROM_PLUGIN item, present the user a summary of what differs. User decides each one: keep plugin version, take source version, or merge.

## Phase 2: Content Consolidation

### 2a. Copy missing frameworks
Copy into current structure first (they get flattened in Phase 4):
- `design-principles/` (prompt.md, examples.md, anti-examples.md) from EPCH source → `frameworks/epch-projects/`
- `landing-page-assembly/` (prompt.md) from EPCH source → `frameworks/epch-projects/`

### 2b. Apply user-approved divergence decisions
Update or replace files per user decisions from Phase 1d.

### 2c. Delete duplicate EPCH advisors
Remove `advisors/epch/april-dunford.md`, `advisors/epch/richard-rumelt.md`, `advisors/epch/shirin-oreizy.md`.

## Phase 3: Skill Code & Registry Updates (BEFORE moving files)

Update all references first so discovery paths point to new locations before files move. This prevents a broken window where skills reference paths that don't exist.

### 3a. `skills/use-advisor/SKILL.md`
- Remove Step 1a (`~/.claude/advisors/prompts/` discovery) entirely
- Replace Step 1b+1c with single glob: `advisors/prompts/*.md`
- Update Step 1b reference from `advisors/directory.md` to `advisors/registry.md` (Quick Reference table)
- Remove repo-based listing grouping — list alphabetically
- Remove line 50 (`~/.claude/` user files reference)

### 3b. `skills/use-framework/SKILL.md`
- Replace Step 1a+1b (manifest + per-repo glob) with single glob: `frameworks/*/prompt.md`
- Remove Step 1c (`~/.claude/frameworks/prompts/` fallback) entirely
- Remove repo-based listing grouping
- Update inline example path: `frameworks/va-web-app/clearing-model/prompt.md` → `frameworks/clearing-model/prompt.md`

### 3c. `skills/add-advisor/SKILL.md`
- Remove Option B from Step 8 (symlink creation instructions, lines 204-209)
- Update all paths: `advisors/{repo-name}/` → `advisors/prompts/`
- Update Step 8b: append to Quick Reference table in `registry.md` (no longer `directory.md`)
- Update canonical example (line 102): `advisors/va-web-app/diana-chapman.md` → `advisors/prompts/diana-chapman.md`
- **Post-migration target DX:** Adding an advisor is 2 steps: (1) create file in `advisors/prompts/`, (2) add row to Quick Reference table in `registry.md`

### 3d. `skills/add-framework/SKILL.md`
- Remove Option B from Step 7 (symlink creation instructions, lines 188-193)
- Update all paths: `frameworks/{repo-name}/` → `frameworks/`
- Update canonical example paths (lines 64, 106, 117): `frameworks/va-web-app/clearing-model/` → `frameworks/clearing-model/`
- **Post-migration target DX:** Adding a framework is 2 steps: (1) create folder with `prompt.md` in `frameworks/`, (2) verify with glob

### 3e. `skills/brainstorming/SKILL.md`
- Update 3 advisor path references: `advisors/.claude/steve-krug.md` → `advisors/prompts/steve-krug.md`, `advisors/.claude/the-architect.md` → `advisors/prompts/the-architect.md` (2 occurrences)

### 3f. `skills/create-design-principles/SKILL.md` + checklist
- Update 3 advisor path references total:
  - `skills/create-design-principles/SKILL.md` lines 12, 270: `advisors/va-web-app/steve-jobs.md` → `advisors/prompts/steve-jobs.md`
  - `skills/create-design-principles/design-critique-checklist.md` line 9: same path update

### 3g. `README.md`
- Update framework count from 130 to 132
- Remove `~/.claude/advisors/prompts/{repo-name}/` custom advisor instructions
- Update any remaining `advisors/{repo-name}/` or `frameworks/{repo-name}/` references
- Audit all old path references with grep before committing

## Phase 4: Flatten Directories

### 4a. Flatten advisors
1. Create `advisors/prompts/`
2. Move all `.md` files from `advisors/va-web-app/`, `advisors/epch/`, `advisors/.claude/` into `advisors/prompts/`
3. Delete empty repo subdirectories
4. Delete `advisors/.repos`

### 4b. Flatten frameworks
1. Move all framework directories from `frameworks/va-web-app/` and `frameworks/epch-projects/` up one level into `frameworks/`
2. Delete empty repo subdirectories
3. Delete `frameworks/.repos`

### 4c. Stale path verification gate
Grep all `skills/**/*.md` for old paths: `advisors/va-web-app/`, `advisors/epch/`, `advisors/.claude/`, `frameworks/va-web-app/`, `frameworks/epch-projects/`. Must return 0 results (excluding `docs/plans/completed/`). If any remain, fix before proceeding.

## Phase 5: Registry Rewrite (merge directory.md into registry.md)

### 5a. `advisors/registry.md` — becomes the single metadata file
- Add a **Quick Reference** table at the top: `slug | name | domains | summary` for ALL advisors (profiled and unprofiled). `use-advisor` reads ONLY this section for listing (not the full file).
- All `prompt:` paths: `advisors/{repo}/slug.md` → `advisors/prompts/slug.md`
- "Adding advisors" instruction (line 9): update from `advisors/{repo-name}/` to `advisors/prompts/`
- "Not Yet Profiled" note (line 251): update path reference from `advisors/va-web-app/` to `advisors/prompts/`
- Convert "Not Yet Profiled" comma-separated list into full table rows in the Quick Reference
- Add Steve Krug (currently missing from directory.md)
- Section structure stays (Selection Guidelines, Real Human Advisors, Synthetic Personas, Not Yet Profiled)

### 5b. Delete `advisors/directory.md`
- Its data is now in the Quick Reference table of `registry.md`
- Update `use-advisor/SKILL.md` to read `advisors/registry.md` instead of `advisors/directory.md`
- Update `add-advisor/SKILL.md` Step 8b to append to the Quick Reference table in `registry.md`

## Phase 6: `~/.claude/` Cleanup

Remove all advisor/framework artifacts from `~/.claude/`:
```
~/.claude/advisors/prompts/epch-projects    (symlink)
~/.claude/advisors/prompts/va-web-app       (symlink)
~/.claude/advisors/prompts/.claude/          (directory, 6 duplicate files)
~/.claude/advisors/prompts/.repos            (manifest)
~/.claude/advisors/registry.md               (diverged copy)
~/.claude/frameworks/prompts/epch-projects   (symlink)
~/.claude/frameworks/prompts/va-web-app      (symlink)
~/.claude/frameworks/prompts/.repos          (manifest)
```

Then remove empty parent directories. The `~/.claude/` repo auto-commits via launchd.

## Phase 7: Version Bump

Update `.claude-plugin/plugin.json` — bump to next minor version (breaking change in discovery behavior).

## Testing & Verification

**TDD note:** This migration involves no application code — only markdown skill files, markdown metadata, and file moves. No test files are created or modified. The verification checklist below serves as the manual test plan.

1. **Stale path gate (Phase 4c):** Grep all `skills/**/*.md` for old paths — must return 0 results (excluding `docs/plans/completed/`)
2. **Advisor discovery:** `/aligned:use-advisor` with no args — all ~60 advisors listed alphabetically, Steve Krug included
3. **Framework discovery:** `/aligned:use-framework` with no args — all ~132 frameworks listed, 2 new EPCH ones included
4. **Glob sanity:** `advisors/prompts/*.md` → ~60 files; `frameworks/*/prompt.md` → ~132
5. **Registry integrity:** Every `prompt:` path in `advisors/registry.md` resolves to an actual file
6. **No `~/.claude/` artifacts:** `~/.claude/advisors/` and `~/.claude/frameworks/` should not exist
7. **Skill smoke tests:** `use-advisor steve jobs`, `use-framework the work`, `add-advisor` listing
8. **README audit:** Grep README.md for old paths — must return 0 results

## Critical Files

| File | Change |
|------|--------|
| `skills/use-advisor/SKILL.md` | Rewrite discovery to single flat glob, read registry.md instead of directory.md |
| `skills/use-framework/SKILL.md` | Rewrite discovery to single flat glob, update inline example path |
| `skills/add-advisor/SKILL.md` | Remove symlink Option B, update paths (line 102 canonical example + Step 8/8b) |
| `skills/add-framework/SKILL.md` | Remove symlink Option B, update paths (lines 64, 106, 117 canonical examples + Step 7) |
| `skills/brainstorming/SKILL.md` | Update 3 advisor path references (steve-krug, the-architect x2) |
| `skills/create-design-principles/SKILL.md` | Update 2 advisor path references (lines 12, 270) |
| `skills/create-design-principles/design-critique-checklist.md` | Update 1 advisor path reference (line 9) |
| `advisors/registry.md` | Merge directory.md content, add Quick Reference table, rewrite all ~29 `prompt:` paths, update instructions (lines 9, 251) |
| `advisors/directory.md` | Delete (merged into registry.md) |
| `advisors/.repos` | Delete |
| `frameworks/.repos` | Delete |
| `.claude-plugin/plugin.json` | Version bump |
| `README.md` | Update framework count, update/remove `~/.claude/` instructions, audit all old path references |
