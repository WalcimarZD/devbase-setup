
import shutil
from pathlib import Path
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_ops_backup_ux(tmp_path):
    """Test backup command creates backup and shows success message."""
    # Manual Setup to avoid core setup issues
    (tmp_path / ".devbase_state.json").write_text("{}")
    (tmp_path / "30-39_OPERATIONS" / "31_backups" / "local").mkdir(parents=True)
    (tmp_path / "dummy.txt").write_text("content")

    # Run backup
    result = runner.invoke(app, ["--root", str(tmp_path), "ops", "backup"])

    assert result.exit_code == 0
    assert "Backup created successfully" in result.stdout
    assert "Creating backup..." in result.stdout

    # Verify backup exists
    backup_dir = tmp_path / "30-39_OPERATIONS" / "31_backups" / "local"
    assert backup_dir.exists()
    backups = list(backup_dir.iterdir())
    assert len(backups) == 1
    assert (backups[0] / "dummy.txt").exists()
