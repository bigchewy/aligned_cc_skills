# Autopilot Orchestration Redesign

**Goal:** Restructure the Ralph autopilot pipeline so plans declare their environment requirements explicitly, the bash orchestrator decomposes into testable phase scripts, and the autopilot halts cleanly with structured reasons instead of crashing when it can't proceed unattended.

**Source Design Doc:** N/A (this IS the design doc)

**Mockups:** `docs/mockups/autopilot-orchestration-redesign.html`

**Architecture:** Three coordinated changes to the same surface. (1) Decompose `autopilot.sh` into typed phase scripts under `docs/ralph_loops/phases/` with a shared `lib/process.sh`. (2) Add a narrow YAML front-matter manifest to plans declaring required MCP tools and env vars — both deterministically probable. (3) Introduce a `.autopilot-halt` sentinel with a structured reason taxonomy so preflight and any phase can halt cleanly with actionable user-facing details.

**Tech Stack:** Bash (`set -u` standardized), Markdown plans with YAML front-matter, Python pytest for static-parse tests over phase scripts and manifest validation.

---

## Background

This redesign is driven by two converging signals:

**Signal 1 — Recurring class of failure.** Plans reach for MCP tool prefixes that don't load in `claude -p` subprocesses. The triggering incidents involved `mcp__playwright-full__*` (a ghost namespace from a deleted `va-web-app/.mcp.json`) and partially-allowlisted `mcp__playwright__browser_resize` / `browser_take_screenshot` / `browser_wait_for`. Headless `claude -p` cannot grant interactive permissions, so the loop halts mid-iteration. Both incidents resolved by deleting the offending tasks — symptom-fix, not root-cause-fix. The plan-authoring contract has no mechanism to verify tool availability against the executor's environment.

**Signal 2 — `autopilot.sh` bloat.** 642 lines, zero tests, ~70 lines of process-management duplicated with `run-ralph.sh`. 9 commits since creation are all bug fixes and timeout tuning — no architectural change. `FINISH-BRANCH.md` (224 lines) is orphaned. Verify-gate logic is triplicated across `VERIFY-BRANCH.md`, `FINISH-BRANCH.md`, and `skills/finishing-a-development-branch/SKILL.md` (acknowledged in `VERIFY-BRANCH.md:3-4`). Three coarse `^### ` matchers on `autopilot.sh:434-436` can match non-task headings like `### Notes`. Phase 2 sentinel parsing (`head -1` / `tail -1` on `.autopilot-plan-path`) works by accident. Discoverability gap: `references/execution-handoff-templates.md` does not surface autopilot at all.

**Signal 3 — Mid-flow "human review" tasks slipping into plans.** Distinct from the recurring MCP class but same overall theme: plans get authored with tasks like "verify the UI looks correct before proceeding" or "review the interface before Task N+1." These are not Prerequisites or Post-Automation steps — they're mid-pipeline pauses asking the user for *judgment*, not execution. The existing Manual Steps Policy in `writing-plans/SKILL.md:100-111` forbids "manual steps" mid-plan but the policy uses "manual" to mean "the user runs a command" — judgment-based review tasks slip past it. The autopilot's value proposition is unattended completion; mid-flow review tasks defeat that proposition entirely. This redesign adds an explicit anti-pattern (see "Anti-Pattern: Mid-Flow Human Review" below).

The user-stated success criterion frames the intent: "I want to know if it will fail and, if there is work to do in advance or after, it should tell me. So there should be clear stages and, if the autopilot isn't going to finish, it should both tell me that upfront and not appear to be erroring out when it hits the stage where I need to do something."

This redesign replaces the implicit pipeline with a typed one: each phase declares its inputs/outputs/exit-codes; the manifest declares the plan's environment requirements; the halt protocol surfaces "human action required" without an error-coded exit.

---

## Architecture

### Component map

```
docs/ralph_loops/
  autopilot.sh                  ← orchestrator (~150 lines target, down from 642)
  run-ralph.sh                  ← unchanged behavior, now sources lib/process.sh
  lib/
    process.sh                  ← heartbeat, watchdog, cleanup, run_claude_phase
    halt.sh                     ← write/read/format .autopilot-halt sentinels
    manifest.sh                 ← parse YAML front-matter, validate vs environment
    stages.sh                   ← stages reporter ("▶ phase N of M: ... | running")
  phases/
    preflight.sh                ← validates env vs plan manifest; writes halt or proceeds
    plan.sh                     ← Phase 1: claude -p with WRITE-PLAN.md
    worktree.sh                 ← Phase 2: create worktree, env-link, merge main
    mockup.sh                   ← Phase 3.5: claude -p with MOCKUP-FIDELITY.md
    verify.sh                   ← Phase 4: claude -p with VERIFY-BRANCH.md
  EXECUTE-PLAN.md               ← unchanged
  WRITE-PLAN.md                 ← unchanged
  MOCKUP-FIDELITY.md            ← unchanged
  VERIFY-BRANCH.md              ← reduced to a thin wrapper around the canonical gate
  FINISH-BRANCH.md              ← DELETED (orphan)
  BEST-PRACTICES.md             ← unchanged
```

