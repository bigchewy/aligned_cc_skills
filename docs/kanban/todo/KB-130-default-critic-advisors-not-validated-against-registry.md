# KB-130: default_critic_advisors IDs not validated against advisors/registry.yaml

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review of feature/framework-runner-refactor)
- **Location:** `e2e/tests/test_registry_schemas.py:205-215` and `frameworks/registry.yaml` (154 entries with optional default_critic_advisors)
- **Observed:** `default_critic_advisors` values in `frameworks/registry.yaml` are checked only for list shape — the IDs themselves are not cross-validated against `advisors/registry.yaml`. The field is load-bearing in `skills/brainstorming/modes/authoring.md` Phase 3 (line 183): if present and non-empty, those advisor IDs become the critic pool instead of the deliverable_type defaults. A renamed or removed advisor ID would silently dispatch to a non-existent advisor.
- **Expected:** Add a referential-integrity test analogous to the existing `follow_on_frameworks` cross-check (test_registry_schemas.py:210-213): for each framework's `default_critic_advisors` list, assert every ID matches an `id` in `advisors/registry.yaml`.
- **Why out of scope:** Cosmetic — no failure observed yet. The branch is already large; deferring to a focused follow-up.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
