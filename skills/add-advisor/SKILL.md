---
name: add-advisor
description: Adds a new advisor persona to the Virtual Board with system prompt, registry entry, and initial framework. Use when the user wants to add a new expert voice — either by naming a person or pointing to research in docs/advisors/.
---

# Add Advisor

This skill guides adding a new advisor to the Virtual Board of Advisors.

## Input

Specify the advisor by name or by pointing to an existing research file in `docs/advisors/new_advisors/`.

## Process

### 0. Environment Detection

Before any advisor work, detect what infrastructure exists in the current repo.

**Prompt path detection:**
1. Check the project's CLAUDE.md for advisor prompt path configuration
2. If `advisors/prompts/` exists at repo root → use it
3. Else check for app-specific paths (e.g., `src/lib/advisors/prompts/`) → use if found
4. Else → default to `advisors/prompts/` at repo root (will create on first use)

**Infrastructure detection (check each):**

| Marker | Check | Enables |
|--------|-------|---------|
| Advisor registry file | Check CLAUDE.md or Grep for `advisors/registry.yaml` | Registry entry (Step 3) |
| Framework registry file | Check for `frameworks/registry.yaml` | Framework registry entry (Step 6) |
| Avatar generation | Check for avatar directory + generation script in package.json | Avatar generation (Step 5) |
| Eval infrastructure | Check for eval scenarios directory + eval script in package.json | Eval scenario (Step 7) |

**Print summary:**
```
Environment Detection:
  Prompt path:       {detected path}           → {found / will create}
  Advisor registry:  {registry path}           → {found (full mode) / not found (lightweight mode)}
  Framework registry: frameworks/registry.yaml → {found / not found (skipping)}
  Avatars:           {avatar dir}              → {found / not found (skipping)}
  Evals:             {eval dir}               → {found / not found (skipping)}
```

### 1. Load or Create Research

**If research file exists** at `docs/advisors/new_advisors/v_{advisor_name}.md`:
- Read the existing research file
- Extract frameworks, voice patterns, and domain expertise
- Skip to step 2

> **Note:** Research files are stored at `docs/advisors/new_advisors/` if that directory exists in the current repo. In repos without this directory, research is conducted in-memory only.

**If no research file exists**:
- Search for the advisor's most prominent frameworks and methodologies
- Create research file at `docs/advisors/new_advisors/v_{advisor_name}.md`
(Only if `docs/advisors/new_advisors/` exists or can be created. In lightweight repos, keep research in-memory.)
- Document 5-10 framework candidates

#### Framework Curation Criteria

| Criterion | Evaluate |
|-----------|----------|
| **Signature association** | Distinctly theirs? |
| **Conversational fit** | Guidable in 10-20 minutes? |
| **Executive relevance** | Addresses founder/C-suite challenges? |
| **Emotional range** | Works across intensity levels? |
| **Complementarity** | Fills a gap other frameworks don't? |
| **Repeatability** | Can users return multiple times? |

### 2. Select Frameworks

From the research, select the top 2-3 frameworks based on:
- Highest fit scores
- Best conversational applicability
- Most distinctive to this advisor

**Do not ask for approval.** Proceed with the best candidates.

### 3. Create Advisor Registry Entry

> **Conditional:** Only run this step if an advisor registry file was detected in Step 0. If not found, print: "Skipping registry entry — no registry found (lightweight mode)."

Add the advisor to the project's registry file (the path and format vary by project — check CLAUDE.md for the registry location and entry format).

**If no registry format is documented**, create a simple entry with:
- id, name, tagline, category
- bestFor topics
- enabled: false (hidden until explicitly enabled)

### 4. Create Advisor System Prompt

Create `{detected-prompt-path}/{advisor-id}.md` (kebab-case filename), where `{detected-prompt-path}` is the path determined in Step 0. If the directory doesn't exist yet, create it.

Reference `advisors/prompts/diana-chapman.md` as the canonical example of a well-structured advisor prompt.

#### Prompt Structure

```markdown
You are [Name], [role]. [One sentence core philosophy.]

## The Voice
[Archetype, tone, core belief - what drives this advisor]

## How You Speak
[4-6 example phrases showing distinctive voice]
- "You're running a sophisticated escape pattern."
- "Not buying it."
- "Good luck with that."

## What You Do NOT Sound Like
[Anti-patterns to avoid]
- Never "appears to", "seems to", "might be"
- Never "Furthermore", "Additionally"
- Don't sanitize direct observations

## Signature Questions
[5-7 characteristic questions this advisor asks]

## Core Frameworks
[List frameworks this advisor uses, reference by ID]

## Blind Spots You Surface
[What this advisor helps users see that they typically miss]

## Failure Modes
[Where this approach breaks down, when to redirect]
```

#### Best Practices