### Phase script contract

Each `phases/*.sh` declares a typed contract in its header. Static-parse tests assert these headers exist and match the runtime sentinel set known to `lib/halt.sh`.

```bash
#!/usr/bin/env bash
# PHASE: preflight
# INPUTS:
#   PROJECT (env var, absolute path) — main repo path
#   PLAN_FILE (env var, absolute path) — plan path on main, may not exist yet for plan.sh
# OUTPUTS:
#   .autopilot-halt (sentinel, in $PROJECT) — written if preflight halts
# EXIT CODES:
#   0 — phase passed, autopilot may proceed
#   2 — halt-with-reason; .autopilot-halt has structured details
#   3 — skip (preflight not applicable; e.g., plan has no manifest yet — backward-compat path)

set -u
source "$(dirname "$0")/../lib/process.sh"
source "$(dirname "$0")/../lib/halt.sh"
source "$(dirname "$0")/../lib/manifest.sh"

# ... phase logic ...
```

The orchestrator (`autopilot.sh`) reads the EXIT CODES contract and routes accordingly:
- `0` → next phase
- `2` → print halt sentinel, exit 0 (NOT an error — this is a clean halt)
- `3` → skip, advance phase counter, continue
- anything else → print stderr, write halt with `reason: phase_crashed`, exit 1

### Plan front-matter manifest (narrow scope)

Plans gain an OPTIONAL YAML front-matter block. Two fields, both deterministically probable:

```yaml
---
mcp-tools-required:
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_click
env-vars-required:
  - SUPABASE_URL
  - OPENAI_API_KEY
---

# Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans...

[rest of plan body]
```

**What's NOT in the manifest:**
- Prerequisites and post-automation steps stay as prose sections (`writing-plans/SKILL.md:100-111` already governs them).
- Plan version numbers, plan-name, etc. — not adopted; YAGNI.
- External services (Supabase, Vercel, Notion) — not directly probable from outside; deferred.

**Authoring (writing-plans):**
- After plan body is drafted and before the critique panel, scan the body for `mcp__*__*` references and `process.env.*` / `os.environ.*` / shell `$VAR` references.
- Generate the manifest from the scan and prepend to the plan file.
- The Verifier critic gains a structural coherence check (deterministic, not LLM-judged): every `mcp__*__*` body reference appears in the manifest, and every manifest entry appears somewhere in the body. Mismatch = HIGH severity finding.

**Validation (autopilot preflight):**
- Parse front-matter from `$PLAN_FILE`. If absent, exit 3 (skip — backward-compat).
- For each `mcp-tools-required[i]`:
  - Extract the server prefix (e.g., `mcp__playwright__browser_navigate` → `playwright`).
  - Locate `.mcp.json` files reachable from the worktree CWD upward; build the merged server set.
  - Halt-with-reason `mcp_unreachable` if the server is not defined.
  - Read `.claude/settings.local.json`'s `permissions.allow` list; halt-with-reason `mcp_tool_not_allowlisted` if the exact tool string is absent.
- For each `env-vars-required[i]`: probe `[ -n "${VAR:-}" ]` against the worktree env; halt-with-reason `env_var_missing` if unset.

### Halt-with-reason sentinel protocol

A new sentinel `.autopilot-halt` mirrors the existing `.ralph-human-blocked` (per `docs/plans/completed/2026-04-28-ralph-autonomy-enforcement.md` Decision 2 — filesystem sentinels, not plan-body markers). Written by `lib/halt.sh` from any phase.

**Write protocol:** atomic via `mv $TMP $PROJECT/.autopilot-halt` (or `$WORKTREE/.autopilot-halt` post-Phase-3). First writer wins; subsequent writers detect the existing sentinel and append a `secondary-halt:` block rather than overwriting. Lifecycle: written by phase script on exit-code-2; read by orchestrator after each phase; deleted by the user (after fix) or by the next successful run of the same phase. Never auto-deleted by the orchestrator on retry — preserving evidence is more valuable than auto-cleanup.

**Format** (newline-delimited key:value, indent-friendly multiline `details`):

