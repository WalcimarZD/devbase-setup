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
import re
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
    # Handle case where cwd is not root (e.g. inside src)
    if not (root / "pyproject.toml").exists():
        # Try to find root
        if (root.parent / "pyproject.toml").exists():
            root = root.parent
        elif (root.parent.parent / "pyproject.toml").exists():
            root = root.parent.parent

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
        console.print(f"   No functional changes detected in src/devbase/ in last {days} days.")

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
    console.print("\n[bold underline]Relatório de Execução:[/bold underline]\n")

    if report["updated"]:
        table = Table(title="✅ Ficheiros de documentação atualizados", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        table = Table(title="⚠️ Inconsistencies Found", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        table = Table(title="📝 Sugestões de melhoria", show_header=False, box=None, style="blue")
        for item in report["suggestions"]:
            table.add_row(f"📝 {item}")
        console.print(table)

    if not report["updated"] and not report["warnings"] and not report["suggestions"]:
        console.print("[green]✅ Sistema consistente! Nenhuma dívida de documentação encontrada.[/green]")

def _analyze_changes(root: Path, days: int) -> List[str]:
    """
    Analyze changes in src/devbase in the last N days using git if available,
    otherwise check mtime.
    """
    changed_files = []
    src_path = root / "src/devbase"

    if not src_path.exists():
        return []

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
    """Check pyproject.toml vs ARCHITECTURE.md and README.md for specific critical libs."""
    pyproject_path = root / "pyproject.toml"
    arch_path = root / "ARCHITECTURE.md"
    readme_path = root / "README.md"

    if not pyproject_path.exists():
        report["warnings"].append("pyproject.toml not found.")
        return

    try:
        pyproject = toml.load(pyproject_path)
        deps = pyproject.get("project", {}).get("dependencies", [])

        # Simplify deps list to just names
        dep_names = set()
        for dep in deps:
            name = re.split(r'[<>=!]', dep)[0].strip()
            dep_names.add(name)

        # Critical libraries to watch for as per instructions
        critical_libs = ["duckdb", "networkx", "pyvis"]

        arch_content = arch_path.read_text() if arch_path.exists() else ""
        readme_content = readme_path.read_text() if readme_path.exists() else ""

        for lib in critical_libs:
            if lib in dep_names:
                if lib not in arch_content:
                    report["warnings"].append(f"Library '{lib}' is in pyproject.toml but missing in ARCHITECTURE.md")
                if lib not in readme_content:
                    report["warnings"].append(f"Library '{lib}' is in pyproject.toml but missing in README.md")

    except Exception as e:
        report["warnings"].append(f"Failed to verify dependencies: {e}")

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands vs Documentation (USAGE-GUIDE and docs/cli/)"""
    commands_dir = root / "src" / "devbase" / "commands"
    docs_cli_dir = root / "docs" / "cli"
    usage_guide = root / "USAGE-GUIDE.md"

    if not commands_dir.exists():
        return

    # 1. Identify Command Modules
    command_files = [f for f in commands_dir.glob("*.py") if f.name != "__init__.py"]

    # 2. Check docs/cli/ mapping
    if docs_cli_dir.exists():
        for cmd_file in command_files:
            expected_doc = docs_cli_dir / f"{cmd_file.stem}.md"
            if not expected_doc.exists():
                report["warnings"].append(f"Missing documentation file: docs/cli/{expected_doc.name}")
                if fix:
                    expected_doc.write_text(f"# {cmd_file.stem.capitalize()} Command\n\nRun `devbase {cmd_file.stem} --help` for details.\n")
                    report["updated"].append(f"Created stub for docs/cli/{expected_doc.name}")

    # 3. Check USAGE-GUIDE.md for new commands/flags
    if usage_guide.exists():
        usage_content = usage_guide.read_text()

        undocumented_cmds = []
        for cmd_file in command_files:
            content = cmd_file.read_text()
            # Look for command definitions
            # Regex to find @app.command("name") or @cli.command("name")
            matches = re.findall(r'@(?:app|cli)\.command\(\s*["\']([\w-]+)["\']', content)

            for cmd_name in matches:
                # Check if specific command "module command" is in usage guide
                # This is heuristic.
                full_cmd_ref = f"{cmd_file.stem} {cmd_name}"
                if full_cmd_ref not in usage_content and cmd_name not in usage_content:
                    undocumented_cmds.append(full_cmd_ref)

        if undocumented_cmds:
            report["warnings"].append(f"New commands detected but not in USAGE-GUIDE.md: {', '.join(undocumented_cmds)}")
            if fix:
                with open(usage_guide, "a") as f:
                    f.write("\n\n## New Commands (Auto-detected)\n")
                    for cmd in undocumented_cmds:
                        f.write(f"- `devbase {cmd}`\n")
                report["updated"].append("USAGE-GUIDE.md (added new commands)")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Schema in code vs TECHNICAL_DESIGN_DOC.md"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    # Adapter is the source of truth for schema creation
    db_adapter = root / "src" / "devbase" / "adapters" / "storage" / "duckdb_adapter.py"

    if not tech_doc.exists():
        report["warnings"].append("TECHNICAL_DESIGN_DOC.md missing.")
        return

    tech_content = tech_doc.read_text()

    # Specific check for hot_fts and cold_fts
    tables_to_check = ["hot_fts", "cold_fts"]

    # Check if they exist in code (either in adapter or knowledge_db service)
    # We check adapter first as it usually has CREATE TABLE
    code_content = ""
    if db_adapter.exists():
        code_content += db_adapter.read_text()

    # Also check knowledge_db.py as fallback or reference
    kdb_service = root / "src" / "devbase" / "services" / "knowledge_db.py"
    if kdb_service.exists():
        code_content += kdb_service.read_text()

    for table in tables_to_check:
        # Check if table is mentioned in code
        if table in code_content:
            # Check if mentioned in docs
            if table not in tech_content:
                report["warnings"].append(f"Table '{table}' found in code but missing explanation in TECHNICAL_DESIGN_DOC.md")
        else:
            # If not in code, weird, but maybe strictly speaking we only check what IS in code
            pass

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Ensure functional changes are logged."""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    has_unreleased = "Unreleased" in content or "In Progress" in content

    if not has_unreleased:
        report["suggestions"].append("Functional changes detected but no 'In Progress' section in CHANGELOG.md")

        if fix:
            # Add Draft section
            lines = content.splitlines()
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_idx = i
                    break

            draft_section = [
                "## [Unreleased] - In Progress",
                "",
                "### Draft",
                ""
            ]
            for change in changes[:5]:
                draft_section.append(f"- Modified {change}")
            if len(changes) > 5:
                draft_section.append(f"- ... and {len(changes)-5} more files.")
            draft_section.append("")

            lines[insert_idx:insert_idx] = draft_section
            changelog.write_text("\n".join(lines))
            report["updated"].append("CHANGELOG.md (Added 'In Progress' section)")
