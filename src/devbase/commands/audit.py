"""
Consistency Audit Command
=========================

Performs automated consistency checks between code and documentation.
Ensures no "Documentation Debt" accumulates.
"""
import os
import sys
import ast
import toml
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


class CommandVisitor(ast.NodeVisitor):
    def __init__(self):
        self.commands = {}  # name -> list of flags

    def _extract_name_from_call(self, call_node):
        """Helper to extract command name from app.command(...) call."""
        name = None
        if call_node.args:
            if isinstance(call_node.args[0], ast.Constant):  # Python 3.8+
                name = call_node.args[0].value
            elif isinstance(call_node.args[0], ast.Str):  # Python <3.8
                name = call_node.args[0].s
        for keyword in call_node.keywords:
            if keyword.arg == "name":
                if isinstance(keyword.value, ast.Constant):
                    name = keyword.value.value
                elif isinstance(keyword.value, ast.Str):
                    name = keyword.value.s
        return name

    def visit_FunctionDef(self, node):
        is_command = False
        command_name = node.name

        # Check decorators
        for decorator in node.decorator_list:
            # @app.command(...)
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "command":
                    is_command = True
                    extracted = self._extract_name_from_call(decorator)
                    if extracted:
                        command_name = extracted
            # @app.command (no call)
            elif isinstance(decorator, ast.Attribute) and decorator.attr == "command":
                is_command = True

        # Note: We removed the 'Context' heuristic to avoid identifying helper functions as commands.
        # Only explicitly decorated commands are matched.

        if is_command:
            flags = set()
            # 1. Parse arguments for defaults that are typer.Option
            defaults = node.args.defaults
            for default in defaults:
                self._extract_flags_from_node(default, flags)

            # 2. Parse arguments for Annotated types
            for arg in node.args.args:
                if arg.annotation:
                    self._extract_flags_from_annotation(arg.annotation, flags)

            self.commands[command_name] = list(flags)

        self.generic_visit(node)

    def _extract_flags_from_annotation(self, annotation, flags):
        # Check for Annotated[...]
        if isinstance(annotation, ast.Subscript):
            # Check if value is Annotated
            is_annotated = False
            if isinstance(annotation.value, ast.Name) and annotation.value.id == "Annotated":
                is_annotated = True
            elif isinstance(annotation.value, ast.Attribute) and annotation.value.attr == "Annotated":
                is_annotated = True

            if is_annotated:
                # In Python 3.9+, slice is the node itself.
                slice_node = annotation.slice
                # If it's a Tuple (standard)
                if isinstance(slice_node, ast.Tuple):
                    for elt in slice_node.elts:
                        self._extract_flags_from_node(elt, flags)
                else:
                    self._extract_flags_from_node(slice_node, flags)

    def _extract_flags_from_node(self, node, flags):
        if isinstance(node, ast.Call):
            func = node.func
            # Check if it is typer.Option or Option
            is_option = False
            if isinstance(func, ast.Attribute) and func.attr == "Option":
                is_option = True
            elif isinstance(func, ast.Name) and func.id == "Option":
                is_option = True

            if is_option:
                # Extract flags from args (strings starting with -)
                for arg in node.args:
                    val = None
                    if isinstance(arg, ast.Constant):
                        val = arg.value
                    elif isinstance(arg, ast.Str):
                        val = arg.s

                    if val and isinstance(val, str) and val.startswith("-"):
                        flags.add(val)

    def visit_Expr(self, node):
        # Handle app.command(...)(func)
        if isinstance(node.value, ast.Call):
            outer_call = node.value
            if isinstance(outer_call.func, ast.Call):
                inner_call = outer_call.func
                if isinstance(inner_call.func, ast.Attribute) and inner_call.func.attr == "command":
                    command_name = self._extract_name_from_call(inner_call)
                    if command_name:
                        # We found a mounted command. We can't see flags here easily.
                        self.commands[command_name] = []
        self.generic_visit(node)


def extract_commands_from_source(source_code: str) -> Dict[str, List[str]]:
    """Extract commands and flags using AST."""
    try:
        tree = ast.parse(source_code)
        visitor = CommandVisitor()
        visitor.visit(tree)
        return visitor.commands
    except Exception:
        return {}


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

def _parse_usage_guide(content: str) -> Dict[str, str]:
    """Parse usage guide into command sections."""
    sections = {}
    current_cmd = None
    buffer = []
    import re
    # Matches: #### `core setup` or ### `devbase core`
    # Group 1: core setup
    header_pattern = re.compile(r'^#+\s+`?(?:devbase\s+)?([\w\s-]+)`?')

    for line in content.splitlines():
        match = header_pattern.match(line)
        if match:
            # Save previous section
            if current_cmd:
                sections[current_cmd] = "\n".join(buffer)

            current_cmd = match.group(1).strip()
            buffer = []
            buffer.append(line)
        else:
            if current_cmd:
                buffer.append(line)

    if current_cmd:
        sections[current_cmd] = "\n".join(buffer)

    return sections


def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands vs Documentation"""
    # 1. Gather all commands from code using AST
    commands_dir = root / "src" / "devbase" / "commands"
    found_commands = {}  # module -> {cmd_name: [flags]}

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        content = cmd_file.read_text()
        commands = extract_commands_from_source(content)
        if commands:
            found_commands[cmd_file.stem] = commands

    # 2. Check Docs
    usage_guide = root / "USAGE-GUIDE.md"  # or docs/cli/
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    # Parse usage guide into sections
    sections = _parse_usage_guide(usage_content)

    missing_cmds = []
    missing_flags = []

    # Map filenames to CLI command groups (based on main.py)
    ALIAS_MAP = {
        "development": "dev",
        "navigation": "nav",
        "operations": "ops"
    }

    for module, cmds in found_commands.items():
        cli_group = ALIAS_MAP.get(module, module)
        for cmd, flags in cmds.items():
            full_cmd = f"{cli_group} {cmd}"

            # Locate section
            # We try various keys: "module cmd", "cmd"
            section_content = sections.get(full_cmd)
            if not section_content:
                section_content = sections.get(cmd)

            if not section_content:
                # If section not found, fallback to checking global content for command existence
                # We strictly require full_cmd ("module cmd") to avoid false positives on common words like "run"
                if full_cmd not in usage_content:
                    missing_cmds.append(full_cmd)
                continue

            # Check flags within the section
            for flag in flags:
                if flag not in section_content:
                    missing_flags.append(f"{full_cmd} {flag}")

    if missing_cmds:
        report["warnings"].append(f"Undocumented commands in USAGE-GUIDE.md: {', '.join(missing_cmds)}")

    if missing_flags:
        report["warnings"].append(f"Undocumented flags in USAGE-GUIDE.md: {', '.join(missing_flags)}")

    if fix and usage_guide.exists() and (missing_cmds or missing_flags):
        with open(usage_guide, "a") as f:
            if missing_cmds:
                f.write("\n\n## Undocumented Commands (Auto-detected)\n")
                for cmd in missing_cmds:
                    f.write(f"- `devbase {cmd}`\n")
            if missing_flags:
                f.write("\n\n## Undocumented Flags (Auto-detected)\n")
                for flag in missing_flags:
                    f.write(f"- `{flag}`\n")

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
