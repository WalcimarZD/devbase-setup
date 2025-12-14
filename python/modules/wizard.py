"""
DevBase Interactive Setup Wizard
================================================================
Guides new users through setup with contextual questions.

Features:
- Developer profile selection
- Optional feature toggles (hooks, AI, PKM)
- Custom workspace location
- Summary and confirmation

Usage:
    from wizard import run_wizard
    config = run_wizard()
"""

from pathlib import Path
from typing import Dict, Any, Optional

# Try to import questionary, fallback to basic input
try:
    import questionary
    from questionary import Style
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False

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
# PROFILES
# ============================================

PROFILES = {
    "fullstack": {
        "name": "🌐 Full-Stack Developer",
        "description": "Web apps, APIs, databases",
        "hooks": True,
        "ai": True,
        "pkm": True,
    },
    "backend": {
        "name": "⚙️ Backend Developer",
        "description": "APIs, microservices, DevOps",
        "hooks": True,
        "ai": True,
        "pkm": False,
    },
    "data": {
        "name": "📊 Data Engineer / Scientist",
        "description": "ML, analytics, notebooks",
        "hooks": True,
        "ai": True,
        "pkm": True,
    },
    "minimal": {
        "name": "📦 Minimal Setup",
        "description": "Just the essentials",
        "hooks": False,
        "ai": False,
        "pkm": False,
    },
}

# Custom style for questionary
WIZARD_STYLE = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'bold'),
    ('answer', 'fg:green'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
]) if HAS_QUESTIONARY else None


def _print_header():
    """Print wizard header."""
    if HAS_RICH:
        console.print()
        console.print(Panel.fit(
            "[bold cyan]🧙 DevBase Setup Wizard[/]\n"
            "[dim]Answer a few questions to customize your setup[/]",
            border_style="cyan"
        ))
        console.print()
    else:
        print("\n" + "=" * 50)
        print("  🧙 DevBase Setup Wizard")
        print("  Answer a few questions to customize your setup")
        print("=" * 50 + "\n")


def _print_summary(config: Dict[str, Any]):
    """Print configuration summary."""
    if HAS_RICH:
        table = Table(title="Configuration Summary", show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Profile", config.get("profile_name", "Custom"))
        table.add_row("Git Hooks", "✅ Enabled" if config.get("hooks") else "❌ Disabled")
        table.add_row("AI Module", "✅ Enabled" if config.get("ai") else "❌ Disabled")
        table.add_row("PKM System", "✅ Enabled" if config.get("pkm") else "❌ Disabled")
        table.add_row("Workspace", str(config.get("root", "Default")))
        
        console.print()
        console.print(table)
        console.print()
    else:
        print("\n--- Configuration Summary ---")
        print(f"  Profile:   {config.get('profile_name', 'Custom')}")
        print(f"  Hooks:     {'Yes' if config.get('hooks') else 'No'}")
        print(f"  AI:        {'Yes' if config.get('ai') else 'No'}")
        print(f"  PKM:       {'Yes' if config.get('pkm') else 'No'}")
        print(f"  Workspace: {config.get('root', 'Default')}")
        print()


def _ask_with_fallback(question: str, choices: list = None, default: bool = True) -> Any:
    """Ask a question with fallback to basic input."""
    if HAS_QUESTIONARY and choices:
        return questionary.select(
            question,
            choices=choices,
            style=WIZARD_STYLE
        ).ask()
    elif HAS_QUESTIONARY:
        return questionary.confirm(
            question,
            default=default,
            style=WIZARD_STYLE
        ).ask()
    else:
        # Fallback to basic input
        if choices:
            print(f"\n{question}")
            for i, choice in enumerate(choices, 1):
                label = choice.title if hasattr(choice, 'title') else str(choice)
                print(f"  {i}. {label}")
            while True:
                try:
                    selection = int(input("Enter number: "))
                    if 1 <= selection <= len(choices):
                        choice = choices[selection - 1]
                        return choice.value if hasattr(choice, 'value') else choice
                except ValueError:
                    pass
                print("Invalid selection. Try again.")
        else:
            response = input(f"{question} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
            if not response:
                return default
            return response in ('y', 'yes')


def run_wizard() -> Dict[str, Any]:
    """
    Run the interactive setup wizard.
    
    Returns:
        Dict with configuration options:
        - profile: str - Selected profile key
        - hooks: bool - Enable git hooks
        - ai: bool - Enable AI module
        - pkm: bool - Enable PKM system
        - root: Optional[Path] - Custom workspace path
    """
    _print_header()
    
    # Step 1: Select profile
    if HAS_QUESTIONARY:
        choices = [
            questionary.Choice(
                title=f"{p['name']} - {p['description']}",
                value=key
            )
            for key, p in PROFILES.items()
        ]
        profile_key = questionary.select(
            "What type of developer are you?",
            choices=choices,
            style=WIZARD_STYLE
        ).ask()
    else:
        print("What type of developer are you?")
        for i, (key, p) in enumerate(PROFILES.items(), 1):
            print(f"  {i}. {p['name']} - {p['description']}")
        while True:
            try:
                selection = int(input("Enter number: "))
                if 1 <= selection <= len(PROFILES):
                    profile_key = list(PROFILES.keys())[selection - 1]
                    break
            except ValueError:
                pass
            print("Invalid selection.")
    
    if profile_key is None:
        return None  # User cancelled
    
    profile = PROFILES[profile_key]
    config = {
        "profile": profile_key,
        "profile_name": profile["name"],
        "hooks": profile["hooks"],
        "ai": profile["ai"],
        "pkm": profile["pkm"],
        "root": None,
    }
    
    # Step 2: Customize options if not minimal
    if profile_key != "minimal":
        print()
        
        # Git Hooks
        if not config["hooks"]:
            config["hooks"] = _ask_with_fallback(
                "Enable Git Hooks for commit validation?",
                default=True
            )
        
        # AI Module
        if not config["ai"]:
            config["ai"] = _ask_with_fallback(
                "Enable AI Assistant module (requires Ollama)?",
                default=False
            )
    
    # Step 3: Custom workspace location
    print()
    use_custom = _ask_with_fallback(
        "Use custom workspace location?",
        default=False
    )
    
    if use_custom:
        if HAS_QUESTIONARY:
            custom_path = questionary.path(
                "Enter workspace path:",
                only_directories=True,
                style=WIZARD_STYLE
            ).ask()
            if custom_path:
                config["root"] = Path(custom_path)
        else:
            custom_path = input("Enter workspace path: ").strip()
            if custom_path:
                config["root"] = Path(custom_path)
    
    # Step 4: Show summary and confirm
    _print_summary(config)
    
    confirm = _ask_with_fallback(
        "Proceed with this configuration?",
        default=True
    )
    
    if not confirm:
        print("\nRestarting wizard...\n")
        return run_wizard()
    
    return config


def apply_wizard_config(config: Dict[str, Any], args) -> None:
    """
    Apply wizard configuration to args namespace.
    
    Args:
        config: Configuration from run_wizard()
        args: argparse.Namespace to modify
    """
    if config is None:
        return
    
    if config.get("root"):
        args.root = config["root"]
    
    # Store config for use by setup modules
    args.wizard_config = config


if __name__ == "__main__":
    # Test the wizard
    result = run_wizard()
    print(f"\nResult: {result}")
