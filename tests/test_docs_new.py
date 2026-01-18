from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_docs_new_interactive(tmp_path):
    """Test that docs new prompts for missing arguments."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Create required template (since command fails if template missing)
    template_dir = tmp_path / "00-09_SYSTEM/07_documentation/templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "template_decision.md").write_text("# [Título da Decisão/Plano]\nDate: [DATA_ATUAL]")

    # Run interactive command
    # Input: "decision" (type) -> "My Decision" (title)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "docs", "new"],
        input="decision\nMy Decision\n"
    )

    # Verify success
    assert result.exit_code == 0
    assert "Created:" in result.stdout
    assert "decision" in result.stdout

    # Verify file created
    dest_dir = tmp_path / "00-09_SYSTEM/07_documentation/decisions"
    assert any("my-decision" in f.name for f in dest_dir.iterdir())
