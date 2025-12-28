"""
Routine Agent Service
=====================
Manages routine and cognitive capital ("Life-OS").

Responsibilities:
- Daily briefing generation
- Daybook summarization
- Inbox triage and classification

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple

from devbase.adapters.ai.groq_adapter import GroqProvider
from devbase.adapters.storage.duckdb_adapter import get_connection
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
    """
    Agent for managing daily routine and cognitive load.

    Integrates telemetry (events), knowledge base (journal), and AI
    to provide briefings and summaries.
    """

    def __init__(self, root_path: Path | None = None):
        """
        Initialize RoutineAgent.

        Args:
            root_path: Root directory of the workspace (defaults to CWD)
        """
        self.root_path = root_path or Path.cwd()
        self.journal_path = self.root_path / "12_private_vault" / "journal"
        self._provider: GroqProvider | None = None

    @property
    def provider(self) -> GroqProvider:
        """Lazy-load AI provider."""
        if self._provider is None:
            self._provider = GroqProvider()
        return self._provider

    def get_daily_logs(self, target_date: str) -> list[dict[str, Any]]:
        """
        Fetch 'track' events for a specific date.

        Args:
            target_date: Date string in YYYY-MM-DD format

        Returns:
            List of event dictionaries
        """
        conn = get_connection()

        # DuckDB query to filter by date (ignoring time)
        query = """
            SELECT timestamp, message, project, metadata
            FROM events
            WHERE event_type = 'track'
            AND strftime(timestamp, '%Y-%m-%d') = ?
            ORDER BY timestamp ASC
        """

        try:
            results = conn.execute(query, [target_date]).fetchall()
            logs = []
            for row in results:
                ts, msg, proj, meta = row
                logs.append({
                    "timestamp": ts,
                    "message": msg,
                    "project": proj,
                    "metadata": meta
                })
            return logs
        except Exception as e:
            logger.error(f"Failed to fetch logs: {e}")
            return []

    def generate_daybook_summary(self, target_date: str) -> DaybookSummary:
        """
        Generate a full summary for the daybook.

        Orchestrates:
        1. Fetching logs
        2. Sanitizing content
        3. AI generation of narrative and focus
        4. Fetching git metrics

        Args:
            target_date: Date string YYYY-MM-DD

        Returns:
            DaybookSummary object
        """
        logs = self.get_daily_logs(target_date)

        # Prepare content for AI
        if not logs:
            raw_content = "No activity logs recorded for this day."
        else:
            lines = []
            for log in logs:
                # Format: [HH:MM] (Project) Message
                ts_str = log["timestamp"].strftime("%H:%M")
                proj_str = f"({log['project']}) " if log["project"] else ""
                lines.append(f"[{ts_str}] {proj_str}{log['message']}")
            raw_content = "\n".join(lines)

        # Security: Sanitize before sending to AI
        sanitized = sanitize_context(raw_content)

        # Default values
        focus = "- [ ] (No logs to infer focus)"
        narrative = "No logs recorded."

        if logs:
            try:
                # Prompt for Focus
                focus_prompt = f"""
Based on these activity logs, identify the 2-3 main tasks or focus areas of the day.
Format as a markdown list of checkboxes.

Logs:
{sanitized.content}

Response:"""
                focus_resp = self.provider.generate(focus_prompt, temperature=0.3)
                focus = focus_resp.content.strip()

                # Prompt for Narrative
                narrative_prompt = f"""
Transform these activity logs into a concise narrative summary of the day's work.
Focus on what was accomplished and any challenges mentioned.
Do not invent facts. Use only the provided logs.

Logs:
{sanitized.content}

