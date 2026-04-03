# Content Alignment to VBoA Positioning — Design

**Goal:** Align four content surfaces to the "Virtual Board of Advisors" positioning before the GitHub repo goes public. Produce a content plan for each surface; execution decision comes after.

**Surfaces:** README (public), onboarding (public), consulting pitch (internal reference in public repo), content/blog (public, on ewp-site).

**Root Causes Addressed:**
1. Positioning work is complete but hasn't been applied to any content surface yet
2. Current content assumes a developer-only audience, but the real audience is broadening to semi-technical leaders who care about outcomes, not implementation details

**Audience broadening hypothesis:** Semi-technical founders are increasingly comfortable with GitHub through vibe coding and adjacent trends. This is a working hypothesis, not validated. Evidence that would confirm it: non-developer GitHub traffic to the repo, install adoption from non-engineering roles, or user feedback indicating non-developer use cases. The content plan should work regardless — leading with outcomes serves both audiences.

**Positioning Source:** `docs/plugin-positioning.md`

**Success Criteria:**

| Surface | Success gate |
|---------|-------------|
| README | A cold visitor with no prior context can articulate what aligned does and who it's for within 30 seconds of reading the top half |
| Onboarding | A new user's first interaction demonstrates value (advisor quality), not configuration |
| Consulting pitch | Provides concrete, repo-backed proof points usable in a live conversation without additional prep |
| Content/blog | Flagship piece published; generates measurable newsletter signups (baseline: any > 0 from this source) |

**Execution Sequence:**

```
README (first — establishes the frame all other surfaces reference)
  ├── Consulting pitch (parallel — independent reference doc)
  └── Onboarding (after README — references README structure)
        └── Content/blog (last — README scenarios link to these pieces;
                          but begin planning immediately since content
                          is an ongoing program, not a discrete deliverable)
```

---

## Surface 1: README

**Current state:** Leads with "Opinionated skill stack for Claude Code" and drops into install commands. Developer-audience assumptions throughout. Skill tables, agents, hooks dominate.

**New structure:**

### 1. Hero
Mechanism-first tagline. Lead with what it does, not what it claims to be:
> 62 expert advisors with real methodologies, auto-selected by context, available 24/7 in Claude Code.

Do NOT lead with "Virtual Board of Advisors" as the headline. Let the concept emerge from the mechanism description. The reasoning: technical founders have pattern-matched "AI advisor" to vaporware. Leading with mechanism lets them discover the concept through evidence, which builds more trust than asserting a category claim upfront. (This principle was validated during the brainstorm pressure test with PM and bootstrapper perspectives.)

### 2. "What this looks like"
2-3 concrete scenarios showing input → output. Brief narratives, not screenshots:

- **Positioning exercise at 11pm:** Invoke `/aligned:brainstorming`, describe your product. The system pulls in April Dunford's 5 Components framework. Steve Jobs pushes back on complexity. Seth Godin challenges whether it's remarkable. You get a multi-advisor critique panel with real methodology, not generic AI advice.
- **Sales deck for tomorrow's meeting:** Invoke `/aligned:generate-deck` with your prospect context. The system structures it using April Dunford's positioning framework, applies your design principles, and runs it through a review panel before delivery.
- **New hire's first strategic decision:** They invoke `/aligned:use-advisor` and get Rob Walling's actual decision frameworks, calibrated to your company's context. The quality of thinking doesn't depend on who's in the room.

This section earns the framing. It bridges the gap between "markdown files in a plugin" and "world-class advisory thinking."

**Pre-ship verification:** Before publishing, run each scenario through the actual skills and verify the descriptions match real output. Per cross-surface principle #5, every claim must be backed by inspectable, working software.

### 3. Who this is for
Leaders of growing companies scaling decision-making. Teams that need consistent, high-quality thinking without a consultant in every room. Technical and semi-technical founders comfortable with Claude Code.

Brief anti-patterns: not a prompt library, not a template collection, not "better prompts for ChatGPT."

### 4. How it works
Brief explanation of the mechanism:
- Advisor personas with encoded voices, signature questions, failure modes, and calibration data
- 135 structured frameworks made interactive and sequential with quality gates
- Skills that auto-select relevant advisors based on context
- Incorporates your company context — competitors, personas, strategy docs — when you layer them into a project

This is where "virtual board of advisors" can appear naturally as a descriptor, not a headline claim. The reader should arrive at this concept having already seen the evidence.

### 5. Quick Start / Install
Move installation commands here. Still important, but not the opening. Keep the current install instructions and quick-start skill list.

