"""
Tests for study commands (review, synthesize).
"""
import sys
import pytest
from pathlib import Path
from typer.testing import CliRunner
from rich.console import Console

# We need to ensure we can import from src
# In a real environment, devbase is installed, but for tests we might need path hacking
sys.path.insert(0, str(Path.cwd() / "src"))

from devbase.main import app

runner = CliRunner()

@pytest.fixture
def mock_knowledge_base(tmp_path):
    """Creates a mock knowledge base with some notes."""
    kb_path = tmp_path / "10-19_KNOWLEDGE" / "11_public_garden"
    kb_path.mkdir(parents=True)

    # Create some notes
    notes = [
        {
            "filename": "note1.md",
            "content": "---\ntitle: Note One\ntype: til\ncreated: 2023-01-01\n---\nContent 1"
        },
        {
            "filename": "note2.md",
            "content": "---\ntitle: Note Two\ntype: concept\ncreated: 2023-01-02\n---\nContent 2"
        },
        {
            "filename": "note3.md",
            "content": "---\ntitle: Note Three\ntype: til\ncreated: 2023-01-03\n---\nContent 3"
        }
    ]

    for note in notes:
        (kb_path / note["filename"]).write_text(note["content"], encoding="utf-8")

    return tmp_path

def test_study_review(mock_knowledge_base):
    """Test study review command."""
    # We need to mock input because the command asks for Enter and Confirm
    # Input stream: Enter (view answer), 'y' (remembered), Enter (next note/finish)
    # The command loops through notes. If we request count=1, we need minimal inputs.

    result = runner.invoke(
        app,
        ["--root", str(mock_knowledge_base), "study", "review", "--count", "1"],
        input="\ny\n" # Enter to reveal, y to confirm remembered
    )

    assert result.exit_code == 0
    assert "Spaced Repetition Review" in result.stdout
    assert "Reviewing 1 note(s)" in result.stdout
    assert "Marked as reviewed" in result.stdout

def test_study_synthesize(mock_knowledge_base):
    """Test study synthesize command."""
    # Input stream: 'n' (do not create synthesis note)

    result = runner.invoke(
        app,
        ["--root", str(mock_knowledge_base), "study", "synthesize"],
        input="n\n"
    )

    assert result.exit_code == 0
    assert "Forced Synthesis Challenge" in result.stdout
    assert "Concept A:" in result.stdout
    assert "Concept B:" in result.stdout

def test_study_synthesize_create_note(mock_knowledge_base):
    """Test study synthesize command creating a note."""
    # Input stream: 'y' (create note), 'My insight' (content)

    result = runner.invoke(
        app,
        ["--root", str(mock_knowledge_base), "study", "synthesize"],
        input="y\nMy brilliant insight\n"
    )

    assert result.exit_code == 0
    assert "Synthesis note created" in result.stdout

    # Verify file was created
    synthesis_dir = mock_knowledge_base / "10-19_KNOWLEDGE" / "11_public_garden" / "concepts"
    assert any(synthesis_dir.glob("synthesis-*.md"))
