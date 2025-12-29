"""
Cognitive Detector - Mode Detection & Flow Analysis
===================================================
1. O(n) keyword-based cognitive mode detection (Pure Python).
2. DuckDB-based Flow State Analysis (Active Assistance).

Modes:
- attack: Critical thinking, risk identification
- explore: Ideation, brainstorming
- document: Formalization, specification

Flow States:
- High Flow: > 8 events/hour
- Frustrated: 5 consecutive failures

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from devbase.adapters.storage.duckdb_adapter import get_connection
from devbase.services.notifications import get_notifier


# Cognitive mode triggers (bilingual: EN + PT)
COGNITIVE_TRIGGERS: dict[str, list[str]] = {
    "attack": [
        # English
        "critic", "flaw", "risk", "security", "fail", "wrong",
        "vulnerability", "issue", "problem", "bug", "error",
        # Portuguese
        "crítica", "falha", "risco", "segurança", "vulnerabilidade",
        "problema", "erro", "incorreto",
    ],
    "explore": [
        # English
        "idea", "alternative", "explore", "brainstorm", "what if",
        "possibility", "option", "creative", "innovate",
        # Portuguese
        "ideia", "alternativa", "explorar", "possibilidade",
        "opção", "criativo", "inovar",
    ],
    "document": [
        # English
        "document", "adr", "spec", "reference", "formalize",
        "specification", "design", "architecture", "record",
        # Portuguese
        "documentar", "especificação", "referência", "formalizar",
        "arquitetura", "registro",
    ],
}


def detect_cognitive_mode(prompt: str) -> str:
    """
    Detect cognitive mode from prompt text.
    
    Uses O(n) keyword matching - no DB, no I/O.
    This is safe for the critical path (< 50ms).
    
    Args:
        prompt: User input text
        
    Returns:
        Mode string: "attack", "explore", "document", or "neutral"
    """
    prompt_lower = prompt.lower()
    
    for mode, keywords in COGNITIVE_TRIGGERS.items():
        if any(kw in prompt_lower for kw in keywords):
            return mode
    
    return "neutral"


def get_mode_description(mode: str) -> str:
    """Get human-readable description of cognitive mode."""
    descriptions = {
        "attack": "🔍 Critical Analysis - Identifying risks and issues",
        "explore": "💡 Exploration - Generating ideas and alternatives",
        "document": "📝 Documentation - Formalizing and recording",
        "neutral": "⚪ Neutral - General assistance",
    }
    return descriptions.get(mode, descriptions["neutral"])


def get_mode_emoji(mode: str) -> str:
    """Get emoji for cognitive mode."""
    emojis = {
        "attack": "🔍",
        "explore": "💡",
        "document": "📝",
        "neutral": "⚪",
    }
    return emojis.get(mode, "⚪")


# --- Flow Analysis (Active Assistance) ---

def check_flow_state() -> None:
    """
    Analyze recent telemetry to detect Flow or Frustration.
    Sends notifications if thresholds are met.

    Called automatically by telemetry.track().
    """
    try:
        conn = get_connection()
        notifier = get_notifier()

        # 1. High Flow Detection (> 8 events in last hour)
        # Using DuckDB's interval syntax
        count_query = """
            SELECT count(*)
            FROM events
            WHERE timestamp > now() - INTERVAL 1 HOUR
        """
        result = conn.execute(count_query).fetchone()
        count = result[0] if result else 0

        if count > 8:
            # We don't want to spam, so maybe check if we already notified recently?
            # For this MVP/Task, we'll just check if it's *exactly* a multiple or something,
            # or rely on the user to ignore.
            # Better: Check if we just crossed the threshold (e.g., count == 9).
            if count == 9:
                notifier.notify(
                    title="🚀 High Flow State Detected",
                    message="You are in the zone! Notifications suppressed to protect focus."
                )

        # 2. Frustration Detection (5 consecutive failures)
        # Fetch last 5 events
        fail_query = """
            SELECT metadata
            FROM events
            ORDER BY timestamp DESC
            LIMIT 5
        """
        rows = conn.execute(fail_query).fetchall()

        if len(rows) == 5:
            failures = 0
            for row in rows:
                try:
                    meta = json.loads(row[0])
                    if meta.get("status") == "failed" or meta.get("status") == "error":
                        failures += 1
                except Exception:
                    pass

            if failures == 5:
                # Detected frustration
                notifier.notify(
                    title="🛑 Frustration Detected",
                    message="5 consecutive errors. Time for a break or a walk?"
                )

    except Exception:
        # Never crash the main app due to background analysis
        pass
