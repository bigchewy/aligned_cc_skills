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
