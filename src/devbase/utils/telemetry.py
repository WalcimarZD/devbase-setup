"""
Telemetry Service
=================
Centralized event tracking for DevBase.
Persists events to DuckDB for analytics and flow detection.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from devbase.utils.context import detect_context, infer_activity_type, infer_project_name
from devbase.adapters.storage.duckdb_adapter import log_event
from devbase.services.cognitive_detector import check_flow_state

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
        project_name = infer_project_name(context)

        try:
            log_event(
                event_type=action,
                message=message,
                project=project_name,
                metadata=json.dumps(full_metadata)
            )
        except Exception:
            # Telemetry should never crash the app
            pass

        # Trigger Active Assistance (Flow Detection)
        # We do this after logging so the current event counts towards the flow
        try:
            check_flow_state()
        except Exception:
            pass

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
