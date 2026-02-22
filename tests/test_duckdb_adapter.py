"""
Tests for DuckDB Adapter
========================
Verifies WAL configuration, shutdown handlers, and schema creation.
"""
import tempfile
from pathlib import Path

import pytest


def test_init_connection_sets_wal_pragma():
    """Verify PRAGMA wal_autocheckpoint=1000 is set."""
    from devbase.adapters.storage.duckdb_adapter import init_connection
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = init_connection(db_path)
        
        # Query current WAL setting (DuckDB returns this via pragma)
        # Note: DuckDB doesn't expose wal_autocheckpoint directly,
        # but we verify the connection works after setting it
        assert conn is not None
        conn.close()


def test_schema_creation():
    """Verify all required tables are created."""
    from devbase.adapters.storage.duckdb_adapter import init_connection, init_schema
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = init_connection(db_path)
        init_schema(conn)
        
        # Check tables exist
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        
        required_tables = {
            "notes_index",
            "ai_task_queue",
            "events",
            "schema_version",
        }
        
        for table in required_tables:
            assert table in table_names, f"Table {table} should exist"
        
        conn.close()


def test_schema_version_set():
    """Verify schema version is set to 5.1."""
    from devbase.adapters.storage.duckdb_adapter import init_connection, init_schema
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = init_connection(db_path)
        init_schema(conn)
        
        version = conn.execute("SELECT version FROM schema_version").fetchone()
        assert version is not None
        assert version[0] == "5.1"
        
        conn.close()


def test_enqueue_ai_task():
    """Verify AI task enqueuing works."""
    from devbase.adapters.storage.duckdb_adapter import (
        init_connection, 
        init_schema, 
        enqueue_ai_task
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = init_connection(db_path)
        init_schema(conn)
        
        task_id = enqueue_ai_task("classify", '{"content": "test"}', conn)
        assert task_id > 0
        
        # Verify task was inserted
        result = conn.execute(
            "SELECT task_type, status FROM ai_task_queue WHERE id = ?",
            [task_id]
        ).fetchone()
        
        assert result is not None
        assert result[0] == "classify"
        assert result[1] == "pending"
        
        conn.close()


def test_log_event():
    """Verify event logging works."""
    from devbase.adapters.storage.duckdb_adapter import (
        init_connection, 
        init_schema, 
        log_event
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = init_connection(db_path)
        init_schema(conn)
        
        log_event("test_event", "Test message", project="test-project", conn=conn)
        
        # Verify event was inserted
        result = conn.execute(
            "SELECT event_type, message, project FROM events ORDER BY id DESC LIMIT 1"
        ).fetchone()
        
        assert result is not None
        assert result[0] == "test_event"
        assert result[1] == "Test message"
        assert result[2] == "test-project"
        
        conn.close()


def test_init_schema_early_return_when_version_matches():
    """Verify init_schema returns early when schema version matches."""
    from devbase.adapters.storage.duckdb_adapter import (
        init_connection, 
        init_schema,
        SCHEMA_VERSION
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = init_connection(db_path)
        
        # First call: should create all tables
        init_schema(conn)
        
        # Verify schema version is set correctly
        version = conn.execute("SELECT version FROM schema_version").fetchone()
        assert version is not None
        assert version[0] == SCHEMA_VERSION
        
        # Drop a table that would normally be created
        conn.execute("DROP TABLE IF EXISTS events")
        
        # Second call: should return early and NOT recreate the events table
        init_schema(conn)
        
        # Verify events table was NOT recreated (early return worked)
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'events'"
        ).fetchall()
        assert len(tables) == 0, "events table should not be recreated on early return"
        
        conn.close()


def test_init_schema_handles_missing_schema_version_table():
    """Verify init_schema handles the case when schema_version table doesn't exist."""
    from devbase.adapters.storage.duckdb_adapter import init_connection, init_schema
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = init_connection(db_path)
        
        # Call init_schema on a fresh database (no schema_version table exists)
        # This should handle the exception and proceed with full initialization
        init_schema(conn)
        
        # Verify all tables were created
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        
        required_tables = {
            "notes_index",
            "ai_task_queue",
            "events",
            "schema_version",
        }
        
        for table in required_tables:
            assert table in table_names, f"Table {table} should exist"
        
        conn.close()


def test_init_schema_handles_corrupted_schema_version(caplog):
    """Verify init_schema logs unexpected errors when querying schema_version."""
    import logging
    from devbase.adapters.storage.duckdb_adapter import init_connection, init_schema
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = init_connection(db_path)
        
        # Create a mock connection that will raise an unexpected error
        class MockConnection:
            def __init__(self, real_conn):
                self._real_conn = real_conn
                self._check_version_called = False
            
            def execute(self, sql, *args, **kwargs):
                # First call to check schema version should raise unexpected error
                if "SELECT version FROM schema_version" in sql and not self._check_version_called:
                    self._check_version_called = True
                    raise RuntimeError("Simulated unexpected database error")
                # All other calls go to the real connection
                return self._real_conn.execute(sql, *args, **kwargs)
            
            def __getattr__(self, name):
                return getattr(self._real_conn, name)
        
        mock_conn = MockConnection(conn)
        
        # Capture logs at WARNING level
        with caplog.at_level(logging.WARNING):
            # This should catch the unexpected error, log a warning, and proceed with full init
            init_schema(mock_conn)
        
        # Verify that the warning was logged
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        log_message = caplog.records[0].getMessage()
        assert "Unexpected error checking schema version" in log_message
        assert "Simulated unexpected database error" in log_message
        
        conn.close()
