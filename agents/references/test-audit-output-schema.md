# Test Auditor Worker Output Schema

Standard JSON output format for all test auditor workers.

## Worker Output Format

Each worker MUST return a single JSON block:

```json
{
  "category": "Category Name",
  "score": 7.5,
  "total_issues": 12,
  "critical": 1,
  "high": 3,
  "medium": 5,
  "low": 3,
  "checks": [
    {
      "id": "check_identifier",
      "name": "Human-Readable Check Name",
      "status": "passed|failed|warning",
      "details": "Brief explanation"
    }
  ],
  "findings": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "location": "src/path/to/file.test.ts:42",
      "issue": "Concise description of the problem",
      "category": "Category / Specific Rule",
      "recommendation": "Actionable fix suggestion",
      "effort": "S|M|L"
    }
  ]
}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | Audit category name |
| `score` | number | 0-10 scale per `audit-scoring.md` |
| `total_issues` | integer | Sum of all severity counts |
| `critical/high/medium/low` | integer | Issue counts by severity |
| `checks` | array | Discrete audit checks with pass/fail status |
| `findings` | array | Detailed issues with recommendations |

## Finding Effort Estimates

| Code | Meaning |
|------|---------|
| S | < 30 minutes (delete a test, add an assertion) |
| M | 30 min - 2 hours (rewrite a test, add error path tests) |
| L | > 2 hours (restructure test file, add integration tests for untested paths) |
