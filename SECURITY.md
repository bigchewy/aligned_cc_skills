# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this plugin, please report it responsibly.

**Email:** security@ericpage.com

**What to include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact

**Response timeline:**
- Acknowledgment within 48 hours
- Assessment and fix timeline within 1 week

## Scope

This plugin consists of markdown files (skills, agents, advisor prompts, frameworks) and JavaScript hooks. Security concerns most likely involve:

- **Hook scripts** (`hooks/`) — JavaScript that runs on tool events
- **Advisor prompts** — prompt injection risks in advisor persona files
- **Skill workflows** — unintended file system operations or data exposure

Issues in Claude Code itself (the CLI tool) should be reported to [Anthropic](https://www.anthropic.com/responsible-disclosure).
