# Diagram Documentation Standards Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Consolidate brainstorming visual artifacts from file-per-diagram sprawl into single tabbed HTML documents per session, orchestrated by a new session-document-generator agent.

**Source Design Doc:** `docs/plans/2026-03-22-diagram-documentation-standards-design.md`

**Architecture:** A new session-document-generator agent orchestrates existing diagram agents (flowchart-generator, architecture-diagram-generator, mockup-generator) via a "fragment mode" added to each. Fragment mode returns structured data (title, description, bullets, diagram markup) instead of writing standalone HTML files. The orchestrator assembles all fragments into a single tabbed HTML document with an overview tab, grouped navigation, lazy Mermaid rendering, and clickable overview nodes. A Mermaid verification sub-agent validates all diagram blocks before presenting the output.

**Tech Stack:** Markdown agent definitions, Mermaid.js (CDN), hand-coded SVG, Tailwind CSS (CDN), HTML/CSS/JS

---

### ✅ Task 1: Add "Diagram Documentation Principles" section to global design-principles.md

**Files:**
- Modify: `~/.claude/docs/design/design-principles.md` (append new section before "Anti-Patterns")

**Step 1: Write the new section**

Add a `## Diagram Documentation Principles` section with the 8 rules from the design doc. Insert it between the "Diagram Conventions" section and the "Anti-Patterns" section. The section should contain:

```markdown
## Diagram Documentation Principles

These rules apply to all diagram documents generated during brainstorming sessions. Agents and skills reference this section for consistent document structure.

### 1. One file per brainstorming session
All diagrams from a session are consolidated into `docs/mockups/{session-name}.html`. No file-per-diagram sprawl.

### 2. Grouped tab navigation
Top-level tabs organize by topic or diagram type. Topics with sub-detail (e.g., a workflow with multiple steps) get a second level of tabs within. Every document has an Overview tab as the default view.

### 3. Overview tab shows the end-to-end flow
A `graph LR` Mermaid diagram with one node per major topic. Clickable nodes navigate to the corresponding detail tab (with visible hover affordance). Keep it to 4-7 nodes maximum.

### 4. Left-to-right flow
All Mermaid diagrams use `graph LR` unless the content has parallel branches that require `graph TD`. Linear processes always flow left to right.

### 5. Simple diagrams, rich text
Each detail tab has three layers: (1) a heading with badge, (2) a description paragraph + bullet points with bolded key terms, (3) a focused Mermaid or SVG diagram with 4-6 nodes. The text carries the detail; the diagram carries the shape. Tables may follow for structured data.

### 6. Accent color for emphasis, not decoration
Most nodes are neutral (white/muted fills). One or two key nodes per diagram use the orange accent (#e8762b) to draw the eye. Never color every node differently.

### 7. Lazy rendering for hidden tabs
Only the overview Mermaid diagram renders on page load. Detail tab diagrams use `mermaid-deferred` class and render on first tab click. `startOnLoad: false` + `securityLevel: 'loose'`. No `call` keyword in click directives (breaks Mermaid v11.13). Deferred rendering includes try/catch with visible error display on failure.

### 8. Self-contained
Every file works when opened directly in a browser. Mermaid loaded via CDN. No build step, no imports.
```

**Step 2: Verify the edit**

Read `~/.claude/docs/design/design-principles.md` and confirm the new section exists between "Diagram Conventions" and "Anti-Patterns".

**Step 3: Commit**

```bash
git -C ~/.claude add docs/design/design-principles.md
git -C ~/.claude commit -m "docs: add Diagram Documentation Principles to global design-principles"
```

---

### ✅ Task 2: Add fragment mode to flowchart-generator agent

**Files:**
- Modify: `agents/flowchart-generator.md` (add "Fragment Mode" section after "After Generating")

**Step 1: Write the fragment mode section**

Append the following section to the end of `agents/flowchart-generator.md`:

