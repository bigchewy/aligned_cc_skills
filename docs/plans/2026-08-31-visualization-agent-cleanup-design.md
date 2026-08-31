# Visualization Agent Cleanup — Design

## Context

The plugin has two generations of visualization tooling. The current generation —
`skills/_shared/visualization-runner.md`, added in the June visualization-runner
extraction — powers `superpowers:brainstorming` (per Eric's global CLAUDE.md, which
routes all software/interface design brainstorming through superpowers with the
aligned runner as its rendering engine) and `aligned:visualize-design`.

The older generation — four agents under `agents/` — predates that extraction and was
never fully retired:

- `agents/session-document-generator.md` — orchestrates the three diagram agents via a
  "fragment mode" to assemble a consolidated tabbed HTML document.
- `agents/flowchart-generator.md`, `agents/architecture-diagram-generator.md`,
  `agents/mockup-generator.md` — each supports a standalone mode (write a self-contained
  HTML file directly) and a fragment mode (return structured content to
  `session-document-generator`).

A repo audit found:

- `session-document-generator.md` has no live caller anywhere in `skills/`.
- `flowchart-generator.md` and `architecture-diagram-generator.md` have no live caller
  in either mode — standalone or fragment.
- `mockup-generator.md`'s fragment mode has no live caller (same reason —
  `session-document-generator` is dead). Its standalone mode has exactly one live
  caller: `skills/brainstorming/modes/authoring.md` step 3.

None of the four are referenced by `e2e/`, either plugin manifest
(`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`), or any config/eval
file.

`authoring.md`'s disambiguation rule (line 9) already excludes code/software work —
that routes to `superpowers:brainstorming`. So the one live call is not a UI-mockup
case; it fires when aligned's own authoring mode (decks, memos, briefs, positioning
docs) needs to compare content-layout options before the design doc is written. The
current mechanism is a hand-rolled HTML file — Tailwind and Mermaid loaded from a CDN,
hardcoded light-mode-only CSS — written to `docs/mockups/{session-name}/` and opened
locally with `open`. That predates the `design` skill, which is now the current
Claude Code tool for exactly this job: N options as artboards on one canvas, published
through the Artifact tool with theme-awareness, native Mermaid, click-to-select
editing, and a shareable link.

## Decision

**Delete outright** (dead code, zero live callers, confirmed against `skills/`,
`e2e/`, and both plugin manifests):

- `agents/session-document-generator.md`
- `agents/flowchart-generator.md`
- `agents/architecture-diagram-generator.md`
- `agents/mockup-generator.md`

**Rewire the one live call site** — `skills/brainstorming/modes/authoring.md` step 3.

Replace the current dispatch template (which tells a `general-purpose` subagent to
read `agents/mockup-generator.md` and write a static comparison file) with a direct
invocation of the `design` skill, passing the advisor-refined options and asking for
one artboard per option on a single canvas.

## What does not change

- `docs/mockups/` as a directory is left alone. It holds real historical output from
  the current runner pipeline (design-doc renders), not the old agent's output — only
  one session folder in it ever came from `mockup-generator`'s standalone mode. The
  directory stays; the old convention of writing fresh comparison files into it does
  not continue, since the `design` skill publishes to an Artifact URL rather than a
  local file.
- `mockup-generator.md` carried a bolted-on Steve Jobs critique step that ran after
  generating the mockup. `authoring.md` already runs Steve Krug / the topic advisor
  *before* generating the comparison, to shape the options — that step is unaffected
  and stays. The post-hoc Jobs critique does not carry forward; it was specific to the
  old agent, and nothing in `authoring.md`'s flow currently expects it.
- Steps 1, 2, and 4 of `authoring.md`'s option-comparison flow (advisor consult,
  dispatch trigger, and "proceed with the approach selection question" after review)
  are unchanged in shape — only the mechanism inside step 3 changes.

## Testing

This plugin has no automated tests over agent/skill markdown files. Correctness here
means: does the rewired step 3 in `authoring.md` produce a working `design` skill
invocation with the right inputs (number of options, brief description of what's being
compared, project root, session topic). That gets verified by walking through step 3
by hand — reading the rewired dispatch template end to end and confirming it reads as
a valid `design` skill call — not by an automated test, consistent with how the rest
of this plugin's skill/agent markdown is verified.

The shipped args template omits `{project-root}`: the `design` skill runs in-session with the same working directory, unlike the old subagent dispatch, which had to be told the project root explicitly because it started with none.

## Out of scope

- No changes to `skills/_shared/visualization-runner.md`, `visualization-protocol.md`,
  or any part of the current-generation pipeline.
- No change to when visualization fires in `authoring.md` (still gated on the design
  document being written, per the runner's own trigger contract) — folding the
  comparison-mockup step into the runner's tabbed-document pipeline was considered and
  rejected, because the runner only fires after the design doc is written, and this
  step fires earlier, during option exploration.
