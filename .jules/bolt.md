# Bolt's Journal

## 2024-05-22 - Incremental Indexing Pattern
**Learning:** Checking file modification times against a database index before processing avoids expensive I/O and parsing (Frontmatter/Markdown) for unchanged files. This turns O(N) operations into O(N_changed) for subsequent runs.
**Action:** Apply this "stat-first" pattern to any file synchronization or indexing task.

## 2024-05-22 - Pathlib Instantiation Overhead
**Learning:** Instantiating `pathlib.Path` objects inside a tight loop (like recursive directory scanning) adds significant overhead compared to raw string manipulation. For 10,000 files, switching to `os.path.splitext` for extension checking reduced scan time from ~2.9s to ~1.0s (3x speedup).
**Action:** When filtering large lists of files, use string methods (`endswith`, `os.path.splitext`) first, and only instantiate `Path` objects for the matches that will be yielded.

## 2024-05-22 - DuckDB MinMax Indexes
**Learning:** DuckDB automatically maintains MinMax indexes on row groups. For time-series data inserted in roughly chronological order, these implicit indexes are often as effective as explicit B-Tree/ART indexes for range queries, rendering explicit indexing on timestamp columns largely redundant for scan performance on sorted data.
**Action:** Before adding explicit indexes in DuckDB, benchmark against the implicit MinMax behavior, especially for append-only time-series data.

## 2025-05-22 - Single-Pass Content & Metadata Scan
**Learning:** Using `frontmatter.load(path)` internally opens and reads the file. If you also need the file content (e.g., for link extraction), reading it once via `path.read_text()` and then using `frontmatter.loads(content)` avoids a redundant I/O operation.
**Action:** Always prefer `read_text()` + `loads()` over `load()` when the content body is needed for further processing.
