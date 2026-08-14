# Superpowers Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove aligned's dev-workflow skills (superpowers replaces them), rescope brainstorming/root-cause-analysis/kickstart/eval-audit, and ship as release 0.33.0.

**Architecture:** This is a removal-and-rescope release across markdown skill files, four registry/manifest files, and the Python e2e test suite. Every task ends with the full test suite green and one commit, so the branch is always releasable. Spec: `docs/plans/2026-08-14-superpowers-split-design.md`.

**Tech Stack:** Markdown skills, YAML (trigger-map, eval-surface), Python/pytest (e2e/tests), JSON manifests.

## Global Constraints

- Test command (run from repo root): `python3 -m pytest e2e/tests -q`. Full suite must pass at the end of every task.
- Bash: single commands only — no `&&`, `|`, `;`, or `$()`. Use `git -C /Users/ericpage/software/aligned_cc_skills` if not already in the repo.
- Commits: plain `git commit -m "message"`, never heredoc. Multi-line messages use one quoted string.
- `docs/plans/` is gitignored but tracked by convention — irrelevant here; no task adds files there.
- Portability: any reference to superpowers skills in aligned files must be phrased conditionally ("if the superpowers plugin is installed"), never as a hard dependency.
- Do NOT touch: `scripts/autopilot/**` (stays broken pending port), `e2e/tests/test_autopilot_*.py`, `test_ralph_*.py`, `test_verify_branch_thin.py`, `test_execute_plan_no_halt_sentinel.py`, `test_halt_protocol.py`, `test_phase_contracts.py`, `test_lint_guard_enforcement.py` (they assert against autopilot script text, which is unchanged, and stay green).
- Do NOT delete: `skills/brainstorming/references/templates/software-template.html` (visualize-design and the shared visualization protocol use it), `skills/_shared/plan-manifest-format.md`, `skills/_shared/manual-deploy-artifact-catalog.md` (autopilot needs both for the port).
- `skills/create-design-principles/design-critique-checklist.md` is a separate copy from brainstorming's — it stays.
- Version 0.33.0 must land in BOTH `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

---

### Task 1: Preflight — stash unrelated changes, branch, baseline

**Files:**
- No file edits. Git state only.

**Interfaces:**
- Produces: branch `superpowers-split` with a clean tree and a recorded baseline test result all later tasks compare against.

- [ ] **Step 1: Check working tree state**

Run: `git status --short`
Expected dirty files (unrelated in-progress work): `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, `docs/advisor-catalog.html`, `docs/framework-catalog.html`, `frameworks/registry.yaml`. If OTHER files are also dirty, stop and ask Eric before stashing.

- [ ] **Step 2: Stash the unrelated changes**

Run: `git stash push -m "pre-superpowers-split WIP (manifests, catalogs, registry)"`
Expected: stash created; `git status --short` now clean.

- [ ] **Step 3: Create the branch**

Run: `git checkout -b superpowers-split`

- [ ] **Step 4: Baseline test run**

Run: `python3 -m pytest e2e/tests -q`
Expected: PASS (record the count). If anything fails at baseline, record which tests — those failures are pre-existing and must not be "fixed" silently in later tasks; report them to Eric.

---

### Task 2: Rescope brainstorming to three modes (TDD)