```markdown
## Fragment Mode

When dispatched by the session-document-generator with the phrase "Return fragments, do not write HTML files" in the prompt, return structured content instead of writing a standalone HTML file.

**Fragment output format** (return as a fenced code block with language `fragment-json`):

```fragment-json
{
  "title": "Process Flow Title",
  "description": "1-2 sentence description of what this diagram shows.",
  "bullets": [
    "**Key term 1:** explanation",
    "**Key term 2:** explanation"
  ],
  "diagram_type": "mermaid",
  "diagram_markup": "graph LR\n    A([Start]) --> B[Step 1]\n    B --> C{Decision?}\n    ...\n    style A fill:#f0eeeb,...",
  "suggested_badge": "Flow",
  "sub_tabs": null
}
```

**Fields:**
- `title`: Short descriptive title for the tab heading
- `description`: 1-2 sentences for the text layer below the heading
- `bullets`: Array of markdown bullet points with bolded key terms (for the "rich text" layer per Principle 5)
- `diagram_type`: Always `"mermaid"` for this agent
- `diagram_markup`: Raw Mermaid code (no `<pre>` wrapper). Use `graph LR` per Principle 4 unless parallel branches require `graph TD`. Apply semantic color styles to every node.
- `suggested_badge`: Short label for a badge next to the tab heading (e.g., "Flow", "Pipeline", "Decision Tree")
- `sub_tabs`: If the flow has distinct phases (>6 nodes total), return an array of fragment objects (same schema minus `sub_tabs`) — one per phase. The orchestrator renders these as nested sub-tabs. Otherwise `null`.

**Rules in fragment mode:**
- Do NOT write any HTML files
- Do NOT open anything in the browser
- Do NOT include `<pre>`, `<script>`, or any HTML wrapper — just the raw diagram code
- Still read design-principles.md for color tokens and apply them in Mermaid style directives
- Still follow all Mermaid diagram patterns and semantic color rules from this agent
- Keep diagrams to 4-6 nodes per fragment (split into sub_tabs if more)
- Read the "Diagram Documentation Principles" section in design-principles.md and follow all 8 rules

**Standalone mode** (default, current behavior) is unchanged — when not dispatched in fragment mode, produce full self-contained HTML files as before.
```

**Step 2: Verify the edit**

Read `agents/flowchart-generator.md` and confirm the "Fragment Mode" section is present at the end.

**Step 3: Commit**

```bash
git add agents/flowchart-generator.md
git commit -m "feat: add fragment mode to flowchart-generator agent"
```

---

### ✅ Task 3: Add fragment mode to architecture-diagram-generator agent

**Files:**
- Modify: `agents/architecture-diagram-generator.md` (add "Fragment Mode" section after "After Generating")

**Step 1: Write the fragment mode section**

Append the following section to the end of `agents/architecture-diagram-generator.md`:

```markdown
## Fragment Mode

When dispatched by the session-document-generator with the phrase "Return fragments, do not write HTML files" in the prompt, return structured content instead of writing a standalone HTML file.

**Fragment output format** (return as a fenced code block with language `fragment-json`):

```fragment-json
{
  "title": "System Architecture Title",
  "description": "1-2 sentence description of what this diagram shows.",
  "bullets": [
    "**Key term 1:** explanation",
    "**Key term 2:** explanation"
  ],
  "diagram_type": "svg",
  "diagram_markup": "<svg viewBox=\"0 0 800 400\">...</svg>",
  "suggested_badge": "Architecture",
  "sub_tabs": null
}
```

**Fields:**
- `title`: Short descriptive title for the tab heading
- `description`: 1-2 sentences for the text layer below the heading
- `bullets`: Array of markdown bullet points with bolded key terms (for the "rich text" layer per Principle 5)
- `diagram_type`: Always `"svg"` for this agent
- `diagram_markup`: Raw SVG markup (the `<svg>` element with all children). Use design-principles.md tokens for all colors, strokes, and text styles. Use `viewBox` for responsive scaling.
- `suggested_badge`: Short label for a badge next to the tab heading (e.g., "Architecture", "Layers", "Components")
- `sub_tabs`: If the architecture has distinct sections that each need focused diagrams (e.g., separate layers), return an array of fragment objects (same schema minus `sub_tabs`) — one per section. Otherwise `null`.

**Rules in fragment mode:**
- Do NOT write any HTML files
- Do NOT open anything in the browser
- Do NOT update `docs/architecture.md` — that is standalone mode's responsibility
- Still read design-principles.md for color tokens and apply them in SVG styles
- Still follow all SVG diagram conventions from this agent
- Use architecture layer colors for tonal depth in layered diagrams
- Read the "Diagram Documentation Principles" section in design-principles.md and follow all 8 rules

**Standalone mode** (default, current behavior) is unchanged — when not dispatched in fragment mode, produce full self-contained HTML files and update `docs/architecture.md` as before.
```

**Step 2: Verify the edit**

Read `agents/architecture-diagram-generator.md` and confirm the "Fragment Mode" section is present at the end.

**Step 3: Commit**

```bash
git add agents/architecture-diagram-generator.md
git commit -m "feat: add fragment mode to architecture-diagram-generator agent"
```

---

### ✅ Task 4: Add fragment mode to mockup-generator agent

**Files:**
- Modify: `agents/mockup-generator.md` (insert "Fragment Mode" section between the "Design Critique" section and the final "Do NOT commit" note)

