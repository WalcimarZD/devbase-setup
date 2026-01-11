"""
Consistency Audit Command
=========================

Performs automated consistency checks between code and documentation.
Ensures no "Documentation Debt" accumulates.
"""
import os
import sys
import toml
import re
import subprocess
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
from datetime import datetime, timedelta

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
app = typer.Typer()

@app.command("run")
def consistency_audit(
    fix: bool = typer.Option(False, "--fix", help="Attempt to automatically fix issues where possible."),
    days: int = typer.Option(1, "--days", help="Number of days back to check for changes.")
):
    """
    Run a consistency audit between Code and Documentation.
    Checks: Changes, Dependencies, CLI Consistency, DB Integrity, Changelog.
    """
    root = _find_root()
    if not root:
        console.print("[red]Error: Could not find project root (looking for .devbase_state.json or pyproject.toml)[/red]")
        raise typer.Exit(1)

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
        console.print(f"   Found {len(changes)} modified files in src/devbase/ in last {days} days.")
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
    _print_report(report)


def _find_root() -> Optional[Path]:
    """Find the project root."""
    cwd = Path.cwd()
    for _ in range(5):
        if (cwd / ".devbase_state.json").exists() or (cwd / "pyproject.toml").exists():
            return cwd
        cwd = cwd.parent
    return None

