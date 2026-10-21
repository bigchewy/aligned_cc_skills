"""Boris Cherny checks what's new before his first answer, and says so when he can't.

His prompt tells him to read ~/.claude/aligned/boris-cherny-whats-new.md before
he answers. Where he can't read files or search (web chat, or an eval with no
tools), he must not try. A model that tries anyway sends back a fake file read
and no answer. Close the Loop's Phase 0 already covers this case; the advisor
prompt has to cover it too.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BORIS = REPO_ROOT / "advisors" / "prompts" / "boris-cherny.md"
CLOSE_THE_LOOP = REPO_ROOT / "frameworks" / "close-the-loop" / "prompt.md"


def _section(text, heading):
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def test_boris_reads_the_saved_file_first():
    section = _section(BORIS.read_text(encoding="utf-8"), "## Check What's New First")
    assert "~/.claude/aligned/boris-cherny-whats-new.md" in section


def test_boris_answers_without_trying_when_he_cannot_read_or_search():
    section = _section(BORIS.read_text(encoding="utf-8"), "## Check What's New First").lower()
    assert "can't read files" in section
    assert "don't try" in section
    assert "february 2026" in section


def test_close_the_loop_covers_the_same_case():
    text = CLOSE_THE_LOOP.read_text(encoding="utf-8")
    assert "can't search or fetch" in text
