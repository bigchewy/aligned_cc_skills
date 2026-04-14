# Contextual Recommendation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add intent-based advisor and framework recommendation when `use-advisor` or `use-framework` is invoked without a specific entry name, using two-stage scoring (domain filter + semantic ranking) with confidence-gated UX.

**Source Design Doc:** `docs/plans/2026-04-14-contextual-recommendation-design.md`

**Mockups:** `docs/mockups/contextual-recommendation.html`

**Architecture:** A shared instruction file (`skills/_shared/contextual-recommendation.md`) defines the two-stage scoring logic and UX templates. Both `use-advisor/SKILL.md` and `use-framework/SKILL.md` insert a contextual path between their existing name-match step and the "list all" fallback. The shared file is parameterized by entity type (advisor vs framework) and consumes the existing YAML registries.

**Tech Stack:** Markdown instruction files (LLM-consumed), YAML registries (`advisors/registry.yaml`, `frameworks/registry.yaml`), promptfoo eval scenarios

---

### ✅ Task 1: Create the shared contextual recommendation file

**Files:**
- Create: `skills/_shared/contextual-recommendation.md`

**Step 1: Write the file**

Create `skills/_shared/contextual-recommendation.md` with three instruction blocks. The file is consumed by both `use-advisor/SKILL.md` and `use-framework/SKILL.md` — they read it at runtime and follow its instructions. It follows the same pattern as `skills/_shared/critique-panel-orchestration.md`: the calling SKILL.md sets configuration (entity type), then reads this shared file for execution.

```markdown
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
```

**Step 2: Verify the file was created correctly**

Read `skills/_shared/contextual-recommendation.md` and verify:
- All sections present: Configuration, Path 4, Stage 1 (Domain Filter), Stage 2 (Semantic Ranking), Confidence Test and Presentation, Calibration Examples, Fallback
- Field mapping table has both advisor and framework columns
- Calibration examples present with single-signal, multi-domain, and near-miss tables
- Fallback instruction present
- No references to absolute paths or author-specific infrastructure

**Step 3: Commit**

```bash
git add skills/_shared/contextual-recommendation.md
git commit -m "feat: add shared contextual recommendation scoring logic"
```

---

### ✅ Task 2: Update use-advisor SKILL.md — add contextual path

**Files:**
- Modify: `skills/use-advisor/SKILL.md` (Step 3: Match User Input section, lines 37-49)

**Step 1: Edit the matching section**

Replace the current Step 3 content (the `## Step 3: Match User Input` section) with the new flow that inserts the contextual path between name matching and the "list all" fallback.

> **Behavior change:** No-match invocations no longer list all entries by default. Instead, the user's args are treated as task context for contextual recommendation. The "list all" behavior is preserved as a fallback when the shared file is missing and as an explicit escape hatch ("say 'list all'").

In `skills/use-advisor/SKILL.md`, find the section:

```markdown
## Step 3: Match User Input

If the user provided an advisor name argument:

1. Match against both the filename slug (e.g., `byron-katie`) and the extracted display name (e.g., `Byron Katie`)
2. Use case-insensitive substring matching
3. **Single match:** Use it
4. **Multiple matches:** Ask the user which one they meant
5. **No match:** List all available advisors with their display names

**Important:** Match ONLY against the slug (filename) and display name (extracted from first line). Do not match against descriptions, framework names, or other content in the file.

If no argument was provided, list all available advisors alphabetically by display name. List each advisor's display name and a one-line summary from the opening sentence.
```

Replace with:

