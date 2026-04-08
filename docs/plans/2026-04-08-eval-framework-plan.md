# Eval Framework Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Build a Promptfoo-based eval framework that answers whether each skill produces measurably better output than prompting the LLM directly, starting with three MVE scenarios.

**Source Design Doc:** `docs/plans/2026-04-08-eval-framework-design.md`

**Mockups:** `docs/mockups/eval-framework.html`

**Architecture:** Promptfoo runs three-provider comparisons (full-stack, vanilla, aware-but-unaided) for each scenario. Scenario YAMLs use `file://` references to load advisor/framework content as system prompts and fixture content as test vars. A custom Python distinctness scorer post-processes results JSON for inter-persona cosine similarity.

**Tech Stack:** Promptfoo (npm), Python 3 (pytest, openai for embeddings), Anthropic Claude API

---

### ✅ Task 1: Initialize e2e/ directory scaffolding

**Files:**
- Create: `e2e/package.json`
- Create: `e2e/requirements.txt`
- Create: `e2e/.gitignore`
- Create: `e2e/baselines/.gitkeep`
- Create: `e2e/reports/.gitkeep`

**Step 1: Create `e2e/package.json`**

```json
{
  "name": "aligned-evals",
  "version": "0.1.0",
  "private": true,
  "description": "Eval framework for Aligned plugin skills",
  "scripts": {
    "eval": "promptfoo eval",
    "eval:dry-run": "promptfoo eval --dry-run",
    "validate": "promptfoo validate",
    "view": "promptfoo view",
    "test": "pytest tests/ -v",
    "test:scorer": "pytest tests/test_distinctness.py -v"
  },
  "devDependencies": {
    "promptfoo": "^0.100.0"
  }
}
```

**Step 2: Create `e2e/requirements.txt`**

```
openai>=1.0.0,<2.0.0
pytest>=7.0.0
```

**Step 3: Create `e2e/.gitignore`**

```
node_modules/
output/
.promptfoo/
.venv/
*.cache
__pycache__/
.pytest_cache/
*.pyc
```

**Step 4: Create placeholder directories**

```bash
mkdir -p e2e/baselines e2e/reports e2e/scenarios/persona-panel e2e/scenarios/use-advisor e2e/scenarios/use-framework e2e/fixtures/company-briefs e2e/scorers e2e/tests
touch e2e/baselines/.gitkeep e2e/reports/.gitkeep
```

**Step 5: Install dependencies**

```bash
cd e2e && npm install
pip install -r requirements.txt
```

**Step 6: Commit**

```bash
git add e2e/package.json e2e/package-lock.json e2e/requirements.txt e2e/.gitignore e2e/baselines/.gitkeep e2e/reports/.gitkeep
git commit -m "feat(eval): initialize e2e directory scaffolding with promptfoo"
```

---

### ✅ Task 2: Write fixture files

**Files:**
- Create: `e2e/fixtures/sample-pricing-page.md`
- Create: `e2e/fixtures/sample-blog-post.md`
- Create: `e2e/fixtures/company-briefs/b2b-saas-startup.md`

These are synthetic but realistic content pieces (200-400 words each) that serve as inputs for eval scenarios.

**Step 1: Write `e2e/fixtures/sample-pricing-page.md`**

```markdown
# Pricing — FlowMetrics

## Plans

### Starter — Free
- 3 dashboards
- 7-day data retention
- Community support
- Up to 1,000 events/day

### Pro — $49/mo per seat
- Unlimited dashboards
- 90-day data retention
- Email support (48hr SLA)
- Up to 100K events/day
- Custom alerts
- API access

### Enterprise — Custom
- Unlimited everything
- 365-day data retention
- Dedicated success manager
- SSO/SAML
- SLA guarantee (99.9%)
- Custom integrations
- On-premise deployment option

## FAQ

**Can I switch plans anytime?**
Yes. Upgrades are prorated, downgrades take effect at the next billing cycle.

**What counts as an event?**
Any data point sent to our API: page views, custom events, transactions. Dashboard views by your team don't count.

**Do you offer annual discounts?**
Pro annual saves 20%. Enterprise pricing is negotiated per contract.

**What happens when I hit my event limit?**
We buffer up to 2x your limit for 24 hours. After that, new events are dropped until the next day or you upgrade.

## Social Proof

"FlowMetrics cut our reporting setup from 2 weeks to 2 hours." — Sarah Chen, VP Analytics, ScaleGrid

"We switched from Mixpanel because the pricing was predictable." — Marcus Rivera, CTO, Bolt Commerce

Trusted by 2,400+ companies including Notion, Linear, and Vercel.
```

**Step 2: Write `e2e/fixtures/sample-blog-post.md`**

```markdown
# Why Most Product Launches Fail Before They Start

Every quarter, product teams pour months of work into launches that land with a thud. The feature ships, the blog post goes out, a few customers notice, and then... nothing. Usage stays flat. The team blames distribution. Leadership blames the product.

But the real problem happened months earlier, when nobody asked the hard question: who specifically is this for, and what are they doing today instead?

## The "Build It and They'll Come" Trap

I've watched this play out at three companies now. The pattern is always the same:

1. Someone identifies a gap in the product
2. Engineering builds a solution
3. Marketing writes a launch post
4. The feature gets 15% adoption after 90 days
5. Everyone moves on to the next thing

The missing step is between 1 and 2 — validating that the gap matters to a specific buyer segment more than whatever they're currently doing about it.

## What Changes When You Start with Positioning

When you anchor a launch in positioning rather than features, three things shift:

**You kill bad ideas faster.** If you can't articulate what the customer would go back to without your feature, the feature probably isn't solving a real problem.

**Your messaging writes itself.** When you know the competitive alternative is "spreadsheets and an intern," your value prop isn't abstract. It's concrete and comparative.

**Sales knows what to say.** Instead of a feature list, they have a story: "Your current approach breaks at scale. Here's how."

## The Bottom Line

The best launches I've seen don't start with "what should we build?" They start with "what's the buyer doing today, and why is that about to stop working?"

That's positioning. And it's the step most teams skip.
```