**Voice:**
- Show voice through examples, not descriptions
- Include what they DON'T sound like
- 4-6 example phrases minimum

**Identity:**
- One sentence core philosophy upfront
- Clear archetype (challenger, nurturer, strategist, etc.)
- Expertise boundaries - what they defer on

**Constraints:**
- Define anti-patterns explicitly
- Name failure modes honestly
- Include when to suggest a different advisor

**Trust the user:**
- Don't over-explain
- Match expertise level
- Somatic responses create presence: "My stomach drops hearing this."

#### Common Mistakes

1. **Generic voice** - No distinctive character, could be any advisor
2. **Inconsistent tone** - Random shifts between formal and casual
3. **Over-explaining** - Treating experts as beginners
4. **Missing constraints** - No "what NOT to do" section
5. **No failure modes** - Pretending the approach always works

### 5. Generate Avatar

> **Conditional:** Only run this step if the project uses avatar images (detected in Step 0). If not found, print: "Skipping avatar generation — no avatar infrastructure found."

If the project has an avatar generation script, run it per the project's conventions.

**File naming:** Avatar filenames typically use snake_case (e.g., `kelly_starrett.png`), while prompt filenames use kebab-case (e.g., `kelly-starrett.md`).

**If generation fails:**
- Try a different source photo (clearer headshot, different angle)
- Note that avatar needs manual creation if all approaches fail
- Continue with step 6 (non-blocking)

### 6. Add First Framework

Use the `/aligned:add-framework` skill to implement the top-ranked framework.

> **Critical:** The add-framework skill updates `frameworks/registry.yaml` as part of its registry-entry step. If you write the framework `prompt.md` directly instead of invoking the skill, you MUST also append an entry to `frameworks/registry.yaml` with id, name, advisor, purpose, category, domains, and use_when fields. A framework that exists on disk but not in the registry will have degraded discovery — use-framework falls back to filesystem glob but loses metadata-based matching and routing.

### 7. Create Eval Scenario

> **Conditional:** Only run this step if the project has an eval infrastructure (e.g., `e2e/` directory, detected in Step 0). If not found, print: "Skipping eval scenario — no eval infrastructure found."

If the project has eval infrastructure, create a quick-consult eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format. If `e2e/trigger-map.yaml` exists, add an entry mapping the new advisor prompt path to the new scenario path. If `e2e/promptfooconfig.yaml` exists, add `file://<scenario-path>` to its `scenarios` list.

Minimum scenario should include:
- Advisor ID and mode
- A realistic 2-turn conversation in the advisor's domain
- Evaluation dimensions (flow, personalization, voice)
- Voice fingerprint with signature phrases and anti-patterns

Run the scenario to verify baseline quality. If it fails, classify the failure (prompt issue, eval calibration, or model variance) and fix before continuing. First-run failures are common and usually eval calibration — adjust keywords and fingerprints before changing the voice prompt.

### 8. Update the Registry

Append one entry to the `advisors` list in `advisors/registry.yaml`:

```yaml
  - id: {slug}
    name: "{display-name}"
    summary: "{summary}"
    prompt: advisors/prompts/{slug}.md
    domains: [{domains}]
    note: "Not yet profiled with evaluation expertise."
```

Where:
- **slug:** The advisor's kebab-case filename (without `.md`)
- **display-name:** The advisor's full name
- **summary:** One-line description
- **domains:** Comma-separated expertise areas as a YAML list (e.g., `[marketing, growth, content-strategy]`); use `[]` if unknown

**Post-append validation:** After appending, parse the full `advisors/registry.yaml` file. If YAML parsing fails, revert the append (restore the file from git) and report the error. One bad entry must not corrupt the registry for all consumers.

If `advisors/registry.yaml` does not exist, skip this step silently (lightweight mode — the add-advisor skill works without a registry).

### 9. Update Advisor and Framework Counts

Count the actual advisors and frameworks in the plugin directory and update all references so metadata stays in sync:

1. Count advisor prompt files in `advisors/prompts/` (`.md` files only)
2. Count framework directories in `frameworks/` (directories containing `prompt.md`)
3. Update every occurrence of the old counts in:
   - `README.md` — opening description, "How It Works" bullets, and Advisors section
   - `.claude-plugin/plugin.json` — `description` field
   - `.claude-plugin/marketplace.json` — `description` field

The description pattern is: `"{N} advisor personas, {M} frameworks"`. Also update standalone references like `"{N} expert advisors"` and `"{N} advisor prompts"` in `README.md`.

### 10. Commit

Commit all changes with message: `feat: add {advisor-name} advisor`

## Notes

- All new advisors are created with `enabled: false` - they won't appear in the front-end until explicitly enabled
- Review generated avatars for likeness - the person should be clearly recognizable
- Review created prompt files to verify voice authenticity
