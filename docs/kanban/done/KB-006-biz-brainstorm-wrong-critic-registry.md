# KB-006: business-brainstorming references a critic-registry from a different skill

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/business-brainstorming/SKILL.md:109-110`
- **Observed:** Step 1 of the critique panel reads `skills/brainstorming/critic-registry.md` — a registry built for technical design critique (e.g., The Architect, The Security Reviewer). business-brainstorming has no critic-registry of its own, so technical-design critics evaluate business strategy documents, producing mismatched critique.
- **Expected:** Either create a business-specific critic-registry under `skills/business-brainstorming/`, or add a filter/note that selects only domain-appropriate critics from the shared registry.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17

## Triage (2026-02-17)

- **Verdict:** REVISE
- **Evidence:** `skills/business-brainstorming/SKILL.md:109` reads `skills/brainstorming/critic-registry.md`. That file (`skills/brainstorming/critic-registry.md`) now contains a single line: "Critic selection uses `advisors/registry.md`. See that file for per-advisor domain metadata, selection guidelines, and diversity rules." It is a redirect stub, not a technical-critics-specific registry. The canonical registry is `advisors/registry.md`, which contains the full mixed pool of business and technical advisors (Ray Dalio, Richard Rumelt, April Dunford, Jeff Bezos, Eric Ries, Andy Raskin, Rob Walling, Patrick Campbell alongside The Architect, The Security Reviewer, etc.), all with `not_for` guards that would correctly exclude technical critics from business strategy work. The sibling `brainstorming/SKILL.md:56` already reads `advisors/registry.md` directly — bypassing the redirect stub.
- **Root Cause:** `business-brainstorming/SKILL.md` was written when `skills/brainstorming/critic-registry.md` was still the full registry. The registry was later centralized to `advisors/registry.md` and the old file became a redirect stub. `business-brainstorming/SKILL.md` was not updated to point at the canonical source — it still routes through the stub.
- **Risk Assessment:** Minimal. The runtime behavior is functionally unchanged today (both paths reach `advisors/registry.md`). The risk is future divergence: if `skills/brainstorming/critic-registry.md` is updated or removed independently, `business-brainstorming` breaks silently. The fix eliminates that fragile indirect dependency.
- **Validated Fix:** The KB item's proposed solutions (create a business-specific registry, or add a filter) are over-engineered. The `not_for` guards in `advisors/registry.md` already handle domain filtering correctly. The correct fix is a one-line reference update: change line 109 of `skills/business-brainstorming/SKILL.md` from `Read 'skills/brainstorming/critic-registry.md'` to `Read 'advisors/registry.md'` — matching exactly what `brainstorming/SKILL.md:56` does. No new files needed.
- **Files Affected:** `skills/business-brainstorming/SKILL.md` (line 109 only)
- **Estimated Scope:** Small — single-line reference update
