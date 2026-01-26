"""
Tests for PKM highlighting features.
"""
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from rich.text import Text
from devbase.main import app

runner = CliRunner()

def test_pkm_find_highlighting(tmp_path):
    """Test that pkm find highlights the search query in the content preview."""

    # Mock results from KnowledgeDB
    mock_results = [{
        "path": "test.md",
        "title": "Test Title",
        "type": "note",
        "word_count": 100,
        "content_preview": "This content contains the query term inside it."
    }]

    # We need to patch KnowledgeDB to return our mock results
    # and patch the console in pkm.py to inspect the output
    with patch("devbase.services.knowledge_db.KnowledgeDB") as MockDB, \
         patch("devbase.commands.pkm.console") as mock_console:

        # Setup DB mock
        instance = MockDB.return_value
        instance.get_stats.return_value = {"total_notes": 10}
        instance.search.return_value = mock_results

        # Run command: pkm find query
        # We use a query string "query" which appears in "content contains the query term"
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "find", "query"])

        assert result.exit_code == 0

        # Verify console calls
        # We look for a call to console.print that contains a Text object
        found_highlight = False

        for call in mock_console.print.call_args_list:
            args = call[0]
            if args and isinstance(args[0], Text):
                text_obj = args[0]
                plain = text_obj.plain

                # We are looking for the preview text
                if "contains the query term" in plain:
                    # Check spans for highlighting
                    for span in text_obj.spans:
                        span_text = plain[span.start:span.end]
                        # Check if the span covers the query term
                        if "query" in span_text.lower():
                             # Check if style is correct (bold black on yellow)
                             # rich.style.Style or str
                             style_str = str(span.style)
                             if "yellow" in style_str:
                                 found_highlight = True
                                 break

        assert found_highlight, "Search query 'query' was not highlighted in the output preview."
