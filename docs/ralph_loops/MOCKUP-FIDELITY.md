# Mockup Fidelity Check and Fix (Non-Interactive)

You are checking implementation code against design mockups and fixing deviations. One check-and-fix cycle per invocation. The shell loop handles repetition.

## Parameters

Read the parameters appended below this prompt:
- **Plan:** the plan file path
- **Worktree:** the worktree path (CWD should match this)

## Step 1: Find mockups

Read the plan file header. Look for:
- `**Mockups:**` field → the mockups directory path
- If absent, check `**Source Design Doc:**` → read that file → look for `**Mockups:**` there

If no mockups path is found, or the directory doesn't exist:

```bash
touch .mockup-clean
```

Say "No mockups found — skipping fidelity check." and exit.

## Step 2: Check fidelity

Read each HTML mockup file in the mockups directory. For each file, extract:
- Page/component layout structure
- Components present (buttons, cards, lists, inputs, etc.)
- Data displayed (column names, field labels, example content)
- Interactive elements (tabs, accordions, hover states, modals)

Then read the plan file to find the mockup-to-source-file mapping: for each UI task with a mockup verification step, note which source files it creates/modifies and which mockup it references. Read those implementation source files.

Compare mockup elements against implementation. Also search the plan file for `MOCKUP DEVIATION` annotations — these are intentional deviations documented during execution. Treat annotated deviations as accepted.

## Step 3: Evaluate results

**If no unannounced deviations exist** (everything matches or is intentionally deviated):

```bash
touch .mockup-clean
```

Print a brief fidelity summary and exit.

**If unannounced deviations exist:** Continue to Step 4.

## Step 4: Fix deviations

For each unannounced deviation:
1. Read the mockup file and the implementation file side by side
2. Identify the root cause (cosmetic, structural, data binding, or logic)
3. Fix the implementation to match the mockup
4. If a deviation genuinely cannot be fixed without breaking other functionality, add `> MOCKUP DEVIATION: [what and why]` below the relevant task heading in the plan file — this marks it as intentional for future checks

After fixing all deviations:

```bash
git add -A
git commit -m "fix: resolve mockup deviations"
```

## Step 5: Exit

After committing fixes, exit. Do NOT re-check fidelity — the shell loop will start a fresh invocation to verify the fixes.

Say "Fixed N deviations. Re-checking on next iteration." and exit.

Do NOT touch `.mockup-clean` — the next iteration's Step 2 will verify the fixes.

## Rules

- ONE check-and-fix cycle per invocation
- Do NOT touch `.mockup-clean` unless there are truly no deviations (Step 3)
- Treat `MOCKUP DEVIATION` annotations as accepted — do not re-fix them
- Fix root causes, not symptoms (e.g., if a component is missing, add it — don't just add a placeholder)
- Use sub-agents for heavy codebase research to keep context lean
- Do NOT run tests — the verify phase handles that after all mockup iterations complete
