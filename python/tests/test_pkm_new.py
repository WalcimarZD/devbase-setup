from typer.testing import CliRunner
from devbase.main import app
from pathlib import Path

runner = CliRunner()

def test_pkm_new_interactive(tmp_path):
    """Test 'pkm new' prompts for type when missing."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Run command without --type, provide input "tutorial"
    # Input simulates user typing "tutorial" and hitting enter (default is reference if empty)
    # We pass "tutorial\n" to select tutorial.
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "pkm", "new", "my-interactive-note"],
        input="tutorial\n"
    )

    assert result.exit_code == 0
    assert "Select note type" in result.stdout
    assert "Created note" in result.stdout

    # Verify file content
    note_path = tmp_path / "10-19_KNOWLEDGE" / "10_references" / "my-interactive-note.md"
    assert note_path.exists()

    content = note_path.read_text()
    assert "type: tutorial" in content

def test_pkm_new_with_arg(tmp_path):
    """Test 'pkm new' works with argument provided (no prompt)."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "pkm", "new", "my-arg-note", "--type", "how-to"]
    )

    assert result.exit_code == 0
    # Should NOT prompt
    assert "Select note type" not in result.stdout

    note_path = tmp_path / "10-19_KNOWLEDGE" / "10_references" / "my-arg-note.md"
    content = note_path.read_text()
    assert "type: how-to" in content
