// Auto-approve Edit/Write operations when running inside a .worktrees directory.
// This gives worktrees full write access without affecting the main repo.

const input = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'))

if (input.cwd && input.cwd.includes('.worktrees')) {
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'allow',
      permissionDecisionReason: 'Auto-approved: working in git worktree'
    }
  }))
}
