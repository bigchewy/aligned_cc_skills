# KB-054: format_halt MCP reason cases (mcp_unreachable, mcp_tool_not_allowlisted) untested

- **Type:** test gap
- **Discovered during:** finishing-a-development-branch (code-reviewer)
- **Location:** `e2e/tests/test_halt_protocol.py` (test exists for `env_var_missing`, missing for the two MCP reasons)
- **Observed:** `test_format_halt_echoes_canonical_fix` exercises only the `env_var_missing` case. The `mcp_unreachable` and `mcp_tool_not_allowlisted` cases in `lib/halt.sh::format_halt` are reachable in production via `preflight.sh`, but no test asserts their canonical fix-instructions text. A typo in either heredoc would not fail any test.
- **Expected:** Add two assertions to (or extend) `test_format_halt_echoes_canonical_fix`: one calling `format_halt mcp_unreachable` and asserting the output contains a stable substring (e.g., "Define the server in .mcp.json"), and one calling `format_halt mcp_tool_not_allowlisted` and asserting on a stable substring (e.g., "settings.local.json allowlist").
- **Why out of scope:** The C2 fix on this branch covered the function-level paths in `check_mcp_tool` (which echoes the reason ID); these tests would cover the user-facing fix-instructions text in `format_halt`. Distinct concern.
- **Severity:** LOW
- **Created:** 2026-04-30
