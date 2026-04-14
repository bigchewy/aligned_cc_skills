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
      // Try separator match first (" - ", " – ", " — "), then fall back to period-terminated.
      const sepMatch = firstLine.match(/^You are (.+?),\s*guiding someone through (.+?)\s+[-–—]\s+(.+)/);
      const dotMatch = !sepMatch && firstLine.match(/^You are (.+?),\s*guiding someone through (.+?)\./);
      const match = sepMatch || dotMatch;
      if (!match) {
        console.warn(`WARNING: ${slug} — first line doesn't match expected format, not in outlier map`);
        console.warn(`  First line: ${firstLine.substring(0, 100)}`);
        continue;
      }
      const advisorName = match[1].trim();
      name = match[2].trim();
      purpose = sepMatch ? match[3].replace(/\.$/, '').trim() : '';

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
