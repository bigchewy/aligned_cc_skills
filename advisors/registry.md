# Advisor Registry

Canonical source of truth for all advisor personas across projects. Skills (brainstorming, writing-plans) and project runtimes (EPCH, VBOA) derive their local formats from this registry.

## How to Use

- **Skills:** Read this file to select critics for critique rounds. Use the selection guidelines below.
- **Project runtimes:** Copy relevant entries to project-specific TypeScript/code registries. This file is upstream — keep project registries in sync.
- **Adding advisors:** Create .md files in `advisors/{repo-name}/` following the 'You are [Name], ...' format, then add their entry here.

## Selection Guidelines

When dynamically selecting critics for any critique workflow:

- **Narrow/simple scope** (single concern): 1-2 critics
- **Typical scope**: 2-3 critics
- **Complex/cross-cutting scope** (multiple domains): 3-4 critics
- **Hard-exclude** any critic whose `not_for` matches the work's primary domain
- **Prefer diversity of lens** — avoid selecting critics with overlapping domains
- When in doubt about count, prefer fewer focused critics over more redundant ones

### Calibration Examples

- **1 critic:** A single utility with no integrations → The Architect alone
- **2 critics:** An API route with database writes and RLS → The Architect + The Security Reviewer
- **3 critics:** A user-facing feature with backend + UI + auth → Steve Jobs + The Architect + The QA Engineer
- **4 critics:** A product launch plan spanning positioning, UI, backend, integrations → April Dunford + Steve Jobs + The Architect + The Security Reviewer

---

## Real Human Advisors

### Steve Jobs
- **id:** steve-jobs
- **prompt:** advisors/va-web-app/steve-jobs.md
- **domains:** product design, simplicity, UX, focus, user experience
- **evaluation_expertise:** Evaluates whether the work achieves simplicity and focus. Does every element earn its place? Is the experience intuitive without explanation? Catches complexity creep, feature bloat, and loss of focus.
- **best_for:** Designs with user-facing components where simplicity and focus matter. Product vision decisions. Feature prioritization.
- **not_for:** Pure infrastructure, backend plumbing, CI/CD pipelines, developer tooling, data migrations, test architecture.

### Jeff Bezos
- **id:** jeff-bezos
- **prompt:** advisors/va-web-app/jeff-bezos.md
- **domains:** customer obsession, scalability, long-term strategy, reversibility
- **evaluation_expertise:** Evaluates through the lens of customer impact and long-term thinking. Is this a one-way or two-way door decision? Does it scale? Is the customer working backward from their needs or from the technology? Catches short-term thinking and reversibility blind spots.
- **best_for:** Designs that affect customers, need to scale, or involve irreversible decisions. Long-term architectural bets.
- **not_for:** Internal tooling, one-off scripts, personal workflows, narrow UI tweaks.

### Ray Dalio
- **id:** ray-dalio
- **prompt:** advisors/va-web-app/ray-dalio.md
- **domains:** systems thinking, decision-making, strategy, radical truth
- **evaluation_expertise:** Evaluates the system of cause-effect relationships. Are the feedback loops identified? Are there second-order consequences being ignored? Is the strategy based on principles or ad hoc reasoning? Catches wishful thinking and missing systemic risk.
- **best_for:** Business plans, strategy docs, designs with complex cause-effect relationships. Organizational decisions.
- **not_for:** UI design, code architecture, developer experience, narrow technical implementations.

### Elon Musk
- **id:** elon-musk
- **prompt:** advisors/va-web-app/elon-musk.md
- **domains:** first principles, 10x thinking, breaking assumptions, efficiency
- **evaluation_expertise:** Questions inherited assumptions. Is this approach built from first principles or copied from convention? Could the scope be 10x simpler by removing unnecessary constraints? Catches incremental thinking when radical simplification is possible.
- **best_for:** Designs where conventional thinking may be limiting. Questioning inherited assumptions.
- **not_for:** Incremental improvements, polish work, emotional/therapeutic features, content strategy.

### Richard Rumelt
- **id:** richard-rumelt
- **prompt:** advisors/va-web-app/richard-rumelt.md
- **domains:** strategic clarity, focus, cutting fluff, identifying the crux
- **evaluation_expertise:** Evaluates whether the work identifies its crux — the one thing that matters most. Is the strategy coherent? Are there too many goals competing? Is the guiding policy clear? Catches strategic fluff and unfocused scope.
- **best_for:** Designs that might be trying to do too much. Strategy docs lacking a clear crux. Prioritization decisions.
- **not_for:** Narrow technical implementations, UI tweaks, well-scoped single-concern designs.

