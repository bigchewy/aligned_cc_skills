# Skill Auto-Router Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Build a UserPromptSubmit hook that automatically routes natural-language user prompts to the correct framework or skill, so users never need to know slash commands.

**Source Design Doc:** `docs/plans/2026-04-09-skill-auto-router-design.md`

**Mockups:** `docs/mockups/skill-auto-router.html`

**Architecture:** A `UserPromptSubmit` hook (`hooks/skill-router.js`) reads a precomputed routing index (`skill-router.json`) and runs a three-step cascade: (1) framework match against trigger/intent phrases, (2) skill classification via keyword signal patterns with exclusions, (3) pass-through if confidence is below threshold. A build script (`scripts/build-router-index.js`) generates the routing index from framework content using LLM-assisted intent phrase extraction. Telemetry logs routing decisions to a local JSONL file.

**Tech Stack:** Node.js (hook script, build script), JSON (routing index), PromptFoo + pytest (eval), JSONL (telemetry)

---

### Task 1: Create the routing index JSON schema and seed file

**Files:**
- Create: `skill-router.json`

**Step 1: Write the routing index seed file**

Create `skill-router.json` at the repo root with the structure defined in the design doc. Seed it with:
- An empty `frameworks` array (populated by the build script later)
- The four skill routing entries from the design doc: `root-cause-analysis`, `persona-panel`, `kickstart`, `brainstorming` — each with `signals`, `exclude`, and `min_signals` fields

```json
{
  "version": 1,
  "frameworks": [],
  "skills": {
    "root-cause-analysis": {
      "signals": ["why is", "why are", "what's causing", "root cause", "keeps happening", "not working", "failing", "broken", "declining"],
      "exclude": ["why is the sky", "why is it called", "why is there"],
      "min_signals": 2
    },
    "persona-panel": {
      "signals": ["test this with", "how would buyers", "audience reaction", "customer feedback", "persona", "would users"],
      "exclude": [],
      "min_signals": 2
    },
    "kickstart": {
      "signals": ["new project", "start a project", "scaffold", "bootstrap", "from scratch", "set up a new"],
      "exclude": [],
      "min_signals": 2
    },
    "brainstorming": {
      "signals": ["figure out", "think through", "strategy for", "how should I", "help me plan", "design a", "what's the best way to"],
      "exclude": ["help me plan my", "figure out what to eat", "think through my schedule"],
      "min_signals": 2
    }
  }
}
```

**Step 2: Commit**

```bash
git add skill-router.json
git commit -m "feat(router): add skill-router.json seed with skill signal patterns"
```

---

### Task 2: Write the UserPromptSubmit hook — core matching logic

**Files:**
- Create: `hooks/skill-router.js`

**Step 1: Write the hook script**

The hook receives JSON on stdin with the user's prompt in `data.tool_input.user_prompt` (for `UserPromptSubmit` hooks, the input contains the user's message). The hook outputs a JSON response that can append text to the prompt via `hookSpecificOutput`.

Follow the existing hook pattern from `hooks/usage-tracker.js` — async stdin read via `process.stdin.on('data')`, JSON parse, JSON output.

> **NOTE:** The `UserPromptSubmit` hook output schema uses `additionalContext` to append invisible context to the prompt. Before implementing, verify this field name against the current Claude Code hooks documentation at https://docs.anthropic.com/en/docs/claude-code/hooks. If the field name differs, update `outputDirective()` accordingly.

