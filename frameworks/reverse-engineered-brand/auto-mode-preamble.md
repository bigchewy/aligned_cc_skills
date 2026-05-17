# AUTO_MODE — non-interactive execution.

This preamble is injected by the `reverse-engineered-brand` orchestrator when dispatching a framework as a Task sub-agent. It overrides the framework's default interactive contract.

---

## Execution overrides

**Override every "WAIT for user response" gate in the framework's prompt.** Do not pause. Do not prompt. Do not request confirmation. Proceed through every PHASE as if all WAIT gates are removed.

**Skip any mode-detection question ("are you running standalone or orchestrated?"). You are in AUTO_MODE.** If the framework's preamble asks you to identify your execution context, treat it as answered: orchestrated, AUTO_MODE.

---

## Canonical pre-synthesis blob

The orchestrator has provided the following baseline context about the company. Use it to anchor all framework execution:

```
{canonical-pre-synthesis-blob}
```

This substitution contains: org-name, brief positioning hypothesis, ICP hypothesis. Every AUTO_MODE framework receives the same blob so cross-framework outputs share a consistent baseline.

---

## Per-assumption record schema

For every WAIT gate you skip, you MUST emit an assumption record capturing what you inferred and why. This is non-optional.

**Required fields:**

| Field | Type | Description |
|---|---|---|
| `framework_slot` | string | The slot id of the PHASE this assumption belongs to (see slot vocabulary in `open-questions-schema.md`) |
| `inferred_value` | string\|null | What value you inferred for the gap; null if no inference is possible |
| `confidence` | enum | `high` — strong evidence supports the inference; `medium` — partial evidence, plausible; `low` — insufficient evidence, inference is a guess |
| `evidence` | array | Typed-prefix references supporting the inference, e.g. `["source:#1", "source:#3"]`. Empty array if no evidence. |
| `impact` | enum | `P0` — blocks producing a usable draft; `P1` — degrades draft quality; `P2` — cosmetic or low-stakes |

Emit assumption records as the `open_questions` array in the slice's OQ JSON output (see schema reference below).

---

## Emission contract

At the end of execution, emit:

1. Draft markdown to `{brand}/.build/slices/{slice-id}.draft.md`
2. OQ JSON to `{brand}/.build/slices/{slice-id}.oq.json`

The OQ JSON must conform to the schema at `frameworks/reverse-engineered-brand/open-questions-schema.md`.

---

## Schema reference

Full schema definition and slot vocabulary: `frameworks/reverse-engineered-brand/open-questions-schema.md`

Use the slot validator table in that document to verify every `framework_slot` value before emitting.

---

## ATOMICITY rule

**Each open question is a single variable. If you would have asked two things at one WAIT, emit two OQs.**

Do not combine questions into a single OQ. One assumption record = one variable = one question or inference. If a WAIT gate would have produced a compound question ("Is X and also Y?"), split it into two records with separate `id` values.

---

## VERIFICATION-STYLE FRAMEWORKS guardrail

Applies to: `proof-points-audit`, `competitive-battle-card`.

These frameworks verify claims. In AUTO_MODE, you **may NOT fabricate evidence.**

When a claim cannot be verified from available sources:
- Emit an OQ with `confidence: low` and `impact: P0`
- Do NOT write a draft sentence that implies the claim is verified
- Atomicity rule applies: one OQ per unverified claim

If you have no source to verify a claim and would normally ask the user to provide one, the correct action is to emit a `low`/`P0` OQ and omit the claim from the draft.

---

## Cross-framework ordering caveat

`competitive-battle-card` may run before positioning finalizes. The orchestrator provides a positioning DRAFT, not a final approved version.

When writing battle-card content that depends on settled positioning:
- Tag the OQ as `confidence: low`, `impact: P0`
- Set `why_it_matters` to note the upstream dependency, e.g.: `"Positioning is not yet finalized; this battle-card claim may need revision after 5-components-positioning completes."`

Do not assume positioning is final. Do not block execution — emit the OQ and continue.
