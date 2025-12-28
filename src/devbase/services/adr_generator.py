"""
ADR Ghostwriter Service
=======================
Drafts Architecture Decision Records (ADRs) using AI.
Analyses 'track' events labeled 'architecture' or 'decision'.

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from devbase.adapters.ai.groq_adapter import GroqProvider
from devbase.adapters.storage.duckdb_adapter import get_connection
from devbase.services.routine_agent import RoutineAgent
from devbase.services.security.sanitizer import sanitize_context
from rich.console import Console

console = Console()
logger = logging.getLogger("devbase.adr_ghostwriter")


class ADRGhostwriter:
    """
    Service for identifying architectural decisions and drafting ADRs.
    """

    def __init__(self, root_path: Path | None = None):
        self.root_path = root_path or Path.cwd()
        self.adr_dir = self.root_path / "18_adr-decisions"
        self._provider: GroqProvider | None = None

    @property
    def provider(self) -> GroqProvider:
        if self._provider is None:
            self._provider = GroqProvider()
        return self._provider

    def find_recent_decisions(self, hours: int = 24) -> list[dict]:
        """
        Find recent 'track' events with 'architecture' or 'decision' in message/category.
        """
        conn = get_connection()
        query = """
            SELECT timestamp, message, project, metadata
            FROM events
            WHERE event_type = 'track'
            AND timestamp > now() - INTERVAL ? HOUR
            ORDER BY timestamp DESC
        """

        candidates = []
        try:
            rows = conn.execute(query, [hours]).fetchall()
            for row in rows:
                ts, msg, proj, meta_str = row
                msg_lower = msg.lower()

                # Check keywords
                if any(kw in msg_lower for kw in ["architecture", "decision", "design", "pattern", "decisão", "arquitetura"]):
                    candidates.append({
                        "timestamp": ts,
                        "message": msg,
                        "project": proj
                    })
        except Exception as e:
            logger.error(f"Error searching events: {e}")

        return candidates

    def generate_draft(self, context_text: str, title_hint: str = "") -> Path | None:
        """
        Generate an ADR draft from context.
        """
        self.adr_dir.mkdir(parents=True, exist_ok=True)

        # Determine next ID
        existing_files = list(self.adr_dir.glob("*.md"))
        max_id = 0
        for f in existing_files:
            try:
                # Expecting format: 0001-title.md
                num_part = f.name.split("-")[0]
                if num_part.isdigit():
                    max_id = max(max_id, int(num_part))
            except Exception:
                pass

        next_id = max_id + 1
        id_str = f"{next_id:04d}"

        # Sanitize input
        sanitized = sanitize_context(context_text)

        prompt = f"""
Create an Architecture Decision Record (ADR) using the MADR template.
Context:
{sanitized.content}

Title Hint: {title_hint}

Required Format:
# {id_str}. [Short Title]

Date: {datetime.now().strftime('%Y-%m-%d')}

## Status
Proposed

## Context
[Description of the problem/context]

## Decision
[The decision made]

## Consequences
[Pros and Cons]
"""

        try:
            console.print("[dim]🤖 Ghostwriting ADR...[/dim]")
            response = self.provider.generate(prompt, temperature=0.3)
            content = response.content

            # Extract title for filename
            lines = content.splitlines()
            title = "untitled-decision"
            for line in lines:
                if line.startswith(f"# {id_str}."):
                    raw_title = line.replace(f"# {id_str}.", "").strip()
                    # Slugify
                    title = raw_title.lower().replace(" ", "-")
                    # Remove special chars
                    title = "".join(c for c in title if c.isalnum() or c == "-")
                    break

            filename = f"{id_str}-{title}.md"
            file_path = self.adr_dir / filename

            file_path.write_text(content, encoding="utf-8")
            return file_path

        except Exception as e:
            logger.error(f"ADR generation failed: {e}")
            return None

def get_ghostwriter(root: Path) -> ADRGhostwriter:
    return ADRGhostwriter(root)
