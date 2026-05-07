# Brainstorm Live Visualization — Component Reference

> **For the agent:** Read this file once at the start of the visualization phase. Use the HTML template and component classes below to build the live artifact. Do not invent custom classes — use only what's documented here.

## Contents

- Brand Token Injection
- HTML Template
- Components

## Brand Token Injection

The template's color and font values are defined as CSS variables in a `:root` block at the top of the inline `<style>`. Every other reference in the template — Tailwind config, inline CSS rules, Mermaid theme — reads from those variables. Rebrand the artifact by editing only the `:root` block.

### Token contract

The template uses these CSS-variable names. Default values match the aligned plugin's own brand and apply when no project tokens are found.

| Token (in :root)         | Purpose                                                |
|--------------------------|--------------------------------------------------------|
| `--color-background`     | Page/diagram background                                |
| `--color-surface`        | Container regions, card backgrounds                    |
| `--color-muted`          | Inset areas, subtle fills                              |
| `--color-foreground`     | Primary text, headings                                 |
| `--color-secondary`      | Supporting text, captions                              |
| `--color-dimmed`         | Tertiary info (timestamps, axis labels)                |
| `--color-border`         | Dividers, card borders                                 |
| `--color-accent`         | Signature accent (CTAs, highlights, decisions)         |
| `--color-accent-hover`   | Accent hover state                                     |
| `--color-accent-subtle`  | Accent background tint (badges, decision callouts)     |
| `--font-sans`            | Body and UI text                                       |
| `--font-mono`            | Code, file paths                                       |

### Resolving project tokens

Project design-principles files don't always use the exact `--color-*` naming above. Use this resolution order:

1. **Direct match.** If the source file defines `--color-accent`, `--color-foreground`, etc. with the contract names verbatim, use them.
2. **Alias match.** Otherwise, apply this alias table. Project token names appear in many shapes — the table treats `kebab-case`, `camelCase`, and `snake_case` as equivalent (compare case-insensitively after stripping separators).

   | Project token name(s)                                              | Contract token            |
   |--------------------------------------------------------------------|---------------------------|
   | `accent`                                                           | `--color-accent`          |
   | `accent-hover`, `primary-hover`                                    | `--color-accent-hover`    |
   | `accent-subtle`, `accent-bg`, `primary-subtle`                     | `--color-accent-subtle`   |
   | `background`, `bg`, `page`                                         | `--color-background`      |
   | `surface`, `card`, `panel`                                         | `--color-surface`         |
   | `muted`, `inset`                                                   | `--color-muted`           |
   | `foreground`, `text`, `fg`                                         | `--color-foreground`      |
   | `secondary`, `text-secondary`                                      | `--color-secondary`       |
   | `dimmed`, `text-muted`, `muted-foreground`                         | `--color-dimmed`          |
   | `border`                                                           | `--color-border`          |
   | `sans`, `body`, `font-sans`                                        | `--font-sans`             |
   | `mono`, `code`, `font-mono`                                        | `--font-mono`             |

3. **Ambiguous? Halt and ask.** If the source defines `primary` but does NOT define `accent`, `primary` likely IS the brand accent — map `primary` → `--color-accent` and continue. But if the source defines BOTH `primary` AND `accent` (genuine ambiguity), or contains tokens that don't fit any alias (`heading`, `display`, `serif`, `link`, brand-specific names), STOP. Present the proposed mapping to the user as a table — list each project token and where you'd put it (or "unmapped — leave default") — and ask for confirmation or correction before writing the HTML.
4. **Missing tokens.** If the source provides only some contract tokens (common: it has `accent` but no `accent-hover` or `accent-subtle`), leave the missing ones at the template defaults. **Do not derive colors by darkening/lightening** — agents are unreliable at color math, and the visible brand is dominated by the main accent and background.

### Placeholder files

Some projects have a `docs/design/design-principles.md` that's a kickstart-generated 4-line placeholder. Heuristic: the file is under 500 bytes, OR contains the literal string "This file is a placeholder", OR contains "Run `/aligned:create-design-principles`". Treat placeholders as if no file exists — fall back to the next lookup location and surface this warning to the user before writing the artifact:

> Your project's `docs/design/design-principles.md` is still a placeholder. The brainstorm visualization will use the aligned plugin's default tokens. Run `/aligned:create-design-principles` to define the project's brand.

### Writing :root

Once tokens are resolved, populate the `:root` block in the inline `<style>` with the values. Leave every other `var(--color-*)` / `var(--font-*)` reference throughout the template untouched — they resolve through `:root` automatically.

### Semantic colors

