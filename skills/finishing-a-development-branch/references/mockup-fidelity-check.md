# Mockup Fidelity Check — Workflow Reference

Extracted from finishing-a-development-branch SKILL.md to keep that file under 500 lines. This workflow detects UI drift between mockups and implementation, then guides a user-directed fix cycle.

## Contents

- Step 9: Mockup Fidelity Check
- Step 10: Fix Mockup Deviations (user-directed)
  - Step 10a: Root-cause diagnosis
  - Step 10b: Synthesize and fix
  - Step 10c: Re-verify

### Step 9: Mockup Fidelity Check

**After all verification and scans, check if the branch's design has associated mockups.**

This step is **non-blocking** — deviations are reported so the user can decide whether to fix them before merge.

1. **Check for an autopilot mockup result first.** The worktree path is the path given after `at` in the skill invocation (same path used in Step 1 for `.finish-status`). If a `.mockup-clean` file exists inside that worktree path, the mockup fidelity loop already ran and found no unannounced deviations. Report:

```
Mockup fidelity already verified by autopilot. Skipping Steps 1f and 1g.
```

Continue to Step 11.

2. **Find the plan file:** Scan both `docs/plans/*.md` and `docs/plans/completed/*.md` for the plan associated with this branch (match by branch name pattern). The plan may already be in `completed/` if executing-plans archived it. Read the plan header's `**Mockups:**` field for the mockups directory path. If the plan has no `**Mockups:**` field, fall back to the `**Source Design Doc:**` field and check that design doc for a `**Mockups:**` field.

3. **Check for mockups:** If a mockups path was found, verify the directory exists. If no mockups path was found or the directory doesn't exist, skip silently — not all features have UI components.

4. **If mockups exist, dispatch a fidelity check agent** via Task tool (`subagent_type=general-purpose`, `model=sonnet`):

   ```
   "You are a mockup fidelity checker. Compare the brainstorming mockups against
   the actual implementation to find visual deviations.

   You have access to Glob, Grep, and Read tools. Do not use Bash for searching.

   Step 1: Read each HTML mockup file in `{mockups-dir}/`. For each file, extract:
   - Page/component layout structure
   - Components present (buttons, cards, lists, inputs, etc.)
   - Data displayed (column names, field labels, example content)
   - Interactive elements (tabs, accordions, hover states, modals)

   Step 2: Read the plan file at `{plan-file-path}`. For each UI task that has a
   mockup verification step, note which source files it creates/modifies and which
   mockup file it references. This gives you the mockup-to-source-file mapping.
   Then read those implementation source files.

   Step 3: Compare mockup elements against implementation. For each mockup:
   - What matches the implementation
   - What deviates (present in mockup but missing/different in code)
   - What was added (present in code but not in mockup)

   Step 4: Search the plan file for 'MOCKUP DEVIATION' annotations — these are
   intentional deviations documented during execution.

   Return a JSON report:
   {
     \"mockups_checked\": N,
     \"matches\": [\"brief description of what matches\"],
     \"deviations\": [
       {
         \"mockup\": \"filename.html\",
         \"element\": \"what's different\",
         \"type\": \"missing|changed|added\",
         \"intentional\": true/false,
         \"annotation\": \"text of MOCKUP DEVIATION note, if any\",
         \"source_files\": [\"src/components/Foo.tsx\"]
       }
     ]
   }

   IMPORTANT: For each deviation, include the source_files array listing
   the implementation file paths you read when comparing against the mockup.
   Downstream steps depend on this field."
   ```

5. **Report findings:**

```
## Mockup Fidelity Check

Mockups checked: N
- Matches: N elements verified
- Intentional deviations: N (documented with MOCKUP DEVIATION)
- Unannounced deviations: N

### Unannounced Deviations (if any)
- [mockup file]: [element] — [missing|changed|added]
```

**If no unannounced deviations:** Report clean, continue to Step 10.

**If unannounced deviations exist:** Show them, continue to Step 10.

**If no mockups found:** Skip silently, continue to Step 10.

