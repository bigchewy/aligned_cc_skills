# Audit Scoring Algorithm

Unified scoring formula for all test auditor workers.

## Penalty Formula

```
penalty = (critical × 2.0) + (high × 1.0) + (medium × 0.5) + (low × 0.2)
score = max(0, 10 - penalty)
```

## Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| 8-10 | Healthy | No urgent issues |
| 6-7 | Moderate | Address when convenient |
| 4-5 | Significant | Prioritize fixes |
| 0-3 | Critical | Immediate action required |

## Severity Weights

| Severity | Weight | Meaning |
|----------|--------|---------|
| CRITICAL | 2.0 | Tests that actively mislead (no assertions, test their own mocks) |
| HIGH | 1.0 | Tests that waste maintenance effort (framework tests, low value) |
| MEDIUM | 0.5 | Tests with fixable issues (happy path only, isolation concerns) |
| LOW | 0.2 | Minor improvements (test naming, minor refactoring) |
