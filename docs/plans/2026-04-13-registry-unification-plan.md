# Registry Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Unify advisor and framework metadata into machine-readable YAML registries, update all consuming skill files, and generate derived reference artifacts (READMEs, searchable HTML catalogs).

**Source Design Doc:** `docs/plans/2026-04-13-registry-unification-design.md`

**Mockups:** `docs/mockups/registry-unification.html`

**Architecture:** Two centralized YAML registries (`advisors/registry.yaml`, `frameworks/registry.yaml`) replace the current markdown registry and filesystem-only discovery. Advisor migration is a deterministic format conversion from the existing `advisors/registry.md`. Framework registry is populated via a three-pass Node.js script (deterministic extraction from 138 `prompt.md` files, LLM classification for 3 fields, merge into draft for review). All 12 consumer skill files are updated to read YAML with glob-based fallback on parse failure. Derived artifacts (READMEs, HTML catalogs) are generated on-demand from the registries.

**Tech Stack:** YAML (registry format), Node.js ESM + `@anthropic-ai/sdk` (generation script — pattern borrowed from `.worktrees/skill-auto-router/scripts/build-router-index.js`, which is CJS; this plan uses ESM `.mjs` for clean `import` syntax), Python/pytest (schema validation tests in `e2e/tests/`), Tailwind CSS CDN (HTML catalogs)

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] Ensure Node.js v18+ is installed
- [ ] Ensure `ANTHROPIC_API_KEY` environment variable is set (needed for Task 4 — framework LLM classification)
- [ ] Install the Anthropic SDK at repo root: if `package.json` does not already exist, run `npm init -y`; then `npm install @anthropic-ai/sdk`

---

### ✅ Task 1: Write YAML Schema Validation Tests

**Files:**
- Create: `e2e/tests/test_registry_schemas.py`

**Step 1: Write the test file**

```python
# e2e/tests/test_registry_schemas.py

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ADVISOR_REQUIRED_FIELDS = {"id", "name", "summary", "prompt", "domains"}
FRAMEWORK_REQUIRED_FIELDS = {"id", "name", "advisor", "purpose", "category", "domains", "use_when"}


class TestAdvisorRegistrySchema:
    """Validates advisors/registry.yaml structure and required fields."""

    @pytest.fixture
    def registry(self):
        path = REPO_ROOT / "advisors" / "registry.yaml"
        assert path.exists(), f"Advisor registry not found at {path}"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data is not None, "Advisor registry is empty"
        return data

    def test_has_advisors_list(self, registry):
        assert "advisors" in registry, "Missing top-level 'advisors' key"
        assert isinstance(registry["advisors"], list), "'advisors' must be a list"
        assert len(registry["advisors"]) > 0, "Advisors list is empty"

    def test_has_selection_guidelines(self, registry):
        assert "selection_guidelines" in registry, "Missing 'selection_guidelines' key"

    def test_all_entries_have_required_fields(self, registry):
        for i, entry in enumerate(registry["advisors"]):
            missing = ADVISOR_REQUIRED_FIELDS - set(entry.keys())
            assert not missing, (
                f"Advisor entry {i} ({entry.get('id', 'unknown')}) "
                f"missing required fields: {missing}"
            )

    def test_domains_is_list(self, registry):
        for entry in registry["advisors"]:
            assert isinstance(entry["domains"], list), (
                f"Advisor {entry['id']}: 'domains' must be a list, "
                f"got {type(entry['domains']).__name__}"
            )

    def test_prompt_paths_exist(self, registry):
        for entry in registry["advisors"]:
            prompt_path = REPO_ROOT / entry["prompt"]
            assert prompt_path.exists(), (
                f"Advisor {entry['id']}: prompt file not found at {entry['prompt']}"
            )

    def test_ids_are_unique(self, registry):
        ids = [e["id"] for e in registry["advisors"]]
        dupes = [x for x in ids if ids.count(x) > 1]
        assert not dupes, f"Duplicate advisor IDs: {set(dupes)}"

    def test_entry_count_matches_prompts(self, registry):
        prompt_dir = REPO_ROOT / "advisors" / "prompts"
        prompt_files = list(prompt_dir.glob("*.md"))
        registry_count = len(registry["advisors"])
        file_count = len(prompt_files)
        assert registry_count == file_count, (
            f"Registry has {registry_count} entries but "
            f"advisors/prompts/ has {file_count} .md files"
        )


class TestFrameworkRegistrySchema:
    """Validates frameworks/registry.yaml structure and required fields."""

    @pytest.fixture
    def registry(self):
        path = REPO_ROOT / "frameworks" / "registry.yaml"
        assert path.exists(), f"Framework registry not found at {path}"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data is not None, "Framework registry is empty"
        return data

    def test_has_frameworks_list(self, registry):
        assert "frameworks" in registry, "Missing top-level 'frameworks' key"
        assert isinstance(registry["frameworks"], list), "'frameworks' must be a list"
        assert len(registry["frameworks"]) > 0, "Frameworks list is empty"

    def test_all_entries_have_required_fields(self, registry):
        for i, entry in enumerate(registry["frameworks"]):
            missing = FRAMEWORK_REQUIRED_FIELDS - set(entry.keys())
            assert not missing, (
                f"Framework entry {i} ({entry.get('id', 'unknown')}) "
                f"missing required fields: {missing}"
            )

    def test_domains_is_list(self, registry):
        for entry in registry["frameworks"]:
            assert isinstance(entry["domains"], list), (
                f"Framework {entry['id']}: 'domains' must be a list, "
                f"got {type(entry['domains']).__name__}"
            )

    def test_ids_are_unique(self, registry):
        ids = [e["id"] for e in registry["frameworks"]]
        dupes = [x for x in ids if ids.count(x) > 1]
        assert not dupes, f"Duplicate framework IDs: {set(dupes)}"

    def test_entry_count_matches_directories(self, registry):
        fw_dir = REPO_ROOT / "frameworks"
        fw_dirs = [
            d for d in fw_dir.iterdir()
            if d.is_dir() and (d / "prompt.md").exists()
        ]
        registry_count = len(registry["frameworks"])
        dir_count = len(fw_dirs)
        assert registry_count == dir_count, (
            f"Registry has {registry_count} entries but "
            f"frameworks/ has {dir_count} directories with prompt.md"
        )

    @pytest.mark.parametrize("slug,expected_name,expected_advisor", [
        ("landing-page-assembly", "Landing Page Assembly", "oli-gardner"),
        ("design-principles", "Design Principles", "steve-jobs"),
        ("do-things-that-dont-scale", "Do Things That Don't Scale", "paul-graham"),
        ("personal-context-intake", "Personal Context Intake", "wise-eric"),
        ("6-step-process", "6-Step Process", "gabor-mate"),
        ("earnestness-filter", "Earnestness Filter", "paul-graham"),
        ("enneagram-typing", "Enneagram Typing", "richard-schwartz"),
        ("focus-through-saying-no", "Focus Through Saying No", "steve-jobs"),
        ("professional-context-intake", "Professional Context Intake", "wise-eric"),
        ("quadrinity", "Quadrinity Process", "jim-dethmer"),
        ("the-story-so-far", "The Story So Far", "wise-eric"),
    ])
    def test_outlier_frameworks_have_correct_metadata(self, registry, slug, expected_name, expected_advisor):
        """Outlier frameworks (hardcoded in generation script) must have correct name and advisor."""
        entry = next((e for e in registry["frameworks"] if e["id"] == slug), None)
        assert entry is not None, f"Outlier framework {slug} not found in registry"
        assert entry["name"] == expected_name, (
            f"Framework {slug}: expected name '{expected_name}', got '{entry['name']}'"
        )
        assert entry["advisor"] == expected_advisor, (
            f"Framework {slug}: expected advisor '{expected_advisor}', got '{entry['advisor']}'"
        )
```

