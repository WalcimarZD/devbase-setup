"""
Migrate Archive Module
======================
Migração de 99_archive para 90-99_ARCHIVE_COLD e 30_ai.

Responsabilidades:
    - *.chatmode.md → 30_ai/33_ai_config/
    - repositorio/ → 91_archived_projects/
    - IA/ → 30_ai/
    - Outros → 92_legacy_docs/
"""

from pathlib import Path
from typing import List

from migration_config import MigrationConfig
from migrate_docs import (
    MigrationSummary,
    MigrationResult,
    copy_directory_contents,
    copy_file_safe,
    ensure_parent_exists,
)


def migrate_chatmodes(
    source_dir: Path,
    dest_dir: Path,
    config: MigrationConfig
) -> List[MigrationResult]:
    """
    Migra arquivos *.chatmode.md para o diretório de configuração de IA.

    Args:
        source_dir: Diretório de origem (99_archive).
        dest_dir: Diretório de destino (33_ai_config).
        config: Configuração de migração.

    Returns:
        Lista de MigrationResult.
    """
    results = []

    if not source_dir.exists():
        return results

    chatmode_files = list(source_dir.glob("*.chatmode.md"))

    if chatmode_files:
        print(f"\n🤖 Arquivos chatmode ({len(chatmode_files)} encontrados):")

    for chatmode in chatmode_files:
        dest_path = dest_dir / chatmode.name

        result = copy_file_safe(
            chatmode,
            dest_path,
            config.dry_run,
            config.verbose,
        )
        results.append(result)

    return results


def migrate_archive(config: MigrationConfig) -> MigrationSummary:
    """
    Executa a migração do arquivo morto.

    Tratamento especial:
        - *.chatmode.md → 30-39_OPERATIONS/30_ai/33_ai_config/
        - repositorio/ → 90-99_ARCHIVE_COLD/91_archived_projects/
        - IA/ → 30-39_OPERATIONS/30_ai/
        - Exames_IA/ → 30-39_OPERATIONS/30_ai/exames-ia/
        - estrutura/ → 90-99_ARCHIVE_COLD/92_legacy_docs/
        - Outros arquivos → 90-99_ARCHIVE_COLD/92_legacy_docs/

    Args:
        config: Configuração de migração.

    Returns:
        MigrationSummary com os resultados.
    """
    summary = MigrationSummary(category="archive")

    source_archive = config.source_root / "99_archive"
    if not source_archive.exists():
        print("⚠️  Diretório 99_archive não encontrado")
        return summary

    print("\n📦 Migrando Arquivo Morto...")
    print("-" * 40)

    # 1. Migrar chatmodes (tratamento especial)
    chatmode_dest = config.target_root / config.chatmode_destination
    chatmode_results = migrate_chatmodes(source_archive, chatmode_dest, config)
    summary.results.extend(chatmode_results)

    for r in chatmode_results:
        if r.success:
            summary.files_copied += 1
        else:
            summary.errors += 1

    # 2. Migrar diretórios mapeados
    for source_rel, dest_rel in config.directory_mappings.items():
        if not source_rel.startswith("99_archive/"):
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

    # 3. Migrar arquivos e diretórios não mapeados
    print("\n📄 Itens não mapeados (→ 92_legacy_docs):")
    legacy_dest = config.target_root / "90-99_ARCHIVE_COLD" / "92_legacy_docs"

    # Diretórios já processados
    processed_dirs = set()
    for source_rel in config.directory_mappings.keys():
        if source_rel.startswith("99_archive/"):
            dir_name = source_rel.replace("99_archive/", "").split("/")[0]
            processed_dirs.add(dir_name)

    for item in source_archive.iterdir():
        # Pular chatmodes (já processados)
        if item.name.endswith(".chatmode.md"):
            continue

        # Pular diretórios já mapeados
        if item.is_dir() and item.name in processed_dirs:
            continue

        dest_path = legacy_dest / item.name

        if item.is_dir():
            results = copy_directory_contents(
                item,
                dest_path,
                config.excluded_dirs,
                config.excluded_files,
                config.dry_run,
                config.verbose,
            )
            summary.results.extend(results)

            for r in results:
                if r.success:
                    summary.files_copied += 1 if not r.is_directory else 0
                    summary.dirs_created += 1 if r.is_directory else 0
                else:
                    summary.errors += 1
        else:
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

    summary = migrate_archive(config)

    print("\n" + "=" * 40)
    print(f"📊 Resumo: {summary.files_copied} arquivos, {summary.errors} erros")
