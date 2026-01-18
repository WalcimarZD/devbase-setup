"""
Auditoria de Consistência (Consistency Audit)
=============================================

Tarefa agendada para garantir a integridade entre Código e Documentação.
Executa verificações de dependências, CLI, DB e Changelog.
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
from rich.text import Text

console = Console()
app = typer.Typer(help="Auditoria de Consistência e Qualidade")

@app.command("run")
def run_audit(
    ctx: typer.Context,
    fix: bool = typer.Option(False, "--fix", help="Tentar corrigir problemas automaticamente (ex: atualizar docs)."),
    days: int = typer.Option(1, "--days", help="Dias para análise de diff (padrão: 1, últimas 24h).")
):
    """
    Executa a Auditoria de Consistência entre Código e Documentação.

    Verifica:
    1. Alterações recentes (Diffs).
    2. Dependências (pyproject.toml vs Docs).
    3. Sincronização de CLI (Novos comandos/flags vs Manuais).
    4. Integridade do Grafo e DB (Tabelas vs Tech Doc).
    5. Changelog (Changes vs Registros).
    """
    # Resolve root from context or cwd
    root = ctx.obj.get("root", Path.cwd()) if ctx.obj else Path.cwd()

    report = {
        "updated": [],
        "warnings": [],
        "suggestions": []
    }

    console.print(Panel("[bold blue]Auditoria de Consistência DevBase[/bold blue]", subtitle="v5.1 Alpha"))

    # 1. Análise de Diffs
    # -------------------
    console.print("[bold]1. Análise de Diffs...[/bold]")
    changes = _analyze_changes(root, days)
    if changes:
        console.print(f"   Encontrados {len(changes)} arquivos alterados em src/devbase/ nas últimas {days}*24h.")
    else:
        console.print("   Nenhuma alteração de código recente detectada.")

    # 2. Verificação de Dependências
    # ------------------------------
    console.print("\n[bold]2. Verificação de Dependências...[/bold]")
    _verify_dependencies(root, report)

    # 3. Sincronização de CLI
    # -----------------------
    console.print("\n[bold]3. Sincronização de CLI...[/bold]")
    _verify_cli_consistency(root, report, fix)

    # 4. Integridade do Grafo e DB
    # ----------------------------
    console.print("\n[bold]4. Integridade do Grafo e DB...[/bold]")
    _verify_db_integrity(root, report)

    # 5. Atualização de Changelog
    # ---------------------------
    if changes:
        console.print("\n[bold]5. Atualização de Changelog...[/bold]")
        _check_changelog(root, report, changes, fix)

    # Relatório de Execução
    # ---------------------
    console.print("\n[bold underline]Relatório de Execução:[/bold underline]\n")

    has_issues = False

    if report["updated"]:
        table = Table(title="✅ Ficheiros de documentação atualizados", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        has_issues = True
        table = Table(title="⚠️ Inconsistências encontradas que exigem decisão humana", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        has_issues = True
        table = Table(title="📝 Sugestões de melhoria para os manuais de utilizador", show_header=False, box=None, style="blue")
        for item in report["suggestions"]:
            table.add_row(f"📝 {item}")
        console.print(table)

    if not report["updated"] and not has_issues:
        console.print("[green]Tudo limpo! Nenhuma dívida de documentação detectada.[/green]")

def _analyze_changes(root: Path, days: int) -> List[str]:
    """
    Analisa alterações em src/devbase nas últimas 24h (ou N days).
    """
    changed_files = []
    src_path = root / "src" / "devbase"

    # Tenta usar git
    try:
        # git log --since="1 day ago" ...
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        # Check if inside git repo
        if (root / ".git").exists():
            result = subprocess.run(
                ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:", str(src_path)],
                capture_output=True, text=True, cwd=str(root)
            )
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                # Filter empty and keep unique
                changed_files = list(set([f.strip() for f in files if f.strip()]))
                return changed_files
    except Exception:
        pass

    # Fallback: verificar mtime
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
    Verifica pyproject.toml vs ARCHITECTURE.md e README.md.
    """
    pyproject_path = root / "pyproject.toml"
    arch_path = root / "ARCHITECTURE.md"
    readme_path = root / "README.md"

    if not pyproject_path.exists():
        report["warnings"].append("pyproject.toml não encontrado.")
        return

    try:
        pyproject = toml.load(pyproject_path)
        deps = pyproject.get("project", {}).get("dependencies", [])
        opt_deps_dict = pyproject.get("project", {}).get("optional-dependencies", {})

        # Flatten all deps
        all_deps = set()

        # Main deps
        for dep in deps:
            name = re.split(r'[<>=!]', dep)[0].strip()
            all_deps.add(name)

        # Optional deps
        for group, dlist in opt_deps_dict.items():
            for dep in dlist:
                name = re.split(r'[<>=!]', dep)[0].strip()
                all_deps.add(name)

        # Carregar Docs
        arch_content = arch_path.read_text(encoding='utf-8') if arch_path.exists() else ""
        readme_content = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

        # Ignorar libs comuns de infra/tooling que não impactam arquitetura
        ignore_libs = {
            "toml", "jinja2", "shellingham", "python-frontmatter", "copier",
            "typer", "rich", "ruff", "mypy", "pytest", "pytest-cov", "hatchling"
        }

        # Libs críticas mencionadas no prompt
        critical_libs = {"duckdb", "networkx", "pyvis", "groq", "fastembed"}

        missing_in_arch = []
        missing_in_readme = []

        for pkg in all_deps:
            if pkg in ignore_libs and pkg not in critical_libs:
                continue

            # Check Architecture
            if pkg.lower() not in arch_content.lower():
                missing_in_arch.append(pkg)

            # Check Readme (less strict, usually mentions main ones)
            if pkg.lower() not in readme_content.lower():
                missing_in_readme.append(pkg)

        if missing_in_arch:
            report["warnings"].append(f"Novas dependências não documentadas em ARCHITECTURE.md: {', '.join(missing_in_arch)}")

        # Para README, colocamos como sugestão
        if missing_in_readme:
             # Filter only critical ones for README warnings to reduce noise
             critical_missing = [p for p in missing_in_readme if p in critical_libs]
             if critical_missing:
                 report["suggestions"].append(f"Dependências importantes ausentes no README.md: {', '.join(critical_missing)}")

    except Exception as e:
        report["warnings"].append(f"Falha ao verificar dependências: {e}")

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """
    Verifica se novos comandos/flags em src/devbase/commands/ estão documentados.
    """
    commands_dir = root / "src" / "devbase" / "commands"
    docs_cli_dir = root / "docs" / "cli"
    usage_guide = root / "USAGE-GUIDE.md"

    # 1. Extrair Comandos do Código
    found_commands = {} # module -> list of {cmd: name, flags: [args]}

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py": continue

        content = cmd_file.read_text(encoding='utf-8')
        module_name = cmd_file.stem

        # Regex para encontrar comandos
        # Ex: @app.command("cmd")
        cmd_matches = re.findall(r'@(?:app|cli)\.command\(\s*(?:name\s*=\s*)?["\']([\w-]+)["\']', content)

        # Regex para encontrar flags/options (simples heurística)
        # typer.Option(..., "--flag", ...)
        flag_matches = re.findall(r'typer\.Option\([^,)]*,.*?"(--[\w-]+)"', content, re.DOTALL)

        if cmd_matches or flag_matches:
            found_commands[module_name] = {
                "commands": set(cmd_matches),
                "flags": set(flag_matches)
            }

    # 2. Verificar Documentação
    undocumented = []

    for module, data in found_commands.items():
        doc_file = docs_cli_dir / f"{module}.md"

        # Determine content to check
        doc_content = ""
        target_file = None

        if doc_file.exists():
            doc_content = doc_file.read_text(encoding='utf-8')
            target_file = doc_file
        elif usage_guide.exists():
            doc_content = usage_guide.read_text(encoding='utf-8')
            target_file = usage_guide

        if not doc_content:
            undocumented.append(f"Módulo {module} sem documentação (esperado em docs/cli/{module}.md ou USAGE-GUIDE.md)")
            continue

        # Check Commands
        for cmd in data["commands"]:
            # Check if command appears in doc
            # We look for `devbase module cmd` or just command name in a header or code block
            if cmd not in doc_content:
                undocumented.append(f"Comando '{module} {cmd}' ausente na documentação.")

                # Auto-fix logic (simple append)
                if fix and target_file:
                    _append_to_doc(target_file, f"\n\n## {cmd} (Auto-detected)\n\nComando detectado automaticamente. Adicione descrição aqui.\n")
                    if str(target_file.relative_to(root)) not in report["updated"]:
                        report["updated"].append(str(target_file.relative_to(root)))

        # Check Flags (Basic check)
        # This is harder because flags are scattered. We just check if the flag string exists in the doc file.
        for flag in data["flags"]:
            if flag not in doc_content:
                # Don't autofix flags yet, just warn
                report["suggestions"].append(f"Flag '{flag}' no módulo '{module}' parece não estar documentada.")

    if undocumented:
        report["warnings"].append(f"Comandos não documentados encontrados: {len(undocumented)} caso(s).")
        for item in undocumented:
            # Add details to suggestions if too many
            if len(report["suggestions"]) < 5:
                report["suggestions"].append(item)