```javascript
#!/usr/bin/env node
// skill-router.js — UserPromptSubmit hook
// Routes user prompts to frameworks or skills via rule-based cascade.
// SYNC REQUIRED: matchFrameworks() and matchSkills() are duplicated in
// e2e/tests/router-eval-helper.js for testing. Changes here must be
// mirrored there, and vice versa.

const fs = require('fs');
const path = require('path');

const PLUGIN_ROOT = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, '..');
const INDEX_PATH = path.join(PLUGIN_ROOT, 'skill-router.json');
const LOG_DIR = path.join(process.env.HOME, '.claude', 'usage-tracking');
const LOG_FILE = path.join(LOG_DIR, 'router-decisions.jsonl');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const prompt = data.tool_input?.user_prompt || '';
    if (!prompt) { exit(); return; }

    // Step 0: Skip explicit skill invocations
    if (/^\s*\/aligned:/.test(prompt)) { exit(); return; }

    const index = loadIndex();
    if (!index) { exit(); return; }

    const promptLower = prompt.toLowerCase();

    // Step 1: Framework match
    const frameworkResult = matchFrameworks(promptLower, index.frameworks || []);
    if (frameworkResult) {
      logDecision('framework', frameworkResult, prompt);
      outputDirective(frameworkResult);
      return;
    }

    // Step 2: Skill classification
    const skillResult = matchSkills(promptLower, index.skills || {});
    if (skillResult) {
      logDecision('skill', skillResult, prompt);
      outputDirective(skillResult);
      return;
    }

    // Step 3: Pass-through
    logDecision('pass-through', null, prompt);
    exit();
  } catch (_) {
    exit();
  }
});

function loadIndex() {
  try {
    return JSON.parse(fs.readFileSync(INDEX_PATH, 'utf8'));
  } catch (_) {
    return null;
  }
}

function matchFrameworks(promptLower, frameworks) {
  const matches = [];
  for (const fw of frameworks) {
    let score = 0;
    // Check trigger words (exact name matches — high confidence)
    for (const trigger of (fw.triggers || [])) {
      if (promptLower.includes(trigger.toLowerCase())) score += 3;
    }
    // Check intent phrases (contextual matches — medium confidence)
    for (const phrase of (fw.intent_phrases || [])) {
      if (promptLower.includes(phrase.toLowerCase())) score += 2;
    }
    if (score >= 3) {
      matches.push({ ...fw, score });
    }
  }
  if (matches.length === 0) return null;
  matches.sort((a, b) => b.score - a.score);
  if (matches.length === 1) {
    return { type: 'single_framework', match: matches[0] };
  }
  return { type: 'multiple_frameworks', matches: matches.slice(0, 3) };
}

function matchSkills(promptLower, skills) {
  for (const [skillId, config] of Object.entries(skills)) {
    // Check exclusion patterns first
    const excluded = (config.exclude || []).some(ex => promptLower.includes(ex.toLowerCase()));
    if (excluded) continue;

    // Count signal matches
    const matchedSignals = (config.signals || []).filter(sig =>
      promptLower.includes(sig.toLowerCase())
    );

    const minRequired = config.min_signals || 2;
    if (matchedSignals.length >= minRequired) {
      return { type: 'skill', skillId, matchedSignals };
    }

    // Relaxed match: 1 signal + long prompt with domain vocabulary
    if (matchedSignals.length === 1 && promptLower.split(/\s+/).length > 20) {
      return { type: 'skill', skillId, matchedSignals, relaxed: true };
    }
  }
  return null;
}

function buildDirectiveText(result) {
  if (result.type === 'single_framework') {
    const fw = result.match;
    return `[ALIGNED-ROUTER] A framework matches this request. Present it to the user and proceed:\n` +
      `- Framework: "${fw.name}" (advisor: ${fw.advisor})\n` +
      `- Say: "This looks like a ${fw.intent_phrases?.[0] || fw.name} problem. I'll walk you through ${fw.name} to structure your thinking. Just say 'skip' if you'd rather go freeform."\n` +
      `- Then: Use Skill(aligned:use-framework) with framework "${fw.id}"`;
  }
  if (result.type === 'multiple_frameworks') {
    const options = result.matches.map((fw, i) =>
      `- Option ${i + 1}: "${fw.name}" — ${fw.intent_phrases?.[0] || 'structured analysis'} (advisor: ${fw.advisor})`
    ).join('\n');
    return `[ALIGNED-ROUTER] Multiple frameworks may apply. Present options and let the user choose:\n` +
      options + '\n' +
      `- Fallback: "Or just talk it through freeform"\n` +
      `- Then: Use Skill(aligned:use-framework) with their choice, or Use Skill(aligned:brainstorming) for freeform`;
  }
  if (result.type === 'skill') {
    const intentMap = {
      'root-cause-analysis': { intent: 'diagnose/fix', say: 'This sounds like a diagnostic problem. I\'ll help you trace the root cause. Say \'skip\' if you\'d rather just discuss it.' },
      'persona-panel': { intent: 'test with audience', say: 'This sounds like you want to test content with your audience. I\'ll set up a persona panel. Say \'skip\' if you\'d rather just discuss it.' },
      'kickstart': { intent: 'start a project', say: 'Sounds like a new project. I\'ll help scaffold it with best practices. Say \'skip\' if you\'d rather start manually.' },
      'brainstorming': { intent: 'explore/strategize', say: 'This sounds like a problem worth thinking through systematically. I\'ll run a structured brainstorm. Say \'skip\' if you\'d rather go freeform.' }
    };
    const mapping = intentMap[result.skillId] || { intent: result.skillId, say: `I'll use the ${result.skillId} skill. Say 'skip' if you'd rather not.` };
    return `[ALIGNED-ROUTER] No framework match, but intent is clear.\n` +
      `- Intent: ${mapping.intent}\n` +
      `- Say: "${mapping.say}"\n` +
      `- Then: Use Skill(aligned:${result.skillId})`;
  }
  return '';
}

function outputDirective(result) {
  const directive = buildDirectiveText(result);
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      suppressPrompt: false,
      additionalContext: directive
    }
  }));
}

function logDecision(type, result, prompt) {
  try {
    fs.mkdirSync(LOG_DIR, { recursive: true });
    const entry = {
      ts: new Date().toISOString(),
      type,
      route: result?.type || 'none',
      detail: result?.type === 'single_framework' ? result.match.id
        : result?.type === 'multiple_frameworks' ? result.matches.map(m => m.id)
        : result?.skillId || null,
      prompt_length: prompt.length,
      prompt_preview: prompt.substring(0, 100)
    };
    fs.appendFileSync(LOG_FILE, JSON.stringify(entry) + '\n');
  } catch (_) {
    // Telemetry failure is non-blocking
  }
}

function exit() {
  process.exit(0);
}
```

**Step 2: Commit**

```bash
git add hooks/skill-router.js
git commit -m "feat(router): add UserPromptSubmit hook with framework and skill matching"
```

---

### Task 3: Register the hook in hooks.json

**Files:**
- Modify: `hooks/hooks.json` (add `UserPromptSubmit` entry)

**Step 1: Add the UserPromptSubmit hook entry**

Read `hooks/hooks.json`. The file has a top-level `"hooks"` wrapper object containing `"PreToolUse"` and `"PostToolUse"`. Add `"UserPromptSubmit"` as a new key **inside** the `"hooks"` object (sibling to `PreToolUse` and `PostToolUse`):

```json
{
  "hooks": {
    "PreToolUse": [ ... existing ... ],
    "PostToolUse": [ ... existing ... ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "node ${CLAUDE_PLUGIN_ROOT}/hooks/skill-router.js",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

The empty `matcher` string means it fires on all user prompts (UserPromptSubmit hooks don't filter by tool name).

**Step 2: Commit**

```bash
git add hooks/hooks.json
git commit -m "feat(router): register skill-router hook in hooks.json"
```

---

### Task 4: Write the build script — framework index generator

**Files:**
- Create: `scripts/build-router-index.js`

**Step 1: Write the build script**

This script reads all framework `prompt.md` files, extracts metadata (name, advisor, slug), and generates trigger/intent phrases. It outputs a complete `skill-router.json` that merges generated framework data with the existing skill routing rules.

The script uses the Anthropic SDK to generate intent phrases from framework descriptions. It requires `ANTHROPIC_API_KEY` in the environment.

```javascript
#!/usr/bin/env node
// build-router-index.js — Generates skill-router.json from framework content.
// Run: node scripts/build-router-index.js
// Requires: ANTHROPIC_API_KEY environment variable

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..');
const FRAMEWORKS_DIR = path.join(REPO_ROOT, 'frameworks');
const OUTPUT_PATH = path.join(REPO_ROOT, 'skill-router.json');
const BATCH_SIZE = 10; // frameworks per LLM call