```
reason: mcp_tool_not_allowlisted
phase: preflight
fix-instructions: |
  The plan declared `mcp__playwright__browser_resize` but it is not in
  this project's `.claude/settings.local.json` allowlist.

  Fix one of:
    1. Open a Claude session in this repo and accept the permission prompt
       once: this writes the tool to the allowlist.
    2. Remove `mcp__playwright__browser_resize` from the plan's
       `mcp-tools-required` and from any task body that references it.

  Then re-run autopilot.sh.
```

**Reason taxonomy** (extensible; v1 set):

| Reason | Phase | Trigger |
|---|---|---|
| `mcp_unreachable` | preflight | Plan declares an MCP tool whose server is not defined in any `.mcp.json` reachable from the worktree CWD |
| `mcp_tool_not_allowlisted` | preflight | Server is defined, but the specific tool string is not in `.claude/settings.local.json`'s `permissions.allow` |
| `env_var_missing` | preflight | Plan declares an env var that is unset in the worktree environment |
| `manifest_drift` | preflight | Plan body references an MCP tool not in the manifest, or vice versa |
| `manifest_malformed` | preflight | YAML front-matter present but unparseable, or required fields missing/wrong type. Parser is Python's `yaml` module (already a dev-dep via pytest) |
| `uncommitted_main` | worktree | Main has uncommitted changes that would block `git merge main` into the worktree |
| `verify_failed` | verify | Tests/build/eval failed (replaces the existing `.finish-status` failure path with a halt-formatted reason) |
| `human_action_required` | ralph (in-loop) | Existing `.ralph-human-blocked` aliases to this — same protocol, unified surface |
| `phase_crashed` | any | Phase script exited unexpectedly; `details:` carries the last 10 lines of stderr |

**Orchestrator response.** When `autopilot.sh` detects `.autopilot-halt` after a phase exits with code 2:
1. Print the structured reason to stdout (formatted, not raw):
   ```
   ✗ phase 1 of 6: preflight | halted (mcp_tool_not_allowlisted)

   The plan declared `mcp__playwright__browser_resize` but it is not in
   this project's `.claude/settings.local.json` allowlist.
   ...
   ```
2. Exit 0 (NOT an error — this is a clean halt). Halts are not failures.
3. The sentinel is left in place so re-running can detect "previous halt" and surface "fix this first" guidance.

### Stages reporter

`lib/stages.sh` provides a single function `report_stage <phase> <total> <name> <status>`:

```
▶ phase 1 of 6: preflight    | running
✓ phase 1 of 6: preflight    | passed (12s)
▶ phase 2 of 6: plan         | running
...
✗ phase 5 of 6: verify       | halted (verify_failed)
```

Replaces the current `=== Phase N: ... ===` banners. Single source of truth for what's happening.

---

## Anti-Pattern: Mid-Flow Human Review (BANNED by writing-plans contract)

**The autopilot's whole value is unattended completion from design doc to verified branch.** The user reviews ONCE, at the end, after `verify.sh` halts cleanly or autopilot completes. Any plan task that inserts "human review" mid-pipeline defeats this proposition — even when framed as "verification," "confirmation," or "user check."

This is distinct from the existing Manual Steps Policy in `writing-plans/SKILL.md:100-111`. That policy governs:
- **Prerequisites** — work the user MUST do because the executor cannot (env setup, OAuth, prod migrations).
- **Post-Automation steps** — work the user does after autopilot completes.

Both are about *execution* the user must perform. The new ban is about *judgment* the plan author wanted the user to provide mid-flow. Different framing — same effect: pipeline halts, autopilot's value evaporates.

### Banned task patterns

writing-plans MUST NOT produce plan tasks containing language like:

| Pattern | Why it's banned |
|---|---|
| "Get user feedback on X before proceeding" | Pipeline doesn't pause for feedback |
| "Have the user verify the UI looks correct" | Mockup fidelity loop is the machine check; user reviews at end |
| "Pause and ask if X is acceptable" | No human present to ask |
| "Review the interface before continuing to Task N+1" | User reviews when autopilot completes |
| "Confirm with user before proceeding" | No conversational surface; loop will halt or guess |
| "Show user the [output/screenshot/result] and wait" | Headless `claude -p` cannot wait for human input |
| "User signs off on the design before implementation" | Sign-off happened during brainstorming; not a plan task |

The pattern is "task body asks for *judgment* mid-pipeline." The pattern is NOT "task body runs a machine check" (those are fine — mockup fidelity, eval scoring, verify gate are all machine-judged).

### What's allowed

- **Prerequisites (before Task 1)** — work the user does to unblock autopilot.
- **Manual Steps (Post-Automation)** — work the user does after autopilot completes.
- **Halt-with-reason (`.autopilot-halt`)** — environment failures the executor genuinely cannot resolve.
- **Mockup fidelity loop** — machine check (claude compares implementation to mockup), not human review.
- **Verify gate** — machine check (tests, build, eval), not human review.
- **End-of-autopilot review** — the user reviews everything at the end, when the branch is ready.