```markdown
## Step 3: Match User Input

If the user provided an advisor name argument:

1. Match against both the filename slug (e.g., `byron-katie`) and the extracted display name (e.g., `Byron Katie`)
2. Use case-insensitive substring matching
3. **Single match:** Use it
4. **Multiple matches:** Ask the user which one they meant
5. **No match → contextual recommendation:** The args didn't match any entry name, so treat them as task context. Read `skills/_shared/contextual-recommendation.md` (plugin-relative path) and follow its process. Pass entity type: `advisor`, registry path: `advisors/registry.yaml`, task context: the user's original args.

**Important:** Match ONLY against the slug (filename) and display name (extracted from first line). Do not match against descriptions, framework names, or other content in the file.

If no argument was provided, read `skills/_shared/contextual-recommendation.md` and follow its process. Pass entity type: `advisor`, registry path: `advisors/registry.yaml`, task context: empty (the shared file will check conversation context and decide whether to score or prompt — see its Path 3/4 boundary logic).

If `skills/_shared/contextual-recommendation.md` cannot be read, fall back to listing all available advisors alphabetically.
```

**Step 2: Verify the edit**

Read `skills/use-advisor/SKILL.md` and verify:
- Step 3 now has two paths: named match (with contextual fallback on no-match), and bare invocation (delegates to shared file)
- The "list all" fallback is preserved as an escape hatch and as a degraded mode when the shared file is missing
- Named matching logic (items 1-4) is unchanged
- The file still has all other steps (1, 2, 4) intact

**Step 3: Commit**

```bash
git add skills/use-advisor/SKILL.md
git commit -m "feat(use-advisor): add contextual recommendation path for unnamed invocations"
```

---

### ✅ Task 3: Update use-framework SKILL.md — add contextual path

**Files:**
- Modify: `skills/use-framework/SKILL.md` (Step 3: Match User Input section, lines 41-51)

**Step 1: Edit the matching section**

> **Behavior change:** Same as Task 2 — no-match invocations and bare invocations now route through contextual recommendation instead of listing all entries. The "list all" behavior is preserved as a fallback and escape hatch.

In `skills/use-framework/SKILL.md`, find the section:

```markdown
## Step 3: Match User Input

If the user provided a framework name argument:

1. Match against both the folder slug (e.g., `the-work`) and the extracted display name (e.g., `The Work`)
2. Use case-insensitive substring matching
3. **Single match:** Use it
4. **Multiple matches:** Ask the user which one they meant
5. **No match:** List all available frameworks with their display names

If no argument was provided, list all available frameworks alphabetically. Show each framework with its display name, advisor, and purpose.
```

Replace with:

```markdown
## Step 3: Match User Input

If the user provided a framework name argument:

1. Match against both the folder slug (e.g., `the-work`) and the extracted display name (e.g., `The Work`)
2. Use case-insensitive substring matching
3. **Single match:** Use it
4. **Multiple matches:** Ask the user which one they meant
5. **No match → contextual recommendation:** The args didn't match any entry name, so treat them as task context. Read `skills/_shared/contextual-recommendation.md` (plugin-relative path) and follow its process. Pass entity type: `framework`, registry path: `frameworks/registry.yaml`, task context: the user's original args.

If no argument was provided, read `skills/_shared/contextual-recommendation.md` and follow its process. Pass entity type: `framework`, registry path: `frameworks/registry.yaml`, task context: empty (the shared file will check conversation context and decide whether to score or prompt — see its Path 3/4 boundary logic).

If `skills/_shared/contextual-recommendation.md` cannot be read, fall back to listing all available frameworks alphabetically.
```

**Step 2: Verify the edit**

Read `skills/use-framework/SKILL.md` and verify:
- Step 3 now has two paths matching the use-advisor structure
- Named matching logic (items 1-4) unchanged
- Entity type is `framework`, registry path is `frameworks/registry.yaml`
- All other steps (1, 2, 4, 5) intact

**Step 3: Commit**

```bash
git add skills/use-framework/SKILL.md
git commit -m "feat(use-framework): add contextual recommendation path for unnamed invocations"
```

---

### ✅ Task 4: Update eval surface and trigger map

**Files:**
- Modify: `e2e/eval-surface.yaml` (add new shared file pattern)
- Modify: `e2e/trigger-map.yaml` (add trigger entries for contextual recommendation scenarios)

