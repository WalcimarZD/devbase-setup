"""
Knowledge Graph Service
========================
Service for building and analyzing the knowledge graph from Markdown files.
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple

import frontmatter
import networkx as nx

from devbase.utils.filesystem import scan_directory


class KnowledgeGraph:
    """
    Manages the knowledge graph built from Markdown notes.
    """

    def __init__(self, root: Path, include_archive: bool = False):
        self.root = root
        self.include_archive = include_archive
        self.graph = nx.DiGraph()
        self.file_map: Dict[str, Path] = {}  # Map stem to path for Wiki-link resolution
        self._scanned = False

    def _get_search_paths(self) -> List[Path]:
        """Get the list of paths to scan based on configuration."""
        paths = [self.root / "10-19_KNOWLEDGE"]
        if self.include_archive:
            paths.append(self.root / "90-99_ARCHIVE_COLD")
        return [p for p in paths if p.exists()]

    def scan(self) -> Dict[str, int]:
        """
        Scans the knowledge base and builds the graph.

        Returns:
            Dict with scan statistics (files, nodes, links, errors).
        """
        self.graph.clear()
        self.file_map.clear()

        search_paths = self._get_search_paths()
        files: List[Path] = []
        errors = 0

        # Regex for Markdown links: [text](link)
        # We ignore external links (http/https)
        md_link_pattern = re.compile(r"\[.*?\]\((.*?)\)")

        # Regex for Wiki-links: [[link]] or [[link|text]]
        wiki_link_pattern = re.compile(r"\[\[(.*?)\]\]")

        # Temporary storage for links to resolve after all nodes are known
        # List of (source_rel, file_path, [list_of_raw_links])
        # Storing raw links instead of content saves memory
        pending_links: List[Tuple[str, Path, List[str], List[str]]] = []

        # 1. Single Pass: Read content once, parse frontmatter, extract links
        for path in search_paths:
            # Optimization: Use scan_directory for centralized pruning
            # Replaces manual path.walk() to ensure consistency with performance guidelines
            for file_path in scan_directory(path, extensions={'.md'}):
                # Store relative path from workspace root for portability
                rel_path = file_path.relative_to(self.root).as_posix()

                # Optimization (Bolt): Read file ONCE.
                # Previous implementation read file twice: once for frontmatter.load(), once for read_text().
                content = ""
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception:
                    # If read fails, we can't do anything with this file
                    errors += 1
                    continue

                try:
                    post = frontmatter.loads(content)
                    title = post.get("title", file_path.stem)
                    tags = post.get("tags", [])
                except Exception:
                    # If frontmatter parse fails, we still want to index the content links
                    errors += 1
                    title = file_path.stem
                    tags = []

                # Add node
                self.graph.add_node(
                    rel_path,
                    title=title,
                    tags=tags,
                    path=str(file_path)
                )

                # Map identifiers for Wiki-link resolution
                # 1. Filename stem (e.g. "note_a" -> "path/to/note_a.md")
                self.file_map[file_path.stem.lower()] = rel_path
                # 2. Title (e.g. "Note A" -> "path/to/note_a.md")
                if title:
                    self.file_map[title.lower()] = rel_path

                files.append(file_path)

                # Extract links immediately if we have content
                if content:
                    raw_md_links = md_link_pattern.findall(content)
                    raw_wiki_links = wiki_link_pattern.findall(content)
                    pending_links.append((rel_path, file_path, raw_md_links, raw_wiki_links))

        # 2. Link Resolution Pass: Resolve links using the built file_map
        links_count = 0

        for source_rel, file_path, md_links, wiki_links in pending_links:
            # Process Markdown links
            for match in md_links:
                target_link = match.split(" ")[0] # handle [text](link "title")

                if target_link.startswith(("http://", "https://", "mailto:")):
                    continue

                # Resolve relative link
                try:
                    # Resolve from current file directory
                    target_path = (file_path.parent / target_link).resolve()
                    if target_path.is_relative_to(self.root):
                        target_rel = target_path.relative_to(self.root).as_posix()

                        # Check if node exists (valid internal link)
                        if self.graph.has_node(target_rel):
                            self.graph.add_edge(source_rel, target_rel)
                            links_count += 1
                except (ValueError, RuntimeError):
                    continue

            # Process Wiki-links
            for match in wiki_links:
                # Handle [[Link|Text]]
                target_name = match.split("|")[0].strip().lower()

                # Try to find target in map
                if target_name in self.file_map:
                    target_rel = self.file_map[target_name]
                    if source_rel != target_rel: # Avoid self-loops
                        self.graph.add_edge(source_rel, target_rel)
                        links_count += 1

        self._scanned = True
        return {
            "files": len(files),
            "nodes": self.graph.number_of_nodes(),
            "links": links_count,
            "errors": errors
        }

    def get_hub_notes(self, n: int = 5) -> List[Tuple[str, int]]:
        """Returns the top N notes with most connections (degree)."""
        if not self.graph:
            return []
        degrees = dict(self.graph.degree())
        return sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:n]

    def get_orphan_notes(self) -> List[str]:
        """Returns list of notes with no connections."""
        if not self.graph:
            return []
        return [n for n, d in self.graph.degree() if d == 0]

    def get_outlinks(self, note_path: str) -> List[str]:
        """Returns list of notes referenced by the given note."""
        # Normalize path
        if str(self.root) in note_path:
             path_obj = Path(note_path)
             if path_obj.is_absolute():
                 try:
                    note_path = path_obj.relative_to(self.root).as_posix()
                 except ValueError:
                    pass

        if note_path in self.graph:
            return list(self.graph.successors(note_path))
        return []

    def get_backlinks(self, note_path: str) -> List[str]:
        """Returns list of notes that reference the given note."""
         # Normalize path
        if str(self.root) in note_path:
             path_obj = Path(note_path)
             if path_obj.is_absolute():
                 try:
                    note_path = path_obj.relative_to(self.root).as_posix()
                 except ValueError:
                    pass

        if note_path in self.graph:
            return list(self.graph.predecessors(note_path))
        return []

    def export_to_graphviz(self, output_path: Path) -> None:
        """Exports the graph to a DOT file."""
        try:
            from networkx.drawing.nx_pydot import write_dot
            write_dot(self.graph, str(output_path))
        except ImportError:
            raise ImportError("Graphviz support requires 'pydot'. Install with 'pip install pydot'.")

    def export_to_pyvis(self, output_path: Path) -> None:
        """Generates an interactive HTML graph using PyVis."""
        try:
            from pyvis.network import Network
        except ImportError:
            raise ImportError("PyVis is not installed. Install with 'pip install devbase[viz]'.")

        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", select_menu=True)

        # Convert NetworkX graph to PyVis
        # We need to ensure node attributes are JSON serializable
        # and maybe style them
        for node in self.graph.nodes(data=True):
            node_id = node[0]
            attrs = node[1]
            label = attrs.get("title", Path(node_id).stem)

            # Size based on degree
            degree = self.graph.degree(node_id)
            size = 10 + (degree * 2)

            net.add_node(node_id, label=label, title=f"{label}\n({node_id})", size=size, color="#4aa3df")

        for source, target in self.graph.edges():
            net.add_edge(source, target, color="#ffffff")

        # Set physics layout
        net.force_atlas_2based()

        net.save_graph(str(output_path))
