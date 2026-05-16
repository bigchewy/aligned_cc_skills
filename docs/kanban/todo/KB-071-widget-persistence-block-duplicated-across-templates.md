# KB-071: 112-line widget persistence block duplicated verbatim across all four HTML templates

- **Type:** simplification
- **Discovered during:** brainstorm-interactive-widgets
- **Location:** `skills/brainstorming/references/templates/{software,business,authoring,planning}-template.html` (lines ~38-151 in each)
- **Observed:** The saveState/restoreState `<script>` block — ~112 lines including widget state capture and restore logic — is byte-for-byte identical across all four mode templates. Test `test_template_md5_equality` (see KB-070) currently enforces this identity, masking the maintenance problem. Any fix to widget persistence — a bug, a new field, an edge case — requires four synchronized edits with no enforcement mechanism beyond the md5 test, which itself is documented as a one-time constraint.
- **Expected:** Extract the shared script into a single partial (similar to how `widgets.html` is now a partial). Each template would inject the shared persistence script the same way it injects widget markup. Eliminates 3 of the 4 copies and gives the architecture stated in `brainstorm-components.md:74` ("templates free to diverge") a path forward without the md5 tripwire.
- **Why out of scope:** Refactoring template authoring conventions belongs in a dedicated branch with its own test plan. The current branch correctly mirrored the existing template structure rather than redesigning it.
- **Severity:** HIGH
- **Created:** 2026-05-15
