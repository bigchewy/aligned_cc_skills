# Lessons Learned: `claude --bare` is incompatible with Max-plan OAuth auth

- **Date:** 2026-05-14
- **Fix branch:** `fix/autopilot-bare-oauth-incompat`
- **Originating plan:** `docs/plans/completed/2026-05-14-autopilot-model-downshift.md` (Task 6)
- **Originating commit:** `2d883ef` — "task 6: adopt claude -p --bare for headless calls"

## What happened

Autopilot was upgraded to invoke `claude -p` with the `--bare` flag at two
headless call sites (`docs/ralph_loops/lib/process.sh:90` and
`docs/ralph_loops/run-ralph.sh:247`). The motivation was sound: per
Anthropic's headless-mode docs, `--bare` is the recommended scripted mode
and is slated to become the default for `-p` in a future release. It
skips MCP servers, hooks, plugin sync, attribution, auto-memory,
background prefetches, keychain reads, and CLAUDE.md auto-discovery —
real token-spend reduction.

The motivating plan included a "Task 5 audit" that verified phase prompts
did not depend on CLAUDE.md auto-discovery, then adopted `--bare` based
on a `verdict: PROCEED` outcome. That audit was a good idea.

The audit did **not** cover the one bullet inside `claude --help` that
sinks the whole plan for Max-plan users:

> `--bare` ... Anthropic auth is strictly ANTHROPIC_API_KEY or
> apiKeyHelper via --settings (OAuth and keychain are never read).

Max-plan users authenticate Claude Code via OAuth. With `--bare` in the
call site, the headless invocation refuses to read OAuth credentials and
immediately exits with `Not logged in · Please run /login`. The plan
phase never writes its sentinel, and autopilot dies on the downstream
"Could not find the plan file after Phase 1." error — which is the
symptom the user sees, three layers removed from the real cause.

## Why this slipped through

Three contributing factors:

1. **Audit scope was prompt-content-only, not auth-pattern.** Task 5 of
   the downshift plan asked: "does any phase prompt depend on
   auto-discovered context?" That's one of six things `--bare` changes.
   Auth-source was bundled into the same flag but never enumerated as a
   separate dimension to check.

2. **Env-var preflight had recently been removed.** Earlier in the same
   May 2026 development window, commits `96c417c` → `6ebfcd2` → `a2e7a39`
   removed env-var preflight validation. That removal was correct on its
   own (it was over-eager and rejected valid configurations). But the
   combination "preflight no longer checks API-key vars" + "headless flag
   now silently requires API-key vars" produced a silent auth failure
   with no early signal — the two changes were independently right and
   jointly wrong.

3. **Author-environment blind spot.** The repo author tests autopilot
   under OAuth. The CI environment (where `--bare` works fine because an
   API key is set) gave green tests. The author's local environment
   produced the failure, but the failure surfaces as "plan file missing"
   rather than "auth misconfigured" — easy to misdiagnose as a Ralph
   timing or sentinel-write bug rather than an auth-flag bug.

## Fix

Two-file revert plus tightened tests plus a preflight guard:

1. **Code (revert):**
   - `docs/ralph_loops/lib/process.sh:90` — `claude -p --bare - < "$PROMPT_FILE"` → `claude -p - < "$PROMPT_FILE"`
   - `docs/ralph_loops/run-ralph.sh:247` — same change.

2. **Tests (encode the constraint with opposite polarity):**
   - `test_lib_process_uses_bare_flag` → `test_lib_process_does_not_use_bare_flag`
   - `test_run_ralph_uses_bare_flag` → `test_run_ralph_does_not_use_bare_flag`
   - `test_plan_phase_invokes_claude_with_bare_flag` → `test_plan_phase_does_not_invoke_claude_with_bare_flag`
   - Docstrings now explain *why* `--bare` is forbidden, not just *that* it is.

3. **Defense-in-depth (preflight guard):**
   - `docs/ralph_loops/phases/preflight.sh` now scans the two known
     headless call sites for `--bare`. If found, it halts with
     `headless_auth_incompat` and a fix-instructions block that points
     here. New halt-reason case is added to `lib/halt.sh` and documented
     in `skills/_shared/autopilot-halt-format.md`.
   - This is belt-and-suspenders over CI: catches the case where someone
     runs autopilot from a branch that bypassed the test suite.

4. **Kanban cleanup:**
   - `KB-067` (which assumed "the `--bare` flag is now permanent") was
     moved to `done/` with a resolution note flipping its polarity.

## Token-spend benefits NOT recovered

The non-auth bits of `--bare` — skip hooks, LSP, plugin sync,
attribution, auto-memory, background prefetches, CLAUDE.md
auto-discovery — are real efficiency wins for scripted invocations.
None of them are exposed as individual CLI flags in the current
Claude Code release; `--bare` is the only way to opt into them, and it
bundles the auth restriction.

This is a gap for any subscription user who scripts Claude Code. Not a
bug in this repo, but a constraint we have to live with.

**Recommended upstream feedback to Anthropic:** add either (a) per-bit
opt-in flags (`--no-claude-md`, `--no-hooks`, `--no-mcp`, etc.) or
(b) a `--bare-no-api-key-restriction` variant that preserves OAuth /
keychain auth while skipping the other features. Until then, autopilot
takes the token-spend hit. The model-downshift work that motivated this
plan (Sonnet for ralph/mockup/verify, Opus retained for plan-writing)
remains in place and continues to be the primary cost lever.

## What to check next time a plan proposes a CLI flag change

When a plan adds, removes, or changes a CLI flag passed to `claude`:

1. **Read the full `--help` entry for the flag, not the docs page.**
   `claude --help` is the authoritative source for behavior; marketing
   docs sometimes omit the auth bullet that just sank this plan.

2. **Audit auth implications first, separately from content
   implications.** A flag can change six things; "does it change which
   auth sources are read" is a distinct question from "does it change
   what context is loaded."

3. **Test under your own auth pattern, not just CI's.** If you
   authenticate via OAuth and CI uses an API key, run the affected
   scripts locally end-to-end after the change. CI green is not the
   same as user-environment green.

4. **Watch for adjacent recent removals.** If preflight validation was
   recently softened, a flag that silently requires the removed
   validation's prerequisites is a setup for a delayed, hard-to-diagnose
   failure. Search recent commits for "preflight" or "remove
   validation" when introducing a flag that depends on env state.

5. **Encode the constraint in tests with opposite polarity if you
   reverse course.** A test that asserts `--bare in args` and a test
   that asserts `--bare not in args` are mirror images. After reverting
   a feature, flip the assertions so the constraint is permanent, not
   ambient — and explain *why* in the docstring so future readers don't
   re-introduce it under the assumption that "the absence test must be
   stale."
