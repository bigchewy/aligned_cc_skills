# Token Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Reduce token consumption when launching skills and subagents, without losing functionality or effectiveness.

**Source Design Doc:** N/A (root cause analysis performed in-session)

**Architecture:** Three categories of safe optimization: (1) remove verbatim CLAUDE.md duplication that loads twice in every context, (2) extract repeated boilerplate sections from skills to a shared directory with on-demand loading, (3) condense verbose skill sections where the length adds no instructional value. All changes preserve the full behavioral intent of every skill and agent.

**Tech Stack:** Markdown files, Claude Code plugin system

---

## Root Cause Summary

Token burn comes from multiplicative effects:
- **CLAUDE.md duplication**: 6 sections (~60 lines) are verbatim in both `~/.claude/CLAUDE.md` and project `CLAUDE.md`. Both load in every context including subagents.
- **Kanban Entry Format**: Identical 22-line section copy-pasted into 5 skills. Loaded every time any of those skills is invoked.
- **Verbose skill files**: The top 5 skills total 2,607 lines. Some sections (rationalizations tables, red flag lists) repeat structural patterns across skills without adding unique value proportional to their size.

**What we're NOT changing** (because it would risk losing effectiveness):
- Critique checklists — the 5 checklist files have intentionally different domain-specific criteria (software vs business vs design). They are NOT duplicates.
- Critic persona prompts — the Architect/Verifier prompts in writing-plans are detailed but that detail drives critique quality.
- Subagent count — reducing critics per round would lower review coverage.
- Skill list injection — this is a Claude Code platform behavior outside our control.

---

### Task 1: Deduplicate project CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (project root)

**Step 1: Remove the 6 duplicated sections from project CLAUDE.md**

The following sections exist verbatim in both `~/.claude/CLAUDE.md` and `CLAUDE.md`. Remove them from the project file, keeping only project-specific content.

**Sections to remove from project CLAUDE.md:**

1. **Bash Tool Restrictions** (lines 46-53) — verbatim copy of global lines 11-18
2. **Communication Style** (lines 55-57) — verbatim copy of global lines 20-22
3. **Testing** (lines 59-63) — near-verbatim copy of global lines 24-28 (only difference: path reference `skills/test-driven-development/testing-anti-patterns.md` vs `~/.claude/skills/test-driven-development/testing-anti-patterns.md`, but since the project CLAUDE.md loads in the project context, the global path is sufficient)
4. **Auto-Critique for Design Documents** (lines 65-67) — verbatim copy of global lines 45-47
5. **Git Commits** (lines 69-71) — verbatim copy of global lines 49-51
6. **Verification Discipline** (lines 82-100) — verbatim copy of global lines 68-86

**Resulting project CLAUDE.md should contain only these sections:**
- Header: "Aligned — Claude Code Skills Plugin"
- Path Rule
- Skill Anatomy
- Cross-References
- Adding a Skill
- Version
- What NOT to Duplicate
- Hook-Triggered Audits (project-specific: Error diagnosis + EVAL AUDIT hooks only)

**Step 2: Verify the file is valid markdown**

Run: `cat CLAUDE.md | head -5` (visually confirm header is intact)

**Step 3: Run git diff to verify only duplicated sections were removed**

Run: `git diff CLAUDE.md`

Expected: Only the 6 duplicated sections removed, project-specific content preserved.

**Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "chore: deduplicate CLAUDE.md — remove sections already in global"
```

---

### Task 2: Create shared Kanban Entry Format reference

**Files:**
- Create: `skills/_shared/kanban-entry-format.md`

**Step 1: Write `skills/_shared/kanban-entry-format.md`**

The directory will be created automatically when the file is written. Extract the Kanban Entry Format section that is currently duplicated in 5 skills.

Content for `skills/_shared/kanban-entry-format.md`:

```markdown
# Kanban Entry Format

When filing an entry to the Kanban board:

1. Read `docs/kanban/.counter` for the next KB number (pad to 3 digits)
2. Derive a kebab-case slug from the title (max 50 chars)
3. Write `docs/kanban/todo/KB-NNN-slug.md`:

