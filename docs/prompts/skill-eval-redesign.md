# Prompt: Skill Eval Redesign

> Run this in a separate Claude Code session in the aligned_cc_skills repo.

## Context

We have a Promptfoo eval framework in `e2e/` that tests whether our Aligned plugin produces better results than prompting an LLM directly. The framework was built yesterday and works for **advisors** (persona prompts like April Dunford) and **frameworks** (structured methodology prompts like 5 Components of Positioning).

The current eval scenarios have a design bug: they define 3 providers and 3 prompts as independent Promptfoo lists, which creates a 3x3 cross-product of 9 test combos. Only 3 are meaningful — the other 6 are noise (e.g., curated system prompt paired with vanilla user prompt). This needs to be fixed.

More importantly, the eval framework doesn't yet handle **skills** — which are the most important thing to evaluate. Skills aren't system prompts. A skill like `brainstorming` is a multi-step interactive workflow (mode detection, project scan, structured phases). The value isn't in a single prompt swap — it's in the process the skill guides the user through.

The question we need to answer: **"By invoking the brainstorming skill (or any skill), do I get a measurably better result than just asking Claude the same question without the skill?"**

## What exists today

Read these files to understand the current state:
- `e2e/README.md` — eval framework overview, three-provider comparison model, pass/fail thresholds
- `e2e/promptfooconfig.yaml` — master config aggregating scenarios
- `e2e/scenarios/use-advisor/april-dunford-blog-critique.yaml` — example advisor scenario
- `e2e/scenarios/use-framework/5-components-positioning.yaml` — example framework scenario
- `e2e/scenarios/persona-panel/pricing-page.yaml` — example skill scenario (persona-panel)
- `e2e/eval-surface.yaml` — glob patterns defining LLM behavior surface
- `e2e/trigger-map.yaml` — maps changed files to eval scenarios
- `e2e/fixtures/company-briefs/b2b-saas-startup.md` — example fixture (DataForge)
- `skills/brainstorming/SKILL.md` — the brainstorming skill entry point
- `skills/brainstorming/modes/business.md` — business mode process
- `skills/brainstorming/modes/software.md` — software mode process

## Task 1: Research best practices

Before designing anything, launch at least one sub-agent to research how other teams evaluate multi-step LLM workflows (not just single-turn prompt comparisons). We need to understand best practices for:

- Evaluating structured/agentic LLM workflows vs. single-turn prompts
- Whether Promptfoo supports multi-turn or agentic eval scenarios, or if we need a different approach
- How other skill/agent frameworks (like LangChain, CrewAI, AutoGen) evaluate whether their orchestration adds value over a single prompt
- What rubric dimensions are most meaningful for process-oriented outputs (not just content quality)

The sub-agent should return concrete findings, not vague summaries. We need to make a build-vs-buy decision: can Promptfoo handle skill evaluation with its existing features (script providers, custom providers, etc.), or do we need a lightweight custom harness?

## Task 2: Fix the cross-product problem in existing scenarios

The 3 existing scenarios (`use-advisor`, `use-framework`, `persona-panel`) each define 3 providers and 3 prompts independently. Promptfoo cross-products them into 9 combos, but only 3 are meaningful:

| Comparison point | System prompt | User prompt |
|---|---|---|
| Vanilla baseline | "You are a helpful assistant." | Plain task ask (no expert/framework named) |
| Aware but unaided | None | Task ask that names the expert/framework |
| Full stack | Curated advisor/framework prompt | Plain task ask |

Restructure each scenario so only these 3 paired combos run. No cross-product. Use Promptfoo's `scenarios` list or `tests` with per-test provider overrides — whatever structure avoids the cross-product while keeping the same assertions and rubrics.

After restructuring, run each scenario individually with `--no-cache` to verify:
1. All 3 tests produce substantive LLM output (not "I don't see the content")
2. The full-stack provider scores higher than vanilla on the weighted rubrics
3. Results appear in `npx promptfoo view`

The `.env` file in `e2e/` has the `ANTHROPIC_API_KEY`.

## Task 3: Design a skill eval scenario for brainstorming

Based on the research findings, design an eval scenario that tests the brainstorming skill (business mode). The comparison should be:

| Comparison point | What Claude gets | User prompt |
|---|---|---|
| Without skill | No system prompt | "Help me develop a positioning strategy for this company: {company_brief}" |
| With skill | The brainstorming SKILL.md + business mode instructions as system prompt | Same user prompt |

The key question: a skill's value is in the structured process it drives. The "with skill" system prompt should include enough of the skill's instructions that Claude follows the brainstorming process in a single response (even though in real usage it's interactive). This is a simplification, but it tests whether the skill's structure produces better output than an unstructured response.

Rubric dimensions for skills should measure process quality, not just content:
- **Structural completeness:** Did the response follow a recognizable structured process (phases, steps, frameworks)?
- **Diagnostic depth:** Did it identify root causes and non-obvious problems, or stay surface-level?
- **Solution specificity:** Are recommendations grounded in the company's specific situation?
- **Actionability:** Could someone execute on the output immediately?
- **Framework application:** Did it apply relevant business frameworks correctly (not hallucinated)?

Create the fixture, scenario YAML, and update `trigger-map.yaml` and `eval-surface.yaml` to include `skills/brainstorming/SKILL.md` and `skills/brainstorming/modes/business.md`.

## Task 4: Run and validate

Run all scenarios (old and new) and verify the full-stack provider consistently outscores vanilla. If it doesn't, that's important data — document what happened and why.

## Constraints

- All file:// paths in scenarios resolve relative to the scenario file location, not CWD
- The `tests.vars` structure works; the `config` + separate `tests` structure does NOT (Promptfoo ignores `config` as a top-level key when running with `-c`)
- Use `--no-cache` when re-running after structural changes
- Don't modify `e2e/README.md` until the new structure is validated
- Follow the repo's portability rule: guard on file existence, don't assume paths exist
