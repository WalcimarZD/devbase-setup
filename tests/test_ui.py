
import pytest
from io import StringIO

from devbase.legacy.ui import UI


def test_ui_print_header(capsys):
    ui = UI(no_color=True)
    ui.print_header("Test Header")
    captured = capsys.readouterr()
    assert "Test Header" in captured.out
    assert "===" in captured.out


def test_ui_print_step_ok(capsys):
    ui = UI(no_color=True)
    # Using specific status to check prefix
    ui.print_step("Success", "OK")
    captured = capsys.readouterr()
    assert "[+]" in captured.out
    assert "Success" in captured.out


def test_ui_print_step_warn(capsys):
    ui = UI(no_color=True)
    ui.print_step("Warning", "WARN")
    captured = capsys.readouterr()
    assert "[!]" in captured.out
    assert "Warning" in captured.out


def test_ui_color_output(monkeypatch, capsys):
    # Force isatty to True to test color codes
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    
    ui = UI(no_color=False)
    ui.print_step("Colored", "OK")
    
    captured = capsys.readouterr()
    # Check for ANSI escape code for Green (OK)
    # \033[92m is standard Green
    assert "\033[92m" in captured.out
    assert "Colored" in captured.out
