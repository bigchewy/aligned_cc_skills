# Brainstorm Live Visualization — Component Reference

> **For the agent:** Read this file once at the start of the visualization phase. Use the HTML template and component classes below to build the live artifact. Do not invent custom classes — use only what's documented here.

## HTML Template

Copy this template as the starting point for every live visualization. Replace `{title}`, `{subtitle}`, and `{context}` with session-specific values.

```html
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
  <!-- LIVE-REFRESH-START -->
  <script>
    (function() {
      const interval = setInterval(() => location.reload(), 3000);
      setTimeout(() => clearInterval(interval), 1800000); // stop after 30 min
    })();
  </script>
  <!-- LIVE-REFRESH-END -->
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
    .tab-btn.active { color: #ff6900; border-bottom-color: #ff6900; }

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
    .sub-tab-btn.active { color: #ff6900; border-bottom-color: #ff6900; }

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
      color: #ff6900;
      font-weight: 500;
      margin-left: 8px;
      vertical-align: middle;
    }
    .badge-deferred {
      font-size: 0.7rem;
      padding: 1px 6px;
      border-radius: 9999px;
      background: #f5f3ef;
      color: #6b7280;
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
      color: #ff6900;
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

    /* Component cards */
    .component-card {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 16px;
    }
    .component-card h3 {
      font-size: 0.95rem;
      font-weight: 600;
      color: #1a1a1a;
      margin-bottom: 4px;
    }
    .component-card .use-case {
      font-size: 0.82rem;
      color: #6b7280;
      margin-bottom: 12px;
    }
    .component-card code {
      font-family: Menlo, Consolas, Monaco, monospace;
      font-size: 0.78rem;
      background: #f5f3ef;
      padding: 2px 6px;
      border-radius: 4px;
      color: #1a1a1a;
    }
    .component-preview {
      background: #faf9f7;
      border: 1px solid #f0eeeb;
      border-radius: 8px;
      padding: 16px;
      margin-top: 12px;
    }

    /* Phase tracker */
    .mini-phase-tracker {
      display: flex;
      gap: 0;
      align-items: center;
    }
    .mini-phase-item {
      padding: 6px 14px;
      font-size: 0.75rem;
      font-weight: 500;
      color: #6b7280;
      background: #f5f3ef;
      border: 1px solid #e5e7eb;
      border-right: none;
    }
    .mini-phase-item:first-child { border-radius: 6px 0 0 6px; }
    .mini-phase-item:last-child { border-radius: 0 6px 6px 0; border-right: 1px solid #e5e7eb; }
    .mini-phase-item.current {
      background: #ff6900;
      color: white;
      border-color: #ff6900;
    }

    /* Card grid */
    .mini-card-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }
    .mini-card {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      padding: 10px;
      font-size: 0.75rem;
      color: #1a1a1a;
    }
    .mini-card strong { font-weight: 600; display: block; margin-bottom: 2px; }
    .mini-card span { color: #6b7280; font-size: 0.7rem; }

    /* Compare grid */
    .mini-compare-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .mini-compare-col {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      padding: 10px;
      font-size: 0.72rem;
    }
    .mini-compare-col h4 {
      font-size: 0.78rem;
      font-weight: 600;
      margin-bottom: 6px;
      color: #1a1a1a;
    }
    .mini-compare-col .pro { color: #047857; }
    .mini-compare-col .con { color: #b91c1c; }

    /* Callouts */
    .mini-callout {
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 0.75rem;
      border-left: 3px solid;
      margin-bottom: 6px;
    }
    .mini-callout.decision { background: #fff7ed; border-color: #ff6900; color: #1a1a1a; }
    .mini-callout.constraint { background: #f5f3ef; border-color: #555555; color: #1a1a1a; }
    .mini-callout.risk { background: #fef2f2; border-color: #b91c1c; color: #b91c1c; }

    /* Change table */
    .change-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }
    .change-table th {
      text-align: left;
      padding: 10px 12px;
      font-weight: 600;
      color: #1a1a1a;
      background: #f5f3ef;
      border-bottom: 1px solid #e5e7eb;
    }
    .change-table td {
      padding: 10px 12px;
      border-bottom: 1px solid #f0eeeb;
      color: #1a1a1a;
      vertical-align: top;
    }
    .change-table .file-path {
      font-family: Menlo, Consolas, monospace;
      font-size: 0.78rem;
      color: #555555;
    }
    .status-badge {
      display: inline-block;
      font-size: 0.7rem;
      padding: 1px 8px;
      border-radius: 9999px;
      font-weight: 500;
    }
    .status-modified { background: #fff7ed; color: #ff6900; }
    .status-unchanged { background: #f5f3ef; color: #6b7280; }
    .status-new { background: #ecfdf5; color: #047857; }

    /* Success criteria */
    .criteria-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .criteria-item {
      display: flex;
      gap: 12px;
      padding: 12px 16px;
      border-bottom: 1px solid #f0eeeb;
      align-items: flex-start;
    }
    .criteria-item:last-child { border-bottom: none; }
    .criteria-num {
      font-family: Menlo, Consolas, monospace;
      font-size: 0.78rem;
      color: #ff6900;
      font-weight: 600;
      flex-shrink: 0;
      padding-top: 1px;
    }
    .criteria-text {
      font-size: 0.85rem;
      color: #1a1a1a;
      line-height: 1.5;
    }
    .criteria-text strong { font-weight: 600; }

    /* Test strategy */
    .test-category {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 16px;
    }
    .test-category h3 {
      font-size: 0.95rem;
      font-weight: 600;
      color: #1a1a1a;
      margin-bottom: 8px;
    }
    .test-items {
      font-size: 0.85rem;
      color: #1a1a1a;
      padding-left: 20px;
      margin: 0;
    }
    .test-items li {
      margin-bottom: 6px;
      line-height: 1.5;
    }

    /* Phase tracker */
    .phase-tracker {
      display: flex;
      gap: 0;
      align-items: center;
      margin-bottom: 24px;
    }
    .phase-item {
      padding: 8px 18px;
      font-size: 0.82rem;
      font-weight: 500;
      color: #6b7280;
      background: #f5f3ef;
      border: 1px solid #e5e7eb;
      border-right: none;
    }
    .phase-item:first-child { border-radius: 6px 0 0 6px; }
    .phase-item:last-child { border-radius: 0 6px 6px 0; border-right: 1px solid #e5e7eb; }
    .phase-current {
      background: #ff6900;
      color: white;
      border-color: #ff6900;
    }

    /* Card grid */
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .card {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 20px;
    }
    .card h3 {
      font-size: 0.95rem;
      font-weight: 600;
      color: #1a1a1a;
      margin-bottom: 8px;
    }
    .card p {
      font-size: 0.85rem;
      color: #555555;
      line-height: 1.5;
      margin: 0;
    }

    /* Comparison grid */
    .compare-grid {
      display: grid;
      gap: 16px;
      margin-bottom: 24px;
    }
    .compare-2col { grid-template-columns: repeat(2, 1fr); }
    .compare-3col { grid-template-columns: repeat(3, 1fr); }
    .compare-grid .col {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 20px;
    }
    .compare-grid .col h3 {
      font-size: 0.95rem;
      font-weight: 600;
      color: #1a1a1a;
      margin-bottom: 8px;
    }
    .compare-grid .pro { color: #047857; font-size: 0.85rem; }
    .compare-grid .con { color: #b91c1c; font-size: 0.85rem; }

    /* Callout boxes */
    .callout {
      padding: 16px 20px;
      border-radius: 8px;
      font-size: 0.85rem;
      border-left: 4px solid;
      margin-bottom: 16px;
      line-height: 1.5;
    }
    .callout-decision { background: #fff7ed; border-color: #ff6900; color: #1a1a1a; }
    .callout-constraint { background: #f5f3ef; border-color: #555555; color: #1a1a1a; }
    .callout-risk { background: #fef2f2; border-color: #b91c1c; color: #1a1a1a; }
    .callout-note { background: #f0f9ff; border-color: #0284c7; color: #1a1a1a; }
    .callout strong {
      display: block;
      font-weight: 600;
      margin-bottom: 4px;
    }
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="subtitle">{subtitle}</p>
  <p class="context">{context}</p>

  <!-- Tab bar and content panels go here -->

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
        secondaryBorderColor: '#ff6900',
        tertiaryColor: '#f5f3ef',
        tertiaryTextColor: '#1a1a1a',
        tertiaryBorderColor: '#555555'
      },
      flowchart: { curve: 'basis', padding: 20, nodeSpacing: 50, rankSpacing: 60 }
    });

    // Render diagrams with class="mermaid" on load
    mermaid.run({ nodes: document.querySelectorAll('.mermaid') });

    function switchTab(tabId) {
      // Deactivate all top-level tabs and panels
      document.querySelectorAll('#main-tabs .tab-btn').forEach(function(b) { b.classList.remove('active'); });
      document.querySelectorAll('.tab-panel').forEach(function(p) { p.classList.remove('active'); });

      // Activate selected
      var btn = document.querySelector('#main-tabs [onclick*="' + tabId + '"]');
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

        // If panel has sub-tabs, activate the first one if none active
        var firstSubBtn = panel.querySelector('.sub-tab-btn');
        if (firstSubBtn && !panel.querySelector('.sub-tab-btn.active')) {
          firstSubBtn.click();
        }
      }
    }

    function switchSubTab(parentId, subId) {
      var parent = document.getElementById('panel-' + parentId);
      if (!parent) return;
      parent.querySelectorAll('.sub-tab-btn').forEach(function(b) { b.classList.remove('active'); });
      parent.querySelectorAll('.sub-panel').forEach(function(p) { p.classList.remove('active'); });

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

## Components

### Phase Tracker

Shows the current brainstorm phase. Use at the top of the visualization to orient the user.

**Workflow step:** All phases — updates as the session progresses.

```html
<div class="phase-tracker">
  <div class="phase-item phase-current">Problem Space</div>
  <div class="phase-item">Root Causes</div>
  <div class="phase-item">Solutions</div>
  <div class="phase-item">Architecture</div>
