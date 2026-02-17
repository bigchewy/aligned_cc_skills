# KB-004: Factor shared fields out of the two return objects in `processEvent`

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `hooks/error-tracker.js:28-62`
- **Observed:** The `PostToolUseFailure` branch (lines 33-43) and the `PostToolUse` branch (lines 48-58) each build a return object with four identical fields: `ts`, `sid`, `tool`, `cwd`. Any change to these fields must be made in two places.
- **Expected:** Extract the shared fields into a `base` object, then spread into each branch's return value.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17

## Triage (2026-02-17)

- **Verdict:** CONFIRM
- **Evidence:** `hooks/error-tracker.js` lines 33-42 and 49-57 each construct return objects with five identical fields: `ts` (line 34, 50), `sid` (line 35, 51), `tool` (line 37, 53), `input` (line 38, 54), `cwd` (line 41, 56). The KB entry said four shared fields but there are actually five — `input` is also shared and identical across both branches (`summarize(data.tool_name, data.tool_input)` called identically in each).
- **Root Cause:** Accidental structural duplication from authoring order. Both branches were written as independent object literals, each specifying the full shape. No intentional design decision to keep them separate. Pattern is isolated to `processEvent`; no other duplication in the file.
- **Risk Assessment:** Low. `processEvent` is a private function with one internal caller (line 17). No test file exists for `error-tracker.js`. The output is JSONL consumed programmatically — field ordering changes from the spread are irrelevant. No auth or security logic is touched. Fix removes lines, does not add abstraction layers.
- **Validated Fix:** Extract five shared fields into a `base` object at the top of `processEvent`, then spread `...base` into each branch's return object. Branch-specific fields (`type`, `error`, `interrupt`) remain in each branch. `interrupt` exists only in `PostToolUseFailure` and must NOT move to `base`. The `detectError` call remains after `base` construction — its arguments are unchanged. `summarize` is called once in `base.input` instead of twice (both original calls were identical).

  ```js
  function processEvent(data) {
    const event = data.hook_event_name;
    const base = {
      ts: new Date().toISOString(),
      sid: data.session_id,
      tool: data.tool_name,
      input: summarize(data.tool_name, data.tool_input),
      cwd: data.cwd
    };

    if (event === 'PostToolUseFailure') {
      return {
        ...base,
        type: 'tool_failure',
        error: data.error || 'Unknown tool failure',
        interrupt: data.is_interrupt || false,
      };
    }

    if (event === 'PostToolUse') {
      const sig = detectError(data.tool_name, data.tool_input, data.tool_response);
      if (sig) {
        return {
          ...base,
          type: 'command_error',
          error: sig,
        };
      }
    }

    return null;
  }
  ```

- **Files Affected:** `hooks/error-tracker.js` only
- **Estimated Scope:** Small — replaces ~14 lines with ~20 lines (net wash, but eliminates duplication); single file, single function, no cross-file changes