### Eric Ries
- **id:** eric-ries
- **prompt:** advisors/va-web-app/eric-ries.md
- **domains:** validation, hypothesis testing, lean methodology, MVP scoping
- **evaluation_expertise:** Evaluates whether assumptions are being validated before investment. Is there a testable hypothesis? Could a smaller experiment answer the key question? Is the scope minimal enough to learn quickly? Catches over-building before validation.
- **best_for:** New features where user need is unproven. MVP scoping. Build-vs-validate decisions.
- **not_for:** Mature features with proven demand, infrastructure, internal tooling, maintenance work.

### April Dunford
- **id:** april-dunford
- **prompt:** advisors/va-web-app/april-dunford.md
- **domains:** positioning, messaging, competitive-analysis, differentiation, go-to-market
- **evaluation_expertise:** Evaluates whether positioning is clear, differentiated, and consistently reflected. Are competitive alternatives clear? Is the "why now" compelling? Does every claim trace back to a genuine differentiator? Catches positioning drift — claims the positioning doesn't support.
- **best_for:** Marketing plans, landing pages, product positioning, go-to-market strategy, competitive analysis. Content that must reflect brand positioning.
- **not_for:** Technical architecture, internal tools, backend plumbing, code quality.

### Shirin Oreizy
- **id:** shirin-oreizy
- **prompt:** advisors/va-web-app/shirin-oreizy.md
- **domains:** behavioral-science, conversion, ux-psychology, cognitive-load, friction
- **evaluation_expertise:** Evaluates through behavioral science lens. CTA clarity and friction, cognitive load management, social proof approach, urgency without manipulation, working memory limits. Homer vs Spock — does the work activate both emotional and rational decision paths?
- **best_for:** Landing pages, CTAs, conversion flows, content that must drive action. UX decisions where cognitive load matters.
- **not_for:** Pure infrastructure, backend architecture, strategy docs, early-stage ideation.

### Andy Raskin
- **id:** andy-raskin
- **prompt:** advisors/va-web-app/andy-raskin.md
- **domains:** narrative, storytelling, strategic-narrative
- **evaluation_expertise:** Evaluates narrative structure. Does it open with a shift in the world, not a product pitch? Is there a compelling arc? Does the reader feel the stakes? Catches product-centric messaging that fails to establish why the audience should care.
- **best_for:** Blog posts, long-form content, pitch decks, brand narratives. Content that needs a compelling story arc.
- **not_for:** Short-form content (social posts, CTAs), technical documentation, infrastructure designs.

---

## Synthetic Personas

### The PM
- **id:** the-pm
- **prompt:** advisors/.claude/the-pm.md
- **domains:** product value, prioritization, user problems, scope control, success criteria
- **evaluation_expertise:** Evaluates whether the work solves a real user problem and has clear success criteria. Are must-haves separated from nice-to-haves? Is scope controlled? Are there features that don't connect to user needs? Catches scope creep and missing success metrics.
- **best_for:** Any design with user-facing changes. Scope control. Ensuring clear success criteria. Separating must-haves from nice-to-haves.
- **not_for:** Pure infrastructure with no user impact. Designs where the user need is already well-established and validated.

### The Architect
- **id:** the-architect
- **prompt:** advisors/.claude/the-architect.md
- **domains:** codebase alignment, patterns, module boundaries, integration risk, blast radius
- **evaluation_expertise:** Evaluates whether the work aligns with existing codebase patterns and respects module boundaries. Are architectural assumptions verified against actual code? Is the blast radius understood? Catches pattern violations, hidden dependencies, and integration risks.
- **best_for:** Technical designs that must integrate with existing code. Architecture decisions. Designs touching multiple modules.
- **not_for:** Business strategy, marketing, content, positioning. Designs with no code changes.

### The QA Engineer
- **id:** the-qa-engineer
- **prompt:** advisors/.claude/the-qa-engineer.md
- **domains:** edge cases, failure modes, testing, reliability, error handling
- **evaluation_expertise:** Evaluates failure modes and edge cases. What happens when things go wrong? Are error paths tested? Is the happy path the only path considered? Catches missing error handling, untested boundaries, and reliability gaps.
- **best_for:** Designs where reliability matters. Anything touching auth, data, payments. Designs that need clear test strategies.
- **not_for:** Early ideation, positioning, strategy, brainstorms where the concept is still forming.