```markdown
# KB-NNN: [Title]

- **Type:** bug
- **Discovered during:** [skill-name]
- **Location:** `[file path]:[line range]`
- **Observed:** [What exists and why it's a problem]
- **Expected:** [What should change]
- **Why out of scope:** [Why it wasn't fixed when discovered]
- **Severity:** LOW | MEDIUM | HIGH
- **Created:** [today's date]
```

4. Write the incremented number back to `docs/kanban/.counter`
```

Note: The `Discovered during` field uses `[skill-name]` as a placeholder — the referencing skill should fill in its own name when filing entries.

**Step 2: Verify `_shared/` does not appear as a skill**

The `_shared/` directory has no `SKILL.md` file, so the Claude Code plugin system should not register it as a skill. Confirm by checking that `skills/_shared/SKILL.md` does not exist (it shouldn't — we only created `kanban-entry-format.md`). If for any reason the directory is picked up as a skill, move the file to `docs/_shared/kanban-entry-format.md` instead (outside the `skills/` tree).

**Step 3: Commit the shared file**

```bash
git add skills/_shared/kanban-entry-format.md
git commit -m "chore: extract shared Kanban entry format to _shared/"
```

---

### Task 3: Replace inline Kanban sections with references

**Files:**
- Modify: `skills/writing-plans/SKILL.md` (~lines 418-439)
- Modify: `skills/executing-plans/SKILL.md` (~lines 161-182)
- Modify: `skills/finishing-a-development-branch/SKILL.md` (~lines 670-691)
- Modify: `skills/systematic-debugging/SKILL.md` (~lines 330-351)
- Modify: `skills/eval-audit/SKILL.md` (~lines 79-100)

**Step 0: Verify all 5 Kanban sections are structurally identical before extracting**

Read the Kanban Entry Format section in all 5 files. Confirm the template body is identical (the only expected difference is the `Discovered during` value — each skill hard-codes its own name). If any file has a structural difference beyond the skill name, note it and adjust the shared template accordingly.

**Step 1: In each of the 5 files, replace the full Kanban Entry Format section with a skill-specific reference**

Replace the entire `## Kanban Entry Format` section (heading through the final line about `.counter`) with a reference that embeds at the workflow point where KB entries are filed. Each skill gets a slightly different replacement to preserve its current `Discovered during` value:

For `writing-plans/SKILL.md`, `finishing-a-development-branch/SKILL.md`, `systematic-debugging/SKILL.md`, and `eval-audit/SKILL.md`:
```markdown
## Kanban Entry Format

When filing a Kanban entry, read `skills/_shared/kanban-entry-format.md` for the template and counter instructions. Use `writing-plans` as the "Discovered during" value.
```
(Replace `writing-plans` with the actual skill name in each file: `finishing-a-development-branch`, `systematic-debugging`, `eval-audit`.)

For `executing-plans/SKILL.md` (which currently uses a more specific format):
```markdown
## Kanban Entry Format

When filing a Kanban entry, read `skills/_shared/kanban-entry-format.md` for the template and counter instructions. Use `[plan filename / Task N]` as the "Discovered during" value (more specific than just the skill name).
```

This is 3 lines instead of 22 lines per file = 95 lines saved across 5 skills. The `Discovered during` values remain static (not runtime-substituted), matching the current behavior.

**Step 2: Verify each file still has the Kanban section header**

Use the Grep tool to search for `Kanban Entry Format` in `skills/*/SKILL.md` with output mode `files_with_matches`.

Expected: All 5 files still match.

**Step 3: Verify the shared file reference is correct**

Use the Grep tool to search for `_shared/kanban-entry-format` in `skills/*/SKILL.md` with output mode `files_with_matches`.

Expected: All 5 files reference the shared file.

**Step 4: Commit**

```bash
git add skills/writing-plans/SKILL.md skills/executing-plans/SKILL.md skills/finishing-a-development-branch/SKILL.md skills/systematic-debugging/SKILL.md skills/eval-audit/SKILL.md
git commit -m "chore: replace inline Kanban sections with shared reference"
```

---

