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
from typing import List, Set, Dict, Any, Tuple
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
    fix: bool = typer.Option(False, "--fix", help="Attempt to automatically fix issues where possible."),
    days: int = typer.Option(1, "--days", help="Number of days back to check for changes.")
):
    """
    Run a consistency audit between Code and Documentation.
    Checks: Dependencies, CLI Commands, Database Integrity.
    """
    _run_audit(fix, days)

def _run_audit(fix: bool, days: int):
    """
    Run a consistency audit between Code and Documentation.
    Checks: Dependencies, CLI Commands, Database Integrity.
    """
    root = Path.cwd()
    report = {
        "updated": [],
        "warnings": [],
        "suggestions": []
    }

    console.print(Panel("[bold blue]DevBase Consistency Audit[/bold blue]", subtitle="v5.1 Alpha"))

    # 1. Diff Analysis
    # ----------------
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

    # 1. Check Git History
    try:
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        result = subprocess.run(
            ["git", "log", f"--since={since_date}", "--name-only", "--pretty=format:", str(src_path)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            files = result.stdout.strip().split('\n')
            for f in files:
                if f.strip():
                    changed_files.append(f.strip())
    except Exception:
        pass

    # 2. Check Local File System (mtime) for uncommitted/recent work
    cutoff = datetime.now().timestamp() - (days * 86400)
    for path in src_path.rglob("*"):
        if path.is_file():
            if path.stat().st_mtime > cutoff:
                try:
                    rel_path = str(path.relative_to(root))
                    if rel_path not in changed_files:
                        changed_files.append(rel_path)
                except ValueError:
                    pass

    return list(set(changed_files))

def _verify_dependencies(root: Path, report: Dict[str, List[str]]):
    """Check pyproject.toml vs ARCHITECTURE.md and README.md"""
    pyproject_path = root / "pyproject.toml"
    arch_path = root / "ARCHITECTURE.md"
    readme_path = root / "README.md"

    # Try docs path if root not found
    if not arch_path.exists(): arch_path = root / "docs/ARCHITECTURE.md"

    if not pyproject_path.exists():
        report["warnings"].append("pyproject.toml not found.")
        return

    try:
        pyproject = toml.load(pyproject_path)
        deps = pyproject.get("project", {}).get("dependencies", [])
        # Extract package names (basic parsing)
        pkg_names = []
        for dep in deps:
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

            if pkg not in readme_content:
                missing_in_readme.append(pkg)

        if missing_in_arch:
            report["warnings"].append(f"Dependencies missing in ARCHITECTURE.md: {', '.join(missing_in_arch)}")

        if missing_in_readme:
             report["suggestions"].append(f"Dependencies missing in README.md: {', '.join(missing_in_readme)}")

    except Exception as e:
        report["warnings"].append(f"Failed to verify dependencies: {e}")

def _extract_commands_and_flags(file_path: Path) -> Dict[str, List[str]]:
    """
    Parse a Typer command file using AST to extract command names and their flags (options).
    Returns a dict: { command_name: [flag1, flag2] }
    """
    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError:
        return {}

    commands = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            is_command = False
            cmd_name = node.name.replace("_", "-")

            # Check decorators
            for decorator in node.decorator_list:
                # Matches @app.command(...) or @cli.command(...)
                if isinstance(decorator, ast.Call) and hasattr(decorator.func, 'attr') and decorator.func.attr == 'command':
                    is_command = True
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                         cmd_name = decorator.args[0].value

            if is_command:
                flags = []
                # Check defaults for typer.Option
                # Defaults correspond to the last n arguments
                num_defaults = len(node.args.defaults)
                offset = len(node.args.args) - num_defaults

                for i, default in enumerate(node.args.defaults):
                    # Check if default is typer.Option(...)
                    if isinstance(default, ast.Call):
                        func_name = ""
                        if isinstance(default.func, ast.Attribute):
                            func_name = default.func.attr

                        if func_name == "Option":
                            # Look for flags in args (strings starting with --)
                            for arg in default.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("--"):
                                    flags.append(arg.value)

                commands[cmd_name] = flags

    return commands

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands vs Documentation (docs/cli/ or USAGE-GUIDE.md)"""
    commands_dir = root / "src" / "devbase" / "commands"
    docs_cli_dir = root / "docs" / "cli"
    usage_guide = root / "USAGE-GUIDE.md"
    if not usage_guide.exists():
        usage_guide = root / "docs" / "USAGE-GUIDE.md"

    for py_file in commands_dir.glob("*.py"):
        if py_file.name == "__init__.py": continue

        module_name = py_file.stem
        commands_info = _extract_commands_and_flags(py_file)

        if not commands_info:
            continue

        # Target doc file: docs/cli/{module_name}.md
        doc_file = docs_cli_dir / f"{module_name}.md"

        # Determine where to look
        target_file = doc_file if doc_file.exists() else usage_guide

        if not target_file.exists():
            report["warnings"].append(f"No documentation found for module '{module_name}' (expected {doc_file.name} or in USAGE-GUIDE.md)")
            continue

        content = target_file.read_text()

        file_updated = False

        for cmd, flags in commands_info.items():
            # Check command existence
            # Loose check: command name should appear in doc
            if cmd not in content:
                report["warnings"].append(f"Command '{cmd}' (from {module_name}) missing in {target_file.name}")
                if fix:
                    # Append to file
                    with open(target_file, "a") as f:
                        f.write(f"\n\n### `{cmd}`\n\n*(Auto-detected command)*\n")
                    content += f"\n\n### `{cmd}`\n\n*(Auto-detected command)*\n"
                    file_updated = True

            # Check flags existence
            for flag in flags:
                if flag not in content:
                    report["warnings"].append(f"Flag '{flag}' for command '{cmd}' missing in {target_file.name}")
                    if fix:
                        # Append to file (simple append)
                        with open(target_file, "a") as f:
                             f.write(f"\n- `{flag}`: (Auto-detected flag)\n")
                        content += f"\n- `{flag}`: (Auto-detected flag)\n"
                        file_updated = True

        if file_updated:
            report["updated"].append(f"{target_file.name} (added missing commands/flags)")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    # Fallback
    if not tech_doc.exists():
        tech_doc = root / "TECHNICAL_DESIGN_DOC.md"

    db_file = root / "src" / "devbase" / "services" / "knowledge_db.py"

    if not tech_doc.exists():
        report["warnings"].append("TECHNICAL_DESIGN_DOC.md not found.")
        return

    if not db_file.exists():
        report["warnings"].append("knowledge_db.py not found.")
        return

    tech_content = tech_doc.read_text()
    db_content = db_file.read_text()

    # Specific checks from prompt
    required_tables = ["hot_fts", "cold_fts"]

    # Also check if they exist in code
    for table in required_tables:
        if table in db_content:
            if table not in tech_content:
                report["warnings"].append(f"Table '{table}' found in knowledge_db.py but missing in TECHNICAL_DESIGN_DOC.md")
        else:
            # If not in code, maybe it's fine, but good to know
            pass

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

            new_section += "\n"

            lines = content.splitlines()
            # Find first h2 or just insert at top (after header)
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_idx = i
                    break

            # If no h2 found, append? No, preprend after title usually.
            if insert_idx > 0:
                lines.insert(insert_idx, new_section)
                changelog.write_text("\n".join(lines))
                report["updated"].append("CHANGELOG.md (added Unreleased section)")

if __name__ == "__main__":
    typer.run(consistency_audit)
