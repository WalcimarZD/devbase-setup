"""
Context Detection Utility
==========================
Detects user's current location context within workspace
for intelligent command behavior.
"""
from pathlib import Path
from typing import Optional


def detect_context(current_dir: Path, workspace_root: Path) -> dict:
    """
    Detect user context based on current directory within workspace.
    
    Args:
        current_dir: Current working directory
        workspace_root: DevBase workspace root
        
    Returns:
        dict with keys:
            - context_type: Type of context (workspace_root, code_area, inside_project, etc.)
            - area: Johnny.Decimal area (e.g., "20-29_CODE")
            - category: Specific category (e.g., "21_monorepo_apps")
            - project_name: Project name if inside a project
            - semantic_location: Semantic name (e.g., "code", "vault")
    """
    try:
        rel_path = current_dir.relative_to(workspace_root)
    except ValueError:
        # Not inside workspace
        return {
            "context_type": "outside_workspace",
            "area": None,
            "category": None,
            "project_name": None,
            "semantic_location": None,
        }

    parts = rel_path.parts if rel_path != Path(".") else []

    if len(parts) == 0:
        return {
            "context_type": "workspace_root",
            "area": None,
            "category": None,
            "project_name": None,
            "semantic_location": "root",
        }

    area = parts[0] if len(parts) > 0 else None
    category = parts[1] if len(parts) > 1 else None
    project = parts[2] if len(parts) > 2 else None

    context = {
        "area": area,
        "category": category,
        "project_name": project,
    }

    # Determine semantic location
    semantic_map = {
        ("20-29_CODE", "21_monorepo_apps"): "code",
        ("20-29_CODE", "22_monorepo_packages"): "packages",
        ("10-19_KNOWLEDGE", "11_public_garden"): "knowledge",
        ("10-19_KNOWLEDGE", "12_private_vault"): "vault",
        ("30-39_OPERATIONS", "30_ai"): "ai",
        ("30-39_OPERATIONS", "31_backups"): "backups",
        ("00-09_SYSTEM", "00_inbox"): "inbox",
    }

    semantic_location = semantic_map.get((area, category))
    context["semantic_location"] = semantic_location

    # Determine context type
    if area == "20-29_CODE" and category == "21_monorepo_apps" and project:
        context["context_type"] = "inside_project"
    elif area == "20-29_CODE":
        context["context_type"] = "code_area"
    elif area == "10-19_KNOWLEDGE":
        context["context_type"] = "knowledge_area"
    elif area == "30-39_OPERATIONS":
        context["context_type"] = "operations_area"
    else:
        context["context_type"] = "generic"

    return context


def infer_project_name(context: dict) -> Optional[str]:
    """
    Infer project name from context for auto-tagging.
    
    Args:
        context: Context dict from detect_context()
        
    Returns:
        str: Project name if inside a project, None otherwise
    """
    if context["context_type"] == "inside_project":
        return context["project_name"]
    return None


def infer_activity_type(context: dict) -> str:
    """
    Infer activity type based on current location.
    
    Args:
        context: Context dict from detect_context()
        
    Returns:
        str: Suggested activity type
    """
    location = context.get("semantic_location")

    if location in ("code", "packages"):
        return "coding"
    elif location == "knowledge":
        return "learning"
    elif location == "vault":
        return "personal"
    elif location == "ai":
        return "ai"
    else:
        return "work"
