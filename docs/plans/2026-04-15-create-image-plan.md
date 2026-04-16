# Create-Image Router Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Restructure the `create-svg-diagram` skill into a generic `create-image` router that handles both diagrams and brand icons via keyword-based routing to separate mode files.

**Source Design Doc:** `docs/plans/2026-04-15-create-image-skill-design.md`

**Architecture:** Single `create-image` SKILL.md acts as a keyword-based router, delegating to `modes/diagram.md` (migrated from `create-svg-diagram`) or `modes/icon.md` (new). The router locates the project's `design-principles.md` before delegating — both modes need it. Follows the brainstorming skill's router pattern: one entry point with mode detection, then handoff to mode-specific files.

**Tech Stack:** Markdown skill files, YAML frontmatter, Claude Code plugin conventions

---

### ✅ Task 1: Create the create-image router SKILL.md

**Files:**
- Create: `skills/create-image/SKILL.md`

**Step 1: Create the directory and router file**

Create `skills/create-image/modes/` directory structure and `skills/create-image/SKILL.md` with the following content (~55 lines — the design doc estimated ~45, but the full routing logic with error handling requires slightly more):

```markdown
---
name: create-image
description: "Use when a diagram, chart, flowchart, icon, or brand visual is
  needed. Routes to diagram mode (charts, flowcharts, matrices, org charts) or
  icon mode (brand icons, custom SVG icons) based on the request."
---

# Create Image

Router for visual artifact creation. Detects the request type and delegates
to the appropriate mode.

## Step 1: Detect Mode

Classify the user's request into one of two modes using keyword matching:

**Icon mode** — creating brand icons or custom SVG icons:
- Keywords: icon, glyph, symbol, brand icon, custom icon

**Diagram mode** — creating charts, flowcharts, or visual frameworks:
- Keywords: diagram, chart, flowchart, org chart, matrix, visual framework,
  bell curve, radial, timeline

**If signals are clear:** Auto-route and proceed to Step 2.

**If ambiguous:** Ask one question: "Are you looking for a brand icon/symbol
or a diagram/chart?"

## Step 2: Locate Design Principles (REQUIRED)

Search for the project's `design-principles.md` in order:
1. `brand/guidelines/design-principles.md`
2. `docs/design/design-principles.md`
3. `~/.claude/docs/design/design-principles.md` (global fallback)

Use Glob to check each path. Use the first match found.

**If none found:** STOP. Tell the user: "No design-principles.md found.
Create one with `/aligned:create-design-principles` or provide at minimum:
background, accent, text colors, and font."

## Step 3: Hand Off to Mode

**If icon mode:**
Read `{base-directory}/modes/icon.md` and follow its process.
Pass the resolved design-principles.md path.

**If diagram mode:**
Read `{base-directory}/modes/diagram.md` and follow its process.
Pass the resolved design-principles.md path.

**If the mode file cannot be Read, STOP and tell the user the plugin
installation may be incomplete.**
```

**Step 2: Verify the file was written correctly**

Read `skills/create-image/SKILL.md`. Verify:
- Frontmatter `name` is `create-image`
- Description mentions both diagrams and icons
- Three search paths for design-principles.md: `brand/guidelines/`, `docs/design/`, and global fallback
- Mode delegation reads from `{base-directory}/modes/`
- Error handling for missing design-principles.md and missing mode files

**Step 3: Commit**

```bash
git add skills/create-image/SKILL.md
git commit -m "feat: create create-image router skill"
```

---

### ✅ Task 2: Migrate diagram mode from create-svg-diagram

**Files:**
- Create: `skills/create-image/modes/diagram.md`
- Reference: `skills/create-svg-diagram/SKILL.md` (source to migrate from)

**Step 1: Read the source file**

Read `skills/create-svg-diagram/SKILL.md` in full. This is the content to migrate.

**Step 2: Create the diagram mode file**

Create `skills/create-image/modes/diagram.md` by transforming the source:

