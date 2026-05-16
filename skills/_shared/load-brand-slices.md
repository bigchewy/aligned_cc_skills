# Load Brand Slices

> **Caller responsibility:** This shared file does NOT resolve `{base-directory}` itself. The calling skill is responsible for resolving its own `{base-directory}` before invoking this loader. See `skills/_shared/resolve-skill-path.md`.

## Purpose

Load addressable slices from a brand folder conforming to `docs/brand-folder-spec.md`. Every brand-consuming generator (`generate-deck`, `generate-blog-post`, `generate-one-pager`, `generate-email`, `generate-landing-page`, `generate-battlecard`) delegates to this skill rather than implementing frontmatter or H2 parsing inline. One loader, six generators (Decision 19). No generator implements slice extraction on its own — all delegation flows through this file.

## Inputs

- `slice_paths` (required) — list of slice addresses in `{folder}/{file-stem}#{slice-slug}` form. Example: `["strategy/positioning#category", "language/voice#tone-principles"]`.
- `min_confidence` (optional, default `medium`) — minimum confidence level a slice must carry to be included. Values: `low`, `medium`, `high`. Slices below this threshold are emitted with `status: below-confidence-threshold`.
- `brand_root` (optional, default `./brand`) — absolute or repo-relative path to the brand folder root.

## Output shape

```yaml
blocks:
  - path: "strategy/positioning#category"     # input slice address
    status: ok                                 # ok | missing | missing-frontmatter | retired
                                               # | below-confidence-threshold | missing-in-body
                                               # | undeclared-slice
    confidence: high                           # from frontmatter or per-section pragma
    body: "Markdown body text…"                # null when status != ok
sources:
  - kind: interview
    value: "2026-01-15 exec interview"
  - kind: survey
    value: "2025-Q4 customer survey"
warnings:
  - "strategy/positioning#category: declared slice has no matching H2 in body — lint failure"
```

## Procedure

1. **Resolve `brand_root`.** Default to `./brand` if the caller did not supply it. The caller is responsible for ensuring the path is absolute or correctly relative to the repo root.

2. **Load contracts (conditional).** Read `{brand_root}/contracts.yaml` only when the caller passes `"all-required-slices-for:{generator-id}"` as a slice path. For direct slice-path callers, skip this step entirely.

3. **For each input slice path `{folder}/{file-stem}#{slice-slug}`:**

   a. Glob `{brand_root}/{folder}/{file-stem}.md`. If the file is absent, emit `{path, status: missing, confidence: null, body: null}` and continue. (Decision 29 — graceful degradation: a missing file is a warning, not a fatal error.)

   b. Read the file. Parse YAML frontmatter — the block delimited by the leading `---` and the matching closing `---`.

   c. Validate required frontmatter fields: `id`, `type`, `slices`, `status`, `confidence`, `updated`, `summary`. If any field is absent, emit `{path, status: missing-frontmatter, confidence: null, body: null}` and add a warning naming the missing fields.

   d. If file `status` is `retired`, emit `{path, status: retired, confidence: null, body: null}` and add a warning: `"{path}: file is retired"`.

   e. If file `confidence` is below `min_confidence`, emit `{path, status: below-confidence-threshold, confidence: <file-confidence>, body: null}` and add a warning: `"{path}: confidence {file-confidence} is below required {min_confidence}"`.

   f. **Two missing-slice cases:**
      - **f-i. Slug declared in frontmatter `slices:` but H2 absent from body:** emit `{path, status: missing-in-body, body: null}` and add a warning: `"{path}: declared slice '{slug}' has no matching H2 in body — lint failure"`. This is the hard error case; the file is internally inconsistent.
      - **f-ii. H2 present in body but slug not listed in frontmatter `slices:`:** if the slug was NOT requested by the caller, skip silently. If the slug WAS requested, emit `{path, status: undeclared-slice, body: null}` and add a warning: `"{path}: undeclared slice '{slug}' ignored"`.

   g. **Slug derivation.** To locate the H2 matching the slice slug: lowercase the H2 heading text, replace runs of non-alphanumeric characters with `-`, strip leading and trailing `-`. The result must equal the requested slug.

   h. **Per-section pragma.** Check the line immediately following the matched H2 for a pragma block: `> [PROVENANCE: status=..., confidence=..., source=..., note="..."]`. If present, override the file-level `status` and `confidence` values for this slice only.

   i. **Extract body.** Capture markdown from immediately after the H2 (and pragma block, if present) up to the next H2 or EOF. Emit `{path, status, confidence, body}`.

4. **Collect sources.** Gather every `sources:` array from the frontmatter of successfully-loaded files. Deduplicate entries by `kind` + `value`. Return the deduped list as `sources:`.

5. **Return** the assembled output: `{blocks, sources, warnings}`.

## Composition rule

When the caller's `slice_paths` include a `personas/{role}` entry alongside any of `audiences/channels/{channel}` and/or `audiences/segments/{segment}`, compose them with this layering order (Decision 22):

1. **Base** — all declared slices from the persona file.
2. **Channel overlay** — `audiences/channels/{channel}`, applied last-write-wins per H2 slug.
3. **Segment overlay** — `audiences/segments/{segment}`, applied last-write-wins per H2 slug.
4. **Prospect overlay** — `clients/{prospect}` (optional, caller-supplied). The loader accepts two shapes:
   - **Single-file:** `clients/{prospect}.md` — all slices in one file.
   - **Folder:** `clients/{prospect}/{slice}.md` — one file per slice slug.
   Probe single-file form first. If both shapes exist for the same prospect, use single-file and add a warning: `"prospect '{name}' exists in both single-file and folder forms; using single-file"`.

Missing dimensions degrade gracefully — composition continues with whatever is present (Decision 29). The caller passes the prospect identifier explicitly; the loader does not auto-discover from conversation context.

## Slug collisions

If two H2 headings in the same file slug-collide, the loader appends `-2`, `-3`, etc. to the second and subsequent colliding headings in document order. A warning is added per collision: `"{path}: slug collision on '{slug}' — appended suffix"`. Callers may treat a collision warning as a hard error if their use case requires unique slugs.

## Loader output usage

Every generator that calls this skill MUST:

1. **Refuse to proceed** if any *required* slice has `status` in `{missing, missing-frontmatter, retired, below-confidence-threshold}`. Surface the warnings to the user before stopping.
2. **Append a sources appendix** to every generated artifact listing each missing or below-threshold slice by path and status.
3. **Add a `DRAFT` disclaimer** at the top of the generated artifact if any consumed block has `status: draft` or `confidence: low`.

## Caller integration checklist

Before shipping a new generator that delegates to this skill:

1. Invoke this loader via the standard `_shared` invocation pattern (read this file via `skills/_shared/load-brand-slices.md` in the generator's procedure).
2. Pass `min_confidence` explicitly — do not rely on the `medium` default for production generators. Require callers to state their threshold.
3. Handle every output block's `status` field. Never assume `body` is non-null. Treat any non-`ok` status as a possible halt condition per the rules in **Loader output usage** above.

## v1 contract enforcement

v1 enforces the loader contract by documentation. Six generators internalize this procedure; drift between them — one generator parsing its own frontmatter, another skipping the per-section pragma — is the predictable failure mode. Every generator MUST link to this skill by path (`skills/_shared/load-brand-slices.md`) in its own SKILL.md and quote the **Output shape** block verbatim, so any change to the output schema propagates visibly. v2 will promote the loader to executable code and enforce structural conformance mechanically; until then, conformance is verified by reading the generator's SKILL.md alongside this file during code review.