def _append_to_doc(filepath: Path, text: str):
    """Appends text to a file."""
    with open(filepath, "a", encoding='utf-8') as f:
        f.write(text)

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """
    Verifica se hot_fts/cold_fts no DB alinham com TECHNICAL_DESIGN_DOC.md.
    """
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    db_file = root / "src" / "devbase" / "services" / "knowledge_db.py"

    if not tech_doc.exists():
        report["warnings"].append("TECHNICAL_DESIGN_DOC.md não encontrado.")
        return

    tech_content = tech_doc.read_text(encoding='utf-8')

    # Check if DB file exists (it should)
    if not db_file.exists():
        report["warnings"].append("knowledge_db.py não encontrado (caminho incorreto?).")
        return

    db_content = db_file.read_text(encoding='utf-8')

    # Tables to check explicitly as per prompt
    tables_to_check = ["hot_fts", "cold_fts"]

    for table in tables_to_check:
        # 1. Check implementation (usage in knowledge_db.py)
        if table not in db_content:
             report["warnings"].append(f"Tabela '{table}' não é referenciada em knowledge_db.py, mas é exigida pela arquitetura.")

        # 2. Check documentation
        if table not in tech_content:
             report["warnings"].append(f"Tabela '{table}' (implementada) não está explicada em TECHNICAL_DESIGN_DOC.md.")

    # Check alignment
    if "hot_fts" in tech_content and "cold_fts" in tech_content:
        # Good
        pass
    else:
        # Should have been caught above, but reinforces
        pass

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """
    Verifica se CHANGELOG.md tem entradas para mudanças recentes.
    """
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        report["warnings"].append("CHANGELOG.md não encontrado.")
        return

    content = changelog.read_text(encoding='utf-8')

    # Check for "In Progress" or "Draft" or "Unreleased"
    has_active_section = any(x in content for x in ["## [Unreleased]", "## In Progress", "## Draft", "## Em Progresso"])

    if not has_active_section:
        report["warnings"].append("Alterações de código detectadas, mas CHANGELOG.md não tem seção 'In Progress' ou 'Unreleased'.")

        if fix:
            # Insert logic
            lines = content.splitlines()
            # Find first header level 2
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## ") and "Unreleased" not in line:
                    insert_idx = i
                    break

            # Create new section
            new_block = [
                "",
                "## [Unreleased] - In Progress",
                "",
                "### Changed",
            ]
            for change in changes[:3]:
                new_block.append(f"- {change}")
            if len(changes) > 3:
                new_block.append(f"- ... e mais {len(changes)-3} arquivos.")
            new_block.append("")

            # Insert
            if insert_idx == 0:
                # Append to end if no headers found (weird changelog)
                lines.extend(new_block)
            else:
                lines[insert_idx:insert_idx] = new_block

            changelog.write_text("\n".join(lines), encoding='utf-8')
            report["updated"].append("CHANGELOG.md (Adicionada seção In Progress)")

