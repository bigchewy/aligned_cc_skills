# Port Remaining Skills, Agents & Archive Local Duplicates

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Port 8 skills, 3 agents to the aligned plugin, enhance eval-failure-triage with unique content from eval-auto-triage, archive all local duplicates, and update settings.json.

**Source Design Doc:** N/A (migration continuation from v0.2.0 plugin parity work)

**Architecture:** Copy local skill/agent files into the plugin's `skills/` and `agents/` directories, applying the standard migration transforms (path prefixes, invocation namespaces, de-personalization, va-web-app generalization). Then archive all local duplicates to `/Users/ericpage/software/archived-claude-local/` and update `~/.claude/settings.json` to remove duplicate hooks and fix skill permission prefixes.

**Tech Stack:** Markdown files, shell scripts, git

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] Ensure you are on the `main` branch of `/Users/ericpage/software/aligned_cc_skills`
- [ ] Ensure working tree is clean (`git status` shows nothing to commit)

---

## Migration Transform Reference

Every ported file must have these transforms applied. This section is the canonical reference — do NOT deviate.

| Transform | From | To |
|-----------|------|----|
| Skill path prefix | `~/.claude/skills/` | `skills/` |
| Agent path prefix | `~/.claude/agents/` | `agents/` |
| Advisor path prefix | `~/.claude/advisors/` | `advisors/` |
| Framework path prefix | `~/.claude/frameworks/` | `frameworks/` |
| Skill invocation | `/skill-name` | `/aligned:skill-name` |
| Cross-skill bare name | `Use business-executing` | `Use /aligned:business-executing` |
| Personal name refs | `Eric`, `your human partner Eric` | `the user`, `your human partner` |
| Personal folder refs | `domains/aligned_consulting/`, `domains/[client]/` | `the project directory` or remove |
| va-web-app paths | `src/lib/advisors/registry.ts`, `public/avatars/` | Generic: "Read the project's CLAUDE.md to find the advisor registry location" |
| va-web-app eval refs | `e2e/scenarios/`, `npm run eval` | Generic: "If the project has an eval infrastructure (e.g., `e2e/` directory), create an eval scenario" |
| Stale self-refs | Wrong directory names in `~/.claude/skills/` paths | Correct plugin-relative paths |
| Filename case | `skill.md` (lowercase) | `SKILL.md` (uppercase) |

---

### Task 1: Port worktree-setup agent

**Files:**
- Create: `agents/worktree-setup.md`
- Source: `/Users/ericpage/.claude/agents/worktree-setup.md`

**Step 1: Copy the agent file**

Read `/Users/ericpage/.claude/agents/worktree-setup.md` in full. Write it to `agents/worktree-setup.md`. This agent has no `~/.claude/` path references and no project-specific content — it's already generic. Copy as-is.

**Step 2: Verify no stale references**

Run Grep for `~/.claude/` in the new file. Expected: 0 matches. The agent references only project-relative paths (`.worktrees/`, `.claude/settings.local.json`).

**Step 3: Commit**

```bash
git add agents/worktree-setup.md
git commit -m "feat: port worktree-setup agent to plugin"
```

---

### Task 2: Port 3 light-transform business skills

These skills need minimal changes: personal name refs and cross-skill invocations only.

**Files:**
- Create: `skills/business-diagnosis/SKILL.md`
- Create: `skills/business-executing/SKILL.md`
- Create: `skills/business-brainstorming/SKILL.md`
- Create: `skills/business-brainstorming/design-critique-checklist.md`
- Source: `/Users/ericpage/.claude/skills/business-diagnosis/SKILL.md`
- Source: `/Users/ericpage/.claude/skills/business-executing/SKILL.md`
- Source: `/Users/ericpage/.claude/skills/business-brainstorming/SKILL.md`
- Source: `/Users/ericpage/.claude/skills/business-brainstorming/design-critique-checklist.md`

**Step 1: Port business-diagnosis**

Read `/Users/ericpage/.claude/skills/business-diagnosis/SKILL.md`. Write to `skills/business-diagnosis/SKILL.md` with these transforms:
- Replace all references to "Eric" with "the user" (e.g., "Discuss with Eric" → "Discuss with the user")
- Replace `domains/` folder references with generic project directory language
- Verify frontmatter `name: business-diagnosis`

**Step 2: Port business-executing**

