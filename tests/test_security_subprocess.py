import subprocess
import shutil
from pathlib import Path
from unittest import mock
import pytest
from typer.testing import CliRunner

from devbase.commands.pkm import app as pkm_app
from devbase.commands.docs import app as docs_app
from devbase.commands.quick import app as quick_app
from devbase.utils.vscode import open_in_vscode
from devbase.services.project_setup import get_project_setup

runner = CliRunner()

@pytest.fixture
def mock_subprocess():
    with mock.patch("subprocess.run") as m:
        yield m

@pytest.fixture
def mock_shutil_which():
    with mock.patch("shutil.which") as m:
        m.return_value = "/usr/bin/code"
        yield m

@pytest.fixture
def mock_context(tmp_path):
    # Mock context obj for Typer commands
    return {"root": tmp_path}

def test_pkm_journal_safe_open(mock_subprocess, mock_shutil_which, mock_context, tmp_path):
    result = runner.invoke(pkm_app, ["journal"], obj=mock_context)

    assert result.exit_code == 0
    assert mock_subprocess.called

    args, kwargs = mock_subprocess.call_args_list[-1]
    cmd = args[0]

    assert isinstance(cmd, list)
    assert cmd[0] == "code"
    assert cmd[1] == "--"
    assert "weekly-" in cmd[2]
    assert kwargs.get("shell") is not True

def test_pkm_icebox_safe_open(mock_subprocess, mock_shutil_which, mock_context, tmp_path):
    # Create icebox file
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True)
    icebox_path.write_text("# Icebox")

    result = runner.invoke(pkm_app, ["icebox"], obj=mock_context)

    assert result.exit_code == 0
    assert mock_subprocess.called

    args, kwargs = mock_subprocess.call_args_list[-1]
    cmd = args[0]

    assert isinstance(cmd, list)
    assert cmd[0] == "code"
    assert cmd[1] == "--"
    assert "icebox.md" in cmd[2]
    assert kwargs.get("shell") is not True

def test_quick_note_safe_open(mock_subprocess, mock_shutil_which, mock_context, tmp_path):
    result = runner.invoke(quick_app, ["note", "My Note", "--edit"], obj=mock_context)

    assert result.exit_code == 0
    assert mock_subprocess.called

    args, kwargs = mock_subprocess.call_args_list[-1]
    cmd = args[0]

    assert isinstance(cmd, list)
    assert cmd[0] == "code"
    assert cmd[1] == "--"
    assert kwargs.get("shell") is not True

def test_vscode_open_safe(mock_subprocess, mock_shutil_which, tmp_path):
    target = tmp_path / "project"
    open_in_vscode(target)

    args, kwargs = mock_subprocess.call_args
    cmd = args[0]

    assert isinstance(cmd, list)
    assert cmd[0] == "code"
    assert cmd[1] == "--"
    assert str(target) == cmd[2]

def test_project_setup_open_ide_safe(mock_subprocess, mock_shutil_which, tmp_path):
    setup = get_project_setup(tmp_path)
    setup._open_ide(tmp_path / "project")

    args, kwargs = mock_subprocess.call_args
    cmd = args[0]

    assert isinstance(cmd, list)
    assert cmd[0] == "code"
    assert cmd[1] == "--"
    assert str(tmp_path / "project") == cmd[2]
