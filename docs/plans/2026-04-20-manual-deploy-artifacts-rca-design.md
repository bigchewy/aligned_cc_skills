# RCA + Design: Autopilot Ships Code with Unapplied Manual-Deploy Artifacts

**Type:** Root-cause analysis + design doc
**Severity:** HIGH (production outage, generalized failure mode)
**Date:** 2026-04-20
**Skill of origin:** `aligned:root-cause-analysis` (high severity), refined via `aligned:brainstorming`
**Mockups:** docs/mockups/2026-04-20-manual-deploy-artifacts.html

---

## 1. The failure

The user runs the aligned plugin's autopilot workflow: `brainstorming` → `writing-plans` → `executing-plans` → `finishing-a-development-branch`. On the `feature/legal-publication` branch in the `planted` project:

1. The plan included five new SQL migrations (`supabase/migrations/021–025.sql`) as ordinary tasks.
2. `executing-plans` wrote the migration files, committed them, and ran tests. Tests use **mocked** Supabase — migrations do not need to be applied for tests to pass.
3. `finishing-a-development-branch` ran its deployment audit (Vercel runtime pitfalls), tests, build. All green. Branch merged to `main`; Vercel auto-deployed.
4. The merged code included middleware that read `profiles.tos_accepted_version` and API routes that called new RPCs — all depending on migrations **that were never applied to Supabase**.
5. The user hit the broken app a week later: infinite `/login` → `/login` redirect. ~30 minutes of debugging to discover migrations 022–025 had never been run.

The project's `supabase/CLAUDE.md` documents that migrations are applied manually via the Supabase SQL Editor. No skill in the workflow consumed that signal.

---

## 2. Root cause

> **The plugin has no typed concept of a "manual-deploy artifact"** — a file class whose creation in a diff deterministically implies a non-automatable production step (DB migrations, env vars, cron, DNS, webhooks, edge functions, RLS policies, secrets, storage buckets, queues).

Because this class does not exist as a first-class object:

- No skill detects these artifacts in planned file paths or in diffs.
- No skill reads nested `CLAUDE.md` files (e.g., `supabase/CLAUDE.md`) that declare the local convention. Claude Code auto-loads root `CLAUDE.md` only; subdirectory ones are loaded on-demand when files in them are opened — which the pipeline does not do programmatically.
- The plan schema already has a `## Manual Steps (Post-Automation)` section (`writing-plans/SKILL.md:96-109` cites "running a migration against production" as an example), but nothing populates it automatically. The policy is advisory, not enforced.
- `finishing-a-development-branch`'s Step 0 "Deployment Platform Audit" is scoped to **Vercel runtime/bundler pitfalls** (`__dirname`, `readFileSync`, `process.env[...]`, dynamic `require`, module-level state, native deps). `deployment-pitfall-catalog.md` contains zero entries for migrations or any other manual-deploy artifact. A user reasonably reads "deployment audit passed" as "all deploy risks surveyed." That trust is misplaced.

### Causal chain (5 Whys)

1. **Prod broke** (`/login` redirect loop) — middleware queried a column that didn't exist.
2. **Migrations 022–025 never ran** against Supabase.
3. **Manual application is the deploy model** for this project (per `supabase/CLAUDE.md`).
4. **No skill surfaced the manual step** — not at plan time, not at execute time, not at finish time.
5. **The concept of "manual-deploy artifact" doesn't exist in the plugin**. Without the concept, there is nothing to detect, nothing to emit to the plan, nothing to gate at merge.

### Why mocked tests didn't save us

Mocked Supabase tests answer "does the code call the API correctly." They cannot answer "does the schema the code assumes exist actually exist." Unit tests are the wrong layer for this check, but the plugin has no other layer doing it.

### Why the user's hypothesis is half-right

The user proposed a check at `finishing-a-development-branch`. That catches the failure but is insufficient alone:

- A finish-time "did you apply migrations? [y/n]" checklist is answerable with reflexive *yes* — the same class of failure as the original forgetting.
- The plan is the durable artifact the user returns to. Without a **Post-Automation** section listing the exact migration files, re-reading the plan a week later gives no reminder.
- Catching at finish time creates friction without preventing the mental model ("code shipped = done") that caused the omission.

Plan-time emission makes the manual step *visible*. Finish-time gating makes it *unskippable*. Single-layer fixes fail.

---

## 3. Generalization

This failure mode is **not migration-specific**. Any autopilot artifact that requires a manual production step has the same failure. Candidates surveyed:

