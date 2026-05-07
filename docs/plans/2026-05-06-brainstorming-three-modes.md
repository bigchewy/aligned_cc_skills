---
---

# Brainstorming Three New Modes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add three new brainstorming modes (Research, Authoring, Planning) alongside the existing Software and Business modes — content-led brainstorms recruit domain experts and produce sequenced arrangements; research-led brainstorms recruit evidence-skeptics and produce comparisons; portfolio-planning brainstorms recruit strategy advisors and produce roadmaps + spawn-lists.

**Source Design Doc:** `docs/plans/2026-05-06-brainstorming-three-modes-design.md`

**Architecture:** Markdown-driven skill expansion. Eight new files (3 mode files, 3 critique checklists, 2 reference protocols) added under `skills/brainstorming/`. Three modified files: the brainstorming `SKILL.md` (router signal sets, disambiguation, mode-explanation block, hand-off branches), `skills/kickstart/SKILL.md` (one-line marketing copy), `skills/_shared/critique-panel-orchestration.md` (drop hardcoded mode example list, add optional `portfolio-file-path` config field). Zero edits to project-scanner, writing-plans, finishing-a-development-branch, executing-plans, kanban-resolve, contextual-recommendation. Authoring's optional Research sub-phase uses a new "Mode-as-sub-flow" pattern (file-mediated sub-agent dispatch via `/tmp/brainstorm-context-{topic}/research-{slug}-question.md` → `research-{slug}-synthesis.md`); the contract is authoritative in `references/research-mini-protocol.md`, not embedded prose.

**Tech Stack:** Markdown skill files; promptfoo eval scenarios (`e2e/scenarios/use-skill/`); pytest structural assertions (`e2e/tests/`).

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] No prerequisites — all tasks are automatable. Optional advisor adds (Marty Cagan, Lex Sisney) are listed in `## Manual Steps (Post-Automation)` because they are launch-time upgrades, not blockers; the default Planning panel (Christensen + Rumelt + Eric Ries) is launch-ready without Cagan, and Authoring's non-PSIU work covers everything Sisney would lead.

---

### ✅ Task 1: Create research-mini-protocol reference

**Files:**
- Create: `skills/brainstorming/references/research-mini-protocol.md`
- Test: `e2e/tests/test_brainstorming_files.py`

**Step 1: Write the failing test**

Create the test file with the first assertion:

```python
# e2e/tests/test_brainstorming_files.py
"""Structural assertions for the brainstorming three-modes implementation."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_research_mini_protocol_has_required_sections():
    text = read("skills/brainstorming/references/research-mini-protocol.md")
    assert "## Phases" in text, "missing ## Phases section"
    assert "## Output contract" in text, "missing ## Output contract section"
    assert "## Recursion forbidden" in text, "missing ## Recursion forbidden section"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ericpage/software/aligned_cc_skills && python -m pytest e2e/tests/test_brainstorming_files.py::test_research_mini_protocol_has_required_sections -v`

Expected: FAIL with `FileNotFoundError` (file does not exist yet).

**Step 3: Write the protocol file**

Create `skills/brainstorming/references/research-mini-protocol.md` with this exact content:

```markdown
# Research Mini-Protocol (Authoring Sub-Flow Contract)

> **Pattern:** Mode-as-sub-flow. This is NOT the Architect-as-proxy pattern in `modes/software.md`. Proxy is one-question-one-decision per dispatch; this protocol is multi-phase (scope → corpus scan → synthesis) inside a single sub-agent dispatch. The sub-agent's main thread returns only a one-line confirmation; the synthesis lives in a file that the parent Authoring session reads inline.

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
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_research_mini_protocol_has_required_sections -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/references/research-mini-protocol.md
git commit -m "brainstorming: add research-mini-protocol contract for Authoring sub-flow"
```

---

### ✅ Task 2: Create spawn-brief template reference

**Files:**
- Create: `skills/brainstorming/references/spawn-brief-template.md`
- Modify: `e2e/tests/test_brainstorming_files.py` (append assertion)

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorming_files.py`:

```python
def test_spawn_brief_template_has_eight_fields():
    text = read("skills/brainstorming/references/spawn-brief-template.md")
    required_fields = [
        "**Target mode:**",
        "**Status:**",
        "**Rough size:**",
        "**Prerequisites:**",
        "**External dependencies:**",
        "**Why now:**",
        "**Spawn brief (one paragraph, brainstorm-ready):**",
        "**Success criterion:**",
    ]
    missing = [f for f in required_fields if f not in text]
    assert not missing, f"missing fields in spawn-brief template: {missing}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_spawn_brief_template_has_eight_fields -v`

Expected: FAIL — file not found.

**Step 3: Write the template file**

Create `skills/brainstorming/references/spawn-brief-template.md`:

```markdown
# Spawn-Brief Template (Planning Portfolio Entry Schema)

> **v0 schema; provisional.** This 8-field schema is authored before any portfolio.md exists. After 2 portfolio docs ship, audit the schema for fields that were dead-weight or missing in practice — the v1 schema is informed by usage, not specified ahead of it.

Each entry in a Planning-mode `portfolio.md` uses this schema verbatim. Multiple entries are stacked under `## ` headings, one per portfolio item.

## Schema

```markdown
## {Item title}

**Target mode:** {Software | Authoring | Research}
**Status:** {pending | brainstorming | planned | in-progress | done}
**Rough size:** {hours | days | weeks}
**Prerequisites:** {bulleted list of items in this portfolio that must complete first, or "none"}
**External dependencies:** {bulleted list of things outside the portfolio's control, or "none"}
**Why now:** {1-2 sentences on what triggered this and what's lost if deferred}
**Spawn brief (one paragraph, brainstorm-ready):**
> {Audience + problem + constraint context for a fresh /aligned:brainstorming session}
**Success criterion:** {one sentence — what must be true when this item is "done"}
```

## Consumer contract

A user invoking `/aligned:brainstorming` against an entry pastes the **spawn-brief paragraph** (the `>` blockquote) as the prompt. The brainstorming router runs normal topic-keyword signal detection on the paragraph prose; the spawn-brief is authored to contain explicit mode-disambiguating keywords ("design...", "sequence...", "compare...") so detection routes correctly.

`target_mode` is **for the human reader and for documentation**, not consumed by the router (no parsing layer exists). If signal detection misses, the user gets the standard 5-way disambiguation question.

`/aligned:writing-plans` is **not** a portfolio.md consumer. The chain is:
*portfolio item → brainstorming → design doc → writing-plans → implementation plan*

## Field semantics

- **Target mode:** Which brainstorming mode this item should route to when its turn comes. Documentation only (router uses signals, not this field).
- **Status:** Lifecycle marker. `pending` is the default after creation. Update inline as items move through brainstorming → planning → execution.
- **Rough size:** Order-of-magnitude estimate. Use `hours` (sub-day), `days` (1-5 days), or `weeks` (>1 week). Items in the `weeks` bucket may need to be re-decomposed before they're brainstorm-ready.
- **Prerequisites:** Items earlier in this same portfolio that must reach `done` before this item is unblocked. List by `## ` heading title.
- **External dependencies:** Things outside the portfolio author's control — third-party APIs, vendor releases, customer commitments, hiring.
- **Why now:** The momentum case. What changed in the world (or the org) that makes this the right time? What's the regret cost of not doing it?
- **Spawn brief:** A single paragraph the user pastes literally into a fresh brainstorming session. Must contain mode-disambiguating keywords.
- **Success criterion:** A one-sentence test someone could run when the item is claimed-done. Must be observable without further dialog.
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_spawn_brief_template_has_eight_fields -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/references/spawn-brief-template.md
git commit -m "brainstorming: add spawn-brief template for Planning portfolio entries"
```

---

### ✅ Task 3: Create research-critique-checklist

**Files:**
- Create: `skills/brainstorming/research-critique-checklist.md`
- Modify: `e2e/tests/test_brainstorming_files.py` (append assertion)

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorming_files.py`:

```python
def test_research_critique_checklist_structure():
    text = read("skills/brainstorming/research-critique-checklist.md")
    assert text.startswith("# Research Critique Checklist"), "missing top heading"
    for section in ["## Critique Criteria", "## Critique Output Format", "## Important"]:
        assert section in text, f"missing {section}"
    for criterion in [
        "Scope clarity", "Corpus coverage", "Source quality",
        "Comparison rigor", "Validation honesty", "Licensing/cost clarity",
        "Recommendation defensibility", "Open-questions completeness",
        "Decision quality",
    ]:
        assert criterion in text, f"missing criterion: {criterion}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_research_critique_checklist_structure -v`

Expected: FAIL — file does not exist.

**Step 3: Write the checklist**

Create `skills/brainstorming/research-critique-checklist.md` modelled on `design-critique-checklist.md` structure (top heading, instructions, criteria, output format, important). Include all 9 criteria from the design doc:

