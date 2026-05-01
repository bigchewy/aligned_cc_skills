# Plugin Split Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Split the single `aligned` plugin into two independent plugins (`aligned-advisors` and `aligned-works`) within the same mono-repo.

**Source Design Doc:** `docs/plans/2026-04-08-plugin-split-design.md`

**Mockups:** `docs/mockups/plugin-split.html`

**Architecture:** Flat split at repo root — `aligned-advisors/` and `aligned-works/` as peer directories, each with its own `.claude-plugin/`, skills, and content. Symlinks from works to advisors for shared content. Mono-repo preserves atomic cross-plugin changes.

**Tech Stack:** Claude Code plugin system (Markdown skills, JSON plugin config, bash hooks/scripts)

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] Verify you are on a feature branch (not main). Run `git branch --show-current` — should show `feature/plugin-split` or similar.
- [ ] Verify `${CLAUDE_PLUGIN_ROOT}` resolution: Create a minimal `aligned-works/` directory with `.claude-plugin/plugin.json` and `hooks/hooks.json` pointing to a trivial test script. Load via `claude --plugin-dir aligned-works/` and trigger a hook. Confirm the hook script receives `CLAUDE_PLUGIN_ROOT` pointing to the `aligned-works/` subdirectory, **not** the repo root. If it resolves to repo root, the hook path architecture must be revised before proceeding — all 3 hooks will break post-move.
- [ ] Verify symlink traversal: In the same test directory, create a symlink (`aligned-works/test-link` → `../some-file.md`). From inside `claude --plugin-dir aligned-works/`, use Read to access `test-link`. Confirm symlinks resolve correctly in the plugin runtime. The design doc's Phase 0 confirmed filesystem-level resolution (2026-04-08), but runtime resolution under `--plugin-dir` must also work.
- [ ] **Windows note:** Tasks 5 uses `ln -s` which requires Developer Mode on Windows. If any contributor runs on Windows, symlink creation will silently fail. This is documented in both plugin READMEs (Task 13) but is not fixable in automation.

---

### Task 1: Create Plugin Directory Scaffolding

**Files:**
- Create: `aligned-advisors/.claude-plugin/plugin.json`
- Create: `aligned-advisors/.claude-plugin/marketplace.json`
- Create: `aligned-works/.claude-plugin/plugin.json`
- Create: `aligned-works/.claude-plugin/marketplace.json`

**Step 1: Create aligned-advisors plugin config**

```bash
mkdir -p aligned-advisors/.claude-plugin
```

Write `aligned-advisors/.claude-plugin/plugin.json`:
```json
{
  "name": "aligned-advisors",
  "version": "1.0.0",
  "description": "Virtual board of advisors for Claude Code: 65 expert personas, 138 structured frameworks, auto-selected by context",
  "author": {
    "name": "Eric Page"
  },
  "repository": "https://github.com/bigchewy/aligned_cc_skills",
  "license": "MIT",
  "keywords": ["advisors", "frameworks", "personas", "brainstorming"]
}
```

Write `aligned-advisors/.claude-plugin/marketplace.json`:
```json
{
  "name": "aligned-advisors",
  "owner": { "name": "Eric Page" },
  "plugins": [
    {
      "name": "aligned-advisors",
      "source": {
        "source": "github",
        "repo": "bigchewy/aligned_cc_skills",
        "path": "aligned-advisors"
      },
      "description": "Virtual board of advisors for Claude Code: 65 expert personas, 138 structured frameworks, auto-selected by context",
      "version": "1.0.0"
    }
  ]
}
```

**Step 2: Create aligned-works plugin config**

```bash
mkdir -p aligned-works/.claude-plugin
```

Write `aligned-works/.claude-plugin/plugin.json`:
```json
{
  "name": "aligned-works",
  "version": "1.0.0",
  "description": "Structured creation workflow for Claude Code: brainstorming, TDD pipeline, automated quality gates, 10 agents, 3 hooks",
  "author": {
    "name": "Eric Page"
  },
  "repository": "https://github.com/bigchewy/aligned_cc_skills",
  "license": "MIT",
  "keywords": ["brainstorming", "tdd", "pipeline", "design-system", "quality-gates"]
}
```

Write `aligned-works/.claude-plugin/marketplace.json`:
```json
{
  "name": "aligned-works",
  "owner": { "name": "Eric Page" },
  "plugins": [
    {
      "name": "aligned-works",
      "source": {
        "source": "github",
        "repo": "bigchewy/aligned_cc_skills",
        "path": "aligned-works"
      },
      "description": "Structured creation workflow for Claude Code: brainstorming, TDD pipeline, automated quality gates, 10 agents, 3 hooks",
      "version": "1.0.0"
    }
  ]
}
```