### 6. Detailed Reference
Skill reference table, agents, hooks, advisors section, team setup, project conventions, iron rules, development, changelog. Everything currently in the README that serves the developer audience stays — it just moves below the fold.

**Key change:** The README works at two levels. The top half (sections 1-4) serves the semi-technical leader asking "what does this do for me?" The bottom half (sections 5-6) serves the developer asking "how does this work and how do I set it up?"

---

## Surface 2: Onboarding

**Current state:** Onboarding is the kickstart skill (`/aligned:kickstart`), which scaffolds project structure and settings. Framed as "installing a plugin."

**New approach:** Frame around "meeting your first advisor."

### First-run experience
After install, the first interaction should demonstrate value, not explain configuration:

1. **Meet an advisor:** Prompt the user to try `/aligned:use-advisor` with a suggested advisor relevant to their domain. "Try `/aligned:use-advisor april-dunford` — she'll challenge your positioning with her actual methodology."
2. **Run a brainstorm:** Show them `/aligned:brainstorming` with a real problem. The auto-detection and advisor auto-selection demonstrates the system working.
3. **Layer in context:** Only after they've experienced value, introduce layering company context (competitors, personas, strategy docs) to make advisors company-aware.

### Where this lives
- Update the kickstart skill's output messaging to include a "what to try first" section after scaffolding
- Add a `GETTING-STARTED.md` or equivalent section in the README (section between "Who this is for" and "How it works") that serves as lightweight onboarding for someone who just installed

### Key principle
The onboarding sequence is: experience value → understand the system → customize it. Not: install → configure → eventually experience value.

### Dual-level approach
Like the README, onboarding works at two levels. The semi-technical leader gets "try this advisor, see what happens" (outcome-first). The developer gets "here's how the skill routing works and how to customize advisors" (mechanism). The kickstart output should surface both paths clearly.

---

## Surface 3: Consulting Pitch

**Current state:** Does not exist.

**Purpose:** Internal reference material for consulting conversations. Note: this doc will live in a public repo, so it's de facto visible — but it's written for Eric's use in conversations, not as a public-facing landing page. This serves a related but distinct goal from the other three surfaces: consulting enablement rather than public content alignment. It's included here because the positioning applies to both, and the repo-as-proof narrative is shared.

### Document: `docs/consulting-pitch.md`

**Structure:**

1. **The demonstration:** "You've seen the plugin. 62 advisors, 135 frameworks, quality gates. Your team can access world-class strategic thinking independently, 24/7."

