# render-review-html

**Role:** Renderer sub-agent dispatched by `reverse-engineered-brand` PHASE 3.7.

Produces the interactive HTML review file by filling in a locked template. Never embeds HTML inline — always reads from `{template-path}`.

---

## Inputs

| Placeholder | Description |
|---|---|
| `{template-path}` | Path to `review-template.html` (from Task 12 / PHASE 3 assets) |
| `{open-questions-json-path}` | Path to the aggregated `.open-questions.json` from PHASE 3.6 |
| `{output-html-path}` | Destination path for the rendered HTML file |
| `{brand-folder-path}` | Path to the brand folder (embedded as `BRAND_FOLDER_PATH` JS constant) |
| `{org-name}` | Organization name (embedded in the page title and `ORG_NAME` JS constant) |

---

## Procedure

### Step 1: Read the template

Read `{template-path}` in full. Capture the content as a string. This is the base for all token substitution.

Do not hardcode or reconstruct any HTML — the template is the single source of truth for structure and styling.

### Step 2: Read and validate the JSON

Read `{open-questions-json-path}`. Parse the content as JSON.

If the file cannot be read or parsed (malformed JSON, missing file), abort immediately with `STATUS: verification_failed`, `NOTES: json_parse_error — {error message}`. Do not proceed to substitution.

**Shape warnings (non-blocking).** Inspect the parsed object for v0.3.0+ fields that the template depends on. If any are missing, accumulate a warning (do NOT abort — v0.2.0 files still render). Surface the accumulated warnings in the final `NOTES` field of the return contract:

- `source_counts` (object) — used by Executive Summary snapshot tiles
- `source_narratives` (object) — used by Executive Summary "Raw material" / "Primary research" cards
- `folders[].grade` (integer 1-5) — used by Sections at a Glance grade column and per-folder summary banners
- `folders[].summary` (string) — used by Sections at a Glance and per-folder summary banners

The renderer should log a warning like `shape_warning: source_narratives missing — exec-summary cards will render empty (legacy v0.2.0 behavior)` for each missing field, then continue.

### Step 3: Sanitize string values

For every string value anywhere in the parsed JSON (nested objects, arrays, all depths), replace every `</` with `<\/`.

This prevents `</script>` inside `question`, `draft_excerpt`, `inferred_value`, `why_it_matters`, `evidence_quote`, competitor `evidence_quotes`, or any other string field from closing the script tag prematurely.

**Sanitize before serializing — never after.**

### Step 4: Re-serialize with stringify discipline

Serialize the sanitized JSON using `JSON.stringify`-equivalent escaping. Backslashes, double-quotes, and control characters MUST be properly escaped.

Do not hand-build the JS literal. Write the full JSON object first, then embed the serialized string result. The embedded value must be a valid JS expression that evaluates to the array of open-question objects.

### Step 5: Substitute tokens

In the template string, replace the following tokens:

| Token | Replacement |
|---|---|
| `{open-questions-json}` | The serialized, sanitized JSON string from Step 4 |
| `{brand-folder-path}` | The input path — escape any `"` characters for JS-safety |
| `{org-name}` | The org name — HTML-escape `<`, `>`, `&`, `"` for the title/header; use the raw value in the JS `ORG_NAME` constant (already safe in a JS string context if `"` is escaped) |

All three tokens must be substituted. A remaining literal token is a substitution failure — surface it in the verify step.

### Step 6: Write the output

Write the substituted string to `{output-html-path}`.

### Step 7: Verify by reading back

Read `{output-html-path}`. Assert all of the following:

1. First line is `<!DOCTYPE html>`
2. Both `<script>` opening tags are present
3. No occurrence of `</script>` exists anywhere in the file except as the closing tag(s) for the script block(s) — the sanitization contract from Step 3 must hold
4. File ends with `</html>`
5. No raw token literal `{open-questions-json}`, `{brand-folder-path}`, or `{org-name}` remains (the three substitutions in Step 5 were complete)
6. **Catch-all token check.** Scan for ANY remaining bracket-delimited token matching the regex `/\{[a-zA-Z][a-zA-Z0-9_-]*\}/`. A match indicates a template token that drifted from the substitution table (e.g., `{Org Name}` Title-Case form, or a newly added template token that no substitution covers). Fail with `NOTES: unsubstituted_token — {matched_string} at byte {N}`.

**Abort-before-open contract:** If any check fails, abort. Return `STATUS: verification_failed` with `NOTES` naming the failed check and the offending byte range. Do NOT call `open` on a malformed file.

**Why Check 6 exists.** The Step 5 substitution table is a whitelist of three known tokens. If the template adds a fourth token (or an existing token's case/format drifts), Step 5 silently does nothing for it and Check 5's literal-string scan misses it. Check 6's regex is the failsafe — it catches drift without anyone having to remember to update Check 5's whitelist.

### Step 8: Open the file

Only if Step 7 passed all checks:

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
VERIFICATION_CHECKS_PASSED: {N}/6
NOTES: (only on failure — name the failed check + offending byte range. Also surface any non-blocking shape warnings from Step 2 here.)
```
