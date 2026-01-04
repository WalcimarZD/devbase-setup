
import os
import shutil
import time
from pathlib import Path
import typer
from devbase.commands.operations import clean
from unittest.mock import MagicMock
import tempfile

def create_test_environment(root: Path):
    """Create a test environment with mixed content."""
    # 1. Create files we want to clean (scattered)
    for i in range(100):
        p = root / f"dir_{i}"
        p.mkdir(parents=True, exist_ok=True)
        (p / f"test.log").write_text("log")
        (p / f"temp.tmp").write_text("tmp")

    # 2. Create a HUGE ignored directory (e.g., node_modules)
    # This represents a typical dev environment bottleneck
    ignored = root / "node_modules" / "heavy_lib"
    ignored.mkdir(parents=True, exist_ok=True)

    print("Creating 10,000 files in node_modules (should be ignored)...")
    for i in range(10000):
        (ignored / f"libfile_{i}.js").write_text("const a = 1;")

def benchmark_clean():
    # Setup
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Setting up test environment in {temp_dir}...")
    create_test_environment(temp_dir)
    print("Environment ready.")

    ctx = MagicMock(spec=typer.Context)
    ctx.obj = {"root": temp_dir}

    # Measure
    start_time = time.time()

    try:
        clean(ctx)
    except Exception as e:
        print(f"Error during clean: {e}")
        # Re-raise to ensure benchmark fails on error
        raise e

    end_time = time.time()
    duration = end_time - start_time

    print(f"Time taken: {duration:.4f} seconds")

    # Cleanup
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    benchmark_clean()