### Task 4: Condense rationalizations tables in top 3 skills

**Files:**
- Modify: `skills/test-driven-development/SKILL.md` (lines ~258-272)
- Modify: `skills/systematic-debugging/SKILL.md` (lines ~296-307)
- Modify: `skills/create-new-skill/SKILL.md` (lines ~453-466)

**Step 1: Read each rationalizations table to identify entries**

Read the "Common Rationalizations" table in each of the 3 files. Identify which entries are the most unique/valuable and which are redundant with the Red Flags or other sections in the same skill.

**Step 2: Trim each table to the top 4 most impactful entries**

For each skill, keep the 4 entries that are most domain-specific and actionable. Remove entries that just restate the skill's core principle in different words. The goal is to keep the behavioral nudge while cutting redundant rows.

**Guidelines per skill:**
- `test-driven-development`: Keep entries about skipping tests, testing after implementation, emergency shortcuts, and "obvious code doesn't need tests". Remove entries that overlap with the Red Flags section.
- `systematic-debugging`: Keep entries about "issue is simple", "emergency/no time", "I see the problem", and "one more fix attempt". Remove entries that overlap with the "Red Flags - STOP" section.
- `create-new-skill`: Keep entries most specific to skill creation. Remove generic ones covered by other skills.

**Step 3: Verify tables are valid markdown**

Visually confirm each table renders correctly (header row, separator, data rows).

**Step 4: Commit**

```bash
git add skills/test-driven-development/SKILL.md skills/systematic-debugging/SKILL.md skills/create-new-skill/SKILL.md
git commit -m "chore: condense rationalizations tables to top entries"
```

---

### Task 5: Trim Red Flags section overlap in systematic-debugging

**Prerequisite: Complete Task 4 first** — both modify `systematic-debugging/SKILL.md` and Task 5's Step 2 depends on Task 4's output.

**Files:**
- Modify: `skills/systematic-debugging/SKILL.md` (lines ~266-294)

**Step 1: Read the "Red Flags" and "your human partner's Signals" sections**

These two sections (lines ~266-294) partially overlap with the Common Rationalizations table and with each other. Read them to identify unique content vs. repetition.

**Step 2: Condense where there's overlap**

- The "Red Flags" list and the "Common Rationalizations" table both say "stop guessing, follow the process." After Task 4 trimmed the table, verify the remaining Red Flag bullets don't repeat the remaining table entries verbatim.
- If a Red Flag bullet says exactly the same thing as a rationalizations row, remove the less specific one.
- Keep all of "your human partner's Signals" — these are concrete external signals, not internal rationalizations.

**Step 3: Commit**

```bash
git add skills/systematic-debugging/SKILL.md
git commit -m "chore: remove Red Flags entries that overlap with rationalizations table"
```

---

### Task 6: Trim finishing-a-development-branch (700 lines)

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Read the full file and identify verbose sections**

At 700 lines, this is the largest skill. Read through and identify:
- Sections where examples are overly detailed for the instruction they illustrate
- Repeated warnings or emphasis that say the same thing multiple ways
- Sections that could be shortened without losing the actual decision logic

**Step 2: Condense identified sections**

Focus on:
- The deployment pitfall references — if sections inline content that's also in `references/deployment-pitfall-catalog.md`, replace with a reference
- Any option descriptions that repeat information from earlier sections
- Verbose step-by-step formatting where the steps are self-evident

**Constraint:** Do NOT remove any of the decision logic, option descriptions, or the core workflow. The skill's value is in guiding a complex multi-option decision. Only trim pure verbosity.

**Step 3: Verify the skill's decision flow is intact**

Read the modified file and confirm: all options (merge, deploy, cleanup, discard) are still fully described with their criteria and steps.