1. **Strip the YAML frontmatter** — remove the `---` / `name:` / `description:` / `---` block at the top of the file
2. **Add a comment header** as the first line: `<!-- Mode file: Read into context by the create-image router. Do not add YAML frontmatter. -->`
3. **Replace the entire `## Step 1: Read Design Principles` section** — from the `## Step 1` heading through the `**If neither file exists:**` block. The original searched two paths (`docs/design/design-principles.md` primary, `~/.claude/docs/design/design-principles.md` fallback). The router now handles this lookup with a broader three-path search, so replace the entire section with:

```markdown
## Step 1: Read Design Principles (REQUIRED)

The router has already located the project's `design-principles.md` and passed its path. **Read that file now.**

Extract: background, foreground, secondary, accent, border, muted colors + font stack + border radii.
```

4. **Keep all remaining content verbatim** — Step 2 (Read Existing Diagrams), SVG Boilerplate, Element Vocabulary, Layout Patterns, Paired Diagrams, Z-Order & Conventions, and Common Mistakes sections are copied without changes.

**Step 3: Verify the migrated content**

Read `skills/create-image/modes/diagram.md`. Verify:
- No YAML frontmatter present
- Comment header is the first line
- Step 1 references the router's located path (does NOT search for design-principles.md independently)
- SVG Boilerplate template with `{token}` placeholders is present and matches source
- Element Vocabulary table has all 8 element types: Primary box, Secondary box, Emphasized box, Dot on curve, Arrow connector, Pennant arrow, Title bar, Tagline
- All 5 layout patterns present: Horizontal flow, Vertical stack, 2x2 grid, Bell curve, Radial circle
- Radial circle trig formula present: `x = cx + R*sin(i*360/N*π/180)`, `y = cy - R*cos(i*360/N*π/180)`
- Common Mistakes table has all 7 entries (no design-principles, radial overlap, text wider than box, lines through boxes, off-palette colors, bare `&`, duplicate marker IDs)

**Step 4: Commit**

```bash
git add skills/create-image/modes/diagram.md
git commit -m "feat: migrate diagram mode from create-svg-diagram"
```

---

### ✅ Task 3: Create the icon mode

**Files:**
- Create: `skills/create-image/modes/icon.md`

**Step 1: Create the icon mode file**

Create `skills/create-image/modes/icon.md` with the following content (~70 lines):

```markdown
<!-- Mode file: Read into context by the create-image router. Do not add YAML frontmatter. -->

# Icon Mode

Generate brand icons that match a project's existing icon style, using
construction patterns from `design-principles.md` and existing icon analysis.

## Step 1: Read Existing Artifacts (mandatory)

The router has already located the project's `design-principles.md` and
passed its path.

**1a. Read the Iconography section:**
Read the design-principles.md file. Find the Iconography section. If no
Iconography section exists, STOP and tell the user:
"The project's design-principles.md has no Iconography section. Add one
manually or run `/aligned:create-design-principles` to regenerate."

**1b. Read existing icons:**
Glob for existing SVG icons in the project's icon directory. Check these
paths in order: `brand/icons/`, `public/icons/`, `src/icons/`,
`assets/icons/`. Use the first directory that contains `.svg` files.

Read all of them to analyze construction patterns.

For projects with more than 20 icons: read 3 from each category listed in
the icon registry file, up to 15 total.

**1c. Read the icon registry:**
Look for an icon registry file (e.g., `ICONS.md`, `icons/README.md`, or a
similar manifest in the icon directory). Read it if one exists.

**1d. Extract output locations:**
From the design-principles.md Technical Spec table, extract:
- SVG source directory (where raw `.svg` files live)
- React component directory (where `.tsx` wrappers live)
- Barrel file path (the `index.ts` that re-exports all icons)

If the Technical Spec table is missing these fields, ask the user for
output locations.

## Step 2: Generate

**2a. Analyze construction patterns** from the icons read in Step 1b:
- Path count (how many `<path>` elements per icon)
- Opacity tiers (which opacity values are used and how)
- Shape vocabulary (organic curves vs geometric primitives)
- Abstraction level (literal vs symbolic representations)

**2b. Generate the new icon** following the project's spec from Step 1a.
Apply these construction constraints:
- Match the path count range observed in existing icons
- Use only opacity values from the project's tier system
- Use the same shape vocabulary (e.g., no `<rect>` or `<line>` for primary
  shapes if existing icons use only `<path>`)
- Match the abstraction level of existing icons

**2c. Apply fallback defaults** for any dimension the project's spec is
silent on:
- `viewBox="0 0 32 32"`
- `fill="currentColor"`
- 3-6 paths per icon
- 4-tier opacity system: 1.0, 0.4-0.55, 0.15-0.3, 0.12-0.15

## Step 3: Output Pipeline

Using the paths extracted in Step 1d:

**3a. Write SVG** to the project's icon source directory.

**3b. Write React component** to the project's component directory.
Follow the pattern of existing React icon components in the project. If no
pattern exists, use a simple functional component that renders the SVG
inline with `width`, `height`, and `className` props.

**3c. Update barrel file** — add the new component export to the barrel
file. Do not fix pre-existing gaps in the barrel file — just register the
new icon.

**3d. Update icon registry** if one exists — add an entry for the new icon
following the existing format.
```

