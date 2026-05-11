# Manual-Deploy Artifact Catalog

Reference document for the manual-deploy artifact detection step. Lists file classes whose creation in a diff deterministically implies a non-automatable production step (e.g., DB migrations). Consumed by `skills/writing-plans/SKILL.md` (Manual Deploy Artifact Scan step) and `skills/finishing-a-development-branch/SKILL.md` (Step 0.5: Manual Deploy Artifact Notice).

**Scope:** Detection-only. The downstream skills surface a notice at plan-write time and at branch-finish time so the manual step isn't forgotten. There is no evidence gate — the assistant does not demand the user paste proof that the manual step was performed.

This catalog is a **superset** of `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md` in shape: severity-section organization and prose per-entry, PLUS a small fenced block inside each entry carrying machine-matchable fields.

## Contents

- [Schema](#schema)
- [Built-in Non-Prod Exemption Patterns](#built-in-non-prod-exemption-patterns)
- [CRITICAL — Production Outage if Skipped](#critical--production-outage-if-skipped)
  - M1: Supabase Migration

---

## Schema

Every entry is a `###` heading with severity inferred from the section it is under. Each entry contains:

- Prose sections: `**Why it needs manual deploy:**`, `**Detection:**`, `**Prod step (for the plan entry):**`, `**Plan section populated:**`.
- Exactly one fenced ```` ```yaml ```` block with these allowed fields:
  - `detector_glob:` OR `detector_grep:` (at least one; may have both)
  - `severity:` (`CRITICAL` | `HIGH` | `MEDIUM` | `LOW`) — must match the parent section

Adding a new artifact class: copy an existing entry, replace fields, keep the fenced-block field names identical. The catalog-integrity pytest at `e2e/tests/test_manual_deploy_catalog.py` validates this schema.

**Severity bar for inclusion:** A class belongs in this catalog only if its failure mode is *silent or hard to detect at runtime*. Loud, immediate runtime errors (e.g., `process.env.X is undefined` crashing the first request with the variable name in the stack trace) do NOT belong here — they self-report and self-fix.

---

## Built-in Non-Prod Exemption Patterns

Files matching ANY of these globs are exempt by default and never produce a notice:

- `**/seed/**`
- `**/fixtures/**`
- `**/__tests__/**`
- `**/*.test.*`

---

## CRITICAL — Production Outage if Skipped

### M1: Supabase Migration

**Why it needs manual deploy:** Supabase projects that use the SQL Editor workflow require each migration to be applied by hand in the target environment. Unapplied migrations mean production code depends on schema (tables, columns, RPCs, policies) that does not exist — producing 500s, infinite redirects, or silent data-path failures. Crucially, the failure mode is silent and hard to debug from the symptom alone, which is why it belongs in this catalog.

**Detection:**
- Glob new files under `supabase/migrations/*.sql` in the branch diff.
- Exclude built-in non-prod patterns (`**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.*`).

**Prod step (for the plan entry):** "Apply each migration below via the Supabase SQL Editor in the production project."

**Plan section populated:** `## Manual Steps (Post-Automation)` — subsection `### M1 migrations`.

**Machine-matchable fields:**

```yaml
detector_glob: "supabase/migrations/*.sql"
severity: CRITICAL
```
