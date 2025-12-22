"""
Knowledge Graph Engine
======================
Parses wikilinks, builds NetworkX graph, and provides navigation primitives.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import frontmatter
import networkx as nx
from rich.console import Console

console = Console()


class KnowledgeGraph:
    """
    Knowledge graph builder and analyzer.
    
    Scans markdown files for:
    - YAML frontmatter metadata
    - Wikilinks [[target]] syntax
    - Bi-directional link relationships
    """
    
    def __init__(self, root: Path):
        self.root = root
        self.graph = nx.DiGraph()
        self.knowledge_base = root / "10-19_KNOWLEDGE"
        
    def parse_wikilinks(self, content: str) -> List[str]:
        """
        Extract [[wikilinks]] from markdown content.
        
        Supports:
        - Simple: [[Note Name]]
        - Aliased: [[Note Name|Display Text]]
        - With path: [[til/2025/note]]
        
        Returns:
            List of target note names/paths
        """
        # Pattern matches [[target]] or [[target|alias]]
        pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        return re.findall(pattern, content)
    
    def resolve_wikilink(self, link: str, source_file: Path) -> Optional[Path]:
        """
        Resolve a wikilink to an actual file path.
        
        Resolution order:
        1. Exact path match (if link contains /)
        2. Filename match in knowledge base
        3. Fuzzy match on title (from frontmatter)
        
        Args:
            link: Wikilink target (e.g., "python-typing" or "til/2025/note")
            source_file: File containing the link (for relative resolution)
            
        Returns:
            Resolved Path or None if not found
        """
        # If link contains path separator, try as partial path
        if "/" in link:
            potential = self.knowledge_base / f"{link}.md"
            if potential.exists():
                return potential
        
        # Search by filename
        search_name = f"{link}.md"
        for md_file in self.knowledge_base.rglob("*.md"):
            if md_file.name == search_name:
                return md_file
        
        # Fuzzy match on title (slower, last resort)
        link_lower = link.lower().replace("-", " ")
        for md_file in self.knowledge_base.rglob("*.md"):
            try:
                post = frontmatter.load(md_file)
                title = post.get("title", "").lower()
                if link_lower in title or title in link_lower:
                    return md_file
            except Exception:
                continue
        
        return None
    
    def scan(self, force_rescan: bool = False) -> Dict[str, int]:
        """
        Scan all markdown files and build graph.
        
        Args:
            force_rescan: If True, rebuild graph from scratch
            
        Returns:
            Dictionary with scan statistics
        """
        if force_rescan:
            self.graph.clear()
        
        stats = {"files": 0, "nodes": 0, "links": 0, "errors": 0}
        
        if not self.knowledge_base.exists():
            console.print(
                f"[yellow]Warning:[/yellow] Knowledge base not found at {self.knowledge_base}"
            )
            return stats
        
        for md_file in self.knowledge_base.rglob("*.md"):
            stats["files"] += 1
            
            try:
                # Parse frontmatter
                post = frontmatter.load(md_file)
                
                # Add node with metadata
                node_id = str(md_file.relative_to(self.root))
                self.graph.add_node(
                    node_id,
                    title=post.get("title", md_file.stem),
                    type=post.get("type", "unknown"),
                    tags=post.get("tags", []),
                    created=post.get("created"),
                    path=str(md_file),
                )
                stats["nodes"] += 1
                
                # Extract and resolve wikilinks
                links = self.parse_wikilinks(post.content)
                for link in links:
                    target_file = self.resolve_wikilink(link, md_file)
                    
                    if target_file:
                        target_id = str(target_file.relative_to(self.root))
                        
                        # Ensure target node exists
                        if not self.graph.has_node(target_id):
                            self.graph.add_node(
                                target_id,
                                title=target_file.stem,
                                path=str(target_file),
                            )
                        
                        # Add directed edge
                        self.graph.add_edge(node_id, target_id, type="wikilink")
                        stats["links"] += 1
                    else:
                        # Broken link (will be caught by doctor --knowledge)
                        pass
                        
            except Exception as e:
                stats["errors"] += 1
                console.print(f"[dim]Error parsing {md_file.name}: {e}[/dim]")
        
        return stats
    
    def get_backlinks(self, filepath: Path) -> List[str]:
        """
        Get all notes linking TO this file (reverse lookup).
        
        Args:
            filepath: Target file
            
        Returns:
            List of source file paths (relative to root)
        """
        node_id = str(filepath.relative_to(self.root))
        
        if not self.graph.has_node(node_id):
            return []
        
        return list(self.graph.predecessors(node_id))
    
    def get_outlinks(self, filepath: Path) -> List[str]:
        """
        Get all notes this file links TO (forward lookup).
        
        Args:
            filepath: Source file
            
        Returns:
            List of target file paths (relative to root)
        """
        node_id = str(filepath.relative_to(self.root))
        
        if not self.graph.has_node(node_id):
            return []
        
        return list(self.graph.successors(node_id))
    
    def find_broken_links(self) -> List[Tuple[str, str]]:
        """
        Find all wikilinks that don't resolve to existing files.
        
        Returns:
            List of (source_file, broken_link_target) tuples
        """
        broken = []
        
        for md_file in self.knowledge_base.rglob("*.md"):
            try:
                post = frontmatter.load(md_file)
                links = self.parse_wikilinks(post.content)
                
                for link in links:
                    target = self.resolve_wikilink(link, md_file)
                    if not target:
                        broken.append((str(md_file.relative_to(self.root)), link))
            except Exception:
                continue
        
        return broken
    
    def get_hub_notes(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Find most connected notes (by combined in+out degree).
        
        Args:
            top_n: Number of top hubs to return
            
        Returns:
            List of (node_id, connection_count) tuples
        """
        if self.graph.number_of_nodes() == 0:
            return []
        
        # Calculate total degree (in + out)
        degrees = {
            node: self.graph.in_degree(node) + self.graph.out_degree(node)
            for node in self.graph.nodes()
        }
        
        # Sort and return top N
        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]
    
    def get_orphan_notes(self) -> List[str]:
        """
        Find notes with no incoming or outgoing links (isolated nodes).
        
        Returns:
            List of orphaned node IDs
        """
        if self.graph.number_of_nodes() == 0:
            return []
        
        orphans = []
        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            
            if in_degree == 0 and out_degree == 0:
                orphans.append(node)
        
        return orphans
    
    def export_to_graphviz(self, output_path: Path) -> None:
        """
        Export graph to Graphviz DOT format for visualization.
        
        Args:
            output_path: Path to save .dot file
        """
        try:
            from networkx.drawing.nx_agraph import write_dot
            write_dot(self.graph, output_path)
            console.print(f"[green]✓[/green] Graph exported to {output_path}")
            console.print("[dim]Visualize with: dot -Tpng graph.dot -o graph.png[/dim]")
        except ImportError:
            console.print("[yellow]⚠️  PyGraphviz not installed[/yellow]")
            console.print("[dim]Install with: pip install pygraphviz[/dim]")
            console.print("[dim]Or use --html for browser-based visualization[/dim]")