Read `/Users/ericpage/.claude/skills/business-executing/SKILL.md`. Write to `skills/business-executing/SKILL.md` with these transforms:
- `elements-of-style:writing-clearly-and-concisely` — leave as-is (it's a separate plugin invocation)
- `Use Business-Diagnosis` or similar bare references → `/aligned:business-diagnosis`
- Verify frontmatter `name: business-executing`

**Step 3: Port business-brainstorming (SKILL.md)**

Read `/Users/ericpage/.claude/skills/business-brainstorming/SKILL.md`. Write to `skills/business-brainstorming/SKILL.md` with these transforms:
- `~/.claude/skills/brainstorming/critic-registry.md` → `skills/brainstorming/critic-registry.md` (this file already exists in the plugin at this path)
- `~/.claude/skills/business-brainstorming/design-critique-checklist.md` → `skills/business-brainstorming/design-critique-checklist.md`
- Replace all "Eric" references with "the user"
- Replace `domains/aligned_consulting/` and `domains/[client]/` with generic project directory language
- `business-planning` or `business-write-plan` bare refs → `/aligned:business-write-plan`
- Verify frontmatter `name: business-brainstorming`

**Step 4: Copy business-brainstorming supporting file**

Read `/Users/ericpage/.claude/skills/business-brainstorming/design-critique-checklist.md`. Write to `skills/business-brainstorming/design-critique-checklist.md`. Verify no `~/.claude/` paths — if any exist, apply the transform table.

**Step 5: Verify cross-references resolve**

Run Grep across the 3 new skill directories for any remaining `~/.claude/` references. Expected: 0 matches.

**Step 6: Commit**

```bash
git add skills/business-diagnosis/ skills/business-executing/ skills/business-brainstorming/
git commit -m "feat: port business-diagnosis, business-executing, business-brainstorming skills"
```

---

### Task 3: Port business-write-plan skill

This skill has a stale internal path reference and personal references.

**Files:**
- Create: `skills/business-write-plan/SKILL.md`
- Create: `skills/business-write-plan/plan-critique-checklist.md`
- Source: `/Users/ericpage/.claude/skills/business-write-plan/SKILL.md`
- Source: `/Users/ericpage/.claude/skills/business-write-plan/plan-critique-checklist.md`

**Step 1: Port the SKILL.md**

Read `/Users/ericpage/.claude/skills/business-write-plan/SKILL.md`. Write to `skills/business-write-plan/SKILL.md` with these transforms:
- **CRITICAL stale path fix:** `~/.claude/skills/business-planning/plan-critique-checklist.md` → `skills/business-write-plan/plan-critique-checklist.md` (the local version has a wrong directory name — fix it during port)
- Replace all "Eric" references with "the user" (e.g., "Checkpoint with Eric" → "Checkpoint with the user")
- Replace `domains/[client]/` and `domains/aligned_consulting/` references with generic project directory language
- `REQUIRED SUB-SKILL: Use business-executing` → `REQUIRED SUB-SKILL: Use /aligned:business-executing`
- `elements-of-style:writing-clearly-and-concisely` — leave as-is
- Verify frontmatter `name: business-write-plan`

**Step 2: Copy supporting file**

Read `/Users/ericpage/.claude/skills/business-write-plan/plan-critique-checklist.md`. Write to `skills/business-write-plan/plan-critique-checklist.md`. Apply transform table to any `~/.claude/` paths.

**Step 3: Verify cross-references resolve**

Grep the new directory for `~/.claude/` and `business-planning` (the stale name). Expected: 0 matches for both.

**Step 4: Commit**

```bash
git add skills/business-write-plan/
git commit -m "feat: port business-write-plan skill (fix stale checklist path)"
```

---

### Task 4: Port find-potential-advisors skill

**Files:**
- Create: `skills/find-potential-advisors/SKILL.md`
- Source: `/Users/ericpage/.claude/skills/find-potential-advisors/SKILL.md`

**Step 1: Port the SKILL.md**

Read `/Users/ericpage/.claude/skills/find-potential-advisors/SKILL.md`. Write to `skills/find-potential-advisors/SKILL.md` with these transforms:
- `src/lib/advisors/` and `src/lib/frameworks/registry.ts` → Generic: "Read the project's CLAUDE.md or advisor registry to check for existing advisors in this domain"
- `docs/plans/YYYY-MM-DD-find-advisor-<domain>-brief.md` — keep as-is (generic output path)
- `/find-potential-advisors` → `/aligned:find-potential-advisors` in invocation examples
- `/add-advisor` → `/aligned:add-advisor` in Phase 6 closing prompt
- Verify frontmatter `name: find-potential-advisors`

**Step 2: Verify no stale references**

Grep for `~/.claude/` and `src/lib/advisors`. Expected: 0 matches.

**Step 3: Commit**

```bash
git add skills/find-potential-advisors/
git commit -m "feat: port find-potential-advisors skill"
```

---

### Task 5: Port create-design-principles skill

This skill has a filename case issue and stale self-references. **Note:** The plugin already has `skills/design-principles/` (interactive discovery session). `create-design-principles` is a different skill — it enforces a specific aesthetic (Linear/Notion/Stripe inspired, Jony Ive precision) rather than discovering design direction interactively. Both coexist: `design-principles` = discover, `create-design-principles` = enforce.

**Files:**
- Create: `skills/create-design-principles/SKILL.md` (note: uppercase SKILL.md)
- Create: `skills/create-design-principles/design-critique-checklist.md`
- Source: `/Users/ericpage/.claude/skills/create-design-principles/skill.md` (note: lowercase)
- Source: `/Users/ericpage/.claude/skills/create-design-principles/design-critique-checklist.md`

**Step 1: Port the SKILL.md (fix filename case)**

Read `/Users/ericpage/.claude/skills/create-design-principles/skill.md`. Write to `skills/create-design-principles/SKILL.md` (uppercase) with these transforms:
- `~/.claude/advisors/prompts/steve-jobs.md` → `advisors/va-web-app/steve-jobs.md` (confirmed: this is where the Steve Jobs advisor lives in the plugin)
- **CRITICAL stale path fix:** `~/.claude/skills/design-principles/design-critique-checklist.md` → `skills/create-design-principles/design-critique-checklist.md` (wrong directory name in source)
- Verify frontmatter `name: create-design-principles`

**Step 2: Port supporting file**

Read `/Users/ericpage/.claude/skills/create-design-principles/design-critique-checklist.md`. Write to `skills/create-design-principles/design-critique-checklist.md`. Apply transforms:
- `~/.claude/advisors/prompts/steve-jobs.md` → `advisors/va-web-app/steve-jobs.md`
- Any other `~/.claude/` references

**Step 3: Verify cross-references resolve**

Grep for `~/.claude/` and `design-principles/design-critique` (the stale partial path). Expected: 0 matches.

**Step 4: Commit**

```bash
git add skills/create-design-principles/
git commit -m "feat: port create-design-principles skill (fix filename case, stale paths)"
```

---

### Task 6: Port add-advisor skill

This is the heaviest transform. The skill has 9 `~/.claude/` references and va-web-app-specific infrastructure.

**Files:**
- Create: `skills/add-advisor/SKILL.md`
- Source: `/Users/ericpage/.claude/skills/add-advisor/SKILL.md`

**Step 1: Read and understand the local skill**

Read `/Users/ericpage/.claude/skills/add-advisor/SKILL.md` in full. Identify all 9 steps and which need transformation.

**Step 2: Port the SKILL.md**

Write to `skills/add-advisor/SKILL.md` with these transforms:

Path transforms:
- `~/.claude/advisors/prompts/va-web-app/diana-chapman.md` → `advisors/va-web-app/diana-chapman.md` (canonical example — verify path with Glob)
- `~/.claude/agents/references/eval-scenario-reference.md` → Remove this reference. The eval scenario reference is project-specific and not in the plugin. Replace the eval step with: "If the project has an eval infrastructure (e.g., `e2e/` directory), create an eval scenario for this advisor."

va-web-app generalization:
- `src/lib/advisors/registry.ts` → "the project's advisor registry file (check CLAUDE.md for location)"
- `public/avatars/` and `npm run avatar` → Make conditional: "If the project uses avatar images, generate one"
- `e2e/scenarios/` and `npm run eval` → Make conditional as above

Symlink infrastructure (Step 8):
- The `~/.claude/advisors/prompts/{repo-name}` symlink step and `.repos` manifest update are about making advisors discoverable across projects. In the plugin context, advisors live in `advisors/{repo-name}/`. Transform this step to: "Add the advisor file to `advisors/{repo-name}/` in the plugin directory. If the advisor is for a specific project and shouldn't be shared globally, add it to `~/.claude/advisors/prompts/{repo-name}/` instead (the user-extension directory)."

- `/add-advisor` → `/aligned:add-advisor` in invocation examples
- Verify frontmatter `name: add-advisor`

**Step 3: Verify cross-references resolve**

Grep for `~/.claude/` in the new file. The ONLY acceptable `~/.claude/` reference is in the user-extension directory instruction (Step 8 alternative path). All others should be plugin-relative.

**Step 4: Commit**

```bash
git add skills/add-advisor/
git commit -m "feat: port add-advisor skill (generalize va-web-app refs)"
```

---

### Task 7: Port add-framework skill

Similar to add-advisor — heavy va-web-app transforms.

**Files:**
- Create: `skills/add-framework/SKILL.md`
- Source: `/Users/ericpage/.claude/skills/add-framework/SKILL.md`

**Step 1: Read and port the SKILL.md**

Read `/Users/ericpage/.claude/skills/add-framework/SKILL.md`. Write to `skills/add-framework/SKILL.md` with these transforms:

Path transforms:
- `~/.claude/frameworks/prompts/va-web-app/clearing-model/prompt.md` → `frameworks/va-web-app/clearing-model/prompt.md` (verify with Glob)
- Same for `examples.md` and `anti-examples.md` references
- `~/.claude/frameworks/prompts/va-web-app/braving-trust-inventory/prompt.md` → `frameworks/va-web-app/braving-trust-inventory/prompt.md`
- `~/.claude/agents/references/eval-scenario-reference.md` → Remove; replace with conditional eval instruction (same as add-advisor)

va-web-app generalization:
- `src/lib/frameworks/registry.ts` → "the project's framework registry file (check CLAUDE.md for location)"
- `e2e/scenarios/`, `npm run eval`, `npm run build` → Make conditional

Symlink infrastructure (Step 7):
- Same approach as add-advisor: primary path is `frameworks/{repo-name}/` in plugin, alternative is `~/.claude/frameworks/prompts/{repo-name}/` for user extensions
- `~/.claude/frameworks/prompts/.repos` → mention only in the user-extension context

- Verify frontmatter `name: add-framework`

**Step 2: Verify cross-references resolve**

Grep for `~/.claude/` — only acceptable in user-extension instructions.

**Step 3: Commit**

```bash
git add skills/add-framework/
git commit -m "feat: port add-framework skill (generalize va-web-app refs)"
```

---

### Task 8: Port error-diagnosis agent

**Files:**
- Create: `agents/error-diagnosis.md`
- Source: `/Users/ericpage/.claude/agents/error-diagnosis.md`

**Step 1: Read and port the agent**

Read `/Users/ericpage/.claude/agents/error-diagnosis.md`. Write to `agents/error-diagnosis.md` with these transforms:
- `~/.claude/error-tracking/errors.jsonl` → `~/.claude/error-tracking/errors.jsonl` (KEEP — this is a user-home state file, not a plugin path. The error-tracker hook writes here regardless of plugin vs local.)
- `~/.claude/hooks/error-tracker.js` → `hooks/error-tracker.js` (plugin-relative reference to the hook script)
- `systematic-debugging` → `/aligned:systematic-debugging`
- `productivity-skills:code-auditor` — leave as-is (separate plugin)
- `productivity-skills:project-bootstrapper` — leave as-is

**Step 2: Verify references**

Grep for `~/.claude/` — only the `error-tracking/errors.jsonl` state file path should remain.

**Step 3: Wire invocation point in CLAUDE.md**

The error-diagnosis agent has never been used because nothing triggers it. Add a brief entry to `CLAUDE.md` under "Hook-Triggered Audits" (or a new section) that documents when to dispatch it:

Add to CLAUDE.md:
```
- **Error diagnosis:** When the `[CRON STATUS]` dashboard or `error-tracker.js` PostToolUse hook indicates accumulated errors, dispatch the `error-diagnosis` agent to classify patterns and identify root causes.
```

This completes the data pipeline: error-tracker.js (collection) → errors.jsonl (storage) → error-diagnosis agent (analysis).

**Step 4: Commit**

```bash
git add agents/error-diagnosis.md CLAUDE.md
git commit -m "feat: port error-diagnosis agent, wire invocation in CLAUDE.md"
```

---

### Task 9: Port artifact-verifier agent

The artifact-verifier adds unique value with its 98% accuracy gate and structured claim taxonomy. Port it as an agent that can be dispatched after critique rounds or for standalone artifact verification.

**Files:**
- Create: `agents/artifact-verifier.md`
- Source: `/Users/ericpage/.claude/agents/artifact-verifier.md`

**Step 1: Read and port the agent**

Read `/Users/ericpage/.claude/agents/artifact-verifier.md`. Write to `agents/artifact-verifier.md`. This agent has no `~/.claude/` path references — copy as-is. Verify frontmatter exists.

**Step 2: Verify no stale references**

Grep for `~/.claude/`. Expected: 0 matches.

**Step 3: Commit**

```bash
git add agents/artifact-verifier.md
git commit -m "feat: port artifact-verifier agent (98% accuracy gate for doc verification)"
```

---

### Task 10: Enhance eval-failure-triage with eval-auto-triage content

The eval-auto-triage agent is superseded, but it has two unique sections worth preserving: the infrastructure error detection table and the trend analysis block.

**Files:**
- Modify: `skills/eval-failure-triage/SKILL.md`
- Reference: `/Users/ericpage/.claude/agents/eval-auto-triage.md`

**Step 1: Read both files**

Read `/Users/ericpage/.claude/agents/eval-auto-triage.md` to extract the infrastructure error detection table and trend analysis section. Read `skills/eval-failure-triage/SKILL.md` to find where they fit.

**Step 2: Add infrastructure pre-check to Phase 1**

In the plugin's `skills/eval-failure-triage/SKILL.md`, add a "Step 0: Infrastructure Pre-Check" before the existing Phase 1 classification. Include the infrastructure error table from eval-auto-triage:

| Symptom | Classification | Fix |
|---------|---------------|-----|
| Runner crashed / timeout | Infrastructure | Check runner config, increase timeout |
| Sibling tool call errors | Infrastructure | Isolate eval scenarios, run sequentially |
| Missing CLI tools (jq, etc.) | Infrastructure | Install dependency or remove from eval |
| Judge output truncated | Infrastructure | Reduce response length or increase judge token limit |
| Incoherent judge reasoning | Calibration | Rewrite judge rubric with concrete examples |

**Step 3: Add trend analysis section**

Add a "Trend Analysis" section after the classification phase. Include patterns from eval-auto-triage:
- Same scenario failing across multiple runs → likely prompt issue
- Same dimension failing across scenarios → likely judge calibration
- Intermittent pass/fail → likely model variance
- New failures after prompt change → likely prompt regression

**Step 4: Verify the enhanced skill reads cleanly**

Read the modified file. Ensure the new sections integrate naturally with the existing flow.

**Step 5: Commit**

```bash
git add skills/eval-failure-triage/SKILL.md
git commit -m "feat: enhance eval-failure-triage with infrastructure pre-check and trend analysis"
```

---

### Task 11: Update README, CLAUDE.md, and plugin.json

**Depends on:** Tasks 1-10 (this task documents what was ported, so all ports must be complete first)

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `.claude-plugin/plugin.json`

**Step 1: Read current README.md**

Read `README.md` in full.

**Step 2: Update skill reference table**

Add 8 new skills to the skill reference table. Use these entries:

| Skill | Layer | Invocation | Description |
|-------|-------|------------|-------------|
| add-advisor | Advisor | `/aligned:add-advisor` | Add a new advisor to the Virtual Board |
| add-framework | Framework | `/aligned:add-framework` | Add a new framework to an existing advisor |
| business-brainstorming | Business | `/aligned:business-brainstorming` | Explore business problems, strategies, decisions |
| business-diagnosis | Business | `/aligned:business-diagnosis` | Diagnose why business deliverables aren't landing |
| business-executing | Business | `/aligned:business-executing` | Execute business plans with deliverables |
| business-write-plan | Business | `/aligned:business-write-plan` | Write business plans with critique panel |
| create-design-principles | Foundation | `/aligned:create-design-principles` | Enforce precise, minimal design system (Linear/Notion/Stripe aesthetic) |
| find-potential-advisors | Advisor | `/aligned:find-potential-advisors` | Research and evaluate potential advisors |

**Step 3: Update agents table**

Add 3 new agents:

| Agent | Description |
|-------|-------------|
| worktree-setup | Isolated git worktree creation with safety checks |
| error-diagnosis | Classify error patterns from error-tracker hook data |
| artifact-verifier | 98% accuracy gate for document fact-checking |

**Step 4: Update counts and permissions**

- Header: `17 skills` → `25 skills`, `5 agents` → `8 agents`
- Permissions section: Add all 8 new skill permissions (`Skill(aligned:add-advisor)`, etc.)
- Changelog: Add 0.3.0 entry documenting the additions

**Step 5: Update CLAUDE.md**

No changes needed to CLAUDE.md — the hook-triggered audits section was already cleaned up. Verify by reading it.

**Step 6: Bump plugin version**

Edit `.claude-plugin/plugin.json`: change `"version": "0.2.1"` to `"version": "0.3.0"`.

**Step 7: Commit**

```bash
git add README.md CLAUDE.md .claude-plugin/plugin.json
git commit -m "docs: update README for 8 new skills, 3 new agents, bump to v0.3.0"
```

---

### Task 12: Archive local duplicates

**ORDERING GATE:** Do NOT start this task until Tasks 1-11 are ALL committed and verified. Archiving destroys local files — if any port failed, the local original is the only recovery source. Before proceeding, run `git log --oneline -15` in the plugin repo and verify commits exist for: worktree-setup, business skills (3), business-write-plan, find-potential-advisors, create-design-principles, add-advisor, add-framework, error-diagnosis, artifact-verifier, eval-failure-triage enhancement, and README/version bump. If any are missing, STOP and complete them first.

Move all local skills/agents/hooks that now have plugin equivalents to the archive directory.

**Files:**
- Create: `/Users/ericpage/software/archived-claude-local/` directory structure
- Move: All 19 local skills from `~/.claude/skills/`
- Move: Overlapping agents from `~/.claude/agents/`
- Move: Overlapping hooks from `~/.claude/hooks/`

**Step 1: Create the archive directory structure**

```bash
mkdir -p /Users/ericpage/software/archived-claude-local/skills
mkdir -p /Users/ericpage/software/archived-claude-local/agents
mkdir -p /Users/ericpage/software/archived-claude-local/agents/workers
mkdir -p /Users/ericpage/software/archived-claude-local/agents/references
mkdir -p /Users/ericpage/software/archived-claude-local/hooks
```

**Step 2: Archive ALL 19 local skills**

All local skills now have plugin equivalents. Move them all:

```bash
mv ~/.claude/skills/add-advisor /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/add-framework /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/autopilot /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/brainstorming /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/business-brainstorming /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/business-diagnosis /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/business-executing /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/business-write-plan /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/create-design-principles /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/create-new-skill /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/executing-plans /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/find-potential-advisors /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/finishing-a-development-branch /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/kanban-resolve /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/kickstart /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/systematic-debugging /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/use-advisor /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/use-framework /Users/ericpage/software/archived-claude-local/skills/
mv ~/.claude/skills/writing-plans /Users/ericpage/software/archived-claude-local/skills/
```

**Step 3: Archive overlapping and orphaned agents**

Move agents that are in the plugin or orphaned. KEEP: audit-settings, code-simplifier-full, doc-staleness-detector (local-only, paired with check-cron-results.sh).

```bash
mv ~/.claude/agents/artifact-verifier.md /Users/ericpage/software/archived-claude-local/agents/
mv ~/.claude/agents/code-reviewer.md /Users/ericpage/software/archived-claude-local/agents/
mv ~/.claude/agents/code-simplifier.md /Users/ericpage/software/archived-claude-local/agents/
mv ~/.claude/agents/error-diagnosis.md /Users/ericpage/software/archived-claude-local/agents/
mv ~/.claude/agents/eval-auto-triage.md /Users/ericpage/software/archived-claude-local/agents/
mv ~/.claude/agents/eval-failure-triage.md /Users/ericpage/software/archived-claude-local/agents/
mv ~/.claude/agents/kanban-triage.md /Users/ericpage/software/archived-claude-local/agents/
mv ~/.claude/agents/mockup-generator.md /Users/ericpage/software/archived-claude-local/agents/
mv ~/.claude/agents/test-auditor.md /Users/ericpage/software/archived-claude-local/agents/
mv ~/.claude/agents/worktree-setup.md /Users/ericpage/software/archived-claude-local/agents/
```

Move workers and references directories (test-auditor infrastructure):

```bash
mv ~/.claude/agents/workers/* /Users/ericpage/software/archived-claude-local/agents/workers/ 2>/dev/null
mv ~/.claude/agents/references/* /Users/ericpage/software/archived-claude-local/agents/references/ 2>/dev/null
rmdir ~/.claude/agents/workers ~/.claude/agents/references 2>/dev/null
```

**Step 4: Archive overlapping hooks**

Move hooks that are in the plugin. KEEP: check-cron-results.sh, check-test-audit.sh (local-only). Also KEEP: error-tracker.js, usage-tracker.js, auto-approve-worktrees.js — these should remain locally so they fire in non-plugin sessions too. Having them in both places is harmless (hooks from both sources fire, producing duplicate entries is acceptable and better than missing data).

**Step 5: Verify what remains locally**

List remaining local files:

```bash
ls ~/.claude/skills/     # Expected: empty directory
ls ~/.claude/agents/     # Expected: audit-settings.md, code-simplifier-full.md, doc-staleness-detector.md
ls ~/.claude/hooks/      # Expected: check-cron-results.sh, check-test-audit.sh, auto-approve-worktrees.js, error-tracker.js, usage-tracker.js
```

---

### Task 13: Update ~/.claude/settings.json

**Files:**
- Modify: `/Users/ericpage/.claude/settings.json`

**Step 1: Read the current settings.json**

Read `/Users/ericpage/.claude/settings.json` in full.

**Step 2: Keep all hook entries in settings.json**

Local hooks are NOT being archived (see Task 12 Step 4 — we keep them for non-plugin session coverage). Therefore, all hook entries in `~/.claude/settings.json` should remain as-is. Both local and plugin hooks will fire in plugin-enabled sessions — this means duplicate hook execution for error-tracker, usage-tracker, and auto-approve-worktrees, but duplicate entries are harmless and preferable to missing coverage.

No edits to the hooks section of settings.json.

**Step 3: Update skill permissions**

Replace bare skill names with `aligned:` prefix for skills that moved to the plugin. Update the permissions array:

Remove (now in plugin — don't need bare permission since plugin handles it):
- `"Skill(brainstorming)"` → `"Skill(aligned:brainstorming)"`
- `"Skill(writing-plans)"` → `"Skill(aligned:writing-plans)"`
- `"Skill(autopilot)"` → `"Skill(aligned:autopilot)"`
- `"Skill(executing-plans)"` → `"Skill(aligned:executing-plans)"`
- `"Skill(finishing-a-development-branch)"` → `"Skill(aligned:finishing-a-development-branch)"`
- `"Skill(add-framework)"` → `"Skill(aligned:add-framework)"`
- `"Skill(add-advisor)"` → `"Skill(aligned:add-advisor)"`
- `"Skill(create-design-principles)"` → `"Skill(aligned:create-design-principles)"`

Add all new plugin skills not yet in the list (from the README permissions section).

**Step 4: Write the updated settings.json**

Write the modified file with proper JSON formatting.

**Step 5: Verify JSON is valid**

Run: `node -e "JSON.parse(require('fs').readFileSync('/Users/ericpage/.claude/settings.json', 'utf8')); console.log('Valid JSON')"` — expected output: `Valid JSON`.

---

## Manual Steps (Post-Automation)

> Complete these steps after all tasks are done.

- [ ] **Test plugin skills in a fresh session:** Start a new Claude Code session with `claude --plugin-dir /Users/ericpage/software/aligned_cc_skills` and verify that `/aligned:business-brainstorming`, `/aligned:add-advisor`, and `/aligned:create-design-principles` load correctly.
- [ ] **Verify local-only system still works:** In a project with a test config file (jest/vitest), verify that the SessionStart hook (`check-cron-results.sh`) still fires and shows the audit dashboard. Verify the UserPromptSubmit hook (`check-test-audit.sh`) still fires the `[TEST AUDIT]` tag.
- [ ] **Push changes:** `git push` from the plugin repo once satisfied.
- [ ] **Consider git-tracking the archive:** `cd /Users/ericpage/software/archived-claude-local && git init && git add . && git commit -m "archive: local Claude skills/agents/hooks migrated to aligned plugin"` — gives you version history if you ever need to recover something.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Artifact-verifier disposition | Port as agent | Retire, merge into critique panels |
| 2 | Error-diagnosis disposition | Port as agent | Retire (never used) |
| 3 | Eval-auto-triage disposition | Extract unique content into eval-failure-triage, retire agent | Port as agent, retire entirely |
| 4 | Eval-failure-triage agent disposition | Retire (superseded by plugin skill) | Port as agent alongside skill |
| 5 | Business skill personal references | Genericize ("the user") | Keep personal refs, strip entirely |
| 6 | add-advisor/add-framework symlink infrastructure | Document both paths (plugin + user-extension) | Strip entirely, port as-is |
| 7 | Version bump | 0.3.0 (8 new skills, 3 new agents = significant feature add) | 0.2.2 (patch), 1.0.0 (stable) |

### Appendix: Decision Details

#### Decision 1: Artifact-verifier disposition
**Chose:** Port as agent
**Why:** The 98% accuracy gate and multi-round re-verification loop add quantitative rigor that the existing critique panels lack. The critique panels do inline fact-checking but have no formal accuracy threshold or retry mechanism. The artifact-verifier is also designed for standalone artifacts (Mermaid diagrams, technical references) that don't go through critique panels at all. Porting it gives skills the option to dispatch it after critique rounds as an additional quality gate, or for non-design artifacts.
**Alternatives rejected:**
- Retire: Loses the accuracy gate, which is the unique value proposition
- Merge into critique panels: Would make the already-complex critique prompts even longer. Better as a separate, optional dispatch.

#### Decision 2: Error-diagnosis disposition
**Chose:** Port as agent
**Why:** Despite zero historical usage, the agent is architecturally sound and completes a data pipeline that's already half-built in the plugin. The plugin ships `error-tracker.js` (data collection) but has no consumer for that data. Without the diagnosis agent, error data accumulates in `errors.jsonl` but is never analyzed. The 8-category classification system and "Misuse" category (detecting CLAUDE.md documentation gaps from error patterns) are valuable. The zero usage is explained by the agent never being wired into any invocation point — there was no hook or CLAUDE.md instruction to trigger it. Porting it and adding a mention in CLAUDE.md would activate it.
**Alternatives rejected:**
- Retire: Would leave the error-tracker hook collecting data that nothing reads — wasteful infrastructure.

#### Decision 3: Eval-auto-triage disposition
**Chose:** Extract unique content, retire agent
**Why:** The classification logic (a)/(b)/(c)/(d) is identical to the plugin's eval-failure-triage skill. The two unique contributions — infrastructure error pre-check and trend analysis — are small enough to fold into the existing skill without bloating it. Maintaining two overlapping eval triage tools creates confusion about which to use.
**Alternatives rejected:**
- Port as agent: Creates "which triage tool do I use?" confusion
- Retire entirely: Loses the infrastructure error table, which catches runner/tooling failures before wasting time on classification

#### Decision 4: Eval-failure-triage agent disposition
**Chose:** Retire (superseded)
**Why:** The plugin's eval-failure-triage skill is a strictly better version: de-identified examples, lessons-learned gate, no stale `jq` commands. Note: the local agent's reference file (`eval-failure-classification-patterns.md`) still exists at `~/.claude/agents/references/eval-failure-classification-patterns.md`, but the plugin's `skills/eval-failure-triage/references/classification-patterns.md` is the canonical, updated copy. The local version will be archived with the rest of the agent references in Task 12.
**Alternatives rejected:**
- Port alongside skill: Two tools doing the same thing. The skill is already the canonical version.

#### Decision 5: Business skill personal references
**Chose:** Genericize to "the user"
**Why:** A shared plugin shouldn't address a specific person by name. Other users installing the plugin would see "Eric" references that don't apply to them. The `domains/aligned_consulting/` folder structure is specific to one consulting practice. Genericizing preserves the workflow while making it applicable to anyone.
**Alternatives rejected:**
- Keep personal refs: Breaks for anyone who isn't Eric
- Strip entirely: Loses the conversational tone and checkpoint patterns that make the business skills effective

#### Decision 6: add-advisor/add-framework symlink infrastructure
**Chose:** Document both paths
**Why:** The plugin already has an advisor/framework discovery system that supports both plugin-shipped content (in `advisors/{repo-name}/`) and user-added content (in `~/.claude/advisors/prompts/{repo-name}/`). The ported skills should document both: default to plugin directory for shared advisors, mention user-extension directory for project-specific or personal advisors. This aligns with the existing use-advisor and use-framework discovery patterns.
**Alternatives rejected:**
- Strip entirely: Users lose the ability to add advisors to specific projects
- Port as-is: `~/.claude/` symlink infrastructure is fragile and not necessary in the plugin model

#### Decision 7: Version bump
**Chose:** 0.3.0
**Why:** Adding 8 skills and 3 agents is a significant feature expansion. Semver pre-1.0: minor version bumps for feature additions, patch for fixes. This is clearly a feature release, not a patch.
**Alternatives rejected:**
- 0.2.2: Undersells the scope of changes
- 1.0.0: Premature — skill interfaces are still evolving
