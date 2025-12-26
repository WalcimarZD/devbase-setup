"""
Cognitive Detector - Mode Detection
====================================
O(n) keyword-based cognitive mode detection.

No DB queries, no I/O, no network calls.
Pure Python string matching for < 50ms cold start compliance.

Modes:
- attack: Critical thinking, risk identification
- explore: Ideation, brainstorming
- document: Formalization, specification

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations


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
        
    Examples:
        >>> detect_cognitive_mode("What are the risks?")
        'attack'
        >>> detect_cognitive_mode("Let's brainstorm ideas")
        'explore'
        >>> detect_cognitive_mode("Hello world")
        'neutral'
    """
    prompt_lower = prompt.lower()
    
    for mode, keywords in COGNITIVE_TRIGGERS.items():
        if any(kw in prompt_lower for kw in keywords):
            return mode
    
    return "neutral"


def get_mode_description(mode: str) -> str:
    """
    Get human-readable description of cognitive mode.
    
    Args:
        mode: Cognitive mode string
        
    Returns:
        Description string
    """
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