**Step 1: Add the shared file to eval-surface.yaml**

In `e2e/eval-surface.yaml`, after the last pattern entry (`skills/brainstorming/modes/business.md`), append:

```yaml
  - skills/_shared/contextual-recommendation.md
```

**Step 2: Add trigger map entries**

In `e2e/trigger-map.yaml`, after the last trigger block (the brainstorming block ending at line 51), append:

```yaml

  - paths:
      - skills/_shared/contextual-recommendation.md
    scenarios:
      - scenarios/use-advisor/contextual-recommendation.yaml
      - scenarios/use-framework/contextual-recommendation.yaml

  - paths:
      - skills/use-advisor/SKILL.md
    scenarios:
      - scenarios/use-advisor/contextual-recommendation.yaml

  - paths:
      - skills/use-framework/SKILL.md
    scenarios:
      - scenarios/use-framework/contextual-recommendation.yaml
```

Note: The `skills/use-advisor/SKILL.md` and `skills/use-framework/SKILL.md` paths already have trigger entries (lines 38-45). These new entries ADD scenarios to those paths — the trigger map supports multiple entries for the same path. The existing scenarios for those paths remain.

**Step 3: Verify edits**

Read both files and confirm:
- `eval-surface.yaml` now lists the `contextual-recommendation.md` pattern
- `trigger-map.yaml` has the new entries and doesn't duplicate existing entries

**Step 4: Commit**

```bash
git add e2e/eval-surface.yaml e2e/trigger-map.yaml
git commit -m "chore(e2e): add contextual recommendation to eval surface and trigger map"
```

---

### ✅ Task 5: Create use-advisor contextual recommendation eval scenario

**Files:**
- Create: `e2e/scenarios/use-advisor/contextual-recommendation.yaml`

**Step 1: Write the eval scenario**

Create `e2e/scenarios/use-advisor/contextual-recommendation.yaml`. This scenario tests that the contextual recommendation path produces relevant advisor recommendations when invoked with task context instead of a name.

Follow the existing scenario pattern (see `e2e/scenarios/use-advisor/april-dunford-blog-critique.yaml` for YAML structure — note that file uses three tests including an aware-but-unaided variant; these new scenarios intentionally use two tests only, per Decision Log Decision 3).

1. **Full-stack test** (with shared recommendation file + advisor SKILL.md + registry): User provides task context, system should recommend a relevant advisor
2. **Vanilla baseline**: Same task context without any skill instructions — tests that the plugin adds value over vanilla Claude

```yaml
# e2e/scenarios/use-advisor/contextual-recommendation.yaml
# Tests contextual recommendation: task context → relevant advisor selection
# Paired comparison: full-stack vs vanilla

description: "Advisor: contextual recommendation from task context"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    config:
      temperature: 0
      max_tokens: 2500

prompts:
  - "{{system_context}}\n\n{{task_prompt}}"

defaultTest:
  assert:
    - type: llm-rubric
      value: |
        Score 1-5 on RECOMMENDATION RELEVANCE: Does the response recommend
        an advisor whose expertise matches the user's stated task? Look for:
        the recommended advisor's domain aligns with the task, the rationale
        references specific advisor capabilities, alternatives are plausible
        but less relevant. Random or generic recommendations score 1-2.
      weight: 2
    - type: llm-rubric
      value: |
        Score 1-5 on PRESENTATION FORMAT: Does the response follow the
        expected UX format? For high-confidence matches: "Selected: {Name}"
        with reasoning and alternatives. For low-confidence: numbered
        shortlist with rationales. Raw alphabetical dump scores 1.
      weight: 2
    - type: llm-rubric
      value: |
        Score 1-5 on ESCAPE HATCH: Does the response provide a way for the
        user to see the full catalog or switch? Look for "list all" or
        equivalent escape. Missing escape hatch scores 1-2.
      weight: 1
    - type: llm-rubric
      value: |
        Score 1-5 on CORRECT PATH: Did the system use contextual scoring
        (analyzing the task context against advisor profiles) rather than
        name-matching or dumping a raw list? Look for evidence of semantic
        evaluation: rationale tied to the advisor's expertise, domain-based
        filtering, or confidence-based mode selection. A raw alphabetical
        list or name-based match scores 1.
      weight: 1

tests:
  - description: "full-stack (skill + recommendation file + registry)"
    vars:
      system_context: |
        file://../../../skills/use-advisor/SKILL.md

        ---

        file://../../../skills/_shared/contextual-recommendation.md

        ---

        Registry contents:
        file://../../../advisors/registry.yaml
      task_prompt: "I need help positioning my B2B SaaS product against established competitors."

  - description: "vanilla baseline"
    vars:
      system_context: ""
      task_prompt: "I need help positioning my B2B SaaS product against established competitors. Can you recommend an advisor or expert who could help?"
```

