# Live Visualization for Brainstorming — Design Document

**Date:** 2026-04-14
**Status:** Draft
**Priority:** 1 of 6 (SuperPowers comparison)
**Supersedes:** Session-document-generator dispatch within brainstorming sessions only (other skills continue using it)
**Mockups:** docs/mockups/live-visualization.html

## Goal

During brainstorming sessions, executives see visual artifacts evolve in real-time as the design takes shape — not generated after the fact as a static deliverable. The browser becomes a live mirror of the brainstorming conversation: the agent updates it, the user watches it, feedback stays in the chat.

This is an architectural shift, not a drop-in replacement: brainstorming moves from multi-agent orchestration (dispatching session-document-generator + diagram sub-agents in fragment mode) to direct HTML authoring by the main agent using a CSS component library.

### Success Criteria

1. **Timing:** The browser shows a meaningful visual artifact within 30 seconds of the agent beginning the design presentation phase — before the user provides feedback on the first section.
2. **Continuity:** The artifact updates at least once per validated design section, with no manual browser refresh required.
3. **Parity:** The final snapshotted artifact at `docs/mockups/{session-name}.html` is at least as informative as artifacts currently produced by the session-document-generator (tabbed layout, Mermaid diagrams, section breakdowns).

### Rollback

If live visualization fails during a session: revert the mode file changes and restore the session-document-generator dispatch. This is a single git revert. The session-document-generator agent and all diagram sub-agents remain unchanged and functional throughout.

