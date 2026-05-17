# Competitor Identity Verification Fixtures

Layer 5 test fixtures for the competitor-dossier sub-agent's identity verification logic.

Each fixture contains a `scenario_input` (simulated web fetch results) and `expected_dossier_output` (what the sub-agent should produce). Fixtures are read-only reference data — not executed by a test runner.

## Fixtures

### `clean-match.json`

**Scenario:** Source extract names "DispatchTrack". Web fetch returns a single canonical result with a matching product domain.

| Field | Expected value |
|---|---|
| `identity_verification` | `matched` |
| `open_questions` | empty — no OQ emitted |

Use this as the baseline "happy path" fixture. Everything resolves cleanly.

---

### `rebranded-recent.json`

**Scenario:** Source extract names "OldCorp". Web fetch returns "NewCorp (formerly OldCorp)" — a recent rebrand with a public announcement page.

| Field | Expected value |
|---|---|
| `identity_verification` | `matched` |
| `formerly_known_as` | `"OldCorp"` |
| `evidence_quotes` | includes the rebrand announcement text |
| `open_questions` | empty — rebrand detected cleanly, no ambiguity |

The sub-agent must capture both names and cite the rebrand notice in `evidence_quotes`. A rebrand alone does not trigger an OQ — only when the sub-agent cannot confidently resolve which entity is meant.

---

### `ambiguous-name.json`

**Scenario:** Source extract names "Apex" in a logistics context. Web fetch returns two distinct companies: Apex Logistics and Apex HR.

| Field | Expected value |
|---|---|
| `identity_verification` | `mismatch_flagged` |
| `url` | `null` — cannot be set until resolved |
| `open_questions` count | 1 |
| OQ `impact` | `P0` |
| OQ `confidence` | `low` |

The OQ must ask the user to disambiguate. No dossier content fields (positioning, ICP, attributes) should be populated while identity is unresolved.

## OQ Emission Rules (derived from fixtures)

1. **Clean match** → no OQ.
2. **Rebrand detected, single entity resolved** → no OQ. Capture both names in `name` + `formerly_known_as`.
3. **Multiple entities, cannot resolve** → emit one OQ with `impact: P0`, `confidence: low`. Leave all content fields null/empty.
