# Fixture Plan: Add TOS Version Column

> Fixture — used by `e2e/tests/test_manual_deploy_integration.py`. Represents the plan AFTER the Manual Deploy Artifact Scan has injected the Post-Automation section.

**Goal:** Add `tos_accepted_version` column to `profiles`.

**Source Design Doc:** N/A

---

### Task 1: Add migration

**Files:**
- Create: `supabase/migrations/022_add_tos_version.sql`

**Step 1:** Write the migration.

```sql
ALTER TABLE profiles ADD COLUMN tos_accepted_version INTEGER;
```

**Step 2:** Commit.

---

<!--
To exempt a file from the manual-deploy gate, add a subsection below:
  ### Non-prod artifacts (exempt from gate)
  - `path/to/file.sql` — reason (token: seed|fixtures|test)
The token must appear literally in the file path, OR match one of the
catalog's built-in exempt tokens (seed, fixtures, test, __tests__).
-->

## Manual Steps (Post-Automation)

### M1 migrations

- `supabase/migrations/022_add_tos_version.sql` — [evidence pending]
