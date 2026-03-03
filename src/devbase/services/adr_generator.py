"""
ADR Ghostwriter Service
=======================
Drafts Architecture Decision Records (ADRs) from telemetry events using AI.

Dependencies are injected so the service is independently testable (DIP).
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from devbase.adapters.storage.event_repository import EventRepository
from devbase.ai.interface import LLMProvider
from devbase.services.security.sanitizer import sanitize_context

logger = logging.getLogger("devbase.adr_ghostwriter")


class ADRGhostwriter:
    """Identifies architectural decisions and drafts ADR markdown files.

    Args:
        root_path: Workspace root (defaults to CWD).
        provider: LLM provider (resolved lazily if omitted).
        events: Event repository (instantiated lazily if omitted).
    """

    def __init__(
        self,
        root_path: Optional[Path] = None,
        provider: Optional[LLMProvider] = None,
        events: Optional[EventRepository] = None,
    ) -> None:
        self.root_path = root_path or Path.cwd()
        self.adr_dir = self.root_path / "18_adr-decisions"
        self._provider = provider
        self._events = events

    @property
    def provider(self) -> LLMProvider:
        """Lazily resolve the LLM provider via the factory."""
        if self._provider is None:
            from devbase.ai.factory import AIProviderFactory
            self._provider = AIProviderFactory.get_provider(self.root_path)
        return self._provider

    @property
    def events(self) -> EventRepository:
        """Lazily create the event repository."""
        if self._events is None:
            self._events = EventRepository()
        return self._events

    def find_recent_decisions(self, hours: int = 24) -> list[dict]:
        """Find recent track events that mention architectural decisions.

        Args:
            hours: Lookback window in hours.

        Returns:
            List of candidate event dicts.
        """
        return self.events.find_decisions(hours=hours)

    def generate_draft(self, context_text: str, title_hint: str = "") -> Optional[Path]:
        """Generate an ADR draft from *context_text* and write it to disk.

        Args:
            context_text: Raw context to be sanitised and sent to the LLM.
            title_hint: Optional short title for the filename.

        Returns:
            Path to the written file, or ``None`` on failure.
        """
        self.adr_dir.mkdir(parents=True, exist_ok=True)

        existing_files = list(self.adr_dir.glob("*.md"))
        max_id = 0
        for f in existing_files:
            try:
                num_part = f.name.split("-")[0]
                if num_part.isdigit():
                    max_id = max(max_id, int(num_part))
            except Exception:
                pass

        id_str = f"{max_id + 1:04d}"
        sanitized = sanitize_context(context_text)

        prompt = (
            f"Create an Architecture Decision Record (ADR) using the MADR template.\n"
            f"Context:\n{sanitized.content}\n\nTitle Hint: {title_hint}\n\n"
            f"Required Format:\n"
            f"# {id_str}. [Short Title]\n\nDate: {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"## Status\nProposed\n\n## Context\n[Description]\n\n"
            f"## Decision\n[The decision]\n\n## Consequences\n[Pros and Cons]"
        )

        try:
            content = self.provider.complete(prompt, temperature=0.3)

            title = "untitled-decision"
            for line in content.splitlines():
                if line.startswith(f"# {id_str}."):
                    raw_title = line.replace(f"# {id_str}.", "").strip()
                    title = "".join(
                        c for c in raw_title.lower().replace(" ", "-")
                        if c.isalnum() or c == "-"
                    )
                    break

            file_path = self.adr_dir / f"{id_str}-{title}.md"
            file_path.write_text(content, encoding="utf-8")
            return file_path

        except Exception as exc:
            logger.error("ADR generation failed: %s", exc)
            return None


def get_ghostwriter(root: Path) -> ADRGhostwriter:
    return ADRGhostwriter(root_path=root)



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
