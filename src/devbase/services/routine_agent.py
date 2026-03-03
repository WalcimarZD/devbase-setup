"""
Routine Agent Service
=====================
Manages routine and cognitive capital ("Life-OS").

Responsibilities:
- Daily briefing generation
- Daybook summarisation
- Inbox triage and classification

Dependencies are injected via the constructor (DIP) so the service
remains independently testable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple, Optional

from devbase.adapters.storage.event_repository import EventRepository
from devbase.ai.interface import LLMProvider
from devbase.config.taxonomy import list_areas
from devbase.services.security.sanitizer import sanitize_context

logger = logging.getLogger("devbase.routine_agent")


class DaybookSummary(NamedTuple):
    """Structured summary for the daybook."""

    date: str
    focus: str
    log_narrative: str
    metrics: dict[str, int]


class RoutineAgent:
    """Agent for managing daily routine and cognitive load.

    Integrates telemetry events, the knowledge base, and AI to provide
    briefings and summaries.

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
        self.journal_path = self.root_path / "12_private_vault" / "journal"
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

    def get_daily_logs(self, target_date: str) -> list[dict[str, Any]]:
        """Fetch 'track' events for a specific date.

        Args:
            target_date: Date string in YYYY-MM-DD format.

        Returns:
            List of event dicts, ordered by timestamp ascending.
        """
        return self.events.find_by_date(target_date, event_type="track")

    def get_flow_summary_stats(self) -> str:
        """Return a human-readable command/commit summary for the last 24 h."""
        return self.events.get_flow_summary(hours=24)

    def generate_daybook_summary(self, target_date: str) -> DaybookSummary:
        """Generate a full daybook summary for *target_date*.

        Orchestrates log fetching, content sanitisation, AI generation,
        and git metric collection.

        Args:
            target_date: Date string ``YYYY-MM-DD``.

        Returns:
            ``DaybookSummary`` with focus areas and narrative.
        """
        logs = self.get_daily_logs(target_date)
        flow_stats = self.get_flow_summary_stats()
        system_prompt = (
            f"Here is the summary of the user's technical activity in the last 24h: {flow_stats}"
        )

        if not logs:
            raw_content = "No activity logs recorded for this day."
        else:
            lines = []
            for log in logs:
                ts = log["timestamp"]
                ts_str = ts.strftime("%H:%M") if hasattr(ts, "strftime") else str(ts)[:16]
                proj_str = f"({log['project']}) " if log.get("project") else ""
                lines.append(f"[{ts_str}] {proj_str}{log['message']}")
            raw_content = "\n".join(lines)

        sanitized = sanitize_context(raw_content)

        focus = "- [ ] (No logs to infer focus)"
        narrative = "No logs recorded."

        if logs:
            try:
                focus_prompt = (
                    f"Based on these activity logs, identify the 2-3 main tasks or focus areas of the day.\n"
                    f"Format as a markdown list of checkboxes.\n\nLogs:\n{sanitized.content}\n\nResponse:"
                )
                focus = self.provider.complete(
                    focus_prompt,
                    system_prompt=system_prompt,
                    temperature=0.3,
                ).strip()

                narrative_prompt = (
                    f"Transform these activity logs into a concise narrative summary of the day's work.\n"
                    f"Focus on what was accomplished. Do not invent facts.\n\n"
                    f"Logs:\n{sanitized.content}\n\nNarrative:"
                )
                narrative = self.provider.complete(
                    narrative_prompt,
                    system_prompt=system_prompt,
                    temperature=0.5,
                ).strip()

            except Exception as exc:
                logger.error("AI generation for daybook failed: %s", exc)

        return DaybookSummary(
            date=target_date,
            focus=focus,
            log_narrative=narrative,
            metrics={"total_events": len(logs)},
        )

    def get_yesterday_pending(self) -> list[str]:
        """Parse the "Amanha" section from yesterday's journal file."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        file_path = self.journal_path / f"{yesterday}.md"

        if not file_path.exists():
            return [f"No journal found for yesterday ({yesterday})"]

        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("Error reading journal: %s", exc)
            return [f"Error reading journal: {exc}"]

        pending: list[str] = []
        capture = False
        for line in content.splitlines():
            if "## 🔜 Amanhã" in line or "## Amanhã" in line:
                capture = True
                continue
            if capture and line.startswith("##"):
                break
            if capture and line.strip().startswith("- [ ]"):
                task = line.strip().replace("- [ ]", "").strip()
                if task:
                    pending.append(task)

        return pending if pending else ["No pending tasks found in yesterday's journal."]

    def _scan_categories(self) -> list[str]:
        """Scan workspace for available JD categories (level 1 and 2)."""
        categories: list[str] = []

        for area in list_areas():
            area_path = self.root_path / area.full
            if not area_path.exists():
                categories.append(area.full)
                continue

            subdirs = [
                item
                for item in area_path.iterdir()
                if item.is_dir() and item.name[0:2].isdigit() and "_" in item.name
            ]

            if subdirs:
                categories.extend(f"{area.full}/{item.name}" for item in subdirs)
            else:
                categories.append(area.full)

        return categories

    def classify_inbox_item(self, content: str) -> dict[str, str]:
        """Classify an inbox text item using available JD categories."""
        categories = self._scan_categories()
        sanitized = sanitize_context(content)
        default_category = "00-09_SYSTEM"

        if not categories:
            return {"category": default_category, "confidence": "low"}

        prompt = (
            "Classify this text into exactly one category from the list below.\n"
            "Respond with only the category value, nothing else.\n\n"
            f"Categories: {', '.join(categories)}\n\n"
            f"Text:\n{sanitized.content}\n"
        )

        try:
            result = self.provider.complete(prompt, temperature=0.0, max_tokens=80).strip()
            selected = next((category for category in categories if category in result), None)
            return {
                "category": selected or default_category,
                "confidence": "high" if selected else "low",
            }
        except Exception as exc:
            logger.error("Classification failed: %s", exc)
            return {
                "category": default_category,
                "confidence": "low",
                "error": str(exc),
            }

    def scan_inbox(self) -> list[Path]:
        """List all non-hidden files in the inbox folder."""
        inbox_path = self.root_path / "00-09_SYSTEM" / "00_inbox"
        if not inbox_path.exists():
            return []
        return [path for path in inbox_path.iterdir() if path.is_file() and not path.name.startswith(".")]

    def move_to_category(self, file_path: Path, category_full_name: str) -> Path | None:
        """Move a file to a destination category, avoiding name collisions."""
        try:
            destination_dir = self.root_path / category_full_name
            destination_dir.mkdir(parents=True, exist_ok=True)

            destination_path = destination_dir / file_path.name
            if destination_path.exists():
                timestamp = datetime.now().strftime("%H%M%S")
                destination_path = destination_dir / f"{destination_path.stem}_{timestamp}{destination_path.suffix}"

            file_path.rename(destination_path)
            return destination_path
        except OSError as exc:
            logger.error("Move failed: %s", exc)
            return None


def get_routine_agent(root: Path) -> RoutineAgent:
    return RoutineAgent(root_path=root)
