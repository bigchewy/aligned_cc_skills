---
name: add-framework
description: Add a new framework to an existing advisor in the Virtual Board. Use this skill when the user wants to add a framework with the folder-based structure (prompt.md, examples.md, anti-examples.md).
---

# Add Framework

This skill guides adding a new framework to the Virtual Board of Advisors.

## Prerequisites

Before starting, gather:
- Framework name and ID (kebab-case)
- Associated advisor(s)
- Source material (book, methodology, research)
- Whether it's a check-in framework (true/false)

## Before You Start: Is This the Expert's Own Method?

A framework voiced by an advisor tells the user "this is how {Advisor} does it." So check two
things before building:

1. **Is it their own published method?** Find it in their book, essay or talk, and open the
   page. If the method belongs to someone else, build it under that person instead, or credit
   them by name in `prompt.md`'s opening. If you can't find a published method at all, say so to
   the user and stop. Don't build a method the expert never described.
2. **Is it useful outside this project?** A framework for one product, one brand or one codebase
   goes in the project repo's `frameworks/`, not in the plugin.

## Process

### 0. Environment Detection

Before any framework work, detect what infrastructure exists in the current repo.

**Plugin or project repo:** "Writing to the plugin itself" means project-cwd contains `.claude-plugin/plugin.json` whose `name` is `aligned`. Otherwise it is a project repo. In a project repo, the registry lives in the project (`<project-cwd>/frameworks/registry.yaml`), never in the plugin.

**Framework path detection:**
1. Check the project's CLAUDE.md for framework prompt path configuration
2. If `frameworks/` exists at repo root and contains subdirectories with `prompt.md` files → use it
3. Else check for app-specific paths (e.g., `src/lib/frameworks/prompts/`) → use if found
4. Else → default to `frameworks/` at repo root (will create on first use)

**Infrastructure detection (check each):**