**Step 2: Run tests to verify they fail**

Run: `cd e2e && python -m pytest tests/test_registry_schemas.py -v`
Expected: FAIL — both registry YAML files do not exist yet.

**Step 3: Commit**

```bash
git add e2e/tests/test_registry_schemas.py
git commit -m "test: add YAML schema validation tests for advisor and framework registries"
```

---

### ✅ Task 2: Generate Advisor Registry YAML

**Files:**
- Create: `advisors/registry.yaml`

This is a deterministic conversion — no LLM needed. Read the existing `advisors/registry.md`, parse the Quick Reference table and detailed entries, and write structured YAML.

**Step 1: Read source files**

Read `advisors/registry.md` in full. The file has:
- Quick Reference table (the `| slug | name | domains | summary |` section)
- Selection Guidelines section (scope rules + calibration examples)
- Detailed entries for profiled advisors (sections under `## Real Human Advisors`, `## Synthetic Personas`, with fields: `id`, `prompt`, `domains`, `evaluation_expertise`, `best_for`, `not_for`)
- Unprofiled advisors have only a Quick Reference row (empty domains, no detailed entry)

**Step 2: Write `advisors/registry.yaml`**

Structure the YAML file with this exact schema:

```yaml
# Advisor Registry — source of truth for all advisor personas
# Skills and project runtimes derive their formats from this registry.

selection_guidelines:
  narrow_scope: "1-2 critics"
  typical_scope: "2-3 critics"
  complex_scope: "3-4 critics"
  rules:
    - "Hard-exclude any critic whose not_for matches the work's primary domain"
    - "Prefer diversity of lens — avoid overlapping domains"
    - "When in doubt, prefer fewer focused critics over more redundant ones"
  calibration_examples:
    - scope: "A single utility with no integrations"
      critics: [the-architect]
    - scope: "An API route with database writes and RLS"
      critics: [the-architect, the-security-reviewer]
    - scope: "A user-facing feature with backend + UI + auth"
      critics: [steve-jobs, the-architect, the-qa-engineer]
    - scope: "A product launch plan spanning positioning, UI, backend, integrations"
      critics: [april-dunford, steve-jobs, the-architect, the-security-reviewer]

advisors:
  # --- Fully profiled entries ---
  - id: steve-jobs
    name: Steve Jobs
    summary: "Co-founder of Apple who demanded insanely great products"
    prompt: advisors/prompts/steve-jobs.md
    domains: [product design, simplicity, UX, focus, user experience]
    evaluation_expertise: >
      Evaluates whether the work achieves simplicity and focus. Does every
      element earn its place? Is the experience intuitive without explanation?
      Catches complexity creep, feature bloat, and loss of focus.
    best_for: >
      Designs with user-facing components where simplicity and focus matter.
      Product vision decisions. Feature prioritization.
    not_for: >
      Pure infrastructure, backend plumbing, CI/CD pipelines, developer tooling,
      data migrations, test architecture.

  # --- Unprofiled entry (minimum viable) ---
  - id: brene-brown
    name: Brene Brown
    summary: "Research professor on courage, shame, and wholehearted leadership"
    prompt: advisors/prompts/brene-brown.md
    domains: []
    note: "Not yet profiled with evaluation expertise."
```

**Conversion rules:**
- Every row in the Quick Reference table becomes one entry in the `advisors` list
- `id` = slug column value
- `name` = name column value
- `summary` = summary column value
- `prompt` = `advisors/prompts/{slug}.md`
- `domains` = parse comma-separated domains column into a YAML list; empty column → `[]`
- For profiled advisors (those with a detailed `### Name` section below the table): add `evaluation_expertise`, `best_for`, `not_for` from the detailed entry
- For unprofiled advisors (no detailed section): omit optional fields, add `note: "Not yet profiled with evaluation expertise."`
- `selection_guidelines` section: copy from the "Selection Guidelines" section in registry.md, converting to the YAML structure shown above
- Sort entries alphabetically by `id`
- Total entries must equal 65 (matching current advisor count)

**Step 3: Validate the output**

