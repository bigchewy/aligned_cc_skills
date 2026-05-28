# Curation Input Fixtures

Test inputs for `curate_open_questions.py`. Each file is a single aggregated OQ queue — a JSON object with an `open_questions` array of the **rich internal shape** — modeling what the aggregation of `.build/slices/*.oq.json` produces at PHASE 3.

## Fixture index

| File | OQ count | Exercises |
|---|---|---|
| `owner-authority-mix.json` | 8 | Owner-first sort ordering |
| `p0-heavy-with-p1-owner.json` | 14 | P1 owner-authority OQ survives a P0-heavy queue |
| `all-p2.json` | 9 | All-P2 backfill to floor path |
| `empty.json` | 0 | Clean-build path (empty input → empty output) |
| `tie-break-collision.json` | 6 | Deterministic tie-break by `(file ASC, aggregation_index ASC)` |

## Fixture detail

### `owner-authority-mix.json`

Eight OQs: 3 `owner_authority: true` at mixed P0/P1, plus 5 non-owner OQs at P0/P1/P2. The curated output must place all owner-authority OQs before non-owner OQs regardless of impact level — a P1 owner item sorts ahead of a P0 non-owner item.

Expected sort order: OQ-1 (owner, P0), OQ-2 (owner, P1), OQ-3 (owner, P1), then non-owner P0s, then P1s, then P2s.

### `p0-heavy-with-p1-owner.json`

Fourteen OQs: 13 non-owner `P0` inferences plus 1 `P1` owner-authority OQ (`"Confirm 'virtual-first cardiometabolic practice' as the default category label"`). This pins that the P1 owner-authority item must survive curation and appear in the output ahead of non-owner P0 items, even when the P0 queue is large. The curator must not discard the owner item in favor of filling slots with higher-impact non-owner OQs.

### `all-p2.json`

Nine OQs, all `impact: P2`, none `owner_authority: true`. Pins the backfill-to-floor path: when no P0 or P1 OQs exist, the curator selects from P2 OQs to meet the minimum output count rather than returning an empty or under-populated result.

### `empty.json`

`{ "open_questions": [] }`. Pins the clean-build path: an empty input queue must produce an empty curated output without errors.

### `tie-break-collision.json`

Six OQs sharing identical `(owner_authority: false, impact: P0, confidence: medium)`. All `aggregation_index` values are `0`. Ordering is decided entirely by `file ASC`. The input deliberately lists files out of alphabetical order:

| Input position | File |
|---|---|
| 1 | `z-audiences.md` |
| 2 | `a-strategy.md` |
| 3 | `m-design.md` |
| 4 | `b-language.md` |
| 5 | `y-personas.md` |
| 6 | `c-market.md` |

Expected output order by file ASC: `a-strategy.md`, `b-language.md`, `c-market.md`, `m-design.md`, `y-personas.md`, `z-audiences.md`. Tests must assert this order to verify a stable, deterministic sort — not the input order.