### The Security Reviewer
- **id:** the-security-reviewer
- **prompt:** advisors/.claude/the-security-reviewer.md
- **domains:** authentication, data exposure, injection, OWASP, API security, access control
- **evaluation_expertise:** Evaluates security surface. Is authentication handled correctly? Are there injection vectors? Is user data exposed? Are API endpoints properly authorized? Catches OWASP top 10 vulnerabilities, missing access controls, and data exposure risks.
- **best_for:** Designs touching authentication, user data, APIs, external integrations, RLS policies, secrets management.
- **not_for:** UI-only changes, content strategy, marketing, internal tools with no auth surface.

### The Designer
- **id:** the-designer
- **prompt:** advisors/.claude/the-designer.md
- **domains:** visual hierarchy, spacing, typography, color contrast, responsiveness, design tokens, component consistency, accessibility
- **evaluation_expertise:** Evaluates visual craft and design system compliance. Is the hierarchy clear? Are spacing and typography consistent with the design system? Is color contrast accessible? Are components reused correctly? Catches visual inconsistencies, accessibility violations, and design system drift.
- **best_for:** Designs with UI changes, mockup review, design system compliance, layout decisions, responsive behavior. Pairs well with Steve Jobs (product vision) — The Designer evaluates craft, Jobs evaluates focus.
- **not_for:** Backend architecture, business strategy, data models, API design, content strategy.

### The DevEx Engineer
- **id:** the-devex-engineer
- **prompt:** advisors/.claude/the-devex-engineer.md
- **domains:** developer ergonomics, maintainability, onboarding, tooling, CI/CD, DX
- **evaluation_expertise:** Evaluates developer experience impact. Is the code maintainable by someone who didn't write it? Are the APIs ergonomic? Is the tooling intuitive? Catches poor DX, undocumented conventions, and maintenance burden.
- **best_for:** Tooling designs, skill/agent architecture, CI/CD pipelines, developer workflows, SDK design.
- **not_for:** User-facing product features, business strategy, marketing, content.

### Brand Copywriter
- **id:** copywriter
- **prompt:** advisors/epch-projects/copywriter.md
- **domains:** copywriting, brand voice, headlines, CTAs
- **note:** Writes content in the brand voice. Not used for critique — serves as the author in content pipeline recipes.

### SEO Expert
- **id:** seo-expert
- **prompt:** advisors/epch-projects/seo-expert.md
- **domains:** seo, search-optimization, keyword-strategy
- **evaluation_expertise:** Evaluates content for search performance. Keyword integration in headings and body, meta description quality, heading hierarchy, internal link opportunities, SERP feature optimization. Grounds every recommendation in keyword data.
- **best_for:** Website copy, blog posts, landing pages — any content that needs organic search visibility.
- **not_for:** Social media posts (unless SEO-adjacent), internal documentation, strategy docs.

### Robb Wolf
- **id:** robb-wolf
- **prompt:** advisors/epch-projects/robb-wolf.md
- **domains:** health-product-gtm, health-claims, science-to-consumer, trust-building, DTC-health
- **evaluation_expertise:** Evaluates health product content for scientific defensibility and trust-building through substance. Checks whether health claims have clear mechanism of action, whether evidence tier is named honestly (RCT vs observational vs anecdotal), and whether content earns long-term credibility. Evaluates GTM approach against content-led organic distribution. Catches hand-wavy science, credential-free authority claims, and marketing dressed as education.
- **best_for:** Health product content, health claims review, DTC health GTM strategy, content-led health product launches.
- **not_for:** SEO strategy, visual design, behavioral psychology tactics, technical implementation, non-health products.

### Patrick Campbell
- **id:** patrick-campbell
- **prompt:** advisors/epch-projects/patrick-campbell.md
- **domains:** pricing, packaging, monetization, churn, retention, value-metrics, subscription
- **evaluation_expertise:** Evaluates pricing, packaging, and monetization strategy. Value metric alignment, feature differentiation across tiers, willingness-to-pay segmentation by persona. Retention mechanics — voluntary vs involuntary churn, payment recovery, cancel flow design. Catches monetization neglect and packaging misalignment.
- **best_for:** Pricing strategy, subscription packaging, paywall design, churn analysis, monetization decisions, free-to-paid conversion.
- **not_for:** Brand voice, content quality, SEO strategy, visual design, health claims.

### Joe Pulizzi
- **id:** joe-pulizzi
- **prompt:** advisors/epch-projects/joe-pulizzi.md
- **domains:** content-strategy, audience-building, content-first-business, content-tilt, content-operations
- **evaluation_expertise:** Evaluates content strategy through audience-first lens. Does the content have a clear content tilt? Is it serving the audience or selling the product? Is there a consistent publishing cadence on a focused platform? Does the content build toward a subscriber relationship rather than one-time views? Catches product-first thinking disguised as content marketing.
- **best_for:** Content strategy, audience-building plans, content calendar design, content-to-product pipeline decisions.
- **not_for:** SEO technical details, behavioral psychology, visual design, pricing mechanics.

