# Live Visualization for Brainstorming — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Replace session-document-generator dispatch in brainstorming with direct HTML authoring using a CSS component library, so executives see visual artifacts evolve in real-time during brainstorming sessions.

**Source Design Doc:** `docs/plans/2026-04-14-live-visualization-design.md`

**Mockups:** `docs/mockups/live-visualization.html`

**Architecture:** The agent writes a self-refreshing HTML file to `/tmp/` during brainstorming, updating it as each design section is validated. The browser auto-reloads via a `setTimeout` script every 3 seconds. At session end, the refresh script is stripped and the file is copied to `docs/mockups/` as the permanent artifact. A single markdown file (`brainstorm-components.md`) serves as both the CSS component reference and the HTML template.

**Tech Stack:** HTML, CSS (custom classes + Tailwind CDN), Mermaid.js CDN, `file://` protocol, `open`/`xdg-open` for browser launch

---

### ✅ Task 1: Create the references directory

**Files:**
- Create: `skills/brainstorming/references/` (directory)

**Step 1: Create the directory**

```bash
mkdir -p skills/brainstorming/references
```

**Step 2: Verify**

```bash
ls skills/brainstorming/references/
```

Expected: empty directory exists.

**Step 3: Commit**

```bash
git add skills/brainstorming/references/.gitkeep
git commit -m "chore: create brainstorming references directory"
```

Note: Create a `.gitkeep` file since git doesn't track empty directories. Write an empty file at `skills/brainstorming/references/.gitkeep`.

---

### ✅ Task 2: Create the brainstorm-components.md — HTML template skeleton

**Files:**
- Create: `skills/brainstorming/references/brainstorm-components.md`

This is the first chunk of the component reference file. It contains the document header, usage instructions, and the full HTML template as a fenced code block. The template includes:

- `<!DOCTYPE html>` through `</head>` with Tailwind CDN, Mermaid CDN, and tailwind.config color tokens
- Self-refresh script wrapped in `<!-- LIVE-REFRESH-START -->` / `<!-- LIVE-REFRESH-END -->` delimiters with a 30-minute timeout (`setTimeout` that clears the reload interval after 1800000ms)
- The refresh mechanism: `setInterval(() => location.reload(), 3000)` inside a script block between the delimiters
- `<body>` skeleton with header area (title, subtitle, context line) and a placeholder comment for tab bar and content sections
- All base CSS in a `<style>` block (pulled from the mockup at `docs/mockups/live-visualization.html`):
  - Body: `background: #faf9f7`, system-ui font stack, 40px padding
  - Tab bar: `.tab-bar`, `.tab-btn`, `.tab-btn.active` (accent color `#ff6900`)
  - Sub-tab bar: `.sub-tab-bar`, `.sub-tab-btn`
  - Tab panels: `.tab-panel`, `.sub-panel` with `.active` display toggle
  - Section container: `.section` (white bg, border, 12px radius, 24px padding)
- Tab switching JavaScript functions (`switchTab`, `switchSubTab`) matching the existing mockup pattern

**Step 1: Study the existing mockup for the exact CSS and JS patterns**

Read `docs/mockups/live-visualization.html` in full. Extract:
1. The complete `<style>` block (all CSS rules)
2. The tab/sub-tab JavaScript at the bottom
3. The Tailwind config block
4. The Mermaid initialization config

**Step 2: Write the component reference file**

Write `skills/brainstorming/references/brainstorm-components.md` with this structure:

