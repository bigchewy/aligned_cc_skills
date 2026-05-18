# KB-144: Dead code — FOLDER_LABEL_TO_TAB map and buildFolderToGroupTab function

- **Type:** dead-code
- **Discovered during:** finishing-a-development-branch (Step 1d code review)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:1962-1971` (FOLDER_LABEL_TO_TAB) and `:1992-2000` (buildFolderToGroupTab)
- **Observed:** Both symbols are declared but never referenced. `FOLDER_LABEL_TO_TAB` predates v0.4.1 (introduced in commit 60ce687, before this branch). `buildFolderToGroupTab` was added in Task 7 of the v0.4.1 plan as a replacement routing helper but its callers were never wired up — the data-driven nav uses `resolveDisplayGroups()` directly.
- **Expected:** Delete both. They are pure dead weight and confuse future readers about which routing path is canonical.
- **Why out of scope:** Pre-existing for FOLDER_LABEL_TO_TAB; clean removal felt outside the scope of a v0.4.1 merge-blocking fix. File for a follow-up cleanup pass.
- **Severity:** LOW
- **Created:** 2026-05-18