async function main() {
  const Anthropic = require('@anthropic-ai/sdk');
  const client = new Anthropic.default();

  // 1. Discover frameworks
  const frameworkDirs = fs.readdirSync(FRAMEWORKS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  console.log(`Found ${frameworkDirs.length} framework directories`);

  // 2. Extract metadata from first line of each prompt.md
  const frameworks = [];
  for (const slug of frameworkDirs) {
    const promptPath = path.join(FRAMEWORKS_DIR, slug, 'prompt.md');
    if (!fs.existsSync(promptPath)) continue;

    const content = fs.readFileSync(promptPath, 'utf8');
    // Skip YAML frontmatter
    const lines = content.split('\n');
    let firstContentLine = '';
    let inFrontmatter = false;
    for (const line of lines) {
      if (line.trim() === '---') {
        inFrontmatter = !inFrontmatter;
        continue;
      }
      if (!inFrontmatter && line.trim()) {
        firstContentLine = line.trim();
        break;
      }
    }

    // Parse: "You are {Advisor}, guiding someone through {Framework} - {purpose}."
    const match = firstContentLine.match(
      /^You are (.+?),\s*guiding someone through (.+?)\s*[-–—.]/
    );
    if (!match) {
      console.warn(`Skipping ${slug}: first line doesn't match expected format`);
      continue;
    }

    const advisorName = match[1].trim();
    const frameworkName = match[2].trim();
    // Derive advisor slug from registry naming convention
    const advisorSlug = advisorName.toLowerCase()
      .replace(/^dr\.\s*/, '')
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9-]/g, '');

    // Extract first ~500 chars of content for LLM context
    const description = content.substring(0, 500);

    frameworks.push({ slug, name: frameworkName, advisor: advisorSlug, advisorName, description });
  }

  console.log(`Parsed ${frameworks.length} frameworks with valid metadata`);

  // 3. Generate trigger/intent phrases via LLM in batches
  const enrichedFrameworks = [];
  for (let i = 0; i < frameworks.length; i += BATCH_SIZE) {
    const batch = frameworks.slice(i, i + BATCH_SIZE);
    console.log(`Processing batch ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(frameworks.length / BATCH_SIZE)}`);

    const batchInput = batch.map((fw, idx) => (
      `Framework ${idx + 1}: "${fw.name}" (slug: ${fw.slug})\n` +
      `Advisor: ${fw.advisorName}\n` +
      `Description excerpt: ${fw.description.substring(0, 300)}\n`
    )).join('\n---\n');

    const response = await client.messages.create({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 2000,
      messages: [{
        role: 'user',
        content: `For each framework below, generate two lists:\n` +
          `1. "triggers" — 2-4 short exact-match terms users might type (framework name fragments, method names, author names). These are high-confidence signals.\n` +
          `2. "intent_phrases" — 3-6 natural language phrases describing the PROBLEM the framework solves (not the framework name). These are what a user would type when they have the problem but don't know the framework exists.\n\n` +
          `Output valid JSON array. Each element: {"slug": "...", "triggers": [...], "intent_phrases": [...]}\n` +
          `No markdown fencing. Just the JSON array.\n\n` +
          batchInput
      }]
    });

    try {
      const text = response.content[0].text.trim();
      const results = JSON.parse(text);
      for (const result of results) {
        const fw = batch.find(f => f.slug === result.slug);
        if (fw) {
          enrichedFrameworks.push({
            id: fw.slug,
            name: fw.name,
            advisor: fw.advisor,
            triggers: result.triggers || [],
            intent_phrases: result.intent_phrases || []
          });
        }
      }
    } catch (e) {
      console.error(`Failed to parse LLM response for batch starting at ${i}: ${e.message}`);
      // Fall back to basic triggers for this batch
      for (const fw of batch) {
        enrichedFrameworks.push({
          id: fw.slug,
          name: fw.name,
          advisor: fw.advisor,
          triggers: [fw.slug.replace(/-/g, ' '), fw.name.toLowerCase()],
          intent_phrases: []
        });
      }
    }
  }

  // 4. Load existing skill routing rules
  let existingSkills = {};
  if (fs.existsSync(OUTPUT_PATH)) {
    try {
      const existing = JSON.parse(fs.readFileSync(OUTPUT_PATH, 'utf8'));
      existingSkills = existing.skills || {};
    } catch (_) {}
  }

  // 5. Write output
  const output = {
    version: 1,
    generated_at: new Date().toISOString(),
    frameworks: enrichedFrameworks,
    skills: existingSkills
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output, null, 2) + '\n');
  console.log(`Wrote ${enrichedFrameworks.length} frameworks + ${Object.keys(existingSkills).length} skill rules to ${OUTPUT_PATH}`);
}

