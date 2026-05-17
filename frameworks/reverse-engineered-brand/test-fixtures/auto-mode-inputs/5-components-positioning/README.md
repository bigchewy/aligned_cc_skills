# AUTO_MODE Fixtures — 5-Components Positioning (FixtureCo)

Vertical-slice test fixtures for the `5-components-positioning` framework running in AUTO_MODE.
FixtureCo is a fictional last-mile logistics SaaS used as a realistic stand-in for smoke testing.

## How to use

Assemble this Task dispatch to run the AUTO_MODE smoke test:

1. **Preamble** — paste the full content of `frameworks/reverse-engineered-brand/auto-mode-preamble.md`
2. **Canonical blob** — paste `canonical-pre-synthesis-blob.md` (the baseline context paragraph)
3. **Source extracts** — paste `source-extracts.json` (2 extracts, post-T15 schema with `entities.role`)
4. **Competitor dossiers** — paste `competitor-dossiers.json` (2 named competitors: DispatchTrack, Onfleet)
5. **Behavioral alternatives** — paste `behavioral-alternatives.json` (2 BA entries)
6. **Framework** — reference `frameworks/5-components-positioning/prompt.md` as the framework to dispatch

Dispatch as a sub-agent (`subagent_type: general-purpose`) with the above assembled prompt.

## Emission contract

Per the AUTO_MODE preamble, the dispatched framework must emit:

- `{output-draft-path}` — path where the positioning draft was written
- `{output-open-questions-path}` — path where the OQ JSON was written

## Acceptance criteria (OQ-4 trigger condition)

The dispatched framework must:

1. Emit open questions (OQs) for **every PHASE** in `5-components-positioning/prompt.md` (PHASE 1–5; PHASE 6 is synthesis and does not require OQs)
2. Not skip or merge phases when emitting OQs
3. Validate every OQ's `framework_slot` against the slot vocabulary in `open-questions-schema.md`:
   - `phase-1-competitive-alternatives`
   - `phase-2-unique-attributes`
   - `phase-3-value`
   - `phase-4-target-customers`
   - `phase-5-market-category`
4. No `framework_slot` value may merge two phases (e.g., `"unique-value"` is invalid — use `phase-2-unique-attributes` and `phase-3-value` separately)

## Files

| File | Schema | Purpose |
|---|---|---|
| `source-extracts.json` | `extract.md` (post-T15, with `entities.role`) | 2 source extracts with competitive, ICP, and value signal |
| `competitor-dossiers.json` | `open-questions-schema.md` `competitors[]` | 2 named competitors with `identity_verification: "matched"` |
| `behavioral-alternatives.json` | `open-questions-schema.md` `behavioral_alternatives[]` | 2 BA entries grounded in source quotes |
| `canonical-pre-synthesis-blob.md` | prose | 1-paragraph baseline for AUTO_MODE context |
| `README.md` | — | This file |
