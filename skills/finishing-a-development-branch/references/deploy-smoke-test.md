# Deploy to Production + Smoke Test — Workflow Reference

Extracted from finishing-a-development-branch SKILL.md. Invoked from Step 4 Option 2.

## Contents

- Step 4a: Merge to main
- Step 4b: Push to remote
- Step 4c: Worktree cleanup
- Step 4d: Wait for deployment
- Step 4e: Run smoke tests
- Step 4f: Report results

---

#### Option 2: Deploy to Production + Smoke Test

**Parse scope:** If the user said "full smoke tests" or similar, set scope to FULL. Otherwise default to QUICK.

**Step 4a: Merge to main** — Same as Option 1's full merge logic (checkout, pull, merge, including untracked-file error recovery).

**Step 4b: Push to remote** — `git push origin <base-branch>`. Record push timestamp for deployment matching.

**Step 4c: Worktree cleanup** — Run Step 5 now.

**Step 4d: Wait for deployment**

First, read `.claude/deployment.json` from the project root. This file configures per-project deployment behavior:

```json
{
  "productionUrl": "https://example.vercel.app",
  "vercelMcpAccess": true,
  "deployWaitSeconds": 120,
  "smokeTestProfiles": ["playwright-full", "playwright-summaries"]
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `productionUrl` | (none) | URL to smoke test against |
| `vercelMcpAccess` | `true` | Whether Vercel MCP tools can access this project's deployments |
| `deployWaitSeconds` | `120` | Seconds to wait before smoke testing (Path B only) |
| `smokeTestProfiles` | `[]` | Playwright MCP profile names. Empty array = no auth, use headless |

**If `.claude/deployment.json` doesn't exist:** Create it interactively. Ask the user:
1. What is the production URL? (e.g., `https://myapp.vercel.app`)
2. Do you have Vercel MCP access to this project's deployments? (yes/no, default: no)
3. Do you use named Playwright auth profiles for smoke tests? (if yes, list them; default: none)

Write the answers to `.claude/deployment.json`, commit it, and continue. This ensures the config exists for all future runs.

**Path A: `vercelMcpAccess` is true (or config missing)**

Read `.vercel/project.json` from the main repo path to get `projectId` and `orgId`:

```bash
cat <main-repo-path>/.vercel/project.json
```

If `.vercel/project.json` doesn't exist, fall through to Path B.

Use the Vercel MCP tool `list_deployments` with the `projectId` and `teamId` (which is the `orgId` value). Poll every 30 seconds (initial estimate — tune based on observed behavior). Look for a deployment in the response array where:
- `target` is `"production"`
- `meta.githubCommitRef` is `"main"`
- `created` (ms timestamp) is after the push timestamp
- `state` is `"READY"`

Verified API response fields: `created` (number, ms), `state` ("READY"/"ERROR"), `target` ("production"), `meta.githubCommitRef`, `meta.githubCommitSha`, `inspectorUrl`.

**Note:** This assumes only one Claude Code instance uses Playwright MCP at a time.

**If deployment fails:** Report and skip smoke tests. Covers: state `ERROR` (show deployment URL), API call failure (show error message), timeout after 10 minutes (suggest checking dashboard).

**Path B: `vercelMcpAccess` is false (or `.vercel/project.json` missing)**

No Vercel API available. Wait `deployWaitSeconds` (default 120s) for auto-deploy, then check if production URL responds (Playwright navigate, expect 2xx). If no response or no `productionUrl` configured, report and skip smoke tests.

**Step 4e: Run smoke tests**

Read `e2e/smoke-test-flows.md` for the flow definitions. The production URL comes from `productionUrl` in `.claude/deployment.json` (Path B) or the Vercel deployment URL (Path A).

Before each Playwright session, kill stale Chrome: run `pkill -f mcp-chrome` (ignore if no matching processes), wait 2s, verify clean with `pgrep -f mcp-chrome`.

**If `smokeTestProfiles` is empty** (or no `e2e/auth/` directory): Run flows directly using `playwright-headless`. QUICK = flows tagged `[QUICK]`, FULL = all flows.

**If `smokeTestProfiles` has entries:** For each profile, navigate with that profile's Playwright MCP connection. If redirected to `/login`, report auth expired and skip that profile. Otherwise run flows based on scope. Kill stale Chrome between profiles.

**Step 4f: Report results** — Show deployment info (commit, URL, verification method) and PASS/FAIL per flow with failure details. Smoke test failures are non-blocking — code is already deployed. Then: Archive plan docs (Step 6).