**Step 2: Verify the icon mode file**

Read `skills/create-image/modes/icon.md`. Verify:
- No YAML frontmatter
- Comment header present as first line
- Three main steps: Read Existing Artifacts, Generate, Output Pipeline
- Step 1a checks for Iconography section and STOPs if missing
- Step 1b reads existing icons with 20-icon cap (reads 3 per category, up to 15 total for large projects)
- Step 1d extracts output locations from Technical Spec table
- Step 2c includes fallback defaults: `viewBox="0 0 32 32"`, `fill="currentColor"`, 3-6 paths, 4-tier opacity
- Step 3 has four sub-steps: SVG, React component, barrel file, registry

**Step 3: Commit**

```bash
git add skills/create-image/modes/icon.md
git commit -m "feat: add icon generation mode for create-image skill"
```

---

### ✅ Task 4: Update README.md skill reference entry

**Files:**
- Modify: `README.md` (the skill reference table, the `create-svg-diagram` row)

**Step 1: Replace the table entry**

Find the `create-svg-diagram` row in the skill reference table and replace it:

Old:
```
| create-svg-diagram | Entry Point | `/aligned:create-svg-diagram` | Generate diagrams, charts, and visual frameworks for presentations and docs |
```

New:
```
| create-image | Entry Point | `/aligned:create-image` | Generate diagrams, charts, icons, and brand visuals — routes to diagram or icon mode |
```

**Step 2: Verify the change**

Read the skill reference table in `README.md`. Confirm:
- The new entry uses `create-image` as the skill name
- Invocation is `/aligned:create-image`
- Description mentions both diagrams and icons
- No remaining `create-svg-diagram` entries in the table

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update skill reference table for create-image rename"
```

---

### ✅ Task 5: Update kickstart permissions

**Files:**
- Modify: `skills/kickstart/SKILL.md` (the permissions `allow` array)

**Step 1: Replace all occurrences of the old skill name**

Use Grep to find all occurrences of `create-svg-diagram` in `skills/kickstart/SKILL.md`. Replace every occurrence with `create-image`. The primary target is the `"Skill(aligned:create-svg-diagram)"` entry in the permissions allow array, but there may be other references in narrative text.

**Step 2: Verify the change**

Use Grep to confirm zero occurrences of `create-svg-diagram` remain in `skills/kickstart/SKILL.md`. Also verify:
- `Skill(aligned:create-image)` is present in the allow list
- No other entries were modified

**Step 3: Commit**

```bash
git add skills/kickstart/SKILL.md
git commit -m "chore: update kickstart permissions for create-image rename"
```

---

### ✅ Task 6: Bump plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json` (the `version` field)
- Modify: `.claude-plugin/marketplace.json` (the `version` field)