**Files:**
- Modify: `e2e/tests/test_brainstorming_files.py`
- Rename: `e2e/fixtures/skill-prompts/brainstorming-four-modes.md` → `brainstorming-three-modes.md`
- Rename: `e2e/scenarios/use-skill/brainstorming-four-modes.yaml` → `brainstorming-three-modes.yaml`
- Delete: `e2e/scenarios/use-skill/brainstorming-five-modes.yaml` (already-retired scenario; its fixture `brainstorming-five-modes.md` doesn't exist)
- Modify: `e2e/trigger-map.yaml:48-52`, `e2e/eval-surface.yaml:17`
- Delete: `skills/brainstorming/modes/software.md`, `skills/brainstorming/design-critique-checklist.md`
- Modify: `skills/brainstorming/SKILL.md`, `skills/brainstorming/modes/roadmap.md:100`, `skills/brainstorming/modes/authoring.md:5,182,184`, `skills/brainstorming/modes/research.md:209`, `skills/brainstorming/references/spawn-brief-template.md:23-27`, `skills/brainstorming/references/brainstorm-components.md:104`, `skills/kickstart/SKILL.md` (the "four modes" marketing copy near the top — found via grep)

**Interfaces:**
- Produces: the name `brainstorming-three-modes` (fixture + scenario), used by trigger-map and tests. The routing-out sentence pattern for software requests, reused verbatim by Tasks 3–4: *"Software design and implementation are out of scope for this plugin. If the superpowers plugin is installed, use `superpowers:brainstorming`; otherwise install a dev-workflow plugin."*

- [ ] **Step 1: Update tests to expect three modes (make them fail first)**

In `e2e/tests/test_brainstorming_files.py`:
- Delete tests that exist solely to check software mode: `test_software_mode_critique_config_unchanged` (line ~379), `test_software_mode_nested_subtabs_reference` (line ~693), and any other test whose body reads `modes/software.md` (find them: `grep -n "modes/software.md" e2e/tests/test_brainstorming_files.py`).
- Rename `test_skill_md_description_names_four_modes` → `..._three_modes`; change the loop list to `["authoring", "research", "roadmap"]` and add `assert "software" not in text.lower()` scoped to the frontmatter description line.
- Rename `test_skill_md_overview_describes_four_modes` → `..._three_modes`; expect three bullet lines, none mentioning Software as a mode.
- Rename `test_skill_md_step1_has_four_signal_sets_and_always_ask` → `..._three_signal_sets_and_always_ask`; expect signal blocks for Authoring/Research/Roadmap plus a software routing-out block (assert the text `superpowers:brainstorming` appears in SKILL.md).
- Update the mode-table structural test (lines ~288-320): three rows, no `modes/software.md`, no `**If software mode:**`.
- Rename `test_four_modes_fixture_exists_and_lists_four_modes` and `test_four_modes_eval_fixture_lists_briefs` to `three_modes` variants; point at the renamed files; mode list `["research", "authoring", "roadmap"]`; add `software` to the retired-modes assertion (the loop asserting retired modes are absent).
- Update the scenario-name list at line ~444 to `brainstorming-three-modes.yaml`.
- Update `test_references_describe_four_modes_post_collapse` (line ~610) to three modes.
- Update `test_kickstart_marketing_copy_mentions_four_modes` (line ~352): assert `"three modes"` and `assert "four modes" not in text.lower()`.
- Line ~81 comment says the canonical mode-file comment "matches modes/software.md:1" — repoint the comparison to `modes/authoring.md:1` (verify that file carries the same canonical first-line comment before repointing; if the comment only exists in software.md, copy the assertion's expected string from authoring.md's actual first line).
- Lines ~485/491/618 reference `/aligned:writing-plans` as an allowed exception — remove the exception; after this task no brainstorming file may reference `/aligned:writing-plans` (assert absence instead).
- Line ~628 template test: keep `software-template.html` in the expected template list (the file stays).

- [ ] **Step 2: Run the file to verify the new expectations fail**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py -q`
Expected: FAIL (three-modes assertions against still-four-modes skill files).

- [ ] **Step 3: Rename fixture and scenario, delete stale scenario**

Run: `git mv e2e/fixtures/skill-prompts/brainstorming-four-modes.md e2e/fixtures/skill-prompts/brainstorming-three-modes.md`
Run: `git mv e2e/scenarios/use-skill/brainstorming-four-modes.yaml e2e/scenarios/use-skill/brainstorming-three-modes.yaml`
Run: `git rm e2e/scenarios/use-skill/brainstorming-five-modes.yaml`
Then edit `brainstorming-three-modes.yaml`: header comment and `description` say three-mode classifier; prompt text says "one of the three brainstorming modes (research, authoring, roadmap)" and "3-way picker"; rubric says all three labels ("Write a document", "Synthesize research", "Break a big intent into a queue of brainstorms"); delete the `software: API endpoint design` test case; `file://` paths point at `brainstorming-three-modes.md`. Edit the fixture `brainstorming-three-modes.md` the same way: strip the software-mode section, keep the other three (it's an excerpt of SKILL.md — regenerate it from the edited SKILL.md after Step 5 if it embeds the detection blocks verbatim).

- [ ] **Step 4: Update trigger-map and eval-surface**

`e2e/trigger-map.yaml` lines 48-52: the entry's paths keep `skills/brainstorming/SKILL.md` and `modes/authoring.md`; scenario list now `scenarios/use-skill/brainstorming-positioning.yaml` and `scenarios/use-skill/brainstorming-three-modes.yaml`.
`e2e/eval-surface.yaml`: delete line 17 (`skills/brainstorming/modes/software.md`).

- [ ] **Step 5: Edit the brainstorming skill files**

Delete: `git rm skills/brainstorming/modes/software.md skills/brainstorming/design-critique-checklist.md`

`skills/brainstorming/SKILL.md`:
- Frontmatter description → `"Structures creative and strategic work through guided dialogue across three modes — content authoring, research synthesis, and roadmap-mode decomposition of a big intent into a queue of brainstorms. Use before authoring, research, or roadmap work that benefits from structured exploration and expert critique. Software design routes to a dev-workflow plugin such as superpowers."`
- Overview: "Three modes"; delete the Software bullet.
- Step 1: replace the whole **Software mode** detection block with:

```markdown
**Software requests route out.** If the request is designing or building
software (features, components, APIs, refactoring, architecture,
implementation, code, data models — anything shaped as "build / design /
refactor X"): software design and implementation are out of scope for this
plugin. If the superpowers plugin is installed, use
`superpowers:brainstorming`; otherwise install a dev-workflow plugin.
Exception: *diagnosing why an existing system isn't behaving as expected*
("why don't I see the new onboarding flow", "why isn't X firing") stays
here — route to Authoring with the `root-cause-analysis` framework.
```

- Picker: three labels (drop "Design a code change"); text "3-way picker"; `--mode authoring|research|roadmap`.
- Disambiguation Rules: replace the two "Software vs Authoring" rules with one "Code-design vs Authoring" rule using the same content-vs-code and diagnostic tests but routing the code-design side to superpowers per the block above. Keep Authoring-vs-Research and Authoring-vs-Roadmap unchanged. In the refusal-handling paragraph, "all 4 modes" → "all 3 modes".
- Step 2 emphasis table and Step 3 mode/checklist table: delete the Software rows.

Other files:
- `modes/roadmap.md:100`: "That brainstorm produces a design doc" sentence — replace the `/aligned:writing-plans` clause with: "build-shaped components continue in a dev-workflow plugin (`superpowers:brainstorming` → `superpowers:writing-plans` if installed)."
- `modes/authoring.md:5`: "Produces a design doc that feeds `/aligned:writing-plans`." → "Produces a sequenced design doc."
- `modes/authoring.md:182,184` (handoff column): "Run /aligned:writing-plans against this doc…" → "If the work needs an implementation plan and the superpowers plugin is installed, run superpowers:writing-plans against this doc."
- `modes/research.md:209`: "Research mode has no `/aligned:writing-plans` follow-on." → "Research mode has no plan-writing follow-on."
- `references/spawn-brief-template.md:23-27`: rewrite the chain as *spawn-list component → /aligned:brainstorming → design doc → (build-shaped components only, superpowers plugin) superpowers:writing-plans → implementation plan*; keep the note that Research/Authoring components terminate at the design doc.
- `references/brainstorm-components.md:104`: delete the Software row of the mode→template table; keep the font note (the template file still exists).
- `skills/kickstart/SKILL.md`: find the "four modes" copy (`grep -n "four modes" skills/kickstart/SKILL.md`) and change to "three modes".
- Sweep: `grep -rn "modes/software" skills/` must return zero hits; `grep -rn "design-critique-checklist" skills/brainstorming/` must return zero hits.

- [ ] **Step 6: Run the full suite**

Run: `python3 -m pytest e2e/tests -q`
Expected: PASS. (`test_authoring_mode_resolver.py`, `test_research_mode_resolver.py`, `test_brainstorming_handoff.py`, `test_brainstorm_widgets.py`, `test_fixtures.py`, `test_trigger_map_*.py` also exercise these files — if any fail, fix the same way: three modes, no software references.)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(brainstorming)!: drop software mode; route software design to superpowers"
```

---

### Task 3: Rescope root-cause-analysis to business/process problems (TDD)

**Files:**
- Modify: `skills/root-cause-analysis/SKILL.md`, `skills/root-cause-analysis/post-fix-review-prompt.md` (if it carries code-bug language — check)
- Test: none exist for RCA content; verification is grep + suite.

**Interfaces:**
- Consumes: the routing-out sentence pattern from Task 2, adapted: code bugs → `superpowers:systematic-debugging`.

- [ ] **Step 1: Edit SKILL.md**

- Frontmatter description → `"Use when a business or process problem isn't resolving — a deliverable that isn't landing, a strategy not producing results, a process breakdown. Supports low (default) and high severity with multi-agent investigation. Code bugs and test failures are out of scope; use a dev-workflow plugin such as superpowers (systematic-debugging)."`
- "When to Use" section: delete the **Software:** bullet list (lines 30-36). Above the **Business:** list add:

```markdown
**Code bugs, test failures, and build breakage are out of scope.** If the
superpowers plugin is installed, use `superpowers:systematic-debugging`
for those; otherwise use your dev-workflow plugin's debugging skill.
```

- Sweep the rest of the file: `grep -n "test failure\|bug\|build\|software\|production" skills/root-cause-analysis/SKILL.md skills/root-cause-analysis/post-fix-review-prompt.md` — rewrite each remaining code-flavored example or instruction in business/process terms, or delete it. The Iron Law, severity levels, and phase structure stay.

- [ ] **Step 2: Run the suite**

Run: `python3 -m pytest e2e/tests -q`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(root-cause-analysis)!: rescope to business/process problems"
```

---

### Task 4: Update kickstart and eval-audit handoffs

**Files:**
- Modify: `skills/kickstart/templates/software.md:46-56`, `skills/eval-audit/SKILL.md:66,89`
- Not modified: `skills/kickstart/templates/business.md` (its `/aligned:root-cause-analysis` reference is business-context and stays), all kanban scaffolding in `skills/kickstart/SKILL.md`.

- [ ] **Step 1: Rewrite the software template's Workflows block**

Replace lines 46-56 of `skills/kickstart/templates/software.md` with:

````markdown
## Section 6 — Workflows

```markdown
## Workflows

- `/aligned:brainstorming` — before authoring, research, or roadmap work
- `/aligned:create-design-principles` — to define design direction
- `/aligned:eval-audit` — to check eval coverage

If the superpowers plugin is installed, use it for the development loop:

- `superpowers:brainstorming` — before designing features
- `superpowers:writing-plans` — before implementation
- `superpowers:executing-plans` — to implement a plan
- `superpowers:finishing-a-development-branch` — to complete work
- `superpowers:systematic-debugging` — before fixing any bug
```
````

- [ ] **Step 2: Update eval-audit**

- Line 66: "If yes, kick off the eval scenario creation work — if the superpowers plugin is installed, use `superpowers:writing-plans` → `superpowers:executing-plans`; otherwise create the scenarios directly in this session."
- Line 89: delete the `**executing-plans**` integration row.

- [ ] **Step 3: Run suite, commit**

Run: `python3 -m pytest e2e/tests -q` — expected PASS.

```bash
git add -A
git commit -m "feat(kickstart,eval-audit): hand dev workflows to superpowers when installed"
```

---

### Task 5: Delete the dev-workflow skills, agents, hook, and their test/e2e surface

**Files:**
- Delete dirs: `skills/writing-plans/`, `skills/executing-plans/`, `skills/finishing-a-development-branch/`, `skills/using-git-worktrees/`, `skills/kanban-resolve/`, `skills/codebase-audit/`
- Delete: `agents/code-reviewer.md`, `agents/code-simplifier.md`, `agents/kanban-triage.md`, `agents/doc-staleness-detector.md`, `hooks/auto-approve-worktrees.js`
- Delete: `e2e/tests/test_writing_plans_anti_review.py`, `test_writing_plans_manifest_authoring.py`, `test_skill_cross_references.py`, `test_critique_buildability_criterion.py`, `test_manual_deploy_integration.py`, `e2e/scenarios/manual-deploy/` (whole dir)
- Modify: `e2e/trigger-map.yaml:149-153`, `e2e/eval-surface.yaml:25-26`, `README.md` (tables), `CLAUDE.md` (Path Rule example), `skills/_shared/plan-manifest-format.md`, `skills/_shared/manual-deploy-artifact-catalog.md`, `skills/_shared/critique-panel-orchestration.md:65`

**Interfaces:**
- Produces: a repo where `grep -rn` for any removed skill name returns hits only in `docs/`, `scripts/autopilot/`, autopilot tests, and the README changelog. Task 6's changelog relies on the exact removal list above.

- [ ] **Step 1: Delete tests for removed behavior first**

Run: `git rm e2e/tests/test_writing_plans_anti_review.py e2e/tests/test_writing_plans_manifest_authoring.py e2e/tests/test_skill_cross_references.py e2e/tests/test_critique_buildability_criterion.py e2e/tests/test_manual_deploy_integration.py`
Before deleting `test_manual_deploy_integration.py`, confirm `test_manual_deploy_catalog.py` covers the kept `_shared` catalog on its own (`grep -n "finishing\|writing-plans" e2e/tests/test_manual_deploy_catalog.py` → expect zero hits; if it has hits, trim those assertions instead of leaving them).

- [ ] **Step 2: Delete the skills, agents, hook, scenario dir**

Run: `git rm -r skills/writing-plans skills/executing-plans skills/finishing-a-development-branch skills/using-git-worktrees skills/kanban-resolve skills/codebase-audit e2e/scenarios/manual-deploy`
Run: `git rm agents/code-reviewer.md agents/code-simplifier.md agents/kanban-triage.md agents/doc-staleness-detector.md hooks/auto-approve-worktrees.js`

- [ ] **Step 3: Update trigger-map and eval-surface**

- `e2e/trigger-map.yaml`: delete the entry at lines 149-153 (paths `skills/writing-plans/SKILL.md` + `skills/_shared/manual-deploy-artifact-catalog.md` → manual-deploy scenario). Update the header comment at line 3 ("Consumer: finishing-a-development-branch Step 1b") to "Consumer: eval-audit Phase 3 cross-validation".
- `e2e/eval-surface.yaml`: delete lines 25-26 (`skills/writing-plans/SKILL.md`, `skills/finishing-a-development-branch/SKILL.md`). Keep line 27 (the `_shared` catalog — eval-audit still audits it). Update the header comment at line 3 to "Consumers: eval-audit Phase 1".

- [ ] **Step 4: Update README tables and CLAUDE.md**

`README.md`:
- Skill table: delete rows for `codebase-audit` (91), `kanban-resolve` (94), `writing-plans` (95), `executing-plans` (96), `finishing-a-development-branch` (97), `using-git-worktrees` (98).
- Row 92 (`root-cause-analysis`) description → "Root cause investigation for business and process problems with optional multi-agent mode".
- Agents table: delete rows 114 (`code-reviewer`), 115 (`code-simplifier`), 118 (`kanban-triage`), 121 (`doc-staleness-detector`).
- Hooks table: delete row 128 (`auto-approve-worktrees.js`).
- Line 200 (manual-deploy catalog note): "Consumed by the autopilot pipeline (currently non-functional pending its port to superpowers skills)."
- Scan the rest of README (`grep -n` for each removed name) — pipeline diagrams or prose sections describing the plan→execute→finish flow get deleted or rewritten to say the development loop now lives in the superpowers plugin. Changelog history entries stay untouched.

`CLAUDE.md` (repo): the Path Rule example `skills/brainstorming/design-critique-checklist.md` → `skills/brainstorming/roadmap-critique-checklist.md`.

- [ ] **Step 5: Update kept _shared files**

- `plan-manifest-format.md` and `manual-deploy-artifact-catalog.md`: add one line under the title: `> Retained for scripts/autopilot, which is non-functional pending its port to superpowers skills (see README changelog 0.33.0).` In `manual-deploy-artifact-catalog.md`, delete the sentence comparing it to `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md` (that file no longer exists) and delete the "Consumed by skills/writing-plans/SKILL.md …" sentence in favor of the autopilot note.
- `critique-panel-orchestration.md:65`: remove the `plan-critique-checklist.md` Crit 11 mention from the YAGNI exception (keep the `design-critique-checklist.md` Crit 3 + 8 part — create-design-principles still uses that checklist).

- [ ] **Step 6: Reference sweep**

Run: `grep -rn "writing-plans" skills agents hooks e2e README.md CLAUDE.md`
Repeat for: `executing-plans`, `finishing-a-development-branch`, `using-git-worktrees`, `kanban-resolve`, `codebase-audit`, `code-reviewer`, `code-simplifier`, `kanban-triage`, `doc-staleness`.
Expected: only hits are (a) `superpowers:` prefixed, (b) README changelog history, (c) autopilot-note lines added above, (d) `e2e/tests/test_autopilot_*` / `test_ralph_*` / `test_verify_branch_thin.py` assertions about autopilot script text. Anything else gets fixed now.

- [ ] **Step 7: Run the full suite**

Run: `python3 -m pytest e2e/tests -q`
Expected: PASS. Likely stragglers: `test_readme_freshness.py` (README table vs filesystem — should now agree), `test_trigger_map_paths.py` / `test_trigger_map_scenarios.py` (paths and scenarios must all exist), `test_contextual_recommendation.py` and `test_shared_runners.py` (may enumerate skills — update their expected lists to the surviving skills), `test_qa_pattern_parity.py`. Fix by updating expectations to the new skill set, never by re-adding removed files.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat!: remove dev-workflow skills, agents, and worktree hook (superpowers replaces them)"
```

---

### Task 6: Version 0.33.0, descriptions, changelog

**Files:**
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `README.md`

- [ ] **Step 1: Bump versions and descriptions**

Both manifests → `"version": "0.33.0"`. `plugin.json` description → `"Skill stack for Claude Code: brainstorming, structured thinking, 60 advisor personas, 116 frameworks, persona panels, brand content generation"` (verify the advisor/framework counts against `advisors/registry.yaml` and `frameworks/registry.yaml` before writing them — the stash from Task 1 contains registry changes, so counts may differ from what's on the branch). Apply the same description to marketplace.json's plugin entry. Keywords: drop `"tdd"` and `"pipeline"`.

- [ ] **Step 2: Write the changelog entry**

Add to README changelog, dated 2026-08-14, version 0.33.0:

```markdown
- **BREAKING:** Removed the dev-workflow skills — the superpowers plugin
  (github.com/obra/superpowers) replaces them: `writing-plans`,
  `executing-plans`, `finishing-a-development-branch`,
  `using-git-worktrees` (same names in superpowers), `kanban-resolve` and
  `codebase-audit` (no replacement). Removed agents: `code-reviewer`,
  `code-simplifier`, `kanban-triage`, `doc-staleness-detector`. Removed
  hook: `auto-approve-worktrees.js`.
- **BREAKING:** `brainstorming` is now three modes (authoring, research,
  roadmap); software design routes to `superpowers:brainstorming`.
- **BREAKING:** `root-cause-analysis` now covers business/process problems
  only; code bugs route to `superpowers:systematic-debugging`.
- Autopilot (`scripts/autopilot/`) is non-functional in this release — it
  drove the removed skills. A follow-up release ports it to superpowers.
```

Also update the skill-count line if the changelog convention tracks it (previous entries do: "25 skills", "26 skills") — count `ls skills` minus `_shared`.

- [ ] **Step 3: Run suite, commit**

Run: `python3 -m pytest e2e/tests -q` — expected PASS (`test_readme_freshness.py` in particular).

```bash
git add -A
git commit -m "chore(release): 0.33.0 — aligned narrows to advisors, frameworks, and content"
```

---

### Task 7: Final verification

- [ ] **Step 1: Full suite**

Run: `python3 -m pytest e2e/tests -q`
Expected: PASS, count reconciled against the Task 1 baseline (baseline minus deleted test files' tests, plus any renamed).

- [ ] **Step 2: Portability audit**

Invoke the `portability-audit` skill (repo-local). Expected: no new findings introduced by this branch.

- [ ] **Step 3: Manifest sync check**

Run: `grep -n "0.33.0" .claude-plugin/plugin.json .claude-plugin/marketplace.json`
Expected: one hit in each.

- [ ] **Step 4: Live-reference sweep (release gate)**

Repeat Task 5 Step 6's greps. Expected: same result — no live references.

---

### Task 8: Eric's local config (outside the repo — do NOT commit to this repo)

**Files:**
- Modify: `/Users/ericpage/.claude/CLAUDE.md`

- [ ] **Step 1: Update the RCA rule and add routing**

In "Root Cause First, Never Symptom-Fix": replace "When the user pastes an error and wants it addressed, run `/aligned:root-cause-analysis` before diagnosing inline or proposing fixes." with "When the user pastes an error and wants it addressed, use `superpowers:systematic-debugging` before diagnosing inline or proposing fixes. For business or process problems that aren't resolving, use `/aligned:root-cause-analysis`."

Add a short section:

```markdown
## Plugin Routing

Software development work (design, plans, implementation, debugging, code
review, branch finishing) uses superpowers skills. Advisors, frameworks,
content, personas, and other non-dev work use aligned skills.
```

- [ ] **Step 2: Done — report**

No commit (personal global file, not a repo deliverable). Report the edit to Eric.

---

## Post-release follow-up (separate effort, not in this plan)

Port `scripts/autopilot/` to drive superpowers skills; un-stash the Task 1 WIP (`git stash pop`) after merging back to main.
