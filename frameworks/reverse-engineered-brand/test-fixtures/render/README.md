# Render Fixtures (Layer 2)

Schema-conformant JSON files used to manually verify `review-template.html` rendering.

| Fixture | Purpose | Critical checks |
|---|---|---|
| `fixture-tiny.json` | Layout spot-check (6 OQs) | Tab nav, single-page-scroll structure |
| `fixture-realistic.json` | Full envelope (~39 OQs, GAP slices, sanitization stress) | `</script>` sanitization, JSON stringify escaping, GAP meta-OQ rendering, paste-back generator copy-clean |
| `fixture-stress.json` | Volume (~130 OQs, Marley-equivalent) | Scroll/tab perf, paste-back generator on a 30-OQ folder |

Manual procedure: paste each fixture into the renderer's `{open-questions-json}` substitution
point in `review-template.html`, open the result in a browser, verify against the locked
mockup at `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`.
