"""
PKM (Personal Knowledge Management) Commands
=============================================
Commands for knowledge graph navigation and analysis.
"""
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

app = typer.Typer(help="Personal Knowledge Management commands")
console = Console()


@app.command()
def find(
    ctx: typer.Context,
    query: Annotated[Optional[str], typer.Argument(help="Search query")] = None,
    tag: Annotated[Optional[List[str]], typer.Option("--tag", "-t", help="Filter by tag(s)")] = None,
    note_type: Annotated[Optional[str], typer.Option("--type", help="Filter by note type")] = None,
    reindex: Annotated[bool, typer.Option("--reindex", help="Rebuild database before searching")] = False,
    global_search: Annotated[bool, typer.Option("--global", "-g", help="Search archived content as well")] = False,
) -> None:
    """
    🔍 Fast search across knowledge base (DuckDB-powered).

    Searches notes by title, content, tags, and type.
    First run will index all notes (~5 sec for 1000 notes).

    Default searches only 'Active Knowledge' (10-19).
    Use --global to also search 'Archived Content' (90-99).

    Examples:
        devbase pkm find python
        devbase pkm find python --global
        devbase pkm find --tag git --tag cli
        devbase pkm find --type til
        devbase pkm find typer --tag python
    """
    from devbase.services.knowledge_db import KnowledgeDB

    root: Path = ctx.obj["root"]
    db = KnowledgeDB(root)

    # Index if database is empty or reindex requested
    stats = db.get_stats()
    if reindex or stats["total_notes"] == 0:
        console.print("[bold]Indexing knowledge base...[/bold]")
        with console.status("[green]Scanning files..."):
            index_stats = db.index_workspace()

        console.print(f"[green]✓[/green] Indexed {index_stats['indexed']} notes")
        if index_stats['errors'] > 0:
            console.print(f"[yellow]⚠[/yellow] {index_stats['errors']} errors")
        console.print()

    # Search
    results = db.search(query=query, tags=tag, note_type=note_type, limit=50, global_search=global_search)

    # Fallback: if --type returned no results, try searching by tag instead
    if not results and note_type and not tag:
        results = db.search(query=query, tags=[note_type], note_type=None, limit=50, global_search=global_search)
        if results:
            console.print(f"[dim](Searching by tag '{note_type}' instead of type)[/dim]")

    if not results:
        console.print("[yellow]No results found[/yellow]")
        db.close()
        return

    console.print(f"\n[bold]Found {len(results)} note(s):[/bold]\n")

    for result in results:
        console.print(f"[cyan]■[/cyan] [bold]{result['title']}[/bold]")
        console.print(f"  [dim]{result['path']}[/dim]")

        if result['type']:
            console.print(f"  Type: [yellow]{result['type']}[/yellow]", end="")
        if result['word_count']:
            console.print(f"  | Words: {result['word_count']}", end="")

        console.print()  # Newline

        # Preview
        if result['content_preview']:
            preview = result['content_preview'][:150].replace("\n", " ")
            console.print(f"  [dim]{preview}...[/dim]")

        console.print()

    db.close()


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
    global_scope: Annotated[
        bool,
        typer.Option("--global", help="Include archive (90-99_ARCHIVE_COLD) in graph"),
    ] = False,
) -> None:
    """
    📊 Visualize knowledge graph statistics.

    Shows network analysis of your knowledge base using NetworkX:
    - Total nodes and connections
    - Hub notes (most connected)
    - Orphan notes (isolated)
    - Connection density

    Supports exporting to Graphviz DOT format or interactive HTML (PyVis).

    Examples:
        devbase pkm graph              # Show stats for active knowledge
        devbase pkm graph --global     # Include archive
        devbase pkm graph --export     # Save as graph.dot
        devbase pkm graph --html       # Interactive visualization
    """
    import networkx as nx

    from devbase.services.knowledge_graph import KnowledgeGraph

    root: Path = ctx.obj["root"]
    kg = KnowledgeGraph(root, include_archive=global_scope)

    with console.status("[bold green]Scanning knowledge base..."):
        stats = kg.scan()

    # Display stats
    console.print("[bold]Scan Results:[/bold]")
    console.print(f"  Files scanned: [cyan]{stats['files']}[/cyan]")
    console.print(f"  Graph nodes: [cyan]{stats['nodes']}[/cyan]")
    console.print(f"  Connections: [cyan]{stats['links']}[/cyan]")
    if stats['errors'] > 0:
        console.print(f"  [yellow]Parse errors: {stats['errors']}[/yellow]")

    # Graph metrics
    if kg.graph.number_of_nodes() > 0:
        console.print("\n[bold]Graph Metrics:[/bold]")
        console.print(f"  Connection density: [cyan]{nx.density(kg.graph):.3f}[/cyan]")

        # Hub notes
        hubs = kg.get_hub_notes(5)
        if hubs:
            console.print("\n[bold]Most Connected Notes:[/bold]")
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
        try:
            kg.export_to_graphviz(output_path)
            console.print(f"\n[green]✓[/green] Graph exported to: [cyan]{output_path}[/cyan]")
        except ImportError as e:
            console.print(f"\n[yellow]⚠️  {str(e)}[/yellow]")
        except Exception as e:
            console.print(f"\n[red]✗[/red] Failed to export graph: {str(e)}")

    if html:
        output_path = root / "knowledge_graph.html"
        try:
            kg.export_to_pyvis(output_path)
            console.print(f"\n[green]✓[/green] Interactive graph saved to: [cyan]{output_path}[/cyan]")
            console.print("[dim]Open in browser to explore[/dim]")
        except ImportError:
            console.print("\n[yellow]⚠️  PyVis not installed[/yellow]")
            console.print("[dim]Install with: pip install devbase[viz][/dim]")


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
    from devbase.services.knowledge_graph import KnowledgeGraph

    root: Path = ctx.obj["root"]
    kg = KnowledgeGraph(root, include_archive=True) # Always include all notes for link analysis

    with console.status("[bold green]Scanning knowledge base..."):
        kg.scan()

    # Get connections
    outlinks = kg.get_outlinks(note)
    backlinks = kg.get_backlinks(note)

    # Check if note exists
    # If not found directly, try to find by resolving it same way as get_outlinks does internally
    # But since scan is done, we can just check if it's in the graph or if it's a valid path
    # note might be a file path passed by user.

    console.print(f"[bold]Link Analysis for:[/bold] [cyan]{note}[/cyan]\n")

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
        console.print("[dim]← No backlinks[/dim]")


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
    from datetime import date, datetime

    import frontmatter

    root: Path = ctx.obj["root"]

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

    # Sort by date (newest first) - normalize to datetime for comparison
    def normalize_date(d):
        if d is None:
            return datetime.min
        if isinstance(d, date) and not isinstance(d, datetime):
            return datetime.combine(d, datetime.min.time())
        return d

    notes.sort(key=lambda x: normalize_date(x["date"]), reverse=True)

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


