"""
Consistency Audit Command
=========================

Performs automated consistency checks between code and documentation.
Ensures no "Documentation Debt" accumulates.
"""
import os
import re
import sys
import toml
import inspect
import subprocess
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
    ctx: typer.Context,
    fix: bool = typer.Option(False, "--fix", help="Attempt to automatically fix issues where possible."),
    days: int = typer.Option(1, "--days", help="Number of days back to check for changes.")
):
    """
    Run a consistency audit between Code and Documentation.
    Checks: Dependencies, CLI Commands, Database Integrity.
    """
    # Use root from context if available (standard DevBase pattern), otherwise detect
    root = ctx.obj.get("root") if ctx.obj else None

    if not root:
        root = Path.cwd()
        # Ensure we are at root
        if not (root / "pyproject.toml").exists():
            # Try to find root upwards
            for parent in root.parents:
                if (parent / "pyproject.toml").exists():
                    root = parent
                    break

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
    console.print("\n[bold]5. Checking Changelog...[/bold]")
    if changes:
        _check_changelog(root, report, changes, fix)
    else:
        console.print("   Skipping changelog check (no changes detected).")

    # Report Execution
    # ----------------
    console.print("\n[bold underline]Relatório de Execução:[/bold underline]\n")

    if report["updated"]:
        table = Table(title="✅ Ficheiros de documentação atualizados", show_header=False, box=None)
        for item in report["updated"]:
            table.add_row(f"✅ {item}")
        console.print(table)

    if report["warnings"]:
        table = Table(title="⚠️ Inconsistências encontradas que exigem decisão humana", show_header=False, box=None, style="yellow")
        for item in report["warnings"]:
            table.add_row(f"⚠️ {item}")
        console.print(table)

    if report["suggestions"]:
        table = Table(title="📝 Sugestões de melhoria para os manuais de utilizador", show_header=False, box=None, style="blue")
        for item in report["suggestions"]:
            table.add_row(f"📝 {item}")
        console.print(table)

    if not report["updated"] and not report["warnings"] and not report["suggestions"]:
        console.print("[green]✅ Sistema consistente! Nenhuma dívida de documentação detectada.[/green]")