**Step 1: Write the fragment mode section**

Insert the following section into `agents/mockup-generator.md` between the "Design Critique" section (ends around line 164) and the final "**Do NOT commit.**" paragraph. The Fragment Mode section should appear before the commit warning so the warning applies to both standalone and fragment modes:

```markdown
## Fragment Mode

When dispatched by the session-document-generator with the phrase "Return fragments, do not write HTML files" in the prompt, return structured content instead of writing a standalone HTML file.

**Fragment output format** (return as a fenced code block with language `fragment-json`):

```fragment-json
{
  "title": "Component Mockup Title",
  "description": "1-2 sentence description of what this mockup shows.",
  "bullets": [
    "**Key term 1:** explanation",
    "**Key term 2:** explanation"
  ],
  "diagram_type": "html",
  "diagram_markup": "<div class=\"mockup-fragment\">...</div>",
  "suggested_badge": "Mockup",
  "sub_tabs": null
}
```

**Fields:**
- `title`: Short descriptive title for the tab heading
- `description`: 1-2 sentences for the text layer below the heading
- `bullets`: Array of markdown bullet points with bolded key terms (for the "rich text" layer per Principle 5)
- `diagram_type`: Always `"html"` for this agent
- `diagram_markup`: Self-contained HTML fragment. Include inline styles or Tailwind classes. Do NOT include `<html>`, `<head>`, `<body>`, or `<script src="tailwind">` tags — the orchestrator's document already loads Tailwind. The fragment should work when inserted into a `<div>` container.
- `suggested_badge`: Short label for a badge next to the tab heading (e.g., "Mockup", "UI", "Layout")
- `sub_tabs`: If the UI has distinct views or states (e.g., different pages, empty state vs. populated), return an array of fragment objects (same schema minus `sub_tabs`). Otherwise `null`.

**Rules in fragment mode:**
- Do NOT write any HTML files
- Do NOT open anything in the browser
- Do NOT include full HTML document structure — return only the content fragment
- Still read design-principles.md for design tokens
- Still follow all mockup guidelines from this agent
- Read the "Diagram Documentation Principles" section in design-principles.md and follow all 8 rules

**Standalone mode** (default, current behavior) is unchanged — when not dispatched in fragment mode, produce full self-contained HTML files as before.
```

**Step 2: Verify the edit**

Read `agents/mockup-generator.md` and confirm the "Fragment Mode" section is present.

**Step 3: Commit**

```bash
git add agents/mockup-generator.md
git commit -m "feat: add fragment mode to mockup-generator agent"
```

---

### ✅ Task 5: Create the session-document-generator agent

**Files:**
- Create: `agents/session-document-generator.md`

**Step 1: Verify the file does not already exist**

Run: `ls agents/session-document-generator.md` — expected: "No such file or directory"

**Step 2: Write the agent file**

Create `agents/session-document-generator.md` with the full orchestrator agent definition. The file should include:

