"""
Post-Migration Module
=====================
Validação final e geração de relatório pós-migração.

Responsabilidades:
    - Contagem de arquivos migrados por categoria
    - Lista de arquivos não migrados (se houver)
    - Instruções para próximos passos
    - Geração de relatório em arquivo
"""

import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

from migration_config import MigrationConfig, CATEGORY_NAMES, CATEGORY_ICONS
from migrate_docs import MigrationSummary


@dataclass
class PostMigrationReport:
    """Relatório completo pós-migração."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source_root: str = ""
    target_root: str = ""
    dry_run: bool = False

    # Estatísticas por categoria
    docs_files: int = 0
    docs_errors: int = 0
    scripts_files: int = 0
    scripts_errors: int = 0
    archive_files: int = 0
    archive_errors: int = 0

    # Totais
    total_files: int = 0
    total_errors: int = 0

    # Detalhes
    failed_files: List[str] = field(default_factory=list)

    def calculate_totals(self):
        """Calcula os totais a partir das categorias."""
        self.total_files = self.docs_files + self.scripts_files + self.archive_files
        self.total_errors = self.docs_errors + self.scripts_errors + self.archive_errors


def generate_post_migration_report(
    config: MigrationConfig,
    summaries: Dict[str, MigrationSummary]
) -> PostMigrationReport:
    """
    Gera o relatório pós-migração a partir dos resumos de cada categoria.

    Args:
        config: Configuração utilizada na migração.
        summaries: Dicionário com MigrationSummary por categoria.

    Returns:
        PostMigrationReport completo.
    """
    report = PostMigrationReport(
        source_root=str(config.source_root),
        target_root=str(config.target_root),
        dry_run=config.dry_run,
    )

    # Processar cada categoria
    if "docs" in summaries:
        report.docs_files = summaries["docs"].files_copied
        report.docs_errors = summaries["docs"].errors
        for r in summaries["docs"].results:
            if not r.success:
                report.failed_files.append(str(r.source))

    if "scripts" in summaries:
        report.scripts_files = summaries["scripts"].files_copied
        report.scripts_errors = summaries["scripts"].errors
        for r in summaries["scripts"].results:
            if not r.success:
                report.failed_files.append(str(r.source))

    if "archive" in summaries:
        report.archive_files = summaries["archive"].files_copied
        report.archive_errors = summaries["archive"].errors
        for r in summaries["archive"].results:
            if not r.success:
                report.failed_files.append(str(r.source))

    report.calculate_totals()
    return report


def print_post_migration_report(report: PostMigrationReport):
    """
    Imprime o relatório pós-migração formatado para o console.

    Args:
        report: Relatório gerado por generate_post_migration_report.
    """
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO PÓS-MIGRAÇÃO")
    print("=" * 60)

    if report.dry_run:
        print("\n⚠️  MODO DRY-RUN: Nenhum arquivo foi copiado")

    print(f"\n📅 Data: {report.timestamp}")
    print(f"📂 Origem: {report.source_root}")
    print(f"📁 Destino: {report.target_root}")

    # Estatísticas por categoria
    print("\n📈 Arquivos migrados por categoria:")
    print(f"   📚 Documentação: {report.docs_files:,} arquivos")
    print(f"   ⚙️  Scripts:      {report.scripts_files:,} arquivos")
    print(f"   📦 Arquivo:      {report.archive_files:,} arquivos")
    print(f"   {'─' * 30}")
    print(f"   📊 TOTAL:        {report.total_files:,} arquivos")

    # Erros
    if report.total_errors > 0:
        print(f"\n❌ Erros encontrados: {report.total_errors}")
        print("   Arquivos com falha:")
        for failed in report.failed_files[:10]:  # Limitar a 10
            print(f"      • {failed}")
        if len(report.failed_files) > 10:
            print(f"      ... e mais {len(report.failed_files) - 10} arquivos")
    else:
        print("\n✅ Todos os arquivos migrados com sucesso!")

    # Próximos passos
    print("\n📋 PRÓXIMOS PASSOS:")
    print("   1. Verificar estrutura: python devbase.py doctor")
    print("   2. Clone manual dos repositórios Git para 21_monorepo_apps/")
    print("   3. Configurar dotfiles: devbase link-dotfiles")
    print("   4. Fazer backup do D:\\Projetos original")

    print("\n" + "=" * 60)


def save_report_to_file(
    report: PostMigrationReport,
    output_path: Optional[Path] = None
) -> Path:
    """
    Salva o relatório em arquivo JSON.

    Args:
        report: Relatório a ser salvo.
        output_path: Caminho do arquivo (opcional).

    Returns:
        Path do arquivo salvo.
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(report.target_root) / f"migration_report_{timestamp}.json"

    report_dict = asdict(report)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Relatório salvo em: {output_path}")
    return output_path


def validate_migration(config: MigrationConfig) -> List[str]:
    """
    Valida se a migração foi bem-sucedida verificando a estrutura do destino.

    Args:
        config: Configuração de migração.

    Returns:
        Lista de avisos/problemas encontrados.
    """
    issues = []

    # Verificar diretórios principais
    expected_dirs = [
        "10-19_KNOWLEDGE/15_references/patterns",
        "10-19_KNOWLEDGE/18_adr-decisions",
        "30-39_OPERATIONS/32_automation",
        "90-99_ARCHIVE_COLD",
    ]

    for dir_rel in expected_dirs:
        dir_path = config.target_root / dir_rel
        if not dir_path.exists():
            issues.append(f"Diretório esperado não criado: {dir_rel}")
        elif not any(dir_path.iterdir()):
            issues.append(f"Diretório vazio: {dir_rel}")

    # Verificar arquivos de padrões
    patterns_dir = config.target_root / "10-19_KNOWLEDGE/15_references/patterns"
    if patterns_dir.exists():
        expected_patterns = [
            "sql-patterns.md",
            "git-patterns.md",
            "python-patterns.md",
        ]
        for pattern_file in expected_patterns:
            if not (patterns_dir / pattern_file).exists():
                issues.append(f"Arquivo de padrão não migrado: {pattern_file}")

    return issues


if __name__ == "__main__":
    # Demonstração com dados de exemplo
    from migration_config import get_default_config

    config = get_default_config()

    # Simular resumos
    summaries = {
        "docs": MigrationSummary(category="docs", files_copied=15, errors=0),
        "scripts": MigrationSummary(category="scripts", files_copied=70, errors=0),
        "archive": MigrationSummary(category="archive", files_copied=25, errors=0),
    }

    report = generate_post_migration_report(config, summaries)
    print_post_migration_report(report)
