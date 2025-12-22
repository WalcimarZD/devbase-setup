"""
DevBase Setup Core Module
================================================================
PROPÓSITO:
    Implementa o setup-core.ps1 em Python.
    Responsável por criar a estrutura básica de diretórios e arquivos de governança.

FUNCIONALIDADES:
    - Cria estrutura Johnny.Decimal (00-09, 10-19, etc.)
    - Processa templates de governança (.gitignore, README, etc.)
    - Substitui placeholders {{DATE}} e {{POLICY_VERSION}}

USO:
    from setup_core import run_setup_core

    run_setup_core(fs, ui, policy_version="3.1")
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Imports relativos (assumindo que estão no mesmo pacote)
from .filesystem import FileSystem
from .ui import UI


def run_setup_core(fs: FileSystem, ui: UI, policy_version: str = "3.1"):
    """
    Executa a lógica do Setup-Core.

    Args:
        fs: Instância do FileSystem.
        ui: Instância da UI.
        policy_version: Versão da política a ser injetada nos templates.
    """
    ui.print_header("1. Core - Structure and Governance")

    # ================================================
    # FASE 1: CRIAÇÃO DA ESTRUTURA DE DIRETÓRIOS
    # ================================================
    folders = [
        # 00-09_SYSTEM
        "00-09_SYSTEM/02_scripts-boot",
        # 40-49_MEDIA_ASSETS
        "40-49_MEDIA_ASSETS/41_raw_images",
        "40-49_MEDIA_ASSETS/42_videos_render",
        "40-49_MEDIA_ASSETS/43_exports",
        # 90-99_ARCHIVE_COLD
        "90-99_ARCHIVE_COLD/91_archived_projects",
        "90-99_ARCHIVE_COLD/92_archived_data",
    ]

    for list_folder in folders:
        fs.ensure_dir(list_folder)

    # ================================================
    # FASE 2: PUBLICAÇÃO DE TEMPLATES
    # ================================================
    from .template_utils import process_templates

    # Localiza o diretório de templates relativo a este arquivo
    # ../templates/core
    current_dir = Path(__file__).resolve().parent
    templates_root = current_dir.parent / "templates" / "core"

    process_templates(fs, ui, templates_root, base_dest_path="", policy_version=policy_version)
