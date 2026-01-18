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

        Optimization (Bolt):
        - Combined two passes into one loop to avoid reading files twice.
        - Uses regex extraction during the first pass.
        - Resolves links after the loop when all nodes are mapped.
        - Reduces I/O overhead by ~50%.

        Returns:
            Dict with scan statistics (files, nodes, links, errors).
        """
        self.graph.clear()
        self.file_map.clear()

        search_paths = self._get_search_paths()
        files: List[Path] = []
        errors = 0
        links_count = 0

        # Regex for Markdown links: [text](link)
        # We ignore external links (http/https)
        md_link_pattern = re.compile(r"\[.*?\]\((.*?)\)")

        # Regex for Wiki-links: [[link]] or [[link|text]]
        wiki_link_pattern = re.compile(r"\[\[(.*?)\]\]")

        # Temporary storage for links to resolve
        # List of (source_rel, target_string, type, file_path)
        # type: 'md' or 'wiki'
        # For md, target_string is the raw link path
        # For wiki, target_string is the target note name
        raw_links: List[Tuple[str, str, str, Path]] = []

        # 1. Single Pass: Read, Parse, Extract
        for path in search_paths:
            # Optimization: Use scan_directory for centralized pruning
            for file_path in scan_directory(path, extensions={'.md'}):
                # Store relative path from workspace root for portability
                try:
                    rel_path = file_path.relative_to(self.root).as_posix()
                except ValueError:
                    continue

                content_text = ""
                try:
                    # READ ONCE: Read content into memory
                    content_text = file_path.read_text(encoding="utf-8")

                    # Parse Frontmatter from string
                    post = frontmatter.loads(content_text)
                    title = post.get("title", file_path.stem)
                    tags = post.get("tags", [])
                except Exception:
                    errors += 1
                    title = file_path.stem
                    tags = []
                    # Keep content_text empty or whatever read_text managed if any
                    if not content_text:
                        # Attempt to re-read or just skip content processing if read failed
                        pass

                # Add node
                self.graph.add_node(
                    rel_path,
                    title=title,
                    tags=tags,
                    path=str(file_path)
                )

                # Map identifiers
                self.file_map[file_path.stem.lower()] = rel_path
                if title:
                    self.file_map[title.lower()] = rel_path

                files.append(file_path)

                if not content_text:
                    continue

                # Extract Markdown links
                for match in md_link_pattern.findall(content_text):
                    target_link = match.split(" ")[0] # handle [text](link "title")
                    if not target_link.startswith(("http://", "https://", "mailto:")):
                        raw_links.append((rel_path, target_link, 'md', file_path))

                # Extract Wiki-links
                for match in wiki_link_pattern.findall(content_text):
                    target_name = match.split("|")[0].strip().lower()
                    raw_links.append((rel_path, target_name, 'wiki', file_path))

        # 2. Resolve Links (In Memory)
        for source_rel, target_raw, link_type, file_path in raw_links:
            target_rel = None

            if link_type == 'md':
                try:
                    # Resolve from current file directory
                    # Note: resolve() might touch FS.
                    target_path = (file_path.parent / target_raw).resolve()

                    if target_path.is_relative_to(self.root):
                        target_rel = target_path.relative_to(self.root).as_posix()
                except (ValueError, RuntimeError):
                    continue

            elif link_type == 'wiki':
                if target_raw in self.file_map:
                    target_rel = self.file_map[target_raw]

            # Add Edge if valid
            if target_rel and self.graph.has_node(target_rel):
                if source_rel != target_rel:
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
