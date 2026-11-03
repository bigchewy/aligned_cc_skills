#!/usr/bin/env node
// generate-framework-registry.mjs — Generates frameworks/registry.draft.yaml from prompt.md files.
// Run: node scripts/generate-framework-registry.mjs [--pass1-only]
// Output is always a draft — review, then rename to registry.yaml.
// Requires: ANTHROPIC_API_KEY environment variable (for Pass 2 LLM classification)
// Document lists are written as {doc, from}. `from` is carried over from the current
// frameworks/registry.yaml when the framework id and the document name both match; otherwise `outside`.
// `stages` and `market` are carried over from the current registry by framework id.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..');
const FRAMEWORKS_DIR = path.join(REPO_ROOT, 'frameworks');
const REGISTRY_PATH = path.join(REPO_ROOT, 'frameworks', 'registry.yaml');
const DRAFT_PATH = path.join(REPO_ROOT, 'frameworks', 'registry.draft.yaml');
const PASS1_DRAFT_PATH = path.join(REPO_ROOT, 'frameworks', 'registry.draft.pass1.yaml');
const BATCH_SIZE = 10;

// Outlier frameworks that don't match the standard first-line format.
// Shared source of truth: frameworks/_outliers.json (also read by e2e/tests/test_registry_schemas.py).
// add-framework enforces the standard format for new entries, so this is a known closed set.
const OUTLIER_MAP = JSON.parse(
  fs.readFileSync(path.join(REPO_ROOT, 'frameworks', '_outliers.json'), 'utf8')
).outliers;

// A frontmatter name may be wrapped in single or double quotes. Return it without them.
function stripQuotes(s) {
  const m = s.match(/^(['"])(.*)\1$/);
  return m ? m[2] : s;
}

export function parseFrontmatter(content) {
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
    fm.required_documents = reqMatch[1].trim().split('\n').map(l => stripQuotes(l.replace(/^\s*-\s*/, '').trim())).filter(Boolean);
  } else if (reqEmpty) {
    fm.required_documents = [];
  }
  if (helpMatch) {
    fm.helpful_documents = helpMatch[1].trim().split('\n').map(l => stripQuotes(l.replace(/^\s*-\s*/, '').trim())).filter(Boolean);
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

      if (!purpose) {
        console.warn(`WARNING: ${slug} — first line uses period-terminated form; purpose will be empty. Use " — purpose" form in prompt.md first line.`);
      }
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
    entry.domains = [];
    entry.use_when = 'NEEDS_CLASSIFICATION';

    // Store content excerpt for Pass 2
    entry._content_excerpt = content.substring(0, 500);

    frameworks.push(entry);
  }

  console.log(`Pass 1: Extracted ${frameworks.length} frameworks deterministically`);
  return frameworks;
}

// Pass 2: LLM classification (domains, use_when)
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
          `1. "domains" — 2-5 freeform tags describing expertise areas\n` +
          `2. "use_when" — a natural language sentence describing WHEN to use this framework\n\n` +
          `Output valid JSON array. Each element: {"id": "...", "domains": [...], "use_when": "..."}\n` +
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
          fw.domains = result.domains || [];
          fw.use_when = result.use_when || '';
          enriched.push(fw);
        }
      }
      // Add any batch entries not in results (LLM missed them)
      for (const fw of batch) {
        if (!enriched.find(e => e.id === fw.id)) {
          console.warn(`  WARNING: LLM missed framework ${fw.id}, using fallback`);
          fw.domains = [];
          fw.use_when = '';
          enriched.push(fw);
        }
      }
    } catch (e) {
      console.error(`  Failed to parse LLM response for batch ${batchNum}: ${e.message}`);
      for (const fw of batch) {
        fw.domains = [];
        fw.use_when = '';
        enriched.push(fw);
      }
    }
  }

  console.log(`Pass 2: Classified ${enriched.length} frameworks`);
  return enriched;
}

