"""
DevBase Setup AI Module
================================================================
PROPÓSITO:
    Implementa o setup-ai.ps1 em Python.
    Configura a infraestrutura para Inteligência Artificial Local.

FUNCIONALIDADES:
    - Cria estrutura 30-39_OPERATIONS/30_ai
    - Configura pastas para Modelos, Contextos e Logs
    - Processa templates de IA.

USO:
    from setup_ai import run_setup_ai

    run_setup_ai(fs, ui, policy_version="3.1")
"""

from pathlib import Path
from filesystem import FileSystem
from ui import UI
from template_utils import process_templates


def run_setup_ai(fs: FileSystem, ui: UI, policy_version: str = "3.1"):
    """
    Executa a lógica do Setup-AI.
    """
    ui.print_header("4. AI - Local Intelligence")

    # ================================================
    # FASE 1: ESTRUTURA DE DIRETÓRIOS
    # ================================================
    
    area_30 = "30-39_OPERATIONS"
    ai_root = f"{area_30}/30_ai"
    
    folders = [
        f"{area_30}",
        f"{ai_root}",
        
        # 31_ai_local: Runtime e Contexto
        f"{ai_root}/31_ai_local/context",
        f"{ai_root}/31_ai_local/logs",
        
        # 32_ai_models: Modelos e Performance
        f"{ai_root}/32_ai_models/models",
        f"{ai_root}/32_ai_models/metadata",
        f"{ai_root}/32_ai_models/benchmarks",
        
        # 33_ai_config: Configuração e Segurança
        f"{ai_root}/33_ai_config/security",
        
        # scripts
        f"{ai_root}/scripts",
    ]

    for folder in folders:
        fs.ensure_dir(folder)

    # ================================================
    # FASE 2: PUBLICAÇÃO DE TEMPLATES
    # ================================================
    # ../../shared/templates/ai
    current_dir = Path(__file__).resolve().parent
    templates_root = current_dir.parent.parent / "shared" / "templates" / "ai"

    # Processa templates jogando dentro de 30_ai
    # Nota: O template_root mapeia para dentro de 30_ai
    # (ex: templates/ai/32_ai_models/benchmark.ps1 -> 30_ai/32_ai_models/benchmark.ps1)
    
    process_templates(
        fs, 
        ui, 
        templates_root, 
        base_dest_path=ai_root, 
        policy_version=policy_version
    )
