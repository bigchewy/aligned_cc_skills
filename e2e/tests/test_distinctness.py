# e2e/tests/test_distinctness.py

import subprocess
import sys
from pathlib import Path

import pytest
from unittest.mock import patch

from scorers.distinctness import (
    parse_persona_sections,
    compute_pairwise_similarity,
    score_results,
    DEFAULT_THRESHOLD,
)


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


class TestComputePairwiseSimilarity:
    """Tests for embedding-based pairwise cosine similarity."""

    @patch("scorers.distinctness.get_embeddings")
    def test_distinct_texts_pass_threshold(self, mock_embeddings):
        """Texts about different topics should have low similarity."""
        mock_embeddings.return_value = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
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
        assert all(p["similarity"] == pytest.approx(1.0, abs=0.01) for p in result["pairs"])

    def test_no_full_stack_outputs_reports_skip(self):
        """Results with no full-stack provider should skip."""
        results_data = {
            "results": {
                "results": [
                    {
                        "provider": {"label": "vanilla"},
                        "description": "Persona-panel: SaaS pricing page critique",
                        "response": {"output": "Some output"},
                    }
                ]
            }
        }
        result = score_results(results_data, scenario_filter="persona-panel")
        assert result["skipped"] is True
        assert "no full-stack" in result["reason"].lower()


class TestCLIErrorPaths:
    """Tests for CLI argument validation in main()."""

    def test_threshold_flag_without_value_exits(self):
        """--threshold with no following value should exit with error."""
        scorer_path = str(Path(__file__).resolve().parent.parent / "scorers" / "distinctness.py")
        result = subprocess.run(
            [sys.executable, scorer_path, "dummy.json", "--threshold"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "requires a numeric value" in result.stdout

    def test_nonexistent_results_file_exits(self):
        """A missing results file should exit with error."""
        scorer_path = str(Path(__file__).resolve().parent.parent / "scorers" / "distinctness.py")
        result = subprocess.run(
            [sys.executable, scorer_path, "/nonexistent/path.json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "not found" in result.stdout
