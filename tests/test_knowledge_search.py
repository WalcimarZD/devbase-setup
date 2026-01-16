"""
Tests for KnowledgeDB Search functionality.
Verifies FTS optimization and fallback behavior.
"""
import pytest
from pathlib import Path
from devbase.services.knowledge_db import KnowledgeDB
from devbase.adapters.storage import duckdb_adapter

@pytest.fixture
def db(tmp_path, monkeypatch):
    """Create a KnowledgeDB instance with temporary root."""
    # Setup directories
    (tmp_path / "10-19_KNOWLEDGE").mkdir()
    (tmp_path / "90-99_ARCHIVE_COLD").mkdir()

    # Mock get_db_path to always return the temp path
    test_db_path = tmp_path / ".devbase" / "test.duckdb"
    monkeypatch.setattr("devbase.adapters.storage.duckdb_adapter.get_db_path", lambda root=None: test_db_path)

    # Force reset connection for test to pick up new path
    duckdb_adapter.close_connection()

    # Create DB instance
    db = KnowledgeDB(tmp_path)

    yield db

    db.close()
    duckdb_adapter.close_connection()

def test_index_and_search_fts(tmp_path, db):
    """Test that indexing creates FTS index and search finds it."""
    # 1. Create content
    note1 = tmp_path / "10-19_KNOWLEDGE" / "note1.md"
    note1.write_text("""---
title: FTS Optimization
tags: [perf, db]
---
This is a test note about DuckDB full text search.
It is very fast.
""", encoding="utf-8")

    note2 = tmp_path / "10-19_KNOWLEDGE" / "note2.md"
    note2.write_text("""---
title: React Components
tags: [frontend]
---
React uses a virtual DOM.
""", encoding="utf-8")

    # 2. Index
    stats = db.index_workspace()
    assert stats["indexed"] == 2

    # 3. Search using FTS (Query present)
    # Should find 'optimization' in title or content
    results = db.search(query="Optimization")
    assert len(results) == 1
    assert results[0]["title"] == "FTS Optimization"

    # Check if FTS was used?
    # Hard to verify internal execution path without mocking,
    # but if FTS index wasn't created, this might fail or fallback to ILIKE.

    # 4. Search unique word
    results = db.search(query="virtual")
    assert len(results) == 1
    assert results[0]["title"] == "React Components"

def test_incremental_indexing_preserves_fts(tmp_path, db):
    """Test that incremental updates refresh FTS."""
    # 1. Initial Index
    note1 = tmp_path / "10-19_KNOWLEDGE" / "note1.md"
    note1.write_text("---\ntitle: Initial\n---\nContent 1", encoding="utf-8")
    db.index_workspace()

    # Verify search
    assert len(db.search("Content")) == 1

    # 2. Add new file
    note2 = tmp_path / "10-19_KNOWLEDGE" / "note2.md"
    note2.write_text("---\ntitle: UniqueNewDoc\n---\nFreshly Minted Content", encoding="utf-8")

    # 3. Re-index (should index 1 file and refresh FTS)
    stats = db.index_workspace()
    assert stats["indexed"] == 1
    assert stats["skipped"] == 1

    # 4. Search new content
    results = db.search("UniqueNewDoc")
    assert len(results) == 1
    assert results[0]["title"] == "UniqueNewDoc"

    # 5. Search old content
    results = db.search("Content")
    assert len(results) == 2

def test_search_without_query_uses_filters(tmp_path, db):
    """Test search without query (browsing) still works."""
    note1 = tmp_path / "10-19_KNOWLEDGE" / "note1.md"
    note1.write_text("---\ntitle: Tagged Note\ntags: [target]\n---\nContent", encoding="utf-8")

    db.index_workspace()

    # Search by tag only (no query -> no FTS)
    results = db.search(tags=["target"])
    assert len(results) == 1
    assert results[0]["title"] == "Tagged Note"

def test_fallback_to_ilike(tmp_path, db, capsys):
    """Test fallback mechanism when FTS fails."""
    # Setup data
    note1 = tmp_path / "10-19_KNOWLEDGE" / "note1.md"
    note1.write_text("---\ntitle: Fallback Test\n---\nUniqueString", encoding="utf-8")
    db.index_workspace()

    # Force FTS failure by dropping the index manually
    db.conn.execute("PRAGMA drop_fts_index('hot_fts')")

    # Search should still work via fallback
    results = db.search("UniqueString")
    assert len(results) == 1
    assert results[0]["title"] == "Fallback Test"

    # Verify we printed a warning/error about FTS failure?
    # The code prints [red]Search error...[/red] then retries.
    # Actually, verify logic:
    # try: execute FTS
    # except: return search(fallback=True)

    # Since we dropped the index, FTS query will fail with "Catalog Error: ... function ... does not exist"
    # So it should trigger the except block.
