<!-- Mode file: Read into context by the create-image router. Do not add YAML frontmatter. -->

# Illustration Mode

Generate decorative illustrations (botanical, organic, atmospheric) that
match a project's existing illustration style, using construction patterns
from `design-principles.md` and reference implementation analysis.

Illustrations are not diagrams and not icons. They are larger-format
decorative art — hero backgrounds, watermarks, section dividers — where
negative space, restraint, and organic construction matter more than
literal representation or information density.

## Step 1: Read Existing Artifacts (mandatory)

The router has already located the project's `design-principles.md` and
passed its path.

**1a. Read the Illustrations section:**
Read the design-principles.md file. Find the Illustrations section. If no
Illustrations section exists, STOP and tell the user:
"The project's design-principles.md has no Illustrations section.
Decorative illustrations are a deliberate product decision — many products
shouldn't have them. To add a spec, either (a) run
`/aligned:create-design-principles` and answer YES when it asks whether
the product needs decorative illustrations (it may push back — that's the
point), or (b) add an Illustrations section manually with subsections for
Style, Opacity Tiers, Construction Patterns, Technical Spec, and
Anti-Patterns."

Extract from this section:
- Opacity tiers (which opacity values are allowed and how they're used —
  typically Standalone, Watermark, Glow tiers)
- Construction patterns (stroke vs fill technique per element type,
  linecap rules, path complexity)
- Element count budget (max elements per illustration)
- Negative space budget (target ratio of untouched background)
- Anti-patterns (what the spec explicitly forbids — overworked detail,
  blobby fills, etc.)
- Reference implementation path (the canonical style anchor, if named in
  the Technical Spec table)

**1b. Read reference implementation:**
If the Illustrations section names a reference implementation (e.g.,
`public/hero-botanical.svg`), Read it. This file is the style anchor.

Analyze:
- Total element count
- Opacity values actually used
- Stroke-vs-fill ratio (how many elements are strokes only, how many are
  fills, any mixed)
- Path complexity per element (are leaves single short bezier curves, or
  multi-path layered shapes?)
- Negative space ratio (approx fraction of viewBox that is background /
  untouched)

If no reference is named, Glob for existing illustrations in these
directories, in order: `brand/assets/images/`, `public/`,
`src/assets/illustrations/`, `assets/illustrations/`. Use the first
directory that contains decorative `.svg` files (exclude icons — skip
anything under `/icons/` subpaths). Read 2-3 and perform the same
analysis. If none exist anywhere, STOP and ask the user: "No existing
illustrations were found and no reference implementation is named in the
design principles. This generation will set the canonical style for the
project. Proceed with the defaults in Step 2c, or would you like to
provide reference images first?"

**1c. Extract output location:**
From the design-principles.md Technical Spec table, extract the
illustration source directory.

If the Technical Spec table is missing this field, fall back to Glob
probing in this order and use the first directory that exists:
`brand/assets/images/`, `public/`, `src/assets/illustrations/`,
`assets/illustrations/`. If none exist, ask the user for the output
location.

## Step 2: Generate

**2a. Apply construction constraints** extracted from Step 1:

- **Element count:** stay within the spec's range. If the reference has
  12 elements, don't generate 40.
- **Opacity:** use only values within the spec's tiers. Do not invent
  intermediate opacities.
- **Stroke-vs-fill technique:** match the reference. If the reference
  uses thin strokes for stems and simple filled paths for leaves, do
  that — don't layer opaque shapes to "add depth."
- **Path complexity:** match per-element complexity. If reference leaves
  are single short bezier paths, don't create multi-path layered leaves.
- **Negative space:** match the reference's ratio. Decorative
  illustrations breathe — resist the urge to fill the canvas.

**2b. Avoid the anti-patterns** named in the spec. Common ones:
- Overworked detail (adding veins, textures, gradients "for realism")
- Blobby opaque fills stacked on top of each other
- Symmetric repetition that reads as a pattern rather than an
  illustration
- Diagram-mode holdovers (no boxes, no title bars, no arrows, no
  connector lines)

**2c. Apply fallback defaults** for any dimension the spec is silent on:
- `viewBox="0 0 800 600"` for hero/background illustrations;
  `viewBox="0 0 400 400"` for standalone feature illustrations
- Element count: 15-20 elements max
- Negative space: 60-70% of viewBox untouched
- Opacity tiers (three-tier system):
  - Standalone: 0.15-0.40 (independent use)
  - Watermark: 0.04-0.08 (behind content)
  - Glow: 0.02-0.05 (soft halos)
- Single color at varying opacity — not a palette. Prefer a design-token
  reference (accent or foreground); a single hardcoded hex is acceptable
  if the spec's Technical Spec table uses one
- Strokes: `stroke-linecap="round"` required. Stroke-width 2-4px for
  primary strokes (stems, branches); 1.5-2px for fine strokes (tendrils,
  roots)
- Element vocabulary: `<path>` for organic subjects. A single `<circle>`
  is acceptable for a background glow. No `<rect>`, no `<line>`, no
  `<polygon>`

## Step 3: Output

Using the path extracted in Step 1c:

**3a. Write SVG** to the project's illustration source directory.

**3b. No React component wrapper.** Unlike icon mode, decorative
illustrations are typically referenced directly as `.svg` files (via
`<img>`, CSS `background-image`, or framework-specific static asset
imports). Do not generate a `.tsx` wrapper.

**3c. No barrel file update.** Illustrations are not enumerated in an
index like icons are.

**3d. Update an illustrations manifest** only if one exists in the
directory (e.g., `ILLUSTRATIONS.md`, `README.md`). Follow the existing
format. Do not create a new manifest file.
