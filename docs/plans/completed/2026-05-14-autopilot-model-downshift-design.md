# Autopilot Model Downshift — Design

**Status:** Ready for plan
**Date:** 2026-05-14
**Motivation:** June 15, 2026 — Anthropic separates programmatic (`claude -p`, Agent SDK) usage from interactive subscription rate limits. Max 20x plan gets $200/mo dedicated Agent SDK credit. Daily autopilot use on Opus 4.7 will exhaust this credit; overflow at API rates is not acceptable to the user.

## Problem

Today, every `claude -p` invocation in the autopilot pipeline inherits the CLI default model (currently Opus 4.7 for this user). There is no per-phase model control. Two call sites:

- `docs/ralph_loops/lib/process.sh:90` — shared by `phases/plan.sh`, `phases/mockup.sh`, `phases/verify.sh`
- `docs/ralph_loops/run-ralph.sh:238` — the 50-iteration Ralph execution loop (dominant cost)

Neither passes `--model`. Settings.json has no `model` key.

**Cost concentration:** Ralph execute loop runs up to 50 iterations × 15-min timeout = 750 min worst case. The plan, mockup, and verify phases combined are ~225 min worst case. Conservative estimate: Ralph is 70–80% of total cost per autopilot run.

## Solution

Route each phase to the cheapest model that can do its work, using **per-phase env vars** (not `--model` flag plumbing). Set `CLAUDE_CODE_SUBAGENT_MODEL` alongside `ANTHROPIC_MODEL` so spawned sub-agents don't leak the savings. Adopt `--bare` mode for headless invocations per Anthropic's published guidance.

### Per-phase model assignments