</div>
```

**Notes:** Add `phase-current` to the active phase. Only one phase should be current at a time. Previous phases lose the class as the session advances.

---

### Card Grid

Displays a grid of items — problems, root causes, solutions, components, or modules. Cards auto-fill to fit available width.

**Workflow step:** Problem exploration, root-cause analysis, solution generation, architecture decomposition.

```html
<div class="card-grid">
  <div class="card">
    <h3>Card Title</h3>
    <p>Description of the item.</p>
  </div>
  <div class="card">
    <h3>Another Card</h3>
    <p>More detail here.</p>
  </div>
</div>
```

**Notes:** Cards expand to fill the row. For fewer than 3 items, cards will be wider. Content within cards is flexible — use `<ul>`, `<p>`, or other elements as needed.

---

### Comparison Grid

Side-by-side comparison of 2–3 approaches or trade-offs.

**Workflow step:** Solution evaluation, architecture trade-off analysis.

```html
<div class="compare-grid compare-2col">
  <div class="col">
    <h3>Option A</h3>
    <p class="pro">+ Fast to implement</p>
    <p class="con">- Limited scalability</p>
  </div>
  <div class="col">
    <h3>Option B</h3>
    <p class="pro">+ Scales well</p>
    <p class="con">- Complex setup</p>
  </div>