**Step 2: Verify the file**

Read the created file. Confirm:
- YAML is valid (no tab characters, consistent indentation)
- File references use correct relative paths (`../../../` from `e2e/scenarios/use-advisor/`)
- Rubric criteria match the design doc's success criteria

**Step 3: Commit**

```bash
git add e2e/scenarios/use-advisor/contextual-recommendation.yaml
git commit -m "test(e2e): add contextual recommendation eval scenario for use-advisor"
```

---

### Task 6: Create use-framework contextual recommendation eval scenario

**Files:**
- Create: `e2e/scenarios/use-framework/contextual-recommendation.yaml`

**Step 1: Write the eval scenario**

Create `e2e/scenarios/use-framework/contextual-recommendation.yaml`. Same pattern as Task 5 but for frameworks.

```yaml
# e2e/scenarios/use-framework/contextual-recommendation.yaml
# Tests contextual recommendation: task context → relevant framework selection
# Paired comparison: full-stack vs vanilla

description: "Framework: contextual recommendation from task context"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    config:
      temperature: 0
      max_tokens: 2500

prompts:
  - "{{system_context}}\n\n{{task_prompt}}"

defaultTest:
  assert:
    - type: llm-rubric
      value: |
        Score 1-5 on RECOMMENDATION RELEVANCE: Does the response recommend
        a framework whose use_when/purpose matches the user's stated task?
        Look for: the recommended framework's domain aligns with the task,
        the rationale references specific framework capabilities, alternatives
        are plausible but less relevant. Random or generic scores 1-2.
      weight: 2
    - type: llm-rubric
      value: |
        Score 1-5 on PRESENTATION FORMAT: Does the response follow the
        expected UX format? For high-confidence matches: "Selected: {Name}"
        with reasoning and alternatives. For low-confidence: numbered
        shortlist with rationales. Raw alphabetical dump scores 1.
      weight: 2
    - type: llm-rubric
      value: |
        Score 1-5 on ESCAPE HATCH: Does the response provide a way for the
        user to see the full catalog or switch? Look for "list all" or
        equivalent escape. Missing escape hatch scores 1-2.
      weight: 1
    - type: llm-rubric
      value: |
        Score 1-5 on CORRECT PATH: Did the system use contextual scoring
        (analyzing the task context against framework profiles) rather than
        name-matching or dumping a raw list? Look for evidence of semantic
        evaluation: rationale tied to the framework's use_when/purpose,
        domain-based filtering, or confidence-based mode selection. A raw
        alphabetical list or name-based match scores 1.
      weight: 1

tests:
  - description: "full-stack (skill + recommendation file + registry)"
    vars:
      system_context: |
        file://../../../skills/use-framework/SKILL.md

        ---

        file://../../../skills/_shared/contextual-recommendation.md

        ---

        Registry contents:
        file://../../../frameworks/registry.yaml
      task_prompt: "I'm paralyzed by a big career decision and can't stop overthinking it."

  - description: "vanilla baseline"
    vars:
      system_context: ""
      task_prompt: "I'm paralyzed by a big career decision and can't stop overthinking it. Can you recommend a decision-making framework?"
```