Verify:
1. YAML parses without errors: `python -c "import yaml; yaml.safe_load(open('advisors/registry.yaml'))"`
2. Entry count is 65
3. All required fields present on every entry
4. All `prompt` paths point to existing files

**Step 4: Run schema validation test**

Run: `cd e2e && python -m pytest tests/test_registry_schemas.py::TestAdvisorRegistrySchema -v`
Expected: PASS (all advisor schema tests green)

**Step 5: Commit**

```bash
git add advisors/registry.yaml
git commit -m "feat: generate advisors/registry.yaml from registry.md"
```

---

### ✅ Task 3: Write Framework Registry Generation Script
> NOTE: Fixed regex bug in plan's script — original `[-–—.]` character class matched hyphens inside framework names (e.g., "5-Step" split at the hyphen). Replaced with two-pass approach: first try separator match (`\s+[-–—]\s+`), then fall back to period-terminated. 21 framework names are longer than ideal due to varied prompt formats — Task 4 LLM pass will clean these up.

**Files:**
- Create: `scripts/generate-framework-registry.mjs`

Model this script on the existing `scripts/build-router-index.js` in the `skill-auto-router` worktree. The script does a three-pass approach.

**Step 1: Write the generation script**

```javascript
#!/usr/bin/env node
// generate-framework-registry.mjs — Generates frameworks/registry.yaml from prompt.md files.
// Run: node scripts/generate-framework-registry.mjs [--pass1-only] [--dry-run]
// Requires: ANTHROPIC_API_KEY environment variable (for Pass 2 LLM classification)

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..');
const FRAMEWORKS_DIR = path.join(REPO_ROOT, 'frameworks');
const OUTPUT_PATH = path.join(REPO_ROOT, 'frameworks', 'registry.yaml');
const DRAFT_PATH = path.join(REPO_ROOT, 'frameworks', 'registry.draft.yaml');
const BATCH_SIZE = 10;

// 11 outlier frameworks that don't match the standard first-line format.
// This is a known, closed set — add-framework enforces the standard format for new entries.
const OUTLIER_MAP = {
  'landing-page-assembly': { name: 'Landing Page Assembly', advisor: 'oli-gardner' },
  'design-principles': { name: 'Design Principles', advisor: 'steve-jobs' },
  'do-things-that-dont-scale': { name: "Do Things That Don't Scale", advisor: 'paul-graham' },
  'earnestness-filter': { name: 'Earnestness Filter', advisor: 'paul-graham' },
  'enneagram-typing': { name: 'Enneagram Typing', advisor: 'richard-schwartz' },
  'focus-through-saying-no': { name: 'Focus Through Saying No', advisor: 'steve-jobs' },
  'personal-context-intake': { name: 'Personal Context Intake', advisor: 'wise-eric' },
  'professional-context-intake': { name: 'Professional Context Intake', advisor: 'wise-eric' },
  'quadrinity': { name: 'Quadrinity Process', advisor: 'jim-dethmer' },
  'the-story-so-far': { name: 'The Story So Far', advisor: 'wise-eric' },
  '6-step-process': { name: '6-Step Process', advisor: 'gabor-mate' },
};

// Starter categories to guide LLM classification (free-form, not enforced as enum)
const STARTER_CATEGORIES = [
  'positioning', 'startup', 'content-strategy', 'social-media', 'pricing',
  'growth', 'podcasting', 'negotiation', 'leadership', 'strategy',
  'psychology', 'health-autonomic', 'health-movement', 'health-fitness',
  'conversion', 'onboarding',
];

function parseFrontmatter(content) {
  const lines = content.split('\n');
  if (lines[0].trim() !== '---') return { frontmatter: {}, body: content };
  let endIdx = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === '---') { endIdx = i; break; }
  }
  if (endIdx === -1) return { frontmatter: {}, body: content };
  // Simple YAML-like frontmatter parsing
  const fm = {};
  const fmLines = lines.slice(1, endIdx).join('\n');
  const reqMatch = fmLines.match(/required_documents:\s*\n((?:\s+-\s+.+\n?)*)/);
  const helpMatch = fmLines.match(/helpful_documents:\s*\n((?:\s+-\s+.+\n?)*)/);
  const reqEmpty = fmLines.match(/required_documents:\s*\[\s*\]/);
  const helpEmpty = fmLines.match(/helpful_documents:\s*\[\s*\]/);

  if (reqMatch) {
    fm.required_documents = reqMatch[1].trim().split('\n').map(l => l.replace(/^\s*-\s*/, '').trim()).filter(Boolean);
  } else if (reqEmpty) {
    fm.required_documents = [];
  }
  if (helpMatch) {
    fm.helpful_documents = helpMatch[1].trim().split('\n').map(l => l.replace(/^\s*-\s*/, '').trim()).filter(Boolean);
  } else if (helpEmpty) {
    fm.helpful_documents = [];
  }

  const body = lines.slice(endIdx + 1).join('\n');
  return { frontmatter: fm, body };
}

function getFirstContentLine(content) {
  const { body } = parseFrontmatter(content);
  for (const line of body.split('\n')) {
    if (line.trim()) return line.trim();
  }
  return '';
}

// Pass 1: Deterministic extraction
function pass1() {
  const dirs = fs.readdirSync(FRAMEWORKS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name)
    .sort();

  const frameworks = [];
  for (const slug of dirs) {
    const promptPath = path.join(FRAMEWORKS_DIR, slug, 'prompt.md');
    if (!fs.existsSync(promptPath)) continue;

    const content = fs.readFileSync(promptPath, 'utf8');
    const { frontmatter } = parseFrontmatter(content);
    const firstLine = getFirstContentLine(content);

    let name, advisor, purpose;

    // Check outlier map first
    if (OUTLIER_MAP[slug]) {
      name = OUTLIER_MAP[slug].name;
      advisor = OUTLIER_MAP[slug].advisor;
      purpose = firstLine.substring(0, 200); // Use first line as fallback purpose
    } else {
      // Standard format: "You are {Advisor}, guiding someone through {Framework} - {purpose}."
      const match = firstLine.match(/^You are (.+?),\s*guiding someone through (.+?)\s*[-–—.]/);
      if (!match) {
        console.warn(`WARNING: ${slug} — first line doesn't match expected format, not in outlier map`);
        console.warn(`  First line: ${firstLine.substring(0, 100)}`);
        continue;
      }
      const advisorName = match[1].trim();
      name = match[2].trim();
      purpose = firstLine.replace(/^You are .+?,\s*guiding someone through .+?\s*[-–—]\s*/, '').replace(/\.$/, '').trim();

      // Derive advisor slug
      advisor = advisorName.toLowerCase()
        .replace(/^dr\.\s*/i, '')
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, '');
    }

    const entry = { id: slug, name, advisor, purpose };

    // Add frontmatter fields if present
    if (frontmatter.required_documents && frontmatter.required_documents.length > 0) {
      entry.required_documents = frontmatter.required_documents;
    }
    if (frontmatter.helpful_documents && frontmatter.helpful_documents.length > 0) {
      entry.helpful_documents = frontmatter.helpful_documents;
    }

    // Placeholder fields for Pass 2 (LLM classification)
    entry.category = 'NEEDS_CLASSIFICATION';
    entry.domains = [];
    entry.use_when = 'NEEDS_CLASSIFICATION';

    // Store content excerpt for Pass 2
    entry._content_excerpt = content.substring(0, 500);

    frameworks.push(entry);
  }

  console.log(`Pass 1: Extracted ${frameworks.length} frameworks deterministically`);
  return frameworks;
}