```markdown
---
model: sonnet
---

# Session Document Generator

## Overview

Orchestrator agent that produces consolidated tabbed HTML documents for brainstorming sessions. Reads the design document, dispatches existing diagram agents in fragment mode, assembles all returned fragments into a single tabbed HTML file with overview navigation, grouped tabs, lazy Mermaid rendering, and clickable overview nodes.

**This agent replaces the previous pattern of dispatching multiple agents that each produce separate HTML files.** The result is one file per session at `docs/mockups/{session-name}.html` — no subdirectory needed.

## When to Use

Dispatched by the brainstorming skill's "Visualization (mandatory)" section. Not typically invoked directly by users.

## Inputs

The dispatch prompt must provide:
- `{design-file-path}` — path to the design document
- `{session-name}` — kebab-case session name (used for the output filename)
- `{project-root}` — project root path

## Step 0: Read Design Principles (REQUIRED)

Read the "Diagram Documentation Principles" section from `docs/design/design-principles.md` in the project root. If not found, read the global fallback at `~/.claude/docs/design/design-principles.md`. These 8 rules govern the entire document structure.

Also extract color tokens and semantic diagram colors from the same file for use in the HTML template.

**Do not proceed without design tokens and diagram documentation principles.**

## Step 1: Analyze the Design Document

Read the design document at `{design-file-path}`. Identify:
1. What visualization types are needed (flowcharts, architecture diagrams, UI mockups)
2. What topics/sections the visualizations should cover
3. Whether any topics have sub-detail that warrants nested sub-tabs

Plan the tab structure:
- **Overview tab** (always first): `graph LR` Mermaid diagram with one node per topic (4-7 nodes max)
- **Detail tabs**: One per major topic, using the appropriate diagram type
- **Sub-tabs**: Within detail tabs that have phases/steps with >6 nodes

## Step 2: Dispatch Diagram Agents in Fragment Mode

Dispatch the appropriate agents **in parallel** using the Task tool (`subagent_type=general-purpose`). Each agent runs in fragment mode.

**Dispatch template for each agent:**

*For flowcharts (data flows, process flows, decision trees):*

"Read `agents/flowchart-generator.md` for your full workflow. Return fragments, do not write HTML files. Generate diagram fragments for the design at `{design-file-path}`. Project root: `{project-root}`. Focus on these flows: {list specific flows from the design}. Return one fragment per distinct flow. Each fragment should have 4-6 nodes maximum — use sub_tabs for more complex flows."

*For architecture diagrams:*

"Read `agents/architecture-diagram-generator.md` for your full workflow. Return fragments, do not write HTML files. Generate diagram fragments for the design at `{design-file-path}`. Project root: `{project-root}`. Focus on these architectural elements: {list specific elements}. Return one fragment per distinct view."

*For UI mockups:*

"Read `agents/mockup-generator.md` for your full workflow. Return fragments, do not write HTML files. Generate mockup fragments for the design at `{design-file-path}`. Project root: `{project-root}`. Focus on these UI elements: {list specific elements}. Return one fragment per distinct view or state."

## Step 3: Assemble the Tabbed HTML Document

Combine all returned fragments into a single HTML file. Use the template structure below.

**Output file:** `docs/mockups/{session-name}.html`

### HTML Template

The full document structure follows. Replace `{tokens}` with actual values from design-principles.md.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{Session Title} — Brainstorming Visualizations</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    // Inject design tokens from design-principles.md (Step 0) into Tailwind config
    // so mockup fragments using custom token classes render correctly.
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            // Populate from design-principles.md color tokens at assembly time
            // e.g.: accent: { DEFAULT: '#e8762b', hover: '#cc6725', subtle: '#fff7ed' }
          },
          fontFamily: {
            sans: ['system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
            mono: ['Menlo', 'Consolas', 'Monaco', 'Courier New', 'monospace']
          },
          borderRadius: {
            sm: '6px',
            md: '12px',
            full: '9999px'
          }
        }
      }
    }
  </script>
  <style>
    body {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #faf9f7;
      margin: 0;
      padding: 40px;
    }
    h1 { font-size: 1.5rem; font-weight: 500; color: #1a1a1a; margin-bottom: 4px; }
    .subtitle { font-size: 0.95rem; color: #555555; margin-bottom: 4px; }
    .context { font-size: 0.88rem; color: #6b7280; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb; }

    /* Tab bar */
    .tab-bar {
      display: flex;
      gap: 2px;
      border-bottom: 2px solid #f0eeeb;
      margin-bottom: 24px;
    }
    .tab-btn {
      padding: 10px 18px;
      font-size: 0.85rem;
      font-weight: 500;
      color: #6b7280;
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      margin-bottom: -2px;
      cursor: pointer;
      transition: color 150ms, border-color 150ms;
      font-family: inherit;
    }
    .tab-btn:hover { color: #1a1a1a; }
    .tab-btn.active { color: #e8762b; border-bottom-color: #e8762b; }

    /* Sub-tab bar */
    .sub-tab-bar {
      display: flex;
      gap: 2px;
      border-bottom: 1px solid #f0eeeb;
      padding-left: 16px;
      background: #faf9f7;
      margin-bottom: 16px;
    }
    .sub-tab-btn {
      padding: 8px 14px;
      font-size: 0.78rem;
      font-weight: 500;
      color: #6b7280;
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      cursor: pointer;
      transition: color 150ms, border-color 150ms;
      font-family: inherit;
    }
    .sub-tab-btn:hover { color: #1a1a1a; }
    .sub-tab-btn.active { color: #e8762b; border-bottom-color: #e8762b; }

    /* Tab panels */
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    .sub-panel { display: none; }
    .sub-panel.active { display: block; }

    /* Content sections */
    .section {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
    }
    .section h2 {
      font-size: 1.1rem;
      font-weight: 500;
      color: #1a1a1a;
      margin-bottom: 8px;
    }
    .badge {
      font-size: 0.7rem;
      padding: 1px 6px;
      border-radius: 9999px;
      background: #fff7ed;
      color: #e8762b;
      font-weight: 500;
      margin-left: 8px;
      vertical-align: middle;
    }
    .description { font-size: 0.88rem; color: #555555; margin-bottom: 12px; line-height: 1.6; }
    .bullet-list { font-size: 0.85rem; color: #1a1a1a; margin-bottom: 16px; padding-left: 20px; }
    .bullet-list li { margin-bottom: 6px; line-height: 1.5; }
    .diagram-container { overflow-x: auto; }
    .back-link {
      font-size: 0.82rem;
      color: #e8762b;
      text-decoration: none;
      cursor: pointer;
      margin-bottom: 16px;
      display: inline-block;
    }
    .back-link:hover { text-decoration: underline; }

    /* Legend */
    .legend { margin-top: 24px; display: flex; gap: 20px; flex-wrap: wrap; }
    .legend-item { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: #555555; }
    .legend-dot { width: 12px; height: 12px; border-radius: 3px; }
  </style>
</head>
<body>
  <h1>{Session Title}</h1>
  <p class="subtitle">Brainstorming session: {session topic}</p>
  <p class="context">{1-2 sentence summary}</p>

  <!-- Top-level tab bar -->
  <div class="tab-bar" id="main-tabs">
    <button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
    <!-- One button per detail tab -->
  </div>

  <!-- Overview panel -->
  <div class="tab-panel active" id="panel-overview">
    <div class="section">
      <div class="diagram-container">
        <pre class="mermaid">
          graph LR
            %% One node per topic, clickable
            %% click NodeId callback "switchTab('tab-id')"
        </pre>
      </div>
    </div>
    <div class="legend">
      <!-- Legend items -->
    </div>
  </div>

  <!-- Detail panels — one per fragment -->
  <!-- Each panel contains: back link, heading with badge, description, bullets, diagram -->

  <script>
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',
      theme: 'base',
      themeVariables: {
        fontFamily: 'system-ui, -apple-system, sans-serif',
        fontSize: '14px',
        lineColor: '#e5e7eb',
        primaryColor: '#f0eeeb',
        primaryTextColor: '#1a1a1a',
        primaryBorderColor: '#e5e7eb',
        secondaryColor: '#fff7ed',
        secondaryTextColor: '#1a1a1a',
        secondaryBorderColor: '#e8762b',
        tertiaryColor: '#f5f3ef',
        tertiaryTextColor: '#1a1a1a',
        tertiaryBorderColor: '#555555'
      },
      flowchart: { curve: 'basis', padding: 20, nodeSpacing: 50, rankSpacing: 60 }
    });

    // Render overview on load
    mermaid.run({ nodes: document.querySelectorAll('.mermaid') });

    function switchTab(tabId) {
      // Deactivate all top-level tabs and panels
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

      // Activate selected
      var btn = document.querySelector('[onclick*="' + tabId + '"]');
      if (btn) btn.classList.add('active');
      var panel = document.getElementById('panel-' + tabId);
      if (panel) {
        panel.classList.add('active');

        // Lazy-render deferred Mermaid diagrams on first activation
        var deferred = panel.querySelectorAll('.mermaid-deferred');
        deferred.forEach(function(el) {
          el.classList.remove('mermaid-deferred');
          el.classList.add('mermaid');
          try {
            mermaid.run({ nodes: [el] });
          } catch (e) {
            var errMsg = document.createElement('p');
            errMsg.style.cssText = 'color:#b91c1c;font-size:0.85rem;';
            errMsg.textContent = 'Diagram rendering failed: ' + e.message;
            el.replaceWith(errMsg);
          }
        });

        // If panel has sub-tabs, activate the first one
        var firstSubBtn = panel.querySelector('.sub-tab-btn');
        if (firstSubBtn && !panel.querySelector('.sub-tab-btn.active')) {
          firstSubBtn.click();
        }
      }
    }

    function switchSubTab(parentId, subId) {
      var parent = document.getElementById('panel-' + parentId);
      if (!parent) return;
      parent.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
      parent.querySelectorAll('.sub-panel').forEach(p => p.classList.remove('active'));

      var btn = parent.querySelector('[onclick*="' + subId + '"]');
      if (btn) btn.classList.add('active');
      var sub = document.getElementById('sub-' + subId);
      if (sub) {
        sub.classList.add('active');
        // Lazy-render deferred diagrams in sub-panel
        var deferred = sub.querySelectorAll('.mermaid-deferred');
        deferred.forEach(function(el) {
          el.classList.remove('mermaid-deferred');
          el.classList.add('mermaid');
          try {
            mermaid.run({ nodes: [el] });
          } catch (e) {
            var errMsg = document.createElement('p');
            errMsg.style.cssText = 'color:#b91c1c;font-size:0.85rem;';
            errMsg.textContent = 'Diagram rendering failed: ' + e.message;
            el.replaceWith(errMsg);
          }
        });
      }
    }
  </script>
</body>
</html>
```

