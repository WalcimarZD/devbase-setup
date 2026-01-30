import pytest
from pathlib import Path
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_audit_run_detects_undocumented_command(tmp_path):
    # Mock repo structure
    src_dir = tmp_path / "src/devbase/commands"
    src_dir.mkdir(parents=True)

    # Create a dummy command
    (src_dir / "dummy.py").write_text("""
import typer
app = typer.Typer()

@app.command("foo")
def foo(flag: bool = typer.Option(False, "--flag")):
    pass
""")

    # Create empty USAGE-GUIDE.md
    (tmp_path / "USAGE-GUIDE.md").write_text("# Guide\n")

    # Run audit command with --root pointing to tmp_path
    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    assert result.exit_code == 0
    # Should warn about undocumented command
    assert "dummy foo" in result.stdout
    # Note: If command is undocumented, flags are skipped in the report

def test_audit_run_detects_undocumented_flag(tmp_path):
    # Mock repo structure
    src_dir = tmp_path / "src/devbase/commands"
    src_dir.mkdir(parents=True)

    # Create a dummy command
    (src_dir / "dummy.py").write_text("""
import typer
app = typer.Typer()

@app.command("foo")
def foo(flag: bool = typer.Option(False, "--flag")):
    pass
""")

    # Document the command but not the flag
    (tmp_path / "USAGE-GUIDE.md").write_text("# Guide\n\n`devbase dummy foo`\n")

    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    assert result.exit_code == 0
    assert "dummy foo --flag" in result.stdout

def test_audit_fix_updates_usage_guide(tmp_path):
    # Mock repo structure
    src_dir = tmp_path / "src/devbase/commands"
    src_dir.mkdir(parents=True)

    # Create a dummy command
    (src_dir / "dummy.py").write_text("""
import typer
app = typer.Typer()

@app.command("bar")
def bar():
    pass
""")

    guide = tmp_path / "USAGE-GUIDE.md"
    guide.write_text("# Guide\n")

    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run", "--fix"])

    assert result.exit_code == 0
    content = guide.read_text()
    assert "Undocumented Commands" in content
    assert "devbase dummy bar" in content

def test_audit_ignores_documented_commands(tmp_path):
    # Mock repo structure
    src_dir = tmp_path / "src/devbase/commands"
    src_dir.mkdir(parents=True)

    # Create a dummy command
    (src_dir / "documented.py").write_text("""
import typer
app = typer.Typer()

@app.command("baz")
def baz():
    pass
""")

    # Document it in USAGE-GUIDE.md
    (tmp_path / "USAGE-GUIDE.md").write_text("# Guide\n\n`devbase documented baz`\n")

    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    assert result.exit_code == 0
    assert "documented baz" not in result.stdout
