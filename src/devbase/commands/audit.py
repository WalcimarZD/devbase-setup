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
from typing import List, Set, Dict, Any, Tuple
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

    # Try git first
    try:
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
        deps = pyproject.get("project", {}).get("dependencies", [])
        pkg_names = []
        for dep in deps:
            name = dep.split(">")[0].split("<")[0].split("=")[0].strip()
            pkg_names.append(name)

        arch_content = arch_path.read_text() if arch_path.exists() else ""
        readme_content = readme_path.read_text() if readme_path.exists() else ""

        missing_in_arch = []
        missing_in_readme = []

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

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands vs Documentation (USAGE-GUIDE and docs/cli/)"""
    commands_dir = root / "src" / "devbase" / "commands"
    docs_cli_dir = root / "docs" / "cli"
    usage_guide = root / "USAGE-GUIDE.md"

    found_commands: Dict[str, List[Tuple[str, List[str]]]] = {}
    # structure: module_name -> [(command_name, [flags])]

    # 1. Parse Commands and Flags
    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        module_name = cmd_file.stem
        content = cmd_file.read_text()

        # Regex to find command definitions
        # Matches: @app.command("name") ... def func(... flag: ... = typer.Option(..., "--flag") ...)
        # This is complex to do with one regex. We will split by command definition.

        # Split content roughly by command decorators
        parts = re.split(r'@(?:app|cli)\.command\(\s*["\']([\w-]+)["\']', content)

        # parts[0] is header, then alternating command_name, command_body
        if len(parts) > 1:
            found_commands[module_name] = []
            for i in range(1, len(parts), 2):
                cmd_name = parts[i]
                cmd_body = parts[i+1]

                # Find flags in the body (typer.Option with --)
                # Matches: typer.Option(..., "--flag", ...) or typer.Option(..., "-f", "--flag")
                flags = re.findall(r'typer\.Option\(.*?"(--[\w-]+)"', cmd_body, re.DOTALL)
                found_commands[module_name].append((cmd_name, flags))

    # 2. Check Docs
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    missing_docs_cli = []

    for module, cmds in found_commands.items():
        doc_file = docs_cli_dir / f"{module}.md"
        doc_content = ""
        if doc_file.exists():
            doc_content = doc_file.read_text()

        doc_updated = False
        new_doc_content = doc_content

        if not doc_file.exists() and fix:
             # Create base file
             new_doc_content = f"# {module.capitalize()} Commands\n\n"
             doc_updated = True

        for cmd, flags in cmds:
            full_cmd = f"devbase {module if module != 'main' else ''} {cmd}".replace("  ", " ")

            # Check USAGE-GUIDE.md (Legacy/Overview)
            if cmd not in usage_content and module not in usage_content:
                 pass # Warning handled below for specific docs? or global one?
                 # We prioritize docs/cli now as per prompt instructions

            # Check docs/cli/<module>.md
            if cmd not in new_doc_content:
                report["warnings"].append(f"Command '{cmd}' missing in docs/cli/{module}.md")
                if fix:
                    new_doc_content += f"\n## `{cmd}`\n\nTODO: Add description.\n"
                    doc_updated = True

            for flag in flags:
                if flag not in new_doc_content:
                    report["warnings"].append(f"Flag '{flag}' for command '{cmd}' missing in docs/cli/{module}.md")
                    if fix:
                         new_doc_content += f"- `{flag}`: TODO document this flag.\n"
                         doc_updated = True

        if fix and doc_updated:
            if not doc_file.parent.exists():
                doc_file.parent.mkdir(parents=True)
            doc_file.write_text(new_doc_content)
            report["updated"].append(f"docs/cli/{module}.md")

    # Update USAGE-GUIDE if needed (Global check)
    # The prompt says: "Atualiza automaticamente os ficheiros correspondentes em docs/cli/ ou o USAGE-GUIDE.md"
    # We handled docs/cli above. We can check if any *new* modules appeared that are not in USAGE-GUIDE.

    if fix and usage_guide.exists():
        updated_usage = False
        with open(usage_guide, "a") as f:
            for module in found_commands:
                if module not in usage_content:
                    f.write(f"\n- `devbase {module}`: See `docs/cli/{module}.md`\n")
                    report["warnings"].append(f"Module '{module}' missing in USAGE-GUIDE.md")
                    updated_usage = True
        if updated_usage:
            report["updated"].append("USAGE-GUIDE.md (added missing modules)")


def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code (Adapter & KnowledgeDB) vs Technical Docs"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    db_files = [
        root / "src" / "devbase" / "services" / "knowledge_db.py",
        root / "src" / "devbase" / "adapters" / "storage" / "duckdb_adapter.py"
    ]

    if not tech_doc.exists():
        report["warnings"].append("TECHNICAL_DESIGN_DOC.md not found.")
        return

    tech_content = tech_doc.read_text()

    found_tables = set()

    for db_file in db_files:
        if not db_file.exists(): continue
        content = db_file.read_text()

        # Regex to find tables
        patterns = [
            r'CREATE TABLE(?:\s+IF NOT EXISTS)?\s+([a-zA-Z0-9_]+)',
            r'PRAGMA create_fts_index\(\s*[\'"]([a-zA-Z0-9_]+)[\'"]',
            r'FROM\s+([a-zA-Z0-9_]+)',
            r'INSERT INTO\s+([a-zA-Z0-9_]+)'
        ]

        for p in patterns:
            matches = re.findall(p, content, re.IGNORECASE)
            found_tables.update(matches)

    # Specific check for hot_fts and cold_fts as requested
    required_tables = {"hot_fts", "cold_fts"}

    # Also check if they were found in code
    missing_in_code = required_tables - found_tables
    if missing_in_code:
        report["warnings"].append(f"Expected tables {missing_in_code} not found in code!")

    # Check if found tables are in docs
    missing_in_doc = []

    # Check all found tables that seem significant (ignoring aliases or common words matched by loose regex)
    # Filter for things that look like our tables
    known_prefixes = ["hot_", "cold_", "notes_", "ai_", "events", "schema_"]

    significant_tables = {t for t in found_tables if any(t.startswith(p) or t == p.rstrip("_") for p in known_prefixes)}
    # Add specifically hot_fts and cold_fts if they exist in found_tables
    significant_tables.update({t for t in found_tables if t in required_tables})

    for table in significant_tables:
        if table not in tech_content:
            missing_in_doc.append(table)

    if missing_in_doc:
        report["warnings"].append(f"Tables in code but missing in TECHNICAL_DESIGN_DOC.md: {', '.join(missing_in_doc)}")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    if "Unreleased" not in content and "In Progress" not in content:
        report["suggestions"].append("CHANGELOG.md missing 'Unreleased' or 'In Progress' section.")

        if fix:
            lines = content.splitlines()
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_idx = i
                    break

            new_section = [
                "## [Unreleased] - In Progress",
                "",
                "### Changed",
            ]
            for change in changes[:5]:
                new_section.append(f"- Modified {change}")
            if len(changes) > 5:
                new_section.append(f"- ... and {len(changes)-5} more files.")
            new_section.append("")

            if insert_idx > 0:
                lines[insert_idx:insert_idx] = new_section
                changelog.write_text("\n".join(lines))
                report["updated"].append("CHANGELOG.md (added Unreleased section)")