### Assembly Rules

1. **Overview tab:** Build a `graph LR` Mermaid diagram with one node per returned fragment (using the fragment's `title` as label). Add `click NodeId callback "switchTab('tab-id')"` directives. Style clickable nodes with `cursor:pointer` via Mermaid styles and add `:hover` border shift using CSS. Do NOT use the `call` keyword in click directives (breaks Mermaid v11.13).

2. **Detail tabs:** For each fragment:
   - Create a `<button class="tab-btn">` in the tab bar with the fragment's title
   - Create a `<div class="tab-panel" id="panel-{slug}">` containing:
     - A back link: `<a class="back-link" onclick="switchTab('overview')">← Overview</a>`
     - Section heading: `<h2>{title}<span class="badge">{suggested_badge}</span></h2>`
     - Description: `<p class="description">{description}</p>`
     - Bullets: `<ul class="bullet-list">` with each bullet rendered from markdown
     - Diagram container: depends on `diagram_type`:
       - `mermaid`: `<pre class="mermaid-deferred">{diagram_markup}</pre>` (lazy-rendered)
       - `svg`: embed `{diagram_markup}` directly in `<div class="diagram-container">`
       - `html`: embed `{diagram_markup}` directly in `<div class="diagram-container">`

3. **Sub-tabs:** If a fragment has non-null `sub_tabs`:
   - Render a `.sub-tab-bar` inside the parent panel
   - Each sub-tab gets a `.sub-panel` with its own heading, description, bullets, and diagram
   - Sub-tab switching uses `switchSubTab(parentId, subId)`

4. **Diagram type handling:**
   - `mermaid` fragments: Use `<pre class="mermaid-deferred">` (not `mermaid`) for lazy rendering per Principle 7
   - `svg` fragments: Embed the raw `<svg>` element directly
   - `html` fragments: Embed the raw HTML fragment directly — Tailwind is already loaded in the document

## Step 4: Run Mermaid Verification

After assembling the HTML file, dispatch a verification sub-agent via Task tool (`subagent_type=general-purpose`):

"You are a Mermaid syntax verifier. Read the HTML file at `{output-file-path}`. Extract every Mermaid code block (both `class='mermaid'` and `class='mermaid-deferred'`). Check each block against these Mermaid v11.13 rules:
- No `call` keyword in click directives
- No HTML tags besides `<br>` in node labels
- No `[/ /]` parallelogram syntax with `/` inside content
- All styled node IDs match declared nodes
- All click node IDs match declared nodes

Report PASS/FAIL per block with specific issues. Write your report to `/tmp/mermaid-verify-{session-name}.md`."

If any block FAILs: fix the syntax in the HTML file and re-run verification until all blocks PASS.

## Step 5: Open in Browser

After verification passes:

```bash
open docs/mockups/{session-name}.html
```

**Do NOT commit.** The brainstorming skill commits all visual artifacts together with the design document after the critique round completes.
```

**Step 3: Verify the file was written**

Read `agents/session-document-generator.md` and confirm it contains all sections: Overview, When to Use, Inputs, Steps 0-5, HTML Template, Assembly Rules.

**Step 4: Commit**

```bash
git add agents/session-document-generator.md
git commit -m "feat: add session-document-generator orchestrator agent"
```

---

### ✅ Task 6: Update brainstorming skill's Visualization section

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (the "Visualization (mandatory)" section, starting at the `**Visualization (mandatory):**` line)

**Step 1: Replace the visualization dispatch section**

Replace the content between `**Visualization (mandatory):**` and `**Fact-Check + Critique Panel (mandatory, dynamic selection with division of labor):**` with the new session-document-generator dispatch.

The new content should be:

```markdown
**Visualization (mandatory):**

Every brainstorm produces at least one visual artifact. After writing the design document and BEFORE the critique round, dispatch the session-document-generator to produce a consolidated visualization document.

**Dispatch template** — replace placeholders with actual values. Uses `subagent_type=general-purpose`:

"Read `agents/session-document-generator.md` for your full workflow.
Generate a consolidated visualization document for the design at `{design-file-path}`.
Session name: `{session-name}`. Project root: `{project-root}`.
Output to `docs/mockups/{session-name}.html`.
Verify all Mermaid diagrams render without errors before opening.
Open the file in the browser after verification passes."

Do not pause for user review — the critique panel will evaluate the visuals alongside the design.
```

**Step 2: Update the Mockups field instruction and commit path**

In the "Documentation" subsection under "After the Design", find the sentence that contains `**Mockups:** docs/mockups/{session-name}/` (it appears inline within prose on line 146). Change the path from `docs/mockups/{session-name}/` to `docs/mockups/{session-name}.html`.

Also find the commit instruction further down (around line 259) that reads:
`Commit the design document, visual artifacts (`docs/mockups/{session-name}/`), and`
Change `docs/mockups/{session-name}/` to `docs/mockups/{session-name}.html` in that line too.

**Step 3: Verify the changes**

Read `skills/brainstorming/SKILL.md` and confirm:
- The old multi-agent dispatch templates are gone
- The new session-document-generator dispatch is present
- Both Mockups path references now use `.html` instead of a directory

**Step 4: Commit**

```bash
git add skills/brainstorming/SKILL.md
git commit -m "feat: brainstorming dispatches session-document-generator instead of individual agents"
```

---

### ✅ Task 7: Update README with new agent entry

**Files:**
- Modify: `README.md` (the Agents table, and the agent count in the header)

**Step 1: Add session-document-generator to the Agents table**

Find the Agents table (the `| Agent | Description |` table). Add a new row:

```
| session-document-generator | Orchestrates diagram agents to produce consolidated tabbed HTML documents |
```

Add it in alphabetical order among the existing entries (after `mockup-generator`, before `steve-jobs`).

**Step 2: Add the two missing generator agents to the Agents table**

The current table is missing `flowchart-generator` and `architecture-diagram-generator`. Add them:

```
| architecture-diagram-generator | Architecture diagrams with SVG and architecture.md updates |
| flowchart-generator | Mermaid.js flowcharts for data flows, processes, and decision trees |
```

Add in alphabetical order (architecture-diagram-generator first, before code-reviewer; flowchart-generator after error-diagnosis, before kanban-triage).

**Step 3: Update the agent count**

In the first line of README.md, change `8 agents` to `11 agents` (adding 3: session-document-generator, flowchart-generator, architecture-diagram-generator).

**Step 4: Verify the changes**

Read `README.md` and confirm the Agents table has 11 entries and the header reflects `11 agents`.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add session-document-generator and missing generator agents to README"
```

---

### ✅ Task 8: Bump plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json` (version field)

**Step 1: Bump the minor version**

Change `"version": "0.8.1"` to `"version": "0.9.0"` — this is a minor version bump because it changes the brainstorming skill's visualization dispatch behavior (existing agents gain new fragment mode, new orchestrator agent introduced).

**Step 2: Verify the change**

Read `.claude-plugin/plugin.json` and confirm the version is `0.9.0`.

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 0.9.0 for diagram documentation standards"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Fragment output format | Fenced code block with `fragment-json` language tag | JSON file on disk, structured prompt response, YAML |
| 2 | Task ordering | Sequential (design-principles first, then agents, then orchestrator, then brainstorming) | Parallel agent modifications, orchestrator first |
| 3 | No tests in this plan | Agent definition files are markdown prompts — no executable code to test | Unit tests for HTML template, snapshot tests |
| 4 | Sub-tab rendering approach | Parent panel contains sub-tab bar and sub-panels | Separate component, accordion instead of tabs |
| 5 | Version bump magnitude | Minor (0.8.1 → 0.9.0) | Patch (0.8.2), breaking (1.0.0) |
| 6 | Fragment mode trigger | Natural-language phrase in dispatch prompt | Structured `fragment: true` flag, env var, separate agent file |
| 7 | Dispatch-tracker mockup consolidation | Out of scope — belongs in dispatch-tracker repo | Include as Task 9 in this plan |

### Appendix: Decision Details

#### Decision 1: Fragment output format
**Chose:** Fenced code block with `fragment-json` language tag
**Why:** Agent sub-agents return text responses. A fenced code block with a distinctive language tag (`fragment-json`) is easy to parse from the response text — the orchestrator can extract everything between the code fences. It's also human-readable for debugging. Writing JSON to a temp file would work but adds file I/O coordination overhead. YAML would also work but JSON is more standard for structured data exchange.
**Alternatives rejected:**
- JSON file on disk: Adds file I/O — agent writes, orchestrator reads. More moving parts, temp file cleanup needed.
- Structured prompt response: Harder to parse reliably; no clear delimiter between metadata and content.
- YAML: Less common in this codebase; JSON is already used in plugin.json and other configs.

#### Decision 2: Task ordering
**Chose:** Sequential — design-principles first, then individual agents get fragment mode, then orchestrator agent, then brainstorming skill update
**Why:** Sequential ordering is simpler for a Ralph loop executor — each task is independently committable and verifiable. At write-time, the tasks don't depend on each other (they all edit separate markdown files). At runtime (when agents are actually invoked), design-principles.md must have the new section before agents reference it, and agents must have fragment mode before the orchestrator dispatches them. But that runtime dependency is satisfied by the time the brainstorming skill runs. The ordering is a convenience choice, not a hard file-write dependency.
**Alternatives rejected:**
- Parallel agent modifications: Tasks 2-4 could theoretically be done in parallel since they edit different files, but sequential ordering is simpler for the executor and each task is small enough that parallelism doesn't save meaningful time.

#### Decision 3: No tests in this plan
**Chose:** No automated tests — all modified files are markdown agent/skill definitions
**Why:** The files being modified (`agents/*.md`, `skills/brainstorming/SKILL.md`, `~/.claude/docs/design/design-principles.md`) are prompt files, not executable code. There is no test infrastructure for agent prompts in this project. The design doc specifies eval scenarios (simple session, mixed session, complex session) as future work — those would test the end-to-end behavior but are out of scope for this plan which implements the agent definitions. Testing these changes means running the brainstorming skill against a real project and verifying the output, which is inherently a manual/eval process.
**Alternatives rejected:**
- Unit tests for HTML template: The HTML template is embedded in a markdown prompt, not a standalone file. There's nothing to import or execute.
- Snapshot tests: No snapshot testing infrastructure exists for agent outputs.

#### Decision 4: Sub-tab rendering approach
**Chose:** Sub-tab bar rendered inside the parent panel, with `switchSubTab(parentId, subId)` function
**Why:** Matches the design doc's CSS spec exactly (`.sub-tab-bar`, `.sub-tab-btn` classes). Keeps sub-tabs scoped to their parent panel — switching top-level tabs hides the sub-tab bar naturally. No extra component abstraction needed.
**Alternatives rejected:**
- Separate component: Over-engineering for generated HTML that's assembled once. No reuse benefit.
- Accordion: The design doc explicitly specifies tabs, not accordions.

#### Decision 5: Version bump magnitude
**Chose:** Minor bump (0.8.1 → 0.9.0)
**Why:** This changes the brainstorming skill's visualization dispatch behavior — existing users will get consolidated documents instead of individual files. That's a visible behavior change, not just a patch. It's not breaking in the semver sense (no API contract is violated — the brainstorming skill's interface is the same), but it's significant enough for a minor bump. The project is pre-1.0, so breaking changes are expected anyway.
**Alternatives rejected:**
- Patch (0.8.2): Understates the significance — this adds a new agent and changes an existing skill's behavior.
- Breaking (1.0.0): Premature — the project isn't ready for a stable interface commitment.