**Step 3: Commit**

```bash
git add aligned-advisors/.claude-plugin/ aligned-works/.claude-plugin/
git commit -m "chore: create plugin scaffolding for aligned-advisors and aligned-works"
```

---

### Task 2: Move Advisor Content into aligned-advisors

**Files:**
- Move: `advisors/` → `aligned-advisors/advisors/`
- Move: `frameworks/` → `aligned-advisors/frameworks/`

**Step 1: Move directories with git mv**

```bash
git mv advisors aligned-advisors/advisors
git mv frameworks aligned-advisors/frameworks
```

**Step 2: Verify the moves**

Run: `ls aligned-advisors/`
Expected: `advisors/  frameworks/  .claude-plugin/`

Run: `ls aligned-advisors/advisors/prompts/ | wc -l`
Expected: `65`

Run: `ls aligned-advisors/frameworks/ | wc -l`
Expected: `138`

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: move advisors/ and frameworks/ into aligned-advisors/"
```

---

### Task 3: Move Advisor Skills into aligned-advisors

**Files:**
- Move: `skills/use-advisor/` → `aligned-advisors/skills/use-advisor/`
- Move: `skills/use-framework/` → `aligned-advisors/skills/use-framework/`
- Move: `skills/add-advisor/` → `aligned-advisors/skills/add-advisor/`
- Move: `skills/add-framework/` → `aligned-advisors/skills/add-framework/`
- Move: `skills/find-potential-advisors/` → `aligned-advisors/skills/find-potential-advisors/`

**Step 1: Create skills directory and move**

```bash
mkdir -p aligned-advisors/skills
git mv skills/use-advisor aligned-advisors/skills/use-advisor
git mv skills/use-framework aligned-advisors/skills/use-framework
git mv skills/add-advisor aligned-advisors/skills/add-advisor
git mv skills/add-framework aligned-advisors/skills/add-framework
git mv skills/find-potential-advisors aligned-advisors/skills/find-potential-advisors
```

**Step 2: Verify**

Run: `ls aligned-advisors/skills/`
Expected: 5 directories: `add-advisor  add-framework  find-potential-advisors  use-advisor  use-framework`

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: move 5 advisor skills into aligned-advisors/skills/"
```

---

### Task 4: Move Works Content into aligned-works

**Files:**
- Move: `skills/` (remaining 17 skill dirs + `_shared/`) → `aligned-works/skills/`
- Move: `agents/` → `aligned-works/agents/`
- Move: `hooks/` → `aligned-works/hooks/`
- Move: `docs/` → `aligned-works/docs/`

**Step 1: Move remaining skills**

```bash
git mv skills aligned-works/skills
```

This moves all remaining skill directories (including `_shared/`) into `aligned-works/skills/`.

**Step 2: Move agents, hooks, docs**

```bash
git mv agents aligned-works/agents
git mv hooks aligned-works/hooks
git mv docs aligned-works/docs
```

**Step 3: Verify**

Run: `ls aligned-works/skills/ | wc -l`
Expected: `18` (17 skills + `_shared`)

Run: `ls aligned-works/agents/ | wc -l`
Expected: `10`

