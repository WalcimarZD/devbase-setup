from pathlib import Path
import pytest

from devbase.utils.filesystem import FileSystem


def test_assert_safe_path_ok(tmp_path):
    fs = FileSystem(str(tmp_path))
    target = tmp_path / "subdir"
    # should not raise
    assert fs.assert_safe_path(target) is True


def test_assert_safe_path_outside_raises(tmp_path):
    fs = FileSystem(str(tmp_path))
    # create a path that resolves outside the root
    outside = tmp_path.joinpath("..", "..", "outside_test").resolve()
    with pytest.raises(ValueError):
        fs.assert_safe_path(outside)



def test_ensure_dir_and_write_atomic(tmp_path):
    fs = FileSystem(str(tmp_path))
    # ensure nested dir is created
    created = fs.ensure_dir("a/b/c")
    assert created.exists()

    # write a file atomically
    fs.write_atomic("a/b/c/hello.txt", "hello world")
    target = Path(tmp_path) / "a" / "b" / "c" / "hello.txt"
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "hello world" in content


class TestFileSystemDryRun:
    """Tests for FileSystem dry_run mode."""

    def test_ensure_dir_dry_run(self, tmp_path):
        """ensure_dir with dry_run should not create directories."""
        fs = FileSystem(str(tmp_path), dry_run=True)
        fs.ensure_dir("test-dir")
        
        assert not (tmp_path / "test-dir").exists()

    def test_write_atomic_dry_run(self, tmp_path):
        """write_atomic with dry_run should not create files."""
        fs = FileSystem(str(tmp_path), dry_run=True)
        fs.write_atomic("test.txt", "content")
        
        assert not (tmp_path / "test.txt").exists()


