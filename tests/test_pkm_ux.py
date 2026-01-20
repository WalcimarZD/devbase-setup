
import pytest
from typer.testing import CliRunner
from unittest.mock import patch
from pathlib import Path
from devbase.main import app
import devbase.adapters.storage.duckdb_adapter as duckdb_adapter

runner = CliRunner()

@pytest.fixture
def mock_db(tmp_path):
    """Mock DuckDB to use a temporary file."""
    db_path = tmp_path / "test_ux.db"

    # Reset singleton
    duckdb_adapter._connection = None
    duckdb_adapter._db_path = None

    with patch("devbase.adapters.storage.duckdb_adapter.get_db_path", return_value=db_path):
        yield db_path

    # Cleanup
    duckdb_adapter.close_connection()
    duckdb_adapter._connection = None

def test_pkm_find_highlighting(tmp_path, mock_db):
    """Test that pkm find highlights search terms."""
    # Setup workspace
    root = tmp_path
    (root / "10-19_KNOWLEDGE" / "11_public_garden").mkdir(parents=True)

    # Create a note
    note_content = """---
title: Test Note
type: note
tags: [test]
---

This is a sample note about Python programming and DuckDB.
"""
    (root / "10-19_KNOWLEDGE" / "11_public_garden" / "test.md").write_text(note_content)

    # Run find command
    result = runner.invoke(app, ["--root", str(root), "pkm", "find", "Python", "--reindex"], env={"FORCE_COLOR": "1"})

    assert result.exit_code == 0
    assert "Found 1 note(s)" in result.stdout
    assert "Test Note" in result.stdout
    assert "Python programming" in result.stdout
