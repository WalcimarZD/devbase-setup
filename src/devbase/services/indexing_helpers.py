"""
Indexing Helpers
================
Shared helpers for workspace indexing workflows.

Centralizes:
- directory scanning
- incremental mtime checks
- hot/cold table resolution
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from devbase.config.taxonomy import get_jd_area_for_path
from devbase.utils.filesystem import scan_directory

if TYPE_CHECKING:
    import duckdb

logger = logging.getLogger(__name__)

ALLOWED_FTS_TABLES = frozenset({"hot_fts", "cold_fts"})
ALLOWED_EMBEDDING_TABLES = frozenset({"hot_embeddings", "cold_embeddings"})


def resolve_tables_for_path(file_path: Path) -> tuple[str, str]:
    """Resolve `(embeddings_table, fts_table)` from path taxonomy area."""
    area = get_jd_area_for_path(file_path)
    is_cold = bool(area and area.area == "90-99")
    if is_cold:
        return "cold_embeddings", "cold_fts"
    return "hot_embeddings", "hot_fts"


def get_existing_mtimes(conn: "duckdb.DuckDBPyConnection", table: str) -> dict[str, int]:
    """Fetch existing `file_path -> mtime_epoch` values for an FTS table."""
    if table not in ALLOWED_FTS_TABLES:
        raise ValueError(f"Invalid FTS table: {table}")

    try:
        rows = conn.execute(f"SELECT file_path, mtime_epoch FROM {table}").fetchall()
        return {row[0]: int(row[1]) for row in rows if row[1] is not None}
    except Exception as exc:
        logger.warning("Could not read existing mtimes from %s: %s", table, exc)
        return {}


def should_skip_file(
    file_path: Path,
    existing_mtimes: dict[str, int],
    *,
    force: bool = False,
) -> tuple[bool, int]:
    """Return `(skip, current_mtime)` for incremental indexing decisions."""
    current_mtime = int(file_path.stat().st_mtime)
    if force:
        return False, current_mtime

    known_mtime = existing_mtimes.get(str(file_path))
    if known_mtime is not None and current_mtime <= known_mtime:
        return True, current_mtime
    return False, current_mtime


def iter_files(path: Path, extensions: set[str]) -> Iterable[Path]:
    """Yield indexable files using the shared directory scanner."""
    return scan_directory(path, extensions=extensions)


def upsert_fts_batch(
    conn: "duckdb.DuckDBPyConnection",
    table: str,
    rows: list[tuple[str, str, str, str, str, int]],
) -> None:
    """Batch upsert records into hot/cold FTS tables."""
    if not rows:
        return
    if table not in ALLOWED_FTS_TABLES:
        raise ValueError(f"Invalid FTS table: {table}")

    conn.executemany(
        f"""
        INSERT INTO {table} (file_path, title, content, tags, note_type, mtime_epoch)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (file_path) DO UPDATE SET
            title = excluded.title,
            content = excluded.content,
            tags = excluded.tags,
            note_type = excluded.note_type,
            mtime_epoch = excluded.mtime_epoch
        """,
        rows,
    )
