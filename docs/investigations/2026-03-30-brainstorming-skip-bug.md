# Brainstorming Skill: Scan & Q&A Skip Bug

**Date:** 2026-03-30
**Status:** Root cause identified, fix proposed
**Symptom:** Brainstorming skill skips project scan and discovery questions, jumping straight to design or approach proposals. Reproduced twice on a friend's machine. Intermittent on author's machine.

## Root Cause

The project scan and Q&A phase are **described but not enforced**. The critique panel later in the skill is protected by MANDATORY/MUST/NEVER markers with explicit "skill violation" consequences. The scan and Q&A have zero equivalent protection.

### Evidence: Asymmetric enforcement language

Grep for `MUST|MANDATORY|NEVER|CRITICAL|IMPORTANT` in SKILL.md:

| Line | Marker | What it protects |
|------|--------|-----------------|
| 3 | `MUST` | Frontmatter — when to *invoke* the skill |
| 174 | `MANDATORY`, `MUST`, `NEVER` | Critique panel uses sub-agents |
| 205 | `MANDATORY` | Checklist path resolution |
| 225 | `IMPORTANT` | Fact-check division of labor |

**Zero enforcement markers protect the project scan or the Q&A phase.** The scan (line 18) says "First, dispatch..." — directional, not gated. The Q&A (line 38) says "Then ask questions..." — also directional.

### Three compounding factors

**1. Instruction density buries the early steps.** The skill is 310 lines. Scan + Q&A occupies lines 16-47 (~10%). The remaining 90% (Architect consult, mockups, critique panels, next steps) uses more detailed, more forceful language. The later sections exert stronger gravitational pull on the LLM. The scan gets treated as preamble rather than gate.

**2. The overview creates a shortcut path.** Lines 10-12:

> "Start by understanding the current project context, then ask questions one at a time to refine the idea."

"Understanding the current project context" is ambiguous. If the user's prompt describes what they want, the LLM can satisfy this by reading the message — it doesn't unambiguously mean "dispatch a scan sub-agent." The detailed instructions below *do* say to dispatch, but the overview planted a looser interpretation first.

**3. The author's environment has reinforcing constraints others don't.** The author's CLAUDE.md files contain verification discipline, root-cause-first mandates, and thoroughness norms that create ambient pressure to follow multi-step processes. Other users have none of that. Their LLM operates on SKILL.md alone, and SKILL.md doesn't self-enforce its early steps.

## Proposed Fixes

### Fix 1: Gate the scan with MANDATORY language

Around line 16, before the dispatch template:

```markdown
**MANDATORY: You MUST dispatch the project scan before asking any questions or proposing any design.** Do not skip the scan because the user's message seems clear — the scan reveals codebase context that shapes which questions to ask. Skipping the scan is a skill violation.
```

### Fix 2: Gate the Q&A with minimum question count

Around line 38, before question classification:

```markdown
**MANDATORY: Ask a minimum of 3 business questions before proposing any approaches or design sections.** Even when the user's request seems fully specified, there are always unstated assumptions about scope, priorities, and constraints. Do not shortcut the Q&A because the problem seems obvious.
```

### Fix 3: Tighten the overview to remove the ambiguous shortcut

Replace lines 10-12:

```markdown
# Before
Start by understanding the current project context, then ask questions one at a time to refine the idea.

# After
Start by dispatching a project scan sub-agent to survey the codebase, then ask questions one at a time to refine the idea.
```

This replaces vague "understanding the current project context" with the specific action required.

### Design principle behind these fixes

Match the enforcement pattern that already works. The critique panel is reliable because it uses triple reinforcement: (1) MANDATORY marker, (2) explicit required action, (3) stated consequence ("skill violation"). Apply the same pattern to any step that must not be skipped.
