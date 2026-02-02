from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_pkm_find_highlight(tmp_path):
    """Test pkm find command runs and highlights results."""
    # Mock KnowledgeDB where it is defined, so the local import in pkm.py picks up the mock
    with patch("devbase.services.knowledge_db.KnowledgeDB") as MockDB:
        mock_instance = MockDB.return_value

        # Configure search results
        mock_instance.search.return_value = [{
            "path": "path/to/python_guide.md",
            "title": "Python Guide",
            "type": "note",
            "word_count": 100,
            "content_preview": "Python is a great language."
        }]

        # Configure get_stats to avoid indexing trigger
        mock_instance.get_stats.return_value = {"total_notes": 10}

        # Invoke command
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "find", "Python"])

        if result.exit_code != 0:
            print(result.stdout)

        assert result.exit_code == 0
        assert "Python Guide" in result.stdout
