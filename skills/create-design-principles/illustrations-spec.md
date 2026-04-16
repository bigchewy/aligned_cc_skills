# Illustrations Spec

Output schema for the Illustrations section of the generated `design-principles.md`. SKILL.md points here when Phase 1 Q6 confirms the project needs decorative illustrations. Place the generated section between Iconography and Questions to Ask.

Illustrations are atmosphere, not UI. The craft is in restraint — generous negative space, a small element count ceiling, a single color at varying opacity. If you're adding more, you're overworking it.

## Opening Paragraph (load-bearing)

Start the generated Illustrations section with a 1–2 sentence paragraph that names the **canonical reference file** by path, element count, and line count (e.g., "The canonical reference is `public/hero-botanical.svg` — 15 elements, 64 lines, single color"). Every downstream decision anchors on this reference.

If no reference exists yet, state that explicitly and require that the first illustration the project ships becomes canonical. Do not leave the slot blank.

## Required Subsections

Generate these in order.

### Style

Short prose covering:

- **Feel** — the emotional register (ethereal/delicate; or bold/graphic; or whatever fits)
- **Approach** — strokes vs fills, line weight, whether shapes are closed or tapered
- **Color** — single color or palette; if single, name the token and say why restraint matters
- **Negative space** — what percentage of the viewBox remains empty; frame emptiness as the aesthetic, not a gap
- **Element count** — commit to a ceiling (e.g., "15–20 max") so restraint is enforceable

### Opacity Tiers

Three-tier table:

| Tier | Opacity | Usage |
|------|---------|-------|
| Standalone | 0.15–0.40 | Visible, independent use |
| Watermark | 0.04–0.08 | Background behind content |
| Glow | 0.02–0.05 | Soft halo behind the form |

Immediately after the table, include a short paragraph clarifying: **opacity is applied via CSS at deploy time, not baked into the SVG.** One illustration file serves all three tiers — author it at standalone opacity, then reduce via CSS when the deployment context calls for watermark or glow. This prevents a proliferation of near-duplicate files and keeps the source asset simple.

### Construction Patterns

Table mapping element types to techniques. Typical rows for botanical subject matter:

| Element | Technique |
|---------|-----------|
| Stems, branches | Thin strokes (2–4px), `stroke-linecap="round"`, cubic bezier curves |
| Leaves | Single filled bezier path per leaf — no internal veins, no layered fills |
| Accent leaves | Smaller filled paths at lower opacity than main leaves |
| Tendrils, roots | Thin strokes (1.5–2px) trailing off organically |
| Background glow | Single `<circle>` at glow-tier opacity, large radius, centered behind the form |

Adjust the rows to match the project's subject matter — geometric illustrations won't have "leaves," abstract ones won't have "stems." Keep the column structure (Element / Technique).

### Technical Spec

Table with these rows:

| Property | Value |
|----------|-------|
| ViewBox | Exact dimensions (e.g., `0 0 800 600` for hero/background, `0 0 400 400` for standalone) |
| Fill | Single color hex or token |
| Stroke | Same color as fill; `stroke-linecap="round"` required |
| Location (source) | Project-specific path for SVG sources |
| Reference implementation | Path to the canonical SVG named in the opening paragraph |

### Anti-Patterns

Bulleted list. Always flag these seven traps:

- Multiple overlapping shapes to simulate depth (use opacity tiers instead)
- Any single element above 0.5 opacity (breaks ethereal quality when the style calls for it)
- Internal detail on simple shapes: veins, texture, layered fills, highlight paths
- More than the declared element-count ceiling (if you're adding more, you're overworking it)
- Multiple colors in one illustration
- Filling more than ~40% of the viewBox
- Complex multi-path shapes where one simple path would do

Add project-specific anti-patterns on top of these seven when the product has its own failure modes.

### Illustrations vs Icons

**Only generate this subsection if the project's design-principles.md also has an Iconography section.** Otherwise omit it — there's nothing to contrast against.

| | Icons | Illustrations |
|---|---|---|
| Scale | Small viewBox (e.g., 32×32) | Large viewBox (e.g., 400×400 to 800×600) |
| Strokes | Forbidden — filled shapes only | Required for stems, lines, tendrils |
| Opacity | Multi-tier hierarchy within one icon | 3-tier deploy-context system |
| Element count | 3–6 paths | 15–20 elements |
| Purpose | UI symbols | Decorative atmosphere |
| Color | `currentColor` (inherits) | Hardcoded token |

Immediately after the table, add prose calling out that **illustrations deliberately invert the icon rules** — specifically, icons forbid strokes for the organic-fill look, while illustrations require thin strokes with `stroke-linecap="round"` for stems. Name this inversion explicitly so a future designer doesn't "correct" it back to the icon rule.