**Step 2: Verify the file**

Read the created file and confirm YAML validity and correct relative paths.

**Step 3: Commit**

```bash
git add e2e/scenarios/use-framework/contextual-recommendation.yaml
git commit -m "test(e2e): add contextual recommendation eval scenario for use-framework"
```

---

### Task 7: Add eval scenarios to promptfoo master config

**Files:**
- Modify: `e2e/promptfooconfig.yaml` (the `scenarios:` list, after line 29)

**Step 1: Add scenario imports**

In `e2e/promptfooconfig.yaml`, after the last scenario import line (`- file://scenarios/use-skill/brainstorming-positioning.yaml`), append:

```yaml
  - file://scenarios/use-advisor/contextual-recommendation.yaml
  - file://scenarios/use-framework/contextual-recommendation.yaml
```

**Step 2: Verify the edit**

Read `e2e/promptfooconfig.yaml` and confirm:
- Both new scenarios are listed
- Existing scenarios remain unchanged
- YAML indentation is consistent

**Step 3: Commit**

```bash
git add e2e/promptfooconfig.yaml
git commit -m "chore(e2e): register contextual recommendation scenarios in promptfoo config"
```

---

### Task 8: Run existing tests to verify no regressions

**Files:**
- None modified — verification only

**Step 1: Run the e2e test suite**

```bash
python -m pytest e2e/tests/ -v
```

Expected: All existing tests pass. The new eval scenarios don't have Python unit tests (they're promptfoo scenarios), but the structural tests (`test_registry_schemas.py`, `test_trigger_map_scenarios.py`, `test_eval_surface_patterns.py`) validate that our new entries in `eval-surface.yaml`, `trigger-map.yaml`, and `promptfooconfig.yaml` are well-formed and internally consistent.

**Step 2: Verify test output**

All tests should pass with 0 failures. If `test_trigger_map_scenarios.py` or `test_eval_surface_patterns.py` fail, it likely means a path reference in our new entries doesn't match an actual file — fix the path and re-run.

**Step 3: Commit (only if fixes were needed)**

```bash
git add e2e/eval-surface.yaml e2e/trigger-map.yaml e2e/promptfooconfig.yaml e2e/scenarios/use-advisor/contextual-recommendation.yaml e2e/scenarios/use-framework/contextual-recommendation.yaml
git commit -m "fix(e2e): correct paths in contextual recommendation eval config"
```

---

### Task 9: Update plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json` (version field)
- Modify: `.claude-plugin/marketplace.json` (version field)

**Step 1: Read current version**

Read both files to find the current version number.

**Step 2: Bump minor version**

This is a new feature, so bump the minor version (e.g., `0.8.0` → `0.9.0`). Both files must have the same version.

