"""
Learning Enhancement Commands: study review, study synthesize
==============================================================
Active learning commands implementing spaced repetition and forced connections.
Based on pedagogical research: Bloom's Taxonomy, Elaboration Theory, Zettelkasten.
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from typing_extensions import Annotated

app = typer.Typer(help="Learning \u0026 knowledge retention commands")
console = Console()


@app.command()
def review(
    ctx: typer.Context,
    count: Annotated[int, typer.Option("--count", "-n", help="Number of notes to review")] = 5,
) -> None:
    """
    🧠 Spaced repetition review session (Active Recall).
    
    Implements the "Testing Effect" - actively retrieving information
    from memory strengthens learning more than passive re-reading.
    
    Algorithm:
    - Prioritizes notes last reviewed >7 days ago
    - Shows only title + context (hides content)
    - Forces you to recall before revealing answer
    - Updates last_reviewed metadata
    
    Example:
        devbase study review          # Review 5 random notes
        devbase study review --count 10
    """
    root: Path = ctx.obj["root"]
    sys.path.insert(0, str(root.parent / "devbase-setup" / "modules" / "python"))
    
    import frontmatter
    
    knowledge_base = root / "10-19_KNOWLEDGE" / "11_public_garden"
    
    if not knowledge_base.exists():
        console.print("[red]Knowledge base not found[/red]")
        raise typer.Exit(1)
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🧠 Spaced Repetition Review[/bold cyan]\n\n"
        "Active Recall strengthens memory.\n"
        "Try to remember BEFORE viewing the answer!",
        border_style="cyan"
    ))
    
    # Collect all markdown files
    notes = []
    for md_file in knowledge_base.rglob("*.md"):
        if md_file.name.startswith("_"):  # Skip indexes
            continue
        
        try:
            post = frontmatter.load(md_file)
            last_reviewed = post.get("last_reviewed")
            created = post.get("created") or post.get("date")
            
            # Calculate priority (days since last review or creation)
            if last_reviewed:
                try:
                    last_dt = datetime.fromisoformat(str(last_reviewed))
                    days_ago = (datetime.now() - last_dt).days
                except (ValueError, TypeError):
                    days_ago = 999  # Never reviewed properly
            elif created:
                try:
                    created_dt = datetime.fromisoformat(str(created))
                    days_ago = (datetime.now() - created_dt).days
                except (ValueError, TypeError):
                    days_ago = 0
            else:
                days_ago = 0
            
            # Only review notes older than 1 day
            if days_ago >= 1:
                notes.append({
                    "path": md_file,
                    "post": post,
                    "days_ago": days_ago,
                    "title": post.get("title", md_file.stem),
                })
        except Exception:
            continue
    
    if not notes:
        console.print("[yellow]No notes eligible for review[/yellow]")
        console.print("[dim]Create some TILs and come back tomorrow![/dim]")
        return
    
    # Sort by days_ago (prioritize least recently reviewed)
    notes.sort(key=lambda x: x["days_ago"], reverse=True)
    
    # Select top N
    review_count = min(count, len(notes))
    to_review = notes[:review_count]
    
    console.print(f"\n[bold]Reviewing {review_count} note(s)...[/bold]\n")
    
    reviewed = 0
    for i, note in enumerate(to_review, 1):
        console.print(Panel(
            f"[bold cyan]Note {i}/{review_count}[/bold cyan]\n\n"
            f"[bold]{note['title']}[/bold]\n\n"
            f"[dim]Last reviewed: {note['days_ago']} days ago[/dim]",
            border_style="cyan"
        ))
        
        console.print("\n[yellow]Try to recall this concept...[/yellow]")
        Prompt.ask("[dim]Press Enter to see the answer[/dim]", default="")
        
        # Show content
        console.print("\n[bold]Answer:[/bold]")
        console.print(Panel(note["post"].content[:500], border_style="green"))
        
        # Ask if remembered
        if Confirm.ask("\n[bold]Did you remember correctly?[/bold]"):
            # Update last_reviewed
            note["post"]["last_reviewed"] = datetime.now().isoformat()
            
            # Save back to file
            with open(note["path"], "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(note["post"]))
            
            reviewed += 1
            console.print("[green]✓ Marked as reviewed[/green]")
        else:
            console.print("[yellow]⚠ Review this again soon[/yellow]")
        
        if i < review_count:
            console.print("\n" + "─" * 60 + "\n")
    
    console.print()
    console.print(Panel.fit(
        f"[bold green]✅ Review Session Complete![/bold green]\n\n"
        f"Reviewed: {reviewed}/{review_count}",
        border_style="green"
    ))


@app.command()
def synthesize(
    ctx: typer.Context,
) -> None:
    """
    🔗 Forced synthesis of random concepts (Bi-Association).
    
    Creativity technique: forces your brain to find connections
    between seemingly unrelated concepts, creating NEW insights.
    
    Based on:
    - Bloom's Taxonomy Level 5 (Synthesize)
    - Zettelkasten linking methodology
    - Creative problem-solving research
    
    Process:
    1. Randomly selects 2 notes from your knowledge base
    2. Challenges you to find connections
    3. Guides you to create a synthesis note
    
    Example:
        devbase study synthesize
    """
    root: Path = ctx.obj["root"]
    sys.path.insert(0, str(root.parent / "devbase-setup" / "modules" / "python"))
    
    import frontmatter
    
    knowledge_base = root / "10-19_KNOWLEDGE" / "11_public_garden"
    
    if not knowledge_base.exists():
        console.print("[red]Knowledge base not found[/red]")
        raise typer.Exit(1)
    
    # Collect eligible notes (TIL, concepts)
    notes = []
    for md_file in knowledge_base.rglob("*.md"):
        if md_file.name.startswith("_"):
            continue
        
        try:
            post = frontmatter.load(md_file)
            note_type = post.get("type", "")
            
            if note_type in ["til", "concept", ""]:  # Include untyped
                notes.append({
                    "path": md_file,
                    "title": post.get("title", md_file.stem),
                    "content": post.content[:200],  # Preview
                })
        except Exception:
            continue
    
    if len(notes) < 2:
        console.print("[yellow]Need at least 2 notes for synthesis[/yellow]")
        console.print("[dim]Create more TILs and try again![/dim]")
        return
    
    # Random selection
    selected = random.sample(notes, 2)
    note_a, note_b = selected
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🔗 Forced Synthesis Challenge[/bold cyan]\n\n"
        "Find connections between seemingly unrelated concepts.\n"
        "This creates NEW knowledge through creative thinking!",
        border_style="cyan"
    ))
    
    console.print("\n[bold]Concept A:[/bold]")
    console.print(Panel(
        f"[cyan]{note_a['title']}[/cyan]\n\n"
        f"[dim]{note_a['content']}...[/dim]",
        border_style="cyan"
    ))
    
    console.print("\n[bold]Concept B:[/bold]")
    console.print(Panel(
        f"[cyan]{note_b['title']}[/cyan]\n\n"
        f"[dim]{note_b['content']}...[/dim]",
        border_style="cyan"
    ))
    
    console.print("\n[bold yellow]❓ Synthesis Questions:[/bold yellow]\n")
    console.print("1. How are these concepts similar?")
    console.print("2. How do they differ?")
    console.print("3. Can one be used to explain the other?")
    console.print("4. Is there a common use case or problem they both solve?")
    console.print("5. What NEW insight emerges from combining them?")
    
    console.print()
    
    if Confirm.ask("[bold]Would you like to create a synthesis note?[/bold]"):
        # Create synthesis note
        synthesis_content = Prompt.ask(
            "\n[cyan]Describe the connection you found[/cyan]",
            default="These concepts relate because..."
        )
        
        date = datetime.now()
        slug = f"synthesis-{date.strftime('%Y%m%d%H%M')}"
        
        synthesis_note = f"""---
title: "Synthesis: {note_a['title'][:30]} × {note_b['title'][:30]}"
date: {date.strftime('%Y-%m-%d')}
type: concept
maturity: budding
tags: [synthesis, connection]
connects:
  - [[{note_a['path'].stem}]]
  - [[{note_b['path'].stem}]]
---

# Synthesis

{synthesis_content}

## Source Concepts

### A: {note_a['title']}
See: [[{note_a['path'].stem}]]

### B: {note_b['title']}
See: [[{note_b['path'].stem}]]

## Insight

<!-- Elaborate on the NEW knowledge created -->

"""
        
        # Save
        save_dir = root / "10-19_KNOWLEDGE" / "11_public_garden" / "concepts"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        save_path = save_dir / f"{slug}.md"
        save_path.write_text(synthesis_note, encoding="utf-8")
        
        console.print()
        console.print(f"[green]✓[/green] Synthesis note created: [cyan]{save_path.relative_to(root)}[/cyan]")
        console.print("[dim]Open it to elaborate on your insight![/dim]")
    else:
        console.print("\n[dim]No problem! The mental exercise itself strengthens connections.[/dim]")