// Pass 2: LLM classification (category, domains, use_when)
async function pass2(frameworks) {
  const Anthropic = (await import('@anthropic-ai/sdk')).default;
  const client = new Anthropic();

  const enriched = [];
  for (let i = 0; i < frameworks.length; i += BATCH_SIZE) {
    const batch = frameworks.slice(i, i + BATCH_SIZE);
    const batchNum = Math.floor(i / BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(frameworks.length / BATCH_SIZE);
    console.log(`Pass 2: Processing batch ${batchNum}/${totalBatches}`);

    const batchInput = batch.map((fw, idx) => (
      `Framework ${idx + 1}: "${fw.name}" (id: ${fw.id})\n` +
      `Advisor: ${fw.advisor}\n` +
      `Purpose: ${fw.purpose}\n` +
      `Content excerpt: ${(fw._content_excerpt || '').substring(0, 300)}\n`
    )).join('\n---\n');

    const response = await client.messages.create({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 2000,
      messages: [{
        role: 'user',
        content: `For each framework below, classify:\n` +
          `1. "category" — one of: ${STARTER_CATEGORIES.join(', ')} (or suggest a new one if none fit)\n` +
          `2. "domains" — 2-5 freeform tags describing expertise areas\n` +
          `3. "use_when" — a natural language sentence describing WHEN to use this framework\n\n` +
          `Output valid JSON array. Each element: {"id": "...", "category": "...", "domains": [...], "use_when": "..."}\n` +
          `No markdown fencing. Just the JSON array.\n\n` +
          batchInput
      }]
    });

    try {
      const raw = response.content[0].text.trim();
      const text = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/, '');
      const results = JSON.parse(text);
      for (const result of results) {
        const fw = batch.find(f => f.id === result.id);
        if (fw) {
          fw.category = result.category || 'uncategorized';
          fw.domains = result.domains || [];
          fw.use_when = result.use_when || '';
          enriched.push(fw);
        }
      }
      // Add any batch entries not in results (LLM missed them)
      for (const fw of batch) {
        if (!enriched.find(e => e.id === fw.id)) {
          console.warn(`  WARNING: LLM missed framework ${fw.id}, using fallback`);
          fw.category = 'uncategorized';
          fw.domains = [];
          fw.use_when = '';
          enriched.push(fw);
        }
      }
    } catch (e) {
      console.error(`  Failed to parse LLM response for batch ${batchNum}: ${e.message}`);
      for (const fw of batch) {
        fw.category = 'uncategorized';
        fw.domains = [];
        fw.use_when = '';
        enriched.push(fw);
      }
    }
  }

  console.log(`Pass 2: Classified ${enriched.length} frameworks`);
  return enriched;
}

// Pass 3: Merge and write YAML
function pass3(frameworks, outputPath) {
  // Remove internal fields
  const cleaned = frameworks.map(fw => {
    const { _content_excerpt, ...rest } = fw;
    return rest;
  });

  // Sort by id
  cleaned.sort((a, b) => a.id.localeCompare(b.id));

  // Build YAML manually for readability
  let yaml = '# Framework Registry — source of truth for all decision frameworks\n';
  yaml += '# Skills use this for discovery, routing, and selection.\n\n';
  yaml += 'frameworks:\n';

  for (const fw of cleaned) {
    yaml += `  - id: ${fw.id}\n`;
    yaml += `    name: "${fw.name.replace(/"/g, '\\"')}"\n`;
    yaml += `    advisor: ${fw.advisor}\n`;
    yaml += `    purpose: "${fw.purpose.replace(/"/g, '\\"')}"\n`;
    yaml += `    category: ${fw.category}\n`;
    yaml += `    domains: [${fw.domains.map(d => `"${d}"`).join(', ')}]\n`;
    yaml += `    use_when: "${fw.use_when.replace(/"/g, '\\"')}"\n`;
    if (fw.required_documents && fw.required_documents.length > 0) {
      yaml += `    required_documents: [${fw.required_documents.map(d => `"${d}"`).join(', ')}]\n`;
    }
    if (fw.helpful_documents && fw.helpful_documents.length > 0) {
      yaml += `    helpful_documents: [${fw.helpful_documents.map(d => `"${d}"`).join(', ')}]\n`;
    }
    yaml += '\n';
  }

  fs.writeFileSync(outputPath, yaml);
  console.log(`Pass 3: Wrote ${cleaned.length} frameworks to ${outputPath}`);
}

