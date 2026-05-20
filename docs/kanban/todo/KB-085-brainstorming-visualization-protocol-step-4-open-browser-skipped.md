# KB-085: Brainstorming visualization-protocol step 4 (open browser) is reliably skipped

- **Type:** bug (recurring agent-behavior regression)
- **Discovered during:** software-mode brainstorm session for exercise-renderers Phase 2 (2026-05-16), surfaced by user
- **Location:** `skills/brainstorming/references/visualization-protocol.md:46-50` — "Live phase" step 4

## Observed

The visualization protocol's step 4 explicitly says:

> **Open the file in the default browser** using a platform-aware pattern (separate Bash call — no `&&` chaining):
> `open /tmp/brainstorm-{topic}-{timestamp}/live.html || xdg-open /tmp/brainstorm-{topic}-{timestamp}/live.html`

Reliably, the agent generates the visualization HTML but does NOT open it. The user has had to explicitly ask "Where is the HTML design doc? You're supposed to open that up." across multiple recent brainstorm sessions.

Today's session: agent wrote `docs/mockups/2026-05-16-exercise-renderers-phase-2.html`, committed it, and presented the next-steps prompt — without ever invoking `open`. The user asked, then the agent ran `open <path>` correctly. Identical-shaped miss in earlier sessions.

## Hypothesis (why this regressed)

Something has changed recently that's causing this to fail reliably, not occasionally. Candidates worth investigating:

1. **Pragmatic-shortcut pressure.** When the agent decides to "skip the full template-copy-and-patch protocol" (writing a tighter compact HTML directly), the `open` step lives inside that protocol's "Live phase" section — skipping the protocol skips the open step. The protocol does NOT clearly state "even if you write the file directly, you must still open it." The step is locked inside the live-iteration loop framing.
2. **Pre-critique-snapshot framing.** The "Pre-critique snapshot" section (lines 64-72) covers copying `live.html` to `docs/mockups/`. The agent reads that as "this is the file write step," then jumps to critique dispatch — bypassing the live-phase's step 4 that already fired earlier in a real live-iteration loop.
3. **CLAUDE.md "Bash for compound commands triggers approval" rule.** The protocol uses `open ... || xdg-open ...` (a shell `||` operator). The user's global CLAUDE.md says compound commands with shell operators trigger interactive approval prompts. The agent may be (silently) avoiding the compound command rather than splitting it. The platform-aware fallback ought to be split into a darwin-vs-linux check rather than a `||` pipeline.
4. **Direct-write-to-mockups path bypasses live phase entirely.** When the agent generates the artifact directly at the committed location (`docs/mockups/{session-name}.html`) rather than `/tmp/brainstorm-{topic}-{timestamp}/live.html`, the live-phase "open" step is structurally never reached. The protocol's step 4 is conditional on having a `/tmp/` live file.

## Expected

When the brainstorming visualization fires (in any mode that produces a visual artifact), the agent should reliably open the resulting HTML in the browser — whether it followed the full live-phase loop OR took the compact-direct-write shortcut. The user shouldn't have to ask.

## Suggested fixes (any one of these would close)

- **F1 (cheapest):** Move the "open in browser" instruction OUT of "Live phase" step 4 and into a new unconditional section at the end of the Pre-critique snapshot block. Something like "Step 3: Open `docs/mockups/{session-name}.html` in the default browser." Make it apply to BOTH the live `/tmp/` file AND the committed-snapshot path.
- **F2:** Split the `open ... || xdg-open ...` recipe into two separate Bash calls with a platform check (`if [[ "$OSTYPE" == "darwin"* ]]; then open ...; else xdg-open ...; fi` — still a compound command, but predictable). Or just document `open` for macOS (which Eric uses) and add xdg-open as a separate line.
- **F3:** Add a step-4 reminder in the mode files (`modes/software.md`, etc.) — "When the visualization protocol writes the file, you must also invoke `open <path>` separately. This is easy to forget."
- **F4 (heaviest):** Bake the open command into the protocol's contract as a non-skippable artifact rather than a step embedded in prose. Hook-driven if Claude Code supports a PostWrite hook that opens HTML files written under `docs/mockups/`.

## Severity

MEDIUM. The artifact still ships (committed correctly), so the brainstorm output is intact. The miss is purely UX-cost: user has to ask, agent has to reread the protocol to find the missing step, brainstorm session loses a beat. But it reliably happens.

## Created

2026-05-16
