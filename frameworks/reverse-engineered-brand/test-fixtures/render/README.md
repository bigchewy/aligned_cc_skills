# Render Fixtures (Layer 2)

Schema-conformant JSON files used to manually verify `review-template.html` rendering.

| Fixture | Purpose | Critical checks |
|---|---|---|
| `fixture-tiny.json` | Layout spot-check (6 OQs) | Tab nav, single-page-scroll structure |
| `fixture-realistic.json` | Full envelope (~39 OQs, GAP slices, sanitization stress) | `</script>` sanitization, JSON stringify escaping, GAP meta-OQ rendering, paste-back generator copy-clean |
| `fixture-stress.json` | Volume (~130 OQs, Marley-equivalent) | Scroll/tab perf, paste-back generator on a 30-OQ folder |
| `valid-legacy-v0.4.0.json` | v0.4.0 schema with no `display_groups` — exercises legacy fallback path | Renderer must not crash or blank when `display_groups` is absent |
| `invalid-headline-too-long.json` | `headline_claim` with exactly 15 words (one over 14-word cap) | Validator must reject |
| `invalid-thinnest-gap-too-long.json` | `thinnest_gap` with exactly 15 words (one over 14-word cap) | Validator must reject |
| `invalid-provided-summary-too-long.json` | `provided_summary` with exactly 26 words (one over 25-word cap) | Validator must reject |
| `invalid-ask-too-long.json` | One `input_asks[].ask` with exactly 13 words (one over 12-word cap) | Validator must reject |
| `invalid-ask-verb-form.json` | One `input_asks[].ask` starting with "If you have…" | Validator must reject verb-form asks |
| `valid-leading-whitespace.json` | `headline_claim` with a leading space; 14 words after trim — passes word count | Validator must accept (trim before counting) |
| `valid-dedupe-collision.json` | Post-dedup state: same ask appeared at critical/recommended/optional across folders; one critical entry results | Documents dedup behavior — renderer ignores unknown `_dedupe_test_note` field |

Manual procedure: paste each fixture into the renderer's `{open-questions-json}` substitution
point in `review-template.html`, open the result in a browser, verify against the locked
mockup at `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`.

## v0.4.0 Legacy-Fallback Coverage

`valid-legacy-v0.4.0.json` is a verbatim copy of `fixture-tiny.json` before the v0.4.1 upgrade. It has `schema_version: "0.4.0"` and no `display_groups` array. The renderer must detect the missing field (or version mismatch) and fall back gracefully — no crash, no blank page, no JS exception. This exercises the legacy-fallback code path independently of the v0.4.1 fixtures.
