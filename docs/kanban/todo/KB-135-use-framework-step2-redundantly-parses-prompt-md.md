# KB-135: use-framework Step 2 redundantly parses prompt.md when registry already has the data

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier scan of feature/framework-runner-refactor)
- **Location:** `skills/use-framework/SKILL.md:30-39`
- **Observed:** Step 1 reads `frameworks/registry.yaml` to get `name`, `advisor`, `purpose`, `category`, `domains`, and `use_when` for every framework. Step 2 then instructs reading the first line of each `prompt.md` to re-parse name and advisor from the `"You are {Advisor}, guiding someone through {Framework}"` natural-language sentence. Two sources of truth for the same fields, and Step 2 creates a parse dependency on a sentence format that has no automated guard.
- **Expected:** Make Step 2 a fallback only triggered when the registry path failed in Step 1. When the registry loads successfully, Step 2 should be a no-op. Documents the registry as authoritative for `name`/`advisor` and removes the dual-source risk.
- **Why out of scope:** Branch was framework-runner extraction, not Step 2 simplification. Both Steps 1 and 2 already exist; the redundancy is pre-existing.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
