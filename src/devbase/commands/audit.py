"""
Consistency Audit Command
=========================

Performs automated consistency checks between code and documentation.
Ensures no "Documentation Debt" accumulates.
"""
import ast
import re
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
    ctx: typer.Context,
    fix: bool = typer.Option(False, "--fix", help="Attempt to automatically fix issues where possible."),
    days: int = typer.Option(1, "--days", help="Number of days back to check for changes.")
):
    """
    Run a consistency audit between Code and Documentation.
    Checks: Dependencies, CLI Commands, Database Integrity.
    """
    root = ctx.obj.get("root", Path.cwd()) if ctx.obj else Path.cwd()
    report = {
        "updated": [],
        "warnings": [],
        "suggestions": []
    }

    console.print(Panel("[bold blue]Auditoria de Consistência do DevBase[/bold blue]", subtitle="v5.1 Alpha"))

    # 1. Diff Analysis
    # ----------------
    console.print("[bold]1. Analisando Alterações (Diff)...[/bold]")
    changes = _analyze_changes(root, days)
    if changes:
        console.print(f"   Encontrados {len(changes)} ficheiros modificados/novos em src/devbase/ nas últimas {days * 24} horas.")
    else:
        console.print("   Nenhuma alteração de código recente detetada.")

    # 2. Verify Dependencies
    # ----------------------
    console.print("\n[bold]2. Verificando Dependências...[/bold]")
    _verify_dependencies(root, report)

    # 3. Synchronization CLI
    # ----------------------
    console.print("\n[bold]3. Sincronizando CLI...[/bold]")
    _verify_cli_consistency(root, report, fix)

    # 4. Graph & DB Integrity
    # -----------------------
    console.print("\n[bold]4. Verificando Integridade do Grafo e DB...[/bold]")
    _verify_db_integrity(root, report)

    # 5. Changelog
    # ------------
    if changes:
        console.print("\n[bold]5. Verificando Changelog...[/bold]")
        _check_changelog(root, report, changes, fix)

    # Report Execution
    # ----------------
    console.print("\n[bold underline]Resumo do Relatório:[/bold underline]\n")

    if report["updated"]:
        table = Table(title="✅ Ficheiros Atualizados", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        table = Table(title="⚠️ Inconsistências Encontradas", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        table = Table(title="📝 Sugestões", show_header=False, box=None, style="blue")
        for item in report["suggestions"]:
            table.add_row(f"📝 {item}")
        console.print(table)

    if not report["updated"] and not report["warnings"] and not report["suggestions"]:
        console.print("[green]O sistema está consistente! Bom trabalho.[/green]")

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
                changed_files.append(str(path.relative_to(root)))

    return changed_files

def _verify_dependencies(root: Path, report: Dict[str, List[str]]):
    """Check pyproject.toml vs ARCHITECTURE.md and README.md"""
    pyproject_path = root / "pyproject.toml"
    arch_path = root / "ARCHITECTURE.md"
    readme_path = root / "README.md"

    if not pyproject_path.exists():
        report["warnings"].append("pyproject.toml não encontrado.")
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
        ignore_libs = ["toml", "jinja2", "shellingham", "python-frontmatter", "copier", "typer", "rich"]

        for pkg in pkg_names:
            if pkg in ignore_libs:
                continue

            # Case insensitive check
            if pkg.lower() not in arch_content.lower():
                missing_in_arch.append(pkg)

            if pkg.lower() not in readme_content.lower():
                missing_in_readme.append(pkg)

        if missing_in_arch:
            report["warnings"].append(f"Novas dependências ausentes na ARCHITECTURE.md: {', '.join(missing_in_arch)}")

        if missing_in_readme:
             report["suggestions"].append(f"Novas dependências ausentes no README.md: {', '.join(missing_in_readme)}")

    except Exception as e:
        report["warnings"].append(f"Falha ao verificar dependências: {e}")

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands and flags vs Documentation using AST"""
    commands_dir = root / "src" / "devbase" / "commands"
    found_commands = [] # List of "module command [options]" strings

    # 1. Parse Code
    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        module_name = cmd_file.stem
        try:
            tree = ast.parse(cmd_file.read_text())
        except Exception:
            continue

        # Visitor to find Typer commands
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check decorators
                is_command = False
                command_name = node.name # Default to func name

                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "command":
                             is_command = True
                             # Try to get command name from args
                             if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                 command_name = decorator.args[0].value

                if is_command:
                    # Found a command, now look for Options/Flags in arguments
                    options = []
                    args = node.args
                    # Check defaults for typer.Option
                    for default in args.defaults:
                        if isinstance(default, ast.Call) and \
                           isinstance(default.func, ast.Attribute) and \
                           default.func.attr == "Option":
                               # Extract flags from args (e.g. "--global", "-g")
                               for arg in default.args:
                                   if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("-"):
                                       options.append(arg.value)

                    cmd_str = f"{module_name} {command_name}"
                    if options:
                        cmd_str += f" [{' '.join(options)}]"
                    found_commands.append(cmd_str)

    # 2. Check Docs
    usage_guide = root / "USAGE-GUIDE.md"
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    # Also check docs/cli/ if it exists (but USAGE-GUIDE is the main one requested)

    undocumented = []
    for cmd in found_commands:
        # Simplistic check: is the "module command" string present?
        # We strip options for the basic check, then maybe check specific flags if needed
        base_cmd = cmd.split("[")[0].strip()

        if base_cmd not in usage_content:
            undocumented.append(cmd)
        else:
            # If command exists, check if significant flags are mentioned
            if "[" in cmd:
                flags = cmd.split("[")[1].replace("]", "").split()
                for flag in flags:
                    if flag not in usage_content:
                        # Report missing flag
                        # We might not want to report every flag if the command is documented generally,
                        # but requirement says "Verifica se ... flags foram adicionados"
                        undocumented.append(f"{base_cmd} (flag: {flag})")

    if undocumented:
        report["warnings"].append(f"Comandos ou flags não documentados no USAGE-GUIDE.md: {', '.join(undocumented)}")

        if fix and usage_guide.exists():
            # Auto-update: Append to a special section
            header = "## 🛠️ Comandos Novos/Não Documentados (Auto-Audit)"

            new_content = usage_content
            if header not in new_content:
                new_content += f"\n\n{header}\n"

            # Parse existing entries to avoid dupes in that section
            existing_section = new_content.split(header)[1]

            added_count = 0
            for item in undocumented:
                if item not in existing_section:
                    new_content += f"- `devbase {item}`\n"
                    added_count += 1

            if added_count > 0:
                usage_guide.write_text(new_content)
                report["updated"].append(f"USAGE-GUIDE.md (adicionados {added_count} itens)")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs"""
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

    # Specific check for hot_fts and cold_fts
    required_tables = ["hot_fts", "cold_fts"]

    missing_in_doc = []
    missing_in_code = []

    for table in required_tables:
        # Check if present in code (loose check usually enough, but we can look for "hot_fts" string)
        if table not in db_content:
             missing_in_code.append(table)

        # Check if present in doc
        if table not in tech_content:
            missing_in_doc.append(table)

    if missing_in_code:
        report["warnings"].append(f"Tabelas críticas ausentes no código knowledge_db.py: {', '.join(missing_in_code)}")

    if missing_in_doc:
        report["warnings"].append(f"Explicações das tabelas ausentes no TECHNICAL_DESIGN_DOC.md: {', '.join(missing_in_doc)}")

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # If there are changes but no "Unreleased" or "In Progress" section, warn
    if "Unreleased" not in content and "In Progress" not in content:
        report["suggestions"].append("CHANGELOG.md pode precisar de uma secção 'Unreleased' para as novas mudanças.")

        if fix:
            # Create a Draft/In Progress section
            today = datetime.now().strftime('%Y-%m-%d')
            new_section = f"\n## [In Progress] - {today}\n### Changed\n"
            for change in changes[:5]: # limit to 5
                new_section += f"- Modificado {change}\n"
            if len(changes) > 5:
                new_section += f"- ... e mais {len(changes)-5} ficheiros.\n"

            # Insert after the main title or first H2
            # Assuming standard Keep A Changelog format
            lines = content.splitlines()
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## ") and "In Progress" not in line:
                    insert_idx = i
                    break

            # If we found a place to insert
            if insert_idx > 0:
                lines.insert(insert_idx, new_section)
                changelog.write_text("\n".join(lines))
                report["updated"].append("CHANGELOG.md (adicionada secção In Progress)")
