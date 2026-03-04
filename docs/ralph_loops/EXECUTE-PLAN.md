# Execute Next Plan Task

⚠️ SINGLE-TASK RULE: Execute exactly ONE task, then EXIT. No exceptions.

You are executing an implementation plan one task at a time.
Each invocation handles ONE task, then stops. The loop handles repetition.

## Step 1: Find the next task

Do NOT read the entire plan file. Instead, use Grep to find task headings:

```
Grep pattern="^### " path="<plan-file>" output_mode="content" -n=true
```

This returns all task headings with line numbers. Find the first heading that does NOT contain ✅. If a task is marked 🔄, resume it (previous iteration may have failed mid-task).

Then use Read with offset and limit to read ONLY that task's section — from its heading line to just before the next `### ` heading. For example, if your task starts at line 45 and the next heading is at line 80:

```
Read file_path="<plan-file>" offset=45 limit=35
```

Do NOT read the entire plan. Large plans bloat context and cause you to process multiple tasks.

## Step 2: If all tasks are complete

If every task heading contains ✅, write the sentinel and stop:

```bash
touch .ralph-done
```

Say "All tasks complete!" and exit.

## Step 3: Execute the task

1. Change to the worktree directory specified below
2. Read ONLY the current task section (you already have it from Step 1)
3. Follow TDD: write failing test first, then implement, then verify
4. Run the specific test file to confirm it passes
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
- If a task fails or is blocked:
  - Mark it 🔄 in the plan file
  - Add a note below the task heading: `> BLOCKED: [description of issue]`
  - Commit the plan file update
  - Exit (the next iteration will see the blocker note and attempt to resolve)
- Do NOT run /aligned:finishing-a-development-branch — the user will handle finishing after the loop completes
- Do NOT modify tasks you are not currently executing
- ⚠️ FINAL REMINDER: After completing one task and committing, output "Task N complete." and EXIT. Do not continue.
