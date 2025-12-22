"""
DevBase Setup Code Module
================================================================
PROPÓSITO:
    Implementa o setup-code.ps1 em Python.
    Configura a estrutura de código e o template Clean Architecture.

FUNCIONALIDADES:
    - Cria estrutura 20-29_CODE
    - Processa templates de código
    - Cria árvore detalhada do template clean-arch

USO:
    from setup_code import run_setup_code

    run_setup_code(fs, ui, policy_version="3.1")
"""

from pathlib import Path
from .filesystem import FileSystem
from .ui import UI
from .template_utils import process_templates


def run_setup_code(fs: FileSystem, ui: UI, policy_version: str = "3.1"):
    """
    Executa a lógica do Setup-Code.
    """
    ui.print_header("2. Code - Clean Architecture")

    # ================================================
    # FASE 1: ESTRUTURA PRINCIPAL
    # ================================================
    # Raiz da área de código
    area_20 = "20-29_CODE"
    
    base_folders = [
        f"{area_20}",
        f"{area_20}/21_monorepo_apps",
        f"{area_20}/22_monorepo_packages",
        f"{area_20}/22_monorepo_packages/shared-types",
        f"{area_20}/22_monorepo_packages/shared-utils",
        f"{area_20}/23_worktrees",
    ]

    for folder in base_folders:
        fs.ensure_dir(folder)

    # ================================================
    # FASE 2: PUBLICAÇÃO DE TEMPLATES
    # ================================================
    # ../templates/code
    current_dir = Path(__file__).resolve().parent
    templates_root = current_dir.parent / "templates" / "code"

    # Processa templates jogando dentro de 20-29_CODE (preservando estrutura interna do template)
    # Nota: No PS1, o destino era calculado relativo a Area20.
    process_templates(fs, ui, templates_root, base_dest_path=area_20, policy_version=policy_version)

    # ================================================
    # FASE 3: ESTRUTURA CLEAN ARCHITECTURE + DDD
    # ================================================
    # Cria pastas vazias específicas do template
    
    template_root = f"{area_20}/__template-clean-arch"
    
    clean_arch_structure = [
        # DOMAIN
        "src/domain/entities",
        "src/domain/value-objects",
        "src/domain/repositories",
        "src/domain/services",
        "src/domain/events",
        
        # APPLICATION
        "src/application/use-cases",
        "src/application/dtos",
        "src/application/mappers",
        "src/application/interfaces",
        
        # INFRASTRUCTURE
        "src/infrastructure/persistence/repositories",
        "src/infrastructure/persistence/migrations",
        "src/infrastructure/external",
        "src/infrastructure/messaging",
        
        # PRESENTATION
        "src/presentation/api",
        "src/presentation/cli",
        "src/presentation/web",
        
        # TESTS
        "tests/unit",
        "tests/integration",
        "tests/e2e",
    ]

    for rel_path in clean_arch_structure:
        fs.ensure_dir(f"{template_root}/{rel_path}")
