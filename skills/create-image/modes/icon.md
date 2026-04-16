<!-- Mode file: Read into context by the create-image router. Do not add YAML frontmatter. -->

# Icon Mode

Generate brand icons that match a project's existing icon style, using
construction patterns from `design-principles.md` and existing icon analysis.

## Step 1: Read Existing Artifacts (mandatory)

The router has already located the project's `design-principles.md` and
passed its path.

**1a. Read the Iconography section:**
Read the design-principles.md file. Find the Iconography section. If no
Iconography section exists, STOP and tell the user:
"The project's design-principles.md has no Iconography section. Add one
manually or run `/aligned:create-design-principles` to regenerate."

**1b. Read existing icons:**
Glob for existing SVG icons in the project's icon directory. Check these
paths in order: `brand/icons/`, `public/icons/`, `src/icons/`,
`assets/icons/`. Use the first directory that contains `.svg` files.

Read all of them to analyze construction patterns.

For projects with more than 20 icons: read 3 from each category listed in
the icon registry file, up to 15 total.

**1c. Read the icon registry:**
Look for an icon registry file (e.g., `ICONS.md`, `icons/README.md`, or a
similar manifest in the icon directory). Read it if one exists.

**1d. Extract output locations:**
From the design-principles.md Technical Spec table, extract:
- SVG source directory (where raw `.svg` files live)
- React component directory (where `.tsx` wrappers live)
- Barrel file path (the `index.ts` that re-exports all icons)

If the Technical Spec table is missing these fields, ask the user for
output locations.

## Step 2: Generate

**2a. Analyze construction patterns** from the icons read in Step 1b:
- Path count (how many `<path>` elements per icon)
- Opacity tiers (which opacity values are used and how)
- Shape vocabulary (organic curves vs geometric primitives)
- Abstraction level (literal vs symbolic representations)

**2b. Generate the new icon** following the project's spec from Step 1a.
Apply these construction constraints:
- Match the path count range observed in existing icons
- Use only opacity values from the project's tier system
- Use the same shape vocabulary (e.g., no `<rect>` or `<line>` for primary
  shapes if existing icons use only `<path>`)
- Match the abstraction level of existing icons

**2c. Apply fallback defaults** for any dimension the project's spec is
silent on:
- `viewBox="0 0 32 32"`
- `fill="currentColor"`
- 3-6 paths per icon
- 4-tier opacity system: 1.0, 0.4-0.55, 0.15-0.3, 0.12-0.15

## Step 3: Output Pipeline

Using the paths extracted in Step 1d:

**3a. Write SVG** to the project's icon source directory.

**3b. Write React component** to the project's component directory.
Follow the pattern of existing React icon components in the project. If no
pattern exists, use a simple functional component that renders the SVG
inline with `width`, `height`, and `className` props.

**3c. Update barrel file** — add the new component export to the barrel
file. Do not fix pre-existing gaps in the barrel file — just register the
new icon.

**3d. Update icon registry** if one exists — add an entry for the new icon
following the existing format.