def _analyze_changes(root: Path, days: int) -> List[str]:
    """
    Analyze changes in src/devbase in the last N days using git if available,
    otherwise check mtime.
    """
    changed_files = []
    src_path = root / "src" / "devbase"

    if not src_path.exists():
        return []

    # Try git first
    try:
        # Get files changed in last N days
        # git log --since="1 day ago" --name-only --pretty=format: src/devbase
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        result = subprocess.run(
            ["git", "log", f"--since={since_date}", "--name-only", "--pretty=format:", str(src_path.relative_to(root))],
            capture_output=True, text=True, cwd=root
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

        # Also check optional-dependencies if needed, but keeping it simple for now

        # Extract package names (basic parsing)
        pkg_names = []
        for dep in deps:
            # Handle "package>=version" or "package"
            # Split by common operators
            name = re.split(r'[<>=!]', dep)[0].strip()
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
            report["warnings"].append(f"Novas bibliotecas no pyproject.toml não mencionadas em ARCHITECTURE.md: {', '.join(missing_in_arch)}")

        if missing_in_readme:
             report["suggestions"].append(f"Bibliotecas não mencionadas em README.md: {', '.join(missing_in_readme)}")

    except Exception as e:
        report["warnings"].append(f"Falha ao verificar dependências: {e}")

def _verify_cli_consistency(root: Path, report: Dict[str, List[str]], fix: bool):
    """Check CLI commands vs Documentation"""
    commands_dir = root / "src" / "devbase" / "commands"
    found_commands = {} # module -> list of command names

    if not commands_dir.exists():
        return

    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name == "__init__.py" or cmd_file.name == "main.py": continue

        content = cmd_file.read_text()
        # Match @app.command("name") or @cli.command("name") or @something.command("name")
        # Also handle arguments/options implicitly, but main goal is command existence
        matches = re.findall(r'@\w+\.command\(\s*["\']([\w-]+)["\']', content)
        if matches:
            found_commands[cmd_file.stem] = matches

    # 2. Check Docs
    usage_guide = root / "USAGE-GUIDE.md"
    usage_content = usage_guide.read_text() if usage_guide.exists() else ""

    # Also check docs/cli/ if it exists (per prompt)
    docs_cli_dir = root / "docs" / "cli"
    docs_cli_content = ""
    if docs_cli_dir.exists():
        for f in docs_cli_dir.glob("*.md"):
            docs_cli_content += f.read_text() + "\n"

    full_docs_content = usage_content + "\n" + docs_cli_content

    missing_docs = []

    for module, cmds in found_commands.items():
        for cmd in cmds:
            # Check if command is mentioned
            # We look for "devbase <module> <cmd>" or just the command if module is implied
            # Or strict check: `devbase module cmd` or `devbase module` ... `cmd`

            # Simple heuristic: The command string must appear in the docs
            if cmd not in full_docs_content:
                 missing_docs.append(f"{module} {cmd}")

    if missing_docs:
        report["warnings"].append(f"Comandos CLI detectados mas não documentados em USAGE-GUIDE.md: {', '.join(missing_docs)}")

        if fix and usage_guide.exists():
            with open(usage_guide, "a") as f:
                f.write("\n\n## Undocumented Commands (Auto-detected)\n")
                f.write("> ⚠️ This section was automatically generated by the Audit bot.\n\n")
                for cmd in missing_docs:
                    f.write(f"- `devbase {cmd}`\n")
            report["updated"].append("USAGE-GUIDE.md (adicionados comandos não documentados)")

def _extract_table_schema(content: str, table_name: str) -> Dict[str, str]:
    """Extract column names and types for a table from SQL content."""
    # Find CREATE TABLE [IF NOT EXISTS] table_name ( ... );
    pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?" + re.escape(table_name) + r"\s*\((.*?)\);", re.IGNORECASE | re.DOTALL)
    match = pattern.search(content)
    if not match:
        return {}

    body = match.group(1)
    # Split by comma, but handle commas inside parens if any (simple split for now as schema is simple)
    # Remove comments
    lines = [line.strip() for line in body.split('\n')]
    columns = {}
    for line in lines:
        line = re.sub(r'--.*$', '', line).strip() # remove comments
        if not line or line.upper().startswith("PRIMARY KEY") or line.upper().startswith("CONSTRAINT"):
            continue

        # Simple extraction: first word is name, rest is type/constraints
        parts = line.split(maxsplit=1)
        if len(parts) >= 2:
            col_name = parts[0].strip(',')
            col_def = parts[1].strip(',')
            columns[col_name] = col_def

    return columns

def _verify_db_integrity(root: Path, report: Dict[str, List[str]]):
    """Check DB Code vs Technical Docs"""
    tech_doc = root / "docs" / "TECHNICAL_DESIGN_DOC.md"
    # adapter file defines the schema
    adapter_file = root / "src" / "devbase" / "adapters" / "storage" / "duckdb_adapter.py"

    if not tech_doc.exists():
        report["warnings"].append("TECHNICAL_DESIGN_DOC.md não encontrado.")
        return

    if not adapter_file.exists():
        report["warnings"].append("duckdb_adapter.py não encontrado.")
        return

    tech_content = tech_doc.read_text()
    adapter_content = adapter_file.read_text()

    tables_to_check = ["hot_fts", "cold_fts"]

    for table in tables_to_check:
        doc_schema = _extract_table_schema(tech_content, table)
        code_schema = _extract_table_schema(adapter_content, table)

        if not doc_schema:
            report["warnings"].append(f"Tabela `{table}` não encontrada na documentação (TECHNICAL_DESIGN_DOC.md).")
            continue

        if not code_schema:
            report["warnings"].append(f"Tabela `{table}` não encontrada na implementação (duckdb_adapter.py).")
            continue

        # Compare columns keys
        doc_cols = set(doc_schema.keys())
        code_cols = set(code_schema.keys())

        if doc_cols != code_cols:
            missing_in_doc = code_cols - doc_cols
            missing_in_code = doc_cols - code_cols
            msg = f"Inconsistência de esquema na tabela `{table}`:"
            if missing_in_doc:
                msg += f"\n  - Colunas no código mas faltam na doc: {missing_in_doc}"
            if missing_in_code:
                msg += f"\n  - Colunas na doc mas faltam no código: {missing_in_code}"
            report["warnings"].append(msg)
        else:
            # Good!
            pass

def _check_changelog(root: Path, report: Dict[str, List[str]], changes: List[str], fix: bool):
    """Check if CHANGELOG.md covers recent changes"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        report["warnings"].append("CHANGELOG.md não encontrado.")
        return

    content = changelog.read_text()

    # If there are changes but no "Unreleased" or "In Progress" section, warn
    # Patterns: ## [Unreleased], ## Unreleased, ## In Progress
    if not re.search(r"##\s+\[?Unreleased\]?", content, re.IGNORECASE) and \
       not re.search(r"##\s+In Progress", content, re.IGNORECASE):

        report["suggestions"].append("CHANGELOG.md deve ter uma secção 'Unreleased' ou 'In Progress' quando há alterações recentes.")

        if fix:
            # Prepend a draft section after the header
            # Assuming standard Keep A Changelog format
            lines = content.splitlines()

            # Find insertion point (after title or first ##)
            insert_idx = -1
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_idx = i
                    break

            new_section_lines = [
                "",
                "## [Unreleased] - In Progress",
                "",
                "### Changed",
            ]
            for change in changes[:5]:
                new_section_lines.append(f"- Modified {change}")
            if len(changes) > 5:
                new_section_lines.append(f"- ... and {len(changes)-5} more files.")
            new_section_lines.append("")

            if insert_idx != -1:
                lines[insert_idx:insert_idx] = new_section_lines
            else:
                lines.extend(new_section_lines) # append if no existing sections

            changelog.write_text("\n".join(lines))
            report["updated"].append("CHANGELOG.md (adicionada secção Unreleased)")
