#!/usr/bin/env python3
"""
DevBase Migration Orchestrator
==============================
Script principal que orquestra toda a migração de D:\\Projetos para D:\\Dev_Workspace.

Uso:
    # Modo dry-run (simulação)
    python run_migration.py --dry-run

    # Migração completa
    python run_migration.py

    # Migrar apenas uma categoria
    python run_migration.py --only docs
    python run_migration.py --only scripts
    python run_migration.py --only archive

    # Pular validação prévia
    python run_migration.py --skip-pre

    # Paths customizados
    python run_migration.py --source D:\\Projetos --target D:\\Dev_Workspace

Autor: DevBase Team
Versão: 1.0.0
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Adicionar diretório atual ao path para imports locais
sys.path.insert(0, str(Path(__file__).parent))

from migration_config import MigrationConfig, get_default_config, validate_config
from pre_migration import run_pre_migration, print_pre_migration_report
from migrate_docs import migrate_docs, MigrationSummary
from migrate_scripts import migrate_scripts
from migrate_archive import migrate_archive
from post_migration import (
    generate_post_migration_report,
    print_post_migration_report,
    save_report_to_file,
    validate_migration,
)


VERSION = "1.0.0"


def print_banner():
    """Imprime o banner do script."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 DevBase Migration Tool v{version}                          ║
║   ─────────────────────────────────────────────────────────   ║
║   Migração: Projetos → Dev_Workspace                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """.format(version=VERSION))


def confirm_migration(config: MigrationConfig) -> bool:
    """
    Solicita confirmação do usuário para prosseguir com a migração.

    Args:
        config: Configuração de migração.

    Returns:
        True se o usuário confirmar, False caso contrário.
    """
    if config.dry_run:
        print("\n🔍 Modo DRY-RUN ativado - nenhum arquivo será copiado")
        return True

    print("\n" + "=" * 60)
    print("⚠️  CONFIRMAÇÃO NECESSÁRIA")
    print("=" * 60)
    print(f"\n📂 Origem:  {config.source_root}")
    print(f"📁 Destino: {config.target_root}")
    print("\nA migração irá COPIAR arquivos (a origem permanece intacta).")

    try:
        response = input("\nDeseja prosseguir? [s/N]: ").strip().lower()
        return response in ("s", "sim", "y", "yes")
    except (KeyboardInterrupt, EOFError):
        print("\n\n❌ Migração cancelada pelo usuário.")
        return False


def run_migration(
    config: MigrationConfig,
    skip_pre: bool = False,
    only_category: Optional[str] = None
) -> int:
    """
    Executa o fluxo completo de migração.

    Args:
        config: Configuração de migração.
        skip_pre: Se True, pula validação prévia.
        only_category: Se definido, migra apenas esta categoria.

    Returns:
        Código de saída (0 = sucesso, 1 = erro).
    """
    summaries: Dict[str, MigrationSummary] = {}

    # ============================================
    # 1. PRÉ-MIGRAÇÃO
    # ============================================
    if not skip_pre:
        print("\n" + "=" * 60)
        print("🔍 FASE 1: PRÉ-MIGRAÇÃO")
        print("=" * 60)

        pre_report = run_pre_migration(config)
        print_pre_migration_report(pre_report, verbose=config.verbose)

        if not pre_report.is_valid:
            print("\n❌ Migração abortada devido a erros na validação prévia.")
            print("   Corrija os problemas listados acima e tente novamente.")
            return 1

        if pre_report.warnings:
            print("\n⚠️  Existem avisos. Recomendamos corrigir antes de prosseguir.")

    # Confirmação
    if not confirm_migration(config):
        return 0

    # ============================================
    # 2. MIGRAÇÃO
    # ============================================
    print("\n" + "=" * 60)
    print("📦 FASE 2: MIGRAÇÃO")
    print("=" * 60)

    start_time = datetime.now()

    # Migrar Documentação
    if only_category is None or only_category == "docs":
        summaries["docs"] = migrate_docs(config)

    # Migrar Scripts
    if only_category is None or only_category == "scripts":
        summaries["scripts"] = migrate_scripts(config)

    # Migrar Arquivo
    if only_category is None or only_category == "archive":
        summaries["archive"] = migrate_archive(config)

    elapsed = datetime.now() - start_time

    # ============================================
    # 3. PÓS-MIGRAÇÃO
    # ============================================
    print("\n" + "=" * 60)
    print("✅ FASE 3: PÓS-MIGRAÇÃO")
    print("=" * 60)

    # Gerar e imprimir relatório
    report = generate_post_migration_report(config, summaries)
    print_post_migration_report(report)

    print(f"\n⏱️  Tempo de execução: {elapsed.total_seconds():.2f} segundos")

    # Salvar relatório se não for dry-run
    if not config.dry_run:
        save_report_to_file(report)

    # Validar migração
    if not config.dry_run:
        issues = validate_migration(config)
        if issues:
            print("\n⚠️  Avisos de validação:")
            for issue in issues:
                print(f"   • {issue}")

    # Sucesso
    if report.total_errors == 0:
        print("\n🎉 Migração concluída com sucesso!")
        return 0
    else:
        print(f"\n⚠️  Migração concluída com {report.total_errors} erros.")
        return 1


def main():
    """Ponto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="DevBase Migration Tool - Migra Projetos para Dev_Workspace",
        epilog="Exemplo: python run_migration.py --dry-run",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular migração sem copiar arquivos",
    )
    parser.add_argument(
        "--source",
        default="D:/Projetos",
        help="Diretório de origem (default: D:/Projetos)",
    )
    parser.add_argument(
        "--target",
        default="D:/Dev_Workspace",
        help="Diretório de destino (default: D:/Dev_Workspace)",
    )
    parser.add_argument(
        "--skip-pre",
        action="store_true",
        help="Pular validações de pré-migração",
    )
    parser.add_argument(
        "--only",
        choices=["docs", "scripts", "archive"],
        help="Migrar apenas uma categoria específica",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Modo silencioso (menos output)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    args = parser.parse_args()

    # Imprimir banner
    if not args.quiet:
        print_banner()

    # Configurar
    config = get_default_config()
    config.source_root = Path(args.source)
    config.target_root = Path(args.target)
    config.dry_run = args.dry_run
    config.verbose = not args.quiet

    # Executar migração
    try:
        exit_code = run_migration(
            config,
            skip_pre=args.skip_pre,
            only_category=args.only,
        )
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\n❌ Migração interrompida pelo usuário.")
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
