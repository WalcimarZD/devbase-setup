"""
Knowledge Database Service
==========================
Handles indexing and searching of knowledge base notes.
Indexes content into DuckDB 'hot_fts' (10-19) and 'cold_fts' (90-99).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import frontmatter

from devbase.adapters.storage import duckdb_adapter
from devbase.services.indexing_helpers import (
    get_existing_mtimes,
    iter_files,
    should_skip_file,
    upsert_fts_batch,
)

logger = logging.getLogger(__name__)

class KnowledgeDB:
    def __init__(self, root: Path):
        self.root = root
        self.conn = duckdb_adapter.get_connection()

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            hot_count = self.conn.execute("SELECT COUNT(*) FROM hot_fts").fetchone()[0]
            cold_count = self.conn.execute("SELECT COUNT(*) FROM cold_fts").fetchone()[0]
            return {
                "total_notes": hot_count + cold_count,
                "hot_notes": hot_count,
                "cold_notes": cold_count
            }
        except Exception as exc:
            logger.warning("Failed to fetch knowledge DB stats: %s", exc)
            return {"total_notes": 0, "hot_notes": 0, "cold_notes": 0}

    def index_workspace(self) -> Dict[str, int]:
        """
        Scan and index the workspace.

        Scans:
        - 10-19_KNOWLEDGE -> hot_fts
        - 90-99_ARCHIVE_COLD -> cold_fts

        Returns:
            Dict with 'indexed', 'skipped', and 'errors' count.
        """
        stats = {"indexed": 0, "skipped": 0, "errors": 0}

        # 1. Index Active Knowledge (Hot)
        hot_path = self.root / "10-19_KNOWLEDGE"
        if hot_path.exists():
            existing_mtimes = get_existing_mtimes(self.conn, "hot_fts")
            self._scan_directory(hot_path, "hot_fts", stats, existing_mtimes)

        # 2. Index Archived Knowledge (Cold)
        cold_path = self.root / "90-99_ARCHIVE_COLD"
        if cold_path.exists():
            existing_mtimes = get_existing_mtimes(self.conn, "cold_fts")
            self._scan_directory(cold_path, "cold_fts", stats, existing_mtimes)

        return stats

    def _scan_directory(
        self,
        path: Path,
        table: str,
        stats: Dict[str, int],
        existing_mtimes: Dict[str, int]
    ) -> None:
        """
        Recursive scan of a directory with batched inserts.
        """
        batch_data: list[tuple[str, str, str, str, str, int]] = []
        batch_size = 500

        for file_path in iter_files(path, extensions={".md"}):
            try:
                skip, current_mtime = should_skip_file(file_path, existing_mtimes)
                if skip:
                    stats["skipped"] += 1
                    continue

                data = self._process_file_data(file_path, current_mtime)
                batch_data.append(data)

                if len(batch_data) >= batch_size:
                    self._flush_batch(table, batch_data)
                    stats["indexed"] += len(batch_data)
                    batch_data = []

            except Exception as exc:
                logger.warning("Error indexing %s: %s", file_path, exc)
                stats["errors"] += 1

        # Flush remaining
        if batch_data:
            try:
                self._flush_batch(table, batch_data)
                stats["indexed"] += len(batch_data)
            except Exception as exc:
                logger.warning("Error flushing remaining batch into %s: %s", table, exc)
                stats["errors"] += len(batch_data)

    def _process_file_data(self, path: Path, mtime: int) -> tuple:
        """Parse file and return data tuple for batch insertion."""
        post = frontmatter.load(path)
        content = post.content
        metadata = post.metadata

        title = metadata.get("title", path.stem)
        tags = ",".join(metadata.get("tags", [])) if isinstance(metadata.get("tags"), list) else str(metadata.get("tags", ""))
        note_type = metadata.get("type", "note")

        return (str(path), title, content, tags, note_type, mtime)

    def _flush_batch(self, table: str, data: List[tuple]) -> None:
        """Execute batch insert using DuckDB executemany."""
        if not data:
            return
        upsert_fts_batch(self.conn, table, data)

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        note_type: Optional[str] = None,
        limit: int = 50,
        global_search: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.

        Args:
            query: Text to search for (in title or content).
            tags: List of tags to filter by.
            note_type: Type of note to filter by.
            limit: Max results.
            global_search: If True, include cold_fts.

        Returns:
            List of result dictionaries.
        """
        params = []
        conditions = []

        if query:
            # Simple ILIKE search for now
            conditions.append("(title ILIKE ? OR content ILIKE ?)")
            wildcard_query = f"%{query}%"
            params.extend([wildcard_query, wildcard_query])

        if tags:
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags ILIKE ?")
                params.append(f"%{tag}%")
            if tag_conditions:
                conditions.append(f"({' OR '.join(tag_conditions)})")

        if note_type:
            conditions.append("note_type ILIKE ?")
            params.append(note_type)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        # Build query parts
        query_parts = []

        # Hot query
        hot_query = f"SELECT file_path, title, content, tags, note_type FROM hot_fts {where_clause}"
        query_parts.append(hot_query)

        if global_search:
            # Cold query
            # We need to duplicate params for the second query part in the UNION
            cold_query = f"SELECT file_path, title, content, tags, note_type FROM cold_fts {where_clause}"
            query_parts.append(cold_query)
            params = params * 2  # Duplicate params for both parts of UNION

        full_query = " UNION ALL ".join(query_parts)
        full_query += " LIMIT ?"
        params.append(limit)

        try:
            rows = self.conn.execute(full_query, params).fetchall()
        except Exception as e:
            logger.error("Search error: %s", e)
            return []

        results = []
        for row in rows:
            file_path = row[0]
            title = row[1]
            content = row[2]
            tags_str = row[3]
            n_type = row[4]

            # Simple word count
            word_count = len(content.split()) if content else 0

            # Preview (simple snippet)
            preview = ""
            if query and content:
                # Find query position
                lower_content = content.lower()
                lower_query = query.lower()
                try:
                    idx = lower_content.index(lower_query)
                    start = max(0, idx - 50)
                    end = min(len(content), idx + 100)
                    preview = content[start:end]
                except ValueError:
                    preview = content[:150]
            elif content:
                preview = content[:150]

            results.append({
                "path": file_path,
                "title": title,
                "type": n_type,
                "word_count": word_count,
                "content_preview": preview
            })

        return results

    def close(self):
        # Connection is managed by adapter, but if we opened anything else...
        pass
