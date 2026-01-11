"""
Security Utilities
==================
Shared security functions for filename sanitization and path validation.
"""
import re


def sanitize_filename(name: str, replacement: str = "-") -> str:
    """
    Sanitize a string to be a safe filename.

    Prevents path traversal by removing slashes and restricting characters.
    Enforces kebab-case-like structure but allows underscores/dots if needed.

    Args:
        name: The input filename/project name
        replacement: Character to replace invalid chars with

    Returns:
        Safe filename string
    """
    if not name:
        raise ValueError("Filename cannot be empty")

    # Block path traversal attempts explicitly first
    if ".." in name or "/" in name or "\\" in name:
        # We could sanitize, but for explicit inputs like project names,
        # it's better to replace separators to flatten the path
        pass

    # Replace path separators
    name = name.replace("/", replacement).replace("\\", replacement)

    # Remove control characters and non-printable chars
    # Allow: a-z, A-Z, 0-9, ., -, _
    # Replace everything else with replacement
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', replacement, name)

    # Remove leading/trailing dots and replacements (prevent .hidden or -dash)
    safe_name = safe_name.strip(".-_")

    # Collapse multiple replacements
    safe_name = re.sub(f'{re.escape(replacement)}+', replacement, safe_name)

    # Prevent reserved filenames (Windows)
    # CON, PRN, AUX, NUL, COM1-9, LPT1-9
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }

    if safe_name.upper() in reserved:
        safe_name += "_safe"

    if not safe_name:
        # Fallback if everything was stripped
        return "unnamed"

    return safe_name

def validate_project_name(name: str) -> None:
    """
    Validate that a project name is strictly safe and follows conventions.

    Args:
        name: Project name to check

    Raises:
        ValueError: If name is invalid or unsafe
    """
    if not name:
        raise ValueError("Project name cannot be empty")

    if ".." in name:
        raise ValueError("Project name cannot contain path traversal sequences ('..')")

    if "/" in name or "\\" in name:
        raise ValueError("Project name cannot contain path separators")

    # Check against sanitized version
    sanitized = sanitize_filename(name)
    if name != sanitized:
        raise ValueError(f"Invalid project name '{name}'. Suggested: '{sanitized}'")
