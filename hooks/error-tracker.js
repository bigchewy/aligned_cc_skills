#!/usr/bin/env node
// error-tracker.js — Claude Code PostToolUse/PostToolUseFailure hook
// Logs tool errors to ~/.claude/error-tracking/errors.jsonl

const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(process.env.HOME, '.claude', 'error-tracking');
const LOG_FILE = path.join(LOG_DIR, 'errors.jsonl');

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
    // Silently fail — never block Claude Code
  }
  process.exit(0);
});

function processEvent(data) {
  const event = data.hook_event_name;
  const base = {
    ts: new Date().toISOString(),
    sid: data.session_id,
    tool: data.tool_name,
    input: summarize(data.tool_name, data.tool_input),
    cwd: data.cwd
  };

  // PostToolUseFailure: tool itself failed (always log)
  if (event === 'PostToolUseFailure') {
    return {
      ...base,
      type: 'tool_failure',
      error: data.error || 'Unknown tool failure',
      interrupt: data.is_interrupt || false,
    };
  }

  // PostToolUse: tool succeeded but command may have failed
  if (event === 'PostToolUse') {
    const sig = detectError(data.tool_name, data.tool_input, data.tool_response);
    if (sig) {
      return {
        ...base,
        type: 'command_error',
        error: sig,
      };
    }
  }

  return null;
}

function detectError(tool, input, response) {
  if (!response) return null;
  const text = typeof response === 'string' ? response : JSON.stringify(response);

  if (tool === 'Bash') {
    // Non-zero exit code
    const exitMatch = text.match(/[Ee]xit code[:\s]+(\d+)/);
    if (exitMatch && exitMatch[1] !== '0') {
      return `Exit code ${exitMatch[1]}: ${firstLine(text)}`;
    }
    // Common error patterns
    const patterns = [
      'command not found', 'Permission denied', 'No such file or directory',
      'ENOENT', 'EACCES', 'ENOMEM', 'MODULE_NOT_FOUND',
      'SyntaxError', 'TypeError', 'ReferenceError',
      'Cannot find module', 'FATAL ERROR'
    ];
    for (const p of patterns) {
      if (text.includes(p)) return `${p}: ${firstLine(text)}`;
    }
  }

  // Write/Edit failures
  if ((tool === 'Write' || tool === 'Edit') && text.includes('"success":false')) {
    return `${tool} failed: ${firstLine(text)}`;
  }

  return null;
}

function summarize(tool, input) {
  if (!input) return '';
  if (tool === 'Bash') return (input.command || '').substring(0, 300);
  if (tool === 'Write' || tool === 'Read' || tool === 'Edit') return input.file_path || '';
  if (tool === 'Glob') return input.pattern || '';
  if (tool === 'Grep') return `${input.pattern || ''} in ${input.path || '.'}`;
  return JSON.stringify(input).substring(0, 200);
}

function firstLine(text) {
  const line = text.split('\n').find(l => l.trim()) || '';
  return line.length > 200 ? line.substring(0, 200) + '...' : line;
}
