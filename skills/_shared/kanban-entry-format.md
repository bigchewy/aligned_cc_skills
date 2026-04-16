# Kanban Entry Format

When filing an entry to the Kanban board:

1. Read `docs/kanban/.counter` for the next KB number (pad to 3 digits)
2. Derive a kebab-case slug from the title (max 50 chars)
3. Write `docs/kanban/todo/KB-NNN-slug.md`:

```markdown
# KB-NNN: [Title]

- **Type:** bug
- **Discovered during:** [skill-name]
- **Location:** `[file path]:[line range]`
- **Observed:** [What exists and why it's a problem]
- **Expected:** [What should change]
- **Why out of scope:** [Why it wasn't fixed when discovered]
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW
- **Created:** YYYY-MM-DD
```

4. Write the incremented number back to `docs/kanban/.counter`