**Step 3: Write `e2e/fixtures/company-briefs/b2b-saas-startup.md`**

```markdown
# Company Brief: DataForge

## What We Do

DataForge is a data pipeline orchestration platform for mid-market companies (200-2,000 employees). We help data engineering teams build, monitor, and debug ETL/ELT pipelines through a visual workflow builder with built-in data quality checks.

## Current State

- 18 months post-launch, 47 paying customers
- $1.2M ARR, growing 15% MoM
- Average deal size $2,100/mo
- 90-day sales cycle
- 3 enterprise logos (>1,000 employees)

## Team

12 people: 6 engineering, 2 sales, 1 marketing, 1 customer success, 2 founders (CEO ex-Databricks, CTO ex-Segment).

## Target Buyer

Data engineering leads at mid-market companies who currently maintain pipelines through a combination of Airflow, custom scripts, and Slack alerts. They spend 30-40% of their time on pipeline maintenance instead of building new data products.

## What Customers Tell Us

- "We tried Airflow but couldn't hire people to maintain it"
- "Our data team was spending more time firefighting than building"
- "The visual debugger is what sold us — we can actually see where pipelines break"
- "We evaluated Dagster and Prefect but they felt too engineer-heavy for our mixed team"

## Competitive Landscape

Direct: Dagster, Prefect, Astronomer (managed Airflow)
Indirect: Custom Airflow deployments, dbt Cloud (partial overlap), Fivetran (ingestion only)
Real alternative for most customers: Cobbled-together Airflow + cron jobs + Slack monitoring

## Current Positioning (what we say today)

"DataForge: Visual data pipeline orchestration for growing teams."

The founders feel this is too generic and doesn't capture why customers pick us over Dagster/Prefect.
```

**Step 4: Commit**

```bash
git add e2e/fixtures/
git commit -m "feat(eval): add fixture content for MVE scenarios"
```

---

### ✅ Task 3: Write persona-panel pricing page scenario

**Files:**
- Create: `e2e/scenarios/persona-panel/pricing-page.yaml`

This scenario tests whether the persona-panel skill produces distinct, specific feedback from multiple buyer personas vs. vanilla's generic review. It matches the detailed example in the design doc.

**Step 1: Write the scenario YAML**

The system prompt for the full-stack provider should load an advisor prompt (the persona-panel skill uses advisor personas as its system context). Use `april-dunford.md` since she's the positioning/pricing expert. The `persona_context` variable loads the advisor file.

```yaml
# e2e/scenarios/persona-panel/pricing-page.yaml
# Promptfoo-native schema -- no translation layer needed

description: "Persona-panel: SaaS pricing page critique"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: full-stack
    config:
      systemMessage: |
        {{persona_context}}

        Evaluate the content below from multiple distinct buyer perspectives.
        For each persona, be concrete -- reference specific elements in the content.
        Provide each persona's unique viewpoint based on their role, psychology,
        and priorities. Structure your output with clear persona headers.
      temperature: 0
      max_tokens: 3000
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: vanilla
    config:
      systemMessage: "You are a helpful assistant."
      temperature: 0
      max_tokens: 3000
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: aware-but-unaided
    config:
      temperature: 0
      max_tokens: 3000

prompts:
  - id: full-stack-prompt
    label: with-skill
    raw: "Evaluate this pricing page for effectiveness:\n\n{{content}}"
  - id: vanilla-prompt
    label: without-skill
    raw: "Review this pricing page and provide detailed feedback:\n\n{{content}}"
  - id: aware-prompt
    label: aware-unaided
    raw: >
      Act as a panel of 5 distinct buyer personas and evaluate this
      pricing page from each perspective separately. Provide specific,
      differentiated feedback from each persona:

      {{content}}

tests:
  - vars:
      content: file://../../fixtures/sample-pricing-page.md
      persona_context: file://../../../advisors/prompts/april-dunford.md
    assert:
      - type: llm-rubric
        value: |
          Score 1-5 on SPECIFICITY: Does the response reference concrete
          elements from the pricing page (specific plan names, price points,
          feature limits, FAQ answers) rather than giving generic advice?
          Generic advice ("add social proof", "clarify pricing") scores 1-2.
          Insights tied to specific content elements with reasoning score 4-5.
        weight: 2
      - type: llm-rubric
        value: |
          Score 1-5 on PERSPECTIVE DIVERSITY: Does the response surface
          multiple distinct viewpoints (e.g., budget-conscious startup vs.
          enterprise buyer vs. technical evaluator), or does it collapse
          to one generic perspective?
        weight: 2
      - type: llm-rubric
        value: |
          Score 1-5 on ACTIONABILITY: Could someone take these
          observations and make specific changes to the pricing page?
          Vague suggestions score 1-2. Concrete recommended changes
          with rationale score 4-5.
        weight: 1
      - type: llm-rubric
        value: |
          Score 1-5 on METHODOLOGY ACCURACY: If the response claims to
          follow a framework or methodology, does it follow it correctly?
          Deduct for hallucinated steps, wrong sequencing, or
          misattributed concepts. Score 5 if no methodology is claimed.
        weight: 1
```

**Step 2: Commit**

```bash
git add e2e/scenarios/persona-panel/pricing-page.yaml
git commit -m "feat(eval): add persona-panel pricing page scenario"
```

---

### ✅ Task 4: Write use-framework 5-Components Positioning scenario

**Files:**
- Create: `e2e/scenarios/use-framework/5-components-positioning.yaml`

This scenario tests whether the 5-Components Positioning framework definition produces a more complete and methodologically accurate positioning document than vanilla or aware-but-unaided.

**Step 1: Write the scenario YAML**

