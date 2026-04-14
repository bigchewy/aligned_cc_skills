#!/usr/bin/env node
// usage-report.js — Generates an HTML usage report from the JSONL tracking log.
// Reads ~/.claude/usage-tracking/usage.jsonl, cross-references against
// skills/ and agents/ directories, and writes docs/usage-report.html.

const fs = require('fs');
const path = require('path');

const PLUGIN_ROOT = path.resolve(__dirname, '..');
const LOG_FILE = path.join(process.env.HOME, '.claude', 'usage-tracking', 'usage.jsonl');
const OUTPUT_FILE = path.join(PLUGIN_ROOT, 'docs', 'usage-report.html');

// --- Data Collection ---

function readLog() {
  if (!fs.existsSync(LOG_FILE)) return [];
  return fs.readFileSync(LOG_FILE, 'utf8').trim().split('\n')
    .map(l => { try { return JSON.parse(l); } catch { return null; } })
    .filter(Boolean);
}

function listSkills() {
  const dir = path.join(PLUGIN_ROOT, 'skills');
  return fs.readdirSync(dir)
    .filter(f => f !== '_shared' && fs.statSync(path.join(dir, f)).isDirectory());
}

function listAgents() {
  const dir = path.join(PLUGIN_ROOT, 'agents');
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.md'))
    .map(f => f.replace('.md', ''));
}

function aggregate(entries) {
  const skills = {};
  const agents = {};

  entries.forEach(e => {
    const bucket = e.type === 'skill' ? skills : agents;
    const name = e.name || 'unknown';
    if (!bucket[name]) bucket[name] = { count: 0, first: e.ts, last: e.ts, sessions: new Set() };
    bucket[name].count++;
    if (e.ts < bucket[name].first) bucket[name].first = e.ts;
    if (e.ts > bucket[name].last) bucket[name].last = e.ts;
    if (e.sid) bucket[name].sessions.add(e.sid);
  });

  // Convert sets to counts
  for (const b of [skills, agents]) {
    for (const k of Object.keys(b)) {
      b[k].sessions = b[k].sessions.size;
    }
  }

  return { skills, agents };
}

function dailyActivity(entries) {
  const days = {};
  entries.forEach(e => {
    const day = e.ts.slice(0, 10);
    days[day] = (days[day] || 0) + 1;
  });
  return Object.entries(days).sort((a, b) => a[0].localeCompare(b[0]));
}

// --- HTML Generation ---

function statusBadge(count) {
  if (count === 0) return '<span class="badge badge-dead">ZERO</span>';
  if (count <= 3) return '<span class="badge badge-low">LOW</span>';
  if (count <= 10) return '<span class="badge badge-moderate">MODERATE</span>';
  return '<span class="badge badge-active">ACTIVE</span>';
}

function buildTable(data, registeredNames, type) {
  // Merge registered names with observed names
  const allNames = new Set([...registeredNames, ...Object.keys(data)]);
  const rows = [];

  for (const name of allNames) {
    const d = data[name] || { count: 0, first: '-', last: '-', sessions: 0 };
    const registered = registeredNames.includes(name);
    rows.push({
      name,
      count: d.count,
      sessions: d.sessions,
      first: d.first === '-' ? '-' : d.first.slice(0, 10),
      last: d.last === '-' ? '-' : d.last.slice(0, 10),
      registered,
    });
  }

  rows.sort((a, b) => b.count - a.count);

  let html = `<table>
    <thead><tr>
      <th>Name</th><th>Invocations</th><th>Sessions</th><th>First</th><th>Last</th><th>Status</th><th>Registered</th>
    </tr></thead><tbody>`;

  for (const r of rows) {
    const regIcon = r.registered ? '<span class="reg-yes">&#10003;</span>' : '<span class="reg-no">external</span>';
    html += `<tr>
      <td class="name-cell">${r.name}</td>
      <td class="num-cell">${r.count}</td>
      <td class="num-cell">${r.sessions}</td>
      <td>${r.first}</td>
      <td>${r.last}</td>
      <td>${statusBadge(r.count)}</td>
      <td>${regIcon}</td>
    </tr>`;
  }

  html += '</tbody></table>';
  return html;
}