Run: `ls aligned-works/hooks/`
Expected: `auto-approve-safe-bash-paths.js  auto-approve-worktrees.js  hooks.json  usage-tracker.js`

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: move remaining skills, agents, hooks, docs into aligned-works/"
```

---

### Task 5: Create Symlinks for Cross-Plugin Content Access

**Files:**
- Create: `aligned-works/advisors` (symlink → `../aligned-advisors/advisors`)
- Create: `aligned-works/frameworks` (symlink → `../aligned-advisors/frameworks`)

**Step 1: Create symlinks**

```bash
ln -s ../aligned-advisors/advisors aligned-works/advisors
ln -s ../aligned-advisors/frameworks aligned-works/frameworks
```

**Step 2: Verify symlinks resolve**

Run: `ls -la aligned-works/advisors`
Expected: Symlink pointing to `../aligned-advisors/advisors`

Run: `head -1 aligned-works/advisors/registry.md`
Expected: First line of registry.md (confirms the symlink resolves)

Run: `ls aligned-works/frameworks/ | wc -l`
Expected: `138`

**Step 3: Commit**

```bash
git add aligned-works/advisors aligned-works/frameworks
git commit -m "refactor: add symlinks from aligned-works to aligned-advisors content"
```

---

### Task 6: Remove Old Plugin Config

**Files:**
- Remove: `.claude-plugin/plugin.json`
- Remove: `.claude-plugin/marketplace.json`
- Remove: `.claude-plugin/` directory

**Step 1: Remove old config**

```bash
git rm -r .claude-plugin/
```

**Step 2: Verify**

Run: `ls .claude-plugin/ 2>&1`
Expected: Error — directory should not exist

**Step 3: Commit**

```bash
git commit -m "refactor: remove old root-level .claude-plugin/"
```

---

### Task 7: Update Skill Name Prefixes — Advisor Skills (aligned-advisors)

**Files:**
- Modify: `aligned-advisors/skills/use-advisor/SKILL.md` (all `/aligned:` → `/aligned-advisors:` for advisor skills, `/aligned-works:` for works skills)
- Modify: `aligned-advisors/skills/use-framework/SKILL.md`
- Modify: `aligned-advisors/skills/add-advisor/SKILL.md`
- Modify: `aligned-advisors/skills/add-framework/SKILL.md`
- Modify: `aligned-advisors/skills/find-potential-advisors/SKILL.md`

**Step 1: Update each file**

For each file, replace all `/aligned:` invocations with the correct new prefix:

**Advisor-to-advisor references** (intra-plugin): `/aligned:use-advisor` → `/aligned-advisors:use-advisor`, etc.
**Advisor-to-works references** (cross-plugin): `/aligned:brainstorming` → `/aligned-works:brainstorming`, etc.

Classification of skill prefixes:
- `aligned-advisors:` skills: `use-advisor`, `use-framework`, `add-advisor`, `add-framework`, `find-potential-advisors`
- `aligned-works:` skills: everything else (brainstorming, writing-plans, executing-plans, finishing-a-development-branch, root-cause-analysis, using-git-worktrees, eval-failure-triage, eval-audit, kickstart, test-driven-development, verification-before-completion, kanban-resolve, codebase-audit, create-new-skill, create-design-principles, persona-panel, create-svg-diagram)

In `use-advisor/SKILL.md`:
- `/aligned:use-advisor` → `/aligned-advisors:use-advisor`
- `/aligned:use-framework` → `/aligned-advisors:use-framework`

In `use-framework/SKILL.md`:
- `/aligned:use-framework` → `/aligned-advisors:use-framework`
- `/aligned:use-advisor` → `/aligned-advisors:use-advisor`

In `add-advisor/SKILL.md`:
- `/aligned:add-framework` → `/aligned-advisors:add-framework`

In `find-potential-advisors/SKILL.md`:
- `/aligned:add-advisor` → `/aligned-advisors:add-advisor`

**Step 2: Verify no stale prefixes remain**

Run: `grep -r '/aligned:' aligned-advisors/skills/ --include='*.md'`
Expected: No matches

**Step 3: Commit**

```bash
git add aligned-advisors/skills/
git commit -m "refactor: update skill prefixes to aligned-advisors: in advisor skills"
```

---

### Task 8: Update Skill Name Prefixes — Works Skills (aligned-works)

**Files:**
- Modify: All `aligned-works/skills/*/SKILL.md` files that contain `/aligned:` references
- Modify: `aligned-works/skills/brainstorming/modes/software.md`
- Modify: `aligned-works/skills/brainstorming/modes/business.md`

**Step 1: Find all files with stale prefixes**

Run: `grep -rl '/aligned:' aligned-works/skills/ --include='*.md'`

This should return files including:
- `brainstorming/modes/software.md` — `/aligned:using-git-worktrees`, `/aligned:writing-plans`
- `executing-plans/SKILL.md` — `/aligned:root-cause-analysis`
- `finishing-a-development-branch/SKILL.md` — `/aligned:using-git-worktrees`, `/aligned:finishing-a-development-branch`
- `root-cause-analysis/SKILL.md` — `/aligned:root-cause-analysis`
- `eval-audit/SKILL.md` — `/aligned:brainstorming`, `/aligned:writing-plans`, `/aligned:executing-plans`, `/aligned:finishing-a-development-branch`
- `writing-plans/SKILL.md` — various references
- `codebase-audit/SKILL.md` — references
- `kanban-resolve/SKILL.md` — references

**Step 2: Replace all occurrences**

For each file, apply the prefix classification from Task 7:
- References to advisor skills → `/aligned-advisors:`
- References to works skills → `/aligned-works:`

**Step 3: Add advisor-unreachable error messaging**

Per the design doc: skills that depend on advisor content should print a one-line message when advisor files are unreachable. Add a check to the following files (near where they read `advisors/registry.md` or advisor prompts):

- `aligned-works/skills/_shared/critique-panel-orchestration.md` (line 34, reads `advisors/registry.md`)
- `aligned-works/skills/brainstorming/modes/software.md` (lines 46, 75, reads advisor prompts)
- `aligned-works/skills/create-design-principles/SKILL.md` (line 12, reads steve-jobs.md)

Add after each advisor file read instruction: "If the advisor file is not found (e.g., aligned-advisors plugin is not co-installed), print: 'Install aligned-advisors for full functionality: /install aligned-advisors' and continue without advisor content where possible."

**Step 4: Verify no stale prefixes remain in works skills**

Run: `grep -r '/aligned:' aligned-works/skills/ --include='*.md'`
Expected: No matches

**Step 5: Commit**

```bash
git add aligned-works/skills/
git commit -m "refactor: update skill prefixes to aligned-works:/aligned-advisors: in works skills"
```

---

### Task 9: Update Skill Name Prefixes — Agents and Ralph Loops

**Files:**
- Modify: All files in `aligned-works/agents/` containing `/aligned:` references
- Modify: All files in `aligned-works/docs/ralph_loops/` containing `/aligned:` or `aligned:` references

**Step 1: Find all files with stale prefixes**

Run: `grep -rl 'aligned:' aligned-works/agents/ aligned-works/docs/ralph_loops/ --include='*.md' --include='*.sh'`

**Step 2: Replace references**

In `aligned-works/docs/ralph_loops/run-ralph.sh` (line 227): `/aligned:finishing-a-development-branch` → `/aligned-works:finishing-a-development-branch`

~~In `aligned-works/docs/ralph_loops/FINISH-BRANCH.md`: replace any `/aligned:` references with correct new prefix.~~ *(Obsoleted: `FINISH-BRANCH.md` deleted in autopilot-orchestration-impl, see `docs/plans/2026-04-30-autopilot-orchestration-impl.md` Task 11.)*

In `aligned-works/docs/ralph_loops/EXECUTE-PLAN.md`: replace any `/aligned:` references with correct new prefix.

In agent files: replace any `/aligned:` references following the same classification rules.

Also update `aligned-works/docs/ralph_loops/autopilot.sh` (line 608): `/aligned:finishing-a-development-branch` → `/aligned-works:finishing-a-development-branch`

**Step 3: Verify**

Run: `grep -r '/aligned:' aligned-works/agents/ aligned-works/docs/ralph_loops/ --include='*.md' --include='*.sh'`
Expected: No matches (except potential references to old plugin name in explanatory text, which should be zero)

**Step 4: Commit**

```bash
git add aligned-works/agents/ aligned-works/docs/ralph_loops/
git commit -m "refactor: update skill prefixes in agents and ralph loop files"
```

---

### Task 10: Update Kickstart Permissions List

**Files:**
- Modify: `aligned-works/skills/kickstart/SKILL.md` (the Phase 5 permissions array and Phase 4/6/7 workflow references)

**Step 1: Update Phase 5 permissions**

Replace the entire `permissions.allow` array in Phase 5 with the split permissions. The 22 entries become:

- Advisor skills (5): `Skill(aligned-advisors:use-advisor)`, `Skill(aligned-advisors:use-framework)`, `Skill(aligned-advisors:add-advisor)`, `Skill(aligned-advisors:add-framework)`, `Skill(aligned-advisors:find-potential-advisors)`
- Works skills (17): `Skill(aligned-works:brainstorming)`, `Skill(aligned-works:writing-plans)`, `Skill(aligned-works:executing-plans)`, `Skill(aligned-works:finishing-a-development-branch)`, `Skill(aligned-works:root-cause-analysis)`, `Skill(aligned-works:using-git-worktrees)`, `Skill(aligned-works:eval-failure-triage)`, `Skill(aligned-works:eval-audit)`, `Skill(aligned-works:kickstart)`, `Skill(aligned-works:test-driven-development)`, `Skill(aligned-works:verification-before-completion)`, `Skill(aligned-works:kanban-resolve)`, `Skill(aligned-works:codebase-audit)`, `Skill(aligned-works:create-new-skill)`, `Skill(aligned-works:create-design-principles)`, `Skill(aligned-works:persona-panel)`, `Skill(aligned-works:create-svg-diagram)`

Also update the Phase 5 detection check: look for `Skill(aligned-works:brainstorming)` instead of `Skill(aligned:brainstorming)`.

**Step 2: Update workflow references in Phase 4 and Phase 7**

Replace all `/aligned:` invocations in the CLAUDE.md templates (Phase 4 Section 6 — Workflows) and Phase 7 (What to Try First) with correct new prefixes.

**Step 3: Update settings.json template**

In Phase 4 (Settings section), replace `"aligned": true` with both plugins:
```json
{
  "enabledPlugins": {
    "aligned-advisors": true,
    "aligned-works": true
  }
}
```

**Step 4: Verify**

Run: `grep '/aligned:' aligned-works/skills/kickstart/SKILL.md`
Expected: No matches

Run: `grep 'Skill(aligned:' aligned-works/skills/kickstart/SKILL.md`
Expected: No matches

**Step 5: Commit**

```bash
git add aligned-works/skills/kickstart/SKILL.md
git commit -m "refactor: update kickstart permissions and templates for two-plugin structure"
```

---

### Task 11: Update Fallback Glob Patterns for Two-Plugin Disambiguation

**Files:**
- Modify: `aligned-works/skills/_shared/critique-panel-orchestration.md` (line 29)
- Modify: `aligned-works/skills/brainstorming/modes/software.md` (lines 208, 236)
- Modify: `aligned-works/skills/brainstorming/modes/business.md` (line 176)
- Modify: `aligned-works/skills/create-design-principles/SKILL.md` (line 283)
- Modify: `aligned-works/skills/writing-plans/SKILL.md` (the fallback Glob pattern in critique panel section and plugin root resolution)

**Step 1: Identify all Glob fallback patterns**

There are 7 instances across 5 files using **two different phrasings**:

**Variant A (5 instances):** "Use the match that lives under a directory containing `.claude-plugin/plugin.json`"
- `critique-panel-orchestration.md` line 29
- `software.md` line 208
- `business.md` line 176
- `create-design-principles/SKILL.md` line 283
- `writing-plans/SKILL.md` line 368

**Variant B (2 instances):** "use the match whose parent directory contains `.claude-plugin/plugin.json`"
- `software.md` line 236
- `writing-plans/SKILL.md` line 521

Replace **both variants** with the two-step find-and-verify pattern:

**Variant A replacement:** Replace the phrase ending in "`.claude-plugin/plugin.json`." with: "If multiple matches exist, Read `.claude-plugin/plugin.json` from the nearest ancestor directory of each match. Use the match whose plugin.json has `\"name\": \"aligned-works\"`."

**Variant B replacement:** Replace the phrase ending in "`.claude-plugin/plugin.json`" with: "if multiple matches exist, Read `.claude-plugin/plugin.json` from the nearest ancestor directory of each match and use the match whose plugin.json has `\"name\": \"aligned-works\"`"

**Error path:** If Glob returns matches but none have a valid `.claude-plugin/plugin.json` with `"name": "aligned-works"` in an ancestor directory, STOP and tell the user: "Could not find the aligned-works plugin root. Verify the plugin is installed correctly."

> **Behavior change:** This changes from a single-step "find directory containing plugin.json" filter to a two-step "find, then verify plugin name" pattern. With two plugins in the repo, the old single-step filter would match twice. The new pattern disambiguates by checking the `name` field. Skills will now fail gracefully on missing/malformed plugin.json rather than returning wrong-plugin content.

**Step 2: Verify both variants are gone**

Run: `grep -r 'lives under a directory containing' aligned-works/skills/ --include='*.md'`
Expected: No matches

Run: `grep -r 'parent directory contains.*plugin\.json' aligned-works/skills/ --include='*.md'`
Expected: No matches

**Step 3: Commit**

```bash
git add aligned-works/skills/
git commit -m "refactor: update Glob fallback patterns for two-plugin disambiguation"
```

---

### Task 12: Update add-advisor and add-framework Count-Update Instructions

**Files:**
- Modify: `aligned-advisors/skills/add-advisor/SKILL.md` (count-update steps referencing README.md, plugin.json, marketplace.json)
- Modify: `aligned-advisors/skills/add-framework/SKILL.md` (same)

**Step 1: Update paths and discovery logic in add-advisor/SKILL.md**

Two areas need updating:

**A. Discovery logic (lines 29-31):** The skill currently checks for `advisors/prompts/` relative to the project working directory. Post-split, advisor content lives at `{plugin-root}/advisors/prompts/` (where plugin-root is `aligned-advisors/`). Change the discovery path from `advisors/prompts/` to use the plugin root: resolve via the "Base directory for this skill:" line printed at skill load (the plugin root is `{base-directory}/../..`), then check `{plugin-root}/advisors/prompts/`. This matches the same resolution pattern used by other skills.

**B. Count-update instructions:** Currently reference:
- `README.md` → should become `aligned-advisors/README.md` (or use the plugin root-relative `README.md` since the skill runs from within `aligned-advisors/`)
- `.claude-plugin/plugin.json` → no change needed (relative to plugin root)
- `.claude-plugin/marketplace.json` → no change needed

Since these skills now live inside `aligned-advisors/`, and the plugin root resolves to `aligned-advisors/`, the `.claude-plugin/` paths remain correct. But the `README.md` reference needs to point to the advisors plugin's README, not the repo root.

Also update any instructions about updating counts in the works plugin's description (since works now has its own plugin.json that doesn't include advisor/framework counts).

**Step 2: Same for add-framework/SKILL.md**

Apply the same path adjustments.

**Step 3: Verify**

Read both files and confirm all paths resolve correctly from within the `aligned-advisors/` plugin root.

**Step 4: Commit**

```bash
git add aligned-advisors/skills/
git commit -m "refactor: update count-update instructions for two-plugin structure"
```

---

### Task 13: Create Plugin READMEs

**Files:**
- Create: `aligned-advisors/README.md`
- Create: `aligned-works/README.md`

**Step 1: Write aligned-advisors/README.md**

Content should include:
- Plugin name, description, installation instructions (`/plugin marketplace add bigchewy/aligned_cc_skills` then `/plugin install aligned-advisors@aligned-advisors`)
- Skill reference table (5 skills)
- Advisor count (65) and framework count (138)
- Quick start guide (use-advisor, use-framework)
- Note about Windows symlink requirements (Developer Mode)
- Link to aligned-works for the full creation workflow
- Version: 1.0.0
- License: MIT

**Step 2: Write aligned-works/README.md**

Content should include:
- Plugin name, description, installation instructions
- Prerequisites: "Recommended: co-install aligned-advisors for full functionality"
- Skill reference table (17 skills)
- Agent table (10 agents)
- Hook table (3 hooks)
- Iron Rules section
- Ralph loop documentation reference
- Version: 1.0.0
- License: MIT

**Step 3: Commit**

```bash
git add aligned-advisors/README.md aligned-works/README.md
git commit -m "docs: add READMEs for aligned-advisors and aligned-works"
```

---

### Task 14: Update Repo-Level Documentation

**Files:**
- Modify: `README.md` (repo root — becomes an overview pointing to both plugins)
- Modify: `CLAUDE.md` (update plugin structure description, version bump process, path rules)
- Modify: `CONTRIBUTING.md` (update skill anatomy paths, adding-a-skill instructions)
- Modify: `.github/ISSUE_TEMPLATE/bug_report.md` (update any plugin references)
- Modify: `.github/pull_request_template.md` (if it references the old structure)

**Step 1: Update root README.md**

Transform from single-plugin README to mono-repo overview:
- Brief description of both plugins
- Installation instructions for each
- Links to per-plugin READMEs for details
- Development section (local testing: `claude --plugin-dir aligned-advisors/` or `claude --plugin-dir aligned-works/`)
- Changelog entry for 1.0.0 (the split)
- Keep License section

**Step 2: Update CLAUDE.md**

Update:
- Path Rule section: both plugins use `skills/` prefix relative to their plugin root
- Version section: both `aligned-advisors/.claude-plugin/plugin.json` and `aligned-works/.claude-plugin/plugin.json` plus their marketplace.json files — all four must match their respective plugin version
- Adding a Skill section: specify which plugin the skill goes in

**Step 3: Update CONTRIBUTING.md**

Update:
- Skill anatomy paths: clarify which plugin directory skills go into
- Testing instructions: `claude --plugin-dir aligned-advisors/` or `claude --plugin-dir aligned-works/`
- Version bump: both plugin.json and marketplace.json in the relevant plugin's `.claude-plugin/`
- Adding an advisor: use `/aligned-advisors:add-advisor`
- Adding a framework: use `/aligned-advisors:add-framework`

**Step 4: Update .github templates**

Update bug_report.md and pull_request_template.md if they reference the old `aligned:` prefix or old paths.

**Step 5: Commit**

```bash
git add README.md CLAUDE.md CONTRIBUTING.md .github/
git commit -m "docs: update repo-level docs for two-plugin structure"
```

---

### Task 15: Update .gitignore Paths

**Files:**
- Modify: `.gitignore` (update paths that reference `docs/` to `aligned-works/docs/`)

**Step 1: Update paths**

Current `.gitignore` entries that need updating:
- `docs/plans/` → `aligned-works/docs/plans/`
- `docs/investigations/` → `aligned-works/docs/investigations/`

Keep generic entries unchanged (`.worktrees/`, `*.log`, etc.).

**Step 2: Verify**

Run: `git status --ignored --short | head -20`
Confirm the gitignore still works for the new paths.

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: update .gitignore paths for new plugin structure"
```

---

### Task 16: Update autopilot.sh and run-ralph.sh Path Resolution

**Files:**
- Modify: `aligned-works/docs/ralph_loops/autopilot.sh` (the `PLUGIN_ROOT` and skill file path resolution)

**Step 1: Verify PLUGIN_ROOT resolution**

In `autopilot.sh`, line 40: `PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"`. After the move, `SCRIPT_DIR` is `aligned-works/docs/ralph_loops/`, so `../..` resolves to `aligned-works/` — which is correct (it should be the works plugin root).

The skill file references on lines 49-51 use `$PLUGIN_ROOT/skills/writing-plans/...` and `$PLUGIN_ROOT/skills/_shared/...` — these are correct since writing-plans and _shared live in aligned-works.

**Step 2: Verify run-ralph.sh**

`run-ralph.sh` uses `SCRIPT_DIR` relative paths. After the move, `EXECUTE-PLAN.md` is still in the same directory. No changes needed.

**Step 3: Verify the `/aligned:finishing-a-development-branch` reference was already updated in Task 9**

Run: `grep 'aligned:' aligned-works/docs/ralph_loops/autopilot.sh`
Run: `grep 'aligned:' aligned-works/docs/ralph_loops/run-ralph.sh`
Expected: References should show `aligned-works:` prefix (updated in Task 9)

**Step 4: Commit (only if changes were needed)**

If any changes were needed beyond Task 9:
```bash
git add aligned-works/docs/ralph_loops/
git commit -m "fix: adjust ralph loop path resolution for plugin split"
```

---

### Task 17: Validate Plugin Structure — Prefix Completeness

**Files:** No modifications — validation only.

**Step 1: Scan for stale `aligned:` references**

Run: `grep -r '/aligned:' aligned-advisors/ aligned-works/ --include='*.md' --include='*.sh' --include='*.js' --include='*.json'`

Expected: Zero matches. Every instance should now be `/aligned-advisors:` or `/aligned-works:`.

Run: `grep -r 'Skill(aligned:' aligned-advisors/ aligned-works/ --include='*.md' --include='*.json'`

Expected: Zero matches. Every instance should now be `Skill(aligned-advisors:` or `Skill(aligned-works:`.

Run: `grep -r '"aligned"' aligned-advisors/ aligned-works/ --include='*.json' --include='*.md'`

Expected: Zero matches in plugin.json/marketplace.json (the old plugin name). May appear in explanatory docs — those are acceptable.

**Step 2: If stale references found, fix them**

Apply the classification rules: advisor skills get `aligned-advisors:`, works skills get `aligned-works:`.

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve remaining stale aligned: prefix references"
```

---

### Task 18: Validate Plugin Structure — Skill Counts

**Files:** No modifications — validation only.

**Step 1: Count skills in each plugin**

Run: `ls -d aligned-advisors/skills/*/ | grep -v _shared | wc -l`
Expected: `5`

Run: `ls -d aligned-works/skills/*/ | grep -v _shared | wc -l`
Expected: `17`

**Step 2: Verify plugin.json skills arrays (if plugin.json includes a skills field)**

Check that each plugin.json only lists skills that exist in its `skills/` directory.

**Step 3: Verify no skill directories were left behind at the old root**

Run: `ls skills/ 2>&1`
Expected: Error — `skills/` directory should not exist at repo root

Run: `ls advisors/ 2>&1`
Expected: Error — `advisors/` directory should not exist at repo root

Run: `ls agents/ hooks/ docs/ 2>&1`
Expected: Errors — these directories should not exist at repo root

**Step 4: Commit any fixes**

Only if discrepancies were found and fixed.

---

### Task 19: Validate Plugin Loading — Smoke Test

**Files:** No modifications — validation only.

**Step 1: Verify aligned-advisors loads independently**

Run: `claude --plugin-dir aligned-advisors/ -p "List the skills available from the aligned-advisors plugin. Just list the skill names, nothing else."`

Expected output should include: `use-advisor`, `use-framework`, `add-advisor`, `add-framework`, `find-potential-advisors`

**Step 2: Verify aligned-works loads independently**

Run: `claude --plugin-dir aligned-works/ -p "List the skills available from the aligned-works plugin. Just list the skill names, nothing else."`

Expected output should include: `brainstorming`, `writing-plans`, `executing-plans`, `finishing-a-development-branch`, and the other 13 works skills.

**Step 3: Verify symlinks work from aligned-works**

Run: `claude --plugin-dir aligned-works/ -p "Read aligned-works/advisors/registry.md and report the first 3 lines."`

Expected: Content from the symlinked registry.md

**Step 4: Document any failures**

If a plugin fails to load, investigate and fix. Common issues:
- Missing SKILL.md frontmatter
- Broken symlinks
- hooks.json path resolution issues (check `${CLAUDE_PLUGIN_ROOT}`)

---

## Manual Steps (Post-Automation)

- [ ] **Test hook discovery:** Load works plugin and trigger a hook event. Verify `${CLAUDE_PLUGIN_ROOT}` resolves to `aligned-works/` (not repo root). If it resolves to repo root, `hooks.json` paths will need the `aligned-works/` prefix stripped.
- [ ] **Test cross-plugin invocation:** Load both plugins (`claude --plugin-dir aligned-advisors/ --plugin-dir aligned-works/`), invoke a works skill that dispatches an advisor skill (e.g., brainstorming → critique panel reads `advisors/registry.md`).
- [ ] **Merge feature branch to main** via `/aligned-works:finishing-a-development-branch` or manually.
- [ ] **Tag both plugins:** `git tag aligned-advisors-v1.0.0` and `git tag aligned-works-v1.0.0`.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Task ordering | File moves first, then reference updates | Interleave moves and updates |
| 2 | Prefix update strategy | Classify all skills up front, apply mechanically | Update ad hoc per file |
| 3 | Validation as separate tasks | Dedicated validation tasks at end | Inline validation in each move task |
| 4 | autopilot.sh changes | Verify-only task (path resolution still works) | Rewrite path resolution |
| 5 | Count-update instructions | Update for advisors plugin only | Update for both plugins |

### Appendix: Decision Details

#### Decision 1: Task ordering — moves first, then reference updates
**Chose:** Complete all `git mv` operations (Tasks 1-6) before updating any references (Tasks 7-16).
**Why:** Interleaving moves and updates would create states where some files reference old paths and some reference new paths. By moving everything first, the repo enters a known-broken state where *all* references are stale, making it easy to systematically find and fix them. This also means each commit in the move phase is a clean structural change, and each commit in the update phase is a clean content change.
**Alternatives rejected:**
- Interleave moves and updates: Creates confusing intermediate states where it's unclear which references are stale and which are updated. Harder to verify completeness.

#### Decision 2: Prefix update strategy — classify all skills up front
**Chose:** Define the full classification (which skills get `aligned-advisors:` vs `aligned-works:`) once in Task 7, then apply it mechanically across all files.
**Why:** With 133 instances across 21+ files, ad-hoc decisions per file would be error-prone and inconsistent. A single classification table ensures every reference gets the correct prefix. The classification is straightforward: 5 advisor skills get `aligned-advisors:`, 17 works skills get `aligned-works:`.
**Alternatives rejected:**
- Ad hoc per file: Too error-prone at this scale. Risk of inconsistent prefixes.

#### Decision 3: Validation as separate tasks
**Chose:** Dedicated validation tasks (17-19) at the end of the plan.
**Why:** Validation requires the complete split to be in place. Running prefix scans before all files are moved would produce false positives. The smoke tests (Task 19) can only run after all structural and reference changes are complete. Keeping validation separate also makes it easy to re-run if fixes are needed.
**Alternatives rejected:**
- Inline validation per task: Would miss cross-task issues (e.g., a reference in a moved file pointing to another not-yet-moved file).

#### Decision 4: autopilot.sh path resolution — verify only
**Chose:** Task 16 is primarily a verification task, not a modification task.
**Why:** `autopilot.sh` uses `SCRIPT_DIR/../..` to find the plugin root. After moving to `aligned-works/docs/ralph_loops/`, `../..` resolves to `aligned-works/` — which is the correct plugin root. All three `$PLUGIN_ROOT`-relative paths resolve correctly:
- `$PLUGIN_ROOT/skills/writing-plans/SKILL.md` → `aligned-works/skills/writing-plans/SKILL.md` (exists, moved in Task 4)
- `$PLUGIN_ROOT/skills/writing-plans/plan-critique-checklist.md` → `aligned-works/skills/writing-plans/plan-critique-checklist.md` (exists, moved in Task 4)
- `$PLUGIN_ROOT/skills/_shared/kanban-entry-format.md` → `aligned-works/skills/_shared/kanban-entry-format.md` (exists, moved in Task 4)

The only changes needed are the `/aligned:` prefix updates in the output messages, which are handled in Task 9.
**Alternatives rejected:**
- Rewrite path resolution: Unnecessary — the existing `../../` convention works correctly in the new structure.

#### Decision 5: Count-update instructions — advisors plugin only
**Chose:** Update the count-update instructions in `add-advisor` and `add-framework` to target `aligned-advisors/` paths only.
**Why:** These skills add content to `advisors/prompts/` and `frameworks/` — both of which live in the advisors plugin. The works plugin's description doesn't include advisor/framework counts, so there's nothing to update there. The count-update instructions should only reference files within their own plugin.
**Alternatives rejected:**
- Update for both plugins: The works plugin's description mentions agents and hooks, not advisors. Cross-plugin count syncing would add complexity with no benefit.
