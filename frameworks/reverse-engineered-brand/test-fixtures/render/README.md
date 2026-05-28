# Render Fixtures

Schema-conformant JSON files consumed by `e2e/tests/test_reb_renderer.py` to verify `render_review.py` behavior.

All fixtures conform to the `review-data.json` envelope (see `open-questions-schema.md`): `org`, `generated_at`, `brand_folder`, `source_counts`, `grade_scale`, `theme`, `sections[]` (overview + 7 areas, with `readout`/`recent_update` only on overview), `open_questions[]` (thin shape, 5–15 entries).

## Valid fixtures

| Fixture | Purpose | Renderer assertion |
|---|---|---|
| `valid-tiny.json` | Minimal valid envelope — 8 sections, 6 thin OQs, full theme with relative font `src_woff2` and a real `logo.src` | Tab nav renders, all 8 sections present, OQs route to correct section panels |
| `valid-realistic.json` | Marley-equivalent — 8 graded sections with `provided[]`/`needed[]`, overview `readout`, 12 OQs, a `</script>`-bearing string in one `why_it_matters` | Sanitization: `</script>` is escaped before injection; all content renders correctly |
| `valid-stress.json` | 15 OQs (at cap), long `provided[]`/`needed[]` lists, multi-face font objects | All 15 OQs render without layout overflow; no JS exception |
| `valid-null-logo-wordmark.json` | `theme.logo.src: null`, `wordmark_text: "The Knot"` | Renderer emits a `.wordmark` text span instead of an `<img>` tag |
| `valid-no-palette-uses-default.json` | `theme.palette: {}` (empty object) | Renderer emits the literal neutral default values for all 17 CSS custom properties |

## Invalid fixtures (renderer must reject — exit non-zero, no `review.html` written)

| Fixture | Invalid condition | Expected rejection |
|---|---|---|
| `invalid-grade-out-of-range.json` | A section has `grade: 7` (outside 1–5) | Validator rejects before render; no output file written |
| `invalid-oq-over-cap.json` | 16 entries in `open_questions[]` (cap is 15) | Validator rejects; no output file written |
| `invalid-remote-font-src.json` | A `theme.fonts.heading.faces[].src_woff2` starts with `https://` | Security guard rejects remote font src; no output file written |
| `invalid-font-src-escapes-folder.json` | A font `src_woff2` of `../marley-raw/Reckless.woff2` (resolves outside brand folder) | Path traversal guard rejects; no output file written |
