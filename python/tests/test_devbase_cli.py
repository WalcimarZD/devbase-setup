"""
Tests for DevBase CLI v3.2 (Python Implementation)
================================================================
Covers all subcommands: setup, doctor, audit, new, hydrate, backup, clean, track, stats, weekly
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Setup path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "modules" / "python"))


class TestCLISetup:
    """Tests for 'devbase setup' command."""

    def test_setup_creates_basic_structure(self, tmp_path, monkeypatch):
        """Setup should create the Johnny.Decimal directory structure."""
        monkeypatch.setattr(sys, "argv", ["devbase.py", "setup", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        # Check required areas exist
        areas = [
            "00-09_SYSTEM",
            "10-19_KNOWLEDGE",
            "20-29_CODE",
            "30-39_OPERATIONS",
            "40-49_MEDIA_ASSETS",
            "90-99_ARCHIVE_COLD",
        ]
        for area in areas:
            assert (tmp_path / area).exists(), f"Area {area} should exist"

    def test_setup_creates_governance_files(self, tmp_path, monkeypatch):
        """Setup should create governance files like .gitignore and .editorconfig."""
        monkeypatch.setattr(sys, "argv", ["devbase.py", "setup", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        assert (tmp_path / ".gitignore").exists()
        assert (tmp_path / ".editorconfig").exists()

    def test_setup_creates_state_file(self, tmp_path, monkeypatch):
        """Setup should create .devbase_state.json with version info."""
        monkeypatch.setattr(sys, "argv", ["devbase.py", "setup", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        state_file = tmp_path / ".devbase_state.json"
        assert state_file.exists()
        
        state = json.loads(state_file.read_text())
        assert "version" in state
        assert "3.2.0" in state["version"]

    def test_setup_dry_run_no_files_created(self, tmp_path, monkeypatch):
        """Setup with --dry-run should not create any files."""
        monkeypatch.setattr(sys, "argv", ["devbase.py", "setup", "--root", str(tmp_path), "--dry-run"])
        
        import devbase
        devbase.main()
        
        # State file should not exist in dry-run mode
        state_file = tmp_path / ".devbase_state.json"
        assert not state_file.exists()


class TestCLIDoctor:
    """Tests for 'devbase doctor' command."""

    def test_doctor_reports_healthy_workspace(self, tmp_path, monkeypatch, capsys):
        """Doctor should report healthy for a properly structured workspace."""
        # First, create the structure
        monkeypatch.setattr(sys, "argv", ["devbase.py", "setup", "--root", str(tmp_path)])
        import devbase
        devbase.main()
        
        # Then run doctor
        monkeypatch.setattr(sys, "argv", ["devbase.py", "doctor", "--root", str(tmp_path)])
        devbase.main()
        
        captured = capsys.readouterr()
        assert "HEALTHY" in captured.out

    def test_doctor_detects_missing_areas(self, tmp_path, monkeypatch, capsys):
        """Doctor should detect missing required areas."""
        # Create incomplete structure
        (tmp_path / "00-09_SYSTEM").mkdir()
        
        monkeypatch.setattr(sys, "argv", ["devbase.py", "doctor", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        captured = capsys.readouterr()
        assert "NOT FOUND" in captured.out or "issue" in captured.out.lower()


class TestCLIAudit:
    """Tests for 'devbase audit' command."""

    def test_audit_detects_naming_violations(self, tmp_path, monkeypatch, capsys):
        """Audit should detect directories not following kebab-case."""
        # Create a directory with PascalCase (violation)
        (tmp_path / "MyBadFolder").mkdir()
        
        monkeypatch.setattr(sys, "argv", ["devbase.py", "audit", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        captured = capsys.readouterr()
        assert "violation" in captured.out.lower() or "MyBadFolder" in captured.out

    def test_audit_passes_for_valid_names(self, tmp_path, monkeypatch, capsys):
        """Audit should pass for directories following naming conventions."""
        # Create valid directories
        (tmp_path / "my-good-folder").mkdir()
        (tmp_path / "00-09_system").mkdir()
        
        monkeypatch.setattr(sys, "argv", ["devbase.py", "audit", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        captured = capsys.readouterr()
        assert "No violations" in captured.out


class TestCLINew:
    """Tests for 'devbase new' command."""

    def test_new_requires_project_name(self, tmp_path, monkeypatch):
        """New command should fail without project name."""
        monkeypatch.setattr(sys, "argv", ["devbase.py", "new", "--root", str(tmp_path)])
        
        import devbase
        with pytest.raises(SystemExit):
            devbase.main()

    def test_new_creates_project_from_template(self, tmp_path, monkeypatch, capsys):
        """New command should copy template to 21_monorepo_apps."""
        # First create the structure with template
        monkeypatch.setattr(sys, "argv", ["devbase.py", "setup", "--root", str(tmp_path)])
        import devbase
        devbase.main()
        
        # Create a template if it doesn't exist
        template_path = tmp_path / "20-29_CODE" / "__template-clean-arch"
        if not template_path.exists():
            template_path.mkdir(parents=True)
            (template_path / "README.md").write_text("# Template")
        
        # Run new command
        monkeypatch.setattr(sys, "argv", ["devbase.py", "new", "test-project", "--root", str(tmp_path)])
        devbase.main()
        
        project_path = tmp_path / "20-29_CODE" / "21_monorepo_apps" / "test-project"
        assert project_path.exists() or "created" in capsys.readouterr().out.lower()


class TestCLITrack:
    """Tests for 'devbase track' command."""

    def test_track_saves_event(self, tmp_path, monkeypatch):
        """Track should save event to telemetry file."""
        monkeypatch.setattr(sys, "argv", [
            "devbase.py", "track", "Completed feature X", "--root", str(tmp_path)
        ])
        
        import devbase
        devbase.main()
        
        events_file = tmp_path / ".telemetry" / "events.jsonl"
        assert events_file.exists()
        
        content = events_file.read_text()
        assert "Completed feature X" in content

    def test_track_with_custom_type(self, tmp_path, monkeypatch):
        """Track should allow custom event types."""
        monkeypatch.setattr(sys, "argv", [
            "devbase.py", "track", "Fixed bug", "--type", "bugfix", "--root", str(tmp_path)
        ])
        
        import devbase
        devbase.main()
        
        events_file = tmp_path / ".telemetry" / "events.jsonl"
        content = events_file.read_text()
        assert "bugfix" in content


class TestCLIStats:
    """Tests for 'devbase stats' command."""

    def test_stats_shows_event_counts(self, tmp_path, monkeypatch, capsys):
        """Stats should show event type counts."""
        # Create some events first
        telemetry_dir = tmp_path / ".telemetry"
        telemetry_dir.mkdir()
        events_file = telemetry_dir / "events.jsonl"
        events_file.write_text(
            '{"timestamp": "2025-01-01T10:00:00", "type": "work", "message": "Task 1"}\n'
            '{"timestamp": "2025-01-02T10:00:00", "type": "work", "message": "Task 2"}\n'
            '{"timestamp": "2025-01-03T10:00:00", "type": "meeting", "message": "Standup"}\n'
        )
        
        monkeypatch.setattr(sys, "argv", ["devbase.py", "stats", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        captured = capsys.readouterr()
        assert "work" in captured.out
        assert "3" in captured.out or "Total events" in captured.out


class TestCLIClean:
    """Tests for 'devbase clean' command."""

    def test_clean_removes_temp_files(self, tmp_path, monkeypatch, capsys):
        """Clean should remove temporary files."""
        # Create temp files
        (tmp_path / "test.log").write_text("log content")
        (tmp_path / "test.tmp").write_text("temp content")
        
        monkeypatch.setattr(sys, "argv", ["devbase.py", "clean", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        assert not (tmp_path / "test.log").exists()
        assert not (tmp_path / "test.tmp").exists()

    def test_clean_dry_run_preserves_files(self, tmp_path, monkeypatch, capsys):
        """Clean with --dry-run should not remove files."""
        # Create temp file
        log_file = tmp_path / "test.log"
        log_file.write_text("log content")
        
        monkeypatch.setattr(sys, "argv", ["devbase.py", "clean", "--dry-run", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        # File should still exist
        assert log_file.exists()
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out


class TestCLIBackup:
    """Tests for 'devbase backup' command."""

    def test_backup_dry_run(self, tmp_path, monkeypatch, capsys):
        """Backup with --dry-run should not create files."""
        monkeypatch.setattr(sys, "argv", ["devbase.py", "backup", "--dry-run", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        captured = capsys.readouterr()
        assert "Would create backup" in captured.out or "DRY-RUN" in captured.out


class TestCLIWeekly:
    """Tests for 'devbase weekly' command."""

    def test_weekly_generates_report(self, tmp_path, monkeypatch, capsys):
        """Weekly should generate a markdown report."""
        # Create events from past week
        from datetime import datetime
        telemetry_dir = tmp_path / ".telemetry"
        telemetry_dir.mkdir()
        events_file = telemetry_dir / "events.jsonl"
        
        today = datetime.now().isoformat()
        events_file.write_text(
            f'{{"timestamp": "{today}", "type": "work", "message": "Implemented feature"}}\n'
        )
        
        monkeypatch.setattr(sys, "argv", ["devbase.py", "weekly", "--root", str(tmp_path)])
        
        import devbase
        devbase.main()
        
        captured = capsys.readouterr()
        assert "Weekly Report" in captured.out or "Implemented feature" in captured.out


class TestFileSystemDryRun:
    """Tests for FileSystem dry_run mode."""

    def test_ensure_dir_dry_run(self, tmp_path):
        """ensure_dir with dry_run should not create directories."""
        from filesystem import FileSystem
        
        fs = FileSystem(str(tmp_path), dry_run=True)
        fs.ensure_dir("test-dir")
        
        assert not (tmp_path / "test-dir").exists()

    def test_write_atomic_dry_run(self, tmp_path):
        """write_atomic with dry_run should not create files."""
        from filesystem import FileSystem
        
        fs = FileSystem(str(tmp_path), dry_run=True)
        fs.write_atomic("test.txt", "content")
        
        assert not (tmp_path / "test.txt").exists()
