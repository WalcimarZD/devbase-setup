"""
DevBase Setup Operations Module
================================================================
PROPÓSITO:
    Implementa o setup-operations.ps1 em Python.
    Configura a área de operações (automação, backups, monitoring).

FUNCIONALIDADES:
    - Cria estrutura 30-39_OPERATIONS (exceto 30_ai que é separado)
    - 31_backups, 32_automation, 33_monitoring, 34_credentials, 35_devbase_cli
    - Processa templates de operações
    - (Opcional) Instala o próprio CLI na pasta de destino

USO:
    from setup_operations import run_setup_operations

    run_setup_operations(fs, ui, policy_version="3.1")
"""

import sys
from pathlib import Path
from filesystem import FileSystem
from ui import UI
from template_utils import process_templates


def run_setup_operations(fs: FileSystem, ui: UI, policy_version: str = "3.1"):
    """
    Executa a lógica do Setup-Operations.
    """
    ui.print_header("5. Operations - Automation")

    # ================================================
    # FASE 1: ESTRUTURA DE DIRETÓRIOS
    # ================================================
    
    area_30 = "30-39_OPERATIONS"
    
    folders = [
        f"{area_30}",
        f"{area_30}/31_backups",
        f"{area_30}/31_backups/local",
        f"{area_30}/31_backups/cloud",
        f"{area_30}/32_automation",
        f"{area_30}/33_monitoring",
        f"{area_30}/34_credentials",
        f"{area_30}/35_devbase_cli",
    ]

    for folder in folders:
        fs.ensure_dir(folder)

    # ================================================
    # FASE 2: PUBLICAÇÃO DE TEMPLATES
    # ================================================
    # ../templates/operations
    current_dir = Path(__file__).resolve().parent
    templates_root = current_dir.parent / "templates" / "operations"

    process_templates(
        fs, 
        ui, 
        templates_root, 
        base_dest_path=area_30, 
        policy_version=policy_version
    )

    # ================================================
    # FASE 3: INSTALAÇÃO DO CLI (PYTHON VERSION)
    # ================================================
    # Copia devbase.py e módulos para 35_devbase_cli para ser self-contained?
    # No PowerShell isso instalava o script. Aqui, vamos copiar apenas
    # o devbase.py como referência por enquanto.
    
    # Root do source (onde estamos rodando)
    # modules/python/setup_operations.py -> .../devbase.py
    source_root = current_dir.parent.parent
    devbase_py = source_root / "devbase.py"
    
    if devbase_py.exists():
        dest_cli = f"{area_30}/35_devbase_cli/devbase.py"
        try:
           fs.copy_atomic(str(devbase_py), dest_cli)
        except Exception as e:
           ui.print_step(f"Failed to copy devbase.py to CLI dir: {e}", "WARN")