The full-stack provider loads `frameworks/5-components-positioning/prompt.md` as the system prompt. This is the behavioral content — the framework's phase definitions, methodology, and voice.

```yaml
# e2e/scenarios/use-framework/5-components-positioning.yaml

description: "Framework: 5-Components Positioning document generation"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: full-stack
    config:
      systemMessage: file://../../../frameworks/5-components-positioning/prompt.md
      temperature: 0
      max_tokens: 4000
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: vanilla
    config:
      systemMessage: "You are a helpful assistant."
      temperature: 0
      max_tokens: 4000
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: aware-but-unaided
    config:
      temperature: 0
      max_tokens: 4000

prompts:
  - id: full-stack-prompt
    label: with-framework
    raw: >
      Walk me through positioning for this company. Complete all phases
      and produce the full positioning document.

      {{company_brief}}
  - id: vanilla-prompt
    label: without-framework
    raw: "Help me position this company:\n\n{{company_brief}}"
  - id: aware-prompt
    label: aware-unaided
    raw: >
      Use April Dunford's 5 Components of Positioning framework to
      position this company. Work through all 5 components in order
      and produce the full positioning document.

      {{company_brief}}

tests:
  - vars:
      company_brief: file://../../fixtures/company-briefs/b2b-saas-startup.md
    assert:
      - type: llm-rubric
        value: |
          Score 1-5 on COMPLETENESS: Does the document address all 5
          components: (1) Competitive alternatives (2) Unique attributes
          (3) Value (4) Best-fit customers (5) Market category?
          Score 1 if fewer than 3, score 5 if all 5 with depth.
        weight: 2
      - type: llm-rubric
        value: |
          Score 1-5 on METHODOLOGY ACCURACY: Does the document follow
          April Dunford's actual methodology correctly? Deductions for:
          hallucinated steps not in her framework, wrong sequencing
          (e.g., starting with market category instead of competitive
          alternatives), misattributed concepts, or generic strategy
          advice labeled as Dunford's method.
        weight: 2
      - type: llm-rubric
        value: |
          Score 1-5 on SPECIFICITY: Are recommendations grounded in
          the specific company's situation (DataForge, mid-market data
          engineering teams, Airflow alternatives)? Generic advice
          applicable to any B2B SaaS scores 1-2.
        weight: 1
      - type: llm-rubric
        value: |
          Score 1-5 on ACTIONABILITY: Could someone take this document
          and execute on it? Concrete next steps with named deliverables
          score 4-5. Vague direction scores 1-2.
        weight: 1
```

**Step 2: Verify the framework prompt file exists and check frontmatter**

Read `frameworks/5-components-positioning/prompt.md` — confirm it starts with YAML frontmatter. Promptfoo's `file://` reference loads the raw file content as the system message. The frontmatter (`---\nrequired_documents:...\n---`) will be included verbatim. This is a known risk: the frontmatter line `required_documents: positioning statement` could be interpreted by the LLM as an instruction to request a positioning statement before proceeding, which would alter eval behavior.

**Mitigation:** After the first eval run, check the full-stack provider output for Task 4. If the LLM asks for a positioning statement instead of generating the document, add a frontmatter-stripping transform or use a wrapper script that strips `---` blocks before loading. For MVE, accept this risk — the eval prompt explicitly says "produce the full positioning document," which should override the frontmatter suggestion.

> **First-run checkpoint:** When executing this task, run the full-stack provider for this scenario first (`npx promptfoo eval -c scenarios/use-framework/5-components-positioning.yaml`). Inspect the output before proceeding. If the output requests a positioning statement rather than generating one, STOP and implement frontmatter stripping before continuing to Task 5.

**Step 3: Commit**

```bash
git add e2e/scenarios/use-framework/5-components-positioning.yaml
git commit -m "feat(eval): add 5-components positioning framework scenario"
```

---

### ✅ Task 5: Write use-advisor April Dunford blog critique scenario

**Files:**
- Create: `e2e/scenarios/use-advisor/april-dunford-blog-critique.yaml`

This scenario tests whether the April Dunford advisor prompt produces sharper, more domain-specific blog post feedback than vanilla or a user who asks generically for "positioning expert feedback."

**Step 1: Write the scenario YAML**

```yaml
# e2e/scenarios/use-advisor/april-dunford-blog-critique.yaml

description: "Advisor: April Dunford blog post critique"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: full-stack
    config:
      systemMessage: file://../../../advisors/prompts/april-dunford.md
      temperature: 0
      max_tokens: 2500
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: vanilla
    config:
      systemMessage: "You are a helpful assistant."
      temperature: 0
      max_tokens: 2500
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: aware-but-unaided
    config:
      temperature: 0
      max_tokens: 2500

prompts:
  - id: full-stack-prompt
    label: with-advisor
    raw: >
      Review this blog post draft. Tell me what's working, what's not,
      and how to make it stronger.

      {{content}}
  - id: vanilla-prompt
    label: without-advisor
    raw: >
      Review this blog post draft. Tell me what's working, what's not,
      and how to make it stronger.

      {{content}}
  - id: aware-prompt
    label: aware-unaided
    raw: >
      You are April Dunford, positioning consultant and author of
      Obviously Awesome. Review this blog post draft. Tell me what's
      working, what's not, and how to make it stronger.

      {{content}}

tests:
  - vars:
      content: file://../../fixtures/sample-blog-post.md
    assert:
      - type: llm-rubric
        value: |
          Score 1-5 on DOMAIN SPECIFICITY: Does the review demonstrate
          deep positioning/marketing domain expertise? Look for references
          to positioning concepts (competitive alternatives, market
          category, value props, buyer segmentation) applied to the
          specific content. Generic writing advice scores 1-2.
        weight: 2
      - type: llm-rubric
        value: |
          Score 1-5 on VOICE CONSISTENCY: Does the response sound like
          a specific expert with a recognizable voice, or like a generic
          AI assistant? Look for: consistent tone, distinctive phrasing,
          opinionated stance, concrete examples from experience.
          Bland, hedge-everything tone scores 1-2.
        weight: 2
      - type: llm-rubric
        value: |
          Score 1-5 on ACTIONABILITY: Could the author take this feedback
          and make specific edits? Line-level suggestions with reasoning
          score 4-5. Vague "consider adding more detail" scores 1-2.
        weight: 1
      - type: llm-rubric
        value: |
          Score 1-5 on INSIGHT QUALITY: Does the review surface non-obvious
          observations that a casual reader would miss? Look for: structural
          critique, audience mismatch flags, logical gaps, missed
          opportunities. Superficial praise/critique scores 1-2.
        weight: 1
```