| Phase | Model | Rationale |
|---|---|---|
| **Plan** (`phases/plan.sh`) | Opus | Architecture decisions, critique panel with sub-agents, 2-round synthesis. Anthropic's `opusplan` alias codifies this pattern. |
| **Ralph execute** (`run-ralph.sh`) | Sonnet | Anthropic docs call Sonnet "daily coding tasks". 50 iterations of mechanical TDD (test → impl → commit) is the canonical use case. Highest-leverage downshift. |
| **Mockup fidelity** (`phases/mockup.sh`) | Sonnet | Multi-file diff reasoning between HTML mockups and source. Haiku tempting but no published benchmark for this task profile. Sonnet now; A/B Haiku in a follow-up. |
| **Verify** (`phases/verify.sh`) | Sonnet | Verify must interpret failing stack traces and build errors. A Haiku misclassification ("transient flake" when it's a real bug) is the worst-case outcome of the entire change. Sonnet, not Haiku. |

### Mechanism

**Each phase script exports two env vars before invoking `run_claude_phase`:**

```bash
# Example: phases/plan.sh
export ANTHROPIC_MODEL="${PLAN_MODEL:-opus}"
export CLAUDE_CODE_SUBAGENT_MODEL="${PLAN_SUBAGENT_MODEL:-opus}"
```

```bash
# Example: phases/verify.sh
export ANTHROPIC_MODEL="${VERIFY_MODEL:-sonnet}"
export CLAUDE_CODE_SUBAGENT_MODEL="${VERIFY_SUBAGENT_MODEL:-sonnet}"
```

```bash
# Example: run-ralph.sh (before line 238)
export ANTHROPIC_MODEL="${RALPH_MODEL:-sonnet}"
export CLAUDE_CODE_SUBAGENT_MODEL="${RALPH_SUBAGENT_MODEL:-sonnet}"
```

The defaults are baked-in (sonnet for ralph/verify/mockup, opus for plan). The `${VAR:-default}` pattern preserves user override via environment.

**Add `--bare` to both `claude -p` call sites:**

- `lib/process.sh:90` — `claude -p --bare - < "$PROMPT_FILE" &`
- `run-ralph.sh:238` — `claude -p --bare - < "$PROMPT_FILE" &`

Per Anthropic docs (https://code.claude.com/docs/en/headless): `--bare` is "the recommended mode for scripted and SDK calls, and will become the default for `-p` in a future release." Skips MCP/hooks/CLAUDE.md auto-discovery — independent token-spend reduction.

**Sub-agent frontmatter audit:** before shipping, grep `agents/*.md` for any `model:` field in frontmatter. Subagent-level `model:` overrides `CLAUDE_CODE_SUBAGENT_MODEL` per Anthropic docs (https://code.claude.com/docs/en/sub-agents). If any subagent pins Opus, decide whether that pinning is intentional (architect-grade reasoning) or stale.

## What this does NOT change

- `MAX_ITERATIONS=50` cap stays. Cost reduction comes from model choice, not iteration cap.
- Timeout values (`PHASE_TIMEOUT`, `MOCKUP_TIMEOUT`, `ITERATION_TIMEOUT`) stay.
- Prompt file structure stays. Cache keys are per-model anyway; staying on one model per phase preserves intra-phase caching.
- The Phase 3.5 (mockup) → Phase 4 (verify) sequencing in `autopilot.sh` stays.

## Risks

1. **Sonnet Ralph produces more failed tests, triggering more iterations.** Net savings could be less than projected. Mitigation: `CONSECUTIVE_FAILURES` cap at 3 (`run-ralph.sh:276-279`) bounds runaway behavior. Monitor first 3 runs.
2. **Subagent frontmatter pinning.** Any agent file with `model: opus` in frontmatter overrides the env var. Audit before shipping.
3. **`--bare` skips CLAUDE.md auto-discovery.** Phase prompts may rely on something in a project's CLAUDE.md. Verify each phase prompt explicitly states what it needs (path, skill file, etc.) rather than relying on auto-loaded context. Spot-check `WRITE-PLAN.md`, `EXECUTE-PLAN.md`, `MOCKUP-FIDELITY.md`, `VERIFY-BRANCH.md`.

## Success criteria

- A full autopilot run on Sonnet ralph + Sonnet verify + Sonnet mockup + Opus plan completes without quality regression (test pass rate, build pass rate, final code review acceptance) compared to baseline Opus-only run.
- Programmatic credit consumption per run drops by ≥50% measured against an Opus-only baseline (post-June 15 once the credit dashboard exists).
- Sub-agents spawned within phases use the same model as the parent phase (verifiable via logs or a dry-run check).

## Files touched

- `docs/ralph_loops/phases/plan.sh` — add `export ANTHROPIC_MODEL`, `export CLAUDE_CODE_SUBAGENT_MODEL`
- `docs/ralph_loops/phases/mockup.sh` — same
- `docs/ralph_loops/phases/verify.sh` — same
- `docs/ralph_loops/run-ralph.sh` — same, plus add `--bare` at line 238
- `docs/ralph_loops/lib/process.sh` — add `--bare` at line 90
- `docs/ralph_loops/autopilot.sh` — extend `export` lines (188, 307, 315) so phase scripts see the new env vars (caller-set overrides)
- Audit pass on `agents/*.md` — no edits expected, just verify no `model:` frontmatter conflicts

## Tests

- Unit-level smoke test: each phase script can be invoked standalone with all required env vars set; the resulting `claude -p` command line contains `--bare` and the env confirms `ANTHROPIC_MODEL` is set per phase.
- Integration test: dry-run autopilot against a trivial design doc; confirm each phase logs which model it used.
- Manual regression: one full autopilot run on a representative real plan, comparing against the most recent Opus-only run for quality and runtime.

## Decision log

- **Why env vars instead of `--model` flag?** Single source of truth per phase; no plumbing through `run_claude_phase`. Anthropic publishes `ANTHROPIC_MODEL` as the supported env var for session model selection.
- **Why not `opusplan` for the plan phase?** `opusplan` switches Opus→Sonnet at the plan→execute boundary *within a single Claude Code session*. Autopilot's plan and ralph are separate `claude -p` processes, so `opusplan` doesn't apply directly. Setting `ANTHROPIC_MODEL=opus` in plan.sh and `=sonnet` in run-ralph.sh achieves the same effect across process boundaries.
- **Why Sonnet for verify, not Haiku?** Architect pushback. Verify interprets failing stack traces and build errors; a Haiku misclassification ("transient flake" vs real bug) is the worst-case outcome of this entire change. Sonnet is the floor.
- **Why Sonnet for mockup, not Haiku?** No published Anthropic benchmark for Haiku on multi-file HTML-vs-source diff reasoning. Conservative default; A/B Haiku in a follow-up after Sonnet baseline is established.
- **Sub-agent inheritance is load-bearing.** Without `CLAUDE_CODE_SUBAGENT_MODEL`, Ralph's research sub-agents and Plan's critique sub-agents stay on default Opus, leaking most of the savings. This is the single highest-risk implementation detail.

## References

- Anthropic — [Claude Code model configuration](https://code.claude.com/docs/en/model-config)
- Anthropic — [Run Claude Code programmatically (headless)](https://code.claude.com/docs/en/headless)
- Anthropic — [Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- Anthropic — [Use the Claude Agent SDK with your Claude plan](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)
