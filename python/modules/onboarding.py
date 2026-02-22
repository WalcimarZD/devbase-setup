"""
DevBase Onboarding Tracker
================================================================
Tracks user progress through onboarding checklist.

Features:
- Persistent checklist state
- Auto-detection of completed items
- Progress display
- Integration with CLI and dashboard

Usage:
    from onboarding import OnboardingTracker, show_onboarding
    tracker = OnboardingTracker(root)
    tracker.show_checklist()
"""

import json
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

# Try to import rich for formatting
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


# ============================================
# CHECKLIST ITEMS
# ============================================

CHECKLIST = [
    {
        "id": "install",
        "title": "Install DevBase",
        "description": "Clone repository and install dependencies",
        "command": None,
        "auto_check": "state_exists",
    },
    {
        "id": "setup",
        "title": "Run initial setup",
        "description": "Initialize your workspace structure",
        "command": "devbase setup",
        "auto_check": "state_version",
    },
    {
        "id": "doctor",
        "title": "Verify installation",
        "description": "Check that everything is working",
        "command": "devbase doctor",
        "auto_check": None,
    },
    {
        "id": "new_project",
        "title": "Create first project",
        "description": "Create a project from the clean-arch template",
        "command": "devbase new my-project",
        "auto_check": "project_exists",
    },
    {
        "id": "first_til",
        "title": "Write a TIL note",
        "description": "Document something you learned today",
        "command": None,
        "auto_check": "til_exists",
    },
    {
        "id": "git_commit",
        "title": "Make a commit",
        "description": "Test git hooks with a real commit",
        "command": None,
        "auto_check": None,
    },
    {
        "id": "backup",
        "title": "Run first backup",
        "description": "Create your first 3-2-1 backup",
        "command": "devbase backup",
        "auto_check": "backup_exists",
    },
    {
        "id": "explore_ai",
        "title": "Try AI assistant",
        "description": "Chat with the AI about DevBase",
        "command": "devbase ai chat",
        "auto_check": None,
    },
]


class OnboardingTracker:
    """
    Tracks user progress through onboarding checklist.
    
    State is stored in .devbase_onboarding.json in the workspace root.
    """
    
    def __init__(self, root: Path):
        self.root = Path(root)
        self.state_file = self.root / ".devbase_onboarding.json"
        self.state = self._load()
    
    def _load(self) -> dict:
        """Load state from file."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "completed": [],
            "started_at": datetime.now().isoformat(),
            "last_updated": None,
        }
    
    def _save(self) -> None:
        """Save state to file."""
        self.state["last_updated"] = datetime.now().isoformat()
        self.state_file.write_text(
            json.dumps(self.state, indent=2),
            encoding="utf-8"
        )
    
    def _auto_check(self, item: dict) -> bool:
        """Auto-detect if an item is completed."""
        check_type = item.get("auto_check")
        
        if check_type == "state_exists":
            return (self.root / ".devbase_state.json").exists()
        
        elif check_type == "state_version":
            state_file = self.root / ".devbase_state.json"
            if state_file.exists():
                try:
                    data = json.loads(state_file.read_text())
                    return data.get("version", "0.0.0") != "0.0.0"
                except:
                    pass
            return False
        
        elif check_type == "project_exists":
            projects = self.root / "20-29_CODE" / "21_monorepo_apps"
            if projects.exists():
                # Check if there's any project besides template
                for item in projects.iterdir():
                    if item.is_dir() and not item.name.startswith("__"):
                        return True
            return False
        
        elif check_type == "til_exists":
            til_dir = self.root / "10-19_KNOWLEDGE" / "11_public_garden" / "til"
            if til_dir.exists():
                return any(til_dir.glob("*.md"))
            return False
        
        elif check_type == "backup_exists":
            backup_dir = self.root / "30-39_OPERATIONS" / "31_backups" / "local"
            if backup_dir.exists():
                return any(backup_dir.iterdir())
            return False
        
        return False
    
    def is_completed(self, item_id: str) -> bool:
        """Check if an item is completed (manually or auto-detected)."""
        if item_id in self.state["completed"]:
            return True
        
        # Try auto-detection
        for item in CHECKLIST:
            if item["id"] == item_id and item.get("auto_check"):
                return self._auto_check(item)
        
        return False
    
    def complete(self, item_id: str) -> None:
        """Mark an item as completed."""
        if item_id not in self.state["completed"]:
            self.state["completed"].append(item_id)
            self._save()
    
    def uncomplete(self, item_id: str) -> None:
        """Mark an item as not completed."""
        if item_id in self.state["completed"]:
            self.state["completed"].remove(item_id)
            self._save()
    
    def get_progress(self) -> Tuple[int, int]:
        """Get completion progress (completed, total)."""
        completed = sum(1 for item in CHECKLIST if self.is_completed(item["id"]))
        return completed, len(CHECKLIST)
    
    def get_next_item(self) -> Optional[dict]:
        """Get the next uncompleted item."""
        for item in CHECKLIST:
            if not self.is_completed(item["id"]):
                return item
        return None
    
    def show_checklist(self) -> None:
        """Display the onboarding checklist."""
        completed, total = self.get_progress()
        
        if HAS_RICH:
            console.print()
            console.print("[bold cyan]🎯 DevBase Onboarding Checklist[/]")
            console.print()
            
            # Progress bar
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green"),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Progress", total=total, completed=completed)
            
            console.print(f"  Progress: {completed}/{total} ({completed/total*100:.0f}%)")
            console.print()
            
            # Checklist table
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Status", width=3)
            table.add_column("Item")
            table.add_column("Command", style="dim")
            
            for item in CHECKLIST:
                is_done = self.is_completed(item["id"])
                status = "[green]✅[/]" if is_done else "[dim]⬜[/]"
                title = f"[dim]{item['title']}[/]" if is_done else item["title"]
                cmd = item.get("command", "")
                
                table.add_row(status, title, cmd)
            
            console.print(table)
            console.print()
            
            # Next step suggestion
            next_item = self.get_next_item()
            if next_item:
                console.print(f"[yellow]👉 Next:[/] {next_item['title']}")
                if next_item.get("command"):
                    console.print(f"   [dim]Run: {next_item['command']}[/]")
            else:
                console.print("[green bold]🎉 Congratulations! You've completed onboarding![/]")
            
            console.print()
        else:
            print("\n🎯 DevBase Onboarding Checklist")
            print(f"Progress: {completed}/{total} ({completed/total*100:.0f}%)\n")
            
            for item in CHECKLIST:
                is_done = self.is_completed(item["id"])
                status = "✅" if is_done else "⬜"
                cmd = f" ({item['command']})" if item.get("command") else ""
                print(f"  {status} {item['title']}{cmd}")
            
            print()
            next_item = self.get_next_item()
            if next_item:
                print(f"👉 Next: {next_item['title']}")
            else:
                print("🎉 Congratulations! You've completed onboarding!")
            print()


def show_onboarding(root: Path) -> None:
    """Convenience function to show onboarding checklist."""
    tracker = OnboardingTracker(root)
    tracker.show_checklist()


if __name__ == "__main__":
    # Test with current directory
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    show_onboarding(root)