**Step 2: Commit**

```bash
git add e2e/scenarios/use-advisor/april-dunford-blog-critique.yaml
git commit -m "feat(eval): add April Dunford blog critique advisor scenario"
```

---

### ✅ Task 6: Write promptfooconfig.yaml master config and validate scenarios

**Files:**
- Create: `e2e/promptfooconfig.yaml`

The master config aggregates all scenario files and configures the judge LLM. Individual scenarios can still run independently via `npx promptfoo eval -c scenarios/<path>`.

**Step 1: Write `e2e/promptfooconfig.yaml`**

```yaml
# e2e/promptfooconfig.yaml
# Master config — aggregates all MVE scenarios
# Run: npx promptfoo eval (from e2e/ directory)
# Run single: npx promptfoo eval -c scenarios/persona-panel/pricing-page.yaml

# Judge LLM configuration — pinned for reproducibility
# Judge variance must not exceed the 0.5-point regression threshold
defaultTest:
  options:
    provider:
      id: anthropic:messages:claude-sonnet-4-20250514
      config:
        temperature: 0
    retry: 2

# Import all MVE scenarios
scenarios:
  - file://scenarios/persona-panel/pricing-page.yaml
  - file://scenarios/use-framework/5-components-positioning.yaml
  - file://scenarios/use-advisor/april-dunford-blog-critique.yaml
```

**Step 2: Validate all scenario files**

Run: `cd e2e && npx promptfoo validate`

Expected: All scenario files pass validation with no schema errors. If validation fails, fix the YAML syntax errors before proceeding.

**Step 3: Commit**

```bash
git add e2e/promptfooconfig.yaml
git commit -m "feat(eval): add master promptfoo config with judge LLM pinning"
```

---

### ✅ Task 7: Write distinctness scorer with TDD — parsing logic

**Files:**
- Create: `e2e/tests/test_distinctness.py`
- Create: `e2e/tests/conftest.py`
- Create: `e2e/tests/__init__.py`
- Create: `e2e/scorers/__init__.py`
- Create: `e2e/scorers/distinctness.py`

The distinctness scorer is a post-processing step that runs after `promptfoo eval` completes. It parses persona-panel output into per-persona sections, computes pairwise cosine similarity using embeddings, and reports pass/fail.

This task covers the persona section parser. Task 8 adds the embedding computation and error paths.

**Step 1: Write failing tests for persona section parsing**

```python
# e2e/tests/test_distinctness.py

import pytest
from scorers.distinctness import parse_persona_sections


class TestParsePersonaSections:
    """Tests for extracting individual persona sections from structured output."""

    def test_parses_markdown_header_sections(self):
        """Sections delimited by ## Persona Name headers."""
        output = (
            "## The Budget-Conscious Startup Founder\n"
            "The free tier is attractive but the jump to $49/seat is steep "
            "for a 5-person team. That's $245/month before we've proven ROI. "
            "I'd want a 14-day Pro trial before committing.\n\n"
            "## The Enterprise Procurement Lead\n"
            "No per-seat pricing transparency on Enterprise is a red flag. "
            "I need to bring a number to my CFO, not 'custom pricing.' "
            "The 99.9% SLA is table stakes — I'd want to see the penalty clause.\n\n"
            "## The Technical Evaluator\n"
            "API access locked behind Pro is frustrating. I want to prototype "
            "an integration before my team commits. The 1,000 events/day free "
            "limit is too low for a meaningful proof-of-concept."
        )
        sections = parse_persona_sections(output)
        assert len(sections) == 3
        assert "Budget-Conscious Startup Founder" in sections[0]["name"]
        assert "$49/seat" in sections[0]["content"]
        assert "Enterprise Procurement Lead" in sections[1]["name"]
        assert "Technical Evaluator" in sections[2]["name"]
        assert "API access" in sections[2]["content"]

    def test_parses_numbered_persona_sections(self):
        """Sections delimited by numbered headers like '1. Persona Name'."""
        output = (
            "1. **The CTO**\n"
            "SSO/SAML only on Enterprise is standard but the lack of "
            "audit logs on Pro is concerning for SOC 2 compliance.\n\n"
            "2. **The Data Analyst**\n"
            "7-day retention on free is useless for weekly reporting. "
            "90 days on Pro works but I'd want 180 for quarterly analysis."
        )
        sections = parse_persona_sections(output)
        assert len(sections) == 2
        assert "CTO" in sections[0]["name"]
        assert "SOC 2" in sections[0]["content"]
        assert "Data Analyst" in sections[1]["name"]

    def test_returns_empty_list_for_unparseable_output(self):
        """Output with no recognizable persona structure."""
        output = (
            "This pricing page has several issues. The free tier is limited "
            "and the jump to Pro is steep. Enterprise pricing should be "
            "more transparent."
        )
        sections = parse_persona_sections(output)
        assert sections == []

    def test_handles_single_persona(self):
        """Edge case: only one persona section."""
        output = (
            "## The Developer\n"
            "API rate limits aren't documented anywhere on the pricing page. "
            "I need to know if 100K events/day is a hard cap or a soft limit."
        )
        sections = parse_persona_sections(output)
        assert len(sections) == 1
        assert "Developer" in sections[0]["name"]
```

