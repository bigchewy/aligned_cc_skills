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
| `summary` | string | **One sentence, ≤25 words.** Write this FIRST. It is the line an executive sees on the card by default. It must stand alone — if the summary needs the rationale to make sense, it is not a summary. The renderer hides `inferred_value`/`why_it_matters`/`rationale` behind a "Show detail" toggle; the summary is the only field most reviewers will read. |
| `inferred_value` | string\|null | A **complete declarative sentence** stating what you inferred — e.g. `"The brand's primary competitor is manual spreadsheet dispatch, not a named SaaS product."` Not `"spreadsheets"` or sentence fragments. Null only if no inference is possible. **Atomicity (see expanded rule below):** if the sentence contains two coordinated predicates joined by "and"/"while"/"but"/"—" where each side stands alone as a claim, split into two OQs. |
| `confidence` | enum | `high` — strong evidence supports the inference; `medium` — partial evidence, plausible; `low` — insufficient evidence, inference is a guess |
| `evidence` | array | Typed-prefix references supporting the inference, e.g. `["source:#1", "source:#3"]`. Empty array if no evidence. |
| `impact` | enum | `P0` — blocks producing a usable draft; `P1` — degrades draft quality; `P2` — cosmetic or low-stakes |
| `why_it_matters` | string | **2-3 sentences, ≤60 words.** Explains downstream stakes if this inference is wrong. Cover (a) what specifically breaks downstream, (b) which surfaces propagate the error, (c) the cost of being wrong vs. confirming. **One-sentence rationales are a schema violation. >60 words is also a violation — rambling.** |
| `rationale` | string | **2-3 sentences, ≤60 words.** Explains HOW the inference was derived from the source material. Cover (a) what the sources show, (b) where evidence converges or diverges, (c) what was assumed to bridge gaps. Quote a key phrase from the source when available. **One-sentence rationales are a schema violation. >60 words is also a violation.** |

Emit assumption records as the `open_questions` array in the slice's OQ JSON output (see schema reference below).

**Why these are required:** the executive reviewing the auto-mode output makes Approve/Reject decisions on each assumption card without re-reading every source. The card must show enough context — what was inferred, why it was inferred, why it matters — for that decision to be informed. A one-sentence `why_it_matters` plus a fragmentary `inferred_value` does not meet that bar. Conversely, a 100-word run-on `inferred_value` defeats skim-comprehension — that is what the summary field is for.

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

## ATOMICITY rule (expanded)

**Each open question is a single variable. If you would have asked or asserted two things at one WAIT, emit two OQs.**

Do not combine questions or claims into a single OQ. One assumption record = one variable = one question or inference. Two indicators that you have a compound that must be split:

1. **Compound question** — your `question` field matches `/\b(and|or)\b.*\?|\?.*\?/` (two predicates joined by "and"/"or", or two question marks). Example: `"Is spreadsheets the real alternative and is DispatchTrack worth calling out?"` → two OQs.
2. **Compound declarative** — your `inferred_value` field contains two coordinated predicates joined by **"and"**, **"while"**, **"but"**, **"however"**, or **"—"** where each side has its own subject + verb and could stand alone as a claim. Example:
   > "Chronic disease has become the dominant cost driver in US healthcare **while** the primary care system has been rendered structurally unable to manage it."
   →
   > OQ A: "Chronic cardiometabolic disease is the dominant cost and outcomes driver in US healthcare."
   > OQ B: "The US primary care system is structurally unable to manage chronic cardiometabolic disease at scale."
   Two independent claims with different evidence and different counter-arguments. Each gets its own `id`, `evidence`, `rationale`, `why_it_matters`, and `summary`.

A single claim with a subordinate clause (relative clause, comma-bound aside, "not X" contrast) is NOT a compound — keep it as one OQ. Example, do NOT split:
> "The brand's primary competitor is manual spreadsheet dispatch, not a named SaaS product."

When in doubt: ask whether each half could carry its own `evidence` array and `why_it_matters` paragraph. If yes, split. If the halves only make sense together, keep one.

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
