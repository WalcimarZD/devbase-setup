"""
Template Engine
===============
Renders project templates with variable substitution.
Supports Jinja2 templating and Copier.
"""
import abc
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from jinja2 import Environment
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def get_git_author() -> Optional[str]:
    """Get git author name from git config."""
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2
        )
        return result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None

def to_pascal_case(name: str) -> str:
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))

def to_snake_case(name: str) -> str:
    return name.replace("-", "_")

def to_camel_case(name: str) -> str:
    words = name.replace("-", "_").split("_")
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])

def gather_template_context(project_name: str, interactive: bool = True) -> Dict[str, str]:
    """Gather context variables for template rendering."""
    context = {
        "project_name": project_name,
        "project_name_pascal": to_pascal_case(project_name),
        "project_name_snake": to_snake_case(project_name),
        "project_name_camel": to_camel_case(project_name),
        "author": get_git_author() or "DevBase User",
        "year": str(datetime.now().year),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
    }

    if interactive:
        console.print()
        console.print("[bold]Project Configuration[/bold]\n")
        
        context["description"] = Prompt.ask(
            "Description",
            default=f"{context['project_name_pascal']} Application"
        )
        
        context["license"] = Prompt.ask(
            "License",
            choices=["MIT", "Apache-2.0", "GPL-3.0", "UNLICENSED"],
            default="MIT"
        )
        
        context["author"] = Prompt.ask(
            "Author",
            default=context["author"]
        )
        console.print()
    else:
        context["description"] = f"{context['project_name_pascal']} Application"
        context["license"] = "MIT"

    return context


class TemplateRenderer(abc.ABC):
    """Abstract base class for template renderers."""
    
    @abc.abstractmethod
    def render(self, template_path: Path, dest_path: Path, context: Dict[str, str], interactive: bool) -> None:
        pass


class CopierRenderer(TemplateRenderer):
    """Renders templates using copier."""
    
    def render(self, template_path: Path, dest_path: Path, context: Dict[str, str], interactive: bool) -> None:
        console.print(f"[dim]Using Copier engine for {template_path.name}...[/dim]")
        
        import copier

        # Prepare data for non-interactive mode - only provide values for known questions
        data = {
            'project_name': context['project_name'],
            'description': context.get('description', f"{context['project_name']} Application"),
            'author': context.get('author', 'DevBase User'),
            'license': context.get('license', 'MIT')
        }

        try:
            if not interactive:
                # Non-interactive: provide data and use defaults for unspecified
                copier.run_copy(
                    src_path=str(template_path),
                    dst_path=str(dest_path),
                    data=data,
                    defaults=True,
                    unsafe=True,
                    quiet=True,
                )
            else:
                # Interactive: use user_defaults to pre-populate but still prompt
                copier.run_copy(
                    src_path=str(template_path),
                    dst_path=str(dest_path),
                    user_defaults=data,
                    unsafe=True,
                    quiet=False,
                )
        except Exception as e:
            console.print(f"[red]Copier failed: {e}[/red]")
            raise


class JinjaRenderer(TemplateRenderer):
    """Renders templates using Jinja2 (Legacy)."""

    def render(self, template_path: Path, dest_path: Path, context: Dict[str, str], interactive: bool) -> None:
        console.print(f"[dim]Using legacy Jinja2 engine for {template_path.name}...[/dim]")
        
        dest_path.mkdir(parents=True, exist_ok=True)
        
        for file in template_path.rglob("*"):
            if file.is_dir():
                continue

            rel_path = file.relative_to(template_path)
            
            # Skip special files
            if file.name in ("copier.yml", "copier.yaml"):
                continue

            if file.suffix == ".template":
                self._render_file(file, dest_path / rel_path.with_suffix(""), context)
            else:
                self._copy_file(file, dest_path / rel_path)

    def _render_file(self, src: Path, dest: Path, context: Dict[str, str]):
        content = src.read_text(encoding="utf-8")
        env = Environment(autoescape=True)
        template = env.from_string(content)
        rendered = template.render(**context)
        
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding="utf-8")
        console.print(f"  [green]✓[/green] {dest.name}")

    def _copy_file(self, src: Path, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        console.print(f"  [dim]→ {dest.name}[/dim]")


def generate_project_from_template(
    template_name: str,
    project_name: str,
    root: Path,
    interactive: bool = True
) -> Path:
    """
    Generate a new project from template.
    Facade that selects the appropriate renderer.
    """
    # 1. Locate template
    potential_paths = [
        root / "00-09_SYSTEM" / "05_templates" / f"__template-{template_name}",
        root / "20-29_CODE" / f"__template-{template_name}",
    ]
    
    template_dir = None
    for path in potential_paths:
        if path.exists():
            template_dir = path
            break
            
    if not template_dir:
        raise FileNotFoundError(f"Template '{template_name}' not found.")

    # 2. Destination
    dest_path = root / "20-29_CODE" / "21_monorepo_apps" / project_name
    if dest_path.exists():
        raise FileExistsError(f"Project '{project_name}' already exists")

    # 3. Context
    context = gather_template_context(project_name, interactive=interactive)

    # 4. Select Strategy
    is_copier = (template_dir / "copier.yml").exists() or (template_dir / "copier.yaml").exists()
    
    renderer: TemplateRenderer
    if is_copier:
        try:
            import copier
            renderer = CopierRenderer()
        except ImportError:
            console.print("[yellow]⚠ Copier not installed. Falling back to simple file copy (might fail).[/yellow]")
            renderer = JinjaRenderer() # Fallback, likely imperfect
    else:
        renderer = JinjaRenderer()

    # 5. Execute
    renderer.render(template_dir, dest_path, context, interactive)
    
    # 6. Persist Metadata
    try:
        import json
        import devbase
        metadata = {
            "template": template_name,
            "created_at": datetime.now().isoformat(),
            "devbase_version": devbase.__version__,
            "author": context.get("author"),
            "description": context.get("description")
        }
        (dest_path / ".devbase.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    except Exception as e:
        console.print(f"[yellow]⚠ Failed to write metadata: {e}[/yellow]")

    # 7. Generate VS Code workspace
    try:
        from devbase.utils.vscode import generate_vscode_workspace
        generate_vscode_workspace(dest_path, project_name)
    except Exception as e:
        console.print(f"[yellow]⚠ Failed to generate workspace: {e}[/yellow]")

    return dest_path

def list_available_templates(root: Path) -> List[str]:
    """List all available project templates."""
    # Search in both locations
    locations = [
        root / "00-09_SYSTEM" / "05_templates",
        root / "20-29_CODE"
    ]
    
    templates = set()
    for loc in locations:
        if loc.exists():
            for item in loc.iterdir():
                if item.is_dir() and item.name.startswith("__template-"):
                    templates.add(item.name.replace("__template-", ""))
                    
    return sorted(list(templates))
