# KB-123: Seven paste-back HTML blocks in review-template are verbatim duplicates varying only by three tokens

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (simplification scan)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:869-983`
- **Observed:** Each folder tab (strategy, language, audiences, personas, market, proof, design) contains an identical `<div class="paste-back">` block — same heading, same instruction sentence, same button labels — differing only in the framework-name span text, the textarea id, and the `onclick` targets. The `FRAMEWORK_BY_FOLDER` map already exists in JS.
- **Expected:** Render the paste-back block from `FRAMEWORK_BY_FOLDER` inside `renderFolderPanel`, eliminating ~90 lines of duplicated markup and making framework additions a one-line JS change instead of a copy-paste HTML addition. Coordinate with KB-120 (folder→framework mapping at slice level) since both touch the same map.
- **Why out of scope:** Found during simplification scan; non-blocking.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