@app.command()
def new(
    ctx: typer.Context,
    name: Annotated[Optional[str], typer.Argument(help="Name of the note (slugified)")] = None,
    note_type: Annotated[Optional[str], typer.Option("--type", "-t", help="Diataxis type (tutorial, how-to, reference, explanation)")] = None,
) -> None:
    """
    📝 Create a new note and queue for AI classification.

    Creates a new note in the appropriate folder based on Diataxis type:
    - tutorial -> 10-19_KNOWLEDGE/10_references (placeholder)
    - how-to -> 10-19_KNOWLEDGE/10_references
    - reference -> 10-19_KNOWLEDGE/10_references
    - explanation -> 10-19_KNOWLEDGE/10_references

    (Note: In v5.1, we default to '10_references' or '11_public_garden' until
     more granular mapping is defined. Using '10_references' for now.)

    After creation, an asynchronous 'classify' task is added to the AI queue.

    Example:
        devbase pkm new my-new-concept --type explanation
    """
    import json
    from datetime import datetime

    from devbase.adapters.storage import duckdb_adapter

    root: Path = ctx.obj["root"]

    from rich.prompt import Prompt

    if name is None:
        name = Prompt.ask("Enter note name")

    if note_type is None:
        note_type = Prompt.ask(
            "Select note type",
            choices=["tutorial", "how-to", "reference", "explanation", "daily", "meeting"],
            default="reference"
        )

    # Simple slugify
    slug = name.lower().replace(" ", "-")
    if not slug.endswith(".md"):
        slug += ".md"

    # Determine target directory
    # Defaulting to 10-19_KNOWLEDGE/10_references as a safe default for now
    target_dir = root / "10-19_KNOWLEDGE" / "10_references"
    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / slug

    if file_path.exists():
        console.print(f"[red]✗[/red] File already exists: {file_path}")
        raise typer.Exit(1)

    # Create content
    content = f"""---
title: {name}
type: {note_type}
created: {datetime.now().isoformat()}
tags: []
status: draft
---

# {name}

"""
    file_path.write_text(content, encoding="utf-8")

    console.print(f"[green]✓[/green] Created note: [cyan]{file_path}[/cyan]")

    # Enqueue AI task
    task_id = duckdb_adapter.enqueue_ai_task(
        task_type="classify",
        payload=json.dumps({"path": str(file_path)})
    )

    if task_id > 0:
        console.print(f"[dim]queued AI classification (task #{task_id})[/dim]")
    else:
        console.print("[yellow]⚠ Failed to enqueue AI task[/yellow]")