### Step 10: Fix Mockup Deviations (user-directed)

**If Step 9 found no unannounced deviations (or was skipped):** Skip silently, continue to Step 11.

**If unannounced deviations exist**, present:

```
⚠ {N} unannounced mockup deviations found:
{bullet list of deviation summaries — one line each}

Would you like to fix any of these before proceeding?
1. Fix all
2. Fix specific (list numbers)
3. Skip — accept deviations as-is

Which option?
```

**If skip:** Continue to Step 11.

**If fix all or fix specific:**

**Step 10a: Root-cause diagnosis.** For each selected deviation, spawn a sub-agent in parallel (`subagent_type=general-purpose`, `model=sonnet`). Each agent receives:

```
You are a mockup deviation analyst. Determine the root cause of this deviation
between a design mockup and the implementation.

Deviation: {deviation summary}
Mockup file: {mockup file path}
Element: {element description}
Type: {missing|changed|added}
Implementation file(s): {source file paths from Step 9 agent report}

You are READ-ONLY. Do not use Edit, Write, NotebookEdit, or any file-modifying
Bash commands. Use Read for files, Grep/Glob for searching.

Investigation steps:
1. Read the mockup file. Identify the intended design for this element.
2. Read the implementation file(s). Find the code that renders this element.
3. Trace the gap. Classify the root cause:
   - COSMETIC: Wrong value in the right place (color, spacing, font, size)
   - STRUCTURAL: Wrong component, missing component, or wrong composition
   - DATA: Correct component but fed wrong data or missing data binding
   - LOGIC: Conditional rendering or state logic doesn't match mockup intent

For STRUCTURAL, DATA, and LOGIC causes, trace one level deeper: why was
this built differently? Check git blame on the relevant lines — was the
mockup created after the code was written? Was a shared component reused
that doesn't support the mockup's design? Is there a data model mismatch?

Return a JSON object:
{
  "deviation": "{summary}",
  "root_cause_type": "COSMETIC|STRUCTURAL|DATA|LOGIC",
  "root_cause": "Specific explanation of why the deviation exists",
  "fix_scope": {
    "files": ["file paths that need changes"],
    "description": "What needs to change and where"
  },
  "risk": "What else could break if this is changed naively"
}
```

If any sub-agent fails or returns unparseable output, report which deviations could not be analyzed and ask the user whether to attempt those fixes without root-cause analysis or skip them.

**Step 10b: Synthesize and fix.** Collect all successful agent reports. Present:

```
## Deviation Root Causes

| # | Deviation | Type | Root Cause | Files |
|---|-----------|------|------------|-------|
| 1 | ...       | COSMETIC | ... | ... |
| ...

### Common Themes (if any)
{shared root causes or patterns across deviations}

### Risks
{any cross-cutting risks from the agent reports}
```

If multiple diagnoses target the same file, review them together before applying fixes — later diagnoses may be subsumed by earlier ones.

After presenting, apply fixes to files in the worktree using absolute paths (do not `cd` into the worktree — see CRITICAL section). Address the identified root causes, not just the surface symptoms.

Commit fixes to the feature branch before re-verifying. Run each command separately (do NOT chain with `&&`):

```bash
git -C <worktree-path> add <files>
```

```bash
git -C <worktree-path> commit -m "fix: resolve mockup deviations"
```

This gives each fix cycle a clean rollback point.

**Step 10c: Re-verify.** After committing fixes:
1. Re-run tests (Step 3) and build (Step 4)
2. If any fixed files match LLM behavior surface patterns, also re-run Step 5 (LLM eval)
3. Re-run the mockup fidelity check (Step 9) to confirm deviations are resolved

**Cycle limit:** Track the number of completed fix-then-verify cycles. Keep iterating until all unannounced deviations are resolved or the user chooses to skip.

- **After each cycle:** If unannounced deviations remain, present them and ask the user: fix or accept?
- **After cycle 5:** If deviations still remain after 5 fix cycles, present them as informational. Do NOT offer to fix again — the deviations likely require manual intervention or a design decision. Continue to Step 11.
