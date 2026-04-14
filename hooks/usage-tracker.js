#!/usr/bin/env node
// usage-tracker.js — Tracks Skill and Task (subagent) invocations
// Logs to ~/.claude/usage-tracking/usage.jsonl

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
