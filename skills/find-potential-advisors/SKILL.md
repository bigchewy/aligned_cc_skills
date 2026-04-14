---
name: find-potential-advisors
description: Research and evaluate potential advisors for the Virtual Board. Use this skill when you need to identify experts in a domain, evaluate their voice mimicry potential, and narrow to top candidates. Predecessor to add-advisor skill.
---

# Find Potential Advisors

A research skill that helps identify and evaluate potential advisors for the Virtual Board. Works for any domain: trauma, leadership, negotiation, creativity, productivity, relationships, etc.

**Input:** A brief document (created through interview or provided directly)
**Output:** Research findings, candidate list, evaluation matrix, and 2-3 finalists for user selection
**Relationship:** Predecessor to `/aligned:add-advisor`

## Invocation

```
/aligned:find-potential-advisors                           # Start interview to create brief
/aligned:find-potential-advisors docs/plans/my-brief.md   # Use existing brief, skip to Phase 2
```

If a brief path is provided as an argument, validate it contains required fields and proceed directly to Phase 2 (Research).

## Phase 1: Interview (or Brief Intake)

If no brief path provided, conduct an interview to create one. Ask questions one at a time:

1. **Domain/Focus Area**
   - "What domain or focus area should this advisor cover?"

2. **Target Users**
   - "Who will use this advisor and what situation are they facing?"

3. **Specific Research Angles** (optional)
   - "Are there specific contexts, populations, or applications the research should focus on?"

4. **Modality Preferences** (optional)
   - "Do you have preferences for the type of approach, or should research guide this?"

5. **Additional Considerations** (optional, open-ended)
   - "Any other requirements? (e.g., cultural context, safety concerns, specific outcomes)"

6. **Differentiation Check** (automatic)
   - Read the project's CLAUDE.md or advisor registry to check for existing advisors in this domain. Resolve the registry by checking for `registry.yaml` first, then `registry.md`, then globbing `advisors/prompts/*.md`.
   - Present: "Current advisors in related areas: [list]. The new advisor should be distinct."
   - Ask: "Any specific overlaps to avoid?"

7. **Candidate Count** (optional, defaults to 10)
   - "How many initial candidates should I research?"

**Interview Flexibility:** Skip questions whose answers are already clear from context. If the user provides a pre-written brief, validate it has required fields and proceed to research.

**Output:** Brief document saved to `docs/plans/YYYY-MM-DD-find-advisor-<domain>-brief.md`

## Phase 2: Research Modalities

Research what approaches are most effective for the domain.

**Process:**
1. Conduct 3-5 web searches per research question using `WebSearch` and `WebFetch` tools (never `Bash(curl)` — it creates stale permission entries)
2. Prioritize systematic reviews and meta-analyses
3. Stop when findings start repeating
4. Include any specialized angles from the brief

**Document:**
- What modalities/frameworks have best evidence?
- What approaches are specifically effective for the target users?
- Any emerging or specialized approaches?
- Sources cited

**Output:** Research section added to brief document.

## Phase 3: Identify Candidates

Based on research, identify candidates (per brief, default 10) who:
- Are recognized experts in effective modalities
- Have substantial public presence
- Have a distinctive voice/approach

**For each candidate, document:**
- Name and credentials
- Primary modality/approach
- Key works (books, frameworks, talks)
- Why they might fit this need

**Output:** Candidates section added to brief document.

## Execution Strategy: Sub-Agents

Phases 2-4 involve significant research. Use sub-agents to parallelize:

**Phase 2 (Research):** Spawn one sub-agent per research question. Each agent conducts 3-5 web searches using `WebSearch` and `WebFetch` tools (never `Bash(curl)`) and returns findings. Consolidate results into the brief.

**Phase 3 (Candidates):** After research identifies key modalities, spawn sub-agents to research 2-3 candidates each in parallel. Each agent returns a candidate profile.

**Phase 4 (Evaluation):** Spawn sub-agents to evaluate 2-3 candidates each for voice mimicry potential. Each agent assesses public material availability and returns a rating.

This parallelization keeps the main session focused on coordination while sub-agents handle deep research.

## Phase 4: Evaluate Voice Mimicry Potential

Assess each candidate's public material availability.

**Evaluation Criteria:**

| Rating | Criteria |
|--------|----------|
| High | 2+ books AND 5+ hours video/audio AND distinctive terminology |
| Medium | 1 book OR 2+ hours content, identifiable style |
| Low | Limited material or generic communication style |

**For each candidate, assess:**
- Written works (books, articles, transcripts)
- Spoken content (talks, podcasts, interviews)
- Distinctive voice markers (phrases, style, signature concepts)
- Accessibility (freely available vs. paywalled)

**Checkpoint:** If fewer than 2 candidates score High or Medium, report to user. Options: expand search criteria, lower threshold, or proceed with limited options.

**Output:** Evaluation matrix added to brief document.

## Phase 5: Narrow to Finalists

Select top 2-3 candidates. For each:

1. **Summary Profile** - Who they are and their approach

2. **Differentiation Analysis** - How they differ from existing advisors

3. **Framework Potential** - What frameworks could be built; how they differ from existing ones

4. **Voice Sample** - Brief example response to a hypothetical user situation relevant to the domain

5. **Trade-offs** - Pros and cons compared to other finalists

**Include:** Claude's recommended choice with reasoning.

**Output:** Finalists section added to brief document.

## Phase 6: User Selection

Present finalists with:
- Comparison summary
- Claude's recommendation
- Request user selection

Once selected:
- Document choice in brief
- Prompt: "Ready to implement? Run `/aligned:add-advisor` to create this advisor."

## Document Structure Options

**Option A: Single Document** (default)
All phases append to one brief.md file with clear section headers.

**Option B: Folder Structure** (for complex searches)
```
docs/plans/find-advisor-<domain>-YYYY-MM-DD/
├── 01-brief.md
├── 02-research.md
├── 03-candidates.md
├── 04-evaluation.md
└── 05-finalists.md
```

Use Option A unless the user requests Option B or the document exceeds reasonable length.
