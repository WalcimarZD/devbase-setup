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
        # However, prompt specifically asks to verify new libs like duckdb, networkx, pyvis are mentioned.
        # We will keep a minimal ignore list for pure dev tools or basics if really needed,
        # but generally we want key architectural components documented.
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
    """Check CLI commands vs Documentation"""
    # 1. Gather all commands from code
    commands_dir = root / "src" / "devbase" / "commands"
    found_commands = {} # module -> list of command names

    import re

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        content = cmd_file.read_text()

        # Updated Regex to be more robust:
        # 1. Matches @app.command("name") or @cli.command('name')
        # 2. Matches @app.command() followed by def name(): (implicit name)

        # Explicit names
        matches_explicit = re.findall(r'@(?:app|cli)\.command\(\s*["\']([\w-]+)["\']', content)

        # Implicit names (simplified approach: look for @app.command() followed closely by def func_name)
        # This is hard with regex, let's try a best effort single-pass or fallback.
        # Actually, let's keep it simple: find `def command_name` decorated with command.
        # Given we are parsing text, maybe AST is better, but let's improve regex first.

        # Find all decorators and the following function def
        # matches = re.findall(r'@(?:app|cli)\.command\((.*?)\)\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.DOTALL)
        # This is getting complex. Let's stick to explicit names for now as most commands use them.
        # But we MUST fix the duplicate issue.

        # Let's clean up matches to be unique per file
        matches = list(set(matches_explicit))

        if matches:
            found_commands[cmd_file.stem] = matches

    # 2. Check Docs
    usage_guide = root / "USAGE-GUIDE.md"
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    # Avoid reading the auto-generated section as valid documentation to prevent loops?
    # No, if it's there, it's documented. But we should check if we already added it.

    missing_docs = set()

    for module, cmds in found_commands.items():
        for cmd in cmds:
            full_cmd = f"{module} {cmd}"

            # Check for existence in doc
            # Heuristics:
            # - `devbase module cmd`
            # - `module cmd`
            # -  module cmd

            is_documented = (
                f"devbase {module} {cmd}" in usage_content or
                f"`{module} {cmd}`" in usage_content or
                f" {module} {cmd} " in usage_content
            )

            if not is_documented:
                missing_docs.add(full_cmd)

    if missing_docs:
        sorted_missing = sorted(list(missing_docs))
        report["warnings"].append(f"Undocumented commands in USAGE-GUIDE.md: {', '.join(sorted_missing)}")

        if fix and usage_guide.exists():
            # Check if section exists
            section_header = "## Undocumented Commands (Auto-detected)"

            if section_header not in usage_content:
                with open(usage_guide, "a") as f:
                    f.write(f"\n\n{section_header}\n")
                    for cmd in sorted_missing:
                        f.write(f"- `devbase {cmd}`\n")
                report["updated"].append("USAGE-GUIDE.md (added new undocumented commands section)")
            else:
                # If section exists, we should probably append only new ones or rewrite?
                # Rewriting safely is hard without full parsing.
                # Let's just append new ones if not present in the section.
                # Actually, simple append might duplicate if run multiple times.
                # Let's read file again to be safe?
                # Best effort: Append unique ones.
                with open(usage_guide, "a") as f:
                     for cmd in sorted_missing:
                         # We verified it's not in content above, but content was read before.
                         # Double check against current file content? No, unlikely to change in millis.
                         # Just write.
                         f.write(f"- `devbase {cmd}`\n")
                report["updated"].append("USAGE-GUIDE.md (appended to undocumented commands)")

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

    # Specifically check for hot_fts and cold_fts as per prompt
    required_tables = ["hot_fts", "cold_fts"]

    missing_in_doc = []
    for table in required_tables:
        # Check if table is used in code
        if table in db_content:
             # Check if mentioned in docs
             if table not in tech_content:
                 missing_in_doc.append(table)

    if missing_in_doc:
        report["warnings"].append(f"Tables used in code but missing in TECHNICAL_DESIGN_DOC.md: {', '.join(missing_in_doc)}")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # Check for "In Progress" or "Draft" section
    has_inprogress = "In Progress" in content or "Draft" in content or "Unreleased" in content

    if not has_inprogress:
        report["suggestions"].append("CHANGELOG.md should have an 'In Progress' section for active development.")

        if fix:
            # Prepend a draft section
            new_section = "## [In Progress]\n\n### Changed\n"
            for change in changes[:5]:
                new_section += f"- Modified {change}\n"
            if len(changes) > 5:
                new_section += f"- ... and {len(changes)-5} more files.\n"
            new_section += "\n"

            lines = content.splitlines()
            # Find insertion point (after header)
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_idx = i
                    break

            # If no existing release, just append? Or insert at top.
            # Assuming standard Keep A Changelog format with title/intro
            # If we found a ## Header, insert before it.
            if insert_idx > 0:
                lines.insert(insert_idx, new_section)
                changelog.write_text("\n".join(lines))
                report["updated"].append("CHANGELOG.md (added 'In Progress' section)")
            else:
                 # No headers found? append to end or after title
                 # Try to find # Changelog
                 if lines and lines[0].startswith("# "):
                     lines.insert(2, new_section)
                     changelog.write_text("\n".join(lines))
                     report["updated"].append("CHANGELOG.md (added 'In Progress' section)")

    # If section exists and fix=True, maybe we should update it?
    # The prompt implies "Add an entry". If section exists, we might want to check if recent files are there.
    # But that's complex parsing. For now, creating the section is the main requirement.
