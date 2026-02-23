# KB-012: README.md changelog is stale

- **Type:** doc-staleness
- **Discovered during:** doc-staleness-detector
- **Location:** `README.md`
- **Observed:** The Changelog section (lines 186-212) stops at version 0.3.0. The plugin is now at version 0.3.2 (per `.claude-plugin/plugin.json`). Two version bumps are unlogged:
  - **0.3.1** (commit c29378a): Finishing-skill regression fixes — restored deploy+smoke test option, worktree cleanup, core principle archive step, KB commit worktree guidance, red flags section, quick reference tables, common mistakes entries, CRITICAL always-run-from-main-repo section.
  - **0.3.2** (commit 742ccf1): Token optimization — trimmed verbosity in create-new-skill and finishing-a-development-branch, condensed rationalizations tables to top 4 entries, extracted shared Kanban entry format to `skills/_shared/kanban-entry-format.md`.
  - **Post-0.3.2 (unreleased):** Business skills sync (major enhancements to all 4 business skills: autonomous mode, dual-critic architecture, issue discovery protocol, Phase 0 multi-agent investigation, etc.), kanban HTML dashboard feature added then partially removed, model frontmatter added to agents, plan-file status marking in executing-plans, dashboard note in writing-plans.
- **Expected:** Changelog should include 0.3.1 and 0.3.2 entries summarizing the above changes. A version bump to 0.3.3 (or 0.4.0 given the scope of business-skills-sync) with its own changelog entry may also be warranted for the unreleased work.
- **Source commits:** 54 commits since doc was last updated (Feb 17 - Feb 23)
- **Severity:** MEDIUM
- **Created:** 2026-02-23