`#b91c1c` (error), `#047857` (success), `#0284c7` (info), and the `#fef2f2`/`#ecfdf5`/`#f0f9ff` callout fills are intentionally hardcoded. They convey meaning that should be consistent across all brands and are not part of the contract.

## HTML Template

Copy this template as the starting point for every live visualization. Replace `{title}`, `{subtitle}`, and `{context}` with session-specific values. Update the `:root` block per "Brand Token Injection" above.

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
            accent: { DEFAULT: 'var(--color-accent)', hover: 'var(--color-accent-hover)', subtle: 'var(--color-accent-subtle)' },
            surface: 'var(--color-surface)',
            muted: 'var(--color-muted)',
            foreground: 'var(--color-foreground)',
            secondary: 'var(--color-secondary)',
            dimmed: 'var(--color-dimmed)',
            border: 'var(--color-border)'
          },
          fontFamily: {
            sans: ['var(--font-sans)'],
            mono: ['var(--font-mono)']
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
      var STATE_KEY = 'brainstorm-state:' + location.pathname;

      function saveState() {
        try {
          var state = { tab: null, subTabs: {}, scrollY: window.scrollY };
          var activeTabBtn = document.querySelector('#main-tabs .tab-btn.active');
          if (activeTabBtn) {
            var m = (activeTabBtn.getAttribute('onclick') || '').match(/switchTab\('([^']+)'\)/);
            if (m) state.tab = m[1];
          }
          document.querySelectorAll('.tab-panel').forEach(function(panel) {
            var activeSubBtn = panel.querySelector('.sub-tab-btn.active');
            if (!activeSubBtn) return;
            var sm = (activeSubBtn.getAttribute('onclick') || '').match(/switchSubTab\('([^']+)',\s*'([^']+)'\)/);
            if (sm) state.subTabs[sm[1]] = sm[2];
          });
          sessionStorage.setItem(STATE_KEY, JSON.stringify(state));
        } catch (e) { /* storage unavailable — skip */ }
      }

      function restoreState() {
        try {
          var raw = sessionStorage.getItem(STATE_KEY);
          if (!raw) return;
          var state = JSON.parse(raw);

          // Pre-mark the target sub-tab button so switchTab's "default to first
          // sub-tab" fallback sees an already-active sub-tab and skips. Without
          // this, switchTab briefly activates the first sub-panel before
          // switchSubTab swaps it to the target — a visible flash.
          if (state.tab && state.subTabs && state.subTabs[state.tab]) {
            var parent = document.getElementById('panel-' + state.tab);
            var subId = state.subTabs[state.tab];
            if (parent && document.getElementById('sub-' + subId)) {
              var btn = parent.querySelector('[onclick*="' + subId + '"]');
              if (btn) {
                parent.querySelectorAll('.sub-tab-btn').forEach(function(b) { b.classList.remove('active'); });
                btn.classList.add('active');
              }
            }
          }

          if (state.tab && typeof switchTab === 'function' && document.getElementById('panel-' + state.tab)) {
            switchTab(state.tab);
          }
          if (state.subTabs && typeof switchSubTab === 'function') {
            Object.keys(state.subTabs).forEach(function(parentId) {
              var subId = state.subTabs[parentId];
              if (document.getElementById('sub-' + subId)) switchSubTab(parentId, subId);
            });
          }
          if (typeof state.scrollY === 'number') window.scrollTo(0, state.scrollY);
        } catch (e) { /* corrupted state — ignore */ }
      }

      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', restoreState);
      } else {
        restoreState();
      }

      var interval = setInterval(function() {
        saveState();
        location.reload();
      }, 15000);
      setTimeout(function() { clearInterval(interval); }, 1800000); // stop after 30 min
    })();
  </script>
  <!-- LIVE-REFRESH-END -->
  <style>
    /* --- Brand tokens ---
       Populated by the brainstorming skill from the project's
       docs/design/design-principles.md (or the global fallback at
       ~/.claude/docs/design/design-principles.md). Defaults below match
       the aligned plugin's own brand and apply when no design-principles
       file is found. The whole inline <style> block, the Tailwind config
       above, and the Mermaid theme below all read from these vars — so
       changing values here is the only edit needed to rebrand the artifact. */
    :root {
      --color-background: #faf9f7;
      --color-surface: #f5f3ef;
      --color-muted: #f0eeeb;
      --color-foreground: #1a1a1a;
      --color-secondary: #555555;
      --color-dimmed: #6b7280;
      --color-border: #e5e7eb;
      --color-accent: #ff6900;
      --color-accent-hover: #e55d00;
      --color-accent-subtle: #fff7ed;
      --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: Menlo, Consolas, Monaco, "Courier New", monospace;
    }
    body {
      font-family: var(--font-sans);
      background: var(--color-background);
      margin: 0;
      padding: 40px;
    }
    h1 { font-size: 1.5rem; font-weight: 500; color: var(--color-foreground); margin-bottom: 4px; }
    .subtitle { font-size: 0.95rem; color: var(--color-secondary); margin-bottom: 4px; }
    .context { font-size: 0.88rem; color: var(--color-dimmed); margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--color-border); }

    /* Tab bar */
    .tab-bar {
      display: flex;
      gap: 2px;
      border-bottom: 2px solid var(--color-muted);
      margin-bottom: 24px;
    }
    .tab-btn {
      padding: 10px 18px;
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--color-dimmed);
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      margin-bottom: -2px;
      cursor: pointer;
      transition: color 150ms, border-color 150ms;
      font-family: inherit;
    }
    .tab-btn:hover { color: var(--color-foreground); }
    .tab-btn.active { color: var(--color-accent); border-bottom-color: var(--color-accent); }

    /* Sub-tab bar */
    .sub-tab-bar {
      display: flex;
      gap: 2px;
      border-bottom: 1px solid var(--color-muted);
      padding-left: 16px;
      background: var(--color-background);
      margin-bottom: 16px;
    }
    .sub-tab-btn {
      padding: 8px 14px;
      font-size: 0.78rem;
      font-weight: 500;
      color: var(--color-dimmed);
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      cursor: pointer;
      transition: color 150ms, border-color 150ms;
      font-family: inherit;
    }
    .sub-tab-btn:hover { color: var(--color-foreground); }
    .sub-tab-btn.active { color: var(--color-accent); border-bottom-color: var(--color-accent); }

    /* Tab panels */
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    .sub-panel { display: none; }
    .sub-panel.active { display: block; }

    /* Content sections */
    .section {
      background: white;
      border: 1px solid var(--color-border);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
    }
    .section h2 {
      font-size: 1.1rem;
      font-weight: 500;
      color: var(--color-foreground);
      margin-bottom: 8px;
    }
    .badge {
      font-size: 0.7rem;
      padding: 1px 6px;
      border-radius: 9999px;
      background: var(--color-accent-subtle);
      color: var(--color-accent);
      font-weight: 500;
      margin-left: 8px;
      vertical-align: middle;
    }
    .badge-deferred {
      font-size: 0.7rem;
      padding: 1px 6px;
      border-radius: 9999px;
      background: var(--color-surface);
      color: var(--color-dimmed);
      font-weight: 500;
      margin-left: 8px;
      vertical-align: middle;
    }
    .description { font-size: 0.88rem; color: var(--color-secondary); margin-bottom: 12px; line-height: 1.6; }
    .bullet-list { font-size: 0.85rem; color: var(--color-foreground); margin-bottom: 16px; padding-left: 20px; }
    .bullet-list li { margin-bottom: 6px; line-height: 1.5; }
    .diagram-container { overflow-x: auto; }
    .back-link {
      font-size: 0.82rem;
      color: var(--color-accent);
      text-decoration: none;
      cursor: pointer;
      margin-bottom: 16px;
      display: inline-block;
    }
    .back-link:hover { text-decoration: underline; }

    /* Legend */
    .legend { margin-top: 24px; display: flex; gap: 20px; flex-wrap: wrap; }
    .legend-item { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--color-secondary); }
    .legend-dot { width: 12px; height: 12px; border-radius: 3px; }

    /* Component cards */
    .component-card {
      background: white;
      border: 1px solid var(--color-border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 16px;
    }
    .component-card h3 {
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--color-foreground);
      margin-bottom: 4px;
    }
    .component-card .use-case {
      font-size: 0.82rem;
      color: var(--color-dimmed);
      margin-bottom: 12px;
    }
    .component-card code {
      font-family: Menlo, Consolas, Monaco, monospace;
      font-size: 0.78rem;
      background: var(--color-surface);
      padding: 2px 6px;
      border-radius: 4px;
      color: var(--color-foreground);
    }
    .component-preview {
      background: var(--color-background);
      border: 1px solid var(--color-muted);
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
      color: var(--color-dimmed);
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-right: none;
    }
    .mini-phase-item:first-child { border-radius: 6px 0 0 6px; }
    .mini-phase-item:last-child { border-radius: 0 6px 6px 0; border-right: 1px solid var(--color-border); }
    .mini-phase-item.current {
      background: var(--color-accent);
      color: white;
      border-color: var(--color-accent);
    }

    /* Card grid */
    .mini-card-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }
    .mini-card {
      background: white;
      border: 1px solid var(--color-border);
      border-radius: 6px;
      padding: 10px;
      font-size: 0.75rem;
      color: var(--color-foreground);
    }
    .mini-card strong { font-weight: 600; display: block; margin-bottom: 2px; }
    .mini-card span { color: var(--color-dimmed); font-size: 0.7rem; }

    /* Compare grid */
    .mini-compare-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .mini-compare-col {
      background: white;
      border: 1px solid var(--color-border);
      border-radius: 6px;
      padding: 10px;
      font-size: 0.72rem;
    }
    .mini-compare-col h4 {
      font-size: 0.78rem;
      font-weight: 600;
      margin-bottom: 6px;
      color: var(--color-foreground);
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
    .mini-callout.decision { background: var(--color-accent-subtle); border-color: var(--color-accent); color: var(--color-foreground); }
    .mini-callout.constraint { background: var(--color-surface); border-color: var(--color-secondary); color: var(--color-foreground); }
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
      color: var(--color-foreground);
      background: var(--color-surface);
      border-bottom: 1px solid var(--color-border);
    }
    .change-table td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--color-muted);
      color: var(--color-foreground);
      vertical-align: top;
    }
    .change-table .file-path {
      font-family: Menlo, Consolas, monospace;
      font-size: 0.78rem;
      color: var(--color-secondary);
    }
    .status-badge {
      display: inline-block;
      font-size: 0.7rem;
      padding: 1px 8px;
      border-radius: 9999px;
      font-weight: 500;
    }
    .status-modified { background: var(--color-accent-subtle); color: var(--color-accent); }
    .status-unchanged { background: var(--color-surface); color: var(--color-dimmed); }
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
      border-bottom: 1px solid var(--color-muted);
      align-items: flex-start;
    }
    .criteria-item:last-child { border-bottom: none; }
    .criteria-num {
      font-family: Menlo, Consolas, monospace;
      font-size: 0.78rem;
      color: var(--color-accent);
      font-weight: 600;
      flex-shrink: 0;
      padding-top: 1px;
    }
    .criteria-text {
      font-size: 0.85rem;
      color: var(--color-foreground);
      line-height: 1.5;
    }
    .criteria-text strong { font-weight: 600; }

    /* Test strategy */
    .test-category {
      background: white;
      border: 1px solid var(--color-border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 16px;
    }
    .test-category h3 {
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--color-foreground);
      margin-bottom: 8px;
    }
    .test-items {
      font-size: 0.85rem;
      color: var(--color-foreground);
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
      color: var(--color-dimmed);
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-right: none;
    }
    .phase-item:first-child { border-radius: 6px 0 0 6px; }
    .phase-item:last-child { border-radius: 0 6px 6px 0; border-right: 1px solid var(--color-border); }
    .phase-current {
      background: var(--color-accent);
      color: white;
      border-color: var(--color-accent);
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
      border: 1px solid var(--color-border);
      border-radius: 12px;
      padding: 20px;
    }
    .card h3 {
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--color-foreground);
      margin-bottom: 8px;
    }
    .card p {
      font-size: 0.85rem;
      color: var(--color-secondary);
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
      border: 1px solid var(--color-border);
      border-radius: 12px;
      padding: 20px;
    }
    .compare-grid .col h3 {
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--color-foreground);
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
    .callout-decision { background: var(--color-accent-subtle); border-color: var(--color-accent); color: var(--color-foreground); }
    .callout-constraint { background: var(--color-surface); border-color: var(--color-secondary); color: var(--color-foreground); }
    .callout-risk { background: #fef2f2; border-color: #b91c1c; color: var(--color-foreground); }
    .callout-note { background: #f0f9ff; border-color: #0284c7; color: var(--color-foreground); }
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
    var __rs = getComputedStyle(document.documentElement);
    function __tok(name, fallback) {
      var v = __rs.getPropertyValue(name).trim();
      return v || fallback;
    }
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',
      theme: 'base',
      themeVariables: {
        fontFamily: __tok('--font-sans', 'system-ui, -apple-system, sans-serif'),
        fontSize: '14px',
        lineColor: __tok('--color-border', '#e5e7eb'),
        primaryColor: __tok('--color-muted', '#f0eeeb'),
        primaryTextColor: __tok('--color-foreground', '#1a1a1a'),
        primaryBorderColor: __tok('--color-border', '#e5e7eb'),
        secondaryColor: __tok('--color-accent-subtle', '#fff7ed'),
        secondaryTextColor: __tok('--color-foreground', '#1a1a1a'),
        secondaryBorderColor: __tok('--color-accent', '#ff6900'),
        tertiaryColor: __tok('--color-surface', '#f5f3ef'),
        tertiaryTextColor: __tok('--color-foreground', '#1a1a1a'),
        tertiaryBorderColor: __tok('--color-secondary', '#555555')
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
