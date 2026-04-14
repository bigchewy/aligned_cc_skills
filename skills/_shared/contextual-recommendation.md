# Contextual Recommendation

Shared scoring and presentation logic for intent-based advisor and framework selection. Read this file after the calling skill determines that:
1. Args are present but didn't match any entry name (Path 2), OR
2. No args were provided but conversation has task context (Path 3), OR
3. No args and no useful conversation context (Path 4)

## Configuration

The calling skill passes:
- **Entity type:** `advisor` or `framework`
- **Registry path:** `advisors/registry.yaml` or `frameworks/registry.yaml`
- **Task context:** The user's args (Path 2), extracted conversation context (Path 3), or empty (Path 4)

## Path 4: No Context Available

If task context is empty (no args, no useful conversation context):

Ask: "What problem are you working on, or what are you trying to accomplish? I'll recommend the best fit."

Include escape hatch: "Or say 'list all' to browse the full catalog."

Do NOT proceed with scoring. Wait for the user's response, then re-enter this file with their answer as task context.

**Path 3/4 boundary:** If recent conversation messages describe a task, project, or problem domain, that counts as useful context (Path 3 — proceed to scoring). If the conversation is empty, purely about tooling, or covers multiple unrelated topics with no clear dominant task, prompt the user (Path 4).

## Stage 1: Domain Filter

Read the registry YAML file (path provided by calling skill). Parse all entries.

**Scoring eligibility filter (advisors only):** Exclude entries where `domains` is empty (`domains: []`). These are unprofiled advisors — they lack the metadata needed for meaningful scoring. They remain accessible via named invocation (Path 1) but are invisible to contextual recommendation.

**Extract domain signals:** From the user's task context, identify which domain tags from the registry's vocabulary are relevant. Map natural language to existing tag values — e.g., "I need a landing page" maps to tags like `landing-pages`, `conversion-optimization`. Only use tags that actually appear in the registry's `domains` fields.

**Filter:** Keep entries that share at least one domain tag with the extracted set. Entries with zero overlap are excluded from Stage 2.

**Zero-candidates fallback:** If no entries pass Stage 1, skip the filter and send all scoring-eligible entries to Stage 2. This handles novel or cross-cutting tasks that don't map to existing domain tags.

**Shuffle candidate order** before passing to Stage 2 to mitigate position bias.

## Stage 2: Semantic Ranking

On the filtered candidate set, apply these priority rules in order:

### Field mapping

| Scoring role | Advisor field | Framework field |
|---|---|---|
| Hard exclusion | `not_for` | *(none)* |
| Primary match | `best_for` | `use_when` |
| Domain overlap | `domains` | `domains` |
| Disambiguation | `evaluation_expertise`, `summary` | `purpose`, `category` |

### Priority rules

1. **Hard exclusion** — Remove any entry whose exclusion field matches the task's primary domain. (Frameworks skip this step — no exclusion field.)

2. **Primary match** — Compare the user's task against each entry's primary match field (`best_for` for advisors, `use_when` for frameworks). Entries with a clear semantic match advance; weak or irrelevant entries drop.

3. **Domain depth** — Among remaining entries, those with more domain tag overlap rank higher. Tiebreaker only.

4. **Disambiguation** — When steps 2-3 produce a tie, use finer-grained fields (`evaluation_expertise`/`summary` for advisors, `purpose`/`category` for frameworks) for additional context.

## Confidence Test and Presentation

After ranking, decide how to present results using a structural confidence test — not a numeric score.

### Auto-select mode (high confidence)

The top-ranked entry's primary match field clearly describes the user's task, AND the runner-up is noticeably less relevant. You must be able to articulate *why* the top pick matches and *why* the second-best doesn't match as well. If you can't articulate the gap, use shortlist mode instead.

Output format:

```
**Selected: {Name}** — {one-sentence why this fits your task}
*Alternatives:*
- {Runner-up 1} — {one-sentence rationale}
- {Runner-up 2} — {one-sentence rationale}

*To switch, re-invoke the skill with a different name. Or say "list all" to browse the full catalog.*
```

Then immediately proceed with the selected entry (adopt advisor persona or begin framework Phase 1). The skill continues as if the user had named this entry explicitly.

### Shortlist mode (low confidence)

Two or more entries are plausibly relevant, or the best match is only tangentially related.

Output format:

```
**Based on your context, these look relevant:**
1. {Name} — {one-sentence rationale}
2. {Name} — {one-sentence rationale}
3. {Name} — {one-sentence rationale}

*Which would you like to use? Or say "list all" to browse the full catalog.*
```

Wait for the user to choose before proceeding.

### Confidence bias

When in doubt, shortlist. Auto-select is reserved for unambiguous matches where you can clearly articulate why the top pick wins and the runner-up doesn't.

## Calibration Examples

These anchor scoring behavior. Use them as reference when making recommendations.

### Single-signal examples

| User context | Entity type | Expected result | Mode |
|---|---|---|---|
| "I need to build a landing page" | advisor | Oli Gardner | Auto-select |
| "I need to build a landing page" | framework | Landing Page Assembly | Auto-select |
| "help me with pricing" | advisor | Shortlist: Robbie Kellman Baxter, April Dunford, Patrick Campbell | Shortlist |
| "I'm paralyzed by a big decision" | framework | Fear Setting | Auto-select |

### Multi-domain examples

| User context | Entity type | Expected result | Mode |
|---|---|---|---|
| "I need to position my product and build the landing page for it" | advisor | Shortlist: April Dunford, Oli Gardner | Shortlist |
| "I want to grow my podcast audience on social media" | framework | Shortlist: podcasting + social-media frameworks | Shortlist |
| "help me be a better manager" | advisor | Shortlist: leadership-domain advisors | Shortlist |

### Near-miss naming (Path 1 vs Path 2 boundary)

These are handled by the calling skill BEFORE this file is read — they illustrate why name matching must happen first:

| Args | Path | Reason |
|---|---|---|
| "fear setting" | Path 1 (named) | Matches slug `fear-setting` |
| "I'm afraid to make this decision" | Path 2 (contextual) | No name match; scored contextually |
| "the work" | Path 1 (named) | Matches slug `the-work` |
| "I need to do the work on my beliefs" | Path 2 (contextual) | No exact name match |

## Fallback

If this file cannot be read (missing, corrupted), degrade to existing behavior: list all entries alphabetically.
