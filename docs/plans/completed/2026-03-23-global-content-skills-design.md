# Design: Global Content Generation Skills

**Goal:** Move 3 content generation skills from `dispatch-tracker/skills/` to `aligned_cc_skills/skills/` so they're globally available via the Aligned plugin. Any project with a `brand/CLAUDE.md` manifest can use them.

**Success criteria:**
- All 3 skills (`generate-deck`, `generate-blog-post`, `generate-one-pager`) live in `aligned_cc_skills/skills/`
- Skills contain zero brand-specific language (no DispatchTrack references)
- Skills retain their opinionated narrative frameworks (Dunford 8-step, PIEI)
- Skills discover brand context via `brand/CLAUDE.md` in the consuming project
- Both dispatch-tracker and ewp-site can invoke the skills immediately after migration
- Existing eval scenarios updated to reference `brand/CLAUDE.md`

## Decision Log

| # | Decision | Chosen | Alternatives Considered | Rationale |
|---|----------|--------|------------------------|-----------|
| 1 | Which skills to move | All 3 (deck, blog, one-pager) | Just the 2 working ones | One-pager is being completed in parallel; plan assumes it's done before execution |
| 2 | How opinionated | Framework-opinionated, brand-agnostic | Fully generic; keep brand-specific local copies | Frameworks (Dunford, PIEI) are good methodology, not brand-specific. Brand context belongs in `brand/` |
| 3 | Brand discovery mechanism | Bare relative path `brand/CLAUDE.md` with halt guard | Glob-based search; configurable path | Matches existing aligned skill conventions (fixed known path + halt if missing) |
| 4 | Reviewer panels | Hardcoded per skill (see below) | Brand-manifest-driven; hardcoded with override | Reviewers are part of the methodology, not the brand |
| 5 | Brand manifest filename | `CLAUDE.md` | `INDEX.md`, `Claude.md` | Consistent with project-level CLAUDE.md convention. Note: Claude does NOT auto-load subdirectory CLAUDE.md files — this is purely a naming convention for discoverability |
| 6 | Blog framework portability | PIEI is the methodology; consuming projects adopt it | Skill reads project-local framework; fully generic | User decision: PIEI is opinionated and valuable. ewp-site's blog skeleton should be updated to align with PIEI |

### Reviewer Panels per Skill

**generate-deck:**
- April Dunford — Positioning Expert (framework adherence, differentiation claims)
- Shirin Oreizy — Behavioral Scientist (decision architecture, narrative psychology)
- Buyer Persona Panel — composite personas per stakeholder

**generate-blog-post:**
- Positioning Expert (framework adherence, Insight collapse detection)
- Editorial/Brand Voice (tone, register, brand ratio)
- Audience Personas (vertical-specific language and pain points)

**generate-one-pager:**
- TBD (will be defined when the skill is completed)

## Scope

### In Scope

1. **Copy 3 SKILL.md files** from `dispatch-tracker/skills/` to `aligned_cc_skills/skills/`
2. **Generalize each SKILL.md:**
   - Replace all DispatchTrack-specific language with brand-manifest-driven instructions
   - Replace `brand/INDEX.md` references with `brand/CLAUDE.md`
   - Add halt guard: if `brand/CLAUDE.md` doesn't exist, halt with setup instructions
   - Make audience/vertical handling dynamic (read what's available from manifest, don't assume specific verticals)
   - Strip hardcoded brand colors/fonts from slide design brief (Step 4b-ii in generate-deck) — replace with "read visual identity values from `brand/guidelines/visual-identity.md`"
   - Keep narrative frameworks (Dunford 8-step, PIEI) embedded in the skill
   - Keep reviewer panel compositions hardcoded (per skill, see above)
   - Keep quality gates and critique log format
3. **Rename dispatch-tracker manifest:** `brand/Claude.md` → `brand/CLAUDE.md`
4. **Update eval scenarios:** Update references from `brand/INDEX.md` to `brand/CLAUDE.md` in dispatch-tracker's `e2e/scenarios/`
5. **Update ewp-site blog skeleton:** Align `brand/templates/blog-post/skeleton.md` with PIEI methodology
6. **Remove skills from dispatch-tracker** after verifying they work from the plugin

### Out of Scope

- Building the one-pager skill (in progress elsewhere)
- Creating a brand scaffold skill (future enhancement)
- Modifying the reviewer panel advisors
- Changing output/learnings directory conventions

## Architecture

### Skill Location

```
aligned_cc_skills/skills/
  generate-deck/SKILL.md
  generate-blog-post/SKILL.md
  generate-one-pager/SKILL.md
```

Invoked as `/aligned:generate-deck`, `/aligned:generate-blog-post`, `/aligned:generate-one-pager` from any project with the Aligned plugin enabled.

### Brand Context Contract

Every consuming project must have:

```
{project-root}/
  brand/
    CLAUDE.md              # Manifest — REQUIRED, skill halts without this
    guidelines/            # Brand rules (voice, terminology, positioning, etc.)
    personas/              # Buyer/audience personas (optional)
    templates/             # Content skeletons and examples (optional)
    assets/                # Visual files (optional)
```

Only `brand/CLAUDE.md` is mandatory. The skill reads the manifest to discover available files and adapts when optional files are missing.

### Required vs Optional Brand Files per Skill

