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

## Process

### 0. Environment Detection

Before any framework work, detect what infrastructure exists in the current repo.

**Framework path detection:**
1. Check the project's CLAUDE.md for framework prompt path configuration
2. If `frameworks/` exists at repo root and contains subdirectories with `prompt.md` files → use it
3. Else check for app-specific paths (e.g., `src/lib/frameworks/prompts/`) → use if found
4. Else → default to `frameworks/` at repo root (will create on first use)

**Infrastructure detection (check each):**

| Marker | Check | Enables |
|--------|-------|---------|
| Framework registry file | Check CLAUDE.md or Grep for registry | Registry entry (Step 5) |
| Eval infrastructure | Check for eval scenarios directory + eval script in package.json | Eval scenario (Step 6) |
| Build script | Read package.json for `build` script | Build verification (Step 8) |

**Print summary:**
```
Environment Detection:
  Framework path: {detected path}              → {found / will create}
  Registry:       {registry path}              → {found / not found (skipping)}
  Evals:          {eval dir}                   → {found / not found (skipping)}
  Build:          package.json build script    → {found / not found (skipping)}
```

### 1. Create Framework Folder

Create the folder structure:

```
{detected-framework-path}/{framework-id}/
├── prompt.md
├── examples.md
└── anti-examples.md
```

Where `{detected-framework-path}` is the path determined in Step 0. If the directory doesn't exist yet, create it.

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

> **Conditional:** Only run this step if `frameworks/registry.yaml` exists in the plugin directory. If not found, print: "Skipping registry entry — no framework registry found (lightweight mode)."

Append one entry to the `frameworks` list in `frameworks/registry.yaml`:

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
- **category:** Ask the user, suggesting from: positioning, startup, content-strategy, social-media, pricing, growth, podcasting, negotiation, leadership, strategy, psychology, health-autonomic, health-movement, health-fitness, conversion, onboarding
- **domains:** 2-5 expertise tags, derived from the framework's content
- **use_when:** Natural language trigger phrase for when to use this framework
- **required_documents, helpful_documents:** From `prompt.md` YAML frontmatter; omit keys if lists are empty

**Post-append validation:** After appending, parse the full `frameworks/registry.yaml` file. If YAML parsing fails, revert the append (restore the file from git) and report the error. One bad entry must not corrupt the registry for all consumers.

### 6. Create Eval Scenario

> **Conditional:** Only run this step if the project has an eval infrastructure (e.g., `e2e/` directory, detected in Step 0). If not found, print: "Skipping eval scenario — no eval infrastructure found."

If the project has eval infrastructure, create an eval scenario to establish a quality baseline. Check the project's CLAUDE.md or existing scenarios for the schema format. If `e2e/trigger-map.yaml` exists, add an entry mapping the new framework file paths (prompt.md, examples.md, anti-examples.md) to the new scenario path. If `e2e/promptfooconfig.yaml` exists, add `file://<scenario-path>` to its `scenarios` list.

**Important:** Check which advisor the framework path actually loads. The framework's primary advisor may not be the advisor the user selected. The voice fingerprint and anti-patterns must match the **actual responding advisor**.

Minimum scenario should include:
- Framework ID, mode, and advisor
- A realistic 2-turn conversation that triggers the framework
- Evaluation dimensions (flow, personalization, voice, framework)
- Voice fingerprint with signature phrases and anti-patterns
- Framework-specific terminology

Run the scenario to verify baseline quality. If it fails, classify the failure (prompt issue, eval calibration, or model variance) and fix. First-run failures are common — usually eval calibration.

### 7. Register Framework for Discovery

Add the framework folder to `frameworks/` in the plugin directory. This makes the framework available in all plugin-enabled sessions.

Place the framework at `frameworks/{framework-slug}/` containing `prompt.md` (required), `examples.md` (optional), and `anti-examples.md` (optional).

### 7b. Update Advisor and Framework Counts

Count the actual advisors and frameworks in the plugin directory and update all references so metadata stays in sync:

1. Count advisor prompt files in `advisors/prompts/` (`.md` files only)
2. Count framework directories in `frameworks/` (directories containing `prompt.md`)
3. Update every occurrence of the old counts in:
   - `README.md` — opening description, "How It Works" bullets, and Advisors section
   - `.claude-plugin/plugin.json` — `description` field
   - `.claude-plugin/marketplace.json` — `description` field

The description pattern is: `"{N} advisor personas, {M} frameworks"`. Also update standalone references like `"{N} expert advisors"` and `"{N} advisor prompts"` in `README.md`.

### 8. Verify

> **Conditional:** Only run build verification if a `build` script was detected in Step 0. If not found, print: "Skipping build verification — no build script found."

If the project has a build script, run it to verify no compilation errors were introduced. If the project has a web interface for testing, verify the framework works in the advisor's session.
