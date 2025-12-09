"""
Migrate Docs Module
===================
Migração de documentação de 02_docs para 10-19_KNOWLEDGE.

Responsabilidades:
    - Copiar diretórios (decisions, guides, specs, etc.)
    - Renomear arquivos PADROES_*.md para patterns/
    - Manter estrutura hierárquica
"""

import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict

from migration_config import MigrationConfig


@dataclass
class MigrationResult:
    """Resultado de uma operação de migração."""
    source: Path
    destination: Path
    success: bool
    is_directory: bool
    error_message: str = ""


@dataclass
class MigrationSummary:
    """Resumo da migração de uma categoria."""
    category: str
    files_copied: int = 0
    dirs_created: int = 0
    errors: int = 0
    results: List[MigrationResult] = field(default_factory=list)


def ensure_parent_exists(path: Path, dry_run: bool = False) -> bool:
    """
    Garante que o diretório pai existe.

    Args:
        path: Caminho do arquivo/diretório.
        dry_run: Se True, não cria o diretório.

    Returns:
        True se o diretório pai existe ou foi criado.
    """
    parent = path.parent
    if parent.exists():
        return True

    if not dry_run:
        parent.mkdir(parents=True, exist_ok=True)
    return True


def copy_file_safe(
    source: Path,
    destination: Path,
    dry_run: bool = False,
    verbose: bool = True
) -> MigrationResult:
    """
    Copia um arquivo de forma segura.

    Args:
        source: Arquivo de origem.
        destination: Caminho de destino.
        dry_run: Se True, apenas simula.
        verbose: Se True, imprime operações.

    Returns:
        MigrationResult com o resultado da operação.
    """
    result = MigrationResult(
        source=source,
        destination=destination,
        success=False,
        is_directory=False,
    )

    if not source.exists():
        result.error_message = "Arquivo de origem não existe"
        return result

    if not source.is_file():
        result.error_message = "Origem não é um arquivo"
        return result

    try:
        ensure_parent_exists(destination, dry_run)

        if dry_run:
            if verbose:
                print(f"  [DRY-RUN] Copiaria: {source.name} → {destination}")
            result.success = True
        else:
            shutil.copy2(source, destination)
            if verbose:
                print(f"  ✓ Copiado: {source.name}")
            result.success = True

    except Exception as e:
        result.error_message = str(e)
        if verbose:
            print(f"  ✗ Erro ao copiar {source.name}: {e}")

    return result


def copy_directory_contents(
    source_dir: Path,
    dest_dir: Path,
    excluded_dirs: set,
    excluded_files: set,
    dry_run: bool = False,
    verbose: bool = True
) -> List[MigrationResult]:
    """
    Copia recursivamente o conteúdo de um diretório.

    Args:
        source_dir: Diretório de origem.
        dest_dir: Diretório de destino.
        excluded_dirs: Diretórios a ignorar.
        excluded_files: Arquivos a ignorar.
        dry_run: Se True, apenas simula.
        verbose: Se True, imprime operações.

    Returns:
        Lista de MigrationResult.
    """
    results = []

    if not source_dir.exists():
        return results

    # Criar diretório de destino
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
    elif verbose:
        print(f"  [DRY-RUN] Criaria diretório: {dest_dir}")

    try:
        for item in source_dir.iterdir():
            # Verificar exclusões
            if item.name in excluded_dirs or item.name in excluded_files:
                continue

            # Verificar padrões de exclusão (ex: *.pyc)
            skip = False
            for pattern in excluded_files:
                if "*" in pattern and item.match(pattern):
                    skip = True
                    break
            if skip:
                continue

            dest_item = dest_dir / item.name

            if item.is_dir():
                # Recursivamente copiar subdiretório
                sub_results = copy_directory_contents(
                    item,
                    dest_item,
                    excluded_dirs,
                    excluded_files,
                    dry_run,
                    verbose,
                )
                results.extend(sub_results)
            else:
                # Copiar arquivo
                result = copy_file_safe(item, dest_item, dry_run, verbose)
                results.append(result)

    except PermissionError as e:
        if verbose:
            print(f"  ✗ Erro de permissão: {source_dir}")

    return results


def migrate_docs(config: MigrationConfig) -> MigrationSummary:
    """
    Executa a migração de documentação.

    Migra:
        - 02_docs/decisions → 18_adr-decisions
        - 02_docs/guides → 15_references/guides
        - 02_docs/specs → 15_references/specs
        - 02_docs/templates → 15_references/templates
        - 02_docs/meetings → 15_references/meetings
        - PADROES_*.md → 15_references/patterns/

    Args:
        config: Configuração de migração.

    Returns:
        MigrationSummary com os resultados.
    """
    summary = MigrationSummary(category="docs")

    source_docs = config.source_root / "02_docs"
    if not source_docs.exists():
        print("⚠️  Diretório 02_docs não encontrado")
        return summary

    print("\n📚 Migrando Documentação...")
    print("-" * 40)

    # 1. Migrar diretórios mapeados
    for source_rel, dest_rel in config.directory_mappings.items():
        if not source_rel.startswith("02_docs/"):
            continue

        source_path = config.source_root / source_rel
        dest_path = config.target_root / dest_rel

        if not source_path.exists():
            continue

        print(f"\n📁 {source_path.name} → {dest_path.relative_to(config.target_root)}")

        results = copy_directory_contents(
            source_path,
            dest_path,
            config.excluded_dirs,
            config.excluded_files,
            config.dry_run,
            config.verbose,
        )
        summary.results.extend(results)

        for r in results:
            if r.success:
                if r.is_directory:
                    summary.dirs_created += 1
                else:
                    summary.files_copied += 1
            else:
                summary.errors += 1

    # 2. Migrar arquivos individuais com renomeação
    print("\n📄 Arquivos com renomeação:")
    for source_rel, dest_rel in config.file_renames.items():
        if not source_rel.startswith("02_docs/"):
            continue

        source_path = config.source_root / source_rel
        dest_path = config.target_root / dest_rel

        if not source_path.exists():
            continue

        result = copy_file_safe(
            source_path,
            dest_path,
            config.dry_run,
            config.verbose,
        )
        summary.results.append(result)

        if result.success:
            summary.files_copied += 1
        else:
            summary.errors += 1

    # 3. Migrar arquivos restantes na raiz de 02_docs
    print("\n📄 Arquivos restantes em 02_docs/:")
    dest_refs = config.target_root / "10-19_KNOWLEDGE" / "15_references"

    for item in source_docs.iterdir():
        if item.is_dir():
            continue  # Diretórios já processados acima

        # Pular arquivos já mapeados
        relative = f"02_docs/{item.name}"
        if relative in config.file_renames:
            continue

        # Arquivos não mapeados vão para 15_references/
        dest_path = dest_refs / item.name

        result = copy_file_safe(
            item,
            dest_path,
            config.dry_run,
            config.verbose,
        )
        summary.results.append(result)

        if result.success:
            summary.files_copied += 1
        else:
            summary.errors += 1

    return summary


if __name__ == "__main__":
    # Teste standalone
    from migration_config import get_default_config

    config = get_default_config()
    config.dry_run = True  # Modo seguro para teste
    config.verbose = True

    summary = migrate_docs(config)

    print("\n" + "=" * 40)
    print(f"📊 Resumo: {summary.files_copied} arquivos, {summary.errors} erros")
