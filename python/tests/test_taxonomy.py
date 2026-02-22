"""
Tests for JD Taxonomy
=====================
Verifies Johnny.Decimal taxonomy validation.
"""
from pathlib import Path

import pytest

from devbase.config.taxonomy import (
    JD_TAXONOMY,
    JD_PATTERN,
    validate_jd_category,
    validate_jd_path,
    get_jd_area_for_path,
    get_category_path,
    list_areas,
)


class TestJDTaxonomy:
    """Tests for taxonomy constants."""
    
    def test_taxonomy_has_core_areas(self):
        """Verify core areas are defined."""
        assert "00-09" in JD_TAXONOMY
        assert "10-19" in JD_TAXONOMY
        assert "20-29" in JD_TAXONOMY
        assert "90-99" in JD_TAXONOMY
    
    def test_taxonomy_values_are_consistent(self):
        """Verify taxonomy values match keys."""
        for key, category in JD_TAXONOMY.items():
            assert category.area == key
            assert category.full.startswith(key)


class TestValidateJDCategory:
    """Tests for category validation."""
    
    def test_valid_category(self):
        """Verify valid categories pass."""
        assert validate_jd_category("10-19_KNOWLEDGE") is True
        assert validate_jd_category("20-29_CODE") is True
        assert validate_jd_category("00-09_SYSTEM") is True
    
    def test_invalid_format(self):
        """Verify invalid formats fail."""
        assert validate_jd_category("invalid") is False
        assert validate_jd_category("10_KNOWLEDGE") is False
        assert validate_jd_category("10-19") is False
    
    def test_invalid_range(self):
        """Verify out-of-range areas fail for core categories."""
        # These should fail because they're core areas with wrong names
        assert validate_jd_category("10-19_CODE") is False  # Should be KNOWLEDGE
        assert validate_jd_category("20-29_KNOWLEDGE") is False  # Should be CODE


class TestValidateJDPath:
    """Tests for path validation."""
    
    def test_valid_jd_path(self):
        """Verify valid JD paths pass."""
        path = Path("workspace/10-19_KNOWLEDGE/notes")
        assert validate_jd_path(path) is True
    
    def test_invalid_jd_path(self):
        """Verify paths with wrong names fail."""
        path = Path("workspace/10-19_WRONGNAME/notes")
        assert validate_jd_path(path) is False
    
    def test_non_jd_path_passes(self):
        """Verify non-JD paths are accepted."""
        path = Path("workspace/src/components")
        assert validate_jd_path(path) is True


class TestGetJDAreaForPath:
    """Tests for area extraction."""
    
    def test_extracts_area(self):
        """Verify area is extracted from path."""
        path = Path("workspace/10-19_KNOWLEDGE/notes/file.md")
        area = get_jd_area_for_path(path)
        
        assert area is not None
        assert area.area == "10-19"
        assert area.name == "KNOWLEDGE"
    
    def test_returns_none_for_non_jd(self):
        """Verify None for non-JD paths."""
        path = Path("workspace/src/main.py")
        area = get_jd_area_for_path(path)
        
        assert area is None


class TestGetCategoryPath:
    """Tests for category path resolution."""
    
    def test_by_area_key(self):
        """Verify path resolution by area key."""
        root = Path("/workspace")
        path = get_category_path("10-19", root)
        
        assert path is not None
        assert path == root / "10-19_KNOWLEDGE"
    
    def test_by_name(self):
        """Verify path resolution by name."""
        root = Path("/workspace")
        path = get_category_path("CODE", root)
        
        assert path is not None
        assert path == root / "20-29_CODE"
    
    def test_invalid_area(self):
        """Verify None for invalid areas."""
        root = Path("/workspace")
        path = get_category_path("INVALID", root)
        
        assert path is None


class TestListAreas:
    """Tests for area listing."""
    
    def test_returns_all_areas(self):
        """Verify all areas are returned."""
        areas = list_areas()
        assert len(areas) == len(JD_TAXONOMY)
    
    def test_sorted_by_area(self):
        """Verify areas are sorted."""
        areas = list_areas()
        area_codes = [a.area for a in areas]
        assert area_codes == sorted(area_codes)
