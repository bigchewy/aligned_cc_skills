# KB-157: Architecture doc update needed — visualization-runner extraction

- **Type:** architecture-doc-update-needed
- **Discovered during:** finishing-a-development-branch
- **Location:** `skills/_shared/visualization-runner.md`, `skills/visualize-design/SKILL.md`
- **Observed:** Branch `feature/visualization-runner-extraction` adds a new shared module (`skills/_shared/visualization-runner.md`), a new skill (`skills/visualize-design/`), and rewires three diagram agents (`agents/flowchart-generator.md`, `agents/architecture-diagram-generator.md`, `agents/mockup-generator.md`) plus the brainstorming visualization protocol to reference the extracted runner. No architecture documentation reflects this new shared-runner structure (`docs/architecture.md` does not exist).
- **Update (2026-08-31):** All three agents named above, plus `session-document-generator.md`, were deleted entirely on `worktree-visualization-agent-cleanup` — none had a live caller. The architecture-documentation ask below still stands; only the "these three were rewired" framing above is now stale.
- **Expected:** Document the visualization-runner architecture — which skills/agents consume the shared runner and the token-resolution ladder ownership — during Kanban triage.
- **Why out of scope:** Architecture diagram work happens during triage with proper attention, not on the merge path (finishing skill Step 6 rule).
- **Severity:** LOW
- **Created:** 2026-06-11
