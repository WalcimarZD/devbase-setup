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
        - Combined two passes into one to reduce I/O overhead.
        - Files are read once: Frontmatter parsed, extracted links stored in memory.
        - Links are resolved after the map is fully populated.
        - Reduces I/O ops by 50%.

        Returns:
            Dict with scan statistics (files, nodes, links, errors).
        """
        self.graph.clear()
        self.file_map.clear()

        search_paths = self._get_search_paths()
        files_count = 0
        errors = 0
        links_count = 0

        # Regex for Markdown links: [text](link)
        # We ignore external links (http/https)
        md_link_pattern = re.compile(r"\[.*?\]\((.*?)\)")

        # Regex for Wiki-links: [[link]] or [[link|text]]
        wiki_link_pattern = re.compile(r"\[\[(.*?)\]\]")

        # Deferred links to resolve after file map is built
        # List of (source_rel, link_type, link_value, source_file_path)
        deferred_links: List[Tuple[str, str, str, Path]] = []

        # 1. Single Pass I/O: Collect nodes, map, and extract links
        for path in search_paths:
            # Optimization: Use scan_directory for centralized pruning
            for file_path in scan_directory(path, extensions={'.md'}):
                files_count += 1
                # Store relative path from workspace root for portability
                rel_path = file_path.relative_to(self.root).as_posix()

                content = ""
                title = file_path.stem
                tags = []
                body = ""

                # ⚡ Bolt Optimization: Read once
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception:
                    # If we can't read the file, skip completely
                    errors += 1
                    continue

                # Parse Frontmatter
                try:
                    post = frontmatter.loads(content)
                    title = post.get("title", file_path.stem)
                    tags = post.get("tags", [])
                    body = post.content # Content after frontmatter
                except Exception:
                    # Fallback for failed parsing: treat entire content as body
                    # This ensures we still extract links even if frontmatter is broken
                    errors += 1
                    body = content

                # Add node immediately
                self.graph.add_node(
                    rel_path,
                    title=title,
                    tags=tags,
                    path=str(file_path)
                )

                # Update file map
                self.file_map[file_path.stem.lower()] = rel_path
                if title:
                    self.file_map[title.lower()] = rel_path

                # Extract links immediately (CPU bound, fast) and defer resolution
                # Extract Markdown links
                for match in md_link_pattern.findall(body):
                    target_link = match.split(" ")[0]
                    if not target_link.startswith(("http://", "https://", "mailto:")):
                        deferred_links.append((rel_path, "md", target_link, file_path))

                # Extract Wiki-links
                for match in wiki_link_pattern.findall(body):
                    target_name = match.split("|")[0].strip().lower()
                    deferred_links.append((rel_path, "wiki", target_name, file_path))

        # 2. Resolve Links (Memory only, no I/O)
        for source_rel, link_type, link_value, source_path in deferred_links:
            target_rel = None

            if link_type == "md":
                try:
                    # Resolve relative link
                    target_path = (source_path.parent / link_value).resolve()
                    if target_path.is_relative_to(self.root):
                        potential_rel = target_path.relative_to(self.root).as_posix()
                        if self.graph.has_node(potential_rel):
                            target_rel = potential_rel
                except (ValueError, RuntimeError):
                    continue

            elif link_type == "wiki":
                if link_value in self.file_map:
                    target_rel = self.file_map[link_value]

            if target_rel and source_rel != target_rel:
                self.graph.add_edge(source_rel, target_rel)
                links_count += 1

        self._scanned = True
        return {
            "files": files_count,
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
