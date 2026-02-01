from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from devbase.main import app
from rich.text import Text

runner = CliRunner()

def test_pkm_find_highlighting(tmp_path):
    # Mock KnowledgeDB
    with patch("devbase.services.knowledge_db.KnowledgeDB") as MockDB, \
         patch("devbase.commands.pkm.console") as mock_console:

        mock_db = MagicMock()
        MockDB.return_value = mock_db

        # Setup mock return values
        mock_db.get_stats.return_value = {"total_notes": 10}
        mock_db.search.return_value = [{
            "path": "test.md",
            "title": "Test Note",
            "type": "note",
            "word_count": 100,
            "content_preview": "This is a test note about python context."
        }]

        # Run command
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "find", "python"])

        assert result.exit_code == 0

        found_highlighted_text = False
        for call in mock_console.print.call_args_list:
            args, _ = call
            if args:
                arg = args[0]
                if isinstance(arg, Text):
                    plain_text = arg.plain
                    if "python" in plain_text:
                        for span in arg.spans:
                            start, end, style = span
                            span_text = plain_text[start:end]
                            if span_text.lower() == "python":
                                # Verify we are using a highlighting style
                                # We can check strictly or just that a style exists
                                if style:
                                    found_highlighted_text = True
                                    break

        assert found_highlighted_text, "Search term 'python' was not highlighted in output"
