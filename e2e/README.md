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

Validate config loads correctly (runs 1 test):

```bash
npx promptfoo eval --filter-first-n 1 --no-write
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
