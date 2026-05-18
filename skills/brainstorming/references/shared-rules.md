<!-- Shared rules: Read into context once at the start of every brainstorming session per the SKILL.md Step 3 instruction. Applies to all four modes. Do not add YAML frontmatter. -->

# Shared Rules — Brainstorming Skill

These rules are constant across every brainstorming mode. Mode files do not repeat them — they apply by virtue of having been read here.

## Path Resolution

Within every mode file, `{base-directory}` resolves to the brainstorming skill directory (the router), not `modes/`. The router's `SKILL.md` Path Resolution note specifies the full resolution procedure (line printed at skill load, or — if compressed — Glob `$HOME` for `**/.claude-plugin/plugin.json` and take the parent of the matched `.claude-plugin/` directory as the plugin root). Mode files inherit this resolution.

## Re-reading the project scan

The router dispatches a project scan once per session. Results live at `/tmp/brainstorm-context-{topic}/project-scan.md`.

If a question during the brainstorm requires deeper detail about the project — a specific module's pattern, prior research artifacts, content registries, prior plans, or whatever the active mode's scan emphasized — read that file rather than re-exploring in the main thread. Do not dispatch a second scan.

## Stripping the live-refresh script

This rule applies to the two modes that produce a live HTML artifact: software and authoring. Research and Roadmap modes do not generate a live artifact and skip this rule.

Before committing the snapshot at `docs/mockups/{session-name}.html`, verify that both `<!-- LIVE-REFRESH-START -->` and `<!-- LIVE-REFRESH-END -->` delimiters exist in the file. If either delimiter is missing, STOP and flag the issue — a committed artifact with an active refresh script is a silent bug. If both are present, remove the block (inclusive of delimiters). The final committed artifact must not auto-refresh.

**Widget survival.** After stripping, any widget tables (`decisions-table`, `questions-table`) and their `WIDGETS-SCRIPT` block MUST still be present and bind on load. Widget code lives in a separate `<script>` block delimited by `<!-- WIDGETS-SCRIPT-START -->` / `<!-- WIDGETS-SCRIPT-END -->`, outside the LIVE-REFRESH delimiters. If a committed snapshot is missing the widget script after a strip, the widget block was injected inside the LIVE-REFRESH delimiters by mistake — re-run the visualization-protocol's widget-injection step and verify the block lands before `</body>` and AFTER `<!-- LIVE-REFRESH-END -->`.

## Interaction principles (apply to every mode)

- **One question at a time** — Don't overwhelm with multiple questions
- **Multiple choice preferred** — Easier to answer than open-ended when possible
- **Gates are mandatory** — Confirm completion of each phase before moving on
