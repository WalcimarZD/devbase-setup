"""
Telemetry Service
=================
Centralized event tracking for DevBase.
Persists events to DuckDB for analytics and flow detection.
"""
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from devbase.utils.context import detect_context, infer_activity_type, infer_project_name
from devbase.adapters.storage.event_repository import EventRepository
from devbase.services.cognitive_detector import check_flow_state

logger = logging.getLogger(__name__)

class TelemetryService:
    def __init__(self, root: Path):
        self.root = root
        self._session_id = str(uuid.uuid4())  # Cache per-instance (session)

    def track(
        self,
        message: str,
        category: Optional[str] = None,
        action: str = "track",
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track an event.
        
        Args:
            message: Description of event
            category: Event category (auto-detected if None)
            action: Action name (e.g., track, create_project, build)
            status: Outcome (success, failure)
            metadata: Additional data
            
        Returns:
            dict: The recorded event structure
        """
        # Auto-detect context
        current_dir = Path.cwd()
        context = detect_context(current_dir, self.root)
        
        if not category:
            category = infer_activity_type(context)

        # Prepare metadata payload (serializing extras)
        full_metadata = {
            "session_id": self._session_id,
            "status": status,
            "category": category,
            "context": {
                "type": context.get("context_type"),
                "area": context.get("area"),
                "semantic_location": context.get("semantic_location")
            }
        }

        # Merge user metadata
        if metadata:
            full_metadata.update(metadata)

        # Log to DuckDB
        project_name = metadata.get("project_override") if metadata and "project_override" in metadata else infer_project_name(context)

        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": action,
            "message": message,
            "project": project_name,
            "category": category, # for easier querying
            "metadata": full_metadata
        }

        # 1. DuckDB Write via EventRepository
        try:
            EventRepository().log(
                event_type=action,
                message=message,
                project=project_name,
                metadata=json.dumps(full_metadata)
            )
        except Exception as e:
            logger.debug("Telemetry DuckDB write failed: %s", e)

        # 2. JSONL Fallback (opt-in via config: telemetry.jsonl_fallback = true)
        try:
            from devbase.utils.config import Config
            cfg = Config(root=self.root)
            if cfg.get("telemetry.jsonl_fallback", False):
                log_dir = self.root / ".telemetry"
                log_dir.mkdir(exist_ok=True)
                log_file = log_dir / "events.jsonl"
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event_data) + "\n")
        except Exception as e:
            logger.debug("Telemetry JSONL write failed: %s", e)

        # Trigger Active Assistance (Flow Detection)
        # We do this after logging so the current event counts towards the flow
        try:
            check_flow_state()
        except Exception as e:
            logger.debug(f"Flow detection trigger failed: {e}")

        # Return event dict for callers who might need it (mostly legacy)
        return {
            "timestamp": datetime.now().isoformat(),
            "event_type": action,
            "message": message,
            "project": project_name,
            "metadata": full_metadata
        }

def get_telemetry(root: Path) -> TelemetryService:
    return TelemetryService(root)
