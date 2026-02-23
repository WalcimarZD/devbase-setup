"""Pytest conftest — shared fixtures for DevBase test suite."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def devbase_workspace(tmp_path: Path) -> Path:
    """Create a minimal valid DevBase workspace for testing.

    Creates the required Johnny.Decimal area folders and a valid
    .devbase_state.json so commands don't trigger first-run setup.
    """
    import json
    from datetime import datetime

    areas = [
        "00-09_SYSTEM/00_inbox",
        "00-09_SYSTEM/01_dotfiles",
        "00-09_SYSTEM/05_templates",
        "00-09_SYSTEM/07_documentation",
        "10-19_KNOWLEDGE/11_public_garden",
        "10-19_KNOWLEDGE/12_private_vault",
        "20-29_CODE/21_monorepo_apps",
        "20-29_CODE/22_worktrees",
        "30-39_OPERATIONS/31_backups",
        "40-49_MEDIA_ASSETS",
        "90-99_ARCHIVE_COLD",
    ]
    for area in areas:
        (tmp_path / area).mkdir(parents=True, exist_ok=True)

    state = {
        "version": "5.1.0",
        "policyVersion": "5.0",
        "lastUpdate": datetime.now().isoformat(),
        "installedAt": datetime.now().isoformat(),
        "migrations": [],
    }
    (tmp_path / ".devbase_state.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )

    return tmp_path


@pytest.fixture
def mock_ai_provider() -> MagicMock:
    """Pre-configured mock AI provider (Ports & Adapters interface).

    Returns a MagicMock implementing the LLMProvider ABC contract:
    - complete() -> str
    - validate_connection() -> bool
    """
    provider = MagicMock()
    provider.complete.return_value = "Mocked AI response"
    provider.validate_connection.return_value = True
    return provider
