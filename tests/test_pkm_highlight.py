
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from rich.console import Console
from devbase.main import app
from devbase.commands.pkm import app as pkm_app

runner = CliRunner()

@pytest.fixture
def mock_db():
    with patch("devbase.services.knowledge_db.KnowledgeDB") as MockDB:
        db_instance = MockDB.return_value
        yield db_instance

def test_pkm_find_highlighting(mock_db, tmp_path):
    # Setup mock results
    mock_db.get_stats.return_value = {"total_notes": 10}
    mock_db.search.return_value = [
        {
            "title": "Python Basics",
            "path": str(tmp_path / "10-19_KNOWLEDGE/python.md"),
            "type": "guide",
            "word_count": 100,
            "content_preview": "This is a guide about Python programming."
        }
    ]

    # Run command with wider terminal to avoid truncation
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "pkm", "find", "Python"],
        env={"COLUMNS": "200"}
    )

    assert result.exit_code == 0

    # Check table structure
    assert "Title" in result.stdout
    assert "Type" in result.stdout
    assert "Preview" in result.stdout

    # Check content (might be slightly formatted/truncated if not wide enough, but 200 should be enough)
    assert "Python Basics" in result.stdout
    assert "guide" in result.stdout
    assert "This is a guide about Python programming." in result.stdout