### Enforcement

The Verifier critic in `references/critique-panel-prompts.md` Criterion 10 (Autonomy violations) gains an explicit rule:

> **Mid-flow human review check.** Any task whose body contains "human review," "user verifies," "review the [UI/interface/mockup/output]," "wait for user," "confirm with user," "before proceeding ask," "user signs off," "get user approval," or semantically equivalent language MUST be flagged as HIGH severity. Suggest restructure: move to Manual Steps (Post-Automation) if it's real verification work the user must do, or remove if it's a gratuitous gate.

Exemption: Prerequisites, Manual Steps (Post-Automation), and Decision Log sections — these are explicitly user-facing and not part of the autopilot's task flow. Task bodies are not exempt regardless of where in the plan they sit.

### Why this isn't already caught

The existing Manual Steps Policy uses "manual" in the sense "the user runs a command outside autopilot." A "human review" task uses different framing — it asks for *judgment*, not *execution* — and slips past. The new explicit list of banned phrasings, in the same Verifier critic that already enforces TDD discipline and Manual Steps placement, closes this gap.

### Test surface

`test_writing_plans_anti_review.py` (new):
- Static-parse: writing-plans/SKILL.md contains a "Mid-Flow Human Review" section with the banned-pattern list.
- Static-parse: references/critique-panel-prompts.md Verifier section references the new rule.
- Fixture-based: a synthetic plan containing each banned pattern triggers a HIGH-severity finding from a mock Verifier check.

---

## Data flow

```
autopilot.sh DESIGN_DOC
  │
  ├─→ phase 1: preflight.sh
  │     ├─ if no plan exists yet: skip MCP/env checks, defer to phase 1.5
  │     ├─ else: validate manifest vs environment
  │     ├─ exit 0 → continue
  │     └─ exit 2 → halt cleanly (mcp_unreachable | env_var_missing | etc.)
  │
  ├─→ phase 2: plan.sh (skipped if .autopilot-plan-path sentinel matches)
  │     └─ claude -p with WRITE-PLAN.md → writes plan to main, sentinel
  │
  ├─→ phase 1.5: preflight.sh (re-run, now with plan present)
  │     └─ validates plan manifest; halt-with-reason if violations
  │
  ├─→ phase 3: worktree.sh
  │     ├─ create/attach worktree
  │     ├─ npm install / cargo / pyproject detect
  │     ├─ env-link mirroring (root + per-app symlinks)
  │     └─ git merge main
  │
  ├─→ phase 4: ralph (run-ralph.sh as today)
  │     ├─ iterates EXECUTE-PLAN.md until .ralph-done or .ralph-human-blocked
  │     └─ .ralph-human-blocked translates to .autopilot-halt(human_action_required)
  │
  ├─→ phase 5: mockup.sh (skipped if no **Mockups:** field)
  │     └─ claude -p with MOCKUP-FIDELITY.md, up to MAX_MOCKUP_ITERATIONS
  │
  └─→ phase 6: verify.sh
        ├─ claude -p with VERIFY-BRANCH.md
        ├─ writes .finish-status: SUCCESS or FAILED
        └─ FAILED translates to .autopilot-halt(verify_failed)
```

