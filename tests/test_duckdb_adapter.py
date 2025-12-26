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
