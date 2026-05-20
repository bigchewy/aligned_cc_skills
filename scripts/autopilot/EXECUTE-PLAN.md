# Execute Next Plan Task

⚠️ SINGLE-TASK RULE: Execute exactly ONE task, then EXIT. No exceptions.

⚠️ UNATTENDED MODE: You are running unattended under autopilot. Never request human action. Never write halt sentinels. If a task cannot complete in this iteration — for ANY reason, including needing human action no agent can perform — mark it 🔄 BLOCKED and exit. The wrapper auto-skips after MAX_BLOCKED_ITERATIONS (default 3) consecutive blocks and surfaces skipped items in the final verify-phase report. There is no mid-run user-action surface.

You are executing an implementation plan one task at a time.
Each invocation handles ONE task, then stops. The loop handles repetition.

## Step 1: Find the next task

Do NOT read the entire plan file. Instead, use Grep to find task headings:

```
Grep pattern="^### (✅|🔄|⏭️)?\s*\d" path="<plan-file>" output_mode="content" -n=true
```

This matches only numbered task headings (e.g., `### 1. Setup auth`, `### ✅ 2. Add routes`) and ignores non-task headings like `### Notes` or `### Dependencies`. Find the first heading that does NOT contain ✅ AND does NOT contain ⏭️. If a task is marked 🔄, resume it (previous iteration may have failed mid-task; the wrapper tracks consecutive blocks). Skip over ⏭️ tasks — those were auto-skipped by the wrapper after hitting the BLOCKED cap; only the user can re-enable them by rewriting the heading.

Then use Read with offset and limit to read ONLY that task's section — from its heading line to just before the next `### ` heading. For example, if your task starts at line 45 and the next heading is at line 80:

```
Read file_path="<plan-file>" offset=45 limit=35
```

Do NOT read the entire plan. Large plans bloat context and cause you to process multiple tasks.

## Sentinel

One sentinel signals `run-ralph.sh` that work is complete:
- `.ralph-done` — every task heading is ✅ (complete) or ⏭️ (auto-skipped after MAX_BLOCKED_ITERATIONS blocks)

Step 2 covers when to write `.ralph-done`.

If the loop is interrupted (Ctrl+C, SIGTERM) after the sentinel was written but before `run-ralph.sh` could observe it, the sentinel stays on disk. The next launch's startup cleanup removes it — this is intentional, not a bug. Re-launching from a clean checkpoint is the correct recovery path.

## Step 2: If all tasks are settled

If every task heading contains ✅ or ⏭️, write the sentinel and stop:

```bash
touch .ralph-done
```

Say "All tasks settled!" and exit. (✅ = completed; ⏭️ = auto-skipped by wrapper after BLOCKED cap. Either way, no further iteration is needed.)

## Step 3: Execute the task

1. Change to the worktree directory specified below
2. Read ONLY the current task section (you already have it from Step 1)
3. Follow TDD: write failing test first, then implement, then verify
4. Run only the test file(s) you created or modified in this task — never the full suite.
   If a plan step says `npm test` or `vitest run` with no file path, scope it to the modified file instead.
   Examples: `npm test -- path/to/foo.test.ts`, `npx jest path/to/foo.test.ts`, `npx vitest run path/to/foo.test.ts`.
   The full suite runs in Phase 9 only.
   If a plan step says `npm run build`, `next build`, `tsc` (whole-project typecheck), or `npm run lint` (whole-codebase),
   skip that step entirely — these are full-project operations that Phase 9 already runs. Note the skip in your
   completion message. Do NOT run them; they spawn large worker pools and duplicate Phase 9.
   If a task's ENTIRE PURPOSE is running the full suite, building, or linting (e.g., titled "Final full-suite
   verification", "End-to-end verification", "Full build check"): mark it ✅ immediately with the message
   "Task N complete. Skipped — this is Phase 9 scope (full suite, build, lint). Phase 9 will run these."
   Do not execute any commands in it.
5. If the task spec includes a mockup verification step, perform it now —
   read the referenced mockup HTML and compare against your implementation.
   If you intentionally deviate, add `> MOCKUP DEVIATION: [what and why]` below the task heading.
6. If the task involves LLM behavior surface files (prompts, prompt builders),
   run the project's eval command and verify it passes
7. Mark the task with ✅ in the plan file (replace the task heading prefix)
8. Commit: `git add [changed files] && git commit -m "task N: [description]"`

## Step 4: STOP — your invocation is finished

⚠️ After committing, you are DONE. Follow these steps exactly:

1. Output "Task N complete." (where N is the task number you just finished)
2. Make NO further tool calls
3. Do NOT read the plan file again
4. Do NOT look at the next task
5. Do NOT do "one more quick thing"

Your job for this invocation is finished. The loop will start a new invocation for the next task.

## Rules

- ⚠️ ONE task per invocation — this is the #1 failure mode and is repeated intentionally
- Read skill files as needed for patterns and conventions
- Use sub-agents for heavy codebase research to keep context lean
- If a task cannot complete in this iteration — for ANY reason — mark it 🔄 BLOCKED and exit. This covers BOTH transient failures (mid-execution error, partial state) AND needs-human cases (paid API calls, manual Dashboard/UI work, OAuth consent, manual paste from external system):
  - Mark it 🔄 in the plan file (replace the task heading prefix)
  - Add `> BLOCKED: [one-line reason]` below the task heading
  - Commit the plan file update
  - Exit. The next iteration will retry.
  - After MAX_BLOCKED_ITERATIONS (default 3) consecutive 🔄 marks on the same task, the wrapper rewrites the heading to `### ⏭️ Task N: <title>` and continues. The user reviews ⏭️ tasks in the final verify-phase report — there is no mid-run halt.
  - NEVER write halt sentinel files. NEVER print messages claiming the loop is stopping. NEVER request human action. The autopilot contract is unattended; mid-run user action is forbidden by design.
- Do NOT run /aligned:finishing-a-development-branch — the user will handle finishing after the loop completes
- Do NOT modify tasks you are not currently executing
- ⚠️ FINAL REMINDER: After completing one task and committing, output "Task N complete." and EXIT. Do not continue.
