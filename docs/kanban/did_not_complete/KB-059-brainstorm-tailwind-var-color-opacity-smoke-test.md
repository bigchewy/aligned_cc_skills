# KB-059: Brainstorm template needs browser smoke test for Tailwind `var()` color values + opacity modifiers

- **Type:** bug
- **Discovered during:** root-cause-analysis (QA Engineer critique)
- **Location:** `skills/brainstorming/references/brainstorm-components.md` (Tailwind config block, ~line 30)
- **Observed:** Tailwind Play CDN (`cdn.tailwindcss.com`) accepts `'var(--color-accent)'` as a color value in `tailwind.config.theme.extend.colors`. Solid-color utility classes (`bg-accent`, `text-accent`) resolve correctly because browsers evaluate the CSS variable at paint time. **Opacity modifiers** (`bg-accent/50`, `ring-accent/30`) do NOT — Tailwind needs a concrete color value at compile time to compute the alpha channel, and `var()` references break that path. Today the brainstorm template doesn't use any opacity-modifier utilities, so this is theoretical. But the failure mode is silent (utility resolves to garbage) and would surface if anyone adds an opacity-modifier utility to the template later.
- **Expected:** Open a populated `live.html` (using non-default tokens like Deep Mirror's) in a real browser and verify: (a) Tailwind utilities render correctly, (b) Mermaid diagram colors apply, (c) the live-refresh cycle preserves brand across reloads. If opacity modifiers are wanted in future template updates, swap the Tailwind config approach to write literal hex values into the config alongside `:root` (agent substitutes both places).
- **Why out of scope:** No current usage of opacity modifiers in the template. Manual smoke testing wasn't run as part of the initial fix.
- **Severity:** LOW
- **Created:** 2026-05-06
