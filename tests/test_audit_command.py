"""
Tests for the audit command.
"""
import os
from pathlib import Path
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_audit_consistency_command(tmp_path):
    """Test the full audit consistency command flow."""
    # Setup minimal workspace
    root = tmp_path

    cwd = os.getcwd()
    os.chdir(root)

    try:
        (root / ".devbase_state.json").write_text('{}')

        # Create pyproject.toml
        (root / "pyproject.toml").write_text("""
[project]
name = "test-proj"
dependencies = ["typer>=0.12.0", "requests"]
[project.optional-dependencies]
dev = ["pytest"]
        """)

        # Create ARCHITECTURE.md (missing requests)
        (root / "ARCHITECTURE.md").write_text("Uses typer and pytest.")
        (root / "README.md").write_text("Uses typer.")

        # Create USAGE-GUIDE.md
        (root / "USAGE-GUIDE.md").write_text("# Guide\n\n## Core\n\n- `devbase core setup`\n")

        # Create source files
        src = root / "src/devbase/commands"
        src.mkdir(parents=True)

        # Create a command file with a flag defined in multiline style to test AST parsing
        (src / "test_cmd.py").write_text("""
import typer
app = typer.Typer()
@app.command("my-cmd")
def my_cmd(
    flag: str = typer.Option(
        ...,
        "--my-flag",
        help="Multiline flag"
    )
):
    pass
        """)

        # Create minimal docs/cli
        (root / "docs/cli").mkdir(parents=True)
        (root / "docs/cli/test_cmd.md").write_text("# Test Cmd")

        # Create TECHNICAL_DESIGN_DOC.md
        docs = root / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "TECHNICAL_DESIGN_DOC.md").write_text("Contains table hot_fts.")

        # Create knowledge_db.py
        services = root / "src/devbase/services"
        services.mkdir(parents=True)
        (services / "knowledge_db.py").write_text("CREATE TABLE hot_fts (id INT); CREATE TABLE cold_fts (id INT);")

        # Run audit command
        result = runner.invoke(app, ["audit", "run", "--fix"])

        print(result.stdout) # For debugging if it fails
        assert result.exit_code == 0

        # Check output headers
        assert "DevBase Consistency Audit" in result.stdout

        # Check dependencies
        assert "requests" in result.stdout

        # Check CLI
        assert "test_cmd my-cmd" in result.stdout
        # Flag '--my-flag' should be reported as missing in docs
        assert "test_cmd --my-flag" in result.stdout

        # Check DB
        assert "cold_fts" in result.stdout

        # Check FIX applied to USAGE-GUIDE
        usage_content = (root / "USAGE-GUIDE.md").read_text()
        assert "test_cmd my-cmd" in usage_content

    finally:
        os.chdir(cwd)

def test_audit_changelog_update(tmp_path):
    """Test that CHANGELOG.md is updated when git changes are detected."""
    root = tmp_path
    cwd = os.getcwd()
    os.chdir(root)

    try:
        (root / ".devbase_state.json").write_text('{}')

        # Init git repo
        import subprocess
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "config", "user.email", "you@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Your Name"], check=True)

        # Create initial structure
        (root / "src/devbase").mkdir(parents=True)
        (root / "src/devbase/file.py").write_text("print('hello')")
        (root / "CHANGELOG.md").write_text("# Changelog\n\n## [1.0.0] - 2024-01-01\n- Initial release")

        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

        # Modify file
        (root / "src/devbase/file.py").write_text("print('hello world')")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Modify file"], check=True)

        # Run audit with fix
        result = runner.invoke(app, ["audit", "run", "--fix", "--days", "1"])

        assert result.exit_code == 0
        assert "Checking Changelog..." in result.stdout

        # Check CHANGELOG.md
        content = (root / "CHANGELOG.md").read_text()
        assert "[Unreleased] - In Progress" in content
        assert "Modified src/devbase/file.py" in content or "Modified file.py" in content

    finally:
        os.chdir(cwd)