@app.command()
def journal(
    ctx: typer.Context,
    entry: Annotated[Optional[str], typer.Argument(help="Entry text (if empty, opens file)")] = None,
) -> None:
    """
    📔 Add entry to weekly journal (auto-created).
    
    If entry text is provided:
    - Appends to '10-19_KNOWLEDGE/12_private-vault/journal/weekly-YYYY-Www.md'
    - Tracks telemetry
    
    If no text:
    - Opens the file in editor
    
    Example:
        devbase pkm journal "Learned about DuckDB today"
    """
    from datetime import datetime
    import subprocess
    
    root: Path = ctx.obj["root"]
    
    # Calculate filename (ISO Week date)
    today = datetime.now()
    year, week, weekday = today.isocalendar()
    filename = f"weekly-{year}-W{week:02d}.md"
    
    journal_dir = root / "10-19_KNOWLEDGE" / "12_private-vault" / "journal"
    journal_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = journal_dir / filename
    
    # Create if missing
    if not file_path.exists():
        start_of_week = today # Approximation for created date
        content = f"""---
type: journal
template: weekly-retrospective
created: {start_of_week.strftime('%Y-%m-%d')}
tags: [journal, retrospective]
status: active
---

# Weekly Journal ({year}-W{week:02d})

## 📅 Log

"""
        file_path.write_text(content, encoding="utf-8")
        console.print(f"[green]✓[/green] Created new journal: [cyan]{file_path.name}[/cyan]")
    
    # Action
    if entry:
        # Append entry
        timestamp = today.strftime("%H:%M")
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"- [{timestamp}] {entry}\n")
        
        console.print(f"[green]✓[/green] Added entry to [cyan]{filename}[/cyan]")
        
        # Telemetry
        from devbase.utils.telemetry import get_telemetry
        telemetry = get_telemetry(root)
        telemetry.track(
            message=f"Added journal entry: {entry[:30]}...",
            category="journal",
            action="pkm_journal_add",
            status="success"
        )
    else:
        # Open in editor (VS Code)
        import shutil

        console.print(f"Opening [cyan]{filename}[/cyan]...")
        if shutil.which("code"):
            subprocess.run(["code", str(file_path)], check=False)
        else:
            console.print("[yellow]⚠ 'code' (VS Code) not found in PATH[/yellow]")


@app.command()
def icebox(
    ctx: typer.Context,
    idea: Annotated[Optional[str], typer.Argument(help="Idea to add (if empty, opens file)")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Section tag (default: 'Novas Ideias')")] = None,
) -> None:
    """
    🧊 Add item to Icebox (02_planning/icebox.md).
    
    If idea text is provided:
    - Appends to Icebox file
    - Tracks telemetry
    
    If no text:
    - Opens the file in editor
    
    Example:
        devbase pkm icebox "Migrate to localized dates"
    """
    import subprocess
    from datetime import datetime
    
    root: Path = ctx.obj["root"]
    file_path = root / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    
    if not file_path.exists():
        console.print(f"[red]✗[/red] Icebox file not found at {file_path}")
        return

    if idea:
        # Append idea
        timestamp = datetime.now().strftime("%Y-%m-%d")
        category = tag if tag else "Inbox"
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n### [{category.upper()}] {idea}\n")
            f.write(f"**Data:** {timestamp}\n")
            f.write(f"**Status:** PROPOSED\n\n---\n")
            
        console.print(f"[green]✓[/green] Added to Icebox: [cyan]{idea}[/cyan]")
         
        # Telemetry
        from devbase.utils.telemetry import get_telemetry
        telemetry = get_telemetry(root)
        telemetry.track(
            message=f"Added icebox item: {idea[:30]}...",
            category="planning",
            action="pkm_icebox_add",
            status="success"
        )
    else:
         # Open in editor
        import shutil

        console.print(f"Opening [cyan]icebox.md[/cyan]...")
        if shutil.which("code"):
            subprocess.run(["code", str(file_path)], check=False)
        else:
            console.print("[yellow]⚠ 'code' (VS Code) not found in PATH[/yellow]")
