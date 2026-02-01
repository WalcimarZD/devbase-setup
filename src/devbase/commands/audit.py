"""
Consistency Audit Command
=========================

Performs automated consistency checks between code and documentation.
Ensures no "Documentation Debt" accumulates.
"""
import ast
import os
import re
import sys
import toml
import inspect
import subprocess
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

class CLIParser(ast.NodeVisitor):
    """Parses Typer command files to extract commands and flags."""
    def __init__(self):
        self.commands = {} # command_name -> {flags: [], lineno: int}
        self.current_command = None

    def visit_FunctionDef(self, node):
        # Check decorators for @app.command or @cli.command
        is_command = False
        cmd_name = node.name.replace("_", "-") # Default name inference

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Attribute) and func.attr == 'command':
                    is_command = True
                    # Check for name argument
                    if decorator.args:
                        arg = decorator.args[0]
                        if isinstance(arg, ast.Constant):
                            cmd_name = arg.value
                    # check keywords
                    for kw in decorator.keywords:
                        if kw.arg == 'name':
                            if isinstance(kw.value, ast.Constant):
                                cmd_name = kw.value.value

        if is_command:
            self.current_command = cmd_name
            self.commands[cmd_name] = {"flags": [], "lineno": node.lineno}
            self.generic_visit(node)
            self.current_command = None

    def visit_arg(self, node):
        # We need to find if this arg has a default value that is typer.Option
        # But visit_arg doesn't give us the default value directly in the same node context easily during traversal
        # usually defaults are in FunctionDef.args.defaults
        pass

    def visit_arguments(self, node):
        # iterate args and defaults together
        # defaults correspond to the last n args
        args = node.args
        defaults = node.defaults

        # Adjust for defaults alignment
        offset = len(args) - len(defaults)

        for i, default in enumerate(defaults):
            arg_node = args[offset + i]
            # Check if default is typer.Option
            if isinstance(default, ast.Call):
                func = default.func
                if isinstance(func, ast.Attribute) and func.attr == 'Option':
                    # It's an Option. Check args for flag names (starting with --)
                    for opt_arg in default.args:
                        if isinstance(opt_arg, ast.Constant) and isinstance(opt_arg.value, str) and opt_arg.value.startswith("--"):
                            if self.current_command:
                                self.commands[self.current_command]["flags"].append(opt_arg.value)


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
    """Check CLI commands vs Documentation"""
    commands_dir = root / "src" / "devbase" / "commands"
    found_commands = {} # module -> list of {cmd, flags}

    # 1. Parse Code
    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        try:
            content = cmd_file.read_text()
            tree = ast.parse(content)
            parser = CLIParser()
            parser.visit(tree)
            if parser.commands:
                found_commands[cmd_file.stem] = parser.commands
        except Exception as e:
            report["warnings"].append(f"Failed to parse {cmd_file.name}: {e}")

    # 2. Check Docs (USAGE-GUIDE.md and docs/cli/*.md)
    usage_guide = root / "USAGE-GUIDE.md"
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    docs_cli_dir = root / "docs" / "cli"

    missing_docs = [] # list of (module, command, type, item_name)

    for module, commands in found_commands.items():
        # Check if specific doc file exists
        doc_file = docs_cli_dir / f"{module}.md"
        doc_content = doc_file.read_text() if doc_file.exists() else ""

        combined_content = usage_content + "\n" + doc_content

        for cmd_name, info in commands.items():
            full_cmd = f"devbase {module} {cmd_name}" if module != "main" else f"devbase {cmd_name}"
            # Check Command
            if cmd_name not in combined_content and full_cmd not in combined_content:
                 missing_docs.append((module, cmd_name, "command", full_cmd))

            # Check Flags
            for flag in info["flags"]:
                if flag not in combined_content:
                    missing_docs.append((module, cmd_name, "flag", flag))

    if missing_docs:
        undocumented_summary = [f"{item[3]} ({item[2]})" for item in missing_docs]
        report["warnings"].append(f"Undocumented CLI items: {', '.join(undocumented_summary)}")

        if fix and usage_guide.exists():
            with open(usage_guide, "a") as f:
                f.write("\n\n## Undocumented Items (Auto-detected)\n")
                current_module = None
                for module, cmd, kind, item in missing_docs:
                    if module != current_module:
                        f.write(f"\n### Module: {module}\n")
                        current_module = module
                    if kind == "command":
                        f.write(f"- Command: `{item}`\n")
                    else:
                        f.write(f"- Flag: `{item}` (in command `{cmd}`)\n")

            report["updated"].append("USAGE-GUIDE.md (added undocumented items)")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs"""
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

    # 1. Check DB Code for hot_fts and cold_fts usage
    required_tables = ["hot_fts", "cold_fts"]
    missing_in_code = []
    for table in required_tables:
        if table not in db_content:
            missing_in_code.append(table)

    if missing_in_code:
        report["warnings"].append(f"Expected tables not found in knowledge_db.py source: {', '.join(missing_in_code)}")

    # 2. Check Docs for hot_fts and cold_fts
    missing_in_doc = []
    for table in required_tables:
        if table not in tech_content:
            missing_in_doc.append(table)

    if missing_in_doc:
        report["warnings"].append(f"Tables missing in TECHNICAL_DESIGN_DOC.md: {', '.join(missing_in_doc)}")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # Check for "In Progress" or "Unreleased"
    if "In Progress" not in content and "Unreleased" not in content:
        report["suggestions"].append("CHANGELOG.md missing 'In Progress' or 'Unreleased' section.")

        if fix:
            # Prepend a draft section
            new_section = "## [Unreleased] - In Progress\n\n### Changed\n"
            for change in changes[:5]: # limit to 5
                new_section += f"- Modified {change}\n"
            if len(changes) > 5:
                new_section += f"- ... and {len(changes)-5} more files.\n"

            lines = content.splitlines()
            # Find first h2 to insert before
            insert_idx = 0
            found_header = False
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_idx = i
                    found_header = True
                    break

            if not found_header and lines:
                # If no H2, maybe H1 is title, insert after
                insert_idx = 1 if len(lines) > 0 else 0

            if insert_idx >= 0:
                lines.insert(insert_idx, new_section)
                changelog.write_text("\n".join(lines))
                report["updated"].append("CHANGELOG.md (added In Progress section)")