2. **The gap the plugin doesn't close:** The plugin ships with methodology but not your company's institutional knowledge. Your competitors, your personas, your strategic priorities, your lessons learned — that's what turns generic advisors into advisors that operate with your company's context. (Note: use "incorporates" / "operates with" language here, not "knows" or "learns" — per cross-surface principle #4.)

3. **What the engagement delivers:**
   - Institutional knowledge capture: codify tribal knowledge into AI-consumable context
   - Custom advisor calibration: tune advisors to your domain, market, and competitive landscape
   - Cultural transformation: shift from "AI as chatbot" to "AI as rigorous thinking partner"
   - Team enablement: every team member gets access to the same quality of strategic thinking

4. **The outcome:** Decision quality that doesn't degrade as the company grows. The CEO doesn't need to be in every room. The new hire makes decisions with the same frameworks as the founder.

5. **Proof:** The plugin itself. It's open-source — inspect the methodology, try the advisors, see the quality gates. This isn't a pitch deck claim; it's working software.

### How this connects to ewp-site
The AI enablement page at ewp-site already frames AI as a leadership problem. The consulting pitch doc in this repo provides the specific plugin-backed proof points. Cross-reference but don't duplicate.

---

## Surface 4: Content / Blog

**Current state:** ewp-site has 6 blog posts (CEO coaching / org systems voice). No content about the aligned plugin specifically.

**Approach:** Advisor + framework combinations as natural content pieces. Content lives on ewp-site (where the blog infrastructure exists), with the aligned repo linking to key pieces.

**Why this surface matters most for growth:** The README, onboarding, and consulting pitch only serve people who already found you. Content is the only surface that brings new people to the repo. Despite being listed fourth, content planning should begin immediately — it's an ongoing program, not a discrete deliverable.

### Content tilt

The content tilt (what makes this content uniquely different): **nobody else shows recognized expert methodologies running as AI-native executable workflows with real output.** Every AI article says "use AI for strategy." This content shows April Dunford's actual framework running, with quality gates enforcing the process, producing real output. The tilt is the demonstration, not the claim. Use this as a filter: if a proposed piece doesn't show the system working with real methodology, it doesn't belong.

### Content strategy

**Format:** Each piece demonstrates a specific advisor + framework in action. "Here's what it looks like to run [framework] with [advisor]."

**Note on "mechanism before metaphor":** This principle applies to the README and docs (skeptical technical founders evaluating a repo). For content marketing, the metaphor IS the hook — "Steve Jobs reviews your product design" is what gets clicks. The mechanism is the payoff inside the piece. Different audiences, different entry points.

**Flagship piece (publish first as validation):**

1. **"How to run a positioning exercise with April Dunford at 2 AM"** — Walk through an actual positioning exercise using the plugin. Show the multi-advisor critique. This is the piece that makes eyes light up. **Publish this before planning pieces 2-4.** If this piece generates newsletter signups and repo traffic, the content strategy is validated. If it doesn't, revisit the approach before investing in more content.

**Subsequent pieces (contingent on flagship validation):**

2. **"Your team's decisions shouldn't depend on who's in the room"** — Thesis piece connecting to the ewp-site CEO coaching voice. The aligned plugin as the system that makes this real.

3. **"What happens when Steve Jobs reviews your product design"** — Hook piece. Provocative title, shows the advisor persona depth (not generic roleplay).

4. **"135 frameworks you'll actually use (because the AI won't let you skip steps)"** — The quality gates angle. Differentiates from prompt libraries.

### Voice
Match the ewp-site blog voice: direct, CEO-coaching, systems-thinking. Not developer docs voice.

### Publishing cadence and ownership
- **Owner:** Eric
- **Cadence:** Flagship piece published within 2 weeks of repo going public. Subsequent pieces: one per month minimum if flagship validates.
- **Platform:** ewp-site blog (one platform, consistently)

### Distribution
- Publish on ewp-site blog
- Link from aligned README's "What this looks like" section to the flagship pieces
- Each piece is a standalone demonstration that sells the plugin without feeling like marketing

### Audience capture strategy

A GitHub star is not a subscriber — repo visitors need a path to an ongoing relationship.

**Cross-surface placement:**

| Surface | Capture mechanism |
|---------|------------------|
| README | Link to newsletter signup in the "Who this is for" section. One line: "Get notified when new advisors and frameworks ship." |
| Blog posts | Each post ends with a CTA to the newsletter. Value proposition: "One email when a new advisor or framework drops — no spam, no fluff." |
| Consulting pitch | Not applicable (1:1 conversations) |
| Onboarding (kickstart) | After first advisor interaction, suggest: "Want to know when new advisors ship? [link]" |

**Platform:** Newsletter hosted on ewp-site (where the blog already lives). Single subscriber list.

**Success metric:** Newsletter signups from repo and blog sources. Baseline target: any > 0 from these sources in the first month. Refine after baseline established.

---

## Cross-Surface Consistency

All four surfaces share the same positioning principles:

1. **Mechanism before metaphor** (README and docs). Show what it does, then name what it is. Exception: content marketing uses metaphor as the hook and mechanism as the payoff — different audience, different entry point.
2. **Outcome-first, implementation-second.** Lead with what it does for the reader, not how it's built.
3. **Dual-level architecture.** Top layer for the semi-technical leader, deeper layer for the developer. Apply to all surfaces, not just README — onboarding, consulting pitch, and blog content all serve both audiences.
4. **Honest framing of context layering.** The system incorporates your company context when you configure it (manual process). Use "incorporates" or "uses," not "learns" or "knows." Don't imply automatic or adaptive behavior.
5. **The repo is the proof.** Every claim in every surface is backed by inspectable, working software. Verify README scenario descriptions against actual skill output before publishing.

---

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Lead with mechanism, not "Virtual Board of Advisors" metaphor | Pressure test finding: technical founders pattern-match "AI advisor" to vaporware. Leading with mechanism lets them discover the concept through evidence. |
| Keep detailed reference tables in README | Still valuable for developer audience; just move below the fold |
| Blog content on ewp-site, not this repo | Blog infrastructure exists there; voice matches; avoids maintaining two blogs |
| Consulting pitch as a doc in this repo, not on ewp-site | Internal reference doc that happens to live in a public repo. The repo is the proof. |
| Onboarding framed as "meet your advisor" not "install a plugin" | Positioning doc recommendation; value-first experience |
| Publish flagship blog piece first as validation | Content strategy is a hypothesis. Validate with one strong piece before investing in three more. |
| Audience broadening treated as hypothesis, not fact | No data yet on non-developer adoption. Content plan works for both audiences regardless. |
| Newsletter as audience capture platform | GitHub stars don't create relationships. Newsletter hosted on ewp-site provides a single subscriber list across blog and repo traffic. |