// Read a registry.yaml (or a draft this script wrote) into one record per framework:
// {id, froms: [{key, doc, from}], stages, market}. It reads two layouts: the registry's
// (entries start `- `, keys indented two, lists at the key's indent) and the script's own
// (entries start `  - id:`, keys indented four, list items two deeper than their key).
// `from` is an id, a list of ids, or 'outside'.
function parseRegistry(text) {
  const unquote = s => {
    s = s.trim();
    if (s.length >= 2 && s.startsWith("'") && s.endsWith("'")) return s.slice(1, -1).replace(/''/g, "'");
    if (s.length >= 2 && s.startsWith('"') && s.endsWith('"')) {
      try { return JSON.parse(s); } catch (e) { return s.slice(1, -1); }
    }
    return s;
  };
  const inlineList = v => v.slice(1, -1).split(',').map(s => unquote(s)).filter(Boolean);

  const readEntry = lines => {
    if (lines.length === 0) return null;
    const keyIndent = lines[0].startsWith('- ') ? 2 : 4;
    const rec = { id: null, docs: [], stages: null, market: null };
    let section = null;
    let cur = null;
    let curListKey = null;
    const finish = () => {
      if (cur) rec.docs.push({ key: curListKey, doc: unquote(cur.doc), from: cur.from === null ? 'outside' : cur.from });
      cur = null;
    };
    lines.forEach((line, i) => {
      const km = line.match(/^(\s*)(- )?([A-Za-z_]+):\s?(.*)$/);
      const isKey = km && (i === 0 ? Boolean(km[2]) : !km[2] && km[1].length === keyIndent);
      if (isKey) {
        finish();
        section = null;
        const [, , , key, rawValue] = km;
        const value = rawValue.trim();
        if (key === 'id') rec.id = unquote(value);
        else if (key === 'market') rec.market = unquote(value);
        else if (key === 'stages') {
          rec.stages = value.startsWith('[') && value.endsWith(']') ? inlineList(value) : [];
          if (!value) section = 'stages';
        } else if (key === 'required_documents' || key === 'helpful_documents') {
          section = 'docs';
          curListKey = key;
        }
        return;
      }
      let m;
      if (section === 'stages' && (m = line.match(/^\s*- (.+)$/))) {
        rec.stages.push(unquote(m[1]));
      } else if (section === 'docs' && (m = line.match(/^(\s*)- doc:\s?(.*)$/))) {
        finish();
        cur = { doc: m[2], from: null, listing: false, dash: m[1].length };
      } else if (section === 'docs' && cur && (m = line.match(/^\s+from:\s?(.*)$/))) {
        const v = m[1].trim();
        if (!v) {
          cur.from = [];
          cur.listing = true;
        } else if (v.startsWith('[') && v.endsWith(']')) {
          cur.from = inlineList(v);
        } else {
          cur.from = unquote(v);
        }
      } else if (section === 'docs' && cur && cur.listing && (m = line.match(/^\s*- (.+)$/))) {
        cur.from.push(unquote(m[1]));
      } else if (section === 'docs' && cur && cur.from === null && line.search(/\S/) >= cur.dash + 4) {
        cur.doc += ' ' + line.trim();
      }
    });
    finish();
    return rec.id ? rec : null;
  };

  const records = [];
  let entry = [];
  for (const line of text.split('\n')) {
    if (line.startsWith('- ') || /^  - id:/.test(line)) {
      const rec = readEntry(entry);
      if (rec) records.push(rec);
      entry = [];
    }
    entry.push(line);
  }
  const last = readEntry(entry);
  if (last) records.push(last);
  return records;
}

// Map of `${id}\u0000${doc}` -> `from` for every document in a registry or draft.
export function loadExistingFroms(text) {
  const froms = new Map();
  for (const rec of parseRegistry(text)) {
    for (const d of rec.docs) froms.set(`${rec.id}\u0000${d.doc}`, d.from);
  }
  return froms;
}

// Map of id -> {stages?, market?} for every framework that has either field.
export function loadExistingMeta(text) {
  const meta = new Map();
  for (const rec of parseRegistry(text)) {
    const m = {};
    if (rec.market) m.market = rec.market;
    if (rec.stages && rec.stages.length > 0) m.stages = rec.stages;
    if (Object.keys(m).length > 0) meta.set(rec.id, m);
  }
  return meta;
}

// `market` and `stages` for one framework as registry YAML, or '' when it has neither.
export function metaYaml(id, meta) {
  const m = meta.get(id);
  if (!m) return '';
  let out = '';
  if (m.market) out += `    market: ${m.market}\n`;
  if (m.stages) out += `    stages:\n${m.stages.map(s => `      - ${s}\n`).join('')}`;
  return out;
}

// One document list as registry YAML: [{doc, from}], four-space key, six-space items.
export function documentsYaml(key, docs, id, froms) {
  let out = `    ${key}:\n`;
  for (const d of docs) {
    const from = froms.get(`${id}\u0000${d}`) ?? 'outside';
    out += `      - doc: ${JSON.stringify(d)}\n`;
    out += Array.isArray(from) ? `        from: [${from.join(', ')}]\n` : `        from: ${from}\n`;
  }
  return out;
}

// Pass 3: Merge and write YAML
function pass3(frameworks, outputPath) {
  const existing = fs.existsSync(REGISTRY_PATH) ? fs.readFileSync(REGISTRY_PATH, 'utf8') : '';
  const froms = loadExistingFroms(existing);
  const meta = loadExistingMeta(existing);

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
    yaml += `    domains: [${fw.domains.map(d => `"${d}"`).join(', ')}]\n`;
    yaml += `    use_when: "${fw.use_when.replace(/"/g, '\\"')}"\n`;
    yaml += metaYaml(fw.id, meta);
    if (fw.required_documents && fw.required_documents.length > 0) {
      yaml += documentsYaml('required_documents', fw.required_documents, fw.id, froms);
    }
    if (fw.helpful_documents && fw.helpful_documents.length > 0) {
      yaml += documentsYaml('helpful_documents', fw.helpful_documents, fw.id, froms);
    }
    yaml += '\n';
  }

  fs.writeFileSync(outputPath, yaml);
  console.log(`Pass 3: Wrote ${cleaned.length} frameworks to ${outputPath}`);
}

// Main (skipped when another file imports this one, as the tests do)
function main() {
  const args = process.argv.slice(2);
  const pass1Only = args.includes('--pass1-only');

  const frameworks = pass1();

  if (pass1Only) {
    console.log('\n--pass1-only: Skipping Pass 2 (LLM classification)');
    pass3(frameworks, PASS1_DRAFT_PATH);
    process.exit(0);
  }

  pass2(frameworks).then(enriched => {
    pass3(enriched, DRAFT_PATH);
    console.log(`\nDraft written to ${DRAFT_PATH}`);
    console.log('Review the draft, then rename to registry.yaml when satisfied.');
  }).catch(e => {
    console.error(`Build failed: ${e.message}`);
    process.exit(1);
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
