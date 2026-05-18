# KB-134: TestFrameworkRegistrySchema methods re-parse registry.yaml independently of the class fixture

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier scan of feature/framework-runner-refactor)
- **Location:** `e2e/tests/test_registry_schemas.py:174-215`
- **Observed:** `test_every_framework_has_valid_deliverable_type` (L177), `test_registry_documents_deliverable_type_taxonomy` (L189), and `test_optional_fields_have_correct_shape_when_present` (L196) each open and parse `frameworks/registry.yaml` from scratch inside the method body — bypassing the class's `registry` fixture (L90-95) that already performs the parse.
- **Expected:** Convert these three methods to consume the class `registry` fixture. Eliminates duplicate file I/O and ensures all tests in the class operate on the same parsed view.
- **Why out of scope:** Tests work; runtime impact negligible. Deferred to focused cleanup.
- **Severity:** LOW
- **Created:** 2026-05-17
