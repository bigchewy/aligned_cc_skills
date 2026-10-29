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

Every advisor gets a research file at `docs/advisors/new_advisors/v_{advisor_name}.md`. Create
the folder if it doesn't exist. The voice and the frameworks are built from this file, and the
check in Step 10 tests the prompt against it.

**If a research file or a find-potential-advisors brief exists**, read it. It counts as the
research file only if it has everything listed below. Fill in whatever is missing, and write the
result to the research file path.

**Otherwise**, research the advisor with `WebSearch` and `WebFetch`. Open the pages. A search
snippet is a lead, not a source.

The research file must contain:
- **Sources:** each book, essay, talk or interview you used, with its URL.
- **Voice:** 8 to 12 real quotes, copied word for word, each with its URL. Add their own terms
  and phrases, each with the URL of a page where they use it.
- **Framework candidates:** 5 to 10, each with the source it comes from (URL, or book and
  chapter).
- **From memory, not checked:** anything you believe but couldn't confirm on a page.

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

Step 5 builds every framework you select, so select only what you'll build. List the candidates
you didn't select in the prompt's Core Frameworks section as "also available in conversation,
not yet guided frameworks."

**Where each framework goes.** A framework that only makes sense in one project (for one
product, one brand, one codebase) goes in that project repo's `frameworks/`, even when the
advisor goes in the plugin. Only frameworks useful to anyone go in the plugin.

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
- Every phrase in quotation marks under "How You Speak" appears word for word in the research
  file's Voice section, with its URL. Lines in their style that aren't real quotes go outside
  quotation marks.

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

### 5. Add Each Selected Framework

Run `/aligned:add-framework` once for every framework selected in Step 2. Don't write framework
files by hand: the skill's source check and final check only run if you use it. Building one
framework and listing the rest as names is not done.

When frameworks for the same advisor, or for advisors built together, hand off to each other,
add a line in each `prompt.md` naming the other framework and when to switch to it.

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
   - `advisors/README.md` — the count in the headline, and a row for the new advisor in Quick Reference
   - `frameworks/README.md` — the count in the headline, and the category table, for each framework added

The description pattern is: `"{N} advisor personas, {M} frameworks"`. Also update standalone references like `"{N} expert advisors"` and `"{N} advisor prompts"` in `README.md`.

If `e2e/tests/test_readme_freshness.py` exists, run it. It fails when a count is behind.

### 9. Commit

Commit all changes with message: `feat: add {advisor-name} advisor`

### 10. Check and Report

Start a fresh agent, one that wrote none of the files. Give it the paths of everything this run
wrote, the research file, and `{base-directory}/report-template.md`. It follows the template's
"Check agent" section and returns a list of problems. Fix each problem, then commit the fixes.

Then report to the user in the template's shape. The report always ends with
**What was skipped or not done**. Write "Nothing" when nothing was.

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line
> printed at skill load. If compressed, follow `skills/_shared/resolve-skill-path.md`.

## Mistakes Real Runs Made

`anti-examples.md` shows each one with what to do instead. In short: one framework built when
three were picked, framework files written by hand, voice phrases from memory, no research file,
evals skipped for a reason that wasn't true, a one-product framework put in the plugin, and the
work never read before it was called done.

## Notes

- **Started inside another task.** Run every step anyway. The user gets an advisor they'll use
  for months, and the task you were on can wait the few minutes. Anything you skip goes in the
  report.
- **Several advisors at once.** Give each its own agent. Tell each agent to read this skill
  itself, rather than retelling the steps in your own words. When they finish, add the
  hand-offs between their frameworks (Step 5), then run Step 10 once over all of them.
- All new advisors are created with `enabled: false` - they won't appear in the front-end until explicitly enabled
- Review created prompt files to verify voice authenticity
- **Local advisors require two files.** Advisors have no glob fallback (unlike frameworks): a prompt
  file with no `advisors/registry.yaml` entry is a silent no-op — it will never appear in listings,
  panels, or contextual recommendation. When adding an advisor to a project-local repo, you MUST
  write both `advisors/registry.yaml` (full-schema entry) and `advisors/prompts/<id>.md`. This skill
  writes both; if you hand-author, do the same.
