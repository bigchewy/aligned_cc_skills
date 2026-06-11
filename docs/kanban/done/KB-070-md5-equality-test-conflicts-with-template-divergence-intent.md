# KB-070: test_template_md5_equality will fail on first intended template divergence

- **Type:** bug
- **Discovered during:** brainstorm-interactive-widgets
- **Location:** `e2e/tests/test_brainstorm_widgets.py:29-33`
- **Observed:** `test_template_md5_equality` asserts that all four mode templates share a single MD5 hash. The architecture documentation at `skills/brainstorming/references/brainstorm-components.md:74` explicitly states: "The four templates start as byte-identical copies; they are independent files going forward, free to diverge as the modes' visual needs differ." The test enforces byte-identity as a permanent invariant, which directly contradicts the documented intent. Any future mode-specific template change — the stated purpose of having four separate files — will break this test. The test was intended to enforce the widget-state composition update landed uniformly (all four templates updated together), which is a one-time constraint, not a permanent one.
- **Expected:** The test should either be removed after this branch merges (since the one-time uniformity contract has been verified) or converted to a weaker assertion: each template contains `state.widgets` (which `test_templates_compose_widget_state` already checks). Keeping it as an MD5 equality check turns every future legitimate template divergence into a failing test with no clear fix path.
- **Why out of scope:** Removing the test is a repo-level decision about test intent, not a local fix. Filing to track the future cleanup.
- **Severity:** MEDIUM
- **Created:** 2026-05-15
- **Resolved:** 2026-06-11 — Removed `test_template_md5_equality` (and its now-orphaned `_md5` helper + `hashlib` import) from `e2e/tests/test_brainstorm_widgets.py`. The test fired on the first intended divergence exactly as predicted: Task 11 of the visualization-runner-extraction plan baked the Overview scaffold into the five visualizing templates, intentionally excluding roadmap-template.html. Per-template coverage remains via `test_templates_compose_widget_state` and `test_visualizing_templates_share_overview_scaffold`.