```markdown
# Brainstorm Live Visualization — Component Reference

> **For the agent:** Read this file once at the start of the visualization phase. Use the HTML template and component classes below to build the live artifact. Do not invent custom classes — use only what's documented here.

## HTML Template

Copy this template as the starting point for every live visualization. Replace `{title}`, `{subtitle}`, and `{context}` with session-specific values.

\`\`\`html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <!-- Mermaid for diagrams -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <!-- Tailwind for utility classes -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            accent: { DEFAULT: '#ff6900', hover: '#e55d00', subtle: '#fff7ed' },
            surface: '#f5f3ef',
            muted: '#f0eeeb',
            foreground: '#1a1a1a',
            secondary: '#555555',
            dimmed: '#6b7280',
            border: '#e5e7eb'
          },
          fontFamily: {
            sans: ['system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
            mono: ['Menlo', 'Consolas', 'Monaco', 'Courier New', 'monospace']
          }
        }
      }
    }
  </script>
  <!-- LIVE-REFRESH-START -->
  <script>
    (function() {
      const interval = setInterval(() => location.reload(), 3000);
      setTimeout(() => clearInterval(interval), 1800000); // stop after 30 min
    })();
  </script>
  <!-- LIVE-REFRESH-END -->
  <style>
    /* [All CSS from the mockup — body, tabs, sections, components] */
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="subtitle">{subtitle}</p>
  <p class="context">{context}</p>

  <!-- Tab bar and content panels go here -->

  <script>
    /* [Tab switching JS + Mermaid init] */
  </script>
</body>
</html>
\`\`\`
```

Fill in the complete CSS from the mockup's `<style>` block and the complete JS from the mockup's script sections. The CSS should include all component classes documented in subsequent sections of this file. The JS should include `switchTab`, `switchSubTab`, and Mermaid initialization with `securityLevel: 'loose'` and lazy rendering via `mermaid-deferred` class.

**Step 3: Verify the template is valid**

Read back `skills/brainstorming/references/brainstorm-components.md` and confirm:
- The HTML template is inside a fenced code block
- `<!-- LIVE-REFRESH-START -->` and `<!-- LIVE-REFRESH-END -->` delimiters are present
- The 30-minute timeout is present
- Color tokens match: `#faf9f7` background, `#ff6900` accent, `#e55d00` accent hover, `#fff7ed` accent subtle
- Mermaid CDN and Tailwind CDN script tags are present

**Step 4: Commit**

```bash
git add skills/brainstorming/references/brainstorm-components.md
git commit -m "feat: add brainstorm component reference with HTML template"
```

---

### ✅ Task 3: Add v1 component classes to brainstorm-components.md

**Files:**
- Modify: `skills/brainstorming/references/brainstorm-components.md` (append component documentation sections after the HTML template)

Append documentation sections for each v1 component listed in the design doc. Each section includes: component name, description, workflow step it maps to, HTML pattern with class names, and a usage example. The CSS for these components must also be included in the template's `<style>` block (added in Task 2).

**v1 Components to document (from design doc):**

1. **Phase tracker** — `<div class="phase-tracker">` with `.phase-item` and `.phase-current`. Shows current brainstorm phase.
2. **Card grid** — `<div class="card-grid">` with `.card` items. For problems, root causes, solutions, components, modules.
3. **Comparison grid** — `<div class="compare-grid compare-{n}col">`. For approach trade-offs (2-3 options).
4. **Tabbed navigation** — Already in template (`.tab-bar`, `.tab-btn`, `.sub-tab-bar`, `.sub-tab-btn`). Document the pattern and usage.
5. **Callout boxes** — `<div class="callout callout-{type}">` for decision, constraint, risk, note types.
6. **Mermaid containers** — `<div class="diagram-container"><pre class="mermaid-deferred">`. For architecture diagrams, flows, state machines.
7. **Section containers** — `<div class="section">`. Already in template CSS. Document usage.

**Deferred components** (document as "Deferred — not yet implemented"):
- Quadrant map
- Decision log

**Step 1: Design the CSS for each new component**

Study the existing mockup's visual style (colors, spacing, border-radius, font sizes) to ensure new components are visually consistent. Key design tokens to match:
- Card background: white, border `#e5e7eb`, border-radius 12px
- Accent: `#ff6900`, hover: `#e55d00`, subtle bg: `#fff7ed`
- Text: `#1a1a1a` primary, `#555555` secondary, `#6b7280` dimmed
- Spacing: 24px padding for containers, 16px gaps

