
from unittest.mock import patch

import pytest

from devbase.services.knowledge_graph import KnowledgeGraph


@pytest.fixture
def temp_kb(tmp_path):
    """Creates a temporary knowledge base structure."""
    kb_root = tmp_path / "workspace"
    kb_root.mkdir()

    (kb_root / "10-19_KNOWLEDGE" / "10_resources").mkdir(parents=True)

    # Create 3 files
    for i in range(3):
        (kb_root / "10-19_KNOWLEDGE" / "10_resources" / f"note_{i}.md").write_text(
            f"---\ntitle: Note {i}\n---\nLink to [[Note {i+1}]]", encoding="utf-8"
        )

    return kb_root

def test_io_count(temp_kb):
    kg = KnowledgeGraph(temp_kb, include_archive=False)

    # Mock Path.read_text to count calls
    # We also need to let it actually read the file so the logic continues,
    # or just return dummy content.
    # Since we need to verify I/O count, we can just spy on it.

    # However, read_text is a method on the INSTANCE.
    # We can patch pathlib.Path.read_text.

    with patch("pathlib.Path.read_text", autospec=True) as mock_read_text, \
         patch("builtins.open", side_effect=open) as mock_open:

        # We need mock_read_text to actually work or return something valid
        # so the code doesn't crash or skip.
        # But wait, if we mock read_text, the original read_text won't be called,
        # so open() won't be called by read_text.

        # So:
        # 1. frontmatter.load -> calls open() -> caught by mock_open
        # 2. read_text -> caught by mock_read_text (does NOT call open)

        # So total operations = mock_open calls (from frontmatter) + mock_read_text calls.

        # We need read_text to return valid content so regex doesn't fail (though regex failing is fine, we just count calls).
        mock_read_text.return_value = "---\ntitle: Foo\n---\n[[Link]]"

        kg.scan()

        # Count frontmatter opens
        fm_open_count = 0
        for c in mock_open.mock_calls:
            args = c.args
            if args:
                path = str(args[0])
                if path.endswith(".md") and "workspace" in path:
                    fm_open_count += 1

        # Count read_text calls
        read_text_count = 0
        for c in mock_read_text.mock_calls:
            # First arg is 'self' (the Path object)
            args = c.args
            if args:
                path = str(args[0])
                if path.endswith(".md") and "workspace" in path:
                    read_text_count += 1

        print(f"Frontmatter opens: {fm_open_count}")
        print(f"read_text calls: {read_text_count}")
        total = fm_open_count + read_text_count
        print(f"Total IO ops: {total}")

        assert total == 3, f"Expected 3 ops (1 per file), got {total}"
