# Prompt: Skill Eval Redesign

> Copy the text below and paste it as your first message in a new Claude Code session, opened in the `aligned_cc_skills` repo.

---

## What I need

Design and implement eval scenarios that test whether our Aligned plugin **skills** produce measurably better results than prompting Claude directly. The core question: "By invoking the brainstorming skill, do I get a better outcome than just asking Claude the same question without the skill?"

## Background

We have a working Promptfoo eval framework in `e2e/` that already tests **advisors** (persona prompts) and **frameworks** (methodology prompts) with a 3-way comparison: full-stack vs. vanilla vs. aware-but-unaided. Those scenarios are working and validated — don't touch them.

But skills are fundamentally different from advisors and frameworks. A skill like `brainstorming` isn't a system prompt swap — it's a multi-step interactive workflow (mode detection, project scan, structured phases with gates). The value is in the *process*, not a single prompt/response pair.

## Read these files first

Current eval infrastructure:
- `e2e/README.md` — framework overview and pass/fail thresholds
- `e2e/promptfooconfig.yaml` — master config
- `e2e/scenarios/use-advisor/april-dunford-blog-critique.yaml` — working example of the paired comparison pattern (study this structure — it's the validated approach)
- `e2e/eval-surface.yaml` — glob patterns defining LLM behavior surface
- `e2e/trigger-map.yaml` — maps changed files to eval scenarios
- `e2e/fixtures/company-briefs/b2b-saas-startup.md` — existing fixture

The brainstorming skill:
- `skills/brainstorming/SKILL.md` — entry point (mode detection, project scan dispatch)
- `skills/brainstorming/modes/business.md` — business mode process (Goal → Problems → Root Causes → Solutions)
- `skills/brainstorming/modes/software.md` — software mode process
- `skills/brainstorming/business-critique-checklist.md` — critique checklist

## Task 1: Research best practices

Before designing anything, launch at least one sub-agent to research how other teams evaluate multi-step LLM workflows. We need concrete findings on:

- **Promptfoo capabilities:** Does Promptfoo support multi-turn, agentic, or script-based eval scenarios? Can we use custom providers or script providers to simulate a skill workflow in a single eval run?
- **Industry approaches:** How do frameworks like LangChain, CrewAI, LangSmith, or Braintrust evaluate whether structured orchestration adds value over a single prompt? What patterns exist for "process quality" evaluation?
- **Rubric design for process outputs:** What dimensions matter when evaluating structured/phased outputs vs. unstructured responses? (e.g., structural completeness, diagnostic depth, framework adherence)
- **Build vs. buy decision:** Can Promptfoo handle skill evaluation with existing features, or do we need a lightweight custom test harness?

The sub-agent should search the web and return concrete findings with source URLs — not vague summaries. This research informs everything else.

## Task 2: Design and build a brainstorming skill eval scenario

Based on the research, design an eval scenario for the brainstorming skill (business mode). The comparison:

| Comparison point | What Claude gets | User prompt |
|---|---|---|
| **Without skill** | No context | "Help me develop a positioning strategy for this company: {company_brief}" |
| **With skill** | Brainstorming SKILL.md + business mode instructions embedded in prompt | Same user prompt |

The "with skill" version should include enough of the skill's instructions (from SKILL.md and modes/business.md) that Claude follows the structured brainstorming process in a single response. This is a simplification of the interactive workflow, but it tests whether the skill's structure produces better output.

Rubric dimensions for skills should measure **process quality**, not just content:
- **Structural completeness:** Did the response follow a recognizable structured process (phases, steps, frameworks)?
- **Diagnostic depth:** Did it identify root causes and non-obvious problems, or stay surface-level?
- **Solution specificity:** Are recommendations grounded in the company's specific situation?
- **Actionability:** Could someone execute on the output immediately?
- **Framework application:** Did it apply relevant business frameworks correctly (not hallucinated)?

Deliverables:
1. Scenario YAML at `e2e/scenarios/use-skill/brainstorming-positioning.yaml`
2. Update `e2e/trigger-map.yaml` to map `skills/brainstorming/SKILL.md` and `skills/brainstorming/modes/business.md` to this scenario
3. Update `e2e/eval-surface.yaml` to include `skills/brainstorming/modes/business.md` if it's not already there

## Task 3: Run and validate

Run the new brainstorming scenario with `--no-cache` and verify:
1. Both tests produce substantive output (not empty/confused responses)
2. The with-skill version scores higher than without-skill on the process quality rubrics
3. If it doesn't score higher, document what happened — that's valuable data about the skill's actual value

Then run all scenarios together via `npx promptfoo eval` to verify nothing is broken.

The `.env` file in `e2e/` has the `ANTHROPIC_API_KEY`.

## Critical constraints (learned the hard way)

- **file:// in vars resolves for prompt templates but NOT for provider config (systemMessage).** Put system context in a `{{system_context}}` prompt var, not in the provider. See the advisor scenario for the working pattern.
- **`tests.vars` works; `config` + separate `tests` does NOT.** Promptfoo ignores `config:` as a top-level key when running with `-c`.
- **Use `--no-cache` when re-running after structural changes.** Promptfoo aggressively caches.
- **One provider, one prompt template, multiple test entries.** Each test sets different vars for `system_context`, `task_prompt`, and input content. This avoids the cross-product problem.
- **Follow the repo's portability rule:** Guard on file existence, don't assume paths exist. This is a distributed plugin.
