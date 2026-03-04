---
name: claude-profile
description: "Use when the user wants to switch Claude Code accounts, check which account is active, toggle between primary and secondary profiles, or configure directory-specific account overrides"
---

# Claude Profile Switcher

## Overview

Manage which Claude Code account (PRIMARY or SECONDARY) launches from the terminal. A shell function reads `~/.claude_account_config` on every `claude` launch and sets `CLAUDE_CONFIG_DIR` accordingly.

## When to Use

- User wants to switch all repos to backup account (usage running low)
- User wants to switch back to primary after renewal
- User wants a specific directory to use a different account
- User asks "which account am I using?" or "what profile is active?"

## Quick Reference

| Command | Effect |
|---------|--------|
| `claude` | Uses auto-detected profile (default + overrides) |
| `claude-primary` | Forces PRIMARY, ignores config |
| `claude-secondary` | Forces SECONDARY, ignores config |

| Profile | Color | Config directory |
|---------|-------|-----------------|
| PRIMARY | Cyan | `$HOME` |
| SECONDARY | Yellow | `$HOME/.claude_personal` |

## Steps

1. Read `~/.claude_account_config` using the Read tool
2. Display current configuration:
   - Default profile (PRIMARY or SECONDARY)
   - Any directory overrides
3. Ask user what they want using AskUserQuestion:
   - **Switch default** — flip between PRIMARY/SECONDARY for all directories
   - **Add override** — specific directory uses a different profile than default
   - **Remove override** — delete a directory-specific override
   - **View only** — just show current config (done after step 2)
4. Edit `~/.claude_account_config` using the Edit tool
5. Remind user: changes take effect on the **next** `claude` launch

## Config Format

`~/.claude_account_config` is a sourceable shell script:

```bash
CLAUDE_DEFAULT_PROFILE="PRIMARY"
CLAUDE_PRIMARY_DIR="$HOME"
CLAUDE_SECONDARY_DIR="$HOME/.claude_personal"
CLAUDE_DIR_OVERRIDES=""
```

`CLAUDE_DIR_OVERRIDES` holds newline-separated entries: `substring|PROFILE`

```bash
CLAUDE_DIR_OVERRIDES="/software/epch|SECONDARY
/personal|PRIMARY"
```

## Rules

- **Only edit `~/.claude_account_config`** — never modify `~/.zshrc`, `~/.bashrc`, or `~/.claude_switcher.sh`
- Keep `CLAUDE_PRIMARY_DIR` and `CLAUDE_SECONDARY_DIR` unchanged unless the user explicitly asks to reconfigure account paths
- When adding overrides, use the most specific directory substring that uniquely identifies the project