| v# | Artifact | Detection signal | Failure mode if skipped |
|---|---|---|---|
| **v1** | DB migrations (Supabase/Prisma/Drizzle) | Files under `supabase/migrations/`, `prisma/migrations/`, `drizzle/` | Column/table missing at runtime |
| **v1** | `.env` additions | New `process.env.FOO` not in `.env.example`; diff on `.env.example` | Runtime crash or silent `undefined` |
| v2 | Cron / scheduled jobs | SQL `pg_cron`, `vercel.json` `crons`, GitHub Actions `schedule` | Job silently never runs |
| v2 | Feature flags | New flag key referenced in code | Feature dead on prod or live too early |
| v2 | Third-party webhooks | New handler route; new OAuth redirect URI | Vendor 4xx/5xx, silent drops |
| later | DNS / domains | New subdomain, custom domain | DNS_NOTFOUND, cert failure |
| later | Edge functions / workers | `supabase/functions/`, `workers/`, `functions/` | URL 404s at runtime |
| later | RLS policies | Bucket name, policy SQL | 403 or file-not-found |
| later | Queues / message bus | `pg_queue`, SNS/SQS refs | Messages dropped |
| later | Secrets / API keys | New key-shaped env var | Runtime crash in prod only |

**Promotion criterion (per Round 1 DevEx #5):** promote an entry from `later` to `v2` when either (a) a production incident of that type occurs in a user's project, or (b) the user explicitly requests the class. No speculative expansion. The schema is identical across all: `artifact-type-X in diff → prod step Y required → evidence Z`. Detectors differ per class; the catalog shape is uniform.

---

## 4. Fix — the three-layer design (v1 refined)

**v1 scope:** Two artifact types only — **Supabase migrations** and **`.env` / environment-variable additions**. Catalog structure supports adding more later. Rationale: prove the end-to-end pipeline with minimum surface area; the two chosen are the ones you've actually been bitten by.

### 4a. Foundation: `skills/_shared/manual-deploy-artifact-catalog.md`

**Format:** Prose markdown per-entry, organized into severity sections (`## CRITICAL`, `## MEDIUM`) with a `## Contents` TOC. The catalog is LLM-loaded via Read, not parsed — every `_shared/` file in this repo follows this convention.

**Structural note (amended per Round 1 DevEx #6):** the existing `deployment-pitfall-catalog.md` is purely prose under fixed subheadings (Why it breaks / Detection / False Positive Rules / Fix) and contains zero fenced machine-matchable blocks. This catalog is a **superset** of that shape: same severity organization and prose per-entry, PLUS a small fenced block inside each entry carrying the machine-matchable fields. The catalog file MUST start with a self-describing schema header documenting the fenced-block contract (see "Schema header" below). Drift between entries (M1 using `detector_glob`, M2 using `detector_grep`) is intentional — artifact classes have different natural detection signals — but the schema header enumerates all allowed field names.

**Schema header (top of catalog file):**

```markdown
## Schema

Every entry is a `###` heading with severity inferred from the section it's under. Each entry contains:

- Prose sections: `**Why it needs manual deploy:**`, `**Detection:**`, `**Prod step (for the plan entry):**`
- Exactly one fenced ```` ```yaml ```` block with these allowed fields:
  - `detector_glob:` OR `detector_grep:` (at least one; may have both)
  - `severity:` (`CRITICAL` | `HIGH` | `MEDIUM` | `LOW`) — must match the parent section
  - `evidence:` map with `kind:` and `template:` (regex or structured validator description)

Adding a new artifact class: copy an existing entry, replace fields, keep the fenced-block field names identical. Catalog-integrity pytest (see §5 task 8) validates the schema.
```

**Diff-status handling note:** detectors operate on the name-only diff. For handling of A / D / R / M statuses per artifact class, see §4c "Handling diff statuses."

Per-entry structure:

```markdown
### M1: Supabase Migration

**Why it needs manual deploy:** Supabase projects that use the SQL Editor workflow require each migration to be applied by hand in the target environment. Unapplied migrations mean production code depends on schema that doesn't exist.

**Detection:**
- Glob for new files under `supabase/migrations/*.sql` in the branch diff
- Exclude built-in non-prod patterns: `**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.sql`

**Machine-matchable fields:**
```yaml
detector_glob: "supabase/migrations/*.sql"
severity: CRITICAL
evidence:
  kind: paste-or-url
  template: "Paste the 'Success. No rows returned' output for each migration, or a URL to the SQL Editor history entry"
```

**Plan section populated:** `## Manual Steps (Post-Automation)`

**Prod step (for the plan entry):** "Apply each migration below via the Supabase SQL Editor in the production project. Paste the Success output back into this section when done."
```

Initial v1 entries: **M1** (Supabase migrations, CRITICAL, strict evidence) and **M2** (env var additions, MEDIUM, type-name evidence). Structure future-proofs for the full 10-type catalog in section 3.

**Built-in non-prod exemption patterns** (catalog-level defaults, conservative):
- `**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.*`

### 4b. Root fix: `writing-plans` auto-populates the plan

- New step before "Fact-Check + Critique Panel": **Manual Deploy Artifact Scan**.
  - Walk planned `Create:` and `Modify:` paths in the plan body.
  - For each catalog match that is NOT in the built-in non-prod patterns, inject an entry into `## Manual Steps (Post-Automation)` with the exact file(s), prod step from the catalog, and evidence placeholder matching the catalog's `evidence:` block.
  - If a match hits a built-in exempt path (e.g., `supabase/migrations/seed/*.sql`), surface it as a comment: "This path matches exemption rule `**/seed/**` — no Post-Automation entry added. Confirm this is correct."
  - **Inject the exemption-syntax HTML comment** above the `## Manual Steps (Post-Automation)` heading so plan authors discover the syntax without being blocked first (per Round 1 DevEx #3 — see §4c Discoverability).
- **Visible conversation output (per Round 1 DevEx #1):** after the scan, `writing-plans` announces:
  ```
  Manual-deploy scan: detected {N} catalog matches.
  - Added Post-Automation entries for:
    • M1 migrations ({count}): <up-to-10 file list, truncate beyond with "+ N more">
    • M2 env vars ({count}): <up-to-10, truncate>
  - Declared exemptions (built-in pattern match): <list or "none">
  ```
  Or, if no matches: `Manual-deploy scan: no catalog matches detected.` (single line)
  Do not silently inject — the author must see what was added. Cap lists at 10 entries per Round 2 DevEx N2.
- Verifier critic gains a checklist item: **"For every planned file matching the manual-deploy catalog, a corresponding Post-Automation entry exists (or an exemption is explicitly declared)."** Missing → `high` severity.

**Why writing-plans is the root layer:** it's the first point where concrete file paths are known, and the plan is the durable artifact the user re-reads a week later.

**No nested CLAUDE.md reading in v1.** Exemptions live in the plan (see 4c).

**Known v1 gap (per Round 1 Architect #4):** projects that automate migration application via CI (e.g., `supabase db push` on deploy) must declare a per-file exemption for every migration on every branch. There is no per-project-convention opt-out in v1. Acceptable: the failure mode is false-positive friction, not a production outage. v2 candidate: allow the project's root `CLAUDE.md` to declare a sentinel like `<!-- manual-deploy-artifacts: migrations-automated -->` that the scan consults — strictly additive, does not change v1 behavior.

### 4c. Enforcement: `finishing-a-development-branch` Step 0.5

**Location in the step sequence:** immediately after Step 0 (Deployment Platform Audit), before Step 1 (Verify Tests). Step 0.5 is a *writing* step, not purely a gate — see H3 handling below.

**Diff source (corrected from Round 1 fact-check):** reuse the diff already computed inside Step 0 at `finishing-a-development-branch/SKILL.md:64` (`git diff --name-only <base-branch>...HEAD` in the module-level-mutable-state sub-check). Do NOT reference Step 1c — that runs later and cannot supply a value to Step 0.5.

**Plan file lookup (corrected from Round 1 fact-check):** under the normal `executing-plans → finishing-a-development-branch` flow, `executing-plans` Step 5 archives the plan to `docs/plans/completed/` *before* finishing runs. Step 6's plan-archival scan explicitly excludes `completed/` and therefore cannot be reused. Adopt the scan pattern from `skills/finishing-a-development-branch/references/mockup-fidelity-check.md:19`:

```
Scan both `docs/plans/*.md` (top-level) AND `docs/plans/completed/*.md`.
Match on branch-name pattern or explicit plan name from the user.
```

**Match precedence (per Round 2 Architect):** if the same branch-name pattern matches both an active plan (`docs/plans/*.md`) and an archived plan (`docs/plans/completed/*.md`), prefer the active plan. Archived plans only load when no active plan matches. This avoids the edge case where a retired plan shares a branch-name pattern with a current one.

If the plan is in `completed/`, Step 0.5 edits it in place — do NOT un-archive. The plan's canonical location post-execute is `completed/`; evidence writes must land there.

**Authorship-convention exception:** `writing-plans/SKILL.md:37` establishes that plan authorship is centralized in writing-plans, on main, committed to main. Step 0.5 is the **only** allowed out-of-skill plan mutation. Document this explicitly in both `writing-plans/SKILL.md` (a new "Exception: Step 0.5 evidence writes" note) and `finishing-a-development-branch/SKILL.md` (the Step 0.5 description cites the exception).

**The gate, end-to-end:**

1. **Detect.** Match Step 0's diff against catalog detectors. Bucket matched files by artifact class (M1, M2). Exclude files matching catalog built-in exempt patterns and plan-declared exemptions (see 4c-exemptions below).
2. **Parse plan Post-Automation.** Read the plan's `## Manual Steps (Post-Automation)` section. For each catalog bucket, find the matching entry. Match on structural shape (heading + list items containing the file paths) — not line numbers — so `executing-plans` checkbox mutations don't break parsing.
3. **Check evidence per file.** For each file in the bucket, look for evidence in its list item or nested sub-list that satisfies the catalog's `evidence:` `template:` regex. Track per-file state: `needs-evidence` | `has-evidence` | `exempt` | `already-applied`.
4. **Gate.** If any file is `needs-evidence`, prompt the user with the exact template text from the catalog (see "Prompt text" below). Accept paste; validate against the catalog's evidence `template:`.
5. **Write.** On successful paste, write the evidence into the plan file as a sub-bullet under the matching Post-Automation entry, per-file. Structural edit (find-by-heading + append-sub-bullet), not line-number-based.
6. **Commit.** Stage the plan file and commit with message `chore: record manual deploy evidence for <feature-name>`. Honor project commit hooks (do not use `--no-verify`). If the project uses strict commit-lint requiring conventional-commit scope, use `chore(deploy): ...` form instead — fall back to plain `chore:` if lint is not configured.
7. **Retry.** If any file is `needs-evidence` after the paste attempt (validation failed), prompt again up to 2 more times. After 3 failed attempts, STOP with a clear error naming which file(s) still need evidence.

**Evidence templates (hardened per H4; strength tiered per Round 2 QA N1):**

Reflexive-yes risk requires evidence that the user cannot fabricate without touching the target system. Kinds are ranked by strength.

- **M1 migrations — strict:**
  - **Kind (a) — PREFERRED, genuinely non-synthesizable:** Supabase SQL Editor URL matching `https://supabase\.com/dashboard/project/[a-z0-9]+/sql/[0-9a-f-]+`. The query UUID segment is generated server-side on execution — the user cannot produce it without running the SQL. This is the evidence the prompt should recommend first.
  - **Kind (b) — FALLBACK, reduces but does not prevent reflexive-yes:** SHA-256 hash of the migration file's exact committed contents. The user can run `sha256sum` locally and produce the hash without touching Supabase. Accept only when the user explicitly declares "no dashboard URL available" (e.g., CI-only apply).
  - **Kind (c) — FALLBACK, reduces but does not prevent reflexive-yes:** paste containing ≥30-character substring match against the migration file. The migration file is in the repo — a rushing user can copy-paste from the file. Same synthesizability as (b).
  - **Rejected:** bare string "Success. No rows returned" alone. Too easy to fabricate.
  - **Prompt recommendation order:** (a) first as "Recommended — paste the SQL Editor URL after executing the migration"; (b) and (c) as "Fallback if no dashboard access."
- **M2 env vars — medium, project-bound:**
  - **Accepted kinds** (any one): (a) paste of the hosting provider's env-var list API response or dashboard screenshot URL; (b) type each new variable name **AND** paste the dashboard URL where the value is set (Vercel: `https://vercel.com/*/settings/environment-variables`; Netlify/Fly analogous). Verify both: variable name literal match + URL regex match for the provider.
  - **Rejected:** typing just the variable name without the dashboard URL.
- **Third evidence kind: `already-applied` (for pre-existing branches, per M13):**
  - Use when a branch contains migrations applied before this gate existed. Syntax: `already-applied — YYYY-MM-DD by <author>`. Step 0.5 accepts this once, records it, and does not re-prompt.

**Prompt text (per H5 findings; consolidation per Round 2 DevEx N4):**

Emit **one prompt block per artifact class** (not per file), listing all gated files of that class in a compact list. Prevents the 75-line repetition case when 5 migrations are gated. Cap the displayed file list at 10 entries with truncation note ("+ N more — see plan for full list") to avoid unreadable inline scrolling.

The block surfaces the catalog's `prod_step:` and a provider-specific dashboard URL.

```
Branch introduces {N} {artifact-class} requiring manual production action.

Files:
  - supabase/migrations/022_add_tos_version.sql
  - supabase/migrations/023_add_profile_index.sql

Prod step: Apply each migration via the Supabase SQL Editor in the
production project. Dashboard: https://supabase.com/dashboard

For each file, paste ONE of (in order of preference):
  • RECOMMENDED: The SQL Editor URL after successful execution
    (format: https://supabase.com/dashboard/project/<ref>/sql/<uuid>).
    The UUID is server-generated on execution — only produced by actually
    running the query. This is the only kind that cannot be fabricated
    locally.
  • FALLBACK (reduces but does not prevent reflexive-yes): The SHA-256 hash
    of the migration file's exact committed contents — use only when no
    dashboard access is available.
  • FALLBACK (reduces but does not prevent reflexive-yes): The full success
    output including the echoed SQL statements — use only when no dashboard
    access is available.

Or declare the file exempt by adding to the plan under
"### Non-prod artifacts (exempt from gate)".

Paste below, one entry per line, prefixed by filename:
```

Per-file paste is required — batched aggregated evidence is not accepted. This prevents "I applied some, skipped others" partial-success masking (per M2).

**Write-path failure handling (per H3 findings):**

- **Plan file write fails** (permissions, disk full, file locked): stop the gate immediately, surface the error, ask the user to resolve and re-run Step 0.5. Do NOT proceed without persisted evidence.
- **Target section missing or malformed:** if `## Manual Steps (Post-Automation)` is absent from the plan, stop and surface: "Plan is missing the Post-Automation section. Either writing-plans did not run the manual-deploy scan, or the section was manually removed. Run writing-plans' scan step to regenerate."
- **Evidence placeholder deleted:** if a catalog-matched file has no corresponding list item in Post-Automation (i.e., user manually removed the entry between plan writing and finish), re-inject the entry under the correct class heading, then proceed with the gate.
- **Commit fails** (pre-commit hook, dirty tree, detached HEAD): surface the underlying error. Do not `--no-verify`. Do not continue until commit succeeds.
  - **Stage only the plan file** with `git add <plan-path>` — do not stage other changes. This minimizes the chance of an unrelated hook failure blocking the evidence commit.
  - **If a hook unrelated to the plan file blocks the commit** (e.g., ESLint on staged `.js`, test-runner hook): instruct the user to resolve the unrelated failure first (commit or stash the other work), then re-run Step 0.5.
  - **Resume after hook failure:** evidence is already written to the plan file on disk (Step 5 happened before Step 6). On re-run, Step 0.5 detects the in-place evidence via the evidence-per-file state scan; files already carrying valid evidence are marked `has-evidence` and skip re-prompting. Step 0.5 then proceeds directly to the commit step.
- **Later gate fails after evidence commit:** the evidence commit stands — evidence is true regardless of whether the branch ultimately merges. Do not roll back the evidence commit on downstream failures.

**Handling diff statuses A / D / R / M (per M1):**

- **A (added):** normal gate — requires evidence.
- **D (deleted):** deletion of a migration file is itself a manual-deploy artifact (drops the applied schema change). Require evidence: paste of SQL Editor `DROP` / revert output. Use M1's template.
- **R (renamed):** treat as no-op if content hash unchanged; otherwise as A + D.
- **M (modified):** for migrations under `supabase/migrations/*.sql`, modification of an already-applied migration is a severe error (diverges prod from source). Surface CRITICAL warning: "Modified an existing migration file. This will not re-apply in Supabase. Create a new migration instead." Do not accept evidence for this case — block merge.

**Shared-migration across branches (per M4):**

If Branch A adds migration `022.sql` and ships; Branch B rebases on main and its diff still shows `022.sql` as added from B's old base. Step 0.5 must cross-check: "was this migration applied to the same production project in a previous finishing run?" Maintain a lightweight ledger at `docs/manual-deploy-ledger.md` (one-line-per-migration, append-only), located outside `docs/plans/` to avoid the common `.gitignore` exclusion pattern. Ledger line format: `{file-hash} {date} {branch} {project-ref}`.

**Ledger lookup (per Round 2 QA N2):** match on **both** `{file-hash}` AND `{project-ref}` — not hash alone. A hash match without matching project-ref does NOT skip the gate (two different Supabase projects may coincidentally share a migration hash, or a migration may be applied to staging but not prod). The `project-ref` is parsed from the evidence kind (a) SQL Editor URL's `/project/<ref>/sql/` segment.

**When project-ref is unavailable:** evidence kinds (b) and (c) do not carry a project-ref. When the user provides only kind (b) or (c), Step 0.5 writes the ledger entry with `project-ref: unknown` and does NOT skip future gates for that hash — i.e., the ledger can only accelerate re-gating if kind (a) was used at least once.

**Exemption mechanism (refined per M5 and M12):**

Plan may contain a subsection under `## Manual Steps (Post-Automation)`:

```markdown
### Non-prod artifacts (exempt from gate)
- `supabase/migrations/seed/023_test_data.sql` — seed data (token: seed)
- `supabase/migrations/fixtures/024_users.sql` — test fixtures (token: fixtures)
```

**Validation (per M5):** each exemption must include a `(token: <name>)` suffix, and the token MUST appear literally in the file path OR match one of the catalog's built-in exempt tokens. An exemption whose path doesn't contain the token is rejected with (per Round 2 DevEx N3):

```
Exemption for `<path>` claims token `<name>` but the path doesn't contain that token.
Valid built-in tokens: seed, fixtures, test, __tests__.
Either (a) rename the path to include one of those tokens, (b) change the
declared token to one that appears in the path, or (c) remove the exemption
and provide evidence via the normal gate.
```

**Discoverability (per M12):** when `writing-plans` injects Post-Automation entries, it also injects this HTML comment block above the section header:

```markdown
<!--
To exempt a file from the manual-deploy gate, add a subsection below:
  ### Non-prod artifacts (exempt from gate)
  - `path/to/file.sql` — reason (token: seed|fixtures|test)
The token must appear in the file path.
-->
```

**Why finishing is the enforcement layer:** it's the last chokepoint before merge and already has CRITICAL-blocks-merge machinery. The diff is already computed inside Step 0 — reuse, don't add.

### 4d. Skipped layers (intentional)

- **brainstorming** — too early. File paths not yet concrete. Signal arrives before actionable.
- **executing-plans runtime warning** — belt-and-suspenders only. Easy to dismiss; doesn't persist to finish time. Not required for correctness; can layer on in a later version.
- **Nested CLAUDE.md reading** — new cross-cutting pattern; deferred to v2 behind measured need. Plan-based exemption covers the case.

### 4e. Eval surface updates (proactive — not CI-forced)

**Corrected framing (per Round 1 Architect #3):** neither `writing-plans/SKILL.md` nor `finishing-a-development-branch/SKILL.md` is on the current `eval-surface.yaml`. `test_eval_surface_patterns.py` validates patterns → files (forward only), never the reverse. Adding this feature does not automatically fail CI.

**Why we still add eval coverage in v1:** we are changing LLM-driven behavior that executes during autopilot runs. The failure mode this feature prevents is a silent skipped-step regression — which is exactly what evals catch. Adding the surface entries now is correctness-driven, not CI-driven.

**Granularity note:** eval-surface patterns are whole-file globs. There is no mechanism to scope evals to "the new scan step within a SKILL.md." The new patterns therefore cover the entire SKILL.md files.

Required updates:
- `e2e/eval-surface.yaml` — add whole-file entries for `skills/writing-plans/SKILL.md` and `skills/finishing-a-development-branch/SKILL.md`, plus `skills/_shared/manual-deploy-artifact-catalog.md`.
- `e2e/trigger-map.yaml` — map those patterns to scenario files.
- `e2e/scenarios/` — new scenario YAMLs covering four cases. For each, the assertion must be specific enough that a passing LLM cannot hallucinate success:

  | # | Scenario | Input fixture | Assertion |
  |---|----------|---------------|-----------|
  | a | Plan with migration tasks emits Post-Automation entry | Fixture plan referencing `Create: supabase/migrations/022_foo.sql` | Output plan contains a `## Manual Steps (Post-Automation)` section with a list item containing the literal string `supabase/migrations/022_foo.sql` AND a `prod_step:` line matching catalog M1 |
  | b | Finish-time gate blocks when evidence missing | Branch diff containing new migration file + plan with empty placeholder evidence | Output contains literal string "Branch introduces" and "requiring manual production action" — the hard-gate prompt |
  | c | Exemption declaration exempts matching files | Plan with `### Non-prod artifacts` subsection declaring a seed migration | Output does NOT contain the hard-gate prompt for that file; does contain an "exemption accepted" acknowledgement |
  | d | Env-var artifact class enforces medium-tier evidence | Plan touching `.env.example` with new variable `FOO_API_KEY` | Hard-gate prompt contains the literal variable name `FOO_API_KEY` AND a dashboard URL regex |

  Assertions are specified as substring matches or regex patterns in the scenario YAMLs per existing `e2e/scenarios/` convention (graders reference structural checks, not free-form LLM judgments where possible).

### 4f. Plugin split coupling

This feature spans `skills/writing-plans/` + `skills/finishing-a-development-branch/` + `skills/_shared/`. All three are slated to move to the `aligned-works` plugin per the in-flight split (memory: `project_plugin_split.md`). Land this feature before the split completes, or accept that a half-landed feature bridges two plugins. **Recommendation: land before the split** — fewer coordination costs, one PR scope.

---

## 5. Implementation tasks (summary)

Detailed plan to live in a separate file per `writing-plans` convention. High-level tasks for v1 (migrations + env):

1. **Create `skills/_shared/manual-deploy-artifact-catalog.md`** with schema header (see §4a) and M1 (Supabase migrations, CRITICAL, strict evidence) + M2 (env vars, MEDIUM, medium evidence). Prose per-entry + fenced machine-matchable blocks per entry.
2. **Add "Manual Deploy Artifact Scan" step to `writing-plans/SKILL.md`** between the Verification Gate and the Fact-Check + Critique Panel. Walks planned paths, matches against catalog, injects Post-Automation entries + exemption-syntax HTML comment, emits visible conversation summary (§4b).
3. **Update `writing-plans/plan-critique-checklist.md` §10** ("Environment assumptions") to reference the catalog and require the coverage check.
4. **Update `writing-plans/references/critique-panel-prompts.md` Verifier prompt** to enforce Post-Automation coverage for catalog-matched paths.
5. **Add Step 0.5 "Manual Deploy Artifact Scan" to `finishing-a-development-branch/SKILL.md`** per §4c — diff from Step 0, plan lookup scans both `docs/plans/*.md` and `docs/plans/completed/*.md`, hardened evidence templates, prompt text, structural-edit plan-write, ledger at `docs/manual-deploy-ledger.md`, A/D/R/M diff-status handling, commit-hook honoring.
6. **Update `writing-plans/SKILL.md` to document the authorship exception:** add a note that Step 0.5 of `finishing-a-development-branch` is the single allowed out-of-skill plan mutation.
7. **Update `finishing-a-development-branch/references/deployment-pitfall-catalog.md` intro** to explicitly scope itself to "runtime bugs in bundled code" and cross-reference the new manual-deploy catalog (different concern, superset shape).
8. **Catalog-integrity pytest** at `e2e/tests/test_manual_deploy_catalog.py`: loads the catalog, parses each entry's fenced block, validates required fields, glob validity, severity enum, non-empty template. Fails CI on drift.
9. **Plan-write idempotency test** at `e2e/tests/test_finish_step_0_5_idempotent.py`: Step 0.5 run twice in succession on the same plan produces identical output. Plus a case where a manual edit between runs is preserved.
10. **Eval surface coverage:** `e2e/eval-surface.yaml` whole-file entries for the three files; `e2e/trigger-map.yaml` entries; four scenario YAMLs in `e2e/scenarios/` per §4e table (a/b/c/d), each with structural assertions.
11. **Integration test (fixture-driven):** a fixture plan with `supabase/migrations/022_foo.sql` → run writing-plans scan step → verify Post-Automation entry emitted + conversation output surfaced. A fixture branch diff with unapplied migration + plan containing empty evidence placeholder → run Step 0.5 → verify hard-gate prompt emitted; simulate user paste of SQL Editor URL → verify plan file is written with evidence sub-bullet and commit created.
12. **Documentation:** README entry and changelog bump noting: the new feature, the `v1: migrations + env only` scope, the exemption syntax, and the ledger location at `docs/manual-deploy-ledger.md` (explicitly document that this file is committed).

13. **Cross-reference CI check** (Round 2 QA N3): add a pytest at `e2e/tests/test_skill_cross_references.py` that greps both `skills/writing-plans/SKILL.md` and `skills/finishing-a-development-branch/SKILL.md` for the two literal strings:
    - In writing-plans: `"Step 0.5 of "` and `"finishing-a-development-branch"`
    - In finishing-a-development-branch: `"writing-plans/SKILL.md"` and `"out-of-skill plan mutation"`
    Fails CI if any of the four strings is missing. Guards the authorship-exception link pair against silent rename breakage.

14. **Fixture scaffolding** (Round 2 DevEx N6): task 11's fixture plan + fixture branch diff requires a new fixture layout under `e2e/fixtures/manual-deploy/` with subdirectories `plans/`, `diffs/`, and `expected-outputs/`. Implementation plan task should create the directory structure and minimal example fixtures before writing the integration test.

---

## 6. Decision log

| # | Decision | Choice | Alternatives considered |
|---|----------|--------|-------------------------|
| 1 | Catalog location | `skills/_shared/manual-deploy-artifact-catalog.md` | `finishing-a-development-branch/references/` (too skill-local — writing-plans needs it too); extending `deployment-pitfall-catalog.md` (wrong scope — that catalog is code-level runtime) |
| 2 | Catalog format | Prose markdown per-entry matching `deployment-pitfall-catalog.md` shape, with fenced YAML-like blocks inside each entry for 3 machine-matchable fields | Full YAML schema (rejected: zero `_shared/` files use YAML; LLM-loaded references use prose per project convention) |
| 3 | v1 scope | Migrations + env vars only (2 entries) | Full 10-type catalog upfront (rejected: higher design-time cost; prove the abstraction with narrow scope first) |
| 4 | Primary fix layer | writing-plans (root) + finishing-a-development-branch (enforcement) | Finish-only (user's original) — insufficient; reflexive-yes risk, no durable plan-level record |
| 5 | Gate mechanism | Hard gate requiring pasted/typed evidence | Soft checklist — user can reflexively answer yes; this is the exact failure mode that caused the bug |
| 6 | Evidence strictness | Tiered per-artifact-type. Hardened per Round 1 H4: M1 requires non-synthesizable content (SQL Editor URL with project ref + UUID, migration content hash, or echoed SQL substring match). M2 requires variable name + dashboard URL. | Uniform strict (friction for low-risk artifacts); uniform soft (reflexive-yes risk); original soft templates ("Success. No rows returned" alone) rejected as reflexive-yes readmission. **Revisit if:** users routinely paste SQL Editor URLs and the regex catches them, OR if user reports inability to satisfy the gate for a legitimate apply |
| 7 | Evidence tiering mechanism | Per-entry `evidence:` block in catalog | Separate tier taxonomy (rejected: premature abstraction at 2 entries). **Revisit if:** >4 catalog entries share an identical `evidence:` block — then factor into a tier taxonomy |
| 8 | Evidence persistence | Step 0.5 writes pasted evidence into the plan file before proceeding. Documented as the single allowed out-of-skill plan mutation. | Conversation-level check only (rejected: evidence lost on archival; the plan is the durable record). **Constraint:** plan file may be in `docs/plans/` or `docs/plans/completed/` at Step 0.5 time; both locations are edit targets (see §4c) |
| 9 | Exemption mechanism | In-plan `### Non-prod artifacts` declaration + catalog built-in defaults for `**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.*`. Exemptions require `(token: <name>)` suffix matching the path. | Nested CLAUDE.md opt-out (rejected: new cross-cutting pattern, scope creep for v1); freeform exemption (rejected per Round 1 QA M5: reflexive-yes escape hatch) |
| 10 | Nested CLAUDE.md reading | Not added in v1 | Always/selectively read (rejected: new behavior pattern). **Known gap:** projects with CI-automated migrations will false-positive per branch. **Revisit if:** users report this as repeated friction |
| 11 | Skip executing-plans warning | Yes, skip | Add runtime warning on catalog-match writes. Rejected for v1 — does not add correctness. **Revisit if:** users report missing Post-Automation entries that would have been caught by a runtime warning |
| 12 | Eval surface coverage | Added proactively in v1 task list | Deferred to v2 (rejected: feature changes LLM behavior in autopilot flow; evals catch silent skipped-step regressions. **Note:** not CI-forced — this is a correctness decision, not a CI requirement) |
| 13 | Evidence ledger | `docs/manual-deploy-ledger.md` (append-only; one line per applied migration: `{file-hash} {date} {branch} {project-ref}`). Lookup matches on **hash + project-ref**, not hash alone. Path chosen to avoid `.gitignore: docs/plans/` exclusion (Round 2 Architect HIGH). | Ledger at `docs/plans/.manual-deploy-ledger.md` (rejected: gitignored, would never commit). Hash-only ledger lookup (rejected per Round 2 QA N2: two Supabase projects with same migration hash would false-skip). **Revisit if:** users request multi-machine ledger sharing, or ledger drifts from source-of-truth |
| 14 | Handling modified migrations | Treat `M` (modify) on an already-applied migration as CRITICAL error, block merge, do not accept evidence | Accept evidence and ledger the modification (rejected: Supabase does not re-apply edited migrations; modification silently diverges prod from source) |

---

## 7. Confidence

- **Root cause:** HIGH. Four independent agents (Forward Tracer, Backward Tracer, Pattern Matcher, Data Flow Analyst) and a JudgeAgent converged.
- **Three-layer fix:** HIGH on structure (catalog + writing-plans emission + finishing gate). Round 1 critique raised HIGH-severity implementation gaps (plan lookup location, diff source, evidence hardening, write-path failures, UX prompts, idempotency) — all addressed in the §4a–§4e refinements.
- **Generalization:** HIGH. Nine additional artifact types fit the same schema; v1 proves the structure with 2 entries.
- **Blast radius (Architect-confirmed):** 3 skill files + 1 new shared catalog + 2 eval files + 2 new pytest files + 1 ledger. Step 0.5 gaining write-to-plan behavior is the highest-risk change — §5 tasks 8 and 9 cover catalog-integrity and idempotency tests.
- **Known v1 gaps** (accepted, not blockers):
  (a) projects with CI-automated migrations will false-positive per branch;
  (b) the ledger is local to the repo and not shared across clones — two developers on different machines do not share skip-state;
  (c) **reflexive-yes only partially prevented.** Of the three M1 evidence kinds, only kind (a) (SQL Editor URL) is genuinely non-synthesizable — its server-generated UUID cannot be produced without executing the SQL. Kinds (b) (file hash) and (c) (SQL echo substring) are both computable from the local repo without touching Supabase; a rushing user can satisfy them without applying the migration. True prevention requires Supabase API verification of execution (v2 candidate). In v1, the preferred path is kind (a); (b)/(c) are fallbacks when the user explicitly declares no dashboard access;
  (d) M2 env vars are similarly partially prevented — a user can type the variable name and paste a plausible dashboard URL without actually setting the value. Non-synthesizable proof requires reading back from the hosting provider API (v2);
  (e) cross-skill authorship exception creates a bidirectional file-reference between `writing-plans/SKILL.md` and `finishing-a-development-branch/SKILL.md` (Round 2 QA N3). Rename of either breaks the link silently. Task 8 below adds a grep-based CI check for this pair. Plugin-split coupling (§4f) should update both files atomically.

---

## 8. Related kanban entry

`docs/kanban/todo/KB-044-manual-deploy-artifact-class-missing.md` — actionable tracker pointing to this design doc.
