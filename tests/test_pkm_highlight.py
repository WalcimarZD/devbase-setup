from unittest.mock import patch
from typer.testing import CliRunner
from devbase.main import app
from devbase.adapters.storage.duckdb_adapter import init_connection, init_schema

runner = CliRunner()

def test_pkm_find_returns_results(tmp_path):
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Create a note
    note_path = tmp_path / "10-19_KNOWLEDGE" / "11_public_garden" / "test_note.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("---\ntitle: Test Note\n---\n\nThis is a search query test.", encoding="utf-8")

    # Setup temporary DB
    db_path = tmp_path / "test.duckdb"
    conn = init_connection(db_path)
    init_schema(conn)

    with patch("devbase.services.knowledge_db.duckdb_adapter.get_connection", return_value=conn):
        # Run find (indexes implicitly)
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "find", "search"])

    conn.close()

    if result.exit_code != 0:
        print(result.stdout)

    assert result.exit_code == 0
    assert "Test Note" in result.stdout
    assert "search query test" in result.stdout
