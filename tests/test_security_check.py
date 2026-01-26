
import pytest
from pathlib import Path
from devbase.commands.security_check import find_unprotected_secrets

def test_find_unprotected_secrets_detects_exposed_files(tmp_path):
    """
    Test that find_unprotected_secrets correctly identifies files NOT in .gitignore
    while ignoring files that ARE in .gitignore.

    This test reproduces the critical bug where ALL files were ignored if .gitignore existed.
    """
    # Create .gitignore
    gitignore = tmp_path / ".gitignore"
    # We ignore *.key files and the ignored_dir directory
    gitignore.write_text("*.key\nignored_dir/\n")

    # Create a secret file that SHOULD be ignored (matches *.key in gitignore)
    # And matches sensitive pattern *.key
    ignored_secret = tmp_path / "secret.key"
    ignored_secret.write_text("SECRET_KEY=123")

    # Create a directory that SHOULD be ignored
    ignored_dir = tmp_path / "ignored_dir"
    ignored_dir.mkdir()
    # Matches sensitive pattern .env
    (ignored_dir / ".env").write_text("SECRET=456")

    # Create a secret file that SHOULD be detected (not in .gitignore)
    # Matches sensitive pattern .env
    exposed_secret = tmp_path / ".env"
    exposed_secret.write_text("API_KEY=exposed")

    # Create a nested secret file that SHOULD be detected
    # Matches sensitive pattern .env
    nested_dir = tmp_path / "src"
    nested_dir.mkdir()
    nested_exposed = nested_dir / ".env"
    nested_exposed.write_text("DB_PASS=exposed")

    # Run scan
    issues = find_unprotected_secrets(tmp_path)

    # Convert issues to list of filenames for easy assertion
    issue_files = [str(path.relative_to(tmp_path)).replace("\\", "/") for path, reason in issues]

    # Verify results
    assert ".env" in issue_files, "Root .env should be detected as exposed"
    assert "src/.env" in issue_files, "Nested src/.env should be detected as exposed"

    assert "secret.key" not in issue_files, "*.key file should be ignored by gitignore"
    assert "ignored_dir/.env" not in issue_files, "File in ignored directory should be ignored"
