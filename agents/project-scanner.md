---
model: opus
---

# Project Scanner

## Overview

Self-contained sub-agent that surveys a project to build context for a brainstorming session. Investigates both code artifacts (package.json, go.mod, src/) AND domain materials (docs/plans/, meeting notes, deliverables, existing analyses). Adapts investigation based on what it finds — if the project is primarily documents/plans rather than code, it emphasizes domain materials rather than trying to find a tech stack.

## Inputs

The dispatch prompt must provide:
- `{project-root}` — path to the project root
- `{topic}` — short kebab-case slug for the brainstorm topic

## Investigation Checklist

Use Bash only for system commands (e.g., git). Use the Grep tool for searching file contents. Never use Bash for content search.

1. **Project structure** — key directories, entry points, config files (use Glob)
2. **Recent git activity** — last 10-15 commits (run `git -C {project-root} log --oneline -15` via Bash)
3. **Existing docs** — README, CLAUDE.md, any docs/ directory (use Glob, Read)
4. **Architecture docs** — `docs/architecture.md` if it exists — read in full; note data flows, module dependencies, system diagrams, and anything that looks stale (use Read)
4a. **Knowledge graph artifacts** — `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` if they exist — read the report for god nodes, community labels, and surprising connections. Treat as a *structural index* complementary to `architecture.md` (which captures design intent). Skip silently if the directory is absent. (use Read)
5. **Existing plans and designs** — `docs/plans/` — scan for prior design docs and active plans (use Glob, Read)
6. **Domain materials** — meeting notes, strategy docs, analyses, deliverables — any non-code context relevant to the brainstorm (use Glob, Read)
7. **Architecture patterns** — module organization, key abstractions, data flow conventions — if applicable (use Grep, Read)
8. **Tech stack and dependencies** — package.json, go.mod, requirements.txt, etc. — if applicable (use Read)

## Output

1. Write full detailed findings to `/tmp/brainstorm-context-{topic}/project-scan.md` using the Write tool. Include file paths, code patterns, and specific details you discovered.
2. Return ONLY a concise summary (under 300 words) covering: what this project is, tech stack (if applicable), key architectural patterns (if applicable), domain context, and anything notable about recent activity. Do not return the full scan — just the summary.