// Main
const args = process.argv.slice(2);
const pass1Only = args.includes('--pass1-only');
const dryRun = args.includes('--dry-run');

const frameworks = pass1();

if (pass1Only) {
  console.log('\n--pass1-only: Skipping Pass 2 (LLM classification)');
  const outPath = dryRun ? DRAFT_PATH.replace('.yaml', '.pass1.yaml') : DRAFT_PATH;
  pass3(frameworks, outPath);
  process.exit(0);
}

pass2(frameworks).then(enriched => {
  const outPath = dryRun ? DRAFT_PATH : DRAFT_PATH;
  pass3(enriched, outPath);
  console.log(`\nDraft written to ${outPath}`);
  console.log('Review the draft, then rename to registry.yaml when satisfied.');
}).catch(e => {
  console.error(`Build failed: ${e.message}`);
  process.exit(1);
});
```

**Step 2: Run Pass 1 only to validate deterministic extraction**

Run: `node scripts/generate-framework-registry.mjs --pass1-only`
Expected output:
- `Pass 1: Extracted 138 frameworks deterministically`
- `Pass 3: Wrote 138 frameworks to frameworks/registry.draft.yaml`
- No `WARNING` lines for unexpected outliers

Also verify the `--dry-run` flag:
Run: `node scripts/generate-framework-registry.mjs --pass1-only --dry-run`
Expected: writes to `frameworks/registry.draft.pass1.yaml` instead of the standard draft path. Confirm the file exists.

**Step 3: Validate Pass 1 output**

Read `frameworks/registry.draft.yaml` (it exists after --pass1-only as `.draft.yaml`). Verify:
1. YAML parses without errors
2. 138 entries present
3. All entries have `id`, `name`, `advisor`, `purpose` fields populated
4. `category` is `NEEDS_CLASSIFICATION` and `domains` is `[]` (expected — Pass 2 hasn't run)
5. Outlier frameworks (`landing-page-assembly`, `design-principles`, etc.) have correct `name` and `advisor` values

**Step 4: Commit the script**

```bash
git add scripts/generate-framework-registry.mjs
git commit -m "feat: add framework registry generation script (Pass 1 deterministic extraction)"
```

---

### ✅ Task 4: Run LLM Classification and Finalize Framework Registry

**Files:**
- Create: `frameworks/registry.yaml` (renamed from draft)

**Step 1: Run full generation (Pass 1 + Pass 2 + Pass 3)**

Run: `node scripts/generate-framework-registry.mjs`
Expected:
- `Pass 1: Extracted 138 frameworks deterministically`
- 14 batch processing messages (`Pass 2: Processing batch N/14`)
- `Pass 2: Classified 138 frameworks`
- `Pass 3: Wrote 138 frameworks to frameworks/registry.draft.yaml`

If any batches fail (LLM parse errors), the script falls back to `uncategorized` for those entries. Re-run if more than 5 entries end up uncategorized.

**Step 2: Review the draft**

Read `frameworks/registry.draft.yaml`. Spot-check:
1. Categories are from the starter set (or sensible new ones)
2. Domains are relevant 2-5 tag lists
3. `use_when` phrases are natural language trigger sentences
4. No `NEEDS_CLASSIFICATION` values remain
5. `uncategorized` count is ≤ 5 (acceptable)

**Step 3: Rename draft to final**

```bash
mv frameworks/registry.draft.yaml frameworks/registry.yaml
```

Clean up any intermediate files (e.g., `registry.draft.pass1.yaml` if it exists).

**Step 4: Run schema validation tests**

Run: `cd e2e && python -m pytest tests/test_registry_schemas.py -v`
Expected: ALL PASS (both advisor and framework schema tests green)

**Step 5: Commit**

```bash
git add frameworks/registry.yaml
git commit -m "feat: generate frameworks/registry.yaml via three-pass batch processing"
```

---

### Task 5: Update Advisor-Facing Consumer Skills

**Files:**
- Modify: `skills/_shared/critique-panel-orchestration.md` (the `Read advisors/registry.md` line in the Round 1 section)
- Modify: `skills/use-advisor/SKILL.md` (Step 1a section)
- Modify: `skills/add-advisor/SKILL.md` (Step 8b section)

**Step 1: Update critique-panel-orchestration.md**

In `skills/_shared/critique-panel-orchestration.md`, find the line that says:

```
1. Read `advisors/registry.md`.
```

Replace with:

```
1. Read `advisors/registry.yaml`. Parse the `advisors` list — each entry has: `id`, `name`, `prompt`, `domains` (list), `evaluation_expertise`, `best_for`, `not_for`. Read the `selection_guidelines` section for count rules, hard-exclude logic, and diversity preferences. If the YAML file doesn't exist or fails to parse, fall back to globbing `advisors/prompts/*.md` and parsing first lines for name/domain extraction.
```

**Step 2: Update use-advisor/SKILL.md**

In `skills/use-advisor/SKILL.md`, replace the entire Step 1a section (starting with `**Step 1a: Read the Quick Reference table**` through the fallback sentence) with:

```markdown
**Step 1a: Read the advisor registry (`advisors/registry.yaml`)**

Read the file `advisors/registry.yaml` (plugin-relative). Parse the `advisors` list — each entry has `id`, `name`, `domains` (list), and `summary`. Use this as the primary listing source.

If `advisors/registry.yaml` does not exist or fails to parse, fall back to Step 1b.
```

**Step 3: Update add-advisor/SKILL.md**

In `skills/add-advisor/SKILL.md`, replace Step 8b entirely (the section starting with `### 8b. Update the Registry` through the `summary` field description) with:

```markdown
### 8b. Update the Registry

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
```

**Note:** Step 8c (count updates in `README.md`, `plugin.json`, `marketplace.json`) is unchanged — it has no dependency on the registry format and continues to work as-is.

**Step 4: Commit**

```bash
git add skills/_shared/critique-panel-orchestration.md skills/use-advisor/SKILL.md skills/add-advisor/SKILL.md
git commit -m "feat: update advisor-facing consumers to read YAML registry"
```