**Step 2: Add component CSS to the template's `<style>` block**

Edit the HTML template in the fenced code block to include CSS rules for: `.phase-tracker`, `.phase-item`, `.phase-current`, `.card-grid`, `.card`, `.compare-grid`, `.compare-2col`, `.compare-3col`, `.callout`, `.callout-decision`, `.callout-constraint`, `.callout-risk`, `.callout-note`.

**Step 3: Append component documentation sections**

After the HTML template code block, append a `## Components` section with subsections for each component. Each subsection includes:
- Component name and description
- Workflow step it maps to
- HTML usage example (fenced code block)
- Notes on variants or conditional usage

**Step 4: Verify completeness (component class correctness check)**

Read back the file and confirm:
- All 7 v1 components have CSS in the template
- All 7 v1 components have documentation sections
- 2 deferred components are noted
- No component class is documented without a corresponding CSS rule (grep the `<style>` block for each class name referenced in the documentation sections)
- No CSS class exists in the `<style>` block without a corresponding documentation section

Note: The design doc's Testing Strategy calls for automated component class correctness checks. This manual verification step fulfills that requirement for v1. An automated script (e.g., grep-based CI check) is deferred until the component library stabilizes — the class list will change frequently during initial development.

**Step 5: Commit**

```bash
git add skills/brainstorming/references/brainstorm-components.md
git commit -m "feat: add v1 component classes and documentation to brainstorm-components"
```

---

### Task 4: Replace session-document-generator dispatch in software.md — initial visualization

**Files:**
- Modify: `skills/brainstorming/modes/software.md` (the `**Visualization (mandatory):**` section, lines 135-148)

Replace the session-document-generator dispatch block with live visualization instructions. The new block tells the agent to:

1. Read `skills/brainstorming/references/brainstorm-components.md`
2. Write initial HTML to `/tmp/brainstorm-{topic}-{timestamp}/live.html` using the template
3. Open the file in the browser: `open /tmp/brainstorm-{topic}-{timestamp}/live.html` (separate Bash call — no `&&` chaining due to auto-approve hook). If the open command fails (headless environment), log a warning and continue.
4. The self-refresh script begins the 3-second reload cycle automatically

**Step 1: Read the current content**

Read `skills/brainstorming/modes/software.md` lines 135-148 to confirm exact current content before editing.

**Step 2: Replace the dispatch block**

Replace lines 135-148 (from `**Visualization (mandatory):**` through `Do not pause for user review — the critique panel will evaluate the visuals alongside the design.`) with new content.

The new `**Visualization (mandatory):**` section should contain:

```markdown
**Visualization (mandatory):**

Every brainstorm produces a live visual artifact. After writing the design document and BEFORE the critique round, start the live visualization:

1. Read `skills/brainstorming/references/brainstorm-components.md` for the HTML template and component reference.
2. Write the initial HTML to `/tmp/brainstorm-{topic}-{timestamp}/live.html` using the template. Replace `{title}`, `{subtitle}`, and `{context}` with session-specific values. Use a timestamp (e.g., epoch seconds) to prevent collision if the same topic is brainstormed twice. Populate the initial content with the design sections validated so far.
3. Open the file in the default browser using a platform-aware pattern (separate Bash call — no `&&` chaining):
   `open /tmp/brainstorm-{topic}-{timestamp}/live.html || xdg-open /tmp/brainstorm-{topic}-{timestamp}/live.html`
   If both commands fail (headless environment), log a warning and continue — the artifact still gets written.
4. As each subsequent design section is validated in conversation, update the HTML file (Write tool) to add the new section's content. The browser picks up changes within 3 seconds via the self-refresh script.
```

**Step 3: Verify the edit**

