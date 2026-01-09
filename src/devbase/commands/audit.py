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
import subprocess
from pathlib import Path
from typing import List, Set, Dict, Any, Optional, Tuple
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
    """Analyze changes in src/devbase in the last N days."""
    changed_files = []
    src_path = root / "src/devbase"

    # Try git first
    try:
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        # Check if git is available and repo is valid
        if (root / ".git").exists():
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
                try:
                    rel_path = str(path.relative_to(root))
                    changed_files.append(rel_path)
                except ValueError:
                    pass

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
        deps = pyproject.get("project", {}).get("dependencies", [])

        pkg_names = []
        for dep in deps:
            # Handle "package>=version", "package<version", "package==version"
            name = dep.split(">")[0].split("<")[0].split("=")[0].strip()
            pkg_names.append(name)

        arch_content = arch_path.read_text() if arch_path.exists() else ""
        readme_content = readme_path.read_text() if readme_path.exists() else ""

        # Specific libraries to always check as per prompt
        critical_libs = {"duckdb", "networkx", "pyvis"}
        # Standard libs to ignore
        ignore_libs = {"toml", "jinja2", "shellingham", "python-frontmatter", "copier", "typer", "rich"}

        missing_in_arch = []
        missing_in_readme = []

        for pkg in pkg_names:
            if pkg in ignore_libs and pkg not in critical_libs:
                continue

            if pkg not in arch_content:
                missing_in_arch.append(pkg)

            # For README, we might be more lenient, but prompt asked for check
            # We can check for a "Technologies" or "Stack" section, but simple string search is safest
            if pkg in critical_libs and pkg not in readme_content:
                missing_in_readme.append(pkg)

        if missing_in_arch:
            report["warnings"].append(f"Dependencies missing in ARCHITECTURE.md: {', '.join(missing_in_arch)}")

        if missing_in_readme:
             report["suggestions"].append(f"Critical libs missing in README.md: {', '.join(missing_in_readme)}")

    except Exception as e:
        report["warnings"].append(f"Failed to verify dependencies: {e}")

class CommandVisitor(ast.NodeVisitor):
    def __init__(self):
        self.commands = [] # List of (name, docstring, args)

    def visit_FunctionDef(self, node):
        # Check decorators
        is_command = False
        cmd_name = node.name # Default to func name

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                # @app.command("name")
                if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'command':
                    is_command = True
                    if decorator.args:
                        if isinstance(decorator.args[0], ast.Constant): # python 3.8+
                             cmd_name = decorator.args[0].value
                        elif isinstance(decorator.args[0], ast.Str): # python <3.8
                             cmd_name = decorator.args[0].s
            elif isinstance(decorator, ast.Attribute) and decorator.attr == 'command':
                 # @app.command without parens (rare in typer but possible)
                 is_command = True

        if is_command:
            args = []
            for arg in node.args.args:
                # Naive arg parsing, deeper inspection of type/defaults needed for full flags
                args.append(arg.arg)

            doc = ast.get_docstring(node) or ""
            self.commands.append({
                "name": cmd_name,
                "doc": doc,
                "args": args
            })

        self.generic_visit(node)

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands vs Documentation using AST."""
    commands_dir = root / "src" / "devbase" / "commands"
    docs_cli_dir = root / "docs" / "cli"
    usage_guide = root / "USAGE-GUIDE.md"

    if not commands_dir.exists():
        return

    # module -> list of command data
    module_commands = {}

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        try:
            tree = ast.parse(cmd_file.read_text())
            visitor = CommandVisitor()
            visitor.visit(tree)
            if visitor.commands:
                module_commands[cmd_file.stem] = visitor.commands
        except Exception:
            report["warnings"].append(f"Failed to parse {cmd_file.name}")

    # Check Docs
    for module, cmds in module_commands.items():
        doc_file = docs_cli_dir / f"{module}.md"

        # Determine target content
        target_content = ""
        target_file_name = ""

        if doc_file.exists():
            target_content = doc_file.read_text()
            target_file_name = f"docs/cli/{module}.md"
        elif usage_guide.exists():
            target_content = usage_guide.read_text()
            target_file_name = "USAGE-GUIDE.md"

        missing_cmds = []
        for cmd in cmds:
            # Check if command is mentioned
            # Heuristic: look for command name
            if cmd["name"] not in target_content:
                missing_cmds.append(cmd)

        if missing_cmds:
            report["warnings"].append(f"Undocumented commands in {target_file_name}: {[c['name'] for c in missing_cmds]}")

            if fix:
                if not doc_file.exists() and not usage_guide.exists():
                    report["warnings"].append(f"No place to document {module} commands.")
                    continue

                if doc_file.exists():
                    # Append to specific doc file
                    with open(doc_file, "a") as f:
                        f.write("\n\n## Auto-Detected Commands\n")
                        for c in missing_cmds:
                            f.write(f"\n### `{c['name']}`\n")
                            f.write(f"{c['doc']}\n")
                            if c['args']:
                                f.write(f"**Arguments/Flags:** {', '.join(c['args'])}\n")
                    report["updated"].append(f"docs/cli/{module}.md")

                elif usage_guide.exists():
                    # Append to USAGE-GUIDE
                    with open(usage_guide, "a") as f:
                        f.write(f"\n\n## New Commands in {module}\n")
                        for c in missing_cmds:
                            f.write(f"- `{c['name']}`: {c['doc'].splitlines()[0] if c['doc'] else 'No description'}\n")
                    report["updated"].append("USAGE-GUIDE.md")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs for hot_fts/cold_fts."""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    db_file = root / "src" / "devbase" / "services" / "knowledge_db.py"

    if not tech_doc.exists():
        report["warnings"].append("TECHNICAL_DESIGN_DOC.md not found.")
        return

    if not db_file.exists():
        report["warnings"].append("knowledge_db.py not found.")
        return

    tech_content = tech_doc.read_text()
    db_content = db_file.read_text()

    # Explicit check for hot_fts and cold_fts
    required_tables = ["hot_fts", "cold_fts"]

    for table in required_tables:
        # Check if used in code
        if table not in db_content:
             report["warnings"].append(f"Table '{table}' expected in knowledge_db.py but not found.")

        # Check if documented
        if table not in tech_content:
            report["warnings"].append(f"Table '{table}' found in requirements/code but missing in TECHNICAL_DESIGN_DOC.md.")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes."""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # Check for "In Progress" or "Draft" or "Unreleased"
    has_unreleased = any(x in content for x in ["Unreleased", "In Progress", "Draft"])

    if not has_unreleased:
        report["suggestions"].append("CHANGELOG.md needs an 'In Progress' or 'Unreleased' section.")

        if fix:
            # Add "In Progress" section
            # Insert after the header or at the top
            lines = content.splitlines()
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## "): # First release header
                    insert_idx = i
                    break

            new_section = [
                "",
                "## [Unreleased] - In Progress",
                "",
                "### Changed",
                *[f"- Modified {c}" for c in changes[:5]],
            ]
            if len(changes) > 5:
                new_section.append(f"- ... and {len(changes)-5} more files.")
            new_section.append("")

            if insert_idx > 0:
                lines[insert_idx:insert_idx] = new_section
                changelog.write_text("\n".join(lines))
                report["updated"].append("CHANGELOG.md (added In Progress section)")

if __name__ == "__main__":
    app()
