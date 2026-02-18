---
name: add-advisor
description: Add a new advisor to the Virtual Board. Use this skill when the user wants to add a new advisor persona, including framework research, advisor entry creation, system prompt, and initial framework implementation.
---

# Add Advisor

This skill guides adding a new advisor to the Virtual Board of Advisors.

## Invocation

```
/aligned:add-advisor
"I want to add a new advisor based on Brene Brown"
```

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
| Advisor registry file | Check CLAUDE.md or Grep for registry | Registry entry (Step 3) |
| Avatar generation | Check for avatar directory + generation script in package.json | Avatar generation (Step 5) |
| Eval infrastructure | Check for eval scenarios directory + eval script in package.json | Eval scenario (Step 7) |

**Print summary:**
```
Environment Detection:
  Prompt path: {detected path}           → {found / will create}
  Registry:    {registry path}           → {found (full mode) / not found (lightweight mode)}
  Avatars:     {avatar dir}              → {found / not found (skipping)}
  Evals:       {eval dir}               → {found / not found (skipping)}
```

> **Editor note:** A parallel environment detection section exists in `skills/add-framework/SKILL.md` (Step 0). If you change the path-detection priority order here, apply the equivalent change there.

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

Reference `advisors/va-web-app/diana-chapman.md` as the canonical example of a well-structured advisor prompt.

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

### 7. Create Eval Scenario

> **Conditional:** Only run this step if the project has an eval infrastructure (e.g., `e2e/` directory, detected in Step 0). If not found, print: "Skipping eval scenario — no eval infrastructure found."

If the project has eval infrastructure, create a quick-consult eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format.

Minimum scenario should include:
- Advisor ID and mode
- A realistic 2-turn conversation in the advisor's domain
- Evaluation dimensions (flow, personalization, voice)
- Voice fingerprint with signature phrases and anti-patterns

Run the scenario to verify baseline quality. If it fails, dispatch the `eval-failure-triage` agent via Task tool to classify and fix before continuing. First-run failures are common and usually eval calibration — adjust keywords and fingerprints before changing the voice prompt.

### 8. Register Advisor for Discovery

Add the advisor prompt file to the appropriate location for cross-project discovery:

**Option A (plugin-shared advisor):** Add the file to `advisors/{repo-name}/` in the plugin directory. This makes the advisor available in all plugin-enabled sessions.

**Option B (project-specific advisor):** Keep the file in the project's local prompt path (from Step 0). If you want it discoverable across projects without the plugin, add it to `~/.claude/advisors/prompts/{repo-name}/` as well.

For Option B, if `~/.claude/advisors/prompts/{repo-name}` doesn't exist yet:
1. Create it as a symlink to the project's prompt path
2. Register in `~/.claude/advisors/prompts/.repos` manifest (append repo-name if not listed)
3. Verify: Glob `~/.claude/advisors/prompts/{repo-name}/**/*.md` returns the advisor files

### 8b. Update the Directory

If `advisors/directory.md` exists (plugin-relative), append one row to the table under the appropriate `### {repo-name}` heading:

```
| {slug} | {display-name} | {summary} |
```

- **slug:** The advisor's kebab-case filename (without `.md`)
- **display-name:** Extracted from the prompt file's first line ("You are [Name], ...")
- **summary:** A concise phrase from the opening sentence describing the advisor

If `directory.md` doesn't exist, skip this step — the advisor is still discoverable via glob fallback in `use-advisor`.

### 9. Commit

Commit all changes with message: `feat: add {advisor-name} advisor`

## Notes

- All new advisors are created with `enabled: false` - they won't appear in the front-end until explicitly enabled
- Review generated avatars for likeness - the person should be clearly recognizable
- Review created prompt files to verify voice authenticity