#### Decision 6: Fragment mode trigger
**Chose:** Natural-language phrase ("Return fragments, do not write HTML files") in the dispatch prompt
**Why:** Agent definitions are markdown files interpreted by LLMs, not programmatic code. A natural-language sentinel phrase is the most reliable trigger mechanism — the agent reads its instructions and recognizes the phrase. A structured `fragment: true` flag would require parsing a flag from the prompt text, which is functionally identical but adds indirection. The phrase is explicit and self-documenting. The orchestrator's dispatch templates use this exact phrase, so the contract is clear. If the phrase needs to change, both the agent files and the orchestrator dispatch templates must be updated in sync.
**Alternatives rejected:**
- Structured `fragment: true` flag: No parsing advantage — the agent is an LLM reading instructions, not code parsing JSON. Adds a layer of indirection for no benefit.
- Environment variable: Not applicable — agents don't read environment variables.
- Separate agent file: Duplicates capability and creates drift risk. Fragment mode is a behavioral switch, not a different agent.

#### Decision 7: Dispatch-tracker mockup consolidation out of scope
**Chose:** Out of scope for this plan — the consolidation work belongs in the dispatch-tracker project
**Why:** The design doc's "Files Changed" section lists 7 files to consolidate across `docs/mockups/deck-generation-workflow/` and `docs/mockups/brand-assets/`. These files live in the dispatch-tracker project (`/Users/ericpage/software/dispatch-tracker/`), not in the aligned_cc_skills plugin repo. This plan targets aligned_cc_skills only. The consolidation is a separate task that should be planned and executed in the dispatch-tracker project context, using the new session-document-generator agent once it exists. The design doc describes it as a migration task for existing artifacts — it validates the new tooling but isn't part of building the tooling itself.
**Alternatives rejected:**
- Include as Task 9: Would cross repo boundaries — this plan writes to `aligned_cc_skills`, not `dispatch-tracker`. The writing-plans skill explicitly forbids writing plans for repo B into repo A.