---

### Task 6: Update Framework-Facing Consumer Skills

**Files:**
- Modify: `skills/use-framework/SKILL.md` (Step 1a section)
- Modify: `skills/add-framework/SKILL.md` (Step 5 section)

**Step 1: Update use-framework/SKILL.md**

In `skills/use-framework/SKILL.md`, replace Step 1a entirely (the section starting with `**Step 1a: Glob frameworks from all locations**` through the "Context management" paragraph) with:

```markdown
**Step 1a: Discover frameworks from registry and filesystem**

**Primary source:** Read `frameworks/registry.yaml` (plugin-relative). Parse the `frameworks` list — each entry has `id`, `name`, `advisor`, `purpose`, `category`, `domains` (list), and `use_when`. Use this as the primary listing source.

**Fallback:** If `frameworks/registry.yaml` does not exist or fails to parse, glob `frameworks/*/prompt.md` from both plugin and project directories (deduplicate by slug, project-local wins). This also discovers project-local frameworks not in the plugin registry.

**Merge:** If both the registry and project-local glob return results, merge them. Registry entries are the canonical source for plugin frameworks. Project-local frameworks (found via glob but not in registry) are appended to the list.

**Context management:** When listing all frameworks, use registry metadata (name, advisor, purpose) directly. Do not read full `prompt.md` contents during discovery — full reads happen only after matching.
```

**Step 2: Update add-framework/SKILL.md**

In `skills/add-framework/SKILL.md`, replace Step 5 entirely (the section starting with `### 5. Add Registry Entry` through the fallback format description) with:

```markdown
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
```

> **Behavior change:** Step 5 previously wrote to a project-local registry in an arbitrary format (detected at runtime). It now writes specifically to the plugin's own `frameworks/registry.yaml`. Project-local registries are unaffected — this step's conditional guard (`Only run if frameworks/registry.yaml exists in the plugin directory`) ensures it only fires for the plugin registry.

**Step 3: Commit**

```bash
git add skills/use-framework/SKILL.md skills/add-framework/SKILL.md
git commit -m "feat: update framework-facing consumers to read YAML registry"
```

---

### Task 7: Update Batch B Consumer Files

**Files:**
- Modify: `skills/brainstorming/critic-registry.md` (entire content)
- Modify: `skills/find-potential-advisors/SKILL.md` (the Differentiation Check step — this is a functional consumer of the advisor registry, not just a documentation reference; treat edits with the same care as Task 5 consumer updates)
- Modify: `README.md` (documentation references to registry)
- Modify: `skills/kickstart/SKILL.md` (documentation references, fix outdated count)
- Modify: `docs/mockups/plugin-split.html` (architecture diagram references)

**Step 1: Update critic-registry.md**

Replace the entire content of `skills/brainstorming/critic-registry.md` with:

```
Critic selection uses `advisors/registry.yaml`. See that file for per-advisor domain metadata, selection guidelines, and diversity rules.
```

**Step 2: Update find-potential-advisors/SKILL.md**

In `skills/find-potential-advisors/SKILL.md`, find the Differentiation Check step text:

```
Read the project's CLAUDE.md or advisor registry to check for existing advisors in this domain
```

Replace with:

```
Read the project's CLAUDE.md or advisor registry to check for existing advisors in this domain. Resolve the registry by checking for `registry.yaml` first, then `registry.md`, then globbing `advisors/prompts/*.md`.
```

**Note:** Keep generic wording per design decision D10 — `find-potential-advisors` is a portable skill that should not hardcode a specific registry path. The resolution order is an additional hint, not a hardcoded dependency.

**Step 3: Update README.md**

In `README.md`, find any references to `advisors/registry.md` and update them to `advisors/registry.yaml`. The README should reference the YAML registry as the source of truth. If the README references "Quick Reference table," update to reference "the advisors list in `advisors/registry.yaml`."

**Step 4: Update kickstart/SKILL.md**

In `skills/kickstart/SKILL.md`:
1. Find the outdated advisor count (e.g., "62 advisors") and update to match the current count (65).
2. Find any references to `advisors/registry.md` and update to `advisors/registry.yaml`.

**Step 5: Update plugin-split.html**

In `docs/mockups/plugin-split.html`, find references to `registry.md` in architecture diagram nodes. Update to `registry.yaml`. Use Grep to find all occurrences first, then update each one.

**Step 6: Commit**

```bash
git add skills/brainstorming/critic-registry.md skills/find-potential-advisors/SKILL.md README.md skills/kickstart/SKILL.md docs/mockups/plugin-split.html
git commit -m "feat: update Batch B consumer files to reference YAML registries"
```

---

### Task 8: Verify Migration Completeness and Delete Old Registry

**Files:**
- Delete: `advisors/registry.md`

**Step 1: Grep for stale references**

Run: Grep for `registry.md` across all skill files.

Pattern: `registry\.md`
Path: `skills/`
Glob: `**/*.md`

Expected: **Zero matches.** If any matches remain, fix them before proceeding.

Also check:
- `README.md` — zero matches for `registry.md` (except in changelog/history sections if present)
- `.claude-plugin/` files — zero matches

**Intentionally excluded from this grep check** (per design doc Section 2 "Not changed"):
- `e2e/eval-surface.yaml` — references `frameworks/*/prompt.md` globs, not `registry.md`; no change needed
- `docs/plans/2026-04-08-plugin-split-design.md` and `docs/plans/2026-04-08-plugin-split-plan.md` — historical plan documents with dated path references

**Step 2: Verify registry entry counts match**

1. Count entries in `advisors/registry.yaml`: should be 65
2. Count entries in `frameworks/registry.yaml`: should be 138
3. Count files in `advisors/prompts/`: should be 65
4. Count directories in `frameworks/` with `prompt.md`: should be 138

All four numbers must match their pairs.

**Step 3: Delete old registry file**

```bash
git rm advisors/registry.md
git commit -m "chore: remove advisors/registry.md (replaced by registry.yaml)"
```

This is a separate commit for revert safety — if something breaks, this single commit can be reverted to restore the markdown registry while keeping all other changes.

---

### Task 9: Generate Advisors README

**Files:**
- Create: `advisors/README.md`

**Step 1: Read the registry**

Read `advisors/registry.yaml` in full. Count total advisors, count profiled (those with `evaluation_expertise` field), count unprofiled.

**Step 2: Generate README**

Write `advisors/README.md` with this structure:
- Title: `# Advisor Registry`
- Counts: total, profiled, unprofiled
- Quick reference table: `| ID | Name | Domains | Summary |` — one row per advisor, sorted alphabetically by ID
- Profiled advisors section: for each advisor with `evaluation_expertise`, show name + one-line expertise summary
- Unprofiled advisors section: list of names that need profiling
- Selection guidelines summary (from registry `selection_guidelines`)
- Footer noting this file is auto-generated from `advisors/registry.yaml`

**Step 3: Commit**

```bash
git add advisors/README.md
git commit -m "docs: generate advisors/README.md from YAML registry"
```

---

### Task 10: Generate Frameworks README

**Files:**
- Create: `frameworks/README.md`

**Step 1: Read the registry**

Read `frameworks/registry.yaml` in full. Count total frameworks, count per category.

**Step 2: Generate README**

Write `frameworks/README.md` with this structure:
- Title: `# Framework Registry`
- Total count + count per category
- Quick reference table: `| ID | Name | Advisor | Category | Use When |` — sorted alphabetically by ID
- Grouped sections by category: each category gets a heading with its frameworks listed
- Footer noting this file is auto-generated from `frameworks/registry.yaml`

**Step 3: Commit**

```bash
git add frameworks/README.md
git commit -m "docs: generate frameworks/README.md from YAML registry"
```

---

### Task 11: Generate Advisor Catalog HTML

**Files:**
- Create: `docs/advisor-catalog.html`

**Step 1: Read the mockup for design reference**

Read `docs/mockups/registry-unification.html` to understand the visual design. Also read an existing HTML file for Tailwind config conventions: `docs/skill-orchestration.html` (if it exists) or any `docs/mockups/*.html` file.

**Step 2: Read the registry**

Read `advisors/registry.yaml` in full.

**Step 3: Generate the HTML catalog**

Write `docs/advisor-catalog.html` as a self-contained HTML file with:
- Tailwind CSS CDN with project design tokens (accent `#ff6900`, surface `#f5f3ef`)
- Search box that filters by name, domain, and summary (real-time filtering via JavaScript)
- Card layout showing each advisor: name, domains as tags, summary
- Expandable details on click: `evaluation_expertise`, `best_for`, `not_for` (for profiled advisors)
- Profiled/unprofiled visual distinction (e.g., badge or muted styling for unprofiled)
- Selection guidelines sidebar or section
- Cross-links to frameworks: for each advisor, list their frameworks (requires reading `frameworks/registry.yaml` for advisor cross-reference)
- Responsive design (mobile-friendly)
- Footer noting auto-generated from `advisors/registry.yaml`

**Step 4: Open in browser and verify**

Open `docs/advisor-catalog.html` in a browser. Verify:
1. All 65 advisors display
2. Search filters work (type "positioning" → shows April Dunford and others with positioning domain)
3. Expandable details open/close correctly
4. Responsive at mobile widths
5. Cross-links to frameworks are accurate

**Step 5: Commit**

```bash
git add docs/advisor-catalog.html
git commit -m "feat: generate searchable advisor catalog HTML"
```

---

### Task 12: Generate Framework Catalog HTML

**Files:**
- Create: `docs/framework-catalog.html`

**Step 1: Read the mockup and registry**

Read `docs/mockups/registry-unification.html` for design reference. Read `frameworks/registry.yaml` in full.

**Step 2: Generate the HTML catalog**

Write `docs/framework-catalog.html` as a self-contained HTML file with:
- Tailwind CSS CDN with project design tokens (accent `#ff6900`, surface `#f5f3ef`)
- Search box that filters by name, advisor, category, domain, and use_when
- Category grouping with counts (collapsible sections)
- Card or table layout showing each framework: name, advisor, category, use_when
- Expandable details on click: domains, required_documents, helpful_documents
- Cross-links to advisor: each framework links to its advisor's entry in the advisor catalog
- Responsive design
- Footer noting auto-generated from `frameworks/registry.yaml`

**Step 3: Open in browser and verify**

Open `docs/framework-catalog.html` in a browser. Verify:
1. All 138 frameworks display
2. Category grouping shows correct counts
3. Search filters work across all fields
4. Expandable details open/close correctly
5. Responsive at mobile widths

**Step 4: Commit**

```bash
git add docs/framework-catalog.html
git commit -m "feat: generate searchable framework catalog HTML"
```

---

### Task 13: Update E2E Trigger Map

**Files:**
- Modify: `e2e/trigger-map.yaml` (add registry file trigger entries)

**Step 1: Add registry trigger entries**

Append as new list items inside the `triggers:` key of `e2e/trigger-map.yaml` (not at the end of the file — they must be indented under `triggers:`):

```yaml
  - paths:
      - advisors/registry.yaml
    scenarios:
      - scenarios/persona-panel/pricing-page.yaml
      - scenarios/use-advisor/april-dunford-blog-critique.yaml

  - paths:
      - frameworks/registry.yaml
    scenarios:
      - scenarios/use-framework/5-components-positioning.yaml
```

Rationale: Changes to registry files can affect advisor selection (critique panel) and framework discovery (use-advisor, use-framework). Map to existing eval scenarios that exercise these paths.

**Step 2: Run all e2e tests**

Run: `cd e2e && python -m pytest tests/ -v`
Expected: ALL PASS (schema tests + existing tests)

**Step 3: Commit**

```bash
git add e2e/trigger-map.yaml
git commit -m "test: add registry YAML files to e2e trigger map"
```

---

### Task 14: Bump Plugin Version

**Files:**
- Modify: `.claude-plugin/plugin.json` (the `version` field)
- Modify: `.claude-plugin/marketplace.json` (the `version` field)

**Step 1: Read current version**

Read `.claude-plugin/plugin.json`. Current version is `0.17.0`.

**Step 2: Bump minor version**

This is a feature release (new registry format, updated consumers, new derived artifacts). Bump to `0.18.0`.

Update in both files:
- `.claude-plugin/plugin.json`: `"version": "0.18.0"`
- `.claude-plugin/marketplace.json`: `"version": "0.18.0"`

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version to 0.18.0 for registry unification"
```

---

## Manual Steps (Post-Automation)

> Complete these steps after all tasks finish.

- [ ] Review `frameworks/registry.yaml` LLM-classified fields (`category`, `domains`, `use_when`) for quality — spot-check 10-15 entries across categories
- [ ] Open `docs/advisor-catalog.html` and `docs/framework-catalog.html` in a browser for visual QA
- [ ] Run one `use-advisor` and one `use-framework` invocation to verify YAML reading works end-to-end
- [ ] Run one `add-advisor` (test entry) to verify YAML append + post-append validation works, then revert
- [ ] If satisfied, delete `scripts/generate-framework-registry.mjs` (one-off migration script) or keep for future re-generation

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Advisor conversion approach | Direct LLM-based conversion (read MD, write YAML) | Node.js script, Python script |
| 2 | Framework generation script language | Node.js (ESM) | Python, direct LLM conversion |
| 3 | Test framework for schema validation | Python/pytest (in existing `e2e/tests/`) | Node.js test, shell script validation |
| 4 | Consumer update commit strategy | Group by dependency (advisor-facing, framework-facing, batch B) | One commit per file, one mega-commit |
| 5 | Old registry deletion timing | Separate commit after all consumers verified | Same commit as last consumer update |
| 6 | HTML catalog generation approach | Single-task per catalog | Combined task, template-based generation |

### Appendix: Decision Details

#### Decision 1: Advisor conversion approach
**Chose:** Direct LLM-based conversion — the executor reads `advisors/registry.md` and writes `advisors/registry.yaml` directly without an intermediary script.
**Why:** The advisor registry has 65 entries and the conversion is fully deterministic (no LLM classification needed). A script adds complexity for a one-time operation that fits comfortably in a single context window. The markdown structure is well-defined (Quick Reference table + detailed entry sections), making direct parsing straightforward.
**Alternatives rejected:**
- Node.js script: Over-engineering for 65 deterministic entries. Would need to be written, tested, run, and deleted.
- Python script: Same over-engineering concern, plus would add a dependency not currently at repo root.

#### Decision 2: Framework generation script language
**Chose:** Node.js (ESM) modeled on existing `scripts/build-router-index.js` in the `skill-auto-router` worktree.
**Why:** The framework registry requires LLM classification for 3 fields across 138 entries, making a script appropriate. Node.js with the `@anthropic-ai/sdk` is the established pattern in this repo — `build-router-index.js` already implements batched LLM calls at this exact scale (138 frameworks, batches of 10). Using the same language and patterns reduces cognitive overhead for maintenance. The ESM format (`.mjs`) is used for clean `import` syntax without additional bundler config.
**Alternatives rejected:**
- Python: Would work but isn't the established pattern. The `e2e/` directory uses Python for tests, but generation scripts use Node.js.
- Direct LLM conversion: 138 entries with 500-char content excerpts would overwhelm a single context window, and batched API calls are more reliable.

#### Decision 3: Test framework for schema validation
**Chose:** Python/pytest in the existing `e2e/tests/` directory.
**Why:** The `e2e/tests/` directory already has pytest infrastructure (`conftest.py`, `package.json` with `"test": "pytest tests/ -v"`). Adding schema validation tests here keeps all structural validation in one place. The existing `test_trigger_map_paths.py` and `test_eval_surface_patterns.py` demonstrate the same pattern — verifying file structure and metadata correctness.
**Alternatives rejected:**
- Node.js test: Would need a separate test runner setup at repo root.
- Shell script: Fragile YAML parsing, hard to maintain assertion logic.

#### Decision 4: Consumer update commit strategy
**Chose:** Three commits: advisor-facing consumers (critique-panel + use-advisor + add-advisor), framework-facing consumers (use-framework + add-framework), Batch B reference files (5 documentation/peripheral files).
**Why:** Groups by logical dependency while keeping commits reviewable. Advisor-facing consumers depend only on `advisors/registry.yaml` (Task 2). Framework-facing consumers depend only on `frameworks/registry.yaml` (Task 4). Batch B files are independent reference updates. This grouping means any commit can be reverted without breaking the others, and bisection is meaningful.
**Alternatives rejected:**
- One commit per file: 10 commits for simple edits is excessive granularity.
- One mega-commit: Harder to review, risky to revert.

#### Decision 5: Old registry deletion timing
**Chose:** Separate commit after all consumer updates are verified and grep confirms zero stale references.
**Why:** The design doc explicitly calls for this: "Separate commit for revert safety and worktree compatibility." If something breaks post-migration, reverting the deletion commit instantly restores the old registry without touching any consumer updates. This is especially important because two feature worktrees exist (`plugin-split-plan`, `skill-auto-router`) that may reference `registry.md`.
**Alternatives rejected:**
- Same commit as last consumer update: Loses the clean revert boundary.

#### Decision 6: HTML catalog generation approach
**Chose:** One task per catalog (advisor catalog = Task 11, framework catalog = Task 12).
**Why:** Each catalog is a substantial self-contained HTML file (~500+ lines) with search, filtering, expandable details, cross-links, and responsive design. Combining them into one task would exceed the 15-minute guideline and increase context window pressure. Separate tasks also allow the advisor catalog to be committed and verified before building the framework catalog (which cross-references it).
**Alternatives rejected:**
- Combined task: Too large for one Ralph loop invocation.
- Template-based generation: Would require building a template engine first — YAGNI for two files.
