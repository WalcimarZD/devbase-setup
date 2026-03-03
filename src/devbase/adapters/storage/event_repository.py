"""
Event Repository
================
Single abstraction layer for all DuckDB queries against the *events* table.

Every service that needs telemetry data depends on this class, never on
raw SQL strings scattered across the codebase.  Satisfies DIP: services
depend on this abstraction; the DuckDB adapter detail is hidden here.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from devbase.adapters.storage import duckdb_adapter

logger = logging.getLogger(__name__)

# Allowed FTS table names — prevents SQL injection via table parameter.
_FTS_TABLES = frozenset({"hot_fts", "cold_fts"})


class EventRepository:
    """Repository for telemetry events stored in DuckDB.

    All SQL against the *events* table is centralised here.  Services
    receive structured Python dicts; they never touch raw connections.
    """

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_recent_by_type(
        self,
        event_type: str,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Return events of *event_type* from the last *hours* hours.

        Args:
            event_type: Value of the ``event_type`` column to filter on.
            hours: Lookback window in hours.

        Returns:
            List of event dicts (keys: timestamp, message, project, metadata).
        """
        conn = duckdb_adapter.get_connection()
        query = """
            SELECT timestamp, message, project, metadata
            FROM events
            WHERE event_type = ?
              AND timestamp > now() - INTERVAL ? HOUR
            ORDER BY timestamp DESC
        """
        try:
            rows = conn.execute(query, [event_type, hours]).fetchall()
            return [
                {"timestamp": row[0], "message": row[1], "project": row[2], "metadata": row[3]}
                for row in rows
            ]
        except Exception as exc:
            logger.error("EventRepository.find_recent_by_type failed: %s", exc)
            return []

    def find_by_date(
        self,
        target_date: str,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return events for a specific calendar date.

        Args:
            target_date: Date string in ``YYYY-MM-DD`` format.
            event_type: Optional filter on event type.

        Returns:
            List of event dicts ordered by timestamp ascending.
        """
        conn = duckdb_adapter.get_connection()
        params: List[Any] = [target_date]
        query = """
            SELECT timestamp, message, project, metadata
            FROM events
            WHERE strftime(timestamp, '%Y-%m-%d') = ?
        """
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp ASC"

        try:
            rows = conn.execute(query, params).fetchall()
            return [
                {"timestamp": row[0], "message": row[1], "project": row[2], "metadata": row[3]}
                for row in rows
            ]
        except Exception as exc:
            logger.error("EventRepository.find_by_date failed: %s", exc)
            return []

    def count_recent(self, hours: int = 1) -> int:
        """Count all events in the last *hours* hours.

        Args:
            hours: Lookback window.

        Returns:
            Event count.
        """
        conn = duckdb_adapter.get_connection()
        try:
            result = conn.execute(
                "SELECT count(*) FROM events WHERE timestamp > now() - INTERVAL ? HOUR",
                [hours],
            ).fetchone()
            return result[0] if result else 0
        except Exception as exc:
            logger.debug("EventRepository.count_recent failed: %s", exc)
            return 0

    def find_last_n(self, n: int) -> List[Dict[str, Any]]:
        """Return the *n* most recent events regardless of type.

        Args:
            n: Number of events to return.

        Returns:
            List of event dicts (keys: timestamp, event_type, message, metadata).
        """
        conn = duckdb_adapter.get_connection()
        try:
            rows = conn.execute(
                """
                SELECT timestamp, event_type, message, metadata
                FROM events
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                [n],
            ).fetchall()
            return [
                {"timestamp": row[0], "event_type": row[1], "message": row[2], "metadata": row[3]}
                for row in rows
            ]
        except Exception as exc:
            logger.debug("EventRepository.find_last_n failed: %s", exc)
            return []

    def get_flow_summary(self, hours: int = 24) -> str:
        """Produce a human-readable hourly activity summary.

        Args:
            hours: Lookback window in hours.

        Returns:
            Multi-line string with command/commit counts per hour.
        """
        conn = duckdb_adapter.get_connection()
        query = """
            SELECT
                strftime(timestamp, '%Y-%m-%d %H:00') AS start_time,
                count(CASE WHEN event_type = 'command' THEN 1 END) AS commands,
                count(CASE WHEN event_type = 'commit'  THEN 1 END) AS commits
            FROM events
            WHERE timestamp >= (current_timestamp - INTERVAL ? HOUR)
            GROUP BY 1
            ORDER BY 1 DESC
        """
        try:
            results = conn.execute(query, [hours]).fetchall()
            if not results:
                return "No technical activity recorded in the last 24h."
            lines = [f"Technical activity summary ({hours}h):"]
            for row in results:
                lines.append(f"- {row[0]}: {row[1]} commands, {row[2]} commits")
            return "\n".join(lines)
        except Exception as exc:
            logger.debug("EventRepository.get_flow_summary failed: %s", exc)
            return "Activity statistics unavailable."

    def find_decisions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Find track-type events that mention architectural decisions.

        Filters by a bilingual (EN/PT) keyword set.

        Args:
            hours: Lookback window in hours.

        Returns:
            Filtered list of track events.
        """
        candidates = self.find_recent_by_type("track", hours=hours)
        keywords = {
            "architecture", "decision", "design", "pattern",
            "decisão", "arquitetura",
        }
        return [
            c for c in candidates
            if any(kw in c.get("message", "").lower() for kw in keywords)
        ]

    def count_today_by_type(
        self,
        event_type: str,
        user: Optional[str] = None,
    ) -> int:
        """Count events of *event_type* created today, optionally by *user*.

        Args:
            event_type: Value of the ``event_type`` column to filter on.
            user: Optional user identifier stored in the JSON metadata.

        Returns:
            Event count for today.
        """
        conn = duckdb_adapter.get_connection()
        query = """
            SELECT COUNT(*)
            FROM events
            WHERE event_type = ?
              AND timestamp::DATE = current_date()
        """
        params: List[Any] = [event_type]
        if user:
            query += " AND json_extract_string(metadata, '$.user') = ?"
            params.append(user)
        try:
            result = conn.execute(query, params).fetchone()
            return result[0] if result else 0
        except Exception as exc:
            logger.debug("EventRepository.count_today_by_type failed: %s", exc)
            return 0

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def log(
        self,
        event_type: str,
        message: str,
        project: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> None:
        """Write a new event to the store.

        Args:
            event_type: Event category (e.g. ``'track'``, ``'ai_generation'``).
            message: Human-readable description.
            project: Optional project name.
            metadata: Optional JSON-encoded metadata string.
        """
        duckdb_adapter.log_event(
            event_type=event_type,
            message=message,
            project=project,
            metadata=metadata,
        )
