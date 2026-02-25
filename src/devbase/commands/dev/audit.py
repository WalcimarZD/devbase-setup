"""
Audit Commands
===============
Workspace naming convention audit.
"""
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any

import typer
from rich.console import Console
from typing_extensions import Annotated

from devbase.utils.config import get_config

app = typer.Typer()
console = Console()


def is_ignored(path: Path, root: Path) -> bool:
    """Check if path is ignored by git. Silent failure if git not present."""
    try:
        # Resolve path relative to root to avoid absolute path issues with git
        rel_path = path.relative_to(root)
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(rel_path)],
            cwd=root,
            capture_output=True
        )
        return result.returncode == 0
    except Exception:
        return False


def validate_johnny_decimal(name: str, pattern: str) -> bool:
    """Verify if folder follows Johnny.Decimal XX-XX_Name."""
    return bool(re.match(pattern, name))


def validate_markdown_naming(path: Path) -> bool:
    """Verify kebab-case for Markdown files."""
    if path.suffix.lower() != '.md':
        return True
    name_no_ext = path.stem
    return bool(re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name_no_ext))


def validate_content_patterns(path: Path, patterns: List[str]) -> List[str]:
    """Check for prohibited patterns in file content."""
    found = []
    if not path.is_file():
        return found
    try:
        # Only check text files (basic heuristic)
        if path.suffix.lower() not in ['.md', '.py', '.js', '.ts', '.ps1', '.txt', '.toml', '.json', '.yaml', '.yml']:
            return found
            
        content = path.read_text(encoding='utf-8', errors='ignore')
        for p in patterns:
            if re.search(p, content):
                found.append(p)
    except Exception:
        pass
    return found


@app.command()
def audit(
    ctx: typer.Context,
    fix: Annotated[
        bool,
        typer.Option("--fix", help="Automatically fix violations where possible"),
    ] = False,
) -> None:
    """
    🔍 DevBase Universal Governance Audit.

    Validates:
    1. Johnny.Decimal (XX-XX_Name) for folders.
    2. kebab-case for Markdown files.
    3. Prohibited regex patterns in tracked content.
    
    Respects .gitignore: Ignored files are invisible to the audit.
    """
    root: Path = ctx.obj["root"]
    config = get_config()
    
    # Load rules from config
    rules = config.get("audit.rules", {})
    jd_config = rules.get("johnny_decimal", {"enabled": True, "pattern": r"^\d{2}-\d{2}_[A-Z][a-zA-Z0-9_]*$"})
    naming_config = rules.get("naming", {"markdown_kebab_case": True})
    patterns_config = rules.get("patterns", {"prohibited_patterns": []})
    
    console.print()
    console.print("[bold]DevBase Universal Governance Audit[/bold]")
    console.print(f"Workspace: [cyan]{root}[/cyan]\n")

    violations = []

    with console.status("[bold cyan]Analyzing files (respecting .gitignore)...[/bold cyan]"):
        # We scan everything, but filter out ignored items
        for item in root.rglob('*'):
            # 1. Privacy Filter: Soberania do .gitignore
            if is_ignored(item, root):
                continue

            # Standard ignore list for speed/sanity (non-git items)
            if any(part.startswith('.') for part in item.relative_to(root).parts if part != '.'):
                if not (item.is_file() and item.name == '.gitignore'): # Keep gitignore itself? Usually yes.
                    continue

            # 2. Johnny.Decimal Validation (Folders only)
            if item.is_dir() and jd_config.get("enabled"):
                # Only check top-level-ish folders or specific categories? 
                # TDD says folders must follow XX-XX_Nome.
                # We check folders that look like they should be Johnny.Decimal (start with digits)
                if re.match(r'^\d{2}', item.name):
                    if not validate_johnny_decimal(item.name, jd_config.get("pattern")):
                        violations.append({
                            'type': 'Johnny.Decimal',
                            'path': item,
                            'message': f"Folder '{item.name}' violates XX-XX_Nome convention."
                        })

            # 3. Naming Validation (Markdown kebab-case)
            if item.is_file() and naming_config.get("markdown_kebab_case"):
                if not validate_markdown_naming(item):
                    violations.append({
                        'type': 'Naming',
                        'path': item,
                        'message': f"Markdown file '{item.name}' must be kebab-case."
                    })

            # 4. Prohibited Patterns Validation
            if item.is_file():
                prohibited = patterns_config.get("prohibited_patterns", [])
                if prohibited:
                    found = validate_content_patterns(item, prohibited)
                    for p in found:
                        violations.append({
                            'type': 'Pattern',
                            'path': item,
                            'message': f"Prohibited pattern '{p}' found in content."
                        })

    if not violations:
        console.print("[bold green]✅ Governance Audit Passed: No violations found.[/bold green]")
        return
    else:
        console.print(f"[yellow]Found {len(violations)} governance violation(s):[/yellow]\n")

        for v in violations:
            color = "red" if v['type'] == 'Pattern' else "yellow"
            console.print(f"  [{color}]✗ [bold]{v['type']}:[/bold] {v['message']}[/{color}]")
            console.print(f"    [dim]Path: {v['path'].relative_to(root)}[/dim]\n")

        if fix:
            console.print("[bold]Attempting to fix naming violations...[/bold]")
            # Pattern violations can't be easily auto-fixed safely
            for v in [v for v in violations if v['type'] in ['Johnny.Decimal', 'Naming']]:
                try:
                    # Simple fix logic
                    name = v['path'].name
                    if v['type'] == 'Naming':
                        # kebab-case fix
                        suggestion = re.sub(r'([a-z])([A-Z])', r'\1-\2', v['path'].stem).lower()
                        suggestion = re.sub(r'[_ ]', '-', suggestion) + v['path'].suffix
                    else:
                        # JD fix: XX-XX-Name to XX-XX_Name
                        suggestion = re.sub(r'^(\d{2})-(\d{2})[- ]', r'\1-\2_', name)
                    
                    new_path = v['path'].parent / suggestion
                    v['path'].rename(new_path)
                    console.print(f"  [green]✓[/green] Fixed: {name} → {suggestion}")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed to fix {v['path'].name}: {e}")
        
        # Pre-commit hook depends on exit code
        raise typer.Exit(code=1)
