# Content Alignment to VBoA Positioning — Execution Plan

> **For Claude:** REQUIRED SUB-SKILL: Use /aligned:business-executing to implement this plan task-by-task.

**Diagnosis:** The positioning work is complete (`docs/plugin-positioning.md`) but hasn't been applied to any content surface. The README currently leads with "Opinionated skill stack for Claude Code" and drops into install commands — a developer-only frame that repels the actual target audience (semi-technical leaders evaluating the repo cold). The onboarding flow starts with configuration, not value. There is no consulting reference doc. There is no content driving discovery. The obstacle is not "we need to write content" — it is that every public-facing surface assumes the wrong audience and buries the value proposition below implementation details.

**The crux:** Task 1 (scenario verification) is the highest-risk unknown. The design doc's README scenarios describe specific advisor behaviors (April Dunford's framework auto-selected, Steve Jobs pushing back on complexity). These descriptions may not match actual skill output because advisor selection is dynamic. If major discrepancies emerge, Tasks 2–6 must be re-scoped before proceeding. Everything downstream depends on Task 1 producing accurate, verified scenario descriptions.

**Goal:** Align four content surfaces (README, onboarding, consulting pitch, content/blog) to the "Virtual Board of Advisors" positioning before the GitHub repo goes public. Each surface should work at two levels: outcome-first for semi-technical leaders, mechanism-deep for developers.

**Source Design Doc:** `docs/plans/2026-04-03-content-alignment-design.md`

**Audience:** Eric (executor), with deliverables targeting: semi-technical founders/leaders evaluating the repo cold, and developers setting up the plugin.

**Format:** Ordered task list with dependencies. Each task produces a specific artifact. Tasks are grouped by surface, respecting the dependency chain: README → Onboarding (depends on README) | Consulting Pitch (parallel) → Content/Blog (last).