**Step 4: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "chore: trim verbosity in finishing-a-development-branch skill"
```

---

### Task 7: Trim create-new-skill (664 lines)

**Files:**
- Modify: `skills/create-new-skill/SKILL.md`

**Step 1: Read the full file and identify verbose sections**

At 664 lines, this is the second largest skill. Read through and identify:
- Extended examples that could be shortened while preserving the pattern they teach
- Sections that explain the same concept in multiple paragraphs when one would suffice
- Content that's also covered in supporting docs (`anthropic-best-practices.md`, `testing-skills-with-subagents.md`, `persuasion-principles.md`) and doesn't need to be inline

**Step 2: Condense identified sections**

Focus on:
- Replace any inline content that duplicates a supporting doc with a reference to read the doc
- Trim multi-paragraph explanations to their essential instruction
- Keep all templates, checklists, and structural guidance — these are the skill's core value

**Constraint:** Do NOT remove the TDD methodology, testing templates, or skill anatomy guidance. Only trim redundant explanations.

**Step 3: Verify the skill's workflow is intact**

Read the modified file and confirm: the full skill creation workflow (TDD approach, templates, testing, iteration) is still complete.

**Step 4: Commit**

```bash
git add skills/create-new-skill/SKILL.md
git commit -m "chore: trim verbosity in create-new-skill skill"
```

---

### ✅ Task 8: Update cross-references after restructuring

**Files:**
- Potentially modify: any file referencing the removed CLAUDE.md sections or the old Kanban format location

**Step 1: Search for references to removed content**

Use Grep to search all `skills/**/*.md` and `agents/*.md` for:
- References to the project CLAUDE.md sections that were removed (e.g., "See CLAUDE.md" for Bash restrictions, testing, etc.)
- References to inline Kanban format that now lives in `_shared/`

**Step 2: Update any broken references**

If any skill references a specific section of project CLAUDE.md that was removed, update the reference to point to the global CLAUDE.md or remove the reference if the instruction is already part of the global context.

**Step 3: Verify no broken cross-references remain**

Use the Grep tool to search for `CLAUDE.md` in `skills/` and `agents/` directories with output mode `content`. Verify all references are valid.

**Step 4: Commit (if changes were needed)**

Stage only the specific files modified in Step 2 by name (e.g., `git add skills/foo/SKILL.md agents/bar.md`). Do not use `git add -u` or `git add .`.

```bash
git add <each modified file by name>
git commit -m "chore: update cross-references after token optimization"
```

---

### Task 9: Verify plugin still loads correctly

**Step 1: Check that plugin.json is still valid**

Read `.claude-plugin/plugin.json` and verify it hasn't been modified.

**Step 2: Verify all SKILL.md files have valid frontmatter**

For each modified SKILL.md, verify the `---` frontmatter block is intact at the top of the file.

**Step 3: Bump version**

Update `.claude-plugin/plugin.json` version from `0.3.1` to `0.3.2`.

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 0.3.2 for token optimization"
```

---

## Token Savings Estimate

| Change | Lines Removed | Contexts Affected | Impact |
|--------|--------------|-------------------|--------|
| CLAUDE.md dedup | ~60 lines | Every session + every subagent | **High** — loaded in ALL contexts |
| Kanban extraction | ~95 lines (19 per skill × 5) | 5 skills | **Medium** — only loaded when skill invoked |
| Rationalizations trim | ~20-30 lines | 3 skills | **Low-Medium** |
| Red Flags trim | ~10-15 lines | 1 skill | **Low** |
| finishing-branch trim | ~50-100 lines | 1 skill | **Medium** |
| create-new-skill trim | ~50-100 lines | 1 skill | **Medium** |

**Conservative total: ~300-400 lines removed**, with the CLAUDE.md dedup having the highest multiplied impact because it affects every single context.

---

## What This Plan Does NOT Do (and why)

1. **Does not consolidate critique checklists** — the 5 checklist files have intentionally different criteria for different domains (software design, business design, design principles, software plans, business plans). Merging them would lose domain specificity.

2. **Does not shorten critic persona prompts** — the Architect and Verifier prompts in writing-plans are long but that detail is what makes critique effective. Shortening risks vague, unhelpful critique.

3. **Does not reduce subagent count** — critique quality depends on independent parallel evaluation. Cutting from 2 critics to 1 would reduce coverage.

4. **Does not address skill list injection** — this is a Claude Code platform behavior. The full skill list (~1,200 tokens) is injected into every message by the system, not by our plugin.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Where to deduplicate CLAUDE.md | Remove from project, keep in global | Remove from global, keep in project |
| 2 | How to share Kanban format | `_shared/` dir with Read reference | `@` auto-load reference; CLAUDE.md instruction |
| 3 | Critique checklist consolidation | Do not consolidate | Merge into 2-3 shared checklists with parameters |
| 4 | Rationalizations table approach | Trim to top 4 entries | Remove entirely; move to reference file |

### Appendix: Decision Details

#### Decision 1: Where to deduplicate CLAUDE.md
**Chose:** Remove duplicated sections from project CLAUDE.md, keep them in global `~/.claude/CLAUDE.md`.
**Why:** The global CLAUDE.md loads in every project. The project CLAUDE.md only loads in `aligned_cc_skills`. Since the instructions apply universally (Bash restrictions, testing, verification discipline, etc.), the global file is the canonical home. Removing from the project file means these instructions load once instead of twice when working in this repo. For other repos, nothing changes — they still get the global instructions.
**Alternatives rejected:**
- Remove from global, keep in project: Would break these instructions for every other repo the user works in. The global file is the correct canonical location for universal rules.

#### Decision 2: How to share Kanban Entry Format
**Chose:** Create `skills/_shared/kanban-entry-format.md` and replace inline sections with a skill-specific reference that embeds at the workflow point where KB entries are filed. Each skill's replacement preserves its hard-coded `Discovered during` value (no runtime substitution). The `executing-plans` skill retains its more specific `[plan filename / Task N]` format.
**Why:** This approach means the Kanban format is only loaded into context when the agent actually needs to file a KB entry (when it reads the referenced file). The SKILL.md stays short. The agent reads the shared file on-demand. The reference follows the codebase's established pattern of instructing reads at the point of need (e.g., `finishing-a-development-branch` line 46: "Read CLAUDE.md to determine the deployment platform"). The `_shared/` directory has no SKILL.md so won't register as a skill.
**Alternatives rejected:**
- `@` auto-load reference: Using `@kanban-entry-format.md` would auto-load the file into context when the skill is invoked — no savings over inline content.
- CLAUDE.md instruction: Adding Kanban format to CLAUDE.md would load it in every context, not just skills that need it. Worse than the current duplication.
- Generic `[skill-name]` placeholder: Would change `Discovered during` from static values to runtime-substituted, a behavioral regression. Especially problematic for `executing-plans` which uses a richer format than just the skill name.

#### Decision 3: Critique checklist consolidation
**Chose:** Do not consolidate the 5 checklist files.
**Why:** After reading all 5 files, they are NOT duplicates. Each has domain-specific criteria: the software design checklist evaluates architecture feasibility, YAGNI, and data flow. The business design checklist evaluates goal precision, root cause depth, and stakeholder coverage. The design principles checklist has 3 named critic voices (Steve Jobs, Senior Product Designer, CX Lead). Merging these would either lose domain specificity or require a complex parameterized template that's harder to maintain. The user explicitly said "I don't want to lose functionality or effectiveness."
**Alternatives rejected:**
- Merge into 2-3 shared checklists with parameters: Would require the skill to pass domain context to a generic checklist, adding complexity. The structural overlap (Instructions, Output Format, Important sections) saves ~30 lines per pair but risks making the checklists harder to evolve independently.

#### Decision 4: Rationalizations table approach
**Chose:** Trim each table from 8-11 entries to the top 4 most domain-specific entries.
**Why:** The tables serve a real purpose — they preempt rationalization patterns that lead to skill violations. But 8-11 entries per table means many entries are generic ("emergency means skip process") that overlap with Red Flags sections in the same skill. Keeping the 4 most unique/impactful entries preserves the behavioral nudge while cutting 40-60% of table length. This is the safest middle ground between "keep all" and "remove entirely."
**Alternatives rejected:**
- Remove entirely: These tables are a proven pattern for preventing skill violations. Removing them risks more frequent process skipping.
- Move to reference file: The tables work because they're visible when the skill loads. Making them on-demand defeats their purpose as preemptive reminders.
