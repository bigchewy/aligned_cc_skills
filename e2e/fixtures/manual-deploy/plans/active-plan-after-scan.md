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

## Manual Steps (Post-Automation)

### M1 migrations

- `supabase/migrations/022_add_tos_version.sql` — Apply via the Supabase SQL Editor in the production project.