**Success Criteria:**
- README top half passes the "30-second cold visitor" test (someone with no context can articulate what aligned does and who it's for)
- Onboarding first interaction demonstrates advisor value, not configuration
- Consulting pitch provides repo-backed proof points usable in a live conversation
- Flagship blog post published; generates measurable newsletter signups (baseline: any > 0)
- All 5 cross-surface principles from the design doc are consistently applied

---

## Task 1: Verify README Scenario Claims by Running Actual Skills

**Output:**
- Create: `docs/plans/content-alignment-artifacts/scenario-verification-log.md`
- Reference: `docs/plans/2026-04-03-content-alignment-design.md` (Section: Surface 1, "What this looks like")
- Review: Each scenario description accurately reflects real skill output

**Step 1: Run the positioning exercise scenario**

Invoke `/aligned:brainstorming` with a sample product description (use the aligned plugin itself as the product). Capture: Does the system pull in April Dunford's 5 Components? Does Steve Jobs push back on complexity? Does Seth Godin challenge remarkability? Does a multi-advisor critique panel run with real methodology?

Record which parts of the README scenario description match reality and which need adjustment.

**Step 2: Run the sales deck scenario**

Invoke `/aligned:generate-deck` with sample prospect context (e.g., a B2B SaaS company evaluating the plugin). Capture: Does it use April Dunford's positioning framework? Does it apply the brand visual identity and messaging framework? Does a review panel run (April Dunford lens, Shirin Oreizy lens, buyer personas)?

Record matches and discrepancies.

**Step 3: Run the advisor scenario**

Invoke `/aligned:use-advisor rob-walling` and walk through a decision (e.g., "Should I open-source this plugin or keep it closed?"). Capture: Does it use Rob Walling's actual decision frameworks? Does it calibrate to company context?

Record matches and discrepancies.

**Step 4: Write verification log**

Create `docs/plans/content-alignment-artifacts/scenario-verification-log.md` documenting:
- Each scenario tested
- Exact skill invocations used
- What matched the design doc description
- What needs to be adjusted in the README copy
- Any new observations that would make the scenarios more compelling

**Decision rule for partial matches:** The brainstorming skill uses dynamic advisor selection — specific advisors (Steve Jobs, Seth Godin, April Dunford) may or may not appear for a given invocation. If the expected specific advisors do not appear, note which advisors did appear and what methodology they applied. Adjusted scenario descriptions should describe what the system reliably does (multi-advisor critique with real methodology, auto-selected by context), not what it did once. If the core mechanic is present but specific advisors differ, update the example advisor names to match observed reality. If the core mechanic itself is absent (no multi-advisor critique, no real methodology), escalate to the user — the design doc needs revision before proceeding.

**Acceptance criteria:**
- [ ] All 3 scenarios from the design doc have been run through actual skills
- [ ] Discrepancies between design doc descriptions and actual output are documented
- [ ] Decision rule applied: scenarios describe reliable behavior, not one-off observations
- [ ] Adjusted scenario descriptions are drafted and ready for Task 2

---

## Task 2: Rewrite README Top Half (Sections 1–4)

**Output:**
- Edit: `README.md` (sections 1–4, above the fold)
- Reference: `docs/plugin-positioning.md`, `docs/plans/2026-04-03-content-alignment-design.md` (Surface 1), scenario verification log from Task 1
- Review: Cold visitor 30-second comprehension test

**Depends on:** Task 1 (verified scenario descriptions)

**Step 1: Draft Section 1 — Hero**

Write the mechanism-first tagline. Per the design doc:
> 62 expert advisors with real methodologies, auto-selected by context, available 24/7 in Claude Code.

Do NOT lead with "Virtual Board of Advisors." Let the concept emerge from evidence. One sentence below the tagline that expands on the value: leaders of growing companies get world-class strategic thinking without hiring consultants for every function.

Tone: Direct, confident, specific. No buzzwords. Active voice.

**Step 2: Draft Section 2 — "What this looks like"**

Write 2–3 concrete scenarios using the verified descriptions from Task 1. Each scenario: brief narrative showing input → output. Format:
- **Bold scenario title** (e.g., "Positioning exercise at 11pm")
- 3–4 sentences describing what happens when you invoke the skill
- Emphasize: real methodology, multi-advisor critique, not generic AI advice

**Step 3: Draft Section 3 — "Who this is for"**

Target: Leaders of growing companies scaling decision-making. Teams needing consistent, high-quality thinking. Technical and semi-technical founders comfortable with Claude Code.

Include anti-patterns: not a prompt library, not a template collection, not "better prompts for ChatGPT."

Add one line linking to the newsletter: "Get notified when new advisors and frameworks ship." (per the design doc's audience capture strategy — link target TBD, placeholder OK for now)

**Step 4: Draft Section 4 — "How it works"**

Brief mechanism explanation covering:
- Advisor personas with encoded voices, signature questions, failure modes, calibration data
- 135 structured frameworks made interactive and sequential with quality gates
- Skills that auto-select relevant advisors based on context
- Company context incorporation (competitors, personas, strategy docs)

This is where "virtual board of advisors" appears naturally as a descriptor, not a headline claim. The reader should arrive at this concept having already seen evidence.

**Step 5: Review against success criteria**

Check:
- [ ] A cold visitor can articulate what aligned does within 30 seconds of reading sections 1–4
- [ ] Mechanism before metaphor — "Virtual Board of Advisors" doesn't appear until section 4
- [ ] Every claim traces to a real, inspectable capability (cross-surface principle #5)
- [ ] Dual-level: top half serves the "what does this do for me?" question
- [ ] Honest framing: uses "incorporates" / "uses" for context layering, not "learns" / "knows" (principle #4)
- [ ] No sycophantic language, no buzzwords, no happy talk

**Step 6: Checkpoint with user**

Present the drafted sections 1–4. Wait for feedback before continuing to Task 3.

**Acceptance criteria:**
- [ ] Sections 1–4 pass the 30-second cold visitor test
- [ ] All 5 cross-surface principles applied
- [ ] Scenario descriptions verified against actual skill output (Task 1)
- [ ] User has approved the top half before proceeding

---

## Task 3: Restructure README Bottom Half (Sections 5–6)

**Output:**
- Edit: `README.md` (sections 5–6, below the fold)
- Reference: Current `README.md` content (installation, permissions, skill reference table, agents, hooks, etc.)
- Review: Developer audience can find everything they need

**Depends on:** Task 2 (top half establishes the frame that bottom half references)

**Step 1: Move Quick Start / Install to Section 5**

Relocate the current installation commands and quick-start skill list. Keep the existing install instructions verbatim — they work. Add a brief transition sentence connecting the top half ("Now that you've seen what aligned does, here's how to set it up").

**Step 2: Organize Section 6 — Detailed Reference**

Reorganize existing content into Section 6:
- Skill reference table (keep as-is)
- Agents section
- Hooks section
- Advisors section (quick reference to the 62 advisors)
- Frameworks section (reference to the 135 frameworks)
- Team setup
- Project conventions
- Iron rules
- Development
- Changelog

No content changes needed — this is a structural move, not a rewrite. The developer audience content stays intact.

**Step 3: Review transition**

Check:
- [ ] The README reads as a coherent document from top to bottom
- [ ] No content was lost in the restructure (diff the before/after to confirm)
- [ ] Section 5 begins with a transition sentence explicitly referencing the top half
- [ ] Section 6 reference content matches current reality

**Audience for sections 5–6:** Developers setting up the plugin and contributors. They need to find installation instructions, skill reference tables, agent docs, and project conventions quickly. The restructure must not break their ability to navigate.

**Step 4: Checkpoint with user**

Present the restructured bottom half. Verify the developer audience can locate: (a) installation commands, (b) skill reference table, (c) agent list, (d) hook configuration within the new structure.

**Acceptance criteria:**
- [ ] All existing README reference content preserved (confirmed via diff)
- [ ] Section 5 begins with an explicit transition from the outcome-focused top half
- [ ] A developer unfamiliar with the repo can locate installation instructions, skill reference table, and agent docs within the new structure
- [ ] Installation instructions tested by following them verbatim — all commands exit 0
- [ ] User has approved the restructure

---

## Task 4: Create Consulting Pitch Document

**Output:**
- Create: `docs/consulting-pitch.md`
- Reference: `docs/plugin-positioning.md`, `docs/plans/2026-04-03-content-alignment-design.md` (Surface 3)
- Review: Provides proof points usable in a live conversation without additional prep

**Can run parallel with:** Task 3 (independent of README bottom half)

**Step 1: Draft the 5-section structure**

Write `docs/consulting-pitch.md` following the design doc structure:

1. **The demonstration** — "You've seen the plugin. 62 advisors, 135 frameworks, quality gates. Your team can access world-class strategic thinking independently, 24/7."

2. **The gap the plugin doesn't close** — The plugin ships with methodology but not your company's institutional knowledge. Use "incorporates" / "operates with" language, not "learns" / "knows" (principle #4). Describe what's missing: competitors, personas, strategic priorities, lessons learned.

3. **What the engagement delivers** — Four concrete deliverables:
   - Institutional knowledge capture: codify tribal knowledge into AI-consumable context
   - Custom advisor calibration: tune advisors to your domain, market, competitive landscape
   - Cultural transformation: shift from "AI as chatbot" to "AI as rigorous thinking partner"
   - Team enablement: every team member gets access to same quality of strategic thinking

4. **The outcome** — Decision quality that doesn't degrade as the company grows. The CEO doesn't need to be in every room.

5. **Proof** — The plugin itself. Open-source, inspectable methodology, working software. Not a pitch deck claim.

Tone: Direct, conversational (written for Eric to use in live conversations). Not marketing copy. Not developer docs.

**Step 2: Add cross-reference to ewp-site**

Note at the bottom: the AI enablement page at ewp-site frames AI as a leadership problem. This doc provides the specific plugin-backed proof points. Reference but don't duplicate.

**Step 3: Review against success criteria**

Check:
- [ ] Usable in a live conversation without additional prep
- [ ] Every claim backed by inspectable, working software (principle #5)
- [ ] Honest framing of context layering (principle #4)
- [ ] Dual-level: outcome for the leader, mechanism for the technical evaluator
- [ ] No marketing fluff — direct and evidence-based

**Step 4: Checkpoint with user**

Present the consulting pitch doc. Wait for feedback.

**Acceptance criteria:**
- [ ] Document provides concrete proof points, not assertions
- [ ] Tone matches live conversation use (not landing page, not developer docs)
- [ ] Cross-reference to ewp-site included
- [ ] User has approved before proceeding

---

## Task 5: Update Onboarding — Kickstart Skill Output

**Output:**
- Edit: `skills/kickstart/SKILL.md` (add "what to try first" section to output)
- Reference: `docs/plans/2026-04-03-content-alignment-design.md` (Surface 2), current kickstart skill
- Review: First interaction demonstrates value, not configuration

**Depends on:** Task 2 (README establishes the frame onboarding references)

**Step 1: Read the full kickstart skill**

Read `skills/kickstart/SKILL.md` in full to understand the current scaffolding output and where a "what to try first" section fits.

**Step 2: Draft "What to try first" output section**

After the kickstart scaffolding completes, add output messaging that guides the user to experience value:

1. **Meet an advisor:** "Try `/aligned:use-advisor april-dunford` — she'll challenge your positioning with her actual methodology."
2. **Run a brainstorm:** "Try `/aligned:brainstorming` with a real problem you're working on. The system auto-detects your domain and selects relevant advisors."
3. **Layer in context:** "Once you've experienced the advisors, layer in your company context (competitors, personas, strategy docs) to make them company-aware."

Sequence is: experience value → understand the system → customize it.

**Step 3: Add dual-level paths**

Surface both paths in the kickstart output:
- For the leader: "Try an advisor, see what happens" (outcome-first)
- For the developer: "See how skill routing works: read `skills/brainstorming/SKILL.md` for the auto-detection logic"

**Step 4: Add newsletter suggestion**

After first advisor interaction suggestion, add: "Want to know when new advisors ship? [newsletter link placeholder]"

**Step 5: Review against success criteria**

Check:
- [ ] First interaction demonstrates advisor value, not plugin configuration
- [ ] Experience → understand → customize sequence
- [ ] Dual-level paths clear
- [ ] Newsletter capture point included
- [ ] Doesn't break existing kickstart scaffolding flow

**Acceptance criteria:**
- [ ] Kickstart output guides user to immediate value experience
- [ ] Both semi-technical leader and developer paths surfaced
- [ ] Existing scaffolding functionality preserved

---

## Task 6: Add Getting-Started Content to README

**Output:**
- Edit: `README.md` (add getting-started section between "Who this is for" and "How it works")
- Reference: `docs/plans/2026-04-03-content-alignment-design.md` (Surface 2, "Where this lives")
- Review: Lightweight onboarding for someone who just installed

**Depends on:** Task 2 (README top half structure), Task 5 (onboarding messaging alignment)

**Step 1: Draft getting-started section**

Add a brief section between "Who this is for" (section 3) and "How it works" (section 4) that serves as lightweight onboarding:

- "Start here" with 3 suggested first actions (matching kickstart output from Task 5)
- Brief, not duplicating the Quick Start in section 5 — this is about experiencing value, not installing

**Step 2: Review fit**

Check:
- [ ] Doesn't duplicate the Quick Start / Install section (section 5)
- [ ] Consistent messaging with kickstart output (Task 5)
- [ ] Flows naturally in the README narrative arc

**Acceptance criteria:**
- [ ] Getting-started section provides a value-first entry point in the README itself
- [ ] Consistent with onboarding messaging from Task 5

---

## Task 7: Plan Flagship Blog Post

**Output:**
- Create: `docs/plans/content-alignment-artifacts/flagship-blog-brief.md`
- Reference: `docs/plans/2026-04-03-content-alignment-design.md` (Surface 4), `docs/plugin-positioning.md`
- Review: Brief is actionable enough to produce a draft

**Can start immediately** (content planning begins in parallel per design doc)

**Step 1: Write the blog post brief**

Title: "How to Run a Positioning Exercise with April Dunford at 2 AM"

**Primary audience:** Semi-technical leaders who have never used the plugin but are curious about AI-augmented strategic thinking. Secondary: developers evaluating the methodology depth.

Brief should include:
- **Hook:** The metaphor IS the hook for content (per design doc — different from README's mechanism-first approach)
- **Content tilt:** Show a recognized expert methodology running as an AI-native executable workflow with real output. If the piece doesn't show the system working with real methodology, it doesn't belong.
- **Structure:**
  - Open with the scenario (it's 2 AM, you have a positioning problem)
  - Walk through an actual positioning exercise using the plugin
  - Show the multi-advisor critique in action
  - End with what the output looks like vs. what you'd get from generic AI
- **Voice:** Match ewp-site blog voice — direct, CEO-coaching, systems-thinking. Not developer docs.
- **CTA:** Newsletter signup. "One email when a new advisor or framework drops — no spam, no fluff."
- **Platform:** ewp-site blog
- **Target publish date:** Within 2 weeks of repo going public

**Step 2: Run the actual exercise**

Run `/aligned:brainstorming` with a real positioning problem to capture actual output for the blog post. This is both content research and a verification of the scenario claims. Save the captured output to `docs/plans/content-alignment-artifacts/positioning-exercise-output.md`.

**Step 3: Draft the blog post outline**

Write a section-by-section outline with:
- Opening hook (2–3 sentences)
- Each section's key point and approximate word count
- Where to embed actual plugin output
- Closing CTA

**Step 4: Checkpoint with user**

Present the brief and outline. This is a validation gate — per the design doc, publish the flagship piece first. If it doesn't generate signups and traffic, revisit before investing in pieces 2–4.

**Acceptance criteria:**
- [ ] Brief is specific enough to produce a full draft
- [ ] Content tilt is clear: methodology + AI-native workflow + real output
- [ ] Voice matches ewp-site blog tone
- [ ] CTA and distribution plan included
- [ ] User approves brief before full drafting begins

---

## Task 8: Draft Flagship Blog Post

**Output:**
- Create: Blog post draft at `docs/plans/content-alignment-artifacts/flagship-blog-draft.md` (staging location — final publish location on ewp-site determined during Task 9a)
- Reference: `docs/plans/content-alignment-artifacts/flagship-blog-brief.md` (Task 7), `docs/plans/content-alignment-artifacts/positioning-exercise-output.md` (Task 7 Step 2)
- Review: Passes the content tilt filter and voice check

**Depends on:** Task 7 (approved brief and outline)

**Step 1: Write the full draft**

**Primary audience:** Semi-technical leaders curious about AI-augmented strategic thinking (per Task 7 brief). Write for the leader; the developer audience is secondary here.

Follow the approved outline from Task 7. Key writing principles:
- Active voice, short sentences, no jargon (elements-of-style principles)
- Show, don't tell — embed actual plugin output where possible
- The content tilt is the demonstration, not the claim
- Every section must pass the "so what?" test
- Direct, CEO-coaching voice (not developer docs voice)

Target: 1,500–2,500 words.

**Step 2: Self-review**

Check:
- [ ] Opens with a shift in the world, not a product pitch (Andy Raskin principle)
- [ ] Shows real methodology running, not generic AI output
- [ ] Voice matches ewp-site blog posts
- [ ] CTA is clear and non-pushy
- [ ] No claims that can't be verified by inspecting the repo

**Step 3: Checkpoint with user**

Present the full draft. This is the key validation piece — flagship must land before investing in subsequent content.

**Acceptance criteria:**
- [ ] Full draft complete at target word count
- [ ] Content tilt verified: recognized methodology + AI-native workflow + real output
- [ ] Voice consistent with ewp-site
- [ ] Ready for publication pending user approval

---

## Task 9: Assess Newsletter State and Capture Signup URL

**Output:**
- Create: `docs/plans/content-alignment-artifacts/newsletter-assessment.md` (options, recommendation, current state)
- Reference: `docs/plans/2026-04-03-content-alignment-design.md` (Audience capture strategy)
- Review: Signup URL is known OR implementation plan is scoped for a separate ewp-site task

**Can start in parallel** (independent research). **Critical path note:** The newsletter signup URL is a hard dependency for Tasks 2, 5, 8, and 10. If this assessment takes longer than expected, it becomes the bottleneck for the entire plan. Tasks 2, 5, and 8 can proceed with placeholder URLs, but Task 10 (integration) cannot finalize until the real URL is known.

**Step 1: Assess current ewp-site newsletter state**

Check what newsletter infrastructure already exists on ewp-site. Document:
- Is there an existing email list or signup form?
- What email platform is in use (if any)?
- Where would the signup form live?
- What is the blog post publishing workflow? (Determines Task 8's final publish location)

**Step 2: Produce a decision memo**

Write `docs/plans/content-alignment-artifacts/newsletter-assessment.md` covering:
- Current state of ewp-site newsletter infrastructure
- Options for implementation (with effort estimates)
- Recommended approach
- The signup URL (if infrastructure already exists) or what's needed to get one
- Blog post publish location recommendation

**Step 3: Checkpoint with user**

Present the assessment. If newsletter infrastructure already exists, capture the signup URL and proceed. If it doesn't, the implementation is out of scope for this plan — it becomes a separate ewp-site task. Get user decision before proceeding.

**Acceptance criteria:**
- [ ] ewp-site newsletter state documented
- [ ] Signup URL captured (if it exists) OR implementation scoped as a separate task with estimated effort
- [ ] Blog post publish location decided
- [ ] User has approved the approach

---

## Task 10: Cross-Surface Newsletter Integration

**Output:**
- Edit: `README.md` (add signup link), `skills/kickstart/SKILL.md` (add signup link)
- Reference: Newsletter signup URL from Task 9
- Review: All surfaces have appropriate capture mechanisms

**Depends on:** Task 9 (signup URL — must be resolved, not placeholder), Task 2 (README), Task 5 (kickstart), Task 8 (blog post)

**Step 1: Add newsletter link to README**

In the "Who this is for" section (section 3), add one line: "Get notified when new advisors and frameworks ship." with the signup URL.

**Step 2: Add newsletter link to kickstart output**

In the onboarding "what to try first" output (Task 5), add the suggestion after first advisor interaction: "Want to know when new advisors ship? [signup URL]"

**Step 3: Verify blog post CTA has correct URL**

Confirm the flagship blog post CTA (in `docs/plans/content-alignment-artifacts/flagship-blog-draft.md`) points to the correct newsletter signup URL.

**Step 4: Verify placement table**

Cross-check against the design doc's placement table:

| Surface | Capture mechanism | Status |
|---------|------------------|--------|
| README | Newsletter link in "Who this is for" | ✓ |
| Blog posts | CTA at end of each post | ✓ |
| Consulting pitch | Not applicable | N/A |
| Onboarding (kickstart) | Suggestion after first advisor interaction | ✓ |

**Acceptance criteria:**
- [ ] All 3 applicable surfaces have newsletter capture points
- [ ] All links point to the correct signup URL
- [ ] Placement matches design doc specification

---

## Task 11: Cross-Surface Consistency Audit

**Output:**
- Create: `docs/plans/content-alignment-artifacts/consistency-audit.md`
- Review: All 5 cross-surface principles applied consistently

**Depends on:** Tasks 2, 3, 4, 5, 6, 8, 10 (all content surfaces complete)

**Step 1: Audit principle 1 — Mechanism before metaphor**

Check README and docs: mechanism leads, metaphor follows. Check content/blog: metaphor hooks, mechanism pays off. Confirm the exception is applied correctly (content uses metaphor as hook per design doc).

**Step 2: Audit principle 2 — Outcome-first, implementation-second**

Check all surfaces: does each lead with what it does for the reader, not how it's built?

**Step 3: Audit principle 3 — Dual-level architecture**

Check all surfaces have both layers:
- README: top half (leader) / bottom half (developer)
- Onboarding: outcome path / mechanism path
- Consulting pitch: outcome for leader / mechanism for technical evaluator
- Blog: hook for leader / depth for practitioner

**Step 4: Audit principle 4 — Honest framing of context layering**

Search all modified files for "learns," "knows," or any language implying automatic/adaptive behavior. Replace with "incorporates," "uses," "operates with."

**Step 5: Audit principle 5 — The repo is the proof**

Verify every claim across all surfaces traces to inspectable, working software. Flag any assertion not backed by a real capability.

**Step 6: Write audit report**

Document findings in `docs/plans/content-alignment-artifacts/consistency-audit.md`. For each principle: pass/fail per surface, with specific issues and fixes needed.

**Step 7: Checkpoint with user**

Present the audit report. Do NOT apply fixes across multiple surfaces without user sign-off on the findings. Cross-surface consistency fixes can change framing language in the consulting pitch, README, onboarding, and blog — the user must approve the proposed changes before they're applied.

**Step 8: Apply approved fixes**

Correct inconsistencies approved by the user in Step 7.

**Acceptance criteria:**
- [ ] All 5 principles pass across all 4 surfaces
- [ ] No "learns" / "knows" language in any surface
- [ ] Every claim backed by inspectable software
- [ ] Audit report documented
- [ ] User has approved all cross-surface fixes before application

---

## Task 12: Final Pre-Ship Verification

**Output:**
- Create: `docs/plans/content-alignment-artifacts/pre-ship-checklist.md`
- Review: Everything is ready for the repo to go public

**Depends on:** Task 11 (consistency audit complete and clean)

**Step 1: Verify README scenario descriptions against actual output**

Re-run the 3 README scenarios (from Task 1) against the final README copy. Confirm descriptions still match. This catches drift introduced during editing.

**Step 2: Verify all file references**

Check that every file path referenced across all surfaces actually exists:
- `docs/consulting-pitch.md` exists
- `docs/plugin-positioning.md` exists
- Any other referenced files exist

**Step 3: Verify counts**

Confirm the README's stated counts match reality:
- Advisor count (currently 62)
- Framework count (currently 135)
- Skill count (currently 31)
- Agent count (currently 13)

**Step 4: Compile pre-ship checklist**

Create `docs/plans/content-alignment-artifacts/pre-ship-checklist.md`:
- [ ] README top half passes 30-second cold visitor test
- [ ] README scenario descriptions verified against actual skill output
- [ ] All stated counts accurate
- [ ] Consulting pitch document complete and reviewed
- [ ] Kickstart onboarding updated with value-first experience
- [ ] Getting-started section in README
- [ ] Flagship blog post drafted and approved
- [ ] Newsletter infrastructure operational
- [ ] Newsletter links in all applicable surfaces
- [ ] Cross-surface consistency audit clean
- [ ] All file references valid
- [ ] No "learns" / "knows" language anywhere

**Step 5: Checkpoint with user**

Present the pre-ship checklist. This is the final gate before the repo goes public.

**Acceptance criteria:**
- [ ] All checklist items pass
- [ ] User signs off on readiness

---

## Decision Log

### Summary
| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Task ordering | README first, then parallel consulting + onboarding, content last | Design doc's dependency chain: README establishes the frame others reference |
| 2 | Scenario verification as Task 1 | Verify before writing, not after | Design doc principle #5: every claim backed by working software. Can't write accurate scenarios without running them first |
| 3 | Consulting pitch parallel with README bottom half | Tasks 3 and 4 are independent | Consulting pitch doesn't reference README structure; can draft simultaneously |
| 4 | Blog post brief before full draft | Two-step content process | Design doc specifies flagship validation before investing in pieces 2–4. Brief checkpoint prevents wasted effort |
| 5 | Newsletter infrastructure as separate task | Decouple from content work | URL is needed by multiple surfaces (README, onboarding, blog). Best to establish early and integrate later |
| 6 | Cross-surface audit as dedicated task | Not inline during writing | Easy to miss principle violations when focused on individual surfaces. Dedicated audit catches drift |
| 7 | Content pieces 2–4 excluded from this plan | Out of scope | Design doc explicitly says: publish flagship first, validate, then decide on subsequent pieces. Pieces 2–4 are contingent on flagship performance |
| 8 | ewp-site blog work scoped but not detailed | Separate repo, separate context | Blog infrastructure, publishing, and newsletter setup depend on ewp-site's current state. Tasks 8–9 deliberately leave implementation flexible |
| 9 | Artifact directory for working files | `docs/plans/content-alignment-artifacts/` | Keeps verification logs, briefs, and audit reports organized alongside the plan without cluttering `docs/` |

### Appendix: Decision Details

#### Decision 1: Task ordering follows design doc dependency chain
**Chose:** README → Consulting Pitch (parallel) + Onboarding (after README) → Content/Blog
**Why:** The design doc specifies this sequence because the README establishes the frame all other surfaces reference. The onboarding messaging must be consistent with the README's structure. The consulting pitch is independent. Content planning starts immediately but execution comes last.
**Alternatives rejected:**
- All surfaces in parallel: Would risk inconsistency since surfaces reference each other
- Content first: Content references the README scenarios and needs the repo to be near-ready
- Consulting pitch first: If the primary crux were converting consulting conversations, starting with the pitch would be correct. We are accepting the README-first order on the assumption that public repo comprehension is the primary barrier, not consulting conversion. The design doc's dependency chain is based on content architecture (README establishes the frame), not revenue priority.

#### Decision 2: Scenario verification blocks README writing
**Chose:** Run actual skills and capture output before writing README scenarios
**Why:** Cross-surface principle #5 states every claim must be backed by inspectable, working software. The design doc explicitly says "Before publishing, run each scenario through the actual skills and verify the descriptions match real output." Writing unverified scenarios risks publishing claims that don't match reality.
**Alternatives rejected:**
- Write scenarios first, verify later: Risks anchoring on aspirational descriptions that don't match actual output
- Skip verification: Violates principle #5

#### Decision 7: Content pieces 2–4 excluded from this plan
**Chose:** Only plan and draft the flagship blog post. Exclude "Your team's decisions shouldn't depend on who's in the room," "What happens when Steve Jobs reviews your product design," and "135 frameworks you'll actually use."
**Why:** The design doc explicitly marks pieces 2–4 as "contingent on flagship validation." The flagship piece is a hypothesis test — if it doesn't generate newsletter signups and repo traffic, the approach needs revision before investing in more content. Including pieces 2–4 in this plan would be premature.
**Alternatives rejected:**
- Plan all 4 pieces: Violates the design doc's validation-first approach
- Skip content entirely: Design doc says to begin planning immediately even though execution is last

#### Decision 8: ewp-site work scoped loosely
**Chose:** Tasks 7–9 describe what needs to happen on ewp-site but leave implementation details flexible
**Why:** This plan covers the aligned repo. The ewp-site blog infrastructure, publishing workflow, and newsletter platform depend on that repo's current state, which hasn't been assessed. Over-specifying implementation for a separate codebase would produce a plan that's wrong on contact.
**Risk:** The newsletter signup URL (Task 9) is a hard dependency for three other tasks. If ewp-site assessment reveals that newsletter infrastructure doesn't exist and must be built, Task 9 becomes the critical path to shipping. Content-creation tasks (2, 5, 8) can proceed with placeholder URLs, but Task 10 (integration) and Task 11 (audit) cannot finalize until the real URL is known.
**Alternatives rejected:**
- Fully specify ewp-site implementation: Premature without assessing current state
- Exclude ewp-site entirely: Content/blog is a core surface in the design doc; can't ignore it
