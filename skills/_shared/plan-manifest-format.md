# Plan Manifest Format

Plans MAY include an OPTIONAL YAML front-matter block declaring the executor environment requirements. The autopilot's preflight phase reads this manifest and halts cleanly when the environment cannot satisfy it.

## Schema

```yaml
---
mcp-tools-required:
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_snapshot
env-vars-required:
  - SUPABASE_URL
  - OPENAI_API_KEY
---
```

Both fields are arrays of strings. Both are optional; an empty list is equivalent to omitting the field. A plan with no front-matter is valid (preflight returns exit 3 = skip).

## Authoring

The `writing-plans` skill auto-generates this manifest from the plan body before the critique panel runs. The Verifier critic enforces structural coherence: every `mcp__*__*` body reference must appear in `mcp-tools-required`, and vice versa. The author does not edit the manifest by hand — it is regenerated whenever the plan body changes. (See "Manifest authoring visibility" in the design doc — manifest writes are autonomous; the user reviews the manifest by reading the committed plan, not via interactive prompt.)

## Validation (autopilot preflight)

Preflight applies these probes against the worktree environment:

**MCP tools.** For each `mcp-tools-required[i]`:
1. Extract the server prefix (e.g., `mcp__playwright__browser_navigate` → `playwright`).
2. Walk `.mcp.json` files **upward from the worktree CWD**: worktree → main repo → `$HOME/.claude/`. Build the merged server set (later levels do not override earlier). If no `.mcp.json` defines the server prefix, halt with `reason: mcp_unreachable`.
3. Read `.claude/settings.local.json` (in the worktree first, then main repo, then `$HOME/.claude/`). Concatenate the `permissions.allow` arrays. If the exact tool string is absent, halt with `reason: mcp_tool_not_allowlisted`.

**Edge cases:**
- Symlinked worktrees: resolve the worktree path with `pwd -P` before walking.
- Conflicting `.mcp.json` at different levels: first definition wins (worktree > main > home).
- Missing `permissions.allow` field: treat as empty array (every tool fails the allowlist check).
- Missing `settings.local.json`: treat as `{"permissions":{"allow":[]}}`.

**Env vars.** For each `env-vars-required[i]`, probe `[ -n "${VAR:-}" ]` against the worktree shell environment. Halt with `reason: env_var_missing` on the first unset variable. Multiple missing variables collapse into one halt sentinel listing all of them in `details:`.

## Coherence check (Verifier critic)

The writing-plans Verifier runs a deterministic structural diff:
- Every `mcp__*__*` reference in the plan body MUST appear in `mcp-tools-required`.
- Every `mcp-tools-required` entry MUST appear at least once in the plan body.
- Both directions: same rule for `env-vars-required` vs `process.env.*` / `os.environ.*` / shell `${VAR}` references.

**Scope:** the body scan SKIPS:
- Fenced code blocks (``` ``` `) with language tags `text`, `markdown`, or `yaml` (where examples shouldn't trigger detection)
- Blockquoted lines (`> ...`)
- Inline code spans (`` `...` ``) — only checked for env-var refs in surrounding prose, not the inline contents

Mismatch is flagged HIGH severity. The Verifier reports the missing entries in both directions; the author re-runs manifest generation rather than editing by hand.
