// Auto-approve Bash commands that only operate on known-safe paths.
// Prevents permission prompts for:
//   - /tmp/ paths (skill temp files, critique rounds)
//   - ~/.claude/ paths (reading skills, config, plugins)
//
// Security properties:
//   - Commands with shell operators (&&, ||, ;, |) are NOT auto-approved
//   - Harmless redirects (2>&1, 2>/dev/null) are correctly ignored
//   - Path traversal (..) is blocked
//   - Only paths under known-safe prefixes are approved

const os = require('os')
const path = require('path')

const input = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'))
const cmd = (input.tool_input?.command || '').trim()

// Strip harmless redirect patterns before checking for shell operators.
// 2>&1, >&2, 2>/dev/null, etc. contain & and > characters that look
// like shell operators but are just file descriptor redirects.
const cmdStripped = cmd
  .replace(/\d*>&\d+/g, '')            // 2>&1, >&2
  .replace(/\d*>+\s*\/dev\/null/g, '') // 2>/dev/null, >>/dev/null
  .replace(/\d*>&-/g, '')              // 2>&- (close fd)

// After stripping redirects, check for actual shell operators.
// &&, ||, ;, &, | can chain to operations on unsafe paths.
if (/&&|\|\||[;&|]/.test(cmdStripped)) process.exit(0)

const HOME = os.homedir()
const SAFE_PREFIXES = [
  '/tmp/',
  path.join(HOME, '.claude') + '/',
]
const SAFE_EXACT = ['/dev/null']

// Extract all absolute paths from the command
const paths = cmd.match(/\/[^\s"']+/g) || []

if (paths.length === 0) process.exit(0)

// All paths must be under a known-safe prefix with no traversal
const allSafe = paths.every(p => {
  if (p.includes('..')) return false
  if (SAFE_EXACT.includes(p)) return true
  return SAFE_PREFIXES.some(prefix => p.startsWith(prefix))
})

if (allSafe) {
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'allow',
      permissionDecisionReason: 'Auto-approved: all paths under known-safe directories'
    }
  }))
}
