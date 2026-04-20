# KB-044: Autopilot lacks "manual-deploy artifact" concept — ships code dependent on unapplied migrations/env/cron/etc

- **Type:** bug
- **Discovered during:** root-cause-analysis (high severity)
- **Location:** `skills/writing-plans/SKILL.md:96-109`, `skills/finishing-a-development-branch/SKILL.md:46-102`, `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md` (entire scope)
- **Observed:** The autopilot workflow (brainstorming → writing-plans → executing-plans → finishing-a-development-branch) has no detection for files whose creation implies a non-automatable production step. `writing-plans` has a `Manual Steps (Post-Automation)` section in its plan schema and names "running a migration against production" as an example, but nothing populates it automatically. `finishing-a-development-branch`'s Step 0 Deployment Audit is scoped to Vercel runtime/bundler pitfalls — it never scans the diff for manual-deploy artifacts. No skill reads nested `CLAUDE.md` files (e.g., `supabase/CLAUDE.md`) that declare project-local deploy conventions. Failure observed: a feature branch with 5 Supabase migrations + middleware depending on them shipped to prod with migrations unapplied; broke `/login` flow for a week until manually diagnosed.
- **Expected:** The plugin needs a typed concept of "manual-deploy artifact" implemented in three layers:
  1. **Foundation:** `skills/_shared/manual-deploy-artifact-catalog.md` listing artifact classes (migrations, env vars, cron, DNS, webhooks, edge functions, RLS, queues, secrets) with per-entry detector, prod-step description, evidence format, and project-convention-doc path.
  2. **Root fix (writing-plans):** new "Manual Deploy Artifact Scan" step that walks planned file paths, matches against the catalog, and auto-injects entries into the `## Manual Steps (Post-Automation)` section. Verifier critic enforces coverage.
  3. **Enforcement (finishing-a-development-branch):** new Step 0.5 that scans the branch diff against the catalog and **hard-gates** merge when catalog-matched files exist without documented evidence in the plan. Evidence must be pasted/typed — not a yes/no checkbox (reflexive-yes was the original failure mode).
- **Why out of scope:** Fix spans 3 skills + new shared catalog; requires design, task plan, and test-fixture project. See design doc in `docs/plans/2026-04-20-manual-deploy-artifacts-rca-design.md`.
- **Severity:** HIGH
- **Created:** 2026-04-20