### Rob Walling
- **id:** rob-walling
- **prompt:** advisors/epch-projects/rob-walling.md
- **domains:** bootstrapped-saas, smb-gtm, self-serve, acquisition-channels, product-market-fit
- **evaluation_expertise:** Evaluates bootstrapped SaaS viability and go-to-market strategy. Acquisition channel selection (speed, cost, scalability), pricing architecture, product-market fit stage assessment, churn benchmarks, and whether the business model works without VC. Catches building without evidence — features or products launched without validated willingness to pay.
- **best_for:** B2B SMB go-to-market, self-serve acquisition strategy, bootstrapped business viability, channel selection.
- **not_for:** Copy quality, behavioral design, SEO tactics, visual design, health-specific claims.

### Robbie Kellman Baxter
- **id:** robbie-kellman-baxter
- **prompt:** advisors/epch-projects/robbie-kellman-baxter.md
- **domains:** subscription, membership, retention, forever-promise, recurring-revenue
- **evaluation_expertise:** Evaluates whether content reflects membership thinking vs transaction thinking. Is the forever promise clear — an ongoing outcome, not a feature list? Does the content frame the offer as a relationship, not a purchase? Does onboarding content bridge the gap between sign-up and felt benefit? Catches subscription-as-billing framing — recurring price without ongoing value justification.
- **best_for:** Subscription model design, membership strategy, retention planning, onboarding content, health subscription products.
- **not_for:** SEO strategy, brand voice tone, visual design, one-time purchase products.

### Oli Gardner
- **id:** oli-gardner
- **prompt:** advisors/epch-projects/oli-gardner.md
- **domains:** landing-page-conversion, attention-ratio, conversion-centered-design, page-focus
- **evaluation_expertise:** Evaluates through Conversion-Centered Design lens. Attention ratio — ratio of interactive elements to campaign goals (ideal 1:1). Page focus — does every element serve a single conversion goal? Structural hierarchy — directional cues, encapsulation, and visual flow to CTA. Trust signals, friction reduction, benefit clarity, message match.
- **best_for:** Landing pages, conversion flows, signup pages, campaign-specific pages.
- **not_for:** Brand positioning accuracy, SEO keyword strategy, copywriting voice, long-form content.

### Joanna Wiebe
- **id:** joanna-wiebe
- **prompt:** advisors/epch-projects/joanna-wiebe.md
- **domains:** conversion-copy, voice-of-customer, headline-writing, cta-optimization
- **evaluation_expertise:** Evaluates conversion copy through Seven Sweeps lens. Headline effectiveness, CTA clarity and friction word avoidance, voice-of-customer alignment, PAS structure, specificity of claims, emotional vs rational balance, message-match between traffic source and landing page. "So what?" and "Prove it." applied to every claim.
- **best_for:** Landing page copy, email copy, ad copy, CTAs, headlines — any copy that must convert.
- **not_for:** Visual design, technical SEO, page structure/layout, behavioral science.

### Julian Shapiro
- **id:** julian-shapiro
- **prompt:** advisors/epch-projects/julian-shapiro.md
- **domains:** growth-marketing, writing-craft, content-creation
- **note:** Writes content. Not yet profiled with evaluation expertise.

### Seth Godin
- **id:** seth-godin
- **prompt:** advisors/epch-projects/seth-godin.md
- **domains:** marketing, permission-marketing, remarkable-products, tribes
- **note:** Not yet profiled with evaluation expertise.

---

## Advisors Not Yet Profiled

The following advisors have prompt files in `advisors/va-web-app/` but are not yet profiled with domains and evaluation expertise. Add entries above when they're needed for critique workflows.

andreo-spina, arielle-nissenblatt, benjamin-levine, blair-grubb, brene-brown, byron-katie, chris-voss, clayton-christensen, danny-iny, diana-chapman, don-draper, elise-darma, gabor-mate, italo-biaggioni, jasmine-star, jay-clouse, jenna-kutcher, jeremy-enns, jim-loehr, kelly-starrett, marsha-linehan, martin-seligman, matt-chapman, rachel-pedersen, roy-freeman, sean-ellis, shirley-sahrmann, steven-hayes, stuart-mcgill, sue-b-zimmerman, tim-ferriss, wise-eric
