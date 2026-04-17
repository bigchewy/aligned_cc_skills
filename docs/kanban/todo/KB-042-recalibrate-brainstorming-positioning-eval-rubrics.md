# KB-042: Recalibrate brainstorming-positioning eval rubrics

- **Type:** bug
- **Discovered during:** 2026-04-16-skill-audit-round3.md / Step 1b (finishing-a-development-branch)
- **Location:** `e2e/scenarios/use-skill/brainstorming-positioning.yaml:19-65`
- **Observed:** Both test cases (with-skill, without-skill) fail 0/2 with exit code 100. Cached tokens (`Total Tokens: 3,683 (cached)`) confirm the same failure baseline has existed on `main` since the scenario was introduced in `7a314a9`. The five llm-rubric assertions (structural completeness, diagnostic depth, solution specificity, actionability, framework application) use promptfoo's default 0.5 threshold against weighted 1–5 rubrics — likely miscalibrated such that no Claude response passes.
- **Expected:** Either (a) lower the rubric threshold to a value Claude can hit on a reasonable positioning response, (b) tighten the rubric prompts so a strong response clearly hits 4–5, or (c) set explicit `threshold:` values per assertion. The eval should distinguish real regressions from calibration noise.
- **Why out of scope:** The skill-audit-round3 branch only added a placeholder-definition block (`{topic}`, `{project-root}`) to `skills/brainstorming/SKILL.md`. The eval uses `fixtures/skill-prompts/brainstorming-business.md` as system_context — not SKILL.md — and the fixture does not reference the new placeholders. My edit cannot affect eval output (confirmed by cache hit). This is pre-existing calibration, not a regression from this branch.
- **Severity:** MEDIUM
- **Created:** 2026-04-16