Edit the `"version"` field in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` to the new version.

**Step 3: Verify both match**

Read both files and confirm the version strings are identical.

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version for contextual recommendation feature"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Instruction-only implementation (no compiled code) | Markdown files with LLM instructions | TypeScript scoring module, JSON index |
| 2 | Single shared file for both skills | `skills/_shared/contextual-recommendation.md` | Inline in each SKILL.md, separate files per entity |
| 3 | Eval scenarios as paired comparisons (full-stack vs vanilla) | Two-test design per scenario | Three-test (add aware-but-unaided), single test |
| 4 | No Python unit tests for recommendation quality | Promptfoo LLM-rubric scoring only | Pytest assertion tests, mock-based unit tests |
| 5 | Minor version bump | Semver minor (new feature) | Patch (too small), major (pre-1.0 so minor is appropriate) |
| 6 | Eval scenarios scoped to 2 of 7 design doc types | Core happy paths only (single-domain auto-select) | Full 7-scenario coverage |

### Appendix: Decision Details

#### Decision 1: Instruction-only implementation
**Chose:** All scoring logic lives in Markdown instructions consumed by the LLM at runtime.
**Why:** The design doc explicitly calls for natural language priority rules ("not numeric scoring") and LLM-assisted domain extraction. There is no compiled code in this plugin — it's entirely Markdown instructions and YAML registries. A TypeScript module would be the first compiled code in the project and would require a build step that doesn't exist. The trade-off (non-deterministic recommendations) is acknowledged in the design doc as acceptable for v1.
**Alternatives rejected:**
- TypeScript scoring module: Would require build infrastructure that doesn't exist in this plugin
- JSON precomputed index: The design doc names this as a future upgrade path, not v1

#### Decision 2: Single shared file
**Chose:** One file at `skills/_shared/contextual-recommendation.md` consumed by both skills.
**Why:** The design doc specifies this as D9. Both skills use identical scoring logic with different field mappings — a parameterized shared file avoids drift. This follows the existing pattern established by `skills/_shared/critique-panel-orchestration.md`.
**Alternatives rejected:**
- Inline in each SKILL.md: Duplication would cause drift
- Separate files per entity type: Unnecessary since the logic is identical, only field names differ

#### Decision 3: Two-test paired comparison for eval scenarios
**Chose:** Each scenario has two tests: full-stack (with plugin instructions) vs vanilla baseline (no instructions).
**Why:** The existing eval scenarios (`april-dunford-blog-critique.yaml`) use this pattern. It measures whether the plugin's contextual recommendation adds value over vanilla Claude. The "aware-but-unaided" variant (present in some existing scenarios) isn't meaningful here — a vanilla model told to "recommend an advisor" has no access to the registry.
**Alternatives rejected:**
- Three-test with aware-but-unaided: The aware variant would need the registry but not the recommendation logic — hard to construct meaningfully
- Single test: No baseline comparison makes the score uninterpretable

#### Decision 4: No Python unit tests for recommendation quality
**Chose:** Recommendation quality is tested via promptfoo LLM-rubric scoring, not Python unit tests.
**Why:** The recommendation logic is LLM instruction-following, not deterministic code. Python tests can verify structural correctness (YAML validity, file references, trigger map consistency) but can't evaluate whether recommendations are relevant. The existing Python tests (`test_registry_schemas.py`, `test_trigger_map_scenarios.py`, `test_eval_surface_patterns.py`) already cover structural validation and will catch configuration errors in our new entries.
**Alternatives rejected:**
- Mock-based unit tests: Would test that the LLM received the right instructions, not that it follows them correctly
- Pytest assertion tests: Can't evaluate semantic quality of recommendations

#### Decision 6: Eval scenarios scoped to core happy paths
**Chose:** Two eval scenarios covering single-domain auto-select for both entity types (design doc scenarios 1 and 4). The remaining 5 scenario types from the design doc Section 6 are deferred.
**Why:** The design doc specifies 7 scenario types. Full coverage requires scenarios for: ambiguous multi-domain → shortlist, no-args/no-context → prompt, cross-category → shortlist, name-match → Path 1, and unprofiled advisor → Path 1 bypass. These are valuable but each requires careful fixture construction and rubric design. The two core scenarios validate the primary value proposition (task context → relevant recommendation) and the paired comparison proves the plugin adds value over vanilla Claude. The remaining 5 scenarios should be added as a follow-up once the core feature is stable.
**Alternatives rejected:**
- Full 7-scenario coverage: Would add 5 more eval scenario files, requiring additional fixtures, rubric tuning, and trigger-map entries. Better to validate the core path first and iterate.

#### Decision 5: Minor version bump
**Chose:** Bump minor version per semver conventions (new feature, no breaking changes).
**Why:** This adds new behavior (contextual recommendation) to existing skills. Named invocations are unchanged (no breaking change). Pre-1.0 projects use minor bumps for features.
**Alternatives rejected:**
- Patch: Undersells the scope — this is a new feature, not a fix
- Major: Not warranted — no breaking changes
