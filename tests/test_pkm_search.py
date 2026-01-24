from unittest.mock import patch

from typer.testing import CliRunner

from devbase.main import app

runner = CliRunner()

def test_pkm_find_output_format(tmp_path):
    """
    Test that 'pkm find' outputs results.
    We initially expect the sequential format, then we will update this test
    to expect the Table format.
    """
    # Mock results
    mock_results = [
        {
            "path": "10-19_KNOWLEDGE/10_references/test.md",
            "title": "Test Note",
            "type": "reference",
            "word_count": 100,
            "content_preview": "This is a preview of the content."
        },
        {
            "path": "10-19_KNOWLEDGE/11_projects/proj.md",
            "title": "Project Note",
            "type": "project",
            "word_count": 50,
            "content_preview": None
        }
    ]

    # Mock KnowledgeDB
    with patch("devbase.services.knowledge_db.KnowledgeDB") as MockDB:
        # Setup the mock instance
        mock_instance = MockDB.return_value
        mock_instance.get_stats.return_value = {"total_notes": 10} # Prevent reindexing
        mock_instance.search.return_value = mock_results

        # Run command
        # We need to pass --root because main callback requires it or detects it
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "find", "query"])

        print(result.stdout) # For debugging if needed

        assert result.exit_code == 0

        # Verify output format (Table)
        assert "Found 2 note(s):" in result.stdout
        assert "Title" in result.stdout
        assert "Type" in result.stdout
        assert "Words" in result.stdout
        assert "Path" in result.stdout
        assert "Preview" in result.stdout

        # Check rows
        assert "Test Note" in result.stdout
        assert "reference" in result.stdout
        assert "100" in result.stdout
        assert "This is a preview" in result.stdout