## Decision Log

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Interaction model | Live mirror | Agent updates browser; feedback stays in chat. Simplest model, highest leverage. |
| 2 | Activation scope | Brainstorming only (v1) | Prove the concept before expanding to frameworks, critique panels, etc. |
| 3 | Critique panel visibility | Backstage | Visualization shows design during collaborative phases. Critique findings come through conversation. |
| 4 | Relationship to session-document-generator | Supersedes it for brainstorming | One visualization pipeline, not two. Supersedes both the initial dispatch (software.md ~137-148, business.md ~140-147) and the post-critique re-dispatch (software.md ~215-228, business.md ~183-196). Session-document-generator stays for other skills. |
| 5 | View approach | Frame template with CSS components | Freeform HTML with pre-built CSS classes. Agent generates content using documented components. |
| 6 | Lifecycle | Fully automatic | Skill starts visualization at design phase; auto-stops at session end. No user management. |
| 7 | Delivery mechanism | File-based with self-refresh | No web server. Agent writes HTML with self-refresh script; browser auto-reloads every 3s. Alternatives considered: (a) keep session-document-generator as-is (no live visualization — doesn't close the timing gap), (b) SSE-based persistent server (higher fidelity but ~300 lines of server code, shell scripts, PID management — complexity not justified until file-based approach hits UX limits). |
| 8 | Update mechanism | `setTimeout(() => location.reload(), 3000)` | Simpler than SSE/WebSocket. Works over `file://` protocol. 3s latency is imperceptible for brainstorming. |
| 9 | Template architecture | Single markdown file with inline HTML | One file = no drift between template and docs. The file is a component reference with an embedded HTML template, not an orchestrator like the session-document-generator. |
| 10 | Theme | Light only | No `prefers-color-scheme`. Matches every existing visualization artifact in the codebase. |
| 11 | Path resolution | Relative paths in mode files | Matches existing mode file patterns (`agents/...`, `skills/...`). Not `$CLAUDE_PLUGIN_ROOT`. |

## Architecture

### Overview

The agent writes a self-refreshing HTML file during brainstorming. The browser auto-reloads to show changes. At session end, the refresh script is stripped and the file becomes the permanent artifact at `docs/mockups/{session-name}.html`.

No web server. No shell scripts for lifecycle management. No process management. The entire system is: write a file, open it, update it, finalize it.

### Data Flow

```
Agent reads skills/brainstorming/references/brainstorm-components.md (once, at visualization start)
     |
     v
Agent writes /tmp/brainstorm-{topic}-{timestamp}/live.html (Write tool)
     |
     v
Browser auto-reloads (self-refresh script, 3s interval, 30min timeout)
     |
     v
Agent updates the same file as design evolves (Write tool)
     |
     v
Browser picks up changes on next reload cycle
     |
     v
Pre-critique: copy live file to docs/mockups/{session-name}.html (critique reads from here)
     |
     v
Post-critique: if design changed, update docs/mockups/ copy; strip refresh script from final copy
```

### Components

**1. `skills/brainstorming/references/brainstorm-components.md` — Template + Component Reference**

Single file containing:
- Full HTML template as a fenced code block
- Self-refresh script in a delimited block (`<!-- LIVE-REFRESH-START -->` / `<!-- LIVE-REFRESH-END -->`) with a 30-minute timeout (stops reloading after 30 minutes of page being open, preventing indefinite reload if session is abandoned)
- Hardcoded design tokens matching existing artifacts and `~/.claude/docs/design/design-principles.md`: `#faf9f7` background, `#ff6900` accent, `#e55d00` accent hover, `#fff7ed` accent subtle, system-ui font stack
- Tailwind CSS from CDN, Mermaid.js from CDN with lazy rendering
- CSS component classes with documentation and usage examples

**2. Mode file changes (`skills/brainstorming/modes/software.md` and `business.md`)**

Replace session-document-generator dispatch with inline live visualization instructions:
- At design presentation phase: agent reads `skills/brainstorming/references/brainstorm-components.md`, writes initial HTML, opens it
- During presentation: agent updates the HTML file after each validated section
- Pre-critique: copy live file to `docs/mockups/{session-name}.html` so the critique panel can access it at its configured path
- Post-critique: if critique modified the design, fully regenerate the HTML at `docs/mockups/{session-name}.html` (not surgical edit — full rewrite from the corrected design, using the same component reference). Strip the refresh script from the final copy.

Specific lines replaced in each mode file:
- `software.md` ~137-148 (initial visualization dispatch) → live visualization start instructions
- `software.md` ~215-228 (post-critique re-dispatch) → conditional full regeneration + refresh script stripping
- `business.md` ~140-147 (conditional visualization dispatch) → conditional live visualization start
- `business.md` ~183-196 (post-critique re-dispatch) → conditional regeneration + stripping

### CSS Component Library

Components mapped to brainstorming workflow steps:

| Component | v1 Essential | Workflow Step | HTML Pattern |
|-----------|-------------|---------------|-------------|
| **Phase tracker** | Yes | Both modes: shows current phase in the brainstorm | `<div class="phase-tracker">` with `.phase-item` and `.phase-current` |
| **Card grid** | Yes | Business: problems, root causes, solutions. Software: components, modules. | `<div class="card-grid">` with `.card` items |
| **Comparison grid** | Yes | Both modes: approach trade-offs (2-3 options) | `<div class="compare-grid compare-{n}col">` |
| **Tabbed navigation** | Yes | Both modes: organizing multi-section designs | Matching session-document-generator's existing tab/sub-tab pattern |
| **Callout boxes** | Yes | Both modes: decisions, constraints, risks, Architect notes | `<div class="callout callout-{type}">` (decision, constraint, risk, note) |
| **Mermaid containers** | Yes | Software mode: architecture diagrams, flows, state machines | `<div class="diagram-container"><pre class="mermaid">` |
| **Section containers** | Yes | Both modes: content grouping | `<div class="section">` |
| **Quadrant map** | Deferred | No current workflow step maps to this; add when a framework (e.g., Eisenhower matrix) needs it | `<div class="quadrant-map">` with 4 `.quadrant` cells |
| **Decision log** | Deferred | Could enhance design presentation but not required by current flow | `<div class="decision-log">` with `.decision-entry` items |

### Session Lifecycle

**Phase 1 — Start (automatic, at design presentation phase):**
1. Agent reads `skills/brainstorming/references/brainstorm-components.md`
2. Agent writes initial HTML to `/tmp/brainstorm-{topic}-{timestamp}/live.html` using the template and appropriate components (timestamp prevents collision if the same topic is brainstormed twice)
3. Agent opens the file in the default browser. On macOS: `open /tmp/brainstorm-{topic}-{timestamp}/live.html`. On Linux: `xdg-open`. The mode file should use a platform-aware pattern: `open /path || xdg-open /path` (separate Bash call — must not chain with `&&` due to auto-approve hook at `hooks/auto-approve-safe-bash-paths.js`). If the open command fails (headless environment), log a warning and continue — the artifact still gets written.
4. Browser opens, self-refresh script begins 3-second reload cycle (with 30-minute timeout)

**Phase 2 — Update (during design presentation):**
5. Agent presents a design section in chat, user validates
6. Agent updates the HTML file to reflect the validated section
7. Browser picks up the change within 3 seconds

**Phase 3 — Finalize (pre-critique through post-critique):**
8. Before critique dispatch: agent copies the live file to `docs/mockups/{session-name}.html` so the critique panel can access it at the configured path
9. Critique panel runs (unchanged process — reads from `docs/mockups/`)
10. If critique modified the design document: agent fully regenerates the HTML at `docs/mockups/{session-name}.html` from the corrected design using the component reference
11. Agent strips the `<!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END -->` block from the `docs/mockups/` copy
12. Agent adds `**Mockups:** docs/mockups/{session-name}.html` to the design document header (written AFTER copy — downstream consumers expect the file to exist at commit time)
13. Agent commits design doc + mockup together

**Business mode conditional:** In business mode, visualization is conditional ("if the design warrants visual artifacts"). The mode file preserves this gate — not all business brainstorms produce visuals. Software mode is always-on.

### What Changes in Existing Files

| File | Change |
|------|--------|
| `skills/brainstorming/modes/software.md` | Replace session-document-generator dispatch (~137-148) with live visualization start. Replace post-critique step 1 (~215-228) with conditional regeneration + stripping. Update critique panel's `visual-artifacts` config to reference the pre-critique copy. |
| `skills/brainstorming/modes/business.md` | Same replacements (~140-147 initial, ~183-196 post-critique), preserving the conditional gate (~136). |
| New: `skills/brainstorming/references/brainstorm-components.md` | Component reference + HTML template. |

### What Stays Unchanged

- **Session-document-generator agent** — Still used by other skills that dispatch it
- **Mockup-generator agent** — Still used for approach comparison mockups during brainstorming Q&A phase
- **Critique panel process** — Evaluates `docs/mockups/{session-name}.html` as before (pre-critique copy ensures this)
- **Post-critique commit step** and next-step prompt
- **Flowchart-generator, architecture-diagram-generator** — Unchanged; the live HTML embeds Mermaid diagrams directly

## Testing Strategy

### Refresh Script Stripping
- Verify the `<!-- LIVE-REFRESH-START -->` / `<!-- LIVE-REFRESH-END -->` delimiters survive HTML generation and are cleanly removable
- Test with edge cases: nested HTML comments within the block, minified HTML, multiline script tags
- Verify the stripped file is valid HTML (no orphaned tags from the removal)

### Mermaid Rendering
- Verify Mermaid diagrams render correctly in the self-refreshing file over `file://` protocol
- Test lazy rendering on tab switch (existing pattern from session-document-generator)
- Verify Mermaid syntax is valid before writing to file (reuse the verification step from session-document-generator)

### Finalization Integrity
- Verify the copy from `/tmp/` to `docs/mockups/` produces a valid standalone HTML file
- Verify the `**Mockups:**` field in the design doc points to a file that exists
- Verify the committed artifact renders correctly when opened after the session

### Component Class Correctness
- Each CSS class referenced in the component documentation must exist in the HTML template's `<style>` block
- The reference doc and template are in the same file, but verify no class is documented that isn't defined (and vice versa)

### Platform Behavior
- Verify `open` / `xdg-open` fallback works on macOS and Linux
- Verify graceful degradation when no browser is available (headless)

## Known Limitations

1. **Reload flash.** The page goes white for a frame on each 3-second reload. For a brainstorming artifact on a second monitor, this is tolerable. If users report it as a problem, a persistent web server with SSE becomes the justified upgrade.

2. **Tailwind CDN over `file://`.** 7 of 8 pre-existing mockup files in `docs/mockups/` use Tailwind CDN over `file://`. The 3-second reload may cause flash-of-unstyled-content (FOUC) if the CDN script re-fetches on each cycle. Browser caching mitigates this in most cases; inlining critical CSS in the template is a future optimization if FOUC is observed.

3. **No interaction capture.** v1 is view-only. User feedback flows through conversation. If future versions need click/annotation capture, HTTP POST to a lightweight server is the path — not WebSocket.

4. **Write atomicity.** The Write tool is atomic at the filesystem level on macOS (write + rename), so the browser shouldn't see truncated HTML mid-write. Called out as an assumption.

5. **macOS-primary.** The `open` command is macOS-native. Linux fallback (`xdg-open`) is included but untested. Headless environments get a warning, not an error.

## Future Expansion

If the file-based approach proves out, natural next steps include extending to other skills (framework walkthroughs, critique panels) and adding interaction capture. A persistent web server becomes justified only if users hit concrete UX problems with file-based refresh.
