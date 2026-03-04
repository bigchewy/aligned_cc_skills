# Recommended Hooks

Optional hooks that reduce permission prompt noise when using Aligned skills.

## Bash Path Auto-Approve

Skills that run plan critique and brainstorming create temp files in `/tmp/` and read skill config from `~/.claude/`. Without this hook, every such Bash command triggers a permission prompt.

**Security properties:** Shell operators (`&&`, `||`, `;`, `|`) always blocked. Path traversal (`..`) blocked. Only `/tmp/` and `~/.claude/` paths approved. Harmless redirects (`2>&1`, `2>/dev/null`) correctly ignored.

### Setup

1. Save `hooks/auto-approve-safe-bash-paths.js` (included in this repo) to `~/.claude/hooks/`

2. Add to `~/.claude/settings.json` under `hooks.PreToolUse`:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "node ~/.claude/hooks/auto-approve-safe-bash-paths.js",
      "timeout": 5
    }
  ]
}
```
