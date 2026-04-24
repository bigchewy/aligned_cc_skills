#!/usr/bin/env node
// optional-usage-tracker.js — reference copy, NOT wired into the plugin.
// Identical logic to the canonical ~/.claude/hooks/usage-tracker.js maintained upstream.
// To enable on your machine: copy to ~/.claude/hooks/usage-tracker.js and add a
// PostToolUse hook entry for Skill|Task|Agent in ~/.claude/settings.json. See
// docs/plans/2026-04-23-claude-usage-logging-design.md "Plugin/global duplication"
// for rationale.

const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(process.env.HOME, '.claude', 'usage-tracking');
const LOG_FILE = path.join(LOG_DIR, 'usage.jsonl');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const entry = processEvent(data);
    if (entry) {
      fs.mkdirSync(LOG_DIR, { recursive: true });
      fs.appendFileSync(LOG_FILE, JSON.stringify(entry) + '\n');
    }
  } catch (_) {
    // Silently fail
  }
  process.exit(0);
});

function processEvent(data) {
  const tool = data.tool_name;
  const input = data.tool_input || {};

  if (tool === 'Skill') {
    return {
      ts: new Date().toISOString(),
      sid: data.session_id,
      type: 'skill',
      name: input.skill || 'unknown',
      args: input.args || null,
      cwd: data.cwd
    };
  }

  if (tool === 'Task' || tool === 'Agent') {
    return {
      ts: new Date().toISOString(),
      sid: data.session_id,
      type: 'agent',
      name: input.subagent_type || 'unknown',
      description: input.description || null,
      cwd: data.cwd
    };
  }

  return null;
}