**Step 2: Run tests to verify they fail**

Run: `cd e2e && python -m pytest tests/test_distinctness.py -v`

Expected: ImportError — `scorers.distinctness` module doesn't exist yet.

**Step 3: Create `e2e/scorers/__init__.py` and `e2e/tests/__init__.py`**

```bash
touch e2e/scorers/__init__.py e2e/tests/__init__.py
```

Also create `e2e/tests/conftest.py` to configure the Python path. This file also serves as the designated location for any shared pytest fixtures added post-MVE.

```python
# e2e/tests/conftest.py
import sys
from pathlib import Path

# Add e2e/ to Python path so `from scorers.distinctness import ...` works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

**Step 4: Implement persona section parser**

```python
# e2e/scorers/distinctness.py
"""
Inter-persona distinctness scorer for persona-panel eval scenarios.

Runs as a post-processing step AFTER `promptfoo eval` completes.
Parses persona-panel output into per-persona sections, computes pairwise
cosine similarity using embeddings, and reports pass/fail.

Usage:
    python scorers/distinctness.py results.json [--threshold 0.92]
"""

from __future__ import annotations

import re


def parse_persona_sections(output: str) -> list[dict]:
    """Extract individual persona sections from structured LLM output.

    Supports two formats:
    - Markdown headers: ## Persona Name
    - Numbered bold: 1. **Persona Name**

    Returns list of {"name": str, "content": str} dicts.
    Returns empty list if no recognizable persona structure found.
    """
    sections: list[dict] = []

    # Try markdown headers first: ## The Persona Name or ## Persona Name
    header_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    headers = list(header_pattern.finditer(output))

    if len(headers) >= 2:
        for i, match in enumerate(headers):
            name = match.group(1).strip()
            start = match.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(output)
            content = output[start:end].strip()
            sections.append({"name": name, "content": content})
        return sections

    # Try numbered bold: 1. **Persona Name**
    numbered_pattern = re.compile(
        r"^\d+\.\s+\*\*(.+?)\*\*\s*$", re.MULTILINE
    )
    numbered_headers = list(numbered_pattern.finditer(output))

    if len(numbered_headers) >= 2:
        for i, match in enumerate(numbered_headers):
            name = match.group(1).strip()
            start = match.end()
            end = (
                numbered_headers[i + 1].start()
                if i + 1 < len(numbered_headers)
                else len(output)
            )
            content = output[start:end].strip()
            sections.append({"name": name, "content": content})
        return sections

    # Single header — still return it
    if len(headers) == 1:
        name = headers[0].group(1).strip()
        content = output[headers[0].end() :].strip()
        sections.append({"name": name, "content": content})
        return sections

    if len(numbered_headers) == 1:
        name = numbered_headers[0].group(1).strip()
        content = output[numbered_headers[0].end() :].strip()
        sections.append({"name": name, "content": content})
        return sections

    return []
```

**Step 5: Run tests to verify they pass**

Run: `cd e2e && python -m pytest tests/test_distinctness.py -v`

Expected: All 4 tests PASS.

**Step 6: Commit**

```bash
git add e2e/scorers/ e2e/tests/
git commit -m "feat(eval): add persona section parser with tests"
```

---

### ✅ Task 8: Add embedding computation, CLI entry point, and error path tests

**Files:**
- Modify: `e2e/scorers/distinctness.py` (add `compute_similarity`, `score_results`, `main`)
- Modify: `e2e/tests/test_distinctness.py` (add similarity and error path tests)

**Step 1: Write failing tests for similarity computation and CLI**

Append to `e2e/tests/test_distinctness.py`:

```python
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from scorers.distinctness import (
    compute_pairwise_similarity,
    score_results,
    DEFAULT_THRESHOLD,
)


class TestComputePairwiseSimilarity:
    """Tests for embedding-based pairwise cosine similarity."""

    @patch("scorers.distinctness.get_embeddings")
    def test_distinct_texts_pass_threshold(self, mock_embeddings):
        """Texts about different topics should have low similarity."""
        # Simulate embeddings that are far apart (cosine sim ~0.5)
        mock_embeddings.return_value = [
            [1.0, 0.0, 0.0],  # persona 1: pricing concerns
            [0.0, 1.0, 0.0],  # persona 2: technical evaluation
            [0.0, 0.0, 1.0],  # persona 3: enterprise compliance
        ]
        sections = [
            {"name": "Budget Buyer", "content": "pricing is steep"},
            {"name": "Tech Lead", "content": "API limits matter"},
            {"name": "Compliance", "content": "SOC 2 required"},
        ]
        result = compute_pairwise_similarity(sections)
        assert result["pass"] is True
        assert result["max_similarity"] == pytest.approx(0.0, abs=0.01)
        assert len(result["pairs"]) == 3  # C(3,2) = 3 pairs

    @patch("scorers.distinctness.get_embeddings")
    def test_identical_texts_fail_threshold(self, mock_embeddings):
        """Identical embeddings should fail with similarity 1.0."""
        mock_embeddings.return_value = [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ]
        sections = [
            {"name": "Persona A", "content": "same text"},
            {"name": "Persona B", "content": "same text"},
        ]
        result = compute_pairwise_similarity(sections)
        assert result["pass"] is False
        assert result["max_similarity"] == pytest.approx(1.0, abs=0.01)

    @patch("scorers.distinctness.get_embeddings")
    def test_barely_below_threshold_passes(self, mock_embeddings):
        """Similarity at 0.919 (just below 0.92 threshold) should pass."""
        import math

        # Vectors with cosine similarity ~0.919
        mock_embeddings.return_value = [
            [1.0, 0.0],
            [0.919, math.sqrt(1 - 0.919**2)],
        ]
        sections = [
            {"name": "A", "content": "text a"},
            {"name": "B", "content": "text b"},
        ]
        result = compute_pairwise_similarity(sections, threshold=0.92)
        assert result["pass"] is True