**Step 1: Update both version numbers**

In `.claude-plugin/plugin.json`, change `"version": "0.20.0"` to `"version": "0.21.0"`.

In `.claude-plugin/marketplace.json`, change `"version": "0.20.0"` to `"version": "0.21.0"`.

**Step 2: Verify both files match**

Read both files and confirm the version is `"0.21.0"` in each.

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version to 0.21.0"
```

---

### Task 7: Delete the old create-svg-diagram directory

**Files:**
- Delete: `skills/create-svg-diagram/SKILL.md`
- Delete: `skills/create-svg-diagram/` (entire directory)

**Step 1: Remove the old skill directory**

```bash
rm -rf skills/create-svg-diagram/
```

**Step 2: Verify deletion**

Use Glob for `skills/create-svg-diagram/**/*`. Confirm no files are returned.

**Step 3: Output migration notice**

After deleting, print this notice to the user (or add it to the commit message body):

> **Migration required:** If you have `Skill(aligned:create-svg-diagram)` in your `~/.claude/settings.json`, replace it with `Skill(aligned:create-image)`. The old skill name will no longer resolve.

**Step 4: Commit**

```bash
git add -u skills/create-svg-diagram/
git commit -m "chore: remove old create-svg-diagram skill directory"
```

---

### Task 8: Verify no dangling cross-references

**Step 1: Search for remaining references**

Use Grep to search the entire repo for the literal string `create-svg-diagram`.

**Acceptable results** (historical artifacts, do not update):
- `docs/mockups/plugin-split.html` — planning artifact
- `docs/diagrams/skill-agent-mind-map.svg` — diagram artifact
- `docs/skill-orchestration.html` — documentation artifact
- `docs/plans/2026-04-15-create-image-skill-design.md` — the source design doc for this work

**Unacceptable results** (must fix if found):
- Any file under `skills/` still referencing `create-svg-diagram`
- `README.md` referencing `create-svg-diagram` in the skill table
- `.claude-plugin/` files referencing `create-svg-diagram`

**Step 2: Fix any dangling references**

If unacceptable references are found, fix them by replacing `create-svg-diagram` with `create-image`.

**Step 3: Commit only if fixes were needed**

Stage only the specific files that were fixed (never use `git add -A`):

```bash
git add <fixed-file-1> <fixed-file-2>
git commit -m "fix: remove dangling create-svg-diagram references"
```

---

### Task 9: Post-implementation validation

**Step 1: Validate routing — icon mode**

Invoke `/aligned:create-image` with a request like "create a seedling icon."

**Pass:** Skill reads `modes/icon.md` and begins the icon creation process (reads design-principles Iconography section, globs for existing icons).
**Fail:** Skill reads `modes/diagram.md` or produces diagram boilerplate.

**Step 2: Validate routing — diagram mode**

Invoke `/aligned:create-image` with a request like "create a flowchart showing the auth flow."

**Pass:** Skill reads `modes/diagram.md` and begins the diagram creation process (reads design-principles for color tokens, references element vocabulary).
**Fail:** Skill reads `modes/icon.md`.

**Step 3: Validate ambiguous request handling**

Invoke `/aligned:create-image` with a request like "create a visual for the onboarding flow."

**Pass:** Skill asks a clarifying question ("Are you looking for a brand icon/symbol or a diagram/chart?").
**Fail:** Skill auto-routes without asking.

**Step 4: Validate missing design-principles handling**

In a directory with no `design-principles.md` at any of the three search paths, invoke `/aligned:create-image`.

**Pass:** Skill STOPs and tells user to create a design-principles.md or run `/aligned:create-design-principles`.
**Fail:** Skill proceeds without design tokens.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Version bump magnitude | 0.21.0 (minor) | 0.20.1 (patch) |
| 2 | Non-source cross-references | Leave as-is in historical artifacts | Update all references everywhere |
| 3 | Commit granularity | One commit per logical unit (up to 8 commits) | Single commit for all changes |
| 4 | Deletion ordering | Delete old skill last (Task 7) | Delete old skill first |
| 5 | Design-principles search path | Unified 3-path search for both modes | Mode-specific search paths |

### Appendix: Decision Details

#### Decision 1: Minor version bump (0.21.0)
**Chose:** 0.21.0
**Why:** This is a user-facing skill rename (`create-svg-diagram` → `create-image`) with a new capability (icon mode). Users who have `Skill(aligned:create-svg-diagram)` in their permission settings will need to update to `Skill(aligned:create-image)`. Per semver, adding a new mode is a feature addition, and renaming a public skill is a breaking change to anyone referencing the old name. A minor bump signals "check your config." Pre-1.0, minor bumps are conventional for this kind of change.
**Alternatives rejected:**
- 0.20.1 (patch): Understates the scope — this adds a new capability and renames a user-facing entry point.

#### Decision 2: Leave non-source cross-references as-is
**Chose:** Don't update references in planning artifacts (`docs/mockups/`, `docs/diagrams/`, `docs/skill-orchestration.html`).
**Why:** These are historical snapshots created when the skill was called `create-svg-diagram`. Updating them to say `create-image` would be revisionist — the documents were accurate at the time they were written. Only source files (`skills/`, `README.md`, `.claude-plugin/`) need updating because they affect runtime behavior and user-facing documentation.
**Alternatives rejected:**
- Update all references: Would modify historical documents to reference a name that didn't exist when they were written, reducing their value as a record of decisions made.

#### Decision 3: One commit per logical unit
**Chose:** Up to 8 separate commits (one per task).
**Why:** Each commit is a coherent, independently reviewable change. If any step introduces an issue, `git bisect` can isolate it. The skill instructions emphasize frequent commits. The create → migrate → extend → update-refs → delete sequence is a natural progression where each commit leaves the repo in a valid state (both old and new skills coexist until Task 7).
**Alternatives rejected:**
- Single commit: Harder to review, harder to bisect. Loses the ability to identify which specific change introduced a problem.

#### Decision 4: Delete old skill last
**Chose:** Delete `skills/create-svg-diagram/` in Task 7, after all new files are created and references updated.
**Why:** During Tasks 1-6, both the old and new skill directories coexist. This means if any task fails mid-execution, the old skill still works. The executor can verify the new skill is complete before the old one is removed. Deleting first would leave a window where no diagram skill exists. Note: During Tasks 1-6, both `/aligned:create-svg-diagram` and `/aligned:create-image` will be simultaneously active in the plugin (plugin discovery scans `skills/*/SKILL.md`). This is intentional — the old skill remains functional as a fallback while the new one is being built and verified.
**Alternatives rejected:**
- Delete first: Creates a broken state where `/aligned:create-svg-diagram` invocations fail and `/aligned:create-image` doesn't exist yet. Risky if execution is interrupted.

#### Decision 5: Unified design-principles.md search path (behavioral change)
**Chose:** The router uses a single, broadened search path for both modes: `brand/guidelines/` → `docs/design/` → global fallback.
**Why:** The original `create-svg-diagram` skill searched only two paths: `docs/design/design-principles.md` (primary) and `~/.claude/docs/design/design-principles.md` (global fallback). The new router adds `brand/guidelines/design-principles.md` as the first search path, per the design doc's requirement to support projects like Planted that store design principles under `brand/guidelines/`. This changes lookup behavior for diagram mode users: a project with both `brand/guidelines/design-principles.md` and `docs/design/design-principles.md` will now use the `brand/guidelines/` version. This is an intentional broadening — the `brand/guidelines/` path is the more specific, project-aware location and should take precedence.
**Alternatives rejected:**
- Mode-specific search paths (diagram uses old 2-path order, icon uses new 3-path order): Adds complexity for marginal benefit. Projects with both files almost certainly want the `brand/guidelines/` version to win — it's the more intentionally placed file. Splitting search logic by mode creates a confusing inconsistency where the same project gets different design tokens depending on whether you ask for an icon or a diagram.