```markdown
# Research Critique Checklist

You are a research reviewer. Your job is to find issues in research syntheses by verifying every claim against actual sources, checking the rigor of comparisons, and probing for evidence-quality issues. You are skeptical, thorough, and evidence-driven. You do not manufacture issues — if something checks out, say Pass.

Critique a research memo for scope clarity, source quality, and recommendation defensibility. Don't trust citations or rankings without checking. Every issue you report must include evidence — no evidence means no issue.

## Instructions

1. Read the research memo at the path provided. If the file cannot be read or is empty, report the error and stop.
2. For each criterion below, verify against the cited sources and project materials:
   - **Read** referenced documents, papers, framework registries
   - **Grep** to find related prior research
   - **Glob** to confirm referenced files exist
3. Write a critique to stdout (do NOT rewrite the memo)
4. Output a numbered list of specific issues with severity

**Applicability assessment:** After reading the memo, quickly assess which of the 9 criteria below apply. If a criterion clearly doesn't apply (e.g., "Licensing/cost clarity" when no candidate has commercial restrictions; "Comparison rigor" when the memo is a single-source review with no comparison table), mark it **N/A** with a one-line reason in the Checklist Results table and skip verification for that criterion.

**When you can't verify:** If the memo cites external sources you can't access, flag it as `[UNVERIFIABLE]` with the reason — don't skip it or assume it's correct.

**Evidence labeling:** For each issue, indicate `[EXTRACTED]` (directly quoted) or `[INFERRED]` (logical deduction from omissions or patterns).

## Critique Criteria

### 1. Scope clarity

- Is the research question stated explicitly?
- Is the corpus boundary defined (literature only, frameworks only, instruments, prior art)?
- Are out-of-scope candidates explicitly excluded with a one-line reason?

- BAD: Memo opens "let's review change management approaches" with no question, no corpus boundary, no exclusion list.
- GOOD: "Question: which ACT-derived frameworks are most validated for chronic pain populations? Corpus: peer-reviewed RCTs 2010-2026 + clinical practice guidelines. Out of scope: non-ACT contextual therapies."

### 2. Corpus coverage

- Did the memo miss obvious candidates given the stated corpus boundary?
- For comparative reviews, are the "usual suspects" all present, or are there suspicious omissions?
- Are coverage gaps explicitly named?

- BAD: ACT-frameworks review missing Hayes' canonical work.
- GOOD: Memo explicitly notes "Bach & Hayes 2002 not included — pre-RCT era; cited for historical context only."

### 3. Source quality

- Are citations to peer-reviewed sources where applicable?
- Are sources recent enough to reflect current evidence?
- Are non-peer-reviewed sources (blog posts, industry reports) flagged as such?

- BAD: Memo cites a vendor white paper as evidence of efficacy without flagging the source bias.
- GOOD: Each citation tagged with venue + date; non-peer-reviewed sources flagged inline.

### 4. Comparison rigor

- Are candidates compared on consistent axes?
- Are the axes apples-to-apples (e.g., not comparing one framework's "ease of adoption" to another's "theoretical depth")?
- Is missing data on a candidate-axis cell flagged, not silently dropped?

- BAD: Comparison table has empty cells with no indication of why (data missing? researcher didn't check? construct doesn't apply?).
- GOOD: Empty cells annotated `[no data — author has not measured]` or `[N/A — construct doesn't apply to this framework]`.

### 5. Validation honesty

- Does the memo distinguish "validated" (RCTs, replicated outcomes) from "endorsed by author" or "widely used"?
- Are validation claims sourced?
- Are unvalidated candidates labeled as such?

- BAD: Calls a framework "evidence-based" because the author wrote a popular book about it.
- GOOD: "Validated in 3 RCTs (citations) for adult depression; no published evidence for adolescent populations."

### 6. Licensing/cost clarity

- For instruments/frameworks with commercial-use restrictions, is the licensing model named?
- Are author-outreach requirements (e.g., "must contact author for permission") flagged?
- Are pricing tiers documented for paid options?

- BAD: Memo recommends a clinical instrument without noting it's only free for non-commercial use.
- GOOD: "Instrument X: free for research; commercial use requires per-seat license at $200/year."

### 7. Recommendation defensibility

- Would another reasonable researcher reach the same recommendation given the same evidence?
- Are alternatives ranked with explicit trade-off rationale?
- Is the recommendation's confidence level honest (not falsely high or hedged-into-uselessness)?

- BAD: Recommends candidate X with no comparison to runner-up Y, and no trade-off discussion.
- GOOD: "Recommended: X. Rationale: highest validated efficacy on the target population; lower licensing cost than Y; trade-off — X has thinner adolescent-specific evidence than Y, mitigated by [plan]."

### 8. Open-questions completeness

- What's left unresolved at the end of the memo?
- Are unresolved questions enumerated, or buried?
- Do open questions name what evidence would resolve them?

- BAD: Memo ends with the recommendation; no open questions section.
- GOOD: "Open questions: (1) does Framework X's adolescent evidence base hold beyond N=200? Resolves with: a multi-site replication study. (2) ..."

### 9. Decision quality (if Decision Log present)

- For each decision, assess whether the chosen approach is the best option given the stated alternatives.
- Rate each: **sound**, **questionable**, **wrong**.
- Cite evidence from the corpus or domain knowledge for any non-sound rating.
- If no Decision Log, mark N/A.

## Critique Output Format

```markdown
# Research Critique: {Memo Name}

**Memo file:** `{filepath}`
**Critiqued:** {date}

## Summary
{1-2 sentence overall assessment}

## Issues

### 1. {Issue title} (high/medium/low)
**Criterion:** {Which checklist item}
**Problem:** {What's wrong}
**Evidence:** {Quoted citation, missing source, or unsupported claim that proves it}
**Suggested fix:** {What to change in the memo}

### 2. ...

## Checklist Results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Scope clarity | {Pass / N issues found / N/A — reason} |
| 2 | Corpus coverage | {Pass / N issues found / N/A — reason} |
| 3 | Source quality | {Pass / N issues found / N/A — reason} |
| 4 | Comparison rigor | {Pass / N issues found / N/A — reason} |
| 5 | Validation honesty | {Pass / N issues found / N/A — reason} |
| 6 | Licensing/cost clarity | {Pass / N issues found / N/A — reason} |
| 7 | Recommendation defensibility | {Pass / N issues found / N/A — reason} |
| 8 | Open-questions completeness | {Pass / N issues found / N/A — reason} |
| 9 | Decision quality | {Pass / N issues found / N/A — reason} |
```

## Important

- Verify against actual sources, not memory — use Read, Grep, and Glob (never Bash grep)
- Report what IS wrong, not what MIGHT be wrong
- Include evidence (citations, quotes, missing sources) for every issue
- Do NOT rewrite the memo — just identify issues
- Severity guide: **high** = will mislead a reader making a decision, **medium** = will cause confusion or rework, **low** = cosmetic
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_research_critique_checklist_structure -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/research-critique-checklist.md
git commit -m "brainstorming: add research-critique-checklist with 9 criteria"
```

---

### ✅ Task 4: Create authoring-critique-checklist

**Files:**
- Create: `skills/brainstorming/authoring-critique-checklist.md`
- Modify: `e2e/tests/test_brainstorming_files.py` (append assertion)

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorming_files.py`:

```python
def test_authoring_critique_checklist_structure():
    text = read("skills/brainstorming/authoring-critique-checklist.md")
    assert text.startswith("# Authoring Critique Checklist"), "missing top heading"
    for section in ["## Critique Criteria", "## Critique Output Format", "## Important"]:
        assert section in text, f"missing {section}"
    for criterion in [
        "Population fit", "Constraint preservation", "Sequencing rigor",
        "Library coverage", "Voice consistency", "Goal-metric alignment",
        "v1/v2 scoping", "Code/schema seam", "Decision quality",
    ]:
        assert criterion in text, f"missing criterion: {criterion}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_authoring_critique_checklist_structure -v`

Expected: FAIL — file not found.

**Step 3: Write the checklist**

Create `skills/brainstorming/authoring-critique-checklist.md`. Mirror the structure of `design-critique-checklist.md`. The 9 criteria match the design's `§Authoring/Critique-checklist criteria` list. Include detailed criterion bodies, BAD/GOOD examples, the Critique Output Format block (with all 9 criteria in the results table), and the Important section. The checklist's introductory paragraph should explain that Authoring critiques content-led brainstorms (curriculum design, framework prompt authoring, exercise sequencing) and the criteria are tuned for arrangements rather than architecture.

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_authoring_critique_checklist_structure -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/authoring-critique-checklist.md
git commit -m "brainstorming: add authoring-critique-checklist with 9 criteria"
```

---

### ✅ Task 5: Create planning-critique-checklist

**Files:**
- Create: `skills/brainstorming/planning-critique-checklist.md`
- Modify: `e2e/tests/test_brainstorming_files.py` (append assertion)

**Step 1: Write the failing test**

Append:

```python
def test_planning_critique_checklist_structure():
    text = read("skills/brainstorming/planning-critique-checklist.md")
    assert text.startswith("# Planning Critique Checklist"), "missing top heading"
    for section in ["## Critique Criteria", "## Critique Output Format", "## Important"]:
        assert section in text, f"missing {section}"
    for criterion in [
        "Opportunity-space clarity", "Inventory completeness", "Sizing realism",
        "Dependency rigor", "Sequencing logic", "Capacity vs scope",
        "Spawn-brief quality", "Strategic coherence", "Decision quality",
    ]:
        assert criterion in text, f"missing criterion: {criterion}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_planning_critique_checklist_structure -v`

Expected: FAIL.

**Step 3: Write the checklist**

Create `skills/brainstorming/planning-critique-checklist.md`. Mirror `design-critique-checklist.md` structure (top heading, instructions, criteria, output format, important). Include all 9 criteria from the design doc's §Planning Critique-checklist criteria list. Note in the introductory section that Planning critique evaluates two coordinated artifacts (`roadmap.md` for strategic frame; `portfolio.md` for the spawn-list) — criterion 7 (Spawn-brief quality) operates on the portfolio. The portfolio path is read by critics as a supplementary input alongside `visual-artifacts`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_planning_critique_checklist_structure -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/planning-critique-checklist.md
git commit -m "brainstorming: add planning-critique-checklist with 9 criteria"
```

---

### ✅ Task 6: Create modes/research.md

**Files:**
- Create: `skills/brainstorming/modes/research.md`
- Modify: `e2e/tests/test_brainstorming_files.py` (append assertions)

**Step 1: Write the failing test**

Append:

```python
def test_research_mode_file_structure():
    text = read("skills/brainstorming/modes/research.md")
    # First line must be the canonical mode-file HTML comment (matches modes/software.md:1)
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    assert "Within this mode file, `{base-directory}` resolves to" in text, "missing base-directory note"
    # Required process phases per design §Research/Process
    for phase in ["Question scoping", "Corpus scan", "Comparative synthesis", "Skeptic pass", "Ranking"]:
        assert phase in text, f"missing process phase: {phase}"
    # Critique panel config must match design §Research/Critique-panel config
    assert "Fact-check mode: all-critics" in text
    assert "Criteria assignment: no" in text
    assert "research-critique-checklist.md" in text
    assert "POST-CRITIQUE CHECKLIST" in text, "missing post-critique checklist anchor"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_research_mode_file_structure -v`

Expected: FAIL.

**Step 3: Write the mode file**

Create `skills/brainstorming/modes/research.md` modelled on `modes/business.md` structure (mode-file HTML comment on line 1, base-directory note, Contents, Overview, The Process, After the Synthesis, Design Critique, Key Principles). Include:

- **The Process** with 5 phases per design §Research:
  1. Question scoping
  2. Corpus scan (passes mode=research to project-scanner — emphasize KBs, registries, knowledge folders, prior research artifacts)
  3. Comparative synthesis (auto-consult domain advisors topic-routed: Hayes for ACT, Levine for exercise physiology, Grubb for autonomic-disorders, etc., dispatched analogous to Architect auto-consult in software.md)
  4. **Skeptic pass — ship with inline single-purpose Skeptic role as the default committed path.** The role is authored inline in this mode file (a short prompt block instructing the selected critic to verify citations, check for missing counter-evidence, and flag licensing/cost claims that aren't sourced). Rumelt is the canonical critic for cutting-fluff source-quality skepticism (`id: richard-rumelt`). Document Architect-retargeting (telling The Architect to evaluate literature/KB evidence rather than codebase) as an **UPGRADE PATH** in a clearly marked block (e.g., a `<!-- UPGRADE PATH: ... -->` HTML comment or an "Upgrade path (post-pilot)" subsection). Do NOT activate the upgrade path until the Manual Steps Skeptic-Pass pilot validates that The Architect's "you do NOT evaluate business strategy" guardrail does not fire under the retargeting prompt.
  5. Ranking + decision memo

- **Output:** `docs/plans/YYYY-MM-DD-<topic>-research.md` for plan-shape work, or `knowledge/<area>/README.md` for KB-shape work. Sections: Scope → Corpus map → Comparison table → Ranking with caveats → Open questions queue → Sources cited.

- **Critique panel configuration block** (verbatim YAML-shape, matching `business.md:183-191`):
  ```
  - Skill name: brainstorming
  - Checklist filename: research-critique-checklist.md
  - Fact-check mode: all-critics
  - Fact-check tools: Glob, Grep, Read, WebSearch, WebFetch
  - Aggregation: sub-agent
  - Criteria assignment: no
  - Visual artifacts: none
  - Critique temp directory: /tmp/brainstorm-critique-{topic}
  ```

  *Note:* Research deliverables are research memos / KB artifacts, not design docs with diagrams — Research mode does not run the brainstorming visualization step, so the critic prompt template should not reference `{visual-artifacts-path}`. Drop the `Also review the visual artifacts at {visual-artifacts-path}` clause from the universal critic prompt for Research mode (it appears in `business.md:197` and `software.md:220, 229` but is absent here).

- **Universal critic prompt template** (mirrors `business.md:193-200` shape) with mode-specific Skeptic Pass instructions: when the critic is Rumelt, instruct cutting-fluff source-quality skepticism. The default Skeptic Pass invocation uses an inline single-purpose Skeptic role authored within this mode file (the prompt block tells the selected critic to verify citations, check for missing counter-evidence, and flag licensing/cost claims that aren't sourced). The Architect is NOT included in the default Skeptic Pass critic pool — its retargeting requires pilot validation per the Manual Steps.

- **Upgrade path (gated on pilot validation):** Once the Skeptic-Pass pilot in Manual Steps validates that The Architect's persona guardrails do not fire under retargeting, swap the inline Skeptic role for "Architect retargeted at literature/KB sources for evidence-trace verification" by editing this mode file to extend the Skeptic Pass critic pool. Until that pilot passes, the inline Skeptic role is the only committed path.

- **POST-CRITIQUE CHECKLIST — 3 mandatory steps** matching `business.md:206-228` structure:
  1. Visualization finalization (conditional, per business.md pattern)
  2. Commit
  3. **Step 3 — Next step prompt:** Different from Software/Business — Research has no `/aligned:writing-plans` follow-on. Output exactly two affordances:
     - Commit the research synthesis where it landed (`docs/plans/*-research.md` or `knowledge/<area>/README.md`)
     - Optional: open a follow-up Authoring or Software brainstorm using this research as input context. No autopilot.

- **No auto-Architect for codebase grounding** — Research mode doesn't depend on the codebase. Document this explicitly in The Process section.

- Standard **Design Critique** and **Key Principles** sections matching the shape of `modes/business.md`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_research_mode_file_structure -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/modes/research.md
git commit -m "brainstorming: add Research mode file"
```

---

### ✅ Task 7: Create modes/authoring.md

**Files:**
- Create: `skills/brainstorming/modes/authoring.md`
- Modify: `e2e/tests/test_brainstorming_files.py` (append assertions)

**Step 1: Write the failing test**

Append:

```python
def test_authoring_mode_file_structure():
    text = read("skills/brainstorming/modes/authoring.md")
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    assert "Within this mode file, `{base-directory}` resolves to" in text
    # Process phases
    for phase in [
        "Population & constraints",
        "Corpus scan",
        "Optional Research sub-phase",
        "Arrangement",
        "Orphan / residual catalog",
        "Architect audit",
    ]:
        assert phase in text, f"missing process phase: {phase}"
    # Critique panel config (division-of-labor)
    assert "Fact-check mode: division-of-labor" in text
    assert "Criteria assignment: yes" in text
    assert "authoring-critique-checklist.md" in text
    # Sub-flow contract pointers
    assert "research-mini-protocol.md" in text
    assert "/tmp/brainstorm-context-" in text
    assert "research-{question-slug}-question.md" in text
    assert "research-{question-slug}-synthesis.md" in text
    # Error paths for sub-flow
    assert "5 minutes" in text or "five minutes" in text, "missing sub-agent timeout"
    assert "## Synthesis" in text and "## Open Questions" in text and "## Confidence" in text, \
        "missing required synthesis-file headings in validation step"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_authoring_mode_file_structure -v`

Expected: FAIL.

**Step 3: Write the mode file**

Create `skills/brainstorming/modes/authoring.md` modelled on `modes/software.md` structure. Include all 6 phases from the design's §Authoring/Process. Critical sections:

- **Disambiguation rules** (Authoring vs Software, Authoring vs Research) per design §Authoring/Disambiguation rules.

- **Process phases** (1-6 per design):
  1. Population & constraints
  2. Corpus scan (mode=authoring; emphasize content registries, frameworks, prior curricula, KBs)
  3. **Optional Research sub-phase (Mode-as-sub-flow pattern)** — file-mediated handoff:
     - Authoring **first asks the user** "this needs evidence — should I dispatch a Research mini-flow?" before launching (no silent auto-dispatch).
     - On approval, write the question + context + constraints to `/tmp/brainstorm-context-{topic}/research-{question-slug}-question.md`.
     - Dispatch a `general-purpose` Task with a prompt that points at `skills/brainstorming/references/research-mini-protocol.md` and at the question file.
     - Wait for sub-agent to write `research-{question-slug}-synthesis.md` (5-minute timeout).
     - **Validation step** (mandatory before integration): Read the synthesis file. If any of `## Synthesis`, `## Open Questions`, `## Confidence` is missing, OR if `## Confidence` is present but lacks a caveat after the high/medium/low value, surface the malformed result to the user with: "synthesis came back malformed — proceed with partial answer, retry, or skip the research and continue without evidence?"
     - **Failure paths:** Three handled cases per design §Error paths:
       (a) Sub-agent crashes / no `Synthesis written to {path}` confirmation within 5 minutes → surface failure; user picks (skip / retry / retarget).
       (b) Confirmation arrives but synthesis file missing/empty → same three options.
       (c) Synthesis file fails validation (missing heading or missing confidence caveat) → same three options.
       No silent retries. No auto-fallback to inline research (would defeat context-window discipline).
  4. **Arrangement** — sequence/group/tier the corpus against constraints with the domain-advisor panel (Hayes, Loehr, Chapman, Seligman, Sisney, Brown, Mate, Linehan, Levine, Grubb — topic-routed). Domain advisors lead. Panel pattern follows `_shared/critique-panel-orchestration.md`.
  5. Orphan / residual catalog
  6. Architect audit (conditional — only if there's a code/schema seam)

- **Output:** `docs/plans/YYYY-MM-DD-<topic>-design.md`. Sections: Why now → Goal → Hard constraints → Core commitments → What changes → Decision log → Out of scope → Orphan / residual catalog → Tests required (if code seam).

- **Critique panel configuration block:**
  ```
  - Skill name: brainstorming
  - Checklist filename: authoring-critique-checklist.md
  - Fact-check mode: division-of-labor
  - Fact-check tools: Glob, Grep, Read, WebSearch, WebFetch
  - Aggregation: sub-agent
  - Criteria assignment: yes
  - Visual artifacts: docs/mockups/{session-name}.html
  - Critique temp directory: /tmp/brainstorm-critique-{topic}
  ```

- **Criteria mapping table** (mirroring `software.md:201-213`) — map each of the 9 authoring-critique criteria to best-fit advisor domains.

- **Fact-checker prompt template** and **Regular critic prompt template** matching `software.md` shape with `{checklist-path}`, `{design-file-path}`, `{visual-artifacts-path}`, `{report-path}` placeholders.

- **POST-CRITIQUE CHECKLIST — 3 mandatory steps** matching `software.md:238-278` structure. **Step 3 — Next step prompt:** matches Software mode (Option A: hands-on writing-plans + worktree; Option B: autopilot.sh). Authoring's `*-design.md` is `writing-plans`-compatible.

- **Sisney absence handling:** If the topic matches PSIU/Four-Forces keywords and `advisors/prompts/lex-sisney.md` is absent, note the absence to the user once and proceed with remaining domain advisors. Do not block.

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_authoring_mode_file_structure -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/modes/authoring.md
git commit -m "brainstorming: add Authoring mode file with Research sub-flow"
```

---

### ✅ Task 8: Create modes/planning.md

**Files:**
- Create: `skills/brainstorming/modes/planning.md`
- Modify: `e2e/tests/test_brainstorming_files.py` (append assertions)

**Step 1: Write the failing test**

Append:

```python
def test_planning_mode_file_structure():
    text = read("skills/brainstorming/modes/planning.md")
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    assert "Within this mode file, `{base-directory}` resolves to" in text
    # 5 process phases
    for phase in [
        "Opportunity space",
        "Candidate inventory",
        "Sizing & dependencies",
        "Sequencing & rationale",
        "Spawn briefs per item",
    ]:
        assert phase in text, f"missing process phase: {phase}"
    # Two-artifact output
    assert "-roadmap.md" in text
    assert "-portfolio.md" in text
    # Critique panel
    assert "Fact-check mode: division-of-labor" in text
    assert "Criteria assignment: yes" in text
    assert "planning-critique-checklist.md" in text
    # Default panel + Cagan-conditional
    assert "Christensen" in text and "Rumelt" in text and "Eric Ries" in text, \
        "missing default launch panel"
    # Cagan absence-handling must reference the actual prompt-file path, not just the name
    assert "advisors/prompts/marty-cagan.md" in text, \
        "Cagan absence-handling must check the actual prompt-file path"
    # Spawn-brief reference
    assert "spawn-brief-template.md" in text
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_planning_mode_file_structure -v`

Expected: FAIL.

**Step 3: Write the mode file**

Create `skills/brainstorming/modes/planning.md` modelled on `modes/business.md` (Phase 1-4 structure with gates) with planning-specific content. Include:

- **Disambiguation rules** (Planning vs Business: RCA-shaped vs portfolio-shaped; Planning vs Software: single-feature vs multi-feature) per design §Planning/Disambiguation rules.

- **The Process** with 5 phases:
  1. Opportunity space & constraints (goal, audience, time horizon, budget, capacity, success criteria)
  2. Candidate inventory (sources: prior research, customer asks, technical debt, opportunities, deferred items from past plans)
  3. Sizing & dependencies (per-candidate rough size + dependencies + prerequisites + risks; strategy/PM panel grounded in Cagan/Christensen/Ries)
  4. Sequencing & rationale (lead criteria: dependency unblocking, risk reduction, value delivery, momentum)
  5. Spawn briefs per item — each portfolio entry uses the schema from `references/spawn-brief-template.md`. **Reference the template; do not duplicate the schema in this mode file.**

- **Advisors:** Default launch panel = Christensen + Rumelt + Eric Ries. **Marty Cagan is "preferred lead when available"** — the mode file checks for `advisors/prompts/marty-cagan.md` existence on entry. If absent, silently uses the default panel without surfacing the absence (per design §Error paths #5). Topic-conditional additions: Bezos, Paul Graham, Garry Tan, Lara Hogan via the dynamic critic selector in `_shared/critique-panel-orchestration.md`. Cite Rumelt's `frameworks/kernel-of-good-strategy/` and Bezos's `frameworks/type-1-type-2-decisions/` as reference-grade frameworks. The Architect joins for codebase-reality dependency check (late audit).

- **Output (two artifacts):**
  - `docs/plans/YYYY-MM-DD-<topic>-roadmap.md` — strategic frame, sequencing rationale, dependency map, success criteria. **This is the primary `{design-file-path}` passed to the critique panel.**
  - `docs/plans/YYYY-MM-DD-<topic>-portfolio.md` — spawn-list with status-tagged entries (one entry per portfolio item, each using the 8-field schema from `references/spawn-brief-template.md`). **Attached to critique dispatches as a supplementary input.**

- **Critique panel configuration block:**
  ```
  - Skill name: brainstorming
  - Checklist filename: planning-critique-checklist.md
  - Fact-check mode: division-of-labor
  - Fact-check tools: Glob, Grep, Read, WebSearch, WebFetch
  - Aggregation: sub-agent
  - Criteria assignment: yes
  - Visual artifacts: docs/mockups/{session-name}.html
  - Portfolio file: docs/plans/YYYY-MM-DD-<topic>-portfolio.md
  - Critique temp directory: /tmp/brainstorm-critique-{topic}
  ```

- **Critic prompt extension:** Both the fact-checker and regular critic prompt templates include the line: "Read also `{portfolio-file-path}` for the spawn-list — evaluate spawn-brief quality (criterion 7) against it."

- **Criteria mapping table** mapping each of the 9 planning-critique criteria to best-fit advisor domains.

- **POST-CRITIQUE CHECKLIST — 3 mandatory steps:**
  1. Visualization finalization (per business.md pattern; conditional — most planning brainstorms produce dependency-map / sequencing visualizations)
  2. Commit (`roadmap.md` + `portfolio.md` + `docs/architecture.md` if updated; staged together)
  3. **Step 3 — Next step prompt:** Different from Software/Authoring — Planning has no `/aligned:writing-plans` follow-on on the portfolio itself. Output exactly two affordances:
     - Commit `roadmap.md` + `portfolio.md` to `docs/plans/`.
     - "Pick the first item from the portfolio and run `/aligned:brainstorming` against its spawn brief — that brainstorm produces a design doc, which `/aligned:writing-plans` then turns into an implementation plan." The portfolio is brainstorm-spawning, not brainstorm-consuming.

- **Out of scope:** WIP-limit logic, swimlanes, status-workflow automation. Distinct from `docs/kanban/` (which holds small auto-found items).

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_planning_mode_file_structure -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/modes/planning.md
git commit -m "brainstorming: add Planning mode file with two-artifact output"
```

---

> **Ordering note for Tasks 9-15:** All seven tasks modify the same file (`skills/brainstorming/SKILL.md`). Run them strictly in order — each task's Edit anchor depends on prior task edits being present. In particular, Task 11 replaces the Step 1 signal sets but preserves the trailing "If signals are mixed or absent" sentence as the bridge into Task 12's Disambiguation Rules subsection — Task 11's replacement block must end with that sentence intact (it's the Edit anchor for Task 12).

### ✅ Task 9: Update SKILL.md frontmatter description

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (frontmatter `description:` field on line 3)
- Modify: `e2e/tests/test_brainstorming_files.py` (append assertion)

**Step 1: Write the failing test**

Append:

```python
def test_skill_md_description_names_five_modes():
    text = read("skills/brainstorming/SKILL.md")
    # Find the frontmatter description line
    lines = text.splitlines()
    desc_line = next((l for l in lines[:10] if l.startswith("description:")), None)
    assert desc_line is not None, "frontmatter description line not found"
    # Must reference all five modes
    for mode in ["software", "business", "research", "authoring", "planning"]:
        assert mode.lower() in desc_line.lower(), f"description missing mode: {mode}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_description_names_five_modes -v`

Expected: FAIL — description currently only names software/business.

**Step 3: Modify SKILL.md frontmatter**

Replace line 3 of `skills/brainstorming/SKILL.md`:

Old (line 3):
```
description: "Structures creative and strategic work through guided dialogue — software design or business strategy. Use before any creative, architectural, or strategic work that benefits from structured exploration and expert critique."
```

New (line 3):
```
description: "Structures creative and strategic work through guided dialogue across five modes — software design, business strategy, research synthesis, content authoring, and multi-feature planning. Use before any creative, architectural, or strategic work that benefits from structured exploration and expert critique."
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_description_names_five_modes -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/SKILL.md
git commit -m "brainstorming: extend SKILL.md description to five modes"
```

---

### ✅ Task 10: Update SKILL.md Overview to describe 5-mode skill

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (Overview section, currently lines 10-14)

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorming_files.py`:

```python
def test_skill_md_overview_describes_five_modes():
    text = read("skills/brainstorming/SKILL.md")
    # Overview section should mention all 5 mode names
    overview_start = text.index("## Overview")
    overview_end = text.index("## Step 1")
    overview = text[overview_start:overview_end]
    for mode in ["Software", "Business", "Research", "Authoring", "Planning"]:
        assert mode in overview, f"Overview missing mode: {mode}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_overview_describes_five_modes -v`

Expected: FAIL.

**Step 3: Replace Overview section**

In `skills/brainstorming/SKILL.md`, replace the existing Overview section (currently 5 lines, "## Overview" through the line ending in "Goal → Problems → Root Causes → Solutions)."):

Old:
```
## Overview
A unified brainstorming skill that adapts its process based on what you're
working on. Software/technical topics get a fluid Q&A with Architect
auto-consult. Business/strategy topics get a structured 4-phase process
(Goal → Problems → Root Causes → Solutions).
```

New:
```
## Overview
A unified brainstorming skill that adapts its process based on what you're
working on. Five modes covering distinct shapes of brainstorm work:

- **Software** — fluid Q&A with Architect auto-consult; deliverable is a design doc.
- **Business** — structured 4-phase process (Goal → Problems → Root Causes → Solutions); deliverable is a strategic plan.
- **Research** — corpus survey + comparative synthesis with Skeptic Pass; deliverable is a research memo or KB artifact.
- **Authoring** — content sequencing with domain-advisor panel and optional Research sub-phase; deliverable is a sequenced design doc (curriculum, framework prompts, exercise programs).
- **Planning** — multi-feature portfolio sequencing with strategy advisors; deliverable is a roadmap + spawn-list portfolio.
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_overview_describes_five_modes -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/SKILL.md
git commit -m "brainstorming: update SKILL.md Overview to describe five modes"
```

---

### ✅ Task 11: Replace SKILL.md Step 1 signal sets

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (Step 1 section — replaces software/business signal lists with 5 sets; "planning" moves from Business to Planning)

**Step 1: Write the failing test**

Append:

```python
def test_skill_md_step1_has_five_signal_sets():
    text = read("skills/brainstorming/SKILL.md")
    step1_start = text.index("## Step 1")
    step2_start = text.index("## Step 2")
    step1 = text[step1_start:step2_start]
    # All 5 mode names appear as bolded headers
    for header in [
        "**Software mode**",
        "**Business mode**",
        "**Research mode**",
        "**Authoring mode**",
        "**Planning mode**",
    ]:
        assert header in step1, f"Step 1 missing signal set header: {header}"
    # 'planning' must NOT appear in Business signal set
    business_idx = step1.index("**Business mode**")
    research_idx = step1.index("**Research mode**")
    business_block = step1[business_idx:research_idx]
    assert "planning" not in business_block.lower(), \
        "'planning' should be in Planning mode signals, not Business"
    # 'planning' MUST appear in Planning signal set
    planning_idx = step1.index("**Planning mode**")
    planning_block = step1[planning_idx:]
    assert "planning" in planning_block.lower() or "roadmap" in planning_block.lower(), \
        "Planning signal set missing planning/roadmap keywords"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_step1_has_five_signal_sets -v`

Expected: FAIL — only 2 signal sets exist today.

**Step 3: Replace Step 1 mode classification block**

In `skills/brainstorming/SKILL.md`, replace the block from `## Step 1: Detect Mode` through the end of the Business mode bullet list (currently up to "non-code directory") with the revised 5-mode block below. **Do NOT remove the existing "If signals are clear" or "If signals are mixed or absent" sentences that follow the Business mode block** — they are downstream Edit anchors for Tasks 12-13. Only replace the classification block; leave the post-classification routing prose intact. Preserve the Signal precedence note verbatim.

```markdown
## Step 1: Detect Mode
Classify the user's topic into one of five modes:

**Signal precedence:** Topic keywords take priority over environment signals.
A user in a code repo asking about "pricing strategy" is business mode, not
software mode. Environment is a tiebreaker when topic keywords are absent.

**Software mode** — building, modifying, or designing software:
- Topic signals: features, components, APIs, bugs, refactoring, architecture,
  implementation, code, testing, data models
- Environment (tiebreaker): project contains code files (package.json,
  Cargo.toml, go.mod, pyproject.toml, etc.)

**Business mode** — strategy, decisions, RCA-shaped diagnosis:
- Topic signals: strategy, sales, marketing, positioning, meeting prep,
  decisions, stakeholders, pricing, proposals, RCA, diagnosis,
  "why isn't this working"
- Environment (tiebreaker): project is docs-only, Obsidian vault, or
  non-code directory

**Research mode** — evidence synthesis, comparative review, literature audit:
- Topic signals: literature review, evidence map, comparative review,
  instrument selection, framework comparison, KB design,
  "what does the literature say", systematic review,
  annotated bibliography
- Environment (tiebreaker): knowledge folders, prior research artifacts,
  or registries are present

**Authoring mode** — content design, curriculum sequencing, voice migration:
- Topic signals: curriculum, program design, sequence content,
  exercise sequencing, content design, "what to teach in what order",
  rewrite for audience, voice migration, framework prompt authoring,
  chapter sequencing
- Environment (tiebreaker): content registries, prior curricula,
  brand voice files are present

**Planning mode** — multi-feature roadmap, portfolio sequencing:
- Topic signals: roadmap, prioritization, portfolio, "what to build next",
  milestone, sequence features, multi-feature build, project plan,
  "too big for one brainstorm"
- Environment (tiebreaker): prior roadmaps, open kanban, or customer asks
  are present
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_step1_has_five_signal_sets -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/SKILL.md
git commit -m "brainstorming: replace Step 1 signal sets with five-mode classification"
```

---

### ✅ Task 12: Add SKILL.md Disambiguation Rules subsection

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (insert new subsection between "If signals are mixed or absent" line and "### Mode Explanation Block" heading)

**Step 1: Write the failing test**

Append:

```python
def test_skill_md_has_disambiguation_rules():
    text = read("skills/brainstorming/SKILL.md")
    assert "### Disambiguation Rules" in text, "missing Disambiguation Rules subsection"
    # All three rule pairs must appear
    for pair in [
        "Software vs Authoring",
        "Authoring vs Research",
        "Business vs Planning",
    ]:
        assert pair in text, f"missing rule: {pair}"
    # 5-way disambiguation question must appear
    assert ("Software design" in text and "Business strategy" in text
            and "Research synthesis" in text and "Content authoring" in text
            and "Multi-feature planning" in text), \
        "5-way disambiguation question must list all five modes"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_has_disambiguation_rules -v`

Expected: FAIL.

**Step 3: Replace the "If signals are mixed or absent" block**

In `skills/brainstorming/SKILL.md`, replace the existing block:

Old:
```
**If signals are mixed or absent:** Ask one question: "Is this a
software/technical design or a business/strategy problem?" Once answered,
present the mode explanation block and proceed to Step 2.
```

New:
```
**If signals are mixed or absent:** Apply the disambiguation rules below before asking. If they resolve to one mode, auto-route. Otherwise ask the 5-way question:

> "Which best describes this work: Software design / Business strategy / Research synthesis / Content authoring / Multi-feature planning?"

Once answered, present the mode explanation block and proceed to Step 2.

### Disambiguation Rules

Apply these in order when topic signals overlap multiple modes:

- **Software vs Authoring:** If the deliverable is *code that runs*, Software. If the deliverable is *content humans consume* (curriculum, prompts, exercises) even when there's a code seam, Authoring. The canonical test: a brainstorm with a runtime adapter (code) but 70% content-sequencing work routes to Authoring.
- **Authoring vs Research:** If the deliverable is *an arrangement* (sequence, registry, curriculum), Authoring. If the deliverable is *an evidence map / ranked synthesis* with no arrangement output, Research. Authoring includes Research as an optional sub-phase (file-mediated sub-agent fork — see modes/authoring.md).
- **Business vs Planning:** If the work is *diagnostic* (why isn't X working, what should we do about Y problem), Business. If the work is *generative portfolio sequencing* (which N things should we build, in what order), Planning.

**Disambiguation refusal handling:** If the user picks "Other" or types a free-form answer that doesn't map to any of the 5 modes, ask one follow-up: "Could you describe in one sentence what you want as the deliverable — a design doc, a strategy memo, an evidence map, a sequenced curriculum, or a multi-feature roadmap?" If still ambiguous after the second question, do NOT silent-default. Instead, present an open-text re-prompt: "Describe in your own words what you're trying to produce." Run signal detection on the free-text answer and route to the closest match. If detection still fails, offer a final explicit list (all 5 modes, plus "I'm not sure — let me explore for a few questions first" which routes to Business mode for RCA-shaped exploration since not-knowing-the-shape is itself a diagnostic stance).
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_has_disambiguation_rules -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/SKILL.md
git commit -m "brainstorming: add disambiguation rules and 5-way question"
```

---

### ✅ Task 13: Update SKILL.md Mode Explanation Block (group-by-deliverable)

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (Mode Explanation Block section + the per-mode description lines after it)

**Step 1: Write the failing test**

Append:

```python
def test_skill_md_mode_explanation_block_grouped():
    text = read("skills/brainstorming/SKILL.md")
    # New grouped headers must appear
    for group in ["Build & ship", "Diagnose & decide", "Sequence work"]:
        assert group in text, f"missing group label: {group}"
    # Each mode must have a description line in SKILL.md
    for mode in [
        "Software mode description",
        "Business mode description",
        "Research mode description",
        "Authoring mode description",
        "Planning mode description",
    ]:
        assert mode in text, f"missing mode description: {mode}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_mode_explanation_block_grouped -v`

Expected: FAIL.

**Step 3: Replace Mode Explanation Block + descriptions**

In `skills/brainstorming/SKILL.md`, replace the existing `### Mode Explanation Block (mandatory on every invocation)` section through the line ending in `tactical tasks move faster, strategic challenges get full diagnostic treatment.` (i.e. through the existing Business mode description) with:

```markdown
### Mode Explanation Block (mandatory on every invocation)

After mode selection, present this block before starting any phase work:

> **Brainstorming** — guided dialogue from idea to validated design with expert critique.
>
> **Selected: {Mode Name}** — {one-sentence description of the process}
> *Why:* {brief reason this mode was selected based on topic/environment signals}
>
> **Other modes:**
> - **Build & ship:** Software, Authoring
> - **Diagnose & decide:** Business, Research
> - **Sequence work:** Planning
>
> *To switch modes or skip phases, just say so.*

Grouping is editorial display only — no enum in code. "Build & ship" both produce design docs that feed `/aligned:writing-plans`; "Diagnose & decide" both produce decision artifacts; "Sequence work" is the portfolio outlier.

**Software mode description:** "Fluid Q&A with automatic Architect consultation on technical decisions. Produces a validated design doc."

**Business mode description:** "Structured phases (Goal, Problems, Root Causes, Solutions) with gates. Adapts depth to task complexity — tactical tasks move faster, strategic challenges get full diagnostic treatment."

**Research mode description:** "Corpus survey, comparative synthesis with Skeptic Pass critique, ranked recommendations with caveats. Produces a research memo or KB artifact."

**Authoring mode description:** "Content sequencing with domain-advisor panel; optional Research sub-phase via file-mediated sub-agent fork. Produces a sequenced design doc (curriculum, framework prompts, exercises)."

**Planning mode description:** "Portfolio sequencing with strategy advisors (Christensen, Rumelt, Eric Ries — plus Cagan when available). Produces a roadmap + spawn-list portfolio whose entries seed future brainstorms."
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_mode_explanation_block_grouped -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/SKILL.md
git commit -m "brainstorming: regroup mode-explanation block by deliverable"
```

---

### ✅ Task 14: Add per-mode project-scanner emphasis strings to Step 2

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (Step 2 dispatch prompt — extend mode emphasis text)

**Step 1: Write the failing test**

Append:

```python
def test_skill_md_step2_has_per_mode_emphasis():
    text = read("skills/brainstorming/SKILL.md")
    step2_start = text.index("## Step 2")
    step3_start = text.index("## Step 3")
    step2 = text[step2_start:step3_start]
    # Each mode's emphasis tag should be present in the dispatch prompt template
    for hint in [
        "code artifacts",
        "domain materials",
        "literature/KB/registries",
        "content registries",
        "prior roadmaps",
    ]:
        assert hint in step2, f"missing per-mode emphasis hint: {hint}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_step2_has_per_mode_emphasis -v`

Expected: FAIL — current Step 2 only mentions "code artifacts|domain materials".

**Step 3: Replace the Step 2 dispatch prompt template**

In `skills/brainstorming/SKILL.md`, replace the existing Step 2 dispatch prompt text:

Old:
```
"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`.
Mode: {software|business} — emphasize {code artifacts|domain materials}
accordingly."
```

New:
```
"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`.
Mode: {software|business|research|authoring|planning} — emphasize {emphasis-text}
accordingly."

**Per-mode emphasis text:**

| Mode | `{emphasis-text}` |
|---|---|
| Software | code artifacts (package.json, src/, architecture.md, recent commits) |
| Business | domain materials (positioning, meeting notes, prior strategy, stakeholders) |
| Research | literature/KB/registries (`knowledge/`, `frameworks/registry.yaml`, `advisors/registry.yaml`, prior `*-research.md`) |
| Authoring | content registries + frameworks + prior curricula (`frameworks/`, exercise/lesson registries, `*-design.md` for content work, brand voice files) |
| Planning | prior roadmaps + open kanban + customer asks (`*-roadmap.md`, `*-portfolio.md`, `docs/kanban/`, `clients/*/`) |
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_step2_has_per_mode_emphasis -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/SKILL.md
git commit -m "brainstorming: add per-mode project-scanner emphasis strings"
```

---

### ✅ Task 15: Add SKILL.md Step 3 hand-off branches for new modes

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (Step 3 — append three new branches)

**Step 1: Write the failing test**

Append:

```python
def test_skill_md_step3_has_five_handoff_branches():
    text = read("skills/brainstorming/SKILL.md")
    step3_start = text.index("## Step 3")
    step3 = text[step3_start:]
    # Each mode must have a handoff branch
    for branch in [
        "**If software mode:**",
        "**If business mode:**",
        "**If research mode:**",
        "**If authoring mode:**",
        "**If planning mode:**",
    ]:
        assert branch in step3, f"missing handoff branch: {branch}"
    # Each mode points to its checklist file
    for checklist in [
        "design-critique-checklist.md",
        "business-critique-checklist.md",
        "research-critique-checklist.md",
        "authoring-critique-checklist.md",
        "planning-critique-checklist.md",
    ]:
        assert checklist in step3, f"missing checklist reference: {checklist}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_step3_has_five_handoff_branches -v`

Expected: FAIL.

**Step 3: Append three new hand-off branches to Step 3**

In `skills/brainstorming/SKILL.md`, locate the existing Step 3 block. After the `**If business mode:**` branch (which ends with the orchestration file path) and before `**If the mode file cannot be Read, STOP...**`, insert the three new branches:

```markdown
**If research mode:**
Read `{base-directory}/modes/research.md` and follow its process.
The base directory for this skill is `{base-directory}`.
The critique checklist for this session is at
`{base-directory}/research-critique-checklist.md`.
The shared orchestration file is at
`{base-directory}/../_shared/critique-panel-orchestration.md`.

**If authoring mode:**
Read `{base-directory}/modes/authoring.md` and follow its process.
The base directory for this skill is `{base-directory}`.
The critique checklist for this session is at
`{base-directory}/authoring-critique-checklist.md`.
The shared orchestration file is at
`{base-directory}/../_shared/critique-panel-orchestration.md`.

**If planning mode:**
Read `{base-directory}/modes/planning.md` and follow its process.
The base directory for this skill is `{base-directory}`.
The critique checklist for this session is at
`{base-directory}/planning-critique-checklist.md`.
The shared orchestration file is at
`{base-directory}/../_shared/critique-panel-orchestration.md`.
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_skill_md_step3_has_five_handoff_branches -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/brainstorming/SKILL.md
git commit -m "brainstorming: add Step 3 handoff branches for Research, Authoring, Planning"
```

---

### Task 16: Update kickstart marketing copy

**Files:**
- Modify: `skills/kickstart/SKILL.md` (currently line 169 — "software or business" → 5-mode reference)

**Step 1: Write the failing test**

Append:

```python
def test_kickstart_marketing_copy_mentions_five_modes():
    text = read("skills/kickstart/SKILL.md")
    # The "Run a brainstorm" line must reference five modes (or simply not say "software or business" any more)
    assert "software or business" not in text, "kickstart still uses two-mode marketing copy"
    # The new copy must explicitly reference five modes
    assert "five modes" in text or "5 modes" in text, "kickstart marketing copy should call out 5-mode router"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_kickstart_marketing_copy_mentions_five_modes -v`

Expected: FAIL.

**Step 3: Modify kickstart/SKILL.md**

Edit `skills/kickstart/SKILL.md` and replace the "Run a brainstorm" marketing line. Locate the existing line (currently around line 169):

Old:
```
**Run a brainstorm.** Try `/aligned:brainstorming` with a real problem you're working on. The system auto-detects whether it's a software or business problem and selects relevant advisors for the critique panel.
```

New:
```
**Run a brainstorm.** Try `/aligned:brainstorming` with a real problem you're working on. The router auto-routes across five modes (software, business, research, authoring, planning) and selects relevant advisors for the critique panel.
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_kickstart_marketing_copy_mentions_five_modes -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/kickstart/SKILL.md
git commit -m "kickstart: update marketing copy from two-mode to five-mode router"
```

---

### Task 17: Update critique-panel-orchestration with portfolio-file-path field

**Files:**
- Modify: `skills/_shared/critique-panel-orchestration.md` (line 98 example list update + Configuration Validation section: add optional `portfolio-file-path` field)

**Step 1: Write the failing test**

Append:

```python
def test_orchestration_supports_portfolio_file_path():
    text = read("skills/_shared/critique-panel-orchestration.md")
    # The hardcoded "(e.g., software.md or business.md)" example list should be gone
    # (replaced with mode-agnostic phrasing per design §What changes)
    assert "(e.g., `software.md` or `business.md`)" not in text, \
        "hardcoded mode example list still present"
    # The optional portfolio-file-path field must be documented
    assert "portfolio-file-path" in text, "missing optional portfolio-file-path config field"
    # Must clarify it's optional (Planning-mode only)
    assert "optional" in text.lower(), "portfolio-file-path must be marked optional"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_orchestration_supports_portfolio_file_path -v`

Expected: FAIL.

**Step 3: Edit critique-panel-orchestration.md**

Two edits to `skills/_shared/critique-panel-orchestration.md`:

**Edit 3a:** Replace line 98 (the Handoff section's first numbered item):

Old:
```
1. **Re-read the invoking skill's mode file** — the file you were handed off from (e.g., `software.md` or `business.md`) at `{base-directory}/modes/<mode-name>.md`. The original content has likely been compressed out of context by now. Use the Read tool to load it again.
```

New:
```
1. **Re-read the invoking skill's mode file** — the file you were handed off from at `{base-directory}/modes/<mode-name>.md`. The original content has likely been compressed out of context by now. Use the Read tool to load it again.
```

**Edit 3b:** In the Configuration Validation section (lines 7-21), add a new bullet for the optional Planning-only field. Insert immediately after the `visual-artifacts` bullet:

Old:
```
- `visual-artifacts` must be a path or "none"
- `critique-temp-directory` must be set
```

New:
```
- `visual-artifacts` must be a path or "none"
- `portfolio-file-path` is OPTIONAL — set only by Planning mode for the spawn-list artifact attached alongside `visual-artifacts`. If present, critic prompt templates may reference `{portfolio-file-path}` and instruct critics to read it for spawn-brief-quality assessment. If absent, ignore.
- `critique-temp-directory` must be set
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_orchestration_supports_portfolio_file_path -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py skills/_shared/critique-panel-orchestration.md
git commit -m "orchestration: add optional portfolio-file-path config; drop hardcoded mode list"
```

---

### Task 18: Backward-compat structural test for Software/Business modes

**Files:**
- Modify: `e2e/tests/test_brainstorming_files.py` (append assertions that verify Software and Business modes' contracts remain intact)

**Step 1: Write the test**

The contract from design §Hard constraints + §Mode-detection updates "Behavior-change disclosure": Software and Business modes are unchanged in observable behavior **except** the SKILL.md mode-explanation block's "Other modes" line. Critique-panel config blocks, output paths, temp-dir patterns, and POST-CRITIQUE CHECKLIST step counts must be untouched.

Append to `e2e/tests/test_brainstorming_files.py`:

```python
def test_software_mode_critique_config_unchanged():
    text = read("skills/brainstorming/modes/software.md")
    # Contract: division-of-labor + criteria-assignment yes + design-critique-checklist
    assert "Fact-check mode: division-of-labor" in text
    assert "Criteria assignment: yes" in text
    assert "Checklist filename: design-critique-checklist.md" in text
    # Output path convention preserved
    assert "docs/plans/YYYY-MM-DD-<topic>-design.md" in text
    # Temp dir pattern preserved
    assert "/tmp/brainstorm-context-{topic}" in text
    assert "/tmp/brainstorm-critique-{topic}" in text
    # Post-critique checklist still has 3 mandatory steps
    assert "POST-CRITIQUE CHECKLIST — 3 mandatory steps" in text


def test_business_mode_critique_config_unchanged():
    text = read("skills/brainstorming/modes/business.md")
    assert "Fact-check mode: all-critics" in text
    assert "Criteria assignment: no" in text
    assert "Checklist filename: business-critique-checklist.md" in text
    assert "docs/plans/YYYY-MM-DD-<topic>-design.md" in text
    assert "/tmp/brainstorm-context-{topic}" in text
    assert "/tmp/brainstorm-critique-{topic}" in text
    assert "POST-CRITIQUE CHECKLIST — 3 mandatory steps" in text
```

**Step 2: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_software_mode_critique_config_unchanged e2e/tests/test_brainstorming_files.py::test_business_mode_critique_config_unchanged -v`

Expected: PASS — these are retroactive tests covering existing behavior. The implementation already exists; the tests are guard rails to ensure later tasks don't accidentally regress Software/Business modes.

> Behavior change: this is a **retroactive** test (per writing-plans plan-critique-checklist criterion 4 — Refactoring/Retroactive Tests row). No "verify it fails" step is appropriate; the implementation already exists in `modes/software.md` and `modes/business.md`. Step 2 confirms PASS rather than FAIL.

**Step 3: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py
git commit -m "brainstorming: add backward-compat structural tests for Software/Business modes"
```

---

### Task 19: Authoring → Research happy-path handoff test

**Files:**
- Create: `e2e/tests/test_brainstorming_handoff.py`
- Create: `e2e/fixtures/brainstorming-handoff/research-instrument-review-question.md` (test fixture)
- Create: `e2e/fixtures/brainstorming-handoff/research-instrument-review-synthesis-valid.md` (well-formed synthesis fixture)

**Step 1: Write the failing test**

Create `e2e/tests/test_brainstorming_handoff.py`:

```python
"""Authoring → Research sub-flow contract tests.

The Authoring mode dispatches a sub-agent that follows the contract in
`skills/brainstorming/references/research-mini-protocol.md`. The sub-agent
writes its synthesis to a file with three required headings; Authoring's
validation step gates integration on those headings being present.

These tests exercise the validator (a pure-Python translation of the
validation step in modes/authoring.md) against fixture synthesis files.
"""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "e2e/fixtures/brainstorming-handoff"


def validate_synthesis(text: str) -> tuple[bool, list[str]]:
    """Return (ok, errors) — same rules as the validation step in modes/authoring.md.

    The protocol contract accepts either em-dash (preferred) or regular hyphen
    as the separator between the level and the caveat.
    """
    errors = []
    if "## Synthesis" not in text:
        errors.append("missing ## Synthesis heading")
    if "## Open Questions" not in text:
        errors.append("missing ## Open Questions heading")
    if "## Confidence" not in text:
        errors.append("missing ## Confidence heading")
    else:
        # Confidence line must contain high|medium|low AND a caveat after a separator.
        idx = text.index("## Confidence")
        body = text[idx + len("## Confidence"):].strip()
        first_line = body.splitlines()[0] if body else ""
        if not any(level in first_line.lower() for level in ("high", "medium", "low")):
            errors.append("## Confidence missing high/medium/low level")
        if "—" not in first_line and "-" not in first_line:
            errors.append("## Confidence missing caveat (separator '—' or '-' required)")
    return (not errors, errors)


def test_well_formed_synthesis_passes_validation():
    fixture = FIXTURES / "research-instrument-review-synthesis-valid.md"
    text = fixture.read_text()
    ok, errors = validate_synthesis(text)
    assert ok, f"valid synthesis fixture failed validation: {errors}"


def test_question_fixture_has_question_and_constraints():
    fixture = FIXTURES / "research-instrument-review-question.md"
    text = fixture.read_text()
    assert "## Question" in text or "Question:" in text, "question file must state question"
    assert "## Constraints" in text or "Constraints:" in text, "question file must state constraints"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_handoff.py -v`

Expected: FAIL — fixtures and test file not yet present.

**Step 3: Create fixtures**

Create `e2e/fixtures/brainstorming-handoff/research-instrument-review-question.md`:

```markdown
# Authoring Sub-Flow Question Fixture

## Question
Which validated wellbeing instrument is best for adolescent populations in a
content-led brainstorm targeting an 8-week curriculum?

## Constraints
- Population: adolescents 13-17
- Voice: brand voice file at brand-voice.md
- Hard requirement: validated in at least one peer-reviewed RCT
- Out of scope: instruments with commercial-use licensing burdens
```

Create `e2e/fixtures/brainstorming-handoff/research-instrument-review-synthesis-valid.md`:

```markdown
## Synthesis
Three candidate instruments emerged from the corpus scan: WEMWBS, PERMA-P,
and the Stirling Children's Wellbeing Scale (SCWBS). WEMWBS has the broadest
adult validation but only thin adolescent-specific evidence (citations: Tennant
et al. 2007; Clarke et al. 2011). PERMA-P (Butler & Kern 2016) was developed
for adults and lacks adolescent psychometrics. SCWBS (Liddle & Carter 2010,
2015) is purpose-built for ages 8-15, with two RCTs in school settings.

For the 13-17 audience, SCWBS is closest to construct fit with the
strongest adolescent-specific evidence base. Its licensing model is
non-commercial use free; the validation evidence is RCT-grade.

## Open Questions
- Does SCWBS extend to the upper end of the 13-17 range, or is the validation
  ceiling at age 15?
- Is there a more recent (post-2020) revalidation in non-UK populations?

## Confidence
medium — the SCWBS evidence is solid for ages 8-15 but my reading didn't find
explicit 16-17 validation; a follow-up corpus scan could resolve this.
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_handoff.py -v`

Expected: PASS — both happy-path tests succeed.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_handoff.py e2e/fixtures/brainstorming-handoff/
git commit -m "brainstorming: add Authoring→Research handoff happy-path tests + fixtures"
```

---

### Task 20: Authoring → Research failure-path tests

**Files:**
- Modify: `e2e/tests/test_brainstorming_handoff.py` (append three error-path tests)
- Create: `e2e/fixtures/brainstorming-handoff/research-instrument-review-synthesis-missing-confidence.md`
- Create: `e2e/fixtures/brainstorming-handoff/research-instrument-review-synthesis-no-caveat.md`
- Create: `e2e/fixtures/brainstorming-handoff/research-instrument-review-synthesis-empty.md`

**Step 1: Write the failing tests**

Append to `e2e/tests/test_brainstorming_handoff.py`:

```python
def test_synthesis_missing_confidence_heading_fails_validation():
    fixture = FIXTURES / "research-instrument-review-synthesis-missing-confidence.md"
    text = fixture.read_text()
    ok, errors = validate_synthesis(text)
    assert not ok, "synthesis missing ## Confidence should fail validation"
    assert any("Confidence" in e for e in errors), \
        f"expected error to call out missing Confidence; got: {errors}"


def test_synthesis_confidence_without_caveat_fails_validation():
    fixture = FIXTURES / "research-instrument-review-synthesis-no-caveat.md"
    text = fixture.read_text()
    ok, errors = validate_synthesis(text)
    assert not ok, "synthesis Confidence without caveat should fail validation"
    assert any("caveat" in e.lower() for e in errors), \
        f"expected error to call out missing caveat; got: {errors}"


def test_synthesis_empty_file_fails_validation():
    fixture = FIXTURES / "research-instrument-review-synthesis-empty.md"
    text = fixture.read_text()
    ok, errors = validate_synthesis(text)
    assert not ok, "empty synthesis should fail validation"
    # All three required headings missing
    assert len(errors) >= 3, f"expected ≥3 errors from empty synthesis; got: {errors}"
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest e2e/tests/test_brainstorming_handoff.py -v`

Expected: FAIL — fixtures don't exist yet.

**Step 3: Create the failure fixtures**

Create `e2e/fixtures/brainstorming-handoff/research-instrument-review-synthesis-missing-confidence.md`:

```markdown
## Synthesis
Three candidate instruments emerged from the corpus scan: WEMWBS, PERMA-P,
and the Stirling Children's Wellbeing Scale (SCWBS). For the 13-17 audience,
SCWBS is closest to construct fit.

## Open Questions
- Does SCWBS extend to age 17?
```

Create `e2e/fixtures/brainstorming-handoff/research-instrument-review-synthesis-no-caveat.md`:

```markdown
## Synthesis
SCWBS is the recommended candidate.

## Open Questions
- (none)

## Confidence
medium
```

Create `e2e/fixtures/brainstorming-handoff/research-instrument-review-synthesis-empty.md`:

```markdown
```

(File contains only a single empty line.)

**Step 4: Run tests to verify they pass**

Run: `python -m pytest e2e/tests/test_brainstorming_handoff.py -v`

Expected: PASS — all three failure-path tests confirm the validator catches each malformed shape.

**Step 5: Commit**

```bash
git add e2e/tests/test_brainstorming_handoff.py e2e/fixtures/brainstorming-handoff/
git commit -m "brainstorming: add Authoring→Research failure-path tests"
```

---

### Task 21: Mode-detection eval scenarios fixture

> **Ordering dependency:** This task creates `e2e/fixtures/skill-prompts/brainstorming-five-modes.md` by embedding signal-set prose verbatim from `skills/brainstorming/SKILL.md` Step 1. Tasks 11-12 must be committed FIRST so the embedded prose reflects the new 5-mode signal sets and disambiguation rules. If this task runs before Tasks 11-12 commit, the fixture will embed the stale 2-mode classification block and the eval scenarios will produce false-positive mode classifications.

**Files:**
- Create: `e2e/scenarios/use-skill/brainstorming-five-modes.yaml`
- Create: `e2e/fixtures/skill-prompts/brainstorming-five-modes.md` (system context fixture if not already covered)
- Modify: `e2e/tests/test_brainstorming_files.py` (append fixture-existence assertion)

**Step 1: Write the failing test**

Append:

```python
def test_five_modes_eval_fixture_lists_15_briefs():
    text = read("e2e/scenarios/use-skill/brainstorming-five-modes.yaml")
    # Smoke check: 5 modes × 3 briefs each = 15 test entries
    test_count = text.count("- description:")
    assert test_count >= 15, f"expected ≥15 test briefs in fixture; found {test_count}"
    # Each mode appears as a label
    for mode_label in ["software", "business", "research", "authoring", "planning"]:
        assert mode_label in text.lower(), f"missing mode label: {mode_label}"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_five_modes_eval_fixture_lists_15_briefs -v`

Expected: FAIL.

**Step 3: Create the eval scenarios fixture**

Create `e2e/scenarios/use-skill/brainstorming-five-modes.yaml`. Model on the existing `brainstorming-positioning.yaml` shape (description, providers, prompts template, defaultTest with llm-rubric assertions, tests array). The 15 briefs must cover all 5 modes per design §Tests required:

- *Software (3):* "Add a new API endpoint for sessions list," "Refactor the auth middleware," "Migrate from Drive to DB."
- *Business (3):* "Why is our pilot conversion stuck," "Pricing strategy for tier-2," "Meeting prep for Basis Tuesday."
- *Research (3):* "Compare frameworks for change management," "What's the evidence on PEM-safe pacing protocols," "Rank wellbeing instruments by licensing burden."
- *Authoring (3 — the ambiguity-prone cases):* "Design a 28-step nervous-system program with capacity tiers" (looks Software-ish; is content-led), "Sequence the leadership curriculum across the four forces" (no code seam), "Author 7 micro-practices per framework registry entry" (corpus-led).
- *Planning (3):* "Sequence the next 8 features for the pilot launch," "Roadmap the multi-team quarter ending August," "What should we build before the Basis kickoff."

The llm-rubric assertion block scores each response on whether it correctly classifies the brief into one of the 5 modes (auto-route success) OR offers the 5-way disambiguation question with the correct mode listed first. ≥80% per-brief correctness is the success target (per design §Diagnosis success criterion 3).

```yaml
# e2e/scenarios/use-skill/brainstorming-five-modes.yaml
description: "Skill: brainstorming five-mode classifier"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    config:
      temperature: 0
      max_tokens: 1500

prompts:
  - "{{system_context}}\n\n---\n\nUser brief: {{brief}}\n\nClassify this brief into one of the five brainstorming modes (software, business, research, authoring, planning) OR ask the 5-way disambiguation question if signals are mixed. State which mode you'd auto-route to (or if you'd ask the disambiguation question, list the modes in order from most-likely to least-likely)."

defaultTest:
  assert:
    - type: llm-rubric
      value: |
        Score 1-5 on CLASSIFICATION ACCURACY: Does the response correctly
        identify the expected mode (given in metadata) as the auto-routed
        choice OR as the first-listed option in the disambiguation question?
        Wrong mode = 1. Correct mode mentioned but not first = 3.
        Correct mode auto-routed or listed first = 5.
      weight: 3
    - type: llm-rubric
      value: |
        Score 1-5 on DISAMBIGUATION QUALITY: If the response asks the
        disambiguation question, does it list all five mode names, and is
        the most-likely mode listed first? Missing modes or wrong order = 1.
        All five present, correct first = 5. (If response auto-routes
        instead of asking, score 3 by default — neither penalize nor reward.)
      weight: 1

tests:
  # Software (3)
  - description: "software-1: API endpoint"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Add a new API endpoint for sessions list"
      expected_mode: software
  - description: "software-2: refactor auth middleware"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Refactor the auth middleware"
      expected_mode: software
  - description: "software-3: migrate from Drive to DB"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Migrate from Drive to DB"
      expected_mode: software

  # Business (3)
  - description: "business-1: pilot conversion diagnosis"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Why is our pilot conversion stuck"
      expected_mode: business
  - description: "business-2: pricing strategy"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Pricing strategy for tier-2"
      expected_mode: business
  - description: "business-3: meeting prep"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Meeting prep for Basis Tuesday"
      expected_mode: business

  # Research (3)
  - description: "research-1: framework comparison"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Compare frameworks for change management"
      expected_mode: research
  - description: "research-2: clinical evidence map"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "What's the evidence on PEM-safe pacing protocols"
      expected_mode: research
  - description: "research-3: instrument ranking"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Rank wellbeing instruments by licensing burden"
      expected_mode: research

  # Authoring (3) — ambiguity-prone
  - description: "authoring-1: nervous-system program"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Design a 28-step nervous-system program with capacity tiers"
      expected_mode: authoring
  - description: "authoring-2: leadership curriculum"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Sequence the leadership curriculum across the four forces"
      expected_mode: authoring
  - description: "authoring-3: micro-practice library"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Author 7 micro-practices per framework registry entry"
      expected_mode: authoring

  # Planning (3)
  - description: "planning-1: feature sequencing"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Sequence the next 8 features for the pilot launch"
      expected_mode: planning
  - description: "planning-2: multi-team roadmap"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "Roadmap the multi-team quarter ending August"
      expected_mode: planning
  - description: "planning-3: portfolio sequencing"
    vars:
      system_context: file://../../fixtures/skill-prompts/brainstorming-five-modes.md
      brief: "What should we build before the Basis kickoff"
      expected_mode: planning
```

Create `e2e/fixtures/skill-prompts/brainstorming-five-modes.md`. The system context should embed the five mode names + signal sets + the disambiguation rules from the new SKILL.md so the classifier has the same context the runtime would. Pull verbatim from `skills/brainstorming/SKILL.md` Step 1 (post-Task 11 edits).

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_five_modes_eval_fixture_lists_15_briefs -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add e2e/scenarios/use-skill/brainstorming-five-modes.yaml e2e/fixtures/skill-prompts/brainstorming-five-modes.md e2e/tests/test_brainstorming_files.py
git commit -m "brainstorming: add five-mode classifier eval scenarios fixture"
```

---

### Task 22: Bump plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Write the failing test**

First, ensure `import json` is in the import block at the top of `e2e/tests/test_brainstorming_files.py`. The file's current header is:

```python
"""Structural assertions for the brainstorming three-modes implementation."""
from pathlib import Path
```

Add `import json` immediately after the docstring (before `from pathlib import Path`). Do NOT append `import json` mid-file at the assertion site — keep all imports grouped at the top of the module.

Then append the test function (no inline import):

```python
def test_plugin_version_bumped():
    plugin_json = json.loads(read(".claude-plugin/plugin.json"))
    marketplace_json = json.loads(read(".claude-plugin/marketplace.json"))
    # Both manifests must agree on version (per CLAUDE.md §Version)
    plugin_version = plugin_json["version"]
    marketplace_version = marketplace_json["plugins"][0]["version"]
    assert plugin_version == marketplace_version, \
        f"plugin.json ({plugin_version}) and marketplace.json ({marketplace_version}) disagree"
    # Must be > 0.26.0 (the version on main when this plan was authored)
    def parse(v):
        return tuple(int(x) for x in v.split("."))
    assert parse(plugin_version) > parse("0.26.0"), \
        f"version {plugin_version} not bumped above pre-plan baseline 0.26.0"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_plugin_version_bumped -v`

Expected: FAIL — version still at 0.26.0.

**Step 3: Bump versions**

Edit `.claude-plugin/plugin.json` line 3:

Old: `"version": "0.26.0",`

New: `"version": "0.27.0",`

Edit `.claude-plugin/marketplace.json` line 12:

Old: `      "version": "0.26.0"`

New: `      "version": "0.27.0"`

**Step 4: Run test to verify it passes**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_plugin_version_bumped -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json e2e/tests/test_brainstorming_files.py
git commit -m "chore: bump plugin version to 0.27.0 for brainstorming five-mode router"
```

---

### Task 23: Cagan-absence runtime test

**Files:**
- Modify: `e2e/tests/test_brainstorming_files.py` (append two assertions)

**Step 1: Write the failing test**

Append two assertions to `e2e/tests/test_brainstorming_files.py` covering both Cagan-present and Cagan-absent paths in `modes/planning.md`:

```python
def test_planning_mode_handles_cagan_absence():
    text = read("skills/brainstorming/modes/planning.md")
    # The mode file must do a file-existence check on the Cagan prompt path
    assert "advisors/prompts/marty-cagan.md" in text, \
        "missing Cagan prompt-file existence check"
    # Default panel without Cagan must be explicitly named
    for advisor in ["Christensen", "Rumelt", "Eric Ries"]:
        assert advisor in text, f"default-panel advisor missing: {advisor}"
    # The mode must say absence is handled silently (no surfaced warning)
    # per design §Error paths #5
    assert "silently" in text.lower() or "without surfacing" in text.lower(), \
        "Cagan-absence handling must be silent (no user-facing warning)"


def test_authoring_mode_handles_sisney_absence():
    text = read("skills/brainstorming/modes/authoring.md")
    # Sisney is referenced as PSIU advisor; absence handling must surface once
    assert "advisors/prompts/lex-sisney.md" in text, \
        "missing Sisney prompt-file existence check"
    # Per design §Error paths #5: Authoring notes Sisney absence ONCE for PSIU work
    assert "PSIU" in text or "Four-Forces" in text or "Four Forces" in text, \
        "Authoring must reference PSIU/Four-Forces context for Sisney"
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_planning_mode_handles_cagan_absence e2e/tests/test_brainstorming_files.py::test_authoring_mode_handles_sisney_absence -v`

Expected: PASS — these are retroactive tests covering content that should have been authored in Tasks 7 and 8. If they fail, the assertion is that Tasks 7 or 8 omitted required language; fix the mode file (not the test) before continuing.

> Test type: retroactive (per writing-plans plan-critique-checklist criterion 4 — "Retroactive tests" row). Implementation already exists; the test verifies the contract was honored.

**Step 3: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py
git commit -m "brainstorming: add Cagan/Sisney absence-handling runtime tests"
```

---

### Task 24: Spawn-brief schema runtime test

**Files:**
- Create: `e2e/fixtures/brainstorming-handoff/portfolio-fixture.md`
- Modify: `e2e/tests/test_brainstorming_handoff.py` (append assertions)

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorming_handoff.py`:

```python
def test_portfolio_fixture_entries_match_schema():
    fixture = FIXTURES / "portfolio-fixture.md"
    text = fixture.read_text()
    # Three entries
    entry_count = text.count("## ") - text.count("##  ")  # crude H2 count
    assert entry_count >= 3, f"expected ≥3 portfolio entries; found {entry_count}"
    # Every required field must appear at least 3 times (one per entry)
    for field in [
        "**Target mode:**",
        "**Status:**",
        "**Rough size:**",
        "**Prerequisites:**",
        "**External dependencies:**",
        "**Why now:**",
        "**Spawn brief (one paragraph, brainstorm-ready):**",
        "**Success criterion:**",
    ]:
        count = text.count(field)
        assert count >= 3, f"field {field} appears {count} times; expected ≥3"


def test_portfolio_entry_with_missing_keywords_signals_disambiguation():
    """Per design §Error paths #4: a spawn-brief paragraph that omits
    mode-disambiguating keywords falls through to 5-way disambiguation —
    not silent mis-routing.

    This is a contract test: the fixture's third entry intentionally
    has a generic spawn brief with no mode-disambiguating verbs ('design',
    'sequence', 'compare', 'roadmap'). The test asserts the brief content
    truly lacks those signals; the runtime test of the router behavior
    is part of the eval scenarios (Task 21).
    """
    fixture = FIXTURES / "portfolio-fixture.md"
    text = fixture.read_text()
    # The third entry is the generic-brief case; find it and check
    # its spawn-brief blockquote does NOT contain mode-disambiguating verbs
    third_marker = "## Generic-brief case"
    if third_marker not in text:
        pytest.skip("portfolio fixture missing 'Generic-brief case' entry — see Task 24 spec")
    third_block_start = text.index(third_marker)
    # Extract the spawn-brief blockquote in the third entry
    spawn_idx = text.index("**Spawn brief", third_block_start)
    quote_start = text.index("> ", spawn_idx)
    quote_end = text.index("\n\n", quote_start)
    quote = text[quote_start:quote_end].lower()
    forbidden = ["design", "sequence", "compare", "roadmap", "research", "literature"]
    found = [k for k in forbidden if k in quote]
    assert not found, \
        f"third entry's spawn brief was supposed to be generic; found mode-disambiguating verbs: {found}"
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest e2e/tests/test_brainstorming_handoff.py -v`

Expected: FAIL — fixture does not exist.

**Step 3: Create the portfolio fixture**

Create `e2e/fixtures/brainstorming-handoff/portfolio-fixture.md` with three entries that each match the 8-field schema in `references/spawn-brief-template.md`. The third entry's spawn brief must be intentionally generic (no mode-disambiguating verbs) to exercise the disambiguation-fallback contract:

```markdown
# Sample Portfolio (test fixture)

## Authoring case

**Target mode:** Authoring
**Status:** pending
**Rough size:** weeks
**Prerequisites:** none
**External dependencies:** none
**Why now:** The 28-step nervous-system program is in beta; we need a sequenced curriculum before public launch.
**Spawn brief (one paragraph, brainstorm-ready):**
> Design a 28-step nervous-system program with capacity tiers; sequence the exercises across phases of progressive autonomic load; produce a sequenced curriculum with rationale per slot and an orphan list of exercises that didn't fit.
**Success criterion:** A committed `*-design.md` with 28 ordered slots, each with a populated rationale field.

## Research case

**Target mode:** Research
**Status:** pending
**Rough size:** days
**Prerequisites:** none
**External dependencies:** access to peer-reviewed literature (existing institutional access)
**Why now:** A pricing decision on instrument licenses is gated on this evidence map.
**Spawn brief (one paragraph, brainstorm-ready):**
> Compare wellbeing instruments by validation evidence and licensing burden; produce a ranked evidence map of the 4-6 leading candidates with caveats around adolescent applicability.
**Success criterion:** A committed `*-research.md` memo with a comparison table covering construct fit, evidence grade, licensing model.

## Generic-brief case

**Target mode:** Software
**Status:** pending
**Rough size:** hours
**Prerequisites:** none
**External dependencies:** none
**Why now:** Pilot launch is approaching; this opens a path to a fix.
**Spawn brief (one paragraph, brainstorm-ready):**
> Help me improve the user experience and figure out what to do next about the system overall.
**Success criterion:** Plan ready for implementation.
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest e2e/tests/test_brainstorming_handoff.py -v`

Expected: PASS for both new tests.

**Step 5: Commit**

```bash
git add e2e/fixtures/brainstorming-handoff/portfolio-fixture.md e2e/tests/test_brainstorming_handoff.py
git commit -m "brainstorming: add spawn-brief schema + disambiguation-fallback tests"
```

---

## Manual Steps (Post-Automation)

> Complete these steps manually after all automatable tasks above are committed.

### Skeptic-Pass pilot validation (pre-launch, mandatory for Research mode)

The Architect's prompt has explicit "you do NOT evaluate business strategy" guardrails. The design's §Decision Log entry on Skeptic Pass flags that retargeting Architect at literature/KB evidence is unvalidated under the prompt-injection-overrides-persona convention. Run a real Research-mode brainstorm against an existing artifact to validate the override before launching Research mode.

- [ ] Pilot target: `Documents/Obsidian/aligned/knowledge/change-management/README.md` (existing 8-framework comparative review).
- [ ] Invoke `/aligned:brainstorming` with prompt: "Critique the change-management framework comparison as a Research-mode synthesis." Confirm router auto-routes to Research mode.
- [ ] During the Skeptic Pass phase, observe whether The Architect:
  - (a) Successfully retargets at literature/KB evidence rather than codebase claims.
  - (b) Does NOT trip the "you do NOT evaluate business strategy" guardrail under the Skeptic Pass framing.
  - (c) Surfaces real source-quality issues (citations, evidence gaps, licensing claims).
- [ ] If any of (a)-(c) fail, edit `skills/brainstorming/modes/research.md` to fall back to authoring an inline single-purpose Skeptic role rather than retargeting the Architect. Commit the change to main and re-run pilot.

### Optional advisor add — Marty Cagan (Planning mode upgrade)

- [ ] Run `/aligned:add-advisor "Marty Cagan"` to add Cagan to `advisors/registry.yaml` and create `advisors/prompts/marty-cagan.md`. Domains: discovery, delivery, product-management, opportunity-assessment.
- [ ] Confirm Planning mode picks up Cagan as a panel critic on a real Planning brainstorm. (No code change required — Planning mode reads the registry at dispatch time.)

### Optional advisor add — Lex Sisney (Authoring PSIU work)

- [ ] Run `/aligned:add-advisor "Lex Sisney"` if Authoring brainstorms targeting PSIU/Four-Forces content (e.g., leadership curriculum) are imminent. Hard prereq for PSIU-shaped Authoring; not a blocker for non-PSIU Authoring work.

### Update README skill reference table

- [ ] Verify `README.md`'s skill reference table at the top of the file reflects the brainstorming skill's expanded scope. The skill itself isn't new (so no row addition is required), but the description column should be updated to mention five modes if it currently mentions only software/business.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | TDD shape for markdown-driven skill | Per-file structural pytest assertions | Single shared test file; runtime "smoke" tests only; no tests at all |
| 2 | Where to put plan-manifest YAML | Empty front-matter block | Omit front-matter entirely; embed manifest after header |
| 3 | Plan-test fixture location | `e2e/tests/test_brainstorming_files.py` (append-incrementally) | One pytest file per mode; one pytest file per task |
| 4 | Sub-flow validator implementation | Pure-Python validator translation in test | Shell script; bash regex; full integration test |
| 5 | Eval scenario provider | Same Sonnet-4 setup as `brainstorming-positioning.yaml` | New provider; promptfoo programmatic test; live LLM smoke run |
| 6 | Version bump magnitude | Minor (0.26.0 → 0.27.0) | Patch (0.26.1); major (1.0.0) |
| 7 | Cagan advisor as Prerequisites vs Post-Automation | Post-Automation (optional upgrade) | Prerequisites (gate launch); Inline task within plan |
| 8 | Architect-as-Skeptic retargeting validation | Manual pilot in Post-Automation | Inline pytest mock; defer to runtime; assume guardrail won't fire |
| 9 | Single test file appending vs split modules | Single shared `test_brainstorming_files.py` plus dedicated `test_brainstorming_handoff.py` | Per-artifact files; pytest parametrize across artifacts |
| 10 | Coverage of Cagan-absence + spawn-brief tests | Dedicated Tasks 23 and 24 | Roll into existing tasks; defer to Post-Automation; skip entirely |

### Appendix: Decision Details

#### Decision 1: TDD shape for markdown-driven skill
**Chose:** Per-file structural pytest assertions verifying file existence + required headings/content.
**Why:** The brainstorming skill is markdown-driven; "tests" in the conventional unit-test sense don't apply. The design doc explicitly calls out "eval-style and structural" tests. Pytest gives a uniform runner, integrates with CI, and forces each task to author a verifiable contract before creating the artifact. The alternative — runtime smoke tests via the Claude harness — is high-cost (requires a real model invocation) and slow. No-tests is rejected because the project's CLAUDE.md mandates TDD.
**Alternatives rejected:**
- *Single shared test file:* Rejected because creating per-task ordering dependencies inside one file complicates parallel work; the chosen approach (incremental append to one file) keeps the file count low while preserving order.
- *Runtime smoke tests only:* Rejected because they require a live LLM call per task, which is slow, costly, and flakey — fail-loud structural checks catch 90% of the regressions at near-zero cost.
- *No tests:* Rejected per project TDD policy.

#### Decision 2: Where to put plan-manifest YAML
**Chose:** Empty YAML front-matter block (`---\n---\n`) at the top of this plan.
**Why:** Per `skills/_shared/plan-manifest-format.md`, an empty manifest is intentional — it signals "author confirmed no env requirements" rather than "no manifest, skip preflight." This plan is markdown editing only — no MCP tool dispatches, no `process.env` references, no shell `${VAR}` references. The autopilot's preflight step will exit cleanly with "manifest present, nothing to check."
**Alternatives rejected:**
- *Omit front-matter:* Would cause preflight to return "no manifest, skip" — looks the same in practice but loses the explicit "author confirmed" signal.
- *Embed manifest after header:* Violates the format spec (must be at file head between `---` markers).

#### Decision 3: Plan-test fixture location
**Chose:** Single `e2e/tests/test_brainstorming_files.py` extended incrementally per task; separate `e2e/tests/test_brainstorming_handoff.py` for the more complex sub-flow validator + fixtures.
**Why:** Per project pattern (e.g., `e2e/tests/test_manual_deploy_catalog.py` in catalog-integrity), one pytest file per concern is conventional. The structural tests for files share boilerplate (the `read()` helper); putting them together keeps the helper DRY. The handoff tests use file fixtures and a Python validator — splitting them out keeps imports clean. Per-artifact splitting (one file per mode) was rejected as over-fragmentation for ~10 small assertions.
**Alternatives rejected:**
- *One pytest file per mode/checklist/template:* 8+ test files for what amounts to file-existence checks; defeats DRY.
- *One pytest file per task:* Same problem as per-mode plus index-creep as task count grows.

#### Decision 4: Sub-flow validator implementation
**Chose:** Pure-Python translation of the `modes/authoring.md` validation step, inside `test_brainstorming_handoff.py`.
**Why:** The validator's logic — "presence of three headings; Confidence-line has level + caveat" — is straightforward string analysis. A pure-Python validator that mirrors the prose contract is testable in CI without spinning up the brainstorming runtime. The pytest test exercises it against fixture files. If the prose contract drifts from the validator, future tests will surface the gap.
**Alternatives rejected:**
- *Shell script:* Less testable; harder to integrate with pytest assertion idioms.
- *Full integration test (real Claude dispatch):* Slow, costly, flakey. Reserve for the manual Skeptic-Pass pilot which already exists in Post-Automation.

#### Decision 5: Eval scenario provider
**Chose:** Same provider/model setup as the existing `brainstorming-positioning.yaml` (Sonnet 4, temperature 0).
**Why:** Consistency with existing eval infrastructure makes results comparable across scenarios and lets the eval CLI run all brainstorming evals in one batch. Sonnet 4 is the production routing model for skill invocations; testing the classifier on a smaller model would risk false negatives that don't reproduce in real use.
**Alternatives rejected:**
- *New provider/model:* Adds maintenance burden without benefit.
- *Programmatic test instead of llm-rubric:* The classification is open-ended (auto-route OR ask disambiguation) — rule-based scoring would fail on legitimate disambiguation responses.

#### Decision 6: Version bump magnitude
**Chose:** Minor bump 0.26.0 → 0.27.0.
**Why:** This is a feature addition (3 new modes, signal-set expansion, mode-explanation-block format change) that is observably new behavior to plugin users. Pre-1.0 semver convention treats minor bumps as feature additions. The mode-explanation-block change is a small cosmetic surface change, not breaking — Software/Business modes' core observable behavior (process, output, advisor pool, critique config) is unchanged.
**Alternatives rejected:**
- *Patch bump (0.26.1):* Underclaims the surface change; users browsing changelogs would miss the new modes.
- *Major bump (1.0.0):* Pre-1.0 status implies the project hasn't reached API stability; a 1.0 bump signals commitment we're not ready to make.

#### Decision 7: Cagan advisor as Prerequisites vs Post-Automation
**Chose:** Post-Automation (optional upgrade).
**Why:** Per design Decision Log entry #4 (verbatim): "Cagan as preferred-when-available, not load-bearing. Default launch panel = Christensen + Rumelt + Eric Ries." All three are in the registry. Planning mode is launch-ready without Cagan. Adding Cagan is a panel upgrade that does not block any task in this plan. Putting it in Prerequisites would force the user to perform an `/aligned:add-advisor` call before plan execution — autonomy violation per the writing-plans Manual Steps Policy.
**Alternatives rejected:**
- *Prerequisites (gate launch):* Contradicts design's explicit "preferred when available" decision.
- *Inline task within plan:* `/aligned:add-advisor` is interactive — Ralph loop can't drive it cleanly.

#### Decision 8: Architect-as-Skeptic retargeting validation
**Chose:** Ship Research mode with the inline single-purpose Skeptic role as the default committed path. Document Architect-retargeting as an upgrade path inside `modes/research.md`, gated on the Skeptic-Pass pilot in Manual Steps. The pilot validates whether Architect's persona guardrails fire under retargeting; if it passes, edit the mode file to extend the Skeptic Pass critic pool.
**Why:** The Round 1 Architect critic flagged that committing the unvalidated Architect-retargeting path creates a commit-hygiene problem — if the pilot fails, the fix is a post-commit edit rather than a clean ship. Inverting the default (inline Skeptic ships, Architect-retargeting is the upgrade) eliminates that risk while preserving the design's intent: the design's Decision Log hedge already specified inline-Skeptic as the fall-back, so making it the day-zero default just reorders the rollout. The pilot still runs; it just unlocks an upgrade rather than confirming a default.
**Alternatives rejected:**
- *Original plan (Architect-retargeting default + pilot validates):* Rejected after Round 1 critique — commits a path that may not work, then requires post-commit cleanup if the pilot fails.
- *Skip the Skeptic Pass entirely until pilot:* Rejected — Research mode without Skeptic Pass loses its core value (cutting-fluff source-quality skepticism); shipping with the inline role preserves the value at day zero.
- *Inline pytest mock for the guardrail:* Cannot mock the Architect's response convincingly; failure mode is whether real prompt-injection works at runtime.

#### Decision 9: Single test file appending vs split modules
**Chose:** Single shared `test_brainstorming_files.py` (file-structure assertions, ~12 tests) + dedicated `test_brainstorming_handoff.py` (sub-flow validator + 4 tests + 4 fixtures).
**Why:** The structural assertions all share the `REPO_ROOT` and `read()` helper — duplicating across 8+ files would violate DRY. The handoff tests have a meaningful validator function that's worth isolating. Two files is the right granularity; per-task files would create indexing noise without readability gain.
**Alternatives rejected:**
- *One file per task:* Index sprawl; helper duplication.
- *One file per artifact (mode/checklist/template):* Same problem.
- *Pytest parametrize over a manifest:* Harder to read; obscures which mode each test is asserting against.

#### Decision 10: Coverage of Cagan-absence + spawn-brief tests
**Chose:** Dedicated Tasks 23 and 24 covering the design's `§Tests required` items that Round 1 flagged as missing — Cagan-absence runtime test, Sisney-absence runtime test, and spawn-brief schema test (with disambiguation-fallback contract).
**Why:** The Verifier critic flagged three design-required tests with no plan task. Rather than rolling them into existing tasks (which would bloat already-long Tasks 7, 8, and 19), dedicated tasks keep each task focused on one coherent commit. Tasks 23 and 24 are retroactive (the implementation in Tasks 7-8 must already provide the content tested) — this is the conventional shape for "verify the contract was honored" tests in markdown-driven skills.
**Alternatives rejected:**
- *Roll into existing tasks:* Tasks 7, 8 and 19 already span 100+ lines each; adding more assertions makes them harder to review and execute.
- *Defer to Post-Automation:* These tests are automatable; Post-Automation is reserved for genuinely manual work (the Skeptic-Pass pilot).
- *Skip entirely:* Violates the design's explicit `§Tests required` enumeration.
