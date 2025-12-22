"""
PKM (Personal Knowledge Management) Commands
=============================================
Commands for knowledge graph navigation and analysis.
"""
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

app = typer.Typer(help="Personal Knowledge Management commands")
console = Console()


@app.command()
def graph(
    ctx: typer.Context,
    export: Annotated[
        bool,
        typer.Option("--export", "-e", help="Export graph to DOT format"),
    ] = False,
    html: Annotated[
        bool,
        typer.Option("--html", help="Generate interactive HTML visualization"),
    ] = False,
) -> None:
    """
    📊 Visualize knowledge graph statistics.
    
    Shows network analysis of your knowledge base:
    - Total nodes and connections
    - Hub notes (most connected)
    - Orphan notes (isolated)
    - Connection density
    
    Examples:
        devbase pkm graph              # Show stats
        devbase pkm graph --export      # Save as graph.dot
        devbase pkm graph --html        # Interactive visualization
    """
    import sys

    root: Path = ctx.obj["root"]
    
    # Add modules to path
    sys.path.insert(0, str(root.parent / "devbase-setup" / "modules" / "python"))
    
    from knowledge.graph import KnowledgeGraph
    
    console.print()
    console.print("[bold]Knowledge Graph Analysis[/bold]")
    console.print(f"Workspace: [cyan]{root}[/cyan]\n")
    
    # Build graph
    kg = KnowledgeGraph(root)
    
    with console.status("[bold green]Scanning knowledge base..."):
        stats = kg.scan()
    
    # Display stats
    console.print(f"[bold]Scan Results:[/bold]")
    console.print(f"  Files scanned: [cyan]{stats['files']}[/cyan]")
    console.print(f"  Graph nodes: [cyan]{stats['nodes']}[/cyan]")
    console.print(f"  Connections: [cyan]{stats['links']}[/cyan]")
    if stats['errors'] > 0:
        console.print(f"  [yellow]Parse errors: {stats['errors']}[/yellow]")
    
    # Graph metrics
    if kg.graph.number_of_nodes() > 0:
        console.print(f"\n[bold]Graph Metrics:[/bold]")
        console.print(f"  Connection density: [cyan]{nx.density(kg.graph):.3f}[/cyan]")
        
        # Hub notes
        hubs = kg.get_hub_notes(5)
        if hubs:
            console.print(f"\n[bold]Most Connected Notes:[/bold]")
            table = Table(show_header=True)
            table.add_column("Note", style="cyan")
            table.add_column("Links", justify="right", style="green")
            
            for node, degree in hubs:
                title = kg.graph.nodes[node].get("title", Path(node).stem)
                table.add_row(title, str(degree))
            
            console.print(table)
        
        # Orphans
        orphans = kg.get_orphan_notes()
        if orphans:
            console.print(f"\n[yellow]⚠️  Found {len(orphans)} orphan note(s)[/yellow]")
            console.print("[dim]Orphans have no links (consider adding connections)[/dim]")
    
    # Export options
    if export:
        output_path = root / "knowledge_graph.dot"
        kg.export_to_graphviz(output_path)
    
    if html:
        try:
            from pyvis.network import Network
            
            net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
            net.from_nx(kg.graph)
            
            output_path = root / "knowledge_graph.html"
            net.save_graph(str(output_path))
            
            console.print(f"\n[green]✓[/green] Interactive graph saved to: [cyan]{output_path}[/cyan]")
            console.print("[dim]Open in browser to explore[/dim]")
        except ImportError:
            console.print("\n[yellow]⚠️  PyVis not installed[/yellow]")
            console.print("[dim]Install with: pip install pyvis[/dim]")


