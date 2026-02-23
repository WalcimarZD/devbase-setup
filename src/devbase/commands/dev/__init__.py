"""
Development Commands Package
==============================
Split from the monolithic development.py for maintainability.

Sub-modules:
    project  — new, import, open, info, list, archive, update, restore
    scaffold — blueprint, adr-gen
    audit    — audit (naming conventions)
    worktree — worktree-add, worktree-list, worktree-remove
"""
import typer

from devbase.commands.dev.project import app as project_app
from devbase.commands.dev.scaffold import app as scaffold_app
from devbase.commands.dev.audit import app as audit_app
from devbase.commands.dev.worktree import app as worktree_app

app = typer.Typer(help="Development commands")

# Register all sub-module commands onto this single Typer app
for source_app in [project_app, scaffold_app, audit_app, worktree_app]:
    for command_info in source_app.registered_commands:
        app.registered_commands.append(command_info)
    for group_info in source_app.registered_groups:
        app.registered_groups.append(group_info)
