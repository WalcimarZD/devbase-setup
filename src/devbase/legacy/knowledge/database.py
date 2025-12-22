"""
Knowledge Database Module
==========================
SQLite-based knowledge base indexing for fast queries and search.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import frontmatter
from rich.console import Console

console = Console()


class KnowledgeDB:
    """
    SQLite knowledge database for indexing and searching notes.
    
    Schema:
    - notes: Main note metadata
    - tags: Tag associations
    - links: Wikilink relationships
    """
    
    def __init__(self, root: Path):
        self.root = root
        self.db_path = root / ".devbase" / "knowledge.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        
    def connect(self) -> None:
        """Initialize database connection and create schema if needed."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()
        
    def _create_schema(self) -> None:
        """Create database schema."""
        cursor = self.conn.cursor()
        
        # Notes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                type TEXT,
                status TEXT,
                created TIMESTAMP,
                updated TIMESTAMP,
                last_reviewed TIMESTAMP,
                content_preview TEXT,
                word_count INTEGER
            )
        """)
        
        # Tags table (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                note_id INTEGER,
                tag TEXT NOT NULL,
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
            )
        """)
        
        # Links table (graph edges)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS links (
                source_id INTEGER,
                target_path TEXT,
                FOREIGN KEY (source_id) REFERENCES notes(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title)")
        
        self.conn.commit()
        
    def index_workspace(self) -> Dict[str, int]:
        """
        Scan workspace and index all markdown files.
        
        Returns:
            Dictionary with indexing statistics
        """
        if not self.conn:
            self.connect()
            
        cursor = self.conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM notes")
        cursor.execute("DELETE FROM tags")
        cursor.execute("DELETE FROM links")
        
        knowledge_base = self.root / "10-19_KNOWLEDGE"
        
        stats = {"indexed": 0, "skipped": 0, "errors": 0}
        
        for md_file in knowledge_base.rglob("*.md"):
            if md_file.name.startswith("_"):
                stats["skipped"] += 1
                continue
                
            try:
                post = frontmatter.load(md_file)
                
                # Insert note
                rel_path = str(md_file.relative_to(self.root))
                content_preview = post.content[:500]
                word_count = len(post.content.split())
                
                cursor.execute("""
                    INSERT INTO notes (path, title, type, status, created, updated, 
                                     last_reviewed, content_preview, word_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rel_path,
                    post.get("title", md_file.stem),
                    post.get("type"),
                    post.get("status"),
                    post.get("created"),
                    post.get("updated"),
                    post.get("last_reviewed"),
                    content_preview,
                    word_count
                ))
                
                note_id = cursor.lastrowid
                
                # Insert tags
                tags = post.get("tags", [])
                for tag in tags:
                    cursor.execute("INSERT INTO tags (note_id, tag) VALUES (?, ?)",
                                 (note_id, tag))
                
                # Extract wikilinks (simplified)
                import re
                links = re.findall(r'\[\[([^\]]+)\]\]', post.content)
                for link in links:
                    cursor.execute("INSERT INTO links (source_id, target_path) VALUES (?, ?)",
                                 (note_id, link))
                
                stats["indexed"] += 1
                
            except Exception as e:
                stats["errors"] += 1
                console.print(f"[dim]Error indexing {md_file.name}: {e}[/dim]")
        
        self.conn.commit()
        return stats
        
    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        note_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search notes by various criteria.
        
        Args:
            query: Text search in title/content (LIKE search)
            tags: Filter by tags (AND logic)
            note_type: Filter by note type
            limit: Maximum results
            
        Returns:
            List of matching notes
        """
        if not self.conn:
            self.connect()
            
        cursor = self.conn.cursor()
        
        # Build dynamic query
        where_clauses = []
        params = []
        
        if query:
            where_clauses.append("(n.title LIKE ? OR n.content_preview LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
            
        if note_type:
            where_clauses.append("n.type = ?")
            params.append(note_type)
            
        base_query = "SELECT DISTINCT n.* FROM notes n"
        
        if tags:
            # Join with tags for filtering
            for i, tag in enumerate(tags):
                base_query += f" JOIN tags t{i} ON n.id = t{i}.note_id"
                where_clauses.append(f"t{i}.tag = ?")
                params.append(tag)
        
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
            
        base_query += f" LIMIT {limit}"
        
        cursor.execute(base_query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
            
        return results
        
    def get_stats(self) -> Dict:
        """Get knowledge base statistics."""
        if not self.conn:
            self.connect()
            
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Note count
        cursor.execute("SELECT COUNT(*) as count FROM notes")
        stats["total_notes"] = cursor.fetchone()["count"]
        
        # Notes by type
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM notes 
            WHERE type IS NOT NULL 
            GROUP BY type
        """)
        stats["by_type"] = {row["type"]: row["count"] for row in cursor.fetchall()}
        
        # Top tags
        cursor.execute("""
            SELECT tag, COUNT(*) as count 
            FROM tags 
            GROUP BY tag 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats[" top_tags"] = {row["tag"]: row["count"] for row in cursor.fetchall()}
        
        return stats
        
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
