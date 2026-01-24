import pytest
from typer.testing import CliRunner
from pathlib import Path
import sys
import subprocess
# Ensure src is in path if not already
sys.path.append("src")

from src.devbase.commands.audit import app

runner = CliRunner()

def setup_mock_workspace(tmp_path):
    (tmp_path / "src/devbase/commands").mkdir(parents=True)
    (tmp_path / "src/devbase/services").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)

    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "docs/TECHNICAL_DESIGN_DOC.md").write_text("")
    (tmp_path / "src/devbase/services/knowledge_db.py").write_text("")
    (tmp_path / "USAGE-GUIDE.md").write_text("# Usage Guide\n")

def test_audit_run_detects_undocumented_cli(tmp_path, monkeypatch):
    setup_mock_workspace(tmp_path)

    # Create a command file with undocumented items
    cmd_file = tmp_path / "src/devbase/commands/test_cmd.py"
    cmd_file.write_text("""
import typer
app = typer.Typer()

@app.command("my-command")
def my_command(
    flag: str = typer.Option("default", "--my-flag")
):
    pass
""")

    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Invoke app directly (Typer treating single command app as the command)
    result = runner.invoke(app, [], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Undocumented commands/flags" in result.stdout
    # Normalize stdout to handle Rich wrapping
    stdout_normalized = " ".join(result.stdout.split())
    assert "devbase test_cmd my-command (command)" in stdout_normalized
    assert "devbase test_cmd my-command --my-flag (flag)" in stdout_normalized

def test_audit_fix_updates_usage_guide(tmp_path, monkeypatch):
    setup_mock_workspace(tmp_path)

    cmd_file = tmp_path / "src/devbase/commands/test_cmd.py"
    cmd_file.write_text("""
import typer
app = typer.Typer()

@app.command("my-command")
def my_command():
    pass
""")

    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    result = runner.invoke(app, ["--fix"], catch_exceptions=False)

    assert result.exit_code == 0
    content = (tmp_path / "USAGE-GUIDE.md").read_text()
    assert "Undocumented Items" in content
    assert "devbase test_cmd my-command" in content

def test_audit_updates_changelog(tmp_path, monkeypatch):
    setup_mock_workspace(tmp_path)
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## [1.0.0]\n- Old changes\n")

    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Mock subprocess.run to simulate git log finding changes
    def mock_run(args, **kwargs):
        # Check if it's the git log command
        # ["git", "log", ..., str(src_path)]
        if isinstance(args, list) and "git" in args and "log" in args:
             class MockResult:
                 returncode = 0
                 stdout = "src/devbase/foo.py\nsrc/devbase/bar.py"
             return MockResult()
        # Fallback for other calls (none expected in this path but safe to pass through or error)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = runner.invoke(app, ["--fix"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Checking Changelog" in result.stdout

    content = changelog.read_text()
    assert "[Unreleased] - In Progress" in content
    assert "Modified src/devbase/foo.py" in content
