# TODO: Flesh out the Manual-Deploy Artifact Catalog (post-v1)

**Catalog:** `skills/_shared/manual-deploy-artifact-catalog.md`
**Current coverage (v1):** M1 Supabase Migration (CRITICAL), M2 Env Var Addition (MEDIUM).

Each new entry needs: `detector_glob:` and/or `detector_grep:`, severity, evidence schema (kind + template), and the four prose sections (Why it needs manual deploy, Detection, Prod step, Plan section populated). See the Schema section of the catalog.

## Candidate Entries (Proposed)

### CRITICAL — Production Outage if Skipped

- **M3: DNS / domain / TLS record changes** — diffs adding domain config, `CNAME`/`A` record files, Cloudflare/Route53 Terraform blocks. Evidence: DNS provider console screenshot or `dig` output.
- **M4: OAuth app / third-party API credential rotation** — diffs to files named `*oauth*`, `*credentials*`, or renames of env var keys that imply rotation (e.g., `STRIPE_SECRET_KEY_V2`). Evidence: provider console confirmation + kill-switch for prior key.
- **M5: Webhook endpoint registration** — adding `app.post('/webhooks/*')` routes or Stripe/GitHub webhook handler files. Evidence: provider dashboard webhook URL + signing secret set in prod.

### HIGH — Likely Runtime Error or Degraded Feature

- **M6: Feature flag addition** — new flag keys in `growthbook.config.*`, `launchdarkly.*`, `unleash.*`, or calls to `flags.get('new-key')` with a key that didn't exist before. Evidence: flag created in provider with default value.
- **M7: Scheduled job / cron registration** — new files under `crons/`, `jobs/`, or Vercel `vercel.json` `crons` array additions. Evidence: provider console confirming the schedule is registered.
- **M8: Queue / topic creation** — new SQS/Kafka/Pub-Sub/Supabase Queues topic names in code that didn't previously exist. Evidence: topic exists in provider + IAM bindings in place.

### MEDIUM — Silent Misconfig or Delayed Failure

- **M9: CDN / storage bucket policy change** — diffs to `cdn.json`, S3/GCS bucket policy files, CORS config. Evidence: live bucket policy matches the committed file.
- **M10: Rate-limit / quota config change** — diffs to `rate-limits.yaml`, Upstash/Redis-based quota config. Evidence: prod config endpoint returns the new limits.
- **M11: Monitoring / alert rule addition** — new `*.alert.yaml`, Datadog/Grafana/PagerDuty rule files. Evidence: alert visible in dashboard + test-fire link.
- **M12: Online database index creation** — migrations containing `CREATE INDEX CONCURRENTLY` (vs regular `CREATE INDEX` already covered by M1) need explicit production-apply-and-verify evidence because the migration runner may not apply `CONCURRENTLY`. Evidence: `\d+ <table>` output or `pg_stat_progress_create_index` snapshot.

### LOW — Cosmetic or Easily Recovered

- **M13: Email template changes in transactional-mail provider** — if templates live in SendGrid/Resend/Postmark rather than code. Evidence: provider template version bumped.

## Cross-Cutting Work

- **Expand the built-in exemption patterns.** Currently only a single pattern. Add: `**/test/**`, `**/*.test.*`, `**/fixtures/**`, `**/seed/**`, `**/mocks/**`.
- **Author a severity-promotion rule.** Some artifacts flip severity by context (e.g., a feature flag behind `if (isAdmin)` is LOW; gating the login page is CRITICAL). Decide: stay deterministic (file-based only, no context), or add a prose note asking the plan writer to confirm.
- **Catalog integrity test for new entries.** `e2e/tests/test_manual_deploy_catalog.py` already enforces schema. Verify new entries satisfy it — do not loosen the schema.
- **Eval scenarios for the new classes.** Each new entry should ship with at least one `e2e/scenarios/manual-deploy/` scenario proving the detector fires and the gate demands evidence.

## Open Questions

1. **Detector cost.** Grep-based detectors run on every plan-write. If the catalog grows past ~30 entries, consider pre-compiling the detector set or parallelizing the scan. Not urgent until count > 20.
2. **False-positive triage flow.** When a detector fires but the author knows it's not a deploy artifact (e.g., a migration file added but already applied last week), the exemption mechanism covers it. Is the current exemption UX clear, or does it need a first-class "acknowledge" button distinct from exemption?
3. **M2 evidence strength.** The current M2 evidence template accepts a screenshot URL *or* a CLI command output. That's intentionally loose for v1. Tighten to require both, or split M2 into platform-specific entries (Vercel / Fly / Railway / self-hosted)?

## Not in Scope for This TODO

- Rewriting v1 (M1, M2) — they're shipped and working.
- Adding a UI — the catalog is agent-consumed, not a human dashboard.