Read back the modified lines to confirm:
- The session-document-generator dispatch is fully removed
- The new instructions reference `skills/brainstorming/references/brainstorm-components.md`
- The `/tmp/` path includes `{timestamp}` for collision prevention
- The `open || xdg-open` platform-aware pattern is present as a single Bash call (no `&&` chaining)
- The instruction to update after each validated section is present

**Step 4: Commit**

```bash
git add skills/brainstorming/modes/software.md
git commit -m "feat: replace session-document-generator dispatch with live visualization in software mode"
```

---

### Task 5: Replace post-critique visualization refresh in software.md

> **Depends on:** Task 4 (Task 4 introduces the `/tmp/` live file path that this task's pre-critique snapshot references)

**Files:**
- Modify: `skills/brainstorming/modes/software.md` (the post-critique Step 1, lines 215-230)

Replace the session-document-generator re-dispatch with the live visualization finalization process:
1. Pre-critique: copy the live file to `docs/mockups/{session-name}.html`
2. Post-critique: if the design changed, fully regenerate the HTML at `docs/mockups/{session-name}.html` from the corrected design using the component reference (not surgical edit — full rewrite)
3. Strip the `<!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END -->` block from the `docs/mockups/` copy

**Step 1: Read the current post-critique Step 1 content**

Read `skills/brainstorming/modes/software.md` lines 213-231 to confirm exact content.

**Step 2: Replace the post-critique Step 1**

Replace the content from `**Step 1 of 3 — Visualization refresh (conditional):**` through `Do not pause for user review — the critique has already validated the design content. The refresh ensures visual fidelity only.` with:

```markdown
**Step 1 of 3 — Visualization finalization:**

a. **Pre-critique copy** (do this BEFORE dispatching the critique panel): Copy the current live file from `/tmp/brainstorm-{topic}-{timestamp}/live.html` to `docs/mockups/{session-name}.html` so the critique panel can access it at its configured `visual-artifacts` path.

b. **Post-critique update** (conditional — after critique completes): If the design document was modified by fact-check corrections or user-approved critique fixes, fully regenerate the HTML at `docs/mockups/{session-name}.html` from the corrected design using `skills/brainstorming/references/brainstorm-components.md`. Do not surgically edit — do a full rewrite from the corrected design to avoid drift.

   Only skip regeneration if the design document is unchanged (all critique verdicts were APPROVE with no corrections applied).

c. **Strip the refresh script:** Verify that both `<!-- LIVE-REFRESH-START -->` and `<!-- LIVE-REFRESH-END -->` delimiters exist in `docs/mockups/{session-name}.html` before stripping. If either delimiter is missing, STOP and flag the issue — a committed artifact with an active refresh script is a silent bug. If both are present, remove the block (inclusive of delimiters). The final committed artifact must not auto-refresh.
```

**Step 3: Move the pre-critique copy instruction**

The pre-critique copy (step a above) needs to happen BEFORE the critique panel dispatch, not after it. The nested sub-tabs rule block occupies lines 150-157, and the critique panel section starts at line 159. Insert the pre-critique snapshot block after line 157 (end of nested sub-tabs rule), before line 159 (start of critique panel).

Add the pre-critique copy as a separate instruction block between the nested sub-tabs rule and "Fact-Check + Critique Panel":

```markdown
**Pre-critique snapshot:**

Before dispatching the critique panel, copy the live visualization to its permanent location so critics can access it:
1. Copy `/tmp/brainstorm-{topic}-{timestamp}/live.html` to `docs/mockups/{session-name}.html`
2. Add `**Mockups:** docs/mockups/{session-name}.html` to the design document header (write AFTER the copy so the file exists at commit time)
3. The critique panel's `visual-artifacts` config references `docs/mockups/{session-name}.html` — this copy ensures it exists at that path.
```

> **Behavioral change:** This inserts a mandatory pre-critique file copy step that doesn't exist in the current flow. If this step is skipped during execution, the critique panel's `visual-artifacts` path references a non-existent file, and critics fail silently on visual review.

Then simplify the post-critique Step 1 to only cover the conditional regeneration and stripping (remove step a from it since it moved earlier).

**Step 4: Verify the edit**

Read the modified file to confirm:
- Pre-critique snapshot instruction appears before the critique panel section
- Post-critique Step 1 handles conditional regeneration and refresh script stripping
- No references to session-document-generator remain in the post-critique section
- The critique panel's `visual-artifacts: docs/mockups/{session-name}.html` config is unchanged

**Step 5: Commit**

```bash
git add skills/brainstorming/modes/software.md
git commit -m "feat: replace post-critique session-document-generator re-dispatch with live viz finalization"
```

---

### Task 6: Replace session-document-generator dispatch in business.md — initial visualization

**Files:**
- Modify: `skills/brainstorming/modes/business.md` (the `**Visualization (conditional):**` section, lines 136-149)

Same replacement as Task 4, but preserving the conditional gate: "If the design document warrants visual artifacts..."

**Step 1: Read the current content**

Read `skills/brainstorming/modes/business.md` lines 136-149.

**Step 2: Replace the dispatch block**

Replace the session-document-generator dispatch with live visualization instructions, keeping the conditional wrapper:

```markdown
**Visualization (conditional):**

If the design document warrants visual artifacts (process flow diagrams, decision flows, data flow visualizations — most business designs will), start the live visualization:

1. Read `skills/brainstorming/references/brainstorm-components.md` for the HTML template and component reference.
2. Write the initial HTML to `/tmp/brainstorm-{topic}-{timestamp}/live.html` using the template. Replace `{title}`, `{subtitle}`, and `{context}` with session-specific values. Use a timestamp to prevent collision.
3. Open the file in the default browser using a platform-aware pattern (separate Bash call — no `&&` chaining):
   `open /tmp/brainstorm-{topic}-{timestamp}/live.html || xdg-open /tmp/brainstorm-{topic}-{timestamp}/live.html`
   If both commands fail (headless environment), log a warning and continue.
4. As each subsequent design section is validated, update the HTML file to add the new section's content. The browser picks up changes within 3 seconds.

If the design does not warrant visual artifacts, skip this section entirely and omit the `**Mockups:**` field from the design document header.
```

**Step 3: Verify the edit**

Confirm:
- Conditional gate preserved ("If the design document warrants visual artifacts")
- Skip instruction preserved for designs without visuals
- No session-document-generator references remain
- Component reference path is correct

**Step 4: Commit**

```bash
git add skills/brainstorming/modes/business.md
git commit -m "feat: replace session-document-generator dispatch with live visualization in business mode"
```

---

### Task 7: Replace post-critique visualization refresh in business.md

> **Depends on:** Task 6 (Task 6 introduces the `/tmp/` live file path that this task's pre-critique snapshot references)

**Files:**
- Modify: `skills/brainstorming/modes/business.md` (the post-critique Step 1, lines 183-198)

Same replacement as Task 5 (pre-critique snapshot + post-critique conditional regeneration + stripping), but with the business mode conditional: "Also skip if no visualization was generated."

**Step 1: Read the current content**

Read `skills/brainstorming/modes/business.md` lines 179-200.

**Step 2: Add pre-critique snapshot instruction**

Insert between the visualization section end and the critique panel start. Include the conditional: "If visualization was started..."

**Step 3: Replace the post-critique Step 1**

Replace with conditional regeneration + stripping, preserving the skip condition for designs without visuals:

```markdown
**Step 1 of 3 — Visualization finalization (conditional):**

If a live visualization was started: after the critique completes, conditionally regenerate and strip the refresh script (same process as software mode — see Task 5). If the design document was not modified, skip regeneration but still strip the refresh script from `docs/mockups/{session-name}.html`.

If no visualization was generated (design did not warrant visual artifacts), skip this step entirely.
```

**Step 4: Verify the edit**

Confirm the conditional gates are preserved and no session-document-generator references remain.

**Step 5: Commit**

```bash
git add skills/brainstorming/modes/business.md
git commit -m "feat: replace post-critique session-document-generator re-dispatch with live viz finalization in business mode"
```

---

### Task 8: Update the critique panel visual-artifacts config

**Files:**
- Modify: `skills/brainstorming/modes/software.md` (the critique panel configuration block, around line 168)
- Modify: `skills/brainstorming/modes/business.md` (the critique panel configuration block, around line 162)

The critique panel's `Visual artifacts:` config currently points to `docs/mockups/{session-name}.html`. This path remains correct (the pre-critique snapshot from Tasks 5/7 copies the live file there before critics access it). However, verify that the critic prompt templates still reference `{visual-artifacts-path}` and that no critic prompt references the session-document-generator.

**Step 1: Verify software.md critique config**

Read `skills/brainstorming/modes/software.md` lines 159-205. Confirm:
- `Visual artifacts: docs/mockups/{session-name}.html` is present
- Critic prompts reference `{visual-artifacts-path}`, not a `/tmp/` path
- No critic prompt mentions session-document-generator

**Step 2: Verify business.md critique config**

Read `skills/brainstorming/modes/business.md` lines 153-177. Same checks.

**Step 3: If any references to session-document-generator exist in critic prompts, remove them**

Search both files for "session-document-generator" and remove any remaining references.

**Step 4: Commit (only if changes were made)**

```bash
git add skills/brainstorming/modes/software.md skills/brainstorming/modes/business.md
git commit -m "fix: remove stale session-document-generator references from critique config"
```

---

### Task 9: Update nested sub-tabs rule and verify cross-references

> **Depends on:** Tasks 4-8 (verifies and cleans up references introduced by earlier tasks; both mode files were last modified in Task 8)

**Files:**
- Modify: `skills/brainstorming/modes/software.md` (nested sub-tabs rule, line 150)
- Read-only verification across all modified files

**Step 1: Verify cross-references**

Grep all `skills/brainstorming/**/*.md` files for:
- `session-document-generator` — should only appear in the "What Stays Unchanged" context (if any) or in the nested sub-tabs rule note that says "applies to session-document-generator AND mockup-generator dispatches". Since we're removing session-document-generator dispatch from brainstorming, update the nested sub-tabs rule to remove the "session-document-generator AND" prefix, leaving just "mockup-generator dispatches" (the mockup-generator is still used during Q&A phase).
- `brainstorm-components.md` — should appear in the new visualization sections of both mode files
- `LIVE-REFRESH` — should appear in the component reference and in the post-critique finalization sections

**Step 2: Update the nested sub-tabs rule in software.md**

In `software.md` lines 150-157, the nested sub-tabs rule says "applies to session-document-generator AND mockup-generator dispatches". Update this to: "applies to mockup-generator dispatches and live visualization updates" since session-document-generator is no longer dispatched from brainstorming.

Note: `business.md` line 151 has a simpler version of this rule that does not reference session-document-generator — no update needed there.

**Step 3: Fix any broken references found**

**Step 4: Commit (only if changes were made)**

```bash
git add skills/brainstorming/modes/software.md skills/brainstorming/modes/business.md
git commit -m "fix: update nested sub-tabs rule to reference live visualization instead of session-document-generator"
```

---

### Task 10: Remove .gitkeep and verify final state

**Files:**
- Modify: `skills/brainstorming/references/.gitkeep` (remove — no longer needed since `brainstorm-components.md` exists)

**Step 1: Remove .gitkeep**

```bash
git rm skills/brainstorming/references/.gitkeep
```

**Step 2: Run final verification**

- Glob `skills/brainstorming/references/*` — should contain only `brainstorm-components.md`
- Grep all `skills/brainstorming/modes/*.md` for `session-document-generator` — confirm it only appears in contexts where it's still used (e.g., mockup-generator note) or not at all
- Read the first 20 lines of both mode files to confirm no structural damage

**Step 3: Commit**

```bash
git commit -m "chore: remove .gitkeep, brainstorm-components.md now populates references/"
```

Note: The `git rm` in Step 1 already staged the removal. Do not run `git rm` again here.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Component reference file format | Single markdown file with embedded HTML template | Separate HTML template file + separate docs file |
| 2 | Task ordering for mode file edits | Complete each mode file (initial + post-critique) before moving to next | Group by replacement type across files |
| 3 | Pre-critique snapshot placement | Separate instruction block before critique panel | Inside post-critique Step 1 |
| 4 | CSS authoring approach | Extract CSS from existing mockup | Write CSS from scratch based on design tokens |
| 5 | .gitkeep lifecycle | Create in Task 1, remove in Task 10 | Skip .gitkeep, create directory and file together in Task 2 |

### Appendix: Decision Details

#### Decision 1: Component reference file format
**Chose:** Single markdown file with embedded HTML template
**Why:** The design doc explicitly specifies this architecture (Decision 9): "One file = no drift between template and docs." The component documentation and the HTML template it references need to stay in sync. A single file means the agent reads one file and gets both the template to copy and the component reference to consult. Two files would risk them diverging.
**Alternatives rejected:**
- Separate HTML template + docs file: Creates drift risk. The agent would need to read two files and mentally merge them. The design doc explicitly rejected this.

#### Decision 2: Task ordering for mode file edits
**Chose:** Complete each mode file before moving to the next: software.md initial dispatch (Task 4) → software.md post-critique (Task 5) → business.md initial dispatch (Task 6) → business.md post-critique (Task 7)
**Why:** Each mode file has two replacement sites (initial dispatch and post-critique). Completing both replacements in one file before moving to the next keeps context local — the executor finishes software.md fully, then applies the same pattern to business.md. The post-critique step depends on the initial dispatch step within the same file (it references the `/tmp/` path introduced by the initial dispatch).
**Alternatives rejected:**
- Group by replacement type (all initial dispatches first, then all post-critique): Would mean touching each file twice in non-adjacent tasks, and the executor would lose context about the specific file's structure between passes.

#### Decision 3: Pre-critique snapshot placement
**Chose:** Separate instruction block between visualization and critique panel sections
**Why:** The design doc's data flow shows the pre-critique copy happening before critique dispatch. Embedding it in the post-critique section would be too late — critics need the file to exist at `docs/mockups/` when they run. A separate block makes the ordering explicit and hard to miss.
**Alternatives rejected:**
- Inside post-critique Step 1: Wrong timing — critics would try to read a file that doesn't exist yet.

#### Decision 4: CSS authoring approach
**Chose:** Extract CSS from existing mockup at `docs/mockups/live-visualization.html`
**Why:** The mockup already contains production-quality CSS for tabs, sections, and all base components. It uses the exact design tokens specified in the design doc. Extracting ensures visual consistency with the existing mockup ecosystem (7 other mockup files use the same patterns). Writing from scratch would risk subtle visual differences.
**Alternatives rejected:**
- Write from scratch: Unnecessary work with drift risk. The mockup is the source of truth for visual style.

#### Decision 5: .gitkeep lifecycle
**Chose:** Create `.gitkeep` in Task 1, remove it in Task 10 after `brainstorm-components.md` exists
**Why:** Git doesn't track empty directories. Task 1 creates the directory structure, Tasks 2-3 populate it. Without `.gitkeep`, Task 1's commit would have nothing to commit. The cleanup in Task 10 keeps the repo tidy.
**Alternatives rejected:**
- Skip `.gitkeep`, create directory implicitly in Task 2: Would mean Task 1 isn't independently commitable. Bite-sized commits require each task to produce a commitable unit.
