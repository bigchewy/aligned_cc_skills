#!/usr/bin/env node
// Bump the plugin's patch version in both manifests that declare it.
//
// Claude Code copies this repo into a versioned plugin cache and only re-copies
// when the version string changes. Content edits with the version left alone
// never reach the cache, so an unbumped commit ships nothing.
//
// .claude-plugin/plugin.json is the version Claude Code reads; the enclosing
// marketplace entry must agree with it (`claude plugin tag` validates that).
// Both are written here so they can never drift.

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..');
const PLUGIN_JSON = path.join(REPO_ROOT, '.claude-plugin', 'plugin.json');
const MARKETPLACE_JSON = path.join(REPO_ROOT, '.claude-plugin', 'marketplace.json');

function bumpPatch(version) {
  const parts = version.split('.');
  if (parts.length !== 3 || parts.some((p) => !/^\d+$/.test(p))) {
    throw new Error(`version "${version}" is not major.minor.patch`);
  }
  parts[2] = String(Number(parts[2]) + 1);
  return parts.join('.');
}

// Rewrite the version in place with a targeted replace rather than a JSON
// round-trip, so hand-formatting in these manifests survives.
function replaceVersion(file, from, to) {
  const before = fs.readFileSync(file, 'utf8');
  const needle = `"version": "${from}"`;
  if (!before.includes(needle)) {
    throw new Error(`${path.relative(REPO_ROOT, file)} has no ${needle}`);
  }
  fs.writeFileSync(file, before.replace(needle, `"version": "${to}"`));
}

const pluginVersion = JSON.parse(fs.readFileSync(PLUGIN_JSON, 'utf8')).version;
const marketplaceVersion = JSON.parse(fs.readFileSync(MARKETPLACE_JSON, 'utf8'))
  .plugins.find((p) => p.name === 'aligned').version;

const next = bumpPatch(pluginVersion);

replaceVersion(PLUGIN_JSON, pluginVersion, next);
// The marketplace entry may already have drifted; rewrite from whatever it says.
replaceVersion(MARKETPLACE_JSON, marketplaceVersion, next);

process.stdout.write(next + '\n');
