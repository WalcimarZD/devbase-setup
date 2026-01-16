from unittest.mock import MagicMock, patch
from rich.text import Text
from typer.testing import CliRunner
from devbase.commands.pkm import app

runner = CliRunner()

def test_pkm_find_highlighting():
    # Mock result from DB
    mock_results = [
        {
            "path": "path/to/note.md",
            "title": "Python Basics",
            "type": "note",
            "word_count": 100,
            "content_preview": "Python is a great language. I love python."
        }
    ]

    # Patch the class where it is DEFINED, so that when pkm imports it, it gets the mock.
    with patch("devbase.services.knowledge_db.KnowledgeDB") as MockDB:
        mock_instance = MockDB.return_value
        mock_instance.get_stats.return_value = {"total_notes": 10}
        mock_instance.search.return_value = mock_results

        # Mock console
        with patch("devbase.commands.pkm.console") as mock_console:
            # Run command
            # We need to pass a mock root in context
            result = runner.invoke(app, ["find", "python"], obj={"root": MagicMock()})

            assert result.exit_code == 0

            # Check if console.print was called with Text object
            text_calls = [
                args[0] for args, _ in mock_console.print.call_args_list
                if args and isinstance(args[0], Text)
            ]

            assert len(text_calls) > 0
            preview_text = text_calls[0]

            # Verify content
            assert "Python is a great language" in preview_text.plain

            # Check style of spans
            highlight_spans = [span for span in preview_text.spans if span.style == "black on yellow"]
            assert len(highlight_spans) >= 2
