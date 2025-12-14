import sys
from pathlib import Path
import pytest

# Ensure local modules/python is importable during tests
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "modules" / "python"))

from filesystem import FileSystem  # noqa: E402


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
    assert content.endswith("\n")
    assert "hello world" in content
