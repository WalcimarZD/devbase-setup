"""
Consistency Audit Command
=========================

Performs automated consistency checks between code and documentation.
Ensures no "Documentation Debt" accumulates.
"""
import ast
import os
import sys
import toml
import inspect
import subprocess
import re
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
from datetime import datetime, timedelta

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()
app = typer.Typer()

@app.command("run")
def consistency_audit(
    ctx: typer.Context,
    fix: bool = typer.Option(False, "--fix", help="Attempt to automatically fix issues where possible."),
    days: int = typer.Option(1, "--days", help="Number of days back to check for changes.")
):
    """
    Run a consistency audit between Code and Documentation.
    Checks: Dependencies, CLI Commands, Database Integrity.
    """
    # Use workspace root from context if available, else current directory
    root = ctx.obj.get("root", Path.cwd()) if ctx.obj else Path.cwd()

    report = {
        "updated": [],
        "warnings": [],
        "suggestions": []
    }

    console.print(Panel("[bold blue]DevBase Consistency Audit[/bold blue]", subtitle="v5.1 Alpha"))

    # 1. Diff Analysis (Simulated/Best Effort)
    # ----------------------------------------
    console.print("[bold]1. Analyzing Changes...[/bold]")
    changes = _analyze_changes(root, days)
    if changes:
        console.print(f"   Found {len(changes)} modified/new files in src/devbase/ in last {days} days.")
    else:
        console.print("   No recent code changes detected.")

    # 2. Verify Dependencies
    # ----------------------
    console.print("\n[bold]2. Verifying Dependencies...[/bold]")
    _verify_dependencies(root, report)

    # 3. Synchronization CLI
    # ----------------------
    console.print("\n[bold]3. Verifying CLI Consistency...[/bold]")
    _verify_cli_consistency(root, report, fix)

    # 4. Graph & DB Integrity
    # -----------------------
    console.print("\n[bold]4. Verifying DB Schema Integrity...[/bold]")
    _verify_db_integrity(root, report)

    # 5. Changelog
    # ------------
    if changes:
        console.print("\n[bold]5. Checking Changelog...[/bold]")
        _check_changelog(root, report, changes, fix)

    # Report Execution
    # ----------------
    console.print("\n[bold underline]Audit Summary:[/bold underline]\n")

    if report["updated"]:
        table = Table(title="✅ Updated Files", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        table = Table(title="⚠️ Inconsistencies Found", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        table = Table(title="📝 Suggestions", show_header=False, box=None, style="blue")
        for item in report["suggestions"]:
            table.add_row(f"📝 {item}")
        console.print(table)

    if not report["updated"] and not report["warnings"] and not report["suggestions"]:
        console.print("[green]System is consistent! Good job.[/green]")

def _analyze_changes(root: Path, days: int) -> List[str]:
    """
    Analyze changes in src/devbase in the last N days using git if available,
    otherwise check mtime.
    """
    changed_files = []
    src_path = root / "src/devbase"

    # Try git first
    try:
        # Get files changed in last N days
        # git log --since="1 day ago" --name-only --pretty=format: src/devbase
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        result = subprocess.run(
            ["git", "log", f"--since={since_date}", "--name-only", "--pretty=format:", str(src_path)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            files = result.stdout.strip().split('\n')
            changed_files = [f for f in files if f.strip()]
            return list(set(changed_files))
    except Exception:
        pass

    # Fallback to mtime
    cutoff = datetime.now().timestamp() - (days * 86400)
    for path in src_path.rglob("*"):
        if path.is_file():
            if path.stat().st_mtime > cutoff:
                changed_files.append(str(path.relative_to(root)))

    return changed_files

def _verify_dependencies(root: Path, report: Dict[str, List[str]]):
    """Check pyproject.toml vs ARCHITECTURE.md and README.md"""
    pyproject_path = root / "pyproject.toml"
    arch_path = root / "ARCHITECTURE.md"
    readme_path = root / "README.md"

    if not pyproject_path.exists():
        report["warnings"].append("pyproject.toml not found.")
        return

    try:
        pyproject = toml.load(pyproject_path)
        project_config = pyproject.get("project", {})
        deps = project_config.get("dependencies", [])
        optional_deps = project_config.get("optional-dependencies", {})

        all_deps = list(deps)
        for _, opt_list in optional_deps.items():
            all_deps.extend(opt_list)

        # Extract package names (basic parsing)
        pkg_names = []
        for dep in all_deps:
            # Handle "package>=version" or "package"
            name = dep.split(">")[0].split("<")[0].split("=")[0].strip()
            pkg_names.append(name)

        # Check docs
        arch_content = arch_path.read_text() if arch_path.exists() else ""
        readme_content = readme_path.read_text() if readme_path.exists() else ""

        missing_in_arch = []
        missing_in_readme = []

        # Dependencies to ignore (standard or very common tools that might not need explicit arch docs)
        ignore_libs = ["toml", "jinja2", "shellingham", "python-frontmatter", "copier"]

        for pkg in pkg_names:
            if pkg in ignore_libs:
                continue

            if pkg not in arch_content:
                missing_in_arch.append(pkg)

            # README usually doesn't list all deps, but prompt says "mentioned in ARCHITECTURE.md and README.md"
            if pkg not in readme_content:
                missing_in_readme.append(pkg)

        if missing_in_arch:
            report["warnings"].append(f"Dependencies missing in ARCHITECTURE.md: {', '.join(missing_in_arch)}")

        if missing_in_readme:
             report["suggestions"].append(f"Dependencies missing in README.md: {', '.join(missing_in_readme)}")

    except Exception as e:
        report["warnings"].append(f"Failed to verify dependencies: {e}")

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands and flags vs Documentation using AST."""
    commands_dir = root / "src" / "devbase" / "commands"
    if not commands_dir.exists():
         report["warnings"].append("src/devbase/commands not found.")
         return

    found_commands: Dict[str, List[Dict[str, Any]]] = {} # module -> list of {name: cmd, flags: [flags]}

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        try:
            tree = ast.parse(cmd_file.read_text())
            module_commands = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for decorators
                    is_command = False
                    cmd_name = node.name # Default to function name

                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            # Check for @app.command("name")
                            if hasattr(decorator.func, 'attr') and decorator.func.attr == 'command':
                                is_command = True
                                if decorator.args and isinstance(decorator.args[0], ast.Constant): # Python 3.8+
                                     cmd_name = decorator.args[0].value
                                elif decorator.args and isinstance(decorator.args[0], ast.Str): # Python < 3.8
                                     cmd_name = decorator.args[0].s

                    if is_command:
                        # Extract arguments as potential flags
                        flags = []
                        for arg in node.args.args:
                            # Typer converts function args to kebab-case flags
                            # e.g. "my_flag" -> "--my-flag"
                            flag_name = "--" + arg.arg.replace("_", "-")
                            # Ignore context
                            if arg.arg != "ctx":
                                flags.append(flag_name)

                        module_commands.append({"name": cmd_name, "flags": flags})

            if module_commands:
                found_commands[cmd_file.stem] = module_commands

        except Exception as e:
            report["warnings"].append(f"Failed to parse {cmd_file.name}: {e}")

    # 2. Check Docs
    usage_guide = root / "USAGE-GUIDE.md"
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    # Also check docs/cli/ if exists
    docs_cli_dir = root / "docs" / "cli"
    if docs_cli_dir.exists():
        for f in docs_cli_dir.glob("*.md"):
             usage_content += "\n" + f.read_text()

    missing_docs = []

    for module, cmds in found_commands.items():
        for cmd_info in cmds:
            cmd = cmd_info["name"]
            flags = cmd_info["flags"]

            # Check command
            full_cmd = f"{module} {cmd}"
            if full_cmd not in usage_content and cmd not in usage_content:
                missing_docs.append(f"Command: {full_cmd}")

            # Check flags
            # This is heuristic, checking if the flag is mentioned anywhere in the docs
            # Ideally should check in the section of that command, but global check is a good start
            for flag in flags:
                if flag not in usage_content:
                    # Maybe it's mentioned as code `flag` or **flag**
                    if f"`{flag}`" not in usage_content and f"**{flag}**" not in usage_content:
                         # Don't flag standard flags if possible, but Typer adds --help etc.
                         # User args are usually significant.
                         missing_docs.append(f"Flag: {full_cmd} {flag}")

    if missing_docs:
        report["warnings"].append(f"Undocumented items in USAGE-GUIDE.md or docs/cli/: {', '.join(missing_docs)}")
        if fix and usage_guide.exists():
            with open(usage_guide, "a") as f:
                f.write("\n\n## Undocumented Items (Auto-detected)\n")
                for item in missing_docs:
                    f.write(f"- {item}\n")
            report["updated"].append("USAGE-GUIDE.md (added list of undocumented items)")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    # Check both adapter (definition) and service (usage)
    adapter_file = root / "src" / "devbase" / "adapters" / "storage" / "duckdb_adapter.py"
    db_file = root / "src" / "devbase" / "services" / "knowledge_db.py"

    if not tech_doc.exists():
        report["warnings"].append("TECHNICAL_DESIGN_DOC.md not found.")
        return

    tech_content = tech_doc.read_text()

    found_tables = set()
    table_pattern = r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?([a-zA-Z0-9_]+)'

    # 1. Check Adapter (Primary Source of Truth)
    if adapter_file.exists():
        adapter_content = adapter_file.read_text()
        matches = re.findall(table_pattern, adapter_content, re.IGNORECASE)
        found_tables.update(matches)

    # 2. Check Service (Usage - Backup)
    if db_file.exists():
        db_content = db_file.read_text()
        # Fallback to loose matching if needed, but sticking to explicit table names found in queries
        # Simple extraction of words that follow FROM/INTO
        usage_patterns = [
             r'INSERT INTO\s+([a-zA-Z0-9_]+)',
             r'FROM\s+([a-zA-Z0-9_]+)',
        ]
        for pattern in usage_patterns:
            matches = re.findall(pattern, db_content, re.IGNORECASE)
            found_tables.update(matches)

    # Filter for significant tables
    significant_tables = {t for t in found_tables if 'fts' in t or 'embeddings' in t or 'notes' in t}

    missing_in_doc = []
    for table in significant_tables:
        if table not in tech_content:
            missing_in_doc.append(table)

    if missing_in_doc:
        report["warnings"].append(f"Tables found in code but missing in TECHNICAL_DESIGN_DOC.md: {', '.join(missing_in_doc)}")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # If there are changes but no "Unreleased" or "In Progress" section, warn
    if "Unreleased" not in content and "In Progress" not in content:
        report["suggestions"].append("CHANGELOG.md might need an 'Unreleased' section for new changes.")

        if fix:
            # Prepend a draft section
            new_section = "## [Unreleased] - In Progress\n\n### Changed\n"
            for change in changes[:5]: # limit to 5
                new_section += f"- Modified {change}\n"
            if len(changes) > 5:
                new_section += f"- ... and {len(changes)-5} more files.\n"

            # Simple prepend (risky if format is strict, better to append or insert after header)
            # Assuming standard Keep A Changelog format
            lines = content.splitlines()
            # Find first h2
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_idx = i
                    break

            if insert_idx > 0:
                lines.insert(insert_idx, new_section)
                changelog.write_text("\n".join(lines))
                report["updated"].append("CHANGELOG.md (added Unreleased section)")
