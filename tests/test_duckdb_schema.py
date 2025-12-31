import duckdb
import pytest
from unittest.mock import MagicMock, call
from devbase.adapters.storage import duckdb_adapter

class TestDuckDBSchemaOptimization:
    def test_init_schema_warm_start(self):
        """Verify init_schema returns early if version matches."""
        mock_conn = MagicMock()
        # Mock result for SELECT version -> returns ('5.1',)
        mock_conn.execute.return_value.fetchone.return_value = (duckdb_adapter.SCHEMA_VERSION,)

        duckdb_adapter.init_schema(mock_conn)

        # Verify only the check was executed
        assert mock_conn.execute.call_count == 1
        mock_conn.execute.assert_called_with("SELECT version FROM schema_version")

    def test_init_schema_cold_start_exception(self):
        """Verify init_schema proceeds if table check raises CatalogException."""
        mock_conn = MagicMock()
        # Simulate table missing
        mock_conn.execute.side_effect = [
            duckdb.CatalogException("Table does not exist"),
            MagicMock(), # CREATE TABLE schema_version
            MagicMock(), # CREATE TABLE notes_index
            MagicMock(), # CREATE TABLE hot_fts
            MagicMock(), # CREATE TABLE cold_fts
            MagicMock(), # INSTALL fts; LOAD fts
            MagicMock(), # PRAGMA create_fts_index hot
            MagicMock(), # PRAGMA create_fts_index cold
            MagicMock(), # CREATE TABLE hot_embeddings
            MagicMock(), # CREATE TABLE cold_embeddings
            MagicMock(), # CREATE SEQUENCE ai_task_queue_id_seq
            MagicMock(), # CREATE TABLE ai_task_queue
            MagicMock(), # CREATE SEQUENCE events_id_seq
            MagicMock(), # CREATE TABLE events
            MagicMock(), # SELECT COUNT(*)
            MagicMock(), # INSERT (maybe)
        ]

        # Mock fetchone for the count check (last call) to return 0 so it inserts
        mock_conn.execute.return_value.fetchone.return_value = (0,)

        duckdb_adapter.init_schema(mock_conn)

        # Should execute many statements (checking > 1 is enough)
        assert mock_conn.execute.call_count > 1
        # Verify CREATE TABLE was called
        create_calls = [c for c in mock_conn.execute.call_args_list if "CREATE TABLE" in str(c)]
        assert len(create_calls) > 0

    def test_init_schema_version_mismatch(self):
        """Verify init_schema proceeds if version does not match."""
        mock_conn = MagicMock()
        # Mock result for SELECT version -> returns '5.0' (mismatch)
        mock_conn.execute.return_value.fetchone.return_value = ('5.0',)

        duckdb_adapter.init_schema(mock_conn)

        # Should execute many statements
        assert mock_conn.execute.call_count > 1

    def test_init_schema_no_result(self):
        """Verify init_schema proceeds if version query returns None (empty table)."""
        mock_conn = MagicMock()
        # Mock result for SELECT version -> returns None
        mock_conn.execute.return_value.fetchone.return_value = None

        duckdb_adapter.init_schema(mock_conn)

        # Should execute many statements
        assert mock_conn.execute.call_count > 1

    def test_integration_real_duckdb(self, tmp_path):
        """Integration test with real DuckDB file."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))

        # 1. Cold start
        duckdb_adapter.init_schema(conn)

        # Verify version is set
        ver = conn.execute("SELECT version FROM schema_version").fetchone()[0]
        assert ver == duckdb_adapter.SCHEMA_VERSION

        # 2. Warm start (check logs or debug hook? Hard to check internally without mocking, but we can trust the unit test for logic)
        # However, we can verify it doesn't crash
        duckdb_adapter.init_schema(conn)

        conn.close()