function buildActivityChart(daily) {
  if (daily.length === 0) return '<p class="description">No activity data.</p>';
  const max = Math.max(...daily.map(d => d[1]));
  let html = '<div class="chart">';
  for (const [day, count] of daily) {
    const pct = Math.round((count / max) * 100);
    html += `<div class="chart-row">
      <span class="chart-label">${day}</span>
      <div class="chart-bar-container">
        <div class="chart-bar" style="width: ${pct}%"></div>
      </div>
      <span class="chart-value">${count}</span>
    </div>`;
  }
  html += '</div>';
  return html;
}

function generateHTML(entries, registeredSkills, registeredAgents) {
  const { skills, agents } = aggregate(entries);
  const daily = dailyActivity(entries);

  const dates = entries.map(e => e.ts).sort();
  const dateRange = dates.length > 0
    ? `${dates[0].slice(0, 10)} to ${dates.at(-1).slice(0, 10)}`
    : 'No data';
  const generated = new Date().toISOString().slice(0, 16).replace('T', ' ');

  const totalSkillInvocations = Object.values(skills).reduce((s, d) => s + d.count, 0);
  const totalAgentInvocations = Object.values(agents).reduce((s, d) => s + d.count, 0);
  const uniqueSkills = Object.keys(skills).length;
  const uniqueAgents = Object.keys(agents).length;
  const zeroSkills = registeredSkills.filter(n => !skills[n] && !skills['aligned:' + n]);
  const zeroAgents = registeredAgents.filter(n => !agents[n]);

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Usage Report \u2014 Aligned Plugin</title>
  <style>
    body {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #faf9f7;
      margin: 0;
      padding: 40px;
    }
    h1 { font-size: 1.5rem; font-weight: 500; color: #1a1a1a; margin-bottom: 4px; }
    .subtitle { font-size: 0.95rem; color: #555555; margin-bottom: 4px; }
    .context { font-size: 0.88rem; color: #6b7280; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb; }

    .tab-bar {
      display: flex; gap: 2px; border-bottom: 2px solid #f0eeeb;
      margin-bottom: 24px; flex-wrap: wrap;
    }
    .tab-btn {
      padding: 10px 18px; font-size: 0.85rem; font-weight: 500; color: #6b7280;
      background: transparent; border: none; border-bottom: 2px solid transparent;
      margin-bottom: -2px; cursor: pointer; transition: color 150ms, border-color 150ms;
      font-family: inherit;
    }
    .tab-btn:hover { color: #1a1a1a; }
    .tab-btn.active { color: #ff6900; border-bottom-color: #ff6900; }

    .tab-panel { display: none; }
    .tab-panel.active { display: block; }

    .section {
      background: white; border: 1px solid #e5e7eb; border-radius: 12px;
      padding: 24px; margin-bottom: 24px;
    }
    .section h2 { font-size: 1.1rem; font-weight: 500; color: #1a1a1a; margin-bottom: 8px; }
    .description { font-size: 0.88rem; color: #555555; margin-bottom: 12px; line-height: 1.6; }

    .stats-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 16px; margin-bottom: 24px;
    }
    .stat-card {
      background: white; border: 1px solid #e5e7eb; border-radius: 12px;
      padding: 20px; text-align: center;
    }
    .stat-value { font-size: 1.8rem; font-weight: 600; color: #1a1a1a; }
    .stat-label { font-size: 0.78rem; color: #6b7280; margin-top: 4px; }

    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    thead th {
      text-align: left; padding: 8px 12px; border-bottom: 2px solid #f0eeeb;
      color: #6b7280; font-weight: 500; font-size: 0.78rem; text-transform: uppercase;
    }
    tbody td { padding: 8px 12px; border-bottom: 1px solid #f5f3f0; }
    tbody tr:hover { background: #faf9f7; }
    .name-cell { font-weight: 500; color: #1a1a1a; }
    .num-cell { font-variant-numeric: tabular-nums; text-align: right; }

    .badge {
      font-size: 0.7rem; padding: 2px 8px; border-radius: 9999px;
      font-weight: 500; display: inline-block;
    }
    .badge-active { background: #ecfdf5; color: #059669; }
    .badge-moderate { background: #fffbeb; color: #d97706; }
    .badge-low { background: #fff7ed; color: #ea580c; }
    .badge-dead { background: #fef2f2; color: #dc2626; }

    .reg-yes { color: #059669; font-weight: 600; }
    .reg-no { color: #9ca3af; font-size: 0.75rem; }

    .chart { margin: 8px 0; }
    .chart-row { display: flex; align-items: center; margin: 3px 0; }
    .chart-label { width: 90px; font-size: 0.78rem; color: #6b7280; flex-shrink: 0; }
    .chart-bar-container { flex: 1; height: 18px; background: #f5f3f0; border-radius: 4px; overflow: hidden; margin: 0 8px; }
    .chart-bar { height: 100%; background: #ff6900; border-radius: 4px; transition: width 300ms; }
    .chart-value { width: 36px; text-align: right; font-size: 0.78rem; color: #1a1a1a; font-variant-numeric: tabular-nums; flex-shrink: 0; }

    .zero-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
    .zero-pill {
      font-size: 0.78rem; padding: 3px 10px; border-radius: 9999px;
      background: #fef2f2; color: #dc2626; font-weight: 500;
    }
  </style>
</head>
<body>
  <h1>Usage Report</h1>
  <p class="subtitle">Aligned Plugin \u2014 Skill & Agent Telemetry</p>
  <p class="context">Data range: ${dateRange} \u00b7 Generated: ${generated} UTC</p>

  <div class="stats-grid">
    <div class="stat-card"><div class="stat-value">${entries.length}</div><div class="stat-label">Total Invocations</div></div>
    <div class="stat-card"><div class="stat-value">${totalSkillInvocations}</div><div class="stat-label">Skill Calls</div></div>
    <div class="stat-card"><div class="stat-value">${totalAgentInvocations}</div><div class="stat-label">Agent Calls</div></div>
    <div class="stat-card"><div class="stat-value">${uniqueSkills + uniqueAgents}</div><div class="stat-label">Unique Names</div></div>
  </div>

  <div class="tab-bar">
    <button class="tab-btn active" onclick="showTab('skills')">Skills</button>
    <button class="tab-btn" onclick="showTab('agents')">Agents</button>
    <button class="tab-btn" onclick="showTab('activity')">Daily Activity</button>
    <button class="tab-btn" onclick="showTab('dead')">Dead / Zero</button>
  </div>

  <div id="tab-skills" class="tab-panel active">
    <div class="section">
      <h2>Skill Invocations</h2>
      <p class="description">Sorted by invocation count. "Registered" means a matching directory exists in skills/.</p>
      ${buildTable(skills, registeredSkills, 'skill')}
    </div>
  </div>

  <div id="tab-agents" class="tab-panel">
    <div class="section">
      <h2>Agent Invocations</h2>
      <p class="description">Sorted by invocation count. "Registered" means a matching .md file exists in agents/.</p>
      ${buildTable(agents, registeredAgents, 'agent')}
    </div>
  </div>

  <div id="tab-activity" class="tab-panel">
    <div class="section">
      <h2>Daily Activity</h2>
      <p class="description">Invocations per day across all skills and agents.</p>
      ${buildActivityChart(daily)}
    </div>
  </div>

  <div id="tab-dead" class="tab-panel">
    <div class="section">
      <h2>Registered Skills with Zero Invocations</h2>
      <p class="description">These skills exist in skills/ but have no entries in the tracking log for this period.</p>
      ${zeroSkills.length > 0
        ? '<div class="zero-list">' + zeroSkills.map(n => '<span class="zero-pill">' + n + '</span>').join('') + '</div>'
        : '<p class="description">None \u2014 all registered skills have at least one invocation.</p>'}
    </div>
    <div class="section">
      <h2>Registered Agents with Zero Invocations</h2>
      <p class="description">These agents exist in agents/ but have no entries in the tracking log for this period.</p>
      ${zeroAgents.length > 0
        ? '<div class="zero-list">' + zeroAgents.map(n => '<span class="zero-pill">' + n + '</span>').join('') + '</div>'
        : '<p class="description">None \u2014 all registered agents have at least one invocation.</p>'}
    </div>
  </div>

  <script>
    function showTab(id) {
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-' + id).classList.add('active');
      event.target.classList.add('active');
    }
  </script>
</body>
</html>`;
}

// --- Main ---

const entries = readLog();
const registeredSkills = listSkills();
const registeredAgents = listAgents();
const html = generateHTML(entries, registeredSkills, registeredAgents);

fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
fs.writeFileSync(OUTPUT_FILE, html);
console.log('Report written to', OUTPUT_FILE);
console.log(`${entries.length} entries, ${registeredSkills.length} registered skills, ${registeredAgents.length} registered agents`);
