"""
Consistency Audit Command
=========================

Performs automated consistency checks between code and documentation.
Ensures no "Documentation Debt" accumulates.
"""
import os
import sys
import toml
import inspect
import subprocess
import ast
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
    root = Path.cwd()
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
        table = Table(title="✅ Ficheiros de documentação atualizados", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        table = Table(title="⚠️ Inconsistencies Found (Inconsistências encontradas)", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        table = Table(title="📝 Suggestions (Sugestões de melhoria)", show_header=False, box=None, style="blue")
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

class CLICommandVisitor(ast.NodeVisitor):
    def __init__(self):
        self.commands: List[Tuple[str, List[str]]] = []  # List of (command_name, [flags])

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Check decorators for @app.command or @cli.command
        is_command = False
        command_name = node.name # Default to function name
        explicit_name = False

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func = decorator.func
                # Handle app.command() or cli.command() or something.command()
                if isinstance(func, ast.Attribute) and func.attr == 'command':
                    is_command = True
                    # Try to get name argument
                    if decorator.args:
                        # decorator.args[0]
                        arg0 = decorator.args[0]
                        if isinstance(arg0, ast.Constant): # python 3.8+
                             command_name = arg0.value
                             explicit_name = True
                        elif isinstance(arg0, ast.Str): # python < 3.8
                             command_name = arg0.s
                             explicit_name = True
                    # Check kwargs for 'name'
                    for keyword in decorator.keywords:
                        if keyword.arg == 'name':
                            if isinstance(keyword.value, ast.Constant):
                                command_name = keyword.value.value
                                explicit_name = True
                            elif isinstance(keyword.value, ast.Str):
                                command_name = keyword.value.s
                                explicit_name = True

        if is_command and not explicit_name:
            # Typer converts snake_case to kebab-case by default if no name is provided
            command_name = command_name.replace("_", "-")

        if is_command:
            flags = []
            # Iterate over defaults to find Options
            for default in node.args.defaults:
                if isinstance(default, ast.Call):
                    is_option = False
                    if isinstance(default.func, ast.Attribute) and default.func.attr == 'Option':
                        is_option = True
                    elif isinstance(default.func, ast.Name) and default.func.id == 'Option':
                        is_option = True

                    if is_option:
                        # Check args for strings starting with --
                        for arg in default.args:
                            val = None
                            if isinstance(arg, ast.Constant):
                                val = arg.value
                            elif isinstance(arg, ast.Str):
                                val = arg.s

                            if isinstance(val, str) and val.startswith('--'):
                                flags.append(val)

            self.commands.append((command_name, flags))

        self.generic_visit(node)

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands vs Documentation using AST parsing"""
    commands_dir = root / "src" / "devbase" / "commands"
    found_commands: Dict[str, List[Tuple[str, List[str]]]] = {} # module -> list of (cmd, flags)

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        try:
            content = cmd_file.read_text()
            tree = ast.parse(content)
            visitor = CLICommandVisitor()
            visitor.visit(tree)
            if visitor.commands:
                found_commands[cmd_file.stem] = visitor.commands
        except Exception as e:
            report["warnings"].append(f"Failed to parse {cmd_file.name}: {e}")

    # 2. Check Docs
    usage_guide = root / "USAGE-GUIDE.md"
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    missing_docs = []

    for module, cmds in found_commands.items():
        for cmd_name, flags in cmds:
            # Check command
            # Heuristic: "devbase <module> <cmd>"
            full_cmd = f"{module} {cmd_name}"

            # Very basic check: is the command name in the text?
            if full_cmd not in usage_content and cmd_name not in usage_content:
                missing_docs.append(f"{full_cmd} (command)")

            # Check flags
            for flag in flags:
                if flag not in usage_content:
                    # Maybe it's documented near the command?
                    # For now, simplistic check: if flag is nowhere in doc, it's suspicious
                    # But flags like --help are common.
                    if flag not in ["--help", "--version"]:
                         # We might get false positives if flag is common (e.g. --name) and documented elsewhere
                         # But let's report it for now as per "strict" audit
                         # To avoid noise, maybe only check if command is present but flag isn't?
                         pass
                         # For this task, let's stick to commands primarily as per original logic,
                         # but add flags to report if command is missing or if explicitly requested.
                         # The prompt says "new commands or flags... were added".

                         # Let's add it to missing list if unique
                         if f"{flag}" not in usage_content:
                             missing_docs.append(f"{full_cmd} {flag}")

    if missing_docs:
        report["warnings"].append(f"Undocumented commands/flags in USAGE-GUIDE.md: {', '.join(missing_docs)}")
        if fix and usage_guide.exists():
            # Append a todo section
            with open(usage_guide, "a") as f:
                f.write("\n\n## Undocumented Commands/Flags (Auto-detected)\n")
                for item in missing_docs:
                    f.write(f"- `{item}`\n")
            report["updated"].append("USAGE-GUIDE.md (added list of undocumented items)")

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

    # Extract table names from DB code using basic regex for SQL patterns
    # Matches: INSERT INTO table_name, FROM table_name, CREATE TABLE table_name
    import re
    table_patterns = [
        r'INSERT INTO\s+([a-zA-Z0-9_]+)',
        r'FROM\s+([a-zA-Z0-9_]+)',
        r'CREATE TABLE\s+([a-zA-Z0-9_]+)'
    ]

    found_tables = set()
    for pattern in table_patterns:
        matches = re.findall(pattern, db_content, re.IGNORECASE)
        found_tables.update(matches)

    # Filter out likely SQL keywords or temp aliases if regex is too loose,
    # but strictly looking for prompt's specific concern: hot_fts, cold_fts
    # We filter for tables that seem "significant" (e.g., have 'fts' or 'embeddings' or are 'notes')
    significant_tables = {t for t in found_tables if 'fts' in t or 'embeddings' in t or 'notes' in t}

    # Explicit check for hot_fts and cold_fts
    critical_tables = {"hot_fts", "cold_fts"}
    for crit in critical_tables:
        if crit not in found_tables:
            report["warnings"].append(f"Critical table '{crit}' NOT found in knowledge_db.py implementation!")
        if crit not in tech_content:
            report["warnings"].append(f"Critical table '{crit}' NOT documented in TECHNICAL_DESIGN_DOC.md!")

    missing_in_doc = []
    for table in significant_tables:
        if table not in tech_content and table not in critical_tables: # Avoid double reporting
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
