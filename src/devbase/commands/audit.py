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
    Checks: Dependencies, CLI Commands, Database Integrity, Changelog.
    """
    root = Path.cwd()
    # Handle cases where cwd is not root (try to find root)
    if not (root / "pyproject.toml").exists():
        if os.environ.get("DEVBASE_ROOT"):
            root = Path(os.environ["DEVBASE_ROOT"])
        else:
             # Try walking up
             current = root
             while current != current.parent:
                 if (current / "pyproject.toml").exists():
                     root = current
                     break
                 current = current.parent

    report = {
        "updated": [],
        "warnings": [],
        "suggestions": []
    }

    console.print(Panel("[bold blue]DevBase Consistency Audit[/bold blue]", subtitle="v5.1 Alpha"))

    # 1. Diff Analysis
    # ----------------
    console.print("[bold]1. Analise de Diffs (Últimas 24h+)...[/bold]")
    changes = _analyze_changes(root, days)
    if changes:
        console.print(f"   Found {len(changes)} modified/new files in src/devbase/.")
    else:
        console.print("   No recent code changes detected.")

    # 2. Verify Dependencies
    # ----------------------
    console.print("\n[bold]2. Verificação de Dependências...[/bold]")
    _verify_dependencies(root, report)

    # 3. Synchronization CLI
    # ----------------------
    console.print("\n[bold]3. Sincronização de CLI...[/bold]")
    _verify_cli_consistency(root, report, fix)

    # 4. Integridade do Grafo e DB
    # ----------------------------
    console.print("\n[bold]4. Integridade do Grafo e DB...[/bold]")
    _verify_db_integrity(root, report)

    # 5. Changelog
    # ------------
    if changes:
        console.print("\n[bold]5. Atualização de Changelog...[/bold]")
        _check_changelog(root, report, changes, fix)

    # Relatório de Execução
    # ---------------------
    console.print("\n[bold underline]Relatório de Execução:[/bold underline]\n")

    if report["updated"]:
        # ✅ Ficheiros de documentação atualizados.
        console.print("✅ Ficheiros de documentação atualizados:")
        for item in report["updated"]:
            console.print(f"   - {item}")

    if report["warnings"]:
        # ⚠️ Inconsistências encontradas que exigem decisão humana.
        console.print("\n⚠️ Inconsistências encontradas que exigem decisão humana:")
        for item in report["warnings"]:
             console.print(f"   - {item}")

    if report["suggestions"]:
        # 📝 Sugestões de melhoria para os manuais de utilizador.
        console.print("\n📝 Sugestões de melhoria para os manuais de utilizador:")
        for item in report["suggestions"]:
             console.print(f"   - {item}")

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

    # Try looking in docs/ if not in root
    if not arch_path.exists() and (root / "docs/ARCHITECTURE.md").exists():
        arch_path = root / "docs/ARCHITECTURE.md"

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

        # Dependencies to ignore (standard or very common tools)
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
    commands_dir = root / "src" / "devbase" / "commands"

    # module -> list of (command_name, [list of flags])
    found_commands: Dict[str, List[Tuple[str, List[str]]]] = {}

    if not commands_dir.exists():
         report["warnings"].append(f"Commands dir not found at {commands_dir}")
         return

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        content = cmd_file.read_text()

        # Match @app.command("name") or @cli.command("name")
        # And try to capture arguments/options. This is hard with regex, so we'll do best effort.
        # We can scan for Option(..., "--flag") inside functions.

        # Simple approach: Find command names
        cmd_matches = re.findall(r'@(?:app|cli)\.command\(\s*["\']([\w-]+)["\']', content)

        # Also find global flags defined in arguments with typer.Option(..., "--flag")
        # This is very loose, scanning the whole file for flags, not associating with specific commands strictly
        # But for audit purposes, we want to know if "--something" exists in code but not docs.
        flag_matches = re.findall(r'typer\.Option\(.*?"(--[\w-]+)"', content)

        if cmd_matches:
            found_commands[cmd_file.stem] = []
            for cmd in cmd_matches:
                found_commands[cmd_file.stem].append((cmd, flag_matches))

    # 2. Check Docs (USAGE-GUIDE.md and docs/cli/*.md)
    usage_guide = root / "USAGE-GUIDE.md"
    if not usage_guide.exists() and (root / "docs/USAGE-GUIDE.md").exists():
        usage_guide = root / "docs/USAGE-GUIDE.md"

    docs_cli_dir = root / "docs" / "cli"

    combined_docs_content = ""
    if usage_guide.exists():
        combined_docs_content += usage_guide.read_text()

    if docs_cli_dir.exists():
        for doc_file in docs_cli_dir.glob("*.md"):
            combined_docs_content += doc_file.read_text()

    missing_docs = []
    missing_flags = []

    for module, cmds in found_commands.items():
        for cmd_name, flags in cmds:
            # Check if command is mentioned
            full_cmd = f"{module} {cmd_name}"

            # Special case for "main" or "core" if structured differently
            if module == "main":
                check_name = f"devbase {cmd_name}"
            else:
                check_name = f"{module} {cmd_name}"

            if check_name not in combined_docs_content and cmd_name not in combined_docs_content:
                missing_docs.append(check_name)

            # Check flags (loose check)
            for flag in flags:
                if flag not in combined_docs_content:
                    if f"{check_name} {flag}" not in missing_flags: # avoid dups
                         missing_flags.append(f"{check_name} {flag}")

    if missing_docs:
        report["warnings"].append(f"Undocumented commands: {', '.join(missing_docs)}")

        if fix and usage_guide.exists():
            # Append a todo section
            with open(usage_guide, "a") as f:
                f.write("\n\n## Undocumented Commands (Auto-detected)\n")
                for cmd in missing_docs:
                    f.write(f"- `{cmd}`\n")
            report["updated"].append("USAGE-GUIDE.md (added list of undocumented commands)")

    if missing_flags:
         # Often flags are many, so maybe just suggest checking them
         # Limit report to first 5
         display_flags = missing_flags[:5]
         msg = f"Undocumented flags (sample): {', '.join(display_flags)}"
         if len(missing_flags) > 5:
             msg += f" ... and {len(missing_flags)-5} more."
         report["suggestions"].append(msg)


def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs (hot_fts/cold_fts)"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    if not tech_doc.exists() and (root / "TECHNICAL_DESIGN_DOC.md").exists():
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

    # Specific requirements from prompt: hot_fts, cold_fts
    required_tables = ["hot_fts", "cold_fts"]

    missing_in_doc = []

    # Check if these tables are mentioned in Code
    for table in required_tables:
        if table in db_content:
            # If in code, must be in doc
            if table not in tech_content:
                missing_in_doc.append(table)

    # Also generic check
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

    significant_tables = {t for t in found_tables if 'fts' in t or 'embeddings' in t}
    for table in significant_tables:
        if table not in tech_content:
            if table not in missing_in_doc:
                missing_in_doc.append(table)

    if missing_in_doc:
        report["warnings"].append(f"Tables found in code but missing in TECHNICAL_DESIGN_DOC.md: {', '.join(missing_in_doc)}")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # Look for "In Progress" or "Draft" or "Unreleased"
    has_active_section = any(x in content for x in ["In Progress", "Draft", "Unreleased"])

    if not has_active_section:
        report["suggestions"].append("CHANGELOG.md might need an 'In Progress' or 'Draft' section for new changes.")

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
            for i, line in enumerate(lines):
                if line.startswith("## ") and i > 2: # Skip header/title
                    insert_idx = i
                    break

            # If no h2 found, append? No, keep it top.
            # Usually Keep A Changelog has ## [Unreleased] at top.
            # If not found, insert after the first few lines (title)
            if insert_idx == 0:
                 # Find where header ends
                 for i, line in enumerate(lines):
                     if line.startswith("# Changelog"):
                         insert_idx = i + 4 # Skip title and some description
                         break

            if insert_idx > 0:
                lines.insert(insert_idx, "\n" + new_section)
                changelog.write_text("\n".join(lines))
                report["updated"].append("CHANGELOG.md (added In Progress section)")
