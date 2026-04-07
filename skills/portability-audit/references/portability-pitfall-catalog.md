# Portability Pitfall Catalog

Reference document for the portability audit skill. Contains detection categories, regex patterns, false-positive rules, and suggested fixes for each violation type.

## How to Use This Catalog

For each category:
1. Run the **Detection** regex via Grep across the file set from Phase 1
2. For each match, read surrounding context and apply **False Positive Rules**
3. Report true positives with the **Severity**, file location, matched pattern, risk explanation, and suggested fix

---

## CRITICAL — Absolute User Paths

These contain a literal username directory. They work on exactly one machine and always break for other users.

### P1: Absolute User Paths

**Why it breaks:** Paths like `/Users/ericpage/` or `/home/alice/` are hardcoded to a specific machine. Any other user who clones the plugin gets immediate failures when skills reference these paths.

**Detection:**
- Grep for `/Users/[a-zA-Z][a-zA-Z0-9._-]+/` (macOS)
- Grep for `/home/[a-zA-Z][a-zA-Z0-9._-]+/` (Linux)
- Grep for `C:\\Users\\[a-zA-Z][a-zA-Z0-9._-]+\\` (Windows)

**False Positive Rules:**
- Match is inside a fenced code block AND uses a generic placeholder (e.g., `/Users/yourname/`) → SAFE
- Match is on the same line as an `e.g.` marker → SAFE (inline example like `e.g., /Users/alice/`)
- Match is inside a CLAUDE.md file that documents the path as intentional → SAFE (verify against Phase 0 CLAUDE.md content)
- Path uses `$HOME`, `${HOME}`, `process.env.HOME`, or `os.homedir()` instead of a literal username → SAFE (these are programmatic and resolve per-user)

**Fix:** Replace with:
- `~/.claude/...` for Claude Code convention paths
- `{base-directory}/...` for skill-relative paths
- `$HOME/...` or `${HOME}/...` for shell scripts
- `process.env.HOME` or `os.homedir()` for JS/TS

---

## HIGH — Non-Plugin External File Dependencies

References to files outside the plugin tree that aren't standard Claude Code paths. The skill will fail for other users if the file doesn't exist and there's no fallback.

### P2: Non-Plugin External File Dependencies

**Why it breaks:** If a skill references `~/some-custom-dir/file.md` that only exists on the author's machine, other users get a missing file error with no recovery path.

**Detection:**
- Grep for paths starting with `~/` followed by directories that are NOT `.claude/` or `.config/`
- Regex: `~/(?!\.claude/|\.config/)[a-zA-Z0-9._-]+/`
- For each match, verify the referenced file does NOT exist in the plugin repo using Glob
- Skip paths containing template variables: `{base-directory}`, `{project-root}`, `{plugin-root}`, `{design-file-path}`

**False Positive Rules:**
- `~/.claude/` paths → SAFE (tilde expands per-user, standard Claude Code convention)
- `~/.config/` paths → SAFE (XDG base directory convention)
- Path contains template variables (`{base-directory}`, `{project-root}`, etc.) → SAFE (runtime-resolved)
- `${CLAUDE_PLUGIN_ROOT}` → SAFE (plugin runtime environment variable)
- Shell `||` chaining on the same line → SAFE (graceful fallback)
- `command -v` feature detection on the same line → SAFE
- Shell conditional `if [ -f ... ]; then` wrapping the reference → SAFE
- Match is inside a fenced code block with generic placeholders → SAFE
- Match is on the same line as an `e.g.` marker → SAFE

**Fix:** Add a fallback chain: check local repo first, then `~/.claude/`, then plugin-bundled default. Or bundle the required file in the skill's `references/` directory.

---

## MEDIUM — Platform-Specific Assumptions

macOS-only commands or paths that break on Linux. Lower severity because the plugin primarily targets macOS Claude Code users, but still a portability concern.

### P3: Platform-Specific Assumptions

**Why it breaks:** Commands like `date -j`, `pbcopy`, or `open` (without fallback) only exist on macOS. Linux users get "command not found" errors.

**Detection — only in executable files (.sh, .js, .ts):**
- Grep for `date -j` (macOS-specific date flag)
- Grep for `pbcopy` or `pbpaste` (macOS clipboard)
- Grep for `\bopen ` followed by a URL or file path (macOS open command, not a generic word)
- Grep for `/usr/local/bin/` (assumes Homebrew)

**False Positive Rules:**
- Shell `||` chaining on the same line (e.g., `date -j ... || date -d ...`) → SAFE (has fallback)
- `command -v` feature detection wrapping the command → SAFE
- Match is in a `.md` documentation file (not executable) → SAFE (documentation describing macOS usage, not runtime code)

**Fix:** Add cross-platform fallback:
```bash
# date
date -j -f "%Y-%m-%d" "2026-01-01" "+%s" 2>/dev/null || date -d "2026-01-01" "+%s"

# clipboard
command -v pbcopy >/dev/null && echo "text" | pbcopy || echo "text" | xclip -selection clipboard
```

---

## Maintenance

Update this catalog when:
- New portability violations are discovered during audits
- The plugin starts targeting additional platforms
- New false-positive patterns are identified

Last updated: 2026-04-07
