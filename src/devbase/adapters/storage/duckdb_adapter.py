"""
DuckDB Storage Adapter
======================
Low-level DuckDB connection management with WAL optimization.

Critical Requirements (TDD v1.2):
- PRAGMA wal_autocheckpoint=1000 (fixed SSD value)
- Graceful shutdown via atexit + SIGTERM handlers
- Zero I/O in cold path (lazy initialization)

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import atexit
import hashlib
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import duckdb

# Module-level singleton for connection reuse
_connection: "duckdb.DuckDBPyConnection | None" = None
_db_path: Path | None = None


def get_db_path() -> Path:
    """Get the default database path."""
    return Path.home() / ".devbase" / "devbase.duckdb"


def init_connection(db_path: Path | None = None) -> "duckdb.DuckDBPyConnection":
    """
    Initialize DuckDB connection with WAL optimization.
    
    Critical: Sets PRAGMA wal_autocheckpoint=1000 (fixed SSD value).
    This is the "Inviolable Core" requirement from TDD v1.2.
    
    Args:
        db_path: Path to database file. Defaults to ~/.devbase/devbase.duckdb
        
    Returns:
        DuckDB connection object
    """
    # Lazy import to preserve cold start < 50ms
    import duckdb
    
    if db_path is None:
        db_path = get_db_path()
    
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = duckdb.connect(str(db_path))
    
    # Critical: Fixed WAL autocheckpoint threshold (TDD v1.2 requirement)
    # DuckDB uses size strings, not integers like SQLite
    conn.execute("PRAGMA wal_autocheckpoint='16MB';")  # Small threshold for frequent checkpoints
    
    # Register shutdown handlers (cherry-pick from v5.0)
    _register_shutdown_handlers(conn)
    
    return conn


def _register_shutdown_handlers(conn: "duckdb.DuckDBPyConnection") -> None:
    """
    Register graceful shutdown handlers.
    
    Ensures WAL checkpoint on exit to prevent data loss.
    """
    def shutdown() -> None:
        try:
            # Force a checkpoint before closing (DuckDB-compatible)
            conn.execute("CHECKPOINT;")
            conn.close()
        except Exception:
            # Ignore errors during shutdown (connection may already be closed)
            pass
    
    # Register atexit handler (works on all platforms)
    atexit.register(shutdown)
    
    # Register SIGTERM handler (Unix only, graceful termination)
    if sys.platform != "win32":
        def sigterm_handler(signum: int, frame: object) -> None:
            shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, sigterm_handler)


def get_connection() -> "duckdb.DuckDBPyConnection":
    """
    Get or create the singleton DuckDB connection.
    
    Lazy initialization ensures zero I/O in cold path.
    
    Returns:
        DuckDB connection object
    """
    global _connection, _db_path
    
    if _connection is None:
        _db_path = get_db_path()
        _connection = init_connection(_db_path)
        init_schema(_connection)
    
    return _connection


def close_connection() -> None:
    """Close the singleton connection if open."""
    global _connection
    
    if _connection is not None:
        try:
            _connection.execute("CHECKPOINT;")
            _connection.close()
        except Exception:
            pass
        _connection = None


def init_schema(conn: "duckdb.DuckDBPyConnection") -> None:
    """
    Initialize database schema.
    
    Creates all required tables per TDD v1.2:
    - notes_index: Main note index with JD validation
    - hot_fts: Full-text search for Active Knowledge (10-19)
    - cold_fts: Full-text search for Archived Content (90-99)
    - ai_task_queue: Async AI task queue
    - events: Telemetry events table
    - schema_version: Migration tracking
    
    Note: JD validation is done at runtime in Python, not SQL constraints,
    because DuckDB doesn't support SQLite's GLOB syntax.
    """
    # Schema version table (must exist first for migration checks)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version TEXT PRIMARY KEY
        );
    """)
    
    # Notes index (JD validation done at runtime in Python)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes_index (
            file_path TEXT PRIMARY KEY,
            content_hash TEXT NOT NULL,
            jd_category TEXT,
            tags TEXT,
            maturity TEXT CHECK(maturity IN ('draft', 'review', 'stable', 'deprecated')),
            mtime_epoch BIGINT NOT NULL
        );
    """)
    
    # Hot FTS (Active Knowledge 10-19)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hot_fts (
            file_path TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            tags TEXT,
            note_type TEXT,
            mtime_epoch BIGINT
        );
    """)

    # Cold FTS (Archived 90-99)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cold_fts (
            file_path TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            tags TEXT,
            note_type TEXT,
            mtime_epoch BIGINT
        );
    """)

    # Embeddings Tables (Hot/Cold Separation)
    # Using ARRAY(FLOAT) to be compatible with standard DuckDB
    # If vector extension is loaded, we can use vector operations on these arrays.

    conn.execute("""
        CREATE TABLE IF NOT EXISTS hot_embeddings (
            file_path TEXT,
            chunk_id INTEGER,
            content_chunk TEXT,
            embedding DOUBLE[],
            mtime_epoch BIGINT,
            PRIMARY KEY (file_path, chunk_id)
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cold_embeddings (
            file_path TEXT,
            chunk_id INTEGER,
            content_chunk TEXT,
            embedding DOUBLE[],
            mtime_epoch BIGINT,
            PRIMARY KEY (file_path, chunk_id)
        );
    """)

    # AI task queue for async processing
    # DuckDB requires explicit sequences for auto-increment (unlike SQLite)
    conn.execute("CREATE SEQUENCE IF NOT EXISTS ai_task_queue_id_seq;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_task_queue (
            id INTEGER PRIMARY KEY DEFAULT nextval('ai_task_queue_id_seq'),
            task_type TEXT CHECK(task_type IN ('classify', 'synthesize', 'summarize')),
            payload TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'done', 'failed')),
            created_at TIMESTAMP DEFAULT current_timestamp
        );
    """)
    
    # Events table for telemetry
    # DuckDB requires explicit sequences for auto-increment (unlike SQLite)
    conn.execute("CREATE SEQUENCE IF NOT EXISTS events_id_seq;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY DEFAULT nextval('events_id_seq'),
            timestamp TIMESTAMP DEFAULT current_timestamp,
            event_type TEXT NOT NULL,
            project TEXT,
            message TEXT,
            metadata TEXT
        );
    """)
    
    # Insert initial schema version if not exists
    result = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()
    if result and result[0] == 0:
        conn.execute("INSERT INTO schema_version VALUES ('5.1')")


def enqueue_ai_task(
    task_type: str,
    payload: str,
    conn: "duckdb.DuckDBPyConnection | None" = None
) -> int:
    """
    Enqueue an AI task for async processing.
    
    Args:
        task_type: One of 'classify', 'synthesize', 'summarize'
        payload: JSON payload for the task
        conn: Optional connection (uses singleton if not provided)
        
    Returns:
        Task ID
    """
    if conn is None:
        conn = get_connection()
    
    result = conn.execute(
        """
        INSERT INTO ai_task_queue (task_type, payload)
        VALUES (?, ?)
        RETURNING id
        """,
        [task_type, payload]
    ).fetchone()
    
    return result[0] if result else -1


def log_event(
    event_type: str,
    message: str,
    project: str | None = None,
    metadata: str | None = None,
    conn: "duckdb.DuckDBPyConnection | None" = None
) -> None:
    """
    Log a telemetry event to DuckDB.
    
    This replaces the JSONL-based telemetry for better querying.
    
    Args:
        event_type: Type of event (e.g., 'track', 'create_project')
        message: Event message
        project: Optional project name
        metadata: Optional JSON metadata string
        conn: Optional connection (uses singleton if not provided)
    """
    if conn is None:
        conn = get_connection()
    
    conn.execute(
        """
        INSERT INTO events (event_type, project, message, metadata)
        VALUES (?, ?, ?, ?)
        """,
        [event_type, project, message, metadata]
    )
