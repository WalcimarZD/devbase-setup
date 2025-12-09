def test_devbase_creates_readme_and_gitignore(tmp_path, monkeypatch):
    # Ensure modules/python is importable (devbase.py expects it)
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "modules" / "python"))

    # Run devbase.main with a temporary root directory
    monkeypatch.setattr(sys, "argv", ["devbase.py", "--root", str(tmp_path)])

    # Import and run
    import devbase

    devbase.main()

    readme = tmp_path / "README.md"
    gitignore = tmp_path / ".gitignore"
    assert readme.exists()
    assert gitignore.exists()
    # Quick content sanity
    assert "DevBase" in readme.read_text(encoding="utf-8")
    assert "12_private_vault/" in gitignore.read_text(encoding="utf-8")
