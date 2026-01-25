import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from rich.text import Text
from typer.testing import CliRunner
from devbase.main import app

class TestPkmHighlight(unittest.TestCase):
    def test_find_highlighting_mock_table(self):
        """Test that pkm find results are rendered in a table with highlighted terms."""
        # Patch KnowledgeDB to return fake results
        # Patch Table to intercept add_row calls
        # Patch console to avoid actual printing
        with patch("devbase.services.knowledge_db.KnowledgeDB") as MockDB, \
             patch("devbase.commands.pkm.Table") as MockTable, \
             patch("devbase.commands.pkm.console"):

            mock_db_instance = MockDB.return_value
            mock_db_instance.get_stats.return_value = {"total_notes": 1}
            mock_db_instance.search.return_value = [
                {
                    "title": "Test Note",
                    "path": Path("/tmp/test.md"),
                    "type": "reference",
                    "word_count": 100,
                    "content_preview": "This is a python test note.",
                }
            ]

            mock_table_instance = MockTable.return_value

            runner = CliRunner()
            # We need to pass a valid root or mock whatever checks root,
            # but usually commands access root from ctx.obj which is populated by main.
            # Passing --root . works if we mock everything that uses it.
            # KnowledgeDB is mocked, so it won't actually use the root path.
            result = runner.invoke(app, ["--root", ".", "pkm", "find", "python"])

            if result.exit_code != 0:
                print(result.stdout)

            self.assertEqual(result.exit_code, 0)

            # Check add_row calls
            self.assertTrue(mock_table_instance.add_row.called)
            args, _ = mock_table_instance.add_row.call_args

            # args: title, type, words, path, preview
            self.assertEqual(args[0], "Test Note")
            self.assertEqual(args[1], "reference")
            self.assertEqual(args[2], "100")

            # args[4] should be the preview Text object
            preview_text = args[4]
            self.assertIsInstance(preview_text, Text)
            self.assertIn("python", preview_text.plain)

            # Check if it has styles. Text._spans contains (start, end, style)
            # We expect highlighting for "python"
            # "This is a python test note." -> python is at index 10
            # rich 13+ use spans
            found_highlight = False
            # Check if any span has our style
            # Note: style object or string depending on how it was passed.
            # We passed string "bold yellow reverse"
            for span in preview_text.spans:
                # span is a NamedTuple (start, end, style)
                if span.style == "bold yellow reverse":
                    found_highlight = True
                    break

            self.assertTrue(found_highlight, "Highlight style 'bold yellow reverse' not applied to preview text")
