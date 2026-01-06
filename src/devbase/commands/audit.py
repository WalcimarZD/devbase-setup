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
from typing import List, Set, Dict, Any
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
    Executa auditoria de consistência entre Código e Documentação.
    Verifica: Dependências, Comandos CLI, Integridade de DB.
    """
    root = Path.cwd()
    # Using Portuguese keys for internal structure to match report or keep English internal?
    # I'll keep English internal keys but output Portuguese.
    report = {
        "updated": [],
        "warnings": [],
        "suggestions": []
    }

    console.print(Panel("[bold blue]DevBase Consistency Audit[/bold blue]", subtitle="v5.1 Alpha"))

    # 1. Diff Analysis
    # ----------------
    console.print("[bold]1. Análise de Diffs...[/bold]")
    changes = _analyze_changes(root, days)
    if changes:
        console.print(f"   Encontrados {len(changes)} ficheiros modificados em src/devbase/ nas últimas 24h.")
    else:
        console.print("   Nenhuma alteração de código recente detetada.")

    # 2. Verify Dependencies
    # ----------------------
    console.print("\n[bold]2. Verificação de Dependências...[/bold]")
    _verify_dependencies(root, report)

    # 3. Synchronization CLI
    # ----------------------
    console.print("\n[bold]3. Sincronização de CLI...[/bold]")
    _verify_cli_consistency(root, report, fix)

    # 4. Graph & DB Integrity
    # -----------------------
    console.print("\n[bold]4. Integridade do Grafo e DB...[/bold]")
    _verify_db_integrity(root, report)

    # 5. Changelog
    # ------------
    if changes:
        console.print("\n[bold]5. Atualização de Changelog...[/bold]")
        _check_changelog(root, report, changes, fix)

    # Report Execution
    # ----------------
    console.print("\n[bold underline]Relatório de Execução:[/bold underline]\n")

    if report["updated"]:
        table = Table(title="✅ Ficheiros de documentação atualizados", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)
    else:
        if not report["warnings"]:
             console.print("✅ Ficheiros de documentação atualizados (Nenhuma alteração necessária).")


    if report["warnings"]:
        table = Table(title="⚠️ Inconsistencies encontradas que exigem decisão humana", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        table = Table(title="📝 Sugestões de melhoria para os manuais de utilizador", show_header=False, box=None, style="blue")
        for item in report["suggestions"]:
            table.add_row(f"📝 {item}")
        console.print(table)

    if not report["warnings"] and not report["updated"] and not report["suggestions"]:
        console.print("[green]Tudo limpo! Nenhuma dívida de documentação detetada.[/green]")

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
        # Check if git repo exists
        if (root / ".git").exists():
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

    # Fallback to mtime if git fails or not a repo
    cutoff = datetime.now().timestamp() - (days * 86400)
    if src_path.exists():
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
    arch_path = root / "docs" / "ARCHITECTURE.md"
    readme_path = root / "README.md"

    # If ARCHITECTURE.md is in root or docs/ check both
    if not arch_path.exists():
        arch_path = root / "ARCHITECTURE.md"

    if not pyproject_path.exists():
        report["warnings"].append("pyproject.toml não encontrado.")
        return

    try:
        pyproject = toml.load(pyproject_path)
        deps = pyproject.get("project", {}).get("dependencies", [])
        # Extract package names
        pkg_names = []
        for dep in deps:
            name = dep.split(">")[0].split("<")[0].split("=")[0].strip()
            pkg_names.append(name)

        arch_content = arch_path.read_text() if arch_path.exists() else ""
        readme_content = readme_path.read_text() if readme_path.exists() else ""

        # Specific prompt checks + general check
        # Prompt examples: duckdb, networkx, pyvis
        priority_checks = ["duckdb", "networkx", "pyvis"]

        missing_in_arch = []
        missing_in_readme = []

        ignore_libs = ["toml", "jinja2", "shellingham", "python-frontmatter", "copier", "typer", "rich"]

        for pkg in pkg_names:
            if pkg in ignore_libs:
                continue

            # Check Architecture
            if pkg not in arch_content:
                missing_in_arch.append(pkg)

            # Check README (only priority ones strictly, others optional but good to have)
            if pkg in priority_checks and pkg not in readme_content:
                missing_in_readme.append(pkg)

        if missing_in_arch:
            report["warnings"].append(f"Novas bibliotecas no pyproject.toml não mencionadas na ARCHITECTURE.md: {', '.join(missing_in_arch)}")

        if missing_in_readme:
             report["suggestions"].append(f"Bibliotecas importantes ausentes no README.md: {', '.join(missing_in_readme)}")

    except Exception as e:
        report["warnings"].append(f"Falha ao verificar dependências: {e}")

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands and flags vs Documentation"""
    commands_dir = root / "src" / "devbase" / "commands"
    if not commands_dir.exists():
        return

    found_commands = {} # module -> list of (command_name, list_of_flags)

    # Regex for commands: @app.command("name")
    cmd_regex = re.compile(r'@(?:app|cli)\.command\(\s*["\']([\w-]+)["\']')
    # Regex for options: typer.Option(..., "--flag", ...)
    # This is rough, usually looking for string literals starting with -- inside Option calls
    opt_regex = re.compile(r'typer\.Option\(.*?(?:["\'](--[\w-]+)["\']).*?\)', re.DOTALL)

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        content = cmd_file.read_text()

        # This is a simplification. Ideally we parse the AST to map flags to commands.
        # But for "new flags added" check, finding them in the file is a good first step.
        cmds = cmd_regex.findall(content)
        opts = opt_regex.findall(content)

        if cmds or opts:
            found_commands[cmd_file.stem] = {"cmds": cmds, "opts": opts}

    # Check Docs
    usage_guide = root / "docs" / "USAGE-GUIDE.md"
    if not usage_guide.exists():
        usage_guide = root / "USAGE-GUIDE.md"

    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    missing_cmds = []
    missing_opts = []

    for module, data in found_commands.items():
        for cmd in data["cmds"]:
            full_cmd = f"devbase {module} {cmd}"
            # Check for command mention
            if cmd not in usage_content and module not in ["main", "core"]: # core might use subcommands differently
                 missing_cmds.append(f"{module} {cmd}")

        for opt in data["opts"]:
            if opt not in usage_content:
                missing_opts.append(f"{module}: {opt}")

    if missing_cmds:
        report["warnings"].append(f"Comandos não documentados no USAGE-GUIDE.md: {', '.join(missing_cmds)}")
        if fix and usage_guide.exists():
            with open(usage_guide, "a") as f:
                f.write("\n\n## Undocumented Commands (Auto-detected)\n")
                for c in missing_cmds:
                    f.write(f"- `{c}`\n")
            report["updated"].append("USAGE-GUIDE.md (adicionados comandos em falta)")

    if missing_opts:
        report["suggestions"].append(f"Flags/Opções novas detetadas mas não documentadas: {', '.join(missing_opts)}")

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs (Hot/Cold FTS alignment)"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    db_file = root / "src" / "devbase" / "services" / "knowledge_db.py"

    if not tech_doc.exists():
        return

    if not db_file.exists():
        return

    tech_content = tech_doc.read_text()
    db_content = db_file.read_text()

    # Check for hot_fts and cold_fts explicitly
    required_tables = ["hot_fts", "cold_fts"]

    for table in required_tables:
        # Check in Code
        in_code = table in db_content
        # Check in Doc
        in_doc = table in tech_content

        if in_code and not in_doc:
            report["warnings"].append(f"Tabela '{table}' usada no código mas não explicada no TECHNICAL_DESIGN_DOC.md")
        elif not in_code and in_doc:
             # Maybe deprecated in code but still in doc?
             report["suggestions"].append(f"Tabela '{table}' está na documentação mas não parece ser usada no knowledge_db.py")

        # Verify alignment of purpose if possible (hard with regex, trusting presence for now)

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return

    content = changelog.read_text()

    # If there are changes but no "Unreleased" or "In Progress" section, warn
    if "Unreleased" not in content and "In Progress" not in content:
        report["warnings"].append("CHANGELOG.md precisa de uma secção 'In Progress' ou 'Unreleased' para as novas mudanças.")

        if fix:
            # Prepend a draft section after header
            # Assuming typical Keep A Changelog structure
            lines = content.splitlines()
            new_lines = []
            inserted = False
            for line in lines:
                new_lines.append(line)
                if not inserted and line.startswith("# ") and "Changelog" in line:
                    # Insert after title
                    new_lines.append("")
                    new_lines.append("## [Unreleased] - In Progress")
                    new_lines.append("### Changed")
                    for change in changes[:5]:
                        new_lines.append(f"- Alterado: {change}")
                    if len(changes) > 5:
                        new_lines.append(f"- ... e mais {len(changes)-5} ficheiros.")
                    new_lines.append("")
                    inserted = True

            if inserted:
                changelog.write_text("\n".join(new_lines))
                report["updated"].append("CHANGELOG.md (Adicionada secção In Progress)")
