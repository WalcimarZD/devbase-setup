"""
Tests for AI Security and Pipeline
==================================
Integration tests for the AI pipeline including:
- Security Enforcer (Persistence)
- Sanitizer (4-Layers)
- PKM New Command -> Task Queue

Author: DevBase Team
Version: 5.1.0
"""
import json
import pytest
from pathlib import Path
from typer.testing import CliRunner

from devbase.services.security.enforcer import get_enforcer, QuotaExceeded
from devbase.services.security.sanitizer import sanitize_context
from devbase.adapters.storage import duckdb_adapter
from devbase.commands.pkm import app as pkm_app

runner = CliRunner()


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """Setup a clean DuckDB for testing."""
    db_path = tmp_path / "test.duckdb"

    # Patch get_db_path in adapter
    monkeypatch.setattr("devbase.adapters.storage.duckdb_adapter.get_db_path", lambda: db_path)

    # Initialize connection
    conn = duckdb_adapter.init_connection(db_path)
    duckdb_adapter.init_schema(conn)

    # Force reset connection singleton
    monkeypatch.setattr("devbase.adapters.storage.duckdb_adapter._connection", conn)
    monkeypatch.setattr("devbase.adapters.storage.duckdb_adapter._db_path", db_path)

    yield conn

    conn.close()


@pytest.fixture
def mock_root(tmp_path):
    """Create a mock workspace root."""
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "10-19_KNOWLEDGE" / "10_references").mkdir(parents=True)
    return root


class TestSecurityEnforcer:
    """Integration tests for SecurityEnforcer with DuckDB persistence."""

    def test_quota_tracking_persistence(self, clean_db):
        """Verify quota is tracked and persisted in DuckDB."""
        enforcer = get_enforcer()
        user = "test_user_quota"

        # Reset tracker internal state (since it's a singleton in tests if not careful, but we rely on DB)
        # Actually QuotaTracker reads from DB every time.

        # 1. Initial count should be 0
        assert enforcer.tracker.get_count(user) == 0

        # 2. Record usage
        enforcer.record_usage(user)
        assert enforcer.tracker.get_count(user) == 1

        # 3. Check DB directly
        count = clean_db.execute(
            "SELECT COUNT(*) FROM events WHERE event_type='ai_generation'"
        ).fetchone()[0]
        assert count == 1

        # 4. Check QuotaExceeded
        # Config defaults to 5
        for _ in range(4):
            enforcer.record_usage(user)

        assert enforcer.tracker.get_count(user) == 5

        with pytest.raises(QuotaExceeded):
            enforcer.enforce("some/path", user)


class TestSanitizerIntegration:
    """Verify Sanitizer works as expected in pipeline context."""

    def test_sanitizer_blocks_openai_key(self):
        """Ensure OpenAI keys are redacted."""
        raw = "Draft with sk-1234567890abcdef1234567890abcdef1234567890abcdef"
        context = sanitize_context(raw)

        assert "sk-" not in context.content
        assert "[REDACTED]" in context.content
        assert context.signature is not None

    def test_sanitizer_audit_log(self, clean_db):
        """Ensure sanitization produces an audit log (if hooked up)."""
        # Note: default sanitizer uses print/logging.
        # In production, we'd hook it to duckdb_adapter.log_event.
        # Here we just verify the context object is correct.
        context = sanitize_context("test content")
        assert len(context.signature) == 64


class TestPKMNewPipeline:
    """Test full flow: pkm new -> file created -> task enqueued."""

    def test_new_note_enqueues_task(self, clean_db, mock_root):
        """Verify 'pkm new' creates file and enqueues classify task."""

        # Run command
        # We need to inject the context obj with root
        result = runner.invoke(pkm_app, ["new", "test-note", "--type", "explanation"], obj={"root": mock_root})

        assert result.exit_code == 0
        assert "Created note" in result.stdout
        assert "queued AI classification" in result.stdout

        # 1. Verify file existence
        expected_file = mock_root / "10-19_KNOWLEDGE" / "10_references" / "test-note.md"
        assert expected_file.exists()
        content = expected_file.read_text()
        assert "type: explanation" in content

        # 2. Verify task in DB
        task = clean_db.execute(
            "SELECT task_type, payload, status FROM ai_task_queue WHERE task_type='classify'"
        ).fetchone()

        assert task is not None
        assert task[0] == "classify"
        payload = json.loads(task[1])
        assert payload["path"] == str(expected_file)
        assert task[2] == "pending"
