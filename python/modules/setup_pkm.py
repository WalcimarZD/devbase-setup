"""
DevBase Setup PKM Module
================================================================
PROPÓSITO:
    Implementa o setup-pkm.ps1 em Python.
    Configura a estrutura de Gestão de Conhecimento Pessoal (Personal Knowledge Management).

FUNCIONALIDADES:
    - Cria estrutura 10-19_KNOWLEDGE (Public Garden, Private Vault, etc.)
    - Processa templates de notas com placeholders avançados (Week, Year).

USO:
    from setup_pkm import run_setup_pkm

    run_setup_pkm(fs, ui, policy_version="3.1")
"""

from pathlib import Path
from datetime import datetime, timedelta
from filesystem import FileSystem
from ui import UI
from template_utils import process_templates


def run_setup_pkm(fs: FileSystem, ui: UI, policy_version: str = "3.1"):
    """
    Executa a lógica do Setup-PKM.
    """
    ui.print_header("3. PKM - Knowledge Management")

    # ================================================
    # FASE 1: ESTRUTURA DE DIRETÓRIOS
    # ================================================
    
    area_10 = "10-19_KNOWLEDGE"
    
    # Lista plana de diretórios a criar
    folders = [
        f"{area_10}",
        
        # 11_public_garden
        f"{area_10}/11_public_garden/posts",
        f"{area_10}/11_public_garden/notes",
        f"{area_10}/11_public_garden/til",
        
        # 12_private_vault (Air-Gap)
        f"{area_10}/12_private_vault/journal",
        f"{area_10}/12_private_vault/finances",
        f"{area_10}/12_private_vault/credentials",
        f"{area_10}/12_private_vault/brag-docs",
        
        # 15_references
        f"{area_10}/15_references/papers",
        f"{area_10}/15_references/books",
        f"{area_10}/15_references/patterns",
        f"{area_10}/15_references/checklists",
        
        # 18_adr-decisions
        f"{area_10}/18_adr-decisions",
    ]

    for folder in folders:
        fs.ensure_dir(folder)

    # ================================================
    # FASE 2: PUBLICAÇÃO DE TEMPLATES
    # ================================================
    # ../../shared/templates/pkm
    current_dir = Path(__file__).resolve().parent
    templates_root = current_dir.parent.parent / "shared" / "templates" / "pkm"

    # Preparar replacements adicionais
    now = datetime.now()
    replacements = {
        "{{YEAR}}": now.strftime("%Y"),
        "{{WEEK_NUMBER}}": now.strftime("%V"), # ISO week number
        "{{DATE_PLUS_6}}": (now + timedelta(days=6)).strftime("%Y-%m-%d"),
    }

    # Processa templates jogando dentro de 10-19_KNOWLEDGE
    process_templates(
        fs, 
        ui, 
        templates_root, 
        base_dest_path=area_10, 
        policy_version=policy_version,
        extra_replacements=replacements
    )
