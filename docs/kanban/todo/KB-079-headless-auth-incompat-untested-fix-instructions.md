# KB-079: `headless_auth_incompat` fix-instructions never tested for stable substrings

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code-reviewer Step 1d on simplify-autopilot-halt-merge-handling)
- **Location:** `e2e/tests/test_halt_protocol.py:67-72` (`test_format_halt_echoes_canonical_fix` parametrize) and `docs/ralph_loops/lib/halt.sh:110-136` (the `headless_auth_incompat` heredoc)
- **Observed:** `test_format_halt_echoes_canonical_fix` parametrizes over 4 halt reasons (down from 5 after the simplify-halt branch dropped `uncommitted_main`). `headless_auth_incompat` exists in `format_halt()`, has a real `write_halt` callsite in `preflight.sh:50`, and is documented in the taxonomy table — but it has never been included in this parametrize. A typo in its heredoc (instructions about `--bare`, ANTHROPIC_API_KEY, the canonical invocation, etc.) would not trip any test. The drift-detector test only enforces case-vs-callsite parity, not heredoc content.
- **Expected:** Add a parametrize row asserting on a stable substring, e.g., `("headless_auth_incompat", "--bare")` or `("headless_auth_incompat", "ANTHROPIC_API_KEY")`. Pick a substring that would change if the heredoc was rewritten to convey something materially different.
- **Why out of scope:** The simplify-halt branch only modified rows it removed; adding a row is a separate concern. Pre-existing gap, surfaced now because removing `uncommitted_main` left only 4 of 6 reasons covered.
- **Severity:** MEDIUM
- **Created:** 2026-05-16
