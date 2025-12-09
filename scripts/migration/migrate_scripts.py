"""
Migrate Scripts Module
======================
Migração de scripts de 03_scripts para 30-39_OPERATIONS.

Responsabilidades:
    - automation/ → 32_automation/
    - database/ → 32_automation/db-scripts/
    - utilities/ → 32_automation/utilities/
"""

from pathlib import Path
from typing import List

from migration_config import MigrationConfig
from migrate_docs import (
    MigrationSummary,
    copy_directory_contents,
    copy_file_safe,
)


def migrate_scripts(config: MigrationConfig) -> MigrationSummary:
    """
    Executa a migração de scripts de automação.

    Migra:
        - 03_scripts/automation → 32_automation
        - 03_scripts/database → 32_automation/db-scripts
        - 03_scripts/utilities → 32_automation/utilities

    Args:
        config: Configuração de migração.

    Returns:
        MigrationSummary com os resultados.
    """
    summary = MigrationSummary(category="scripts")

    source_scripts = config.source_root / "03_scripts"
    if not source_scripts.exists():
        print("⚠️  Diretório 03_scripts não encontrado")
        return summary

    print("\n⚙️  Migrando Scripts de Automação...")
    print("-" * 40)

    # 1. Migrar diretórios mapeados
    for source_rel, dest_rel in config.directory_mappings.items():
        if not source_rel.startswith("03_scripts/"):
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

    # 2. Migrar arquivos na raiz de 03_scripts (ex: README.md)
    print("\n📄 Arquivos na raiz de 03_scripts/:")
    dest_automation = config.target_root / "30-39_OPERATIONS" / "32_automation"

    for item in source_scripts.iterdir():
        if item.is_dir():
            continue  # Diretórios já processados

        dest_path = dest_automation / item.name

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
    config.dry_run = True
    config.verbose = True

    summary = migrate_scripts(config)

    print("\n" + "=" * 40)
    print(f"📊 Resumo: {summary.files_copied} arquivos, {summary.errors} erros")
