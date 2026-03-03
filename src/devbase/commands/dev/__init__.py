"""
Development Commands Package
==============================
Architecture: Command Merger Pattern.
Flattens sub-module commands into a single 'dev' namespace.
"""
import typer

from devbase.commands.dev.project import app as project_app
from devbase.commands.dev.scaffold import app as scaffold_app
from devbase.commands.dev.audit import app as audit_app
from devbase.commands.dev.worktree import app as worktree_app

app = typer.Typer(help="Project Lifecycle & Worktrees")

# Safely merge commands from sub-apps to maintain a flat structure
# Standardizing on .registered_commands ensures all metadata (ctx, types) is preserved.
def _merge_commands():
    for source_app in [project_app, scaffold_app, audit_app, worktree_app]:
        # Merge individual commands
        for command in source_app.registered_commands:
            app.registered_commands.append(command)
        
        # Merge groups if any exist
        for group in source_app.registered_groups:
            app.registered_groups.append(group)

_merge_commands()
