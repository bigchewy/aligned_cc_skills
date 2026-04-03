# Pre-Ship Checklist

**Date:** 2026-04-03

## Content Surfaces

- [x] README top half passes 30-second cold visitor test — hero states mechanism, scenarios show concrete examples, "How it works" explains the system
- [x] README scenario descriptions verified against actual skill code — Task 1 verification log confirms mechanics; adjusted for dynamic advisor selection
- [x] All stated counts accurate — 62 advisors, 135 frameworks, 30 skills, 13 agents (verified against filesystem)
- [x] Consulting pitch document complete (`docs/consulting-pitch.md`) — 5-section structure, evidence-based, conversational tone
- [x] Kickstart onboarding updated with value-first "What to Try First" section (Phase 7)
- [x] Getting-started section added to README ("Start Here" between "Who This Is For" and "How It Works")
- [x] Flagship blog post drafted (`docs/plans/content-alignment-artifacts/flagship-blog-draft.md`)

## Cross-Surface Consistency

- [x] Cross-surface consistency audit clean — all 5 principles pass across all 4 surfaces
- [x] No "learns" / "knows" language referring to the system in any surface
- [x] Every claim backed by inspectable software (principle #5 verified)
- [x] All file references valid — `docs/consulting-pitch.md`, `docs/plugin-positioning.md` exist

## Pending (Blocked on User Input)

- [ ] Newsletter infrastructure operational — Buttondown account exists in ewp-site but `NEXT_PUBLIC_BUTTONDOWN_USERNAME` not set. Need username from Eric.
- [ ] Newsletter links activated in README, kickstart, and blog post — currently HTML comment placeholders
- [ ] Flagship blog post published on ewp-site — draft staged, needs MDX conversion and publish date

## Pre-Ship Actions Required

1. **Eric:** Provide Buttondown username → enables Task 10 (newsletter link integration)
2. **Eric:** Set `NEXT_PUBLIC_BUTTONDOWN_USERNAME` in ewp-site production `.env.local`
3. **Execute Task 10:** Replace newsletter placeholders with actual URLs across README, kickstart, blog post
4. **Publish flagship blog post:** Convert draft to MDX, add to `ewp-site/src/content/blog/`, set publish date
5. **Final verification:** Re-run README scenarios through actual skill invocations (Task 12 Step 1 — deferred to actual skill runs, not code analysis)
