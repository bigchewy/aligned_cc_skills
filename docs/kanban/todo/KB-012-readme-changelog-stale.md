# KB-012: README.md is stale

- **Type:** doc-staleness
- **Discovered during:** doc-staleness-detector
- **Location:** `README.md`
- **Observed:** Multiple sections of README.md are out of sync with the current codebase (plugin version 0.10.0):
  1. **Headline count (line 3):** Says "28 skills" but there are 31 SKILL.md files. Missing from count: `persona-panel`, `create-svg-diagram`, `claude-profile`.
  2. **Skill Reference table (lines 78-108):** Missing 3 skills: `persona-panel` (content testing against buyer personas), `create-svg-diagram` (hand-coded SVG diagrams with design tokens), `claude-profile` (purpose unknown — needs investigation).
  3. **Permissions section (lines 36-65):** Missing `Skill(aligned:persona-panel)`, `Skill(aligned:create-svg-diagram)`, `Skill(aligned:claude-profile)`.
  4. **Changelog (lines 197-235):** Stops at version 0.6.0. The plugin is now at 0.10.0. Missing changelog entries for 0.7.0 through 0.10.0, which include: advisor/framework directory flattening, persona-panel skill, create-svg-diagram skill, autopilot pipeline, session-document-generator agent, fragment mode for diagram agents, content generation skills (generate-deck, generate-blog-post, generate-one-pager), global design-principles fallback, brainstorming visualization refresh, and extensive generate-blog-post enhancements (MDX output, context-aware delivery, HTML preview, asset manifest).
- **Expected:** Update headline to "31 skills", add 3 missing skills to reference table and permissions section, add changelog entries for versions 0.7.0 through 0.10.0 summarizing the major features listed above.
- **Source commits:** 10 source commits since README was last updated (Mar 23-24), but the changelog gap spans months of accumulated drift from versions 0.6.0 to 0.10.0.
- **Severity:** HIGH
- **Created:** 2026-02-23
- **Updated:** 2026-03-24 (re-scanned by doc-staleness-detector — drift has grown significantly since original filing)
