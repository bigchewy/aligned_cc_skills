# render-review-html

**Role:** Renderer sub-agent dispatched by `reverse-engineered-brand` PHASE 3.7.

Produces the interactive HTML review file by invoking the deterministic Python renderer. Never does token substitution itself — the script owns all rendering, sanitization, and verification.

---

## Inputs

| Placeholder | Description |
|---|---|
| `{review-data-json-path}` | Path to the `review-data.json` written by PHASE 3 |
| `{template-path}` | Path to `review-template.html` (from PHASE 3 assets) |
| `{output-html-path}` | Destination path for the rendered HTML file |
| `{org-name}` | Organization name |
| `{brand-folder-path}` | Path to the brand folder |

---

## Procedure

### Step 1: Render via the deterministic script

```bash
python3 frameworks/reverse-engineered-brand/scripts/render_review.py \
  "{review-data-json-path}" "{template-path}" "{output-html-path}" "{org-name}" "{brand-folder-path}"
```

The script validates the data (grade range, OQ ≤ 15, offline-safety of font/logo srcs), emits theme CSS + server-side panels + the sanitized inline `REVIEW_DATA` snapshot, runs the verify-before-open checks (DOCTYPE, `<script>` present, no unsanitized `</script>`, closing `</html>`, no unsubstituted `{TOKEN}`), and writes the file ONLY if all checks pass.

**Shape warnings (non-blocking, R5).** Before invoking the script, inspect `{review-data-json-path}` and emit a warning for each missing key. These are pre-flight warnings only — the Python validator is the hard gate:

- `sections` (array) — used by the per-section panels
- `theme.palette` (object) — used for self-theming CSS
- `source_counts` (object) — used by Executive Summary snapshot tiles

Surface any warnings in the return `NOTES` field.

### Step 2: Abort-before-open contract

If the script exits non-zero, do NOT open the file. Return `STATUS: verification_failed` with the script's stderr in `NOTES`.

### Step 3: Open (only on exit 0)

```bash
open {output-html-path}
```

The dispatching framework is responsible for telling the user the file is open and how to use it.

---

## Return Contract

Return a compact status block of ≤ 80 words:

```
STATUS: success | verification_failed
OUTPUT_PATH: {output-html-path}
BYTES_WRITTEN: {n}
VERIFICATION_CHECKS_PASSED: {N} (as reported by the script)
NOTES: (only on failure — script stderr. Also surface any non-blocking shape warnings from Step 1 here.)
```
