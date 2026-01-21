
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from typer.testing import CliRunner
from devbase.commands.pkm import app
from rich.text import Text
import traceback

runner = CliRunner()

class TestPKMHighlight(unittest.TestCase):
    @patch('devbase.services.knowledge_db.KnowledgeDB')
    @patch('devbase.commands.pkm.console')
    def test_find_highlights_query(self, mock_console, mock_db_cls):
        # Setup mock DB
        mock_db = mock_db_cls.return_value
        mock_db.get_stats.return_value = {"total_notes": 10}
        mock_db.search.return_value = [
            {
                "title": "Python Tips",
                "path": "notes/python.md",
                "type": "note",
                "word_count": 100,
                "content_preview": "This is a note about Python programming and pythonic ways."
            }
        ]

        # Run command
        # remove --root argument as we are invoking sub-app directly
        # ensure root is a Path object in context
        result = runner.invoke(app, ["find", "Python"], obj={"root": Path(".")})

        if result.exit_code != 0:
            print(f"Command failed with exit code: {result.exit_code}")
            print(f"Output: {result.stdout}")
            if result.exc_info:
                print("Exception:")
                traceback.print_exception(*result.exc_info)

        # Verify db.search called correctly
        mock_db.search.assert_called_once()

        # Check console.print calls
        preview_printed = False
        highlighted = False

        for call in mock_console.print.call_args_list:
            args, _ = call
            if args:
                arg = args[0]
                # Check if it is the preview string
                if isinstance(arg, str) and "This is a note about Python" in arg:
                    print(f"Found plain string preview: {arg}")
                    preview_printed = True
                elif isinstance(arg, Text) and "This is a note about Python" in arg.plain:
                    print(f"Found Text object preview: {arg.plain}")
                    preview_printed = True
                    # Check for highlighting
                    if arg.spans:
                        print(f"Spans found: {arg.spans}")
                        highlighted = True
                    else:
                        print("No spans found in Text object")

        if not preview_printed:
            print("Preview not found in console output")

        self.assertTrue(preview_printed, "Preview should be printed")

        # Should fail initially (highlighted=False)
        self.assertTrue(highlighted, "Preview should be highlighted with Text object")

if __name__ == '__main__':
    unittest.main()
