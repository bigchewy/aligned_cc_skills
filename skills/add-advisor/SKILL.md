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

**Plugin or project repo:** "Writing to the plugin itself" means project-cwd contains `.claude-plugin/plugin.json` whose `name` is `aligned`. Otherwise it is a project repo. In a project repo, the registry lives in the project (`<project-cwd>/advisors/registry.yaml` and `<project-cwd>/frameworks/registry.yaml`), never in the plugin.

**Prompt path detection:**
1. Check the project's CLAUDE.md for advisor prompt path configuration
2. If `advisors/prompts/` exists at repo root → use it
3. Else check for app-specific paths (e.g., `src/lib/advisors/prompts/`) → use if found
4. Else → default to `advisors/prompts/` at repo root (will create on first use)

**Infrastructure detection (check each):**

| Marker | Check | Enables |
|--------|-------|---------|
| Advisor registry file | Check CLAUDE.md, then `<project-cwd>/advisors/registry.yaml` (or the plugin's when writing to the plugin itself) | Registry entry (Steps 3 and 7). In a project repo a missing registry is created, not skipped |
| Framework registry file | Check for `<project-cwd>/frameworks/registry.yaml` (or the plugin's when writing to the plugin itself) | Framework registry entry (Step 5). In a project repo a missing registry is created, not skipped |
| Eval infrastructure | Check for eval scenarios directory + eval script in package.json | Eval scenario (Step 6) |

**Print summary:**
```
Environment Detection:
  Prompt path:       {detected path}           → {found / will create}
  Writing to:        {plugin itself / project repo}
  Advisor registry:  {registry path}           → {found (full mode) / will create (project repo) / not found (lightweight mode)}
  Framework registry: frameworks/registry.yaml → {found / will create (project repo) / not found (skipping)}
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

> **Conditional:** Skip this step only in lightweight mode: writing to the plugin itself, no advisor registry detected in Step 0. Print: "Skipping registry entry — no registry found (lightweight mode)." In a project repo the default is to write `<project-cwd>/advisors/registry.yaml` (created in Step 7 if absent).

Add the advisor to the registry file. Writing to the plugin itself, or when the project's CLAUDE.md documents its own registry location and entry format, follow that. Otherwise in a project repo, Step 7 writes the full-schema entry.

**If no registry format is documented and Step 7 does not apply**, create a simple entry with:
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

### 5. Add First Framework

Use the `/aligned:add-framework` skill to implement the top-ranked framework.

> **Critical:** The add-framework skill updates the framework registry as part of its registry-entry step (`<project-cwd>/frameworks/registry.yaml` in a project repo; create it if absent, with a one-line comment header and a `frameworks:` list key; the plugin's `frameworks/registry.yaml` when writing to the plugin itself). If you write the framework `prompt.md` directly instead of invoking the skill, you MUST also append an entry to that registry with id, name, advisor, purpose, category, domains, and use_when fields. A framework that exists on disk but not in the registry will have degraded discovery — use-framework falls back to filesystem glob but loses metadata-based matching and routing.

### 6. Create Eval Scenario

> **Conditional:** Only run this step if the project has an eval infrastructure (e.g., `e2e/` directory, detected in Step 0). If not found, print: "Skipping eval scenario — no eval infrastructure found."

If the project has eval infrastructure, create a quick-consult eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format, and copy an existing scenario's provider and options lines exactly. If `e2e/trigger-map.yaml` exists, add an entry mapping the new advisor prompt path to the new scenario path.

Minimum scenario should include:
- Advisor ID and mode
- A realistic 2-turn conversation in the advisor's domain
- Evaluation dimensions (flow, personalization, voice)
- Voice fingerprint with signature phrases and anti-patterns

Run the new scenario to verify baseline quality. If `e2e/run_evals.py` exists, run only the new scenario from `e2e/` with `npm run eval -- <scenario-path>`. The runner uses the Claude Code login. Never skip the run because `ANTHROPIC_API_KEY` is not set. Never suggest `--all` unless a file in `e2e/providers/` changed; a new scenario only needs its own run. When a provider file did change, state the call count and token cost before asking the user. If `e2e/run_evals.py` does not exist, use the project's own eval command. If the scenario fails, classify the failure (prompt issue, eval calibration, or model variance) and fix before continuing. First-run failures are common and usually eval calibration — adjust keywords and fingerprints before changing the voice prompt.

### 7. Update the Registry

Writing to the plugin itself: append to the plugin's `advisors/registry.yaml`. Project repo: append to `<project-cwd>/advisors/registry.yaml`. If that file does not exist, create it with a one-line comment header and the list key, then append the entry:

```yaml
# Project advisors. Merged with the aligned plugin's registry; entries here win on a matching id.
advisors:
```

Append one entry to the `advisors` list in the registry file:

```yaml
  - id: {slug}
    name: "{display-name}"
    summary: "{summary}"
    prompt: advisors/prompts/{slug}.md
    domains: [{domains}]
    note: "Not yet profiled with evaluation expertise."
```

> **Read-side note:** The `prompt:` field is written for human readability but is ignored by the read side — `skills/_shared/resolve-advisor-source.md` derives the prompt path from `id` + scope + the configured prompt-dir. Do not rely on `prompt:` to point the resolver anywhere.

Where:
- **slug:** The advisor's kebab-case filename (without `.md`)
- **display-name:** The advisor's full name
- **summary:** One-line description
- **domains:** Comma-separated expertise areas as a YAML list (e.g., `[marketing, growth, content-strategy]`); use `[]` if unknown

**Post-append validation:** After appending, parse the full registry file you wrote. If YAML parsing fails, revert the append and report the error. Restore the previous content; if you just created the file, it is untracked, so delete the newly created file instead of restoring it from git. One bad entry must not corrupt the registry for all consumers.

If the registry does not exist and you are writing to the plugin itself, skip this step silently (lightweight mode — the add-advisor skill works without a registry). In a project repo, create it as described above.

### 8. Update Advisor and Framework Counts

> **Conditional:** Only when writing to the plugin itself. In a project repo, skip this step: the plugin's README and manifests do not describe project content.

Count the actual advisors and frameworks in the plugin directory and update all references so metadata stays in sync:

1. Count advisor prompt files in `advisors/prompts/` (`.md` files only)
2. Count framework directories in `frameworks/` (directories containing `prompt.md`)
3. Update every occurrence of the old counts in:
   - `README.md` — opening description, "How It Works" bullets, and Advisors section
   - `.claude-plugin/plugin.json` — `description` field
   - `.claude-plugin/marketplace.json` — `description` field

The description pattern is: `"{N} advisor personas, {M} frameworks"`. Also update standalone references like `"{N} expert advisors"` and `"{N} advisor prompts"` in `README.md`.

### 9. Commit

Commit all changes with message: `feat: add {advisor-name} advisor`

## Notes

- All new advisors are created with `enabled: false` - they won't appear in the front-end until explicitly enabled
- Review created prompt files to verify voice authenticity
- **Local advisors require two files.** Advisors have no glob fallback (unlike frameworks): a prompt
  file with no `advisors/registry.yaml` entry is a silent no-op — it will never appear in listings,
  panels, or contextual recommendation. When adding an advisor to a project-local repo, you MUST
  write both `advisors/registry.yaml` (full-schema entry) and `advisors/prompts/<id>.md`. This skill
  writes both; if you hand-author, do the same.
