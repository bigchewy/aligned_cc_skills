# Manual-Deploy Artifact Catalog

Reference document for the manual-deploy artifact detection step. Lists file classes whose creation in a diff deterministically implies a non-automatable production step (e.g., DB migrations, environment variables). Consumed by `skills/writing-plans/SKILL.md` (Manual Deploy Artifact Scan step) and `skills/finishing-a-development-branch/SKILL.md` (Step 0.5: Manual Deploy Artifact Gate).

This catalog is a **superset** of `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md` in shape: severity-section organization and prose per-entry, PLUS a small fenced block inside each entry carrying machine-matchable fields.

## Contents

- [Schema](#schema)
- [Built-in Non-Prod Exemption Patterns](#built-in-non-prod-exemption-patterns)
- [CRITICAL — Production Outage if Skipped](#critical--production-outage-if-skipped)
  - M1: Supabase Migration
- [MEDIUM — Likely Runtime Error or Silent Misconfig](#medium--likely-runtime-error-or-silent-misconfig)
  - M2: Environment Variable Addition

---

## Schema

Every entry is a `###` heading with severity inferred from the section it is under. Each entry contains:

- Prose sections: `**Why it needs manual deploy:**`, `**Detection:**`, `**Prod step (for the plan entry):**`, `**Plan section populated:**`.
- Exactly one fenced ```` ```yaml ```` block with these allowed fields:
  - `detector_glob:` OR `detector_grep:` (at least one; may have both)
  - `severity:` (`CRITICAL` | `HIGH` | `MEDIUM` | `LOW`) — must match the parent section
  - `evidence:` map with `kind:` and `template:` (regex or structured validator description)

Adding a new artifact class: copy an existing entry, replace fields, keep the fenced-block field names identical. The catalog-integrity pytest at `e2e/tests/test_manual_deploy_catalog.py` validates this schema.

---

## Built-in Non-Prod Exemption Patterns

Files matching ANY of these globs are exempt by default and never produce a gate prompt:

- `**/seed/**`
- `**/fixtures/**`
- `**/__tests__/**`
- `**/*.test.*`

Plan authors may declare additional exemptions inline (see `skills/writing-plans/SKILL.md` "Manual Deploy Artifact Scan" step for syntax).

---

## CRITICAL — Production Outage if Skipped

### M1: Supabase Migration

**Why it needs manual deploy:** Supabase projects that use the SQL Editor workflow require each migration to be applied by hand in the target environment. Unapplied migrations mean production code depends on schema (tables, columns, RPCs, policies) that does not exist — producing 500s, infinite redirects, or silent data-path failures.

**Detection:**
- Glob new files under `supabase/migrations/*.sql` in the branch diff.
- Exclude built-in non-prod patterns (`**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.*`).

**Prod step (for the plan entry):** "Apply each migration below via the Supabase SQL Editor in the production project. Paste the SQL Editor URL (recommended) or the file's SHA-256 hash back into this section when done."

**Plan section populated:** `## Manual Steps (Post-Automation)` — subsection `### M1 migrations`.

**Machine-matchable fields:**

```yaml
detector_glob: "supabase/migrations/*.sql"
severity: CRITICAL
evidence:
  kind: url-or-hash-or-paste
  template: "One of: (a) Supabase SQL Editor URL matching https://supabase\\.com/dashboard/project/[a-z0-9]+/sql/[0-9a-f-]+ ; (b) SHA-256 hash (64 hex chars) of the migration file's committed contents; (c) a paste containing a >=30-character substring of the committed migration file."
```

---

## MEDIUM — Likely Runtime Error or Silent Misconfig

### M2: Environment Variable Addition

**Why it needs manual deploy:** New `process.env.FOO` references in source code crash at runtime (or read `undefined` silently) unless the variable is set in the hosting provider (Vercel / Netlify / Fly / self-hosted). Code ships green; the first request on production throws.

**Detection:**
- Grep for `process\.env\.[A-Z_]+` in source and cross-check against `.env.example`. Any name referenced in the diff that is not yet in `.env.example` is a candidate.
- Also detect when `.env.example` itself is modified to add a variable.
- Exclude the built-in non-prod patterns.

**Prod step (for the plan entry):** "Set each new variable in the hosting provider's environment settings. Paste the provider dashboard URL showing the variable is set (Vercel format: `https://vercel.com/*/settings/environment-variables`; Netlify and Fly analogous)."

**Plan section populated:** `## Manual Steps (Post-Automation)` — subsection `### M2 env vars`.

**Machine-matchable fields:**

```yaml
detector_grep: "process\\.env\\.[A-Z_]+"
detector_glob: ".env.example"
severity: MEDIUM
evidence:
  kind: name-and-url
  template: "Variable name (literal match of what was added to .env.example) AND a hosting-provider dashboard URL — Vercel: https://vercel\\.com/[^ ]+/settings/environment-variables ; Netlify: https://app\\.netlify\\.com/[^ ]+/settings/env ; Fly: https://fly\\.io/apps/[^ ]+/secrets ."
```