main().catch(e => {
  console.error(`Build failed: ${e.message}`);
  process.exit(1);
});
```

**Step 2: Verify the script parses without syntax errors**

Run: `node -c scripts/build-router-index.js`
Expected: No output (clean parse)

**Step 3: Commit**

```bash
git add scripts/build-router-index.js
git commit -m "feat(router): add build script for generating routing index from framework content"
```

---

### Task 5: Install the Anthropic SDK as a dev dependency

**Files:**
- Create: `package.json` (if it doesn't exist at repo root)
- Modify: `package.json` (add `@anthropic-ai/sdk` dev dependency)

**Step 1: Check if package.json exists at repo root**

Use Glob to check for `/Users/ericpage/software/aligned_cc_skills/package.json`. If it doesn't exist, create it:

```json
{
  "name": "aligned-cc-skills",
  "version": "0.17.0",
  "private": true,
  "description": "Skill stack for Claude Code",
  "devDependencies": {}
}
```

**Step 2: Install the Anthropic SDK**

Run: `npm install --save-dev @anthropic-ai/sdk`
Expected: Package added to `devDependencies` in `package.json`

> **Note:** This creates a root-level `package.json` alongside the existing `e2e/package.json`. The root package handles build-time dependencies (Anthropic SDK); the `e2e/` package handles eval dependencies (PromptFoo). Both must be installed separately (`npm install` at root for build script, `cd e2e && npm install` for evals).

**Step 3: Add node_modules to .gitignore if not already there**

Check `.gitignore` for `node_modules`. If missing, append `node_modules/` to it.

**Step 4: Commit**

```bash
git add package.json package-lock.json .gitignore
git commit -m "chore: add @anthropic-ai/sdk dev dependency for router build script"
```

---

### Task 6: Run the build script to generate the framework index

**Files:**
- Modify: `skill-router.json` (populated with framework data)

**Step 1: Verify model ID and run the build script**

First, verify the model ID works with a minimal test call:
Run: `node -e "const A = require('@anthropic-ai/sdk'); const c = new A.default(); c.messages.create({model:'claude-haiku-4-5-20251001',max_tokens:10,messages:[{role:'user',content:'hi'}]}).then(r=>console.log('OK:',r.model)).catch(e=>console.error('FAIL:',e.message))"`
Expected: `OK: claude-haiku-4-5-20251001` (or similar). If the model ID is rejected, check the Anthropic API docs for the current Haiku model ID and update `build-router-index.js` accordingly.

Then run the build script:
Run: `ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY node scripts/build-router-index.js`
Expected: Output showing `Found 138 framework directories`, batch processing logs, and `Wrote N frameworks + 4 skill rules to skill-router.json`

**Step 2: Verify the output**

Read `skill-router.json` and verify:
- `frameworks` array has entries with `id`, `name`, `advisor`, `triggers`, `intent_phrases`
- `skills` object preserves the four original skill entries
- `version` is 1

**Step 3: Spot-check framework entries**

Verify a few framework entries have reasonable triggers and intent phrases. For example, the `positioning-canvas` framework should have triggers like `"positioning canvas"`, `"positioning"` and intent phrases related to product positioning problems.

**Step 4: Commit**

```bash
git add skill-router.json
git commit -m "feat(router): generate framework routing index from 138 frameworks"
```

---

### Task 7: Create the test corpus file structure

**Files:**
- Create: `e2e/scenarios/skill-router/test-corpus.yaml`

**Step 1: Create the test corpus**

Create a YAML file with 50+ labeled test prompts. Each entry has:
- `prompt`: the user's natural language input
- `expected_route`: one of `framework:<slug>`, `skill:<slug>`, or `pass-through`
- `category`: one of `framework-single`, `framework-multiple`, `skill`, `pass-through`, `explicit-invocation`

Organize by category. Include edge cases: explicit `/aligned:` invocations (should pass through), prompts that contain a single signal word (should NOT trigger skill routing), prompts with exclusion phrases, ambiguous prompts.

```yaml
# Skill Auto-Router Test Corpus
# Each entry: prompt text, expected routing decision, category
# Used for measuring precision, false positive rate, and override rate

