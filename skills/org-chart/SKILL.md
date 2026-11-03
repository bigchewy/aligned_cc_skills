---
name: org-chart
description: "Use when a CEO asks to see the org chart, asks about the seats in a company and which ones the plugin covers, or asks what to do about a role they have not hired for yet. Opens the prebuilt B2B and B2C org chart pages, where every seat lists its jobs and the command to run for each. For where do I start requests, or which framework to start with for a problem, use the playbook skill instead. For running a named framework, use use-framework."
---

# Org Chart

Opens the org chart pages that ship with the plugin. Each chart shows the seats a company needs, which ones the plugin covers, and which ones are missing. Click a seat to see its jobs and the command to run for each.

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/org-chart/`. See `skills/_shared/resolve-skill-path.md` for rationale.

## Steps

1. Check that `{base-directory}/pages/index.html` exists.
2. If it is missing, tell the user the plugin install looks incomplete and stop. Build nothing.
3. Open it with the command for the user's system:
   - macOS: `open {base-directory}/pages/index.html`
   - Linux: `xdg-open {base-directory}/pages/index.html`
   - Windows: `cmd /c start "" {base-directory}\pages\index.html`
4. Tell the user the page is open. If they asked about a job, such as sales or hiring, name the seat that owns it and the command from that seat's page.

The page links to a B2B chart and a B2C chart. Both are the same for every user.
