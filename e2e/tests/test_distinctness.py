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