def _analyze_changes(root: Path, days: int) -> List[str]:
    """Analyze changes in src/devbase in the last N days."""
    changed_files = []
    src_path = root / "src/devbase"

    # Try git first
    try:
        # Using git log with a relative date, robust to timezone issues in simple checks
        cmd = ["git", "log", f"--since={days}.days", "--name-only", "--pretty=format:", str(src_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            files = result.stdout.strip().split('\n')
            changed_files = [f.strip() for f in files if f.strip()]
            if changed_files:
                return list(set(changed_files))
    except Exception:
        pass

    # Fallback to mtime
    cutoff = datetime.now().timestamp() - (days * 86400)
    for path in src_path.rglob("*"):
        if path.is_file():
            if path.stat().st_mtime > cutoff:
                try:
                    changed_files.append(str(path.relative_to(root)))
                except ValueError:
                    changed_files.append(str(path))

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

        # Collect all dependencies (main + optional)
        deps = pyproject.get("project", {}).get("dependencies", [])
        optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})

        all_deps_strings = list(deps)
        for group in optional_deps.values():
            all_deps_strings.extend(group)

        pkg_names = []
        for dep in all_deps_strings:
            # Handle "package>=version" or "package"
            name = re.split(r'[<>=]', dep)[0].strip()
            pkg_names.append(name)

        arch_content = arch_path.read_text().lower() if arch_path.exists() else ""
        readme_content = readme_path.read_text().lower() if readme_path.exists() else ""

        # Core libs that MUST be documented (examples from prompt + critical ones)
        core_libs = ["duckdb", "networkx", "pyvis", "groq", "fastembed"]

        # Libs to ignore (standard utilities)
        ignore_libs = ["python", "toml", "jinja2", "shellingham", "python-frontmatter", "copier", "typer", "rich", "uv", "plyer"]

        missing_in_arch = []
        missing_in_readme = []

        for pkg in pkg_names:
            pkg_lower = pkg.lower()
            if pkg_lower in ignore_libs:
                continue

            # If it's a core lib, it must be in ARCHITECTURE.md
            if pkg_lower in core_libs:
                if pkg_lower not in arch_content:
                    missing_in_arch.append(pkg)
                if pkg_lower not in readme_content:
                    missing_in_readme.append(pkg)
            elif pkg_lower not in arch_content and pkg_lower not in readme_content:
                 # Warn if strictly unknown lib appears
                 pass

        if missing_in_arch:
            report["warnings"].append(f"Core dependencies missing in ARCHITECTURE.md: {', '.join(missing_in_arch)}")

        if missing_in_readme:
             report["suggestions"].append(f"Core dependencies missing in README.md: {', '.join(missing_in_readme)}")

    except Exception as e:
        report["warnings"].append(f"Failed to verify dependencies: {e}")

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands and flags vs Documentation"""
    commands_dir = root / "src" / "devbase" / "commands"

    # Store found elements: module -> {command: [flags]}
    found_cli_elements = {}

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        module_name = cmd_file.stem
        content = cmd_file.read_text()

        # Parse commands: @app.command("name")
        command_matches = re.findall(r'@(?:app|cli)\.command\(\s*["\']([\w-]+)["\']', content)

        # Parse global flags in module: Option(..., "--flag")
        # Note: This finds flags anywhere in the file. Associating them to specific commands
        # without AST is hard, but usually checking if the flag exists in docs for that module is enough.
        flag_matches = re.findall(r'Option\(.*?,? ?["\'](--[\w-]+)["\']', content)

        found_cli_elements[module_name] = {
            "commands": command_matches,
            "flags": list(set(flag_matches))
        }

    # Check against Docs
    usage_guide = root / "USAGE-GUIDE.md"
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    docs_cli_dir = root / "docs" / "cli"

    for module, elements in found_cli_elements.items():
        doc_file = docs_cli_dir / f"{module}.md"

        # Determine target content to check
        # Prioritize specific doc file, fallback to USAGE-GUIDE
        target_content = usage_content
        target_file = usage_guide

        if doc_file.exists():
            target_content = doc_file.read_text()
            target_file = doc_file

        # Check Commands
        missing_cmds = []
        for cmd in elements["commands"]:
            # Check for "command" or "module command" or "`command`"
            # Simple check: is the string in the file?
            if cmd not in target_content:
                missing_cmds.append(cmd)

        # Check Flags
        missing_flags = []
        for flag in elements["flags"]:
            if flag not in target_content:
                missing_flags.append(flag)

        if missing_cmds:
            msg = f"Undocumented commands in {target_file.name} for '{module}': {', '.join(missing_cmds)}"
            report["warnings"].append(msg)
            if fix:
                _append_undocumented(target_file, f"Commands ({module})", missing_cmds)
                report["updated"].append(f"{target_file.name} (added commands for {module})")

        if missing_flags:
            msg = f"Undocumented flags in {target_file.name} for '{module}': {', '.join(missing_flags)}"
            report["warnings"].append(msg)
            if fix:
                _append_undocumented(target_file, f"Flags ({module})", missing_flags)
                report["updated"].append(f"{target_file.name} (added flags for {module})")

def _append_undocumented(filepath: Path, section_type: str, items: List[str]):
    """Append undocumented items to file."""
    with open(filepath, "a") as f:
        f.write(f"\n\n## Undocumented {section_type} (Auto-detected)\n")
        for item in items:
            f.write(f"- `{item}`\n")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs (hot_fts, cold_fts)"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    if not tech_doc.exists():
        # Fallback location
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

    required_tables = ["hot_fts", "cold_fts"]

    # Check if explained in docs
    missing_docs = []
    for table in required_tables:
        if table in db_content:
            if table not in tech_content:
                missing_docs.append(table)

    if missing_docs:
        report["warnings"].append(f"Tables used in knowledge_db.py but missing in TECHNICAL_DESIGN_DOC.md: {', '.join(missing_docs)}")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    if "Unreleased" not in content and "In Progress" not in content:
        report["suggestions"].append("CHANGELOG.md missing 'Unreleased' section for new changes.")

        if fix:
            lines = content.splitlines()
            # Insert after header
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("# Changelog") or line.startswith("# Change Log"):
                     insert_idx = i + 1
                     break

            if insert_idx == 0: insert_idx = 0 # Just top if no header found

            new_section = [
                "",
                "## [Unreleased] - In Progress",
                "### Changed",
            ]
            for change in changes[:5]:
                new_section.append(f"- Modified {change}")
            if len(changes) > 5:
                new_section.append(f"- ... and {len(changes)-5} more.")

            lines[insert_idx:insert_idx] = new_section
            changelog.write_text("\n".join(lines))
            report["updated"].append("CHANGELOG.md (added Unreleased section)")

def _print_report(report: Dict[str, List[str]]):
    console.print("\n[bold underline]Audit Summary:[/bold underline]\n")

    if report["updated"]:
        table = Table(title="✅ Ficheiros de documentação atualizados", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        table = Table(title="⚠️ Inconsistências encontradas que exigem decisão humana", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        table = Table(title="📝 Sugestões de melhoria para os manuais de utilizador", show_header=False, box=None, style="blue")
        for item in report["suggestions"]:
            table.add_row(f"📝 {item}")
        console.print(table)

    if not report["updated"] and not report["warnings"] and not report["suggestions"]:
        console.print("[green]System is consistent! No documentation debt found.[/green]")
