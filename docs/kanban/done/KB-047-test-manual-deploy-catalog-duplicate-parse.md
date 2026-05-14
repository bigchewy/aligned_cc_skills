# KB-047: `test_manual_deploy_catalog.py` parses catalog + YAML blocks multiple times

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code simplifier scan for feature/manual-deploy-artifacts)
- **Location:** `e2e/tests/test_manual_deploy_catalog.py:84-125`
- **Observed:** Two redundancies:
  1. Three `@pytest.mark.parametrize` decorators each call `_read_catalog()` + `_iter_entries()` independently at module import, reading and parsing the catalog file three times (lines 84, 90, 98).
  2. `test_entry_yaml_block_has_allowed_fields` (lines 99-125) re-runs the same `re.findall(r"\`\`\`yaml\n(.*?)\`\`\`", ...)` regex that `test_entry_has_exactly_one_fenced_yaml_block` already ran on the same entry body. The parsed YAML is not shared.
- **Expected:** Introduce a module-level `ENTRIES = list(_iter_entries(_read_catalog()))` constant used by all three parametrize decorators. For the YAML re-extraction, either include the parsed YAML in the parametrize tuple or merge the two YAML tests into one.
- **Why out of scope:** The tests pass and the overhead is negligible at current catalog size. Filing for when the catalog grows or when the same pattern appears in a sibling test file.
- **Severity:** MEDIUM
- **Created:** 2026-04-20