**generate-deck:**
| File | Required? | Behavior if missing |
|------|-----------|-------------------|
| `brand/CLAUDE.md` | Required | Halt with setup instructions |
| `brand/guidelines/brand-voice.md` | Required | Halt — cannot generate on-brand content without voice |
| `brand/guidelines/messaging-framework.md` | Required | Halt — value props drive deck narrative |
| `brand/guidelines/visual-identity.md` | Recommended | Skip slide design brief; output markdown only |
| `brand/guidelines/competitive.md` | Optional | Skip competitive positioning slides |
| `brand/guidelines/proof-points.md` | Optional | Skip proof/social-proof slides |
| `brand/guidelines/terminology.md` | Optional | No terminology enforcement |
| `brand/personas/` | Optional | Skip buyer-persona-specific tuning in review panel |
| `brand/guidelines/audiences/` | Optional | Generate without vertical-specific language |
| `brand/templates/deck/framework.md` | Optional | Use skill-embedded Dunford 8-step as default |
| `prospects/{slug}.md` | Optional | Prompt user for prospect context inline |

**generate-blog-post:**
| File | Required? | Behavior if missing |
|------|-----------|-------------------|
| `brand/CLAUDE.md` | Required | Halt with setup instructions |
| `brand/guidelines/brand-voice.md` | Required | Halt — cannot generate on-brand content without voice |
| `brand/guidelines/messaging-framework.md` | Recommended | Generate without value-prop integration |
| `brand/guidelines/terminology.md` | Optional | No terminology enforcement |
| `brand/guidelines/proof-points.md` | Optional | Skip proof-point integration |
| `brand/guidelines/competitive.md` | Optional | Skip competitive context |
| `brand/guidelines/audiences/` | Optional | Generate for general audience |
| `brand/templates/blog-post/framework.md` | Optional | Use skill-embedded PIEI as default |

### Brand Discovery Flow

1. Skill is invoked from consuming project (e.g., ewp-site)
2. Skill reads `brand/CLAUDE.md` (relative to project root)
3. If missing → halt with message: "No brand context found. This skill requires a `brand/` directory with a `brand/CLAUDE.md` manifest at the project root."
4. If found → parse manifest, check for required files (per skill matrix above), halt if required files missing
5. Load available optional files, note which are absent
6. Proceed with framework-driven generation, skipping quality gates tied to absent optional files

### What Lives Where

| Content | Location | Why |
|---------|----------|-----|
| Narrative frameworks (Dunford, PIEI) | Skill SKILL.md | Methodology — portable across brands |
| 4-step workflow (Input → Generate → Review → Deliver) | Skill SKILL.md | Process — portable across brands |
| Reviewer panel composition | Skill SKILL.md | Methodology — part of the quality process |
| Quality gates | Skill SKILL.md | Standards — portable across brands |
| Brand voice, terminology | `brand/guidelines/` | Brand-specific |
| Buyer/audience personas | `brand/personas/` | Brand-specific |
| Content templates and examples | `brand/templates/` | Brand-specific |
| Messaging, positioning, competitive | `brand/guidelines/` | Brand-specific |
| Proof points, credentials | `brand/guidelines/` | Brand-specific |
| Visual identity (colors, fonts, spacing) | `brand/guidelines/` | Brand-specific |
| Output files | `output/` at project root | Project-specific |
| Critique logs | `learnings/` at project root | Project-specific |
| Prospect files (decks only) | `prospects/` at project root | Project-specific |

### Generalization Changes per Skill

**generate-deck:**
- Strip: "DispatchTrack narrative arc", specific verticals, DispatchTrack color/font references
- Strip: Hardcoded hex codes, font names, and "DispatchTrack Blue" from slide design brief (Step 4b-ii) — replace with instruction to read values from `brand/guidelines/visual-identity.md`
- Replace: "Read audience profiles listed in `brand/CLAUDE.md`" instead of hardcoded vertical names
- Keep: Dunford 8-step arc instructions, 3-reviewer panel (Dunford + Oreizy + Buyer Personas), quality gates, critique log format
- Adapt: If manifest has no audience profiles, generate without audience-specific tuning (don't halt). If no visual-identity file, output markdown only without slide design brief.

**generate-blog-post:**
- Strip: DispatchTrack terminology, specific vertical references, DispatchTrack proof-point references
- Replace: "Read proof points from `brand/guidelines/proof-points.md`" instead of hardcoded stats
- Keep: PIEI 8-element arc instructions, 3-reviewer panel (Positioning + Editorial/Brand Voice + Audience Personas), quality gates, critique log format
- Adapt: If manifest has no proof points, generate without proof-point integration (don't halt). If no audience profiles, generate for general audience.

**generate-one-pager:**
- Assumed complete before execution. Same generalization pattern as above.

### Consuming Project Readiness

| Project | `brand/CLAUDE.md` | Action Needed |
|---------|---|---|
| dispatch-tracker | Has `brand/Claude.md` | Rename to `brand/CLAUDE.md` |
| ewp-site | Has `brand/CLAUDE.md` | Update `brand/templates/blog-post/skeleton.md` to align with PIEI methodology |

### Testing

Testing follows the existing e2e eval pattern. After migration:
1. Update all eval scenarios in `dispatch-tracker/e2e/scenarios/` to reference `brand/CLAUDE.md` instead of `brand/INDEX.md`
2. Invoke `/aligned:generate-blog-post` from ewp-site with a test topic
3. Verify it reads `brand/CLAUDE.md`, loads ewp-site brand context, generates PIEI-structured output
4. Invoke `/aligned:generate-deck` from dispatch-tracker
5. Verify it still works with dispatch-tracker's brand context
6. Verify halt guard works by invoking from a project without `brand/CLAUDE.md`
7. Verify graceful degradation by invoking from a project with only required files (no optional files)