Narrative:"""
                narrative_resp = self.provider.generate(narrative_prompt, temperature=0.5)
                narrative = narrative_resp.content.strip()

            except Exception as e:
                logger.warning(f"AI generation failed: {e}")
                focus = "- [ ] (AI unavailable)"
                narrative = raw_content  # Fallback to raw logs

        # Git Metrics
        metrics = self.get_git_metrics()

        return DaybookSummary(
            date=target_date,
            focus=focus,
            log_narrative=narrative,
            metrics=metrics
        )

    def get_git_metrics(self) -> dict[str, int]:
        """
        Fetch git metrics for the current day using GitPython library.

        Returns:
            Dictionary with commits, prs, and issues counts
        """
        metrics = {"commits": 0, "prs": 0, "issues": 0}

        try:
            # Use GitPython for safe git operations
            from git import InvalidGitRepositoryError, Repo

            # Initialize repository from current path
            repo = Repo(self.root_path, search_parent_directories=True)

            # Count commits since midnight
            from datetime import datetime
            midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # Get commits from HEAD since midnight
            commits = list(repo.iter_commits('HEAD', since=midnight))
            metrics["commits"] = len(commits)

            # PRs and Issues would require GH CLI or API, keeping simple for now
            # per instructions ("podes usar comandos de shell simples (git)")

        except ImportError:
            logger.warning("GitPython not available, git metrics unavailable")
        except InvalidGitRepositoryError:
            pass  # Not a git repo
        except Exception as e:
            logger.warning(f"Git metrics failed: {e}")

        return metrics

    def get_yesterday_pending(self) -> list[str]:
        """
        Parse 'Amanhã' section from yesterday's journal.

        Returns:
            List of pending tasks (strings)
        """
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        file_path = self.journal_path / f"{yesterday}.md"

        if not file_path.exists():
            return [f"No journal found for yesterday ({yesterday})"]

        try:
            content = file_path.read_text(encoding="utf-8")

            # Simple parsing: look for "## 🔜 Amanhã" and take subsequent lines
            # until next header or end of file
            pending = []
            capture = False
            for line in content.splitlines():
                if "## 🔜 Amanhã" in line or "## Amanhã" in line:
                    capture = True
                    continue
                if capture and line.startswith("##"):
                    break
                if capture and line.strip().startswith("- [ ]"):
                    # Extract task text
                    task = line.strip().replace("- [ ]", "").strip()
                    if task:
                        pending.append(task)

            return pending if pending else ["No pending tasks found in yesterday's journal."]

        except Exception as e:
            logger.error(f"Error reading journal: {e}")
            return [f"Error reading journal: {e}"]

    def classify_inbox_item(self, content: str) -> dict[str, str]:
        """
        Classify a text item using JD taxonomy.

        Args:
            content: Raw text content

        Returns:
            Dict with 'category', 'reasoning'
        """
        # Get valid categories from taxonomy
        # We use the full names (e.g., "10-19_KNOWLEDGE") as targets
        categories = [c.full for c in list_areas()]

        # Sanitize
        sanitized = sanitize_context(content)

        try:
            category = self.provider.classify(sanitized.content, categories)
            return {"category": category, "confidence": "high"}
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {"category": "00-09_SYSTEM", "confidence": "low", "error": str(e)}

    def scan_inbox(self) -> list[Path]:
        """List files in the Inbox."""
        inbox_path = self.root_path / "00-09_SYSTEM" / "00_inbox"
        if not inbox_path.exists():
            return []

        # Return all files, ignoring hidden ones
        return [p for p in inbox_path.iterdir() if p.is_file() and not p.name.startswith(".")]

    def move_to_category(self, file_path: Path, category_full_name: str) -> Path | None:
        """
        Move a file to the suggested category.

        Args:
            file_path: Source file path
            category_full_name: Destination category name (e.g., "20-29_CODE")

        Returns:
            New path if successful, None otherwise
        """
        try:
            dest_dir = self.root_path / category_full_name
            if not dest_dir.exists():
                # Try to find it in taxonomy if it's just an area
                # But here we assume category_full_name matches a root folder
                # If not, create it?
                # The taxonomy defines root folders like "10-19_KNOWLEDGE"
                # So we should expect these to exist or be creatable.
                dest_dir.mkdir(parents=True, exist_ok=True)

            new_path = dest_dir / file_path.name

            # Handle collision
            if new_path.exists():
                stem = new_path.stem
                suffix = new_path.suffix
                timestamp = datetime.now().strftime("%H%M%S")
                new_path = dest_dir / f"{stem}_{timestamp}{suffix}"

            file_path.rename(new_path)
            return new_path
        except Exception as e:
            logger.error(f"Move failed: {e}")
            return None
