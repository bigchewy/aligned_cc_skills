# Autopilot Halt Format

The autopilot pipeline halts cleanly via a `.autopilot-halt` sentinel written by any phase. The orchestrator detects the sentinel after a phase exits with code 2, prints the formatted reason, and exits 0 — halts are NOT failures.

## Sentinel format

Newline-delimited `key: value`, with `fix-instructions` as a YAML block-literal:

```
reason: <reason-id>
phase: <phase-name>
log: <absolute path to log file>
next-action: <one-line>
fix-instructions: |
  Multi-line, indent-friendly. Tells the user EXACTLY what to do.
```

Required fields: `reason`, `phase`, `log`, `next-action`. Optional: `fix-instructions` (centralized in `lib/halt.sh` keyed by reason; phase scripts pass details only).

## Write protocol

1. Phase script calls `write_halt <reason> <phase> [details]` from `lib/halt.sh`.
2. `write_halt` writes to `$HALT_PATH.tmp` then `mv` to `$HALT_PATH` (atomic overwrite). The orchestrator exits on first halt, so only one halt is written per run.
3. Phase exits with code 2.

## Lifecycle

- Written by phase script on exit-code-2.
- Read + formatted by orchestrator after each phase.
- **Deleted explicitly by the user after they apply the fix** — the orchestrator never auto-deletes a halt sentinel, even on a successful re-run. Preserving evidence outweighs auto-cleanup convenience.
- Re-running with a stale `.autopilot-halt` present surfaces the prior sentinel via `cat $HALT_PATH` and exits 0 with re-run guidance ("Resolve the issue per fix-instructions above, delete `.autopilot-halt`, then re-run."). The user must `rm .autopilot-halt` before progress can resume.

## Reason taxonomy

| Reason | Phase | Trigger |
|---|---|---|
| `mcp_unreachable` | preflight | Plan declares an MCP tool whose server is not defined in any reachable `.mcp.json` |
| `mcp_tool_not_allowlisted` | preflight | Server defined; tool string not in `permissions.allow` |
| `manifest_malformed` | preflight | Front-matter present but unparseable / missing required fields |
| `verify_failed` | verify | Tests / build / eval failed |
| `phase_crashed` | any | Phase script exited unexpectedly; `details:` carries last 10 lines of stderr. **Skipped for transient external errors** (API stream timeouts, 5xx, network blips) so a plain re-run recovers without manual halt cleanup — see `is_transient_error` in `lib/halt.sh`. |
| `headless_auth_incompat` | preflight | A headless `claude` call site uses `--bare`, which restricts auth to API-key only and breaks Max-plan OAuth users |
| `executed_worktree_exists` | plan | Fresh plan-write requested, but a worktree for the predicted branch has commits ahead of main (resume sentinel lost) — writing a new plan would clobber executed work |

## Centralized fix-instructions (DevEx M7)

`lib/halt.sh` provides `format_halt <reason>` which echoes the canonical user-facing fix instructions for that reason. This means adding a new reason touches two surfaces (lib/halt.sh + this doc) instead of every phase script.

## Orchestrator response

When `autopilot.sh` detects `.autopilot-halt` after a phase exits with code 2:
1. Print the formatted reason to stdout (use `format_halt` output).
2. Exit 0 (NOT an error — clean halt).
3. Leave the sentinel in place so re-running surfaces "previous halt" guidance.
