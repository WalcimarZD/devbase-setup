"""
Telemetry Service
=================
Centralized event tracking for DevBase.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from devbase.utils.context import detect_context, infer_activity_type, infer_project_name

class TelemetryService:
    def __init__(self, root: Path):
        self.root = root
        self.telemetry_dir = root / ".telemetry"
        self.events_file = self.telemetry_dir / "events.jsonl"
        self._session_id = str(uuid.uuid4())  # Cache per-instance (session)
        self._ensure_dir()

    def _ensure_dir(self):
        self.telemetry_dir.mkdir(exist_ok=True)

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
            dict: The recorded event
        """
        # Auto-detect context
        current_dir = Path.cwd()
        context = detect_context(current_dir, self.root)
        
        if not category:
            category = infer_activity_type(context)

        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "session_id": self._session_id,  # Use cached session ID
            "duration_ms": 0,
            "category": category,
            "action": action,
            "status": status,
            "message": message,
            "context": {
                "type": context.get("context_type"),
                "project": infer_project_name(context),
                "area": context.get("area"),
                "category": context.get("category"),
                "semantic_location": context.get("semantic_location")
            },
            "metadata": metadata or {}
        }

        try:
            with open(self.events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            # Telemetry should never crash the app
            pass

        return event

def get_telemetry(root: Path) -> TelemetryService:
    return TelemetryService(root)
