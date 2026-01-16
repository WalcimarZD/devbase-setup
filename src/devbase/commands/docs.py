"""
Documentation Commands: new
===========================
Commands for generating standard documentation from templates.
"""
import re
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt
from typing_extensions import Annotated

app = typer.Typer(help="📚 Documentation generator")
console = Console()

TEMPLATE_MAP = {
    "decision": {
        "template": "template_decision.md",
        "dir": "00-09_SYSTEM/07_documentation/decisions",
        "prefix": "decision"
    },
    "guide": {
        "template": "template_guide.md",
        "dir": "10-19_KNOWLEDGE/10_references/guides",
        "prefix": "guide"
    },
    "spec": {
        "template": "template_spec.md",
        "dir": "00-09_SYSTEM/07_documentation/specs",
        "prefix": "spec"
    }
}

@app.command()
def new(
    ctx: typer.Context,
    doc_type: Annotated[str, typer.Argument(help="Type: decision, guide, or spec")],
    title: Annotated[str, typer.Argument(help="Document title")],
    open: Annotated[bool, typer.Option("--open", "-o", help="Open in VS Code")] = True,
) -> None:
    """
    📄 Create a new document from standard templates.
    
    Generates a file with correct naming convention and location.
    
    Examples:
        devbase docs new decision "Refactor Auth"
        devbase docs new guide "How to Debug"
        devbase docs new spec "User Profile API"
    """
    root: Path = ctx.obj["root"]
    
    # Validate type
    doc_type = doc_type.lower()
    if doc_type not in TEMPLATE_MAP:
        console.print(f"[red]Invalid type: {doc_type}[/red]")
        console.print(f"Available types: {', '.join(TEMPLATE_MAP.keys())}")
        raise typer.Exit(1)
        
    config = TEMPLATE_MAP[doc_type]
    
    # Prepare paths
    template_path = root / "00-09_SYSTEM/07_documentation/templates" / config["template"]
    dest_dir = root / config["dir"]
    
    if not template_path.exists():
        console.print(f"[red]Template not found: {template_path}[/red]")
        console.print("Run 'devbase docs init' (or check phase 5) to create templates.")
        raise typer.Exit(1)
        
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename (YYYY-MM-DD_type_kebab-title.md)
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    
    filename = f"{date_str}_{config['prefix']}_{slug}.md"
    file_path = dest_dir / filename
    
    # Read and process template
    content = template_path.read_text(encoding="utf-8")
    content = content.replace("[DATA_ATUAL]", date_str)
    content = content.replace("[Título...]", title) # Generic fallback
    content = content.replace("[Título da Decisão/Plano]", title)
    content = content.replace("[Título do Guia]", title)
    content = content.replace("[Nome da Funcionalidade]", title)
    
    # Save
    file_path.write_text(content, encoding="utf-8")
    
    console.print()
    console.print(f"[green]✓[/green] Created: [cyan]{file_path.relative_to(root)}[/cyan]")
    
    # Open in Editor
    if open:
        import shutil
        import subprocess
        if shutil.which("code"):
            subprocess.run(["code", "--", str(file_path)], check=False)
            console.print("[dim]Opened in VS Code[/dim]")