test_cases:
  # --- Explicit invocations (must pass through) ---
  - prompt: "/aligned:brainstorming I want to redesign our pricing page"
    expected_route: pass-through
    category: explicit-invocation
    reason: "Explicit skill invocation should bypass router"

  - prompt: "/aligned:use-advisor April Dunford"
    expected_route: pass-through
    category: explicit-invocation
    reason: "Explicit skill invocation should bypass router"

  # --- Framework matches (single) ---
  - prompt: "I need to figure out how to position our product against cheaper competitors"
    expected_route: "framework:positioning-canvas"
    category: framework-single
    reason: "Positioning problem maps to positioning canvas"

  - prompt: "We need to define our competitive alternatives and differentiated value"
    expected_route: "framework:5-components-positioning"
    category: framework-single
    reason: "Mentions specific positioning methodology concepts"

  - prompt: "I want to apply first principles thinking to our infrastructure costs"
    expected_route: "framework:first-principles-thinking"
    category: framework-single
    reason: "Explicit mention of first principles"

  - prompt: "Help me build a content strategy for our SaaS blog"
    expected_route: "framework:content-inc-model"
    category: framework-single
    reason: "Content strategy maps to Content Inc"

  - prompt: "We need to validate whether our startup idea has legs before building anything"
    expected_route: "framework:leap-of-faith-assumptions"
    category: framework-single
    reason: "Startup validation maps to lean startup frameworks"

  - prompt: "I need to set up a growth hacking process for our product launch"
    expected_route: "framework:growth-hacking-process"
    category: framework-single
    reason: "Explicit mention of growth hacking"

  - prompt: "Our landing page conversion rate is terrible, help me fix it"
    expected_route: "framework:landing-page-assembly"
    category: framework-single
    reason: "Landing page conversion maps to landing page framework"

  - prompt: "I want to understand the jobs our customers are hiring our product to do"
    expected_route: "framework:jobs-to-be-done"
    category: framework-single
    reason: "JTBD language maps directly"

  # --- Framework matches (multiple possible) ---
  - prompt: "We're losing enterprise deals to a competitor who's undercutting us on price"
    expected_route: "framework:multiple"
    category: framework-multiple
    reason: "Could be positioning, competitive analysis, or pricing"

  - prompt: "I need to figure out our go-to-market strategy for a new product"
    expected_route: "framework:multiple"
    category: framework-multiple
    reason: "GTM spans positioning, market type, audience"

  # --- Skill matches ---
  - prompt: "Our onboarding process is a mess and new hires keep quitting in the first 90 days. What's causing this and how do we fix it?"
    expected_route: "skill:root-cause-analysis"
    category: skill
    reason: "Diagnostic problem with 'what's causing' + 'fix' signals"

  - prompt: "Our revenue has been declining for three months and I don't know why it's not working"
    expected_route: "skill:root-cause-analysis"
    category: skill
    reason: "'declining' + 'not working' signals"

  - prompt: "Why is our customer churn rate so high? It keeps happening despite our efforts"
    expected_route: "skill:root-cause-analysis"
    category: skill
    reason: "'why is' + 'keeps happening' signals"

  - prompt: "I want to test this sales pitch with potential buyers and see how they'd react"
    expected_route: "skill:persona-panel"
    category: skill
    reason: "'test this with' + 'buyers' signals"

  - prompt: "How would our target audience react to this new pricing page? Can you simulate customer feedback?"
    expected_route: "skill:persona-panel"
    category: skill
    reason: "'audience reaction' + 'customer feedback' signals"

  - prompt: "I want to start a new SaaS project from scratch with proper conventions"
    expected_route: "skill:kickstart"
    category: skill
    reason: "'new project' equivalent + 'from scratch' signals"

  - prompt: "Help me scaffold a new project with testing and CI set up"
    expected_route: "skill:kickstart"
    category: skill
    reason: "'scaffold' + 'new project' context"

  - prompt: "I need to figure out the best pricing strategy for our enterprise tier. Help me think through the tradeoffs."
    expected_route: "skill:brainstorming"
    category: skill
    reason: "'figure out' + 'think through' signals"

  - prompt: "How should I approach our Q3 planning? I need to design a process that works for a team of 30."
    expected_route: "skill:brainstorming"
    category: skill
    reason: "'how should I' + 'design a' signals"

  - prompt: "Help me plan our product roadmap for the next two quarters"
    expected_route: "skill:brainstorming"
    category: skill
    reason: "'help me plan' + strategic context"

  # --- Pass-through (must NOT trigger routing) ---
  - prompt: "Summarize this document for me"
    expected_route: pass-through
    category: pass-through
    reason: "Generic request, no skill/framework signals"

  - prompt: "What does this error mean: TypeError cannot read property of undefined"
    expected_route: pass-through
    category: pass-through
    reason: "Code debugging, not diagnostic RCA"

  - prompt: "Write a Python script that reads a CSV and outputs JSON"
    expected_route: pass-through
    category: pass-through
    reason: "Direct coding task"

  - prompt: "Explain how React hooks work"
    expected_route: pass-through
    category: pass-through
    reason: "Educational question"

  - prompt: "Fix the bug in my authentication middleware"
    expected_route: pass-through
    category: pass-through
    reason: "Code fix request, not strategic RCA"

  - prompt: "Why is the sky blue?"
    expected_route: pass-through
    category: pass-through
    reason: "Excluded phrase for RCA"

  - prompt: "Why is it called JavaScript when it has nothing to do with Java?"
    expected_route: pass-through
    category: pass-through
    reason: "Excluded phrase for RCA"

  - prompt: "Help me plan my vacation to Portugal"
    expected_route: pass-through
    category: pass-through
    reason: "Excluded phrase for brainstorming ('help me plan my')"

  - prompt: "Figure out what to eat for dinner tonight"
    expected_route: pass-through
    category: pass-through
    reason: "Excluded phrase for brainstorming"

  - prompt: "Can you read this file and tell me what it does?"
    expected_route: pass-through
    category: pass-through
    reason: "Simple file reading request"

  - prompt: "Create a git branch called feature/new-api"
    expected_route: pass-through
    category: pass-through
    reason: "Git command, not a skill"

  - prompt: "What's the weather like today?"
    expected_route: pass-through
    category: pass-through
    reason: "Casual question"

  - prompt: "Run the test suite and fix any failures"
    expected_route: pass-through
    category: pass-through
    reason: "Direct coding task"

  - prompt: "Review this pull request for me"
    expected_route: pass-through
    category: pass-through
    reason: "Code review request"

  - prompt: "How do I deploy to production?"
    expected_route: pass-through
    category: pass-through
    reason: "DevOps question"

  # --- Edge cases: single signal (should NOT trigger) ---
  - prompt: "Why is this function returning null?"
    expected_route: pass-through
    category: pass-through
    reason: "Single RCA signal ('why is') in code context — below threshold"

  - prompt: "What's the best way to sort an array in JavaScript?"
    expected_route: pass-through
    category: pass-through
    reason: "Single brainstorming signal in code context — below threshold"

  - prompt: "Help me plan the database schema"
    expected_route: pass-through
    category: pass-through
    reason: "Single brainstorming signal in code context — below threshold"

  - prompt: "I need to figure out this regex"
    expected_route: pass-through
    category: pass-through
    reason: "Single brainstorming signal in code context — below threshold"

  - prompt: "This API keeps failing with a 500 error"
    expected_route: pass-through
    category: pass-through
    reason: "Single RCA signal ('failing') in code context — below threshold"

  # --- Edge cases: long prompts with single signal (may trigger relaxed match) ---
  - prompt: "We've been struggling with our go-to-market approach for the past quarter. Our sales team is confused about who to target, marketing is creating content for the wrong audience, and our product team is building features nobody asked for. I need help figuring out how to get everyone aligned on who our ideal customer actually is."
    expected_route: "skill:brainstorming"
    category: skill
    reason: "Long prompt with domain vocabulary + 'figuring out' signal triggers relaxed match"

  # --- Edge cases: coding + business hybrid ---
  - prompt: "Our SaaS metrics dashboard is not working properly and our MRR has been declining. I think there's a data pipeline issue but also wondering if our pricing is wrong."
    expected_route: "skill:root-cause-analysis"
    category: skill
    reason: "'not working' + 'declining' signals — diagnostic intent clear despite code mention"

  # --- Additional pass-through to ensure 50+ ---
  - prompt: "Refactor this component to use TypeScript"
    expected_route: pass-through
    category: pass-through
    reason: "Refactoring task"

  - prompt: "Add error handling to the payment processing function"
    expected_route: pass-through
    category: pass-through
    reason: "Code improvement task"

  - prompt: "What's the difference between useMemo and useCallback?"
    expected_route: pass-through
    category: pass-through
    reason: "Technical question"

  - prompt: "Generate a README for this project"
    expected_route: pass-through
    category: pass-through
    reason: "Documentation task"

  - prompt: "Set up ESLint and Prettier for the project"
    expected_route: pass-through
    category: pass-through
    reason: "Tooling setup"

  - prompt: "I committed to the wrong branch, help me fix it"
    expected_route: pass-through
    category: pass-through
    reason: "Git recovery task"

  - prompt: "Translate this component from class-based to functional"
    expected_route: pass-through
    category: pass-through
    reason: "Code migration task"
