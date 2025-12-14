"""
DevBase CLI UX Helpers
================================================================
Better error messages, command suggestions, and progressive disclosure.

Features:
- Typo correction with suggestions
- Rich error formatting
- Essential vs full command lists
- Contextual help

Usage:
    from cli_ux import show_error, suggest_command, show_essential_commands
"""

from difflib import get_close_matches
from typing import Optional, List, Dict

# Try to import rich for formatting
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


# ============================================
# COMMAND DEFINITIONS
# ============================================

COMMANDS: Dict[str, Dict[str, str]] = {
    # Essential commands (shown by default)
    "setup": {
        "description": "Initialize your workspace",
        "example": "devbase setup",
        "essential": True,
    },
    "doctor": {
        "description": "Check workspace health",
        "example": "devbase doctor",
        "essential": True,
    },
    "new": {
        "description": "Create a new project",
        "example": "devbase new my-project",
        "essential": True,
    },
    # Productivity commands
    "hydrate": {
        "description": "Sync templates to latest",
        "example": "devbase hydrate",
        "essential": False,
    },
    "backup": {
        "description": "Create 3-2-1 backup",
        "example": "devbase backup",
        "essential": False,
    },
    "clean": {
        "description": "Remove temp files",
        "example": "devbase clean",
        "essential": False,
    },
    # Tracking commands
    "track": {
        "description": "Log an activity",
        "example": "devbase track 'Finished feature X'",
        "essential": False,
    },
    "stats": {
        "description": "Show usage statistics",
        "example": "devbase stats",
        "essential": False,
    },
    "weekly": {
        "description": "Generate weekly report",
        "example": "devbase weekly",
        "essential": False,
    },
    # Advanced commands
    "audit": {
        "description": "Check naming conventions",
        "example": "devbase audit",
        "essential": False,
    },
    "dashboard": {
        "description": "Open web dashboard",
        "example": "devbase dashboard",
        "essential": False,
    },
    "ai": {
        "description": "AI assistant (requires Ollama)",
        "example": "devbase ai chat",
        "essential": False,
    },
    "onboarding": {
        "description": "Show onboarding progress",
        "example": "devbase onboarding",
        "essential": False,
    },
}

COMMAND_NAMES = list(COMMANDS.keys())
ESSENTIAL_COMMANDS = [k for k, v in COMMANDS.items() if v.get("essential")]


def suggest_command(invalid: str) -> Optional[str]:
    """
    Suggest similar commands for typo correction.
    
    Args:
        invalid: The invalid command entered by user
        
    Returns:
        Suggested command or None if no match found
    """
    matches = get_close_matches(invalid, COMMAND_NAMES, n=1, cutoff=0.6)
    return matches[0] if matches else None


def show_error(
    message: str,
    suggestion: Optional[str] = None,
    help_url: Optional[str] = None,
    command: Optional[str] = None
) -> None:
    """
    Show rich error message with suggestions.
    
    Args:
        message: Error message to display
        suggestion: Optional suggested command
        help_url: Optional URL for more info
        command: Optional correct command example
    """
    if HAS_RICH:
        content = f"[red bold]❌ Error:[/] {message}"
        
        if suggestion:
            content += f"\n\n[yellow]💡 Did you mean:[/] devbase {suggestion}"
        
        if command:
            content += f"\n\n[cyan]📝 Example:[/] {command}"
        
        if help_url:
            content += f"\n\n[dim]📖 For more info: {help_url}[/]"
        
        console.print()
        console.print(Panel(content, title="DevBase", border_style="red"))
        console.print()
    else:
        print(f"\n❌ Error: {message}")
        if suggestion:
            print(f"💡 Did you mean: devbase {suggestion}")
        if command:
            print(f"📝 Example: {command}")
        if help_url:
            print(f"📖 For more info: {help_url}")
        print()


