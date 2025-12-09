"""
Migration Configuration
=======================
Configuração central para migração do ambiente Projetos para DevBase.

Este módulo define:
    - Paths de origem e destino
    - Mapeamento de diretórios
    - Transformações de nomenclatura
    - Lista de exclusões

Baseado no Case Study Migration (case-study-migration.md).
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class MigrationConfig:
    """Configuração completa da migração."""

    # === PATHS PRINCIPAIS ===
    source_root: Path = field(default_factory=lambda: Path("D:/Projetos"))
    target_root: Path = field(default_factory=lambda: Path("D:/Dev_Workspace"))

    # === MAPEAMENTO DE DIRETÓRIOS ===
    # Formato: origem (relativo a source_root) -> destino (relativo a target_root)
    directory_mappings: Dict[str, str] = field(default_factory=lambda: {
        # Documentação (02_docs -> 10-19_KNOWLEDGE)
        "02_docs/decisions": "10-19_KNOWLEDGE/18_adr-decisions",
        "02_docs/guides": "10-19_KNOWLEDGE/15_references/guides",
        "02_docs/specs": "10-19_KNOWLEDGE/15_references/specs",
        "02_docs/templates": "10-19_KNOWLEDGE/15_references/templates",
        "02_docs/meetings": "10-19_KNOWLEDGE/15_references/meetings",

        # Scripts (03_scripts -> 30-39_OPERATIONS)
        "03_scripts/automation": "30-39_OPERATIONS/32_automation",
        "03_scripts/database": "30-39_OPERATIONS/32_automation/db-scripts",
        "03_scripts/utilities": "30-39_OPERATIONS/32_automation/utilities",

        # Archive (99_archive -> múltiplos destinos)
        "99_archive/repositorio": "90-99_ARCHIVE_COLD/91_archived_projects",
        "99_archive/IA": "30-39_OPERATIONS/30_ai",
        "99_archive/estrutura": "90-99_ARCHIVE_COLD/92_legacy_docs",
        "99_archive/Exames_IA": "30-39_OPERATIONS/30_ai/exames-ia",
    })

    # === MAPEAMENTO DE ARQUIVOS INDIVIDUAIS ===
    # Renomeação de arquivos específicos (origem -> destino)
    file_renames: Dict[str, str] = field(default_factory=lambda: {
        # Padrões de documentação
        "02_docs/PADROES.md": "10-19_KNOWLEDGE/15_references/patterns/coding-patterns.md",
        "02_docs/PADROES_SQL.md": "10-19_KNOWLEDGE/15_references/patterns/sql-patterns.md",
        "02_docs/PADROES_GIT.md": "10-19_KNOWLEDGE/15_references/patterns/git-patterns.md",
        "02_docs/PADROES_PYTHON.md": "10-19_KNOWLEDGE/15_references/patterns/python-patterns.md",
        "02_docs/PADROES_FRONTEND.md": "10-19_KNOWLEDGE/15_references/patterns/frontend-patterns.md",

        # Outros arquivos específicos
        "02_docs/ICEBOX.md": "10-19_KNOWLEDGE/15_references/icebox.md",
        "02_docs/JOURNAL.md": "10-19_KNOWLEDGE/11_journal/legacy-journal.md",
        "02_docs/knowledge-prompting-standards.md": "10-19_KNOWLEDGE/15_references/prompting-standards.md",
    })

    # === ARQUIVOS CHATMODE (tratamento especial) ===
    # Padrão: *.chatmode.md -> 30_ai/33_ai_config/
    chatmode_destination: str = "30-39_OPERATIONS/30_ai/33_ai_config"

    # === EXCLUSÕES ===
    # Diretórios a ignorar durante a cópia
    excluded_dirs: Set[str] = field(default_factory=lambda: {
        ".git",
        ".vs",
        ".vscode",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "bin",
        "obj",
        "packages",
        ".nuget",
    })

    # Arquivos a ignorar
    excluded_files: Set[str] = field(default_factory=lambda: {
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
        "*.pyc",
        "*.pyo",
    })

    # === CONFIGURAÇÕES DE EXECUÇÃO ===
    dry_run: bool = False
    verbose: bool = True
    create_backup_manifest: bool = True


def get_default_config() -> MigrationConfig:
    """Retorna a configuração padrão de migração."""
    return MigrationConfig()


def validate_config(config: MigrationConfig) -> List[str]:
    """
    Valida a configuração de migração.

    Returns:
        Lista de erros encontrados (vazia se válido).
    """
    errors = []

    # Verificar se source existe
    if not config.source_root.exists():
        errors.append(f"Diretório de origem não existe: {config.source_root}")

    # Verificar se target existe (DevBase deve ter sido executado)
    if not config.target_root.exists():
        errors.append(
            f"Diretório de destino não existe: {config.target_root}\n"
            "  Dica: Execute 'python devbase.py --root D:\\Dev_Workspace' primeiro."
        )

    # Verificar estrutura DevBase mínima
    required_dirs = [
        "10-19_KNOWLEDGE",
        "20-29_CODE",
        "30-39_OPERATIONS",
        "90-99_ARCHIVE_COLD",
    ]
    for dir_name in required_dirs:
        dir_path = config.target_root / dir_name
        if config.target_root.exists() and not dir_path.exists():
            errors.append(
                f"Estrutura DevBase incompleta: {dir_name} não encontrado.\n"
                "  Dica: Execute 'python devbase.py --root D:\\Dev_Workspace' primeiro."
            )

    return errors


# === CONSTANTES DE EXIBIÇÃO ===
CATEGORY_NAMES = {
    "docs": "Documentação",
    "scripts": "Scripts de Automação",
    "archive": "Arquivo Morto",
}

CATEGORY_ICONS = {
    "docs": "📚",
    "scripts": "⚙️",
    "archive": "📦",
}
