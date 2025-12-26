"""
Johnny.Decimal Taxonomy - Single Source of Truth
=================================================
Defines the JD v5.0 taxonomy used throughout DevBase.

This module is the SSOT for:
- Area definitions (00-09, 10-19, etc.)
- Category naming conventions
- Path validation

SQL constraints use format-only checks; runtime validation uses this module.

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple


class JDCategory(NamedTuple):
    """Johnny.Decimal category definition."""
    
    area: str      # e.g., "10-19"
    name: str      # e.g., "KNOWLEDGE"
    full: str      # e.g., "10-19_KNOWLEDGE"


# Single Source of Truth: JD v5.0 Taxonomy
JD_TAXONOMY: dict[str, JDCategory] = {
    "00-09": JDCategory("00-09", "SYSTEM", "00-09_SYSTEM"),
    "10-19": JDCategory("10-19", "KNOWLEDGE", "10-19_KNOWLEDGE"),
    "20-29": JDCategory("20-29", "CODE", "20-29_CODE"),
    "30-39": JDCategory("30-39", "OPERATIONS", "30-39_OPERATIONS"),
    "40-49": JDCategory("40-49", "MEDIA_ASSETS", "40-49_MEDIA_ASSETS"),
    "90-99": JDCategory("90-99", "ARCHIVE_COLD", "90-99_ARCHIVE_COLD"),
}

# Additional valid category names (for subcategories)
VALID_CATEGORY_NAMES: frozenset[str] = frozenset({
    "SYSTEM",
    "KNOWLEDGE", 
    "CODE",
    "OPERATIONS",
    "MEDIA_ASSETS",
    "ARCHIVE_COLD",
    "PRIVATE_VAULT",
    "TEMP",
})

# Compiled regex pattern for JD format validation
JD_PATTERN = re.compile(r"^([0-9]{2})-([0-9]{2})_([A-Z][A-Z0-9_]*)$")

# SQL CHECK constraint (format-only, immutable)
SQL_JD_CHECK = "jd_category GLOB '[0-9][0-9]-[0-9][0-9]_*'"


def validate_jd_category(category: str) -> bool:
    """
    Validate a JD category string.
    
    Validates both format and area range.
    
    Args:
        category: Category string like "10-19_KNOWLEDGE"
        
    Returns:
        True if valid, False otherwise
        
    Examples:
        >>> validate_jd_category("10-19_KNOWLEDGE")
        True
        >>> validate_jd_category("invalid")
        False
    """
    match = JD_PATTERN.match(category)
    if not match:
        return False
    
    area_start, area_end, name = match.groups()
    area_key = f"{area_start}-{area_end}"
    
    # Check if area is in defined taxonomy
    if area_key in JD_TAXONOMY:
        return JD_TAXONOMY[area_key].name == name
    
    # For custom areas (not in core taxonomy), just validate format
    return name.upper() in VALID_CATEGORY_NAMES or name.isupper()


def validate_jd_path(path: Path) -> bool:
    """
    Validate if a path follows the JD taxonomy.
    
    Checks each path component for JD format compliance.
    
    Args:
        path: Path to validate
        
    Returns:
        True if path follows JD taxonomy, False otherwise
    """
    for part in path.parts:
        match = JD_PATTERN.match(part)
        if match:
            area_start, area_end, name = match.groups()
            area_key = f"{area_start}-{area_end}"
            
            # If it's a core area, name must match
            if area_key in JD_TAXONOMY:
                if JD_TAXONOMY[area_key].name != name:
                    return False
    
    return True


def get_jd_area_for_path(path: Path) -> JDCategory | None:
    """
    Extract JD area from a path.
    
    Scans path components for JD-formatted directories.
    
    Args:
        path: Path to analyze
        
    Returns:
        JDCategory if found, None otherwise
    """
    for part in path.parts:
        match = JD_PATTERN.match(part)
        if match:
            area_key = f"{match.group(1)}-{match.group(2)}"
            if area_key in JD_TAXONOMY:
                return JD_TAXONOMY[area_key]
    
    return None


def get_category_path(area_key: str, workspace_root: Path) -> Path | None:
    """
    Get the full path for a JD area.
    
    Args:
        area_key: Area key like "10-19" or full name like "KNOWLEDGE"
        workspace_root: Workspace root path
        
    Returns:
        Full path to the category directory, or None if not found
    """
    # Handle both "10-19" and "KNOWLEDGE" formats
    for key, category in JD_TAXONOMY.items():
        if key == area_key or category.name == area_key.upper():
            return workspace_root / category.full
    
    return None


def list_areas() -> list[JDCategory]:
    """
    List all JD areas in order.
    
    Returns:
        List of JDCategory objects sorted by area code
    """
    return sorted(JD_TAXONOMY.values(), key=lambda c: c.area)