class TestErrorPaths:
    """Error handling for API failures and malformed input."""

    @patch("scorers.distinctness.get_embeddings")
    def test_embedding_api_rate_limit_skips_with_warning(self, mock_embeddings):
        """429 from embedding API should skip, not crash."""
        mock_embeddings.side_effect = Exception("Rate limit exceeded (429)")
        sections = [
            {"name": "A", "content": "text"},
            {"name": "B", "content": "other text"},
        ]
        result = compute_pairwise_similarity(sections)
        assert result["skipped"] is True
        assert "rate limit" in result["reason"].lower() or "error" in result["reason"].lower()

    @patch("scorers.distinctness.get_embeddings")
    def test_embedding_api_server_error_skips_with_warning(self, mock_embeddings):
        """500 from embedding API should skip, not crash."""
        mock_embeddings.side_effect = Exception("Internal server error (500)")
        sections = [
            {"name": "A", "content": "text"},
            {"name": "B", "content": "other text"},
        ]
        result = compute_pairwise_similarity(sections)
        assert result["skipped"] is True

    def test_unparseable_output_reports_skip(self):
        """Results with no persona structure should report unparseable."""
        results_data = {
            "results": {
                "results": [
                    {
                        "provider": {"label": "full-stack"},
                        "description": "Persona-panel: SaaS pricing page critique",
                        "response": {"output": "Generic feedback with no persona structure."},
                    }
                ]
            }
        }
        result = score_results(results_data, scenario_filter="persona-panel")
        assert result["skipped"] is True
        assert "unparseable" in result["reason"].lower()

    @patch("scorers.distinctness.get_embeddings")
    def test_all_identical_outputs_fail_with_matrix(self, mock_embeddings):
        """All personas producing identical output should fail clearly."""
        mock_embeddings.return_value = [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ]
        sections = [
            {"name": "Persona 1", "content": "identical"},
            {"name": "Persona 2", "content": "identical"},
            {"name": "Persona 3", "content": "identical"},
        ]
        result = compute_pairwise_similarity(sections)
        assert result["pass"] is False
        assert result["max_similarity"] == pytest.approx(1.0, abs=0.01)
        # All 3 pairs should show 1.0
        assert all(p["similarity"] == pytest.approx(1.0, abs=0.01) for p in result["pairs"])
```

**Step 2: Run tests to verify new tests fail**

Run: `cd e2e && python -m pytest tests/test_distinctness.py -v`

Expected: ImportError for `compute_pairwise_similarity`, `score_results`, `DEFAULT_THRESHOLD`.

**Step 3: Implement similarity computation and CLI**

Append to `e2e/scorers/distinctness.py`:

```python
import json
import sys
from itertools import combinations

