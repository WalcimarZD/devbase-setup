"""
Tests for Knowledge Graph Service
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from devbase.services.knowledge_graph import KnowledgeGraph

@pytest.fixture
def temp_kb(tmp_path):
    """Creates a temporary knowledge base structure."""
    kb_root = tmp_path / "workspace"
    kb_root.mkdir()

    (kb_root / "10-19_KNOWLEDGE" / "10_resources").mkdir(parents=True)
    (kb_root / "10-19_KNOWLEDGE" / "11_projects").mkdir(parents=True)
    (kb_root / "90-99_ARCHIVE_COLD").mkdir(parents=True)

    # Note A (Resources) -> Links to Note B
    (kb_root / "10-19_KNOWLEDGE" / "10_resources" / "note_a.md").write_text(
        "---\ntitle: Note A\n---\nLink to [[Note B]]", encoding="utf-8"
    )

    # Note B (Resources) -> Links to Note C (standard link)
    (kb_root / "10-19_KNOWLEDGE" / "10_resources" / "note_b.md").write_text(
        "---\ntitle: Note B\n---\nLink to [Note C](../11_projects/note_c.md)", encoding="utf-8"
    )

    # Note C (Projects) -> No links
    (kb_root / "10-19_KNOWLEDGE" / "11_projects" / "note_c.md").write_text(
        "---\ntitle: Note C\n---\nJust content", encoding="utf-8"
    )

    # Archive Note -> Links to Note A
    (kb_root / "90-99_ARCHIVE_COLD" / "archive.md").write_text(
        "---\ntitle: Archive\n---\nOld link to [[Note A]]", encoding="utf-8"
    )

    return kb_root

def test_scan_active_scope(temp_kb):
    """Test scanning only active knowledge base."""
    kg = KnowledgeGraph(temp_kb, include_archive=False)
    stats = kg.scan()

    assert stats["files"] == 3
    assert stats["nodes"] == 3
    assert stats["links"] == 2  # A->B, B->C

    # Verify nodes
    assert kg.graph.has_node("10-19_KNOWLEDGE/10_resources/note_a.md")
    assert kg.graph.has_node("10-19_KNOWLEDGE/10_resources/note_b.md")
    assert kg.graph.has_node("10-19_KNOWLEDGE/11_projects/note_c.md")
    assert not kg.graph.has_node("90-99_ARCHIVE_COLD/archive.md")

def test_scan_global_scope(temp_kb):
    """Test scanning with archive included."""
    kg = KnowledgeGraph(temp_kb, include_archive=True)
    stats = kg.scan()

    assert stats["files"] == 4
    assert stats["nodes"] == 4
    assert stats["links"] == 3  # Active links + Archive->A

    assert kg.graph.has_node("90-99_ARCHIVE_COLD/archive.md")

def test_link_parsing(temp_kb):
    """Verify correct link parsing (Wiki and Markdown)."""
    kg = KnowledgeGraph(temp_kb)
    kg.scan()

    # Wiki link: [[Note B]] from Note A
    assert kg.graph.has_edge(
        "10-19_KNOWLEDGE/10_resources/note_a.md",
        "10-19_KNOWLEDGE/10_resources/note_b.md"
    )

    # Markdown link: [Note C](../11_projects/note_c.md) from Note B
    assert kg.graph.has_edge(
        "10-19_KNOWLEDGE/10_resources/note_b.md",
        "10-19_KNOWLEDGE/11_projects/note_c.md"
    )

def test_metrics(temp_kb):
    """Test graph analysis metrics."""
    kg = KnowledgeGraph(temp_kb)
    kg.scan()

    # Hubs: Note B has 1 out, 1 in (degree 2 if undirected, but DiGraph counts in+out for degree?)
    # networkx degree on DiGraph is in_degree + out_degree
    # A: out=1, in=0 -> 1
    # B: out=1, in=1 -> 2
    # C: out=0, in=1 -> 1

    hubs = kg.get_hub_notes()
    hub_notes = [n[0] for n in hubs]
    assert "10-19_KNOWLEDGE/10_resources/note_b.md" == hub_notes[0]

    # Add orphan
    (temp_kb / "10-19_KNOWLEDGE" / "orphan.md").write_text("Orphan", encoding="utf-8")
    kg.scan()
    orphans = kg.get_orphan_notes()
    assert "10-19_KNOWLEDGE/orphan.md" in orphans

def test_get_links(temp_kb):
    """Test retrieving in/out links for a specific note."""
    kg = KnowledgeGraph(temp_kb)
    kg.scan()

    # Outlinks
    outlinks = kg.get_outlinks("10-19_KNOWLEDGE/10_resources/note_a.md")
    assert len(outlinks) == 1
    assert "10-19_KNOWLEDGE/10_resources/note_b.md" in outlinks

    # Backlinks
    backlinks = kg.get_backlinks("10-19_KNOWLEDGE/10_resources/note_b.md")
    assert len(backlinks) == 1
    assert "10-19_KNOWLEDGE/10_resources/note_a.md" in backlinks

@patch("networkx.drawing.nx_pydot.write_dot")
def test_export_dot(mock_write, temp_kb):
    """Test DOT export calls networkx."""
    kg = KnowledgeGraph(temp_kb)
    kg.scan()

    output = temp_kb / "graph.dot"
    kg.export_to_graphviz(output)

    mock_write.assert_called_once()

def test_export_pyvis_missing_dep(temp_kb):
    """Test PyVis missing dependency error."""
    kg = KnowledgeGraph(temp_kb)

    # Simulate missing pyvis
    with patch.dict("sys.modules", {"pyvis.network": None}):
        with pytest.raises(ImportError):
            kg.export_to_pyvis(temp_kb / "graph.html")
