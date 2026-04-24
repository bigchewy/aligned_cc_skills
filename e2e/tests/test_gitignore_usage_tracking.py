"""Regression test: ensure ~/.claude/.gitignore continues to ignore usage-tracking/.

The forward-compatibility guard from docs/plans/2026-04-23-claude-usage-logging-design.md
section 'Forward-compatibility guard (QA)'. If someone refactors the ignore file and
drops coverage of usage-tracking/, this test catches it.
"""
import subprocess
from pathlib import Path


def test_usage_tracking_is_git_ignored():
    claude_dir = Path.home() / ".claude"
    if not claude_dir.is_dir():
        # Skip on CI / fresh installs — this is a regression guard for the author's env.
        return
    candidates = [
        "usage-tracking/prompts-abc123.jsonl",
        "usage-tracking/violations.jsonl",
        "digests/2026-W17.md",
    ]
    for rel in candidates:
        result = subprocess.run(
            ["git", "-C", str(claude_dir), "check-ignore", "--no-index", rel],
            capture_output=True, text=True,
        )
        # check-ignore exits 0 if path IS ignored, 1 if NOT ignored.
        assert result.returncode == 0, (
            f"~/.claude/{rel} is NOT gitignored — auto-commit would push it. "
            f"Review the '*' catch-all + allowlist in ~/.claude/.gitignore."
        )
