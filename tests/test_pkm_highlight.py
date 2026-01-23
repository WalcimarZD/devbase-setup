
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from rich.text import Text

from devbase.commands.pkm import app

runner = CliRunner()

@pytest.fixture
def mock_knowledge_db():
    with patch("devbase.services.knowledge_db.KnowledgeDB") as MockDB:
        db_instance = MockDB.return_value
        db_instance.get_stats.return_value = {"total_notes": 10, "hot_notes": 10, "cold_notes": 0}
        # Simulate search result
        db_instance.search.return_value = [{
            "path": "test.md",
            "title": "Test Note",
            "type": "note",
            "word_count": 100,
            "content_preview": "The quick brown fox jumps over the lazy dog."
        }]
        yield MockDB

@patch("devbase.commands.pkm.console")
def test_pkm_find_highlights_query(mock_console, mock_knowledge_db):
    """Test that search query is highlighted in results."""

    # Run the command with a dummy root
    result = runner.invoke(app, ["find", "fox"], obj={"root": "."})

    assert result.exit_code == 0

    # Verify console.print calls
    # We are looking for the call that prints the preview
    # Current implementation calls console.print(f"  [dim]{preview}...[/dim]")
    # We want to change it to use a Text object with highlighting

    # Iterate over all calls to print
    found_highlighted_text = False
    for call in mock_console.print.call_args_list:
        args, _ = call
        if args:
            arg = args[0]
            # Verify if we are printing a Text object
            if isinstance(arg, Text):
                # Check if it contains the text and has styles applied
                # "fox" should have a specific style (e.g. black on yellow)
                # Note: Rich styles are stored in spans
                if "fox" in arg.plain:
                    # Check spans for highlighting
                    # Just checking if any span covers the word "fox" with a style
                    for span in arg.spans:
                        if span.style == "black on yellow":
                            found_highlighted_text = True
                            break

    assert found_highlighted_text, "Search query 'fox' should be highlighted in output"
