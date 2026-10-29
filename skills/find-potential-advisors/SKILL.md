---
name: find-potential-advisors
description: "Use when exploring a new domain for the Virtual Board, looking for real experts to model as advisors, or before running add-advisor on someone not yet chosen."
---

# Find Potential Advisors

Finds real experts for a domain, counts how much of their own material is public, and
recommends 2 or 3 finalists to turn into advisors with `/aligned:add-advisor`. Works for any
domain: trauma, leadership, design, growth, medicine, negotiation.

**Output:** one brief file, filled in from `report-template.md`, and a short summary in chat.

## The core rule

**Each phase is done by different agents, and every count and quote in the report has a URL.**

- The agent that picks a candidate is the worst one to grade them. So candidates are profiled
  by one agent and evaluated by another, which gets their names and nothing else.
- Search snippets are wrong often enough to matter. In one run, two snippets gave episode
  lengths that were 15 and 20 minutes off from the episode pages. Only opened pages count.
- A report from memory looks just like a researched one unless it shows its sources. So the
  report shows every URL, every sum, and what was skipped.

Eight runs in a row merged these phases and guessed the ratings. `anti-examples.md` shows how.
`examples.md` shows what the evidence should look like.

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line
> printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the
> parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}`
> as `<plugin-root>/skills/find-potential-advisors/`. See `skills/_shared/resolve-skill-path.md`.

## Invocation

```
/aligned:find-potential-advisors                          # interview first
/aligned:find-potential-advisors docs/plans/my-brief.md   # use an existing brief
```

## Phase 1: Interview

The main session does this part. The brief it produces is the Brief section of
`report-template.md`.

If a brief path was given, read it and check every field in the template's Brief section.
Ask only for the fields that are missing.

Otherwise, go through these one at a time. Skip a question when you're highly confident of the
answer from what the user said or from files you've read. Don't skip one by guessing. Ask the
ones you can't answer with confidence.

1. What domain should this advisor cover?
2. Who will use the advisor, and what situation are they in?
3. Any contexts, groups of people or uses the research should focus on? (optional)
4. Any preference for the kind of approach, or should the research decide? (optional)
5. Anything else: cultural context, safety concerns, outcomes? (optional)
6. **Overlaps.** Read `skills/_shared/resolve-advisor-source.md` and follow it to get the
   merged advisor list. Find the advisors whose domains are near this one. Always do this
   lookup, even when you skip the question.
   - If the user already said which advisors to stay away from, or it's clear (for example,
     no one nearby), don't ask. Write your assumption in the brief and say it in one line when
     the search starts, so the user can correct it.
   - If there are nearby advisors and you can't tell which the user wants kept separate, name
     them, one line each, and ask: "Which of these should the new advisor stay away from, and
     is there anyone else?"
7. How many candidates? (default 10)

Then write the brief to `docs/plans/YYYY-MM-DD-find-advisor-<domain>-brief.md`. Include a
hypothetical situation for the voice samples and 3 to 5 research questions. Write both
yourself from the interview.

## Phases 2 to 6: Run the workflow

If the Workflow tool is available in this session, call it:

- `scriptPath`: `{base-directory}/workflow.js`
- `args`:
  - `brief_path`: the brief's absolute path
  - `skill_dir`: `{base-directory}`
  - `research_questions`: the questions from the brief
  - `candidate_count`: the number from the brief
  - `exclude`: every advisor named under "Advisors already on the board nearby", plus anyone
    else the user named

The script runs each phase with its own agents:
1. One research agent per question.
2. One agent picks the candidates.
3. Profile agents take 3 candidates each. A different agent then evaluates each group.
4. The script works out each rating from the counted items that have URLs.
5. One agent picks the finalists.
6. One agent writes the brief.
7. A fresh agent checks the brief, with one round of fixes.

With 10 candidates and 4 questions, that's about 16 agents.

It runs in the background. Tell the user in one or two sentences that it has started and
roughly how many agents it will use. Then carry on. If this skill was started from inside
another task, go back to that task while the workflow runs.

When the workflow finishes, read its result:

- **`done`:** read the brief. Give the user its Chat summary section. If `problems` isn't empty,
  add each problem to the "What was skipped or not verified" list you show.
- **`too_few`:** fewer than 2 candidates rated High or Medium. Show the Chat summary, then ask
  which to do: widen the search, lower the bar, or go ahead with the best candidate.
- **`failed`:** say which step failed, from `skipped`. Offer to rerun with `resumeFromRunId`, so
  the finished agents aren't paid for twice.

## If the Workflow tool is not available

Run the same agents with the Agent tool. Every agent gets this line, then its inputs:
`Read {base-directory}/agent-prompts.md, the section "## <Section>", and follow it.`

Make a task list with one item per agent below. Check each item off when its agent returns.

1. **Research.** One agent per research question, all at once. Give each one the brief path and
   its question. Wait for all of them.
2. **Candidates.** One agent. Give it the brief path, the candidate count, the names to leave
   out, and all the research results.
3. **Profile, then evaluate.** Split the candidates into groups of 3. For each group, start a
   Profile agent. When it returns, start an Evaluate agent for the same names. The evaluator
   must be a different agent, and it gets the names only.
4. **Ratings.** Work out each rating yourself with the rubric under Evaluation in
   `report-template.md`. Count only items with URLs. Show the minutes and their sum.
5. **Too few?** If fewer than 2 candidates are High or Medium, start a Write agent for the
   sections up to Evaluation. Then stop and give the user the three choices.
6. **Finalists.** One agent. Give it the strong candidates, ranked, with their profiles and
   evaluations.
7. **Write.** One agent. Give it all the results as JSON.
8. **Check.** A fresh agent with the brief path. If it finds problems, start a Fix agent, then a
   second Check agent.

Then report the result the same way as in the workflow section above.

## Phase 7: The user picks

Give the user the brief's Chat summary. It has the recommendation, the finalists with their
counts, who was left out, **What was skipped or not verified**, the brief's path, and the
question of which to add.

When they pick, write the choice into the brief. Then tell them the next step is
`/aligned:add-advisor <name>` with the brief as its research file.

## Red flags

If you catch yourself thinking any of these, stop and run the step as written:

| Thought | What's true |
|---------|-------------|
| "I'll merge research and candidate-finding into one agent to save time." | The agent that finds a candidate then grades them. That's how eight runs went wrong. |
| "The search snippet gives the episode length." | Snippets were off by 15 and 20 minutes from the pages. Open the page. |
| "I know he did that project, from memory." | It goes in "What was skipped or not verified," not in the recommendation. |
| "Four books and lots of talks. Clearly High." | High needs 5 counted hours with URLs. Count them. |
| "I'll guess which advisors to steer clear of." | If you can't tell, ask question 6. If you can, write the assumption in the brief and say it. |
| "I'll write the voice sample myself." | Build it from real quotes with URLs. |
| "The report looks fine, so I'll skip the check." | The check is how you find out. Run it. |
| "This is a side task. I'll keep it small." | The user builds an advisor on it. Run the workflow and go back to the main task. |
| "Nothing was skipped, so I'll leave that section out." | Write "Nothing." Leaving it out reads as hiding it. |

## Files

- `workflow.js`: the Workflow script for Phases 2 to 6.
- `agent-prompts.md`: instructions for each agent. The script and the fallback both use it.
- `report-template.md`: the brief's sections, the rating rubric, and the Chat summary shape.
- `examples.md`: evidence done right, from a real run.
- `anti-examples.md`: the ways real runs went wrong.
