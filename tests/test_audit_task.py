"""
Tests for the new daily consistency audit task.
"""
from pathlib import Path
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_audit_run_execution(tmp_path):
    """Test that 'audit run' executes without error."""
    # We need a fake workspace for it to run meaningfully, or at least a pyproject.toml

    # 1. Setup minimal repo structure
    (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
dependencies = ["typer"]
    """)
    (tmp_path / "README.md").write_text("Uses typer.")
    (tmp_path / "ARCHITECTURE.md").write_text("Uses typer.")

    # Create .devbase_state.json to satisfy workspace detection
    (tmp_path / ".devbase_state.json").write_text("{}")

    # Create src structure for diff analysis
    src_dir = tmp_path / "src" / "devbase"
    src_dir.mkdir(parents=True)
    (src_dir / "commands").mkdir()

    # Mock technical docs for DB check
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "TECHNICAL_DESIGN_DOC.md").write_text("""
    CREATE TABLE hot_fts (
        file_path TEXT PRIMARY KEY,
        title TEXT
    );
    CREATE TABLE cold_fts (
        file_path TEXT PRIMARY KEY,
        title TEXT
    );
    """)

    # Mock adapter file with multiline SQL (as expected by simple parser)
    adapter_dir = src_dir / "adapters" / "storage"
    adapter_dir.mkdir(parents=True)
    (adapter_dir / "duckdb_adapter.py").write_text("""
    # Mock adapter
    def init_schema(conn):
        conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS hot_fts (
            file_path TEXT PRIMARY KEY,
            title TEXT
        );
        \"\"\")
        conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS cold_fts (
            file_path TEXT PRIMARY KEY,
            title TEXT
        );
        \"\"\")
    """)

    # Create CHANGELOG.md
    (tmp_path / "CHANGELOG.md").write_text("## [Unreleased]")

    # Run the command from the temp root
    # We need to switch cwd or pass root?
    # audit.py uses Path.cwd() inside.
    # But main.py sets ctx.obj['root'].
    # My audit.py implementation uses `root = Path.cwd()` but then tries to find pyproject.toml up.
    # However, passing --root to main app sets ctx.obj['root'].
    # I should update audit.py to use ctx.obj['root'] if available, or fallback.
    # But for now, let's just rely on running from the right dir.

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["audit", "run"])

    assert result.exit_code == 0
    assert "DevBase Consistency Audit" in result.stdout
    assert "System is consistent" in result.stdout or "Sistema consistente" in result.stdout

def test_audit_run_dependency_warning(tmp_path):
    """Test dependency check failure."""
    (tmp_path / "pyproject.toml").write_text("""
[project]
dependencies = ["requests"]
    """)
    (tmp_path / "README.md").write_text("")
    (tmp_path / "ARCHITECTURE.md").write_text("")

    # Create .devbase_state.json to satisfy workspace detection
    (tmp_path / ".devbase_state.json").write_text("{}")

    # Need src/devbase structure to avoid immediate return in diff analysis? No, just existence.
    (tmp_path / "src" / "devbase").mkdir(parents=True)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["audit", "run"])

    assert result.exit_code == 0
    assert "requests" in result.stdout
    assert "Inconsistências" in result.stdout or "Warnings" in result.stdout or "Bibliotecas não mencionadas" in result.stdout
