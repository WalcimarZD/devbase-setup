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
    ctx: typer.Context,
    fix: bool = typer.Option(False, "--fix", help="Attempt to automatically fix issues where possible."),
    days: int = typer.Option(1, "--days", help="Number of days back to check for changes.")
):
    """
    Run a consistency audit between Code and Documentation.
    Checks: Dependencies, CLI Commands, Database Integrity.
    """
    root = ctx.obj.get("root", Path.cwd())
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
    # Try doc path if root path not found (handles both repo structures)
    if not arch_path.exists():
        arch_path = root / "docs" / "ARCHITECTURE.md"

    readme_path = root / "README.md"

    if not pyproject_path.exists():
        report["warnings"].append("pyproject.toml not found.")
        return

    try:
        pyproject = toml.load(pyproject_path)
        project_config = pyproject.get("project", {})
        deps = project_config.get("dependencies", [])

        # Add optional dependencies
        optional_deps = project_config.get("optional-dependencies", {})
        for group in optional_deps.values():
            deps.extend(group)

        # Extract package names (basic parsing)
        pkg_names = []
        for dep in deps:
            # Handle "package>=version", "package<version", "package==version", "package"
            name = re.split(r'[<>=]', dep)[0].strip()
            pkg_names.append(name)

        # Check docs
        arch_content = arch_path.read_text() if arch_path.exists() else ""
        readme_content = readme_path.read_text() if readme_path.exists() else ""

        missing_in_arch = []
        missing_in_readme = []

        # Dependencies to ignore (standard or very common tools that might not need explicit arch docs)
        # Updated list based on common dev deps
        ignore_libs = ["toml", "jinja2", "shellingham", "python-frontmatter", "copier", "plyer", "hatchling"]

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
    """Check CLI commands and flags vs Documentation"""
    commands_dir = root / "src" / "devbase" / "commands"
    found_commands = {} # module -> list of (command_name, flags_list)

    # Map filenames to cli groups (simplified)
    # This should match main.py registration
    group_map = {
        "core": "core",
        "development": "dev",
        "navigation": "nav",
        "audit": "audit",
        "operations": "ops",
        "quick": "quick",
        "docs": "docs",
        "pkm": "pkm",
        "study": "study",
        "analytics": "analytics",
        "ai": "ai"
    }

    if not commands_dir.exists():
         report["warnings"].append(f"Commands directory not found: {commands_dir}")
         return

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        module_name = cmd_file.stem
        group_name = group_map.get(module_name, module_name) # Default to filename if not in map

        content = cmd_file.read_text()

        # Regex to find commands
        # Also capture the function definition to scan for flags inside arguments
        # This is a simple parser, might miss complex cases

        # Pattern: @app.command(...) ... def func(...)
        # We'll just find all command names first
        cmd_matches = re.finditer(r'@(?:app|cli)\.command\(\s*["\']([\w-]+)["\']', content)

        for match in cmd_matches:
            cmd_name = match.group(1)
            # Naive flag extraction: look for typer.Option(..., "--flag") in the whole file
            # Ideally we should limit to the function scope, but that's hard with regex.
            # We will just collect ALL flags in the file and associate them with the module for now.
            # Or better: check if known flags are in docs.

            # Let's stick to checking if command exists in docs.
            if group_name not in found_commands:
                found_commands[group_name] = []
            found_commands[group_name].append(cmd_name)

    # Scan for flags globally in the file (approximation)
    # Flags: typer.Option(..., "--flag" or "-f")
    found_flags = {}
    for cmd_file in commands_dir.glob("*.py"):
         content = cmd_file.read_text()
         flags = re.findall(r'--([\w-]+)', content)
         # Filter out common flags usually not documented per command or documented globally
         filtered_flags = {f for f in flags if f not in ['help', 'version', 'verbose', 'root']}
         if filtered_flags:
             found_flags[cmd_file.stem] = filtered_flags

    # 2. Check Docs
    usage_guide = root / "USAGE-GUIDE.md"
    if not usage_guide.exists():
        usage_guide = root / "docs" / "USAGE-GUIDE.md"

    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    missing_docs = []

    for group, cmds in found_commands.items():
        for cmd in cmds:
            full_cmd = f"devbase {group} {cmd}"
            # Check for "devbase group cmd" OR "devbase group ... cmd"
            if full_cmd not in usage_content and f"{group} {cmd}" not in usage_content:
                missing_docs.append(full_cmd)

    if missing_docs:
        report["warnings"].append(f"Undocumented commands in USAGE-GUIDE.md: {', '.join(missing_docs)}")
        if fix and usage_guide.exists():
            with open(usage_guide, "a") as f:
                f.write("\n\n## Undocumented Commands (Auto-detected)\n")
                for cmd in missing_docs:
                    f.write(f"- `{cmd}`\n")
            report["updated"].append(f"{usage_guide.name} (added list of undocumented commands)")

    # Check flags (loose check)
    missing_flags = []
    for module, flags in found_flags.items():
        for flag in flags:
            if f"--{flag}" not in usage_content:
                # heuristic: ignore if flag is very common like "name"
                missing_flags.append(f"--{flag} (in {module})")

    if missing_flags:
        # Just suggest, don't warn too hard as flags might be documented generically
        report["suggestions"].append(f"Potentially undocumented flags: {', '.join(missing_flags[:10])}...")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    if not tech_doc.exists():
         tech_doc = root / "TECHNICAL_DESIGN_DOC.md"

    # Check both Schema Definition (Adapter) and Usage (Service)
    db_adapter = root / "src" / "devbase" / "adapters" / "storage" / "duckdb_adapter.py"
    db_service = root / "src" / "devbase" / "services" / "knowledge_db.py"

    if not tech_doc.exists():
        report["warnings"].append("TECHNICAL_DESIGN_DOC.md not found.")
        return

    tech_content = tech_doc.read_text()

    found_tables = set()

    # 1. Check Adapter for CREATE TABLE
    if db_adapter.exists():
        adapter_content = db_adapter.read_text()
        create_matches = re.findall(r'CREATE TABLE IF NOT EXISTS\s+([a-zA-Z0-9_]+)', adapter_content, re.IGNORECASE)
        found_tables.update(create_matches)

    # 2. Check Service for usage (if adapter didn't exist or just to be sure)
    if db_service.exists():
        service_content = db_service.read_text()
        usage_matches = re.findall(r'(?:FROM|INSERT INTO|UPDATE)\s+([a-zA-Z0-9_]+)', service_content, re.IGNORECASE)
        # Filter usage matches to only likely table names (avoiding SQL keywords captured by loose regex)
        # But for 'hot_fts' and 'cold_fts' specifically, we want to be sure.
        found_tables.update(usage_matches)

    # Specific check for hot_fts and cold_fts as per requirement
    required_tables = {'hot_fts', 'cold_fts'}

    # Filter found tables to only those that seem like table definitions we care about
    # or just check against the required list + others found

    missing_in_doc = []
    for table in found_tables:
        # Ignore common SQL keywords if regex slipped
        if table.upper() in ['SELECT', 'WHERE', 'FROM', 'INSERT', 'UPDATE', 'DELETE']: continue

        # If it's a "significant" table, check if documented
        if table in required_tables or 'fts' in table or 'index' in table or 'queue' in table:
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
