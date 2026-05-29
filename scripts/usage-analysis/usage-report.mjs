#!/usr/bin/env node
// usage-report.mjs — Token/cost analysis of Claude Code transcripts.
//
// Answers: how much would my usage have cost on the API, broken down by
// repo, by skill, and by how the session was launched (interactive vs.
// headless `claude -p` — the latter is what autopilot/ralph drive).
//
// Pricing comes from `ccusage` (github.com/ryoppippi/ccusage), which prices
// each session from the published per-model API rates. This script does NOT
// re-derive pricing; it joins ccusage's per-session cost to metadata it reads
// out of the transcript files (cwd, entrypoint, Skill tool invocations).
//
// Usage:
//   node usage-report.mjs                      # runs `npx ccusage session --json` for you
//   node usage-report.mjs --ccusage-json FILE  # reuse a saved ccusage dump (faster)
//   node usage-report.mjs --top 25             # rows per table (default 15)
//
// Config dir resolves to $CLAUDE_CONFIG_DIR or ~/.claude.

import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { execFileSync } from "node:child_process";

// ---- args ----
const argv = process.argv.slice(2);
const getArg = (flag, def) => {
  const i = argv.indexOf(flag);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : def;
};
const TOP = parseInt(getArg("--top", "15"), 10);
const CCUSAGE_JSON = getArg("--ccusage-json", null);

const CONFIG_DIR = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude");
const PROJECTS_DIR = path.join(CONFIG_DIR, "projects");

// ---- 1. ccusage per-session costs (accurate pricing), keyed by sessionId ----
function loadCcusage() {
  if (CCUSAGE_JSON) {
    return JSON.parse(fs.readFileSync(CCUSAGE_JSON, "utf8"));
  }
  process.stderr.write("Running ccusage (npx ccusage@latest session --json)… ");
  const out = execFileSync("npx", ["-y", "ccusage@latest", "session", "--json"], {
    maxBuffer: 1 << 30,
    encoding: "utf8",
  });
  process.stderr.write("done.\n");
  return JSON.parse(out);
}

const cc = loadCcusage().session;
const costById = {};
for (const s of cc) costById[s.period] = s.totalCost;
const ccTotal = cc.reduce((a, s) => a + s.totalCost, 0);

// ---- 2. walk transcripts, extract metadata per session file ----
function* walk(dir) {
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else if (e.isFile() && p.endsWith(".jsonl")) yield p;
  }
}

// Collapse git worktrees back into their parent repo.
function repoOf(cwd) {
  if (!cwd) return "(unknown)";
  return cwd
    .replace(/\/\.worktrees\/.*$/, "")
    .replace(/--worktrees-.*$/, "")
    .replace(/\/\.claude\/worktrees\/.*$/, "");
}

// Autopilot prompt signatures (headless `claude -p` phases driven by scripts/autopilot).
const AUTOPILOT_SIGNATURES = [
  ["ralph-execute", "SINGLE-TASK RULE"],
  ["plan", "Write Implementation Plan (Non-Interactive)"],
  ["unattended", "running unattended under autopilot"],
];

const byRepo = {};
const skillFirst = {};
const skillInvokes = {};
const byLaunch = { interactive: 0, headless: 0, unknown: 0 };
const byAutopilotPhase = {};
let mapped = 0, missing = 0, headlessAutopilot = 0;

for (const file of walk(PROJECTS_DIR)) {
  const id = path.basename(file, ".jsonl");
  const cost = costById[id];
  let txt;
  try { txt = fs.readFileSync(file, "utf8"); } catch { continue; }

  let cwd = null, entrypoint = null;
  const skills = [];
  for (const line of txt.split("\n")) {
    if (!line) continue;
    let o;
    try { o = JSON.parse(line); } catch { continue; }
    if (o.cwd && !cwd) cwd = o.cwd;
    if (o.entrypoint && !entrypoint) entrypoint = o.entrypoint;
    const content = o.message?.content;
    if (Array.isArray(content)) {
      for (const b of content) {
        if (b.type === "tool_use" && b.name === "Skill" && b.input?.skill) {
          skills.push(b.input.skill);
          skillInvokes[b.input.skill] = (skillInvokes[b.input.skill] || 0) + 1;
        }
      }
    }
  }

  if (cost === undefined) { missing++; continue; } // e.g. Codex logs, empty sessions
  mapped += cost;

  byRepo[repoOf(cwd)] = (byRepo[repoOf(cwd)] || 0) + cost;

  const launch = entrypoint == null ? "unknown" : entrypoint.startsWith("sdk") ? "headless" : "interactive";
  byLaunch[launch] += cost;

  if (launch === "headless") {
    let tagged = false;
    for (const [phase, sig] of AUTOPILOT_SIGNATURES) {
      if (txt.includes(sig)) {
        byAutopilotPhase[phase] = (byAutopilotPhase[phase] || 0) + cost;
        tagged = true;
        break;
      }
    }
    if (tagged) headlessAutopilot += cost;
  }

  const uniq = [...new Set(skills)];
  if (uniq.length) skillFirst[skills[0]] = (skillFirst[skills[0]] || 0) + cost;
}

// ---- 3. report ----
const fmt = (n) => "$" + n.toFixed(2);
const pct = (n) => ((n / mapped) * 100).toFixed(1) + "%";
const rows = (obj) => Object.entries(obj).sort((a, b) => b[1] - a[1]);

console.log("\n=== VALIDATION ===");
console.log("ccusage grand total (all agents):", fmt(ccTotal));
console.log("Mapped to a Claude transcript    :", fmt(mapped));
console.log("Unmapped session files           :", missing, "(Codex logs live outside the Claude config dir; plus empty sessions)");

console.log("\n=== SPEND BY REPO (top " + TOP + ") ===");
for (const [r, c] of rows(byRepo).slice(0, TOP)) {
  console.log(fmt(c).padStart(11), pct(c).padStart(7), " ", r.replace(os.homedir(), "~"));
}

console.log("\n=== HOW SESSIONS WERE LAUNCHED ===");
console.log("Interactive (you typing, entrypoint=cli):", fmt(byLaunch.interactive).padStart(11), pct(byLaunch.interactive).padStart(8));
console.log("Headless (claude -p; autopilot/ralph)   :", fmt(byLaunch.headless).padStart(11), pct(byLaunch.headless).padStart(8));
if (byLaunch.unknown > 0)
  console.log("Unknown entrypoint                      :", fmt(byLaunch.unknown).padStart(11), pct(byLaunch.unknown).padStart(8));
console.log("  └─ headless spend matching an autopilot prompt signature:", fmt(headlessAutopilot), "(" + pct(headlessAutopilot) + ")");
for (const [phase, c] of rows(byAutopilotPhase)) {
  console.log("       ", phase.padEnd(14), fmt(c).padStart(11), pct(c).padStart(8));
}

console.log("\n=== SPEND BY SKILL (Skill-tool invocations — interactive only) ===");
console.log("Note: autopilot does NOT invoke writing-plans/executing-plans via the Skill");
console.log("tool. It feeds the SKILL.md text into a headless `claude -p`, so its spend");
console.log("shows up under 'Headless' above, NOT in this table.\n");
for (const [s, c] of rows(skillFirst).slice(0, TOP)) {
  console.log(fmt(c).padStart(11), pct(c).padStart(7), `(${skillInvokes[s] || 0}x)`.padStart(7), " ", s);
}
const skillTotal = Object.values(skillFirst).reduce((a, b) => a + b, 0);
console.log("\nSessions that began with a Skill-tool call:", fmt(skillTotal), "=", pct(skillTotal), "of mapped spend.");
console.log("");