</div>
```

**Notes:** Use `compare-2col` for two options, `compare-3col` for three. Use `.pro` and `.con` classes for green/red coloring of trade-off items.

---

### Tabbed Navigation

Organizes content into switchable tabs. Already included in the template — use `switchTab()` and `switchSubTab()` for interaction.

**Workflow step:** Top-level organization (e.g., Overview / Details / Architecture) and sub-sections within tabs.

```html
<div class="tab-bar" id="main-tabs">
  <button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
  <button class="tab-btn" onclick="switchTab('details')">Details</button>
</div>

<div id="panel-overview" class="tab-panel active">
  <!-- Overview content -->
</div>

<div id="panel-details" class="tab-panel">
  <!-- Sub-tabs example -->
  <div class="sub-tab-bar">
    <button class="sub-tab-btn active" onclick="switchSubTab('details','problems')">Problems</button>
    <button class="sub-tab-btn" onclick="switchSubTab('details','causes')">Root Causes</button>
  </div>
  <div id="sub-problems" class="sub-panel active"><!-- content --></div>
  <div id="sub-causes" class="sub-panel"><!-- content --></div>
</div>
```

**Notes:** Panel IDs must be `panel-{tabId}`. Sub-panel IDs must be `sub-{subId}`. The first tab and sub-tab should have `active` class by default.

---

### Callout Boxes

Highlight decisions, constraints, risks, or notes that need attention.

**Workflow step:** Any phase — use when surfacing key findings or decisions.

```html
<div class="callout callout-decision">
  <strong>Decision</strong>
  We will use a microservices architecture for the backend.
</div>

<div class="callout callout-constraint">
  <strong>Constraint</strong>
  Budget limited to $50k for initial implementation.
</div>

<div class="callout callout-risk">
  <strong>Risk</strong>
  Third-party API may have rate limits that affect throughput.
</div>

<div class="callout callout-note">
  <strong>Note</strong>
  This approach requires team training on the new framework.
</div>
```

**Notes:** Four variants: `callout-decision` (orange), `callout-constraint` (gray), `callout-risk` (red), `callout-note` (blue). The `<strong>` label is optional but recommended.

---

### Mermaid Containers

Wraps Mermaid diagrams for architecture diagrams, flows, and state machines. Use `mermaid-deferred` for diagrams in hidden tabs (rendered on first activation).

**Workflow step:** Architecture phase — system diagrams, data flows, state machines.

```html
<!-- Immediate render (visible on load) -->
<div class="diagram-container">
  <pre class="mermaid">
graph TD
  A[Client] --> B[API Gateway]
  B --> C[Service]
  </pre>
</div>

<!-- Deferred render (in a hidden tab) -->
<div class="diagram-container">
  <pre class="mermaid-deferred">
graph TD
  A[Start] --> B[End]
  </pre>
</div>
```

**Notes:** Use `mermaid` class for diagrams visible on initial load. Use `mermaid-deferred` for diagrams inside hidden tabs — they render automatically when the tab is first activated. The `.diagram-container` provides horizontal scroll for wide diagrams.

---

### Section Containers

General-purpose content wrapper with white background, border, and rounded corners. Already in the template CSS.

**Workflow step:** Any phase — use to group related content within a tab panel.

```html
<div class="section">
  <h2>Section Title</h2>
  <p class="description">Supporting description text.</p>
  <ul class="bullet-list">
    <li>First point</li>
    <li>Second point</li>
  </ul>
</div>
```

**Notes:** Sections stack vertically with 24px spacing. Use `.description` for secondary text and `.bullet-list` for lists within sections.

---

### Deferred Components

The following components are planned but not yet implemented:

- **Quadrant map** — For 2×2 prioritization grids (impact vs. effort, urgency vs. importance). Deferred until use cases are validated in live sessions.
- **Decision log** — Running log of decisions made during the session with rationale. Deferred until the session flow stabilizes.
