# KB-149: Move mock error path coverage check from code-reviewer to Step 3 as static lint

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch RCA (2026-05-21)
- **Location:** `agents/code-reviewer.md:88-115` (Section 5 "Mock Error Path Coverage Inspection") and `skills/finishing-a-development-branch/SKILL.md:155-178` (Step 3 "Verify Tests")
- **Observed:** Section 5 of the code-reviewer agent prompt is a deterministic, file-based check — for each `mockResolvedValue` in a test file, confirm a matching `mockRejectedValue` exists. It does not require LLM judgment. It currently lives in the prose code-reviewer alongside six other sections that DO require judgment (plan alignment, architecture, security). This coupling created the 2026-05-21 incident where the reviewer reached for `npm test` to "verify" mock coverage. Slim #1 Option B (adding a PROHIBITED OPERATIONS block) closed the immediate execution-overreach risk, but Section 5 still lives in the wrong agent — a static check buried in a judgment agent's prompt.
- **Expected:** Move the mock-coverage check to Step 3 (Verify Tests) as a static pre-check that runs before `npm test`. Implement as a small grep/awk script (~30-60 lines) or a small Node.js linter. Block with CRITICAL severity if unbalanced mocks are found. Then remove Section 5 from `agents/code-reviewer.md` (reducing the reviewer from 7 to 6 sections) and remove the "Pay special attention to Section 5" line from the dispatch prompt in `references/code-review-scan.md`.
- **Why out of scope:** Implementing the lint script correctly (handling `describe` block scoping, matching mocks by function name across success/failure pairs, managing false positives) is non-trivial — likely 1–2 hours of focused work plus tests. Slim #1 Option B closed the dangerous behavior with a 20-line edit; this entry captures the structural fix for when there's appetite to do it right.
- **Severity:** MEDIUM
- **Created:** 2026-05-21