@app.command()
def links(
    ctx: typer.Context,
    note: Annotated[str, typer.Argument(help="Note path (relative to 10-19_KNOWLEDGE)")],
) -> None:
    """
    🔗 Show connections for a specific note.
    
    Displays:
    - Outgoing links (notes this file references)
    - Incoming links (backlinks - who references this note)
    
    Example:
        devbase pkm links til/2025-12-22-typer-context.md
    """
    import sys
    import networkx as nx

    root: Path = ctx.obj["root"]
    sys.path.insert(0, str(root.parent / "devbase-setup" / "modules" / "python"))
    
    from knowledge.graph import KnowledgeGraph
    
    # Resolve note path
    note_path = root / "10-19_KNOWLEDGE" / note
    if not note_path.exists():
        # Try with .md extension
        note_path = root / "10-19_KNOWLEDGE" / f"{note}.md"
    
    if not note_path.exists():
        console.print(f"[red]✗[/red] Note not found: {note}")
        raise typer.Exit(1)
    
    console.print()
    console.print(f"[bold]Links for:[/bold] [cyan]{note_path.name}[/cyan]\n")
    
    # Build graph
    kg = KnowledgeGraph(root)
    kg.scan()
    
    # Get connections
    outlinks = kg.get_outlinks(note_path)
    backlinks = kg.get_backlinks(note_path)
    
    # Display outgoing
    if outlinks:
        console.print(f"[bold]→ Links to ({len(outlinks)}):[/bold]")
        for target in outlinks:
            title = kg.graph.nodes[target].get("title", Path(target).stem)
            console.print(f"  • [cyan]{title}[/cyan] [dim]({target})[/dim]")
    else:
        console.print("[dim]→ No outgoing links[/dim]")
    
    console.print()
    
    # Display incoming
    if backlinks:
        console.print(f"[bold]← Linked by ({len(backlinks)}):[/bold]")
        for source in backlinks:
            title = kg.graph.nodes[source].get("title", Path(source).stem)
            console.print(f"  • [cyan]{title}[/cyan] [dim]({source})[/dim]")
    else:
        console.print("[dim]← No backlinks (orphan note)[/dim]")


@app.command()
def index(
    ctx: typer.Context,
    folder: Annotated[str, typer.Argument(help="Folder to index (e.g., 'til')")],
) -> None:
    """
    📚 Generate index/MOC (Map of Content) for a folder.
    
    Creates _index.md file with:
    - Chronological list of recent notes
    - Grouping by tags
    - Metadata summary
    
    Example:
        devbase pkm index til
    """
    import sys
    from datetime import datetime

    root: Path = ctx.obj["root"]
    sys.path.insert(0, str(root.parent / "devbase-setup" / "modules" / "python"))
    
    import frontmatter
    
    target_dir = root / "10-19_KNOWLEDGE" / "11_public_garden" / folder
    
    if not target_dir.exists():
        console.print(f"[red]✗[/red] Folder not found: {folder}")
        raise typer.Exit(1)
    
    console.print()
    console.print(f"[bold]Indexing:[/bold] [cyan]{folder}[/cyan]\n")
    
    # Collect all markdown files
    notes = []
    for md_file in target_dir.rglob("*.md"):
        if md_file.name.startswith("_"):  # Skip index files
            continue
        
        try:
            post = frontmatter.load(md_file)
            notes.append({
                "path": md_file,
                "title": post.get("title", md_file.stem),
                "date": post.get("date", post.get("created")),
                "tags": post.get("tags", []),
            })
        except Exception:
            continue
    
    # Sort by date (newest first)
    notes.sort(key=lambda x: x["date"] if x["date"] else datetime.min, reverse=True)
    
    # Generate index content
    index_content = f"""# {folder.upper()} Index

> Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

**Total notes:** {len(notes)}

## Recent Notes

"""
    
    # Add recent 20
    for note in notes[:20]:
        rel_path = note["path"].relative_to(target_dir)
        date_str = note["date"].strftime("%Y-%m-%d") if note["date"] else "undated"
        index_content += f"- [{date_str}] [{note['title']}]({rel_path})\n"
    
    if len(notes) > 20:
        index_content += f"\n... and {len(notes) - 20} more notes\n"
    
    # Group by tags
    tag_groups = {}
    for note in notes:
        for tag in note["tags"]:
            if tag not in tag_groups:
                tag_groups[tag] = []
            tag_groups[tag].append(note)
    
    if tag_groups:
        index_content += "\n## By Tag\n\n"
        for tag, tagged_notes in sorted(tag_groups.items()):
            index_content += f"### #{tag} ({len(tagged_notes)} notes)\n\n"
    
    # Save index
    index_file = target_dir / "_index.md"
    index_file.write_text(index_content, encoding="utf-8")
    
    console.print(f"[green]✓[/green] Index created: [cyan]{index_file}[/cyan]")
    console.print(f"[dim]Indexed {len(notes)} note(s)[/dim]")
