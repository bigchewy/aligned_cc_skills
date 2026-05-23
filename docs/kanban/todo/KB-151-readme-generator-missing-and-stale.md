# KB-151: advisors/README.md and frameworks/README.md have no generator and are stale

- **Type:** bug
- **Discovered during:** writing-plans
- **Location:** `advisors/README.md`, `frameworks/README.md`
- **Observed:** Both files carry an "*Auto-generated from `<registry>.yaml`*" footer but no generator script exists (`scripts/` has `generate-catalogs.py` for HTML and `generate-framework-registry.mjs` for the framework registry, neither writes the markdown READMEs). As a result both drifted: `advisors/README.md` claimed "65 advisors" against a live registry of 76 and still listed the removed `benjamin-levine` and the nonexistent `copywriter`; `frameworks/README.md` claimed "138 frameworks" against an actual 151.
- **Expected:** A generator (e.g., `scripts/generate-readmes.py`, parallel to `generate-catalogs.py`) that rewrites both markdown READMEs from `advisors/registry.yaml` and `frameworks/registry.yaml`, so the "auto-generated" footer is true and the counts/tables cannot drift. The local-advisors plan (`docs/plans/2026-05-23-local-advisors-plan.md`, Task 17) regenerates the READMEs by hand and adds a freshness guard (`e2e/tests/test_readme_freshness.py`), but a real generator is the durable fix.
- **Why out of scope:** Building a faithful generator (profiled/unprofiled split, by-category framework breakdown) is a feature beyond the local-advisors migration; the plan handles the immediate correctness via hand-regeneration + a guard test.
- **Severity:** LOW
- **Created:** 2026-05-23
