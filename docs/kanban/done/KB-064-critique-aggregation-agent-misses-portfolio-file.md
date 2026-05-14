# KB-064: Aggregation agent in Planning mode does not receive portfolio-file-path

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (Step 1d code review)
- **Location:** `skills/_shared/critique-panel-orchestration.md:60-67`
- **Observed:** The aggregation agent prompt reads only `{critique-temp-directory}/round-1/` and `{design-file-path}`. It does not read `{portfolio-file-path}`. In Planning mode, the fact-checker and regular critic both receive `{portfolio-file-path}` and evaluate spawn-brief quality (criterion 7) against the portfolio. The aggregation agent summarizes those critic reports without ever reading the portfolio itself — so it cannot independently verify or extend any portfolio-grounded factual claims. The configuration validation section documents `portfolio-file-path` as a field "critic prompt templates may reference," but the aggregation agent is not a critic prompt template, leaving the scope inconsistent.
- **Expected:** Decide whether the aggregation agent in Planning mode should also read `{portfolio-file-path}`. If yes: extend the aggregation agent's prompt template to optionally include `{portfolio-file-path}` when set, and add a structural test asserting the portfolio path is referenced in the aggregation prompt. If no: document explicitly that aggregation does not see the portfolio, and update the configuration validation section to clarify which agents receive the field.
- **Why out of scope:** Filed during code review after merge-readiness verification. Not a correctness defect at runtime — critics still produce portfolio-grounded findings; the aggregator only loses an independent verification layer over criterion 7. No test currently covers the gap.
- **Severity:** MEDIUM
- **Created:** 2026-05-06
