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

# Import command functions directly for standard registration
from devbase.commands.dev.project import (
    new, import_project, open_project, restore_packages, restore_project, info_project, list_projects, archive, update
)
from devbase.commands.dev.scaffold import blueprint, adr_gen
from devbase.commands.dev.audit import audit
from devbase.commands.dev.worktree import worktree_add, worktree_list, worktree_remove

app = typer.Typer(help="Development commands")

# Standard registration ensures correct argument parsing and context (ctx) propagation
# Project commands
app.command(name="new")(new)
app.command(name="import")(import_project)
app.command(name="open")(open_project)
app.command(name="restore-packages")(restore_packages)
app.command(name="restore")(restore_project)
app.command(name="info")(info_project)
app.command(name="list")(list_projects)
app.command(name="archive")(archive)
app.command(name="update")(update)

# Scaffold commands
app.command(name="blueprint")(blueprint)
app.command(name="adr-gen")(adr_gen)

# Audit commands
app.command(name="audit")(audit)

# Worktree commands
app.command(name="worktree-add")(worktree_add)
app.command(name="worktree-list")(worktree_list)
app.command(name="worktree-remove")(worktree_remove)
