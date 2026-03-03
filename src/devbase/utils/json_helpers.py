"""
JSON Utility Helpers
====================
Safe JSON extraction from unstructured LLM responses.

Centralised SSOT so every service that parses LLM output stays DRY.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def safe_json_extract(text: str) -> Dict[str, Any]:
    """Extract and parse the first JSON object found in ``text``.

    Locates the outermost ``{ ... }`` block and parses it.
    Returns an empty dict on any failure so callers can handle
    gracefully without branching on None.

    Args:
        text: Raw LLM response that may contain a JSON object.

    Returns:
        Parsed dict, or ``{}`` if extraction or parsing fails.
    """
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON delimiters found in response")
        return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to extract JSON from AI response: %s", exc)
        return {}
