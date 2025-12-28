"""
Async AI Worker - Background Task Processing
=============================================
Daemon thread-based worker for async AI task processing.

Design Decisions:
- Thread-based (not process) for simplicity
- Daemon=True so it dies with main process
- Polls ai_task_queue table in DuckDB
- Only starts if ai.enabled=True in config

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    import duckdb


# Logger for worker errors (non-blocking)
logger = logging.getLogger("devbase.async_worker")


class AIWorker:
    """
    Background worker for processing AI tasks.

    Polls the ai_task_queue table and processes tasks asynchronously.
    Uses a daemon thread that automatically terminates with the main process.

    Usage:
        worker = AIWorker(db_path)
        worker.start()
        # ... application runs ...
        worker.stop()  # Optional, daemon thread will stop automatically
    """

    def __init__(
        self,
        db_path: Path,
        poll_interval: float = 5.0,
        handlers: dict[str, Callable[[str], str]] | None = None
    ):
        """
        Initialize AI worker.

        Args:
            db_path: Path to DuckDB database
            poll_interval: Seconds between polls (default 5.0)
            handlers: Optional dict of task_type -> handler function
        """
        self.db_path = db_path
        self.poll_interval = poll_interval
        self.handlers = handlers or {}

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the worker thread."""
        if self._thread and self._thread.is_alive():
            return  # Already running

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="devbase-ai-worker",
            daemon=True  # Dies with main process
        )
        self._thread.start()
        logger.info("AI worker started")

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the worker gracefully.

        Args:
            timeout: Max seconds to wait for thread to stop
        """
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
            logger.info("AI worker stopped")

    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._thread is not None and self._thread.is_alive()

    def register_handler(self, task_type: str, handler: Callable[[str], str]) -> None:
        """
        Register a handler for a task type.

        Args:
            task_type: Type of task (e.g., 'classify', 'synthesize')
            handler: Function that takes payload and returns result
        """
        self.handlers[task_type] = handler

    def _run_loop(self) -> None:
        """Main worker loop."""
        # Lazy import to avoid cold start penalty
        import duckdb

        conn = duckdb.connect(str(self.db_path), read_only=False)

        try:
            while not self._stop_event.is_set():
                try:
                    task = self._fetch_next_task(conn)
                    if task:
                        self._process_task(conn, task)
                    else:
                        # No tasks, wait before next poll
                        self._stop_event.wait(self.poll_interval)
                except Exception as e:
                    logger.error(f"Worker loop error: {e}")
                    # Back off on error
                    self._stop_event.wait(self.poll_interval * 2)
        finally:
            conn.close()

    def _fetch_next_task(self, conn: duckdb.DuckDBPyConnection) -> dict[str, Any] | None:
        """
        Fetch and claim the next pending task.

        Uses UPDATE...RETURNING for atomic claim.
        """
        try:
            result = conn.execute("""
                UPDATE ai_task_queue
                SET status = 'processing'
                WHERE id = (
                    SELECT id FROM ai_task_queue
                    WHERE status = 'pending'
                    ORDER BY created_at
                    LIMIT 1
                )
                RETURNING id, task_type, payload, created_at
            """).fetchone()

            if result:
                return {
                    "id": result[0],
                    "task_type": result[1],
                    "payload": result[2],
                    "created_at": result[3],
                }
        except Exception as e:
            logger.error(f"Fetch task error: {e}")

        return None

    def _process_task(self, conn: duckdb.DuckDBPyConnection, task: dict[str, Any]) -> None:
        """Process a single task."""
        task_id = task["id"]
        task_type = task["task_type"]

        try:
            # Get handler
            handler = self.handlers.get(task_type)
            if not handler:
                raise ValueError(f"No handler for task type: {task_type}")

            # Execute handler
            result = handler(task["payload"])

            # Mark as done
            conn.execute(
                "UPDATE ai_task_queue SET status = 'done' WHERE id = ?",
                [task_id]
            )

            logger.info(f"Task {task_id} completed: {task_type}")

            # Notify completion (optional - could trigger notification)
            self._on_task_complete(task, result)

        except Exception as e:
            # Mark as failed
            conn.execute(
                "UPDATE ai_task_queue SET status = 'failed' WHERE id = ?",
                [task_id]
            )
            logger.error(f"Task {task_id} failed: {e}")

    def _on_task_complete(self, task: dict[str, Any], result: str) -> None:
        """
        Called when a task completes successfully.

        Override or extend for custom notifications.
        """
        # Default: no-op
        # Subclasses can send desktop notifications, update UI, etc.
        pass


# Default handlers for common task types
# These use GroqProvider when available, with fallback to stubs

def _get_llm_provider():
    """Get LLM provider or None if not available."""
    try:
        from devbase.adapters.ai.groq_adapter import GroqProvider
        return GroqProvider()
    except Exception:
        return None


def _default_classify_handler(payload: str) -> str:
    """Classify handler using LLM when available."""
    data = json.loads(payload)
    content = data.get("content", "")
    categories = data.get("categories", ["general", "task", "note", "idea"])

    provider = _get_llm_provider()
    if provider:
        try:
            result = provider.classify(content, categories)
            return json.dumps({"category": result, "confidence": 0.9, "source": "llm"})
        except Exception as e:
            logger.warning(f"LLM classify failed, using fallback: {e}")

    # Fallback: simple keyword matching
    return json.dumps({"category": categories[0], "confidence": 0.5, "source": "fallback"})


def _default_summarize_handler(payload: str) -> str:
    """Summarize handler using LLM when available."""
    data = json.loads(payload)
    content = data.get("content", "")
    max_length = data.get("max_length", 50)

    provider = _get_llm_provider()
    if provider:
        try:
            result = provider.summarize(content, max_length=max_length)
            return json.dumps({"summary": result, "source": "llm"})
        except Exception as e:
            logger.warning(f"LLM summarize failed, using fallback: {e}")

    # Fallback: simple truncation
    truncated = content[:max_length * 5] + "..." if len(content) > max_length * 5 else content
    return json.dumps({"summary": truncated, "source": "fallback"})


def _default_synthesize_handler(payload: str) -> str:
    """Synthesize handler using LLM when available."""
    data = json.loads(payload)
    prompt = data.get("prompt", "")

    provider = _get_llm_provider()
    if provider:
        try:
            response = provider.generate(prompt)
            return json.dumps({"result": response.content, "source": "llm"})
        except Exception as e:
            logger.warning(f"LLM synthesize failed, using fallback: {e}")

    # Fallback: acknowledge without processing
    return json.dumps({"result": "Task queued but LLM not available", "source": "fallback"})


def _summarize_day_handler(payload: str) -> str:
    """
    Handle summarize_day task: Generates the Daybook.

    Payload: {"date": "YYYY-MM-DD"}
    """
    try:
        from devbase.services.routine_agent import RoutineAgent

        data = json.loads(payload)
        target_date = data.get("date")
        if not target_date:
            return json.dumps({"error": "Missing date"})

        agent = RoutineAgent()
        summary = agent.generate_daybook_summary(target_date)

        # Locate template
        template_path = Path("src/devbase/templates/pkm/12_private_vault/journal/template-daybook.md.template")
        if not template_path.exists():
            # Try relative to module if installed as package
            template_path = Path(__file__).parents[2] / "templates" / "pkm" / "12_private_vault" / "journal" / "template-daybook.md.template"

        if not template_path.exists():
            return json.dumps({"error": "Template not found"})

        template_content = template_path.read_text(encoding="utf-8")

        # Basic template processing
        final_lines = []
        lines = template_content.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i]

            if "{{DATE}}" in line:
                line = line.replace("{{DATE}}", summary.date)
                final_lines.append(line)

            elif "## 🎯 Foco do Dia" in line:
                final_lines.append(line)
                final_lines.append("")
                final_lines.append(summary.focus)
                # Skip placeholder list items
                while i + 1 < len(lines) and lines[i+1].strip().startswith("- [ ] ["):
                    i += 1

            elif "## 📝 Log de Trabalho" in line:
                final_lines.append(line)
                final_lines.append("")
                final_lines.append(summary.log_narrative)
                # Skip placeholder sections
                while i + 1 < len(lines) and (lines[i+1].strip().startswith("###") or "[Atividade]" in lines[i+1] or "[Notas" in lines[i+1]):
                    i += 1

            elif "## 📊 Métricas" in line:
                final_lines.append(line)
                final_lines.append("")
                final_lines.append(f"- Commits: {summary.metrics.get('commits', 0)}")
                final_lines.append(f"- PRs: {summary.metrics.get('prs', 0)}")
                final_lines.append(f"- Issues fechadas: {summary.metrics.get('issues', 0)}")
                # Skip placeholder metrics
                while i + 1 < len(lines) and lines[i+1].strip().startswith("- "):
                    i += 1
            else:
                final_lines.append(line)

            i += 1

        final_content = "\n".join(final_lines)

        # Write to file
        output_path = agent.journal_path / f"{summary.date}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(final_content, encoding="utf-8")

        return json.dumps({"path": str(output_path), "status": "created"})

    except Exception as e:
        logger.error(f"Summarize day failed: {e}")
        return json.dumps({"error": str(e)})


# Module-level worker instance
_worker: AIWorker | None = None


def get_worker(db_path: Path | None = None) -> AIWorker:
    """
    Get or create the singleton AI worker.

    Args:
        db_path: Database path (only used on first call)

    Returns:
        AIWorker instance
    """
    global _worker

    if _worker is None:
        if db_path is None:
            db_path = Path.home() / ".devbase" / "devbase.duckdb"

        _worker = AIWorker(db_path)

        # Register default handlers
        _worker.register_handler("classify", _default_classify_handler)
        _worker.register_handler("summarize", _default_summarize_handler)
        _worker.register_handler("synthesize", _default_synthesize_handler)
        _worker.register_handler("summarize_day", _summarize_day_handler)

    return _worker


def start_worker_if_enabled() -> bool:
    """
    Start the AI worker if AI is enabled in config.

    Returns:
        True if worker was started, False otherwise
    """
    try:
        from devbase.utils.config import get_config
        config = get_config()

        if config.get("ai.enabled", False):
            worker = get_worker()
            worker.start()
            return True
    except Exception as e:
        logger.warning(f"Could not start AI worker: {e}")

    return False