```

**Step 2: Commit**

```bash
git add e2e/scenarios/skill-router/test-corpus.yaml
git commit -m "feat(router): add 50+ labeled test prompts for routing accuracy measurement"
```

---

### Task 8: Write the test runner for the test corpus

**Files:**
- Create: `e2e/tests/test_router_accuracy.py`

**Step 1: Write the pytest test**

This test loads the test corpus, runs each prompt through the router's matching logic (extracted to a shared module), and measures precision and false positive rate.

Rather than shelling out to the hook script for each test case, import the matching logic directly. Since the hook is Node.js, the test will shell out to a small Node.js evaluation script.

```python
"""Test routing accuracy against the labeled test corpus."""
import json
import subprocess
import yaml
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
CORPUS_PATH = REPO_ROOT / "e2e" / "scenarios" / "skill-router" / "test-corpus.yaml"
EVAL_SCRIPT = REPO_ROOT / "e2e" / "tests" / "router-eval-helper.js"


@pytest.fixture(scope="module")
def corpus():
    with open(CORPUS_PATH) as f:
        data = yaml.safe_load(f)
    return data["test_cases"]


@pytest.fixture(scope="module")
def router_results(corpus):
    """Run all prompts through the router and collect results."""
    prompts = [tc["prompt"] for tc in corpus]
    result = subprocess.run(
        ["node", str(EVAL_SCRIPT), json.dumps(prompts)],
        capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    assert result.returncode == 0, f"Eval script failed: {result.stderr}"
    return json.loads(result.stdout)


def test_corpus_has_minimum_size(corpus):
    assert len(corpus) >= 50, f"Test corpus has only {len(corpus)} cases, need 50+"


def test_explicit_invocations_pass_through(corpus, router_results):
    """Explicit /aligned: invocations must always pass through."""
    for tc, result in zip(corpus, router_results):
        if tc["category"] == "explicit-invocation":
            assert result["type"] == "pass-through", (
                f"Explicit invocation was routed: {tc['prompt'][:60]}"
            )


def test_pass_through_cases_not_routed(corpus, router_results):
    """Pass-through prompts must not trigger routing (false positive check)."""
    false_positives = []
    for tc, result in zip(corpus, router_results):
        if tc["category"] == "pass-through":
            if result["type"] != "pass-through":
                false_positives.append({
                    "prompt": tc["prompt"][:80],
                    "routed_to": result.get("detail"),
                })

    pass_through_count = sum(1 for tc in corpus if tc["category"] == "pass-through")
    fp_rate = len(false_positives) / pass_through_count if pass_through_count else 0

    assert fp_rate <= 0.05, (
        f"False positive rate {fp_rate:.1%} exceeds 5% threshold. "
        f"False positives: {json.dumps(false_positives, indent=2)}"
    )


def test_skill_routing_precision(corpus, router_results):
    """When router fires for skill routes, it must pick the right skill."""
    correct = 0
    total = 0
    mismatches = []

    for tc, result in zip(corpus, router_results):
        if tc["category"] == "skill":
            total += 1
            expected_skill = tc["expected_route"].replace("skill:", "")
            if result.get("detail") == expected_skill:
                correct += 1
            else:
                mismatches.append({
                    "prompt": tc["prompt"][:80],
                    "expected": expected_skill,
                    "got": result.get("detail"),
                })

    precision = correct / total if total else 0
    assert precision >= 0.80, (
        f"Skill routing precision {precision:.1%} below 80% gate. "
        f"Mismatches: {json.dumps(mismatches, indent=2)}"
    )


def test_framework_routing_precision(corpus, router_results):
    """When router fires for framework routes, it must pick a relevant framework."""
    correct = 0
    total = 0
    mismatches = []

    for tc, result in zip(corpus, router_results):
        if tc["category"] == "framework-single":
            total += 1
            expected_fw = tc["expected_route"].replace("framework:", "")
            if result.get("detail") == expected_fw:
                correct += 1
            elif result["type"] in ("single_framework", "multiple_frameworks"):
                # Routed to a framework, just not the exact expected one
                correct += 0.5
            else:
                mismatches.append({
                    "prompt": tc["prompt"][:80],
                    "expected": expected_fw,
                    "got": result.get("detail"),
                })

    precision = correct / total if total else 0
    assert precision >= 0.70, (
        f"Framework routing precision {precision:.1%} below 70% gate. "
        f"Mismatches: {json.dumps(mismatches, indent=2)}"
    )


def test_overall_routing_accuracy(corpus, router_results):
    """Overall accuracy across all categories."""
    correct = 0
    total = len(corpus)

    for tc, result in zip(corpus, router_results):
        expected = tc["expected_route"]
        if expected == "pass-through":
            if result["type"] == "pass-through":
                correct += 1
        elif expected.startswith("framework:multiple"):
            if result["type"] == "multiple_frameworks":
                correct += 1
        elif expected.startswith("framework:"):
            fw_id = expected.replace("framework:", "")
            if result["type"] == "single_framework" and result.get("detail") == fw_id:
                correct += 1
            elif result["type"] in ("single_framework", "multiple_frameworks"):
                # Partial credit: routed to a framework (may not be exact match)
                correct += 0.5
        elif expected.startswith("skill:"):
            skill_id = expected.replace("skill:", "")
            if result.get("detail") == skill_id:
                correct += 1

    accuracy = correct / total if total else 0
    # Report accuracy but don't fail — framework matching depends on generated index quality
    print(f"\nOverall routing accuracy: {accuracy:.1%} ({correct}/{total})")
```

**Step 2: Commit**

```bash
git add e2e/tests/test_router_accuracy.py
git commit -m "feat(router): add pytest accuracy tests for routing corpus"
```

---

### Task 9: Write the Node.js eval helper for tests

**Files:**
- Create: `e2e/tests/router-eval-helper.js`

**Step 1: Write the eval helper**

This script takes a JSON array of prompts as a CLI argument, runs each through the router matching logic (extracted from `hooks/skill-router.js`), and outputs results as JSON to stdout.

```javascript
#!/usr/bin/env node
// router-eval-helper.js — Runs router matching logic against a list of prompts.
// Usage: node router-eval-helper.js '["prompt1", "prompt2", ...]'
// SYNC REQUIRED: Matching logic duplicated from hooks/skill-router.js.
// Changes to matchFrameworks/matchSkills in either file must be mirrored.

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const INDEX_PATH = path.join(REPO_ROOT, 'skill-router.json');

const prompts = JSON.parse(process.argv[2]);
const index = JSON.parse(fs.readFileSync(INDEX_PATH, 'utf8'));

const results = prompts.map(prompt => {
  // Step 0: explicit invocation bypass
  if (/^\s*\/aligned:/.test(prompt)) {
    return { type: 'pass-through', detail: null };
  }

  const promptLower = prompt.toLowerCase();

  // Step 1: framework match
  const fwMatches = [];
  for (const fw of (index.frameworks || [])) {
    let score = 0;
    for (const trigger of (fw.triggers || [])) {
      if (promptLower.includes(trigger.toLowerCase())) score += 3;
    }
    for (const phrase of (fw.intent_phrases || [])) {
      if (promptLower.includes(phrase.toLowerCase())) score += 2;
    }
    if (score >= 3) fwMatches.push({ ...fw, score });
  }

  if (fwMatches.length > 0) {
    fwMatches.sort((a, b) => b.score - a.score);
    if (fwMatches.length === 1) {
      return { type: 'single_framework', detail: fwMatches[0].id };
    }
    return { type: 'multiple_frameworks', detail: fwMatches.slice(0, 3).map(m => m.id) };
  }

  // Step 2: skill classification
  for (const [skillId, config] of Object.entries(index.skills || {})) {
    const excluded = (config.exclude || []).some(ex => promptLower.includes(ex.toLowerCase()));
    if (excluded) continue;

    const matchedSignals = (config.signals || []).filter(sig =>
      promptLower.includes(sig.toLowerCase())
    );

    const minRequired = config.min_signals || 2;
    if (matchedSignals.length >= minRequired) {
      return { type: 'skill', detail: skillId };
    }

    if (matchedSignals.length === 1 && promptLower.split(/\s+/).length > 20) {
      return { type: 'skill', detail: skillId, relaxed: true };
    }
  }

  // Step 3: pass-through
  return { type: 'pass-through', detail: null };
});

console.log(JSON.stringify(results));
```

**Step 2: Verify it parses**

Run: `node -c e2e/tests/router-eval-helper.js`
Expected: No output (clean parse)

**Step 3: Commit**

```bash
git add e2e/tests/router-eval-helper.js
git commit -m "feat(router): add Node.js eval helper for test corpus evaluation"
```

---

### Task 10: Run the test corpus and verify precision gate

> **Depends on:** Tasks 1, 6, 7, 8, and 9 must be completed first — the eval helper reads `skill-router.json` which needs to be populated by the build script.

**Files:**
- No new files

**Step 1: Run the tests**

Run from the repo root: `python -m pytest e2e/tests/test_router_accuracy.py -v`

Expected: All tests pass. Key metrics to verify:
- `test_corpus_has_minimum_size`: 50+ test cases
- `test_explicit_invocations_pass_through`: All explicit invocations pass through
- `test_pass_through_cases_not_routed`: False positive rate ≤ 5%
- `test_skill_routing_precision`: Precision ≥ 80% (build gate)
- `test_framework_routing_precision`: Framework matches are correct
- Overall accuracy printout: target ≥ 90% for shipped state (informational, not gating)

> **Two thresholds:** The 80% precision gate is for the build phase (blocks shipping if below). The design doc's north-star success criterion is 90% match precision for the shipped product. If overall accuracy is between 80-90%, proceed but note it as a known gap to address via signal tuning.

**Step 2: If tests fail, diagnose and fix**

If false positive rate exceeds threshold: review which pass-through prompts were incorrectly routed and add exclusion patterns to `skill-router.json`.

If skill precision is below threshold: review signal patterns — they may be too broad or too narrow. Adjust signal lists in `skill-router.json`.

**Step 3: Commit any fixes**

```bash
git add skill-router.json
git commit -m "fix(router): tune signal patterns based on test corpus results"
```

---

### Task 11: Update hooks.json documentation in README.md

**Files:**
- Modify: `README.md` (the Hooks table, approximately the `### Hooks` section)

**Step 1: Add the skill-router hook to the Hooks table**

Find the `### Hooks` section in `README.md` and add a row for the new hook:

```markdown
| UserPromptSubmit | `skill-router.js` | Routes prompts to frameworks/skills via rule-based cascade |
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add skill-router hook to README hooks table"
```

---

### Task 12: Update plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json` (version bump)
- Modify: `.claude-plugin/marketplace.json` (version bump)

**Step 1: Bump version from 0.17.0 to 0.18.0**

In `.claude-plugin/plugin.json`, change `"version": "0.17.0"` to `"version": "0.18.0"`.

In `.claude-plugin/marketplace.json`, find the version field and update it to `"0.18.0"` as well.

**Step 2: Add changelog entry to README.md**

Find the `#### Changelog` section in `README.md` and add at the top:

```markdown
##### 0.18.0: Skill Auto-Router
- New `UserPromptSubmit` hook auto-routes natural language prompts to frameworks and skills
- Rule-based cascade: framework match → skill classification → pass-through
- Precomputed routing index (`skill-router.json`) with 138 framework entries and 4 skill signal sets
- Build script (`scripts/build-router-index.js`) regenerates index from framework content via LLM
- Telemetry logs routing decisions to `~/.claude/usage-tracking/router-decisions.jsonl`
- Test corpus with 50+ labeled prompts for accuracy measurement
```

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
git commit -m "chore: bump version to 0.18.0, add changelog for skill auto-router"
```

---

## Deferred: User Override ("Skip") Telemetry

Design doc Deliverable 5 specifies logging user override events (when users say "skip" after a routing suggestion). This requires observing user responses to the router's suggestion, which the current `UserPromptSubmit` hook architecture cannot do — the hook fires before Claude processes the message, not after the user responds. Implementing skip detection requires either:
1. A `PostToolUse` hook that watches for "skip" in the conversation after a routing directive was sent, or
2. A convention where Claude reports the override via a tool call that the `usage-tracker.js` hook can capture.

**This is deferred to a follow-up task** after the core routing is validated. The routing decision telemetry (what the router chose) ships in this plan; the override telemetry (whether the user accepted) requires a design decision about the detection mechanism.

## Note: `skill-router.json` as Distributed Artifact

The generated `skill-router.json` is committed to the repo and ships with the plugin. All users get the pre-built routing index — they do not need to run the build script. The build script (`scripts/build-router-index.js`) is a maintainer tool, run when frameworks are added or updated. This is intentional: the index must be available at hook runtime without requiring users to have an `ANTHROPIC_API_KEY`.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Matching logic duplication | Duplicate in hook + eval helper | Shared module import, single script |
| 2 | Test approach | Shell out to Node.js eval helper from pytest | Pure Node.js tests, pure Python reimplementation |
| 3 | Framework scoring threshold | Score ≥ 3 (one trigger or two intent phrases) | Score ≥ 2 (lower), Score ≥ 5 (higher) |
| 4 | Build script LLM model | claude-haiku-4-5 | claude-sonnet-4-6, manual curation |
| 5 | Telemetry file location | `~/.claude/usage-tracking/router-decisions.jsonl` | Same file as usage-tracker, separate directory |
| 6 | Relaxed skill match | 1 signal + 20+ word prompt | Strict min_signals only, no relaxed path |
| 7 | Hook output mechanism | `additionalContext` field in hookSpecificOutput | Direct prompt modification, separate system message |

### Appendix: Decision Details

#### Decision 1: Matching logic duplication
**Chose:** Duplicate matching logic in `hooks/skill-router.js` and `e2e/tests/router-eval-helper.js`
**Why:** The hook script must be self-contained — it runs via stdin/stdout with a 5-second timeout. Importing from it would require refactoring it into a module + wrapper, adding complexity for minimal benefit. The matching logic is ~40 lines and unlikely to diverge because changes to routing rules happen in `skill-router.json`, not in code.
**Alternatives rejected:**
- Shared module import: Adds a `require()` dependency chain to a hook that must be fast and self-contained. Would require restructuring the hook's stdin-based architecture.
- Single script for both: Testing via the hook's stdin/stdout interface is slow (process spawn per test case) and harder to debug.

#### Decision 2: Test approach
**Chose:** Python pytest shelling out to a Node.js eval helper
**Why:** The project already uses pytest for e2e tests (`e2e/tests/test_trigger_map_paths.py`, etc.). Keeping tests in the same framework reduces cognitive overhead. The eval helper batches all prompts in a single Node.js process call, so the performance cost of cross-language testing is minimal (one process spawn per test run, not per case).
**Alternatives rejected:**
- Pure Node.js tests: Would require adding a JS test framework (Jest, Vitest) when pytest is already established.
- Pure Python reimplementation: Would create a third copy of matching logic that could diverge from the Node.js implementation.

#### Decision 3: Framework scoring threshold
**Chose:** Score ≥ 3 (one trigger match = 3 points, or two intent phrase matches = 4 points)
**Why:** Triggers are high-confidence signals (framework names, author names), so one trigger should be sufficient. Intent phrases are medium-confidence and need at least two to reach threshold. This aligns with the design doc's precision-first principle.
**Alternatives rejected:**
- Score ≥ 2: Too permissive — a single intent phrase match would trigger routing, violating the precision-first principle.
- Score ≥ 5: Too strict — would require a trigger + intent phrase simultaneously, making framework routing rare.

#### Decision 4: Build script LLM model
**Chose:** claude-haiku-4-5 for intent phrase generation
**Why:** Intent phrase generation is a straightforward extraction task — Haiku is sufficient and significantly cheaper. The build script processes 138 frameworks in batches of 10, so 14 API calls. Haiku's cost makes this negligible even if run frequently.
**Alternatives rejected:**
- claude-sonnet-4-6: Overkill for structured extraction. Higher cost with marginal quality improvement.
- Manual curation: 138 frameworks is too many to curate manually. LLM-generated phrases provide a good starting point that can be manually refined based on test corpus results.

#### Decision 5: Telemetry file location
**Chose:** Separate file `router-decisions.jsonl` in the existing `~/.claude/usage-tracking/` directory
**Why:** Router decisions have different schema and volume than skill/agent usage events. Separate files make it easier to analyze routing patterns independently. Using the same directory follows the existing convention.
**Alternatives rejected:**
- Same file as usage-tracker: Different event schemas would complicate analysis.
- Separate directory: Unnecessary fragmentation when the existing directory already handles usage data.

#### Decision 6: Relaxed skill match
**Chose:** Allow 1 signal + 20+ word prompt to trigger routing
**Why:** The design doc specifies `min_signals: 2` as the base requirement, but also describes "one signal phrase plus a domain context signal (e.g., the prompt is longer than 20 words and contains problem-domain vocabulary)." Long prompts with a single signal are more likely to be genuine business/strategy requests than short technical questions. This captures the "CEO who writes paragraphs" user profile from the design doc.
**Alternatives rejected:**
- Strict min_signals only: Would miss legitimate use cases where the user describes a complex problem but only uses one signal phrase.
- No relaxed path: Simpler but leaves a gap in the routing for the primary persona.

#### Decision 7: Hook output mechanism
**Chose:** `additionalContext` field in `hookSpecificOutput`
**Why:** `UserPromptSubmit` hooks can append context that Claude sees but the user doesn't — matching the design doc's requirement for routing directives that are invisible to the user. The `additionalContext` field is the documented mechanism for this in Claude Code's hook architecture.
**Alternatives rejected:**
- Direct prompt modification: Not supported by the hook API — hooks can't rewrite the user's prompt.
- Separate system message: Not available in the hook output format.
