"""
Consistency Audit Command
=========================

Performs automated consistency checks between code and documentation.
Ensures no "Documentation Debt" accumulates.
"""
import os
import sys
import toml
import ast
import inspect
import subprocess
from pathlib import Path
from typing import List, Set, Dict, Any
from datetime import datetime, timedelta

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()
app = typer.Typer()

class CLIParser(ast.NodeVisitor):
    """
    AST Visitor to extract Typer commands and options from source code.
    """
    def __init__(self):
        self.commands = []
        self.flags = []

    def visit_FunctionDef(self, node):
        # 1. Detect Commands via decorators: @app.command("name")
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "command":
                     if decorator.args:
                         arg = decorator.args[0]
                         if isinstance(arg, ast.Constant): # Python 3.8+
                             self.commands.append(arg.value)
                         elif isinstance(arg, ast.Str): # Python <3.8
                             self.commands.append(arg.s)

        # 2. Detect Flags via defaults: arg = typer.Option(..., "--flag")
        for default in node.args.defaults:
            self._extract_flags(default)

        self.generic_visit(node)

    def _extract_flags(self, node):
        if isinstance(node, ast.Call):
            # Check for typer.Option
            if (isinstance(node.func, ast.Attribute) and node.func.attr == "Option") or \
               (isinstance(node.func, ast.Name) and node.func.id == "Option"):

                # Check args for flags (strings starting with -)
                for arg in node.args:
                    val = None
                    if isinstance(arg, ast.Constant):
                        val = arg.value
                    elif isinstance(arg, ast.Str):
                        val = arg.s

                    if val and isinstance(val, str) and val.startswith("-"):
                        self.flags.append(val)

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
    console.print("\n[bold underline]Resumo da Auditoria:[/bold underline]\n")

    if report["updated"]:
        table = Table(title="✅ Ficheiros de documentação atualizados", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        table = Table(title="⚠️ Inconsistencies Found (Inconsistências encontradas que exigem decisão humana)", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        table = Table(title="📝 Suggestions (Sugestões de melhoria para os manuais de utilizador)", show_header=False, box=None, style="blue")
        for item in report["suggestions"]:
            table.add_row(f"📝 {item}")
        console.print(table)

    if not report["updated"] and not report["warnings"] and not report["suggestions"]:
        console.print("[green]Sistema consistente! Bom trabalho.[/green]")

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
    found_commands = {} # module -> list of command names
    found_flags = {} # module -> list of flags

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        try:
            content = cmd_file.read_text()
            parser = CLIParser()
            parser.visit(ast.parse(content))

            if parser.commands:
                found_commands[cmd_file.stem] = parser.commands
            if parser.flags:
                found_flags[cmd_file.stem] = parser.flags
        except Exception:
            continue

    # 2. Check Docs
    usage_guide = root / "USAGE-GUIDE.md"
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    # Also check docs/cli/{module}.md
    docs_cli_dir = root / "docs" / "cli"

    missing_docs = []
    missing_flags = []

    for module, cmds in found_commands.items():
        # Determine target doc file
        doc_file = docs_cli_dir / f"{module}.md"
        target_content = usage_content
        target_file_name = "USAGE-GUIDE.md"

        if doc_file.exists():
            target_content = doc_file.read_text()
            target_file_name = f"docs/cli/{module}.md"

        for cmd in cmds:
            # Check if command is mentioned
            full_cmd = f"{module} {cmd}"
            # Check for simple mention of the command name
            if cmd not in target_content:
                 missing_docs.append(f"{full_cmd} (in {target_file_name})")

    for module, flags in found_flags.items():
        doc_file = docs_cli_dir / f"{module}.md"
        target_content = usage_content
        target_file_name = "USAGE-GUIDE.md"

        if doc_file.exists():
            target_content = doc_file.read_text()
            target_file_name = f"docs/cli/{module}.md"

        for flag in flags:
            if flag not in target_content:
                missing_flags.append(f"{flag} (in {module} -> {target_file_name})")

    if missing_docs:
        report["warnings"].append(f"Undocumented commands: {', '.join(missing_docs)}")
        if fix and usage_guide.exists():
            # Append a todo section to USAGE-GUIDE.md as fallback
            with open(usage_guide, "a") as f:
                f.write("\n\n## Undocumented Commands (Auto-detected)\n")
                for cmd in missing_docs:
                    f.write(f"- `devbase {cmd}`\n")
            report["updated"].append("USAGE-GUIDE.md (added list of undocumented commands)")

    if missing_flags:
        report["warnings"].append(f"Undocumented flags: {', '.join(missing_flags)}")

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

    # Specifically check for hot_fts and cold_fts logic
    required_tables = ["hot_fts", "cold_fts"]

    # We check if these strings are present in knowledge_db.py in a context that implies usage
    missing_in_code = []
    for table in required_tables:
        if table not in db_content:
            missing_in_code.append(table)

    if missing_in_code:
        report["warnings"].append(f"Expected tables {', '.join(missing_in_code)} not found in knowledge_db.py source.")

    # Check docs
    missing_in_doc = []
    for table in required_tables:
        if table not in tech_content:
            missing_in_doc.append(table)

    if missing_in_doc:
        report["warnings"].append(f"Tables {', '.join(missing_in_doc)} missing in TECHNICAL_DESIGN_DOC.md explanation.")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # If there are changes but no "Unreleased" or "In Progress" section, warn
    if "Unreleased" not in content and "In Progress" not in content and "Draft" not in content:
        report["suggestions"].append("CHANGELOG.md might need an 'In Progress' or 'Draft' section for new changes.")

        if fix:
            # Prepend a draft section
            new_section = "## [Draft] - In Progress\n\n### Changed\n"
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
                report["updated"].append("CHANGELOG.md (added Draft section)")
