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

_Entries added in subsequent tasks._

---

## MEDIUM — Likely Runtime Error or Silent Misconfig

_Entries added in subsequent tasks._
