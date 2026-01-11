"""
Tests for Security Utilities
============================
Verifies filename sanitization and path validation.
"""
import pytest
from devbase.utils.security import sanitize_filename, validate_project_name

class TestSanitizeFilename:
    def test_basic_filename(self):
        assert sanitize_filename("my-project") == "my-project"
        assert sanitize_filename("MyProject") == "MyProject"

    def test_replaces_separators(self):
        assert sanitize_filename("path/to/project") == "path-to-project"
        assert sanitize_filename("path\\to\\project") == "path-to-project"

    def test_removes_traversal(self):
        # The sanitizer is aggressive, replaces dots if they aren't standard
        # Actually it allows dots but strips leading/trailing
        assert sanitize_filename("../../../target") == "target"
        # ".." becomes "unnamed" because dot is allowed char, but ".." -> "." * 2
        # My implementation: safe_name = re.sub(r'[^a-zA-Z0-9._-]', replacement, name)
        # then strip(".-_")
        # if name is "..", regex keeps "..". strip removes both dots -> empty -> "unnamed"
        assert sanitize_filename("..") == "unnamed"

    def test_replaces_invalid_chars(self):
        # "cool project!" -> "cool-project-" -> strip -> "cool-project"
        assert sanitize_filename("cool project!") == "cool-project"
        assert sanitize_filename("user@host:proj") == "user-host-proj"

    def test_collapses_dashes(self):
        assert sanitize_filename("a///b") == "a-b"
        assert sanitize_filename("a...b") == "a...b" # dots allowed inside

    def test_windows_reserved(self):
        assert sanitize_filename("CON") == "CON_safe"
        assert sanitize_filename("nul") == "nul_safe"
        assert sanitize_filename("LPT1") == "LPT1_safe"

    def test_empty_fallback(self):
        # Implementation raises ValueError on empty input at start
        with pytest.raises(ValueError):
            sanitize_filename("")

        # If input becomes empty after stripping (e.g. "/"), it returns "unnamed"
        assert sanitize_filename("/") == "unnamed"

class TestValidateProjectName:
    def test_valid_names(self):
        validate_project_name("my-project")
        validate_project_name("project-123")

    def test_invalid_names_raise(self):
        with pytest.raises(ValueError, match="path traversal"):
            validate_project_name("../evil")

        with pytest.raises(ValueError, match="path separators"):
            validate_project_name("a/b")

        with pytest.raises(ValueError, match="Suggested"):
            validate_project_name("Bad Name!")
