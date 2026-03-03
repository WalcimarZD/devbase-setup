"""
Tests for EventRepository
==========================
Uses an in-memory DuckDB connection so no files are written to disk and
tests are fully isolated from each other.
"""
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def in_memory_conn():
    """Return a fresh in-memory DuckDB connection with the events table."""
    import duckdb

    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id           VARCHAR DEFAULT gen_random_uuid(),
            timestamp    TIMESTAMPTZ NOT NULL DEFAULT now(),
            event_type   VARCHAR NOT NULL,
            message      VARCHAR,
            project      VARCHAR,
            metadata     VARCHAR
        )
    """)
    return conn


@pytest.fixture()
def repo(in_memory_conn):
    """Return an EventRepository whose calls hit the in-memory connection."""
    from devbase.adapters.storage.event_repository import EventRepository

    r = EventRepository()
    # Patch the module-level get_connection to return our in-memory conn
    with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
        # Also patch log_event to INSERT directly into our in-memory conn
        def _log_event(event_type, message, project=None, metadata=None):
            in_memory_conn.execute(
                "INSERT INTO events (event_type, message, project, metadata) VALUES (?, ?, ?, ?)",
                [event_type, message, project, metadata],
            )

        with patch("devbase.adapters.storage.duckdb_adapter.log_event", side_effect=_log_event):
            yield r


# ---------------------------------------------------------------------------
# Tests: log()
# ---------------------------------------------------------------------------

class TestLog:
    def test_log_inserts_event(self, repo, in_memory_conn):
        """log() writes a row to the events table."""
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            with patch("devbase.adapters.storage.duckdb_adapter.log_event") as mock_log:
                repo.log(event_type="track", message="unit test", project="p1")
                mock_log.assert_called_once_with(
                    event_type="track",
                    message="unit test",
                    project="p1",
                    metadata=None,
                )

    def test_log_with_metadata(self, repo, in_memory_conn):
        """log() forwards JSON metadata string to storage layer."""
        payload = json.dumps({"key": "value"})
        with patch("devbase.adapters.storage.duckdb_adapter.log_event") as mock_log:
            repo.log(event_type="ai_generation", message="gen", metadata=payload)
            mock_log.assert_called_once_with(
                event_type="ai_generation",
                message="gen",
                project=None,
                metadata=payload,
            )


# ---------------------------------------------------------------------------
# Tests: find_recent_by_type()
# ---------------------------------------------------------------------------

class TestFindRecentByType:
    def test_returns_matching_events(self, in_memory_conn):
        """find_recent_by_type() returns rows with the requested event_type."""
        from devbase.adapters.storage.event_repository import EventRepository

        in_memory_conn.execute(
            "INSERT INTO events (event_type, message, project, metadata) VALUES ('track', 'msg1', 'proj', NULL)"
        )
        in_memory_conn.execute(
            "INSERT INTO events (event_type, message, project, metadata) VALUES ('cmd', 'msg2', 'proj', NULL)"
        )

        repo = EventRepository()
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            results = repo.find_recent_by_type("track", hours=48)

        assert len(results) == 1
        assert results[0]["message"] == "msg1"

    def test_returns_empty_list_when_no_match(self, in_memory_conn):
        """find_recent_by_type() returns [] when no events match."""
        from devbase.adapters.storage.event_repository import EventRepository

        repo = EventRepository()
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            results = repo.find_recent_by_type("nonexistent", hours=48)

        assert results == []


# ---------------------------------------------------------------------------
# Tests: find_by_date()
# ---------------------------------------------------------------------------

class TestFindByDate:
    def test_returns_events_for_date(self, in_memory_conn):
        """find_by_date() returns only events on the specified date."""
        from devbase.adapters.storage.event_repository import EventRepository

        today = datetime.now().strftime("%Y-%m-%d")
        in_memory_conn.execute(
            "INSERT INTO events (timestamp, event_type, message) VALUES (now(), 'track', 'today')"
        )

        repo = EventRepository()
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            results = repo.find_by_date(today)

        assert any(r["message"] == "today" for r in results)

    def test_filters_by_event_type(self, in_memory_conn):
        """find_by_date() respects optional event_type filter."""
        from devbase.adapters.storage.event_repository import EventRepository

        today = datetime.now().strftime("%Y-%m-%d")
        in_memory_conn.execute(
            "INSERT INTO events (timestamp, event_type, message) VALUES (now(), 'track', 'track-event')"
        )
        in_memory_conn.execute(
            "INSERT INTO events (timestamp, event_type, message) VALUES (now(), 'cmd', 'cmd-event')"
        )

        repo = EventRepository()
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            results = repo.find_by_date(today, event_type="track")

        assert all(r["message"] == "track-event" for r in results)


# ---------------------------------------------------------------------------
# Tests: count_recent()
# ---------------------------------------------------------------------------

class TestCountRecent:
    def test_returns_correct_count(self, in_memory_conn):
        """count_recent() counts all events in the lookback window."""
        from devbase.adapters.storage.event_repository import EventRepository

        for i in range(3):
            in_memory_conn.execute(
                f"INSERT INTO events (event_type, message) VALUES ('track', 'evt{i}')"
            )

        repo = EventRepository()
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            count = repo.count_recent(hours=1)

        assert count == 3

    def test_returns_zero_when_empty(self, in_memory_conn):
        """count_recent() returns 0 when the table is empty."""
        from devbase.adapters.storage.event_repository import EventRepository

        repo = EventRepository()
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            assert repo.count_recent(hours=1) == 0


# ---------------------------------------------------------------------------
# Tests: count_today_by_type()
# ---------------------------------------------------------------------------

class TestCountTodayByType:
    def test_counts_by_event_type(self, in_memory_conn):
        """count_today_by_type() counts only matching event_type rows from today."""
        from devbase.adapters.storage.event_repository import EventRepository

        in_memory_conn.execute(
            "INSERT INTO events (event_type, message) VALUES ('ai_generation', 'gen1')"
        )
        in_memory_conn.execute(
            "INSERT INTO events (event_type, message) VALUES ('ai_generation', 'gen2')"
        )
        in_memory_conn.execute(
            "INSERT INTO events (event_type, message) VALUES ('track', 'other')"
        )

        repo = EventRepository()
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            count = repo.count_today_by_type("ai_generation")

        assert count == 2

    def test_returns_zero_for_unknown_type(self, in_memory_conn):
        """count_today_by_type() returns 0 for a type with no entries."""
        from devbase.adapters.storage.event_repository import EventRepository

        repo = EventRepository()
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            assert repo.count_today_by_type("phantom_event") == 0


# ---------------------------------------------------------------------------
# Tests: find_last_n()
# ---------------------------------------------------------------------------

class TestFindLastN:
    def test_returns_n_most_recent(self, in_memory_conn):
        """find_last_n(2) returns exactly 2 rows."""
        from devbase.adapters.storage.event_repository import EventRepository

        for i in range(5):
            in_memory_conn.execute(
                f"INSERT INTO events (event_type, message) VALUES ('track', 'evt{i}')"
            )

        repo = EventRepository()
        with patch("devbase.adapters.storage.duckdb_adapter.get_connection", return_value=in_memory_conn):
            results = repo.find_last_n(2)

        assert len(results) == 2