DEFAULT_THRESHOLD = 0.92


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings from OpenAI text-embedding-3-small.

    Uses OpenAI because distinctness measurement doesn't need large
    embeddings — small model is cheaper and sufficient for cosine distance.
    """
    from openai import OpenAI

    client = OpenAI()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def compute_pairwise_similarity(
    sections: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    """Compute pairwise cosine similarity across persona sections.

    Returns:
        {
            "pass": bool,
            "max_similarity": float,
            "pairs": [{"a": str, "b": str, "similarity": float}, ...],
            "skipped": False,
        }
        On API error:
        {"skipped": True, "reason": str}
    """
    texts = [s["content"] for s in sections]

    try:
        embeddings = get_embeddings(texts)
    except Exception as e:
        return {
            "skipped": True,
            "reason": f"Embedding API error: {e}",
        }

    pairs = []
    max_sim = 0.0
    for i, j in combinations(range(len(sections)), 2):
        sim = _cosine_similarity(embeddings[i], embeddings[j])
        pairs.append({
            "a": sections[i]["name"],
            "b": sections[j]["name"],
            "similarity": round(sim, 4),
        })
        max_sim = max(max_sim, sim)

    return {
        "pass": max_sim < threshold,
        "max_similarity": round(max_sim, 4),
        "pairs": pairs,
        "threshold": threshold,
        "skipped": False,
    }


def score_results(
    results_data: dict,
    scenario_filter: str = "persona-panel",
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    """Score distinctness from Promptfoo results JSON.

    Filters for full-stack provider results from persona-panel scenarios,
    parses persona sections, and computes similarity.
    """
    results_list = results_data.get("results", {}).get("results", [])

    # Find full-stack outputs from matching scenarios
    full_stack_outputs = []
    for r in results_list:
        provider_label = r.get("provider", {}).get("label", "")
        description = r.get("description", "")
        if provider_label == "full-stack" and scenario_filter in description.lower():
            output = r.get("response", {}).get("output", "")
            if output:
                full_stack_outputs.append(output)

    if not full_stack_outputs:
        return {"skipped": True, "reason": "No full-stack outputs found in results"}

    # Parse persona sections from the first matching output
    sections = parse_persona_sections(full_stack_outputs[0])

    if len(sections) < 2:
        return {"skipped": True, "reason": "Unparseable: fewer than 2 persona sections found"}

    return compute_pairwise_similarity(sections, threshold=threshold)


def main():
    """CLI entry point: python scorers/distinctness.py results.json [--threshold 0.92]"""
    if len(sys.argv) < 2:
        print("Usage: python scorers/distinctness.py <results.json> [--threshold 0.92]")
        sys.exit(1)

    results_path = sys.argv[1]
    threshold = DEFAULT_THRESHOLD

    if "--threshold" in sys.argv:
        idx = sys.argv.index("--threshold")
        threshold = float(sys.argv[idx + 1])

    with open(results_path) as f:
        results_data = json.load(f)

    result = score_results(results_data, threshold=threshold)

    print(json.dumps(result, indent=2))

    if result.get("skipped"):
        print(f"\nWARNING: Distinctness check skipped — {result['reason']}")
        sys.exit(0)

    if result["pass"]:
        print(f"\nPASS: Max similarity {result['max_similarity']} < {threshold}")
    else:
        print(f"\nFAIL: Max similarity {result['max_similarity']} >= {threshold}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 4: Run all tests to verify they pass**

Run: `cd e2e && python -m pytest tests/test_distinctness.py -v`

Expected: All tests PASS (11 total: 4 parsing + 3 similarity + 4 error path).

**Step 5: Commit**

```bash
git add e2e/scorers/distinctness.py e2e/tests/
git commit -m "feat(eval): add distinctness scorer with embedding similarity and error handling"
```

---

### Task 9: Write README.md with setup instructions

**Files:**
- Create: `e2e/README.md`

MVE scope: minimal setup instructions. Full methodology README is a post-MVE deliverable.

**Step 1: Write `e2e/README.md`**

```markdown
# Aligned Eval Framework

Quantitative evaluation of Aligned plugin skills using Promptfoo.

**Core question:** Does a skill produce a measurably better deliverable than prompting the LLM directly?

## Prerequisites

- Node.js 18+
- Python 3.10+
- `ANTHROPIC_API_KEY` environment variable (for eval providers and judge LLM)
- `OPENAI_API_KEY` environment variable (for distinctness scorer embeddings)

## Setup

```bash
cd e2e
npm install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Running Evals

Run all MVE scenarios:

```bash
npx promptfoo eval
```

Run a single scenario:

```bash
npx promptfoo eval -c scenarios/persona-panel/pricing-page.yaml
```

Validate scenario YAML syntax:

```bash
npx promptfoo validate
```

Dry run (validates wiring without API calls):

```bash
npx promptfoo eval --dry-run
```

View results in browser:

```bash
npx promptfoo view
```

## Running the Distinctness Scorer

After an eval run, score inter-persona distinctness:

```bash
python scorers/distinctness.py output/latest.json
```

Adjust the similarity threshold (default 0.92):

```bash
python scorers/distinctness.py output/latest.json --threshold 0.90
```

## Running Tests

```bash
cd e2e
python -m pytest tests/ -v
```

## Three-Provider Comparison

Every scenario runs input through three providers:

| Provider | System Prompt | What It Proves |
|----------|--------------|----------------|
| **Full Stack** | Advisor/framework prompt | What Aligned users get |
| **Vanilla** | "You are a helpful assistant." | Baseline — no structure |
| **Aware But Unaided** | None (framework named in user prompt) | Competent ChatGPT user |

## Pass/Fail Thresholds

| Metric | Threshold |
|--------|-----------|
| Full-stack vs. vanilla delta | >= +1.0 avg across rubrics |
| Full-stack vs. aware-but-unaided delta | >= +0.5 avg |
| Absolute full-stack score | >= 3.5 / 5.0 avg |
| Inter-persona distinctness | cosine similarity < 0.92 all pairs |

Thresholds are starting points — calibrate after the first few runs.
```

**Step 2: Commit**

```bash
git add e2e/README.md
git commit -m "docs(eval): add MVE README with setup and usage instructions"
```

---

### Task 10: Add fixture smoke tests, run end-to-end validation, and final commit

**Files:**
- Create: `e2e/tests/test_fixtures.py`

**Step 1: Write fixture smoke tests**

The design doc requires smoke tests confirming each fixture loads and is non-empty.

```python
# e2e/tests/test_fixtures.py

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

EXPECTED_FIXTURES = [
    "sample-pricing-page.md",
    "sample-blog-post.md",
    "company-briefs/b2b-saas-startup.md",
]


@pytest.mark.parametrize("fixture_path", EXPECTED_FIXTURES)
def test_fixture_exists_and_is_non_empty(fixture_path):
    """Each fixture file must exist and contain content."""
    full_path = FIXTURES_DIR / fixture_path
    assert full_path.exists(), f"Fixture not found: {full_path}"
    content = full_path.read_text()
    assert len(content.strip()) > 0, f"Fixture is empty: {full_path}"
```

**Step 2: Run fixture smoke tests**

Run: `cd e2e && python -m pytest tests/test_fixtures.py -v`

Expected: All 3 fixture tests PASS.

**Step 3: Validate all scenario YAML files**

Run: `cd e2e && npx promptfoo validate`

Expected: All 3 scenario files pass validation. If any fail, fix the schema errors.

**Step 4: Run dry run**

Run: `cd e2e && npx promptfoo eval --dry-run`

Expected: Pipeline wires up correctly — providers, prompts, and test vars resolve without errors. No API calls are made.

**Step 5: Run all tests**

Run: `cd e2e && python -m pytest tests/ -v`

Expected: All tests pass (11 scorer tests + 3 fixture smoke tests = 14 total).

**Step 6: Final commit**

```bash
git add e2e/tests/test_fixtures.py
git commit -m "test(eval): add fixture smoke tests and validate end-to-end pipeline"
```

If validation or dry run required fixes, stage those too:

```bash
git add e2e/tests/test_fixtures.py e2e/scenarios/ e2e/promptfooconfig.yaml e2e/scorers/
git commit -m "test(eval): add fixture smoke tests and fix validation issues"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | `file://` path resolution strategy | Relative paths from scenario YAML location | Absolute paths, repo-root-relative with `--config-dir` |
| 2 | Distinctness scorer as standalone Python script | Post-processing step on results JSON | Promptfoo inline `type: python` assertion, Node.js implementation |
| 3 | Scenario YAML file references for system prompts | `file://` with relative paths to advisor/framework files | Inline system prompts, environment variable interpolation |
| 4 | Single fixture per scenario for MVE | One test case per scenario | Multiple test cases with `vars` array |
| 5 | Blog critique (not positioning) for advisor scenario | April Dunford reviewing a blog post | April Dunford running a positioning exercise (overlaps with framework scenario) |
| 6 | Persona-panel system prompt: multi-persona framing | Multi-persona "evaluate from multiple buyer perspectives" | Design doc's single-persona "evaluate from your specific buyer perspective" |
| 7 | Persona-panel max_tokens: 3000 | 3000 (accommodates multi-persona output) | Design doc's 2000 |
| 8 | Post-MVE fixture deferral | Only 3 fixtures for MVE | Design doc lists 5 fixture files (sample-landing-page.md, sample-design-doc.md, dtc-health-product.md also referenced) |

### Appendix: Decision Details

#### Decision 1: `file://` path resolution strategy
**Chose:** Relative paths from scenario YAML file location (e.g., `file://../../fixtures/sample-pricing-page.md`)
**Why:** Promptfoo resolves `file://` paths relative to the config file that contains them. Since scenarios live in `e2e/scenarios/<skill-type>/`, paths must navigate up to reach `e2e/fixtures/` (two levels) or the repo root for advisor/framework files (three levels). This matches Promptfoo's documented behavior and avoids relying on undocumented `--config-dir` flags that could change between versions.
**Alternatives rejected:**
- Absolute paths: Would break on any machine other than the author's. Non-starter for a git-committed config.
- Repo-root-relative with custom base: Promptfoo doesn't natively support a `basePath` config. Would require a wrapper script.

#### Decision 2: Distinctness scorer implementation approach
**Chose:** Standalone Python script that post-processes Promptfoo results JSON
**Why:** Promptfoo's `type: python` custom assertions receive a single output string per invocation. Inter-persona distinctness requires comparing all persona outputs simultaneously (pairwise cosine similarity). This is structurally impossible as an inline assertion. The design doc explicitly specifies this approach (see "Custom Distinctness Scorer" section).
**Alternatives rejected:**
- Inline Promptfoo assertion: Can't access multiple provider outputs in a single assertion call. Architectural mismatch.
- Node.js implementation: The design doc specifies Python with OpenAI embeddings. Python's ecosystem is stronger for numerical computation. Keeping the scorer in Python also lets us use pytest for testing.

#### Decision 3: System prompt loading via `file://`
**Chose:** Direct `file://` references to existing advisor prompt and framework prompt.md files
**Why:** The design doc explicitly states that advisor prompts and framework `prompt.md` files contain the behavioral content suitable for system prompts. SKILL.md files contain Claude Code orchestration instructions (sub-agent dispatch, tool usage) that are meaningless in API calls. Using `file://` avoids duplicating content and ensures evals test the same content that users get.
**Alternatives rejected:**
- Inline system prompts: Would duplicate advisor/framework content, creating drift risk.
- Template files: Unnecessary indirection for MVE. If system prompts need preprocessing later, add a transform step then.

#### Decision 4: Single fixture per scenario for MVE
**Chose:** One test case per scenario YAML (one `vars` entry in the `tests` array)
**Why:** MVE goal is proving the harness works and the ship/kill signal is meaningful. Three scenarios × three providers = 9 API calls is enough to validate the comparison pattern. Adding multiple fixtures per scenario increases cost and complexity without changing the fundamental question of whether the eval works. Post-MVE can add `vars` array entries for broader coverage.
**Alternatives rejected:**
- Multiple test cases: Premature for MVE. The first run will reveal whether scoring rubrics need calibration — running more test cases against uncalibrated rubrics wastes API spend.

#### Decision 5: Blog critique for advisor scenario (not positioning)
**Chose:** April Dunford reviewing a blog post about product launches
**Why:** The use-framework scenario already tests April Dunford's 5-Components Positioning methodology with a company brief. Using the same advisor for positioning in both scenarios would create overlap and wouldn't test a distinct skill shape. A blog critique tests the "single advisor critique" pattern: domain expert voice applied to content review, which is the primary use case for `use-advisor`. The blog post content is deliberately related to positioning (it discusses product launch failures) so the advisor's domain expertise is relevant.
**Alternatives rejected:**
- Positioning exercise: Overlaps with the use-framework 5-Components scenario. Both would test the same methodology, just with different orchestration.
- Different advisor: April Dunford is the most developed advisor and is referenced throughout the design doc. Using her for both scenarios keeps the MVE focused.

#### Decision 6: Persona-panel system prompt framing
**Chose:** Multi-persona framing ("Evaluate from multiple distinct buyer perspectives... Structure your output with clear persona headers")
**Why:** The design doc's example uses a single-persona framing ("your specific buyer perspective"), but the persona-panel skill's core value is producing *multiple distinct perspectives*. A single-persona system prompt would produce a single-viewpoint output, making the distinctness scorer meaningless and defeating the purpose of the scenario. The multi-persona framing instructs the LLM to produce structured, per-persona sections that the distinctness scorer can parse and compare.
**Alternatives rejected:**
- Design doc's single-persona framing: Would produce a single perspective, not a multi-persona panel. The distinctness scorer requires multiple parseable sections.

#### Decision 7: Persona-panel max_tokens increase to 3000
**Chose:** 3000 tokens (up from design doc's 2000)
**Why:** The multi-persona system prompt (Decision 6) asks for structured output from multiple personas. Each persona section needs 300-500 tokens for substantive feedback. With 5 personas at 400 tokens each, 2000 tokens would truncate the output. 3000 gives headroom for 5 detailed persona sections without waste.
**Alternatives rejected:**
- 2000 (design doc value): Risk of truncated output, especially for the full-stack provider where persona sections need depth.

#### Decision 8: Post-MVE fixture deferral
**Chose:** Only 3 fixture files for MVE (sample-pricing-page.md, sample-blog-post.md, b2b-saas-startup.md)
**Why:** The design doc's repo structure lists additional fixtures (sample-landing-page.md, sample-design-doc.md, dtc-health-product.md) but only 3 MVE scenarios exist. Each fixture maps to one scenario. Additional fixtures are post-MVE artifacts for expanded scenario coverage.
**Alternatives rejected:**
- Create all 5 fixtures now: No scenario uses them. Writing content that sits unused adds maintenance burden without value.
