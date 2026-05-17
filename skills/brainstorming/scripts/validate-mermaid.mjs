#!/usr/bin/env node
// Validates every <pre class="mermaid"|"mermaid-deferred"> block in an HTML file
// by parsing it with mermaid (matching the CDN version the templates load).
//
// Usage:  node validate-mermaid.mjs <path-to-html>
// First-use setup: npm install (inside this directory)
//
// Exits 0 if every block parses. Exits 1 with a tight per-block summary if any
// block fails: file, block index (0-based), the snippet of source mermaid sees
// (after HTML-entity decode and br-tag elision, matching browser textContent),
// and the parser's caret-pointer error.

import fs from 'node:fs';
import path from 'node:path';

const htmlPath = process.argv[2];
if (!htmlPath) {
  console.error('usage: node validate-mermaid.mjs <path-to-html>');
  process.exit(2);
}
if (!fs.existsSync(htmlPath)) {
  console.error(`not found: ${htmlPath}`);
  process.exit(2);
}

let mermaid;
try {
  mermaid = (await import('mermaid')).default;
} catch (err) {
  const here = path.dirname(new URL(import.meta.url).pathname);
  console.error('mermaid module not found. From this directory:');
  console.error(`  ${here}`);
  console.error('install dependencies with: npm install');
  process.exit(2);
}

// Mermaid's parse() runs the parser first, then post-processes the result
// (sanitizing via DOMPurify, registering hooks). In a DOM-less Node env those
// post-parse steps throw, but by then the parser has already accepted or
// rejected the source. We treat DOM-shaped errors as parser-success and only
// surface errors whose message looks like a real parser diagnostic.
function isDomEnvironmentError(msg) {
  return /DOMPurify|document is not defined|window is not defined/.test(msg);
}

const html = fs.readFileSync(htmlPath, 'utf8');

// Mermaid reads node.textContent at runtime. To match what the browser
// delivers we (a) decode HTML entities and (b) drop br element tags
// (they become element nodes with empty textContent).
const namedEntities = {
  '&quot;': '"', '&amp;': '&', '&lt;': '<', '&gt;': '>', '&apos;': "'",
  '&nbsp;': ' ', '&rarr;': '→', '&larr;': '←',
  '&mdash;': '—', '&ndash;': '–', '&hellip;': '…',
};
function decode(s) {
  let out = s;
  for (const [ent, ch] of Object.entries(namedEntities)) out = out.split(ent).join(ch);
  out = out.replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n));
  out = out.replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)));
  out = out.replace(/<br\s*\/?\s*>/gi, '');
  return out;
}

const re = /<pre\s+class="mermaid(?:-deferred)?"[^>]*>([\s\S]*?)<\/pre>/g;
const blocks = [];
let m;
while ((m = re.exec(html)) !== null) {
  blocks.push(decode(m[1]).replace(/^\s+|\s+$/g, ''));
}

if (blocks.length === 0) {
  console.log(`${htmlPath}: no mermaid blocks found`);
  process.exit(0);
}

const failures = [];
for (let i = 0; i < blocks.length; i++) {
  try {
    await mermaid.parse(blocks[i]);
  } catch (err) {
    const message = err?.message || String(err);
    if (isDomEnvironmentError(message)) continue;
    failures.push({ index: i, source: blocks[i], message });
  }
}

if (failures.length === 0) {
  console.log(`${htmlPath}: ${blocks.length} mermaid block(s) — all parse OK`);
  process.exit(0);
}

console.error(`${htmlPath}: ${failures.length} of ${blocks.length} mermaid block(s) failed to parse:`);
for (const f of failures) {
  console.error(`\n  block #${f.index}:`);
  for (const line of f.message.split('\n').slice(0, 6)) console.error(`    ${line}`);
  console.error(`  --- source (textContent as mermaid sees it) ---`);
  for (const line of f.source.split('\n').slice(0, 12)) console.error(`    ${line}`);
}
process.exit(1);
