"""
Consistency Audit Command
=========================

Performs automated consistency checks between code and documentation.
Ensures no "Documentation Debt" accumulates.
"""
import os
import re
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

@app.command("run")
def consistency_audit(
    ctx: typer.Context,
    fix: bool = typer.Option(False, "--fix", help="Attempt to automatically fix issues where possible."),
    days: int = typer.Option(1, "--days", help="Number of days back to check for changes.")
):
    """
    Run a consistency audit between Code and Documentation.
    Checks: Diffs, Dependencies, CLI Consistency, DB Integrity, Changelog.
    """
    root = ctx.obj.get("root") if ctx.obj else Path.cwd()
    report = {
        "updated": [],
        "warnings": [],
        "suggestions": []
    }

    console.print(Panel("[bold blue]DevBase Consistency Audit[/bold blue]", subtitle="v5.1 Alpha"))

    # 1. Diff Analysis
    # ----------------
    console.print("[bold]1. Analisando Alterações (Diff Analysis)...[/bold]")
    changes = _analyze_changes(root, days)
    if changes:
        console.print(f"   Found {len(changes)} modified/new files in src/devbase/ in last {days} days.")
    else:
        console.print("   No recent code changes detected.")

    # 2. Verify Dependencies
    # ----------------------
    console.print("\n[bold]2. Verificando Dependências...[/bold]")
    _verify_dependencies(root, report)

    # 3. Synchronization CLI
    # ----------------------
    console.print("\n[bold]3. Verificando CLI Consistency...[/bold]")
    _verify_cli_consistency(root, report, fix)

    # 4. Graph & DB Integrity
    # -----------------------
    console.print("\n[bold]4. Verificando DB Schema Integrity...[/bold]")
    _verify_db_integrity(root, report)

    # 5. Changelog
    # ------------
    if changes:
        console.print("\n[bold]5. Verificando Changelog...[/bold]")
        _check_changelog(root, report, changes, fix)

    # Report Execution
    # ----------------
    console.print("\n[bold underline]Relatório de Execução:[/bold underline]\n")

    if report["updated"]:
        # "✅ Ficheiros de documentação atualizados."
        table = Table(title="✅ Ficheiros de documentação atualizados", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        # "⚠️ Inconsistências encontradas que exigem decisão humana."
        table = Table(title="⚠️ Inconsistências encontradas que exigem decisão humana", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        # "📝 Sugestões de melhoria para os manuais de utilizador."
        table = Table(title="📝 Sugestões de melhoria para os manuais de utilizador", show_header=False, box=None, style="blue")
        for item in report["suggestions"]:
            table.add_row(f"📝 {item}")
        console.print(table)

    if not report["updated"] and not report["warnings"] and not report["suggestions"]:
        console.print("[green]System is consistent! No documentation debt found.[/green]")

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
    """
    Check pyproject.toml vs ARCHITECTURE.md and README.md.
    Specifically checks for added libraries (e.g., duckdb, networkx, pyvis).
    """
    pyproject_path = root / "pyproject.toml"
    arch_path = root / "docs/ARCHITECTURE.md"
    # Try root architecture if doc one doesn't exist
    if not arch_path.exists():
        arch_path = root / "ARCHITECTURE.md"

    readme_path = root / "README.md"

    if not pyproject_path.exists():
        report["warnings"].append("pyproject.toml not found.")
        return

    try:
        pyproject = toml.load(pyproject_path)
        deps = pyproject.get("project", {}).get("dependencies", [])
        opt_deps = pyproject.get("project", {}).get("optional-dependencies", {})

        all_deps = list(deps)
        for group in opt_deps.values():
            all_deps.extend(group)

        # Extract package names (basic parsing)
        pkg_names = []
        for dep in all_deps:
            # Handle "package>=version" or "package"
            name = dep.split(">")[0].split("<")[0].split("=")[0].strip()
            # Normalize names (lowercase)
            pkg_names.append(name.lower())

        # Check docs
        arch_content = arch_path.read_text().lower() if arch_path.exists() else ""
        readme_content = readme_path.read_text().lower() if readme_path.exists() else ""

        # Dependencies to explicitly check and report if missing
        priority_checks = ["duckdb", "networkx", "pyvis"]
        # Standard libs to ignore
        ignore_libs = ["toml", "jinja2", "shellingham", "python-frontmatter", "copier", "typer", "rich"]

        for pkg in pkg_names:
            if pkg in ignore_libs:
                continue

            # If it's a priority check, be stricter
            is_priority = pkg in priority_checks

            missing_in_arch = pkg not in arch_content
            missing_in_readme = pkg not in readme_content

            if missing_in_arch:
                 msg = f"Dependency '{pkg}' missing in ARCHITECTURE.md"
                 if is_priority:
                     report["warnings"].append(msg)
                 else:
                     # Just a suggestion for non-priority
                     pass # report["suggestions"].append(msg)

            if missing_in_readme and is_priority:
                 report["suggestions"].append(f"Dependency '{pkg}' could be mentioned in README.md")

    except Exception as e:
        report["warnings"].append(f"Failed to verify dependencies: {e}")

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """
    Check for new commands or flags (like --global or core debug).
    Update docs/cli/ or USAGE-GUIDE.md.
    """
    commands_dir = root / "src" / "devbase" / "commands"
    docs_cli_dir = root / "docs" / "cli"
    usage_guide = root / "USAGE-GUIDE.md"

    if not commands_dir.exists():
        return

    found_commands = {} # module -> list of {name, flags}

    # Iterate over command files
    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        module_name = cmd_file.stem
        content = cmd_file.read_text()

        # 1. Find commands
        # Match @app.command("name")
        cmd_matches = re.findall(r'@(?:app|cli)\.command\(\s*["\']([\w-]+)["\']', content)

        # 2. Find flags (Options)
        # Match typer.Option(..., "--flag", ...)
        # This is a loose regex, finding all "--flag" strings inside the file might be enough for a "new flag detected" check
        # But let's try to be specific to typer.Option definitions
        flag_matches = re.findall(r'typer\.Option\s*\(.*?,?\s*["\'](--[\w-]+)["\']', content, re.DOTALL)

        if cmd_matches or flag_matches:
            found_commands[module_name] = {
                "commands": cmd_matches,
                "flags": flag_matches
            }

    # Check Documentation
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    # Read all CLI docs
    cli_docs_content = ""
    if docs_cli_dir.exists():
        for doc_file in docs_cli_dir.glob("*.md"):
            cli_docs_content += doc_file.read_text()

    combined_docs = usage_content + "\n" + cli_docs_content

    missing_cmds = []
    missing_flags = []

    for module, data in found_commands.items():
        # Check commands
        for cmd in data["commands"]:
            # Check for "devbase <module> <cmd>" or just command name if strict check fails
            # We look for the command string in docs
            if cmd not in combined_docs:
                missing_cmds.append(f"{module} {cmd}")

        # Check flags
        for flag in data["flags"]:
            # Ignore common flags often undocumented explicitly in lists
            if flag in ["--help", "--version", "--verbose", "--root", "--no-color"]:
                continue
            if flag not in combined_docs:
                missing_flags.append(f"{module} ... {flag}")

    if missing_cmds:
        report["warnings"].append(f"Undocumented commands: {', '.join(missing_cmds)}")
        if fix:
            _update_cli_docs(root, missing_cmds, report)

    if missing_flags:
        report["warnings"].append(f"Undocumented flags: {', '.join(missing_flags)}")
        # We don't auto-fix flags yet as context is hard to place, just report.

def _update_cli_docs(root: Path, missing_cmds: List[str], report: Dict[str, List[str]]):
    """Update USAGE-GUIDE.md or create/update docs/cli/ files"""
    docs_cli_dir = root / "docs" / "cli"
    usage_guide = root / "USAGE-GUIDE.md"

    # Organize by module
    by_module = {}
    for item in missing_cmds:
        parts = item.split()
        if len(parts) >= 2:
            mod, cmd = parts[0], parts[1]
            if mod not in by_module: by_module[mod] = []
            by_module[mod].append(cmd)

    # If docs/cli exists, try to update individual files
    if docs_cli_dir.exists():
        for mod, cmds in by_module.items():
            doc_file = docs_cli_dir / f"{mod}.md"
            if doc_file.exists():
                with open(doc_file, "a") as f:
                    f.write("\n\n## Undocumented Commands (Auto-detected)\n")
                    for cmd in cmds:
                        f.write(f"- `{cmd}`\n")
                report["updated"].append(f"docs/cli/{mod}.md")
            else:
                # Create new file? Or fallback to USAGE-GUIDE
                # Let's fallback to USAGE-GUIDE for safety unless explicitly asked to generate new files
                pass

    # Fallback: Append to USAGE-GUIDE.md
    if usage_guide.exists():
         with open(usage_guide, "a") as f:
            f.write("\n\n## Undocumented Commands (Auto-detected)\n")
            for item in missing_cmds:
                f.write(f"- `devbase {item}`\n")
            report["updated"].append("USAGE-GUIDE.md")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """
    Check DB Code vs Technical Docs.
    Specifically hot_fts and cold_fts tables.
    """
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    # Fallback location
    if not tech_doc.exists():
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

    # Specific check for hot_fts and cold_fts
    # We check if these strings appear in the DB code (as table names) and in the Doc
    required_tables = ["hot_fts", "cold_fts"]

    for table in required_tables:
        in_code = table in db_content
        in_doc = table in tech_content

        if in_code and not in_doc:
            report["warnings"].append(f"Table '{table}' found in knowledge_db.py but missing in TECHNICAL_DESIGN_DOC.md")
        elif not in_code and in_doc:
             # This might be okay (doc ahead of code), but worth noting?
             pass

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """
    Check if CHANGELOG.md covers recent changes.
    Adds 'In Progress' entry if missing and fix=True.
    """
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # If there are changes but no "Unreleased" or "In Progress" section, warn
    if "Unreleased" not in content and "In Progress" not in content:
        report["suggestions"].append("CHANGELOG.md might need an 'In Progress' or 'Unreleased' section.")

        if fix:
            # Prepend a draft section
            new_section = "## [In Progress]\n\n### Changed\n"
            for change in changes[:5]:
                new_section += f"- Modified {change}\n"
            if len(changes) > 5:
                new_section += f"- ... and {len(changes)-5} more files.\n"

            lines = content.splitlines()
            # Insert after header (simplified)
            # Find first h2
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_idx = i
                    break

            if insert_idx == 0 and not lines[0].startswith("##"):
                 # Maybe header is at top
                 insert_idx = 1

            lines.insert(insert_idx, new_section)
            changelog.write_text("\n".join(lines))
            report["updated"].append("CHANGELOG.md (added In Progress section)")
