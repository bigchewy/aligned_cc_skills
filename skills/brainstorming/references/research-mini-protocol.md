# Research Mini-Protocol (Authoring Sub-Flow Contract)

> **Pattern:** Mode-as-sub-flow. This is NOT the Architect-as-proxy pattern in `modes/authoring.md`. Proxy is one-question-one-decision per dispatch; this protocol is multi-phase (scope → corpus scan → synthesis) inside a single sub-agent dispatch. The sub-agent's main thread returns only a one-line confirmation; the synthesis lives in a file that the parent Authoring session reads inline.

## Inputs

The dispatching Authoring session writes a question file to `/tmp/brainstorm-context-{topic}/research-{question-slug}-question.md` containing:
- The curatorial decision in dispute (1-2 sentences)
- The constraints carried from Authoring (population, voice, hard requirements)
- A hint at relevant corpora to scan (literature, frameworks, registries) — optional

The dispatch prompt passed by Authoring MUST point at this file and at this protocol file's path. The sub-agent reads both before doing anything else.

## Phases

This protocol covers phases 1–3 of `modes/research.md` only — scope, corpus scan, synthesis. Phase 4 (Skeptic Pass), Phase 5 (Ranking + decision memo), and the Research mode critique panel are deliberately excluded.

**Phase 1 — Scope.** Read the question file. State (in your working memory, not in output) what the question is, what corpus is in scope, and what's out. If the question is ambiguous, do NOT halt — interpret it conservatively and note the interpretation in `## Open Questions` at the end.

**Phase 2 — Corpus scan.** Read the parent's `/tmp/brainstorm-context-{topic}/project-scan.md` (already written by the brainstorming router) for project context. Do NOT trigger your own project scan — recursive scan dispatch is forbidden. Use Glob/Grep/Read to surface candidate sources from registries, knowledge folders, and prior research artifacts.

**Phase 3 — Synthesis.** Compare candidates on construct fit, evidence quality, licensing/cost, validation status. Use your own reading and reasoning — do not dispatch domain advisors as sub-sub-agents. The sub-flow is single-level.

## Output contract

Write the synthesis to `/tmp/brainstorm-context-{topic}/research-{question-slug}-synthesis.md` using EXACTLY this structure:

```
## Synthesis
{2–4 paragraphs with citations to specific files, papers, or registry entries}

## Open Questions
- {bulleted list of unresolved sub-questions; empty list = a single bullet "- (none)"}

## Confidence
{high | medium | low} — {one-sentence caveat naming what would shift the assessment}
```

All three top-level headings are MANDATORY. The `## Confidence` line MUST contain the level (high/medium/low) AND a one-line caveat. The caveat is separated from the level by either an em-dash (`—`, preferred) or a regular hyphen (`-`); the parent Authoring session accepts either. The parent validates these structural rules before integrating the synthesis.

After writing, return ONLY the literal string `Synthesis written to {path}` — no transcript, no preamble. The parent session never sees your reading or reasoning; it sees only the synthesis file.

## Recursion forbidden

The sub-agent MUST NOT:
- Dispatch its own project-scanner sub-agent (read the parent's existing scan instead)
- Dispatch domain-advisor consults as further sub-agents
- Trigger a critique panel
- Write a decision memo or commit any files outside `/tmp/`
- Re-enter this protocol via another Task tool dispatch

Any of the above defeats Authoring's context-window discipline. If a sub-question genuinely needs deeper research, surface it in `## Open Questions` for the parent to handle in a fresh, separate brainstorming session.
