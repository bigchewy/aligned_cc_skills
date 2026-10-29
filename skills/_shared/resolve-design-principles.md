# Resolving the Design-Principles File

Shared lookup for the design-principles file whose tokens a page should use. Used by
`skills/_shared/visualization-runner.md` (brainstorm and design pages) and
`skills/_shared/framework-runner.md` (the artifact at the end of every framework). Change the
lookup here, not in the callers.

> **Note:** This is a `skills/_shared/` library file. The caller passes `{project-root}`. Do NOT
> add a Path Resolution note here.

## Lookup order

Use the first usable file:

a. **Project root:** `{project-root}/docs/design/design-principles.md`
b. **Monorepo apps:** if (a) is missing, Glob `{project-root}/apps/*/docs/design/design-principles.md`. Same for `{project-root}/packages/*/docs/design/design-principles.md`.
   - Exactly one match: use it.
   - Multiple matches: ask the user which app or package the page is for, then use that one.
   - Zero matches: continue to (c).
c. **Global fallback:** `~/.claude/docs/design/design-principles.md`. This is the user's own
   default brand for repos that have none.

## Placeholder check

A file is a kickstart placeholder, and counts as missing, if it is under 500 bytes, OR contains
"This file is a placeholder", OR contains "Run `/aligned:create-design-principles`". Skip it,
go on to the next step, and tell the user once: *"`<path>` is still a placeholder, so this page
uses `<the file you used, or the default tokens>`. Run `/aligned:create-design-principles` to
define the brand."*

## Result

Return the path of the file used, or `none`. With `none`, the caller uses its own default
tokens. Every page built from this lookup says which file supplied its tokens, or that none was
found, so a page in the wrong brand is easy to spot.