| Marker | Check | Enables |
|--------|-------|---------|
| Framework registry file | Check CLAUDE.md, then `<project-cwd>/frameworks/registry.yaml` (or the plugin's `frameworks/registry.yaml` when writing to the plugin itself) | Registry entry (Step 5). In a project repo a missing registry is created, not skipped |
| Eval infrastructure | Check for eval scenarios directory + eval script in package.json | Eval scenario (Step 6) |
| Build script | Read package.json for `build` script | Build verification (Step 8) |

**Print summary:**
```
Environment Detection:
  Framework path: {detected path}              → {found / will create}
  Writing to:     {plugin itself / project repo}
  Registry:       {registry path}              → {found / will create (project repo) / not found (skipping, plugin lightweight mode)}
  Evals:          {eval dir}                   → {found / not found (skipping)}
  Build:          package.json build script    → {found / not found (skipping)}
```

### 1. Create Framework Folder

Create the folder structure:

```
{detected-framework-path}/{framework-id}/
├── prompt.md
├── examples.md
├── anti-examples.md
└── sources.md
```

Where `{detected-framework-path}` is the path determined in Step 0. If the directory doesn't exist yet, create it.

`sources.md` records where each part came from. The framework runner doesn't load it, so it costs
nothing when the framework runs. Write it as you go:
- One line per phase: the phase name and its source (URL, or book and chapter).
- A phase or rule you added that the expert never described starts with `Added:` and says why.
- Each quote or story attributed to the expert in `examples.md`, with its URL.
- Credit for anyone else whose method the framework uses.

### 2. Create prompt.md

Reference `frameworks/clearing-model/prompt.md` and `frameworks/braving-trust-inventory/prompt.md` as canonical examples of well-structured framework prompts.

Structure:
```markdown
You are {Advisor}, guiding someone through {framework} - {purpose}.

## The {Framework} Practice

{1-2 sentences of context}

### PHASE 1: {Name}

Start by saying:
"{Opening dialogue in advisor's voice}"

**WAIT for user response before continuing.**

### PHASE 2: {Name}

After user responds, say:
"{Acknowledge and guide to next element}"

**WAIT for user response before continuing.**

If they struggle:
"{Alternative prompts}"

[Continue for all phases...]

### PHASE N: Integration

Close with:
"{Summary and next steps}"

## Key Rules
- Complete each phase fully before moving to the next
- ALWAYS pause and wait for user input at marked points
- {Framework-specific guidance - positive framing}
```

### 3. Create examples.md

Reference `frameworks/clearing-model/examples.md` as the canonical example.

Structure by phase with 2-3 examples each:
- Golden path (user doing it right)
- Common struggles (user needs redirection)
- Edge cases (challenging scenarios)

Include notes explaining WHY each response works.

The user lines and coaching lines are written for the framework. Anything put in the expert's
mouth as their own words or story has to be in `sources.md` with its URL.

### 4. Create anti-examples.md

Reference `frameworks/clearing-model/anti-examples.md` as the canonical example.

Include 3-5 failure modes with:
- User input that triggers the mistake
- Wrong response
- Right response
- Positive explanation (focus on what TO DO)

### Writing Quality

When writing prompt.md, examples.md, and anti-examples.md, follow these craft guidelines:

**WAIT Markers:**
- After EVERY question, add: `**WAIT for the user to respond.**`
- Never rush through phases
- Let user responses guide the flow

**Scripted Language:**
- Use "Say something like:" + actual words
- Allows variation while maintaining intent
- More reliable than abstract instructions

**Branches:**
- Handle positive AND negative responses
- Include resistance scripts
- Know when to redirect to different approach

**Transitions:**
- Use `---` between phases
- Summarize before moving on
- Confirm alignment at key moments

**Common Mistakes to Avoid:**
1. **No pauses** — Rushing through without waiting for user input
2. **Missing branches** — Only handling the happy path
3. **Abstract instructions** — "Guide them through" instead of actual scripts
4. **No examples** — Expecting perfect execution without demonstration
5. **Rigid structure** — No flexibility for user's actual responses

### 5. Add Registry Entry

> **Where to write:** Writing to the plugin itself: append to the plugin's `frameworks/registry.yaml`. Project repo: append to `<project-cwd>/frameworks/registry.yaml`. If that file does not exist, create it with a one-line comment header and the list key, then append the entry:
>
> ```yaml
> # Project frameworks. Merged with the aligned plugin's registry; entries here win on a matching id.
> frameworks:
> ```
>
> **Conditional:** Skip this step only in lightweight mode: writing to the plugin itself, no `frameworks/registry.yaml` found. Print: "Skipping registry entry — no framework registry found (lightweight mode)." In a project repo the default is to create the registry.

Append one entry to the `frameworks` list in the registry file:

```yaml
  - id: {framework-slug}
    name: "{framework-display-name}"
    advisor: {advisor-slug}
    purpose: "{purpose from first line of prompt.md}"
    category: {category}
    domains: [{domains}]
    use_when: "{trigger phrase}"
    required_documents: [{list from frontmatter, or omit if empty}]
    helpful_documents: [{list from frontmatter, or omit if empty}]
```

Derive field values:
- **id:** The framework's directory name (kebab-case slug)
- **name, advisor, purpose:** Parsed from the first line of `prompt.md` (`You are {Advisor}, guiding someone through {Name} - {purpose}.`)
- **category:** Pick an existing category from the registry's other entries. A new category needs the user's yes first: ask, naming the closest existing category and why it doesn't fit.
- **domains:** 2-5 expertise tags, derived from the framework's content
- **use_when:** Natural language trigger phrase for when to use this framework
- **required_documents, helpful_documents:** From `prompt.md` YAML frontmatter; omit keys if lists are empty

**Post-append validation:** After appending, parse the full registry file you wrote. If YAML parsing fails, revert the append and report the error. Restore the previous content; if you just created the file, it is untracked, so delete the newly created file instead of restoring it from git. One bad entry must not corrupt the registry for all consumers.

### 6. Create Eval Scenario

> **Conditional:** Only run this step if the project has an eval infrastructure (e.g., `e2e/` directory, detected in Step 0). If not found, print: "Skipping eval scenario — no eval infrastructure found."

If the project has eval infrastructure, create an eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format, and copy an existing scenario's provider and options lines exactly. If `e2e/trigger-map.yaml` exists, add an entry mapping the new framework file paths (prompt.md, examples.md, anti-examples.md) to the new scenario path.

**Important:** Check which advisor the framework path actually loads. The framework's primary advisor may not be the advisor the user selected. The voice fingerprint and anti-patterns must match the **actual responding advisor**.

Minimum scenario should include:
- Framework ID, mode, and advisor
- A realistic 2-turn conversation that triggers the framework
- Evaluation dimensions (flow, personalization, voice, framework)
- Voice fingerprint with signature phrases and anti-patterns
- Framework-specific terminology

Run the new scenario to verify baseline quality. If `e2e/run_evals.py` exists, run only the new scenario from `e2e/` with `npm run eval -- <scenario-path>`. The runner uses the Claude Code login. Never skip the run because `ANTHROPIC_API_KEY` is not set. Never suggest `--all` unless a file in `e2e/providers/` changed; a new scenario only needs its own run. When a provider file did change, state the call count and token cost before asking the user. If `e2e/run_evals.py` does not exist, use the project's own eval command. If the scenario fails, classify the failure (prompt issue, eval calibration, or model variance) and fix. First-run failures are common — usually eval calibration.

### 7. Update Advisor and Framework Counts

> **Conditional:** Only when writing to the plugin itself. In a project repo, skip this step: the plugin's README and manifests do not describe project content.

Count the actual advisors and frameworks in the plugin directory and update all references so metadata stays in sync:

1. Count advisor prompt files in `advisors/prompts/` (`.md` files only)
2. Count framework directories in `frameworks/` (directories containing `prompt.md`)
3. Update every occurrence of the old counts in:
   - `README.md` — opening description, "How It Works" bullets, and Advisors section
   - `.claude-plugin/plugin.json` — `description` field
   - `.claude-plugin/marketplace.json` — `description` field
   - `frameworks/README.md` — the count in the headline, and the category table
   - `advisors/README.md` — only if an advisor was added too

The description pattern is: `"{N} advisor personas, {M} frameworks"`. Also update standalone references like `"{N} expert advisors"` and `"{N} advisor prompts"` in `README.md`.

If `e2e/tests/test_readme_freshness.py` exists, run it. It fails when a count is behind.

### 8. Verify

> **Conditional:** Only run build verification if a `build` script was detected in Step 0. If not found, print: "Skipping build verification — no build script found."

If the project has a build script, run it to verify no compilation errors were introduced. If the project has a web interface for testing, verify the framework works in the advisor's session.

### 9. Check and Report

Start a fresh agent, one that wrote none of the files. Give it the framework folder, the
registry path, and `{base-directory}/report-template.md`. It follows the template's "Check agent"
section and returns a list of problems. Fix each problem.

Then report to the user in the template's shape. The report always ends with
**What was skipped or not done**. Write "Nothing" when nothing was.

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line
> printed at skill load. If compressed, follow `skills/_shared/resolve-skill-path.md`.

## Mistakes Real Runs Made

`anti-examples.md` shows each one with what to do instead. In short: phases invented for an
expert who never wrote them, someone else's method voiced as the advisor's, a one-product
framework put in the plugin, a category made up without asking, and the README counts missed.

## Notes

- **Started inside another task.** Run every step anyway, including the eval and the check.
  Anything you skip goes in the report.