def show_success(message: str, next_steps: List[str] = None) -> None:
    """
    Show success message with optional next steps.
    
    Args:
        message: Success message
        next_steps: Optional list of suggested next steps
    """
    if HAS_RICH:
        content = f"[green bold]✅ {message}[/]"
        
        if next_steps:
            content += "\n\n[bold]Next steps:[/]"
            for i, step in enumerate(next_steps, 1):
                content += f"\n  {i}. {step}"
        
        console.print()
        console.print(Panel(content, title="DevBase", border_style="green"))
        console.print()
    else:
        print(f"\n✅ {message}")
        if next_steps:
            print("\nNext steps:")
            for i, step in enumerate(next_steps, 1):
                print(f"  {i}. {step}")
        print()


def show_essential_commands() -> None:
    """Show only essential commands for new users."""
    if HAS_RICH:
        console.print()
        console.print("[bold cyan]🚀 Essential Commands[/]")
        console.print()
        
        for cmd_name in ESSENTIAL_COMMANDS:
            cmd = COMMANDS[cmd_name]
            console.print(f"  [green]devbase {cmd_name}[/]")
            console.print(f"  [dim]{cmd['description']}[/]")
            console.print()
        
        console.print("[dim]Run 'devbase --all' to see all commands[/]")
        console.print()
    else:
        print("\n🚀 Essential Commands\n")
        for cmd_name in ESSENTIAL_COMMANDS:
            cmd = COMMANDS[cmd_name]
            print(f"  devbase {cmd_name} - {cmd['description']}")
        print("\nRun 'devbase --all' to see all commands\n")


def show_all_commands() -> None:
    """Show all available commands grouped by category."""
    if HAS_RICH:
        table = Table(title="DevBase Commands", show_header=True)
        table.add_column("Command", style="green")
        table.add_column("Description", style="white")
        table.add_column("Example", style="dim")
        
        # Essential first
        for cmd_name in ESSENTIAL_COMMANDS:
            cmd = COMMANDS[cmd_name]
            table.add_row(
                f"⭐ {cmd_name}",
                cmd["description"],
                cmd["example"]
            )
        
        # Then the rest
        for cmd_name, cmd in COMMANDS.items():
            if cmd_name not in ESSENTIAL_COMMANDS:
                table.add_row(
                    cmd_name,
                    cmd["description"],
                    cmd["example"]
                )
        
        console.print()
        console.print(table)
        console.print()
    else:
        print("\n=== DevBase Commands ===\n")
        print("Essential:")
        for cmd_name in ESSENTIAL_COMMANDS:
            cmd = COMMANDS[cmd_name]
            print(f"  ⭐ {cmd_name:12} - {cmd['description']}")
        
        print("\nAll Commands:")
        for cmd_name, cmd in COMMANDS.items():
            if cmd_name not in ESSENTIAL_COMMANDS:
                print(f"  {cmd_name:12} - {cmd['description']}")
        print()


def get_command_help(command: str) -> Optional[str]:
    """
    Get detailed help for a specific command.
    
    Args:
        command: Command name
        
    Returns:
        Help text or None if command not found
    """
    if command not in COMMANDS:
        return None
    
    cmd = COMMANDS[command]
    help_text = f"""
Command: devbase {command}

Description:
  {cmd['description']}

Example:
  {cmd['example']}

For more options, run:
  devbase {command} --help
"""
    return help_text


if __name__ == "__main__":
    # Test CLI UX functions
    print("Testing show_essential_commands:")
    show_essential_commands()
    
    print("\nTesting show_all_commands:")
    show_all_commands()
    
    print("\nTesting show_error:")
    show_error(
        "Command 'seutp' not found",
        suggestion="setup",
        command="devbase setup"
    )
    
    print("\nTesting suggest_command:")
    print(f"  'seutp' -> {suggest_command('seutp')}")
    print(f"  'dctr' -> {suggest_command('dctr')}")
    print(f"  'xyz' -> {suggest_command('xyz')}")
