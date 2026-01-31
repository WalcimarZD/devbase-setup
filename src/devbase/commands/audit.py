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
    root = ctx.obj["root"]
    report = {
        "updated": [],
        "warnings": [],
        "suggestions": []
    }

    console.print(Panel("[bold blue]DevBase Consistency Audit[/bold blue]", subtitle="v5.1 Alpha"))

    # 1. Diff Analysis (Simulated/Best Effort)
    # ----------------------------------------
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
    console.print("\n[bold]3. Verificando Consistência da CLI...[/bold]")
    _verify_cli_consistency(root, report, fix)

    # 4. Graph & DB Integrity
    # -----------------------
    console.print("\n[bold]4. Verificando Integridade do Schema DB...[/bold]")
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
        table = Table(title="✅ Ficheiros de documentação atualizados.", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        table = Table(title="⚠️ Inconsistências encontradas que exigem decisão humana.", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        table = Table(title="📝 Sugestões de melhoria para os manuais de utilizador.", show_header=False, box=None, style="blue")
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
        arch_content = arch_path.read_text().lower() if arch_path.exists() else ""
        readme_content = readme_path.read_text().lower() if readme_path.exists() else ""

        missing_in_arch = []
        missing_in_readme = []

        # Dependencies to ignore (standard or very common tools that might not need explicit arch docs)
        ignore_libs = ["toml", "jinja2", "shellingham", "python-frontmatter", "copier", "typer", "rich", "pydantic", "httpx"]

        for pkg in pkg_names:
            if pkg in ignore_libs:
                continue

            # Simple case-insensitive string check
            if pkg.lower() not in arch_content:
                missing_in_arch.append(pkg)

            if pkg.lower() not in readme_content:
                missing_in_readme.append(pkg)

        if missing_in_arch:
            report["warnings"].append(f"Novas bibliotecas no pyproject.toml ausentes na ARCHITECTURE.md: {', '.join(missing_in_arch)}")

        if missing_in_readme:
             report["suggestions"].append(f"Bibliotecas ausentes no README.md: {', '.join(missing_in_readme)}")

    except Exception as e:
        report["warnings"].append(f"Falha ao verificar dependências: {e}")

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands vs Documentation (USAGE-GUIDE.md or docs/cli/*.md)"""
    commands_dir = root / "src" / "devbase" / "commands"
    found_commands = {} # module -> list of command names

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        content = cmd_file.read_text()
        # Match @app.command("name") or @cli.command("name")
        matches = re.findall(r'@(?:app|cli)\.command\(\s*["\']([\w-]+)["\']', content)
        if matches:
            found_commands[cmd_file.stem] = matches

    # Check Docs
    # Heuristic: Check docs/cli/{module}.md first, then fallback to USAGE-GUIDE.md
    docs_cli_dir = root / "docs" / "cli"
    usage_guide = root / "USAGE-GUIDE.md"

    missing_docs = []

    for module, cmds in found_commands.items():
        doc_file = docs_cli_dir / f"{module}.md"
        doc_content = ""

        # Determine source of truth for this module
        target_file = None

        if doc_file.exists():
            doc_content = doc_file.read_text()
            target_file = doc_file
        elif usage_guide.exists():
            doc_content = usage_guide.read_text()
            target_file = usage_guide

        if not target_file:
             report["warnings"].append("Nenhuma documentação encontrada (docs/cli/ ou USAGE-GUIDE.md).")
             return

        for cmd in cmds:
            # Check if command is mentioned
            # Heuristic: "devbase <module> <cmd>" or just the command name if inside module specific doc
            full_cmd = f"{module} {cmd}"

            is_documented = False
            if full_cmd in doc_content:
                is_documented = True
            elif cmd in doc_content and target_file == doc_file:
                # If specific file, maybe just command name is enough
                is_documented = True

            if not is_documented:
                missing_docs.append((module, cmd, target_file))

    if missing_docs:
        grouped_missing = {}
        for mod, cmd, file_path in missing_docs:
            if file_path not in grouped_missing:
                grouped_missing[file_path] = []
            grouped_missing[file_path].append(f"{mod} {cmd}")

        for file_path, cmds in grouped_missing.items():
            report["warnings"].append(f"Comandos não documentados em {file_path.name}: {', '.join(cmds)}")

            if fix and file_path.exists():
                with open(file_path, "a") as f:
                    f.write("\n\n## Undocumented Commands (Auto-detected)\n")
                    for cmd in cmds:
                        f.write(f"- `devbase {cmd}`\n")
                report["updated"].append(f"{file_path.name} (adicionado lista de comandos)")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs (specifically hot_fts/cold_fts)"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    db_file = root / "src" / "devbase" / "services" / "knowledge_db.py"

    if not tech_doc.exists():
        report["warnings"].append("TECHNICAL_DESIGN_DOC.md não encontrado.")
        return

    if not db_file.exists():
        report["warnings"].append("knowledge_db.py não encontrado.")
        return

    tech_content = tech_doc.read_text()
    db_content = db_file.read_text()

    # 1. Check for table existence in code
    required_tables = ["hot_fts", "cold_fts"]
    missing_in_code = []
    for table in required_tables:
        if table not in db_content: # Simple string check usually enough for existence
            missing_in_code.append(table)

    if missing_in_code:
        report["warnings"].append(f"Tabelas críticas ausentes no código (knowledge_db.py): {', '.join(missing_in_code)}")

    # 2. Check for documentation alignment
    missing_in_doc = []
    for table in required_tables:
        if table not in tech_content:
            missing_in_doc.append(table)

    if missing_in_doc:
        report["warnings"].append(f"Tabelas críticas ausentes na TECHNICAL_DESIGN_DOC.md: {', '.join(missing_in_doc)}")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # Check for "In Progress" or "Unreleased"
    if "In Progress" not in content and "Unreleased" not in content:
        report["suggestions"].append("CHANGELOG.md deve ter uma seção 'In Progress' ou 'Unreleased'.")

        if fix:
            # Prepend a draft section
            new_section = "## [In Progress] - Draft\n\n### Changed\n"
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
                report["updated"].append("CHANGELOG.md (adicionado seção In Progress)")
