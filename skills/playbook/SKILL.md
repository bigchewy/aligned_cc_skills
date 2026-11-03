---
name: playbook
description: "Use when a CEO asks to see the playbook, asks which framework to start with for a problem, or asks what should come before a framework. Opens the prebuilt playbook map, where every framework sits in an I, We or It area with a start-here pick, and each framework page shows the documents it needs and the frameworks that write them. For running a specific framework, use use-framework instead."
---

# Playbook

Opens the playbook pages that ship with the plugin. The map puts every framework in an area under I (work on yourself), We (work on the team) or It (work on the company and the product). Each area marks one framework to start with. Click a framework to see what it needs, which frameworks write those documents, and the command that starts it.

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/playbook/`. See `skills/_shared/resolve-skill-path.md` for rationale.

## Steps

1. Check that `{base-directory}/pages/index.html` exists.
2. If it is missing, tell the user the plugin install looks incomplete and stop. Build nothing.
3. Open it with the command for the user's system:
   - macOS: `open {base-directory}/pages/index.html`
   - Linux: `xdg-open {base-directory}/pages/index.html`
   - Windows: `cmd /c start "" {base-directory}\pages\index.html`
4. Tell the user the page is open. If they named a problem, read `{base-directory}/layers.yaml`, pick the area whose note fits it, and name that area, its layer, and its `start` framework with the command `/aligned:use-framework <id>`.

The pages are the same for every user. The stage and market filters at the top narrow the map.
