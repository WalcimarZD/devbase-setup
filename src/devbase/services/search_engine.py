"""
Search Engine Service (Local RAG)
=================================
Implements local semantic search using FastEmbed and DuckDB.

Features:
- Markdown-aware chunking
- Local embedding generation (Zero Network)
- Hybrid search (BM25 + Cosine Similarity)
- Hot/Cold partition support

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from fastembed import TextEmbedding

from devbase.adapters.storage.duckdb_adapter import get_connection
from devbase.config.taxonomy import get_jd_area_for_path
from devbase.services.security.sanitizer import sanitize_context
from devbase.utils.filesystem import scan_directory

logger = logging.getLogger("devbase.search_engine")


@dataclass
class SearchResult:
    """Unified search result."""
    file_path: str
    content: str
    score: float
    source: str  # 'vector' or 'fts'


class MarkdownSplitter:
    """
    Splits Markdown content into chunks preserving header context.

    Strategy:
    1. Split by H1/H2 headers
    2. Further split by paragraph if chunk is too large
    """

    def __init__(self, max_words: int = 500):
        self.max_words = max_words

    def split(self, text: str) -> List[str]:
        """Split text into chunks."""
        # Simple header-based splitting for now
        # Regex matches headers like "# Title" or "## Subtitle"
        # We capture the delimiter to keep it
        parts = re.split(r'(^#{1,3} .*)', text, flags=re.MULTILINE)

        chunks = []
        current_chunk = ""

        for part in parts:
            if not part.strip():
                continue

            # If it's a header, start a new chunk if current is substantial
            if re.match(r'^#{1,3} ', part):
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = part
            else:
                # Content part
                # Check if adding this makes it too big
                if len(current_chunk.split()) + len(part.split()) > self.max_words:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = part
                else:
                    current_chunk += "\n" + part

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


class SearchEngine:
    """
    Core search engine for DevBase.

    Handles indexing and retrieval of knowledge chunks.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize Search Engine.

        Args:
            model_name: FastEmbed model name (default is optimized for CPU/local)
        """
        self.model_name = model_name
        self._embedding_model = None
        self.splitter = MarkdownSplitter()

    @property
    def embedding_model(self) -> TextEmbedding:
        """Lazy load embedding model."""
        if self._embedding_model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._embedding_model = TextEmbedding(model_name=self.model_name)
        return self._embedding_model

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        # FastEmbed returns a generator of iterables (numpy arrays)
        embeddings = list(self.embedding_model.embed([text]))
        # Ensure it's converted to list
        result = embeddings[0]
        if hasattr(result, "tolist"):
            return result.tolist()
        return list(result)

    def index_file(self, file_path: Path, force: bool = False) -> None:
        """
        Process and index a single file.

        Args:
            file_path: Path to the file
            force: If True, re-index even if mtime hasn't changed
        """
        if not file_path.exists() or not file_path.is_file():
            return

        # Determine if Hot or Cold
        area = get_jd_area_for_path(file_path)
        is_cold = area and area.area == "90-99"
        table = "cold_embeddings" if is_cold else "hot_embeddings"

        mtime = int(file_path.stat().st_mtime)
        rel_path = str(file_path)

        conn = get_connection()

        # Check if already indexed and up-to-date
        if not force:
            existing = conn.execute(
                f"SELECT mtime_epoch FROM {table} WHERE file_path = ? LIMIT 1",
                [rel_path]
            ).fetchone()
            if existing and existing[0] == mtime:
                return  # Up to date

        # Read and Sanitize
        try:
            raw_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Skipping binary/unreadable file {file_path}: {e}")
            return

        sanitized = sanitize_context(raw_content)

        # Chunk
        chunks = self.splitter.split(sanitized.content)

        # Clear existing chunks for this file
        conn.execute(f"DELETE FROM {table} WHERE file_path = ?", [rel_path])

        # Determine FTS table
        fts_table = "cold_fts" if is_cold else "hot_fts"
        conn.execute(f"DELETE FROM {fts_table} WHERE file_path = ?", [rel_path])

        # Upsert into FTS (File level)
        # We store the full content for FTS search
        conn.execute(
            f"""
            INSERT INTO {fts_table} (file_path, title, content, mtime_epoch)
            VALUES (?, ?, ?, ?)
            """,
            [rel_path, file_path.name, sanitized.content, mtime]
        )

        # Embed and Insert (Chunk level)
        # ⚡ Bolt Optimization: Batch embedding and insertion
        valid_chunks = [c for c in chunks if c.strip()]

        if valid_chunks:
            # Batch embedding generation (faster on both CPU/GPU)
            embeddings = list(self.embedding_model.embed(valid_chunks))

            # Prepare data for bulk insert
            # Convert numpy arrays to lists if necessary for DuckDB
            data = []
            for i, (chunk, vec) in enumerate(zip(valid_chunks, embeddings)):
                vector_list = vec.tolist() if hasattr(vec, "tolist") else list(vec)
                data.append((rel_path, i, chunk, vector_list, mtime))

            # Bulk insert (reduces transaction overhead)
            conn.executemany(
                f"""
                INSERT INTO {table} (file_path, chunk_id, content_chunk, embedding, mtime_epoch)
                VALUES (?, ?, ?, ?, ?)
                """,
                data
            )

        logger.debug(f"Indexed {rel_path} ({len(valid_chunks)} chunks)")

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """
        Perform hybrid search (Vector + Keyword).

        Args:
            query: Search query
            limit: Max results to return

        Returns:
            List of SearchResult objects
        """
        conn = get_connection()
        query_vec = self.generate_embedding(query)

        results = []

        # 1. Vector Search (Cosine Similarity)
        # Using array_cosine_similarity function from DuckDB
        for table in ["hot_embeddings", "cold_embeddings"]:
            try:
                # DuckDB < 0.10 might need different syntax, assuming recent version
                # array_cosine_similarity returns -1 to 1. We want highest.
                # Note: list_cosine_similarity is the function name in newer DuckDB versions for lists
                rows = conn.execute(
                    f"""
                    SELECT file_path, content_chunk, list_cosine_similarity(embedding, ?) as score
                    FROM {table}
                    ORDER BY score DESC
                    LIMIT ?
                    """,
                    [query_vec, limit]
                ).fetchall()

                for row in rows:
                    results.append(SearchResult(
                        file_path=row[0],
                        content=row[1],
                        score=row[2],
                        source="vector"
                    ))
            except Exception as e:
                logger.error(f"Vector search failed on {table}: {e}")

        # 2. FTS Search (BM25)
        # We query hot_fts and cold_fts for keywords
        # Note: FTS usually returns whole files, so we treat the 'content' as a large chunk.
        # Ideally, we would map back to chunks, but for now we mix file-level FTS results.

        # Whitelist allowed tables to prevent SQL injection
        ALLOWED_FTS_TABLES = ["hot_fts", "cold_fts"]
        sanitized_query = query.replace("'", "''")  # Basic SQL escape

        for table in ALLOWED_FTS_TABLES:
            try:
                # Simple MATCH query
                rows = conn.execute(
                    f"""
                    SELECT file_path, content, score
                    FROM (
                        SELECT file_path, content, fts_main_{table}.match_bm25(file_path, ?) as score
                        FROM {table}
                        WHERE score IS NOT NULL
                    )
                    ORDER BY score DESC
                    LIMIT ?
                    """,
                    [sanitized_query, limit]
                ).fetchall()

                for row in rows:
                    results.append(SearchResult(
                        file_path=row[0],
                        content=row[1],
                        score=row[2], # BM25 score is arbitrary, normalization would be better but keeping simple
                        source="fts"
                    ))
            except Exception as e:
                # FTS might not be set up or query syntax issue
                logger.debug(f"FTS search failed/skipped on {table}: {e}")

        # 3. Sort and Deduplicate
        # We prioritize Hot results implicitly if scores are similar, but here we just sort by score
        # Note: BM25 scores and Vector scores are not directly comparable without normalization.
        # But usually high relevance in either is good context.
        results.sort(key=lambda x: x.score, reverse=True)

        # Deduplicate by content (simple check)
        seen = set()
        final_results = []
        for r in results:
            h = hash(r.content)
            if h not in seen:
                seen.add(h)
                final_results.append(r)

        return final_results[:limit]

    def rebuild_index(self, workspace_root: Path) -> None:
        """
        Rebuild index for entire workspace.
        """
        # Scan Knowledge and Code areas
        targets = [
            workspace_root / "10-19_KNOWLEDGE",
            workspace_root / "20-29_CODE",
            workspace_root / "90-99_ARCHIVE_COLD"
        ]

        extensions = {'.md', '.txt', '.py', '.rs', '.js', '.ts', '.go'}
        count = 0

        for target in targets:
            if not target.exists():
                continue

            # Optimization: Use os.walk with pruning via scan_directory
            # This avoids scanning massive directories like node_modules
            for path in scan_directory(target, extensions=extensions):
                self.index_file(path, force=True)
                count += 1

        logger.info(f"Rebuild complete. Indexed {count} files.")
