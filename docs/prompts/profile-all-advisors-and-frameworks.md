# Prompt: Complete Advisor & Framework Profiling

Copy and paste this into a new Claude Code session in the `aligned_cc_skills` repo.

---

I need to complete the metadata profiles for all advisors and frameworks in the Aligned plugin so that every entry in both registries is fully populated and eligible for contextual recommendation scoring.

## What "complete" means

**Advisors** (`advisors/registry.yaml`) — 35 entries are currently unprofiled (they have a `note: "Not yet profiled with evaluation expertise."` field). Each needs three fields added:

- `evaluation_expertise`: 2-3 sentences describing what this advisor evaluates and catches. Written from the advisor's perspective — what do they look for, what do they flag, what patterns do they spot? Derive this from the advisor's prompt file (`advisors/prompts/{id}.md`).
- `best_for`: 1-2 sentences describing the kinds of work this advisor is best suited for. Think: what task contexts should trigger a recommendation of this advisor?
- `not_for`: 1-2 sentences describing work this advisor should NOT be applied to. What domains are outside their expertise or would produce bad advice?

Also populate `domains` if currently empty (`domains: []`). Use 3-5 keyword tags that describe the advisor's area of expertise, matching the tag style of existing profiled entries.

Remove the `note` field after profiling.

**Reference a profiled entry** for calibration — April Dunford (`id: april-dunford`) is a good example of the target quality.

**Frameworks** (`frameworks/registry.yaml`) — check for any entries with empty `purpose` fields (`purpose: ""`) and fill them in. The purpose should be a concise description of what the framework does, derived from the framework's `prompt.md` file. Also verify that `domains` and `use_when` fields are populated and accurate for every entry.

## Process

Use `/aligned:brainstorming` to design your approach, then execute it. The work is mostly reading each advisor's prompt file, understanding their expertise, and writing accurate metadata. Batch the work — don't do one advisor at a time in separate commits.

**Suggested batches:**
1. Profile all unprofiled advisors (read each prompt file, write the three fields + domains)
2. Audit framework registry for empty/weak fields and fix them
3. Run the schema validation tests (`e2e/tests/test_registry_schemas.py`) to confirm everything parses
4. Commit with a message like "feat: complete advisor and framework profiling for contextual recommendation"

## Quality bar

After this work is done, every advisor and every framework should be eligible for the contextual recommendation feature described in `docs/plans/2026-04-14-contextual-recommendation-design.md`. That means:
- Every advisor has non-empty `domains`, `evaluation_expertise`, `best_for`, and `not_for`
- Every framework has non-empty `domains`, `use_when`, and `purpose`
- No `note: "Not yet profiled"` entries remain
- Schema validation tests pass
