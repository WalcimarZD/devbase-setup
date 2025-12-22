"""
Template Engine
===============
Renders project templates with variable substitution.
Supports Jinja2 templating for customizable scaffolding.
"""
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

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
    """Convert kebab-case to PascalCase."""
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


def to_snake_case(name: str) -> str:
    """Convert kebab-case to snake_case."""
    return name.replace("-", "_")


def to_camel_case(name: str) -> str:
    """Convert kebab-case to camelCase."""
    words = name.replace("-", "_").split("_")
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def gather_template_context(project_name: str, interactive: bool = True) -> Dict[str, str]:
    """
    Gather context variables for template rendering.
    
    Args:
        project_name: Base project name (kebab-case)
        interactive: If True, prompt user for additional info
        
    Returns:
        dict: Template context variables
    """
    context = {
        # Project names in various cases
        "project_name": project_name,
        "project_name_pascal": to_pascal_case(project_name),
        "project_name_snake": to_snake_case(project_name),
        "project_name_camel": to_camel_case(project_name),

        # Metadata
        "author": get_git_author() or "DevBase User",
        "year": str(datetime.now().year),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
    }

    if interactive:
        console.print()
        console.print("[bold]Project Configuration[/bold]\n")

        # Description
        description = Prompt.ask(
            "Description",
            default=f"{context['project_name_pascal']} Application"
        )
        context["description"] = description

        # License
        license_choice = Prompt.ask(
            "License",
            choices=["MIT", "Apache-2.0", "GPL-3.0", "UNLICENSED"],
            default="MIT"
        )
        context["license"] = license_choice

        # Author (confirm/override)
        author_confirmed = Prompt.ask(
            "Author",
            default=context["author"]
        )
        context["author"] = author_confirmed

        console.print()
    else:
        # Non-interactive defaults
        context["description"] = f"{context['project_name_pascal']} Application"
        context["license"] = "MIT"

    return context


def render_template_file(template_path: Path, context: Dict[str, str]) -> str:
    """
    Render a single template file using Jinja2.
    
    Args:
        template_path: Path to template file
        context: Template variables
        
    Returns:
        str: Rendered content
    """
    # Read template
    content = template_path.read_text(encoding="utf-8")

    # Create Jinja2 environment
    env = Environment(autoescape=False)
    template = env.from_string(content)

    # Render
    return template.render(**context)


def generate_project_from_template(
    template_name: str,
    project_name: str,
    root: Path,
    interactive: bool = True
) -> Path:
    """
    Generate a new project from template with variable substitution.
    
    Args:
        template_name: Template name (e.g., "clean-arch", "api", "cli")
        project_name: Name of new project (kebab-case)
        root: Workspace root
        interactive: If True, prompt for additional context
        
    Returns:
        Path: Path to created project
    """
    # Locate template
    template_dir = root / "00-09_SYSTEM" / "05_templates" / f"__template-{template_name}"

    if not template_dir.exists():
        raise FileNotFoundError(f"Template '{template_name}' not found at {template_dir}")

    # Gather context
    context = gather_template_context(project_name, interactive=interactive)

    # Destination
    dest_path = root / "20-29_CODE" / "21_monorepo_apps" / project_name

    if dest_path.exists():
        raise FileExistsError(f"Project '{project_name}' already exists")

    dest_path.mkdir(parents=True)

    # Copy and render files
    console.print(f"[dim]Generating from template: {template_name}[/dim]")

    for file in template_dir.rglob("*"):
        if file.is_dir():
            continue

        # Calculate relative path
        rel_path = file.relative_to(template_dir)

        # Determine destination file
        if file.suffix == ".template":
            # Remove .template extension and render
            dest_file = dest_path / rel_path.with_suffix("")

            # Render template
            rendered = render_template_file(file, context)

            # Write
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(rendered, encoding="utf-8")

            console.print(f"  [green]✓[/green] {dest_file.name}")
        else:
            # Copy as-is (binary files, images, etc.)
            dest_file = dest_path / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(file.read_bytes())

            console.print(f"  [dim]→ {dest_file.name}[/dim]")

    return dest_path


def list_available_templates(root: Path) -> list[str]:
    """
    List all available project templates.
    
    Args:
        root: Workspace root
        
    Returns:
        list: Template names (without __template- prefix)
    """
    templates_dir = root / "00-09_SYSTEM" / "05_templates"

    if not templates_dir.exists():
        return []

    templates = []
    for item in templates_dir.iterdir():
        if item.is_dir() and item.name.startswith("__template-"):
            template_name = item.name.replace("__template-", "")
            templates.append(template_name)

    return sorted(templates)
