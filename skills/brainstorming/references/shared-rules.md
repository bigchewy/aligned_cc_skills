<!-- Shared rules: Read into context once at the start of every brainstorming session per the SKILL.md Step 3 instruction. Applies to all three modes. Do not add YAML frontmatter. -->

# Shared Rules — Brainstorming Skill

These rules are constant across every brainstorming mode. Mode files do not repeat them — they apply by virtue of having been read here.

## Path Resolution

Within every mode file, `{base-directory}` resolves to the brainstorming skill directory (the router), not `modes/`. The router's `SKILL.md` Path Resolution note specifies the full resolution procedure (line printed at skill load, or — if compressed — Glob `$HOME` for `**/.claude-plugin/plugin.json` and take the parent of the matched `.claude-plugin/` directory as the plugin root). Mode files inherit this resolution.

## Re-reading the project scan

The router dispatches a project scan once per session. Results live at `/tmp/brainstorm-context-{topic}/project-scan.md`.

If a question during the brainstorm requires deeper detail about the project — a specific module's pattern, prior research artifacts, content registries, prior plans, or whatever the active mode's scan emphasized — read that file rather than re-exploring in the main thread. Do not dispatch a second scan.

## Stripping the live-refresh script

The canonical strip-script rule (verify the `<!-- LIVE-REFRESH-START -->`/`<!-- LIVE-REFRESH-END -->` delimiters, remove the block, preserve the widget script) lives in `skills/_shared/visualization-runner.md` § "Stripping the live-refresh script". It applies to the authoring mode; research and roadmap modes skip it.

## Interaction principles (apply to every mode)

- **One question at a time** — Don't overwhelm with multiple questions
- **Multiple choice preferred** — Easier to answer than open-ended when possible
- **Gates are mandatory** — Confirm completion of each phase before moving on