The double-preflight (phase 1 and phase 1.5) is intentional: phase 1 catches environment-level issues that block plan-writing itself (e.g., MCP servers required by writing-plans's own behavior), phase 1.5 catches plan-vs-env mismatches once the plan exists. If the plan exists at autopilot launch (resume case), phase 1 has full information and phase 1.5 is a no-op.

---

## Error handling

**Three failure classes, three protocols:**

| Class | Mechanism | User experience |
|---|---|---|
| **Halt-with-reason** | `.autopilot-halt` sentinel, exit code 2 from phase, exit 0 from autopilot.sh | Clean message, no error tone, actionable fix-instructions, re-run after fix |
| **Phase crash** | Phase exited with non-2 non-zero code (or `cleanup` trap fired); autopilot.sh writes halt with `reason: phase_crashed`, exits 1 | Error tone, last 10 lines of stderr, points to log file |
| **Watchdog timeout** | Existing `lib/process.sh` behavior — claude -p killed by SIGTERM/SIGKILL after timeout | Existing message; counts toward consecutive-timeout cap |

The key change: **halts are not failures.** Currently `.ralph-human-blocked` exits the loop but the autopilot then prints "ERROR: Ralph loop failed (exit code N)" because non-zero exit codes propagate. The new protocol distinguishes "I cleanly stopped because you need to do X" from "something went wrong."

**Cleanup trap on phase scripts.** Each phase's `cleanup` trap also writes a halt sentinel if it dies abnormally — so the orchestrator always sees structured info, never a silent crash.

---

## Testing

Static-parse tests under `e2e/tests/`, following the `test_ralph_sentinels.py` pattern (read file, assert on text content; no subprocess execution per `2026-04-28-ralph-autonomy-enforcement.md` Decision 7).

**New test files:**

- `test_phase_contracts.py` — for each phase script in `phases/`, assert:
  - Has the `# PHASE:`, `# INPUTS:`, `# OUTPUTS:`, `# EXIT CODES:` header.
  - Declared sentinel names match the set known to `lib/halt.sh`.
  - Sources `lib/process.sh` and (if applicable) `lib/halt.sh` and `lib/manifest.sh`.
  - Uses `set -u` (not `set -euo`) — pinned for shared lib compatibility.

- `test_halt_protocol.py` — for `lib/halt.sh`:
  - The reason taxonomy in code matches the design doc (table at the top of this file).
  - `write_halt` accepts `reason`, `phase`, `fix-instructions` and emits the documented format.
  - `read_halt` round-trips a sentinel without loss.

- `test_manifest_validation.py` — for `lib/manifest.sh`:
  - Given a fixture plan with manifest, `validate_manifest` correctly halts on each ghost MCP server, missing env var, manifest drift case.
  - Given a plan without front-matter, `parse_manifest` returns "absent" without error.
  - Path-walk correctly merges `.mcp.json` from worktree → parent → user-level.

- `test_writing_plans_manifest_authoring.py` — static-parse on `skills/writing-plans/SKILL.md`:
  - Manifest-authoring section exists with the documented procedure.
  - Verifier critic prompt (`references/critique-panel-prompts.md`) references the structural coherence check.

**Existing test files unchanged:**
- `test_ralph_sentinels.py` — `run-ralph.sh` behavior is unchanged. Add one assertion that `run-ralph.sh` sources `lib/process.sh` (proves dedupe shipped).
- `test_skill_cross_references.py` — flag if `FINISH-BRANCH.md` is removed but still referenced anywhere.

**No subprocess testing** — consistent with the postmortem plan's Decision 7. The phase contracts are static; the manifest validator's logic is unit-testable as bash functions called from pytest via subprocess (allowed because the unit boundary is the function, not the orchestrator).

---

## Implementation epics

Three roughly-independent epics. The actual `writing-plans` run will produce ~20 task-level steps; this is the design-level chunking.

### Epic A — Decompose & dedupe (smallest, ships first)

- Extract `lib/process.sh` from `autopilot.sh` and `run-ralph.sh`. Standardize on `set -u`. Both callers source it.
- Split `autopilot.sh` phases into `phases/{plan,worktree,mockup,verify}.sh` (preflight comes in Epic B, ralph stays in `run-ralph.sh`).
- Replace `=== Phase N: ===` banners with `lib/stages.sh` reporter.
- Fix the coarse `^### ` plan-completion regex (use `^### (✅|🔄)?\s*\d` per EXECUTE-PLAN.md).
- Delete `FINISH-BRANCH.md` after grep'ing all of `skills/**/*.md` and `docs/**/*.md` for stragglers.
- Collapse triplicated verify-gate: `VERIFY-BRANCH.md` becomes a thin wrapper that calls into `skills/finishing-a-development-branch/SKILL.md`'s canonical steps.
- Tests: `test_phase_contracts.py` (decomposition only — preflight contract added in Epic B).

### Epic B — Manifest contract

- Define manifest schema in `skills/_shared/plan-manifest-format.md`.
- writing-plans: add manifest-authoring step before critique panel; add Verifier structural coherence check.
- `lib/manifest.sh`: parse YAML, validate against env.
- `phases/preflight.sh`: read manifest, run probes, halt-with-reason on violations.
- Add manifest to ALL active plans in `docs/plans/` (one bulk migration commit; non-blocking — preflight skips when manifest absent).
- Tests: `test_manifest_validation.py`, `test_writing_plans_manifest_authoring.py`.

### Epic C — Halt protocol

- Define reason taxonomy in `skills/_shared/autopilot-halt-format.md`.
- `lib/halt.sh`: write/read/format sentinels.
- All phase scripts emit halt-with-reason on stop conditions (replaces ad-hoc error messages).
- Orchestrator detects `.autopilot-halt`, surfaces formatted message, exits 0.
- Alias `.ralph-human-blocked` → `.autopilot-halt(human_action_required)` so the surface is unified.
- Tests: `test_halt_protocol.py`.

**Sequencing.** Epic A ships first (no dependencies). Epic B depends on Epic A's `phases/` decomposition. Epic C depends on Epic A's `lib/` extraction but can ship in parallel with Epic B. A minimum-viable cut would ship A only and add B/C later — but the recurring failure class only resolves once B's preflight check is live, so don't stop at A.

---

## Open questions

These resolve during writing-plans, not in this design doc:

1. **Should preflight run twice?** Phase 1 (env-only, before plan exists) and phase 1.5 (manifest validation, after plan exists) is the design above. Alternative: single preflight after plan-writing — simpler, but environment issues that break plan-writing itself surface as plan.sh crashes instead of clean halts.

2. **`.ralph-human-blocked` deprecation timeline.** Coexist as alias indefinitely, or remove after migration?

3. **Manifest migration of existing plans.** Bulk-add manifests to all ~25 active plans in `docs/plans/`, or only require for new plans? The design defaults to optional/backward-compatible, but the bulk migration buys cleaner enforcement sooner.

4. **VERIFY-BRANCH.md collapse target.** Make `VERIFY-BRANCH.md` a thin wrapper around `skills/finishing-a-development-branch/SKILL.md` — or move the canonical steps into `skills/_shared/verify-gate.md` and have both reference it? The latter is cleaner but touches more files.

5. **Discoverability gap.** The user's selected option was "Composite (Recommended)," not "Composite + go after the discoverability gap too." Re-surface autopilot in `references/execution-handoff-templates.md` and `brainstorming/modes/software.md` as part of this design, or defer to a follow-up?

---

## Round 1 Critique — Open Issues for writing-plans

The brainstorming critique panel (The Architect, The QA Engineer, The DevEx Engineer) ran Round 1 against this design. The HIGH-severity items below were applied directly to this design (see edits to Decision 7, Halt protocol write protocol, manifest_malformed reason, Anti-Pattern section). The remaining items below are deferred to the writing-plans run, which has its own critique panel that will re-evaluate them in implementation context.

Reports archived at `/tmp/brainstorm-critique-autopilot-orchestration-redesign/round-1/`.

**Applied to this design:**
- Decision 7 expanded to make `run-ralph.sh` flag change explicit
- Halt sentinel write protocol added (atomic, first-writer-wins, no auto-cleanup)
- `manifest_malformed` reason added to taxonomy
- Anti-Pattern: Mid-Flow Human Review section added (user-surfaced HIGH item)
- Fact-check corrections: "11 commits" → "9 commits", `completed/` path on postmortem reference, three `^### ` matchers (not one)

**Deferred to writing-plans (HIGH severity):**
- **`.mcp.json` resolution algorithm.** Architect H2 + QA flagged: "merged set walking upward from CWD" is not a documented Claude behavior. writing-plans must either cite Claude Code's MCP loading semantics or declare a conservative algorithm with edge-case coverage (symlinked worktrees, conflicting `.mcp.json` files at different levels, missing `settings.local.json`, missing `permissions.allow` field).
- **Manifest-authoring visibility.** DevEx H3: runs without user override. writing-plans must specify whether the user sees/edits the proposed manifest before commit.
- **Double-preflight state ambiguity.** QA H6: SIGKILL/OOM during plan-write leaves Phase 1.5 reading partial YAML. Need fixture test for "partial plan file" or "interrupted Phase 2"; or drop double-preflight in favor of single after-plan preflight.

**Deferred to writing-plans (MEDIUM severity):**
- Per-phase stderr capture spec (or drop "last 10 lines" promise from `phase_crashed`)
- `_shared/` vs `docs/ralph_loops/` location for autopilot-internal schemas (Architect M3 — likely move to `docs/ralph_loops/`)
- Phase script invocation pattern (LIB_DIR/PHASES_DIR exports vs absolute-path resolution)
- Resolve preflight numbering ("of 6" with 7 phases is a viz/code drift seed)
- Centralize fix-instructions in `lib/halt.sh` keyed by reason (DevEx M7 — reduces "add a halt reason" from 6 surfaces to 2)
- Halt format must always include: reason + log path + next action (DevEx M8)
- `.ralph-human-blocked` aliasing impact on `test_ralph_sentinels.py:24`
- `.finish-status` consumer enumeration (mockup change table currently silent on its disposition)
- Coherence check regex must skip fenced code blocks / blockquotes / inline code (QA M11)
- Test surface for orchestrator exit-code dispatch (0/2/3/non-zero/SIGINT/SIGKILL/127/130/137)
- Phase registry pattern so adding a new phase doesn't touch 4-6 files (DevEx M14)

**Deferred to writing-plans (LOW severity):**
- Env-link block extraction guardrail ("move verbatim, don't refactor")
- Cleanup trap stacking pattern
- Decision 1 rationale rewrite ("bash is right tool for process glue" — stronger framing)
- Update or close `docs/plans/2026-04-08-plugin-split-plan.md` before deleting FINISH-BRANCH.md

The critique panel did NOT find issues with: the Composite vs alternatives choice, Decision 5 (no subprocess testing), Decision 6 (optional manifest in v1), the file layout (Architect approves with the location-fix above), or the goal/success criteria framing.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Orchestration model | Bash with `claude -p` per phase, decomposed into typed phase scripts | Skill-based orchestration (Approach C); manifest-driven runner (full Approach B) |
| 2 | Plan contract scope | YAML front-matter, MCP tools + env vars only | Full 5-field manifest (plan-version, prereqs, post-auto); pure prose conventions |
| 3 | Halt mechanism | New `.autopilot-halt` sentinel with structured reason taxonomy | Generalize `.ralph-human-blocked`; use exit codes alone; print-and-pray |
| 4 | Coherence check | Deterministic structural (manifest ↔ body diff) | Verifier-critic LLM judgement |
| 5 | Test pattern | Static-parse pytest, no subprocess | Subprocess testing with PATH-shimmed fake `claude` |
| 6 | Existing-plan migration | Optional manifest in v1; preflight skips when absent | Mandatory front-matter, blocking migration |
| 7 | `set -e` standardization | `set -u` only, with explicit exit-code checks; applies to `autopilot.sh`, `run-ralph.sh`, all phase scripts, and lib | `set -euo pipefail`; leave inconsistent |
| 8 | FINISH-BRANCH.md disposition | Delete (with stragglers grep) | Keep as alternative manual-merge path |
| 9 | Mid-flow human review | Forbidden by writing-plans contract; Verifier critic flags as HIGH | Trust existing Manual Steps Policy; make autopilot tolerant (silent skip) |

### Appendix: Decision Details

#### Decision 1: Orchestration model
**Chose:** Bash with `claude -p` per phase, decomposed into typed phase scripts.
**Why:** The Architect review made this load-bearing. Subagents (Approach C) share parent CLI state — MCP server set, permission state, accumulated context. The 50-iteration ralph loop depends on per-iteration process boundaries that only `claude -p` from bash provides. `BEST-PRACTICES.md:13` explicitly states `-p` is required for clean per-iteration exit. Replacing bash with skill-orchestration would either re-invent `claude -p` from inside a skill (worse) or lose context isolation (regression).
**Alternatives rejected:**
- Skill-based orchestration: would need `claude -p` from inside the skill anyway, with no precedent in `e2e/tests/` for testing it; rewrites discoverability (`brainstorming/modes/software.md:250-257` says "Run from any terminal" — a skill invocation is not "any terminal").
- Manifest-driven runner: would require a new runtime (not bash), increasing dependencies and making the plugin less portable.

#### Decision 2: Plan contract scope
**Chose:** YAML front-matter, two fields only — `mcp-tools-required` and `env-vars-required`.
**Why:** These are the only fields with deterministic machine-checkable probes. Env vars: `[ -n "${VAR:-}" ]`. MCP tools: read `.mcp.json` chain, read `.claude/settings.local.json`, exact string match. Prerequisites and post-automation steps are prose for humans (already governed by `writing-plans/SKILL.md:100-111`); forcing them into YAML creates a coherence-check problem and a migration cost without solving a known recurring failure.
**Alternatives rejected:**
- Full 5-field manifest: introduces drift surface; migration cost unjustified.
- Pure prose conventions: grep-based extraction is fragile (a code-block example mentioning `mcp__playwright-fake__` would false-positive); explicit declaration is cleaner.

#### Decision 3: Halt mechanism
**Chose:** New `.autopilot-halt` sentinel with structured reason taxonomy (8 reasons in v1).
**Why:** The user's success criterion explicitly distinguishes "tell me upfront" from "appear to be erroring out." Existing `.ralph-human-blocked` is bool — present or absent. The MCP failure class needs more than that: the user needs to know *what* tool, *what* to do. Structured reasons enable formatted output, future tooling (e.g., a halt-history report), and unify the disparate halt paths (preflight, in-loop, verify) under one protocol.
**Alternatives rejected:**
- Generalize `.ralph-human-blocked`: backward-compat appeal, but the existing sentinel is bool-only and adding fields to it changes its protocol; cleaner to introduce new + alias.
- Exit codes alone: not enough information for actionable user-facing message.

#### Decision 4: Coherence check
**Chose:** Deterministic structural diff — every `mcp__*__*` body reference appears in manifest, and vice versa.
**Why:** The Architect noted that LLM-judged coherence ("does this manifest match the body?") is the wrong tool — it's an eval at plan-write time on a contract that should be machine-checkable. Verifier critic is great for autonomy violations and TDD enforcement (subjective, multi-signal); overkill and unreliable for "do these two list literals agree."
**Alternatives rejected:**
- Verifier-critic LLM judgement: nondeterministic, slower, less precise.

#### Decision 5: Test pattern
**Chose:** Static-parse pytest, no subprocess execution.
**Why:** Consistent with `2026-04-28-ralph-autonomy-enforcement.md` Decision 7 — explicitly rejected adding subprocess test infrastructure (PATH shimming, fake `claude` binaries) for the previous "8-line bash change." This redesign is bigger but the test cost remains: phase contracts are textually verifiable; manifest logic is bash-callable from pytest at function boundary.
**Alternatives rejected:**
- Subprocess testing: would require PATH-shimming `claude` and other invariants; high infra cost; tests would be slower and flakier.

#### Decision 6: Existing-plan migration
**Chose:** Optional manifest in v1; preflight returns exit 3 (skip) when manifest absent.
**Why:** ~25 active plans in `docs/plans/`. Mandatory migration is a blocking change. Preflight-skip preserves backward compatibility — plans without manifests run as today, plans with manifests get the new validation. Bulk-migrate as a v2 task once Epic B is stable.
**Alternatives rejected:**
- Mandatory: blocks Epic B's ship; migration cost unjustified upfront.

#### Decision 7: `set -e` standardization
**Chose:** `set -u` only across `autopilot.sh`, `run-ralph.sh`, all phase scripts, and `lib/`. Explicit exit-code checks throughout.
**Why:** Current state: `autopilot.sh` uses `set -uo pipefail`; `run-ralph.sh` uses `set -euo pipefail`. Sourced lib functions inherit caller flags — under `-e` (run-ralph.sh) they exit on any non-zero; without `-e` (autopilot.sh) they don't. Two callers, two semantics, one shared lib = subtle bugs. `set -u` (catch undefined vars) is universally useful. `set -e` interacts badly with the explicit exit-code checks the autopilot already does (e.g., `MERGE_EXIT=0; git merge ... || MERGE_EXIT=$?`). Pin one flag set across all callers — explicit and consistent.
**Note on `run-ralph.sh` change:** This IS a behavioral change to `run-ralph.sh` (currently `set -euo pipefail`). Existing tests in `test_ralph_sentinels.py` don't cover flag-set behavior, so they continue to pass; new test_phase_contracts.py asserts `set -u` across all callers.
**Alternatives rejected:**
- `set -euo pipefail`: would require rewriting the explicit exit-code patterns throughout; subtle interactions with sourced libs.
- Leave inconsistent: the recurring failure class (mocked-up fix-and-it-still-breaks) is partly attributable to inconsistent error-propagation semantics across the pipeline.

#### Decision 8: FINISH-BRANCH.md disposition
**Chose:** Delete after grep'ing all `skills/**/*.md` and `docs/**/*.md` for stragglers.
**Why:** 224-line orphan, never invoked by `autopilot.sh`. The autopilot stops at verification by design (`autopilot.sh:17-18`); merging is a separate manual step via `finishing-a-development-branch`. FINISH-BRANCH.md predates that decision. Per the project scan: one mention in `finishing-a-development-branch/SKILL.md` referring to autopilot, not to FINISH-BRANCH.md itself. Round 1 fact-check found one active reference in `docs/plans/2026-04-08-plugin-split-plan.md:410` (an open plan that instructs updating FINISH-BRANCH.md) — that plan must be updated or closed before deletion.
**Alternatives rejected:**
- Keep as alternative manual-merge path: no documented user flow currently surfaces it; maintaining dead code is not free.

#### Decision 9: Mid-flow human review forbidden by contract
**Chose:** writing-plans contract explicitly forbids mid-flow "human review," "user verifies," "review the [X]," and similar judgment-pause tasks. Verifier critic flags them as HIGH severity. Anti-pattern documented in this design's "Anti-Pattern: Mid-Flow Human Review" section.
**Why:** The autopilot's whole value is unattended completion. The user reviews at the END, when verify halts cleanly or autopilot completes. Mid-flow review defeats the value proposition. The existing Manual Steps Policy uses "manual" too narrowly — it covers commands the user runs, not judgment-based pauses framed as "verification." User reports the recurrence directly: "you keep writing into the plan that a certain task needs 'human review' before continuing but the whole point is to do the whole thing and then I only look at the end."
**Alternatives rejected:**
- Trust the existing Manual Steps Policy: empirically doesn't catch judgment-based review tasks; user reports recurring incidents.
- Make autopilot tolerant (skip "human review" tasks silently): worst-case behavior — plan author thought a check was needed; silently skipping makes failures look like passes. Better to reject the plan at writing-plans time than to skip at execution.
- Auto-rephrase tasks to remove review language: heuristic rewrites lose author intent; explicit refusal forces a real fix.
